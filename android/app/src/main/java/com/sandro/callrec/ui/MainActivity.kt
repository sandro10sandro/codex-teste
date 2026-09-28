package com.sandro.callrec.ui

import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
import android.graphics.Typeface
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.text.InputType
import android.view.View
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import com.sandro.callrec.device.DeviceProfile
import com.sandro.callrec.device.DialerSupport
import com.sandro.callrec.device.OemDialer
import com.sandro.callrec.log.TechLog
import com.sandro.callrec.probe.CapabilityProbe
import com.sandro.callrec.probe.Permissions
import com.sandro.callrec.probe.Phase
import com.sandro.callrec.probe.PrefsKeyValueStore
import com.sandro.callrec.probe.ProbeStore
import com.sandro.callrec.record.CallRecorderService
import com.sandro.callrec.record.ServiceState
import com.sandro.callrec.storage.OemRecordingImporter
import com.sandro.callrec.storage.RecordingStore
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/** Tela única de laboratório: permissões, sonda, monitoramento, importação, log. Construída em código (sem XML/androidx). */
class MainActivity : Activity() {

    private val ui = Handler(Looper.getMainLooper())
    private lateinit var kv: PrefsKeyValueStore
    private lateinit var store: ProbeStore
    private lateinit var statusView: TextView
    private lateinit var outputView: TextView
    private lateinit var extraInput: EditText

    private val refresh = object : Runnable {
        override fun run() {
            renderStatus()
            ui.postDelayed(this, 1000)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        TechLog.init(this)
        kv = PrefsKeyValueStore(this)
        store = ProbeStore(kv)
        setContentView(buildLayout())
        showConsentIfNeeded()
    }

    override fun onResume() {
        super.onResume()
        ui.post(refresh)
    }

    override fun onPause() {
        ui.removeCallbacks(refresh)
        super.onPause()
    }

    // ------------------------------------------------------------------ layout

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()

    private fun label(text: String) = TextView(this).apply {
        this.text = text
        textSize = 13f
        setTypeface(typeface, Typeface.BOLD)
        setPadding(0, dp(14), 0, dp(4))
    }

    private fun button(text: String, onClick: () -> Unit) = Button(this).apply {
        this.text = text
        isAllCaps = false
        setOnClickListener { onClick() }
    }

    private fun mono(size: Float = 11f) = TextView(this).apply {
        typeface = Typeface.MONOSPACE
        textSize = size
        setTextIsSelectable(true)
    }

    private fun buildLayout(): View {
        val col = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(16), dp(16), dp(16), dp(24))
        }
        col.addView(TextView(this).apply {
            text = "CallLab — gravador de chamadas (laboratório)"
            textSize = 20f
            setTypeface(typeface, Typeface.BOLD)
        })
        col.addView(mono().apply { text = DeviceProfile.current(this@MainActivity).summary() })

        statusView = mono()
        col.addView(label("Estado"))
        col.addView(statusView)

        col.addView(label("1. Acessos"))
        col.addView(button("Conceder permissões de execução") { requestRuntime() })
        col.addView(button("Acesso a notificações (nome/app do WhatsApp)") {
            open(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
        })
        col.addView(button("Ignorar otimização de bateria") { requestBatteryExemption() })
        col.addView(button("Acessibilidade (necessária para gravar em chamada)") { open(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)) })

        col.addView(label("2. Diagnóstico"))
        col.addView(button("Rodar sonda de capacidades (ocioso)") { runProbe() })
        col.addView(button("Zerar aprendizado deste aparelho") {
            kv.clear()
            toast("Aprendizado apagado")
        })
        extraInput = EditText(this).apply {
            hint = "IDs extras de AudioSource (só valores que o AudioRecord aceita), ex.: 1997,1998,1999,2000"
            inputType = InputType.TYPE_CLASS_TEXT
            setText(store.extraSources().joinToString(","))
        }
        col.addView(extraInput)
        col.addView(button("Salvar IDs extras de fonte") { saveExtras() })

        col.addView(label("3. Gravação"))
        col.addView(button("Iniciar monitoramento de chamadas") { startMonitoring() })
        col.addView(button("Parar monitoramento") { CallRecorderService.stop(this) })
        col.addView(button("Gravar teste manual (10 s)") { manualTest() })

        col.addView(label("4. Gravação nativa do discador (duas pontas)"))
        col.addView(button("Diagnóstico do discador e do fabricante") { dialerDiagnosis() })
        col.addView(button("Abrir configurações de gravação do discador") { openDialerRecording() })
        val ui = getSharedPreferences("calllab_ui", MODE_PRIVATE)
        col.addView(CheckBox(this).apply {
            text = "Importar automaticamente a gravação nativa após cada chamada"
            isChecked = ui.getBoolean("auto_import_native", true)
            setOnCheckedChangeListener { _, on -> ui.edit().putBoolean("auto_import_native", on).apply() }
        })

        col.addView(label("5. Biblioteca"))
        col.addView(button("Gravações") { startActivity(Intent(this, RecordingsActivity::class.java)) })
        col.addView(button("Importar gravações nativas do fabricante") { scanNative() })

        col.addView(label("6. Log técnico"))
        col.addView(button("Ver log") { outputView.text = TechLog.readTail(60_000).ifBlank { "(log vazio)" } })
        col.addView(button("Compartilhar log") { shareLog() })

        col.addView(label("Saída"))
        outputView = mono().apply { text = "Rode a sonda para ver o relatório." }
        col.addView(outputView)

        return ScrollView(this).apply { addView(col) }
    }

    // ------------------------------------------------------------------ ações

    private fun renderStatus() {
        val snap = Permissions.snapshot(this)
        statusView.text = buildString {
            appendLine("Serviço: ${ServiceState.status}${if (ServiceState.currentSource.isNotEmpty()) " via ${ServiceState.currentSource}" else ""}")
            snap.entries.forEach { (k, v) -> appendLine("${if (v) "[x]" else "[ ]"} $k") }
            append("Log: ${TechLog.path ?: "-"}")
        }
    }

    private fun requestRuntime() {
        val missing = Permissions.missingRuntime(this)
        if (missing.isEmpty()) toast("Todas as permissões já concedidas") else requestPermissions(missing.toTypedArray(), 10)
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        permissions.zip(grantResults.toList()).forEach { (p, r) ->
            TechLog.event("perm", "resultado de permissão", "permission" to p, "granted" to (r == 0))
        }
        renderStatus()
    }

    private fun requestBatteryExemption() {
        val direct = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, Uri.parse("package:$packageName"))
        if (!open(direct, quiet = true)) open(Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS))
    }

    /** Abre a tela; devolve false se nenhum app trata a intenção. [quiet] suprime o aviso para permitir fallback. */
    private fun open(i: Intent, quiet: Boolean = false): Boolean = try {
        startActivity(i)
        true
    } catch (t: Throwable) {
        if (!quiet) toast("Não foi possível abrir: ${t.message}")
        false
    }

    private fun runProbe() {
        if (!Permissions.has(this, android.Manifest.permission.RECORD_AUDIO)) {
            toast("Conceda RECORD_AUDIO primeiro")
            return
        }
        outputView.text = "Executando sonda…"
        Thread({
            val report = CapabilityProbe(this, store).runAll(Phase.IDLE) { msg ->
                runOnUiThread { outputView.text = msg }
            }
            val saved = saveReport(report.toJson().toString(2), report.toText())
            runOnUiThread {
                outputView.text = report.toText() + "\nRelatório salvo em:\n$saved"
            }
        }, "Probe").start()
    }

    private fun saveReport(json: String, text: String): String {
        val dir = File(getExternalFilesDir(null) ?: filesDir, "reports").also { it.mkdirs() }
        val stamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
        File(dir, "probe_$stamp.json").writeText(json)
        val txt = File(dir, "probe_$stamp.txt")
        txt.writeText(text)
        return txt.absolutePath
    }

    private fun saveExtras() {
        val ids = extraInput.text.toString().split(",", " ", ";").mapNotNull { it.trim().toIntOrNull() }
        store.setExtraSources(ids)
        TechLog.event("probe", "IDs extras de fonte salvos", "ids" to ids.joinToString())
        toast("Salvo: ${ids.joinToString().ifEmpty { "nenhum" }}")
    }

    private fun startMonitoring() {
        val missing = Permissions.missingRuntime(this).filter {
            it == android.Manifest.permission.RECORD_AUDIO || it == android.Manifest.permission.READ_PHONE_STATE
        }
        if (missing.isNotEmpty()) {
            toast("Conceda RECORD_AUDIO e READ_PHONE_STATE primeiro")
            return
        }
        if (!Permissions.isAccessibilityEnabled(this)) {
            AlertDialog.Builder(this)
                .setTitle("Acessibilidade desativada")
                .setMessage(
                    "Pela documentação do Android, durante uma chamada um app comum recebe SILÊNCIO do " +
                        "microfone; a exceção para app não privilegiado é ser um serviço de acessibilidade ativo. " +
                        "Sem ele, as gravações de chamada tendem a sair vazias (o app registra isso no log).\n\n" +
                        "Ative \"CallLab\" em Acessibilidade. No Android 13+, apps instalados fora da loja podem " +
                        "exigir liberar \"Configurações restritas\" em Informações do app.",
                )
                .setPositiveButton("Abrir acessibilidade") { _, _ -> open(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)) }
                .setNegativeButton("Iniciar mesmo assim") { _, _ -> launchMonitor() }
                .show()
            return
        }
        launchMonitor()
    }

    private fun launchMonitor() =
        CallRecorderService.startForeground(this, CallRecorderService.ACTION_START_MONITOR)

    private fun manualTest() {
        if (!Permissions.has(this, android.Manifest.permission.RECORD_AUDIO)) {
            toast("Conceda RECORD_AUDIO primeiro")
            return
        }
        CallRecorderService.startForeground(this, CallRecorderService.ACTION_MANUAL_START, 10)
        toast("Gravando 10 s. Fale e/ou toque áudio no alto-falante.")
    }

    private fun dialerDiagnosis() {
        outputView.text = "Analisando o discador…"
        Thread({
            val hits = store.nativeHits(DeviceProfile.current(this).key)
            val text = DialerSupport.report(this, hits)
            runOnUiThread { outputView.text = text }
        }, "DialerDiag").start()
    }

    private fun openDialerRecording() {
        val oem = DeviceProfile.current(this).oem
        val how = DialerSupport.openRecordingSettings(this)
        outputView.text = when (how) {
            DialerSupport.Opened.SETTINGS_SCREEN -> "Abri a tela de configuração do discador.\n\n" + OemDialer.instructions(oem)
            DialerSupport.Opened.DIALER_APP ->
                "Abri o app Telefone (este fabricante não expõe a tela de gravação diretamente). Faça o caminho:\n\n" + OemDialer.instructions(oem)
            DialerSupport.Opened.DIAL_GENERIC ->
                "Abri o discador. Faça o caminho:\n\n" + OemDialer.instructions(oem)
            DialerSupport.Opened.FAILED -> "Não consegui abrir o discador. Faça manualmente:\n\n" + OemDialer.instructions(oem)
        }
    }

    private fun scanNative() {
        outputView.text = "Procurando gravações nativas…"
        Thread({
            val found = OemRecordingImporter.scan(this)
            runOnUiThread {
                if (found.isEmpty()) {
                    outputView.text = "Nenhuma gravação de chamada acessível via MediaStore.\n" +
                        "Gravações mantidas em armazenamento privado do discador não são visíveis a apps de terceiros."
                    return@runOnUiThread
                }
                AlertDialog.Builder(this)
                    .setTitle("${found.size} gravação(ões) encontradas")
                    .setMessage(found.take(12).joinToString("\n") { "${it.path}${it.name}" })
                    .setPositiveButton("Importar todas") { _, _ ->
                        Thread({
                            val rs = RecordingStore(this)
                            val keys = rs.importKeys().toMutableSet()
                            val n = found.count { OemRecordingImporter.importOne(this, rs, it, keys) != null }
                            runOnUiThread { outputView.text = "$n importada(s); ${found.size - n} já existiam ou falharam." }
                        }, "Import").start()
                    }
                    .setNegativeButton("Cancelar", null)
                    .show()
            }
        }, "ScanNative").start()
    }

    private fun shareLog() {
        val text = TechLog.readTail(100_000)
        if (text.isBlank()) {
            toast("Log vazio")
            return
        }
        startActivity(
            Intent.createChooser(
                Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT, text),
                "Compartilhar log",
            ),
        )
    }

    private fun showConsentIfNeeded() {
        val prefs = getSharedPreferences("calllab_ui", MODE_PRIVATE)
        if (prefs.getBoolean("consent_v1", false)) return
        AlertDialog.Builder(this)
            .setTitle("Uso responsável")
            .setMessage(
                "Este app grava chamadas neste aparelho de laboratório. Use apenas em aparelhos seus e em " +
                    "conversas para as quais você tem o direito de gravar; a lei sobre gravar a outra parte varia " +
                    "por país e situação. Uma notificação permanente fica visível enquanto o monitoramento estiver ativo.",
            )
            .setCancelable(false)
            .setPositiveButton("Entendi e aceito") { _, _ -> prefs.edit().putBoolean("consent_v1", true).apply() }
            .setNegativeButton("Sair") { _, _ -> finish() }
            .show()
    }

    private fun toast(s: String) = Toast.makeText(this, s, Toast.LENGTH_SHORT).show()
}

package com.sandro.callrec.device

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.telecom.TelecomManager
import com.sandro.callrec.log.TechLog
import com.sandro.callrec.storage.OemRecordingImporter

/** Integração com o discador do sistema para a gravação de chamada embutida do fabricante. */
object DialerSupport {

    enum class Opened { SETTINGS_SCREEN, DIALER_APP, DIAL_GENERIC, FAILED }

    fun defaultDialer(context: Context): String? = try {
        (context.getSystemService(Context.TELECOM_SERVICE) as TelecomManager).defaultDialerPackage
    } catch (_: Throwable) {
        null
    }

    private fun isInstalled(pm: PackageManager, pkg: String) = try {
        pm.getPackageInfo(pkg, 0)
        true
    } catch (_: Throwable) {
        false
    }

    /**
     * Tenta abrir a tela de gravação de chamada do discador. Cada componente candidato é tentado de verdade
     * (a maioria dos fabricantes não exporta a tela); se nenhum abrir, abre o próprio discador, e por último o
     * teclado de discagem. As instruções por fabricante ([OemDialer.instructions]) cobrem o caminho manual.
     */
    fun openRecordingSettings(context: Context): Opened {
        val pm = context.packageManager
        val dialer = defaultDialer(context)
        for (t in OemDialer.settingsTargets(dialer)) {
            try {
                val i = Intent().setClassName(t.pkg, t.cls).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                if (i.resolveActivity(pm) == null) continue
                context.startActivity(i)
                TechLog.event("dialer", "abriu tela de configuração", "pkg" to t.pkg, "cls" to t.cls)
                return Opened.SETTINGS_SCREEN
            } catch (t2: Throwable) {
                TechLog.event("dialer", "tela não abriu", "pkg" to t.pkg, "cls" to t.cls, "error" to t2.javaClass.simpleName)
            }
        }
        if (dialer != null) {
            try {
                pm.getLaunchIntentForPackage(dialer)?.let {
                    context.startActivity(it.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                    TechLog.event("dialer", "abriu o discador", "pkg" to dialer)
                    return Opened.DIALER_APP
                }
            } catch (_: Throwable) {
            }
        }
        return try {
            context.startActivity(Intent(Intent.ACTION_DIAL).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            Opened.DIAL_GENERIC
        } catch (_: Throwable) {
            Opened.FAILED
        }
    }

    /** Diagnóstico legível: o que este aparelho sugere sobre gravação nativa e o que já apareceu na prática. */
    fun report(context: Context, nativeHits: Int): String {
        val profile = DeviceProfile.current(context)
        val pm = context.packageManager
        val dialer = defaultDialer(context)
        val present = OemDialer.KNOWN_DIALERS.filter { isInstalled(pm, it) }
        val found = OemRecordingImporter.scan(context)
        return buildString {
            appendLine("== GRAVAÇÃO NATIVA DO DISCADOR ==")
            appendLine("Fabricante: ${profile.oem.name}  (${profile.manufacturer} ${profile.model})")
            appendLine("Discador padrão: ${dialer ?: "não identificado"}")
            appendLine("Pacotes de discador presentes: ${if (present.isEmpty()) "nenhum conhecido" else present.joinToString()}")
            appendLine("Costuma ter gravador embutido: ${if (OemDialer.likelyHasBuiltInRecorder(profile.oem)) "provável (varia por região)" else "incerto"}")
            appendLine()
            appendLine("Gravações de chamada acessíveis (MediaStore): ${found.size}")
            found.map { it.path }.distinct().take(5).forEach { appendLine("  pasta: $it") }
            appendLine("Importações automáticas bem-sucedidas neste aparelho: $nativeHits")
            appendLine()
            appendLine("Como ligar a gravação automática:")
            appendLine(OemDialer.instructions(profile.oem))
            appendLine()
            appendLine(
                if (found.isNotEmpty()) "Há arquivos acessíveis: este é o caminho para as DUAS pontas. Ouça um para confirmar."
                else "Nenhum arquivo acessível ainda. Ligue a gravação automática, faça uma chamada e volte aqui. " +
                    "Se o discador não tiver o recurso, ou guardar em armazenamento privado, este caminho não existe neste aparelho.",
            )
        }
    }
}

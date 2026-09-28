package com.sandro.callrec.record

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.graphics.drawable.Icon
import android.media.AudioManager
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.PowerManager
import android.provider.CallLog
import android.telephony.TelephonyManager
import com.sandro.callrec.device.DeviceProfile
import com.sandro.callrec.log.TechLog
import com.sandro.callrec.probe.AudioSources
import com.sandro.callrec.probe.CallContext
import com.sandro.callrec.probe.CapabilityProbe
import com.sandro.callrec.probe.Learning
import com.sandro.callrec.probe.Permissions
import com.sandro.callrec.probe.Phase
import com.sandro.callrec.probe.PrefsKeyValueStore
import com.sandro.callrec.probe.ProbeResult
import com.sandro.callrec.probe.ProbeStore
import com.sandro.callrec.probe.StrategyRanker
import com.sandro.callrec.storage.CallKind
import com.sandro.callrec.storage.RecordingMeta
import com.sandro.callrec.storage.RecordingStore
import com.sandro.callrec.telephony.CallEventBus
import com.sandro.callrec.telephony.CallLogResolver
import com.sandro.callrec.telephony.CallMonitor
import com.sandro.callrec.ui.MainActivity

/**
 * Serviço em primeiro plano (tipo microfone): detecta chamadas celulares (TelephonyCallback) e por
 * aplicativo (modo de áudio MODE_IN_COMMUNICATION + notificações), e grava com o CascadeRecorder.
 * Precisa ser iniciado pelo usuário com o app visível (restrição do Android 12+/14 para serviços de
 * microfone). Reiniciar após reboot exige abrir o app de novo.
 */
class CallRecorderService : Service(), CascadeRecorder.Listener {

    private enum class Origin { CELLULAR, VOIP, MANUAL }

    private class Active(
        val origin: Origin,
        val kind: CallKind,
        val phase: String,
        val ctx: CallContext,
        val startedAt: Long,
        val files: RecordingStore.NewFiles,
        val recorder: CascadeRecorder,
        val profile: DeviceProfile,
        val audioMode: Int,
        val speaker: Boolean,
        val voipPackage: String?,
        val voipTitle: String?,
    )

    private val handler = Handler(Looper.getMainLooper())
    private lateinit var am: AudioManager
    private lateinit var probeStore: ProbeStore
    private lateinit var recStore: RecordingStore
    private var callMonitor: CallMonitor? = null
    private var active: Active? = null
    private var wakeLock: PowerManager.WakeLock? = null
    private var inForeground = false

    private var cellularState = TelephonyManager.CALL_STATE_IDLE
    private var wasRinging = false
    private var voipHits = 0
    private var voipMisses = 0

    private val voipPoll = object : Runnable {
        override fun run() {
            pollVoip()
            handler.postDelayed(this, POLL_MS)
        }
    }

    override fun onCreate() {
        super.onCreate()
        TechLog.init(this)
        am = getSystemService(Context.AUDIO_SERVICE) as AudioManager
        probeStore = ProbeStore(PrefsKeyValueStore(this))
        recStore = RecordingStore(this)
        createChannel()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START_MONITOR -> startMonitoring()
            ACTION_STOP_MONITOR -> stopMonitoring()
            ACTION_MANUAL_START -> {
                if (!startMonitoring()) return START_NOT_STICKY
                val seconds = intent.getIntExtra(EXTRA_SECONDS, 10).coerceIn(3, 600)
                beginSession(Origin.MANUAL, CallKind.MANUAL, Phase.MANUAL)
                handler.removeCallbacks(manualStop)
                handler.postDelayed(manualStop, seconds * 1000L)
            }
            ACTION_MANUAL_STOP -> endSession()
            else -> stopSelf() // reiniciado pelo sistema sem intenção do usuário
        }
        return START_NOT_STICKY
    }

    override fun onDestroy() {
        teardown()
        super.onDestroy()
    }

    private val manualStop = Runnable { if (active?.origin == Origin.MANUAL) endSession() }

    // ---------------------------------------------------------------- monitoramento

    private fun startMonitoring(): Boolean {
        if (ServiceState.monitoring) return true
        if (!enterForeground("Monitorando chamadas")) {
            stopSelf()
            return false
        }
        try {
            callMonitor = CallMonitor(this) { s -> handler.post { onCellularState(s) } }.also { it.start() }
        } catch (t: Throwable) {
            TechLog.error("svc", "monitor de chamada indisponível (READ_PHONE_STATE?)", t)
        }
        handler.postDelayed(voipPoll, POLL_MS)
        ServiceState.monitoring = true
        ServiceState.status = "monitorando"
        TechLog.event("svc", "monitoramento iniciado", "device" to DeviceProfile.current(this).key)
        return true
    }

    private fun stopMonitoring() {
        teardown()
        stopSelf()
    }

    private fun teardown() {
        handler.removeCallbacks(voipPoll)
        handler.removeCallbacks(manualStop)
        endSession()
        callMonitor?.stop()
        callMonitor = null
        CallEventBus.clear()
        if (inForeground) {
            try { stopForeground(STOP_FOREGROUND_REMOVE) } catch (_: Throwable) {}
            inForeground = false
        }
        ServiceState.monitoring = false
        ServiceState.recording = false
        ServiceState.status = "parado"
        ServiceState.currentSource = ""
    }

    private fun onCellularState(state: Int) {
        cellularState = state
        when (state) {
            TelephonyManager.CALL_STATE_RINGING -> wasRinging = true
            TelephonyManager.CALL_STATE_OFFHOOK -> {
                if (active == null) {
                    beginSession(
                        Origin.CELLULAR,
                        if (wasRinging) CallKind.CELLULAR_IN else CallKind.CELLULAR_OUT,
                        Phase.CELLULAR,
                    )
                }
            }
            TelephonyManager.CALL_STATE_IDLE -> {
                wasRinging = false
                if (active?.origin == Origin.CELLULAR) endSession()
            }
        }
    }

    private fun pollVoip() {
        val inComm = am.mode == AudioManager.MODE_IN_COMMUNICATION
        val a = active
        if (a == null) {
            if (cellularState != TelephonyManager.CALL_STATE_IDLE) return
            if (inComm) {
                if (++voipHits >= 2) {
                    voipHits = 0
                    beginSession(Origin.VOIP, CallKind.VOIP, Phase.VOIP)
                }
            } else {
                voipHits = 0
            }
        } else if (a.origin == Origin.VOIP) {
            if (!inComm) {
                if (++voipMisses >= 3) {
                    voipMisses = 0
                    endSession()
                }
            } else {
                voipMisses = 0
            }
        }
    }

    // ---------------------------------------------------------------- sessão de gravação

    private fun beginSession(origin: Origin, kind: CallKind, phase: String) {
        if (active != null) return
        if (!Permissions.has(this, Manifest.permission.RECORD_AUDIO)) {
            TechLog.event("svc", "sem RECORD_AUDIO; gravação não iniciada")
            return
        }
        val profile = DeviceProfile.current(this)
        val ctx = Learning.contextFor(phase)
        val stats = probeStore.stats(profile.key, ctx)
        val sweep = StrategyRanker.shouldSweepPrivileged(
            Permissions.has(this, "android.permission.CAPTURE_AUDIO_OUTPUT"), stats,
        )
        val ranked = StrategyRanker.rankMicClass(
            Build.VERSION.SDK_INT, CapabilityProbe.unprocessedSupported(this), stats,
            probeStore.winner(profile.key, ctx), probeStore.extraSources(),
        )
        val startedAt = System.currentTimeMillis()
        val files = recStore.newFiles(kind, startedAt)
        val recorder = CascadeRecorder(this, files.audio, sweep, ranked, phase, this)
        val voip = if (origin == Origin.VOIP) CallEventBus.currentVoip() else null
        active = Active(
            origin, kind, phase, ctx, startedAt, files, recorder, profile, am.mode, am.isSpeakerphoneOn,
            voip?.packageName, voip?.title,
        )
        acquireWakeLock()
        ServiceState.recording = true
        ServiceState.status = "gravando (${kind.label})"
        TechLog.event(
            "svc", "sessão iniciada",
            "origin" to origin.name, "kind" to kind.name, "sweepPrivileged" to sweep,
            "candidates" to ranked.joinToString { AudioSources.name(it) },
            "audioMode" to am.mode, "speaker" to am.isSpeakerphoneOn, "voipPkg" to voip?.packageName,
        )
        updateNotification("Gravando (${kind.label})")
        recorder.start()
    }

    private fun endSession() {
        val a = active ?: return
        active = null
        voipMisses = 0
        ServiceState.recording = false
        ServiceState.currentSource = ""
        if (ServiceState.monitoring) {
            ServiceState.status = "monitorando"
            updateNotification("Monitorando chamadas")
        }
        val voipNow = if (a.origin == Origin.VOIP) CallEventBus.currentVoip() else null
        // O join do gravador e a gravação de metadados saem da thread principal.
        Thread({ finalizeSession(a, voipNow?.packageName, voipNow?.title) }, "FinalizeSession").start()
    }

    private fun finalizeSession(a: Active, pkgNow: String?, titleNow: String?) {
        try {
            val report = a.recorder.stopAndAwait()
            releaseWakeLock()
            val endedAt = System.currentTimeMillis()
            if (report == null) {
                TechLog.event("svc", "gravador não devolveu relatório")
                return
            }
            val recordAudio = Permissions.has(this, Manifest.permission.RECORD_AUDIO)
            report.attempts.forEach { Learning.apply(probeStore, a.profile.key, it, recordAudio) }
            if (report.hadSignal && report.finalSourceId >= 0) {
                probeStore.setWinner(a.profile.key, a.ctx, report.finalSourceId)
            }
            if (!report.audioCreated) {
                TechLog.event("svc", "nenhum áudio capturado; sem arquivo", "attempts" to report.attempts.size)
                return
            }
            val notes = buildList {
                if (!report.hadSignal) add("Nenhuma fonte entregou sinal (veja as tentativas: bloqueio ou silêncio por política).")
                if (a.origin == Origin.CELLULAR && report.finalSourceId >= 0 &&
                    !AudioSources.isPrivileged(report.finalSourceId)
                ) {
                    add("Captura pelo microfone: o lado remoto só é captado acusticamente (viva-voz).")
                }
            }.joinToString(" ")
            val meta = RecordingMeta(
                id = a.files.id,
                kind = a.kind,
                startedAt = a.startedAt,
                endedAt = endedAt,
                durationMs = report.durationMs,
                number = null,
                contactName = a.voipTitle ?: titleNow,
                app = a.voipPackage ?: pkgNow,
                finalSourceId = report.finalSourceId,
                sampleRate = report.sampleRate,
                segments = report.segments,
                attempts = report.attempts,
                deviceKey = a.profile.key,
                phase = a.phase,
                audioModeAtStart = a.audioMode,
                speakerphoneAtStart = a.speaker,
                notes = notes,
                audioPath = a.files.audio.absolutePath,
            )
            recStore.save(meta)
            TechLog.event("svc", "gravação salva", "file" to meta.audioPath, "durationMs" to meta.durationMs)
            if (a.origin == Origin.CELLULAR) scheduleCallLogEnrichment(meta, 3)
        } catch (t: Throwable) {
            TechLog.error("svc", "falha ao finalizar sessão", t)
        }
    }

    private fun scheduleCallLogEnrichment(meta: RecordingMeta, attemptsLeft: Int) {
        handler.postDelayed({
            Thread({
                val e = CallLogResolver.latestSince(this, meta.startedAt - 90_000)
                if (e == null) {
                    if (attemptsLeft > 1) handler.post { scheduleCallLogEnrichment(meta, attemptsLeft - 1) }
                    return@Thread
                }
                val kind = when (e.type) {
                    CallLog.Calls.OUTGOING_TYPE -> CallKind.CELLULAR_OUT
                    CallLog.Calls.INCOMING_TYPE, CallLog.Calls.MISSED_TYPE, CallLog.Calls.REJECTED_TYPE -> CallKind.CELLULAR_IN
                    else -> CallKind.CELLULAR_UNKNOWN
                }
                val updated = meta.copy(
                    number = e.number, contactName = e.name, kind = kind,
                    notes = (meta.notes + " Registro de chamadas: ${CallLogResolver.typeLabel(e.type)}, ${e.durationSec}s.").trim(),
                )
                recStore.save(updated)
                TechLog.event("svc", "metadados enriquecidos pelo registro de chamadas", "number" to e.number, "name" to e.name)
            }, "CallLogEnrich").start()
        }, 2500)
    }

    // CascadeRecorder.Listener (chamado da thread do gravador)
    override fun onSourceChanged(sourceId: Int, note: String) {
        val name = AudioSources.name(sourceId)
        ServiceState.currentSource = name
        handler.post { if (active != null) updateNotification("Gravando via $name") }
    }

    override fun onAttempt(result: ProbeResult) = Unit

    // ---------------------------------------------------------------- notificação / wakelock

    private fun createChannel() {
        if (Build.VERSION.SDK_INT < 26) return
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(
            NotificationChannel(CHANNEL, "Monitoramento de chamadas", NotificationManager.IMPORTANCE_LOW),
        )
    }

    private fun buildNotification(text: String): Notification {
        val open = PendingIntent.getActivity(
            this, 0, Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
        val stop = PendingIntent.getService(
            this, 1, Intent(this, CallRecorderService::class.java).setAction(ACTION_STOP_MONITOR),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
        @Suppress("DEPRECATION")
        val b = if (Build.VERSION.SDK_INT >= 26) Notification.Builder(this, CHANNEL) else Notification.Builder(this)
        return b.setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .setContentTitle("CallLab")
            .setContentText(text)
            .setContentIntent(open)
            .setOngoing(true)
            .addAction(
                Notification.Action.Builder(
                    Icon.createWithResource(this, android.R.drawable.ic_media_pause), "Parar", stop,
                ).build(),
            )
            .build()
    }

    private fun enterForeground(text: String): Boolean {
        return try {
            val n = buildNotification(text)
            if (Build.VERSION.SDK_INT >= 29) {
                startForeground(NOTIF_ID, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE)
            } else {
                startForeground(NOTIF_ID, n)
            }
            inForeground = true
            true
        } catch (t: Throwable) {
            TechLog.error("svc", "não foi possível entrar em primeiro plano (app precisa estar visível ao iniciar)", t)
            false
        }
    }

    private fun updateNotification(text: String) {
        if (!inForeground) return
        getSystemService(NotificationManager::class.java).notify(NOTIF_ID, buildNotification(text))
    }

    private fun acquireWakeLock() {
        if (wakeLock?.isHeld == true) return
        val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "CallLab:recording").apply {
            acquire(4 * 60 * 60 * 1000L)
        }
    }

    private fun releaseWakeLock() {
        try { if (wakeLock?.isHeld == true) wakeLock?.release() } catch (_: Throwable) {}
        wakeLock = null
    }

    companion object {
        const val ACTION_START_MONITOR = "com.sandro.callrec.START_MONITOR"
        const val ACTION_STOP_MONITOR = "com.sandro.callrec.STOP_MONITOR"
        const val ACTION_MANUAL_START = "com.sandro.callrec.MANUAL_START"
        const val ACTION_MANUAL_STOP = "com.sandro.callrec.MANUAL_STOP"
        const val EXTRA_SECONDS = "seconds"
        private const val CHANNEL = "calllab_monitor"
        private const val NOTIF_ID = 4201
        private const val POLL_MS = 700L

        /** Inicia (ou reforça) o serviço em primeiro plano. Deve ser chamado com o app visível. */
        fun startForeground(context: Context, action: String, seconds: Int? = null) {
            val i = Intent(context, CallRecorderService::class.java).setAction(action)
            if (seconds != null) i.putExtra(EXTRA_SECONDS, seconds)
            if (Build.VERSION.SDK_INT >= 26) context.startForegroundService(i) else context.startService(i)
        }

        fun stop(context: Context) {
            context.stopService(Intent(context, CallRecorderService::class.java))
        }
    }
}

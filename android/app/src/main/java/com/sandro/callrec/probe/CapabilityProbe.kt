package com.sandro.callrec.probe

import android.content.Context
import android.media.AudioManager
import android.os.SystemClock
import com.sandro.callrec.device.DeviceProfile
import com.sandro.callrec.log.TechLog
import org.json.JSONArray
import org.json.JSONObject

data class ProbeReport(
    val profile: DeviceProfile,
    val permissions: PermissionSnapshot,
    val phase: String,
    val results: List<ProbeResult>,
    val verdicts: List<String>,
    val skippedForSdk: List<Int>,
) {
    fun toJson(): JSONObject = JSONObject().apply {
        put("device", profile.toJson())
        put("permissions", permissions.toJson())
        put("phase", phase)
        put("results", JSONArray(results.map { it.toJson() }))
        put("verdicts", JSONArray(verdicts))
        put("skippedForSdk", JSONArray(skippedForSdk.map { AudioSources.name(it) }))
    }

    fun toText(): String = buildString {
        appendLine("== RELATÓRIO DA SONDA (fase: $phase) ==")
        appendLine(profile.summary())
        appendLine()
        appendLine("Permissões / acessos:")
        permissions.entries.forEach { (k, v) -> appendLine("  ${if (v) "[x]" else "[ ]"} $k") }
        appendLine()
        appendLine("Fontes de áudio testadas:")
        appendLine("  %-20s %-19s %8s %6s %s".format("FONTE", "STATUS", "RMS", "PICO", "DETALHE"))
        results.forEach {
            appendLine(
                "  %-20s %-19s %8.1f %6d %s".format(it.name, it.status.name, it.rms, it.peak, it.detail),
            )
        }
        if (skippedForSdk.isNotEmpty()) {
            appendLine("  (não existem nesta API: ${skippedForSdk.joinToString { AudioSources.name(it) }})")
        }
        appendLine()
        appendLine("Conclusões:")
        if (verdicts.isEmpty()) appendLine("  (sem conclusões)") else verdicts.forEach { appendLine("  - $it") }
    }
}

class CapabilityProbe(private val context: Context, private val store: ProbeStore) {

    private val am = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager

    fun probeSource(sourceId: Int, durationMs: Long, phase: String): ProbeResult {
        val t0 = SystemClock.elapsedRealtime()
        val mode = am.mode
        val opened = CaptureSession.open(sourceId)
        val session = opened.session
            ?: return ProbeResult(
                sourceId, opened.status ?: ProbeStatus.INIT_FAILED, 0, 0, 0.0, 0, null,
                opened.detail, SystemClock.elapsedRealtime() - t0, mode, phase,
            )
        try {
            val acc = LevelAccumulator()
            val buf = ShortArray(session.sampleRate / 10)
            var frames = 0L
            var silenced: Boolean? = null
            var polled = false
            var readError: Int? = null
            while (SystemClock.elapsedRealtime() - t0 < durationMs) {
                val n = session.read(buf)
                if (n < 0) {
                    readError = n
                    break
                }
                acc.add(buf, n)
                frames += n
                if (!polled && SystemClock.elapsedRealtime() - t0 >= durationMs / 2) {
                    silenced = session.isSilencedByPolicy(am)
                    polled = true
                }
            }
            val status = when {
                readError != null -> ProbeStatus.READ_ERROR
                silenced == true -> ProbeStatus.SILENCED_BY_POLICY
                AudioMath.isSilent(acc.peak) -> ProbeStatus.OK_SILENT
                else -> ProbeStatus.OK_SIGNAL
            }
            val detail = when {
                readError != null -> "read() = $readError"
                else -> opened.detail
            }
            return ProbeResult(
                sourceId, status, session.sampleRate, frames, acc.rms, acc.peak, silenced, detail,
                SystemClock.elapsedRealtime() - t0, mode, phase,
            )
        } catch (t: Throwable) {
            return ProbeResult(
                sourceId, ProbeStatus.EXCEPTION, session.sampleRate, 0, 0.0, 0, null,
                "${t.javaClass.simpleName}: ${t.message}", SystemClock.elapsedRealtime() - t0, mode, phase,
            )
        } finally {
            session.close()
        }
    }

    fun runAll(phase: String, durationMs: Long = 1500, onProgress: (String) -> Unit = {}): ProbeReport {
        val profile = DeviceProfile.current(context)
        val perms = Permissions.snapshot(context)
        val extras = store.extraSources()
        val ids = (AudioSources.all + extras).distinct()
        val (testable, skipped) = ids.partition { AudioSources.minSdk(it) <= profile.sdkInt }
        TechLog.event(
            "probe", "início da sonda",
            "phase" to phase, "device" to profile.key, "sources" to testable.joinToString { AudioSources.name(it) },
            "captureAudioOutput" to perms.captureAudioOutput,
        )

        val results = mutableListOf<ProbeResult>()
        for (id in testable) {
            onProgress("Testando ${AudioSources.name(id)}…")
            val r = probeSource(id, durationMs, phase)
            results += r
            Learning.apply(store, profile.key, r, perms.granted("RECORD_AUDIO"))
            TechLog.event(
                "probe", "resultado ${r.name}",
                "status" to r.status.name, "rms" to r.rms, "peak" to r.peak, "rate" to r.sampleRate,
                "silencedByPolicy" to r.silencedByPolicy, "detail" to r.detail, "audioMode" to r.audioMode, "phase" to phase,
            )
            SystemClock.sleep(150) // dá tempo ao HAL para liberar o dispositivo de captura
        }
        val verdicts = LimitVerdict.explain(results, perms.captureAudioOutput)
        verdicts.forEach { TechLog.event("probe", "conclusão", "text" to it) }
        return ProbeReport(profile, perms, phase, results, verdicts, skipped)
    }

    companion object {
        fun unprocessedSupported(context: Context): Boolean {
            val am = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
            return am.getProperty(AudioManager.PROPERTY_SUPPORT_AUDIO_SOURCE_UNPROCESSED) == "true"
        }
    }
}

package com.sandro.callrec.probe

import org.json.JSONObject

enum class ProbeStatus {
    /** Abriu, iniciou e entregou amplitude real. */
    OK_SIGNAL,

    /** Abriu e iniciou, mas só entregou zeros (silêncio digital). */
    OK_SILENT,

    /** AudioRecord.isClientSilenced == true: a política de áudio do Android zerou este cliente. */
    SILENCED_BY_POLICY,

    /** Falha ao construir o AudioRecord (permissão/estado). */
    INIT_FAILED,

    /** Construiu mas startRecording() falhou. */
    START_FAILED,

    /** read() devolveu código de erro. */
    READ_ERROR,

    EXCEPTION,
}

data class ProbeResult(
    val sourceId: Int,
    val status: ProbeStatus,
    val sampleRate: Int,
    val framesRead: Long,
    val rms: Double,
    val peak: Int,
    val silencedByPolicy: Boolean?,
    val detail: String,
    val elapsedMs: Long,
    val audioMode: Int,
    val phase: String,
) {
    val name: String get() = AudioSources.name(sourceId)
    val hasSignal: Boolean get() = status == ProbeStatus.OK_SIGNAL

    fun toJson(): JSONObject = JSONObject().apply {
        put("source", sourceId)
        put("name", name)
        put("status", status.name)
        put("sampleRate", sampleRate)
        put("framesRead", framesRead)
        put("rms", Math.round(rms * 100.0) / 100.0)
        put("peak", peak)
        silencedByPolicy?.let { put("silencedByPolicy", it) }
        put("detail", detail)
        put("elapsedMs", elapsedMs)
        put("audioMode", audioMode)
        put("phase", phase)
    }

    companion object {
        fun fromJson(o: JSONObject) = ProbeResult(
            sourceId = o.optInt("source"),
            status = try { ProbeStatus.valueOf(o.optString("status")) } catch (_: Exception) { ProbeStatus.EXCEPTION },
            sampleRate = o.optInt("sampleRate"),
            framesRead = o.optLong("framesRead"),
            rms = o.optDouble("rms", 0.0),
            peak = o.optInt("peak"),
            silencedByPolicy = if (o.has("silencedByPolicy")) o.optBoolean("silencedByPolicy") else null,
            detail = o.optString("detail"),
            elapsedMs = o.optLong("elapsedMs"),
            audioMode = o.optInt("audioMode"),
            phase = o.optString("phase"),
        )
    }
}

/** Instantâneo de permissões e acessos especiais; entra em todo relatório. */
data class PermissionSnapshot(val entries: LinkedHashMap<String, Boolean>) {
    fun granted(name: String) = entries[name] == true

    val captureAudioOutput: Boolean get() = granted("CAPTURE_AUDIO_OUTPUT")

    fun toJson(): JSONObject = JSONObject().apply { entries.forEach { (k, v) -> put(k, v) } }
}

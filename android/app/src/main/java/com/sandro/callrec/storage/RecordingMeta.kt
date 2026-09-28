package com.sandro.callrec.storage

import com.sandro.callrec.probe.AudioSources
import com.sandro.callrec.probe.ProbeResult
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

enum class CallKind(val label: String) {
    CELLULAR_IN("chamada recebida"),
    CELLULAR_OUT("chamada realizada"),
    CELLULAR_UNKNOWN("chamada"),
    VOIP("chamada por aplicativo"),
    MANUAL("teste manual"),
    OEM_IMPORT("gravação nativa do fabricante"),
}

data class SegmentInfo(
    val sourceId: Int,
    val startMs: Long,
    val endMs: Long,
    val rms: Double,
    val peak: Int,
    val silencedByPolicy: Boolean?,
    val reason: String,
) {
    val sourceName: String get() = AudioSources.name(sourceId)

    fun toJson() = JSONObject().apply {
        put("source", sourceId)
        put("name", sourceName)
        put("startMs", startMs)
        put("endMs", endMs)
        put("rms", Math.round(rms * 100.0) / 100.0)
        put("peak", peak)
        silencedByPolicy?.let { put("silencedByPolicy", it) }
        put("reason", reason)
    }

    companion object {
        fun fromJson(o: JSONObject) = SegmentInfo(
            o.optInt("source"), o.optLong("startMs"), o.optLong("endMs"), o.optDouble("rms", 0.0), o.optInt("peak"),
            if (o.has("silencedByPolicy")) o.optBoolean("silencedByPolicy") else null, o.optString("reason"),
        )
    }
}

data class RecordingMeta(
    val id: String,
    val kind: CallKind,
    val startedAt: Long,
    val endedAt: Long,
    val durationMs: Long,
    val number: String?,
    val contactName: String?,
    val app: String?,
    val finalSourceId: Int,
    val sampleRate: Int,
    val segments: List<SegmentInfo>,
    val attempts: List<ProbeResult>,
    val deviceKey: String,
    val phase: String,
    val audioModeAtStart: Int,
    val speakerphoneAtStart: Boolean,
    val notes: String,
    val audioPath: String,
    val importKey: String? = null,
) {
    fun toJson(): JSONObject = JSONObject().apply {
        put("id", id)
        put("kind", kind.name)
        put("startedAt", startedAt)
        put("endedAt", endedAt)
        put("durationMs", durationMs)
        number?.let { put("number", it) }
        contactName?.let { put("contactName", it) }
        app?.let { put("app", it) }
        put("finalSource", finalSourceId)
        put("finalSourceName", AudioSources.name(finalSourceId))
        put("sampleRate", sampleRate)
        put("segments", JSONArray(segments.map { it.toJson() }))
        put("attempts", JSONArray(attempts.map { it.toJson() }))
        put("deviceKey", deviceKey)
        put("phase", phase)
        put("audioModeAtStart", audioModeAtStart)
        put("speakerphoneAtStart", speakerphoneAtStart)
        put("notes", notes)
        put("audioPath", audioPath)
        importKey?.let { put("importKey", it) }
    }

    companion object {
        private fun JSONObject.str(k: String): String? = if (has(k) && !isNull(k)) getString(k) else null

        fun fromJson(o: JSONObject): RecordingMeta {
            val segs = o.optJSONArray("segments") ?: JSONArray()
            val atts = o.optJSONArray("attempts") ?: JSONArray()
            return RecordingMeta(
                id = o.getString("id"),
                kind = try { CallKind.valueOf(o.optString("kind")) } catch (_: Exception) { CallKind.MANUAL },
                startedAt = o.optLong("startedAt"),
                endedAt = o.optLong("endedAt"),
                durationMs = o.optLong("durationMs"),
                number = o.str("number"),
                contactName = o.str("contactName"),
                app = o.str("app"),
                finalSourceId = o.optInt("finalSource", -1),
                sampleRate = o.optInt("sampleRate"),
                segments = (0 until segs.length()).map { SegmentInfo.fromJson(segs.getJSONObject(it)) },
                attempts = (0 until atts.length()).map { ProbeResult.fromJson(atts.getJSONObject(it)) },
                deviceKey = o.optString("deviceKey"),
                phase = o.optString("phase"),
                audioModeAtStart = o.optInt("audioModeAtStart"),
                speakerphoneAtStart = o.optBoolean("speakerphoneAtStart"),
                notes = o.optString("notes"),
                audioPath = o.optString("audioPath"),
                importKey = o.str("importKey"),
            )
        }
    }
}

object RecordingFormat {
    fun duration(ms: Long): String {
        val s = ms / 1000
        return "%d:%02d".format(s / 60, s % 60)
    }

    fun timestamp(ms: Long): String = SimpleDateFormat("dd/MM/yyyy HH:mm:ss", Locale.getDefault()).format(Date(ms))

    fun who(m: RecordingMeta): String = when {
        m.contactName != null && m.number != null -> "${m.contactName} (${m.number})"
        m.contactName != null -> m.contactName
        m.number != null -> m.number
        m.app != null -> m.app
        else -> "desconhecido"
    }

    fun label(m: RecordingMeta): String =
        "${timestamp(m.startedAt)} · ${m.kind.label} · ${duration(m.durationMs)}\n${who(m)}"

    fun details(m: RecordingMeta): String = buildString {
        appendLine("Tipo: ${m.kind.label}")
        appendLine("Contato/número: ${who(m)}")
        if (m.app != null) appendLine("Aplicativo: ${m.app}")
        appendLine("Início: ${timestamp(m.startedAt)}")
        appendLine("Duração: ${duration(m.durationMs)}")
        appendLine("Fonte final: ${AudioSources.name(m.finalSourceId)} @ ${m.sampleRate} Hz")
        appendLine("Viva-voz no início: ${if (m.speakerphoneAtStart) "sim" else "não"}; modo de áudio: ${m.audioModeAtStart}")
        appendLine("Aparelho: ${m.deviceKey}")
        appendLine()
        appendLine("Segmentos de captura:")
        if (m.segments.isEmpty()) appendLine("  (nenhum)")
        m.segments.forEach {
            appendLine(
                "  ${it.sourceName}: ${it.startMs / 1000.0}s–${it.endMs / 1000.0}s rms=%.1f pico=%d%s — %s".format(
                    it.rms, it.peak,
                    when (it.silencedByPolicy) { true -> " [SILENCIADO PELA POLÍTICA]"; else -> "" },
                    it.reason,
                ),
            )
        }
        appendLine()
        appendLine("Tentativas de abertura / varredura:")
        if (m.attempts.isEmpty()) appendLine("  (nenhuma)")
        m.attempts.forEach { appendLine("  ${it.name}: ${it.status.name} — ${it.detail}") }
        if (m.notes.isNotBlank()) {
            appendLine()
            appendLine("Notas: ${m.notes}")
        }
        appendLine()
        append("Arquivo: ${m.audioPath}")
    }
}

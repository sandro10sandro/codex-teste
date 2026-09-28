package com.sandro.callrec

import com.sandro.callrec.probe.AudioSources
import com.sandro.callrec.probe.Phase
import com.sandro.callrec.probe.ProbeResult
import com.sandro.callrec.probe.ProbeStatus
import com.sandro.callrec.storage.CallKind
import com.sandro.callrec.storage.RecordingFormat
import com.sandro.callrec.storage.RecordingMeta
import com.sandro.callrec.storage.SegmentInfo
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class RecordingMetaTest {

    private fun sample(number: String? = "+5511999990000", name: String? = "Maria", app: String? = null) = RecordingMeta(
        id = "20260928_101500_cellular_in",
        kind = CallKind.CELLULAR_IN,
        startedAt = 1_790_000_000_000,
        endedAt = 1_790_000_065_000,
        durationMs = 65_000,
        number = number, contactName = name, app = app,
        finalSourceId = AudioSources.MIC, sampleRate = 16000,
        segments = listOf(
            SegmentInfo(AudioSources.UNPROCESSED, 0, 3000, 0.0, 0, true, "silêncio"),
            SegmentInfo(AudioSources.MIC, 3000, 65_000, 412.5, 9000, null, "fim da chamada"),
        ),
        attempts = listOf(
            ProbeResult(AudioSources.VOICE_CALL, ProbeStatus.INIT_FAILED, 0, 0, 0.0, 0, null, "SecurityException", 3, 2, Phase.CELLULAR),
        ),
        deviceKey = "motorola|moto g|34", phase = Phase.CELLULAR, audioModeAtStart = 2, speakerphoneAtStart = true,
        notes = "n", audioPath = "/x/y.wav",
    )

    @Test
    fun jsonRoundTripPreservesEverything() {
        val m = sample()
        val back = RecordingMeta.fromJson(JSONObject(m.toJson().toString()))
        assertEquals(m.copy(segments = back.segments, attempts = back.attempts).id, back.id)
        assertEquals(CallKind.CELLULAR_IN, back.kind)
        assertEquals("+5511999990000", back.number)
        assertEquals("Maria", back.contactName)
        assertEquals(2, back.segments.size)
        assertEquals(true, back.segments[0].silencedByPolicy)
        assertNull(back.segments[1].silencedByPolicy)
        assertEquals(412.5, back.segments[1].rms, 0.01)
        assertEquals(ProbeStatus.INIT_FAILED, back.attempts.single().status)
        assertEquals("SecurityException", back.attempts.single().detail)
        assertTrue(back.speakerphoneAtStart)
        assertEquals(AudioSources.MIC, back.finalSourceId)
    }

    @Test
    fun nullFieldsStayNullAfterRoundTrip() {
        val back = RecordingMeta.fromJson(JSONObject(sample(number = null, name = null, app = null).toJson().toString()))
        assertNull(back.number)
        assertNull(back.contactName)
        assertNull(back.app)
        assertNull(back.importKey)
    }

    @Test
    fun unknownKindFallsBackInsteadOfCrashing() {
        val o = sample().toJson().put("kind", "FUTURE_KIND")
        assertEquals(CallKind.MANUAL, RecordingMeta.fromJson(o).kind)
    }

    @Test
    fun whoPrefersNameAndNumberThenAppThenUnknown() {
        assertEquals("Maria (+5511999990000)", RecordingFormat.who(sample()))
        assertEquals("+5511999990000", RecordingFormat.who(sample(name = null)))
        assertEquals("com.whatsapp", RecordingFormat.who(sample(number = null, name = null, app = "com.whatsapp")))
        assertEquals("desconhecido", RecordingFormat.who(sample(number = null, name = null)))
    }

    @Test
    fun durationFormat() {
        assertEquals("1:05", RecordingFormat.duration(65_000))
        assertEquals("0:00", RecordingFormat.duration(0))
    }

    @Test
    fun detailsMentionPolicySilencingAndAttempts() {
        val d = RecordingFormat.details(sample())
        assertTrue(d, "SILENCIADO PELA POLÍTICA" in d)
        assertTrue(d, "VOICE_CALL: INIT_FAILED" in d)
    }
}

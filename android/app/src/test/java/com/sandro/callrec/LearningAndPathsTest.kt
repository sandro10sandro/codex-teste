package com.sandro.callrec

import com.sandro.callrec.probe.AudioSources
import com.sandro.callrec.probe.CallContext
import com.sandro.callrec.probe.Learning
import com.sandro.callrec.probe.MemoryKeyValueStore
import com.sandro.callrec.probe.Phase
import com.sandro.callrec.probe.ProbeResult
import com.sandro.callrec.probe.ProbeStatus
import com.sandro.callrec.probe.ProbeStore
import com.sandro.callrec.storage.OemPaths
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class LearningAndPathsTest {

    private fun r(src: Int, st: ProbeStatus, phase: String) =
        ProbeResult(src, st, 16000, 0, 0.0, 0, null, "", 0, 0, phase)

    @Test
    fun failuresWithoutRecordAudioDoNotPolluteStats() {
        val s = ProbeStore(MemoryKeyValueStore())
        Learning.apply(s, "k", r(AudioSources.MIC, ProbeStatus.INIT_FAILED, Phase.CELLULAR), recordAudioGranted = false)
        assertTrue(s.stats("k", CallContext.CELLULAR).isEmpty())
    }

    @Test
    fun idlePrivilegedRefusalCountsForEveryContext() {
        val s = ProbeStore(MemoryKeyValueStore())
        Learning.apply(s, "k", r(AudioSources.VOICE_CALL, ProbeStatus.INIT_FAILED, Phase.IDLE), true)
        CallContext.values().forEach {
            assertEquals(1, s.stats("k", it)[AudioSources.VOICE_CALL]!!.failures)
        }
    }

    @Test
    fun idlePrivilegedSilenceIsInconclusive() {
        val s = ProbeStore(MemoryKeyValueStore())
        Learning.apply(s, "k", r(AudioSources.VOICE_CALL, ProbeStatus.OK_SILENT, Phase.IDLE), true)
        CallContext.values().forEach { assertTrue(s.stats("k", it).isEmpty()) }
    }

    @Test
    fun inCallSilenceOnPrivilegedIsRecordedInThatContextOnly() {
        val s = ProbeStore(MemoryKeyValueStore())
        Learning.apply(s, "k", r(AudioSources.VOICE_CALL, ProbeStatus.OK_SILENT, Phase.CELLULAR), true)
        assertEquals(1, s.stats("k", CallContext.CELLULAR)[AudioSources.VOICE_CALL]!!.silentRuns)
        assertTrue(s.stats("k", CallContext.VOIP).isEmpty())
    }

    @Test
    fun policySilencingCountsAsSilent() {
        val s = ProbeStore(MemoryKeyValueStore())
        Learning.apply(s, "k", r(AudioSources.MIC, ProbeStatus.SILENCED_BY_POLICY, Phase.VOIP), true)
        assertEquals(1, s.stats("k", CallContext.VOIP)[AudioSources.MIC]!!.silentRuns)
    }

    @Test
    fun oemPathHeuristic() {
        assertTrue(OemPaths.looksLikeCallRecording("Recordings/Call/"))
        assertTrue(OemPaths.looksLikeCallRecording("MIUI/sound_recorder/call_rec/"))
        assertTrue(OemPaths.looksLikeCallRecording("Music/Recordings/Call Recordings/"))
        assertTrue(OemPaths.looksLikeCallRecording("Gravações de chamadas/"))
        assertFalse(OemPaths.looksLikeCallRecording("Music/Albums/"))
        assertFalse(OemPaths.looksLikeCallRecording("Recordings/Voice/"))
        assertFalse(OemPaths.looksLikeCallRecording("Download/"))
    }
}

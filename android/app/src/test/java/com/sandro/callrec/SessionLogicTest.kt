package com.sandro.callrec

import com.sandro.callrec.probe.AudioMath
import com.sandro.callrec.probe.AudioSources
import com.sandro.callrec.probe.CallContext
import com.sandro.callrec.probe.Learning
import com.sandro.callrec.probe.MemoryKeyValueStore
import com.sandro.callrec.probe.Phase
import com.sandro.callrec.probe.ProbeResult
import com.sandro.callrec.probe.ProbeStatus
import com.sandro.callrec.probe.ProbeStore
import com.sandro.callrec.record.CascadeRecorder
import com.sandro.callrec.storage.OemPaths
import com.sandro.callrec.storage.SegmentInfo
import com.sandro.callrec.telephony.CallLogEntry
import com.sandro.callrec.telephony.CallLogMatcher
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class SessionLogicTest {

    private fun r(src: Int, st: ProbeStatus, phase: String = Phase.CELLULAR) =
        ProbeResult(src, st, 16000, 0, 0.0, 0, null, "", 0, 0, phase)

    private fun seg(src: Int, signalMs: Long, silenced: Boolean? = null) =
        SegmentInfo(src, 0, 1000, 0.0, 0, silenced, "", signalMs)

    // ---- critério único de sinal

    @Test
    fun signalCriterionNeedsSustainedSignalAndNoPolicySilencing() {
        assertFalse(AudioMath.qualifiesAsSignal(799, null))
        assertTrue(AudioMath.qualifiesAsSignal(800, null))
        assertTrue(AudioMath.qualifiesAsSignal(5000, false))
        assertFalse(AudioMath.qualifiesAsSignal(5000, true)) // trava e depois é silenciado: não vence
    }

    // ---- Report

    private fun report(vararg segs: SegmentInfo) =
        CascadeRecorder.Report(emptyList(), segs.toList(), -1, 16000, 0, true, false, 0)

    @Test
    fun bestSourceIsTheOneWithMostSustainedSignalAmongQualifyingSegments() {
        val rep = report(
            seg(AudioSources.UNPROCESSED, 3000, silenced = true), // silenciado: não conta
            seg(AudioSources.MIC, 1000),
            seg(AudioSources.CAMCORDER, 9000),
            seg(AudioSources.MIC, 2000), // MIC soma 3000
        )
        assertTrue(rep.hadSignal)
        assertEquals(AudioSources.CAMCORDER, rep.bestSourceId)
    }

    @Test
    fun noQualifyingSegmentMeansNoWinner() {
        val rep = report(seg(AudioSources.MIC, 100), seg(AudioSources.UNPROCESSED, 5000, silenced = true))
        assertFalse(rep.hadSignal)
        assertEquals(-1, rep.bestSourceId)
    }

    // ---- aprendizado por sessão

    @Test
    fun sessionLearningCountsEachSourceOutcomeOnce() {
        val s = ProbeStore(MemoryKeyValueStore())
        val many = List(50) { r(AudioSources.MIC, ProbeStatus.READ_ERROR) } + r(AudioSources.CAMCORDER, ProbeStatus.OK_SIGNAL)
        Learning.applySession(s, "k", many, true)
        assertEquals(1, s.stats("k", CallContext.CELLULAR)[AudioSources.MIC]!!.failures)
        assertEquals(1, s.stats("k", CallContext.CELLULAR)[AudioSources.CAMCORDER]!!.successes)
    }

    @Test
    fun globalFailureDoesNotCountAgainstMicSourcesButPrivilegedRefusalStillDoes() {
        val s = ProbeStore(MemoryKeyValueStore())
        val attempts = listOf(
            r(AudioSources.VOICE_CALL, ProbeStatus.INIT_FAILED),
            r(AudioSources.UNPROCESSED, ProbeStatus.INIT_FAILED),
            r(AudioSources.MIC, ProbeStatus.START_FAILED),
        )
        Learning.applySession(s, "k", attempts, true)
        val st = s.stats("k", CallContext.CELLULAR)
        assertEquals(1, st[AudioSources.VOICE_CALL]!!.failures)
        assertNull(st[AudioSources.UNPROCESSED])
        assertNull(st[AudioSources.MIC])
    }

    @Test
    fun failuresCountNormallyWhenSomeSourceOpened() {
        val s = ProbeStore(MemoryKeyValueStore())
        Learning.applySession(
            s, "k",
            listOf(r(AudioSources.UNPROCESSED, ProbeStatus.INIT_FAILED), r(AudioSources.MIC, ProbeStatus.OK_SIGNAL)),
            true,
        )
        assertEquals(1, s.stats("k", CallContext.CELLULAR)[AudioSources.UNPROCESSED]!!.failures)
    }

    // ---- casamento do registro de chamadas

    private fun e(type: Int, date: Long, number: String = "1") = CallLogEntry(number, null, type, 30, date)

    @Test
    fun callLogPicksAnsweredCallClosestToStart() {
        val start = 1_000_000L
        val pick = CallLogMatcher.pick(
            listOf(
                e(CallLogEntry.INCOMING, start - 80_000, "antiga"),
                e(CallLogEntry.INCOMING, start - 20_000, "certa"),
                e(3, start - 2_000, "perdida"), // MISSED_TYPE: sem gravação, ignorada
                e(5, start - 1_000, "rejeitada"), // REJECTED_TYPE
            ),
            start, start + 60_000,
        )
        assertEquals("certa", pick!!.number)
    }

    @Test
    fun callLogIgnoresEntriesOutsideTheWindowAndReturnsNullWhenNone() {
        val start = 1_000_000L
        assertNull(CallLogMatcher.pick(listOf(e(CallLogEntry.OUTGOING, start - 200_000)), start, start + 10_000))
        assertNull(CallLogMatcher.pick(listOf(e(CallLogEntry.OUTGOING, start + 100_000)), start, start + 10_000))
        assertNull(CallLogMatcher.pick(emptyList(), start, start + 10_000))
    }

    // ---- pasta em API < 29

    @Test
    fun folderOfStripsTheFileNameSoLegacyPathsBehaveLikeRelativePath() {
        assertEquals("/storage/emulated/0/Recordings/Call/", OemPaths.folderOf("/storage/emulated/0/Recordings/Call/x.m4a"))
        assertEquals("x.m4a", OemPaths.folderOf("x.m4a"))
        // O nome do arquivo não pode mais fazer uma gravação de voz comum parecer gravação de chamada.
        assertFalse(OemPaths.looksLikeCallRecording(OemPaths.folderOf("/storage/emulated/0/Recordings/Voice/call_notes.m4a")))
    }
}

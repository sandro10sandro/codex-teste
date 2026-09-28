package com.sandro.callrec

import com.sandro.callrec.probe.AudioSources
import com.sandro.callrec.probe.SourceStat
import com.sandro.callrec.probe.StrategyRanker
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class StrategyRankerTest {

    @Test
    fun defaultPriorPutsUnprocessedFirstAndVoiceCommunicationLast() {
        val r = StrategyRanker.rankMicClass(34, true, emptyMap(), null)
        assertEquals(AudioSources.UNPROCESSED, r.first())
        assertEquals(AudioSources.VOICE_COMMUNICATION, r.last())
    }

    @Test
    fun unprocessedDroppedWhenUnsupported() {
        val r = StrategyRanker.rankMicClass(34, false, emptyMap(), null)
        assertFalse(AudioSources.UNPROCESSED in r)
        assertEquals(AudioSources.VOICE_RECOGNITION, r.first())
    }

    @Test
    fun voicePerformanceOnlyFromApi29() {
        assertFalse(AudioSources.VOICE_PERFORMANCE in StrategyRanker.rankMicClass(28, true, emptyMap(), null))
        assertTrue(AudioSources.VOICE_PERFORMANCE in StrategyRanker.rankMicClass(29, true, emptyMap(), null))
    }

    @Test
    fun learnedWinnerBubblesToTop() {
        val stats = mapOf(AudioSources.CAMCORDER to SourceStat(successes = 2))
        val r = StrategyRanker.rankMicClass(34, true, stats, AudioSources.CAMCORDER)
        assertEquals(AudioSources.CAMCORDER, r.first())
    }

    @Test
    fun repeatedlyFailingSourceIsDropped() {
        val stats = mapOf(AudioSources.UNPROCESSED to SourceStat(failures = 3))
        val r = StrategyRanker.rankMicClass(34, true, stats, null)
        assertFalse(AudioSources.UNPROCESSED in r)
    }

    @Test
    fun neverReturnsEmptyEvenIfEverythingFailed() {
        val stats = AudioSources.micClass.associateWith { SourceStat(failures = 5) }
        assertTrue(StrategyRanker.rankMicClass(34, true, stats, null).isNotEmpty())
    }

    @Test
    fun extrasAreAppendedButPrivilegedExtrasIgnored() {
        val r = StrategyRanker.rankMicClass(34, true, emptyMap(), null, listOf(1999, AudioSources.VOICE_CALL))
        assertTrue(1999 in r)
        assertFalse(AudioSources.VOICE_CALL in r)
    }

    @Test
    fun privilegedSweepRunsUntilTwoNegativesEach() {
        assertTrue(StrategyRanker.shouldSweepPrivileged(false, emptyMap()))
        val negative = AudioSources.privileged.associateWith { SourceStat(failures = 2) }
        assertFalse(StrategyRanker.shouldSweepPrivileged(false, negative))
    }

    @Test
    fun privilegedSweepAlwaysRunsIfPermissionGrantedOrEverSucceeded() {
        val negative = AudioSources.privileged.associateWith { SourceStat(failures = 9) }
        assertTrue(StrategyRanker.shouldSweepPrivileged(true, negative))
        val oneWin = negative + (AudioSources.VOICE_CALL to SourceStat(successes = 1, failures = 9))
        assertTrue(StrategyRanker.shouldSweepPrivileged(false, oneWin))
    }
}

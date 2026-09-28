package com.sandro.callrec

import com.sandro.callrec.device.Oem
import com.sandro.callrec.device.OemDialer
import com.sandro.callrec.probe.MemoryKeyValueStore
import com.sandro.callrec.probe.ProbeStore
import com.sandro.callrec.storage.OemAutoImport
import com.sandro.callrec.storage.OemPaths
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class NativeRecorderTest {

    private data class Rec(val name: String, val dateMs: Long)

    private fun rec(name: String, dateMs: Long) = Rec(name, dateMs)

    private fun pick(list: List<Rec>, start: Long, end: Long) = OemAutoImport.pickForCall(list, { it.dateMs }, start, end)

    @Test
    fun pickForCallKeepsOnlyRecordingsIndexedAroundTheCallAndOrdersByProximity() {
        val start = 10_000_000L
        val end = start + 60_000
        val picked = pick(
            listOf(
                rec("antiga", start - 600_000),        // bem antes: outra chamada
                rec("logo_depois", end + 30_000),      // indexada após o fim: entra
                rec("no_inicio", start + 1_000),       // mais próxima do início
                rec("muito_depois", end + 900_000),    // fora da janela de 5 min
            ),
            start, end,
        )
        assertEquals(listOf("no_inicio", "logo_depois"), picked.map { it.name })
    }

    @Test
    fun pickForCallReturnsEmptyWhenNothingMatches() {
        assertTrue(pick(emptyList(), 0, 10).isEmpty())
        assertTrue(pick(listOf(rec("x", 5_000_000)), 0, 10_000).isEmpty())
    }

    @Test
    fun pathHeuristicAcceptsKnownFoldersAndStillRejectsOrdinaryAudio() {
        assertTrue(OemPaths.looksLikeCallRecording("MIUI/sound_recorder/call_rec/"))
        assertTrue(OemPaths.looksLikeCallRecording("Recordings/Call/"))
        assertTrue(OemPaths.looksLikeCallRecording("Music/Recordings/Call Recordings/"))
        assertTrue(OemPaths.looksLikeCallRecording("PhoneRecord/"))
        assertFalse(OemPaths.looksLikeCallRecording("Music/Albums/"))
        assertFalse(OemPaths.looksLikeCallRecording("Recordings/Voice/"))
        assertFalse(OemPaths.looksLikeCallRecording("Download/"))
    }

    @Test
    fun nativeHitsAreCountedPerDevice() {
        val s = ProbeStore(MemoryKeyValueStore())
        assertEquals(0, s.nativeHits("moto|g"))
        s.recordNativeHit("moto|g")
        s.recordNativeHit("moto|g")
        assertEquals(2, s.nativeHits("moto|g"))
        assertEquals(0, s.nativeHits("samsung|s"))
    }

    @Test
    fun everyOemHasNonEmptyInstructions() {
        Oem.values().forEach { assertTrue(it.name, OemDialer.instructions(it).isNotBlank()) }
    }

    @Test
    fun unknownDialerHasNoDirectSettingsTargets() {
        assertTrue(OemDialer.settingsTargets(null).isEmpty())
        assertTrue(OemDialer.settingsTargets("com.exemplo.desconhecido").isEmpty())
        assertTrue(OemDialer.settingsTargets("com.google.android.dialer").isNotEmpty())
    }
}

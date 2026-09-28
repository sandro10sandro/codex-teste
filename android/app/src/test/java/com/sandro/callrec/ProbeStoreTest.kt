package com.sandro.callrec

import com.sandro.callrec.probe.CallContext
import com.sandro.callrec.probe.MemoryKeyValueStore
import com.sandro.callrec.probe.Outcome
import com.sandro.callrec.probe.ProbeStore
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class ProbeStoreTest {

    @Test
    fun recordsAccumulatePerProfileContextAndSource() {
        val s = ProbeStore(MemoryKeyValueStore())
        s.record("moto|g", CallContext.CELLULAR, 1, Outcome.SUCCESS)
        s.record("moto|g", CallContext.CELLULAR, 1, Outcome.SUCCESS)
        s.record("moto|g", CallContext.CELLULAR, 1, Outcome.SILENT)
        s.record("moto|g", CallContext.CELLULAR, 4, Outcome.FAILURE)
        val st = s.stats("moto|g", CallContext.CELLULAR)
        assertEquals(2, st[1]!!.successes)
        assertEquals(1, st[1]!!.silentRuns)
        assertEquals(1, st[4]!!.failures)
        assertEquals(emptyMap<Int, Any>(), s.stats("moto|g", CallContext.VOIP))
        assertEquals(emptyMap<Int, Any>(), s.stats("samsung|s", CallContext.CELLULAR))
    }

    @Test
    fun winnerAndExtrasRoundTrip() {
        val s = ProbeStore(MemoryKeyValueStore())
        assertNull(s.winner("k", CallContext.VOIP))
        s.setWinner("k", CallContext.VOIP, 6)
        assertEquals(6, s.winner("k", CallContext.VOIP))
        s.setExtraSources(listOf(1999, 1999, 2000))
        assertEquals(listOf(1999, 2000), s.extraSources())
    }

    @Test
    fun corruptedStoredJsonDegradesToEmpty() {
        val kv = MemoryKeyValueStore()
        kv.put("stats|k|CELLULAR", "{not json")
        assertEquals(emptyMap<Int, Any>(), ProbeStore(kv).stats("k", CallContext.CELLULAR))
    }
}

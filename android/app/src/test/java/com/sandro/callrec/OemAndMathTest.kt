package com.sandro.callrec

import com.sandro.callrec.device.Oem
import com.sandro.callrec.probe.AudioMath
import com.sandro.callrec.probe.LevelAccumulator
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class OemAndMathTest {

    @Test
    fun oemDetection() {
        assertEquals(Oem.MOTOROLA, Oem.from("motorola", "motorola"))
        assertEquals(Oem.MOTOROLA, Oem.from("LENOVO", "motorola"))
        assertEquals(Oem.SAMSUNG, Oem.from("samsung", "samsung"))
        assertEquals(Oem.XIAOMI, Oem.from("Xiaomi", "POCO"))
        assertEquals(Oem.XIAOMI, Oem.from("Xiaomi", "Redmi"))
        assertEquals(Oem.OPPO_FAMILY, Oem.from("OnePlus", "OnePlus"))
        assertEquals(Oem.GOOGLE, Oem.from("Google", "google"))
        assertEquals(Oem.OTHER, Oem.from("acme", "acme"))
    }

    @Test
    fun levelAccumulator() {
        val acc = LevelAccumulator()
        acc.add(shortArrayOf(3, -4, 0, 0), 2) // só os dois primeiros
        assertEquals(2L, acc.samples)
        assertEquals(4, acc.peak)
        assertEquals(Math.sqrt((9.0 + 16.0) / 2), acc.rms, 1e-9)
        acc.reset()
        assertEquals(0.0, acc.rms, 0.0)
    }

    @Test
    fun silenceThreshold() {
        assertTrue(AudioMath.isSilent(0))
        assertTrue(AudioMath.isSilent(2))
        assertFalse(AudioMath.isSilent(3))
    }
}

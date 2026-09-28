package com.sandro.callrec

import com.sandro.callrec.record.WavWriter
import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder

class WavWriterTest {

    @Test
    fun headerAndPayloadAreConsistent() {
        val f = File.createTempFile("wav", ".wav")
        try {
            WavWriter(f, 16000).use { w ->
                w.write(shortArrayOf(1, -1, 256, 32767), 4)
                assertEquals(8, w.bytesWritten)
            }
            val b = ByteBuffer.wrap(f.readBytes()).order(ByteOrder.LITTLE_ENDIAN)
            assertEquals(44 + 8, b.capacity())
            assertEquals("RIFF", String(b.array(), 0, 4))
            assertEquals(36 + 8, b.getInt(4))
            assertEquals("WAVE", String(b.array(), 8, 4))
            assertEquals(1, b.getShort(20).toInt())
            assertEquals(1, b.getShort(22).toInt())
            assertEquals(16000, b.getInt(24))
            assertEquals(32000, b.getInt(28))
            assertEquals(8, b.getInt(40))
            assertEquals(1, b.getShort(44).toInt())
            assertEquals(-1, b.getShort(46).toInt())
            assertEquals(256, b.getShort(48).toInt())
            assertEquals(32767, b.getShort(50).toInt())
        } finally {
            f.delete()
        }
    }

    @Test
    fun closeIsIdempotentAndWritesAfterCloseAreIgnored() {
        val f = File.createTempFile("wav", ".wav")
        try {
            val w = WavWriter(f, 8000)
            w.write(shortArrayOf(5), 1)
            w.close()
            w.close()
            w.write(shortArrayOf(6), 1)
            assertEquals(44L + 2, f.length())
        } finally {
            f.delete()
        }
    }

    @Test
    fun headerIsSyncedPeriodicallySoTruncatedFilesStayValid() {
        val f = File.createTempFile("wav", ".wav")
        try {
            val w = WavWriter(f, 16000)
            w.write(ShortArray(80_000), 80_000) // 160 000 bytes -> dispara syncHeader
            val b = ByteBuffer.wrap(f.readBytes()).order(ByteOrder.LITTLE_ENDIAN)
            assertEquals(160_000, b.getInt(40))
            w.close()
        } finally {
            f.delete()
        }
    }
}

package com.sandro.callrec.record

import java.io.Closeable
import java.io.File
import java.io.RandomAccessFile

/** Escritor WAV PCM 16-bit little-endian. O cabeçalho é atualizado periodicamente (recuperável se o processo morrer). */
class WavWriter(
    val file: File,
    val sampleRate: Int,
    private val channels: Int = 1,
) : Closeable {
    private val raf = RandomAccessFile(file, "rw")
    private var dataBytes = 0L
    private var closed = false
    private var lastHeaderSync = 0L

    init {
        raf.setLength(0)
        raf.write(header(0))
    }

    val bytesWritten: Long get() = dataBytes

    @Synchronized
    fun write(buf: ShortArray, len: Int) {
        if (closed || len <= 0) return
        val bytes = ByteArray(len * 2)
        for (i in 0 until len) {
            val v = buf[i].toInt()
            bytes[i * 2] = (v and 0xFF).toByte()
            bytes[i * 2 + 1] = ((v shr 8) and 0xFF).toByte()
        }
        raf.write(bytes)
        dataBytes += bytes.size
        // ~5 s de áudio em 16 kHz mono
        if (dataBytes - lastHeaderSync >= 160_000) syncHeader()
    }

    @Synchronized
    private fun syncHeader() {
        val end = raf.filePointer
        raf.seek(0)
        raf.write(header(dataBytes))
        raf.seek(end)
        lastHeaderSync = dataBytes
    }

    @Synchronized
    override fun close() {
        if (closed) return
        syncHeader()
        raf.close()
        closed = true
    }

    private fun header(dataLen: Long): ByteArray {
        val byteRate = sampleRate * channels * 2
        val out = ByteArray(44)
        fun putStr(off: Int, s: String) = s.forEachIndexed { i, c -> out[off + i] = c.code.toByte() }
        fun putInt(off: Int, v: Long) {
            out[off] = (v and 0xFF).toByte()
            out[off + 1] = ((v shr 8) and 0xFF).toByte()
            out[off + 2] = ((v shr 16) and 0xFF).toByte()
            out[off + 3] = ((v shr 24) and 0xFF).toByte()
        }
        fun putShort(off: Int, v: Int) {
            out[off] = (v and 0xFF).toByte()
            out[off + 1] = ((v shr 8) and 0xFF).toByte()
        }
        putStr(0, "RIFF")
        putInt(4, 36 + dataLen)
        putStr(8, "WAVE")
        putStr(12, "fmt ")
        putInt(16, 16)
        putShort(20, 1)
        putShort(22, channels)
        putInt(24, sampleRate.toLong())
        putInt(28, byteRate.toLong())
        putShort(32, channels * 2)
        putShort(34, 16)
        putStr(36, "data")
        putInt(40, dataLen)
        return out
    }
}

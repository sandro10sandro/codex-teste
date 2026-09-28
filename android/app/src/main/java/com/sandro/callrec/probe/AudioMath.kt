package com.sandro.callrec.probe

import kotlin.math.abs
import kotlin.math.sqrt

/** Acumula nível de amplitude (RMS e pico) sobre amostras PCM 16-bit. */
class LevelAccumulator {
    private var sumSquares = 0.0
    var samples = 0L
        private set
    var peak = 0
        private set

    fun add(buf: ShortArray, len: Int) {
        for (i in 0 until len) {
            val v = buf[i].toInt()
            sumSquares += v.toDouble() * v
            val a = abs(v)
            if (a > peak) peak = a
        }
        samples += len
    }

    val rms: Double get() = if (samples == 0L) 0.0 else sqrt(sumSquares / samples)

    fun reset() {
        sumSquares = 0.0
        samples = 0
        peak = 0
    }
}

object AudioMath {
    /** Pico até este valor é tratado como silêncio digital (fonte bloqueada/zerada). */
    const val SILENCE_PEAK = 2

    /** Tempo mínimo de janelas com sinal para um segmento contar como "deu sinal". */
    const val MIN_SIGNAL_MS = 800L

    fun isSilent(peak: Int) = peak <= SILENCE_PEAK

    /**
     * Critério ÚNICO de sucesso de um segmento (aprendizado, escolha do vencedor e relatório usam este):
     * sinal sustentado e não silenciado pela política de áudio no último sondeio.
     */
    fun qualifiesAsSignal(signalMs: Long, silencedAtEnd: Boolean?): Boolean =
        signalMs >= MIN_SIGNAL_MS && silencedAtEnd != true
}

package com.sandro.callrec.probe

enum class CallContext { CELLULAR, VOIP, MANUAL }

data class SourceStat(val successes: Int = 0, val silentRuns: Int = 0, val failures: Int = 0)

/**
 * Decide, de forma pura e testável, a ordem de tentativa das fontes.
 *
 * Duas famílias:
 *  - privilegiadas (VOICE_CALL/DOWNLINK/UPLINK/REMOTE_SUBMIX): varredura rápida no início da chamada;
 *    se o aparelho as recusar de forma repetida, a varredura é pulada (resultado negativo em cache).
 *  - microfone: cascata ordenada por prior + histórico aprendido neste aparelho.
 *
 * Prior: UNPROCESSED/VOICE_RECOGNITION/MIC/CAMCORDER primeiro, porque sem AEC/NS o alto-falante
 * (viva-voz) vaza para o microfone; VOICE_COMMUNICATION por último, pois aplica cancelamento de
 * eco justamente sobre o áudio remoto.
 */
object StrategyRanker {

    fun shouldSweepPrivileged(capturePermissionGranted: Boolean, stats: Map<Int, SourceStat>): Boolean {
        if (capturePermissionGranted) return true
        if (AudioSources.privileged.any { (stats[it]?.successes ?: 0) > 0 }) return true
        // Só para de tentar depois de >= 2 negativas em cada fonte privilegiada.
        return AudioSources.privileged.any {
            val s = stats[it] ?: SourceStat()
            s.failures + s.silentRuns < 2
        }
    }

    fun rankMicClass(
        sdkInt: Int,
        unprocessedSupported: Boolean,
        stats: Map<Int, SourceStat>,
        winner: Int?,
        extras: List<Int> = emptyList(),
    ): List<Int> {
        val base = AudioSources.micClass
            .filter { AudioSources.minSdk(it) <= sdkInt }
            .filter { it != AudioSources.UNPROCESSED || unprocessedSupported }
        val candidates = base + extras.filter { it !in base && !AudioSources.isPrivileged(it) }.distinct()

        fun prior(id: Int): Double {
            val i = base.indexOf(id)
            return if (i < 0) 0.0 else (base.size - i) * 0.1
        }

        fun score(id: Int): Double {
            val s = stats[id] ?: SourceStat()
            return s.successes * 3.0 - s.silentRuns * 2.0 - s.failures * 1.5 +
                (if (id == winner) 5.0 else 0.0) + prior(id)
        }

        val usable = candidates.filterNot {
            val s = stats[it] ?: SourceStat()
            s.failures >= 3 && s.successes == 0
        }
        val pool = usable.ifEmpty { candidates }
        return pool.sortedByDescending { score(it) }
    }
}

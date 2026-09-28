package com.sandro.callrec.probe

/**
 * Catálogo de valores de MediaRecorder.AudioSource. Usa inteiros literais porque parte deles
 * (REMOTE_SUBMIX, VOICE_CALL...) existe mas exige privilégio de plataforma para uso real.
 */
object AudioSources {
    const val DEFAULT = 0
    const val MIC = 1
    const val VOICE_UPLINK = 2
    const val VOICE_DOWNLINK = 3
    const val VOICE_CALL = 4
    const val CAMCORDER = 5
    const val VOICE_RECOGNITION = 6
    const val VOICE_COMMUNICATION = 7
    const val REMOTE_SUBMIX = 8
    const val UNPROCESSED = 9
    const val VOICE_PERFORMANCE = 10

    /** Fontes que dependem de CAPTURE_AUDIO_OUTPUT (signature|privileged). */
    val privileged = listOf(VOICE_CALL, VOICE_DOWNLINK, VOICE_UPLINK, REMOTE_SUBMIX)

    /** Fontes que passam pelo microfone físico e são acessíveis a app comum. */
    val micClass = listOf(
        UNPROCESSED, VOICE_RECOGNITION, MIC, CAMCORDER, VOICE_PERFORMANCE, DEFAULT, VOICE_COMMUNICATION,
    )

    val all: List<Int> = privileged + micClass

    fun isPrivileged(id: Int) = id in privileged

    /** API mínima em que a constante existe. */
    fun minSdk(id: Int): Int = when (id) {
        UNPROCESSED -> 24
        VOICE_PERFORMANCE -> 29
        else -> 1
    }

    fun name(id: Int): String = when (id) {
        DEFAULT -> "DEFAULT"
        MIC -> "MIC"
        VOICE_UPLINK -> "VOICE_UPLINK"
        VOICE_DOWNLINK -> "VOICE_DOWNLINK"
        VOICE_CALL -> "VOICE_CALL"
        CAMCORDER -> "CAMCORDER"
        VOICE_RECOGNITION -> "VOICE_RECOGNITION"
        VOICE_COMMUNICATION -> "VOICE_COMMUNICATION"
        REMOTE_SUBMIX -> "REMOTE_SUBMIX"
        UNPROCESSED -> "UNPROCESSED"
        VOICE_PERFORMANCE -> "VOICE_PERFORMANCE"
        -1 -> "N/D"
        else -> "CUSTOM_$id"
    }
}

object Phase {
    const val IDLE = "idle"
    const val CELLULAR = "cellular_call"
    const val VOIP = "voip_call"
    const val MANUAL = "manual_test"
}

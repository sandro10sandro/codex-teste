package com.sandro.callrec.probe

import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioRecord
import android.os.Build
import kotlin.math.max

/** Uma captura aberta e iniciada numa fonte específica. Falhas de abertura viram ProbeStatus, não exceções. */
class CaptureSession private constructor(
    val sourceId: Int,
    private val record: AudioRecord,
    val sampleRate: Int,
) {
    /** Lê PCM 16-bit; devolve nº de amostras ou código de erro negativo do AudioRecord. */
    fun read(buf: ShortArray): Int = record.read(buf, 0, buf.size)

    /**
     * true = a política de áudio do Android está entregando zeros a este cliente
     * (captura simultânea com app de chamada/VoIP, restrição de segundo plano etc.).
     * null = não determinável (API < 29 ou sessão não listada).
     */
    fun isSilencedByPolicy(am: AudioManager): Boolean? {
        if (Build.VERSION.SDK_INT < 29) return null
        return try {
            val id = record.audioSessionId
            am.activeRecordingConfigurations.firstOrNull { it.clientAudioSessionId == id }?.isClientSilenced
        } catch (_: Throwable) {
            null
        }
    }

    fun close() {
        try { record.stop() } catch (_: Throwable) {}
        try { record.release() } catch (_: Throwable) {}
    }

    class OpenOutcome(val session: CaptureSession?, val status: ProbeStatus?, val detail: String)

    companion object {
        val DEFAULT_RATES = intArrayOf(16000, 44100, 48000, 8000)

        fun open(sourceId: Int, rates: IntArray = DEFAULT_RATES): OpenOutcome {
            var lastDetail = "nenhuma taxa de amostragem suportada"
            for (rate in rates) {
                val min = AudioRecord.getMinBufferSize(rate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
                if (min <= 0) {
                    lastDetail = "getMinBufferSize($rate)=$min"
                    continue
                }
                val rec = try {
                    AudioRecord(
                        sourceId, rate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT,
                        max(min * 2, rate / 5 * 2),
                    )
                } catch (t: Throwable) {
                    return OpenOutcome(null, ProbeStatus.INIT_FAILED, "${t.javaClass.simpleName}: ${t.message}")
                }
                if (rec.state != AudioRecord.STATE_INITIALIZED) {
                    rec.release()
                    lastDetail = "AudioRecord.state=UNINITIALIZED (taxa $rate)"
                    continue
                }
                try {
                    rec.startRecording()
                } catch (t: Throwable) {
                    rec.release()
                    return OpenOutcome(null, ProbeStatus.START_FAILED, "${t.javaClass.simpleName}: ${t.message}")
                }
                if (rec.recordingState != AudioRecord.RECORDSTATE_RECORDING) {
                    rec.release()
                    return OpenOutcome(null, ProbeStatus.START_FAILED, "recordingState=${rec.recordingState} após startRecording")
                }
                return OpenOutcome(CaptureSession(sourceId, rec, rate), null, "taxa $rate Hz")
            }
            return OpenOutcome(null, ProbeStatus.INIT_FAILED, lastDetail)
        }
    }
}

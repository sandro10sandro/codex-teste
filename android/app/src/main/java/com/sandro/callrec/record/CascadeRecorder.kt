package com.sandro.callrec.record

import android.content.Context
import android.media.AudioManager
import android.os.SystemClock
import com.sandro.callrec.log.TechLog
import com.sandro.callrec.probe.AudioMath
import com.sandro.callrec.probe.AudioSources
import com.sandro.callrec.probe.CaptureSession
import com.sandro.callrec.probe.LevelAccumulator
import com.sandro.callrec.probe.ProbeResult
import com.sandro.callrec.probe.ProbeStatus
import com.sandro.callrec.storage.SegmentInfo
import java.io.File

/**
 * Grava uma chamada num único WAV contínuo, escolhendo a fonte em tempo real:
 *
 *  1. Varredura rápida (~0,4 s cada) das fontes privilegiadas (VOICE_CALL etc.), se a política permitir.
 *     Se alguma entregar sinal, é usada: é o único caminho que capta as duas pontas sem viva-voz.
 *  2. Cascata de microfone na ordem recebida. Uma fonte muda por 3 s é abandonada; a primeira que entrega
 *     sinal por ~0,8 s é travada e mantida até o fim. Se uma volta completa não achar sinal, trava na
 *     melhor observada (ou na primeira) e segue gravando, registrando o diagnóstico (isClientSilenced).
 *
 * Toda tentativa, falha e segmento vai para o relatório e para o log técnico.
 */
class CascadeRecorder(
    private val context: Context,
    private val wavFile: File,
    private val sweepPrivileged: Boolean,
    private val micCandidates: List<Int>,
    private val phase: String,
    private val listener: Listener,
) {
    interface Listener {
        fun onSourceChanged(sourceId: Int, note: String)
        fun onAttempt(result: ProbeResult)
    }

    data class Report(
        val attempts: List<ProbeResult>,
        val segments: List<SegmentInfo>,
        val finalSourceId: Int,
        val sampleRate: Int,
        val durationMs: Long,
        val audioCreated: Boolean,
    ) {
        val hadSignal: Boolean get() = segments.any { !AudioMath.isSilent(it.peak) }
    }

    private enum class End { STOPPED, SILENT_TIMEOUT, READ_ERROR, TIME_UP }

    private class Pump {
        var end = End.STOPPED
        var readError = 0
        var frames = 0L
        var signalMs = 0L
        var silenced: Boolean? = null
        var locked = false
        val acc = LevelAccumulator()
    }

    @Volatile private var stopRequested = false
    private var thread: Thread? = null
    @Volatile private var report: Report? = null

    private val am = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager

    fun start() {
        thread = Thread({ runSafely() }, "CascadeRecorder").also { it.start() }
    }

    fun stopAndAwait(timeoutMs: Long = 5000): Report? {
        stopRequested = true
        thread?.join(timeoutMs)
        return report
    }

    private fun runSafely() {
        val attempts = mutableListOf<ProbeResult>()
        val segments = mutableListOf<SegmentInfo>()
        var writer: WavWriter? = null
        var rate = 0
        var finalSource = -1
        val t0 = SystemClock.elapsedRealtime()
        try {
            fun tryOpen(id: Int, rates: IntArray): CaptureSession? {
                val o = CaptureSession.open(id, rates)
                if (o.session == null) {
                    val r = ProbeResult(
                        id, o.status ?: ProbeStatus.INIT_FAILED, 0, 0, 0.0, 0, null, o.detail, 0, am.mode, phase,
                    )
                    attempts += r
                    listener.onAttempt(r)
                    TechLog.event("rec", "falha ao abrir ${r.name}", "status" to r.status.name, "detail" to o.detail)
                }
                return o.session
            }

            fun classify(st: Pump): ProbeStatus = when {
                st.readError < 0 -> ProbeStatus.READ_ERROR
                st.silenced == true -> ProbeStatus.SILENCED_BY_POLICY
                AudioMath.isSilent(st.acc.peak) -> ProbeStatus.OK_SILENT
                else -> ProbeStatus.OK_SIGNAL
            }

            fun attemptOf(id: Int, st: Pump, sampleRate: Int, detail: String, elapsed: Long): ProbeResult {
                val r = ProbeResult(
                    id, classify(st), sampleRate, st.frames, st.acc.rms, st.acc.peak, st.silenced,
                    detail, elapsed, am.mode, phase,
                )
                attempts += r
                listener.onAttempt(r)
                return r
            }

            var current: CaptureSession? = null
            var currentId = -1

            // 1) Varredura das fontes privilegiadas.
            if (sweepPrivileged) {
                for (id in AudioSources.privileged) {
                    if (stopRequested) break
                    val s = tryOpen(id, CaptureSession.DEFAULT_RATES) ?: continue
                    val began = SystemClock.elapsedRealtime()
                    val st = pump(s, null, SWEEP_READ_MS, 0)
                    val r = attemptOf(id, st, s.sampleRate, "varredura de ${SWEEP_READ_MS} ms", SystemClock.elapsedRealtime() - began)
                    TechLog.event(
                        "rec", "varredura ${r.name}", "status" to r.status.name, "rms" to r.rms, "peak" to r.peak,
                        "silenced" to r.silencedByPolicy,
                    )
                    if (r.status == ProbeStatus.OK_SIGNAL) {
                        current = s
                        currentId = id
                        break
                    }
                    s.close()
                }
            }

            if (current != null) {
                rate = current.sampleRate
                writer = WavWriter(wavFile, rate)
                finalSource = currentId
                listener.onSourceChanged(currentId, "fonte privilegiada com sinal")
                TechLog.event("rec", "usando fonte privilegiada", "source" to AudioSources.name(currentId))
                val segStart = SystemClock.elapsedRealtime() - t0
                val st = pump(current, writer, 0, 0)
                current.close()
                segments += SegmentInfo(
                    currentId, segStart, SystemClock.elapsedRealtime() - t0, st.acc.rms, st.acc.peak, st.silenced,
                    if (st.end == End.STOPPED) "fim da chamada" else "erro de leitura ${st.readError}",
                )
                attemptOf(currentId, st, rate, "segmento contínuo", SystemClock.elapsedRealtime() - t0 - segStart)
            }

            // 2) Cascata de microfone (também é o plano B se a fonte privilegiada morrer).
            if (!stopRequested && micCandidates.isNotEmpty()) {
                val order = micCandidates
                val trials = HashMap<Int, Pump>()
                var idx = 0
                var lockedOn: Int? = null
                var openFailures = 0
                var firstNote = "início da cascata de microfone"
                while (!stopRequested) {
                    val id = lockedOn ?: order[idx % order.size]
                    val s = tryOpen(id, if (rate > 0) intArrayOf(rate) else CaptureSession.DEFAULT_RATES)
                    if (s == null) {
                        openFailures++
                        if (openFailures >= order.size) {
                            TechLog.event("rec", "nenhuma fonte de microfone pôde ser aberta")
                            break
                        }
                        if (lockedOn != null) lockedOn = null
                        idx++
                        continue
                    }
                    openFailures = 0
                    if (writer == null) {
                        rate = s.sampleRate
                        writer = WavWriter(wavFile, rate)
                    }
                    listener.onSourceChanged(id, firstNote)
                    TechLog.event("rec", "gravando com ${AudioSources.name(id)}", "note" to firstNote, "rate" to rate)
                    val segStart = SystemClock.elapsedRealtime() - t0
                    val st = pump(s, writer, 0, if (lockedOn == null) SILENCE_SWITCH_MS else 0)
                    s.close()
                    trials[id] = st
                    val reason = when (st.end) {
                        End.STOPPED -> "fim da chamada"
                        End.SILENT_TIMEOUT -> "silêncio por ${SILENCE_SWITCH_MS / 1000} s; tentando outra fonte"
                        End.READ_ERROR -> "erro de leitura ${st.readError}"
                        End.TIME_UP -> "tempo esgotado"
                    }
                    segments += SegmentInfo(
                        id, segStart, SystemClock.elapsedRealtime() - t0, st.acc.rms, st.acc.peak, st.silenced, reason,
                    )
                    attemptOf(id, st, rate, "segmento: $reason", SystemClock.elapsedRealtime() - t0 - segStart)
                    if (st.acc.peak > AudioMath.SILENCE_PEAK || st.locked) finalSource = id
                    if (st.locked && lockedOn == null) lockedOn = id

                    when (st.end) {
                        End.STOPPED, End.TIME_UP -> break
                        End.SILENT_TIMEOUT -> {
                            idx++
                            firstNote = "silêncio na fonte anterior"
                            if (lockedOn == null && idx >= order.size) {
                                val best = trials.entries
                                    .filter { it.value.signalMs > 0 }
                                    .maxByOrNull { it.value.acc.rms }?.key
                                lockedOn = best ?: order.first()
                                firstNote = if (best != null) "voltando à melhor fonte observada"
                                else "nenhuma fonte deu sinal; mantendo a preferida"
                                TechLog.event(
                                    "rec", "volta completa sem travar", "lockedOn" to AudioSources.name(lockedOn),
                                    "hadSignal" to (best != null),
                                )
                            }
                        }
                        End.READ_ERROR -> {
                            firstNote = "reabrindo após erro de leitura"
                            SystemClock.sleep(200)
                            if (lockedOn == null) idx++
                        }
                    }
                }
                if (finalSource < 0) finalSource = lockedOn ?: order.first()
            }
        } catch (t: Throwable) {
            TechLog.error("rec", "erro fatal no gravador", t)
        } finally {
            var created = false
            try {
                writer?.close()
                created = writer != null && wavFile.exists() && wavFile.length() > 44
                if (!created && wavFile.exists()) wavFile.delete()
            } catch (t: Throwable) {
                TechLog.error("rec", "falha ao fechar WAV", t)
            }
            report = Report(attempts, segments, finalSource, rate, SystemClock.elapsedRealtime() - t0, created)
            TechLog.event(
                "rec", "gravação encerrada", "durationMs" to (SystemClock.elapsedRealtime() - t0),
                "finalSource" to AudioSources.name(finalSource), "segments" to segments.size, "created" to created,
            )
        }
    }

    /** Lê PCM até stop, tempo esgotado, erro ou (se busca ativa) silêncio prolongado. */
    private fun pump(s: CaptureSession, writer: WavWriter?, maxMs: Long, silenceSwitchMs: Long): Pump {
        val st = Pump()
        val buf = ShortArray(s.sampleRate / 10)
        val win = LevelAccumulator()
        val began = SystemClock.elapsedRealtime()
        var lastPoll = began
        while (true) {
            if (stopRequested) { st.end = End.STOPPED; break }
            val now = SystemClock.elapsedRealtime()
            if (maxMs > 0 && now - began >= maxMs) { st.end = End.TIME_UP; break }
            if (!st.locked && st.signalMs >= LOCK_SIGNAL_MS) st.locked = true
            if (!st.locked && silenceSwitchMs > 0 && now - began >= silenceSwitchMs) {
                st.end = End.SILENT_TIMEOUT
                break
            }
            val n = s.read(buf)
            if (n < 0) { st.end = End.READ_ERROR; st.readError = n; break }
            if (n == 0) { SystemClock.sleep(10); continue }
            writer?.write(buf, n)
            st.frames += n
            st.acc.add(buf, n)
            win.reset()
            win.add(buf, n)
            if (!AudioMath.isSilent(win.peak)) st.signalMs += n * 1000L / s.sampleRate
            if (now - lastPoll >= 1000) {
                st.silenced = s.isSilencedByPolicy(am)
                lastPoll = now
            }
        }
        if (st.silenced == null) st.silenced = s.isSilencedByPolicy(am)
        return st
    }

    companion object {
        const val SWEEP_READ_MS = 400L
        const val SILENCE_SWITCH_MS = 3000L
        const val LOCK_SIGNAL_MS = 800L
    }
}

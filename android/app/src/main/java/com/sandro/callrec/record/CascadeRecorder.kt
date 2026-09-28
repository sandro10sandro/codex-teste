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
import java.io.IOException

/**
 * Grava uma chamada num único WAV contínuo, escolhendo a fonte em tempo real:
 *
 *  1. Varredura rápida (~0,4 s cada) das fontes privilegiadas (VOICE_CALL etc.), se a política permitir.
 *     Se alguma entregar sinal, é usada e o áudio da varredura entra no arquivo. É o único caminho que
 *     capta as duas pontas sem viva-voz.
 *  2. Cascata de microfone na ordem recebida. Fonte com silêncio digital por 3 s é abandonada; a que dá
 *     sinal por ~0,8 s é travada. Uma fonte travada que volte a silêncio digital por 8 s é destravada
 *     (no máximo [MAX_UNLOCKS] vezes; depois a trava é definitiva).
 *
 * Silêncio por POLÍTICA (isClientSilenced == true) não é tratado como fonte ruim: pela documentação do
 * Android, durante uma chamada um app comum recebe silêncio em qualquer fonte de microfone (exceto serviço
 * de acessibilidade ou app privilegiado), então trocar de fonte não ajuda. Nesse caso o gravador fica onde
 * está e registra o diagnóstico.
 *
 * Tempos de segmento e duração seguem a linha do tempo do WAV (bytes gravados), não o relógio de parede.
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

        /** A thread do gravador terminou (fim normal, falha de disco ou nenhuma fonte abriu). */
        fun onFinished()
    }

    data class Report(
        val attempts: List<ProbeResult>,
        val segments: List<SegmentInfo>,
        /** Última fonte usada (pode não ter dado sinal). */
        val finalSourceId: Int,
        val sampleRate: Int,
        /** Duração do áudio gravado (linha do tempo do WAV). */
        val durationMs: Long,
        val audioCreated: Boolean,
        val ioFailure: Boolean,
        val droppedRecords: Int,
    ) {
        val hadSignal: Boolean get() = segments.any { it.qualifies }

        /** Fonte com mais sinal sustentado entre os segmentos que qualificam; -1 se nenhum. */
        val bestSourceId: Int
            get() = segments.filter { it.qualifies }
                .groupBy { it.sourceId }
                .maxByOrNull { (_, v) -> v.sumOf { it.signalMs } }?.key ?: -1
    }

    private enum class End { STOPPED, SILENT_TIMEOUT, READ_ERROR, IO_ERROR, TIME_UP }

    private class Cfg(
        val maxMs: Long = 0,
        /** Enquanto não travada: silêncio digital por este tempo encerra o segmento. */
        val searchSilenceMs: Long = 0,
        /** Depois de travada: silêncio digital por este tempo encerra o segmento (destrava). */
        val lockedSilenceMs: Long = 0,
    )

    private class Pump {
        var end = End.STOPPED
        var readError = 0
        var frames = 0L
        var signalMs = 0L
        var digitalSilentRunMs = 0L
        var silenced: Boolean? = null
        var locked = false
        val acc = LevelAccumulator()
    }

    @Volatile private var stopRequested = false
    @Volatile var finished = false
        private set
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
        val attempts = ArrayList<ProbeResult>()
        val segments = ArrayList<SegmentInfo>()
        val failureSeen = HashSet<String>()
        var dropped = 0
        var writer: WavWriter? = null
        var rate = 0
        var lastUsed = -1
        var ioFailed = false
        val t0 = SystemClock.elapsedRealtime()

        fun wavMs(): Long = writer?.let { it.bytesWritten * 1000L / (rate * 2L) } ?: 0L

        fun addAttempt(r: ProbeResult) {
            if (attempts.size >= MAX_RECORDS) { dropped++; return }
            attempts += r
            listener.onAttempt(r)
        }

        fun tryOpen(id: Int, rates: IntArray): CaptureSession? {
            val o = CaptureSession.open(id, rates)
            if (o.session == null) {
                val r = ProbeResult(
                    id, o.status ?: ProbeStatus.INIT_FAILED, 0, 0, 0.0, 0, null, o.detail, 0, am.mode, phase,
                )
                // Falhas repetidas idênticas (mesma fonte/status/detalhe) entram uma vez só no relatório.
                if (failureSeen.add("$id|${r.status}|${o.detail}")) {
                    addAttempt(r)
                    TechLog.event("rec", "falha ao abrir ${r.name}", "status" to r.status.name, "detail" to o.detail)
                }
            }
            return o.session
        }

        fun classify(st: Pump, minSignalMs: Long): ProbeStatus = when {
            st.readError < 0 -> ProbeStatus.READ_ERROR
            st.silenced == true -> ProbeStatus.SILENCED_BY_POLICY
            st.signalMs >= minSignalMs -> ProbeStatus.OK_SIGNAL
            else -> ProbeStatus.OK_SILENT
        }

        fun endSegment(id: Int, st: Pump, startMs: Long, sampleRate: Int, reason: String) {
            val endMs = wavMs()
            if (segments.size >= MAX_RECORDS) { dropped++; return }
            segments += SegmentInfo(
                id, startMs, endMs, st.acc.rms, st.acc.peak, st.silenced, reason, st.signalMs,
            )
            addAttempt(
                ProbeResult(
                    id, classify(st, AudioMath.MIN_SIGNAL_MS), sampleRate, st.frames, st.acc.rms, st.acc.peak,
                    st.silenced, "segmento: $reason", endMs - startMs, am.mode, phase,
                ),
            )
        }

        try {
            // 1) Varredura das fontes privilegiadas; o áudio lido fica em memória para não se perder.
            var kept: CaptureSession? = null
            var keptId = -1
            val pending = ArrayList<ShortArray>()
            if (sweepPrivileged) {
                for (id in AudioSources.privileged) {
                    if (stopRequested) break
                    val s = tryOpen(id, CaptureSession.DEFAULT_RATES) ?: continue
                    var keep = false
                    try {
                        val chunks = ArrayList<ShortArray>()
                        val began = SystemClock.elapsedRealtime()
                        val st = pump(s, { b, n -> chunks += b.copyOf(n) }, Cfg(maxMs = SWEEP_READ_MS))
                        val status = classify(st, SWEEP_MIN_SIGNAL_MS)
                        val r = ProbeResult(
                            id, status, s.sampleRate, st.frames, st.acc.rms, st.acc.peak, st.silenced,
                            "varredura de $SWEEP_READ_MS ms", SystemClock.elapsedRealtime() - began, am.mode, phase,
                        )
                        addAttempt(r)
                        TechLog.event(
                            "rec", "varredura ${r.name}", "status" to r.status.name, "rms" to r.rms,
                            "peak" to r.peak, "silenced" to r.silencedByPolicy,
                        )
                        if (status == ProbeStatus.OK_SIGNAL) {
                            keep = true
                            kept = s
                            keptId = id
                            pending += chunks
                        }
                    } finally {
                        if (!keep) s.close()
                    }
                    if (keep) break
                }
            }

            val privileged = kept
            var privilegedFailed = false
            if (privileged != null) {
                try {
                    rate = privileged.sampleRate
                    val w = WavWriter(wavFile, rate)
                    writer = w
                    pending.forEach { w.write(it, it.size) }
                    lastUsed = keptId
                    listener.onSourceChanged(keptId, "fonte privilegiada com sinal")
                    TechLog.event("rec", "usando fonte privilegiada", "source" to AudioSources.name(keptId))
                    val st = pump(
                        privileged, { b, n -> w.write(b, n) },
                        // Em chamada dois lados podem ficar calados; só desiste após silêncio digital longo. Vale
                        // também se nunca chegou a travar (a varredura aprova com menos sinal que o lock exige).
                        Cfg(searchSilenceMs = PRIV_LOCKED_SILENCE_MS, lockedSilenceMs = PRIV_LOCKED_SILENCE_MS),
                    )
                    val reason = when (st.end) {
                        End.STOPPED -> "fim da chamada"
                        End.SILENT_TIMEOUT -> "silêncio digital por ${PRIV_LOCKED_SILENCE_MS / 1000} s; voltando ao microfone"
                        End.IO_ERROR -> "erro de gravação em disco"
                        else -> "erro de leitura ${st.readError}"
                    }
                    endSegment(keptId, st, 0, rate, reason)
                    if (st.end == End.IO_ERROR) ioFailed = true
                    if (st.end == End.READ_ERROR || st.end == End.SILENT_TIMEOUT) privilegedFailed = true
                } finally {
                    privileged.close()
                }
            }

            // 2) Cascata de microfone (também é o plano B se a fonte privilegiada morrer).
            if (!stopRequested && !ioFailed && micCandidates.isNotEmpty() &&
                (privileged == null || privilegedFailed)
            ) {
                val order = micCandidates
                val trials = HashMap<Int, Pump>()
                var idx = 0
                var lockedOn: Int? = null
                var unlocks = 0
                var consecutiveOpenFailures = 0
                var readErrors = 0
                var lastGoodAt = SystemClock.elapsedRealtime()
                var note = "início da cascata de microfone"
                while (!stopRequested && !ioFailed) {
                    val id = lockedOn ?: order[idx % order.size]
                    val s = tryOpen(id, if (rate > 0) intArrayOf(rate) else CaptureSession.DEFAULT_RATES)
                    if (s == null) {
                        consecutiveOpenFailures++
                        if (lockedOn != null) lockedOn = null
                        idx++
                        if (consecutiveOpenFailures >= order.size) {
                            // Rodada inteira sem abrir. O discador pode ainda estar segurando o microfone
                            // no começo da chamada: espera e tenta de novo até o prazo.
                            if (SystemClock.elapsedRealtime() - lastGoodAt >= OPEN_RETRY_MS) {
                                TechLog.event("rec", "nenhuma fonte de microfone abriu dentro do prazo", "ms" to OPEN_RETRY_MS)
                                break
                            }
                            SystemClock.sleep(OPEN_BACKOFF_MS)
                            consecutiveOpenFailures = 0
                        }
                        continue
                    }
                    consecutiveOpenFailures = 0
                    lastGoodAt = SystemClock.elapsedRealtime()
                    try {
                        if (writer == null) {
                            rate = s.sampleRate
                            writer = WavWriter(wavFile, rate)
                        }
                        val w = writer!!
                        lastUsed = id
                        listener.onSourceChanged(id, note)
                        TechLog.event("rec", "gravando com ${AudioSources.name(id)}", "note" to note, "rate" to rate)
                        val segStart = wavMs()
                        val permanent = unlocks >= MAX_UNLOCKS
                        val st = pump(
                            s, { b, n -> w.write(b, n) },
                            Cfg(
                                searchSilenceMs = if (lockedOn == null) SILENCE_SWITCH_MS else 0,
                                lockedSilenceMs = if (permanent) 0 else LOCKED_SILENCE_MS,
                            ),
                        )
                        trials[id] = st
                        val reason = when (st.end) {
                            End.STOPPED -> "fim da chamada"
                            End.SILENT_TIMEOUT ->
                                if (st.locked) "silêncio digital por ${LOCKED_SILENCE_MS / 1000} s após travar; retomando cascata"
                                else "silêncio digital por ${SILENCE_SWITCH_MS / 1000} s; tentando outra fonte"
                            End.READ_ERROR -> "erro de leitura ${st.readError}"
                            End.IO_ERROR -> "erro de gravação em disco"
                            End.TIME_UP -> "tempo esgotado"
                        }
                        endSegment(id, st, segStart, rate, reason)

                        when (st.end) {
                            End.STOPPED, End.TIME_UP -> break
                            End.IO_ERROR -> {
                                ioFailed = true
                                break
                            }
                            End.SILENT_TIMEOUT -> {
                                readErrors = 0
                                if (st.locked) {
                                    unlocks++
                                    lockedOn = null
                                    idx = order.indexOf(id) + 1
                                    note = "fonte travada ficou muda"
                                } else {
                                    idx++
                                    note = "silêncio na fonte anterior"
                                }
                                if (lockedOn == null && (idx >= order.size || unlocks >= MAX_UNLOCKS)) {
                                    val best = trials.entries
                                        .filter { AudioMath.qualifiesAsSignal(it.value.signalMs, it.value.silenced) }
                                        .maxByOrNull { it.value.signalMs }?.key
                                    if (best != null || idx >= order.size) {
                                        lockedOn = best ?: order.first()
                                        note = if (best != null) "voltando à melhor fonte observada"
                                        else "nenhuma fonte deu sinal; mantendo a preferida"
                                        TechLog.event(
                                            "rec", "volta completa; travando", "lockedOn" to AudioSources.name(lockedOn),
                                            "hadSignal" to (best != null),
                                        )
                                    }
                                }
                            }
                            End.READ_ERROR -> {
                                readErrors++
                                if (readErrors > MAX_READ_ERRORS) {
                                    TechLog.event("rec", "erros de leitura repetidos; encerrando", "count" to readErrors)
                                    break
                                }
                                note = "reabrindo após erro de leitura"
                                SystemClock.sleep(minOf(200L shl readErrors, 2000L))
                                if (lockedOn == null) idx++
                            }
                        }
                    } finally {
                        s.close()
                    }
                }
            }
        } catch (t: Throwable) {
            TechLog.error("rec", "erro fatal no gravador", t)
        } finally {
            var created = false
            var durationMs = 0L
            try {
                durationMs = wavMs()
                writer?.close()
                created = writer != null && wavFile.exists() && wavFile.length() > 44
                if (!created && wavFile.exists()) wavFile.delete()
            } catch (t: Throwable) {
                TechLog.error("rec", "falha ao fechar WAV", t)
            }
            report = Report(attempts, segments, lastUsed, rate, durationMs, created, ioFailed, dropped)
            finished = true
            TechLog.event(
                "rec", "gravação encerrada", "audioMs" to durationMs, "wallMs" to (SystemClock.elapsedRealtime() - t0),
                "lastSource" to AudioSources.name(lastUsed), "segments" to segments.size, "created" to created,
                "ioFailure" to ioFailed, "droppedRecords" to dropped,
            )
            try { listener.onFinished() } catch (_: Throwable) {}
        }
    }

    /** Lê PCM até stop, tempo esgotado, erro, falha de disco ou (conforme [Cfg]) silêncio digital prolongado. */
    private fun pump(s: CaptureSession, sink: ((ShortArray, Int) -> Unit)?, cfg: Cfg): Pump {
        val st = Pump()
        val buf = ShortArray(s.sampleRate / 10)
        val win = LevelAccumulator()
        val began = SystemClock.elapsedRealtime()
        var lastPoll = began
        while (true) {
            if (stopRequested) { st.end = End.STOPPED; break }
            val now = SystemClock.elapsedRealtime()
            if (cfg.maxMs > 0 && now - began >= cfg.maxMs) { st.end = End.TIME_UP; break }
            if (!st.locked && st.signalMs >= AudioMath.MIN_SIGNAL_MS) st.locked = true
            // Silenciado por política: trocar de fonte não resolve; só o silêncio digital "puro" dispara troca.
            if (st.silenced != true) {
                if (!st.locked && cfg.searchSilenceMs > 0 && now - began >= cfg.searchSilenceMs) {
                    st.end = End.SILENT_TIMEOUT
                    break
                }
                if (st.locked && cfg.lockedSilenceMs > 0 && st.digitalSilentRunMs >= cfg.lockedSilenceMs) {
                    st.end = End.SILENT_TIMEOUT
                    break
                }
            }
            val n = s.read(buf)
            if (n < 0) { st.end = End.READ_ERROR; st.readError = n; break }
            if (n == 0) { SystemClock.sleep(10); continue }
            if (sink != null) {
                try {
                    sink(buf, n)
                } catch (e: IOException) {
                    TechLog.error("rec", "falha ao gravar no disco", e)
                    st.end = End.IO_ERROR
                    break
                }
            }
            st.frames += n
            st.acc.add(buf, n)
            win.reset()
            win.add(buf, n)
            val ms = n * 1000L / s.sampleRate
            if (!AudioMath.isSilent(win.peak)) {
                st.signalMs += ms
                st.digitalSilentRunMs = 0
            } else {
                st.digitalSilentRunMs += ms
            }
            if (now - lastPoll >= 1000) {
                st.silenced = s.isSilencedByPolicy(am)
                lastPoll = now
            }
        }
        st.silenced = s.isSilencedByPolicy(am)
        return st
    }

    companion object {
        const val SWEEP_READ_MS = 400L
        const val SWEEP_MIN_SIGNAL_MS = 300L
        const val SILENCE_SWITCH_MS = 3000L
        const val LOCKED_SILENCE_MS = 8000L
        const val PRIV_LOCKED_SILENCE_MS = 30_000L
        const val MAX_UNLOCKS = 3
        const val MAX_READ_ERRORS = 5
        const val OPEN_RETRY_MS = 20_000L
        const val OPEN_BACKOFF_MS = 1000L
        const val MAX_RECORDS = 200
    }
}

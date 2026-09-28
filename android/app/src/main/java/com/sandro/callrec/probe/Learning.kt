package com.sandro.callrec.probe

/** Traduz um resultado de tentativa em aprendizado persistente, com as guardas que evitam contaminar as estatísticas. */
object Learning {

    fun contextFor(phase: String): CallContext = when (phase) {
        Phase.CELLULAR -> CallContext.CELLULAR
        Phase.VOIP -> CallContext.VOIP
        else -> CallContext.MANUAL
    }

    fun outcomeFor(status: ProbeStatus): Outcome = when (status) {
        ProbeStatus.OK_SIGNAL -> Outcome.SUCCESS
        ProbeStatus.OK_SILENT, ProbeStatus.SILENCED_BY_POLICY -> Outcome.SILENT
        else -> Outcome.FAILURE
    }

    /**
     * Aprende com uma sessão inteira: cada par (fonte, desfecho) conta UMA vez, mesmo que a fonte tenha sido
     * reaberta várias vezes, e falha global (nada chegou a abrir) não conta contra as fontes de microfone.
     */
    fun applySession(store: ProbeStore, profileKey: String, attempts: List<ProbeResult>, recordAudioGranted: Boolean) {
        val anyNonFailure = attempts.any { outcomeFor(it.status) != Outcome.FAILURE }
        val seen = HashSet<Pair<Int, Outcome>>()
        for (r in attempts) {
            val o = outcomeFor(r.status)
            if (!seen.add(r.sourceId to o)) continue
            if (o == Outcome.FAILURE && !anyNonFailure && !AudioSources.isPrivileged(r.sourceId)) continue
            apply(store, profileKey, r, recordAudioGranted)
        }
    }

    fun apply(store: ProbeStore, profileKey: String, r: ProbeResult, recordAudioGranted: Boolean) {
        val outcome = outcomeFor(r.status)
        val noCall = r.phase == Phase.IDLE || r.phase == Phase.MANUAL
        val priv = AudioSources.isPrivileged(r.sourceId)
        when {
            // Sem RECORD_AUDIO qualquer falha é do app, não da fonte: não contamina o aprendizado.
            !recordAudioGranted && outcome == Outcome.FAILURE -> Unit
            // Silêncio de fonte privilegiada sem chamada ativa é inconclusivo.
            priv && noCall && outcome == Outcome.SILENT -> Unit
            // Recusa na abertura de fonte privilegiada vale para qualquer contexto de chamada.
            priv && noCall && outcome == Outcome.FAILURE ->
                CallContext.values().forEach { store.record(profileKey, it, r.sourceId, outcome) }
            else -> store.record(profileKey, contextFor(r.phase), r.sourceId, outcome)
        }
    }
}

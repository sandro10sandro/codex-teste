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

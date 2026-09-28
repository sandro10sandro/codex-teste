package com.sandro.callrec.probe

/** Traduz os resultados da sonda em conclusões técnicas legíveis (onde exatamente está o limite). */
object LimitVerdict {

    private val blockedStatuses = setOf(
        ProbeStatus.INIT_FAILED, ProbeStatus.START_FAILED, ProbeStatus.EXCEPTION,
        ProbeStatus.SILENCED_BY_POLICY, ProbeStatus.READ_ERROR,
    )

    fun explain(results: List<ProbeResult>, capturePermissionGranted: Boolean): List<String> {
        val out = mutableListOf<String>()
        val phase = results.firstOrNull()?.phase ?: Phase.IDLE
        val priv = results.filter { AudioSources.isPrivileged(it.sourceId) }
        val mic = results.filter { !AudioSources.isPrivileged(it.sourceId) }

        val privOk = priv.filter { it.hasSignal }
        if (privOk.isNotEmpty()) {
            out += "FONTE PRIVILEGIADA ACESSÍVEL: ${privOk.joinToString { it.name }} entregou sinal. " +
                "Valide numa chamada real: se cobrir as duas pontas, é o melhor método neste aparelho."
        } else if (priv.isNotEmpty()) {
            val blocked = priv.filter { it.status in blockedStatuses }
            val silent = priv.filter { it.status == ProbeStatus.OK_SILENT }
            if (blocked.isNotEmpty()) {
                val permTxt = if (capturePermissionGranted) {
                    "CAPTURE_AUDIO_OUTPUT concedida, mas a plataforma ainda recusou"
                } else {
                    "CAPTURE_AUDIO_OUTPUT = NEGADA (permissão signature|privileged: só app assinado com a " +
                        "chave da plataforma ou instalado em partição privilegiada; sem root/bootloader " +
                        "desbloqueado um app de usuário não pode recebê-la)"
                }
                out += "LIMITE COMPROVADO (áudio direto da rede): $permTxt. Recusadas: " +
                    blocked.joinToString { "${it.name}[${it.status.name}: ${it.detail}]" } + "."
            }
            if (silent.isNotEmpty()) {
                val hint = if (phase == Phase.IDLE) {
                    " Em ociosidade (sem chamada ativa) silêncio é esperado: repita a sonda DURANTE uma chamada."
                } else {
                    " Durante a chamada isso indica áudio zerado pela política de áudio."
                }
                out += "Abriram mas entregaram silêncio digital: ${silent.joinToString { it.name }}.$hint"
            }
        }

        val micOk = mic.filter { it.hasSignal }
        if (micOk.isNotEmpty()) {
            out += "Microfone acessível via: ${micOk.joinToString { it.name }}."
            if (privOk.isEmpty()) {
                out += "Lado remoto: sem fonte privilegiada, só chega ao microfone acusticamente " +
                    "(viva-voz). Fora do viva-voz, espera-se apenas a sua própria voz."
            }
        }

        val policy = results.filter { it.status == ProbeStatus.SILENCED_BY_POLICY && !AudioSources.isPrivileged(it.sourceId) }
        if (policy.isNotEmpty()) {
            out += "Captura simultânea bloqueada pela política de áudio (isClientSilenced=true) em: " +
                policy.joinToString { it.name } +
                ". Outro app (chamada/VoIP) detém o microfone com prioridade."
        }

        if (micOk.isEmpty() && mic.isNotEmpty()) {
            out += "Nenhuma fonte de microfone entregou sinal. Verifique RECORD_AUDIO, privacidade do " +
                "microfone (chave global) e se outro app retém o microfone."
        }
        return out
    }
}

package com.sandro.callrec.device

/**
 * Conhecimento (independente de Android) sobre a gravação de chamada embutida no discador do fabricante.
 *
 * O discador do sistema grava as DUAS PONTAS com privilégio de plataforma (CAPTURE_AUDIO_OUTPUT), algo
 * que um app de usuário não consegue. Um app comum não tem API para FORÇAR essa gravação; o que dá para
 * fazer, de forma legítima, é: (a) levar o usuário à tela onde ele liga o "gravar automaticamente" do
 * próprio discador, e (b) importar o arquivo resultante quando ele cai em pasta acessível.
 *
 * Os componentes de tela abaixo são "melhor esforço" e variam por versão; quem decide é a checagem em
 * tempo real (só abre o que o PackageManager confirmar como acessível). Por isso a lista pode errar sem
 * quebrar nada: o fallback é abrir o próprio discador e as instruções por fabricante.
 */
object OemDialer {

    /** Alvo de tela a tentar abrir (componente explícito). */
    data class SettingsTarget(val pkg: String, val cls: String, val label: String)

    /** Discadores/pacotes que costumam ter gravação de chamada embutida. */
    val KNOWN_DIALERS = setOf(
        "com.google.android.dialer",
        "com.samsung.android.dialer",
        "com.samsung.android.incallui",
        "com.android.dialer",
        "com.android.contacts",
        "com.miui.contacts",
        "com.android.phone",
        "com.motorola.dialer",
        "com.oneplus.dialer",
        "com.oppo.dialer",
        "com.coloros.dialer",
        "com.vivo.dialer",
        "com.transsion.phonemaster",
    )

    /**
     * Componentes de configuração de gravação, por pacote de discador (melhor esforço). Cada um é
     * validado em tempo real; os que não existirem/forem privados são ignorados.
     */
    fun settingsTargets(dialerPkg: String?): List<SettingsTarget> {
        if (dialerPkg == null) return emptyList()
        return when (dialerPkg) {
            "com.google.android.dialer", "com.android.dialer" -> listOf(
                SettingsTarget(dialerPkg, "com.android.dialer.settings.DialerSettingsActivity", "Configurações do telefone"),
                SettingsTarget(dialerPkg, "com.android.dialer.settings.SettingsActivity", "Configurações do telefone"),
            )
            "com.samsung.android.dialer", "com.samsung.android.incallui" -> listOf(
                SettingsTarget("com.samsung.android.dialer", "com.samsung.android.dialer.DialerActivity", "Telefone Samsung"),
            )
            else -> emptyList()
        }
    }

    /** Onde fica o interruptor de gravação automática, por fabricante (texto para o usuário). */
    fun instructions(oem: Oem): String = when (oem) {
        Oem.XIAOMI ->
            "MIUI/HyperOS: Telefone → menu (⋮) → Configurações → Gravar chamadas → ligar \"Gravar chamadas automaticamente\". " +
                "Escolha \"Todas as chamadas\". O arquivo costuma ir para MIUI/sound_recorder/call_rec (acessível)."
        Oem.SAMSUNG ->
            "One UI: Telefone → menu (⋮) → Configurações → Gravar chamadas → \"Gravar chamadas automaticamente\". " +
                "Disponível só em algumas regiões; em muitos aparelhos o arquivo fica em armazenamento privado do discador (não acessível)."
        Oem.MOTOROLA ->
            "Motorola: Telefone → menu → Configurações → Gravar chamada (quando presente na sua região). " +
                "Sem o recurso, o botão de gravar aparece durante a chamada e você toca manualmente."
        Oem.OPPO_FAMILY ->
            "ColorOS/OxygenOS: Telefone → Configurações → Gravar chamadas → gravação automática. Pasta Recordings/Call (costuma ser acessível)."
        Oem.HUAWEI ->
            "EMUI: Telefone → menu → Configurações → Gravar chamadas automaticamente (varia por região)."
        Oem.GOOGLE ->
            "Telefone Google: durante a chamada há um botão \"Gravar\"; a gravação automática por número/desconhecidos fica em " +
                "Configurações → Gravação de chamada. Disponibilidade varia por país."
        Oem.OTHER ->
            "Abra o app Telefone → Configurações e procure \"Gravar chamada\". Se houver \"gravar automaticamente\", ligue."
    }

    /** Só um palpite: este fabricante costuma ter gravação embutida? (a confirmação real é achar arquivos.) */
    fun likelyHasBuiltInRecorder(oem: Oem): Boolean = oem in setOf(
        Oem.XIAOMI, Oem.OPPO_FAMILY, Oem.HUAWEI, Oem.SAMSUNG, Oem.GOOGLE, Oem.MOTOROLA,
    )
}

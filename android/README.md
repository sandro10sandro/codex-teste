# CallLab — gravador de chamadas de laboratório (Android, sem root)

App Kotlin **sem dependências externas** (só framework Android) para pesquisar, aparelho a aparelho,
qual método de captura de áudio funciona para chamadas celulares e por aplicativo (WhatsApp),
**sem root e sem desbloquear o bootloader**. Em vez de supor um método, ele **testa as fontes, registra
o que funcionou/falhou e passa a usar a melhor** naquele fabricante/modelo/versão.

Uso pretendido: aparelhos próprios de laboratório. Veja "Uso responsável" no fim.

## A regra do Android que define tudo

Documentação oficial, *Sharing audio input* ("Android 10 behavior", cenário *Voice call + ordinary app*).
Uma chamada está ativa quando `AudioManager.getMode()` é `MODE_IN_CALL` ou `MODE_IN_COMMUNICATION`
(ou seja, chamada celular **e** chamada VoIP como a do WhatsApp). Nesse estado:

- a chamada sempre recebe o áudio;
- um app **comum recebe silêncio**, exceto se for um **serviço de acessibilidade**;
- só um app privilegiado com `CAPTURE_AUDIO_OUTPUT` captura a própria chamada (as duas pontas).

Consequências para este projeto:

1. **Sem o serviço de acessibilidade ativo, espere gravações vazias durante chamadas**, em qualquer fonte de
   microfone. Trocar de fonte não ajuda: a política vale para o app, não para a fonte. O app detecta isso com
   `isClientSilenced` e grava o diagnóstico (`SILENCED_BY_POLICY`).
2. **Com** a acessibilidade ativa, o app pode capturar do **microfone** durante a chamada. Isso dá a sua voz e,
   em viva-voz, o áudio do interlocutor por vazamento acústico. Não dá o fluxo de áudio da rede. (Que o vazamento
   seja aproveitável em cada aparelho é inferência a confirmar pela sonda/log; a doc só diz que pode capturar.)
3. As duas pontas limpas (`VOICE_CALL`/`UPLINK`/`DOWNLINK`, `REMOTE_SUBMIX`) exigem `CAPTURE_AUDIO_OUTPUT`
   (`signature|privileged`), que um app de usuário não recebe sem root/sistema. O app tenta essas fontes e registra
   a recusa; um aparelho com build de laboratório que a conceda seria detectado.
4. Áudio de VoIP (WhatsApp) é criptografado e roteado pelo app; não há API pública que o entregue. Vale a mesma regra
   de chamada acima.

No Android 13+ um app instalado fora da loja pode exigir liberar **"Configurações restritas"** (Informações do app)
antes de o Android deixar ativar a acessibilidade.

## Como obter o APK

O APK é gerado pelo GitHub Actions (`.github/workflows/android.yml`): abra a execução do workflow
**Android APK** → artefato **calllab-debug-apk** → `app-debug.apk` → `adb install -r app-debug.apk`.

Build local: Android Studio (abrir a pasta `android/`) ou `cd android && ./gradlew assembleDebug`
(requer JDK 17 e Android SDK 34).

## Roteiro de teste num aparelho

1. Instalar o APK. Aceitar o aviso de uso responsável.
2. **Conceder permissões de execução** e **ativar o serviço de acessibilidade "CallLab"** (necessário para gravar
   durante chamada, veja acima). Ativar também **Acesso a notificações** (nome/app do WhatsApp) e, se quiser,
   **Ignorar otimização de bateria**.
3. **Rodar sonda de capacidades** (ociosa): testa cada `AudioSource` e mostra a recusa das fontes privilegiadas.
   Ela **só roda sem chamada** e por isso não prevê o comportamento em chamada; a evidência em chamada está nas
   tentativas e segmentos de cada gravação real.
4. **Iniciar monitoramento** (app visível; exigência do Android para serviço de microfone) e fazer chamadas:
   celular (com e sem viva-voz) e WhatsApp. Se a acessibilidade estiver desligada o app avisa.
5. Abrir **Gravações**: cada uma mostra fonte usada, segmentos, tentativas, se o Android silenciou o app e se a
   acessibilidade estava ativa.
6. **Compartilhar log** para comparar aparelhos.

## Arquitetura

| Peça | Papel |
|---|---|
| `probe/CapabilityProbe`, `CaptureSession` | Abre cada fonte, lê PCM, mede sinal e consulta a política de áudio |
| `probe/StrategyRanker`, `ProbeStore`, `Learning` | Ordena as fontes e **aprende por aparelho** (`fabricante\|modelo\|SDK`; para VoIP, por app) |
| `probe/LimitVerdict` | Converte resultados em conclusão técnica do limite |
| `record/CascadeRecorder` | Varredura das fontes privilegiadas + cascata de microfone, WAV contínuo |
| `record/CallRecorderService` | Serviço em primeiro plano; detecta chamada celular e VoIP e grava |
| `record/KeepAliveAccessibilityService` | Serviço de acessibilidade mínimo (sem eventos, sem ler tela): dá ao app a exceção documentada |
| `telephony/*` | `TelephonyCallback`/`PhoneStateListener`, registro de chamadas, listener de notificações |
| `storage/*` | Biblioteca `AAAA/MM/` + JSON de metadados; importador de gravações nativas do fabricante |
| `log/TechLog` | Log JSONL: qual método funcionou/falhou, com detalhe |

Como uma chamada é gravada:

1. **Varredura das fontes privilegiadas** (~0,4 s cada), enquanto o aparelho ainda não as recusou 2 vezes cada.
   Se alguma der sinal, é usada e o áudio da varredura entra no arquivo.
2. **Cascata de microfone**, ordem por prior + histórico: `UNPROCESSED`, `VOICE_RECOGNITION`, `MIC`, `CAMCORDER`,
   `VOICE_PERFORMANCE`, `DEFAULT`, `VOICE_COMMUNICATION` (por último: aplica cancelamento de eco sobre o áudio
   remoto do alto-falante). Silêncio digital por 3 s troca de fonte; sinal sustentado por ~0,8 s trava; uma fonte
   travada que volte a silêncio digital por 8 s é destravada (até 3 vezes). Silêncio por **política** não dispara
   troca (não adianta). Fontes que só falharam vão para o fim da lista, não somem.
3. **Chamada celular tem prioridade**: se atender uma ligação durante uma sessão VoIP ou teste manual, esta é
   encerrada e a celular é gravada.

Paralelas, fora da gravação: **importação de gravações nativas do fabricante** (heurística de pasta via MediaStore;
gravações em armazenamento privado do discador não são visíveis) e **IDs extras de `AudioSource`** na tela.
Os extras só valem para valores que o `AudioRecord` aceita (0–10 públicos, mais 1997–2000 que são fontes de
sistema e devem ser recusadas): o `AudioRecord` valida a fonte, então isso **não alcança fontes proprietárias de
fabricante**; para isso seria preciso outro caminho (`MediaRecorder`/parâmetros do HAL), não implementado.

## Limitações conhecidas

- Nada foi testado em aparelho físico; o repositório compila e roda testes JVM, e o comportamento de áudio
  depende do hardware e do fabricante.
- **Captura de reprodução (`AudioPlaybackCapture` via MediaProjection)** para VoIP não está implementada; a doc
  limita o alvo a `USAGE_MEDIA/GAME/UNKNOWN`, sem `VOICE_COMMUNICATION`.
- Inicialização após reboot: serviço de microfone não pode ser iniciado em segundo plano no Android 14+; é
  preciso abrir o app.
- O número/contato de chamada celular vem do registro de chamadas, escolhendo a entrada atendida mais próxima do
  início da gravação. É heurística: pode falhar se o registro demorar a gravar (o app tenta 3 vezes) ou se
  duas chamadas ocorrerem em sequência muito próxima.
- Nome do contato de VoIP vem do título da notificação de chamada; depende de "Acesso a notificações".
- Compartilhar log envia o **final do texto** do log (até ~100 mil caracteres, incluindo o arquivo rotacionado),
  não o arquivo; o arquivo completo está em `Android/data/com.sandro.callrec/files/logs/`.
- O áudio lido na varredura de fontes privilegiadas que **não** dão sinal não entra no arquivo (até ~0,4 s cada).

## Uso responsável

Grave apenas em aparelhos seus e conversas para as quais você tem direito de gravar. A regra sobre gravar
a outra parte varia por país e situação. O app mantém uma notificação permanente enquanto monitora e não
tenta se esconder do dono do aparelho.

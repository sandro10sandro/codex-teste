# CallLab — gravador de chamadas de laboratório (Android, sem root)

App Kotlin **sem dependências externas** (só framework Android) para pesquisar, aparelho a aparelho,
qual método de captura de áudio funciona para chamadas celulares e por aplicativo (WhatsApp),
**sem root e sem desbloquear o bootloader**. Em vez de supor um método, ele **testa todos, registra
o que funcionou/falhou e passa a usar o melhor** naquele fabricante/modelo/versão.

Uso pretendido: aparelhos próprios de laboratório. Veja "Uso responsável" no fim.

## Como obter o APK

O APK é gerado pelo GitHub Actions (`.github/workflows/android.yml`): abra a execução do workflow
**Android APK** → artefato **calllab-debug-apk** → `app-debug.apk` → `adb install -r app-debug.apk`.

Build local: Android Studio (abrir a pasta `android/`) ou `cd android && ./gradlew assembleDebug`
(requer JDK 17 e Android SDK 34).

## Roteiro de teste num aparelho

1. Instalar o APK. Aceitar o aviso de uso responsável.
2. **Conceder permissões**; ativar **Acesso a notificações** (para nome/app do WhatsApp); opcionalmente
   **Ignorar otimização de bateria** e o serviço de **Acessibilidade (experimental)**.
3. **Rodar sonda de capacidades**: testa cada `AudioSource`, mede pico/RMS, consulta
   `isClientSilenced` e gera o relatório (`Android/data/com.sandro.callrec/files/reports/`).
4. **Iniciar monitoramento** (app visível; exigência do Android para serviço de microfone) e fazer
   chamadas: celular (com e sem viva-voz) e WhatsApp.
5. Abrir **Gravações**: cada uma mostra fonte usada, segmentos, tentativas e diagnóstico.
6. **Compartilhar log** (`techlog.jsonl`) para comparar aparelhos.

## Arquitetura

| Peça | Papel |
|---|---|
| `probe/CapabilityProbe`, `CaptureSession` | Abre cada fonte, lê PCM, mede sinal e consulta a política de áudio |
| `probe/StrategyRanker`, `ProbeStore`, `Learning` | Ordena as fontes e **aprende por aparelho** (`fabricante\|modelo\|SDK`) |
| `probe/LimitVerdict` | Converte resultados em conclusão técnica do limite |
| `record/CascadeRecorder` | Varredura das fontes privilegiadas + cascata de microfone, WAV contínuo |
| `record/CallRecorderService` | Serviço em primeiro plano; detecta chamada celular e VoIP e grava |
| `telephony/*` | `TelephonyCallback`/`PhoneStateListener`, registro de chamadas, listener de notificações |
| `storage/*` | Biblioteca `AAAA/MM/` + JSON de metadados; importador de gravações nativas do fabricante |
| `log/TechLog` | Log JSONL: qual método funcionou/falhou, com detalhe |

Estratégias, em ordem de tentativa numa chamada:

1. **Fontes privilegiadas** (`VOICE_CALL`, `VOICE_DOWNLINK`, `VOICE_UPLINK`, `REMOTE_SUBMIX`), varredura de
   ~0,4 s. É o único caminho que capta as duas pontas sem viva-voz. Após 2 negativas por fonte no
   aparelho, a varredura deixa de ser repetida (a menos que a permissão apareça).
2. **Microfone**, ordem por prior + histórico: `UNPROCESSED`, `VOICE_RECOGNITION`, `MIC`, `CAMCORDER`,
   `VOICE_PERFORMANCE`, `DEFAULT`, `VOICE_COMMUNICATION`. `VOICE_COMMUNICATION` fica por último porque aplica
   cancelamento de eco justamente sobre o áudio remoto vindo do alto-falante. Fonte muda por 3 s é trocada;
   a que entrega sinal por ~0,8 s é travada.
3. **Gravador nativo do fabricante**: importa da MediaStore gravações que o discador (Samsung, Xiaomi,
   Motorola…) já fez, por heurística de pasta. Gravações em armazenamento privado do discador não são visíveis.
4. **IDs extras de `AudioSource`** informados na tela, para experimentar valores específicos de fabricante.

## Limites (o que o Android impõe)

| Fato | Evidência que o app registra |
|---|---|
| `VOICE_CALL/UPLINK/DOWNLINK` e `REMOTE_SUBMIX` exigem `CAPTURE_AUDIO_OUTPUT` (`signature\|privileged`). App instalado pelo usuário não a recebe. | `checkSelfPermission == DENIED` + falha em `AudioRecord` (`INIT_FAILED`/`START_FAILED`, com a exceção) |
| Sem essas fontes, o áudio do interlocutor só chega ao microfone **acusticamente**, ou seja, com viva-voz | Relatório da sonda e notas de cada gravação |
| Outro app com o microfone (chamada/VoIP) pode fazer o Android **zerar** a captura do nosso app | `SILENCED_BY_POLICY` (`isClientSilenced`) por segmento |
| Áudio de chamada VoIP é criptografado e roteado pelo app; não há API pública de captura | Não há fonte que entregue as duas pontas; só microfone |

Estes fatos foram **derivados da documentação e da arquitetura do Android**. A confirmação empírica
por aparelho é justamente o que a sonda e o log produzem; um aparelho de laboratório com build
`userdebug`/OEM pode se comportar diferente, e o app detecta isso.

## Ainda não coberto / a verificar em aparelho

- **Captura de reprodução (`AudioPlaybackCapture` via MediaProjection)** para VoIP: a documentação limita
  o alvo a `USAGE_MEDIA/GAME/UNKNOWN`, sem `VOICE_COMMUNICATION`; não está implementado como experimento.
- Efeito do serviço de **acessibilidade** sobre a elegibilidade de captura em segundo plano: hipótese
  medida pelo log, sem garantia.
- Inicialização após reboot: serviço de microfone não pode ser iniciado em segundo plano no Android 14+;
  é preciso abrir o app.
- Os primeiros ~0,4 s da varredura privilegiada não entram no arquivo.
- Validação em aparelho real (Motorola/Samsung/Xiaomi): feita por você; este repositório compila e roda
  testes JVM, mas o comportamento de áudio depende do hardware.

## Uso responsável

Grave apenas em aparelhos seus e conversas para as quais você tem direito de gravar. A regra sobre gravar
a outra parte varia por país e situação. O app mantém uma notificação permanente enquanto monitora e não
tenta se esconder do dono do aparelho.

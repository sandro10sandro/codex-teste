package com.sandro.callrec.record

/** Estado observável do serviço, lido pela UI (mesmo processo). */
object ServiceState {
    @Volatile var monitoring = false
    @Volatile var recording = false
    @Volatile var status = "parado"
    @Volatile var currentSource = ""
}

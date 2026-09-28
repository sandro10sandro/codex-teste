package com.sandro.callrec.record

import android.accessibilityservice.AccessibilityService
import android.view.accessibility.AccessibilityEvent
import com.sandro.callrec.log.TechLog

/**
 * Serviço de acessibilidade mínimo e experimental: não declara tipos de evento, não lê janelas
 * (canRetrieveWindowContent=false) e não faz nada além de registrar que está ativo. Existe para
 * que a sonda meça, aparelho a aparelho, se ter um serviço de acessibilidade ativo altera a
 * elegibilidade de captura de áudio em segundo plano. O resultado é registrado no log técnico.
 */
class KeepAliveAccessibilityService : AccessibilityService() {
    override fun onServiceConnected() {
        super.onServiceConnected()
        TechLog.init(this)
        TechLog.event("a11y", "serviço de acessibilidade conectado")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) = Unit

    override fun onInterrupt() = Unit

    override fun onDestroy() {
        TechLog.event("a11y", "serviço de acessibilidade destruído")
        super.onDestroy()
    }
}

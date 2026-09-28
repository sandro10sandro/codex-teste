package com.sandro.callrec.record

import android.accessibilityservice.AccessibilityService
import android.view.accessibility.AccessibilityEvent
import com.sandro.callrec.log.TechLog

/**
 * Serviço de acessibilidade mínimo: não declara tipos de evento, não lê janelas (canRetrieveWindowContent=false)
 * e não faz nada além de registrar que está ativo. Existe porque, pela documentação do Android ("Sharing audio
 * input"), durante uma chamada (MODE_IN_CALL / MODE_IN_COMMUNICATION) um app comum recebe silêncio do microfone e
 * a exceção para app não privilegiado é ser um serviço de acessibilidade. O estado desta habilitação é registrado
 * no log e nos metadados de cada gravação, para comparar aparelho a aparelho.
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

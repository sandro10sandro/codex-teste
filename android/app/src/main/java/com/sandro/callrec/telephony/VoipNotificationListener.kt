package com.sandro.callrec.telephony

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import com.sandro.callrec.log.TechLog

/**
 * Observa notificações de chamada de apps de mensagens (WhatsApp) para obter aplicativo e nome do
 * contato. Requer "Acesso a notificações" concedido pelo usuário nas Configurações. O início/fim
 * efetivo da gravação é confirmado pelo modo de áudio (MODE_IN_COMMUNICATION), não só pela notificação.
 */
class VoipNotificationListener : NotificationListenerService() {

    override fun onListenerConnected() {
        TechLog.init(this)
        TechLog.event("voip", "listener de notificações conectado")
    }

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        if (!isWatchedCall(sbn)) return
        val title = sbn.notification.extras?.getCharSequence(Notification.EXTRA_TITLE)?.toString()
        TechLog.event(
            "voip", "notificação de chamada",
            "pkg" to sbn.packageName, "title" to title, "ongoing" to isOngoing(sbn),
            "category" to sbn.notification.category, "key" to sbn.key,
        )
        CallEventBus.post(VoipNotification(sbn.packageName, title, sbn.key, posted = true))
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification) {
        if (!isWatchedCall(sbn)) return
        TechLog.event("voip", "notificação de chamada removida", "pkg" to sbn.packageName, "key" to sbn.key)
        CallEventBus.post(VoipNotification(sbn.packageName, null, sbn.key, posted = false))
    }

    private fun isOngoing(sbn: StatusBarNotification) =
        sbn.notification.flags and Notification.FLAG_ONGOING_EVENT != 0

    private fun isWatchedCall(sbn: StatusBarNotification): Boolean {
        if (sbn.packageName !in WATCHED_PACKAGES) return false
        val n = sbn.notification
        return n.category == Notification.CATEGORY_CALL || isOngoing(sbn)
    }

    companion object {
        val WATCHED_PACKAGES = setOf("com.whatsapp", "com.whatsapp.w4b")
    }
}

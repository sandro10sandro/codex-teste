package com.sandro.callrec.telephony

import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CopyOnWriteArrayList

/** Evento de chamada por aplicativo (VoIP) observado pelo NotificationListener. */
data class VoipNotification(val packageName: String, val title: String?, val key: String, val posted: Boolean)

/** Barramento em processo entre o NotificationListenerService e o serviço de gravação. */
object CallEventBus {
    fun interface Listener {
        fun onVoipNotification(n: VoipNotification)
    }

    private val listeners = CopyOnWriteArrayList<Listener>()

    /** Chamadas por app ativas segundo notificações: key -> notificação. */
    private val active = ConcurrentHashMap<String, VoipNotification>()

    fun register(l: Listener) { listeners.addIfAbsent(l) }
    fun unregister(l: Listener) { listeners.remove(l) }

    fun post(n: VoipNotification) {
        if (n.posted) active[n.key] = n else active.remove(n.key)
        listeners.forEach { it.onVoipNotification(n) }
    }

    /** Melhor palpite do app/contato da chamada VoIP em curso (última notificação ativa). */
    fun currentVoip(): VoipNotification? = active.values.firstOrNull()

    fun clear() = active.clear()
}

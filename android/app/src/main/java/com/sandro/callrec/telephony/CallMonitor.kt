package com.sandro.callrec.telephony

import android.content.Context
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.telephony.PhoneStateListener
import android.telephony.TelephonyCallback
import android.telephony.TelephonyManager
import com.sandro.callrec.log.TechLog

/** Estado de chamada celular (IDLE / RINGING / OFFHOOK), compatível com API 24 a 34. */
class CallMonitor(private val context: Context, private val onState: (state: Int) -> Unit) {

    private val tm = context.getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager
    private var callback: Any? = null

    @Suppress("DEPRECATION")
    fun start() {
        if (callback != null) return
        if (Build.VERSION.SDK_INT >= 31) {
            val cb = object : TelephonyCallback(), TelephonyCallback.CallStateListener {
                override fun onCallStateChanged(state: Int) = dispatch(state)
            }
            tm.registerTelephonyCallback(context.mainExecutor, cb)
            callback = cb
        } else {
            val l = object : PhoneStateListener() {
                @Deprecated("Deprecated in Java")
                override fun onCallStateChanged(state: Int, phoneNumber: String?) = dispatch(state)
            }
            // PhoneStateListener precisa ser registrado em thread com Looper.
            Handler(Looper.getMainLooper()).post { tm.listen(l, PhoneStateListener.LISTEN_CALL_STATE) }
            callback = l
        }
        TechLog.event("telephony", "monitor de chamada iniciado", "api" to Build.VERSION.SDK_INT)
    }

    @Suppress("DEPRECATION")
    fun stop() {
        val cb = callback ?: return
        callback = null
        try {
            if (Build.VERSION.SDK_INT >= 31 && cb is TelephonyCallback) {
                tm.unregisterTelephonyCallback(cb)
            } else if (cb is PhoneStateListener) {
                tm.listen(cb, PhoneStateListener.LISTEN_NONE)
            }
        } catch (t: Throwable) {
            TechLog.error("telephony", "falha ao parar monitor", t)
        }
    }

    private fun dispatch(state: Int) {
        TechLog.event("telephony", "estado de chamada", "state" to stateName(state))
        onState(state)
    }

    companion object {
        fun stateName(s: Int) = when (s) {
            TelephonyManager.CALL_STATE_IDLE -> "IDLE"
            TelephonyManager.CALL_STATE_RINGING -> "RINGING"
            TelephonyManager.CALL_STATE_OFFHOOK -> "OFFHOOK"
            else -> "UNKNOWN($s)"
        }
    }
}

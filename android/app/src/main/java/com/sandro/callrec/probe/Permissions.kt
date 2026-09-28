package com.sandro.callrec.probe

import android.Manifest
import android.content.ComponentName
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.os.PowerManager
import android.provider.Settings
import com.sandro.callrec.record.KeepAliveAccessibilityService
import com.sandro.callrec.telephony.VoipNotificationListener

object Permissions {

    /** Permissões de runtime que o app pede ao usuário. */
    fun runtimeNeeded(): Array<String> {
        val l = mutableListOf(
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.READ_PHONE_STATE,
            Manifest.permission.READ_CALL_LOG,
            Manifest.permission.READ_CONTACTS,
        )
        if (Build.VERSION.SDK_INT >= 33) {
            l += Manifest.permission.POST_NOTIFICATIONS
            l += Manifest.permission.READ_MEDIA_AUDIO
        } else {
            l += Manifest.permission.READ_EXTERNAL_STORAGE
        }
        return l.toTypedArray()
    }

    fun has(context: Context, perm: String) =
        context.checkSelfPermission(perm) == PackageManager.PERMISSION_GRANTED

    fun missingRuntime(context: Context): List<String> = runtimeNeeded().filter { !has(context, it) }

    fun snapshot(context: Context): PermissionSnapshot {
        val m = LinkedHashMap<String, Boolean>()
        m["RECORD_AUDIO"] = has(context, Manifest.permission.RECORD_AUDIO)
        m["READ_PHONE_STATE"] = has(context, Manifest.permission.READ_PHONE_STATE)
        m["READ_CALL_LOG"] = has(context, Manifest.permission.READ_CALL_LOG)
        m["READ_CONTACTS"] = has(context, Manifest.permission.READ_CONTACTS)
        if (Build.VERSION.SDK_INT >= 33) {
            m["POST_NOTIFICATIONS"] = has(context, Manifest.permission.POST_NOTIFICATIONS)
            m["READ_MEDIA_AUDIO"] = has(context, Manifest.permission.READ_MEDIA_AUDIO)
        }
        // Evidência técnica do limite: signature|privileged; app de usuário nunca a recebe.
        m["CAPTURE_AUDIO_OUTPUT"] = has(context, "android.permission.CAPTURE_AUDIO_OUTPUT")
        m["notification_listener_enabled"] = isNotificationListenerEnabled(context)
        m["accessibility_service_enabled"] = isAccessibilityEnabled(context)
        m["battery_optimization_ignored"] = isIgnoringBatteryOptimizations(context)
        return PermissionSnapshot(m)
    }

    fun isNotificationListenerEnabled(context: Context): Boolean {
        val flat = Settings.Secure.getString(context.contentResolver, "enabled_notification_listeners") ?: return false
        val me = ComponentName(context, VoipNotificationListener::class.java)
        return flat.split(":").any { ComponentName.unflattenFromString(it) == me }
    }

    fun isAccessibilityEnabled(context: Context): Boolean {
        val flat = Settings.Secure.getString(context.contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES) ?: return false
        val me = ComponentName(context, KeepAliveAccessibilityService::class.java)
        return flat.split(":").any { ComponentName.unflattenFromString(it) == me }
    }

    fun isIgnoringBatteryOptimizations(context: Context): Boolean {
        val pm = context.getSystemService(Context.POWER_SERVICE) as PowerManager
        return pm.isIgnoringBatteryOptimizations(context.packageName)
    }
}

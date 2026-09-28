package com.sandro.callrec.device

import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import org.json.JSONArray
import org.json.JSONObject

data class DeviceProfile(
    val manufacturer: String,
    val brand: String,
    val model: String,
    val device: String,
    val product: String,
    val sdkInt: Int,
    val release: String,
    val securityPatch: String,
    val fingerprint: String,
    val display: String,
    val oem: Oem,
    val installedOfInterest: List<String>,
) {
    /** Chave de adaptação: fabricante|modelo|SDK. Estatísticas aprendidas são guardadas por ela. */
    val key: String get() = "${manufacturer.lowercase()}|$model|$sdkInt"

    fun toJson(): JSONObject = JSONObject().apply {
        put("manufacturer", manufacturer)
        put("brand", brand)
        put("model", model)
        put("device", device)
        put("product", product)
        put("sdk", sdkInt)
        put("release", release)
        put("securityPatch", securityPatch)
        put("fingerprint", fingerprint)
        put("display", display)
        put("oem", oem.name)
        put("installedOfInterest", JSONArray(installedOfInterest))
        put("key", key)
    }

    fun summary(): String = buildString {
        appendLine("$manufacturer $model ($device) — Android $release (API $sdkInt)")
        appendLine("Fabricante detectado: ${oem.name}; patch de segurança: $securityPatch")
        appendLine("Build: $display")
        append("Pacotes de interesse presentes: ")
        append(if (installedOfInterest.isEmpty()) "nenhum" else installedOfInterest.joinToString())
    }

    companion object {
        /** Discadores, gravadores e mensageiros relevantes ao diagnóstico por fabricante. */
        val PACKAGES_OF_INTEREST = listOf(
            "com.whatsapp", "com.whatsapp.w4b",
            "com.google.android.dialer", "com.android.dialer",
            "com.samsung.android.dialer", "com.samsung.android.incallui",
            "com.motorola.dialer", "com.motorola.callredirection",
            "com.android.incallui",
            "com.miui.voiceassist", "com.miui.soundrecorder", "com.android.soundrecorder",
            "com.coloros.soundrecorder", "com.oplus.soundrecorder", "com.huawei.soundrecorder",
        )

        fun current(context: Context): DeviceProfile {
            val pm = context.packageManager
            val present = PACKAGES_OF_INTEREST.filter { pkg ->
                try {
                    pm.getPackageInfo(pkg, 0)
                    true
                } catch (_: PackageManager.NameNotFoundException) {
                    false
                } catch (_: Throwable) {
                    false
                }
            }
            return DeviceProfile(
                manufacturer = Build.MANUFACTURER,
                brand = Build.BRAND,
                model = Build.MODEL,
                device = Build.DEVICE,
                product = Build.PRODUCT,
                sdkInt = Build.VERSION.SDK_INT,
                release = Build.VERSION.RELEASE,
                securityPatch = Build.VERSION.SECURITY_PATCH,
                fingerprint = Build.FINGERPRINT,
                display = Build.DISPLAY,
                oem = Oem.from(Build.MANUFACTURER, Build.BRAND),
                installedOfInterest = present,
            )
        }
    }
}

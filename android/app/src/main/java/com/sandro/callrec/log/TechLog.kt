package com.sandro.callrec.log

import android.content.Context
import android.util.Log
import org.json.JSONObject
import java.io.File
import java.text.SimpleDateFormat
import java.util.ArrayDeque
import java.util.Date
import java.util.Locale

/**
 * Log técnico em JSON Lines. Cada linha é um evento com timestamp, tag, mensagem e campos livres,
 * para identificar exatamente qual método de captura funcionou ou falhou em cada aparelho.
 */
object TechLog {
    private const val MAX_BYTES = 1_500_000L
    private const val RING = 400

    private val lock = Any()
    private val ring = ArrayDeque<String>()
    private var file: File? = null
    private val tsFmt = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSZ", Locale.US)

    fun init(context: Context) {
        synchronized(lock) {
            if (file != null) return
            val dir = File(context.getExternalFilesDir(null) ?: context.filesDir, "logs")
            dir.mkdirs()
            file = File(dir, "techlog.jsonl")
        }
    }

    val path: String? get() = file?.absolutePath

    fun event(tag: String, msg: String, vararg fields: Pair<String, Any?>) {
        val o = JSONObject()
        o.put("ts", synchronized(lock) { tsFmt.format(Date()) })
        o.put("tag", tag)
        o.put("msg", msg)
        for ((k, v) in fields) o.put(k, v ?: JSONObject.NULL)
        val line = o.toString()
        Log.i("CallLab/$tag", line)
        synchronized(lock) {
            ring.addLast(line)
            while (ring.size > RING) ring.removeFirst()
            val f = file ?: return
            try {
                if (f.exists() && f.length() > MAX_BYTES) {
                    val old = File(f.parentFile, "techlog.1.jsonl")
                    old.delete()
                    f.renameTo(old)
                }
                f.appendText(line + "\n")
            } catch (t: Throwable) {
                Log.w("CallLab/TechLog", "falha ao gravar log: ${t.message}")
            }
        }
    }

    fun error(tag: String, msg: String, t: Throwable, vararg fields: Pair<String, Any?>) {
        event(tag, msg, *fields, "error" to "${t.javaClass.name}: ${t.message}")
    }

    /** Últimas linhas em memória (para a tela de log). */
    fun tail(n: Int = 120): List<String> = synchronized(lock) { ring.toList().takeLast(n) }

    /** Conteúdo completo do arquivo, limitado ao final para caber em compartilhamento. */
    fun readTail(maxChars: Int = 180_000): String {
        val f = file ?: return ""
        return try {
            val s = f.readText()
            if (s.length > maxChars) s.substring(s.length - maxChars) else s
        } catch (_: Throwable) {
            ""
        }
    }
}

package com.sandro.callrec.storage

import android.content.Context
import android.net.Uri
import android.os.Build
import android.provider.MediaStore
import com.sandro.callrec.device.DeviceProfile
import com.sandro.callrec.log.TechLog
import java.io.File

data class NativeRecording(
    val uri: Uri,
    val name: String,
    val path: String,
    val dateMs: Long,
    val durationMs: Long,
    val size: Long,
) {
    val key: String get() = "$path$name|$size|$dateMs"
}

object OemPaths {
    /** Em API < 29 a coluna DATA é o caminho completo; extrai só a pasta para ter o mesmo sentido de RELATIVE_PATH. */
    fun folderOf(dataPath: String): String {
        val i = dataPath.lastIndexOf('/')
        return if (i >= 0) dataPath.substring(0, i + 1) else dataPath
    }

    /**
     * Heurística por caminho: discadores de fabricantes gravam em pastas como "Recordings/Call",
     * "MIUI/sound_recorder/call_rec", "Call recordings", "Gravações de chamadas". Não depende de
     * uma lista fixa por modelo, então também pega pastas que eu não conheço.
     */
    fun looksLikeCallRecording(path: String): Boolean {
        val p = path.lowercase()
        val call = "call" in p || "chamada" in p || "ligac" in p
        val rec = "rec" in p || "grava" in p
        return call && rec
    }
}

/**
 * Estratégia "gravador nativo do fabricante": muitos aparelhos (Samsung, Xiaomi, Motorola etc.) já
 * têm gravação de chamada no discador, com acesso privilegiado às duas pontas. Quando o arquivo cai
 * numa pasta acessível via MediaStore, este importador o traz para a biblioteca do app.
 * Gravações mantidas em armazenamento privado do discador não são visíveis a apps de terceiros.
 */
object OemRecordingImporter {

    fun scan(context: Context): List<NativeRecording> {
        val out = mutableListOf<NativeRecording>()
        val pathCol = if (Build.VERSION.SDK_INT >= 29) MediaStore.Audio.Media.RELATIVE_PATH else @Suppress("DEPRECATION") MediaStore.Audio.Media.DATA
        try {
            context.contentResolver.query(
                MediaStore.Audio.Media.EXTERNAL_CONTENT_URI,
                arrayOf(
                    MediaStore.Audio.Media._ID, MediaStore.Audio.Media.DISPLAY_NAME, pathCol,
                    MediaStore.Audio.Media.DATE_ADDED, MediaStore.Audio.Media.DURATION, MediaStore.Audio.Media.SIZE,
                ),
                null, null, "${MediaStore.Audio.Media.DATE_ADDED} DESC",
            )?.use { c ->
                while (c.moveToNext()) {
                    val raw = c.getString(2) ?: continue
                    val path = if (Build.VERSION.SDK_INT >= 29) raw else OemPaths.folderOf(raw)
                    if (!OemPaths.looksLikeCallRecording(path)) continue
                    val id = c.getLong(0)
                    out += NativeRecording(
                        uri = android.content.ContentUris.withAppendedId(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, id),
                        name = c.getString(1) ?: "audio_$id",
                        path = path,
                        dateMs = c.getLong(3) * 1000,
                        durationMs = c.getLong(4),
                        size = c.getLong(5),
                    )
                }
            }
        } catch (t: Throwable) {
            TechLog.error("oem", "falha ao varrer MediaStore", t)
        }
        TechLog.event("oem", "varredura de gravações nativas", "found" to out.size, "paths" to out.map { it.path }.distinct().take(8).joinToString())
        return out
    }

    /**
     * Copia para a biblioteca do app. Devolve null se já importada ou em caso de erro. [knownKeys] é o
     * conjunto de chaves já importadas (mutável: recebe a nova chave), calculado uma vez por lote.
     */
    fun importOne(context: Context, store: RecordingStore, item: NativeRecording, knownKeys: MutableSet<String>): RecordingMeta? {
        if (item.key in knownKeys) return null
        var partial: File? = null
        return try {
            val ext = item.name.substringAfterLast('.', "m4a").lowercase().take(5)
            val files = store.newFiles(CallKind.OEM_IMPORT, item.dateMs, ext)
            partial = files.audio
            context.contentResolver.openInputStream(item.uri)?.use { input ->
                files.audio.outputStream().use { input.copyTo(it) }
            } ?: run {
                files.audio.delete()
                return null
            }
            val profile = DeviceProfile.current(context)
            val meta = RecordingMeta(
                id = files.id, kind = CallKind.OEM_IMPORT, startedAt = item.dateMs,
                endedAt = item.dateMs + item.durationMs, durationMs = item.durationMs,
                number = null, contactName = null, app = null, finalSourceId = -1, sampleRate = 0, // desconhecidos
                segments = emptyList(), attempts = emptyList(), deviceKey = profile.key, phase = "oem_import",
                audioModeAtStart = 0, speakerphoneAtStart = false,
                notes = "Importada do gravador nativo do fabricante. Origem: ${item.path}${item.name}. " +
                    "O horário é a data de inclusão no MediaStore (pode diferir do início da chamada); " +
                    "número e contato não estão disponíveis nesse arquivo.",
                audioPath = files.audio.absolutePath, importKey = item.key,
            )
            store.save(meta)
            knownKeys += item.key
            partial = null
            TechLog.event("oem", "gravação nativa importada", "name" to item.name, "path" to item.path)
            meta
        } catch (t: Throwable) {
            TechLog.error("oem", "falha ao importar ${item.name}", t)
            null
        } finally {
            // Cópia interrompida não deixa arquivo parcial órfão na biblioteca.
            partial?.delete()
        }
    }
}

package com.sandro.callrec.storage

import android.content.Context
import android.os.Environment
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Armazenamento organizado: <externo do app>/Music/CallLab/AAAA/MM/AAAAMMDD_HHMMSS_<tipo>.<ext> + .json de metadados.
 * O diretório específico do app dispensa permissão de armazenamento e é acessível por `adb pull`.
 */
class RecordingStore(val root: File) {

    constructor(context: Context) : this(
        File(context.getExternalFilesDir(Environment.DIRECTORY_MUSIC) ?: context.filesDir, "CallLab"),
    )

    data class NewFiles(val audio: File, val meta: File, val id: String)

    fun newFiles(kind: CallKind, startedAt: Long, ext: String = "wav"): NewFiles {
        val year = SimpleDateFormat("yyyy", Locale.US).format(Date(startedAt))
        val month = SimpleDateFormat("MM", Locale.US).format(Date(startedAt))
        val dir = File(root, "$year/$month").also { it.mkdirs() }
        val stamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date(startedAt))
        var id = "${stamp}_${kind.name.lowercase()}"
        var n = 1
        while (File(dir, "$id.json").exists() || File(dir, "$id.$ext").exists()) id = "${stamp}_${kind.name.lowercase()}_${n++}"
        return NewFiles(File(dir, "$id.$ext"), File(dir, "$id.json"), id)
    }

    fun save(meta: RecordingMeta) {
        val audio = File(meta.audioPath)
        File(audio.parentFile, "${audio.nameWithoutExtension}.json").writeText(meta.toJson().toString(2))
    }

    fun list(): List<RecordingMeta> {
        if (!root.exists()) return emptyList()
        return root.walkTopDown()
            .filter { it.isFile && it.extension == "json" }
            .mapNotNull { f ->
                try {
                    RecordingMeta.fromJson(org.json.JSONObject(f.readText()))
                } catch (_: Throwable) {
                    null
                }
            }
            .sortedByDescending { it.startedAt }
            .toList()
    }

    fun delete(meta: RecordingMeta) {
        val audio = File(meta.audioPath)
        audio.delete()
        File(audio.parentFile, "${audio.nameWithoutExtension}.json").delete()
    }

    fun hasImportKey(key: String): Boolean = list().any { it.importKey == key }
}

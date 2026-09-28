package com.sandro.callrec.ui

import android.app.Activity
import android.app.AlertDialog
import android.graphics.Typeface
import android.media.MediaPlayer
import android.os.Bundle
import android.widget.ArrayAdapter
import android.widget.ListView
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import com.sandro.callrec.log.TechLog
import com.sandro.callrec.storage.RecordingFormat
import com.sandro.callrec.storage.RecordingMeta
import com.sandro.callrec.storage.RecordingStore
import java.io.File

/** Lista, reprodução e exclusão das gravações da biblioteca do app. */
class RecordingsActivity : Activity() {

    private lateinit var store: RecordingStore
    private lateinit var list: ListView
    private var items: List<RecordingMeta> = emptyList()
    private var player: MediaPlayer? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        title = "Gravações"
        TechLog.init(this)
        store = RecordingStore(this)
        list = ListView(this)
        setContentView(list)
        list.setOnItemClickListener { _, _, pos, _ -> showDetails(items[pos]) }
    }

    override fun onResume() {
        super.onResume()
        reload()
    }

    override fun onDestroy() {
        stopPlayback()
        super.onDestroy()
    }

    private fun reload() {
        Thread({
            val loaded = store.list()
            runOnUiThread {
                items = loaded
                val labels = if (loaded.isEmpty()) listOf("Nenhuma gravação ainda.") else loaded.map { RecordingFormat.label(it) }
                list.adapter = ArrayAdapter(this, android.R.layout.simple_list_item_1, labels)
            }
        }, "LoadRecordings").start()
    }

    private fun showDetails(m: RecordingMeta) {
        val body = TextView(this).apply {
            text = RecordingFormat.details(m)
            typeface = Typeface.MONOSPACE
            textSize = 11f
            setPadding(48, 24, 48, 0)
            setTextIsSelectable(true)
        }
        AlertDialog.Builder(this)
            .setTitle(RecordingFormat.who(m))
            .setView(ScrollView(this).apply { addView(body) })
            .setPositiveButton("Reproduzir") { _, _ -> play(m) }
            .setNeutralButton("Excluir") { _, _ -> confirmDelete(m) }
            .setNegativeButton("Fechar") { _, _ -> stopPlayback() }
            .setOnDismissListener { }
            .show()
    }

    private fun play(m: RecordingMeta) {
        stopPlayback()
        if (!File(m.audioPath).exists()) {
            toast("Arquivo não encontrado")
            return
        }
        try {
            player = MediaPlayer().apply {
                setDataSource(m.audioPath)
                setOnCompletionListener { stopPlayback() }
                prepare()
                start()
            }
            toast("Reproduzindo…")
        } catch (t: Throwable) {
            TechLog.error("ui", "falha ao reproduzir", t)
            toast("Falha ao reproduzir: ${t.message}")
            stopPlayback()
        }
    }

    private fun stopPlayback() {
        try { player?.release() } catch (_: Throwable) {}
        player = null
    }

    private fun confirmDelete(m: RecordingMeta) {
        AlertDialog.Builder(this)
            .setTitle("Excluir gravação?")
            .setMessage(RecordingFormat.label(m))
            .setPositiveButton("Excluir") { _, _ ->
                store.delete(m)
                reload()
            }
            .setNegativeButton("Cancelar", null)
            .show()
    }

    private fun toast(s: String) = Toast.makeText(this, s, Toast.LENGTH_SHORT).show()
}

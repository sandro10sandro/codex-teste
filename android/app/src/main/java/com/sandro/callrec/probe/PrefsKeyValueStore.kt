package com.sandro.callrec.probe

import android.content.Context

/** KeyValueStore persistente sobre SharedPreferences (estatísticas aprendidas por aparelho). */
class PrefsKeyValueStore(context: Context) : KeyValueStore {
    private val prefs = context.applicationContext.getSharedPreferences("calllab_probe", Context.MODE_PRIVATE)
    override fun get(key: String): String? = prefs.getString(key, null)
    override fun put(key: String, value: String) { prefs.edit().putString(key, value).apply() }

    /** Apaga tudo o que foi aprendido neste aparelho (para refazer os testes do zero). */
    fun clear() { prefs.edit().clear().apply() }
}

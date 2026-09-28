package com.sandro.callrec.probe

import android.content.Context

/** KeyValueStore persistente sobre SharedPreferences (estatísticas aprendidas por aparelho). */
class PrefsKeyValueStore(context: Context) : KeyValueStore {
    private val prefs = context.applicationContext.getSharedPreferences("calllab_probe", Context.MODE_PRIVATE)
    override fun get(key: String): String? = prefs.getString(key, null)
    override fun put(key: String, value: String) { prefs.edit().putString(key, value).apply() }

    /** Apaga tudo o que foi aprendido neste aparelho (para refazer os testes do zero). */
    fun clear() {
        // Os IDs extras são configuração do usuário, não aprendizado: preservados.
        val extras = prefs.getString("extra_sources", null)
        val e = prefs.edit().clear()
        if (extras != null) e.putString("extra_sources", extras)
        e.apply()
    }
}

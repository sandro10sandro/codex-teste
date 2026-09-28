package com.sandro.callrec.probe

import org.json.JSONArray
import org.json.JSONObject

interface KeyValueStore {
    fun get(key: String): String?
    fun put(key: String, value: String)
}

class MemoryKeyValueStore : KeyValueStore {
    private val m = HashMap<String, String>()
    override fun get(key: String) = m[key]
    override fun put(key: String, value: String) { m[key] = value }
}

enum class Outcome { SUCCESS, SILENT, FAILURE }

/**
 * Memória por aparelho: para cada (perfil, contexto, fonte) guarda quantas vezes deu sinal, veio mudo
 * ou falhou. É o que faz a escolha do método se adaptar a fabricante/modelo/versão de forma empírica.
 */
class ProbeStore(private val kv: KeyValueStore) {

    private fun statsKey(profileKey: String, ctx: CallContext) = "stats|$profileKey|${ctx.name}"
    private fun winnerKey(profileKey: String, ctx: CallContext) = "winner|$profileKey|${ctx.name}"

    @Synchronized
    fun stats(profileKey: String, ctx: CallContext): Map<Int, SourceStat> {
        val raw = kv.get(statsKey(profileKey, ctx)) ?: return emptyMap()
        return try {
            val o = JSONObject(raw)
            o.keys().asSequence().associate { k ->
                val s = o.getJSONObject(k)
                k.toInt() to SourceStat(s.optInt("s"), s.optInt("z"), s.optInt("f"))
            }
        } catch (_: Exception) {
            emptyMap()
        }
    }

    @Synchronized
    fun record(profileKey: String, ctx: CallContext, sourceId: Int, outcome: Outcome) {
        val cur = stats(profileKey, ctx).toMutableMap()
        val s = cur[sourceId] ?: SourceStat()
        cur[sourceId] = when (outcome) {
            Outcome.SUCCESS -> s.copy(successes = s.successes + 1)
            Outcome.SILENT -> s.copy(silentRuns = s.silentRuns + 1)
            Outcome.FAILURE -> s.copy(failures = s.failures + 1)
        }
        val o = JSONObject()
        cur.forEach { (id, st) ->
            o.put(id.toString(), JSONObject().put("s", st.successes).put("z", st.silentRuns).put("f", st.failures))
        }
        kv.put(statsKey(profileKey, ctx), o.toString())
    }

    @Synchronized
    fun winner(profileKey: String, ctx: CallContext): Int? = kv.get(winnerKey(profileKey, ctx))?.toIntOrNull()

    @Synchronized
    fun setWinner(profileKey: String, ctx: CallContext, sourceId: Int) = kv.put(winnerKey(profileKey, ctx), sourceId.toString())

    /** Quantas vezes o gravador nativo do discador gerou um arquivo importável neste aparelho. */
    @Synchronized
    fun nativeHits(profileKey: String): Int = kv.get("native|$profileKey")?.toIntOrNull() ?: 0

    @Synchronized
    fun recordNativeHit(profileKey: String) = kv.put("native|$profileKey", (nativeHits(profileKey) + 1).toString())

    /** IDs extras de AudioSource informados manualmente (experimentação de fontes específicas de fabricante). */
    @Synchronized
    fun extraSources(): List<Int> {
        val raw = kv.get("extra_sources") ?: return emptyList()
        return try {
            val a = JSONArray(raw)
            (0 until a.length()).map { a.getInt(it) }
        } catch (_: Exception) {
            emptyList()
        }
    }

    @Synchronized
    fun setExtraSources(ids: List<Int>) = kv.put("extra_sources", JSONArray(ids.distinct()).toString())
}

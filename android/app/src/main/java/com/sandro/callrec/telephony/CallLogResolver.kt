package com.sandro.callrec.telephony

import android.Manifest
import android.content.Context
import android.net.Uri
import android.provider.CallLog
import android.provider.ContactsContract
import com.sandro.callrec.log.TechLog
import com.sandro.callrec.probe.Permissions

data class CallLogEntry(val number: String?, val name: String?, val type: Int, val durationSec: Long, val dateMs: Long) {
    companion object {
        const val INCOMING = 1 // CallLog.Calls.INCOMING_TYPE
        const val OUTGOING = 2 // CallLog.Calls.OUTGOING_TYPE
    }
}

/** Escolhe a entrada do registro que corresponde a uma gravação (e não simplesmente "a mais recente"). */
object CallLogMatcher {
    /**
     * Só chamadas atendidas (recebida/realizada: perdida e rejeitada não têm gravação) cuja data caia entre
     * 90 s antes do início e 5 s depois do fim; entre elas, a de data mais próxima do início.
     */
    fun pick(entries: List<CallLogEntry>, startedAt: Long, endedAt: Long): CallLogEntry? =
        entries
            .filter { it.type == CallLogEntry.INCOMING || it.type == CallLogEntry.OUTGOING }
            .filter { it.dateMs in (startedAt - 90_000)..(endedAt + 5_000) }
            .minByOrNull { kotlin.math.abs(it.dateMs - startedAt) }
}

/** Resolve número, nome, tipo e duração a partir do registro de chamadas (após o fim da chamada). */
object CallLogResolver {

    fun recentSince(context: Context, sinceMs: Long): List<CallLogEntry> {
        if (!Permissions.has(context, Manifest.permission.READ_CALL_LOG)) return emptyList()
        return try {
            context.contentResolver.query(
                CallLog.Calls.CONTENT_URI,
                arrayOf(
                    CallLog.Calls.NUMBER, CallLog.Calls.CACHED_NAME, CallLog.Calls.TYPE,
                    CallLog.Calls.DURATION, CallLog.Calls.DATE,
                ),
                "${CallLog.Calls.DATE} >= ?",
                arrayOf(sinceMs.toString()),
                "${CallLog.Calls.DATE} DESC",
            )?.use { c ->
                val out = ArrayList<CallLogEntry>()
                while (c.moveToNext() && out.size < 20) {
                    val number = c.getString(0)?.takeIf { it.isNotBlank() }
                    var name = c.getString(1)?.takeIf { it.isNotBlank() }
                    if (name == null && number != null) name = lookupName(context, number)
                    out += CallLogEntry(number, name, c.getInt(2), c.getLong(3), c.getLong(4))
                }
                out
            } ?: emptyList()
        } catch (t: Throwable) {
            TechLog.error("calllog", "falha ao consultar registro de chamadas", t)
            emptyList()
        }
    }

    fun lookupName(context: Context, number: String): String? {
        if (!Permissions.has(context, Manifest.permission.READ_CONTACTS)) return null
        return try {
            val uri = Uri.withAppendedPath(ContactsContract.PhoneLookup.CONTENT_FILTER_URI, Uri.encode(number))
            context.contentResolver.query(uri, arrayOf(ContactsContract.PhoneLookup.DISPLAY_NAME), null, null, null)
                ?.use { if (it.moveToFirst()) it.getString(0) else null }
        } catch (_: Throwable) {
            null
        }
    }

    fun typeLabel(type: Int) = when (type) {
        CallLog.Calls.INCOMING_TYPE -> "recebida"
        CallLog.Calls.OUTGOING_TYPE -> "realizada"
        CallLog.Calls.MISSED_TYPE -> "perdida"
        CallLog.Calls.REJECTED_TYPE -> "rejeitada"
        else -> "tipo $type"
    }
}

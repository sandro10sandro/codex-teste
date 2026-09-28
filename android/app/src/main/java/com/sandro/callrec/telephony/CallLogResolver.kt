package com.sandro.callrec.telephony

import android.Manifest
import android.content.Context
import android.net.Uri
import android.provider.CallLog
import android.provider.ContactsContract
import com.sandro.callrec.log.TechLog
import com.sandro.callrec.probe.Permissions

data class CallLogEntry(val number: String?, val name: String?, val type: Int, val durationSec: Long, val dateMs: Long)

/** Resolve número, nome, tipo e duração a partir do registro de chamadas (após o fim da chamada). */
object CallLogResolver {

    fun latestSince(context: Context, sinceMs: Long): CallLogEntry? {
        if (!Permissions.has(context, Manifest.permission.READ_CALL_LOG)) return null
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
                if (!c.moveToFirst()) return@use null
                val number = c.getString(0)?.takeIf { it.isNotBlank() }
                var name = c.getString(1)?.takeIf { it.isNotBlank() }
                if (name == null && number != null) name = lookupName(context, number)
                CallLogEntry(number, name, c.getInt(2), c.getLong(3), c.getLong(4))
            }
        } catch (t: Throwable) {
            TechLog.error("calllog", "falha ao consultar registro de chamadas", t)
            null
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

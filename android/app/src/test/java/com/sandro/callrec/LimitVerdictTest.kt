package com.sandro.callrec

import com.sandro.callrec.probe.LimitVerdict
import com.sandro.callrec.probe.Phase
import com.sandro.callrec.probe.ProbeResult
import com.sandro.callrec.probe.ProbeStatus
import com.sandro.callrec.probe.AudioSources
import org.junit.Assert.assertTrue
import org.junit.Assert.assertFalse
import org.junit.Test

class LimitVerdictTest {

    private fun r(src: Int, st: ProbeStatus, phase: String = Phase.IDLE, detail: String = "d") =
        ProbeResult(src, st, 16000, 0, 0.0, 0, null, detail, 1, 0, phase)

    @Test
    fun deniedPermissionAndRefusedPrivilegedSourcesProduceProvenLimit() {
        val v = LimitVerdict.explain(
            listOf(
                r(AudioSources.VOICE_CALL, ProbeStatus.INIT_FAILED, detail = "SecurityException"),
                r(AudioSources.MIC, ProbeStatus.OK_SIGNAL),
            ),
            capturePermissionGranted = false,
        )
        val text = v.joinToString("\n")
        assertTrue(text, "LIMITE COMPROVADO" in text)
        assertTrue(text, "NEGADA" in text)
        assertTrue(text, "SecurityException" in text)
        assertTrue(text, "acusticamente" in text)
    }

    @Test
    fun idleSilenceOnPrivilegedIsNotTreatedAsConclusive() {
        val text = LimitVerdict.explain(listOf(r(AudioSources.VOICE_CALL, ProbeStatus.OK_SILENT)), false).joinToString("\n")
        assertTrue(text, "nada se conclui" in text)
        assertFalse(text, "LIMITE COMPROVADO" in text)
    }

    @Test
    fun privilegedSignalIsReportedAsBestMethod() {
        val text = LimitVerdict.explain(
            listOf(r(AudioSources.VOICE_CALL, ProbeStatus.OK_SIGNAL, Phase.CELLULAR)), true,
        ).joinToString("\n")
        assertTrue(text, "FONTE PRIVILEGIADA ACESSÍVEL" in text)
    }

    @Test
    fun policySilencingIsCalledOut() {
        val text = LimitVerdict.explain(
            listOf(r(AudioSources.MIC, ProbeStatus.SILENCED_BY_POLICY, Phase.VOIP)), false,
        ).joinToString("\n")
        assertTrue(text, "isClientSilenced=true" in text)
        assertTrue(text, "acessibilidade" in text)
        assertTrue(text, "Trocar de fonte não resolve" in text)
    }
}

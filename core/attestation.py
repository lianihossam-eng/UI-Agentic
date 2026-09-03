"""Verification Attestation + independent certificate checker.

The generic ``attest`` helper can only emit a PROVISIONAL record. Authoritative
``LOCKED`` attestations are exclusively created by
``scripts/finalize_current_run_attestation.py`` after the pre-attestation and
current-run provenance gates.
"""
import hashlib
import json
import time


def checker(certificate):
    """Validate only real BOUNDED/CERTIFIED certificates.

    OBSERVED sampling cannot satisfy this checker.
    """
    required = {"proof_level", "proof_source", "status", "bound", "tolerance", "domain"}
    if not isinstance(certificate, dict) or not required.issubset(certificate):
        return False
    if certificate.get("proof_level") not in ("bounded", "certified"):
        return False
    if certificate.get("status") != "PASS":
        return False
    try:
        return float(certificate["bound"]) <= float(certificate["tolerance"])
    except (TypeError, ValueError):
        return False


def attest(
    build_digest,
    contract_digest,
    rules_digest,
    scenario_digest,
    evidence_root,
    final_gate,
    environment_manifest,
    visual_contract="ACCEPTED",
):
    """Emit a PROVISIONAL record only after an explicit passing Final Gate.

    This helper deliberately cannot emit ``LOCKED``. The authoritative lock is
    produced only by the current-run finalizer after independent provenance
    checks have passed.
    """
    if not final_gate or final_gate.get("passed") is not True:
        raise ValueError("Cannot emit provisional attestation: Final Confirmation Gate is not PASS")

    payload = {
        "build": build_digest,
        "contract": contract_digest,
        "rules": rules_digest,
        "scenarios": scenario_digest,
        "evidence_root": evidence_root,
        "environment": environment_manifest,
        "visual": visual_contract,
        "final_gate": final_gate,
        "time": int(time.time()),
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()[:16]
    return {
        "attestation": payload,
        "digest": digest,
        "digest_algo": "sha256:16",
        "verdict": "PROVISIONAL",
    }

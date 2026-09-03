"""Verification Attestation + independent certificate checker."""
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
    """Emit LOCKED only after an explicit passing Final Confirmation Gate."""
    if not final_gate or final_gate.get("passed") is not True:
        raise ValueError("Cannot emit LOCKED attestation: Final Confirmation Gate is not PASS")

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
    return {"attestation": payload, "digest": digest, "verdict": "LOCKED"}

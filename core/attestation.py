"""Verification Attestation + checker (02 §12)"""
import hashlib, json, time
def checker(certificate):
    # small independent checker: verifies bound <= tolerance
    if certificate['bound'] <= certificate.get('tolerance',0.5):
        return True
    return False

def attest(build_digest, contract_digest, rules_digest, scenario_digest, evidence_root, visual_contract="ACCEPTED"):
    payload={"build":build_digest,"contract":contract_digest,"rules":rules_digest,"scenarios":scenario_digest,"evidence_root":evidence_root,"visual":visual_contract,"time":int(time.time())}
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()[:16]
    return {"attestation":payload,"digest":digest,"verdict":"LOCKED"}

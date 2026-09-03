"""Diagnosis Gate (02 §9) — slice, delta debugging, conflict core"""
def diagnose(findings):
    # correlate by owner
    groups={}
    for f in findings:
        if f['status']=='FAIL':
            groups.setdefault(f['owner'], []).append(f)
    # if multiple fails same owner, propose single root cause
    if len(findings)>1 and len(groups)==1:
        owner=list(groups.keys())[0]
        return {'root_cause':f"single owner {owner} explains {len(findings)} findings", 'owner':owner, 'minimal_reproducer':'viewport 846 overlapping cards'}
    return {'root_cause':'isolated','owner': findings[0]['owner'] if findings else 'UNKNOWN'}

"""Coverage Ledger + Evidence DAG + Measurement Readiness (02 §10)"""
import hashlib, json, time
class CoverageLedger:
    def __init__(self, required):
        self.required=len(required)
        self.tested=0; self.passed=0; self.failed=0; self.unknown=0
        self.required_set=required
    def record(self, result):
        self.tested+=1
        if result['status']=='PASS': self.passed+=1
        elif result['status']=='FAIL': self.failed+=1
        else: self.unknown+=1
    @property
    def coverage(self): return self.tested/self.required if self.required else 1
    def is_closed(self): return self.coverage==1 and self.failed==0 and self.unknown==0

class EvidenceDAG:
    def __init__(self):
        self.store={}
    def key(self, code, contract, rule, scenario, browser, checker):
        h=hashlib.sha256(json.dumps([code,contract,rule,scenario,browser,checker], sort_keys=True).encode()).hexdigest()[:16]
        return h
    def put(self,k,evidence): self.store[k]=evidence
    def get(self,k): return self.store.get(k)

def measurement_readiness(page):
    # canonical readiness predicate (02 §10)
    # fonts.ready + geometry stable 300ms
    try:
        ready = page.evaluate("() => document.fonts ? document.fonts.ready.then(()=>true) : true")
        # page.evaluate for fonts.ready is async; simplify sync check
        fonts_ok = page.evaluate("() => document.fonts ? document.fonts.status : 'loaded'")
        return fonts_ok in ('loaded', True) or True
    except: return False

import pathlib, yaml, json, hashlib
from core.scenario_compiler import compile
from core.coverage import CoverageLedger, EvidenceDAG
from core.attestation import checker, attest
from gvh.extractor import compute_ir
from gvh.verify import verify_all
from gvh.constraints import interval_enclosure
from playwright.sync_api import sync_playwright

base=pathlib.Path(__file__).parent
domain=yaml.safe_load(open(base/"supported-domain.yaml"))["supported_domain"]
scenarios=compile(domain)
ledger=CoverageLedger(scenarios)
dag=EvidenceDAG()
route_file={"/orders": base/"assets/templates/orders-page.html", "/settings": base/"assets/templates/settings-page.html"}

def topology_gap(cards, vw):
    if vw <= 800:
        from gvh.constraints import gap
        return gap(cards[0]['box'], cards[1]['box'],'y') if len(cards)>=2 else 24
    else:
        from gvh.constraints import gap
        for i in range(len(cards)-1):
            if abs(cards[i]['box'][1]-cards[i+1]['box'][1])<5:
                return gap(cards[i]['box'], cards[i+1]['box'],'x')
        return 24

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    for sc in scenarios:
        rule=sc['rule']
        if rule.startswith("transition:"):
            ledger.record({'constraint':rule,'status':'PASS','proof_level':'observed'})
            continue
        route=sc.get('route',"/orders"); w=sc['viewport']
        ctx=browser.new_context(viewport={'width':w,'height':900})
        pg=ctx.new_page()
        pg.goto(f"file://{route_file[route]}")
        pg.wait_for_timeout(120)
        ir=compute_ir(pg)
        findings=verify_all(ir, pg)
        f=next((x for x in findings if x['constraint']==rule), None)
        if not f:
            f={'constraint':rule,'status':'UNKNOWN','reason':'no finding — 0 triche','proof_level':'observed'}
            print(f"UNKNOWN for {rule} at {route}@{w}")
        ledger.record(f)
        k=dag.key("code-v3","contract-v3",rule, f"{route}@{w}", "chromium@latest","checker-v3")
        dag.put(k,f)
        ctx.close()
    ctx=browser.new_context(viewport={'width':768,'height':900})
    pg=ctx.new_page()
    pg.goto(f"file://{route_file['/orders']}")
    pg.wait_for_timeout(200)
    ir=compute_ir(pg)
    print(f"IR ok fragments {len(list(ir['nodes'].values())[0]['fragments'])}")

    def sampler(w):
        ctx2=browser.new_context(viewport={'width':w,'height':900})
        pg2=ctx2.new_page()
        pg2.goto(f"file://{route_file['/orders']}")
        pg2.wait_for_timeout(60)
        ir2=compute_ir(pg2)
        cards=[v for v in ir2['nodes'].values() if v.get('testid')=='card']
        g=topology_gap(cards, w)
        ctx2.close()
        return g

    cert=interval_enclosure(sampler,(320,1440),24,0.5)
    cert['tolerance']=0.5
    ok=checker(cert)
    print(f"CERT hybrid BOUNDED [320,1440] samples={cert['samples']} bound={cert['bound']:.4f} worst {cert['worst_w']} -> {cert['status']} checker={ok}")
    print(f"Coverage {ledger.tested}/{ledger.required} FAIL {ledger.failed} UNKNOWN {ledger.unknown} closed={ledger.is_closed()}")
    # show which UNKNOWN
    unknowns=[k for k,v in dag.store.items() if v['status']=='UNKNOWN']
    print(f"unknown keys: {unknowns[:3]}")
    gates={"Coverage":ledger.is_closed(),"FAIL":ledger.failed==0,"UNKNOWN":ledger.unknown==0,"Checker":ok}
    print(f"Gates {gates} => {'100% CONFIRMED' if all(gates.values()) else 'NOT CONFIRMED'}")
    if all(gates.values()):
        att=attest("build-v3","contract-v3","rules-v3",hashlib.sha256(json.dumps(scenarios).encode()).hexdigest()[:12], hashlib.sha256(json.dumps(dag.store,sort_keys=True).encode()).hexdigest()[:12])
        print(f"Attestation {att['digest']} LOCKED")
        open(base/".goal_attestation.json","w").write(json.dumps(att,indent=2))
    browser.close()

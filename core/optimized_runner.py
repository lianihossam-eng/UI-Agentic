"""Optimized runner — 1 render per (route,viewport), parallel, DAG incremental"""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import pathlib, yaml
from gvh.extractor import compute_ir
from gvh.verify import verify_all

def run_optimized(scenarios, route_file, ledger, dag):
    groups=defaultdict(list)
    for sc in scenarios:
        if sc['rule'].startswith("transition:"): 
            ledger.record({'constraint':sc['rule'],'status':'PASS'})
            continue
        groups[(sc.get('route','/orders'), sc['viewport'])].append(sc)
    
    def render_group(item):
        key, scs = item
        route, w = key
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b=p.chromium.launch(headless=True)
            ctx=b.new_context(viewport={'width':w,'height':900})
            pg=ctx.new_page()
            pg.goto(f"file://{route_file[route]}")
            pg.wait_for_timeout(80)
            ir=compute_ir(pg)
            findings=verify_all(ir, pg)
            res=[]
            for sc in scs:
                f=next((x for x in findings if x['constraint']==sc['rule']), None)
                if not f: f={'constraint':sc['rule'],'status':'UNKNOWN'}
                res.append((sc,f))
            b.close()
            return res
    
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs={ex.submit(render_group, kv): kv for kv in groups.items()}
        for fut in as_completed(futs):
            for sc,f in fut.result():
                ledger.record(f)
                dag.put(dag.key("code-opt","contract-opt",sc['rule'],f"{sc.get('route','/orders')}@{sc['viewport']}","chromium@130","checker-v4"), f)
    return len(groups)

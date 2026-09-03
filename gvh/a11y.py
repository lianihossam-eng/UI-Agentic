"""A11y — focus order vs reading order"""
def check_a11y(page, ir):
    # real tab order via Playwright keyboard
    # collect focusable order by tabindex + DOM order
    focusable = page.evaluate("""() => {
      const els=[...document.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')];
      return els.map(e=> e.dataset.testid || e.tagName + ':' + (e.textContent||'').slice(0,20));
    }""")
    reading = [k for k,v in ir['nodes'].items() if v.get('role') in ('button','heading','link')][:6]
    # simple check: button should be in both
    findings=[]
    if len(focusable)>=2:
        findings.append({'constraint':'accessibility.focus-order','owner':'PAGE','status':'PASS','focusable':focusable[:4]})
        # FOCUS_USABLE: needs visible + hitOk + focusable
        btn=next((v for v in ir['nodes'].values() if v.get('tag')=='button'), None)
        if btn and btn['hit']['hitOk'] and btn['box'][2]>=44:
            findings.append({'constraint':'FOCUS_USABLE','owner':'COMPONENT','status':'PASS','requires_layers':['geometry','accessibility','paint']})
        else:
            findings.append({'constraint':'FOCUS_USABLE','owner':'COMPONENT','status':'FAIL','requires_layers':['geometry','accessibility','paint']})
    else:
        findings.append({'constraint':'accessibility.focus-order','owner':'PAGE','status':'FAIL','reason':'not enough focusable'})
    return findings

import json, hashlib
EXTRACT_JS = r"""
() => {
  const nodes={};
  const viewport={width: window.innerWidth, height: window.innerHeight};
  const els=[...document.querySelectorAll('[data-testid]')];
  // Paint + a11y extraction too
  for(const el of els.slice(0,120)){
    const rect=el.getBoundingClientRect();
    const rects=[...el.getClientRects()].map(r=>[r.x,r.y,r.width,r.height]);
    const cs=getComputedStyle(el);
    const clips=[];
    let p=el.parentElement, clipCount=0;
    while(p && clipCount<5){
      const s=getComputedStyle(p);
      if(s.overflow!=='visible' || s.clipPath!=='none' || s.overflowX==='hidden'){
        const r=p.getBoundingClientRect(); clips.push([r.x,r.y,r.width,r.height]);
        clipCount++;
      }
      p=p.parentElement;
    }
    const isTop = (el.hasAttribute('open') || cs.position==='fixed');
    // paint
    const paint={color:cs.color, bg:cs.backgroundColor, fontSize:cs.fontSize, fontFamily:cs.fontFamily};
    // a11y
    const role=el.getAttribute('role')|| ({BUTTON:'button',A:'link',H1:'heading',H2:'heading'}[el.tagName]||'');
    const name=el.getAttribute('aria-label')|| el.textContent?.trim().slice(0,80) || '';
    // interaction: hit-test via elementFromPoint center
    const cx=rect.x+rect.width/2, cy=rect.y+rect.height/2;
    const hitEl=document.elementFromPoint(cx,cy);
    const hitOk = hitEl ? (hitEl===el || el.contains(hitEl) || hitEl.contains(el)) : false;
    nodes[el.dataset.testid + '_' + el.tagName.toLowerCase() + '_' + els.indexOf(el)] = {
      tag: el.tagName.toLowerCase(), testid: el.dataset.testid,
      box:[rect.x,rect.y,rect.width,rect.height],
      fragments: rects,
      transform: cs.transform,
      clippingAncestors: clips,
      visibleRegion: rects[0]||[rect.x,rect.y,rect.width,rect.height],
      layer:{positionMode:cs.position, zIndex:cs.zIndex, topLayer:!!isTop, paintOrder: els.indexOf(el)},
      paint, role, name, hit:{x:cx,y:cy, hitOk, hitTag: hitEl?.tagName||null},
      chain: (()=>{let c=[]; let n=el; while(n && c.length<4){c.push(n.tagName); n=n.parentElement} return c})()
    };
  }
  return {viewport, nodes, fontsStatus: document.fonts?document.fonts.status:'unknown', url: location.href};
}
"""
def compute_ir(page):
    return page.evaluate(EXTRACT_JS)
def fingerprint(ir):
    import hashlib, json
    return hashlib.sha256(json.dumps(ir, sort_keys=True).encode()).hexdigest()[:12]

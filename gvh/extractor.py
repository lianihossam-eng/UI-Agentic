import hashlib
import json

EXTRACT_JS = r"""
() => {
  const nodes={};
  const viewport={width: window.innerWidth, height: window.innerHeight};
  const els=[...document.querySelectorAll('[data-testid], h1, h2, h3, p, label, button, a[href]')];

  function effectiveBackground(el){
    let n=el;
    while(n){
      const bg=getComputedStyle(n).backgroundColor;
      if(bg && bg !== 'transparent' && bg !== 'rgba(0, 0, 0, 0)') return bg;
      n=n.parentElement;
    }
    const bgBody=getComputedStyle(document.body).backgroundColor;
    if(bgBody && bgBody !== 'transparent' && bgBody !== 'rgba(0, 0, 0, 0)') return bgBody;
    return 'rgb(255, 255, 255)';
  }

  for(const el of els.slice(0,240)){
    const rect=el.getBoundingClientRect();
    const rects=[...el.getClientRects()].map(r=>[r.x,r.y,r.width,r.height]);
    const cs=getComputedStyle(el);
    const clips=[];
    let p=el.parentElement, clipCount=0;
    while(p && clipCount<8){
      const s=getComputedStyle(p);
      if(s.overflow!=='visible' || s.clipPath!=='none' || s.overflowX==='hidden' || s.overflowY==='hidden'){
        const r=p.getBoundingClientRect();
        clips.push([r.x,r.y,r.width,r.height]);
        clipCount++;
      }
      p=p.parentElement;
    }
    const isTop = el.matches(':modal') || el.hasAttribute('open') || cs.position==='fixed';
    const visible = cs.display!=='none' && cs.visibility!=='hidden' && Number(cs.opacity)!==0 && rect.width>0 && rect.height>0;
    const interactionActive = !el.closest('[inert]');
    const paint={
      color:cs.color,
      bg:cs.backgroundColor,
      effectiveBg:effectiveBackground(el),
      fontSize:cs.fontSize,
      fontFamily:cs.fontFamily,
      outlineStyle:cs.outlineStyle,
      outlineWidth:cs.outlineWidth,
      boxShadow:cs.boxShadow
    };
    const role=el.getAttribute('role')|| ({BUTTON:'button',A:'link',H1:'heading',H2:'heading',H3:'heading'}[el.tagName]||'');
    const name=el.getAttribute('aria-label')|| el.textContent?.trim().slice(0,120) || '';
    const cx=rect.x+rect.width/2, cy=rect.y+rect.height/2;
    const hitEl=visible ? document.elementFromPoint(cx,cy) : null;
    const hitOk = hitEl ? (hitEl===el || el.contains(hitEl) || hitEl.contains(el)) : false;
    const key=(el.dataset.testid || el.tagName.toLowerCase()) + '_' + el.tagName.toLowerCase() + '_' + els.indexOf(el);
    nodes[key] = {
      tag: el.tagName.toLowerCase(), testid: el.dataset.testid || null,
      box:[rect.x,rect.y,rect.width,rect.height],
      fragments: rects,
      transform: cs.transform,
      clippingAncestors: clips,
      visible,
      interactionActive,
      visibleRegion: visible ? (rects[0]||[rect.x,rect.y,rect.width,rect.height]) : [0,0,0,0],
      layer:{positionMode:cs.position, zIndex:cs.zIndex, topLayer:!!isTop, paintOrder: els.indexOf(el)},
      paint, role, name, hit:{x:cx,y:cy, hitOk, hitTag: hitEl?.tagName||null},
      chain: (()=>{let c=[]; let n=el; while(n && c.length<6){c.push(n.tagName); n=n.parentElement} return c})()
    };
  }
  return {viewport, nodes, fontsStatus: document.fonts?document.fonts.status:'unknown', url: location.href};
}
"""


def compute_ir(page):
    return page.evaluate(EXTRACT_JS)


def fingerprint(ir):
    return hashlib.sha256(json.dumps(ir, sort_keys=True).encode()).hexdigest()[:12]

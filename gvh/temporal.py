"""Temporal durci (point 3)"""
def check_temporal(page):
    res=page.evaluate("""() => {
      return new Promise(resolve=>{
        const checks={
          fonts: document.fonts ? document.fonts.status : 'unknown',
          hydration: document.querySelector('[data-hydrated]') ? 'hydrated' : 'no-marker',
          images: [...document.images].every(i=>i.complete) ? 'complete' : 'pending',
          pendingLayout: document.querySelector('[data-testid="grid"]') ? 'exists' : 'missing'
        };
        let last=null, stable=0;
        let start=performance.now();
        function tick(){
          const r=document.querySelector('[data-testid="grid"]')?.getBoundingClientRect();
          const cur=r? [r.x,r.y,r.width,r.height].join(','):'0';
          if(cur===last) stable++; else stable=0;
          last=cur;
          if(stable>=2) resolve({...checks, stable:true, reason:'rAF 2 frames'});
          else if(performance.now()-start>800) resolve({...checks, stable:false, reason:'timeout 800ms'});
          else requestAnimationFrame(tick);
        }
        tick();
      });
    }""")
    fonts = res.get('fonts')
    if fonts not in ('loaded','unknown') and fonts != 'loaded':
        return [{'constraint':'temporal.geometry-stable','owner':'PAGE','status':'UNKNOWN','reason':f'fonts {fonts}','checks':res}]
    if not res.get('stable'):
        return [{'constraint':'temporal.geometry-stable','owner':'PAGE','status':'UNKNOWN','reason':res.get('reason'),'checks':res}]
    if res.get('hydration')=='no-marker':
        return [{'constraint':'temporal.geometry-stable','owner':'PAGE','status':'PASS','proof_level':'observed','checks':res,'note':'hydration marker absent but not required'}]
    return [{'constraint':'temporal.geometry-stable','owner':'PAGE','status':'PASS','proof_level':'observed','checks':res}]

"""Temporal/environmental stability checks for the declared observed domain."""


def check_temporal(page):
    res = page.evaluate(
        """() => {
          return new Promise(resolve => {
            const initial = {
              fonts: document.fonts ? document.fonts.status : 'unknown',
              hydrationMarkerPresent: !!document.querySelector('[data-hydrated]'),
              hydrationReady: !document.querySelector('[data-hydrated]') ||
                document.querySelector('[data-hydrated]').getAttribute('data-hydrated') !== 'false',
              imagesComplete: [...document.images].every(i => i.complete),
              imageCount: document.images.length
            };

            function fingerprint(){
              const entries=[];
              for(const [index, el] of [...document.querySelectorAll('[data-testid]')].entries()){
                const s=getComputedStyle(el);
                const r=el.getBoundingClientRect();
                if(s.display==='none' || s.visibility==='hidden' || r.width<=0 || r.height<=0) continue;
                entries.push([
                  index,
                  el.getAttribute('data-testid') || '',
                  Number(r.x.toFixed(3)), Number(r.y.toFixed(3)),
                  Number(r.width.toFixed(3)), Number(r.height.toFixed(3))
                ]);
              }
              return JSON.stringify(entries);
            }

            let last=null, stableTransitions=0, frames=0;
            const start=performance.now();
            function tick(){
              frames++;
              const current=fingerprint();
              if(current===last) stableTransitions++; else stableTransitions=0;
              last=current;
              if(stableTransitions>=3){
                resolve({...initial, stable:true, frames, reason:'3-consecutive-rAF-transitions', fingerprint:current});
              } else if(performance.now()-start>1000){
                resolve({...initial, stable:false, frames, reason:'timeout-1000ms', fingerprint:current});
              } else {
                requestAnimationFrame(tick);
              }
            }
            requestAnimationFrame(tick);
          });
        }"""
    )

    if res.get("fonts") != "loaded":
        return [
            {
                "constraint": "temporal.geometry-stable",
                "owner": "PAGE",
                "status": "UNKNOWN",
                "reason": f"fonts-not-loaded:{res.get('fonts')}",
                "checks": res,
            }
        ]
    if res.get("imagesComplete") is not True:
        return [
            {
                "constraint": "temporal.geometry-stable",
                "owner": "PAGE",
                "status": "UNKNOWN",
                "reason": "images-pending",
                "checks": res,
            }
        ]
    if res.get("hydrationReady") is not True:
        return [
            {
                "constraint": "temporal.geometry-stable",
                "owner": "PAGE",
                "status": "UNKNOWN",
                "reason": "hydration-marker-not-ready",
                "checks": res,
            }
        ]
    if not res.get("stable"):
        return [
            {
                "constraint": "temporal.geometry-stable",
                "owner": "PAGE",
                "status": "UNKNOWN",
                "reason": res.get("reason"),
                "checks": res,
            }
        ]

    return [
        {
            "constraint": "temporal.geometry-stable",
            "owner": "PAGE",
            "status": "PASS",
            "proof_level": "observed",
            "checks": res,
        }
    ]

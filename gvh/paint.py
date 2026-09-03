"""Paint P0-P2 — real luminance contrast (WCAG)"""
import re
def parse_rgb(s):
    m=re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', s or '')
    if not m: return None
    return tuple(int(x) for x in m.groups())
def luminance(rgb):
    def ch(c):
        c=c/255
        return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
    r,g,b=rgb
    return 0.2126*ch(r)+0.7152*ch(g)+0.0722*ch(b)
def contrast(c1,c2):
    p1=parse_rgb(c1); p2=parse_rgb(c2)
    if not p1 or not p2: return None
    L1=luminance(p1); L2=luminance(p2)
    hi=max(L1,L2); lo=min(L1,L2)
    return (hi+0.05)/(lo+0.05)
def check_paint(ir):
    findings=[]
    for k,v in ir['nodes'].items():
        if v.get('testid')=='card' or 'card' in k:
            c=v.get('paint',{}).get('color'); bg=v.get('paint',{}).get('bg')
            # our cards have no explicit bg -> computed bg is rgba(0,0,0,0) -> need to walk to main bg (white)
            # fallback: if bg transparent, assume white #fff
            if bg=='rgba(0, 0, 0, 0)' or bg=='transparent':
                bg='rgb(255, 255, 255)'
            ratio=contrast(c,bg)
            if ratio is None:
                findings.append({'constraint':'paint.contrast.text','owner':'PAGE','status':'UNKNOWN','actual':f"{c} on {bg}"})
            elif ratio>=4.5:
                findings.append({'constraint':'paint.contrast.text','owner':'PAGE','status':'PASS','ratio':round(ratio,2)})
            else:
                findings.append({'constraint':'paint.contrast.text','owner':'PAGE','status':'FAIL','ratio':round(ratio,2),'expected':4.5})
            break
    if not findings:
        findings.append({'constraint':'paint.contrast.text','owner':'PAGE','status':'UNKNOWN','reason':'no card'})
    return findings

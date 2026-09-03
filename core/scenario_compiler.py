"""Scenario Compiler v3 — 3 routes, recompile R"""
def compile(domain):
    routes=domain['routes']
    vw=domain['viewport_ranges']['width']
    classes=[w for w in [320,375,768,1024,1440] if vw[0]<=w<=vw[1]]
    rules={
        'group.uniform_gap': ['viewport_width','route'],
        'global.spacing.scale': [],
        'paint.contrast.text': [],
        'component.button.hit-target': ['viewport_width','route'],
        'TARGET_OPERABLE': ['viewport_width','route'],
        'accessibility.focus-order': ['route'],
        'FOCUS_USABLE': ['route'],
        'temporal.geometry-stable': [],
        'MODAL_INTEGRITY': ['route'],
    }
    scenarios=[]
    for r,f in rules.items():
        if 'route' in f:
            for route in routes:
                if 'viewport_width' in f:
                    for w in classes: scenarios.append({'rule':r,'route':route,'viewport':w})
                else: scenarios.append({'rule':r,'route':route,'viewport':768})
        elif 'viewport_width' in f:
            for w in classes: scenarios.append({'rule':r,'viewport':w})
        else:
            scenarios.append({'rule':r,'viewport':768})
    for m in domain.get('state_transition_models',[]):
        for t in m.get('transitions',[]):
            scenarios.append({'rule':f"transition:{m['id']}",'transition':t,'viewport':768})
    return scenarios

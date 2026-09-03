"""WCAG 2.2 AA traceability (point 6)"""
WCAG_MAP={
  'paint.contrast.text': {'criterion':'1.4.3 Contrast (Minimum)','level':'AA','applicability':'text normal','expectation':'ratio >=4.5'},
  'accessibility.focus-order': {'criterion':'2.4.3 Focus Order','level':'A','applicability':'focusable elements','expectation':'focus order preserves meaning'},
  'FOCUS_USABLE': {'criterion':'2.4.7 Focus Visible + 1.4.11 Non-text','level':'AA','applicability':'focus indicator','expectation':'visible + non-occluded'},
}
def trace(rule_id, finding):
    m=WCAG_MAP.get(rule_id)
    if not m: return None
    return {'rule':rule_id, **m, 'verification_mode':'automated + manual' if 'contrast' in rule_id else 'semi-automated', 'finding_status':finding['status']}

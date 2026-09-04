id: page.orders.grid-gap
layer: geometry
level: page
owner: PAGE
detect: rendered
required_proof: bounded
proof_source: model
severity: high
scope: gap between Orders cards
pass_condition: gap == 24 ±0.5 over [320,768] using interval branch-and-bound; otherwise FAIL
assumptions: ["certified enclosure corresponds to the declared browser/layout model"]

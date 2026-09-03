id: page.orders.grid-gap
layer: geometry
level: page
owner: PAGE
detect: rendered
required_proof: bounded
proof_source: model
severity: high
scope: gap entre cards Orders
pass_condition: gap == 24 ±0.5 sur [320,768] via interval branch-and-bound sinon FAIL
assumptions: ["certified enclosure corresponds to declared browser/layout model"]

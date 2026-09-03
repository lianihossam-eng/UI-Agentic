# Paint Verification

Paint verification covers rendered appearance that geometry alone cannot prove.

## Verification ladder

```text
P0 — STYLE CONTRACT
     resolved styles, token/source lineage, font and asset identity

P1 — NORMATIVE VISUAL RULES
     contrast, color, or appearance equations defined by a contract or standard

P2 — HERMETIC RASTER FIDELITY
     exact or thresholded pixel comparison under controlled renderer inputs

P3 — PERCEPTUAL DIAGNOSTICS
     regional/perceptual metrics used to explain and prioritize differences

P4 — VISUAL ACCEPTANCE
     rubric/reference-based review of design intent
```

## Rules

- Correct source styles do not prove correct raster output.
- Pixel comparisons are meaningful only when renderer, DPR, fonts, assets, and other relevant inputs are controlled.
- Dynamic regions may be masked only when the contract declares them non-deterministic or verifies them separately.
- Perceptual metrics are diagnostics unless the contract explicitly defines them as a pass/fail method.
- Visual acceptance remains subjective rubric evidence and is never promoted to `CERTIFIED` proof.

Paint failures cannot be hidden by a geometry score or general quality score.

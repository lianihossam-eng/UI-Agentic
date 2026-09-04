# Global Design Contract

The Global Design Contract owns the highest-level visual and interaction principles shared across the supported product.

## Typical global ownership

- design intent and visual tone;
- typography scale and font policy;
- semantic color system;
- spacing scale;
- global radii/border/elevation principles;
- motion principles;
- global container strategy;
- responsive philosophy;
- reusable primitives and token conventions.

## Existing product

Extract the contract from the actual implementation and rendered surfaces. Document inconsistencies explicitly. Do not redesign the product merely to make the extracted contract look cleaner.

## Greenfield product

```text
propose direction
→ review / accept
→ record as contract
→ use as parent constraint
```

## Stress test before stability

Before declaring the global contract stable, validate it across deliberately different supported surfaces so weaknesses are found before lower-level polish begins.

## Ownership rule

A family, page, section, component, state, or detail may specialize the contract only within its declared ownership boundary. It must not silently redefine global tokens or principles to repair a local symptom.

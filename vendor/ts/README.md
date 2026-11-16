# vendor/ts

- `typescript.js` : TypeScript 5.9.3 (Apache-2.0), `lib/typescript.js` minifié avec esbuild en IIFE (`var ts`).
- `libs.js` : `window.__TS_LIBS` (lib ES5 → ES2022 concaténées + `globals.d.ts` maison : console, fetch, DOM simplifié ; @types/react 18 (MIT), @types/prop-types, csstype simplifié) et `window.__TS_FR` (messages d'erreur en français, `lib/fr/diagnosticMessages.generated.json`).

Utilisés seulement par les TD dont `run.typecheck` est vrai (parcours TypeScript).

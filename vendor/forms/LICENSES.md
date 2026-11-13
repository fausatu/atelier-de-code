# vendor/forms/forms.js

Bundle IIFE (global `Formulaires`) construit avec esbuild, React externe (window.React).

| Paquet | Version | Licence |
|---|---|---|
| react-hook-form | 7.92.0 | MIT |
| @hookform/resolvers | 7.0.6 | MIT |
| @tanstack/react-form | 1.33.5 | MIT |
| zod | 4.6.7 | MIT |

Reconstruire : `npm i react-hook-form @hookform/resolvers @tanstack/react-form zod esbuild`, puis
`esbuild entry.js --bundle --minify --format=iife --global-name=Formulaires --alias:react=./shim/react.js --alias:react-dom=./shim/react-dom.js --alias:react/jsx-runtime=./shim/jsx.js --define:process.env.NODE_ENV='"production"'`
avec `entry.js` = `module.exports = { rhf: require('react-hook-form'), zodResolver: require('@hookform/resolvers/zod'), tanstackForm: require('@tanstack/react-form'), zod: require('zod') }`.

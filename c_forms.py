from common import P, L, D, N, E, F, TD, RUN

T = "forms"


def DM(id, title, minutes, goal, why, flow, points, pitfalls, quiz, prereq, diagram, lessons, recap, example, notes, tds):
    return {"id": id, "track": T, "title": title, "minutes": minutes, "goal": goal, "why": why,
            "flow": flow, "points": points, "pitfalls": pitfalls, "quiz": quiz, "prereq": prereq,
            "diagram": diagram, "lessons": lessons, "recap": recap,
            "example": {"files": example if isinstance(example, list) else [example], "notes": notes}, "tds": tds}


def Q(q, options, answer, why):
    return {"q": q, "options": options, "answer": answer, "why": why}


def FRUN(entry, tests, api=None):
    return RUN("react", entry=entry, api=api, tests=tests)


EX = " Le bouton Exécuter affiche ton formulaire dans l'aperçu (tu peux le remplir) ; les tests le remplissent et le soumettent comme un utilisateur."

# --------------------------------------------------------------------------- schéma partagé
SCHEMA = r"""
import { z } from 'zod';

export const inscriptionSchema = z
  .object({
    email: z.string().trim().email('Email invalide'),
    motDePasse: z.string().min(8, '8 caractères minimum').regex(/\d/, 'Au moins un chiffre'),
    confirmation: z.string(),
    age: z.coerce.number({ message: 'Âge invalide' }).int().min(16, 'Il faut avoir 16 ans'),
    cgu: z.boolean().refine((v) => v, 'Accepte les conditions'),
  })
  .refine((d) => d.motDePasse === d.confirmation, {
    message: 'Les mots de passe sont différents',
    path: ['confirmation'],
  });

export type Inscription = z.infer<typeof inscriptionSchema>;
"""

SCHEMA_FILE = F("schema.ts", "ts", SCHEMA)

INSCR_API = r"""
window.__recu = [];
__api["POST /api/inscriptions"] = (p, body) => { window.__recu.push(body); return [201, { id: 1 }]; };
"""

INSCR_TESTS = r"""
const champ = (n) => $('[name=' + n + ']');
const erreur = (n) => { const e = $('#erreur-' + n); return e ? e.textContent : ''; };
await submit('form');
await tick(150);
assert.equal(erreur('email'), 'Email invalide', 'Soumission vide : « Email invalide »');
assert.equal(erreur('motDePasse'), '8 caractères minimum', 'Soumission vide : « 8 caractères minimum »');
assert.equal(erreur('cgu'), 'Accepte les conditions', 'Soumission vide : « Accepte les conditions »');
assert.equal(window.__recu.length, 0, 'Rien n\'est envoyé tant que le formulaire est invalide');
await type(champ('email'), 'ana@exemple.fr');
await type(champ('motDePasse'), 'secret');
await tick(100);
assert.equal(erreur('email'), '', 'Email corrigé : l\'erreur disparaît');
assert.equal($('#force').textContent, 'Faible', 'Force du mot de passe : « Faible » (moins de 8)');
await type(champ('motDePasse'), 'secret123');
await tick(100);
assert.equal($('#force').textContent, 'Moyen', 'Force : « Moyen » (8 à 11)');
await type(champ('motDePasse'), 'secret123456');
await tick(100);
assert.equal($('#force').textContent, 'Fort', 'Force : « Fort » (12 et plus)');
await type(champ('confirmation'), 'autre');
await blur(champ('confirmation'));
await type(champ('age'), '17');
await click(champ('cgu'));
await submit('form');
await tick(150);
assert.equal(erreur('confirmation'), 'Les mots de passe sont différents', 'Confirmation différente : message sous « confirmation »');
await type(champ('confirmation'), 'secret123456');
await submit('form');
await waitFor(() => /Compte créé/.test(text()), 3000);
assert.equal(window.__recu.length, 1, 'Formulaire valide : envoyé une fois');
const b = window.__recu[0] || {};
assert(b.age === 17, 'L\'âge est envoyé comme un NOMBRE (17), pas une chaîne', 'reçu : ' + JSON.stringify(b.age));
assert(b.email === 'ana@exemple.fr' && b.cgu === true, 'Email et cgu envoyés');
"""

# =========================================================================== 1. Fait main
main = DM("form-main", "Du formulaire fait main aux bibliothèques", 25,
  "Comprendre tout ce qu'un formulaire doit gérer, pour voir exactement ce que React Hook Form et TanStack Form font à ta place.",
  "Tu sais faire un formulaire à la main avec useState. Les bibliothèques semblent « magiques » parce qu'elles cachent ce travail : une fois qu'on l'a fait soi-même, leur API devient logique.",
  ["Stocker les **valeurs**", "Valider et stocker les **erreurs**", "Savoir quels champs ont été **touchés** (pour ne pas crier trop tôt)",
   "Gérer **l'envoi** (en cours, succès, erreur serveur)", "Remettre à zéro ou recharger des valeurs"],
  ["Un formulaire, ce n'est pas que des valeurs : il y a aussi les erreurs, les champs touchés, l'état d'envoi, les erreurs serveur.",
   "On n'affiche pas une erreur sur un champ que l'utilisateur n'a pas encore quitté (ou avant la 1re soumission).",
   "Un **schéma** (zod) décrit les règles une seule fois ; on peut le réutiliser avec RHF, TanStack Form et même côté serveur.",
   "React Hook Form : champs **non contrôlés** (le DOM garde la valeur, RHF la lit via une `ref`).",
   "TanStack Form : champs **contrôlés**, chaque champ est un composant qui lit l'état du formulaire."],
  ["Afficher toutes les erreurs dès l'ouverture du formulaire.", "Oublier de bloquer le bouton pendant l'envoi (double soumission).", "Dupliquer les règles de validation dans chaque formulaire."],
  [Q("Quand afficher l'erreur « Email invalide » ?", ["dès l'ouverture", "quand le champ a été quitté (touché) ou après une tentative d'envoi", "seulement côté serveur", "jamais"], 1, "Sinon on reproche à l'utilisateur ce qu'il n'a pas encore fait."),
   Q("Que fait `z.coerce.number()` avec \"17\" ?", ["erreur", "renvoie 17 (nombre)", "renvoie \"17\"", "renvoie NaN"], 1, "Les champs HTML donnent des chaînes ; coerce convertit."),
   Q("Différence clé entre RHF et TanStack Form ?", ["RHF est payant", "RHF : champs non contrôlés lus par ref ; TanStack : champs contrôlés", "TanStack ne valide pas", "aucune"], 1, "C'est ce qui explique leurs API si différentes.")],
  prereq=[
    P("Champ contrôlé", "La valeur vit dans le state React : `value={state}` + `onChange`. React redessine à chaque frappe."),
    P("Champ non contrôlé", "La valeur vit dans le DOM (l'input lui-même) ; on la lit quand on en a besoin, via une `ref`."),
    P("Touché (touched)", "Un champ que l'utilisateur a quitté au moins une fois (événement blur)."),
    P("Schéma zod", "Un objet qui décrit la forme et les règles des données : `z.object({ email: z.string().email() })`. `safeParse` dit si c'est valide et renvoie les erreurs."),
    P("Dirty", "« Modifié » : la valeur actuelle est différente de la valeur de départ."),
  ],
  diagram=D(
    nodes=[
      N("m", 0, 1, "Formulaire fait main", "useState partout", kind="file", color="muted"),
      N("st", 1, 1, "État du formulaire", "valeurs, erreurs, envoi…", kind="db", color="accent"),
      N("rhf", 2, 0, "React Hook Form", "non contrôlé · register", kind="box", color="warn"),
      N("tsf", 2, 2, "TanStack Form", "contrôlé · form.Field", kind="box", color="good"),
      N("z", 3, 1, "Schéma zod", "les règles, une fois", kind="doc", color="accent"),
    ],
    edges=[E("m", "st", "tu gères tout"), E("st", "rhf"), E("st", "tsf"), E("rhf", "z", dashed=True), E("tsf", "z", dashed=True)],
    caption="Les deux bibliothèques gèrent le même état à ta place, de deux façons différentes ; un schéma zod peut servir aux deux."),
  lessons=[
    L("Tout ce qu'un « simple » formulaire doit gérer", r"""
Ton formulaire fait main ressemble sûrement à ça :

```tsx
const [email, setEmail] = useState('');
const [erreur, setErreur] = useState('');
<input value={email} onChange={(e) => setEmail(e.target.value)} />
```

Pour un vrai formulaire d'entreprise, il faut en plus :

| Besoin | État à gérer |
|---|---|
| les valeurs de chaque champ | `valeurs` |
| les erreurs de validation | `erreurs` (par champ) |
| ne pas afficher d'erreur avant que l'utilisateur ait quitté le champ | `touches` (par champ) |
| tout afficher après une tentative d'envoi | `soumis` |
| bloquer le bouton pendant l'envoi | `enCours` |
| erreurs renvoyées par l'API (« email déjà utilisé ») | erreurs serveur |
| savoir si on a modifié quelque chose (bouton Enregistrer) | `dirty` |
| recharger des valeurs venant de l'API, remettre à zéro | `reset` |
| listes de champs (lignes de facture) | ajout / suppression / index |

Avec 10 champs, ça fait vite 10 `useState`, des `if` partout et des bugs (erreur affichée trop tôt, double envoi…). **C'est exactement ce que font les bibliothèques de formulaires.** Le 1er TD te fait écrire ce travail à la main, pour reconnaître ensuite chaque morceau dans RHF et TanStack Form.
"""),
    L("Les règles dans un schéma (zod)", r"""
Plutôt que des `if` dans le composant, on décrit les règles **une fois**, dans un schéma :

```ts
import { z } from 'zod';

export const inscriptionSchema = z.object({
  email: z.string().trim().email('Email invalide'),
  motDePasse: z.string().min(8, '8 caractères minimum'),
  age: z.coerce.number().int().min(16, 'Il faut avoir 16 ans'),   // "17" → 17
  cgu: z.boolean().refine((v) => v, 'Accepte les conditions'),
}).refine((d) => d.motDePasse === d.confirmation, {
  message: 'Les mots de passe sont différents',
  path: ['confirmation'],                       // l'erreur s'affiche sous ce champ
});

export type Inscription = z.infer<typeof inscriptionSchema>;   // le type TS gratuit
```

- `safeParse(données)` renvoie `{ success: true, data }` (données **nettoyées** : trim, conversions) ou `{ success: false, error }` avec `error.issues` : une liste `{ path: ['email'], message: 'Email invalide' }`.
- `.refine()` sur l'objet entier sert aux règles **entre champs** (confirmation, dates début/fin).
- `z.coerce.number()` convertit la chaîne d'un `<input type="number">` en nombre.

Le même schéma marche avec React Hook Form (`zodResolver`), TanStack Form (directement) et côté serveur Node. (Zod 4 : `z.email()` existe aussi ; en zod 3 les messages se passent pareil.)
"""),
    L("Deux philosophies : non contrôlé (RHF) et contrôlé (TanStack)", r"""
**React Hook Form** laisse la valeur **dans le DOM**. `register('email')` renvoie `{ name, onChange, onBlur, ref }` que tu étales sur l'input. RHF lit la valeur par la `ref` quand il en a besoin (validation, envoi). Conséquence : très peu de re-rendus, une API courte, mais il faut un adaptateur (`Controller`) pour les composants qui n'ont pas d'input natif (sélecteur maison, étoiles…).

```tsx
const { register, handleSubmit, formState: { errors } } = useForm();
<input {...register('email', { required: 'Email requis' })} />
```

**TanStack Form** garde la valeur **dans son store**, et chaque champ est un composant qui la lit (champ **contrôlé**) :

```tsx
const form = useForm({ defaultValues: { email: '' }, onSubmit: ({ value }) => … });
<form.Field name="email" children={(field) => (
  <input value={field.state.value} onChange={(e) => field.handleChange(e.target.value)} onBlur={field.handleBlur} />
)} />
```

Plus verbeux, mais **tout** est explicite et typé (le nom `"email"` est vérifié par TypeScript), et n'importe quel composant peut être un champ.

| | Formulaire fait main | React Hook Form | TanStack Form |
|---|---|---|---|
| valeur | `useState` | DOM (ref) | store du formulaire |
| brancher un input | `value` + `onChange` | `{...register('x')}` | `<form.Field>` + `value` + `handleChange` |
| erreurs | ton state | `formState.errors.x.message` | `field.state.meta.errors` |
| envoi | ton `onSubmit` | `handleSubmit(fn)` | `form.handleSubmit()` + `onSubmit` dans `useForm` |
"""),
  ],
  recap=["Un formulaire gère valeurs, erreurs, champs touchés, envoi, erreurs serveur, dirty, reset.",
         "Erreur visible si le champ est touché ou après une tentative d'envoi.",
         "zod : les règles une fois ; `safeParse`, `.refine` entre champs, `z.coerce.number`.",
         "RHF = non contrôlé (`register`) ; TanStack Form = contrôlé (`form.Field`)."],
  example=F("Newsletter.tsx", "tsx", r"""
import { useState } from 'react';

export default function Newsletter() {
  const [email, setEmail] = useState('');
  const [touche, setTouche] = useState(false);
  const [enCours, setEnCours] = useState(false);
  const erreur = /^\S+@\S+\.\S+$/.test(email) ? '' : 'Email invalide';

  async function envoyer(e: React.FormEvent) {
    e.preventDefault();
    setTouche(true);
    if (erreur) return;
    setEnCours(true);
    await fetch('/api/newsletter', { method: 'POST', body: JSON.stringify({ email }) });
    setEnCours(false);
  }

  return (
    <form onSubmit={envoyer}>
      <input value={email} onChange={(e) => setEmail(e.target.value)} onBlur={() => setTouche(true)} />
      {touche && erreur && <p role="alert">{erreur}</p>}
      <button disabled={enCours}>{enCours ? 'Envoi…' : "S'inscrire"}</button>
    </form>
  );
}
"""),
  notes=["Trois `useState` pour un seul champ : valeur, touché, envoi.", "L'erreur est calculée, mais affichée seulement si le champ est touché.", "Le bouton est bloqué pendant l'envoi."],
  tds=[
    TD(1, "Un formulaire fait main… complet",
       "Ce formulaire d'inscription à la newsletter affiche ses erreurs dès l'ouverture, se soumet deux fois si on clique vite, et ignore les erreurs du serveur. Rends-le propre **à la main** (sans bibliothèque) : c'est exactement le travail que les bibliothèques feront pour toi ensuite." + EX,
       ["Erreurs : prénom vide → `Prénom requis` ; email vide → `Email requis` ; email mal formé → `Email invalide`",
        "Une erreur ne s'affiche que si le champ a été **quitté** (blur) ou après une **tentative d'envoi** ; dans `<p role=\"alert\" id=\"erreur-prenom\">` / `id=\"erreur-email\"`",
        "Pendant l'envoi (`POST /api/newsletter`), le bouton est désactivé et affiche `Envoi…`",
        "Succès → message `Merci Ana !` (avec le prénom) et champs vidés ; réponse **409** → `Déjà inscrit` sous l'email"],
       [F("Newsletter.tsx", "tsx", r"""
import { useState } from 'react';

export default function Newsletter() {
  const [prenom, setPrenom] = useState('');
  const [email, setEmail] = useState('');
  const [merci, setMerci] = useState('');

  const erreurs: Record<string, string> = {};
  if (!prenom) erreurs.prenom = 'Prénom requis';
  if (!email) erreurs.email = 'Email requis';

  async function envoyer(e: React.FormEvent) {
    e.preventDefault();
    await fetch('/api/newsletter', { method: 'POST', body: JSON.stringify({ prenom, email }) });
    setMerci('Merci ' + prenom + ' !');
  }

  return (
    <form onSubmit={envoyer}>
      <label>Prénom <input name="prenom" value={prenom} onChange={(e) => setPrenom(e.target.value)} /></label>
      {erreurs.prenom && <p role="alert" id="erreur-prenom">{erreurs.prenom}</p>}
      <label>Email <input name="email" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
      {erreurs.email && <p role="alert" id="erreur-email">{erreurs.email}</p>}
      <button type="submit">S'inscrire</button>
      {merci && <p>{merci}</p>}
    </form>
  );
}
""")],
       ["Ajoute `const [touches, setTouches] = useState<Record<string, boolean>>({})` et `const [soumis, setSoumis] = useState(false)` ; un champ montre son erreur si `touches.x || soumis`.",
        "`onBlur={() => setTouches((t) => ({ ...t, email: true }))}`. Au submit : `setSoumis(true); if (Object.keys(erreurs).length) return;`",
        "La réponse : `const res = await fetch(…)` ; `if (res.status === 409) { setErreurServeur('Déjà inscrit'); … }`. Pense à `finally { setEnCours(false) }`."],
       [F("Newsletter.tsx", "tsx", r"""
import { useState } from 'react';

export default function Newsletter() {
  const [prenom, setPrenom] = useState('');
  const [email, setEmail] = useState('');
  const [touches, setTouches] = useState<Record<string, boolean>>({});
  const [soumis, setSoumis] = useState(false);
  const [enCours, setEnCours] = useState(false);
  const [erreurServeur, setErreurServeur] = useState('');
  const [merci, setMerci] = useState('');

  const erreurs: Record<string, string> = {};
  if (!prenom.trim()) erreurs.prenom = 'Prénom requis';
  if (!email) erreurs.email = 'Email requis';
  else if (!/^\S+@\S+\.\S+$/.test(email)) erreurs.email = 'Email invalide';

  const visible = (champ: string) => (touches[champ] || soumis ? erreurs[champ] : undefined);
  const toucher = (champ: string) => () => setTouches((t) => ({ ...t, [champ]: true }));

  async function envoyer(e: React.FormEvent) {
    e.preventDefault();
    setSoumis(true);
    setErreurServeur('');
    if (enCours || Object.keys(erreurs).length > 0) return;
    setEnCours(true);
    try {
      const res = await fetch('/api/newsletter', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prenom, email }) });
      if (res.status === 409) {
        setErreurServeur('Déjà inscrit');
        return;
      }
      setMerci('Merci ' + prenom + ' !');
      setPrenom('');
      setEmail('');
      setTouches({});
      setSoumis(false);
    } finally {
      setEnCours(false);
    }
  }

  const erreurEmail = visible('email') || erreurServeur;
  return (
    <form onSubmit={envoyer}>
      <label>Prénom <input name="prenom" value={prenom} onChange={(e) => setPrenom(e.target.value)} onBlur={toucher('prenom')} /></label>
      {visible('prenom') && <p role="alert" id="erreur-prenom">{visible('prenom')}</p>}
      <label>Email <input name="email" value={email} onChange={(e) => { setEmail(e.target.value); setErreurServeur(''); }} onBlur={toucher('email')} /></label>
      {erreurEmail && <p role="alert" id="erreur-email">{erreurEmail}</p>}
      <button type="submit" disabled={enCours}>{enCours ? 'Envoi…' : "S'inscrire"}</button>
      {merci && <p>{merci}</p>}
    </form>
  );
}
""")],
       ["Aucune erreur à l'ouverture", "Une seule requête même avec deux clics"],
       run=FRUN("Newsletter.tsx", api=r"""
window.__envois = 0;
__api["POST /api/newsletter"] = (p, b) => { window.__envois++; return b.email === 'deja@exemple.fr' ? [409, { detail: 'Déjà inscrit' }] : [201, {}]; };
""", tests=r"""
const err = (n) => { const e = $('#erreur-' + n); return e ? e.textContent : ''; };
assert(!$('[role=alert]'), 'Aucune erreur à l\'ouverture');
await type('[name=email]', 'ana');
assert.equal(err('email'), '', 'Pendant la saisie (champ pas encore quitté) : pas d\'erreur');
await blur('[name=email]');
assert.equal(err('email'), 'Email invalide', 'Champ quitté : « Email invalide »');
assert.equal(err('prenom'), '', 'Le prénom (pas touché) ne montre rien');
await submit('form');
assert.equal(err('prenom'), 'Prénom requis', 'Après une tentative d\'envoi : toutes les erreurs');
assert.equal(window.__envois, 0, 'Formulaire invalide : rien n\'est envoyé');
await type('[name=prenom]', 'Ana');
await type('[name=email]', 'ana@exemple.fr');
await submit('form');
await tick(30);
assert($('button').disabled && $('button').textContent === 'Envoi…', 'Pendant l\'envoi : bouton désactivé « Envoi… »');
await submit('form');
await waitFor(() => /Merci Ana !/.test(text()), 3000);
assert.equal(window.__envois, 1, 'Double soumission : une seule requête');
assert($('[name=prenom]').value === '' && $('[name=email]').value === '', 'Succès : champs vidés');
assert(!$('[role=alert]'), 'Succès : pas d\'erreur affichée sur les champs vidés');
await type('[name=prenom]', 'Léo');
await type('[name=email]', 'deja@exemple.fr');
await submit('form');
await waitFor(() => err('email') === 'Déjà inscrit', 3000);
assert.equal(err('email'), 'Déjà inscrit', 'Réponse 409 : « Déjà inscrit » sous l\'email');
""")),
    TD(2, "Les règles dans un schéma zod",
       "Écris le schéma d'inscription qui servira dans les modules suivants (avec React Hook Form **et** TanStack Form), et une petite fonction qui transforme le résultat de zod en `{ champ: message }`. Le bouton Exécuter lance les tests sur ton module.",
       ["`inscriptionSchema` : `email` (espaces retirés, `Email invalide`), `motDePasse` (`8 caractères minimum`, puis `Au moins un chiffre`), `confirmation` (chaîne)",
        "`age` : la chaîne d'un input devient un nombre ; pas un nombre → `Âge invalide` ; entier ≥ 16 sinon `Il faut avoir 16 ans` ; `cgu` doit être `true` (`Accepte les conditions`)",
        "Confirmation différente du mot de passe → `Les mots de passe sont différents`, **sous le champ `confirmation`**",
        "`valider(donnees)` renvoie `{ ok: true, data }` (données converties) ou `{ ok: false, erreurs }` avec **le premier** message de chaque champ"],
       [F("schema.ts", "ts", r"""
import { z } from 'zod';

export const inscriptionSchema = z.object({
  // à toi
});

export type Inscription = z.infer<typeof inscriptionSchema>;

export function valider(donnees: unknown) {
  // à toi : safeParse, puis { ok: true, data } ou { ok: false, erreurs: { champ: message } }
}
""")],
       ["`z.string().trim().email('Email invalide')` ; `z.coerce.number({ message: 'Âge invalide' }).int().min(16, '…')`.",
        "Règle entre champs : `.refine((d) => d.motDePasse === d.confirmation, { message: '…', path: ['confirmation'] })` après `z.object({…})`.",
        "Dans `valider` : `for (const issue of r.error.issues) { const champ = String(issue.path[0]); erreurs[champ] ??= issue.message; }`."],
       [F("schema.ts", "ts", SCHEMA + r"""
export function valider(donnees: unknown) {
  const r = inscriptionSchema.safeParse(donnees);
  if (r.success) return { ok: true as const, data: r.data };
  const erreurs: Record<string, string> = {};
  for (const issue of r.error.issues) {
    const champ = String(issue.path[0]);
    erreurs[champ] ??= issue.message;
  }
  return { ok: false as const, erreurs };
}
""")],
       ["`\"17\"` devient `17`", "La confirmation a son erreur à elle"],
       run=RUN("js", entry="schema.ts", tests=r"""
const { inscriptionSchema, valider } = require('./schema');
const bon = { email: '  ana@exemple.fr ', motDePasse: 'secret123', confirmation: 'secret123', age: '17', cgu: true };
const r = valider(bon);
assert(r.ok === true, 'Données valides → ok: true', JSON.stringify(r));
assert(r.data && r.data.email === 'ana@exemple.fr', 'Email : espaces retirés');
assert(r.data && r.data.age === 17, 'Âge "17" → 17 (nombre)');
const v = valider({ email: 'ana', motDePasse: 'court', confirmation: 'x', age: '15', cgu: false });
assert(v.ok === false, 'Données invalides → ok: false');
const e = v.erreurs || {};
assert.equal(e.email, 'Email invalide', 'email');
assert.equal(e.motDePasse, '8 caractères minimum', 'motDePasse : le PREMIER message seulement');
assert.equal(e.age, 'Il faut avoir 16 ans', 'age < 16');
assert.equal(e.cgu, 'Accepte les conditions', 'cgu');
assert.equal((valider({ ...bon, motDePasse: 'motdepasse' }).erreurs || {}).motDePasse, 'Au moins un chiffre', 'Mot de passe sans chiffre');
assert.equal((valider({ ...bon, age: 'abc' }).erreurs || {}).age, 'Âge invalide', 'Âge non numérique → « Âge invalide »');
assert.equal((valider({ ...bon, age: '16.5' }).erreurs || {}).age !== undefined, true, 'Âge non entier refusé');
const c = valider({ ...bon, confirmation: 'secret124' });
assert(c.ok === false && c.erreurs.confirmation === 'Les mots de passe sont différents', 'Confirmation différente → erreur sous « confirmation »');
assert(inscriptionSchema.safeParse(bon).success === true, 'inscriptionSchema est bien un schéma zod');
""")),
    TD(3, "Écrire son propre mini React Hook Form",
       "Pour démystifier les bibliothèques, écris un hook `useFormulaire` qui fait le travail répétitif du niveau 1. Le formulaire de contact qui l'utilise est fourni : tu ne touches qu'au hook. Tu verras que `register` de RHF et `form.Field` de TanStack ne font rien d'autre." + EX,
       ["`useFormulaire({ valeursInitiales, valider, onSubmit })` renvoie `{ valeurs, erreurs, enCours, champ, handleSubmit }`",
        "`champ(nom)` renvoie `{ name, value, onChange, onBlur }` à étaler sur un `<input>` / `<textarea>`",
        "`erreurs` ne contient que les erreurs des champs **touchés** (toutes après une tentative d'envoi) ; `valider(valeurs)` renvoie `{ champ: message }`",
        "`handleSubmit(e)` : empêche le rechargement ; si aucune erreur, `enCours` passe à `true` pendant `await onSubmit(valeurs)`"],
       [F("useFormulaire.ts", "ts", r"""
import { useState } from 'react';

type Options<V> = {
  valeursInitiales: V;
  valider: (v: V) => Partial<Record<keyof V, string>>;
  onSubmit: (v: V) => Promise<void> | void;
};

export function useFormulaire<V extends Record<string, string>>({ valeursInitiales, valider, onSubmit }: Options<V>) {
  const [valeurs, setValeurs] = useState(valeursInitiales);
  // à toi : touches, soumis, enCours, erreurs visibles, champ(), handleSubmit()

  return { valeurs, erreurs: {} as Partial<Record<keyof V, string>>, enCours: false, champ: (nom: keyof V) => ({}), handleSubmit: (e: any) => e.preventDefault() };
}
"""), F("Contact.tsx", "tsx", r"""
import { useState } from 'react';
import { useFormulaire } from './useFormulaire';

export default function Contact() {
  const [envoye, setEnvoye] = useState(false);
  const f = useFormulaire({
    valeursInitiales: { nom: '', message: '' },
    valider: (v) => ({
      ...(v.nom.trim() ? {} : { nom: 'Nom requis' }),
      ...(v.message.length >= 10 ? {} : { message: '10 caractères minimum' }),
    }),
    onSubmit: async (v) => {
      await fetch('/api/contact', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(v) });
      setEnvoye(true);
    },
  });

  if (envoye) return <p>Message envoyé</p>;
  return (
    <form onSubmit={f.handleSubmit}>
      <label>Nom <input {...f.champ('nom')} /></label>
      {f.erreurs.nom && <p role="alert" id="erreur-nom">{f.erreurs.nom}</p>}
      <label>Message <textarea {...f.champ('message')} /></label>
      {f.erreurs.message && <p role="alert" id="erreur-message">{f.erreurs.message}</p>}
      <button type="submit" disabled={f.enCours}>{f.enCours ? 'Envoi…' : 'Envoyer'}</button>
    </form>
  );
}
""")],
       ["Toutes les erreurs : `const toutes = valider(valeurs);` ; visibles : `Object.fromEntries(Object.entries(toutes).filter(([k]) => touches[k] || soumis))`.",
        "`champ(nom)` : `{ name: nom, value: valeurs[nom], onChange: (e) => setValeurs((v) => ({ ...v, [nom]: e.target.value })), onBlur: () => setTouches((t) => ({ ...t, [nom]: true })) }`.",
        "`handleSubmit` est `async` : `e.preventDefault(); setSoumis(true); if (Object.keys(toutes).length) return; setEnCours(true); try { await onSubmit(valeurs) } finally { setEnCours(false) }`."],
       [F("useFormulaire.ts", "ts", r"""
import { useState } from 'react';

type Options<V> = {
  valeursInitiales: V;
  valider: (v: V) => Partial<Record<keyof V, string>>;
  onSubmit: (v: V) => Promise<void> | void;
};

export function useFormulaire<V extends Record<string, string>>({ valeursInitiales, valider, onSubmit }: Options<V>) {
  const [valeurs, setValeurs] = useState(valeursInitiales);
  const [touches, setTouches] = useState<Partial<Record<keyof V, boolean>>>({});
  const [soumis, setSoumis] = useState(false);
  const [enCours, setEnCours] = useState(false);

  const toutes = valider(valeurs);
  const erreurs = Object.fromEntries(
    Object.entries(toutes).filter(([nom]) => soumis || touches[nom as keyof V]),
  ) as Partial<Record<keyof V, string>>;

  function champ(nom: keyof V) {
    return {
      name: String(nom),
      value: valeurs[nom],
      onChange: (e: { target: { value: string } }) => setValeurs((v) => ({ ...v, [nom]: e.target.value })),
      onBlur: () => setTouches((t) => ({ ...t, [nom]: true })),
    };
  }

  async function handleSubmit(e: { preventDefault: () => void }) {
    e.preventDefault();
    setSoumis(true);
    if (enCours || Object.keys(toutes).length > 0) return;
    setEnCours(true);
    try {
      await onSubmit(valeurs);
    } finally {
      setEnCours(false);
    }
  }

  return { valeurs, erreurs, enCours, champ, handleSubmit };
}
""")],
       ["Le composant Contact n'a presque plus de logique", "Les erreurs suivent la règle « touché ou soumis »"],
       run=FRUN("Contact.tsx", api=r"""
window.__recu = [];
__api["POST /api/contact"] = (p, b) => { window.__recu.push(b); return [201, {}]; };
""", tests=r"""
const err = (n) => { const e = $('#erreur-' + n); return e ? e.textContent : ''; };
assert(!$('[role=alert]'), 'Aucune erreur à l\'ouverture');
await type('[name=nom]', '');
await blur('[name=nom]');
assert.equal(err('nom'), 'Nom requis', 'Nom quitté vide : « Nom requis »');
assert.equal(err('message'), '', 'Message (pas touché) : rien');
await type('textarea', 'Bonjour');
assert.equal($('textarea').value, 'Bonjour', 'champ() relie la valeur au textarea');
await submit('form');
assert.equal(err('message'), '10 caractères minimum', 'Tentative d\'envoi : toutes les erreurs');
assert.equal(window.__recu.length, 0, 'Invalide : rien n\'est envoyé');
await type('[name=nom]', 'Ana');
await type('textarea', 'Bonjour à toute l\'équipe');
assert(!$('[role=alert]'), 'Corrigé : plus d\'erreur');
await submit('form');
await tick(30);
assert($('button') && $('button').disabled && $('button').textContent === 'Envoi…', 'Pendant l\'envoi : bouton désactivé');
await waitFor(() => /Message envoyé/.test(text()), 3000);
assert(window.__recu.length === 1 && window.__recu[0].nom === 'Ana', 'onSubmit reçoit les valeurs');
""")),
  ])

# =========================================================================== 2. RHF bases
rhf = DM("rhf-bases", "React Hook Form : les bases", 30,
  "Écrire des formulaires avec React Hook Form : `register`, `handleSubmit`, `formState`, les règles, zod, les modes de validation, `reset` et les erreurs serveur.",
  "C'est la bibliothèque de formulaires la plus utilisée en React : tu la croiseras dans presque tous les projets d'entreprise.",
  ["`useForm({ defaultValues, mode, resolver })`", "`{...register('champ', règles)}` sur chaque input",
   "`handleSubmit(onValid)` sur le formulaire : ta fonction ne reçoit que des données valides", "Afficher `formState.errors.champ?.message`, utiliser `isSubmitting`, `isDirty`",
   "Erreurs serveur : `setError` ; données chargées : `reset(données)`"],
  ["`register` renvoie `{ name, onChange, onBlur, ref }` : on l'étale avec `{...}`.",
   "`handleSubmit(fn)` valide tout, puis appelle `fn(données)` seulement si c'est valide ; `isSubmitting` reste vrai tant que `fn` (async) n'est pas finie.",
   "Avec zod : `resolver: zodResolver(schema)` ; `fn` reçoit les données **converties** par le schéma.",
   "`mode` : quand valider la 1re fois (`onSubmit` par défaut, `onBlur`, `onTouched`, `onChange`) ; ensuite RHF revalide à chaque frappe.",
   "`defaultValues` toujours complet ; données venant de l'API → `reset(données)`."],
  ["Oublier `defaultValues` (champs `undefined`, `reset` qui ne marche pas).", "Un `<input type=\"number\">` donne une chaîne : `valueAsNumber: true` ou `z.coerce`.", "Lire `formState` sans le déstructurer (RHF ne suit que ce que tu lis)."],
  [Q("`{...register('email')}` ajoute à l'input…", ["value et onChange", "name, onChange, onBlur, ref", "seulement name", "un state React"], 1, "RHF lit la valeur par la ref : l'input reste non contrôlé."),
   Q("`handleSubmit(envoyer)` appelle `envoyer`…", ["toujours", "seulement si le formulaire est valide", "au premier changement", "jamais si mode onBlur"], 1, "Les données invalides n'arrivent jamais dans ta fonction."),
   Q("Les données de l'API arrivent après le 1er rendu. On fait…", ["setValue sur chaque champ", "reset(données)", "un nouveau useForm", "defaultValues dans un useEffect"], 1, "reset remplace les valeurs ET les valeurs de référence (isDirty repart à false).")],
  prereq=[
    P("`register`", "Fonction de RHF qui « inscrit » un input : elle renvoie les props (`name`, `onChange`, `onBlur`, `ref`) à étaler dessus."),
    P("`formState`", "L'état du formulaire : `errors`, `isSubmitting`, `isDirty`, `isValid`, `isSubmitSuccessful`…"),
    P("Resolver", "Un adaptateur qui confie la validation à une bibliothèque de schémas (`zodResolver(schema)`)."),
    P("`mode`", "Moment de la première validation : `onSubmit` (défaut), `onBlur`, `onTouched` (au 1er blur puis à chaque frappe), `onChange`."),
  ],
  diagram=D(
    nodes=[
      N("in", 0, 1, "<input {...register}>", "valeur dans le DOM", kind="file", color="accent"),
      N("rhf", 1, 1, "useForm", "lit par ref · valide", kind="box", color="warn"),
      N("z", 1, 0, "zodResolver(schema)", "règles + conversions", kind="doc"),
      N("err", 2, 0, "formState.errors", "si invalide", kind="note", color="bad"),
      N("ok", 2, 2, "handleSubmit(fn)", "si valide : fn(données)", kind="pill", color="good"),
      N("api", 3, 2, "API", "422 → setError", kind="db", color="muted"),
    ],
    edges=[E("in", "rhf"), E("z", "rhf", dashed=True), E("rhf", "err"), E("rhf", "ok"), E("ok", "api")],
    caption="Les inputs gardent leur valeur ; RHF la lit, valide (avec zod si tu veux) et n'appelle ta fonction qu'avec des données valides."),
  lessons=[
    L("register, handleSubmit, errors", r"""
```tsx
import { useForm } from 'react-hook-form';

type Valeurs = { email: string; motDePasse: string };

export default function Connexion() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Valeurs>({
    defaultValues: { email: '', motDePasse: '' },
  });

  async function envoyer(donnees: Valeurs) {          // appelé SEULEMENT si tout est valide
    await fetch('/api/connexion', { method: 'POST', body: JSON.stringify(donnees) });
  }

  return (
    <form onSubmit={handleSubmit(envoyer)}>
      <input {...register('email', {
        required: 'Email requis',
        pattern: { value: /^\S+@\S+\.\S+$/, message: 'Email invalide' },
      })} />
      {errors.email && <p role="alert">{errors.email.message}</p>}

      <input type="password" {...register('motDePasse', { required: 'Mot de passe requis', minLength: { value: 8, message: '8 caractères minimum' } })} />
      {errors.motDePasse && <p role="alert">{errors.motDePasse.message}</p>}

      <button disabled={isSubmitting}>{isSubmitting ? 'Connexion…' : 'Se connecter'}</button>
    </form>
  );
}
```

Ce qui a disparu par rapport au fait main : les `useState`, les `onChange`, le calcul des erreurs, `e.preventDefault()`, l'état d'envoi. Règles disponibles dans `register` : `required`, `minLength`, `maxLength`, `min`, `max`, `pattern`, `validate: (v) => v !== 'admin' || 'Interdit'`, et `valueAsNumber: true` pour obtenir un nombre.

Par défaut (`mode: 'onSubmit'`), rien n'est validé avant le 1er envoi ; **ensuite**, chaque frappe revalide le champ (`reValidateMode: 'onChange'`) : l'erreur disparaît dès qu'on corrige.
"""),
    L("Avec un schéma zod", r"""
Dès que les règles deviennent sérieuses, on les met dans un schéma et on branche le **resolver** :

```tsx
import { zodResolver } from '@hookform/resolvers/zod';
import { inscriptionSchema, type Inscription } from './schema';

const { register, handleSubmit, watch, formState: { errors } } = useForm({
  resolver: zodResolver(inscriptionSchema),
  mode: 'onTouched',                 // erreur au 1er blur, puis en direct
  defaultValues: { email: '', motDePasse: '', confirmation: '', age: '', cgu: false },
});

const motDePasse = watch('motDePasse');     // relit la valeur à chaque frappe (pour un affichage)
```

- Plus de règles dans `register` : `{...register('email')}` suffit.
- Ta fonction `handleSubmit(envoyer)` reçoit les données **après** le schéma : `age` est déjà un nombre grâce à `z.coerce`.
- L'erreur d'un `.refine` avec `path: ['confirmation']` arrive dans `errors.confirmation`.
- Une case à cocher `{...register('cgu')}` donne un booléen.

`watch('champ')` fait redessiner le composant à chaque frappe sur ce champ : pratique pour afficher la force d'un mot de passe ou un champ qui dépend d'un autre.
"""),
    L("Charger, modifier, erreurs serveur", r"""
Écran « Modifier mon profil » : les données arrivent de l'API **après** le 1er rendu. On ne recrée pas le formulaire : on appelle `reset` :

```tsx
const { register, handleSubmit, reset, setError, formState: { errors, isDirty, isSubmitting } } = useForm<Profil>({
  defaultValues: { prenom: '', email: '' },
});

useEffect(() => {
  fetch('/api/profil').then((r) => r.json()).then((p) => reset(p));    // valeurs + référence
}, [reset]);
```

`reset(p)` change les valeurs **et** les valeurs de référence : `isDirty` (modifié ?) repart à `false`. Le bouton « Enregistrer » peut donc être `disabled={!isDirty || isSubmitting}`.

Erreurs du serveur : on les remet **dans le formulaire**, sous le bon champ :

```tsx
async function enregistrer(p: Profil) {
  const res = await fetch('/api/profil', { method: 'PUT', body: JSON.stringify(p) });
  if (res.status === 422) {
    const probleme = await res.json();
    for (const e of probleme.errors) setError(e.champ, { type: 'server', message: e.message });
    return;
  }
  reset(await res.json());                       // les nouvelles valeurs deviennent la référence
}
```

Pour une erreur qui ne concerne aucun champ : `setError('root.serveur', { message: 'Service indisponible' })`, affichée avec `errors.root?.serveur?.message`.
"""),
  ],
  recap=["`useForm({ defaultValues })` + `{...register('x', règles)}` + `handleSubmit(fn)`.",
         "Erreurs : `formState.errors.x?.message` ; envoi : `isSubmitting`.",
         "zod : `resolver: zodResolver(schema)` ; `fn` reçoit les données converties.",
         "`mode: 'onTouched'` pour valider au 1er blur ; `watch` pour afficher une valeur en direct.",
         "API : `reset(données)` pour charger, `isDirty` pour le bouton, `setError` pour les erreurs serveur."],
  example=F("Connexion.tsx", "tsx", r"""
import { useForm } from 'react-hook-form';

type Valeurs = { email: string; motDePasse: string };

export default function Connexion() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Valeurs>({
    defaultValues: { email: '', motDePasse: '' },
  });

  return (
    <form onSubmit={handleSubmit(async (d) => { await fetch('/api/connexion', { method: 'POST', body: JSON.stringify(d) }); })}>
      <input {...register('email', { required: 'Email requis' })} />
      {errors.email && <p role="alert">{errors.email.message}</p>}
      <input type="password" {...register('motDePasse', { required: 'Mot de passe requis' })} />
      <button disabled={isSubmitting}>Se connecter</button>
    </form>
  );
}
"""),
  notes=["Aucun `useState` : RHF garde l'état.", "Les règles sont données à `register`.", "`handleSubmit` ne laisse passer que des données valides."],
  tds=[
    TD(1, "Une connexion avec React Hook Form",
       "Le formulaire est posé mais rien n'est branché. Utilise React Hook Form pour la validation, l'envoi et les erreurs." + EX,
       ["`useForm` avec `defaultValues` ; chaque input est branché avec `register`",
        "email : `Email requis`, format → `Email invalide` ; mot de passe : `Mot de passe requis`, moins de 8 → `8 caractères minimum` ; dans `<p role=\"alert\" id=\"erreur-email\">` / `id=\"erreur-motDePasse\"`",
        "Envoi : `POST /api/connexion` ; pendant l'envoi, bouton désactivé `Connexion…` ; succès → `Bienvenue Ana` (le `nom` renvoyé)",
        "401 → `Identifiants incorrects` dans `<p role=\"alert\" id=\"erreur-form\">` (avec `setError('root.serveur', …)`)"],
       [F("Connexion.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm } from 'react-hook-form';

type Valeurs = { email: string; motDePasse: string };

export default function Connexion() {
  const [nom, setNom] = useState('');
  // à toi : useForm

  if (nom) return <p>Bienvenue {nom}</p>;
  return (
    <form>
      <label>Email <input name="email" /></label>
      <label>Mot de passe <input name="motDePasse" type="password" /></label>
      <button type="submit">Se connecter</button>
    </form>
  );
}
""")],
       ["`const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm<Valeurs>({ defaultValues: { email: '', motDePasse: '' } });`",
        "`<input {...register('email', { required: 'Email requis', pattern: { value: /^\\S+@\\S+\\.\\S+$/, message: 'Email invalide' } })} />` (le `name` vient de `register`).",
        "Dans la fonction d'envoi : `if (res.status === 401) { setError('root.serveur', { message: 'Identifiants incorrects' }); return; }` puis `errors.root?.serveur?.message`."],
       [F("Connexion.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm } from 'react-hook-form';

type Valeurs = { email: string; motDePasse: string };

export default function Connexion() {
  const [nom, setNom] = useState('');
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm<Valeurs>({
    defaultValues: { email: '', motDePasse: '' },
  });

  async function envoyer(donnees: Valeurs) {
    const res = await fetch('/api/connexion', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(donnees),
    });
    if (res.status === 401) {
      setError('root.serveur', { message: 'Identifiants incorrects' });
      return;
    }
    setNom((await res.json()).nom);
  }

  if (nom) return <p>Bienvenue {nom}</p>;
  return (
    <form onSubmit={handleSubmit(envoyer)}>
      <label>Email <input {...register('email', {
        required: 'Email requis',
        pattern: { value: /^\S+@\S+\.\S+$/, message: 'Email invalide' },
      })} /></label>
      {errors.email && <p role="alert" id="erreur-email">{errors.email.message}</p>}

      <label>Mot de passe <input type="password" {...register('motDePasse', {
        required: 'Mot de passe requis',
        minLength: { value: 8, message: '8 caractères minimum' },
      })} /></label>
      {errors.motDePasse && <p role="alert" id="erreur-motDePasse">{errors.motDePasse.message}</p>}

      {errors.root?.serveur && <p role="alert" id="erreur-form">{errors.root.serveur.message}</p>}
      <button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Connexion…' : 'Se connecter'}</button>
    </form>
  );
}
""")],
       ["Aucun `useState` pour les champs", "L'erreur disparaît dès qu'on corrige"],
       run=FRUN("Connexion.tsx", api=r"""
window.__envois = 0;
__api["POST /api/connexion"] = (p, b) => { window.__envois++; return b.motDePasse === 'motdepasse1' ? { nom: 'Ana' } : [401, { title: 'Unauthorized' }]; };
""", tests=r"""
const err = (n) => { const e = $('#erreur-' + n); return e ? e.textContent : ''; };
assert(/react-hook-form/.test(source('Connexion.tsx')) && /register\(/.test(source('Connexion.tsx')), 'Utilise register de React Hook Form');
assert(!/useState\(['"]{2}\)[\s\S]*useState\(['"]{2}\)[\s\S]*useState\(['"]{2}\)/.test(source('Connexion.tsx')), 'Pas de useState par champ');
await submit('form');
await tick(80);
assert.equal(err('email'), 'Email requis', 'Envoi vide : « Email requis »');
assert.equal(err('motDePasse'), 'Mot de passe requis', 'Envoi vide : « Mot de passe requis »');
assert.equal(window.__envois, 0, 'Invalide : aucun appel API');
await type('[name=email]', 'ana@exemple');
await type('[name=motDePasse]', 'court');
await submit('form');
await tick(80);
assert.equal(err('email'), 'Email invalide', 'Format → « Email invalide »');
assert.equal(err('motDePasse'), '8 caractères minimum', 'Trop court → « 8 caractères minimum »');
await type('[name=email]', 'ana@exemple.fr');
await tick(60);
assert.equal(err('email'), '', 'Après le 1er envoi, corriger fait disparaître l\'erreur');
await type('[name=motDePasse]', 'mauvais12');
await submit('form');
await tick(40);
assert($('button[type=submit]').disabled && $('button[type=submit]').textContent === 'Connexion…', 'Pendant l\'envoi : bouton désactivé « Connexion… »');
await waitFor(() => err('form') !== '', 3000);
assert.equal(err('form'), 'Identifiants incorrects', '401 → « Identifiants incorrects »');
await type('[name=motDePasse]', 'motdepasse1');
await submit('form');
await waitFor(() => /Bienvenue Ana/.test(text()), 3000);
assert.includes(text(), 'Bienvenue Ana', 'Succès : « Bienvenue Ana »');
""")),
    TD(2, "Inscription avec zod et zodResolver",
       "Branche le schéma d'inscription (fourni, c'est celui du module précédent) sur React Hook Form. Valide au premier blur, affiche la force du mot de passe en direct, et envoie l'âge comme un nombre." + EX,
       ["`resolver: zodResolver(inscriptionSchema)`, `mode: 'onTouched'`, `defaultValues` pour les 5 champs (`cgu: false`)",
        "Inputs avec `name` = nom du champ (`email`, `motDePasse`, `confirmation`, `age`, `cgu` en case à cocher) ; erreurs dans `<p role=\"alert\" id=\"erreur-<champ>\">`",
        "`<p id=\"force\">` : longueur du mot de passe < 8 → `Faible`, < 12 → `Moyen`, sinon `Fort` (avec `watch`)",
        "Envoi valide → `POST /api/inscriptions` avec les données **converties** par le schéma, puis `Compte créé`"],
       [SCHEMA_FILE, F("Inscription.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { inscriptionSchema } from './schema';

export default function Inscription() {
  const [cree, setCree] = useState(false);
  // à toi

  if (cree) return <p>Compte créé</p>;
  return (
    <form>
      <label>Email <input name="email" /></label>
      <label>Mot de passe <input name="motDePasse" type="password" /></label>
      <p id="force"></p>
      <label>Confirmation <input name="confirmation" type="password" /></label>
      <label>Âge <input name="age" type="number" /></label>
      <label><input name="cgu" type="checkbox" /> J'accepte les conditions</label>
      <button type="submit">Créer mon compte</button>
    </form>
  );
}
""")],
       ["`const { register, handleSubmit, watch, formState: { errors } } = useForm({ resolver: zodResolver(inscriptionSchema), mode: 'onTouched', defaultValues: { email: '', motDePasse: '', confirmation: '', age: '', cgu: false } });`",
        "`const n = watch('motDePasse').length; const force = n < 8 ? 'Faible' : n < 12 ? 'Moyen' : 'Fort';`",
        "Un petit composant ou une fonction `erreur(nom)` évite de répéter 5 fois `{errors.x && <p role=\"alert\" id=\"erreur-x\">…}`."],
       [SCHEMA_FILE, F("Inscription.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { inscriptionSchema, type Inscription as Donnees } from './schema';

export default function Inscription() {
  const [cree, setCree] = useState(false);
  const { register, handleSubmit, watch, formState: { errors } } = useForm({
    resolver: zodResolver(inscriptionSchema),
    mode: 'onTouched',
    defaultValues: { email: '', motDePasse: '', confirmation: '', age: '' as unknown as number, cgu: false },
  });

  const n = (watch('motDePasse') || '').length;
  const force = n < 8 ? 'Faible' : n < 12 ? 'Moyen' : 'Fort';

  async function envoyer(donnees: Donnees) {
    await fetch('/api/inscriptions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(donnees) });
    setCree(true);
  }

  const erreur = (nom: keyof Donnees) =>
    errors[nom] ? <p role="alert" id={'erreur-' + nom}>{String(errors[nom]?.message)}</p> : null;

  if (cree) return <p>Compte créé</p>;
  return (
    <form onSubmit={handleSubmit(envoyer)}>
      <label>Email <input {...register('email')} /></label>
      {erreur('email')}
      <label>Mot de passe <input type="password" {...register('motDePasse')} /></label>
      <p id="force">{force}</p>
      {erreur('motDePasse')}
      <label>Confirmation <input type="password" {...register('confirmation')} /></label>
      {erreur('confirmation')}
      <label>Âge <input type="number" {...register('age')} /></label>
      {erreur('age')}
      <label><input type="checkbox" {...register('cgu')} /> J'accepte les conditions</label>
      {erreur('cgu')}
      <button type="submit">Créer mon compte</button>
    </form>
  );
}
""")],
       ["Aucune règle dans `register` : tout est dans le schéma", "L'âge arrive en nombre"],
       run=FRUN("Inscription.tsx", api=INSCR_API, tests=r"""
assert(/zodResolver\(/.test(source('Inscription.tsx')), 'Utilise zodResolver');
await type('[name=email]', 'ana');
assert(!$('#erreur-email'), 'mode onTouched : pas d\'erreur pendant la 1re saisie');
await blur('[name=email]');
await tick(80);
assert($('#erreur-email') && $('#erreur-email').textContent === 'Email invalide', 'mode onTouched : erreur au 1er blur');
""" + INSCR_TESTS)),
    TD(3, "Modifier un profil : reset, isDirty, erreurs serveur",
       "L'écran « Mon profil » charge les données depuis l'API, permet de les modifier et affiche les erreurs renvoyées par le serveur sous les bons champs." + EX,
       ["Pendant le chargement (`GET /api/profil`) : `Chargement…` ; ensuite les champs sont remplis avec `reset(données)`",
        "Le bouton `Enregistrer` est désactivé tant que **rien n'a changé** (`isDirty`) ou pendant l'envoi",
        "`PUT /api/profil` → **422** `{ errors: [{ champ, message }] }` : chaque message sous son champ (`<p role=\"alert\" id=\"erreur-<champ>\">`)",
        "Succès → `Enregistré`, et les nouvelles valeurs deviennent la référence (le bouton se désactive à nouveau)"],
       [F("Profil.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';

type Profil = { prenom: string; email: string; ville: string };

export default function Profil() {
  const [charge, setCharge] = useState(false);
  const [message, setMessage] = useState('');
  const { register, handleSubmit, setValue } = useForm<Profil>();

  useEffect(() => {
    fetch('/api/profil').then((r) => r.json()).then((p: Profil) => {
      setValue('prenom', p.prenom);
      setValue('email', p.email);
      setValue('ville', p.ville);
      setCharge(true);
    });
  }, [setValue]);

  async function enregistrer(p: Profil) {
    await fetch('/api/profil', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(p) });
    setMessage('Enregistré');
  }

  if (!charge) return <p>Chargement…</p>;
  return (
    <form onSubmit={handleSubmit(enregistrer)}>
      <label>Prénom <input {...register('prenom')} /></label>
      <label>Email <input {...register('email')} /></label>
      <label>Ville <input {...register('ville')} /></label>
      <button type="submit">Enregistrer</button>
      {message && <p>{message}</p>}
    </form>
  );
}
""")],
       ["`useForm<Profil>({ defaultValues: { prenom: '', email: '', ville: '' } })` puis `reset(p)` à la réception : `isDirty` devient fiable.",
        "Le formulaire doit rester monté pendant le chargement pour que `reset` fonctionne : affiche `Chargement…` à côté (ou garde le `if` mais appelle `reset` après `setCharge`).",
        "422 : `for (const e of (await res.json()).errors) setError(e.champ, { type: 'server', message: e.message });` ; succès : `reset(await res.json())`."],
       [F("Profil.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';

type Profil = { prenom: string; email: string; ville: string };

export default function Profil() {
  const [charge, setCharge] = useState(false);
  const [message, setMessage] = useState('');
  const { register, handleSubmit, reset, setError, formState: { errors, isDirty, isSubmitting } } = useForm<Profil>({
    defaultValues: { prenom: '', email: '', ville: '' },
  });

  useEffect(() => {
    fetch('/api/profil').then((r) => r.json()).then((p: Profil) => {
      reset(p);
      setCharge(true);
    });
  }, [reset]);

  async function enregistrer(p: Profil) {
    setMessage('');
    const res = await fetch('/api/profil', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(p) });
    if (res.status === 422) {
      const probleme = await res.json();
      for (const e of probleme.errors) setError(e.champ as keyof Profil, { type: 'server', message: e.message });
      return;
    }
    reset(await res.json());
    setMessage('Enregistré');
  }

  const erreur = (nom: keyof Profil) => errors[nom] && <p role="alert" id={'erreur-' + nom}>{errors[nom]?.message}</p>;

  return (
    <form onSubmit={handleSubmit(enregistrer)} hidden={!charge}>
      {!charge && <p>Chargement…</p>}
      <label>Prénom <input {...register('prenom')} /></label>
      {erreur('prenom')}
      <label>Email <input {...register('email')} /></label>
      {erreur('email')}
      <label>Ville <input {...register('ville')} /></label>
      {erreur('ville')}
      <button type="submit" disabled={!isDirty || isSubmitting}>Enregistrer</button>
      {message && <p>{message}</p>}
    </form>
  );
}
""")],
       ["Le bouton suit `isDirty`", "Les erreurs 422 vont sous leurs champs"],
       run=FRUN("Profil.tsx", api=r"""
window.__profil = { prenom: 'Ana', email: 'ana@exemple.fr', ville: 'Lyon' };
window.__puts = 0;
__api["GET /api/profil"] = () => window.__profil;
__api["PUT /api/profil"] = (p, b) => {
  window.__puts++;
  const errors = [];
  if (b.email === 'leo@exemple.fr') errors.push({ champ: 'email', message: 'Email déjà utilisé' });
  if (b.ville.length < 2) errors.push({ champ: 'ville', message: 'Ville trop courte' });
  if (errors.length) return [422, { title: 'Données invalides', errors }];
  window.__profil = Object.assign({}, b, { prenom: b.prenom.trim() });
  return window.__profil;
};
""", tests=r"""
const err = (n) => { const e = $('#erreur-' + n); return e ? e.textContent : ''; };
const bouton = () => $('button[type=submit]');
assert(/Chargement/.test(text()), 'Pendant le chargement : « Chargement… »');
await waitFor(() => $('[name=prenom]') && $('[name=prenom]').value === 'Ana', 3000);
assert.equal($('[name=ville]').value, 'Lyon', 'Champs remplis avec les données de l\'API');
assert(bouton().disabled, 'Rien modifié : Enregistrer désactivé');
await type('[name=ville]', 'Lyo');
assert(!bouton().disabled, 'Après une modification : Enregistrer actif');
await type('[name=ville]', 'Lyon');
assert(bouton().disabled, 'Retour à la valeur d\'origine : de nouveau désactivé (isDirty)');
await type('[name=email]', 'leo@exemple.fr');
await type('[name=ville]', 'L');
await submit('form');
await waitFor(() => err('email') !== '', 3000);
assert.equal(err('email'), 'Email déjà utilisé', '422 : message sous l\'email');
assert.equal(err('ville'), 'Ville trop courte', '422 : message sous la ville');
await type('[name=email]', 'ana.b@exemple.fr');
await type('[name=ville]', 'Lille');
await submit('form');
await waitFor(() => /Enregistré/.test(text()), 3000);
assert.equal(window.__puts, 2, 'Deux envois en tout');
assert(bouton().disabled, 'Après succès : les nouvelles valeurs sont la référence (bouton désactivé)');
assert.equal($('[name=ville]').value, 'Lille', 'La valeur enregistrée reste affichée');
""")),
  ])

# =========================================================================== 3. RHF avancé
ETOILES = r"""
// Fourni par la bibliothèque de composants de l'entreprise : AUCUN <input> à l'intérieur
export function Etoiles({ value, onChange, onBlur }: { value: number; onChange: (n: number) => void; onBlur?: () => void }) {
  return (
    <div role="radiogroup" aria-label="Note" onBlur={onBlur}>
      {[1, 2, 3, 4, 5].map((n) => (
        <button type="button" key={n} aria-label={n + ' étoiles'} aria-pressed={n <= value} onClick={() => onChange(n)}>
          {n <= value ? '★' : '☆'}
        </button>
      ))}
    </div>
  );
}

export function Interrupteur({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button type="button" role="switch" aria-checked={checked} onClick={() => onChange(!checked)}>
      {label} : {checked ? 'oui' : 'non'}
    </button>
  );
}
"""

rhf2 = DM("rhf-avance", "React Hook Form : composants maison, listes, gros formulaires", 30,
  "Brancher des composants qui ne sont pas des inputs (`Controller`), gérer des listes de champs (`useFieldArray`) et découper un gros formulaire en composants (`FormProvider`).",
  "Les formulaires d'entreprise ont des sélecteurs maison, des lignes à ajouter et des sections réutilisées (adresses…). C'est là que `register` seul ne suffit plus.",
  ["Composant sans input natif → `<Controller render={({ field }) => …} />`", "Liste de champs → `useFieldArray` : `fields`, `append`, `remove`, `key={field.id}`",
   "Valeur calculée (total) → `useWatch`", "Gros formulaire → `<FormProvider {...methods}>` + `useFormContext()` dans les sous-composants"],
  ["`register` a besoin d'un vrai input (il pose une `ref`) ; sinon c'est `Controller`.",
   "`Controller` donne `field.value`, `field.onChange`, `field.onBlur` : on les passe au composant maison.",
   "Dans une liste, la clé React est `field.id` (jamais l'index) et le nom `lignes.${i}.quantite`.",
   "`useWatch({ control, name })` redessine seulement là où on en a besoin.",
   "`FormProvider` évite de passer `register` et `errors` en props sur trois niveaux."],
  ["`{...register('note')}` sur un composant maison (rien ne se passe).", "`key={index}` dans une liste (les valeurs se mélangent à la suppression).", "Oublier `valueAsNumber` : `quantite` vaut `\"2\"`."],
  [Q("Un composant `<Etoiles value onChange />` sans input :", ["register", "Controller", "useFieldArray", "watch"], 1, "Controller fait le pont entre RHF et un composant contrôlé."),
   Q("Clé React dans `fields.map` :", ["index", "field.id", "field.nom", "Math.random()"], 1, "field.id est stable même quand on supprime une ligne."),
   Q("Un sous-composant <Adresse /> doit utiliser register :", ["le passer en props partout", "useFormContext() sous un FormProvider", "un 2e useForm", "impossible"], 1, "Le contexte partage le formulaire.")],
  prereq=[
    P("`Controller`", "Composant de RHF qui branche un composant **contrôlé** (value + onChange) sur le formulaire."),
    P("`useFieldArray`", "Hook de RHF pour une liste de groupes de champs : `fields` (avec un `id` stable), `append`, `remove`, `move`…"),
    P("`useWatch`", "Lit des valeurs du formulaire et redessine quand elles changent (version ciblée de `watch`)."),
    P("`FormProvider` / `useFormContext`", "Partage l'objet du formulaire avec tous les composants enfants, sans props."),
  ],
  diagram=D(
    nodes=[
      N("f", 0, 1, "useForm()", "methods", kind="box", color="warn"),
      N("fp", 1, 1, "<FormProvider>", "partage methods", kind="box"),
      N("c", 2, 0, "<Controller>", "composant maison", kind="pill", color="accent"),
      N("fa", 3, 1, "useFieldArray", "+ useWatch (total)", kind="pill", color="accent"),
      N("ctx", 2, 2, "useFormContext()", "<Adresse />", kind="pill", color="accent"),
    ],
    edges=[E("f", "fp"), E("fp", "c"), E("fp", "fa"), E("fp", "ctx")],
    caption="Un seul useForm, partagé par FormProvider ; chaque besoin a son outil."),
  lessons=[
    L("Controller : brancher un composant maison", r"""
`register` pose une `ref` sur un input natif et écoute ses événements. Un composant comme `<Etoiles value onChange />` (des boutons) ou un sélecteur de date d'une librairie UI n'a **pas** d'input : il faut `Controller`.

```tsx
<Controller
  name="note"
  control={control}
  rules={{ validate: (v) => v > 0 || 'Choisis une note' }}
  render={({ field, fieldState }) => (
    <>
      <Etoiles value={field.value} onChange={field.onChange} onBlur={field.onBlur} />
      {fieldState.error && <p role="alert">{fieldState.error.message}</p>}
    </>
  )}
/>
```

`field.onChange` accepte une valeur directement (`onChange(4)`) ou un événement. Variante en hook : `const { field } = useController({ name: 'note', control })`.

C'est le même principe que TanStack Form pour **tous** les champs : value + onChange.
"""),
    L("useFieldArray : des lignes à ajouter et supprimer", r"""
```tsx
const { control, register } = useForm({
  defaultValues: { lignes: [{ designation: '', quantite: 1, prix: 0 }] },
});
const { fields, append, remove } = useFieldArray({ control, name: 'lignes' });

{fields.map((field, i) => (
  <div key={field.id}>                                        {/* id stable, PAS i */}
    <input {...register(`lignes.${i}.designation`)} />
    <input type="number" {...register(`lignes.${i}.quantite`, { valueAsNumber: true })} />
    <button type="button" onClick={() => remove(i)}>Supprimer</button>
  </div>
))}
<button type="button" onClick={() => append({ designation: '', quantite: 1, prix: 0 })}>Ajouter une ligne</button>
```

- Le nom d'un champ de liste : `lignes.${i}.quantite` (avec des points).
- Les erreurs : `errors.lignes?.[i]?.designation?.message`.
- `fields` ne contient pas les valeurs **à jour** (seulement celles de départ) : pour un total, on lit les valeurs avec `useWatch({ control, name: 'lignes' })`.
- Les boutons de la liste ont `type="button"`, sinon ils soumettent le formulaire.
"""),
    L("FormProvider : découper un gros formulaire", r"""
Un formulaire de commande avec deux adresses identiques en structure : on écrit **un** composant `<Adresse prefixe="livraison" />` et on le réutilise.

```tsx
// Commande.tsx
const methods = useForm<Commande>({ defaultValues });
return (
  <FormProvider {...methods}>
    <form onSubmit={methods.handleSubmit(envoyer)}>
      <Adresse prefixe="livraison" />
      {!memeAdresse && <Adresse prefixe="facturation" />}
    </form>
  </FormProvider>
);

// Adresse.tsx
export function Adresse({ prefixe }: { prefixe: 'livraison' | 'facturation' }) {
  const { register, formState: { errors } } = useFormContext<Commande>();
  return <input {...register(`${prefixe}.rue`)} />;
}
```

Pour un champ qui dépend d'un autre (la case « même adresse »), `watch('memeAdresse')` dans le parent. La règle « facturation obligatoire seulement si décochée » se met dans le schéma zod avec `.superRefine` (ou `z.discriminatedUnion`).
"""),
  ],
  recap=["Composant maison → `Controller` (`field.value`, `field.onChange`).",
         "Liste → `useFieldArray`, `key={field.id}`, noms `liste.${i}.champ`.",
         "Total en direct → `useWatch`.",
         "Gros formulaire → `FormProvider` + `useFormContext`.",
         "Règles conditionnelles → `superRefine` dans le schéma."],
  example=F("Avis.tsx", "tsx", r"""
import { Controller, useForm } from 'react-hook-form';
import { Etoiles } from './ui';

export default function Avis() {
  const { control, handleSubmit } = useForm({ defaultValues: { note: 0 } });
  return (
    <form onSubmit={handleSubmit(console.log)}>
      <Controller
        name="note"
        control={control}
        render={({ field }) => <Etoiles value={field.value} onChange={field.onChange} />}
      />
    </form>
  );
}
"""),
  notes=["`Controller` remplace `register` pour un composant sans input.", "`field.onChange(4)` met la note à 4."],
  tds=[
    TD(1, "Controller : des étoiles et un interrupteur",
       "Le formulaire d'avis utilise deux composants de la bibliothèque UI de l'entreprise (fournis dans `ui.tsx`), qui n'ont **aucun** input. Le code actuel fait `{...register(...)}` dessus : la note et l'interrupteur ne sont jamais enregistrés. Corrige avec `Controller`." + EX,
       ["`note` (0 au départ) avec `Etoiles` via `Controller` ; note à 0 à l'envoi → `Choisis une note` dans `<p role=\"alert\" id=\"erreur-note\">`",
        "`recommande` (false au départ) avec `Interrupteur` via `Controller`",
        "`commentaire` reste un `<textarea>` avec `register` (au moins 5 caractères → sinon `5 caractères minimum`, `id=\"erreur-commentaire\"`)",
        "Envoi valide → `POST /api/avis` avec `{ note, recommande, commentaire }`, puis `Merci pour ton avis`"],
       [F("ui.tsx", "tsx", ETOILES), F("Avis.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Etoiles, Interrupteur } from './ui';

type Avis = { note: number; recommande: boolean; commentaire: string };

export default function Avis() {
  const [merci, setMerci] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm<Avis>({
    defaultValues: { note: 0, recommande: false, commentaire: '' },
  });

  async function envoyer(a: Avis) {
    await fetch('/api/avis', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(a) });
    setMerci(true);
  }

  if (merci) return <p>Merci pour ton avis</p>;
  return (
    <form onSubmit={handleSubmit(envoyer)}>
      <Etoiles {...(register('note') as any)} />
      <Interrupteur label="Je recommande" {...(register('recommande') as any)} />
      <textarea {...register('commentaire')} />
      <button type="submit">Envoyer</button>
    </form>
  );
}
""")],
       ["Récupère `control` dans `useForm`, puis `<Controller name=\"note\" control={control} rules={{ validate: (v) => v > 0 || 'Choisis une note' }} render={({ field }) => <Etoiles value={field.value} onChange={field.onChange} onBlur={field.onBlur} />} />`.",
        "Pour l'interrupteur : `render={({ field }) => <Interrupteur label=\"Je recommande\" checked={field.value} onChange={field.onChange} />}`.",
        "Le commentaire : `register('commentaire', { minLength: { value: 5, message: '5 caractères minimum' } })`."],
       [F("ui.tsx", "tsx", ETOILES), F("Avis.tsx", "tsx", r"""
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { Etoiles, Interrupteur } from './ui';

type Avis = { note: number; recommande: boolean; commentaire: string };

export default function Avis() {
  const [merci, setMerci] = useState(false);
  const { control, register, handleSubmit, formState: { errors } } = useForm<Avis>({
    defaultValues: { note: 0, recommande: false, commentaire: '' },
  });

  async function envoyer(a: Avis) {
    await fetch('/api/avis', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(a) });
    setMerci(true);
  }

  if (merci) return <p>Merci pour ton avis</p>;
  return (
    <form onSubmit={handleSubmit(envoyer)}>
      <Controller
        name="note"
        control={control}
        rules={{ validate: (v) => v > 0 || 'Choisis une note' }}
        render={({ field }) => <Etoiles value={field.value} onChange={field.onChange} onBlur={field.onBlur} />}
      />
      {errors.note && <p role="alert" id="erreur-note">{errors.note.message}</p>}

      <Controller
        name="recommande"
        control={control}
        render={({ field }) => <Interrupteur label="Je recommande" checked={field.value} onChange={field.onChange} />}
      />

      <textarea {...register('commentaire', { minLength: { value: 5, message: '5 caractères minimum' } })} />
      {errors.commentaire && <p role="alert" id="erreur-commentaire">{errors.commentaire.message}</p>}
      <button type="submit">Envoyer</button>
    </form>
  );
}
""")],
       ["Cliquer sur une étoile change la note", "La note 0 est refusée"],
       run=FRUN("Avis.tsx", api=r"""
window.__recu = [];
__api["POST /api/avis"] = (p, b) => { window.__recu.push(b); return [201, {}]; };
""", tests=r"""
const err = (n) => { const e = $('#erreur-' + n); return e ? e.textContent : ''; };
await type('textarea', 'Top');
await submit('form');
await tick(100);
assert.equal(err('note'), 'Choisis une note', 'Note à 0 : « Choisis une note »');
assert.equal(err('commentaire'), '5 caractères minimum', 'Commentaire trop court');
await click('[aria-label="4 étoiles"]');
assert.equal($$('[aria-pressed=true]').length, 4, 'Cliquer « 4 étoiles » : 4 étoiles allumées (la valeur revient au composant)');
assert.equal(err('note'), '', 'Note choisie : l\'erreur disparaît');
await click('[role=switch]');
assert.equal($('[role=switch]').getAttribute('aria-checked'), 'true', 'L\'interrupteur passe à oui');
await type('textarea', 'Très bon produit');
await submit('form');
await waitFor(() => /Merci pour ton avis/.test(text()), 3000);
const b = window.__recu[0] || {};
assert(b.note === 4, 'Envoyé : note = 4', JSON.stringify(b));
assert(b.recommande === true, 'Envoyé : recommande = true');
assert(b.commentaire === 'Très bon produit', 'Envoyé : commentaire');
""")),
    TD(2, "useFieldArray : les lignes d'une facture",
       "Écris le formulaire de facture : un client, et des lignes qu'on peut ajouter et supprimer, avec le total en direct." + EX,
       ["`defaultValues` : `client: ''`, `lignes` avec **une** ligne `{ designation: '', quantite: 1, prix: 0 }` ; chaque ligne dans un `<div class=\"ligne\">`",
        "Inputs `name` : `client`, `lignes.<i>.designation`, `lignes.<i>.quantite`, `lignes.<i>.prix` (nombres : `valueAsNumber`) ; bouton `Supprimer` par ligne (désactivé s'il ne reste qu'une ligne) ; bouton `Ajouter une ligne`",
        "`<p id=\"total\">Total : 25.00 €</p>` (somme quantité × prix, 2 décimales), mis à jour pendant la saisie",
        "Validation : client requis (`Client requis`, `id=\"erreur-client\"`), désignation requise (`Désignation requise`, dans un `<p class=\"erreur\">` de la ligne) ; envoi → `POST /api/factures` puis `Facture enregistrée`"],
       [F("Facture.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm, useFieldArray, useWatch } from 'react-hook-form';

type Ligne = { designation: string; quantite: number; prix: number };
type Facture = { client: string; lignes: Ligne[] };

export default function Facture() {
  const [ok, setOk] = useState(false);
  // à toi

  if (ok) return <p>Facture enregistrée</p>;
  return <form></form>;
}
""")],
       ["`const { fields, append, remove } = useFieldArray({ control, name: 'lignes' });` puis `fields.map((field, i) => <div className=\"ligne\" key={field.id}>…</div>)`.",
        "`const lignes = useWatch({ control, name: 'lignes' }); const total = (lignes || []).reduce((t, l) => t + (Number(l.quantite) || 0) * (Number(l.prix) || 0), 0);`",
        "Erreur d'une ligne : `errors.lignes?.[i]?.designation?.message`. Les boutons de la liste ont `type=\"button\"`."],
       [F("Facture.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm, useFieldArray, useWatch } from 'react-hook-form';

type Ligne = { designation: string; quantite: number; prix: number };
type Facture = { client: string; lignes: Ligne[] };

const LIGNE_VIDE: Ligne = { designation: '', quantite: 1, prix: 0 };

export default function Facture() {
  const [ok, setOk] = useState(false);
  const { control, register, handleSubmit, formState: { errors } } = useForm<Facture>({
    defaultValues: { client: '', lignes: [LIGNE_VIDE] },
  });
  const { fields, append, remove } = useFieldArray({ control, name: 'lignes' });
  const lignes = useWatch({ control, name: 'lignes' });
  const total = (lignes || []).reduce((t, l) => t + (Number(l.quantite) || 0) * (Number(l.prix) || 0), 0);

  async function envoyer(f: Facture) {
    await fetch('/api/factures', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(f) });
    setOk(true);
  }

  if (ok) return <p>Facture enregistrée</p>;
  return (
    <form onSubmit={handleSubmit(envoyer)}>
      <label>Client <input {...register('client', { required: 'Client requis' })} /></label>
      {errors.client && <p role="alert" id="erreur-client">{errors.client.message}</p>}

      {fields.map((field, i) => (
        <div className="ligne" key={field.id}>
          <input placeholder="Désignation" {...register(`lignes.${i}.designation`, { required: 'Désignation requise' })} />
          <input type="number" {...register(`lignes.${i}.quantite`, { valueAsNumber: true, min: 1 })} />
          <input type="number" step="0.01" {...register(`lignes.${i}.prix`, { valueAsNumber: true, min: 0 })} />
          <button type="button" onClick={() => remove(i)} disabled={fields.length === 1}>Supprimer</button>
          {errors.lignes?.[i]?.designation && <p className="erreur">{errors.lignes[i]?.designation?.message}</p>}
        </div>
      ))}
      <button type="button" onClick={() => append(LIGNE_VIDE)}>Ajouter une ligne</button>

      <p id="total">Total : {total.toFixed(2)} €</p>
      <button type="submit">Enregistrer</button>
    </form>
  );
}
""")],
       ["Le total suit la saisie", "Supprimer une ligne ne mélange pas les autres"],
       run=FRUN("Facture.tsx", api=r"""
window.__recu = [];
__api["POST /api/factures"] = (p, b) => { window.__recu.push(b); return [201, { id: 1 }]; };
""", tests=r"""
const lignes = () => $$('.ligne');
const btn = (t) => Array.from(document.querySelectorAll('button')).find((b) => b.textContent.trim() === t);
assert.equal(lignes().length, 1, 'Une ligne au départ');
assert(btn('Supprimer') && btn('Supprimer').disabled, 'Une seule ligne : Supprimer désactivé');
await type('[name="lignes.0.designation"]', 'Clavier');
await type('[name="lignes.0.quantite"]', '2');
await type('[name="lignes.0.prix"]', '12.5');
assert.equal($('#total').textContent, 'Total : 25.00 €', 'Total en direct : 2 × 12.5 = 25.00 €');
await click(btn('Ajouter une ligne'));
assert.equal(lignes().length, 2, '« Ajouter une ligne » ajoute une ligne');
await type('[name="lignes.1.designation"]', 'Souris');
await type('[name="lignes.1.quantite"]', '3');
await type('[name="lignes.1.prix"]', '10');
assert.equal($('#total').textContent, 'Total : 55.00 €', 'Total : 25 + 30 = 55.00 €');
await click(btn('Ajouter une ligne'));
await type('[name="lignes.2.designation"]', 'Écran');
await click(lignes()[1].querySelector('button'));
assert.equal(lignes().length, 2, 'Supprimer la ligne du milieu');
assert.equal($('[name="lignes.1.designation"]').value, 'Écran', 'Après suppression, la 3e ligne remonte avec SA valeur (key = field.id)');
await type('[name="lignes.1.designation"]', '');
await submit('form');
await tick(100);
assert.equal($('#erreur-client') && $('#erreur-client').textContent, 'Client requis', 'Client vide : « Client requis »');
assert(lignes()[1].querySelector('.erreur') && lignes()[1].querySelector('.erreur').textContent === 'Désignation requise', 'Désignation vide : erreur dans la ligne');
assert.equal(window.__recu.length, 0, 'Invalide : rien envoyé');
await type('[name=client]', 'ACME');
await type('[name="lignes.1.designation"]', 'Écran');
await submit('form');
await waitFor(() => /Facture enregistrée/.test(text()), 3000);
const f = window.__recu[0] || { lignes: [] };
assert(f.client === 'ACME' && f.lignes.length === 2, 'Envoyé : client + 2 lignes', JSON.stringify(f));
assert(f.lignes[0].quantite === 2 && f.lignes[0].prix === 12.5, 'Quantité et prix envoyés en nombres');
""")),
    TD(3, "FormProvider : un composant Adresse réutilisé",
       "Le formulaire de commande a deux adresses (livraison, facturation) avec les mêmes champs. Écris le composant `Adresse` **une fois** (il utilise `useFormContext`), et le formulaire qui l'utilise deux fois. La facturation n'apparaît que si la case « même adresse » est décochée." + EX,
       ["`Adresse({ prefixe })` : inputs `<prefixe>.rue`, `<prefixe>.codePostal`, `<prefixe>.ville` ; erreurs dans `<p role=\"alert\" id=\"erreur-<prefixe>-<champ>\">` (ex. `erreur-livraison-codePostal`)",
        "Le schéma `commandeSchema` est fourni : rue requise, code postal à 5 chiffres, ville requise ; facturation obligatoire **seulement** si `memeAdresse` est décochée",
        "Case `memeAdresse` (cochée au départ) ; décochée → la 2e adresse s'affiche (`watch`)",
        "Envoi → `POST /api/commandes` avec `{ livraison, facturation }` : si même adresse, `facturation` = copie de `livraison` ; puis `Commande validée`"],
       [F("schema.ts", "ts", r"""
import { z } from 'zod';

export const adresseSchema = z.object({
  rue: z.string().min(1, 'Rue requise'),
  codePostal: z.string().regex(/^\d{5}$/, 'Code postal à 5 chiffres'),
  ville: z.string().min(1, 'Ville requise'),
});

const adresseLibre = z.object({ rue: z.string(), codePostal: z.string(), ville: z.string() });

export const commandeSchema = z
  .object({ livraison: adresseSchema, memeAdresse: z.boolean(), facturation: adresseLibre })
  .superRefine((c, ctx) => {
    if (c.memeAdresse) return;
    const r = adresseSchema.safeParse(c.facturation);
    if (!r.success) for (const i of r.error.issues) ctx.addIssue({ code: 'custom', message: i.message, path: ['facturation', ...i.path] });
  });

export type Commande = z.infer<typeof commandeSchema>;
export const ADRESSE_VIDE = { rue: '', codePostal: '', ville: '' };
"""), F("Adresse.tsx", "tsx", r"""
import type { Commande } from './schema';

export function Adresse({ prefixe }: { prefixe: 'livraison' | 'facturation' }) {
  // à toi : useFormContext<Commande>()
  return <fieldset><legend>{prefixe}</legend></fieldset>;
}
"""), F("Commande.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { commandeSchema, ADRESSE_VIDE, type Commande as Donnees } from './schema';
import { Adresse } from './Adresse';

export default function Commande() {
  const [ok, setOk] = useState(false);
  const methods = useForm<Donnees>({
    resolver: zodResolver(commandeSchema),
    defaultValues: { livraison: ADRESSE_VIDE, memeAdresse: true, facturation: ADRESSE_VIDE },
  });

  // à toi : FormProvider, case memeAdresse, envoi

  if (ok) return <p>Commande validée</p>;
  return (
    <form>
      <Adresse prefixe="livraison" />
      <button type="submit">Commander</button>
    </form>
  );
}
""")],
       ["Dans `Adresse` : `const { register, formState: { errors } } = useFormContext<Commande>();` puis `register(`${prefixe}.rue`)` et `errors[prefixe]?.rue?.message`.",
        "Dans `Commande` : `<FormProvider {...methods}><form onSubmit={methods.handleSubmit(envoyer)}>…</form></FormProvider>` ; `const meme = methods.watch('memeAdresse');`",
        "À l'envoi : `const corps = { livraison: c.livraison, facturation: c.memeAdresse ? c.livraison : c.facturation };`"],
       [F("schema.ts", "ts", r"""
import { z } from 'zod';

export const adresseSchema = z.object({
  rue: z.string().min(1, 'Rue requise'),
  codePostal: z.string().regex(/^\d{5}$/, 'Code postal à 5 chiffres'),
  ville: z.string().min(1, 'Ville requise'),
});

const adresseLibre = z.object({ rue: z.string(), codePostal: z.string(), ville: z.string() });

export const commandeSchema = z
  .object({ livraison: adresseSchema, memeAdresse: z.boolean(), facturation: adresseLibre })
  .superRefine((c, ctx) => {
    if (c.memeAdresse) return;
    const r = adresseSchema.safeParse(c.facturation);
    if (!r.success) for (const i of r.error.issues) ctx.addIssue({ code: 'custom', message: i.message, path: ['facturation', ...i.path] });
  });

export type Commande = z.infer<typeof commandeSchema>;
export const ADRESSE_VIDE = { rue: '', codePostal: '', ville: '' };
"""), F("Adresse.tsx", "tsx", r"""
import { useFormContext } from 'react-hook-form';
import type { Commande } from './schema';

const CHAMPS = [
  ['rue', 'Rue'],
  ['codePostal', 'Code postal'],
  ['ville', 'Ville'],
] as const;

export function Adresse({ prefixe }: { prefixe: 'livraison' | 'facturation' }) {
  const { register, formState: { errors } } = useFormContext<Commande>();
  return (
    <fieldset>
      <legend>{prefixe === 'livraison' ? 'Adresse de livraison' : 'Adresse de facturation'}</legend>
      {CHAMPS.map(([champ, label]) => {
        const message = errors[prefixe]?.[champ]?.message;
        return (
          <div key={champ}>
            <label>{label} <input {...register(`${prefixe}.${champ}`)} /></label>
            {message && <p role="alert" id={`erreur-${prefixe}-${champ}`}>{message}</p>}
          </div>
        );
      })}
    </fieldset>
  );
}
"""), F("Commande.tsx", "tsx", r"""
import { useState } from 'react';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { commandeSchema, ADRESSE_VIDE, type Commande as Donnees } from './schema';
import { Adresse } from './Adresse';

export default function Commande() {
  const [ok, setOk] = useState(false);
  const methods = useForm<Donnees>({
    resolver: zodResolver(commandeSchema),
    defaultValues: { livraison: ADRESSE_VIDE, memeAdresse: true, facturation: ADRESSE_VIDE },
  });
  const meme = methods.watch('memeAdresse');

  async function envoyer(c: Donnees) {
    const corps = { livraison: c.livraison, facturation: c.memeAdresse ? c.livraison : c.facturation };
    await fetch('/api/commandes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps) });
    setOk(true);
  }

  if (ok) return <p>Commande validée</p>;
  return (
    <FormProvider {...methods}>
      <form onSubmit={methods.handleSubmit(envoyer)}>
        <Adresse prefixe="livraison" />
        <label><input type="checkbox" {...methods.register('memeAdresse')} /> Même adresse de facturation</label>
        {!meme && <Adresse prefixe="facturation" />}
        <button type="submit">Commander</button>
      </form>
    </FormProvider>
  );
}
""")],
       ["Un seul composant Adresse, utilisé deux fois", "La facturation n'est exigée que si elle est affichée"],
       run=FRUN("Commande.tsx", api=r"""
window.__recu = [];
__api["POST /api/commandes"] = (p, b) => { window.__recu.push(b); return [201, {}]; };
""", tests=r"""
const err = (id) => { const e = $('#erreur-' + id); return e ? e.textContent : ''; };
assert(/useFormContext/.test(source('Adresse.tsx')), 'Adresse utilise useFormContext');
assert(!$('[name="facturation.rue"]'), 'Case cochée au départ : pas d\'adresse de facturation');
await submit('form');
await tick(120);
assert.equal(err('livraison-rue'), 'Rue requise', 'Livraison vide : « Rue requise »');
assert.equal(err('livraison-codePostal'), 'Code postal à 5 chiffres', 'Livraison vide : code postal');
await type('[name="livraison.rue"]', '3 rue des Lilas');
await type('[name="livraison.codePostal"]', '69001');
await type('[name="livraison.ville"]', 'Lyon');
await click('[name=memeAdresse]');
assert($('[name="facturation.rue"]'), 'Décochée : l\'adresse de facturation apparaît');
await submit('form');
await tick(120);
assert.equal(err('facturation-ville'), 'Ville requise', 'Facturation affichée et vide : erreurs');
assert.equal(window.__recu.length, 0, 'Invalide : rien envoyé');
await click('[name=memeAdresse]');
await submit('form');
await waitFor(() => /Commande validée/.test(text()), 3000);
const c = window.__recu[0] || {};
assert(c.livraison && c.livraison.ville === 'Lyon', 'Envoyé : livraison');
assert(c.facturation && c.facturation.rue === '3 rue des Lilas', 'Même adresse : facturation = copie de livraison', JSON.stringify(c));
""")),
  ])

# =========================================================================== 4. TanStack bases
tsf = DM("tsf-bases", "TanStack Form : les bases", 30,
  "Écrire des formulaires avec TanStack Form : `useForm`, `form.Field`, les validateurs par moment (`onChange`, `onBlur`, `onSubmit`), `form.Subscribe`, zod, la validation asynchrone et les erreurs serveur.",
  "TanStack Form est plus verbeux que React Hook Form, mais tout y est explicite et typé. Une fois le « render prop » de `form.Field` compris, le reste suit.",
  ["`useForm({ defaultValues, onSubmit, validators })`", "Chaque champ : `<form.Field name=\"x\" children={(field) => …} />`",
   "Dans le champ : `field.state.value`, `field.handleChange(v)`, `field.handleBlur`, `field.state.meta.errors`, `isTouched`",
   "État global (bouton, total) : `<form.Subscribe selector={(s) => …}>`", "Le `<form>` appelle `form.handleSubmit()` (après `preventDefault`)"],
  ["Les champs sont **contrôlés** : `value={field.state.value}` + `onChange={(e) => field.handleChange(e.target.value)}`.",
   "Un validateur renvoie un **message** (erreur) ou `undefined` (valide) ; on choisit le moment : `onChange`, `onBlur`, `onSubmit`, et leurs versions `…Async`.",
   "`field.state.meta.errors` est un **tableau** ; avec zod ce sont des objets `{ message }`.",
   "`onSubmit` reçoit les valeurs **brutes** (pas converties par zod) : on fait `schema.parse(value)` si besoin.",
   "`form.Subscribe` / `useStore` : seul ce morceau se redessine quand la sélection change."],
  ["Oublier `onBlur={field.handleBlur}` (les validateurs onBlur ne partent jamais).", "Croire que le 1er clic sur Envoyer revalide tout : si un champ est déjà en erreur, `handleSubmit` s'arrête (voir `canSubmitWhenInvalid`).", "Afficher `field.state.meta.errors` directement (tableau d'objets) au lieu de leurs messages.", "Oublier `e.preventDefault()` avant `form.handleSubmit()`."],
  [Q("Comment un champ TanStack met à jour sa valeur ?", ["register", "field.handleChange(valeur)", "setValue", "automatiquement"], 1, "Le champ est contrôlé : c'est toi qui appelles handleChange."),
   Q("Un validateur valide renvoie…", ["true", "undefined", "null obligatoirement", "''"], 1, "Une valeur (message) = erreur ; undefined = OK."),
   Q("Pour désactiver le bouton pendant l'envoi :", ["useState", "form.Subscribe selector={(s) => s.isSubmitting}", "field.state", "watch"], 1, "Subscribe lit l'état du formulaire sans tout redessiner.")],
  prereq=[
    P("Render prop", "Un composant qui reçoit une **fonction** comme enfant : `children={(field) => <input … />}`. TanStack Form l'appelle avec l'objet du champ."),
    P("`field.state.meta`", "Les métadonnées d'un champ : `errors`, `isTouched`, `isDirty`, `isValidating`…"),
    P("Validateur", "Fonction `({ value }) => message | undefined`, attachée à un moment (`onChange`, `onBlur`, `onSubmit`) ; version async + `…AsyncDebounceMs`."),
    P("Standard Schema", "Interface commune aux bibliothèques de schémas (zod, valibot…) : TanStack Form accepte directement un schéma zod comme validateur."),
  ],
  diagram=D(
    nodes=[
      N("uf", 0, 1, "useForm", "defaultValues, onSubmit", kind="box", color="good"),
      N("v", 0, 0, "validators", "onChange, onBlur…", kind="doc", color="warn"),
      N("st", 1, 1, "Store", "values, meta, errors", kind="db", color="accent"),
      N("fd", 2, 0, "<form.Field>", "lit et écrit sa valeur", kind="pill", color="accent"),
      N("sb", 2, 2, "<form.Subscribe>", "isSubmitting, total…", kind="pill", color="accent"),
      N("api", 3, 1, "onSubmit({ value })", "après handleSubmit", kind="db", color="muted"),
    ],
    edges=[E("uf", "st"), E("v", "uf", dashed=True), E("st", "fd"), E("st", "sb"), E("st", "api")],
    caption="Tout passe par le store : les champs lisent et écrivent leur valeur, Subscribe lit l'état global, onSubmit reçoit les valeurs."),
  lessons=[
    L("useForm et form.Field", r"""
```tsx
import { useForm } from '@tanstack/react-form';

export default function Connexion() {
  const form = useForm({
    defaultValues: { email: '', motDePasse: '' },
    onSubmit: async ({ value }) => {                       // seulement si tout est valide
      await fetch('/api/connexion', { method: 'POST', body: JSON.stringify(value) });
    },
  });

  return (
    <form onSubmit={(e) => { e.preventDefault(); form.handleSubmit(); }}>
      <form.Field
        name="email"                                       // vérifié par TypeScript
        validators={{
          onBlur: ({ value }) => (!value ? 'Email requis' : !/^\S+@\S+\.\S+$/.test(value) ? 'Email invalide' : undefined),
        }}
        children={(field) => (
          <>
            <input
              name={field.name}
              value={field.state.value}
              onBlur={field.handleBlur}
              onChange={(e) => field.handleChange(e.target.value)}
            />
            {field.state.meta.isTouched && field.state.meta.errors.length > 0 && (
              <p role="alert">{field.state.meta.errors.join(', ')}</p>
            )}
          </>
        )}
      />
      <form.Subscribe
        selector={(s) => [s.canSubmit, s.isSubmitting]}
        children={([canSubmit, isSubmitting]) => (
          <button type="submit" disabled={!canSubmit || isSubmitting}>{isSubmitting ? 'Connexion…' : 'Se connecter'}</button>
        )}
      />
    </form>
  );
}
```

À comparer avec React Hook Form : `register('email', règles)` devient un `form.Field` avec `value`/`onChange`/`onBlur` écrits à la main, les règles deviennent des **validateurs** attachés à un moment, et le bouton lit l'état via `form.Subscribe`.

À l'envoi, `handleSubmit` marque tous les champs comme touchés et lance **tous** les validateurs (onChange, onBlur, onSubmit).

**Piège** : si un champ a **déjà** une erreur au moment du 1er clic (`canSubmit` est faux), TanStack Form s'arrête là, sans revalider les autres champs (un 2e clic le fait). Si tu veux que le 1er clic montre toutes les erreurs, ajoute `canSubmitWhenInvalid: true` dans `useForm`, ou désactive le bouton avec `canSubmit`.

Et `mode: 'onTouched'` de RHF n'existe pas : on l'obtient en validant en `onChange` et en n'affichant l'erreur que si `field.state.meta.isBlurred` (ou après un envoi, `submissionAttempts > 0`).
"""),
    L("Valider avec zod, dépendances entre champs", r"""
Un schéma zod peut servir de validateur pour **tout** le formulaire :

```tsx
const form = useForm({
  defaultValues: { email: '', motDePasse: '', confirmation: '', age: '', cgu: false },
  validators: { onChange: inscriptionSchema },       // erreurs réparties dans chaque champ
  onSubmit: async ({ value }) => {
    const donnees = inscriptionSchema.parse(value);    // ← conversions (age "17" → 17)
    await fetch('/api/inscriptions', { method: 'POST', body: JSON.stringify(donnees) });
  },
});
```

Deux différences importantes avec RHF :

- avec zod, `field.state.meta.errors` contient des **objets** (`{ message, path, code }`) : on affiche `errors.map((e) => e?.message ?? e)` ;
- `onSubmit` reçoit les valeurs **telles que saisies**, pas les données transformées par le schéma : si tu as `z.coerce` ou `.trim()`, fais `schema.parse(value)`.

Un champ qui dépend d'un autre (confirmation du mot de passe) avec des validateurs de champ : `onChangeListenTo: ['motDePasse']` relance la validation de la confirmation quand le mot de passe change.

Lire une valeur pour l'afficher (force du mot de passe) : `<form.Subscribe selector={(s) => s.values.motDePasse}>` ou `useStore(form.store, (s) => s.values.motDePasse)`.
"""),
    L("Validation asynchrone et erreurs serveur", r"""
Vérifier qu'un pseudo est libre en appelant l'API, sans l'appeler à chaque lettre :

```tsx
<form.Field
  name="pseudo"
  validators={{
    onChange: ({ value }) => (value.length < 3 ? '3 caractères minimum' : undefined),   // d'abord le sync
    onChangeAsyncDebounceMs: 300,                                                          // attend 300 ms sans frappe
    onChangeAsync: async ({ value }) => {
      const r = await fetch(`/api/pseudos/${encodeURIComponent(value)}`).then((r) => r.json());
      return r.disponible ? undefined : 'Ce pseudo est déjà pris';
    },
  }}
  children={(field) => (
    <>
      <input value={field.state.value} onChange={(e) => field.handleChange(e.target.value)} />
      {field.state.meta.isValidating && <span>Vérification…</span>}
    </>
  )}
/>
```

Le validateur async ne part que si le validateur sync est passé. Pendant l'appel, `field.state.meta.isValidating` est vrai.

Erreurs renvoyées par le serveur **à l'envoi** : un validateur `onSubmitAsync` au niveau du formulaire peut faire l'appel et renvoyer des erreurs par champ :

```tsx
validators: {
  onSubmitAsync: async ({ value }) => {
    const res = await fetch('/api/comptes', { method: 'POST', body: JSON.stringify(value) });
    if (res.status === 422) {
      const p = await res.json();
      return { fields: Object.fromEntries(p.errors.map((e) => [e.champ, e.message])) };
    }
    return undefined;                   // OK → onSubmit est appelé ensuite
  },
},
```

`{ form: 'message' }` donne une erreur globale, lue avec `form.Subscribe selector={(s) => s.errorMap.onSubmit}`.
"""),
  ],
  recap=["`useForm({ defaultValues, onSubmit })` ; `<form onSubmit={(e) => { e.preventDefault(); form.handleSubmit(); }}>`.",
         "`<form.Field name children={(field) => …}>` : `value`, `handleChange`, `handleBlur`, `meta.errors`, `meta.isTouched`.",
         "Validateurs par moment : `onChange`, `onBlur`, `onSubmit`, `…Async` + `…AsyncDebounceMs`.",
         "zod : erreurs = objets `{ message }` ; `onSubmit` reçoit les valeurs brutes → `schema.parse`.",
         "État global : `form.Subscribe` ; erreurs serveur : `onSubmitAsync` → `{ fields, form }`."],
  example=F("Connexion.tsx", "tsx", r"""
import { useForm } from '@tanstack/react-form';

export default function Connexion() {
  const form = useForm({
    defaultValues: { email: '' },
    onSubmit: async ({ value }) => { await fetch('/api/connexion', { method: 'POST', body: JSON.stringify(value) }); },
  });

  return (
    <form onSubmit={(e) => { e.preventDefault(); form.handleSubmit(); }}>
      <form.Field
        name="email"
        validators={{ onBlur: ({ value }) => (!value ? 'Email requis' : undefined) }}
        children={(field) => (
          <>
            <input value={field.state.value} onBlur={field.handleBlur} onChange={(e) => field.handleChange(e.target.value)} />
            {field.state.meta.errors.length > 0 && <p role="alert">{field.state.meta.errors.join(', ')}</p>}
          </>
        )}
      />
      <button type="submit">Se connecter</button>
    </form>
  );
}
"""),
  notes=["Le champ est contrôlé : `value` + `handleChange`.", "Le validateur onBlur part quand on quitte le champ (grâce à `handleBlur`).", "`handleSubmit` valide tout avant d'appeler `onSubmit`."],
  tds=[
    TD(1, "La même connexion, avec TanStack Form",
       "C'est **le même** formulaire que dans le module React Hook Form (mêmes messages, même API), pour comparer. Écris-le avec TanStack Form." + EX,
       ["`useForm` avec `defaultValues` et `onSubmit` ; deux `form.Field` (`email`, `motDePasse`) avec inputs contrôlés et `name`",
        "email (validateur **onBlur**) : `Email requis` / `Email invalide` ; mot de passe (validateur **onChange**) : `Mot de passe requis` / `8 caractères minimum` ; erreur affichée si le champ est touché, dans `<p role=\"alert\" id=\"erreur-<champ>\">`",
        "Bouton via `form.Subscribe` : désactivé et `Connexion…` pendant l'envoi",
        "401 → `Identifiants incorrects` dans `<p role=\"alert\" id=\"erreur-form\">` ; succès → `Bienvenue Ana`"],
       [F("Connexion.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm } from '@tanstack/react-form';

export default function Connexion() {
  const [nom, setNom] = useState('');
  const [erreurServeur, setErreurServeur] = useState('');
  // à toi : useForm

  if (nom) return <p>Bienvenue {nom}</p>;
  return (
    <form>
      <label>Email <input name="email" /></label>
      <label>Mot de passe <input name="motDePasse" type="password" /></label>
      <button type="submit">Se connecter</button>
    </form>
  );
}
""")],
       ["`const form = useForm({ defaultValues: { email: '', motDePasse: '' }, onSubmit: async ({ value }) => { … } });`",
        "Pour ne pas répéter l'affichage : `const Erreur = ({ field }: { field: any }) => field.state.meta.isTouched && field.state.meta.errors.length ? <p role=\"alert\" id={'erreur-' + field.name}>{field.state.meta.errors[0]}</p> : null;`",
        "`<form.Subscribe selector={(s) => s.isSubmitting} children={(enCours) => <button type=\"submit\" disabled={enCours}>…</button>} />`"],
       [F("Connexion.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm } from '@tanstack/react-form';

function Erreur({ field }: { field: any }) {
  const { isTouched, errors } = field.state.meta;
  if (!isTouched || errors.length === 0) return null;
  return <p role="alert" id={'erreur-' + field.name}>{String(errors[0])}</p>;
}

export default function Connexion() {
  const [nom, setNom] = useState('');
  const [erreurServeur, setErreurServeur] = useState('');
  const form = useForm({
    defaultValues: { email: '', motDePasse: '' },
    onSubmit: async ({ value }) => {
      setErreurServeur('');
      const res = await fetch('/api/connexion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(value),
      });
      if (res.status === 401) {
        setErreurServeur('Identifiants incorrects');
        return;
      }
      setNom((await res.json()).nom);
    },
  });

  if (nom) return <p>Bienvenue {nom}</p>;
  return (
    <form onSubmit={(e) => { e.preventDefault(); form.handleSubmit(); }}>
      <form.Field
        name="email"
        validators={{
          onBlur: ({ value }) => (!value ? 'Email requis' : !/^\S+@\S+\.\S+$/.test(value) ? 'Email invalide' : undefined),
        }}
        children={(field) => (
          <>
            <label>Email <input name={field.name} value={field.state.value} onBlur={field.handleBlur} onChange={(e) => field.handleChange(e.target.value)} /></label>
            <Erreur field={field} />
          </>
        )}
      />
      <form.Field
        name="motDePasse"
        validators={{
          onChange: ({ value }) => (!value ? 'Mot de passe requis' : value.length < 8 ? '8 caractères minimum' : undefined),
        }}
        children={(field) => (
          <>
            <label>Mot de passe <input type="password" name={field.name} value={field.state.value} onBlur={field.handleBlur} onChange={(e) => field.handleChange(e.target.value)} /></label>
            <Erreur field={field} />
          </>
        )}
      />
      {erreurServeur && <p role="alert" id="erreur-form">{erreurServeur}</p>}
      <form.Subscribe
        selector={(s) => s.isSubmitting}
        children={(enCours) => <button type="submit" disabled={enCours}>{enCours ? 'Connexion…' : 'Se connecter'}</button>}
      />
    </form>
  );
}
""")],
       ["Mêmes messages que la version React Hook Form", "Le moment de validation est choisi par champ"],
       run=FRUN("Connexion.tsx", api=r"""
window.__envois = 0;
__api["POST /api/connexion"] = (p, b) => { window.__envois++; return b.motDePasse === 'motdepasse1' ? { nom: 'Ana' } : [401, { title: 'Unauthorized' }]; };
""", tests=r"""
const err = (n) => { const e = $('#erreur-' + n); return e ? e.textContent : ''; };
assert(/@tanstack\/react-form/.test(source('Connexion.tsx')) && /form\.Field/.test(source('Connexion.tsx')), 'Utilise form.Field de TanStack Form');
assert(!$('[role=alert]'), 'Aucune erreur à l\'ouverture');
await submit('form');
await tick(100);
assert.equal(err('email'), 'Email requis', 'Envoi vide : « Email requis »');
assert.equal(err('motDePasse'), 'Mot de passe requis', 'Envoi vide : « Mot de passe requis »');
assert.equal(window.__envois, 0, 'Invalide : aucun appel API');
await type('[name=email]', 'ana');
assert.equal(err('email'), 'Email requis', 'Email (validateur onBlur) : le message ne change pas pendant la saisie');
await blur('[name=email]');
assert.equal(err('email'), 'Email invalide', 'Email quitté : « Email invalide »');
await type('[name=motDePasse]', 'abc');
assert.equal(err('motDePasse'), '8 caractères minimum', 'Mot de passe (validateur onChange) : erreur en direct');
await type('[name=email]', 'ana@exemple.fr');
await blur('[name=email]');
await type('[name=motDePasse]', 'mauvais12');
await submit('form');
await tick(40);
assert($('button[type=submit]').disabled && $('button[type=submit]').textContent === 'Connexion…', 'Pendant l\'envoi : « Connexion… » désactivé');
await waitFor(() => err('form') !== '', 3000);
assert.equal(err('form'), 'Identifiants incorrects', '401 → « Identifiants incorrects »');
await type('[name=motDePasse]', 'motdepasse1');
await submit('form');
await waitFor(() => /Bienvenue Ana/.test(text()), 3000);
assert.includes(text(), 'Bienvenue Ana', 'Succès : « Bienvenue Ana »');
""")),
    TD(2, "L'inscription avec un schéma zod",
       "Même inscription qu'avec React Hook Form, même schéma fourni : branche-le comme validateur du formulaire TanStack. Attention aux deux différences : les erreurs sont des objets, et `onSubmit` reçoit les valeurs brutes." + EX,
       ["`validators: { onChange: inscriptionSchema }` sur le formulaire ; 5 `form.Field` (`email`, `motDePasse`, `confirmation`, `age`, `cgu` en case à cocher avec `checked`)",
        "Erreur affichée si le champ est touché : le **message** de la 1re erreur, dans `<p role=\"alert\" id=\"erreur-<champ>\">`",
        "`<p id=\"force\">` (`Faible` < 8, `Moyen` < 12, `Fort`) lu avec `form.Subscribe`",
        "`onSubmit` : envoie `inscriptionSchema.parse(value)` (l'âge en **nombre**) à `POST /api/inscriptions`, puis `Compte créé`"],
       [SCHEMA_FILE, F("Inscription.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm } from '@tanstack/react-form';
import { inscriptionSchema } from './schema';

export default function Inscription() {
  const [cree, setCree] = useState(false);
  // à toi

  if (cree) return <p>Compte créé</p>;
  return (
    <form>
      <button type="submit">Créer mon compte</button>
    </form>
  );
}
""")],
       ["`defaultValues: { email: '', motDePasse: '', confirmation: '', age: '', cgu: false }` ; la case : `checked={field.state.value} onChange={(e) => field.handleChange(e.target.checked)}`.",
        "Message : `const e = field.state.meta.errors[0]; const message = typeof e === 'string' ? e : e?.message;`",
        "Un petit composant `Champ({ name, label, type })` qui rend `<form.Field name={name} children={…} />` évite de tout écrire 4 fois."],
       [SCHEMA_FILE, F("Inscription.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm } from '@tanstack/react-form';
import { inscriptionSchema } from './schema';

type Nom = 'email' | 'motDePasse' | 'confirmation' | 'age';

function message(errors: unknown[]) {
  const e = errors[0] as any;
  return typeof e === 'string' ? e : e?.message;
}

export default function Inscription() {
  const [cree, setCree] = useState(false);
  const form = useForm({
    defaultValues: { email: '', motDePasse: '', confirmation: '', age: '', cgu: false },
    validators: { onChange: inscriptionSchema },
    onSubmit: async ({ value }) => {
      const donnees = inscriptionSchema.parse(value);
      await fetch('/api/inscriptions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(donnees) });
      setCree(true);
    },
  });

  const champ = (name: Nom, label: string, type = 'text') => (
    <form.Field
      name={name}
      children={(field) => (
        <>
          <label>{label} <input type={type} name={name} value={field.state.value} onBlur={field.handleBlur} onChange={(e) => field.handleChange(e.target.value)} /></label>
          {field.state.meta.isTouched && field.state.meta.errors.length > 0 && <p role="alert" id={'erreur-' + name}>{message(field.state.meta.errors)}</p>}
        </>
      )}
    />
  );

  if (cree) return <p>Compte créé</p>;
  return (
    <form onSubmit={(e) => { e.preventDefault(); form.handleSubmit(); }}>
      {champ('email', 'Email')}
      {champ('motDePasse', 'Mot de passe', 'password')}
      <form.Subscribe
        selector={(s) => s.values.motDePasse.length}
        children={(n) => <p id="force">{n < 8 ? 'Faible' : n < 12 ? 'Moyen' : 'Fort'}</p>}
      />
      {champ('confirmation', 'Confirmation', 'password')}
      {champ('age', 'Âge', 'number')}
      <form.Field
        name="cgu"
        children={(field) => (
          <>
            <label><input type="checkbox" name="cgu" checked={field.state.value} onBlur={field.handleBlur} onChange={(e) => field.handleChange(e.target.checked)} /> J'accepte les conditions</label>
            {field.state.meta.isTouched && field.state.meta.errors.length > 0 && <p role="alert" id="erreur-cgu">{message(field.state.meta.errors)}</p>}
          </>
        )}
      />
      <button type="submit">Créer mon compte</button>
    </form>
  );
}
""")],
       ["Le même schéma qu'avec React Hook Form", "`schema.parse(value)` pour les conversions"],
       run=FRUN("Inscription.tsx", api=INSCR_API, tests=r"""
assert(/inscriptionSchema/.test(source('Inscription.tsx')) && /@tanstack\/react-form/.test(source('Inscription.tsx')), 'TanStack Form + le schéma');
""" + INSCR_TESTS)),
    TD(3, "Pseudo disponible ? Validation async et erreurs serveur",
       "Le formulaire de création de compte vérifie que le pseudo est libre **pendant la saisie** (sans appeler l'API à chaque lettre), et affiche sous les bons champs les erreurs renvoyées par le serveur à l'envoi." + EX,
       ["`pseudo` : moins de 3 caractères → `3 caractères minimum` (sync) ; sinon, après **300 ms** sans frappe, `GET /api/pseudos/<pseudo>` → `{ disponible }` ; pris → `Ce pseudo est déjà pris`",
        "Pendant la vérification : `<span id=\"verif\">Vérification…</span>`",
        "`email` requis (`Email requis`) ; erreurs dans `<p role=\"alert\" id=\"erreur-<champ>\">` si touché",
        "Envoi (`onSubmitAsync` du formulaire) : `POST /api/comptes` ; **422** `{ errors: [{ champ, message }] }` → chaque message sous son champ ; succès → `Compte créé`"],
       [F("Compte.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm } from '@tanstack/react-form';

export default function Compte() {
  const [cree, setCree] = useState(false);
  const form = useForm({
    defaultValues: { pseudo: '', email: '' },
    onSubmit: async () => setCree(true),
  });

  if (cree) return <p>Compte créé</p>;
  return (
    <form onSubmit={(e) => { e.preventDefault(); form.handleSubmit(); }}>
      <form.Field
        name="pseudo"
        validators={{
          onChange: async ({ value }) => {
            const r = await fetch('/api/pseudos/' + value).then((r) => r.json());
            return r.disponible ? undefined : 'Ce pseudo est déjà pris';
          },
        }}
        children={(field) => (
          <label>Pseudo <input name="pseudo" value={field.state.value} onChange={(e) => field.handleChange(e.target.value)} /></label>
        )}
      />
      <form.Field
        name="email"
        children={(field) => (
          <label>Email <input name="email" value={field.state.value} onChange={(e) => field.handleChange(e.target.value)} /></label>
        )}
      />
      <button type="submit">Créer</button>
    </form>
  );
}
""")],
       ["Sépare : `onChange` (sync, longueur) + `onChangeAsyncDebounceMs: 300` + `onChangeAsync` (l'appel API).",
        "`{field.state.meta.isValidating && <span id=\"verif\">Vérification…</span>}`",
        "`validators: { onSubmitAsync: async ({ value }) => { const res = await fetch('/api/comptes', …); if (res.status === 422) { const p = await res.json(); return { fields: Object.fromEntries(p.errors.map((e: any) => [e.champ, e.message])) }; } } }`"],
       [F("Compte.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm } from '@tanstack/react-form';

function Erreur({ field }: { field: any }) {
  const { isTouched, errors } = field.state.meta;
  if (!isTouched || errors.length === 0) return null;
  return <p role="alert" id={'erreur-' + field.name}>{String(errors[0])}</p>;
}

export default function Compte() {
  const [cree, setCree] = useState(false);
  const form = useForm({
    defaultValues: { pseudo: '', email: '' },
    validators: {
      onSubmitAsync: async ({ value }) => {
        const res = await fetch('/api/comptes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(value) });
        if (res.status === 422) {
          const p = await res.json();
          return { fields: Object.fromEntries(p.errors.map((e: { champ: string; message: string }) => [e.champ, e.message])) };
        }
        return undefined;
      },
    },
    onSubmit: async () => setCree(true),
  });

  if (cree) return <p>Compte créé</p>;
  return (
    <form onSubmit={(e) => { e.preventDefault(); form.handleSubmit(); }}>
      <form.Field
        name="pseudo"
        validators={{
          onChange: ({ value }) => (value.length < 3 ? '3 caractères minimum' : undefined),
          onChangeAsyncDebounceMs: 300,
          onChangeAsync: async ({ value }) => {
            const r = await fetch('/api/pseudos/' + encodeURIComponent(value)).then((r) => r.json());
            return r.disponible ? undefined : 'Ce pseudo est déjà pris';
          },
        }}
        children={(field) => (
          <>
            <label>Pseudo <input name="pseudo" value={field.state.value} onBlur={field.handleBlur} onChange={(e) => field.handleChange(e.target.value)} /></label>
            {field.state.meta.isValidating && <span id="verif">Vérification…</span>}
            <Erreur field={field} />
          </>
        )}
      />
      <form.Field
        name="email"
        validators={{ onChange: ({ value }) => (!value ? 'Email requis' : undefined) }}
        children={(field) => (
          <>
            <label>Email <input name="email" value={field.state.value} onBlur={field.handleBlur} onChange={(e) => field.handleChange(e.target.value)} /></label>
            <Erreur field={field} />
          </>
        )}
      />
      <form.Subscribe
        selector={(s) => s.isSubmitting}
        children={(enCours) => <button type="submit" disabled={enCours}>{enCours ? 'Création…' : 'Créer'}</button>}
      />
    </form>
  );
}
""")],
       ["Une seule requête pour « anabelle » tapé d'un coup", "Les erreurs serveur arrivent sous les champs"],
       run=FRUN("Compte.tsx", api=r"""
window.__verifs = [];
window.__comptes = 0;
__api["GET /api/pseudos/:pseudo"] = (p) => { window.__verifs.push(p.pseudo); return { disponible: !['ana', 'anabelle'].includes(decodeURIComponent(p.pseudo)) }; };
__api["POST /api/comptes"] = (p, b) => { window.__comptes++; return b.email === 'pris@exemple.fr' ? [422, { title: 'Données invalides', errors: [{ champ: 'email', message: 'Email déjà utilisé' }] }] : [201, { id: 1 }]; };
""", tests=r"""
const err = (n) => { const e = $('#erreur-' + n); return e ? e.textContent : ''; };
await type('[name=pseudo]', 'an');
assert.equal(err('pseudo'), '3 caractères minimum', 'Moins de 3 caractères : erreur immédiate');
assert.equal(window.__verifs.length, 0, '… sans appel API');
for (const p of ['ana', 'anab', 'anabe', 'anabel', 'anabell', 'anabelle']) await type('[name=pseudo]', p);
await tick(150);
assert($('#verif'), 'Pendant l\'attente/la vérification : « Vérification… »');
await waitFor(() => err('pseudo') === 'Ce pseudo est déjà pris', 3000);
assert.equal(window.__verifs.length, 1, 'Saisie rapide : UN seul appel (debounce 300 ms)', 'appels : ' + JSON.stringify(window.__verifs));
assert.equal(window.__verifs[0], 'anabelle', '… avec la dernière valeur');
assert(!$('#verif'), 'Fin de vérification : plus de « Vérification… »');
await type('[name=pseudo]', 'zoe42');
await waitFor(() => window.__verifs.length === 2 && !$('#verif'), 3000);
await tick(50);
assert.equal(err('pseudo'), '', 'Pseudo libre : pas d\'erreur');
await type('[name=email]', 'pris@exemple.fr');
await submit('form');
await waitFor(() => err('email') !== '', 3000);
assert.equal(err('email'), 'Email déjà utilisé', '422 : « Email déjà utilisé » sous l\'email');
assert(!/Compte créé/.test(text()), '422 : le compte n\'est pas créé');
await type('[name=email]', 'zoe@exemple.fr');
await submit('form');
await waitFor(() => /Compte créé/.test(text()), 3000);
assert.equal(window.__comptes, 2, 'Deux envois au serveur');
""")),
  ])

# =========================================================================== 5. TanStack avancé
tsf2 = DM("tsf-avance", "TanStack Form : listes, champs liés et composants de champ", 30,
  "Gérer des listes de champs, des champs qui dépendent d'autres, et surtout le pattern utilisé en entreprise : `createFormHook` avec des composants de champ réutilisables.",
  "Écrire `value`/`onChange`/`onBlur`/erreurs dans chaque `form.Field` devient vite répétitif. En entreprise, on crée une fois des composants (`TextField`, `SubmitButton`) branchés sur TanStack Form : c'est probablement ce que tu vois dans ton projet.",
  ["Liste : `<form.Field name=\"lignes\" mode=\"array\">` + `pushValue` / `removeValue` + sous-champs `lignes[${i}].prix`",
   "Champ lié : `listeners: { onChange }` pour réagir (vider la ville quand le pays change)",
   "Composants de champ : `createFormHookContexts` + `createFormHook` → `useAppForm`, `form.AppField`, `form.AppForm`",
   "Dans un composant de champ : `useFieldContext()` ; dans un bouton : `useFormContext()`"],
  ["Mode tableau : `field.state.value` est le tableau ; `field.pushValue(objet)`, `field.removeValue(i)`.",
   "Sous-champ d'une liste : `name={`lignes[${i}].prix`}` (crochets).",
   "`listeners` réagit à un événement (changement, blur) **sans** être une validation.",
   "`createFormHook` : on déclare une fois les composants ; chaque formulaire utilise `useAppForm` au lieu de `useForm`.",
   "`<form.AppField name=\"email\" children={(field) => <field.TextField label=\"Email\" />} />`."],
  ["`key={i}` sur des lignes qu'on supprime (préférer un id dans la valeur).", "Oublier `form.AppForm` autour d'un `SubmitButton` (pas de contexte).", "Faire la logique « vider la ville » dans le validateur au lieu d'un listener."],
  [Q("Ajouter une ligne dans un champ en mode array :", ["append()", "field.pushValue(ligne)", "setFieldValue('lignes', …) obligatoirement", "useFieldArray"], 1, "C'est l'API du FieldApi en mode array."),
   Q("Dans un TextField réutilisable, comment obtenir le champ ?", ["props field", "useFieldContext()", "useForm()", "register"], 1, "form.AppField fournit le contexte du champ."),
   Q("Vider la ville quand le pays change :", ["validators.onChange", "listeners.onChange", "useEffect sur tout le formulaire", "impossible"], 1, "Les listeners sont faits pour les effets de bord.")],
  prereq=[
    P("Mode array", "Un `form.Field` dont la valeur est un tableau, avec `pushValue`, `removeValue`, `swapValues`…"),
    P("Listener", "Fonction appelée quand un événement arrive sur un champ (`onChange`, `onBlur`, `onMount`), pour déclencher un effet (vider un autre champ…)."),
    P("`createFormHook`", "Fabrique un `useAppForm` qui connaît tes composants de champ (`TextField`…) et de formulaire (`SubmitButton`…)."),
    P("`useFieldContext` / `useFormContext`", "Hooks à utiliser **dans** tes composants de champ / de formulaire pour récupérer le champ ou le formulaire courant."),
  ],
  diagram=D(
    nodes=[
      N("cfh", 0, 1, "createFormHook", "une fois dans le projet", kind="box", color="good"),
      N("tf", 1, 0, "TextField", "useFieldContext()", kind="file", color="accent"),
      N("sb", 1, 2, "SubmitButton", "useFormContext()", kind="file", color="accent"),
      N("uaf", 2, 1, "useAppForm", "dans chaque formulaire", kind="box", color="warn"),
      N("af", 3, 0, "<form.AppField>", "<field.TextField />", kind="pill"),
      N("afo", 3, 2, "<form.AppForm>", "<form.SubmitButton />", kind="pill"),
    ],
    edges=[E("tf", "cfh"), E("sb", "cfh"), E("cfh", "uaf"), E("uaf", "af"), E("uaf", "afo")],
    caption="Les composants de champ sont écrits une fois et enregistrés dans createFormHook ; chaque formulaire les utilise via useAppForm."),
  lessons=[
    L("Listes de champs", r"""
```tsx
const form = useForm({
  defaultValues: { client: '', lignes: [{ designation: '', quantite: 1, prix: 0 }] },
  onSubmit: async ({ value }) => { … },
});

<form.Field name="lignes" mode="array" children={(lignes) => (
  <>
    {lignes.state.value.map((_, i) => (
      <div key={i}>
        <form.Field name={`lignes[${i}].designation`} children={(f) => (
          <input value={f.state.value} onChange={(e) => f.handleChange(e.target.value)} />
        )} />
        <form.Field name={`lignes[${i}].prix`} children={(f) => (
          <input type="number" value={f.state.value} onChange={(e) => f.handleChange(e.target.valueAsNumber)} />
        )} />
        <button type="button" onClick={() => lignes.removeValue(i)}>Supprimer</button>
      </div>
    ))}
    <button type="button" onClick={() => lignes.pushValue({ designation: '', quantite: 1, prix: 0 })}>Ajouter</button>
  </>
)} />

<form.Subscribe
  selector={(s) => s.values.lignes.reduce((t, l) => t + l.quantite * l.prix, 0)}
  children={(total) => <p>Total : {total.toFixed(2)} €</p>}
/>
```

Les nombres : c'est toi qui convertis (`e.target.valueAsNumber`) puisque c'est toi qui appelles `handleChange`. Avantage par rapport à RHF : `field.state.value` est **toujours** à jour (pas de `useWatch` nécessaire).
"""),
    L("Champs liés : listeners", r"""
Quand le pays change, la ville choisie n'a plus de sens : il faut la vider. Ce n'est pas une validation, c'est un **effet** → `listeners` :

```tsx
<form.Field
  name="pays"
  listeners={{
    onChange: ({ value }) => {
      form.setFieldValue('ville', '');        // vider le champ lié
    },
  }}
  children={(field) => <select value={field.state.value} onChange={(e) => field.handleChange(e.target.value)}>…</select>}
/>
```

Pour charger la liste des villes du pays choisi, on lit la valeur (`useStore(form.store, (s) => s.values.pays)`) et on fait la requête dans un `useEffect` (ou avec TanStack Query : `useQuery({ queryKey: ['villes', pays], enabled: !!pays })`).

Autres outils utiles : `form.setFieldValue`, `form.getFieldValue`, `form.reset(valeurs)`, `form.resetField('x')`, `onChangeListenTo` dans un validateur.
"""),
    L("createFormHook : le pattern des projets d'entreprise", r"""
Plutôt que de réécrire `value`/`onChange`/erreurs dans chaque formulaire, on crée **une fois** :

```tsx
// formulaire.tsx (partagé dans tout le projet)
import { createFormHook, createFormHookContexts } from '@tanstack/react-form';

export const { fieldContext, formContext, useFieldContext, useFormContext } = createFormHookContexts();

function TextField({ label, type = 'text' }: { label: string; type?: string }) {
  const field = useFieldContext<string>();
  const erreur = field.state.meta.isTouched && field.state.meta.errors[0];
  return (
    <label>
      {label}
      <input type={type} name={field.name} value={field.state.value} onBlur={field.handleBlur} onChange={(e) => field.handleChange(e.target.value)} />
      {erreur && <p role="alert">{typeof erreur === 'string' ? erreur : erreur.message}</p>}
    </label>
  );
}

function SubmitButton({ label }: { label: string }) {
  const form = useFormContext();
  return <form.Subscribe selector={(s) => s.isSubmitting} children={(enCours) => <button type="submit" disabled={enCours}>{enCours ? 'Envoi…' : label}</button>} />;
}

export const { useAppForm } = createFormHook({
  fieldContext, formContext,
  fieldComponents: { TextField },
  formComponents: { SubmitButton },
});
```

Puis chaque formulaire devient très court :

```tsx
const form = useAppForm({ defaultValues: { email: '' }, validators: { onChange: schema }, onSubmit });

<form onSubmit={(e) => { e.preventDefault(); form.handleSubmit(); }}>
  <form.AppField name="email" children={(field) => <field.TextField label="Email" />} />
  <form.AppForm><form.SubmitButton label="Envoyer" /></form.AppForm>
</form>
```

Si ton projet a des `useAppForm`, `form.AppField` et `field.TextField`, c'est ce mécanisme : cherche le fichier qui appelle `createFormHook`, tu y trouveras tous les composants de champ disponibles.
"""),
  ],
  recap=["Liste : `mode=\"array\"`, `pushValue`, `removeValue`, sous-champs `lignes[${i}].x`.",
         "Total ou affichage dérivé : `form.Subscribe selector`.",
         "Effet sur un autre champ : `listeners.onChange` + `form.setFieldValue`.",
         "Composants de champ : `createFormHookContexts` + `createFormHook` → `useAppForm`, `form.AppField`, `form.AppForm`."],
  example=F("Pays.tsx", "tsx", r"""
import { useForm } from '@tanstack/react-form';

export default function Pays() {
  const form = useForm({ defaultValues: { pays: 'FR', ville: '' }, onSubmit: ({ value }) => console.log(value) });
  return (
    <form.Field
      name="pays"
      listeners={{ onChange: () => form.setFieldValue('ville', '') }}
      children={(field) => (
        <select value={field.state.value} onChange={(e) => field.handleChange(e.target.value)}>
          <option value="FR">France</option>
          <option value="BE">Belgique</option>
        </select>
      )}
    />
  );
}
"""),
  notes=["Le listener vide la ville à chaque changement de pays.", "Ce n'est pas un validateur : il ne produit pas d'erreur."],
  tds=[
    TD(1, "La facture, version TanStack Form",
       "Même facture que dans le module React Hook Form : mêmes noms, mêmes messages. Compare le code obtenu avec ta version RHF." + EX,
       ["`defaultValues` : `client: ''` et une ligne `{ designation: '', quantite: 1, prix: 0 }` ; chaque ligne dans `<div class=\"ligne\">`",
        "Inputs avec `name` : `client`, `lignes[<i>].designation`, `lignes[<i>].quantite`, `lignes[<i>].prix` (nombres avec `valueAsNumber`) ; `Supprimer` (désactivé s'il reste une ligne) ; `Ajouter une ligne`",
        "`<p id=\"total\">Total : 25.00 €</p>` avec `form.Subscribe`",
        "Validateurs : `Client requis` (`id=\"erreur-client\"`), `Désignation requise` dans un `<p class=\"erreur\">` de la ligne ; envoi → `POST /api/factures` puis `Facture enregistrée`"],
       [F("Facture.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm } from '@tanstack/react-form';

type Ligne = { designation: string; quantite: number; prix: number };

export default function Facture() {
  const [ok, setOk] = useState(false);
  // à toi

  if (ok) return <p>Facture enregistrée</p>;
  return <form></form>;
}
""")],
       ["`<form.Field name=\"lignes\" mode=\"array\" children={(lignes) => …} />` ; dedans, `lignes.state.value.map((_, i) => …)`.",
        "Un sous-champ : `<form.Field name={`lignes[${i}].prix`} children={(f) => <input type=\"number\" name={f.name} value={f.state.value} onChange={(e) => f.handleChange(e.target.valueAsNumber)} />} />`",
        "Total : `selector={(s) => s.values.lignes.reduce((t, l) => t + (l.quantite || 0) * (l.prix || 0), 0)}`."],
       [F("Facture.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm } from '@tanstack/react-form';

type Ligne = { designation: string; quantite: number; prix: number };
const LIGNE_VIDE: Ligne = { designation: '', quantite: 1, prix: 0 };

export default function Facture() {
  const [ok, setOk] = useState(false);
  const form = useForm({
    defaultValues: { client: '', lignes: [LIGNE_VIDE] as Ligne[] },
    onSubmit: async ({ value }) => {
      await fetch('/api/factures', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(value) });
      setOk(true);
    },
  });

  if (ok) return <p>Facture enregistrée</p>;
  return (
    <form onSubmit={(e) => { e.preventDefault(); form.handleSubmit(); }}>
      <form.Field
        name="client"
        validators={{ onChange: ({ value }) => (!value.trim() ? 'Client requis' : undefined) }}
        children={(f) => (
          <>
            <label>Client <input name={f.name} value={f.state.value} onBlur={f.handleBlur} onChange={(e) => f.handleChange(e.target.value)} /></label>
            {f.state.meta.isTouched && f.state.meta.errors.length > 0 && <p role="alert" id="erreur-client">{String(f.state.meta.errors[0])}</p>}
          </>
        )}
      />

      <form.Field
        name="lignes"
        mode="array"
        children={(lignes) => (
          <>
            {lignes.state.value.map((_, i) => (
              <div className="ligne" key={i}>
                <form.Field
                  name={`lignes[${i}].designation`}
                  validators={{ onChange: ({ value }) => (!value.trim() ? 'Désignation requise' : undefined) }}
                  children={(f) => (
                    <>
                      <input placeholder="Désignation" name={f.name} value={f.state.value} onBlur={f.handleBlur} onChange={(e) => f.handleChange(e.target.value)} />
                      {f.state.meta.isTouched && f.state.meta.errors.length > 0 && <p className="erreur">{String(f.state.meta.errors[0])}</p>}
                    </>
                  )}
                />
                <form.Field
                  name={`lignes[${i}].quantite`}
                  children={(f) => <input type="number" name={f.name} value={f.state.value} onChange={(e) => f.handleChange(e.target.valueAsNumber)} />}
                />
                <form.Field
                  name={`lignes[${i}].prix`}
                  children={(f) => <input type="number" step="0.01" name={f.name} value={f.state.value} onChange={(e) => f.handleChange(e.target.valueAsNumber)} />}
                />
                <button type="button" onClick={() => lignes.removeValue(i)} disabled={lignes.state.value.length === 1}>Supprimer</button>
              </div>
            ))}
            <button type="button" onClick={() => lignes.pushValue(LIGNE_VIDE)}>Ajouter une ligne</button>
          </>
        )}
      />

      <form.Subscribe
        selector={(s) => s.values.lignes.reduce((t, l) => t + (l.quantite || 0) * (l.prix || 0), 0)}
        children={(total) => <p id="total">Total : {total.toFixed(2)} €</p>}
      />
      <button type="submit">Enregistrer</button>
    </form>
  );
}
""")],
       ["Même comportement que la version RHF", "Les valeurs de la liste sont toujours à jour"],
       run=FRUN("Facture.tsx", api=r"""
window.__recu = [];
__api["POST /api/factures"] = (p, b) => { window.__recu.push(b); return [201, { id: 1 }]; };
""", tests=r"""
const lignes = () => $$('.ligne');
const btn = (t) => Array.from(document.querySelectorAll('button')).find((b) => b.textContent.trim() === t);
assert(/mode="array"/.test(source('Facture.tsx')), 'Utilise un champ en mode array');
assert.equal(lignes().length, 1, 'Une ligne au départ');
assert(btn('Supprimer') && btn('Supprimer').disabled, 'Une seule ligne : Supprimer désactivé');
await type('[name="lignes[0].designation"]', 'Clavier');
await type('[name="lignes[0].quantite"]', '2');
await type('[name="lignes[0].prix"]', '12.5');
assert.equal($('#total').textContent, 'Total : 25.00 €', 'Total : 25.00 €');
await click(btn('Ajouter une ligne'));
assert.equal(lignes().length, 2, 'Ajouter une ligne');
await type('[name="lignes[1].designation"]', 'Souris');
await type('[name="lignes[1].quantite"]', '3');
await type('[name="lignes[1].prix"]', '10');
assert.equal($('#total').textContent, 'Total : 55.00 €', 'Total : 55.00 €');
await click(btn('Ajouter une ligne'));
await type('[name="lignes[2].designation"]', 'Écran');
await click(lignes()[1].querySelector('button'));
assert.equal(lignes().length, 2, 'Supprimer la ligne du milieu');
assert.equal($('[name="lignes[1].designation"]').value, 'Écran', 'La 3e ligne remonte avec sa valeur');
await submit('form');
await tick(100);
assert.equal($('#erreur-client') && $('#erreur-client').textContent, 'Client requis', 'Client vide à l\'envoi : « Client requis »');
assert.equal(window.__recu.length, 0, 'Invalide : rien envoyé');
await type('[name="lignes[1].designation"]', '');
assert(lignes()[1].querySelector('.erreur') && lignes()[1].querySelector('.erreur').textContent === 'Désignation requise', 'Désignation vidée : erreur dans la ligne');
await type('[name=client]', 'ACME');
await type('[name="lignes[1].designation"]', 'Écran');
await submit('form');
await waitFor(() => /Facture enregistrée/.test(text()), 3000);
const f = window.__recu[0] || { lignes: [] };
assert(f.client === 'ACME' && f.lignes.length === 2, 'Envoyé : client + 2 lignes', JSON.stringify(f));
assert(f.lignes[0].quantite === 2 && f.lignes[0].prix === 12.5, 'Nombres envoyés en nombres');
""")),
    TD(2, "createFormHook : des composants de champ maison",
       "Crée le kit de formulaires du projet (`formulaire.tsx`) : un `TextField`, un `SelectField` et un `SubmitButton` branchés sur TanStack Form. Le formulaire de contact qui les utilise est fourni : il ne contient plus aucun `value`/`onChange`." + EX,
       ["`formulaire.tsx` exporte `useAppForm` (via `createFormHookContexts` + `createFormHook`)",
        "`TextField({ label, type? })` : `<label>` + `<input name value onBlur onChange>` ; si touché et en erreur : `<p role=\"alert\" id=\"erreur-<nom>\">` avec le **message** (chaîne ou objet zod)",
        "`SelectField({ label, options })` (options : `{ value, label }[]`) : même principe avec un `<select>`",
        "`SubmitButton({ label })` : désactivé et `Envoi…` pendant l'envoi"],
       [F("formulaire.tsx", "tsx", r"""
import { createFormHook, createFormHookContexts } from '@tanstack/react-form';

// à toi : contextes, TextField, SelectField, SubmitButton, puis useAppForm

export const useAppForm: any = () => {
  throw new Error('useAppForm pas encore écrit');
};
"""), F("Contact.tsx", "tsx", r"""
import { useState } from 'react';
import { z } from 'zod';
import { useAppForm } from './formulaire';

const contactSchema = z.object({
  nom: z.string().min(1, 'Nom requis'),
  email: z.string().email('Email invalide'),
  sujet: z.enum(['devis', 'support', 'autre'], { message: 'Choisis un sujet' }),
  message: z.string().min(10, '10 caractères minimum'),
});

export default function Contact() {
  const [envoye, setEnvoye] = useState(false);
  const form = useAppForm({
    defaultValues: { nom: '', email: '', sujet: '', message: '' },
    validators: { onChange: contactSchema },
    onSubmit: async ({ value }: { value: unknown }) => {
      await fetch('/api/contact', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(value) });
      setEnvoye(true);
    },
  });

  if (envoye) return <p>Message envoyé</p>;
  return (
    <form onSubmit={(e) => { e.preventDefault(); form.handleSubmit(); }}>
      <form.AppField name="nom" children={(field: any) => <field.TextField label="Nom" />} />
      <form.AppField name="email" children={(field: any) => <field.TextField label="Email" type="email" />} />
      <form.AppField
        name="sujet"
        children={(field: any) => (
          <field.SelectField
            label="Sujet"
            options={[
              { value: '', label: '— Choisir —' },
              { value: 'devis', label: 'Demande de devis' },
              { value: 'support', label: 'Support' },
              { value: 'autre', label: 'Autre' },
            ]}
          />
        )}
      />
      <form.AppField name="message" children={(field: any) => <field.TextField label="Message" />} />
      <form.AppForm>
        <form.SubmitButton label="Envoyer" />
      </form.AppForm>
    </form>
  );
}
""")],
       ["`export const { fieldContext, formContext, useFieldContext, useFormContext } = createFormHookContexts();`",
        "Dans `TextField` : `const field = useFieldContext<string>();` ; message : `const e = field.state.meta.errors[0]; const msg = typeof e === 'string' ? e : e?.message;`",
        "`export const { useAppForm } = createFormHook({ fieldContext, formContext, fieldComponents: { TextField, SelectField }, formComponents: { SubmitButton } });`"],
       [F("formulaire.tsx", "tsx", r"""
import { createFormHook, createFormHookContexts } from '@tanstack/react-form';

export const { fieldContext, formContext, useFieldContext, useFormContext } = createFormHookContexts();

function messageErreur(errors: unknown[]): string | undefined {
  const e = errors[0] as any;
  if (!e) return undefined;
  return typeof e === 'string' ? e : e.message;
}

function Erreur() {
  const field = useFieldContext<unknown>();
  const msg = field.state.meta.isTouched ? messageErreur(field.state.meta.errors) : undefined;
  return msg ? <p role="alert" id={'erreur-' + field.name}>{msg}</p> : null;
}

function TextField({ label, type = 'text' }: { label: string; type?: string }) {
  const field = useFieldContext<string>();
  return (
    <div>
      <label>
        {label}{' '}
        <input type={type} name={field.name} value={field.state.value} onBlur={field.handleBlur} onChange={(e) => field.handleChange(e.target.value)} />
      </label>
      <Erreur />
    </div>
  );
}

function SelectField({ label, options }: { label: string; options: { value: string; label: string }[] }) {
  const field = useFieldContext<string>();
  return (
    <div>
      <label>
        {label}{' '}
        <select name={field.name} value={field.state.value} onBlur={field.handleBlur} onChange={(e) => field.handleChange(e.target.value)}>
          {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </label>
      <Erreur />
    </div>
  );
}

function SubmitButton({ label }: { label: string }) {
  const form = useFormContext();
  return (
    <form.Subscribe
      selector={(s) => s.isSubmitting}
      children={(enCours) => <button type="submit" disabled={enCours}>{enCours ? 'Envoi…' : label}</button>}
    />
  );
}

export const { useAppForm } = createFormHook({
  fieldContext,
  formContext,
  fieldComponents: { TextField, SelectField },
  formComponents: { SubmitButton },
});
"""), F("Contact.tsx", "tsx", r"""
import { useState } from 'react';
import { z } from 'zod';
import { useAppForm } from './formulaire';

const contactSchema = z.object({
  nom: z.string().min(1, 'Nom requis'),
  email: z.string().email('Email invalide'),
  sujet: z.enum(['devis', 'support', 'autre'], { message: 'Choisis un sujet' }),
  message: z.string().min(10, '10 caractères minimum'),
});

export default function Contact() {
  const [envoye, setEnvoye] = useState(false);
  const form = useAppForm({
    defaultValues: { nom: '', email: '', sujet: '', message: '' },
    validators: { onChange: contactSchema },
    onSubmit: async ({ value }: { value: unknown }) => {
      await fetch('/api/contact', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(value) });
      setEnvoye(true);
    },
  });

  if (envoye) return <p>Message envoyé</p>;
  return (
    <form onSubmit={(e) => { e.preventDefault(); form.handleSubmit(); }}>
      <form.AppField name="nom" children={(field: any) => <field.TextField label="Nom" />} />
      <form.AppField name="email" children={(field: any) => <field.TextField label="Email" type="email" />} />
      <form.AppField
        name="sujet"
        children={(field: any) => (
          <field.SelectField
            label="Sujet"
            options={[
              { value: '', label: '— Choisir —' },
              { value: 'devis', label: 'Demande de devis' },
              { value: 'support', label: 'Support' },
              { value: 'autre', label: 'Autre' },
            ]}
          />
        )}
      />
      <form.AppField name="message" children={(field: any) => <field.TextField label="Message" />} />
      <form.AppForm>
        <form.SubmitButton label="Envoyer" />
      </form.AppForm>
    </form>
  );
}
""")],
       ["Contact.tsx ne contient ni `value` ni `onChange`", "Les erreurs zod s'affichent comme des messages"],
       run=FRUN("Contact.tsx", api=r"""
window.__recu = [];
__api["POST /api/contact"] = (p, b) => { window.__recu.push(b); return [201, {}]; };
""", tests=r"""
const err = (n) => { const e = $('#erreur-' + n); return e ? e.textContent : ''; };
assert(/createFormHook\(/.test(source('formulaire.tsx')) && /useFieldContext/.test(source('formulaire.tsx')), 'formulaire.tsx utilise createFormHook et useFieldContext');
assert($('input[name=nom]') && $('select[name=sujet]') && $('input[name=email][type=email]'), 'TextField et SelectField rendent les bons éléments (avec name et type)');
assert(text().includes('Nom') && text().includes('Sujet'), 'Les labels sont affichés');
assert(!$('[role=alert]'), 'Aucune erreur à l\'ouverture');
await type('[name=email]', 'ana');
assert.equal(err('email'), 'Email invalide', 'Erreur zod affichée comme un MESSAGE (pas [object Object])');
await submit('form');
await tick(120);
assert.equal(err('nom'), 'Nom requis', 'Envoi : « Nom requis »');
assert.equal(err('sujet'), 'Choisis un sujet', 'SelectField affiche aussi son erreur');
await type('[name=nom]', 'Ana');
await type('[name=email]', 'ana@exemple.fr');
await choose('[name=sujet]', 'support');
await type('[name=message]', 'Mon imprimante ne marche plus');
assert(!$('[role=alert]'), 'Tout corrigé : plus d\'erreur');
await submit('form');
await tick(30);
assert($('button[type=submit]') && $('button[type=submit]').disabled && $('button[type=submit]').textContent === 'Envoi…', 'SubmitButton : « Envoi… » désactivé pendant l\'envoi');
await waitFor(() => /Message envoyé/.test(text()), 3000);
assert(window.__recu[0] && window.__recu[0].sujet === 'support', 'Valeurs envoyées (sujet = support)');
""")),
    TD(3, "Pays, puis ville : des champs liés",
       "Dans le formulaire d'adresse, la liste des villes dépend du pays. Quand le pays change, la ville doit être vidée et la liste rechargée. Aujourd'hui, la ville de l'ancien pays reste sélectionnée (« Lyon, Belgique »)." + EX,
       ["`pays` : `<select name=\"pays\">` avec `FR` (France) et `BE` (Belgique) ; `FR` au départ",
        "Quand le pays change : la ville est **vidée** (avec un `listeners.onChange`)",
        "Les villes viennent de `GET /api/pays/<code>/villes` (tableau de noms) ; pendant le chargement, le `<select name=\"ville\">` est désactivé ; une option vide `— Choisir —`",
        "Ville vide à l'envoi → `Choisis une ville` (`id=\"erreur-ville\"`) ; envoi → `POST /api/adresses` avec `{ pays, ville }` puis `Adresse enregistrée`"],
       [F("Adresse.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import { useForm, useStore } from '@tanstack/react-form';

export default function Adresse() {
  const [ok, setOk] = useState(false);
  const [villes, setVilles] = useState<string[]>([]);
  const form = useForm({
    defaultValues: { pays: 'FR', ville: '' },
    onSubmit: async ({ value }) => {
      await fetch('/api/adresses', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(value) });
      setOk(true);
    },
  });

  useEffect(() => {
    fetch('/api/pays/FR/villes').then((r) => r.json()).then(setVilles);
  }, []);

  if (ok) return <p>Adresse enregistrée</p>;
  return (
    <form onSubmit={(e) => { e.preventDefault(); form.handleSubmit(); }}>
      <form.Field
        name="pays"
        children={(f) => (
          <select name="pays" value={f.state.value} onChange={(e) => f.handleChange(e.target.value)}>
            <option value="FR">France</option>
            <option value="BE">Belgique</option>
          </select>
        )}
      />
      <form.Field
        name="ville"
        children={(f) => (
          <select name="ville" value={f.state.value} onChange={(e) => f.handleChange(e.target.value)}>
            <option value="">— Choisir —</option>
            {villes.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        )}
      />
      <button type="submit">Enregistrer</button>
    </form>
  );
}
""")],
       ["Sur le champ pays : `listeners={{ onChange: () => form.setFieldValue('ville', '') }}`.",
        "Lis le pays courant : `const pays = useStore(form.store, (s) => s.values.pays);` puis `useEffect(() => { setChargement(true); fetch(`/api/pays/${pays}/villes`)… }, [pays]);`",
        "Validateur de la ville : `validators={{ onSubmit: ({ value }) => (!value ? 'Choisis une ville' : undefined) }}`."],
       [F("Adresse.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import { useForm, useStore } from '@tanstack/react-form';

export default function Adresse() {
  const [ok, setOk] = useState(false);
  const [villes, setVilles] = useState<string[]>([]);
  const [chargement, setChargement] = useState(true);
  const form = useForm({
    defaultValues: { pays: 'FR', ville: '' },
    onSubmit: async ({ value }) => {
      await fetch('/api/adresses', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(value) });
      setOk(true);
    },
  });

  const pays = useStore(form.store, (s) => s.values.pays);

  useEffect(() => {
    let actif = true;
    setChargement(true);
    setVilles([]);
    fetch(`/api/pays/${pays}/villes`)
      .then((r) => r.json())
      .then((v: string[]) => { if (actif) setVilles(v); })
      .finally(() => { if (actif) setChargement(false); });
    return () => { actif = false; };
  }, [pays]);

  if (ok) return <p>Adresse enregistrée</p>;
  return (
    <form onSubmit={(e) => { e.preventDefault(); form.handleSubmit(); }}>
      <form.Field
        name="pays"
        listeners={{ onChange: () => form.setFieldValue('ville', '') }}
        children={(f) => (
          <label>Pays <select name="pays" value={f.state.value} onChange={(e) => f.handleChange(e.target.value)}>
            <option value="FR">France</option>
            <option value="BE">Belgique</option>
          </select></label>
        )}
      />
      <form.Field
        name="ville"
        validators={{ onSubmit: ({ value }) => (!value ? 'Choisis une ville' : undefined) }}
        children={(f) => (
          <>
            <label>Ville <select name="ville" value={f.state.value} disabled={chargement} onChange={(e) => f.handleChange(e.target.value)}>
              <option value="">— Choisir —</option>
              {villes.map((v) => <option key={v} value={v}>{v}</option>)}
            </select></label>
            {f.state.meta.errors.length > 0 && <p role="alert" id="erreur-ville">{String(f.state.meta.errors[0])}</p>}
          </>
        )}
      />
      <button type="submit">Enregistrer</button>
    </form>
  );
}
""")],
       ["Plus de « Lyon, Belgique »", "Le select est désactivé pendant le chargement"],
       run=FRUN("Adresse.tsx", api=r"""
window.__recu = [];
const VILLES = { FR: ['Lyon', 'Paris', 'Lille'], BE: ['Bruxelles', 'Liège'] };
__api["GET /api/pays/:code/villes"] = (p) => VILLES[p.code] || [];
__api["POST /api/adresses"] = (p, b) => { window.__recu.push(b); return [201, {}]; };
""", tests=r"""
const options = () => $$('select[name=ville] option').map((o) => o.value).filter(Boolean);
assert(/listeners/.test(source('Adresse.tsx')), 'Utilise un listener');
await waitFor(() => options().length === 3, 3000);
assert.equal(options().join(','), 'Lyon,Paris,Lille', 'Villes de France chargées');
await choose('[name=ville]', 'Lyon');
assert.equal($('[name=ville]').value, 'Lyon', 'Lyon choisi');
await choose('[name=pays]', 'BE');
await tick(30);
assert.equal($('[name=ville]').value, '', 'Pays changé : la ville est vidée');
assert($('[name=ville]').disabled, 'Pendant le chargement des villes : select désactivé');
await waitFor(() => options().join(',') === 'Bruxelles,Liège', 3000);
assert(!$('[name=ville]').disabled, 'Villes de Belgique chargées, select actif');
await submit('form');
await tick(100);
assert.equal($('#erreur-ville') && $('#erreur-ville').textContent, 'Choisis une ville', 'Ville vide à l\'envoi : « Choisis une ville »');
assert.equal(window.__recu.length, 0, 'Rien envoyé');
await choose('[name=ville]', 'Liège');
await submit('form');
await waitFor(() => /Adresse enregistrée/.test(text()), 3000);
assert(window.__recu[0] && window.__recu[0].pays === 'BE' && window.__recu[0].ville === 'Liège', 'Envoyé : { pays: BE, ville: Liège }');
""")),
  ])

# =========================================================================== 6. Comparer / migrer
TACHE_SCHEMA = r"""
import { z } from 'zod';

export const tacheSchema = z.object({
  titre: z.string().trim().min(3, '3 caractères minimum'),
  priorite: z.enum(['basse', 'normale', 'haute'], { message: 'Priorité invalide' }),
  estimation: z.coerce.number({ message: 'Nombre attendu' }).min(0.5, 'Au moins 0,5 h').max(40, '40 h maximum'),
});

export type Tache = z.infer<typeof tacheSchema>;
"""

TACHE_RHF = r"""
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { tacheSchema, type Tache } from './schema';

export default function NouvelleTache() {
  const [creee, setCreee] = useState('');
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(tacheSchema),
    mode: 'onTouched',
    defaultValues: { titre: '', priorite: 'normale', estimation: '' as unknown as number },
  });

  async function creer(t: Tache) {
    const res = await fetch('/api/taches', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(t) });
    const tache = await res.json();
    setCreee(tache.titre);
    reset();
  }

  return (
    <form onSubmit={handleSubmit(creer)}>
      <label>Titre <input {...register('titre')} /></label>
      {errors.titre && <p role="alert" id="erreur-titre">{errors.titre.message}</p>}
      <label>Priorité <select {...register('priorite')}>
        <option value="basse">Basse</option>
        <option value="normale">Normale</option>
        <option value="haute">Haute</option>
      </select></label>
      <label>Estimation (h) <input type="number" step="0.5" {...register('estimation')} /></label>
      {errors.estimation && <p role="alert" id="erreur-estimation">{errors.estimation.message}</p>}
      <button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Création…' : 'Créer'}</button>
      {creee && <p>Tâche « {creee} » créée</p>}
    </form>
  );
}
"""

TACHE_TSF = r"""
import { useState } from 'react';
import { useForm, useStore } from '@tanstack/react-form';
import { tacheSchema } from './schema';

function message(errors: unknown[]) {
  const e = errors[0] as any;
  return typeof e === 'string' ? e : e?.message;
}

export default function NouvelleTache() {
  const [creee, setCreee] = useState('');
  const form = useForm({
    defaultValues: { titre: '', priorite: 'normale', estimation: '' },
    validators: { onChange: tacheSchema, onSubmit: tacheSchema },
    onSubmit: async ({ value }) => {
      const t = tacheSchema.parse(value);
      const res = await fetch('/api/taches', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(t) });
      const tache = await res.json();
      setCreee(tache.titre);
      form.reset();
    },
  });
  // comme mode: 'onTouched' : erreur visible après le 1er blur du champ (ou un envoi), puis en direct
  const envoye = useStore(form.store, (s) => s.submissionAttempts > 0);
  const visible = (meta: { isBlurred: boolean; errors: unknown[] }) => (meta.isBlurred || envoye) && meta.errors.length > 0;

  return (
    <form onSubmit={(e) => { e.preventDefault(); form.handleSubmit(); }}>
      <form.Field
        name="titre"
        children={(f) => (
          <>
            <label>Titre <input name="titre" value={f.state.value} onBlur={f.handleBlur} onChange={(e) => f.handleChange(e.target.value)} /></label>
            {visible(f.state.meta) && <p role="alert" id="erreur-titre">{message(f.state.meta.errors)}</p>}
          </>
        )}
      />
      <form.Field
        name="priorite"
        children={(f) => (
          <label>Priorité <select name="priorite" value={f.state.value} onBlur={f.handleBlur} onChange={(e) => f.handleChange(e.target.value)}>
            <option value="basse">Basse</option>
            <option value="normale">Normale</option>
            <option value="haute">Haute</option>
          </select></label>
        )}
      />
      <form.Field
        name="estimation"
        children={(f) => (
          <>
            <label>Estimation (h) <input type="number" step="0.5" name="estimation" value={f.state.value} onBlur={f.handleBlur} onChange={(e) => f.handleChange(e.target.value)} /></label>
            {visible(f.state.meta) && <p role="alert" id="erreur-estimation">{message(f.state.meta.errors)}</p>}
          </>
        )}
      />
      <form.Subscribe
        selector={(s) => s.isSubmitting}
        children={(enCours) => <button type="submit" disabled={enCours}>{enCours ? 'Création…' : 'Créer'}</button>}
      />
      {creee && <p>Tâche « {creee} » créée</p>}
    </form>
  );
}
"""

TACHE_API = r"""
window.__recu = [];
__api["POST /api/taches"] = (p, b) => { window.__recu.push(b); return [201, Object.assign({ id: window.__recu.length }, b)]; };
"""

TACHE_TESTS = r"""
const err = (n) => { const e = $('#erreur-' + n); return e ? e.textContent : ''; };
assert(!$('[role=alert]'), 'Aucune erreur à l\'ouverture');
await type('[name=titre]', 'ab');
assert.equal(err('titre'), '', 'Pas d\'erreur pendant la 1re saisie');
await blur('[name=titre]');
await tick(80);
assert.equal(err('titre'), '3 caractères minimum', 'Au blur : « 3 caractères minimum »');
await submit('form');
await tick(120);
assert.equal(err('estimation'), 'Au moins 0,5 h', 'Envoi : estimation vide → « Au moins 0,5 h »');
assert.equal(window.__recu.length, 0, 'Invalide : rien envoyé');
await type('[name=titre]', '  Écrire les tests  ');
await choose('[name=priorite]', 'haute');
await type('[name=estimation]', '2.5');
await tick(60);
assert.equal(err('titre'), '', 'Titre corrigé : l\'erreur disparaît');
await submit('form');
await tick(40);
assert($('button[type=submit]').disabled && $('button[type=submit]').textContent === 'Création…', 'Pendant l\'envoi : « Création… » désactivé');
await waitFor(() => /créée/.test(text()), 3000);
const b = window.__recu[0] || {};
assert(b.titre === 'Écrire les tests', 'Envoyé : titre nettoyé (trim)', JSON.stringify(b));
assert(b.priorite === 'haute', 'Envoyé : priorité');
assert(b.estimation === 2.5, 'Envoyé : estimation en NOMBRE (2.5)');
assert.includes(text(), 'Tâche « Écrire les tests » créée', 'Message de confirmation');
assert($('[name=titre]').value === '' && $('[name=priorite]').value === 'normale', 'Formulaire remis à zéro après création');
assert(!$('[role=alert]'), 'Remis à zéro : aucune erreur affichée');
"""

CHAMP_TEXTE = r"""
import { forwardRef, useId } from 'react';

type Props = React.InputHTMLAttributes<HTMLInputElement> & { label: string; erreur?: string };

export const ChampTexte = forwardRef<HTMLInputElement, Props>(function ChampTexte({ label, erreur, ...inputProps }, ref) {
  const id = useId();
  const idErreur = id + '-erreur';
  return (
    <div className="champ">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        ref={ref}
        aria-invalid={erreur ? true : undefined}
        aria-describedby={erreur ? idErreur : undefined}
        {...inputProps}
      />
      {erreur && <p role="alert" id={idErreur} className="erreur">{erreur}</p>}
    </div>
  );
});
"""

compare = DM("forms-compare", "React Hook Form ou TanStack Form : lire, migrer, partager", 30,
  "Passer d'une bibliothèque à l'autre sans te perdre : la table de correspondance, les pièges de chacune, et des composants d'interface partagés par les deux.",
  "Ton entreprise utilise les deux : tu vas lire du RHF le matin et du TanStack Form l'après-midi, et parfois migrer un formulaire. Avec la correspondance en tête, ce sont les mêmes idées sous deux syntaxes.",
  ["Repérer : `register` / `Controller` → RHF ; `form.Field` / `AppField` → TanStack Form", "Traduire avec la table de correspondance",
   "Garder les règles dans un **schéma zod** partagé", "Garder l'apparence dans des composants **sans** bibliothèque (`ChampTexte`), branchés sur l'une ou l'autre"],
  ["Mêmes concepts, mêmes noms ou presque : valeurs par défaut, erreurs, touché, dirty, envoi, reset.",
   "RHF : le formulaire **lit** les inputs (ref) ; TanStack : les inputs **lisent** le formulaire (value).",
   "RHF + zodResolver donne les données **converties** ; TanStack donne les valeurs **brutes** (faire `schema.parse`).",
   "Un composant d'interface partagé reçoit `value`/`onChange`/`erreur`… et transmet la `ref` (`forwardRef`) pour RHF.",
   "Choisir : RHF pour la plupart des formulaires (court, rapide) ; TanStack Form quand le typage strict, les validations fines par moment et les gros formulaires dynamiques comptent."],
  ["Afficher les erreurs TanStack + zod sans `.message`.", "Oublier `forwardRef` dans un composant d'input (RHF ne peut plus focus ni lire la valeur).", "Envoyer `\"2.5\"` au lieu de `2.5` après une migration vers TanStack (pas de `parse`)."],
  [Q("`errors.email?.message` (RHF) devient en TanStack Form…", ["form.errors.email", "le message de field.state.meta.errors[0] dans le form.Field email", "form.getError('email')", "pareil"], 1, "Les erreurs sont portées par chaque champ."),
   Q("Après migration vers TanStack, l'estimation arrive en \"2.5\". Pourquoi ?", ["bug de zod", "onSubmit reçoit les valeurs brutes : il faut schema.parse(value)", "il faut valueAsNumber dans zod", "le serveur"], 1, "Avec RHF, le resolver renvoyait les données converties."),
   Q("Pourquoi `forwardRef` dans `ChampTexte` ?", ["pour le style", "register de RHF passe une ref à l'input (focus sur erreur, lecture)", "pour TanStack", "obligatoire en React 18 pour tous les composants"], 1, "Sans la ref, RHF ne peut pas lire l'input ni le focus.")],
  prereq=[
    P("Migration", "Réécrire un formulaire avec une autre bibliothèque **sans changer son comportement** (les tests restent verts)."),
    P("Composant de présentation", "Un composant qui affiche (label, input, erreur) sans savoir quelle bibliothèque gère l'état."),
    P("`forwardRef`", "En React 18, permet à un composant de transmettre la `ref` reçue à un élément interne (en React 19, `ref` est une prop normale)."),
    P("`aria-invalid` / `aria-describedby`", "Attributs d'accessibilité : le champ est en erreur, et son message d'erreur est tel élément (lu par les lecteurs d'écran)."),
  ],
  diagram=D(
    nodes=[
      N("z", 0, 1, "Schéma zod", "les règles", kind="doc", color="accent"),
      N("rhf", 1, 0, "React Hook Form", "register / Controller", kind="box", color="warn"),
      N("tsf", 1, 2, "TanStack Form", "form.Field / AppField", kind="box", color="good"),
      N("ui", 2, 1, "ChampTexte, Etoiles…", "composants sans bibliothèque", kind="file", color="accent"),
      N("api", 3, 1, "API", "mêmes données", kind="db", color="muted"),
    ],
    edges=[E("z", "rhf"), E("z", "tsf"), E("rhf", "ui"), E("tsf", "ui"), E("ui", "api", dashed=True)],
    caption="Les règles (zod) et l'apparence (composants) sont partagées ; seule la colle du milieu change d'une bibliothèque à l'autre."),
  lessons=[
    L("La table de correspondance", r"""
| Besoin | React Hook Form | TanStack Form |
|---|---|---|
| créer | `useForm({ defaultValues, resolver, mode })` | `useForm({ defaultValues, validators, onSubmit })` |
| brancher un input | `{...register('titre')}` | `<form.Field name="titre" children={(f) => <input value={f.state.value} onChange={(e) => f.handleChange(e.target.value)} onBlur={f.handleBlur} />} />` |
| composant maison | `<Controller render={({ field }) => …} />` | rien de spécial (tout est déjà contrôlé) |
| règles | `register('x', { required, minLength… })` ou `resolver: zodResolver(s)` | `validators={{ onChange, onBlur, onSubmit }}` par champ, ou `validators: { onChange: s }` sur le form |
| moment de validation | `mode: 'onSubmit' \| 'onBlur' \| 'onTouched' \| 'onChange'` | la **clé** du validateur (`onBlur: …`) |
| erreur d'un champ | `formState.errors.titre?.message` | `field.state.meta.errors[0]` (objet zod → `.message`) |
| touché / modifié | `formState.touchedFields.titre`, `isDirty` | `field.state.meta.isTouched`, `isDirty` |
| envoi | `<form onSubmit={handleSubmit(fn)}>` | `<form onSubmit={(e) => { e.preventDefault(); form.handleSubmit(); }}>` |
| données envoyées | **converties** par le resolver | **brutes** → `schema.parse(value)` |
| en cours d'envoi | `formState.isSubmitting` | `<form.Subscribe selector={(s) => s.isSubmitting}>` |
| lire une valeur en direct | `watch('x')` / `useWatch` | `form.Subscribe` / `useStore(form.store, (s) => s.values.x)` |
| liste | `useFieldArray` → `append`, `remove`, `fields[i].id` | `mode="array"` → `pushValue`, `removeValue` |
| erreur serveur | `setError('email', { message })` | `onSubmitAsync` → `{ fields: { email: '…' } }` |
| recharger / vider | `reset(valeurs)` | `form.reset(valeurs)` |
| gros formulaire | `FormProvider` + `useFormContext` | `createFormHook` + `useFieldContext` / `useFormContext` |
"""),
    L("Lequel choisir (et pourquoi ton entreprise a les deux)", r"""
**React Hook Form** : le plus répandu, peu de code, très rapide (les inputs ne font pas redessiner le composant). Idéal pour la majorité des formulaires : connexion, contact, profil, paramètres. Moins confortable dès qu'il y a beaucoup de composants maison (un `Controller` pour chacun) ou des validations très fines selon le moment.

**TanStack Form** : plus récent, plus verbeux au premier abord, mais **tout** est typé (un nom de champ faux = erreur TypeScript), chaque validateur choisit son moment (`onBlur` pour l'un, `onChangeAsync` avec debounce pour l'autre), et `createFormHook` donne un kit de champs maison très propre. Bien adapté aux gros formulaires métier dynamiques.

Dans la pratique, une entreprise qui a les deux a souvent : des formulaires historiques en RHF, et les nouveaux écrans (ou une nouvelle équipe) en TanStack Form. Ce qui rend la cohabitation facile :

1. **un schéma zod par formulaire**, utilisable par les deux ;
2. **des composants d'interface sans bibliothèque** (`ChampTexte`, `Etoiles`) ;
3. un petit adaptateur par bibliothèque (le `TextField` de `createFormHook`, ou `register` + `forwardRef`).
"""),
    L("Méthode de migration (et ses pièges)", r"""
1. **Garder les tests** (ou écrire ceux de l'existant) : la migration ne doit rien changer pour l'utilisateur.
2. Reprendre le **même schéma** et les mêmes `defaultValues`.
3. Remplacer champ par champ (table ci-dessus).
4. Vérifier les trois pièges classiques :
   - **conversions** : RHF → TanStack, les données ne sont plus converties : `schema.parse(value)` dans `onSubmit` ; TanStack → RHF : `valueAsNumber` ou `z.coerce` ;
   - **moment de validation** : `mode: 'onTouched'` (RHF) ≈ validateur `onBlur` puis `onChange` (TanStack) ; un schéma en `onBlur` + `onSubmit` sur le formulaire donne un comportement proche ;
   - **affichage des erreurs** : objets zod côté TanStack (`.message`), et la condition « touché » à ajouter toi-même.
5. Après succès : `reset()` dans les deux cas (sinon les champs gardent leurs valeurs et leurs états).
"""),
  ],
  recap=["Mêmes concepts, deux syntaxes : garde la table de correspondance à portée.",
         "Schéma zod et composants d'interface partagés ; seule la colle change.",
         "RHF : données converties ; TanStack : valeurs brutes → `schema.parse`.",
         "Composant d'input partagé : `forwardRef` + `aria-invalid` + `aria-describedby`."],
  example=F("Correspondance.tsx", "tsx", r"""
// React Hook Form
<input {...register('titre')} />
{errors.titre && <p>{errors.titre.message}</p>}

// TanStack Form
<form.Field name="titre" children={(f) => (
  <>
    <input value={f.state.value} onBlur={f.handleBlur} onChange={(e) => f.handleChange(e.target.value)} />
    {f.state.meta.errors[0] && <p>{f.state.meta.errors[0].message ?? f.state.meta.errors[0]}</p>}
  </>
)} />
"""),
  notes=["Un `register` devient un `form.Field` avec value / onChange / onBlur.", "`errors.x.message` devient le premier élément de `meta.errors`."],
  tds=[
    TD(1, "Migrer un formulaire de React Hook Form vers TanStack Form",
       "L'équipe passe ce formulaire en TanStack Form. Réécris `NouvelleTache.tsx` **sans changer son comportement** : les tests sont ceux de la version actuelle (RHF), ils doivent rester verts." + EX,
       ["`NouvelleTache.tsx` n'importe plus `react-hook-form`, mais `@tanstack/react-form` ; le schéma `tacheSchema` (fourni) reste la source des règles",
        "Mêmes `name`, mêmes messages, mêmes `id` d'erreur ; erreurs au **blur**, puis corrigées en direct, et toutes à l'envoi",
        "Données envoyées **converties** : titre sans espaces autour, estimation en nombre",
        "Bouton `Création…` désactivé pendant l'envoi ; après succès : `Tâche « … » créée` et formulaire remis à zéro"],
       [F("schema.ts", "ts", TACHE_SCHEMA), F("NouvelleTache.tsx", "tsx", TACHE_RHF)],
       ["`mode: 'onTouched'` n'existe pas : valide en direct (`validators: { onChange: tacheSchema, onSubmit: tacheSchema }`) et n'affiche l'erreur que si `field.state.meta.isBlurred` ou après un envoi (`useStore(form.store, (s) => s.submissionAttempts > 0)`).",
        "`onSubmit: async ({ value }) => { const t = tacheSchema.parse(value); … form.reset(); }`",
        "Le `<select>` devient aussi un `form.Field` : `value={f.state.value} onChange={(e) => f.handleChange(e.target.value)}`."],
       [F("schema.ts", "ts", TACHE_SCHEMA), F("NouvelleTache.tsx", "tsx", TACHE_TSF)],
       ["Les mêmes tests qu'avant la migration", "Plus d'import de react-hook-form"],
       run=FRUN("NouvelleTache.tsx", api=TACHE_API, tests=r"""
assert(!/react-hook-form/.test(source('NouvelleTache.tsx')), 'NouvelleTache.tsx n\'importe plus react-hook-form');
assert(/@tanstack\/react-form/.test(source('NouvelleTache.tsx')), 'NouvelleTache.tsx utilise TanStack Form');
""" + TACHE_TESTS)),
    TD(2, "Et dans l'autre sens : de TanStack Form vers React Hook Form",
       "Une autre équipe veut ce formulaire en React Hook Form, comme le reste de son application. Fais la migration inverse, mêmes tests." + EX,
       ["`NouvelleTache.tsx` n'importe plus `@tanstack/react-form`, mais `react-hook-form` (+ `zodResolver`)",
        "Validation au premier blur puis en direct (`mode: 'onTouched'`) ; mêmes messages et `id`",
        "Données converties par le schéma (le resolver s'en charge)",
        "`Création…` pendant l'envoi ; après succès, message et `reset()`"],
       [F("schema.ts", "ts", TACHE_SCHEMA), F("NouvelleTache.tsx", "tsx", TACHE_TSF)],
       ["`useForm({ resolver: zodResolver(tacheSchema), mode: 'onTouched', defaultValues: { titre: '', priorite: 'normale', estimation: '' } })`.",
        "Chaque `form.Field` devient un `{...register('…')}` ; le `<select>` aussi.",
        "`handleSubmit(creer)` : `creer` reçoit déjà l'estimation en nombre."],
       [F("schema.ts", "ts", TACHE_SCHEMA), F("NouvelleTache.tsx", "tsx", TACHE_RHF)],
       ["Le code devient plus court", "Le comportement ne change pas"],
       run=FRUN("NouvelleTache.tsx", api=TACHE_API, tests=r"""
assert(!/@tanstack\/react-form/.test(source('NouvelleTache.tsx')), 'NouvelleTache.tsx n\'importe plus TanStack Form');
assert(/from ['"]react-hook-form['"]/.test(source('NouvelleTache.tsx')), 'NouvelleTache.tsx utilise React Hook Form');
""" + TACHE_TESTS)),
    TD(3, "Un champ d'interface partagé par les deux",
       "Le design system de l'entreprise veut **un seul** composant `ChampTexte` (label, input, message d'erreur, accessibilité) utilisé par les formulaires RHF **et** TanStack. Les deux formulaires sont fournis ; le `ChampTexte` actuel casse le formulaire RHF (la valeur n'est jamais lue) et n'est pas accessible." + EX,
       ["`ChampTexte({ label, erreur, ...inputProps })` : `<label htmlFor>` relié à l'`<input id>` (avec `useId`) ; toutes les autres props vont sur l'input",
        "Il transmet la `ref` à l'input (`forwardRef`) : RHF peut lire la valeur et **mettre le focus** sur le 1er champ en erreur",
        "En erreur : `aria-invalid=\"true\"` sur l'input et `aria-describedby` = id du `<p role=\"alert\">` qui contient le message",
        "Les deux formulaires (`FormRHF`, `FormTanStack`) fonctionnent avec le même composant"],
       [F("ChampTexte.tsx", "tsx", r"""
type Props = React.InputHTMLAttributes<HTMLInputElement> & { label: string; erreur?: string };

export function ChampTexte({ label, erreur, ...inputProps }: Props) {
  return (
    <div className="champ">
      <label>{label}</label>
      <input {...inputProps} />
      {erreur && <p className="erreur">{erreur}</p>}
    </div>
  );
}
"""), F("Formulaires.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm as useFormRHF } from 'react-hook-form';
import { useForm } from '@tanstack/react-form';
import { ChampTexte } from './ChampTexte';

function FormRHF() {
  const [ok, setOk] = useState('');
  const { register, handleSubmit, formState: { errors } } = useFormRHF({ defaultValues: { prenom: '', ville: '' } });
  return (
    <form id="rhf" onSubmit={handleSubmit((d) => setOk('RHF : ' + d.prenom + ', ' + d.ville))}>
      <ChampTexte label="Prénom" {...register('prenom', { required: 'Prénom requis' })} erreur={errors.prenom?.message} />
      <ChampTexte label="Ville" {...register('ville', { required: 'Ville requise' })} erreur={errors.ville?.message} />
      <button type="submit">Envoyer (RHF)</button>
      {ok && <p className="ok">{ok}</p>}
    </form>
  );
}

function FormTanStack() {
  const [ok, setOk] = useState('');
  const form = useForm({ defaultValues: { prenom: '' }, onSubmit: ({ value }) => setOk('TanStack : ' + value.prenom) });
  return (
    <form id="tsf" onSubmit={(e) => { e.preventDefault(); form.handleSubmit(); }}>
      <form.Field
        name="prenom"
        validators={{ onChange: ({ value }) => (!value ? 'Prénom requis' : undefined) }}
        children={(f) => (
          <ChampTexte
            label="Prénom"
            name={f.name}
            value={f.state.value}
            onBlur={f.handleBlur}
            onChange={(e) => f.handleChange(e.target.value)}
            erreur={f.state.meta.isTouched ? f.state.meta.errors[0] as string | undefined : undefined}
          />
        )}
      />
      <button type="submit">Envoyer (TanStack)</button>
      {ok && <p className="ok">{ok}</p>}
    </form>
  );
}

export default function Formulaires() {
  return (
    <>
      <FormRHF />
      <FormTanStack />
    </>
  );
}
""")],
       ["`export const ChampTexte = forwardRef<HTMLInputElement, Props>(function ChampTexte({ label, erreur, ...inputProps }, ref) { … })` et `<input ref={ref} … />`.",
        "`const id = useId(); const idErreur = id + '-erreur';` puis `<label htmlFor={id}>` et `<input id={id} …>`.",
        "`aria-invalid={erreur ? true : undefined}` et `aria-describedby={erreur ? idErreur : undefined}` ; le `<p>` a `id={idErreur}` et `role=\"alert\"`."],
       [F("ChampTexte.tsx", "tsx", CHAMP_TEXTE), F("Formulaires.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm as useFormRHF } from 'react-hook-form';
import { useForm } from '@tanstack/react-form';
import { ChampTexte } from './ChampTexte';

function FormRHF() {
  const [ok, setOk] = useState('');
  const { register, handleSubmit, formState: { errors } } = useFormRHF({ defaultValues: { prenom: '', ville: '' } });
  return (
    <form id="rhf" onSubmit={handleSubmit((d) => setOk('RHF : ' + d.prenom + ', ' + d.ville))}>
      <ChampTexte label="Prénom" {...register('prenom', { required: 'Prénom requis' })} erreur={errors.prenom?.message} />
      <ChampTexte label="Ville" {...register('ville', { required: 'Ville requise' })} erreur={errors.ville?.message} />
      <button type="submit">Envoyer (RHF)</button>
      {ok && <p className="ok">{ok}</p>}
    </form>
  );
}

function FormTanStack() {
  const [ok, setOk] = useState('');
  const form = useForm({ defaultValues: { prenom: '' }, onSubmit: ({ value }) => setOk('TanStack : ' + value.prenom) });
  return (
    <form id="tsf" onSubmit={(e) => { e.preventDefault(); form.handleSubmit(); }}>
      <form.Field
        name="prenom"
        validators={{ onChange: ({ value }) => (!value ? 'Prénom requis' : undefined) }}
        children={(f) => (
          <ChampTexte
            label="Prénom"
            name={f.name}
            value={f.state.value}
            onBlur={f.handleBlur}
            onChange={(e) => f.handleChange(e.target.value)}
            erreur={f.state.meta.isTouched ? f.state.meta.errors[0] as string | undefined : undefined}
          />
        )}
      />
      <button type="submit">Envoyer (TanStack)</button>
      {ok && <p className="ok">{ok}</p>}
    </form>
  );
}

export default function Formulaires() {
  return (
    <>
      <FormRHF />
      <FormTanStack />
    </>
  );
}
""")],
       ["RHF peut lire et focus l'input grâce à la ref", "Le message d'erreur est relié à son champ"],
       run=FRUN("Formulaires.tsx", tests=r"""
const rhf = $('#rhf'), tsf = $('#tsf');
const inp = (f, n) => f.querySelector('input[name=' + n + ']');
const lab = rhf.querySelector('label');
assert(lab && lab.htmlFor && document.getElementById(lab.htmlFor) === inp(rhf, 'prenom'), 'Le label est relié à l\'input (htmlFor = id)');
await submit(rhf);
await tick(120);
assert(document.activeElement === inp(rhf, 'prenom'), 'RHF : focus automatique sur le 1er champ en erreur (la ref est transmise)');
const p = inp(rhf, 'prenom');
assert.equal(p.getAttribute('aria-invalid'), 'true', 'En erreur : aria-invalid="true"');
const desc = p.getAttribute('aria-describedby');
const msg = desc && document.getElementById(desc);
assert(msg && msg.textContent === 'Prénom requis' && msg.getAttribute('role') === 'alert', 'aria-describedby pointe vers le message (role="alert")');
await type(inp(rhf, 'prenom'), 'Ana');
await type(inp(rhf, 'ville'), 'Lyon');
await submit(rhf);
await waitFor(() => rhf.querySelector('.ok'), 2000);
assert.equal(rhf.querySelector('.ok').textContent, 'RHF : Ana, Lyon', 'RHF lit les valeurs à travers ChampTexte');
assert(!inp(rhf, 'prenom').hasAttribute('aria-invalid'), 'Sans erreur : pas d\'aria-invalid');
await type(inp(tsf, 'prenom'), 'x');
await type(inp(tsf, 'prenom'), '');
await tick(60);
const tp = inp(tsf, 'prenom');
assert(tp.getAttribute('aria-invalid') === 'true' && document.getElementById(tp.getAttribute('aria-describedby') || 'x'), 'TanStack : même composant, même accessibilité');
await type(tp, 'Léo');
await submit(tsf);
await waitFor(() => tsf.querySelector('.ok'), 2000);
assert.equal(tsf.querySelector('.ok').textContent, 'TanStack : Léo', 'Le formulaire TanStack fonctionne avec le même composant');
const ids = $$('input').map((i) => i.id);
assert(ids.every(Boolean) && new Set(ids).size === ids.length, 'Chaque input a un id unique (useId)');
""")),
  ])

MODULES = [main, rhf, rhf2, tsf, tsf2, compare]

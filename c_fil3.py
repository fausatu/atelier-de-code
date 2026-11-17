"""Parcours « Projet fil rouge : Bobine », modules 7 à 9 : formulaire de profil, Git en équipe, lancer le projet en local."""
from common import P, L, D, N, E, LANE, F, TD, RUN
from c_fil import FM, Q, JS

# =========================================================================== 7. Le formulaire de profil
PROFILS_API = r"""
const db = window.__db = {
  forfait: { nom: 'Essentiel', max: 3 },
  profils: [{ id: 1, nom: 'Ana', enfant: false, age: null }],
  nextId: 2,
  posts: [],
  patches: [],
};
const violation = (champ, message) => [422, { title: 'Validation Failed', violations: [{ propertyPath: champ, title: message }] }];
const verifierNom = (nom) => {
  const n = String(nom ?? '').trim();
  if (n === '') return violation('nom', 'Donne un nom au profil');
  if (n.length > 20) return violation('nom', '20 caractères maximum');
  return null;
};
__api["GET /api/profils"] = () => db.profils;
__api["POST /api/profils"] = (p, b) => {
  b = b || {}; db.posts.push(b);
  const v = verifierNom(b.nom); if (v) return v;
  if (b.age !== null && b.age !== undefined && (typeof b.age !== 'number' || b.age < 0 || b.age > 17)) return violation('age', "L'âge d'un profil enfant va de 0 à 17 ans");
  if (db.profils.some((x) => x.nom.toLowerCase() === String(b.nom).trim().toLowerCase())) return [409, { error: 'Le profil ' + String(b.nom).trim() + ' existe déjà' }];
  if (db.profils.length >= db.forfait.max) return [409, { error: 'Ton forfait ' + db.forfait.nom + ' permet ' + db.forfait.max + ' profils' }];
  const pr = { id: db.nextId++, nom: String(b.nom).trim(), enfant: b.age !== null && b.age !== undefined, age: b.age ?? null };
  db.profils.push(pr);
  return [201, pr, { Location: '/api/profils/' + pr.id }];
};
__api["PATCH /api/profils/:id"] = (p, b) => {
  b = b || {}; db.patches.push({ id: Number(p.id), ...b });
  const pr = db.profils.find((x) => x.id == p.id);
  if (!pr) return [404, { error: 'Profil introuvable' }];
  const v = verifierNom(b.nom); if (v) return v;
  if (db.profils.some((x) => x.id !== pr.id && x.nom.toLowerCase() === String(b.nom).trim().toLowerCase())) return [409, { error: 'Le profil ' + String(b.nom).trim() + ' existe déjà' }];
  pr.nom = String(b.nom).trim();
  return pr;
};
"""

FCLIENT = F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });
""")

FPROFILS = F("api/profils.ts", "ts", r"""
import { api } from './client';

export type Profil = { id: number; nom: string; enfant: boolean; age: number | null };
export type NouveauProfil = { nom: string; age: number | null };

export async function getProfils(): Promise<Profil[]> {
  const res = await api.get<Profil[]>('/profils');
  return res.data;
}

export async function creerProfil(body: NouveauProfil): Promise<Profil> {
  const res = await api.post<Profil>('/profils', body);
  return res.data;
}

export async function renommerProfil(id: number, nom: string): Promise<Profil> {
  const res = await api.patch<Profil>(`/profils/${id}`, { nom });
  return res.data;
}
""")

SCHEMA_SOL = r"""
import { z } from 'zod';

export const profilSchema = z
  .object({
    nom: z.string().trim().min(1, 'Donne un nom au profil').max(20, '20 caractères maximum'),
    enfant: z.boolean(),
    age: z.string(),
  })
  .refine((v) => !v.enfant || (/^\d+$/.test(v.age) && Number(v.age) <= 17), {
    message: "L'âge d'un profil enfant va de 0 à 17 ans",
    path: ['age'],
  });

export type ValeursProfil = z.input<typeof profilSchema>;

export function versApi(v: z.output<typeof profilSchema>) {
  return { nom: v.nom, age: v.enfant ? Number(v.age) : null };
}
"""

FSCHEMA = F("schema.ts", "ts", SCHEMA_SOL)

FERREURS = F("api/erreurs.ts", "ts", r"""
import axios from 'axios';

export type Violation = { propertyPath: string; title: string };

/** 422 → la liste des violations ; sinon une liste vide. */
export function violations(err: unknown): Violation[] {
  if (axios.isAxiosError(err) && err.response?.status === 422) return err.response.data.violations ?? [];
  return [];
}

/** Message général : 409 → le message du serveur ; réseau → « Connexion impossible » ; autre → générique. */
export function messageGeneral(err: unknown): string {
  if (!axios.isAxiosError(err)) return 'Erreur inattendue';
  if (!err.response) return 'Connexion impossible, réessaie';
  if (err.response.status === 409) return err.response.data.error;
  return 'Impossible d\'enregistrer le profil';
}
""")

APP_FORM = F("App.tsx", "tsx", r"""
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { getProfils } from './api/profils';
import { FormulaireProfil } from './FormulaireProfil';

const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });

function Profils() {
  const { data } = useQuery({ queryKey: ['profils'], queryFn: getProfils });
  return <ul aria-label="Profils">{data?.map((p) => <li key={p.id}>{p.nom}{p.enfant ? ` (${p.age} ans)` : ''}</li>)}</ul>;
}

export default function App() {
  return (
    <QueryClientProvider client={client}>
      <Profils />
      <FormulaireProfil />
    </QueryClientProvider>
  );
}
""")

FORM_SOL = r"""
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQueryClient } from '@tanstack/react-query';
import { profilSchema, versApi, type ValeursProfil } from './schema';
import { creerProfil } from './api/profils';
import { violations, messageGeneral } from './api/erreurs';

export function FormulaireProfil() {
  const qc = useQueryClient();
  const { register, handleSubmit, watch, reset, setError, formState: { errors, isSubmitting } } = useForm<ValeursProfil>({
    resolver: zodResolver(profilSchema),
    defaultValues: { nom: '', enfant: false, age: '' },
  });
  const enfant = watch('enfant');

  async function envoyer(v: ValeursProfil) {
    try {
      await creerProfil(versApi(profilSchema.parse(v)));
      reset();
      await qc.invalidateQueries({ queryKey: ['profils'] });
    } catch (err) {
      const vs = violations(err);
      if (vs.length) {
        for (const x of vs) setError(x.propertyPath as 'nom' | 'age', { type: 'server', message: x.title });
        return;
      }
      setError('root.serveur', { message: messageGeneral(err) });
    }
  }

  return (
    <form onSubmit={handleSubmit(envoyer)}>
      <label>Nom <input {...register('nom')} /></label>
      {errors.nom && <p role="alert" id="erreur-nom">{errors.nom.message}</p>}
      <label><input type="checkbox" {...register('enfant')} /> Profil enfant</label>
      {enfant && <label>Âge <input {...register('age')} /></label>}
      {errors.age && <p role="alert" id="erreur-age">{errors.age.message}</p>}
      {errors.root?.serveur && <p role="alert" id="erreur-serveur">{errors.root.serveur.message}</p>}
      <button type="submit" disabled={isSubmitting}>Créer le profil</button>
    </form>
  );
}
"""

form = FM("fil-formulaire", "Le formulaire de profil (React Hook Form + zod)", 45,
  "Construire le formulaire « Ajouter un profil » de Bobine : validation immédiate avec zod, envoi avec axios, erreurs du serveur (422 sous le bon champ, 409 en message général) et liste rafraîchie avec React Query.",
  "L'API des profils (module 4) refuse un nom vide (422), un nom déjà pris ou un forfait plein (409). Côté écran, la personne doit comprendre **tout de suite** ce qui ne va pas, sans attendre le serveur quand c'est possible, et voir le message du serveur au bon endroit quand c'est lui qui refuse. C'est le travail du formulaire.",
  ["La personne remplit le formulaire ; React Hook Form garde les valeurs.",
   "À l'envoi, le schéma **zod** vérifie d'abord (nom vide, âge manquant) : en cas d'erreur, rien ne part.",
   "Sinon, `versApi` convertit les valeurs en corps d'API, et axios envoie `POST /api/profils`.",
   "201 : on vide le formulaire et on **invalide** `['profils']` : React Query recharge la liste.",
   "422 : chaque violation va sous **son** champ (`setError`) ; 409 : un message général au-dessus du bouton."],
  ["Deux validations : zod dans le front pour le **confort** (réponse immédiate), le DTO Symfony pour la **vérité** (le serveur décide toujours).",
   "Les valeurs du formulaire (`enfant`, `age` en texte) ne sont pas le corps de l'API (`age` en nombre ou `null`) : une petite fonction `versApi` fait la conversion.",
   "422 = un champ est en cause → `setError('nom', …)` ; 409 = la demande contredit l'état → `setError('root.serveur', …)`.",
   "Après une création : `reset()` pour vider, `invalidateQueries(['profils'])` pour que la liste se recharge, sans la modifier à la main.",
   "Les fonctions de `api/` laissent passer les erreurs ; c'est le formulaire qui les traduit."],
  ["Afficher les erreurs serveur dans un `useState` à part : elles ne disparaissent pas quand on corrige le champ.",
   "Envoyer `age: '8'` (texte) ou `age: ''` : le serveur attend un nombre ou `null`.",
   "Oublier `invalidateQueries` : le profil est créé mais la liste ne bouge pas.",
   "Recopier la liste dans un state après la création (`setProfils([...profils, nouveau])`) au lieu d'invalider.",
   "Attraper l'erreur dans `creerProfil` : le formulaire ne sait plus qu'il y en a eu une."],
  [Q("Le serveur répond 409 « Ton forfait Essentiel permet 3 profils ». Où l'afficher ?", ["sous le champ nom", "dans `errors.root.serveur`, au-dessus du bouton", "dans la console", "nulle part, on réessaie"], 1, "Ce n'est la faute d'aucun champ : c'est un message général."),
   Q("Pourquoi valider avec zod si le serveur valide déjà ?", ["le serveur ne valide pas", "pour répondre tout de suite sans aller-retour réseau ; le serveur reste la référence", "pour remplacer la validation du serveur", "zod est obligatoire avec React Hook Form"], 1, "Le front valide pour le confort, le serveur pour la sécurité : quelqu'un peut appeler l'API sans passer par ton formulaire."),
   Q("Après `POST` réussi, la liste ne montre pas le nouveau profil. Il manque :", ["`reset()`", "`invalidateQueries({ queryKey: ['profils'] })`", "`setError`", "un `useEffect`"], 1, "Invalider la clé dit à React Query que la liste est périmée : il la recharge."),
   Q("La case « Profil enfant » est cochée et l'âge est vide. Qui l'empêche ?", ["le `.refine` du schéma zod, avec `path: ['age']`", "le navigateur", "axios", "le serveur seulement"], 0, "La règle concerne deux champs : c'est un `.refine` sur l'objet, rattaché à `age` par `path`.")],
  [P("React Hook Form (RHF)", "La bibliothèque de formulaires vue dans le parcours Formulaires : `useForm()` donne `register` (brancher un champ), `handleSubmit` (envoyer si tout est valide) et `formState.errors` (les erreurs par champ)."),
   P("zod et `zodResolver`", "Un schéma zod décrit les règles ; `resolver: zodResolver(schema)` dit à React Hook Form de valider avec lui. Les messages du schéma arrivent dans `errors`."),
   P("`setError(champ, { message })`", "Ajoute une erreur à la main dans React Hook Form, par exemple une erreur renvoyée par le serveur. `'root.serveur'` à la place d'un nom de champ = une erreur générale, lue dans `errors.root?.serveur?.message`."),
   P("`watch('champ')`", "Lit la valeur actuelle d'un champ et redessine le composant quand elle change : pratique pour n'afficher « Âge » que si la case « enfant » est cochée."),
   P("`reset()`", "Remet le formulaire à ses valeurs de départ (les `defaultValues`) et efface les erreurs."),
   P("`invalidateQueries`", "Dit à React Query qu'une donnée en cache est périmée (`queryKey: ['profils']`) : les composants qui l'affichent la rechargent."),
   P("Violation", "Une erreur de validation renvoyée par Symfony dans un 422 : `{ propertyPath: 'nom', title: 'Donne un nom au profil' }`. `propertyPath` dit quel champ est en cause."),
  ],
  D(
    nodes=[
      N("form", 0, 0, "Formulaire", "register, watch", kind="file", color="accent"),
      N("zod", 0, 1, "Schéma zod", "nom, enfant + âge", kind="doc", color="warn"),
      N("api", 1, 1, "creerProfil", "axios POST /profils", kind="file"),
      N("srv", 2, 1, "Symfony", "DTO + règles métier"),
      N("ok", 2, 0, "201", "reset + invalider ['profils']", kind="pill", color="good"),
      N("ko", 1, 2, "422 / 409", "setError(champ | root)", kind="pill", color="bad"),
    ],
    edges=[E("form", "zod", "handleSubmit"), E("zod", "api", "versApi"), E("api", "srv", "HTTP"), E("srv", "ok", color="good"), E("srv", "ko", dashed=True, color="bad"), E("ko", "form", "sous le champ", dashed=True, back=True)],
    lanes=[LANE("Navigateur", 0, 1, "accent"), LANE("Serveur", 2, 2, "tc")],
    caption="Deux barrières : zod refuse tout de suite ce qu'il peut voir, le serveur a toujours le dernier mot. Ses refus reviennent dans le formulaire."),
  [
    L("Deux validations, deux rôles", r"""
Le formulaire « Ajouter un profil » a trois champs : le **nom**, une case **Profil enfant**, et l'**âge** (affiché seulement si la case est cochée). Il y a deux endroits qui vérifient ces valeurs, et ils n'ont pas le même rôle :

- **zod, dans le navigateur** : il répond **tout de suite**, sans réseau. Il connaît les règles de forme (nom vide, trop long, âge manquant ou hors de 0 à 17).
- **Symfony, sur le serveur** : il a toujours **le dernier mot**, parce qu'on peut appeler l'API sans passer par ton formulaire. Lui seul connaît l'état (le nom est-il déjà pris ? le forfait est-il plein ?).

Les refus du serveur arrivent sous deux formes, à afficher à deux endroits différents :

| Réponse | Ce que ça veut dire | Où l'afficher |
|---|---|---|
| **422** + `violations` | un champ précis est invalide (`propertyPath: 'nom'`) | sous ce champ |
| **409** + `error` | la demande est correcte mais contredit l'état (forfait plein, nom pris) | message général, au-dessus du bouton |
| pas de réponse | réseau coupé, serveur éteint | message général |
"""),
    L("Le schéma : les valeurs du formulaire ne sont pas le corps de l'API", r"""
Le formulaire manipule `{ nom: 'Léo', enfant: true, age: '8' }` : l'âge est un **texte** (un `<input>` donne toujours du texte) et `enfant` une case à cocher. L'API, elle, attend `{ nom: 'Léo', age: 8 }`, ou `age: null` pour un adulte. On sépare donc les deux : un **schéma** pour les valeurs du formulaire, et une fonction **`versApi`** qui les convertit.

Ce qu'utilise le schéma (tout vient du parcours Formulaires) :

- `z.string().trim().min(1, message).max(20, message)` : un texte, sans espaces autour, entre 1 et 20 caractères ;
- `z.boolean()` pour la case ; `z.string()` pour l'âge (on le vérifie juste après) ;
- `.refine((v) => condition, { message, path: ['age'] })` : une règle **entre deux champs**. Ici : si `enfant` est vrai, `age` doit être fait de chiffres (`/^\d+$/.test(texte)` teste ça) et valoir au plus 17. `path: ['age']` range l'erreur sous le champ âge.
- `z.input<typeof schema>` : le type des valeurs **avant** validation (celles du formulaire) ; `z.output<…>` : le type **après** (ici le `nom` a été nettoyé par `trim`).

```ts
import { z } from 'zod';

export const profilSchema = z
  .object({
    nom: z.string().trim().min(1, 'Donne un nom au profil').max(20, '20 caractères maximum'),
    enfant: z.boolean(),
    age: z.string(),
  })
  .refine((v) => !v.enfant || (/^\d+$/.test(v.age) && Number(v.age) <= 17), {
    message: "L'âge d'un profil enfant va de 0 à 17 ans",
    path: ['age'],
  });

export type ValeursProfil = z.input<typeof profilSchema>;

export function versApi(v: z.output<typeof profilSchema>) {
  return { nom: v.nom, age: v.enfant ? Number(v.age) : null };
}
```

`versApi` ne valide rien : elle reçoit des valeurs déjà validées et ne fait que changer leur forme. `Number('8')` donne `8`.
"""),
    L("Brancher le formulaire et afficher les erreurs du serveur", r"""
Le composant assemble ce que tu connais déjà. Avant de lire le code, les pièces une par une :

- `useForm({ resolver: zodResolver(profilSchema), defaultValues })` : le formulaire, validé par le schéma.
- `watch('enfant')` : la valeur actuelle de la case, pour n'afficher le champ âge que si elle est cochée.
- `handleSubmit(envoyer)` : valide avec zod ; si tout est bon, appelle `envoyer(valeurs)`.
- Dans `envoyer`, un `try / catch` autour de l'appel axios (`creerProfil`) :
  - succès → `reset()` vide le formulaire, puis `qc.invalidateQueries({ queryKey: ['profils'] })` fait recharger la liste (`qc` vient de `useQueryClient()`) ;
  - erreur 422 → pour chaque violation, `setError(violation.propertyPath, { message: violation.title })` : le message s'affiche **sous le champ**, exactement comme une erreur zod, et disparaît quand on corrige ;
  - autre erreur → `setError('root.serveur', { message })` : une erreur qui n'appartient à aucun champ.
- `profilSchema.parse(v)` renvoie les valeurs **nettoyées** (le nom sans espaces) que `versApi` attend.

Les deux petites fonctions de traduction sont rangées dans `api/erreurs.ts` : `violations(err)` renvoie la liste des violations d'un 422 (sinon une liste vide), et `messageGeneral(err)` le texte à afficher pour tout le reste (le `error` d'un 409, « Connexion impossible » sans réponse).

```tsx
async function envoyer(v: ValeursProfil) {
  try {
    await creerProfil(versApi(profilSchema.parse(v)));
    reset();
    await qc.invalidateQueries({ queryKey: ['profils'] });
  } catch (err) {
    const vs = violations(err);
    if (vs.length) {
      for (const x of vs) setError(x.propertyPath as 'nom' | 'age', { type: 'server', message: x.title });
      return;
    }
    setError('root.serveur', { message: messageGeneral(err) });
  }
}
```

`x.propertyPath as 'nom' | 'age'` dit à TypeScript que le serveur ne renvoie que ces deux noms de champs (`setError` n'accepte que des noms qui existent dans le formulaire).
"""),
    L("Renommer : un formulaire qui part de données existantes", r"""
Pour **modifier** un profil, le formulaire doit démarrer avec le nom actuel. Le piège : les données arrivent de l'API **après** le premier affichage, et `defaultValues` n'est lu qu'à la création du formulaire.

La solution la plus simple : ne créer le formulaire **qu'une fois les données arrivées**. Un composant parent charge (`useQuery`) et affiche « Chargement… » ; quand le profil est là, il affiche un composant enfant qui contient le `useForm`, avec `defaultValues: { nom: profil.nom }`.

Deux outils de plus :

- `formState.isDirty` : `true` si une valeur a changé par rapport à `defaultValues`. On désactive « Enregistrer » tant que rien n'a changé : `disabled={!isDirty || isSubmitting}`.
- Un 409 « nom déjà pris » concerne cette fois **un champ** (le seul du formulaire) : on peut le mettre sous `nom` avec `setError('nom', …)`.
"""),
  ],
  ["Formulaire : `useForm({ resolver: zodResolver(schema), defaultValues })` ; `watch` pour un champ qui dépend d'un autre.",
   "Les valeurs du formulaire ≠ le corps de l'API : `versApi` convertit (`age` texte → nombre ou `null`).",
   "`try { await creerProfil(...) } catch (err) { … }` : 422 → `setError(champ)`, sinon `setError('root.serveur')`.",
   "Succès : `reset()` + `invalidateQueries({ queryKey: ['profils'] })`.",
   "Modifier : créer le formulaire après le chargement (`defaultValues` = données) ; `isDirty` pour le bouton."],
  [FCLIENT, FPROFILS, FSCHEMA, FERREURS, F("FormulaireProfil.tsx", "tsx", FORM_SOL)],
  ["`schema.ts` décrit les valeurs **du formulaire** ; `versApi` les transforme en corps d'API.",
   "`api/profils.ts` et `api/erreurs.ts` ne connaissent pas React : ils se testent seuls.",
   "Dans `envoyer`, la seule logique est le choix de l'endroit où afficher l'erreur : sous un champ (422) ou en général (le reste).",
   "La liste n'est jamais modifiée à la main : `invalidateQueries` la fait recharger.",
   "Le champ âge n'est affiché que si `watch('enfant')` est vrai."],
  [
    TD(1, "Le schéma et la conversion",
       "Écris le schéma zod des valeurs du formulaire et la fonction `versApi`." + JS,
       ["`profilSchema` : `nom` texte nettoyé (`trim`), 1 à 20 caractères, messages « Donne un nom au profil » et « 20 caractères maximum »",
        "`enfant` booléen ; `age` texte",
        "Règle entre champs : si `enfant` est vrai, `age` doit être un nombre entier de 0 à 17, sinon l'erreur « L'âge d'un profil enfant va de 0 à 17 ans » rangée sous `age`",
        "`versApi(v)` → `{ nom, age }` avec `age` en nombre pour un enfant, `null` sinon"],
       [F("schema.ts", "ts", r"""
import { z } from 'zod';

export const profilSchema = z.object({
  // à toi
});

export type ValeursProfil = z.input<typeof profilSchema>;

export function versApi(v: any) {
  // à toi
  return v;
}
""")],
       ["`z.string().trim().min(1, 'Donne un nom au profil').max(20, '20 caractères maximum')`",
        "`.refine((v) => !v.enfant || (/^\\d+$/.test(v.age) && Number(v.age) <= 17), { message: …, path: ['age'] })` après le `z.object({...})`.",
        "`!v.enfant || …` : si ce n'est pas un enfant, la règle est vraie d'office.",
        "`versApi` : `{ nom: v.nom, age: v.enfant ? Number(v.age) : null }`"],
       [FSCHEMA],
       ["Un nom fait d'espaces est refusé", "« enfant » sans âge est refusé sous `age`", "L'âge part en nombre"],
       run=RUN("js", entry="schema.ts", tests=r"""
const { profilSchema, versApi } = require('./schema');
const err = (v) => { const r = profilSchema.safeParse(v); return r.success ? {} : Object.fromEntries(r.error.issues.map((i) => [String(i.path[0]), i.message])); };
const ok = profilSchema.safeParse({ nom: '  Léo ', enfant: true, age: '8' });
assert(ok.success, 'Léo, enfant, 8 ans : valide', JSON.stringify(ok.error && ok.error.issues));
assert.equal(ok.data && ok.data.nom, 'Léo', 'Le nom est nettoyé (trim)');
assert.equal(err({ nom: '   ', enfant: false, age: '' }).nom, 'Donne un nom au profil', 'Nom fait d\'espaces → « Donne un nom au profil »');
assert.equal(err({ nom: 'x'.repeat(21), enfant: false, age: '' }).nom, '20 caractères maximum', '21 caractères → « 20 caractères maximum »');
assert.equal(err({ nom: 'Léo', enfant: true, age: '' }).age, "L'âge d'un profil enfant va de 0 à 17 ans", 'Enfant sans âge → erreur sous age');
assert.equal(err({ nom: 'Léo', enfant: true, age: '18' }).age, "L'âge d'un profil enfant va de 0 à 17 ans", 'Enfant de 18 ans → refusé');
assert.equal(err({ nom: 'Léo', enfant: true, age: 'huit' }).age, "L'âge d'un profil enfant va de 0 à 17 ans", 'Âge « huit » → refusé');
assert(profilSchema.safeParse({ nom: 'Ana', enfant: false, age: '' }).success, 'Adulte sans âge : valide');
assert.deepEqual(versApi({ nom: 'Léo', enfant: true, age: '8' }), { nom: 'Léo', age: 8 }, 'versApi : âge converti en nombre');
assert.deepEqual(versApi({ nom: 'Ana', enfant: false, age: '12' }), { nom: 'Ana', age: null }, 'versApi : adulte → age null');
""")),
    TD(2, "Le formulaire « Ajouter un profil »",
       "La liste des profils et le schéma sont fournis. Écris `FormulaireProfil` : validation zod, envoi, erreurs du serveur, liste rafraîchie. Le faux serveur a déjà le profil « Ana » et le forfait permet 3 profils." + JS,
       ["Champs : `nom`, case `enfant` (« Profil enfant »), et `age` affiché **seulement** si la case est cochée",
        "Erreurs affichées dans `<p role=\"alert\" id=\"erreur-nom\">`, `id=\"erreur-age\"` et, pour une erreur générale, `id=\"erreur-serveur\"`",
        "Envoi : `creerProfil(versApi(profilSchema.parse(valeurs)))` ; aucune requête si zod refuse",
        "Succès : formulaire vidé (`reset`) et liste rechargée (`invalidateQueries({ queryKey: ['profils'] })`)",
        "422 : chaque violation sous son champ (`setError`) ; 409 ou autre : `setError('root.serveur', …)` avec `messageGeneral(err)`"],
       [FCLIENT, FPROFILS, FSCHEMA, FERREURS, APP_FORM, F("FormulaireProfil.tsx", "tsx", r"""
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQueryClient } from '@tanstack/react-query';
import { profilSchema, versApi, type ValeursProfil } from './schema';
import { creerProfil } from './api/profils';
import { violations, messageGeneral } from './api/erreurs';

export function FormulaireProfil() {
  // à toi
  return <form><p>À compléter</p></form>;
}
""")],
       ["`const { register, handleSubmit, watch, reset, setError, formState: { errors, isSubmitting } } = useForm<ValeursProfil>({ resolver: zodResolver(profilSchema), defaultValues: { nom: '', enfant: false, age: '' } });`",
        "`const qc = useQueryClient();` puis, après le succès : `await qc.invalidateQueries({ queryKey: ['profils'] });`",
        "Case à cocher : `<input type=\"checkbox\" {...register('enfant')} />` donne un booléen.",
        "`{errors.root?.serveur && <p role=\"alert\" id=\"erreur-serveur\">{errors.root.serveur.message}</p>}`"],
       [F("FormulaireProfil.tsx", "tsx", FORM_SOL)],
       ["zod bloque avant le réseau", "Le 409 s'affiche en message général", "Le 422 s'affiche sous le champ"],
       run=RUN("react", entry="App.tsx", api=PROFILS_API, tests=r"""
const err = (n) => { const e = $('#erreur-' + n); return e ? e.textContent : ''; };
await waitFor(() => $$('ul[aria-label=Profils] li').length === 1, 3000);
assert(!$('[name=age]'), 'Case décochée : pas de champ âge');
await submit('form');
await waitFor(() => err('nom') !== '', 2000);
assert.equal(err('nom'), 'Donne un nom au profil', 'Nom vide : erreur de zod sous le nom');
assert.equal(window.__db.posts.length, 0, 'zod a refusé : aucune requête envoyée');
await type('[name=nom]', 'Léo');
await click('[name=enfant]');
await waitFor(() => $('[name=age]'), 2000);
assert($('[name=age]'), 'Case cochée : le champ âge apparaît (watch)');
await submit('form');
await waitFor(() => err('age') !== '', 2000);
assert.equal(err('age'), "L'âge d'un profil enfant va de 0 à 17 ans", 'Enfant sans âge : erreur sous l\'âge');
await type('[name=age]', '8');
await submit('form');
await waitFor(() => $$('ul[aria-label=Profils] li').length === 2, 3000);
assert.deepEqual(window.__db.posts[0], { nom: 'Léo', age: 8 }, 'Corps envoyé : { nom: "Léo", age: 8 } (versApi)');
assert.includes(text(), 'Léo (8 ans)', 'La liste a été rechargée (invalidateQueries)');
assert.equal($('[name=nom]').value, '', 'Le formulaire est vidé (reset)');
await type('[name=nom]', 'ana');
await submit('form');
await waitFor(() => err('serveur') !== '', 3000);
assert.equal(err('serveur'), 'Le profil ana existe déjà', '409 : message général du serveur');
window.__api['POST /api/profils'] = () => [422, { title: 'Validation Failed', violations: [{ propertyPath: 'nom', title: 'Ce nom contient un mot interdit' }] }];
await type('[name=nom]', 'Zoé');
await submit('form');
await waitFor(() => err('nom') !== '', 3000);
assert.equal(err('nom'), 'Ce nom contient un mot interdit', '422 : la violation s\'affiche sous le nom (setError)');
""")),
    TD(3, "Renommer un profil",
       "Écris l'écran « Renommer » d'un profil existant : il démarre avec le nom actuel, le bouton n'est actif que si le nom a changé, et un nom déjà pris s'affiche sous le champ." + JS,
       ["`Renommer({ id })` charge les profils avec `useQuery({ queryKey: ['profils'], queryFn: getProfils })` et y trouve le profil ; « Chargement… » tant qu'il n'est pas là ; « Profil introuvable » s'il n'existe pas",
        "Le formulaire est dans un composant à part, `FormRenommer({ profil })`, avec `defaultValues: { nom: profil.nom }`",
        "Règle zod : nom nettoyé, 1 à 20 caractères (mêmes messages qu'au TD 1)",
        "Bouton « Enregistrer » désactivé tant que `!isDirty` ou pendant l'envoi",
        "`renommerProfil(id, nom)` ; succès → `<p>Profil renommé</p>` et liste invalidée ; 409 ou 422 → message sous le champ (`id=\"erreur-nom\"`)"],
       [FCLIENT, FPROFILS, FERREURS, F("App.tsx", "tsx", r"""
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Renommer } from './Renommer';

const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });

export default function App() {
  return <QueryClientProvider client={client}><Renommer id={2} /></QueryClientProvider>;
}
"""), F("Renommer.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import axios from 'axios';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getProfils, renommerProfil, type Profil } from './api/profils';
import { violations } from './api/erreurs';

const schema = z.object({ nom: z.string() });   // à compléter

export function Renommer({ id }: { id: number }) {
  // à toi
  return <p>À compléter</p>;
}
""")],
       ["`const profil = data?.find((p) => p.id === id);` puis `if (!data) return <p>Chargement…</p>;`",
        "Le composant enfant : `function FormRenommer({ profil }: { profil: Profil }) { const { register, handleSubmit, setError, formState: { errors, isDirty, isSubmitting } } = useForm({ resolver: zodResolver(schema), defaultValues: { nom: profil.nom } }); … }`",
        "409 : `axios.isAxiosError(err) && err.response?.status === 409` → `setError('nom', { message: err.response.data.error })` ; 422 : `violations(err)`."],
       [F("Renommer.tsx", "tsx", r"""
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import axios from 'axios';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getProfils, renommerProfil, type Profil } from './api/profils';
import { violations } from './api/erreurs';

const schema = z.object({ nom: z.string().trim().min(1, 'Donne un nom au profil').max(20, '20 caractères maximum') });
type Valeurs = z.input<typeof schema>;

export function Renommer({ id }: { id: number }) {
  const { data } = useQuery({ queryKey: ['profils'], queryFn: getProfils });
  if (!data) return <p>Chargement…</p>;
  const profil = data.find((p) => p.id === id);
  if (!profil) return <p>Profil introuvable</p>;
  return <FormRenommer profil={profil} />;
}

function FormRenommer({ profil }: { profil: Profil }) {
  const qc = useQueryClient();
  const [ok, setOk] = useState(false);
  const { register, handleSubmit, reset, setError, formState: { errors, isDirty, isSubmitting } } = useForm<Valeurs>({
    resolver: zodResolver(schema),
    defaultValues: { nom: profil.nom },
  });

  async function envoyer(v: Valeurs) {
    setOk(false);
    try {
      const p = await renommerProfil(profil.id, schema.parse(v).nom);
      reset({ nom: p.nom });
      setOk(true);
      await qc.invalidateQueries({ queryKey: ['profils'] });
    } catch (err) {
      const vs = violations(err);
      if (vs.length) { setError('nom', { type: 'server', message: vs[0].title }); return; }
      if (axios.isAxiosError(err) && err.response?.status === 409) { setError('nom', { type: 'server', message: err.response.data.error }); return; }
      setError('nom', { type: 'server', message: 'Impossible de renommer le profil' });
    }
  }

  return (
    <form onSubmit={handleSubmit(envoyer)}>
      <label>Nom <input {...register('nom')} /></label>
      {errors.nom && <p role="alert" id="erreur-nom">{errors.nom.message}</p>}
      <button type="submit" disabled={!isDirty || isSubmitting}>Enregistrer</button>
      {ok && <p>Profil renommé</p>}
    </form>
  );
}
""")],
       ["Le nom actuel est prérempli", "Enregistrer suit `isDirty`", "Un nom déjà pris s'affiche sous le champ"],
       run=RUN("react", entry="App.tsx", api=PROFILS_API + r"""
db.profils.push({ id: 2, nom: 'Léo', enfant: true, age: 8 });
db.nextId = 3;
const g = __api["GET /api/profils"]; __api["GET /api/profils"] = async () => { await new Promise((r) => setTimeout(r, 300)); return g(); };
""", tests=r"""
const err = () => { const e = $('#erreur-nom'); return e ? e.textContent : ''; };
const bouton = () => $('button[type=submit]');
assert(/Chargement/.test(text()), 'Pendant le chargement : « Chargement… »');
await waitFor(() => $('[name=nom]'), 3000);
assert.equal($('[name=nom]').value, 'Léo', 'Le formulaire démarre avec le nom actuel');
assert(bouton().disabled, 'Rien changé : Enregistrer désactivé (isDirty)');
await type('[name=nom]', 'Léon');
assert(!bouton().disabled, 'Nom modifié : Enregistrer actif');
await type('[name=nom]', 'Léo');
assert(bouton().disabled, 'Retour au nom d\'origine : désactivé');
await type('[name=nom]', '  ');
await submit('form');
await waitFor(() => err() !== '', 2000);
assert.equal(err(), 'Donne un nom au profil', 'Nom vide : refusé par zod');
assert.equal(window.__db.patches.length, 0, 'Aucune requête pour un nom vide');
await type('[name=nom]', 'ANA');
await submit('form');
await waitFor(() => err() !== '', 3000);
assert.equal(err(), 'Le profil ANA existe déjà', '409 : le message s\'affiche sous le champ');
await type('[name=nom]', 'Léon');
await submit('form');
await waitFor(() => /Profil renommé/.test(text()), 3000);
assert.deepEqual(window.__db.patches[window.__db.patches.length - 1], { id: 2, nom: 'Léon' }, 'PATCH /api/profils/2 avec { nom: "Léon" }');
assert(bouton().disabled, 'Après succès : le nouveau nom devient la référence');
""")),
  ])

# =========================================================================== 8. Git en équipe
SIM = (" Le bouton **Lancer les commandes** exécute ton script dans un **Git simulé**, avec un dépôt GitHub simulé (`origin`) et la commande `gh` "
       "pour les pull requests. Pour écrire dans un fichier : `echo \"texte\" > fichier` (remplace), `>> fichier` (ajoute une ligne), "
       "`printf \"ligne 1\\nligne 2\\n\" > fichier` pour plusieurs lignes. Regarde le graphe après chaque lancement.")


def SH(code):
    return [F("commandes.sh", "bash", code)]


def GRUN(tests, setup):
    return RUN("git", tests=tests, entry="commandes.sh", start=setup)


BOBINE_REPO = r"""
git.sh('git init');
git.write('README.md', '# Bobine\n');
git.write('front/src/api/types.ts', "export type Genre = 'action' | 'animation' | 'drame';\n\nexport type Profil = {\n  id: number;\n  nom: string;\n};\n");
git.write('front/src/App.tsx', "export default function App() { return <h1>Bobine</h1>; }\n");
git.sh('git add .\ngit commit -m "chore: initialise le projet Bobine"');
git.write('back/src/Controller/ProfilController.php', "<?php // routes des profils\n");
git.sh('git add .\ngit commit -m "feat(profils): ajoute l\'API des profils"');
git.cloneRemote('https://github.com/fausatu/bobine.git');
"""

CONV = r"/^(feat|fix|docs|style|refactor|perf|test|build|ci|chore)(\([a-z0-9-]+\))?!?: [a-zàâçéèêëîïôûùüÿœ0-9]/"

gitm = FM("fil-git", "Travailler en équipe : une branche par tranche, une PR", 40,
  "Livrer une tranche de Bobine comme en entreprise : une branche dédiée, des commits au format Conventional Commits, une pull request, la mise à jour quand `main` a avancé (rebase, conflit) et la fusion.",
  "Le formulaire de profil (module 7) est une **tranche** : un morceau fini et utile. Dans une équipe, on ne le pousse pas directement sur `main` : on le prépare sur une branche, on le propose dans une **pull request** (PR) que quelqu'un relit, et on ne fusionne que quand c'est prêt. Pendant ce temps, `main` avance avec le travail des autres : il faut savoir se remettre à jour sans tout casser.",
  ["Partir de `main` à jour : `git switch main` puis `git pull`.",
   "Créer la branche de la tranche : `git switch -c feat/profils-formulaire`.",
   "Commiter par petites étapes, avec des messages `type(portée): description`.",
   "Pousser la branche (`git push -u origin …`) et ouvrir la PR (`gh pr create`).",
   "Si `main` a avancé : `git fetch`, `git rebase origin/main`, régler les conflits, `git push --force-with-lease`.",
   "Fusionner la PR (`gh pr merge --squash --delete-branch`), revenir sur `main` et `git pull`."],
  ["Une branche = une tranche : petite, finie, relisible en une fois.",
   "Nom de branche = type + sujet : `feat/profils-formulaire`, `fix/reprise-lecture`.",
   "Conventional Commits : `feat(profils): affiche les erreurs du serveur` ; le type dit ce que change le commit, la portée où.",
   "On met sa branche à jour en la **rejouant** sur `origin/main` (rebase) : l'historique reste une ligne droite, facile à relire.",
   "Après un rebase, la branche distante a l'ancienne version : `--force-with-lease` la remplace, mais refuse si quelqu'un d'autre a poussé entre-temps."],
  ["Travailler directement sur `main`.",
   "Une branche qui mélange trois sujets : la PR est impossible à relire.",
   "Des messages `wip`, `modif`, `fix bug` : personne ne sait ce que fait le commit.",
   "`git push --force` (sans `-with-lease`) : peut effacer le travail d'un collègue.",
   "Laisser les marqueurs `<<<<<<<`, `=======`, `>>>>>>>` dans un fichier après un conflit."],
  [Q("Quel message suit Conventional Commits ?", ["`Ajout formulaire`", "`feat(profils): ajoute le formulaire de création`", "`feat: Ajout du formulaire.`", "`profils - formulaire`"], 1, "type(portée): description à l'impératif, en minuscule, sans point final."),
   Q("Ta PR est ouverte, et `main` a reçu un commit de Léa. Pour mettre ta branche à jour en gardant un historique linéaire :", ["`git merge main` sur ta branche", "`git fetch` puis `git rebase origin/main`, puis `git push --force-with-lease`", "supprimer la branche et recommencer", "`git push --force`"], 1, "Le rebase rejoue tes commits par-dessus main ; la branche distante doit ensuite être remplacée, prudemment."),
   Q("Pendant un rebase, Git annonce un conflit dans `types.ts`. Après avoir corrigé le fichier :", ["`git commit -m \"fix conflit\"`", "`git add types.ts` puis `git rebase --continue`", "`git rebase --skip`", "`git push`"], 1, "On marque le fichier comme résolu (`add`), puis on laisse le rebase continuer."),
   Q("`gh pr merge --squash` :", ["fusionne tous les commits de la PR en un seul commit sur main", "supprime la PR", "fait un rebase local", "pousse ta branche"], 0, "Squash = un seul commit propre sur main, avec le titre de la PR.")],
  [P("Branche", "Une ligne de travail parallèle : une étiquette posée sur un commit, qui avance quand tu commites. Vu dans le parcours Git."),
   P("`origin`", "Le nom habituel du dépôt distant (sur GitHub). `origin/main` = la dernière version de `main` que tu as récupérée de GitHub."),
   P("Pull request (PR)", "Une demande, sur GitHub, de fusionner ta branche dans `main`. Elle montre les changements, permet de les commenter, puis de les fusionner. `gh pr create` l'ouvre depuis le terminal."),
   P("Conventional Commits", "Un format de message : `type(portée): description`. Types courants : `feat` (fonctionnalité), `fix` (correction), `refactor`, `test`, `docs`, `chore` (maintenance)."),
   P("Rebase", "Rejouer tes commits par-dessus une autre base (`git rebase origin/main`) : ta branche repart du dernier `main`, comme si tu avais commencé après."),
   P("`--force-with-lease`", "Remplace la branche distante par la tienne (nécessaire après un rebase), **seulement** si personne n'y a poussé depuis ton dernier `fetch`."),
  ],
  D(
    nodes=[
      N("m", 0, 0, "main", "à jour (git pull)", kind="pill", color="muted"),
      N("b", 1, 0, "feat/profils-formulaire", "commits feat(profils): …", kind="pill", color="accent"),
      N("gh", 2, 0, "GitHub", "git push -u origin …"),
      N("pr", 2, 1, "Pull request", "gh pr create", kind="doc", color="warn"),
      N("rb", 1, 1, "main a avancé", "fetch + rebase + --force-with-lease", kind="pill", color="bad"),
      N("mg", 0, 1, "main", "gh pr merge --squash + git pull", kind="pill", color="good"),
    ],
    edges=[E("m", "b", "git switch -c"), E("b", "gh", "push"), E("gh", "pr"), E("pr", "rb", "si besoin", dashed=True), E("rb", "gh", "push", dashed=True), E("pr", "mg", "fusion", color="good")],
    lanes=[LANE("Ton ordinateur", 0, 1, "accent"), LANE("GitHub", 2, 2, "tc")],
    caption="Le trajet d'une tranche : branche, commits, push, PR, mise à jour si main a bougé, fusion."),
  [
    L("Une branche par tranche, un nom qui dit ce qu'elle fait", r"""
Une **tranche** (parcours Découper) est un morceau de fonctionnalité fini et utile : « le formulaire de profil », « reprendre la lecture ». C'est la bonne taille pour une branche : assez petite pour être relue en une fois, assez complète pour être fusionnée sans rien casser.

Le nom de la branche reprend le **type** de changement et le **sujet**, séparés par `/` : `feat/profils-formulaire`, `fix/reprise-position`, `refactor/api-client`. On la crée **depuis `main` à jour** :

```bash
git switch main
git pull                              # récupère ce que les autres ont fusionné
git switch -c feat/profils-formulaire # crée la branche et s'y place
```

`git switch -c nom` crée la branche sur le commit actuel et s'y place. Tout ce que tu commites ensuite avance cette branche, pas `main`.
"""),
    L("Des commits au format Conventional Commits", r"""
Chaque commit raconte **une** étape. Son message suit le format `type(portée): description` :

- le **type** dit ce que change le commit : `feat` (nouvelle fonctionnalité pour l'utilisateur), `fix` (correction), `refactor` (réorganiser sans changer le comportement), `test`, `docs`, `chore` (maintenance) ;
- la **portée**, entre parenthèses, dit **où** : `profils`, `catalogue`, `lecteur` ;
- la **description** commence par un verbe à l'impératif, en minuscule, sans point final.

Pour la tranche du formulaire de profil, une bonne suite de commits :

```bash
git add front/src/schema.ts
git commit -m "feat(profils): ajoute le schéma zod du formulaire"
git add front/src/FormulaireProfil.tsx
git commit -m "feat(profils): affiche les erreurs 422 et 409 du serveur"
```

`git add fichier` choisit ce qui part dans le prochain commit ; `git commit -m "message"` l'enregistre.
"""),
    L("Pousser et ouvrir la pull request", r"""
Ta branche n'existe que sur ton ordinateur. Pour la proposer, on la **pousse** sur GitHub, puis on ouvre la **pull request** :

```bash
git push -u origin feat/profils-formulaire
gh pr create --title "feat(profils): formulaire de création de profil"
```

- `git push -u origin nom` envoie la branche sur `origin` ; `-u` retient le lien entre ta branche et la branche distante (ensuite, un simple `git push` suffit).
- `gh pr create --title "…"` ouvre la PR vers `main` (l'outil `gh` est la ligne de commande de GitHub ; sur le site, c'est le bouton « Compare & pull request »). Le titre suit le même format que les commits : avec une fusion « squash », il deviendra le message du commit sur `main`.

Une PR peut recevoir d'autres commits : si la relecture demande une correction, tu commites sur la même branche et tu fais `git push`, la PR se met à jour toute seule.
"""),
    L("Quand `main` a avancé : rebase, conflit, force-with-lease", r"""
Pendant que tu travaillais, Léa a fusionné sa tranche dans `main`. Ta PR part d'un `main` qui n'existe plus. Avant de fusionner, on rejoue tes commits **par-dessus** le nouveau `main` :

```bash
git fetch                        # récupère origin/main (le commit de Léa) sans rien modifier chez toi
git rebase origin/main           # rejoue tes commits par-dessus
git push --force-with-lease      # remplace la branche distante par la version rejouée
```

Pourquoi « force » ? Après un rebase, tes commits ont de nouveaux identifiants : la branche distante a les anciens, un `git push` normal est refusé. `--force-with-lease` la remplace, **sauf** si quelqu'un y a poussé depuis ton `fetch` (dans ce cas, il refuse au lieu d'effacer son travail).

**Si Léa a modifié les mêmes lignes que toi**, le rebase s'arrête sur un **conflit**. Git écrit les deux versions dans le fichier, entre des marqueurs :

```
<<<<<<< HEAD
  avatar: string;
=======
  enfant: boolean;
>>>>>>> 3f2c1d0 (feat(profils): ajoute enfant au type Profil)
```

Pendant un rebase, la partie `HEAD` (en haut) est la version de `main` (celle de Léa), la partie du bas est **ton** commit. Tu réécris le passage comme il doit être (ici : garder les deux champs), tu **retires les marqueurs**, puis :

```bash
git add front/src/api/types.ts   # « ce fichier est résolu »
git rebase --continue            # le rebase reprend
```

`git rebase --abort` annule tout et remet ta branche comme avant le rebase, si tu préfères recommencer.
"""),
    L("Fusionner et repartir propre", r"""
Quand la PR est relue et à jour, on la fusionne. La façon la plus courante en équipe est le **squash** : tous les commits de la PR deviennent **un seul** commit sur `main`, dont le message est le titre de la PR.

```bash
gh pr merge --squash --delete-branch   # fusionne, puis supprime la branche sur GitHub
git switch main
git pull                               # récupère le commit de fusion
git branch -d feat/profils-formulaire  # supprime la branche locale (facultatif)
```

Tu repars de `main` à jour pour la tranche suivante.
"""),
  ],
  ["Branche depuis `main` à jour : `git switch main`, `git pull`, `git switch -c feat/sujet`.",
   "Commits `type(portée): description` (feat, fix, refactor, test, docs, chore).",
   "`git push -u origin branche` puis `gh pr create --title \"…\"`.",
   "main a avancé : `git fetch`, `git rebase origin/main`, conflits (`add` + `rebase --continue`), `git push --force-with-lease`.",
   "`gh pr merge --squash --delete-branch`, puis `git switch main` et `git pull`."],
  F("commandes.sh", "bash", r"""
# 1. partir de main à jour, créer la branche de la tranche
git switch main
git pull
git switch -c feat/profils-formulaire

# 2. commiter par étapes
git add front/src/schema.ts
git commit -m "feat(profils): ajoute le schéma zod du formulaire"
git add front/src/FormulaireProfil.tsx
git commit -m "feat(profils): affiche les erreurs 422 et 409 du serveur"

# 3. pousser et ouvrir la PR
git push -u origin feat/profils-formulaire
gh pr create --title "feat(profils): formulaire de création de profil"

# 4. main a avancé entre-temps
git fetch
git rebase origin/main
git push --force-with-lease

# 5. fusionner et repartir de main
gh pr merge --squash --delete-branch
git switch main
git pull
"""),
  ["Les étapes 1 et 5 se répondent : on part de `main` à jour, on revient sur `main` à jour.",
   "Chaque `git commit` ne contient que les fichiers choisis avec `git add` juste avant.",
   "`-u` au premier push seulement : ensuite, `git push` sait où envoyer.",
   "L'étape 4 n'est nécessaire que si `main` a reçu des commits pendant ta PR.",
   "Avec `--squash`, `main` reçoit un seul commit, titré comme la PR."],
  [
    TD(1, "Ouvrir la PR du formulaire de profil",
       "Le dépôt Bobine est cloné et à jour. Livre la tranche « formulaire de profil » sur sa propre branche, et ouvre la pull request." + SIM,
       ["Crée la branche `feat/profils-formulaire` depuis `main`",
        "Commit 1 : crée `front/src/schema.ts` (contenu libre, par ex. `export const profilSchema = {};`) ; message `feat(profils): ajoute le schéma zod du formulaire`",
        "Commit 2 : crée `front/src/FormulaireProfil.tsx` ; message au format Conventional Commits, type `feat`, portée `profils`",
        "Pousse la branche en retenant le lien (`-u`) et ouvre la PR avec le titre `feat(profils): formulaire de création de profil`",
        "`main` (local et distant) ne doit pas avoir bougé"],
       SH(r"""
git status
# à toi
"""),
       ["`git switch -c feat/profils-formulaire`",
        "`echo \"export const profilSchema = {};\" > front/src/schema.ts` puis `git add front/src/schema.ts`",
        "`git push -u origin feat/profils-formulaire` puis `gh pr create --title \"feat(profils): formulaire de création de profil\"`"],
       SH(r"""
git status
git switch -c feat/profils-formulaire
echo "export const profilSchema = {};" > front/src/schema.ts
git add front/src/schema.ts
git commit -m "feat(profils): ajoute le schéma zod du formulaire"
echo "export function FormulaireProfil() { return null; }" > front/src/FormulaireProfil.tsx
git add front/src/FormulaireProfil.tsx
git commit -m "feat(profils): affiche les erreurs 422 et 409 du serveur"
git push -u origin feat/profils-formulaire
gh pr create --title "feat(profils): formulaire de création de profil"
"""),
       ["Deux commits sur la branche, aucun sur main", "La PR est ouverte vers main"],
       run=GRUN(r"""
assert.equal(git.failed().length, 0, 'Aucune commande en erreur' + (git.failed().length ? ' : ' + git.failed().join(' · ') : ''));
assert(git.branches['feat/profils-formulaire'], 'La branche feat/profils-formulaire existe');
assert.equal(git.log('main').length, 2, 'main local n\'a pas bougé (2 commits)');
assert.equal(git.remoteLog('main').length, 2, 'main sur GitHub n\'a pas bougé');
const msgs = git.range('main', 'feat/profils-formulaire');
assert.equal(msgs.length, 2, 'Deux commits sur la branche', msgs.join(' | '));
assert(msgs.includes('feat(profils): ajoute le schéma zod du formulaire'), 'Le commit 1 a le message demandé');
const conv = """ + CONV + r""";
assert(msgs.every((m) => conv.test(m)), 'Tous les messages suivent Conventional Commits', msgs.join(' | '));
assert(msgs.some((m) => /^feat\(profils\): /.test(m) && m !== 'feat(profils): ajoute le schéma zod du formulaire'), 'Commit 2 : type feat, portée profils');
assert(git.at('feat/profils-formulaire', 'front/src/schema.ts') !== null && git.at('feat/profils-formulaire', 'front/src/FormulaireProfil.tsx') !== null, 'Les deux fichiers sont dans la branche');
assert.equal(git.remote.branches['feat/profils-formulaire'], git.rev('feat/profils-formulaire'), 'La branche est poussée sur GitHub, à jour');
assert(git.upstream['feat/profils-formulaire'], 'Le lien avec la branche distante est retenu (-u)');
const pr = git.prs.find((p) => p.head === 'feat/profils-formulaire');
assert(pr && pr.state === 'OPEN' && pr.base === 'main', 'Une PR ouverte vers main');
assert.equal(pr && pr.title, 'feat(profils): formulaire de création de profil', 'Le titre de la PR');
""", BOBINE_REPO)),
    TD(2, "main a avancé : rebase, puis fusion",
       "Ta PR est ouverte, mais Léa vient de fusionner une correction du catalogue dans `main` sur GitHub. Mets ta branche à jour en gardant un historique **linéaire**, puis fusionne la PR en squash et reviens sur `main` à jour." + SIM,
       ["Récupère le travail de Léa sans rien modifier chez toi",
        "Rejoue ta branche par-dessus `origin/main`",
        "Remplace la branche distante prudemment",
        "Fusionne la PR en squash en supprimant la branche distante",
        "Reviens sur `main` et mets-le à jour : il doit contenir le commit de Léa puis le tien"],
       SH(r"""
git log --oneline --all
# à toi
"""),
       ["`git fetch` puis `git rebase origin/main` (tu es déjà sur ta branche).",
        "Un `git push` normal est refusé après un rebase : `git push --force-with-lease`.",
        "`gh pr merge --squash --delete-branch`, puis `git switch main` et `git pull`."],
       SH(r"""
git log --oneline --all
git fetch
git rebase origin/main
git push --force-with-lease
gh pr merge --squash --delete-branch
git switch main
git pull
"""),
       ["La branche est rejouée après le commit de Léa", "main contient un seul commit pour toute ta PR"],
       run=GRUN(r"""
assert.equal(git.failed().length, 0, 'Aucune commande en erreur' + (git.failed().length ? ' : ' + git.failed().join(' · ') : ''));
assert(git.used(/^git fetch/) || git.used(/^git pull --rebase/), 'Le travail de Léa a été récupéré (git fetch)');
assert(git.used(/^git rebase origin\/main/), 'La branche a été rejouée sur origin/main (rebase)');
assert(git.used(/--force-with-lease/) && !git.used(/--force(?!-with-lease)\b|\s-f\b/), 'Push avec --force-with-lease (jamais --force seul)');
const pr = git.prs.find((p) => p.head === 'feat/profils-formulaire');
assert(pr && pr.state === 'MERGED', 'La PR est fusionnée');
assert(!git.remote.branches['feat/profils-formulaire'], 'La branche distante est supprimée');
const rl = git.remoteLog('main');
assert.equal(rl[0], 'feat(profils): formulaire de création de profil (#1)', 'main sur GitHub : un seul commit squash, titré comme la PR', rl.join(' | '));
assert.equal(rl[1], 'fix(catalogue): corrige le tri par année', 'Juste avant : le commit de Léa');
assert.equal(git.branch, 'main', 'Tu termines sur main');
assert.equal(git.rev('main'), git.remote.branches.main, 'main local est à jour avec GitHub (git pull)');
assert(git.isLinear('main'), 'Historique de main linéaire (aucun commit de fusion)');
""", BOBINE_REPO + r"""
git.sh('git switch -c feat/profils-formulaire');
git.write('front/src/schema.ts', 'export const profilSchema = {};\n');
git.sh('git add .\ngit commit -m "feat(profils): ajoute le schéma zod du formulaire"');
git.write('front/src/FormulaireProfil.tsx', 'export function FormulaireProfil() { return null; }\n');
git.sh('git add .\ngit commit -m "feat(profils): affiche les erreurs 422 et 409 du serveur"');
git.sh('git push -u origin feat/profils-formulaire');
git.sh('gh pr create --title "feat(profils): formulaire de création de profil"');
git.remoteCommit('main', 'fix(catalogue): corrige le tri par année', { 'front/src/Catalogue.tsx': "// tri par année décroissante\n" }, 'Léa');
""")),
    TD(3, "Un conflit pendant le rebase",
       "Cette fois, Léa a modifié **le même endroit** que toi : elle a ajouté `avatar: string;` au type `Profil` dans `front/src/api/types.ts`, et ton commit y ajoute `enfant: boolean;`. Mets ta branche à jour, résous le conflit en gardant **les deux** champs, puis fusionne." + SIM,
       ["`git fetch` puis `git rebase origin/main` : le rebase s'arrête sur un conflit (lis `git status` et `cat` le fichier)",
        "Réécris `front/src/api/types.ts` sans marqueurs, avec `id`, `nom`, `avatar` **et** `enfant` dans le type `Profil` (et le type `Genre` inchangé)",
        "Termine le rebase, pousse prudemment, fusionne la PR en squash (branche distante supprimée)",
        "Reviens sur `main` à jour"],
       SH(r"""
git status
# à toi
"""),
       ["Pour réécrire le fichier en entier : `printf \"export type Genre = 'action' | 'animation' | 'drame';\\n\\nexport type Profil = {\\n  id: number;\\n  nom: string;\\n  avatar: string;\\n  enfant: boolean;\\n};\\n\" > front/src/api/types.ts`",
        "Puis `git add front/src/api/types.ts` et `git rebase --continue`.",
        "`git push --force-with-lease`, `gh pr merge --squash --delete-branch`, `git switch main`, `git pull`."],
       SH(r"""
git status
git fetch
git rebase origin/main
cat front/src/api/types.ts
printf "export type Genre = 'action' | 'animation' | 'drame';\n\nexport type Profil = {\n  id: number;\n  nom: string;\n  avatar: string;\n  enfant: boolean;\n};\n" > front/src/api/types.ts
git add front/src/api/types.ts
git rebase --continue
git push --force-with-lease
gh pr merge --squash --delete-branch
git switch main
git pull
"""),
       ["Les deux champs sont gardés", "Aucun marqueur de conflit ne reste"],
       run=GRUN(r"""
const f = git.at('origin/main', 'front/src/api/types.ts') || git.file('front/src/api/types.ts') || '';
assert(git.op === null, 'Le rebase est terminé (pas d\'opération en cours)');
assert(!/<<<<<<<|=======|>>>>>>>/.test(git.file('front/src/api/types.ts') || ''), 'Aucun marqueur de conflit dans le fichier');
const pr = git.prs.find((p) => p.head === 'feat/profils-enfant');
assert(pr && pr.state === 'MERGED', 'La PR est fusionnée');
const surMain = git.at(git.remote.branches.main, 'front/src/api/types.ts') || '';
assert(/avatar:\s*string;/.test(surMain) && /enfant:\s*boolean;/.test(surMain), 'Sur main : avatar (Léa) ET enfant (toi) dans Profil', surMain);
assert(/id:\s*number;/.test(surMain) && /nom:\s*string;/.test(surMain) && /export type Genre/.test(surMain), 'id, nom et Genre sont toujours là');
assert(!/<<<<<<<|>>>>>>>/.test(surMain), 'Aucun marqueur sur main');
assert(!git.remote.branches['feat/profils-enfant'], 'Branche distante supprimée');
assert(git.used(/--force-with-lease/) && !git.used(/--force(?!-with-lease)\b|\s-f\b/), 'Push avec --force-with-lease');
assert.equal(git.branch, 'main', 'Tu termines sur main');
assert.equal(git.rev('main'), git.remote.branches.main, 'main local à jour');
assert(git.isLinear('main'), 'Historique linéaire');
assert.equal(git.failed().filter((c) => !/^git rebase origin\/main/.test(c)).length, 0, 'Aucune autre commande en erreur (le rebase qui s\'arrête sur le conflit est normal)', git.failed().join(' · '));
""", BOBINE_REPO + r"""
git.sh('git switch -c feat/profils-enfant');
git.write('front/src/api/types.ts', "export type Genre = 'action' | 'animation' | 'drame';\n\nexport type Profil = {\n  id: number;\n  nom: string;\n  enfant: boolean;\n};\n");
git.sh('git add .\ngit commit -m "feat(profils): ajoute enfant au type Profil"');
git.sh('git push -u origin feat/profils-enfant');
git.sh('gh pr create --title "feat(profils): profils enfants"');
git.remoteCommit('main', 'feat(profils): ajoute un avatar aux profils', { 'front/src/api/types.ts': "export type Genre = 'action' | 'animation' | 'drame';\n\nexport type Profil = {\n  id: number;\n  nom: string;\n  avatar: string;\n};\n" }, 'Léa');
""")),
  ])

# =========================================================================== 9. Lancer Bobine en local
TSH = (" Écris tes commandes dans le fichier (une par ligne), puis **▶ Lancer les commandes** : elles s'exécutent dans un terminal simulé "
       "où `symfony`, `npm`, `curl`, `lsof` et `kill` fonctionnent (les serveurs démarrés restent en arrière-plan). Tu peux ensuite taper d'autres commandes dans le terminal pour explorer.")


def TERM(tests, start, entry="commandes.sh"):
    return RUN("term", entry=entry, tests=tests, start=start)


BOBINE_DISQUE = r"""
t.fichier('bobine/back/composer.json', '{ "name": "fausatu/bobine-back", "require": { "symfony/framework-bundle": "^7.1" } }\n');
t.fichier('bobine/back/bin/console', '#!/usr/bin/env php\n', true);
t.fichier('bobine/back/public/index.php', '<?php // point d\'entrée Symfony\n');
t.fichier('bobine/back/.env', '# Valeurs par défaut, commitées. Mets tes vraies valeurs dans .env.local (jamais commité).\nAPP_ENV=dev\nDATABASE_URL="mysql://app:!ChangeMe!@127.0.0.1:3306/bobine"\n');
t.fichier('bobine/back/.gitignore', '/.env.local\n/vendor/\n');
t.fichier('bobine/front/package.json', JSON.stringify({ name: 'bobine-front', version: '0.1.0', private: true, scripts: { dev: 'vite', build: 'vite build' }, dependencies: { react: '^18.3.1', axios: '^1.7.0', '@tanstack/react-query': '^5.59.0' }, devDependencies: { vite: '^5.4.0' } }, null, 2) + '\n');
t.fichier('bobine/front/vite.config.ts', "import { defineConfig } from 'vite';\nimport react from '@vitejs/plugin-react';\n\nexport default defineConfig({\n  plugins: [react()],\n  server: {\n    proxy: {\n      '/api': 'http://localhost:8000',\n    },\n  },\n});\n");
t.fichier('bobine/front/src/api/client.ts', "import axios from 'axios';\nexport const api = axios.create({ baseURL: '/api' });\n");
"""

terminal = FM("fil-lancer", "Lancer Bobine en local : back, front, .env et ports", 35,
  "Démarrer le back Symfony et le front Vite ensemble, comprendre comment le front joint l'API (proxy), régler les variables d'environnement (`.env`, `.env.local`) et se sortir d'un port déjà occupé.",
  "Un projet full stack, ce sont **deux programmes** qui tournent en même temps sur ton ordinateur : l'API Symfony et le front React (servi par Vite). Chacun écoute sur un **port**, lit sa configuration dans des fichiers `.env`, et ils doivent se trouver. Quand l'un des trois réglages est faux, l'écran reste blanc ou les requêtes échouent : savoir lancer et diagnostiquer, c'est ce qui te débloque le premier jour d'un projet.",
  ["Back : `cd back`, configurer `.env.local`, puis `symfony server:start -d` → l'API écoute sur le port 8000.",
   "Front : `cd front`, `npm install` (une fois), puis `npm run dev` → Vite écoute sur le port 5173.",
   "Le navigateur ne parle qu'à Vite (5173) ; Vite **relaie** les requêtes `/api/...` vers 8000 (le proxy de `vite.config.ts`).",
   "Vérifier de bout en bout : `curl http://localhost:5173/api/films` doit renvoyer le JSON de l'API.",
   "Un port est déjà pris ? `lsof -i :8000` dit quel programme (PID) ; `kill PID` l'arrête, ou on choisit un autre port."],
  ["Deux serveurs, deux ports : 8000 pour l'API, 5173 pour le front. Le navigateur n'ouvre que le 5173.",
   "Le proxy de Vite (`'/api': 'http://localhost:8000'`) évite les problèmes de CORS : pour le navigateur, tout vient de la même adresse.",
   "`.env` est commité (valeurs par défaut, sans secret) ; `.env.local` contient **tes** valeurs (mot de passe de base de données) et n'est **jamais** commité.",
   "On modifie un `.env` ? Il faut **relancer** le serveur pour qu'il le relise.",
   "« Port déjà utilisé » : trouver le PID avec `lsof -i :PORT`, puis arrêter le programme (`kill PID`) ou changer de port."],
  ["Lancer `npm run dev` dans le dossier `back` (ou `symfony` dans `front`) : chaque commande se lance dans **son** dossier.",
   "Oublier `npm install` : `vite: not found`.",
   "Mettre le mot de passe de la base dans `.env` (commité) au lieu de `.env.local`.",
   "Laisser le back démarrer sur 8001 parce que 8000 est pris : le proxy, lui, envoie toujours vers 8000.",
   "Tuer un processus au hasard sans vérifier ce qu'il est (`lsof` d'abord)."],
  [Q("`curl http://localhost:5173/api/films` répond « ECONNREFUSED 127.0.0.1:8000 ». Le problème :", ["le front n'est pas lancé", "le back ne tourne pas sur 8000", "axios est mal installé", "le .env du front est faux"], 1, "Vite répond (5173), mais le proxy ne trouve personne sur 8000."),
   Q("Où mettre `DATABASE_URL` avec ton vrai mot de passe ?", ["`.env`", "`.env.local`", "`composer.json`", "dans le code"], 1, "`.env.local` n'est pas commité : ton mot de passe ne part pas sur GitHub."),
   Q("`symfony server:start` dit « Port 8000 is already in use, using port 8001 ». Avec le proxy vers 8000 :", ["tout marche", "le front n'arrive pas à l'API : il faut libérer 8000 (ou changer le proxy)", "Vite change de port tout seul", "il faut relancer npm install"], 1, "Le proxy vise 8000 ; le back est ailleurs."),
   Q("Trouver quel programme occupe le port 5173 :", ["`ps 5173`", "`lsof -i :5173`", "`kill 5173`", "`npm stop`"], 1, "`lsof -i :PORT` liste le programme qui écoute, avec son PID.")],
  [P("Port", "Un numéro (de 1 à 65535) qui désigne **un** programme serveur sur une machine. Deux programmes ne peuvent pas écouter sur le même port. `http://localhost:8000` = « le programme qui écoute sur le port 8000 de mon ordinateur »."),
   P("`localhost`", "Ton propre ordinateur (adresse `127.0.0.1`)."),
   P("Symfony CLI (`symfony`)", "L'outil en ligne de commande de Symfony. `symfony server:start` lance un serveur web pour le projet du dossier courant ; `-d` le lance en arrière-plan (le terminal reste libre) ; `symfony server:stop` l'arrête."),
   P("Vite", "L'outil qui sert le front React pendant le développement (rechargement instantané). `npm run dev` lance le script `dev` de `package.json`, qui vaut `vite`."),
   P("Proxy", "Un intermédiaire qui relaie des requêtes. Le proxy de Vite reçoit `/api/films` sur le port 5173 et le transmet à `http://localhost:8000/api/films`."),
   P("CORS", "Une protection du navigateur : une page servie par `localhost:5173` n'a pas le droit, par défaut, de lire les réponses de `localhost:8000` (une autre « origine »). Le proxy contourne le problème : tout passe par 5173."),
   P("Fichier `.env`", "Un fichier de configuration `NOM=valeur`, lu au démarrage. Symfony lit `.env` puis `.env.local` (qui l'emporte) ; Vite fait pareil et n'expose au code du front que les variables qui commencent par `VITE_`."),
   P("PID", "Le numéro d'un processus (un programme en cours d'exécution). `kill PID` lui demande de s'arrêter."),
  ],
  D(
    nodes=[
      N("nav", 0, 0, "Navigateur", "http://localhost:5173", kind="actor", color="accent"),
      N("vite", 1, 0, "Vite (front)", "port 5173 · npm run dev", kind="file", color="accent"),
      N("sf", 2, 0, "Symfony (API)", "port 8000 · symfony server:start"),
      N("db", 3, 0, "Base MySQL", "port 3306", kind="db", color="muted"),
      N("env1", 2, 1, "back/.env.local", "DATABASE_URL", kind="doc", color="warn"),
      N("cfg", 1, 1, "vite.config.ts", "proxy '/api' → 8000", kind="doc", color="warn"),
    ],
    edges=[E("nav", "vite", "page + /api/films"), E("vite", "sf", "proxy /api"), E("sf", "db", "SQL"), E("env1", "sf", dashed=True), E("cfg", "vite", dashed=True)],
    lanes=[LANE("Ton ordinateur", 0, 3, "tc")],
    caption="Le navigateur ne voit que Vite ; Vite relaie /api vers Symfony ; Symfony trouve la base grâce à .env.local."),
  [
    L("Deux programmes, deux ports", r"""
Pendant le développement, Bobine, ce sont deux serveurs lancés depuis deux dossiers :

| | Dossier | Commande | Port |
|---|---|---|---|
| L'API (Symfony) | `bobine/back` | `symfony server:start -d` | 8000 |
| Le front (React + Vite) | `bobine/front` | `npm run dev` | 5173 |

Un **port** est un numéro qui identifie un programme serveur sur ta machine : `http://localhost:8000` veut dire « le programme qui écoute sur le port 8000 de mon ordinateur ». Deux programmes ne peuvent pas écouter sur le même port.

Chaque commande se lance **dans son dossier** : `symfony server:start` cherche un projet Symfony (`composer.json`, `bin/console`) dans le dossier courant, et `npm run dev` lit le `package.json` du dossier courant. On se déplace avec `cd` (parcours Terminal) :

```bash
cd ~/bobine/back
symfony server:start -d     # -d : en arrière-plan, le terminal reste disponible
cd ../front
npm install                 # une seule fois : télécharge les dépendances dans node_modules/
npm run dev                 # lance le script "dev" de package.json, c'est-à-dire vite
```

Dans la vraie vie, on ouvre souvent **deux onglets de terminal** : un pour le back, un pour le front (Vite occupe son terminal et affiche ses messages ; `Ctrl+C` l'arrête).
"""),
    L("Comment le front trouve l'API : le proxy de Vite", r"""
Le navigateur charge la page depuis `http://localhost:5173`. Le client axios du front (module 6) a `baseURL: '/api'` : une requête vers `/films` part donc vers `http://localhost:5173/api/films`, c'est-à-dire **vers Vite**, pas vers Symfony.

Vite la relaie grâce au **proxy** déclaré dans `vite.config.ts` :

```ts
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',   // toute requête /api/... est transmise au back
    },
  },
});
```

Pourquoi ne pas appeler `http://localhost:8000` directement depuis le front ? À cause du **CORS** : le navigateur considère `localhost:5173` et `localhost:8000` comme deux sites différents, et bloque par défaut les réponses de l'un lues par l'autre. Avec le proxy, pour le navigateur, tout vient de la même adresse : pas de CORS à configurer en développement.

Pour tester toute la chaîne sans navigateur, `curl` envoie une requête et affiche la réponse :

```bash
curl http://localhost:8000/api/films   # le back seul
curl http://localhost:5173/api/films   # le front → proxy → back : le vrai trajet
```
"""),
    L("Les fichiers .env : la configuration qui dépend de ta machine", r"""
Certaines valeurs changent d'un ordinateur à l'autre : l'adresse et le mot de passe de ta base de données, une clé d'API. Elles ne vont pas dans le code mais dans des fichiers **`.env`**, une ligne `NOM=valeur` par variable, lus au démarrage du serveur.

Symfony en lit deux, dans cet ordre :

- **`.env`** : les valeurs par défaut, **commitées** dans Git. Jamais de vrai secret dedans (on y voit souvent `!ChangeMe!`).
- **`.env.local`** : **tes** valeurs, qui remplacent celles de `.env`. Ce fichier est dans `.gitignore` : il ne part jamais sur GitHub.

Pour configurer ton poste, on copie `.env` en `.env.local`, puis on y met la vraie adresse de la base :

```bash
cd ~/bobine/back
cp .env .env.local
echo 'DATABASE_URL="mysql://bobine:motdepasse@127.0.0.1:3306/bobine"' >> .env.local
cat .env.local
```

`cp source destination` copie un fichier ; `>>` ajoute une ligne à la fin (la dernière valeur d'une variable l'emporte). Côté front, Vite lit aussi `.env` et `.env.local`, mais ne donne au code que les variables qui commencent par **`VITE_`** (`import.meta.env.VITE_TITRE`) : tout ce qui est dans le front est visible par n'importe quel visiteur, donc jamais de secret là non plus.

Un serveur lit ses `.env` **au démarrage** : après une modification, il faut l'arrêter et le relancer (`symfony server:stop`, puis `server:start`).
"""),
    L("« Port déjà utilisé » : trouver qui l'occupe", r"""
Un vieux serveur oublié tourne encore sur 8000 (un autre projet, une ancienne session). Selon l'outil, tu verras :

- Node : `Error: listen EADDRINUSE: address already in use :::8000` (le serveur ne démarre pas) ;
- Vite : `Port 5173 is in use, trying another one...` (il prend 5174 et continue) ;
- Symfony CLI : il prend lui aussi le port libre suivant (8001) et l'annonce.

Les deux derniers ont l'air de marcher, mais attention : **le proxy, lui, vise toujours 8000**. Si le back est parti sur 8001, le front n'arrive plus à l'API.

On trouve le programme qui occupe un port avec `lsof -i :PORT` (« list open files », filtré sur un port). La colonne **PID** donne son numéro, et `kill PID` lui demande de s'arrêter :

```bash
lsof -i :8000
# COMMAND   PID USER   FD   TYPE ... NAME
# node     4242 ana    23u  IPv6 ... TCP *:8000 (LISTEN)
kill 4242
lsof -i :8000          # plus rien : le port est libre
```

Sous Windows (PowerShell), l'équivalent est `Get-NetTCPConnection -LocalPort 8000` puis `Stop-Process -Id PID`. Si tu ne veux pas arrêter l'autre programme, change plutôt de port **des deux côtés** : `symfony server:start --port=8080` et la cible du proxy dans `vite.config.ts`.
"""),
  ],
  ["Back : `cd back`, `.env.local`, `symfony server:start -d` (8000). Front : `cd front`, `npm install`, `npm run dev` (5173).",
   "Le navigateur ne parle qu'à Vite ; le proxy `'/api' → http://localhost:8000` relaie vers Symfony (pas de CORS).",
   "`.env` commité sans secret ; `.env.local` pour tes valeurs, jamais commité ; relancer après modification.",
   "Vérifier la chaîne : `curl http://localhost:5173/api/films`.",
   "Port occupé : `lsof -i :PORT` → PID → `kill PID`, ou changer de port des deux côtés."],
  [F("commandes.sh", "bash", r"""
# --- le back ---
cd ~/bobine/back
cp .env .env.local                                                     # une fois par poste
echo 'DATABASE_URL="mysql://bobine:motdepasse@127.0.0.1:3306/bobine"' >> .env.local
symfony server:start -d                                                # → http://127.0.0.1:8000
curl http://localhost:8000/api/films                                   # le back répond ?

# --- le front ---
cd ../front
npm install                                                            # une fois
npm run dev                                                            # → http://localhost:5173

# --- la chaîne complète : navigateur → Vite → proxy → Symfony ---
curl http://localhost:5173/api/films
"""), F("front/vite.config.ts", "ts", r"""
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
});
""")],
  ["Chaque serveur est lancé depuis **son** dossier : le `cd ../front` est indispensable.",
   "Le `curl` sur 8000 teste le back seul ; celui sur 5173 teste tout le trajet, proxy compris.",
   "`.env.local` est créé à partir de `.env`, puis complété : la dernière ligne `DATABASE_URL` l'emporte.",
   "Le proxy de `vite.config.ts` est le seul endroit où le front connaît le port du back."],
  [
    TD(1, "Démarrer Bobine de A à Z",
       "Le projet est cloné dans `~/bobine` (dossiers `back` et `front`), rien n'est lancé ni configuré. Démarre tout et vérifie la chaîne complète." + TSH,
       ["Dans `back` : crée `.env.local` à partir de `.env`, puis ajoute la ligne `DATABASE_URL=\"mysql://bobine:bobine@127.0.0.1:3306/bobine\"`",
        "Démarre le back en arrière-plan sur le port 8000",
        "Dans `front` : installe les dépendances et démarre Vite (port 5173)",
        "Vérifie la chaîne complète avec `curl` **en passant par le front** : la réponse doit être le JSON des films",
        "`.env` ne doit pas être modifié (seulement `.env.local`)"],
       [F("commandes.sh", "bash", r"""
cd ~/bobine
ls
# à toi
""")],
       ["`cp .env .env.local` puis `echo 'DATABASE_URL=\"mysql://bobine:bobine@127.0.0.1:3306/bobine\"' >> .env.local`",
        "`symfony server:start -d` dans `back` ; `npm install` puis `npm run dev` dans `front`.",
        "`curl http://localhost:5173/api/films` : si tu vois une erreur « Access denied », la base n'est pas configurée dans `.env.local`."],
       [F("commandes.sh", "bash", r"""
cd ~/bobine
ls
cd back
cp .env .env.local
echo 'DATABASE_URL="mysql://bobine:bobine@127.0.0.1:3306/bobine"' >> .env.local
symfony server:start -d
cd ../front
npm install
npm run dev
curl http://localhost:5173/api/films
""")],
       ["Deux serveurs tournent, sur 8000 et 5173", "Le curl via le front renvoie les films"],
       run=TERM(r"""
const procs = term.procs();
const back = procs.find((p) => p.kind === 'symfony' || p.kind === 'php');
const front = procs.find((p) => p.kind === 'vite');
assert(term.exists('bobine/back/.env.local'), '.env.local existe dans back');
assert(/DATABASE_URL="?mysql:\/\/bobine:bobine@127\.0\.0\.1:3306\/bobine/.test(term.read('bobine/back/.env.local') || ''), '.env.local contient la bonne DATABASE_URL');
assert(/!ChangeMe!/.test(term.read('bobine/back/.env') || '') && !/bobine:bobine/.test(term.read('bobine/back/.env') || ''), '.env (commité) n\'a pas été modifié');
assert(back && back.port === 8000, 'Le back tourne sur le port 8000', JSON.stringify(procs.map((p) => p.cmd + ':' + p.port)));
assert(term.isDir('bobine/front/node_modules'), 'Les dépendances du front sont installées (npm install)');
assert(front && front.port === 5173, 'Vite tourne sur le port 5173');
assert(term.used(/curl\s+(https?:\/\/)?localhost:5173\/api\//), 'Un curl passe par le front (localhost:5173/api/...)');
assert(term.lastCurl && term.lastCurl.ok && term.lastCurl.via === 'proxy', 'La réponse vient de l\'API via le proxy (JSON des films)', term.lastCurl ? JSON.stringify(term.lastCurl) : 'aucun curl');
assert.equal(term.failed().length, 0, 'Aucune commande en erreur', term.failed().join(' | '));
""", BOBINE_DISQUE)),
    TD(2, "Le port 8000 est déjà pris",
       "Un ancien serveur de test oublié tourne encore sur le port 8000. Le `.env.local` du back est déjà prêt. Si tu lances le back sans réfléchir, il partira sur 8001… et le proxy du front, lui, vise 8000. Libère le port proprement, puis démarre tout." + TSH,
       ["Trouve quel programme occupe le port 8000 (affiche son PID)",
        "Arrête-le avec son PID",
        "Vérifie que le port est libre, puis démarre le back (sur 8000) et le front",
        "Vérifie la chaîne complète par le front avec `curl`"],
       [F("commandes.sh", "bash", r"""
cd ~/bobine/back
# à toi
""")],
       ["`lsof -i :8000` affiche le PID dans la 2e colonne.",
        "`kill` suivi du PID que tu as lu (le terminal de l'atelier le garde le même à chaque lancement).",
        "Astuce : `kill $(lsof -t -i :8000)` fait les deux en une ligne (`-t` n'affiche que le PID).",
        "Le front s'installe et se lance dans `../front`."],
       [F("commandes.sh", "bash", r"""
cd ~/bobine/back
lsof -i :8000
kill $(lsof -t -i :8000)
lsof -i :8000
symfony server:start -d
cd ../front
npm install
npm run dev
curl http://localhost:5173/api/films
""")],
       ["Le vieux serveur est arrêté, pas un autre", "Le back est bien sur 8000"],
       run=TERM(r"""
const procs = term.procs();
assert(term.used(/lsof\s+.*-i\s*:?8000|lsof\s+-i\s*:8000/), 'Le port 8000 a été inspecté avec lsof');
assert(!procs.some((p) => p.cmd === 'node ancien-test.js'), 'Le vieux serveur (node ancien-test.js) est arrêté');
assert(procs.some((p) => p.cmd === 'node /opt/outil-equipe/serveur.js'), 'L\'autre programme (outil de l\'équipe, port 3000) n\'a pas été touché');
const back = procs.find((p) => p.kind === 'symfony' || p.kind === 'php');
assert(back && back.port === 8000, 'Le back tourne sur 8000 (pas 8001)', JSON.stringify(procs.map((p) => p.cmd + ':' + p.port)));
const front = procs.find((p) => p.kind === 'vite');
assert(front && front.port === 5173, 'Vite tourne sur 5173');
assert(term.lastCurl && term.lastCurl.ok && term.lastCurl.via === 'proxy', 'Le curl par le front renvoie les films', term.lastCurl ? JSON.stringify(term.lastCurl) : 'aucun curl');
""", BOBINE_DISQUE + r"""
t.fichier('bobine/back/.env.local', 'DATABASE_URL="mysql://bobine:bobine@127.0.0.1:3306/bobine"\n');
t.processus('node', 'node /opt/outil-equipe/serveur.js', 3000, 'outil');
t.processus('node', 'node ancien-test.js', 8000, 'ancien serveur de test');
""")),
    TD(3, "Un script pour tout lancer",
       "Tu relances Bobine tous les matins : écris un script `dev.sh` à la racine du projet qui fait tout, puis utilise-le." + TSH,
       ["`~/bobine/dev.sh` commence par `#!/usr/bin/env bash`",
        "S'il n'existe pas encore, il crée `back/.env.local` en copiant `back/.env` (et ne l'écrase **pas** s'il existe déjà)",
        "Il démarre le back en arrière-plan, puis le front (avec `npm install` avant)",
        "Rends-le exécutable et lance-le depuis `~/bobine` ; vérifie avec `curl` par le front",
        "Ici, `back/.env.local` existe déjà avec la bonne base : le script ne doit pas le remplacer"],
       [F("commandes.sh", "bash", r"""
cd ~/bobine
# 1. écrire dev.sh (printf "...\n...\n" > dev.sh)

# 2. le rendre exécutable et le lancer

# 3. vérifier
""")],
       ["Une condition sur une ligne : `[ -f back/.env.local ] || cp back/.env back/.env.local` (« si le fichier n'existe pas, copie »).",
        "Le contenu complet en une commande : `printf '#!/usr/bin/env bash\\n[ -f back/.env.local ] || cp back/.env back/.env.local\\ncd back && symfony server:start -d\\ncd ../front && npm install && npm run dev\\n' > dev.sh`",
        "`chmod +x dev.sh` puis `./dev.sh`."],
       [F("commandes.sh", "bash", r"""
cd ~/bobine
printf '#!/usr/bin/env bash\n[ -f back/.env.local ] || cp back/.env back/.env.local\ncd back && symfony server:start -d\ncd ../front && npm install && npm run dev\n' > dev.sh
chmod +x dev.sh
./dev.sh
curl http://localhost:5173/api/films
""")],
       ["Le script ne remplace pas un `.env.local` existant", "Un seul `./dev.sh` démarre tout"],
       run=TERM(r"""
const s = term.read('bobine/dev.sh') || '';
assert(/^#!\/usr\/bin\/env bash/.test(s), 'dev.sh commence par #!/usr/bin/env bash');
assert(term.isExec('bobine/dev.sh'), 'dev.sh est exécutable (chmod +x)');
assert(/\[\s*-f\s+back\/\.env\.local\s*\]\s*\|\||if\s+\[\s*!\s*-f\s+back\/\.env\.local/.test(s), 'dev.sh ne copie .env que si .env.local n\'existe pas');
assert(/symfony server:start/.test(s) && /npm run dev/.test(s) && /npm install/.test(s), 'dev.sh démarre le back et le front (avec npm install)');
assert(term.used(/^\.\/dev\.sh|^bash dev\.sh/), 'Le script a été lancé');
assert(/bobine:bobine/.test(term.read('bobine/back/.env.local') || ''), '.env.local existant conservé (pas écrasé par .env)');
const procs = term.procs();
assert(procs.some((p) => (p.kind === 'symfony' || p.kind === 'php') && p.port === 8000), 'Le back tourne sur 8000', JSON.stringify(procs.map((p) => p.cmd + ':' + p.port)));
assert(procs.some((p) => p.kind === 'vite' && p.port === 5173), 'Le front tourne sur 5173');
assert(term.lastCurl && term.lastCurl.ok && term.lastCurl.via === 'proxy', 'Le curl par le front renvoie les films', term.lastCurl ? JSON.stringify(term.lastCurl) : 'aucun curl');
""", BOBINE_DISQUE + r"""
t.fichier('bobine/back/.env.local', 'DATABASE_URL="mysql://bobine:bobine@127.0.0.1:3306/bobine"\n');
""")),
  ])

MODULES = [form, gitm, terminal]

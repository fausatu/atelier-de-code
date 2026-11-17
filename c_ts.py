from common import P, L, D, N, E, F, TD, RUN

T = "ts"


def DM(id, title, minutes, goal, why, flow, points, pitfalls, quiz, prereq, diagram, lessons, recap, example, notes, tds):
    return {"id": id, "track": T, "title": title, "minutes": minutes, "goal": goal, "why": why,
            "flow": flow, "points": points, "pitfalls": pitfalls, "quiz": quiz, "prereq": prereq,
            "diagram": diagram, "lessons": lessons, "recap": recap,
            "example": {"files": example if isinstance(example, list) else [example], "notes": notes}, "tds": tds}


def Q(q, options, answer, why):
    return {"q": q, "options": options, "answer": answer, "why": why}


def TRUN(entry, tests, typetests=None, api=None, kind="js"):
    return RUN(kind, entry=entry, tests=tests, typetests=typetests, typecheck=True, api=api)


TS = (" Le bouton Exécuter passe ton code au **vrai compilateur TypeScript** (les erreurs s'affichent dans la sortie, comme dans VS Code), puis l'exécute. "
      "Les tests vérifient le résultat **et** les types : certaines lignes doivent être refusées par TypeScript (✗), d'autres acceptées (✓).")
TSX = (" Le bouton Exécuter vérifie les types avec le vrai compilateur TypeScript, puis affiche le composant. "
       "Les tests vérifient le comportement **et** les types (✗ : TypeScript doit refuser, ✓ : il doit accepter).")


# =========================================================================== 1. Bases
bases = DM("ts-bases", "Les types de base", 25,
  "Lire et écrire les types de base de TypeScript : annotations, inférence, tableaux, objets, champs optionnels, unions simples, et comprendre un message d'erreur de type.",
  "TypeScript trouve une grande partie des bugs avant même d'exécuter le code, et rend le code lisible (« cette fonction prend un Produit et renvoie un nombre »). Dans un projet React ou Next.js d'entreprise, c'est partout.",
  ["Annoter les **paramètres** des fonctions (et souvent le retour)", "Laisser TypeScript **déduire** le reste (`const x = 3` est un `number`)",
   "Décrire les données avec `type` : objets, champs optionnels `?`, tableaux `T[]`", "Lire l'erreur : fichier, ligne, code `TSxxxx`, message"],
  ["TypeScript = JavaScript + des types vérifiés **avant** l'exécution ; à l'exécution, les types disparaissent.",
   "On annote les entrées (paramètres) ; TypeScript déduit les variables locales et souvent le retour.",
   "`type Produit = { nom: string; prix: number; tags?: string[] }` : `?` = le champ peut manquer.",
   "Les **types littéraux** (`'livre' | 'jeu'`) limitent une chaîne à une liste de valeurs.",
   "`any` désactive la vérification : à éviter ; `unknown` = « je ne sais pas encore », à vérifier avant usage."],
  ["Mettre `any` pour faire taire une erreur.", "Annoter tout, même ce qui se déduit (`const n: number = 3`).", "Croire que les types vérifient les données à l'exécution (une réponse d'API peut mentir)."],
  [Q("`function ttc(prix, taux)` en mode strict :", ["c'est accepté", "erreur : le paramètre a implicitement le type any", "prix est un number", "ça plante à l'exécution"], 1, "En strict, chaque paramètre doit avoir un type."),
   Q("`tags?: string[]` veut dire…", ["tags est toujours un tableau", "tags peut être absent (undefined)", "tags peut contenir des undefined", "tags est privé"], 1, "Le `?` rend le champ optionnel."),
   Q("Les types TypeScript à l'exécution :", ["vérifient les réponses d'API", "n'existent plus (le code devient du JavaScript)", "ralentissent le code", "sont dans le navigateur"], 1, "Ils sont effacés à la compilation.")],
  prereq=[
    P("Annotation", "Le type écrit après `:` : `function ttc(prix: number): number`."),
    P("Inférence", "TypeScript déduit le type tout seul : `const total = 0` est un `number`."),
    P("Mode strict", "L'option `strict` du compilateur, activée dans presque tous les projets : refuse les `any` implicites, oblige à gérer `null`…"),
    P("Type littéral", "Un type qui n'accepte qu'une valeur précise : `'livre'`, `42`, `true`. Combiné avec `|` : `'livre' | 'jeu'`."),
  ],
  diagram=D(
    nodes=[
      N("c", 0, 1, "Ton code .ts", "avec des types", kind="file", color="accent"),
      N("t", 1, 1, "Compilateur tsc", "vérifie les types", kind="box", color="warn"),
      N("e", 2, 0, "Erreurs", "si problème", kind="note", color="bad"),
      N("j", 2, 2, "JavaScript", "si ok : types effacés", kind="file", color="good"),
      N("n", 3, 2, "Navigateur / Node", "exécute le JS", kind="pill", color="muted"),
    ],
    edges=[E("c", "t"), E("t", "e"), E("t", "j"), E("j", "n")],
    caption="Les types sont vérifiés avant l'exécution, puis effacés : le navigateur n'exécute que du JavaScript."),
  lessons=[
    L("Pourquoi TypeScript", r"""
Une même fonction écrite deux fois : d'abord en JavaScript, puis en TypeScript. En TypeScript, on ajoute un **type** après chaque paramètre (`prixHT: number`) et après les parenthèses pour la valeur renvoyée (`): number`). Regarde ce qui se passe dans chaque cas quand on l'appelle avec `'10'` (un texte) au lieu de `10` (un nombre).

```ts
function prixTTC(prixHT, taux) {
  return prixHT * (1 + taux);
}
prixTTC('10', 0.2);   // JavaScript : "10" * 1.2 = 12… par hasard. prixTTC('10 €', 0.2) donne NaN.
```

Avec des types, l'erreur apparaît **dans l'éditeur, avant d'exécuter** :

```ts
function prixTTC(prixHT: number, taux: number): number {
  return prixHT * (1 + taux);
}
prixTTC('10', 0.2);
// erreur TS2345 : L'argument de type 'string' n'est pas attribuable au paramètre de type 'number'.
```

Ce que tu gagnes : les bugs de type trouvés tôt, l'autocomplétion (VS Code connaît les champs d'un objet), et une documentation toujours à jour (la signature dit ce qu'on donne et ce qu'on reçoit).

Ce que TypeScript **ne fait pas** : vérifier les données à l'exécution. Les types sont effacés ; une API qui renvoie `"prix": "12"` au lieu de `12` passera (le module 4 montre comment s'en protéger).
"""),
    L("Annoter, déduire, décrire les données", r"""
**Les types de base** : `string`, `number`, `boolean`, `null`, `undefined`, les tableaux `number[]` (ou `Array<number>`), les objets.

**Où annoter** : les paramètres des fonctions, toujours ; le retour, quand c'est une fonction exportée (ça documente et ça protège). Le reste se **déduit** :

```ts
const taux = 0.2;                       // number (déduit)
const noms = ['Ana', 'Léo'];            // string[] (déduit)
function total(lignes: Ligne[]): number {
  let t = 0;                            // number (déduit)
  for (const l of lignes) t += l.prix * l.quantite;   // l : Ligne (déduit)
  return t;
}
```

**Décrire un objet** avec `type` (ou `interface`, presque pareil) :

```ts
type Ligne = { prix: number; quantite: number };

type Produit = {
  id: number;
  nom: string;
  prix: number;
  tags?: string[];                      // optionnel : string[] | undefined
  categorie: 'livre' | 'jeu' | 'musique';   // union de littéraux
};
```

`readonly id: number` empêche de modifier le champ. `Produit[]` est un tableau de produits.
"""),
    L("Lire un message d'erreur", r"""
Une erreur TypeScript a toujours la même forme :

```
panier.ts:12:7  TS2322  Impossible d'assigner le type 'string' au type 'number'.
└─ fichier ─┘ └─┘ └─ code ─┘ └──────────── explication ────────────┘
          ligne:colonne
```

Les plus fréquentes au début :

| Code | Message (résumé) | Cause habituelle |
|---|---|---|
| TS7006 | Le paramètre a implicitement un type 'any' | paramètre sans type |
| TS2322 | Impossible d'assigner le type A au type B | mauvaise valeur dans une variable ou un champ |
| TS2345 | L'argument de type A n'est pas attribuable au paramètre de type B | mauvais argument à l'appel |
| TS2339 | La propriété X n'existe pas sur le type Y | faute de frappe, ou champ oublié dans le type |
| TS2741 | La propriété X est absente du type… | objet incomplet |
| TS2554 | N arguments attendus, mais M reçus | argument oublié ou en trop |

Réflexe : lis le **code** et la **ligne**, puis la **dernière** phrase du message (c'est souvent la plus précise). Le module 6 y revient en détail.
"""),
  ],
  recap=["Annoter les paramètres (et le retour des fonctions exportées) ; laisser déduire le reste.",
         "`type X = { … }`, `?` pour optionnel, `T[]` pour les tableaux, `'a' | 'b'` pour une liste de valeurs.",
         "Pas de `any` pour faire taire une erreur.",
         "Erreur = fichier:ligne, code TSxxxx, message."],
  example=F("produit.ts", "ts", r"""
type Categorie = 'livre' | 'jeu' | 'musique';

type Produit = {
  id: number;
  nom: string;
  prix: number;
  categorie: Categorie;
  tags?: string[];
};

export function libelle(p: Produit): string {
  const etiquettes = p.tags ? ' [' + p.tags.join(', ') + ']' : '';
  return `${p.nom} (${p.categorie}) : ${p.prix.toFixed(2)} €${etiquettes}`;
}

libelle({ id: 1, nom: 'Dune', prix: 9.9, categorie: 'livre' });
// libelle({ id: 2, nom: 'Uno', prix: 7, categorie: 'carte' });   ← TS2322 : 'carte' n'est pas une Categorie
"""),
  notes=["Le type décrit les données une fois.", "La fonction annote son paramètre et son retour.", "Une catégorie inconnue est refusée avant l'exécution."],
  tds=[
    TD(1, "Annoter un fichier JavaScript",
       "Ce fichier vient d'être renommé de `.js` en `.ts` : en mode strict, TypeScript refuse les paramètres sans type. Ajoute les types, sans changer le comportement." + TS,
       ["Crée `type Ligne = { libelle: string; prix: number; quantite: number }` et exporte-le",
        "Annote les paramètres **et** le retour des 4 fonctions : `prixTTC`, `formaterPrix` (renvoie une `string`), `total`, `ligneLaPlusChere` (peut renvoyer `undefined` si la liste est vide)",
        "Plus aucune erreur de type, et pas de `any`",
        "Les appels faux (prix en chaîne, ligne incomplète) doivent être refusés"],
       [F("panier.ts", "ts", r"""
// Renommé de panier.js : TypeScript (strict) signale des erreurs.

export function prixTTC(prixHT, taux) {
  return Math.round(prixHT * (1 + taux) * 100) / 100;
}

export function formaterPrix(montant) {
  return montant.toFixed(2).replace('.', ',') + ' €';
}

export function total(lignes) {
  return lignes.reduce((t, l) => t + l.prix * l.quantite, 0);
}

export function ligneLaPlusChere(lignes) {
  let max;
  for (const l of lignes) if (!max || l.prix * l.quantite > max.prix * max.quantite) max = l;
  return max;
}
""")],
       ["`export function prixTTC(prixHT: number, taux: number): number`.",
        "`total(lignes: Ligne[]): number` ; dans le `reduce`, TypeScript déduit `t` et `l`.",
        "`ligneLaPlusChere(lignes: Ligne[]): Ligne | undefined` et `let max: Ligne | undefined;`."],
       [F("panier.ts", "ts", r"""
export type Ligne = { libelle: string; prix: number; quantite: number };

export function prixTTC(prixHT: number, taux: number): number {
  return Math.round(prixHT * (1 + taux) * 100) / 100;
}

export function formaterPrix(montant: number): string {
  return montant.toFixed(2).replace('.', ',') + ' €';
}

export function total(lignes: Ligne[]): number {
  return lignes.reduce((t, l) => t + l.prix * l.quantite, 0);
}

export function ligneLaPlusChere(lignes: Ligne[]): Ligne | undefined {
  let max: Ligne | undefined;
  for (const l of lignes) if (!max || l.prix * l.quantite > max.prix * max.quantite) max = l;
  return max;
}
""")],
       ["Plus d'erreur TS7006", "Les mauvais appels sont refusés"],
       run=TRUN("panier.ts", tests=r"""
assert.noTypeErrors('Plus aucune erreur de type dans panier.ts');
assert(!/:\s*any\b|<any>|as any/.test(source('panier.ts')), 'Pas de any');
const m = require('./panier');
assert.equal(m.prixTTC(10, 0.2), 12, 'prixTTC(10, 0.2) = 12');
assert.equal(m.formaterPrix(3.5), '3,50 €', 'formaterPrix(3.5) = "3,50 €"');
const L = [{ libelle: 'Clavier', prix: 50, quantite: 1 }, { libelle: 'Souris', prix: 20, quantite: 3 }];
assert.equal(m.total(L), 110, 'total = 110');
assert.equal(m.ligneLaPlusChere(L).libelle, 'Souris', 'ligneLaPlusChere : Souris (60 €)');
assert.equal(m.ligneLaPlusChere([]), undefined, 'liste vide : undefined');
""", typetests=r"""
import { prixTTC, formaterPrix, total, ligneLaPlusChere, type Ligne } from './panier';
// ✗ un prix en chaîne
prixTTC('10', 0.2);
// ✗ une ligne sans quantité
total([{ libelle: 'Clavier', prix: 50 }]);
// ✓ une liste vide
total([]);
// ✓ formaterPrix renvoie une string
const s: string = formaterPrix(1);
// ✗ formaterPrix ne renvoie pas un nombre
const n: number = formaterPrix(1);
// ✗ ligneLaPlusChere peut renvoyer undefined : on ne peut pas lire .prix sans vérifier
const p: number = ligneLaPlusChere([]).prix;
// ✓ le type Ligne est exporté
const l: Ligne = { libelle: 'x', prix: 1, quantite: 1 };
""")),
    TD(2, "Les erreurs de type sont des bugs",
       "Ce fichier compile en JavaScript, mais TypeScript y signale 5 erreurs. Chacune cache un **vrai bug** (les tests le montrent). Corrige le code (pas les types), sans `any`, sans `as`, sans `@ts-ignore`." + TS,
       ["`age` est lu depuis un formulaire : convertis-le en nombre avant de comparer",
        "Corrige la faute de frappe sur la propriété de l'utilisateur, et l'argument oublié",
        "`initiales` doit renvoyer une chaîne dans **tous** les cas (chaîne vide si pas de nom)",
        "Plus aucune erreur de type ; les tests de comportement passent"],
       [F("profil.ts", "ts", r"""
export type Utilisateur = { prenom: string; nom: string; email: string; age: number };

export function lireAge(saisie: string): number {
  const age: number = saisie;
  return age;
}

export function estMajeur(u: Utilisateur): boolean {
  return u.age >= 18;
}

export function signature(u: Utilisateur): string {
  return u.prenom + ' ' + u.nmo.toUpperCase();
}

export function initiales(nomComplet: string): string {
  const morceaux = nomComplet.trim().split(/\s+/).filter(Boolean);
  if (morceaux.length > 0) {
    return morceaux.map((m) => m[0].toUpperCase()).join('');
  }
}

export function salutation(u: Utilisateur, matin: boolean): string {
  return (matin ? 'Bonjour ' : 'Bonsoir ') + u.prenom;
}

export const message = salutation({ prenom: 'Ana', nom: 'Martin', email: 'ana@exemple.fr', age: 30 });
""")],
       ["`lireAge` : `Number(saisie)` convertit la chaîne.",
        "`u.nmo` → `u.nom` ; `salutation(…)` attend un 2e argument (`true` ou `false`).",
        "`initiales` : ajoute un `return ''` après le `if`."],
       [F("profil.ts", "ts", r"""
export type Utilisateur = { prenom: string; nom: string; email: string; age: number };

export function lireAge(saisie: string): number {
  const age: number = Number(saisie);
  return age;
}

export function estMajeur(u: Utilisateur): boolean {
  return u.age >= 18;
}

export function signature(u: Utilisateur): string {
  return u.prenom + ' ' + u.nom.toUpperCase();
}

export function initiales(nomComplet: string): string {
  const morceaux = nomComplet.trim().split(/\s+/).filter(Boolean);
  if (morceaux.length > 0) {
    return morceaux.map((m) => m[0].toUpperCase()).join('');
  }
  return '';
}

export function salutation(u: Utilisateur, matin: boolean): string {
  return (matin ? 'Bonjour ' : 'Bonsoir ') + u.prenom;
}

export const message = salutation({ prenom: 'Ana', nom: 'Martin', email: 'ana@exemple.fr', age: 30 }, true);
""")],
       ["Chaque erreur était un bug", "Corrigé sans tricher"],
       run=TRUN("profil.ts", tests=r"""
assert.noTypeErrors('Plus aucune erreur de type');
assert(!/\bany\b|\bas\s+[A-Za-z{]|@ts-ignore|@ts-expect-error|@ts-nocheck/.test(source('profil.ts')), 'Sans any, sans as, sans @ts-ignore');
const m = require('./profil');
assert(m.lireAge('17') === 17, 'lireAge("17") renvoie le NOMBRE 17');
const u = { prenom: 'Ana', nom: 'Martin', email: 'a@b.c', age: m.lireAge('9') };
assert.equal(m.estMajeur(u), false, 'âge "9" : pas majeur (comparaison de nombres, pas de chaînes)');
assert.equal(m.signature(u), 'Ana MARTIN', 'signature : « Ana MARTIN »');
assert.equal(m.initiales('ana marie martin'), 'AMM', 'initiales');
assert.equal(m.initiales('   '), '', 'initiales sans nom : chaîne vide (pas undefined)');
assert.equal(m.message, 'Bonjour Ana', 'message : « Bonjour Ana »');
""")),
    TD(3, "Décrire les données d'un catalogue",
       "Écris les types d'un petit catalogue et les fonctions qui l'utilisent. Les types doivent **empêcher** les données incorrectes." + TS,
       ["`type Categorie` : `'livre'`, `'jeu'` ou `'musique'` uniquement ; `type Produit` : `id` (non modifiable), `nom`, `prix`, `categorie`, `tags` optionnel (liste de chaînes), `enStock`",
        "`parCategorie(produits, categorie)` renvoie les produits de cette catégorie",
        "`prixMoyen(produits)` renvoie la moyenne des prix, ou `null` si la liste est vide",
        "`tousLesTags(produits)` renvoie les tags sans doublon, triés"],
       [F("catalogue.ts", "ts", r"""
// à toi : Categorie, Produit

export function parCategorie(produits, categorie) {
  return produits.filter((p) => p.categorie === categorie);
}

export function prixMoyen(produits) {
  // à toi
}

export function tousLesTags(produits) {
  // à toi
}
""")],
       ["`readonly id: number` ; `tags?: string[]`.",
        "`prixMoyen(produits: Produit[]): number | null`.",
        "Tags : `[...new Set(produits.flatMap((p) => p.tags ?? []))].sort()`."],
       [F("catalogue.ts", "ts", r"""
export type Categorie = 'livre' | 'jeu' | 'musique';

export type Produit = {
  readonly id: number;
  nom: string;
  prix: number;
  categorie: Categorie;
  tags?: string[];
  enStock: boolean;
};

export function parCategorie(produits: Produit[], categorie: Categorie): Produit[] {
  return produits.filter((p) => p.categorie === categorie);
}

export function prixMoyen(produits: Produit[]): number | null {
  if (produits.length === 0) return null;
  return produits.reduce((t, p) => t + p.prix, 0) / produits.length;
}

export function tousLesTags(produits: Produit[]): string[] {
  return [...new Set(produits.flatMap((p) => p.tags ?? []))].sort();
}
""")],
       ["Les types refusent les données fausses", "Les fonctions sont typées de bout en bout"],
       run=TRUN("catalogue.ts", tests=r"""
assert.noTypeErrors('Aucune erreur de type');
const m = require('./catalogue');
const P = [
  { id: 1, nom: 'Dune', prix: 10, categorie: 'livre', tags: ['sf', 'classique'], enStock: true },
  { id: 2, nom: 'Uno', prix: 8, categorie: 'jeu', enStock: false },
  { id: 3, nom: 'Fondation', prix: 12, categorie: 'livre', tags: ['sf'], enStock: true },
];
assert.deepEqual(m.parCategorie(P, 'livre').map((p) => p.id), [1, 3], 'parCategorie livre : 1 et 3');
assert.equal(m.prixMoyen(P), 10, 'prixMoyen : 10');
assert.equal(m.prixMoyen([]), null, 'prixMoyen d\'une liste vide : null');
assert.deepEqual(m.tousLesTags(P), ['classique', 'sf'], 'tousLesTags : sans doublon, triés');
""", typetests=r"""
import { parCategorie, prixMoyen, tousLesTags, type Produit, type Categorie } from './catalogue';
const ok: Produit = { id: 1, nom: 'Dune', prix: 10, categorie: 'livre', enStock: true };
// ✓ un produit sans tags
const sansTags: Produit = { id: 2, nom: 'Uno', prix: 8, categorie: 'jeu', enStock: false };
// ✗ une catégorie inconnue
const film: Produit = { id: 3, nom: 'Alien', prix: 9, categorie: 'film', enStock: true };
// ✗ un prix en chaîne
const prixTexte: Produit = { id: 4, nom: 'X', prix: '12', categorie: 'jeu', enStock: true };
// ✗ un produit sans enStock
const incomplet: Produit = { id: 5, nom: 'Y', prix: 1, categorie: 'jeu' };
// ✗ l'id n'est pas modifiable
ok.id = 99;
// ✗ parCategorie refuse une catégorie inconnue
parCategorie([ok], 'film');
// ✗ prixMoyen peut renvoyer null : pas directement un number
const moyenne: number = prixMoyen([ok]);
// ✓ tousLesTags renvoie des string
const tags: string[] = tousLesTags([ok]);
// ✓ Categorie accepte 'musique'
const c: Categorie = 'musique';
""")),
  ])

# =========================================================================== 2. Unions et narrowing
unions = DM("ts-unions", "Unions et rétrécissement des types", 30,
  "Utiliser les unions (`A | B`) et apprendre à TypeScript dans quel cas on est (rétrécissement : `typeof`, `===`, `in`, champ discriminant), jusqu'aux unions discriminées et au `switch` exhaustif.",
  "Les données réelles prennent plusieurs formes : un paiement par carte OU par virement, un écran en chargement OU en erreur OU chargé. Les unions décrivent ça exactement, et TypeScript vérifie qu'on n'oublie aucun cas.",
  ["Écrire l'union de toutes les formes possibles", "Vérifier dans quel cas on est (`typeof x === 'string'`, `x.type === 'carte'`, `'iban' in x`)",
   "Dans chaque branche, TypeScript **connaît** le type précis", "`switch` sur le champ discriminant + vérification **exhaustive** (`never`)"],
  ["Une valeur `string | number` ne permet que ce qui est commun aux deux, tant qu'on n'a pas vérifié lequel c'est.",
   "Après `if (typeof x === 'string')`, x est une `string` dans le `if` et un `number` après.",
   "Union discriminée : chaque variante a un champ commun littéral (`type: 'carte'`) qui dit laquelle c'est.",
   "Un `default` qui assigne à `never` fait échouer la compilation si on ajoute une variante sans la gérer.",
   "Décrire les états avec une union rend les états impossibles… impossibles (pas de « chargé mais sans données »)."],
  ["Des champs tous optionnels au lieu d'une union (`{ chargement?: boolean; erreur?: string; donnees?: T }`).", "Un `as` pour forcer le type au lieu de vérifier.", "Oublier le `default` exhaustif."],
  [Q("Après `if (typeof v === 'number') return …`, la suite du code sait que v est…", ["number", "le reste de l'union (sans number)", "any", "unknown"], 1, "TypeScript retire les cas déjà traités."),
   Q("Une union discriminée a…", ["un champ commun avec une valeur littérale différente par variante", "des champs tous optionnels", "une classe par variante", "un enum obligatoire"], 0, "C'est ce champ qui permet de savoir dans quel cas on est."),
   Q("À quoi sert `const _exhaustif: never = p;` dans le `default` ?", ["à rien", "à faire échouer la compilation si une variante n'est pas gérée", "à lever une erreur à l'exécution seulement", "à vider p"], 1, "Si une variante reste, elle n'est pas assignable à never.")],
  prereq=[
    P("Union", "`A | B` : une valeur qui est soit un A, soit un B."),
    P("Rétrécissement (narrowing)", "Quand une condition permet à TypeScript de savoir quel cas de l'union on traite."),
    P("Union discriminée", "Une union d'objets qui ont tous un champ littéral commun (`type`, `statut`, `kind`) différent par variante."),
    P("`never`", "Le type qui n'a aucune valeur : ce qui reste quand tous les cas ont été traités."),
  ],
  diagram=D(
    nodes=[
      N("u", 0, 1, "Paiement", "carte | virement | espèces", kind="db", color="accent"),
      N("s", 1, 1, "switch (p.type)", "+ default : never", kind="box", color="warn"),
      N("c", 2, 0, "case 'carte'", "p.numero connu", kind="pill", color="good"),
      N("v", 2, 2, "case 'virement'", "p.iban connu", kind="pill", color="good"),
      N("e", 3, 1, "case 'especes'", "rien de plus", kind="pill", color="good"),
    ],
    edges=[E("u", "s"), E("s", "c"), E("s", "v"), E("s", "e")],
    caption="Un champ commun dit quelle variante on a ; dans chaque case, TypeScript connaît ses champs ; le default exhaustif attrape les oublis."),
  lessons=[
    L("Unions et rétrécissement", r"""
Une **union** `string | number | null` veut dire « l'un de ces types ». Tant que TypeScript ne sait pas lequel, il refuse les méthodes propres à un seul type (`toFixed` n'existe que sur les nombres, `trim` que sur les textes). Le **rétrécissement**, c'est vérifier le type avec un `if` (`typeof v === 'number'`) : après ce test, TypeScript sait lequel c'est. Pour lire le code : `nombre.toFixed(2)` écrit le nombre avec 2 décimales, `texte.trim()` retire les espaces autour.

```ts
function formater(v: string | number | null): string {
  // v.toFixed(2)           ← erreur : toFixed n'existe pas sur string ni sur null
  if (v === null) return '—';                 // ici v : null
  if (typeof v === 'number') return v.toFixed(2);   // ici v : number
  return v.trim();                            // ici v : string (le seul cas restant)
}
```

Les vérifications que TypeScript comprend :

| Vérification | Pour |
|---|---|
| `typeof x === 'string'` / `'number'` / `'boolean'` | les types primitifs |
| `x === null`, `x === undefined`, `if (x)` | enlever null / undefined |
| `x instanceof Date` | les classes |
| `Array.isArray(x)` | les tableaux |
| `'iban' in x` | un champ présent seulement dans une variante |
| `x.type === 'carte'` | une union discriminée (le plus courant) |
"""),
    L("Unions discriminées", r"""
Une **union discriminée** est une union d'objets qui ont tous un champ commun avec une valeur fixe différente, ici `type: 'carte'`, `'virement'` ou `'especes'`. En testant ce champ (avec un `switch`), TypeScript sait quels autres champs existent. Dans le code : `texte.slice(-4)` garde les 4 derniers caractères, `slice(0, 4)` les 4 premiers ; `never` est le type « impossible », qu'on utilise pour vérifier que tous les cas ont été traités.

```ts
type Paiement =
  | { type: 'carte'; numero: string; expire: string }
  | { type: 'virement'; iban: string }
  | { type: 'especes' };

function libelle(p: Paiement): string {
  switch (p.type) {
    case 'carte':
      return 'Carte ****' + p.numero.slice(-4);   // p.numero existe ici
    case 'virement':
      return 'Virement ' + p.iban.slice(0, 4);    // p.iban existe ici
    case 'especes':
      return 'Espèces';
    default: {
      const _exhaustif: never = p;                // plus aucun cas possible
      return _exhaustif;
    }
  }
}
```

Le jour où quelqu'un ajoute `| { type: 'cheque'; numero: string }`, la ligne `never` provoque une **erreur de compilation** : impossible d'oublier de gérer le nouveau cas.
"""),
    L("Rendre les états impossibles impossibles", r"""
Comparer deux façons de décrire l'état d'un chargement :

```ts
// ✗ tous les mélanges sont permis : { chargement: true, erreur: 'x', donnees: [...] } ?!
type EtatFlou = { chargement: boolean; erreur?: string; donnees?: Produit[] };

// ✓ seulement les états qui existent vraiment
type Etat =
  | { statut: 'chargement' }
  | { statut: 'erreur'; message: string }
  | { statut: 'succes'; donnees: Produit[] };
```

Avec `Etat`, on **ne peut pas** lire `donnees` sans avoir vérifié `statut === 'succes'`, et on ne peut pas créer un état « succès sans données ». Beaucoup de bugs d'interface (spinner qui tourne avec une erreur affichée…) disparaissent.

`as const` fige un tableau ou un objet en littéraux : `const ROLES = ['admin', 'membre'] as const; type Role = (typeof ROLES)[number];` donne `'admin' | 'membre'`.
"""),
  ],
  recap=["`A | B` : seul ce qui est commun est permis avant de vérifier.",
         "`typeof`, `===`, `in`, `instanceof`, `Array.isArray`, champ discriminant : TypeScript rétrécit le type.",
         "Union discriminée + `switch` + `default` en `never` = aucun cas oublié.",
         "Décrire les états par une union : les états impossibles n'existent plus."],
  example=F("etat.ts", "ts", r"""
type Etat =
  | { statut: 'chargement' }
  | { statut: 'erreur'; message: string }
  | { statut: 'succes'; donnees: string[] };

export function resume(e: Etat): string {
  switch (e.statut) {
    case 'chargement': return 'Chargement…';
    case 'erreur': return 'Erreur : ' + e.message;
    case 'succes': return e.donnees.length + ' élément(s)';
    default: { const _x: never = e; return _x; }
  }
}
"""),
  notes=["Chaque statut a ses propres champs.", "Dans chaque case, TypeScript sait lesquels existent.", "Le default `never` attrape les oublis."],
  tds=[
    TD(1, "Une fonction qui accepte plusieurs types",
       "`formater` reçoit une valeur venant d'un tableur : texte, nombre, date, booléen ou vide. Écris-la avec une union et des vérifications de type." + TS,
       ["`type Cellule = string | number | boolean | Date | null` et `formater(v: Cellule): string`",
        "`null` → `'—'` ; nombre → 2 décimales avec une virgule (`3,50`) ; booléen → `oui` / `non` ; date → `JJ/MM/AAAA` ; texte → sans espaces autour",
        "Pas de `any` ni de `as` : uniquement des vérifications (`typeof`, `instanceof`, `===`)",
        "Les autres types (objets, tableaux) sont refusés par TypeScript"],
       [F("cellule.ts", "ts", r"""
export type Cellule = string | number | boolean | Date | null;

export function formater(v: Cellule): string {
  return v.trim();   // TypeScript refuse : v n'est pas forcément une string
}
""")],
       ["Commence par `if (v === null) return '—';`.",
        "Date : `v instanceof Date` ; `String(v.getDate()).padStart(2, '0')`, et `v.getMonth() + 1` pour le mois.",
        "Le dernier cas (après tous les autres `return`) est forcément une `string`."],
       [F("cellule.ts", "ts", r"""
export type Cellule = string | number | boolean | Date | null;

const deux = (n: number) => String(n).padStart(2, '0');

export function formater(v: Cellule): string {
  if (v === null) return '—';
  if (typeof v === 'number') return v.toFixed(2).replace('.', ',');
  if (typeof v === 'boolean') return v ? 'oui' : 'non';
  if (v instanceof Date) return `${deux(v.getDate())}/${deux(v.getMonth() + 1)}/${v.getFullYear()}`;
  return v.trim();
}
""")],
       ["Chaque branche connaît son type", "Pas de as"],
       run=TRUN("cellule.ts", tests=r"""
assert.noTypeErrors('Aucune erreur de type');
assert(!/\bany\b|\bas\s+[A-Za-z]/.test(source('cellule.ts')), 'Pas de any ni de as : seulement des vérifications');
const { formater: f } = require('./cellule');
assert.equal(f(null), '—', 'null → —');
assert.equal(f(3.5), '3,50', '3.5 → 3,50');
assert.equal(f(0), '0,00', '0 → 0,00 (0 n\'est pas « vide »)');
assert.equal(f(true), 'oui', 'true → oui');
assert.equal(f(false), 'non', 'false → non');
assert.equal(f(new Date(2026, 0, 5)), '05/01/2026', 'date → 05/01/2026');
assert.equal(f('  Ana  '), 'Ana', 'texte → sans espaces');
assert.equal(f(''), '', 'texte vide → chaîne vide');
""", typetests=r"""
import { formater } from './cellule';
// ✓ un nombre
formater(12);
// ✓ null
formater(null);
// ✗ un objet
formater({ valeur: 1 });
// ✗ un tableau
formater([1, 2]);
// ✗ undefined (seul null est prévu)
formater(undefined);
""")),
    TD(2, "Union discriminée : les moyens de paiement",
       "Décris les moyens de paiement avec une union discriminée, puis écris les fonctions avec un `switch` **exhaustif**." + TS,
       ["`type Paiement` : `{ type: 'carte'; numero: string; expire: string }`, `{ type: 'virement'; iban: string }`, `{ type: 'especes' }`",
        "`libelle(p)` : `Carte ****1234` (4 derniers chiffres), `Virement FR76…` (4 premiers caractères de l'IBAN + `…`), `Espèces`",
        "`frais(p, montant)` : carte 1,5 % (arrondi au centime), virement 0, espèces 0 au-delà de 1000 € → erreur `Espèces limitées à 1000 €`",
        "Chaque `switch` a un `default` qui assigne `p` à une variable de type `never`"],
       [F("paiement.ts", "ts", r"""
// à toi : le type Paiement (union discriminée)

export function libelle(p) {
  // à toi
}

export function frais(p, montant: number): number {
  // à toi
}
""")],
       ["Le champ discriminant est `type` : `switch (p.type) { case 'carte': … }`.",
        "`default: { const _x: never = p; return _x; }`",
        "Frais carte : `Math.round(montant * 0.015 * 100) / 100`."],
       [F("paiement.ts", "ts", r"""
export type Paiement =
  | { type: 'carte'; numero: string; expire: string }
  | { type: 'virement'; iban: string }
  | { type: 'especes' };

export function libelle(p: Paiement): string {
  switch (p.type) {
    case 'carte':
      return 'Carte ****' + p.numero.slice(-4);
    case 'virement':
      return 'Virement ' + p.iban.slice(0, 4) + '…';
    case 'especes':
      return 'Espèces';
    default: {
      const _exhaustif: never = p;
      return _exhaustif;
    }
  }
}

export function frais(p: Paiement, montant: number): number {
  switch (p.type) {
    case 'carte':
      return Math.round(montant * 0.015 * 100) / 100;
    case 'virement':
      return 0;
    case 'especes':
      if (montant > 1000) throw new Error('Espèces limitées à 1000 €');
      return 0;
    default: {
      const _exhaustif: never = p;
      return _exhaustif;
    }
  }
}
""")],
       ["Chaque variante a ses champs", "Un nouveau moyen de paiement oublié = erreur de compilation"],
       run=TRUN("paiement.ts", tests=r"""
assert.noTypeErrors('Aucune erreur de type');
const src = source('paiement.ts');
assert((src.match(/:\s*never\s*=/g) || []).length >= 2, 'Les deux switch ont un default exhaustif (variable de type never)');
const { libelle, frais } = require('./paiement');
assert.equal(libelle({ type: 'carte', numero: '4970123412341234', expire: '12/28' }), 'Carte ****1234', 'carte');
assert.equal(libelle({ type: 'virement', iban: 'FR7630001007941234567890185' }), 'Virement FR76…', 'virement');
assert.equal(libelle({ type: 'especes' }), 'Espèces', 'espèces');
assert.equal(frais({ type: 'carte', numero: '1', expire: '1' }, 99.99), 1.5, 'frais carte 1,5 % de 99,99 € → 1,50');
assert.equal(frais({ type: 'virement', iban: 'FR' }, 500), 0, 'frais virement 0');
let e = ''; try { frais({ type: 'especes' }, 1500); } catch (x) { e = x.message; }
assert.equal(e, 'Espèces limitées à 1000 €', 'espèces au-delà de 1000 € : erreur');
""", typetests=r"""
import { libelle, type Paiement } from './paiement';
// ✓ un virement avec son iban
const v: Paiement = { type: 'virement', iban: 'FR76' };
// ✗ une carte sans numéro
const c: Paiement = { type: 'carte', expire: '12/28' };
// ✗ un virement avec un numéro de carte au lieu d'un iban
const m: Paiement = { type: 'virement', numero: '1234' };
// ✗ un type de paiement inconnu
libelle({ type: 'cheque' });
declare const p: Paiement;
// ✗ lire iban sans avoir vérifié le type
const iban: string = p.iban;
""")),
    TD(3, "Des états impossibles… impossibles",
       "L'état d'un écran est décrit avec des champs optionnels : rien n'empêche « chargement + erreur + données » en même temps, et le code lit `donnees` sans vérifier. Remplace-le par une **union discriminée** sur `statut`." + TS,
       ["`type EtatProfil` : `{ statut: 'chargement' }`, `{ statut: 'erreur'; message: string }`, `{ statut: 'succes'; profil: Profil }`",
        "`texte(etat)` : `Chargement…`, `Erreur : <message>`, `Bonjour <prenom>` ; avec un `switch` exhaustif",
        "`charger(reponse)` construit l'état à partir d'une réponse `{ ok: boolean; donnees?: Profil; erreur?: string }` (ok sans données = erreur `Réponse vide`)",
        "Les états incohérents sont refusés par TypeScript"],
       [F("etat.ts", "ts", r"""
export type Profil = { prenom: string; email: string };

export type EtatProfil = {
  chargement: boolean;
  erreur?: string;
  profil?: Profil;
};

export function texte(etat: EtatProfil): string {
  if (etat.chargement) return 'Chargement…';
  if (etat.erreur) return 'Erreur : ' + etat.erreur;
  return 'Bonjour ' + etat.profil.prenom;
}

export function charger(reponse: { ok: boolean; donnees?: Profil; erreur?: string }): EtatProfil {
  if (!reponse.ok) return { chargement: false, erreur: reponse.erreur };
  return { chargement: false, profil: reponse.donnees };
}
""")],
       ["`switch (etat.statut)` dans `texte`, avec `default` en `never`.",
        "`charger` : `if (!reponse.ok) return { statut: 'erreur', message: reponse.erreur ?? 'Erreur inconnue' };`",
        "Ok sans données : `if (!reponse.donnees) return { statut: 'erreur', message: 'Réponse vide' };`."],
       [F("etat.ts", "ts", r"""
export type Profil = { prenom: string; email: string };

export type EtatProfil =
  | { statut: 'chargement' }
  | { statut: 'erreur'; message: string }
  | { statut: 'succes'; profil: Profil };

export function texte(etat: EtatProfil): string {
  switch (etat.statut) {
    case 'chargement':
      return 'Chargement…';
    case 'erreur':
      return 'Erreur : ' + etat.message;
    case 'succes':
      return 'Bonjour ' + etat.profil.prenom;
    default: {
      const _exhaustif: never = etat;
      return _exhaustif;
    }
  }
}

export function charger(reponse: { ok: boolean; donnees?: Profil; erreur?: string }): EtatProfil {
  if (!reponse.ok) return { statut: 'erreur', message: reponse.erreur ?? 'Erreur inconnue' };
  if (!reponse.donnees) return { statut: 'erreur', message: 'Réponse vide' };
  return { statut: 'succes', profil: reponse.donnees };
}
""")],
       ["Plus d'état incohérent possible", "Impossible de lire le profil sans vérifier"],
       run=TRUN("etat.ts", tests=r"""
assert.noTypeErrors('Aucune erreur de type');
const { texte, charger } = require('./etat');
assert.equal(texte({ statut: 'chargement' }), 'Chargement…', 'chargement');
assert.equal(texte({ statut: 'erreur', message: 'Hors ligne' }), 'Erreur : Hors ligne', 'erreur');
assert.equal(texte({ statut: 'succes', profil: { prenom: 'Ana', email: 'a@b.c' } }), 'Bonjour Ana', 'succès');
assert.deepEqual(charger({ ok: false, erreur: '500' }), { statut: 'erreur', message: '500' }, 'charger : réponse en erreur');
assert.deepEqual(charger({ ok: true }), { statut: 'erreur', message: 'Réponse vide' }, 'charger : ok mais sans données → Réponse vide');
assert.deepEqual(charger({ ok: true, donnees: { prenom: 'Léo', email: 'l@b.c' } }), { statut: 'succes', profil: { prenom: 'Léo', email: 'l@b.c' } }, 'charger : succès');
""", typetests=r"""
import { texte, type EtatProfil } from './etat';
// ✓ un état de chargement
const a: EtatProfil = { statut: 'chargement' };
// ✗ chargement ET erreur en même temps
const b: EtatProfil = { statut: 'chargement', message: 'x' };
// ✗ succès sans profil
const c: EtatProfil = { statut: 'succes' };
// ✗ erreur sans message
const d: EtatProfil = { statut: 'erreur' };
declare const e: EtatProfil;
// ✗ lire le profil sans vérifier le statut
const prenom = e.profil.prenom;
""")),
  ])

# =========================================================================== 3. Génériques
generiques = DM("ts-generiques", "Génériques et types utilitaires", 30,
  "Écrire des fonctions et des types réutilisables avec les génériques (`<T>`), contraindre un générique (`extends`, `keyof`), et dériver des types avec `Partial`, `Pick`, `Omit`, `Record`.",
  "Sans génériques, on duplique (`premierProduit`, `premierUtilisateur`…) ou on met `any`. Les génériques et les types utilitaires permettent d'écrire une fois, en gardant les types exacts.",
  ["Remplacer le type précis par un **paramètre de type** `T`", "**Contraindre** `T` quand on a besoin de quelque chose (`T extends { id: number }`)",
   "`K extends keyof T` pour accepter seulement un nom de champ existant", "Dériver les types d'un type de base : `Omit`, `Partial`, `Pick`, `Record`"],
  ["`function premier<T>(xs: T[]): T | undefined` : le type de sortie suit le type d'entrée.",
   "TypeScript déduit `T` à l'appel : `premier([1, 2])` → `number | undefined`.",
   "`keyof Produit` = `'id' | 'nom' | 'prix'…` ; `T[K]` = le type du champ K.",
   "Un seul type source (`Utilisateur`), les autres en dérivent : `Omit<Utilisateur, 'id'>` pour la création, `Partial<…>` pour la modification.",
   "`Resultat<T>` (succès ou erreur) : un générique très utile pour les fonctions qui peuvent échouer."],
  ["Mettre `any` au lieu d'un générique.", "Recopier un type au lieu de le dériver (ils divergent au premier changement).", "Un générique sans contrainte alors qu'on utilise `x.id` (erreur)."],
  [Q("`premier(['a', 'b'])` avec `premier<T>(xs: T[]): T | undefined` renvoie…", ["any", "string | undefined", "T", "unknown"], 1, "T est déduit : string."),
   Q("Le type pour créer un utilisateur (sans id ni date, générés par le serveur) :", ["Partial<Utilisateur>", "Omit<Utilisateur, 'id' | 'creeLe'>", "Pick<Utilisateur, 'id'>", "any"], 1, "On retire ce que le client ne fournit pas."),
   Q("`K extends keyof T` sert à…", ["accepter n'importe quelle chaîne", "n'accepter que les noms de champs de T", "copier T", "rendre T optionnel"], 1, "Une faute de frappe dans le nom de champ devient une erreur.")],
  prereq=[
    P("Générique", "Un type en paramètre : `function f<T>(x: T): T`. Comme un paramètre de fonction, mais pour un type."),
    P("Contrainte", "`<T extends Forme>` : T doit au moins avoir la forme indiquée."),
    P("`keyof`", "L'union des noms de champs d'un type : `keyof { a: 1; b: 2 }` = `'a' | 'b'`."),
    P("Type utilitaire", "Un type générique fourni par TypeScript qui transforme un autre type : `Partial`, `Required`, `Pick`, `Omit`, `Record`, `Readonly`, `ReturnType`…"),
  ],
  diagram=D(
    nodes=[
      N("u", 0, 1, "Utilisateur", "le type source", kind="db", color="accent"),
      N("n", 1, 0, "Omit<…, 'id'>", "création", kind="pill", color="good"),
      N("k", 1, 2, "Pick<…, 'nom'>", "affichage public", kind="pill", color="good"),
      N("p", 2, 1, "Partial<…>", "modification", kind="pill", color="good"),
      N("r", 3, 1, "Record<Role, …[]>", "regroupement", kind="pill", color="warn"),
    ],
    edges=[E("u", "n"), E("u", "p"), E("u", "k"), E("p", "r", dashed=True)],
    caption="Un seul type source ; les autres en dérivent et suivent automatiquement ses changements."),
  lessons=[
    L("Fonctions génériques", r"""
Une fonction **générique** a un paramètre de **type**, écrit entre chevrons après son nom : `premier<T>`. `T` est une variable qui contient un type : à l'appel, TypeScript le remplace par le vrai type (`number`, `Produit`…). Dans les exemples : `xs.find((x) => condition)` renvoie le premier élément qui respecte la condition (ou `undefined`), `[...xs]` fait une copie du tableau, `xs.sort(...)` le trie, et `keyof T` désigne « un des noms de champs de T ».

```ts
function premier<T>(xs: T[]): T | undefined {
  return xs[0];
}
const n = premier([1, 2, 3]);         // number | undefined
const p = premier(produits);          // Produit | undefined
```

`T` est un **paramètre de type** : TypeScript le déduit à l'appel. Sans générique, il faudrait `any` (et on perdrait tout) ou une fonction par type.

**Contraindre** quand on utilise quelque chose de `T` :

```ts
function trouverParId<T extends { id: number }>(xs: T[], id: number): T | undefined {
  return xs.find((x) => x.id === id);   // x.id existe grâce à la contrainte
}
```

**Un nom de champ** valide :

```ts
function trierPar<T, K extends keyof T>(xs: T[], cle: K): T[] {
  return [...xs].sort((a, b) => (a[cle] < b[cle] ? -1 : a[cle] > b[cle] ? 1 : 0));
}
trierPar(produits, 'prix');     // ✓
trierPar(produits, 'pirx');     // ✗ erreur : 'pirx' n'est pas une clé de Produit
```
"""),
    L("Types utilitaires : dériver au lieu de recopier", r"""
| Type utilitaire | Effet | Usage typique |
|---|---|---|
| `Partial<T>` | tous les champs optionnels | données d'un PATCH |
| `Required<T>` | tous obligatoires | après validation |
| `Readonly<T>` | tous en lecture seule | état immuable |
| `Pick<T, 'a' \| 'b'>` | garde seulement ces champs | vue publique, DTO de sortie |
| `Omit<T, 'a' \| 'b'>` | retire ces champs | données de création (sans `id`) |
| `Record<K, V>` | objet avec les clés K et les valeurs V | regroupement, dictionnaire |
| `ReturnType<typeof f>` | le type renvoyé par f | réutiliser un résultat |
| `Awaited<P>` | le type dans une Promise | résultat d'une fonction async |

```ts
type Utilisateur = { id: number; nom: string; email: string; role: Role; creeLe: string };

type NouvelUtilisateur = Omit<Utilisateur, 'id' | 'creeLe'>;      // ce que le formulaire envoie
type ModifUtilisateur = Partial<NouvelUtilisateur>;               // un PATCH
type UtilisateurPublic = Pick<Utilisateur, 'id' | 'nom'>;         // ce qu'on montre aux autres
```

Ajouter un champ à `Utilisateur` le propage partout ; avec des copies, il faudrait penser à les modifier toutes.
"""),
    L("Types génériques : Resultat<T>", r"""
Un type peut aussi avoir des paramètres :

```ts
type Resultat<T> = { ok: true; valeur: T } | { ok: false; erreur: string };

function diviser(a: number, b: number): Resultat<number> {
  if (b === 0) return { ok: false, erreur: 'Division par zéro' };
  return { ok: true, valeur: a / b };
}

const r = diviser(10, 2);
if (r.ok) console.log(r.valeur);      // number
else console.log(r.erreur);           // string
```

C'est le même principe que le `safeParse` de zod (`{ success: true, data } | { success: false, error }`) : une union discriminée **générique**. On l'utilise pour les fonctions qui peuvent échouer de façon prévue, au lieu de lever une exception.
"""),
  ],
  recap=["`<T>` : un type en paramètre, déduit à l'appel.",
         "`T extends …` pour utiliser quelque chose de T ; `K extends keyof T` pour un nom de champ.",
         "Dériver : `Omit` (création), `Partial` (modification), `Pick` (vue), `Record` (dictionnaire).",
         "`Resultat<T>` : succès ou erreur, typé."],
  example=F("outils.ts", "ts", r"""
export function grouperPar<T, K extends keyof T>(xs: T[], cle: K): Record<string, T[]> {
  const groupes: Record<string, T[]> = {};
  for (const x of xs) {
    const k = String(x[cle]);
    (groupes[k] ??= []).push(x);
  }
  return groupes;
}

// grouperPar(produits, 'categorie')  → { livre: [...], jeu: [...] }
// grouperPar(produits, 'categrie')   → erreur : pas une clé de Produit
"""),
  notes=["`T` : n'importe quel type d'élément.", "`K` : seulement un nom de champ de T.", "Le résultat garde le type exact des éléments."],
  tds=[
    TD(1, "Des fonctions génériques",
       "Ces fonctions utilitaires sont écrites avec `any` : on perd les types à chaque appel. Réécris-les avec des **génériques**." + TS,
       ["`premier(xs)` et `dernier(xs)` : `T | undefined` selon le type des éléments",
        "`trouverParId(xs, id)` : seulement pour des éléments qui ont un `id: number`",
        "`grouperPar(xs, cle)` : `cle` doit être un nom de champ des éléments ; renvoie `Record<string, T[]>`",
        "Plus aucun `any` dans le fichier"],
       [F("outils.ts", "ts", r"""
export function premier(xs: any[]): any {
  return xs[0];
}

export function dernier(xs: any[]): any {
  return xs[xs.length - 1];
}

export function trouverParId(xs: any[], id: number): any {
  return xs.find((x) => x.id === id);
}

export function grouperPar(xs: any[], cle: string): Record<string, any[]> {
  const groupes: Record<string, any[]> = {};
  for (const x of xs) {
    const k = String(x[cle]);
    (groupes[k] ??= []).push(x);
  }
  return groupes;
}
""")],
       ["`export function premier<T>(xs: T[]): T | undefined`.",
        "`trouverParId<T extends { id: number }>(xs: T[], id: number): T | undefined`.",
        "`grouperPar<T, K extends keyof T>(xs: T[], cle: K): Record<string, T[]>`."],
       [F("outils.ts", "ts", r"""
export function premier<T>(xs: T[]): T | undefined {
  return xs[0];
}

export function dernier<T>(xs: T[]): T | undefined {
  return xs[xs.length - 1];
}

export function trouverParId<T extends { id: number }>(xs: T[], id: number): T | undefined {
  return xs.find((x) => x.id === id);
}

export function grouperPar<T, K extends keyof T>(xs: T[], cle: K): Record<string, T[]> {
  const groupes: Record<string, T[]> = {};
  for (const x of xs) {
    const k = String(x[cle]);
    (groupes[k] ??= []).push(x);
  }
  return groupes;
}
""")],
       ["Les types suivent les données", "Une faute de frappe dans un nom de champ est refusée"],
       run=TRUN("outils.ts", tests=r"""
assert.noTypeErrors('Aucune erreur de type');
assert(!/\bany\b/.test(source('outils.ts')), 'Plus aucun any');
const m = require('./outils');
assert.equal(m.premier([4, 5]), 4, 'premier');
assert.equal(m.dernier([4, 5]), 5, 'dernier');
assert.equal(m.dernier([]), undefined, 'dernier d\'une liste vide');
assert.equal(m.trouverParId([{ id: 1, n: 'a' }, { id: 2, n: 'b' }], 2).n, 'b', 'trouverParId');
assert.deepEqual(Object.keys(m.grouperPar([{ c: 'x' }, { c: 'y' }, { c: 'x' }], 'c')), ['x', 'y'], 'grouperPar');
""", typetests=r"""
import { premier, dernier, trouverParId, grouperPar } from './outils';
type Produit = { id: number; nom: string; categorie: string };
declare const produits: Produit[];
// ✓ premier sur des nombres donne number | undefined
const a: number | undefined = premier([1, 2]);
// ✗ premier sur des nombres ne donne pas une string
const b: string | undefined = premier([1, 2]);
// ✗ dernier peut renvoyer undefined
const c: Produit = dernier(produits);
// ✓ trouverParId garde le type Produit
const d: Produit | undefined = trouverParId(produits, 1);
// ✗ trouverParId refuse des éléments sans id
trouverParId([{ nom: 'x' }], 1);
// ✓ grouperPar par un champ existant
const e: Record<string, Produit[]> = grouperPar(produits, 'categorie');
// ✗ grouperPar par un champ qui n'existe pas
grouperPar(produits, 'categrie');
""")),
    TD(2, "Dériver les types avec Omit, Partial, Pick, Record",
       "Le type `Utilisateur` est fourni. Écris les types dérivés (sans recopier les champs) et les fonctions qui les utilisent." + TS,
       ["`NouvelUtilisateur` = `Utilisateur` sans `id` ni `creeLe` ; `ModifUtilisateur` = les champs de `NouvelUtilisateur`, tous optionnels ; `UtilisateurPublic` = seulement `id` et `nom`",
        "`creer(donnees: NouvelUtilisateur, id: number, maintenant: string): Utilisateur`",
        "`modifier(u: Utilisateur, modif: ModifUtilisateur): Utilisateur` (ne modifie pas `u`, en renvoie une copie)",
        "`parRole(liste)` : `Record<Role, UtilisateurPublic[]>` avec **toujours** les 3 rôles (tableaux vides si personne)"],
       [F("utilisateurs.ts", "ts", r"""
export type Role = 'admin' | 'membre' | 'invite';

export type Utilisateur = {
  id: number;
  nom: string;
  email: string;
  role: Role;
  creeLe: string;
};

// à toi : NouvelUtilisateur, ModifUtilisateur, UtilisateurPublic (sans recopier les champs)

export function creer(donnees, id: number, maintenant: string): Utilisateur {
  // à toi
}

export function modifier(u: Utilisateur, modif): Utilisateur {
  // à toi
}

export function parRole(liste: Utilisateur[]) {
  // à toi
}
""")],
       ["`export type NouvelUtilisateur = Omit<Utilisateur, 'id' | 'creeLe'>;`",
        "`modifier` : `return { ...u, ...modif };`",
        "`parRole` : pars de `{ admin: [], membre: [], invite: [] }` typé `Record<Role, UtilisateurPublic[]>`, puis `push({ id: u.id, nom: u.nom })`."],
       [F("utilisateurs.ts", "ts", r"""
export type Role = 'admin' | 'membre' | 'invite';

export type Utilisateur = {
  id: number;
  nom: string;
  email: string;
  role: Role;
  creeLe: string;
};

export type NouvelUtilisateur = Omit<Utilisateur, 'id' | 'creeLe'>;
export type ModifUtilisateur = Partial<NouvelUtilisateur>;
export type UtilisateurPublic = Pick<Utilisateur, 'id' | 'nom'>;

export function creer(donnees: NouvelUtilisateur, id: number, maintenant: string): Utilisateur {
  return { ...donnees, id, creeLe: maintenant };
}

export function modifier(u: Utilisateur, modif: ModifUtilisateur): Utilisateur {
  return { ...u, ...modif };
}

export function parRole(liste: Utilisateur[]): Record<Role, UtilisateurPublic[]> {
  const groupes: Record<Role, UtilisateurPublic[]> = { admin: [], membre: [], invite: [] };
  for (const u of liste) groupes[u.role].push({ id: u.id, nom: u.nom });
  return groupes;
}
""")],
       ["Aucun champ recopié", "Chaque type refuse ce qu'il doit refuser"],
       run=TRUN("utilisateurs.ts", tests=r"""
assert.noTypeErrors('Aucune erreur de type');
const src = source('utilisateurs.ts');
assert(/Omit\s*</.test(src) && /Partial\s*</.test(src) && /Pick\s*</.test(src) && /Record\s*</.test(src), 'Utilise Omit, Partial, Pick et Record');
assert((src.match(/email\s*:/g) || []).length === 1, 'Le champ email n\'est déclaré qu\'une fois (pas de copie)');
const m = require('./utilisateurs');
const u = m.creer({ nom: 'Ana', email: 'a@b.c', role: 'admin' }, 7, '2026-11-16');
assert.deepEqual(u, { nom: 'Ana', email: 'a@b.c', role: 'admin', id: 7, creeLe: '2026-11-16' }, 'creer');
const u2 = m.modifier(u, { role: 'membre' });
assert(u2.role === 'membre' && u.role === 'admin', 'modifier renvoie une copie et ne touche pas l\'original');
assert.deepEqual(m.parRole([u, u2]), { admin: [{ id: 7, nom: 'Ana' }], membre: [{ id: 7, nom: 'Ana' }], invite: [] }, 'parRole : les 3 rôles, vues publiques');
""", typetests=r"""
import { creer, modifier, parRole, type NouvelUtilisateur, type ModifUtilisateur, type UtilisateurPublic, type Utilisateur } from './utilisateurs';
declare const u: Utilisateur;
// ✓ un nouvel utilisateur sans id ni date
const a: NouvelUtilisateur = { nom: 'Ana', email: 'a@b.c', role: 'membre' };
// ✗ un nouvel utilisateur ne fournit pas d'id
const b: NouvelUtilisateur = { id: 1, nom: 'Ana', email: 'a@b.c', role: 'membre' };
// ✓ une modification partielle
const c: ModifUtilisateur = { email: 'nouveau@b.c' };
// ✗ une modification ne change pas l'id
const d: ModifUtilisateur = { id: 2 };
// ✗ la vue publique ne contient pas l'email
const e: UtilisateurPublic = { id: 1, nom: 'Ana', email: 'a@b.c' };
// ✓ parRole a toujours la clé invite
const f: UtilisateurPublic[] = parRole([u]).invite;
// ✗ parRole n'a pas de clé inconnue
const g = parRole([u]).superadmin;
""")),
    TD(3, "Un type générique : Resultat<T>",
       "Plutôt que de lever des exceptions pour les erreurs prévues, écris un type `Resultat<T>` (succès ou erreur) et quelques fonctions pour le manipuler." + TS,
       ["`type Resultat<T> = { ok: true; valeur: T } | { ok: false; erreur: string }` ; `succes(v)` et `echec(message)` pour en créer",
        "`transformer(r, f)` : applique `f` à la valeur si c'est un succès, sinon renvoie l'erreur telle quelle (le type suit : `Resultat<number>` + `f: number → string` = `Resultat<string>`)",
        "`essayer(f)` : exécute `f()` et renvoie un succès, ou un échec avec le message de l'exception",
        "`lireAge(texte)` : `Resultat<number>` ; erreurs `Âge manquant`, `Âge invalide` (pas un entier ≥ 0)"],
       [F("resultat.ts", "ts", r"""
// à toi : Resultat<T>, succes, echec, transformer, essayer, lireAge
""")],
       ["`export function succes<T>(valeur: T): Resultat<T> { return { ok: true, valeur }; }` ; `echec` renvoie `Resultat<never>` (compatible avec tous).",
        "`transformer<T, U>(r: Resultat<T>, f: (v: T) => U): Resultat<U>`.",
        "`essayer<T>(f: () => T): Resultat<T>` avec `try/catch` ; `e instanceof Error ? e.message : String(e)`."],
       [F("resultat.ts", "ts", r"""
export type Resultat<T> = { ok: true; valeur: T } | { ok: false; erreur: string };

export function succes<T>(valeur: T): Resultat<T> {
  return { ok: true, valeur };
}

export function echec(erreur: string): Resultat<never> {
  return { ok: false, erreur };
}

export function transformer<T, U>(r: Resultat<T>, f: (v: T) => U): Resultat<U> {
  return r.ok ? succes(f(r.valeur)) : r;
}

export function essayer<T>(f: () => T): Resultat<T> {
  try {
    return succes(f());
  } catch (e) {
    return echec(e instanceof Error ? e.message : String(e));
  }
}

export function lireAge(texte: string): Resultat<number> {
  const t = texte.trim();
  if (!t) return echec('Âge manquant');
  const n = Number(t);
  if (!Number.isInteger(n) || n < 0) return echec('Âge invalide');
  return succes(n);
}
""")],
       ["Les types suivent les transformations", "Pas d'exception pour les erreurs prévues"],
       run=TRUN("resultat.ts", tests=r"""
assert.noTypeErrors('Aucune erreur de type');
assert(!/\bany\b/.test(source('resultat.ts')), 'Pas de any');
const m = require('./resultat');
assert.deepEqual(m.succes(3), { ok: true, valeur: 3 }, 'succes');
assert.deepEqual(m.echec('x'), { ok: false, erreur: 'x' }, 'echec');
assert.deepEqual(m.transformer(m.succes(2), (n) => n * 10), { ok: true, valeur: 20 }, 'transformer un succès');
assert.deepEqual(m.transformer(m.echec('non'), (n) => n * 10), { ok: false, erreur: 'non' }, 'transformer un échec : inchangé');
assert.deepEqual(m.essayer(() => JSON.parse('{"a":1}')), { ok: true, valeur: { a: 1 } }, 'essayer : succès');
assert.equal(m.essayer(() => { throw new Error('boum'); }).erreur, 'boum', 'essayer : message de l\'exception');
assert.deepEqual(m.lireAge(' 42 '), { ok: true, valeur: 42 }, 'lireAge("42")');
assert.deepEqual(m.lireAge(''), { ok: false, erreur: 'Âge manquant' }, 'lireAge vide');
assert.deepEqual(m.lireAge('4.5'), { ok: false, erreur: 'Âge invalide' }, 'lireAge("4.5")');
assert.deepEqual(m.lireAge('-1'), { ok: false, erreur: 'Âge invalide' }, 'lireAge("-1")');
""", typetests=r"""
import { succes, echec, transformer, essayer, lireAge, type Resultat } from './resultat';
// ✓ transformer change le type de la valeur
const a: Resultat<string> = transformer(lireAge('3'), (n) => 'âge ' + n);
// ✗ … donc ce n'est plus un Resultat<number>
const b: Resultat<number> = transformer(lireAge('3'), (n) => 'âge ' + n);
// ✓ echec est compatible avec n'importe quel Resultat
const c: Resultat<Date> = echec('non');
declare const r: Resultat<number>;
// ✗ lire valeur sans vérifier ok
const d: number = r.valeur;
// ✓ après vérification, valeur est un number
if (r.ok) { const e: number = r.valeur; }
// ✓ essayer déduit le type renvoyé
const f: Resultat<boolean> = essayer(() => true);
// ✗ un succès sans valeur
const g: Resultat<number> = { ok: true };
""")),
  ])

# =========================================================================== 4. null et unknown
PRODUIT_GUARD = r"""
export type Produit = { id: number; nom: string; prix: number };
"""

nulls = DM("ts-null", "null, undefined et données inconnues", 30,
  "Gérer proprement l'absence de valeur (`null`, `undefined`, `?.`, `??`), éviter les raccourcis dangereux (`!`, `as`, `any`), et vérifier les données qui viennent de l'extérieur avec `unknown` et des gardes de type.",
  "« Cannot read properties of undefined » est l'erreur JavaScript la plus fréquente. En mode strict, TypeScript la signale avant l'exécution ; à condition de ne pas la faire taire avec `!` ou `as`.",
  ["Accepter qu'une valeur puisse manquer : `T | null`, `T | undefined`, champ `?`", "La traiter : `if`, `?.`, `??`, valeur par défaut",
   "Ne pas mentir au compilateur : pas de `!` ni de `as` pour faire taire une erreur", "Données extérieures (JSON, API, localStorage) : `unknown`, puis **vérifier** (garde de type `x is T`, ou zod)"],
  ["`find`, `querySelector`, `Map.get`, `localStorage.getItem` peuvent renvoyer `undefined`/`null` : le type le dit.",
   "`a?.b` donne `undefined` si `a` est absent ; `x ?? 'défaut'` remplace seulement `null`/`undefined` (pas `0` ni `''`, contrairement à `||`).",
   "`x!` et `x as T` disent « crois-moi » : si c'est faux, l'erreur arrive à l'exécution.",
   "`JSON.parse` et `res.json()` renvoient `any` : traite le résultat comme `unknown` et vérifie-le.",
   "Une garde de type `function estProduit(x: unknown): x is Produit` rétrécit le type après un `if`."],
  ["`!` partout pour faire taire `possibly undefined`.", "`const data = await res.json() as Produit[]` sans vérifier.", "`||` au lieu de `??` (perd les 0 et les chaînes vides)."],
  [Q("`produits.find(p => p.id === 3)` a le type…", ["Produit", "Produit | undefined", "Produit[]", "any"], 1, "find peut ne rien trouver."),
   Q("`stock ?? 10` quand stock vaut 0 :", ["10", "0", "undefined", "erreur"], 1, "?? ne remplace que null et undefined."),
   Q("La réponse d'une API, avant vérification, devrait être typée…", ["any", "unknown", "le type attendu avec as", "never"], 1, "unknown oblige à vérifier avant d'utiliser.")],
  prereq=[
    P("`strictNullChecks`", "Option (incluse dans `strict`) qui distingue `string` de `string | null` : on doit gérer l'absence."),
    P("Chaînage optionnel `?.`", "`u?.adresse?.ville` s'arrête et renvoie `undefined` au premier élément absent."),
    P("`??`", "Opérateur de valeur par défaut, seulement pour `null` et `undefined`."),
    P("Garde de type (type guard)", "Fonction qui renvoie un booléen et dit au compilateur le type vérifié : `(x: unknown): x is Produit`."),
  ],
  diagram=D(
    nodes=[
      N("j", 0, 1, "JSON / API", "any (non vérifié)", kind="db", color="muted"),
      N("u", 1, 1, "unknown", "on ne peut rien en faire", kind="note", color="warn"),
      N("g", 2, 1, "estProduit(x)", "garde de type", kind="box", color="accent"),
      N("p", 3, 0, "Produit", "utilisable", kind="pill", color="good"),
      N("r", 3, 2, "rejeté", "message ou ignoré", kind="pill", color="bad"),
    ],
    edges=[E("j", "u"), E("u", "g"), E("g", "p", "oui"), E("g", "r", "non")],
    caption="Les données extérieures passent par unknown et une vérification avant d'être utilisées."),
  lessons=[
    L("Gérer l'absence", r"""
Beaucoup de fonctions peuvent ne **rien** trouver. TypeScript le voit dans leur type de retour et t'oblige à gérer ce cas. Trois exemples dans le code ci-dessous :

- `tableau.find((x) => condition)` renvoie le premier élément qui respecte la condition… ou `undefined` s'il n'y en a aucun. Type : `Produit | undefined`.
- `localStorage.getItem('n')` lit une valeur gardée dans le navigateur ; elle renvoie un texte, ou `null` si la clé n'existe pas. Type : `string | null`.
- `u.adresse?.ville` : le `?.` lit `ville` seulement si `adresse` existe, sinon donne `undefined` au lieu de planter. Et `a ?? b` donne `b` quand `a` est `null` ou `undefined`.

```ts
const p = produits.find((x) => x.id === id);   // Produit | undefined
p.nom;                     // ✗ erreur : 'p' est peut-être 'undefined'

if (!p) return 'Introuvable';
p.nom;                     // ✓ ici p : Produit

const ville = u.adresse?.ville ?? 'Ville inconnue';   // ?. puis valeur par défaut
const n = Number(localStorage.getItem('n') ?? '0');   // getItem : string | null
```

`??` contre `||` :

| Valeur | `x \|\| 10` | `x ?? 10` |
|---|---|---|
| `undefined` / `null` | 10 | 10 |
| `0` | **10** (perdu !) | 0 |
| `''` | **10** | '' |

Utilise `??` pour une valeur par défaut, sauf si tu veux vraiment remplacer `0` et `''`.
"""),
    L("Ne pas mentir au compilateur : `!`, `as`, `any`", r"""
Trois façons de faire taire une erreur, trois façons de cacher un bug. Pour lire le deuxième exemple : `fetch(url)` envoie une requête et donne une réponse `res` ; `await res.json()` lit le corps de cette réponse et le transforme en objet JS, mais **sans aucune garantie** sur sa forme.

```ts
const p = produits.find((x) => x.id === id)!;      // « crois-moi, il existe »
const data = (await res.json()) as Produit[];      // « crois-moi, c'est des produits »
function lire(x: any) { return x.nom.toUpperCase(); }   // « ne vérifie rien »
```

Si c'est faux, TypeScript ne dit rien et l'erreur arrive **chez l'utilisateur**. À la place : gérer le cas (`if (!p)`), ou **vérifier** les données.

Cas où c'est acceptable : `as const` (figer des littéraux), un `!` sur quelque chose que tu viens de vérifier autrement et que TypeScript ne voit pas (rare), un test. Si tu en écris souvent, c'est un signal.
"""),
    L("Données extérieures : unknown et gardes de type", r"""
Ce qui vient de l'extérieur (API, `JSON.parse`, `localStorage`, `postMessage`) n'a **pas** de type garanti. Traite-le comme `unknown` et vérifie :

```ts
export function estProduit(x: unknown): x is Produit {
  return typeof x === 'object' && x !== null
    && typeof (x as Record<string, unknown>).id === 'number'
    && typeof (x as Record<string, unknown>).nom === 'string'
    && typeof (x as Record<string, unknown>).prix === 'number';
}

const brut: unknown = JSON.parse(texte);
if (Array.isArray(brut)) {
  const produits = brut.filter(estProduit);   // Produit[]
}
```

Le `x is Produit` dit au compilateur : « si cette fonction renvoie `true`, x est un Produit ». Ici le `as Record<string, unknown>` est acceptable : il ne fait que permettre de **lire** des champs pour les vérifier.

En vrai projet, on utilise souvent **zod** pour ça : `produitSchema.safeParse(brut)` fait la vérification et donne le type (`z.infer`). Le parcours Formulaires l'utilise.
"""),
  ],
  recap=["`find`, `get`, `querySelector`, `getItem` : le résultat peut manquer.",
         "`if`, `?.`, `??` ; `??` garde 0 et ''.",
         "Pas de `!`, `as`, `any` pour faire taire une erreur.",
         "Données extérieures : `unknown` + garde de type (`x is T`) ou zod."],
  example=F("ville.ts", "ts", r"""
type Utilisateur = { nom: string; adresse?: { ville?: string } };

export function ville(u: Utilisateur | null): string {
  return u?.adresse?.ville ?? 'Ville inconnue';
}

export function lireNombre(cle: string, defaut: number): number {
  const brut = localStorage.getItem(cle);          // string | null
  const n = brut === null ? NaN : Number(brut);
  return Number.isFinite(n) ? n : defaut;
}
"""),
  notes=["`?.` et `??` gèrent toutes les absences en une ligne.", "`getItem` peut renvoyer null : on le traite."],
  tds=[
    TD(1, "Enlever les `!` qui cachent des bugs",
       "Ce code compile grâce à des `!` et des `as`… et plante dès qu'une donnée manque. Supprime-les et gère vraiment les cas d'absence." + TS,
       ["Aucun `!` (non-null) ni `as` dans le fichier, et aucune erreur de type",
        "`nomDuProduit(produits, id)` : `Produit inconnu` si l'id n'existe pas",
        "`villeDe(u)` : la ville, ou `Ville inconnue` si l'utilisateur, l'adresse ou la ville manque",
        "`stockAffiche(p)` : le stock (même `0`), ou `Stock non communiqué` si absent ; `quantiteParDefaut(saisie)` : 1 si la saisie est `null`/`undefined` (mais `0` reste `0`)"],
       [F("absences.ts", "ts", r"""
export type Produit = { id: number; nom: string; stock?: number };
export type Utilisateur = { nom: string; adresse?: { ville?: string } };

export function nomDuProduit(produits: Produit[], id: number): string {
  return produits.find((p) => p.id === id)!.nom;
}

export function villeDe(u: Utilisateur | null): string {
  return u!.adresse!.ville as string;
}

export function stockAffiche(p: Produit): string {
  return String(p.stock || 'Stock non communiqué');
}

export function quantiteParDefaut(saisie: number | null | undefined): number {
  return saisie || 1;
}
""")],
       ["`const p = produits.find(…); return p ? p.nom : 'Produit inconnu';` (ou `p?.nom ?? 'Produit inconnu'`).",
        "`return u?.adresse?.ville ?? 'Ville inconnue';`",
        "`||` remplace aussi le 0 : utilise `??`, ou `p.stock === undefined ? … : …`."],
       [F("absences.ts", "ts", r"""
export type Produit = { id: number; nom: string; stock?: number };
export type Utilisateur = { nom: string; adresse?: { ville?: string } };

export function nomDuProduit(produits: Produit[], id: number): string {
  return produits.find((p) => p.id === id)?.nom ?? 'Produit inconnu';
}

export function villeDe(u: Utilisateur | null): string {
  return u?.adresse?.ville ?? 'Ville inconnue';
}

export function stockAffiche(p: Produit): string {
  return p.stock === undefined ? 'Stock non communiqué' : String(p.stock);
}

export function quantiteParDefaut(saisie: number | null | undefined): number {
  return saisie ?? 1;
}
""")],
       ["Plus de « Cannot read properties of undefined »", "Le 0 n'est plus perdu"],
       run=TRUN("absences.ts", tests=r"""
assert.noTypeErrors('Aucune erreur de type');
const src = source('absences.ts');
assert(!/[\w\)\]]!(?!=)/.test(src.replace(/!==?/g, '')), 'Aucun ! (non-null)');
assert(!/\bas\s+[A-Za-z]/.test(src), 'Aucun as');
const m = require('./absences');
const P = [{ id: 1, nom: 'Clavier', stock: 0 }, { id: 2, nom: 'Souris' }];
assert.equal(m.nomDuProduit(P, 1), 'Clavier', 'nomDuProduit trouvé');
assert.equal(m.nomDuProduit(P, 9), 'Produit inconnu', 'nomDuProduit absent : pas de plantage');
assert.equal(m.villeDe({ nom: 'Ana', adresse: { ville: 'Lyon' } }), 'Lyon', 'villeDe');
assert.equal(m.villeDe(null), 'Ville inconnue', 'villeDe(null)');
assert.equal(m.villeDe({ nom: 'Léo' }), 'Ville inconnue', 'villeDe sans adresse');
assert.equal(m.villeDe({ nom: 'Léo', adresse: {} }), 'Ville inconnue', 'villeDe sans ville');
assert.equal(m.stockAffiche(P[0]), '0', 'stock 0 : « 0 » (pas « non communiqué »)');
assert.equal(m.stockAffiche(P[1]), 'Stock non communiqué', 'stock absent');
assert.equal(m.quantiteParDefaut(0), 0, 'quantité 0 reste 0');
assert.equal(m.quantiteParDefaut(null), 1, 'quantité null → 1');
""")),
    TD(2, "Une garde de type pour du JSON",
       "Un fichier JSON de produits est importé depuis un tableur : certaines lignes sont incomplètes ou mal formées. Écris une **garde de type** et une fonction qui ne garde que les produits valides." + TS,
       ["`estProduit(x: unknown): x is Produit` : objet non null avec `id` (nombre entier), `nom` (chaîne non vide), `prix` (nombre ≥ 0)",
        "`lireProduits(json: string)` : `{ produits: Produit[]; rejets: number }` ; JSON illisible ou pas un tableau → `{ produits: [], rejets: 0 }`",
        "Pas de `any` ; le résultat de `JSON.parse` est rangé dans une variable `unknown`",
        "Après `if (estProduit(x))`, TypeScript connaît `x.prix`"],
       [F("import.ts", "ts", PRODUIT_GUARD + r"""
export function estProduit(x) {
  // à toi
}

export function lireProduits(json: string) {
  const brut = JSON.parse(json);
  return { produits: brut, rejets: 0 };
}
""")],
       ["`typeof x === 'object' && x !== null` d'abord ; ensuite lis les champs via `const o = x as Record<string, unknown>;`.",
        "`Number.isInteger(o.id)` ; `typeof o.nom === 'string' && o.nom.trim() !== ''`.",
        "`let brut: unknown; try { brut = JSON.parse(json); } catch { return { produits: [], rejets: 0 }; }`."],
       [F("import.ts", "ts", PRODUIT_GUARD + r"""
export function estProduit(x: unknown): x is Produit {
  if (typeof x !== 'object' || x === null) return false;
  const o = x as Record<string, unknown>;
  return Number.isInteger(o.id)
    && typeof o.nom === 'string' && o.nom.trim() !== ''
    && typeof o.prix === 'number' && o.prix >= 0;
}

export function lireProduits(json: string): { produits: Produit[]; rejets: number } {
  let brut: unknown;
  try {
    brut = JSON.parse(json);
  } catch {
    return { produits: [], rejets: 0 };
  }
  if (!Array.isArray(brut)) return { produits: [], rejets: 0 };
  const produits = brut.filter(estProduit);
  return { produits, rejets: brut.length - produits.length };
}
""")],
       ["Les lignes invalides sont écartées", "Le type est garanti après la vérification"],
       run=TRUN("import.ts", tests=r"""
assert.noTypeErrors('Aucune erreur de type');
assert(!/\bany\b/.test(source('import.ts')), 'Pas de any');
assert(/:\s*unknown/.test(source('import.ts')), 'Le JSON brut est rangé dans une variable unknown');
const { estProduit: e, lireProduits: l } = require('./import');
assert.equal(e({ id: 1, nom: 'Dune', prix: 10 }), true, 'produit valide');
assert.equal(e({ id: 1.5, nom: 'Dune', prix: 10 }), false, 'id non entier');
assert.equal(e({ id: 1, nom: '  ', prix: 10 }), false, 'nom vide');
assert.equal(e({ id: 1, nom: 'Dune', prix: '10' }), false, 'prix en chaîne');
assert.equal(e({ id: 1, nom: 'Dune', prix: -1 }), false, 'prix négatif');
assert.equal(e(null), false, 'null');
assert.equal(e('Dune'), false, 'une chaîne');
const r = l(JSON.stringify([{ id: 1, nom: 'Dune', prix: 10 }, { id: 2, nom: 'Uno' }, { id: 3, nom: 'Ubik', prix: 7 }, 42]));
assert.deepEqual(r, { produits: [{ id: 1, nom: 'Dune', prix: 10 }, { id: 3, nom: 'Ubik', prix: 7 }], rejets: 2 }, 'lireProduits : 2 valides, 2 rejets');
assert.deepEqual(l('{ pas du json'), { produits: [], rejets: 0 }, 'JSON illisible');
assert.deepEqual(l('{"id":1}'), { produits: [], rejets: 0 }, 'pas un tableau');
""", typetests=r"""
import { estProduit, lireProduits, type Produit } from './import';
declare const x: unknown;
// ✗ on ne peut pas lire x.prix sans vérifier
const a = x.prix;
// ✓ après la garde, x est un Produit
if (estProduit(x)) { const b: number = x.prix; }
// ✓ lireProduits renvoie des Produit
const c: Produit[] = lireProduits('[]').produits;
""")),
    TD(3, "Une réponse d'API qui ment",
       "Ce client d'API fait `as Utilisateur` sur la réponse. Le jour où l'API renvoie `age` en texte, l'erreur arrive bien plus loin, dans un calcul. Rends le client **sûr** : la réponse est vérifiée, et une réponse invalide donne une erreur claire tout de suite." + TS,
       ["`chargerUtilisateur(id)` : `GET /api/utilisateurs/<id>` ; renvoie une `Promise<Utilisateur>`",
        "Statut HTTP non OK → erreur `Utilisateur <id> introuvable` (404) ou `Erreur serveur (<statut>)`",
        "Réponse qui n'a pas la bonne forme (`id` nombre, `nom` chaîne, `age` nombre) → erreur `Réponse invalide pour l'utilisateur <id>`",
        "Pas de `as Utilisateur` ni de `any` : la réponse est `unknown`, vérifiée par une garde `estUtilisateur`"],
       [F("client.ts", "ts", r"""
export type Utilisateur = { id: number; nom: string; age: number };

export async function chargerUtilisateur(id: number): Promise<Utilisateur> {
  const res = await fetch('/api/utilisateurs/' + id);
  const data = await res.json();
  return data as Utilisateur;
}

export async function anneeDeNaissance(id: number, annee: number): Promise<number> {
  const u = await chargerUtilisateur(id);
  return annee - u.age;
}
""")],
       ["`const data: unknown = await res.json();` puis `if (!estUtilisateur(data)) throw new Error(…)`.",
        "Vérifie le statut **avant** de lire le JSON : `if (res.status === 404) throw …; if (!res.ok) throw …`.",
        "La garde : même principe que le niveau 2."],
       [F("client.ts", "ts", r"""
export type Utilisateur = { id: number; nom: string; age: number };

export function estUtilisateur(x: unknown): x is Utilisateur {
  if (typeof x !== 'object' || x === null) return false;
  const o = x as Record<string, unknown>;
  return typeof o.id === 'number' && typeof o.nom === 'string' && typeof o.age === 'number';
}

export async function chargerUtilisateur(id: number): Promise<Utilisateur> {
  const res = await fetch('/api/utilisateurs/' + id);
  if (res.status === 404) throw new Error(`Utilisateur ${id} introuvable`);
  if (!res.ok) throw new Error(`Erreur serveur (${res.status})`);
  const data: unknown = await res.json();
  if (!estUtilisateur(data)) throw new Error(`Réponse invalide pour l'utilisateur ${id}`);
  return data;
}

export async function anneeDeNaissance(id: number, annee: number): Promise<number> {
  const u = await chargerUtilisateur(id);
  return annee - u.age;
}
""")],
       ["L'erreur arrive à la frontière, pas dans un calcul", "Pas de as"],
       run=TRUN("client.ts", api=r"""
__api["GET /api/utilisateurs/1"] = () => ({ id: 1, nom: 'Ana', age: 30 });
__api["GET /api/utilisateurs/2"] = () => ({ id: 2, nom: 'Léo', age: '25' });
__api["GET /api/utilisateurs/3"] = () => [500, { title: 'Erreur' }];
""", tests=r"""
assert.noTypeErrors('Aucune erreur de type');
const src = source('client.ts');
assert(!/as\s+Utilisateur|\bany\b/.test(src), 'Pas de « as Utilisateur » ni de any');
const m = require('./client');
assert.deepEqual(await m.chargerUtilisateur(1), { id: 1, nom: 'Ana', age: 30 }, 'Réponse valide');
assert.equal(await m.anneeDeNaissance(1, 2026), 1996, 'anneeDeNaissance');
const err = async (p) => { try { await p; return ''; } catch (e) { return e.message; } };
assert.equal(await err(m.chargerUtilisateur(2)), 'Réponse invalide pour l\'utilisateur 2', 'age en texte : erreur claire tout de suite');
assert.equal(await err(m.anneeDeNaissance(2, 2026)), 'Réponse invalide pour l\'utilisateur 2', '… et pas un calcul faux plus loin');
assert.equal(await err(m.chargerUtilisateur(9)), 'Utilisateur 9 introuvable', '404');
assert.equal(await err(m.chargerUtilisateur(3)), 'Erreur serveur (500)', '500');
""")),
  ])

# =========================================================================== 5. React
BOUTON_START = r"""
export function Bouton({ variante, onClick, children, desactive }) {
  return (
    <button className={'btn btn-' + (variante ?? 'primaire')} onClick={onClick} disabled={desactive}>
      {children}
    </button>
  );
}

export function Carte({ titre, prix, enPromo, onAjouter }) {
  return (
    <div className="carte">
      <h3>{titre}</h3>
      <p className="prix">{prix.toFixed(2)} €{enPromo && ' (promo)'}</p>
      <Bouton onClick={() => onAjouter(titre)}>Ajouter</Bouton>
    </div>
  );
}

export default function App() {
  return <Carte titre="Clavier" prix={49.9} enPromo onAjouter={(t) => console.log('ajout', t)} />;
}
"""

BOUTON_OK = r"""
import type { ReactNode } from 'react';

export type BoutonProps = {
  variante?: 'primaire' | 'secondaire';
  onClick: () => void;
  children: ReactNode;
  desactive?: boolean;
};

export function Bouton({ variante = 'primaire', onClick, children, desactive = false }: BoutonProps) {
  return (
    <button className={'btn btn-' + variante} onClick={onClick} disabled={desactive}>
      {children}
    </button>
  );
}

export type CarteProps = {
  titre: string;
  prix: number;
  enPromo?: boolean;
  onAjouter: (titre: string) => void;
};

export function Carte({ titre, prix, enPromo = false, onAjouter }: CarteProps) {
  return (
    <div className="carte">
      <h3>{titre}</h3>
      <p className="prix">{prix.toFixed(2)} €{enPromo && ' (promo)'}</p>
      <Bouton onClick={() => onAjouter(titre)}>Ajouter</Bouton>
    </div>
  );
}

export default function App() {
  return <Carte titre="Clavier" prix={49.9} enPromo onAjouter={(t) => console.log('ajout', t)} />;
}
"""

react = DM("ts-react", "TypeScript avec React", 30,
  "Typer des composants React : props (dont `children` et les fonctions), événements, `useState` avec un type, `useRef`, et un hook personnalisé générique.",
  "C'est ce que tu écris tous les jours en entreprise avec React ou Next.js : des props bien typées documentent le composant et empêchent de l'utiliser de travers. **À faire après le parcours React** (et le début de Données & API) : ce module ne réexplique pas `useState`, `useEffect`, `useRef` ni les événements, il leur ajoute seulement des types.",
  ["Décrire les **props** avec un `type` (fonctions comprises)", "Typer les **événements** (`ChangeEvent<HTMLInputElement>`, `FormEvent<HTMLFormElement>`)",
   "Donner un type à **`useState`** quand la valeur de départ ne suffit pas (`null`, `[]`)", "Écrire un **hook générique** (`useFetch<T>`)"],
  ["`type Props = { titre: string; onAjouter: (id: number) => void; children: ReactNode }` puis `function Carte({ titre }: Props)`.",
   "Props optionnelles avec `?` et une valeur par défaut dans la déstructuration.",
   "`useState(null)` est un `null` pour toujours : écris `useState<Produit | null>(null)`.",
   "`useState([])` est un `never[]` : écris `useState<Produit[]>([])`.",
   "Un handler déclaré à part a besoin de son type d'événement ; en ligne (`onChange={(e) => …}`), il est déduit."],
  ["`props: any`.", "`useState(null)` puis `setProduit(p)` (erreur).", "Typer `e` en `any` dans les handlers."],
  [Q("`const [p, setP] = useState(null)` puis `setP(produit)` :", ["ça marche", "erreur : Produit n'est pas assignable à null", "p devient any", "ça plante"], 1, "Il faut useState<Produit | null>(null)."),
   Q("Le type de `children` :", ["string", "ReactNode", "JSX.Element[]", "any"], 1, "ReactNode accepte texte, éléments, listes, null…"),
   Q("Un handler `function changer(e)` passé à `onChange` d'un input :", ["e: Event", "e: React.ChangeEvent<HTMLInputElement>", "e: any", "pas besoin de type"], 1, "Déclaré à part, il n'est pas déduit.")],
  prereq=[
    P("`ReactNode`", "Tout ce que React sait afficher : texte, nombre, élément, tableau, `null`, `undefined`…"),
    P("`React.ChangeEvent<T>`", "Le type de l'événement `onChange` sur l'élément T (`HTMLInputElement`, `HTMLSelectElement`…)."),
    P("Générique de `useState`", "`useState<T>(initial)` : indique le type de la valeur quand le départ ne suffit pas à le déduire."),
    P("Hook personnalisé", "Une fonction `useXxx` qui utilise d'autres hooks ; elle peut être générique."),
  ],
  diagram=D(
    nodes=[
      N("p", 0, 1, "type Props", "titre, prix, onAjouter", kind="doc", color="accent"),
      N("c", 1, 1, "function Carte", "(props: Props)", kind="file", color="good"),
      N("s", 2, 0, "useState<T | null>", "state typé", kind="pill", color="warn"),
      N("e", 2, 2, "ChangeEvent<…>", "événement typé", kind="pill", color="warn"),
      N("u", 3, 1, "<Carte titre=… />", "mauvais usage = erreur", kind="note", color="bad"),
    ],
    edges=[E("p", "c"), E("c", "s"), E("c", "e"), E("c", "u", dashed=True)],
    caption="Les props typées protègent chaque utilisation du composant ; state et événements typés protègent l'intérieur."),
  lessons=[
    L("Typer les props", r"""
Pour typer les **props** d'un composant, on décrit leur forme dans un `type` (une prop finie par `?` est optionnelle ; une fonction s'écrit `(param: type) => typeRetour` ; `ReactNode` est « tout ce que React sait afficher »), puis on l'indique après la déstructuration des props : `function Carte({ titre, prix }: CarteProps)`. `enPromo = false` donne une valeur par défaut à une prop optionnelle.

```tsx
import type { ReactNode } from 'react';

type CarteProps = {
  titre: string;
  prix: number;
  enPromo?: boolean;                       // optionnelle
  onAjouter: (titre: string) => void;      // une fonction : ses paramètres et son retour
  children?: ReactNode;                    // ce qu'on met entre <Carte> et </Carte>
};

export function Carte({ titre, prix, enPromo = false, onAjouter, children }: CarteProps) {
  return <div>{titre} : {prix} €{enPromo && ' (promo)'}{children}<button onClick={() => onAjouter(titre)}>+</button></div>;
}

<Carte titre="Clavier" prix={49.9} onAjouter={ajouter} />      // ✓
<Carte titre="Clavier" prix="49.9" onAjouter={ajouter} />      // ✗ prix doit être un number
<Carte titre="Clavier" prix={49.9} />                          // ✗ onAjouter manquant
```

Pour un composant qui « enrichit » un élément HTML, on peut reprendre toutes ses props : `type Props = React.ComponentProps<'button'> & { variante?: 'primaire' | 'secondaire' }`.
"""),
    L("State, événements, refs", r"""
Trois choses à typer. **`useState<Type>(depart)`** : les chevrons donnent le type de la valeur quand le départ ne suffit pas (`null`, `[]`). **Les événements** : un handler écrit à part reçoit `e`, dont le type dépend de l'élément (`React.ChangeEvent<HTMLInputElement>` pour un input) ; `e.target.value` est le texte tapé, `e.preventDefault()` empêche le navigateur de recharger la page à l'envoi d'un formulaire. **`useRef<HTMLInputElement>(null)`** : une référence vers un élément du DOM, disponible dans `champ.current` (qui peut être `null`, d'où le `?.`).

```tsx
const [produit, setProduit] = useState<Produit | null>(null);   // null au départ, Produit ensuite
const [liste, setListe] = useState<Produit[]>([]);              // [] seul serait never[]
const [filtre, setFiltre] = useState<'tous' | 'promo'>('tous'); // un choix limité
const [n, setN] = useState(0);                                  // déduit : number

function changer(e: React.ChangeEvent<HTMLInputElement>) {      // handler déclaré à part : on type e
  setRecherche(e.target.value);
}
function envoyer(e: React.FormEvent<HTMLFormElement>) {
  e.preventDefault();
}
<input onChange={(e) => setRecherche(e.target.value)} />       // en ligne : e est déduit

const champ = useRef<HTMLInputElement>(null);                  // champ.current : HTMLInputElement | null
champ.current?.focus();
```

| Événement | Type |
|---|---|
| `onChange` d'un input | `React.ChangeEvent<HTMLInputElement>` |
| `onChange` d'un select | `React.ChangeEvent<HTMLSelectElement>` |
| `onSubmit` d'un form | `React.FormEvent<HTMLFormElement>` |
| `onClick` | `React.MouseEvent<HTMLButtonElement>` |
| `onKeyDown` | `React.KeyboardEvent<HTMLInputElement>` |

Astuce : survole `onChange` dans VS Code, il te donne le type exact.
"""),
    L("Un hook générique", r"""
On écrit un **hook générique** `useFetch<T>` : il charge une URL et renvoie l'état du chargement, avec le type `T` des données fourni à l'appel. Il réutilise trois choses déjà vues : une **union discriminée** pour l'état (chargement / erreur / succès), `useState`, et `useEffect` qui lance `fetch(url)` (envoie la requête), vérifie `r.ok` (vrai pour un statut 2xx) et lit le JSON avec `r.json()`. La variable `actif` évite de mettre à jour l'état si le composant a disparu entre-temps.

```tsx
type EtatFetch<T> =
  | { statut: 'chargement' }
  | { statut: 'erreur'; message: string }
  | { statut: 'succes'; donnees: T };

export function useFetch<T>(url: string): EtatFetch<T> {
  const [etat, setEtat] = useState<EtatFetch<T>>({ statut: 'chargement' });
  useEffect(() => {
    let actif = true;
    fetch(url)
      .then((r) => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then((d: T) => actif && setEtat({ statut: 'succes', donnees: d }))
      .catch((e: Error) => actif && setEtat({ statut: 'erreur', message: e.message }));
    return () => { actif = false; };
  }, [url]);
  return etat;
}

const etat = useFetch<Produit[]>('/api/produits');
if (etat.statut === 'succes') etat.donnees.map((p) => p.nom);   // Produit[]
```

Le `T` est fourni à l'appel ; l'union discriminée du module 2 garantit qu'on ne lit `donnees` qu'en cas de succès. (`d: T` fait confiance à l'API : pour plus de sûreté, ajoute une vérification comme au module 4.)
"""),
  ],
  recap=["`type Props` + `function C({ … }: Props)` ; `ReactNode` pour children ; les fonctions avec leurs paramètres.",
         "`useState<T | null>(null)`, `useState<T[]>([])`.",
         "Handler à part : `React.ChangeEvent<HTMLInputElement>`, `React.FormEvent<HTMLFormElement>`.",
         "`useRef<HTMLInputElement>(null)` ; hooks génériques `useFetch<T>`."],
  example=F("Carte.tsx", "tsx", r"""
import type { ReactNode } from 'react';

type CarteProps = {
  titre: string;
  prix: number;
  onAjouter: (titre: string) => void;
  children?: ReactNode;
};

export function Carte({ titre, prix, onAjouter, children }: CarteProps) {
  return (
    <div>
      <h3>{titre}</h3>
      <p>{prix.toFixed(2)} €</p>
      {children}
      <button onClick={() => onAjouter(titre)}>Ajouter</button>
    </div>
  );
}
"""),
  notes=["Le type des props documente le composant.", "Un mauvais usage est refusé à la compilation."],
  tds=[
    TD(1, "Typer les props de deux composants",
       "Ces composants viennent d'un fichier `.jsx` renommé en `.tsx` : leurs props n'ont aucun type. Écris les types, avec des valeurs par défaut pour les props optionnelles." + TSX,
       ["Exporte `BoutonProps` : `variante` optionnelle (`'primaire'` ou `'secondaire'`, `'primaire'` par défaut), `onClick` (sans paramètre), `children`, `desactive` optionnel (`false` par défaut)",
        "Exporte `CarteProps` : `titre`, `prix` (nombre), `enPromo` optionnel, `onAjouter(titre)`",
        "Plus aucune erreur de type, pas de `any`",
        "Les mauvaises utilisations des composants sont refusées"],
       [F("Composants.tsx", "tsx", BOUTON_START)],
       ["`import type { ReactNode } from 'react';` pour `children: ReactNode`.",
        "`export function Bouton({ variante = 'primaire', onClick, children, desactive = false }: BoutonProps)`.",
        "`onAjouter: (titre: string) => void`."],
       [F("Composants.tsx", "tsx", BOUTON_OK)],
       ["Les props documentent les composants", "Une variante inconnue est refusée"],
       run=TRUN("Composants.tsx", kind="react", tests=r"""
assert.noTypeErrors('Aucune erreur de type');
assert(!/\bany\b/.test(source('Composants.tsx')), 'Pas de any');
assert.includes(text(), 'Clavier', 'La carte s\'affiche');
assert.includes($('.prix').textContent, '49.90 € (promo)', 'Prix et promo');
assert($('button.btn-primaire'), 'Variante par défaut : primaire');
""", typetests=r"""
import { Bouton, Carte, type BoutonProps } from './Composants';
// ✓ un bouton minimal
const a = <Bouton onClick={() => {}}>OK</Bouton>;
// ✗ une variante inconnue
const b = <Bouton variante="danger" onClick={() => {}}>OK</Bouton>;
// ✗ un bouton sans onClick
const c = <Bouton>OK</Bouton>;
// ✓ une carte sans promo
const d = <Carte titre="Souris" prix={20} onAjouter={(t) => t.toUpperCase()} />;
// ✗ un prix en chaîne
const e = <Carte titre="Souris" prix="20" onAjouter={() => {}} />;
// ✗ onAjouter reçoit une string, pas un number
const f = <Carte titre="Souris" prix={20} onAjouter={(t: number) => {}} />;
// ✓ BoutonProps est exporté
const g: BoutonProps['variante'] = 'secondaire';
""")),
    TD(2, "State et événements typés",
       "Ce composant de recherche a 4 erreurs de type. Corrige-les **en typant** (pas avec `any`) : le state qui commence à `null`, la liste qui commence vide, les handlers déclarés à part." + TSX,
       ["`selection` commence à `null` puis reçoit un `Produit` : type-le",
        "`resultats` commence à `[]` : type-le",
        "`changer` et `envoyer` sont déclarés à part : type leur événement",
        "Aucune erreur de type, pas de `any` ; le composant marche (chercher, cliquer un résultat, « Sélection : … »)"],
       [F("Recherche.tsx", "tsx", r"""
import { useState } from 'react';

type Produit = { id: number; nom: string; prix: number };

const CATALOGUE: Produit[] = [
  { id: 1, nom: 'Clavier mécanique', prix: 89 },
  { id: 2, nom: 'Souris', prix: 29 },
  { id: 3, nom: 'Tapis de souris', prix: 12 },
];

export default function Recherche() {
  const [terme, setTerme] = useState('');
  const [resultats, setResultats] = useState([]);
  const [selection, setSelection] = useState(null);

  function changer(e) {
    setTerme(e.target.value);
  }

  function envoyer(e) {
    e.preventDefault();
    setResultats(CATALOGUE.filter((p) => p.nom.toLowerCase().includes(terme.toLowerCase())));
  }

  return (
    <form onSubmit={envoyer}>
      <input aria-label="Recherche" value={terme} onChange={changer} />
      <button type="submit">Chercher</button>
      <ul>
        {resultats.map((p) => (
          <li key={p.id}><button type="button" onClick={() => setSelection(p)}>{p.nom}</button></li>
        ))}
      </ul>
      {selection && <p id="selection">Sélection : {selection.nom} ({selection.prix} €)</p>}
    </form>
  );
}
""")],
       ["`useState<Produit[]>([])` et `useState<Produit | null>(null)`.",
        "`function changer(e: React.ChangeEvent<HTMLInputElement>)` ; il faut `import type React from 'react'` ou `import { type ChangeEvent } from 'react'`.",
        "`function envoyer(e: React.FormEvent<HTMLFormElement>)`."],
       [F("Recherche.tsx", "tsx", r"""
import { useState, type ChangeEvent, type FormEvent } from 'react';

type Produit = { id: number; nom: string; prix: number };

const CATALOGUE: Produit[] = [
  { id: 1, nom: 'Clavier mécanique', prix: 89 },
  { id: 2, nom: 'Souris', prix: 29 },
  { id: 3, nom: 'Tapis de souris', prix: 12 },
];

export default function Recherche() {
  const [terme, setTerme] = useState('');
  const [resultats, setResultats] = useState<Produit[]>([]);
  const [selection, setSelection] = useState<Produit | null>(null);

  function changer(e: ChangeEvent<HTMLInputElement>) {
    setTerme(e.target.value);
  }

  function envoyer(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setResultats(CATALOGUE.filter((p) => p.nom.toLowerCase().includes(terme.toLowerCase())));
  }

  return (
    <form onSubmit={envoyer}>
      <input aria-label="Recherche" value={terme} onChange={changer} />
      <button type="submit">Chercher</button>
      <ul>
        {resultats.map((p) => (
          <li key={p.id}><button type="button" onClick={() => setSelection(p)}>{p.nom}</button></li>
        ))}
      </ul>
      {selection && <p id="selection">Sélection : {selection.nom} ({selection.prix} €)</p>}
    </form>
  );
}
""")],
       ["Le state a le bon type dès le départ", "Les handlers sont typés"],
       run=TRUN("Recherche.tsx", kind="react", tests=r"""
assert.noTypeErrors('Aucune erreur de type');
assert(!/\bany\b/.test(source('Recherche.tsx')), 'Pas de any');
await type('[aria-label=Recherche]', 'souris');
await submit('form');
assert.equal($$('li').length, 2, 'Recherche « souris » : 2 résultats');
await click($$('li button')[1]);
assert.equal($('#selection').textContent, 'Sélection : Tapis de souris (12 €)', 'Sélection affichée');
""")),
    TD(3, "Un hook générique useFetch<T>",
       "Écris un hook `useFetch<T>(url)` réutilisable, typé par une union discriminée, et utilise-le dans une liste de produits." + TSX,
       ["`useFetch.ts` exporte `type EtatFetch<T>` (`chargement`, `erreur` avec `message`, `succes` avec `donnees: T`) et `useFetch<T>(url: string): EtatFetch<T>`",
        "Statut HTTP non OK → `{ statut: 'erreur', message: 'HTTP 500' }` ; une réponse arrivée après un changement d'URL ou un démontage est ignorée",
        "`Produits.tsx` appelle `useFetch<Produit[]>('/api/produits')` et affiche `Chargement…`, `Erreur : …` ou la liste (`<li>Nom : prix €</li>`)",
        "Pas de `any`"],
       [F("useFetch.ts", "ts", r"""
import { useEffect, useState } from 'react';

// à toi : EtatFetch<T> et useFetch<T>(url)
export function useFetch(url) {
  return { statut: 'chargement' };
}
"""), F("Produits.tsx", "tsx", r"""
import { useFetch } from './useFetch';

type Produit = { id: number; nom: string; prix: number };

export default function Produits() {
  const etat = useFetch('/api/produits');
  // à toi : afficher selon etat.statut
  return <p>Chargement…</p>;
}
""")],
       ["`const [etat, setEtat] = useState<EtatFetch<T>>({ statut: 'chargement' });`",
        "Dans l'effet : `let actif = true; … return () => { actif = false; };` et `[url]` en dépendance.",
        "`.then((d: T) => { if (actif) setEtat({ statut: 'succes', donnees: d }); })`."],
       [F("useFetch.ts", "ts", r"""
import { useEffect, useState } from 'react';

export type EtatFetch<T> =
  | { statut: 'chargement' }
  | { statut: 'erreur'; message: string }
  | { statut: 'succes'; donnees: T };

export function useFetch<T>(url: string): EtatFetch<T> {
  const [etat, setEtat] = useState<EtatFetch<T>>({ statut: 'chargement' });

  useEffect(() => {
    let actif = true;
    setEtat({ statut: 'chargement' });
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then((d: T) => {
        if (actif) setEtat({ statut: 'succes', donnees: d });
      })
      .catch((e: unknown) => {
        if (actif) setEtat({ statut: 'erreur', message: e instanceof Error ? e.message : String(e) });
      });
    return () => {
      actif = false;
    };
  }, [url]);

  return etat;
}
"""), F("Produits.tsx", "tsx", r"""
import { useFetch } from './useFetch';

type Produit = { id: number; nom: string; prix: number };

export default function Produits() {
  const etat = useFetch<Produit[]>('/api/produits');

  if (etat.statut === 'chargement') return <p>Chargement…</p>;
  if (etat.statut === 'erreur') return <p role="alert">Erreur : {etat.message}</p>;
  return (
    <ul>
      {etat.donnees.map((p) => <li key={p.id}>{p.nom} : {p.prix} €</li>)}
    </ul>
  );
}
""")],
       ["Le hook marche pour n'importe quel type", "Impossible de lire les données avant le succès"],
       run=TRUN("Produits.tsx", kind="react", api=r"""
__api["GET /api/produits"] = async () => { await new Promise((r) => setTimeout(r, 500)); return [{ id: 1, nom: 'Clavier', prix: 89 }, { id: 2, nom: 'Souris', prix: 29 }]; };
""", tests=r"""
assert.noTypeErrors('Aucune erreur de type');
assert(!/\bany\b/.test(source('useFetch.ts') + source('Produits.tsx')), 'Pas de any');
assert.includes(text(), 'Chargement', 'Chargement… au départ');
await waitFor(() => $$('li').length === 2, 3000);
assert.equal($$('li')[0].textContent, 'Clavier : 89 €', 'Liste affichée');
""", typetests=r"""
import { useFetch, type EtatFetch } from './useFetch';
type Produit = { id: number; nom: string };
declare const etat: EtatFetch<Produit[]>;
// ✗ lire donnees sans vérifier le statut
const a = etat.donnees;
// ✓ après vérification, donnees est un Produit[]
if (etat.statut === 'succes') { const b: Produit[] = etat.donnees; }
// ✓ le hook garde le type demandé
function Test() { const e = useFetch<number>('/x'); if (e.statut === 'succes') { const n: number = e.donnees; } return null; }
// ✗ … et refuse un autre type
function Test2() { const e = useFetch<number>('/x'); if (e.statut === 'succes') { const s: string = e.donnees; } return null; }
// ✗ un état de succès sans données
const c: EtatFetch<number> = { statut: 'succes' };
""")),
  ])

# =========================================================================== 6. Lire les erreurs
erreurs = DM("ts-erreurs", "Lire et corriger les erreurs TypeScript", 25,
  "Lire n'importe quel message d'erreur TypeScript, reconnaître les plus fréquents, et les corriger à la source au lieu de les faire taire.",
  "Un message TypeScript fait parfois 5 lignes et fait peur. Avec une méthode de lecture et les 10 erreurs les plus fréquentes en tête, on corrige vite, et on apprend à chaque fois.",
  ["Repérer le **fichier:ligne:colonne** et le **code** (TS2322…)", "Lire le message **de bas en haut** quand il est imbriqué",
   "Se demander : le **type** est faux, ou la **valeur** est fausse ?", "Corriger à la source ; `as`, `!`, `any`, `@ts-ignore` en tout dernier recours"],
  ["Le code (TSxxxx) se cherche sur Internet : chaque code correspond à une famille d'erreurs.",
   "Les messages imbriqués expliquent pas à pas pourquoi deux types ne correspondent pas ; la dernière ligne est la plus précise.",
   "Souvent, l'erreur signale un **vrai bug** (argument oublié, propriété mal écrite, cas null oublié).",
   "Parfois, c'est le **type** qui est trop strict ou trop large : on corrige le type, pas l'appel.",
   "Un type trop permissif (`string` partout) laisse passer des bugs : le resserrer (unions, objets) rend les erreurs visibles."],
  ["`// @ts-ignore` pour avancer.", "Lire seulement la première ligne d'un message imbriqué.", "Changer le type pour qu'il accepte la valeur fausse."],
  [Q("TS2339 « La propriété 'nmo' n'existe pas sur le type 'Utilisateur' » :", ["il faut ajouter nmo au type", "faute de frappe : nom", "il faut un as", "il faut un any"], 1, "Le type est juste, le code est faux."),
   Q("TS18048 « 'p' est peut-être 'undefined' » :", ["ajouter !", "gérer le cas où p est absent", "ignorer", "mettre any"], 1, "C'est exactement le bug « Cannot read properties of undefined »."),
   Q("`envoyer(destinataire: string, sujet: string)` est souvent appelé dans le mauvais ordre. La meilleure correction :", ["un commentaire", "un seul paramètre objet { destinataire, sujet }", "deux fonctions", "any"], 1, "Les noms remplacent l'ordre : impossible d'inverser.")],
  prereq=[
    P("Message imbriqué", "Une erreur dont l'explication tient sur plusieurs lignes indentées, de la plus générale à la plus précise."),
    P("Type trop permissif", "Un type qui accepte des valeurs fausses (`string` pour un statut qui n'a que 3 valeurs possibles)."),
    P("Type « marqué » (branded)", "Un type comme `string & { __marque: 'UserId' }` qui empêche de confondre deux identifiants de même forme."),
  ],
  diagram=D(
    nodes=[
      N("e", 0, 1, "Erreur TSxxxx", "fichier:ligne", kind="note", color="bad"),
      N("l", 1, 1, "Lire de bas en haut", "la ligne la plus précise", kind="box", color="warn"),
      N("v", 2, 0, "La valeur est fausse", "→ corriger le code", kind="pill", color="good"),
      N("t", 2, 2, "Le type est faux", "→ corriger le type", kind="pill", color="good"),
      N("x", 3, 1, "as, !, any, @ts-ignore", "en tout dernier recours", kind="pill", color="muted"),
    ],
    edges=[E("e", "l"), E("l", "v"), E("l", "t"), E("v", "x", dashed=True)],
    caption="Lire l'erreur, décider si c'est la valeur ou le type qui est faux, corriger à la source."),
  lessons=[
    L("Lire un message, même long", r"""
Les erreurs TypeScript sur des objets imbriqués font plusieurs lignes, chacune un peu plus en retrait que la précédente. Chaque ligne précise la précédente : la première dit où est le problème (fichier, ligne, colonne, code d'erreur `TS2322`), la dernière dit exactement ce qui manque. En voici une typique.

```
commande.ts:14:9  TS2322
L'objet n'est pas assignable au type 'Commande'.
  Les types de la propriété 'lignes' sont incompatibles.
    Le type '{ produit: string; qte: number; }[]' n'est pas assignable au type 'Ligne[]'.
      La propriété 'quantite' est absente du type '{ produit: string; qte: number; }'.
```

Lis **de bas en haut** : la dernière ligne dit la cause précise (`quantite` manque : on a écrit `qte`), les lignes au-dessus disent où elle se trouve (dans `lignes`, dans la `Commande`).

Puis pose la question : **la valeur est fausse, ou le type est faux ?**
- `qte` au lieu de `quantite` → la valeur (le code) est fausse : on corrige le code.
- Le champ `remise` est obligatoire dans le type alors qu'il n'existe pas toujours → le type est faux : on le rend optionnel.
"""),
    L("Les erreurs les plus fréquentes", r"""
| Code | Message (résumé) | Correction habituelle |
|---|---|---|
| TS2322 | Impossible d'assigner le type A au type B | convertir la valeur (`Number(…)`), corriger le champ, ou ajuster le type |
| TS2345 | Argument de type A non attribuable au paramètre B | même chose, à l'appel d'une fonction |
| TS2339 | La propriété X n'existe pas sur le type Y | champ manquant dans le type, ou union non rétrécie |
| TS2551 | La propriété X n'existe pas… Est-ce qu'il ne s'agit pas plutôt de Y ? | faute de frappe : TypeScript propose le bon nom |
| TS2741 / TS2739 | Propriété(s) absente(s) | compléter l'objet, ou rendre le champ optionnel |
| TS18048 / TS2532 | X est peut-être undefined | `if`, `?.`, `??` (module 4) |
| TS18047 | X est peut-être null | idem |
| TS7006 | Paramètre avec un type any implicite | annoter le paramètre |
| TS2554 | N arguments attendus, M reçus | argument oublié ou en trop |
| TS2367 | Cette comparaison ne sera jamais vraie (pas de chevauchement) | faute dans une valeur littérale (`'actif'` vs `'active'`) |
| TS2307 | Module introuvable | chemin d'import, extension, paquet non installé |
| TS2578 | Directive @ts-expect-error inutilisée | il n'y a plus d'erreur : supprime la directive |
"""),
    L("Resserrer les types pour faire apparaître les bugs", r"""
Un code peut compiler **et** être faux parce que ses types sont trop larges :

```ts
function envoyerEmail(destinataire: string, sujet: string, corps: string) {}
envoyerEmail('Bienvenue !', 'ana@exemple.fr', '…');     // inversés : aucun problème pour TypeScript

function changerStatut(id: string, statut: string) {}
changerStatut(commande.id, 'livree');                   // 'livrée' ou 'livree' ? TypeScript s'en moque
```

Trois techniques :

1. **Un paramètre objet** : `envoyerEmail({ a, sujet, corps })` → les noms remplacent l'ordre.
2. **Des unions de littéraux** : `type Statut = 'en-attente' | 'payee' | 'livree'` → une faute de frappe devient une erreur.
3. **Des types marqués** pour les identifiants : `type CommandeId = string & { readonly __marque: 'CommandeId' }` → impossible de passer un `ClientId` à la place d'un `CommandeId`, même si ce sont deux chaînes.

C'est le meilleur usage de TypeScript : non pas « faire taire le compilateur », mais **lui donner assez d'informations pour qu'il trouve tes bugs**.
"""),
  ],
  recap=["fichier:ligne, code TSxxxx, message lu de bas en haut.",
         "La valeur est fausse → corriger le code ; le type est faux → corriger le type.",
         "Les 10 codes fréquents : 2322, 2345, 2339, 2741, 18048, 7006, 2554, 2367, 2307, 2578.",
         "Resserrer les types (objet en paramètre, unions, types marqués) pour faire apparaître les bugs."],
  example=F("statut.ts", "ts", r"""
export type Statut = 'en-attente' | 'payee' | 'livree';

export function libelleStatut(s: Statut): string {
  return { 'en-attente': 'En attente', payee: 'Payée', livree: 'Livrée' }[s];
}

// libelleStatut('livrée');   ← TS2345 : '"livrée"' n'est pas attribuable au paramètre de type 'Statut'
"""),
  notes=["Une union de littéraux au lieu de `string`.", "Une faute de frappe devient une erreur de compilation."],
  tds=[
    TD(1, "Six erreurs, six codes différents",
       "Ce fichier contient six erreurs de type de codes différents (lance-le et regarde la sortie : TS18048, TS2551, TS2322, TS2741, TS2554…). Corrige chacune **à la source**." + TS,
       ["Aucune erreur de type à la fin",
        "Interdit : `any`, `as`, `!` (non-null), `@ts-ignore`, `@ts-expect-error`",
        "Les tests de comportement passent (les corrections doivent être les bonnes, pas seulement compiler)",
        "Pour chaque erreur, demande-toi : la valeur est fausse, ou le type ?"],
       [F("commande.ts", "ts", r"""
export type Ligne = { produit: string; prix: number; quantite: number };
export type Commande = { id: number; client: string; lignes: Ligne[]; remise?: number };

export function totalLigne(l: Ligne): number {
  return l.prix * l.quantite;
}

export function total(c: Commande): number {
  const brut = c.lignes.reduce((t, l) => t + totalLigne(l), 0);
  return brut - brut * c.remise;
}

export function libelle(c: Commande): string {
  return 'Commande ' + c.id + ' de ' + c.cliente;
}

export function premiereLigne(c: Commande): string {
  const l = c.lignes[0] ?? undefined;
  const premiere: Ligne | undefined = l;
  return premiere.produit;
}

export function creer(id: number, client: string): Commande {
  const c: Commande = { id: String(id), client, lignes: [] };
  return c;
}

export function ajouter(c: Commande, produit: string, prix: number, quantite: number): Commande {
  return { ...c, lignes: [...c.lignes, { produit, prix }] };
}

export const exemple = ajouter(creer(1, 'Ana'), 'Clavier', 50);
""")],
       ["`c.remise` peut manquer : `c.remise ?? 0`.",
        "`c.cliente` → `c.client` ; `String(id)` → `id` ; la ligne ajoutée oublie `quantite`.",
        "`premiereLigne` : si pas de ligne, renvoie `''`. `exemple` : il manque la quantité (1)."],
       [F("commande.ts", "ts", r"""
export type Ligne = { produit: string; prix: number; quantite: number };
export type Commande = { id: number; client: string; lignes: Ligne[]; remise?: number };

export function totalLigne(l: Ligne): number {
  return l.prix * l.quantite;
}

export function total(c: Commande): number {
  const brut = c.lignes.reduce((t, l) => t + totalLigne(l), 0);
  return brut - brut * (c.remise ?? 0);
}

export function libelle(c: Commande): string {
  return 'Commande ' + c.id + ' de ' + c.client;
}

export function premiereLigne(c: Commande): string {
  const premiere: Ligne | undefined = c.lignes[0];
  return premiere ? premiere.produit : '';
}

export function creer(id: number, client: string): Commande {
  const c: Commande = { id, client, lignes: [] };
  return c;
}

export function ajouter(c: Commande, produit: string, prix: number, quantite: number): Commande {
  return { ...c, lignes: [...c.lignes, { produit, prix, quantite }] };
}

export const exemple = ajouter(creer(1, 'Ana'), 'Clavier', 50, 1);
""")],
       ["Chaque code d'erreur a sa correction", "Aucune triche"],
       run=TRUN("commande.ts", tests=r"""
assert.noTypeErrors('Aucune erreur de type');
const src = source('commande.ts');
assert(!/\bany\b|\bas\s+[A-Za-z]|@ts-ignore|@ts-expect-error|[\w\)\]]!\./.test(src), 'Sans any, as, !, @ts-ignore');
const m = require('./commande');
assert.equal(m.total({ id: 1, client: 'A', lignes: [{ produit: 'x', prix: 10, quantite: 2 }] }), 20, 'total sans remise : 20 (pas NaN)');
assert.equal(m.total({ id: 1, client: 'A', lignes: [{ produit: 'x', prix: 10, quantite: 2 }], remise: 0.1 }), 18, 'total avec 10 % : 18');
assert.equal(m.libelle({ id: 3, client: 'Léo', lignes: [] }), 'Commande 3 de Léo', 'libelle');
assert.equal(m.premiereLigne({ id: 1, client: 'A', lignes: [] }), '', 'premiereLigne sans ligne : chaîne vide');
assert(m.creer(5, 'Zoé').id === 5, 'creer : id reste un nombre');
assert.deepEqual(m.exemple.lignes, [{ produit: 'Clavier', prix: 50, quantite: 1 }], 'exemple : une ligne complète');
""")),
    TD(2, "Corriger un composant React",
       "Ce composant TSX a des erreurs de type typiques de React. Corrige-les sans `any` ni `as`, puis vérifie qu'il marche : choisir une quantité, voir le total, ajouter au panier." + TSX,
       ["Aucune erreur de type, ni `any`, ni `as`, ni `!`",
        "Le `<select>` de quantité met à jour un **nombre** (le total doit être `3 × 12,50 € = 37,50 €`)",
        "`onAjouter` est appelé avec `{ id, quantite }`",
        "Les props manquantes au point d'utilisation sont fournies"],
       [F("Fiche.tsx", "tsx", r"""
import { useState } from 'react';

type Produit = { id: number; nom: string; prix: number };
type FicheProps = { produit: Produit; onAjouter: (choix: { id: number; quantite: number }) => void };

export function Fiche({ produit, onAjouter }: FicheProps) {
  const [quantite, setQuantite] = useState(1);
  const total = (produit.prix * quantite).toFixed(2).replace('.', ',');

  return (
    <div>
      <h2>{produit.nom}</h2>
      <select aria-label="Quantité" value={quantite} onChange={(e) => setQuantite(e.target.value)}>
        {[1, 2, 3, 4].map((n) => <option key={n} value={n}>{n}</option>)}
      </select>
      <p id="total">{quantite} × {produit.prix.toFixed(2).replace('.', ',')} € = {total} €</p>
      <button onClick={() => onAjouter(produit.id, quantite)}>Ajouter au panier</button>
    </div>
  );
}

export default function App() {
  const [panier, setPanier] = useState<string[]>([]);
  return (
    <>
      <Fiche produit={{ id: 7, nom: 'Câble USB-C' }} onAjouter={(c) => setPanier([...panier, c.id + '×' + c.quantite])} />
      <p id="panier">{panier.join(', ')}</p>
    </>
  );
}
""")],
       ["La valeur d'un `<select>` est une chaîne : `Number(e.target.value)`.",
        "`onAjouter` attend **un** objet : `onAjouter({ id: produit.id, quantite })`.",
        "Le produit de `App` doit avoir un `prix` (12.5)."],
       [F("Fiche.tsx", "tsx", r"""
import { useState } from 'react';

type Produit = { id: number; nom: string; prix: number };
type FicheProps = { produit: Produit; onAjouter: (choix: { id: number; quantite: number }) => void };

export function Fiche({ produit, onAjouter }: FicheProps) {
  const [quantite, setQuantite] = useState(1);
  const total = (produit.prix * quantite).toFixed(2).replace('.', ',');

  return (
    <div>
      <h2>{produit.nom}</h2>
      <select aria-label="Quantité" value={quantite} onChange={(e) => setQuantite(Number(e.target.value))}>
        {[1, 2, 3, 4].map((n) => <option key={n} value={n}>{n}</option>)}
      </select>
      <p id="total">{quantite} × {produit.prix.toFixed(2).replace('.', ',')} € = {total} €</p>
      <button onClick={() => onAjouter({ id: produit.id, quantite })}>Ajouter au panier</button>
    </div>
  );
}

export default function App() {
  const [panier, setPanier] = useState<string[]>([]);
  return (
    <>
      <Fiche produit={{ id: 7, nom: 'Câble USB-C', prix: 12.5 }} onAjouter={(c) => setPanier([...panier, c.id + '×' + c.quantite])} />
      <p id="panier">{panier.join(', ')}</p>
    </>
  );
}
""")],
       ["La quantité est un nombre", "L'objet attendu par onAjouter est respecté"],
       run=TRUN("Fiche.tsx", kind="react", tests=r"""
assert.noTypeErrors('Aucune erreur de type');
assert(!/\bany\b|\bas\s+[A-Za-z]|[\w\)\]]!\./.test(source('Fiche.tsx')), 'Sans any, as, !');
await choose('[aria-label="Quantité"]', '3');
assert.equal($('#total').textContent, '3 × 12,50 € = 37,50 €', 'Total : 3 × 12,50 € = 37,50 €');
await click(Array.from(document.querySelectorAll('button')).find((b) => b.textContent === 'Ajouter au panier'));
assert.equal($('#panier').textContent, '7×3', 'onAjouter reçoit { id: 7, quantite: 3 } (un nombre)');
""")),
    TD(3, "Des types trop permissifs",
       "Ce module compile sans erreur… et laisse passer trois bugs (voir les appels en bas du fichier). **Resserre les types** pour que TypeScript refuse ces bugs, puis corrige les appels." + TS,
       ["`envoyerEmail` prend **un objet** `{ a, sujet, corps }` au lieu de trois chaînes (plus d'inversion possible)",
        "`Statut` est une union : `'en-attente' | 'payee' | 'expediee' | 'livree'` ; `changerStatut` refuse les autres chaînes",
        "`CommandeId` et `ClientId` sont deux types **marqués** (`string & { readonly __marque: '…' }`) ; `commandeId(s)` et `clientId(s)` les fabriquent ; `annulerCommande` refuse un `ClientId`",
        "Les appels du bas sont corrigés ; plus aucune erreur de type"],
       [F("boutique.ts", "ts", r"""
export function envoyerEmail(a: string, sujet: string, corps: string): string {
  return `À: ${a} | Sujet: ${sujet} | ${corps}`;
}

export type Statut = string;

export function changerStatut(id: string, statut: Statut): string {
  return `${id} → ${statut}`;
}

export function annulerCommande(id: string): string {
  return 'Commande ' + id + ' annulée';
}

// ---- appels (avec 3 bugs que TypeScript ne voit pas encore)
const commande = 'CMD-42';
const client = 'CLI-7';
export const email = envoyerEmail('Votre commande', 'ana@exemple.fr', 'Merci !');
export const statut = changerStatut(commande, 'livrée');
export const annulation = annulerCommande(client);
""")],
       ["`export function envoyerEmail(m: { a: string; sujet: string; corps: string }): string`.",
        "`export type CommandeId = string & { readonly __marque: 'CommandeId' }; export function commandeId(s: string): CommandeId { return s as CommandeId; }` (le seul `as` permis : dans la fabrique).",
        "En bas : `const commande = commandeId('CMD-42')`, et le statut s'écrit `'livree'`."],
       [F("boutique.ts", "ts", r"""
export function envoyerEmail(m: { a: string; sujet: string; corps: string }): string {
  return `À: ${m.a} | Sujet: ${m.sujet} | ${m.corps}`;
}

export type Statut = 'en-attente' | 'payee' | 'expediee' | 'livree';

export type CommandeId = string & { readonly __marque: 'CommandeId' };
export type ClientId = string & { readonly __marque: 'ClientId' };

export function commandeId(s: string): CommandeId {
  return s as CommandeId;
}

export function clientId(s: string): ClientId {
  return s as ClientId;
}

export function changerStatut(id: CommandeId, statut: Statut): string {
  return `${id} → ${statut}`;
}

export function annulerCommande(id: CommandeId): string {
  return 'Commande ' + id + ' annulée';
}

// ---- appels corrigés
const commande = commandeId('CMD-42');
const client = clientId('CLI-7');
export const email = envoyerEmail({ a: 'ana@exemple.fr', sujet: 'Votre commande', corps: 'Merci !' });
export const statut = changerStatut(commande, 'livree');
export const annulation = annulerCommande(commande);
export const leClient = client;
""")],
       ["Les trois bugs sont devenus des erreurs de compilation", "Les appels sont corrigés"],
       run=TRUN("boutique.ts", tests=r"""
assert.noTypeErrors('Aucune erreur de type');
const m = require('./boutique');
assert.equal(m.email, 'À: ana@exemple.fr | Sujet: Votre commande | Merci !', 'email : destinataire et sujet dans le bon ordre');
assert.equal(m.statut, 'CMD-42 → livree', 'statut : livree');
assert.equal(m.annulation, 'Commande CMD-42 annulée', 'on annule la commande, pas le client');
""", typetests=r"""
import { envoyerEmail, changerStatut, annulerCommande, commandeId, clientId } from './boutique';
// ✗ trois chaînes dans le désordre ne sont plus possibles
envoyerEmail('Sujet', 'ana@exemple.fr', 'Corps');
// ✓ un objet avec des noms
envoyerEmail({ a: 'ana@exemple.fr', sujet: 'S', corps: 'C' });
// ✗ un statut mal écrit
changerStatut(commandeId('C1'), 'livrée');
// ✓ un statut valide
changerStatut(commandeId('C1'), 'expediee');
// ✗ un identifiant client à la place d'un identifiant commande
annulerCommande(clientId('CLI-1'));
// ✗ une simple chaîne n'est pas un CommandeId
annulerCommande('CMD-1');
""")),
  ])

MODULES = [bases, unions, generiques, nulls, react, erreurs]

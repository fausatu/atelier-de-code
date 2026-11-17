"""Parcours « Organiser un projet React » : où ranger ses fichiers, quand passer des props (et éviter le prop drilling)."""
from common import P, L, D, N, E, LANE, F, TD, RUN

T = "orga"


def OM(id, title, minutes, goal, why, flow, points, pitfalls, quiz, prereq, diagram, lessons, recap, example, notes, tds):
    return {"id": id, "track": T, "title": title, "minutes": minutes, "goal": goal, "why": why,
            "flow": flow, "points": points, "pitfalls": pitfalls, "quiz": quiz, "prereq": prereq,
            "diagram": diagram, "lessons": lessons, "recap": recap,
            "example": {"files": example if isinstance(example, list) else [example], "notes": notes}, "tds": tds}


def Q(q, options, answer, why):
    return {"q": q, "options": options, "answer": answer, "why": why}


JS = " Le bouton Exécuter lance les tests sur ton code : chaque message te dit ce qui est juste et pourquoi."
TSH = (" Écris tes commandes dans le fichier (une par ligne), puis **▶ Lancer les commandes** : elles s'exécutent dans un terminal simulé, "
       "dans un dossier recréé à chaque lancement. `mkdir -p`, `mv`, `ls`, `find` fonctionnent comme dans un vrai terminal.")


def TERM(tests, start):
    return RUN("term", entry="commandes.sh", tests=tests, start=start)


# =========================================================================== 1. Où ranger ses fichiers
PLAT = r"""
const f = (p, c) => t.fichier('bobine-front/src/' + p, c || '// ' + p + '\n');
f('main.tsx'); f('App.tsx'); f('queryClient.ts');
f('api/client.ts', "import axios from 'axios';\nexport const api = axios.create({ baseURL: '/api' });\n");
f('api/films.ts'); f('api/profils.ts');
f('components/FilmCard.tsx'); f('components/Catalogue.tsx'); f('components/FiltreGenre.tsx');
f('components/FormulaireProfil.tsx'); f('components/ListeProfils.tsx');
f('components/Bouton.tsx'); f('components/Modale.tsx');
f('hooks/useFilms.ts'); f('hooks/useProfils.ts'); f('hooks/useDebounce.ts');
f('types/film.ts'); f('types/profil.ts');
f('schemas/profilSchema.ts');
t.cd('bobine-front');
"""

dossiers = OM("orga-dossiers", "Où créer mon fichier ? Ranger par fonctionnalité", 30,
  "Savoir où créer chaque nouveau fichier d'un projet React : ranger par **fonctionnalité** (features) plutôt que par type, distinguer ce qui appartient à une seule fonctionnalité de ce qui est partagé, et respecter des règles d'import simples.",
  "Au début d'un projet, tout tient dans `components/` et `hooks/`. Trois mois plus tard, `components/` contient 60 fichiers, et pour modifier « les profils » il faut ouvrir cinq dossiers différents. Savoir où ranger un fichier, c'est savoir où le **retrouver**, et pouvoir modifier une fonctionnalité sans casser les autres.",
  ["Le nouveau fichier sert à **une** fonctionnalité (catalogue, profils, lecteur) ? → `src/features/<fonctionnalité>/`.",
   "Il sert à **plusieurs** fonctionnalités (un bouton, un hook générique, le client axios) ? → `src/shared/`.",
   "Il configure **toute** l'application (le point d'entrée, les routes, le `QueryClient`, les providers) ? → `src/app/`.",
   "Dans une fonctionnalité, on range par rôle : `components/`, `api.ts`, `hooks.ts`, `types.ts`, `schema.ts`, et un `index.ts` qui dit ce qui est utilisable de l'extérieur.",
   "Règles d'import : une fonctionnalité peut importer `shared/` et l'`index.ts` d'une autre ; `shared/` n'importe jamais une fonctionnalité."],
  ["Deux façons de ranger : **par type** (`components/`, `hooks/`, `api/`) ou **par fonctionnalité** (`features/profils/` contient ses composants, son API, ses hooks). La 2e tient mieux quand le projet grandit.",
   "Un fichier commence **dans la fonctionnalité** qui en a besoin. Il passe dans `shared/` le jour où une **deuxième** fonctionnalité en a besoin, pas avant.",
   "`shared/` ne contient que des choses génériques, qui ne parlent d'aucune fonctionnalité : `Bouton`, `Modale`, `useDebounce`, le client axios.",
   "L'`index.ts` d'une fonctionnalité est sa porte d'entrée : les autres importent `features/profils`, jamais `features/profils/components/…`.",
   "Ce n'est pas une loi : une petite appli de 10 fichiers peut rester par type. La règle sert à décider vite, pas à tout déplacer tous les jours."],
  ["Mettre dans `shared/` un composant utilisé par une seule fonctionnalité « au cas où ».",
   "Un `shared/` qui importe une fonctionnalité (`shared/Header.tsx` qui importe `features/profils/…`) : tout devient lié à tout.",
   "Importer l'intérieur d'une autre fonctionnalité au lieu de son `index.ts`.",
   "Un dossier `utils/` fourre-tout : chaque fonction devrait vivre près de ceux qui l'utilisent.",
   "Réorganiser tout le projet d'un coup en pleine fonctionnalité : on range au fil de l'eau, une PR à part (`refactor:`)."],
  [Q("`FormulaireProfil.tsx` n'est utilisé que par les profils. Où le mettre ?", ["`src/components/`", "`src/shared/ui/`", "`src/features/profils/components/`", "`src/app/`"], 2, "Il appartient à une seule fonctionnalité : il vit dans son dossier."),
   Q("Le composant `Bouton` sert au catalogue **et** aux profils :", ["`features/catalogue/components/`", "`shared/ui/`", "on le copie dans les deux", "`app/`"], 1, "Utilisé par deux fonctionnalités et générique : c'est du partagé."),
   Q("Le `QueryClient` et le `QueryClientProvider` de toute l'appli :", ["`shared/`", "`features/catalogue/`", "`app/`", "`hooks/`"], 2, "Ce qui configure l'application entière va dans `app/`."),
   Q("`features/lecteur/` a besoin du type `Profil`. Il importe :", ["`../profils/types`", "`features/profils` (son index.ts)", "il le recopie", "`shared/types`"], 1, "On passe par la porte d'entrée de la fonctionnalité : son `index.ts` exporte ce qui est public.")],
  [P("Fonctionnalité (feature)", "Une partie de l'application qui a du sens pour l'utilisateur : le catalogue, les profils, le lecteur, « Ma liste ». C'est souvent une tranche ou un groupe de tranches."),
   P("Module ES (`import` / `export`)", "Chaque fichier `.ts`/`.tsx` est un module : il **exporte** ce qu'il rend utilisable (`export function …`) et **importe** ce dont il a besoin (`import { api } from '../shared/api/client'`). Le chemin entre guillemets est relatif au fichier qui importe."),
   P("`index.ts`", "Quand on importe un **dossier** (`import { FormulaireProfil } from './features/profils'`), c'est le fichier `index.ts` de ce dossier qui est lu. On s'en sert comme vitrine : il réexporte (`export { … } from './…'`) seulement ce qui est public."),
   P("Partagé (shared)", "Du code utilisé par plusieurs fonctionnalités et qui ne parle d'aucune d'elles : composants d'interface (`Bouton`, `Modale`), hooks génériques (`useDebounce`), le client axios."),
  ],
  D(
    nodes=[
      N("app", 0, 0, "src/app/", "main.tsx, App.tsx, queryClient", kind="file", color="muted"),
      N("cat", 1, 0, "features/catalogue/", "components, api, hooks, index", kind="file", color="accent"),
      N("pro", 1, 1, "features/profils/", "components, api, schema, index", kind="file", color="accent"),
      N("sh", 2, 0, "src/shared/", "ui/Bouton, api/client, hooks/useDebounce", kind="file", color="good"),
    ],
    edges=[E("app", "cat", "importe"), E("app", "pro", "importe"), E("cat", "sh", "importe"), E("pro", "sh", "importe"), E("cat", "pro", "via index.ts", dashed=True)],
    caption="Les flèches d'import vont toujours vers la droite : app → features → shared. shared n'importe jamais une fonctionnalité."),
  [
    L("Ranger par type ou par fonctionnalité", r"""
Il y a deux grandes façons de ranger un projet React. Voici le même front de Bobine rangé des deux façons.

**Par type** : un dossier par sorte de fichier. C'est ce que font la plupart des tutos.

```
src/
├── api/          client.ts, films.ts, profils.ts
├── components/   Catalogue.tsx, FilmCard.tsx, FiltreGenre.tsx, FormulaireProfil.tsx, ListeProfils.tsx, Bouton.tsx, Modale.tsx
├── hooks/        useFilms.ts, useProfils.ts, useDebounce.ts
├── schemas/      profilSchema.ts
└── types/        film.ts, profil.ts
```

Simple au départ. Mais pour travailler sur « les profils », il faut ouvrir `api/`, `components/`, `hooks/`, `schemas/` et `types/` ; et rien ne dit que `Bouton.tsx` sert partout alors que `FormulaireProfil.tsx` ne sert qu'aux profils.

**Par fonctionnalité** : un dossier par partie de l'application, qui contient **tout** ce qui la concerne, plus un dossier pour ce qui est partagé.

```
src/
├── app/                      ce qui configure TOUTE l'appli
│   ├── main.tsx
│   ├── App.tsx
│   └── queryClient.ts
├── features/
│   ├── catalogue/
│   │   ├── components/       Catalogue.tsx, FilmCard.tsx, FiltreGenre.tsx
│   │   ├── api.ts            getFilms, getFilm
│   │   ├── hooks.ts          useFilms
│   │   ├── types.ts          Film, Genre
│   │   └── index.ts          ce que les autres ont le droit d'utiliser
│   └── profils/
│       ├── components/       FormulaireProfil.tsx, ListeProfils.tsx
│       ├── api.ts, hooks.ts, types.ts, schema.ts
│       └── index.ts
└── shared/                   utilisé par plusieurs fonctionnalités
    ├── api/client.ts         le client axios
    ├── ui/                   Bouton.tsx, Modale.tsx
    └── hooks/useDebounce.ts
```

Pour modifier les profils, tout est dans `features/profils/`. Pour supprimer une fonctionnalité, on supprime un dossier. Et la place d'un fichier dit déjà s'il est spécifique ou partagé.
"""),
    L("La question à se poser pour chaque nouveau fichier", r"""
Quand tu crées un fichier, pose ces trois questions **dans cet ordre** :

1. **Il configure toute l'application ?** (le point d'entrée `main.tsx`, `App.tsx`, les routes, le `QueryClient`, les providers) → `src/app/`.
2. **Combien de fonctionnalités s'en servent aujourd'hui ?**
   - **une** → dans le dossier de cette fonctionnalité : `src/features/<nom>/` ;
   - **plusieurs** → `src/shared/`.
3. **Dans la fonctionnalité (ou dans shared), quel est son rôle ?** Un composant → `components/` (ou `ui/` dans shared) ; des appels axios → `api.ts` ; des hooks → `hooks.ts` ; des types → `types.ts` ; un schéma zod → `schema.ts`.

La règle qui évite la plupart des hésitations : **un fichier commence là où il est utilisé**. `FilmCard` est créé dans `features/catalogue/components/`. Le jour où « Ma liste » veut aussi afficher des `FilmCard`, on a deux choix : passer par l'`index.ts` du catalogue (si c'est vraiment « une carte de film du catalogue »), ou le déplacer dans `shared/ui/` (si c'est devenu un composant générique). On ne le met pas dans `shared/` « au cas où » le premier jour.

Et ce qui est **dans** `shared/` ne doit parler d'aucune fonctionnalité : un `Bouton` reçoit un texte et un `onClick`, il ne sait pas ce qu'est un profil.
"""),
    L("Les règles d'import : la porte d'entrée `index.ts`", r"""
Un fichier en **importe** un autre avec `import { quelqueChose } from 'chemin'`. Le chemin commence par `./` (même dossier) ou `../` (dossier parent). Quand le chemin désigne un **dossier**, c'est son fichier `index.ts` qui est lu.

On utilise ça pour donner à chaque fonctionnalité une **porte d'entrée** : son `index.ts` réexporte seulement ce que les autres ont le droit d'utiliser.

```ts
// src/features/profils/index.ts
export { FormulaireProfil } from './components/FormulaireProfil';
export { ListeProfils } from './components/ListeProfils';
export { useProfils } from './hooks';
export type { Profil } from './types';
```

`export { X } from './fichier'` veut dire « je rends disponible le `X` de ce fichier ». `export type` fait pareil pour un type.

Trois règles, faciles à vérifier en lisant les `import` en haut d'un fichier :

| Qui importe | a le droit d'importer | n'a pas le droit |
|---|---|---|
| `app/` | les `index.ts` des fonctionnalités, `shared/` | l'intérieur des fonctionnalités |
| `features/a/` | ses propres fichiers, `shared/`, l'`index.ts` de `features/b` | `features/b/components/...` (l'intérieur de b) |
| `shared/` | `shared/` | **n'importe quelle** fonctionnalité |

Pourquoi ? Si `shared/` importait les profils, tout ce qui utilise `Bouton` dépendrait des profils. Et si on n'importe que l'`index.ts`, on peut réorganiser l'intérieur d'une fonctionnalité sans casser les autres.
"""),
  ],
  ["`app/` = ce qui configure toute l'appli ; `features/<nom>/` = une fonctionnalité ; `shared/` = utilisé par plusieurs, générique.",
   "Un fichier commence là où il est utilisé ; il passe dans `shared/` quand une 2e fonctionnalité en a besoin.",
   "Dans une fonctionnalité : `components/`, `api.ts`, `hooks.ts`, `types.ts`, `schema.ts`, `index.ts`.",
   "On importe une autre fonctionnalité par son `index.ts`, jamais son intérieur.",
   "`shared/` n'importe jamais une fonctionnalité."],
  [F("src/features/profils/index.ts", "ts", r"""
// La porte d'entrée des profils : seul ce qui est exporté ici est utilisable ailleurs.
export { FormulaireProfil } from './components/FormulaireProfil';
export { ListeProfils } from './components/ListeProfils';
export { useProfils } from './hooks';
export type { Profil } from './types';
"""), F("src/features/profils/hooks.ts", "ts", r"""
import { useQuery } from '@tanstack/react-query';
import { getProfils } from './api';                 // même fonctionnalité : chemin relatif court

export function useProfils() {
  return useQuery({ queryKey: ['profils'], queryFn: getProfils });
}
"""), F("src/features/profils/api.ts", "ts", r"""
import { api } from '../../shared/api/client';      // shared : autorisé
import type { Profil } from './types';

export async function getProfils(): Promise<Profil[]> {
  const res = await api.get<Profil[]>('/profils');
  return res.data;
}
"""), F("src/app/App.tsx", "tsx", r"""
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './queryClient';
import { Catalogue } from '../features/catalogue';   // l'index.ts du catalogue
import { ListeProfils } from '../features/profils';  // l'index.ts des profils

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ListeProfils />
      <Catalogue />
    </QueryClientProvider>
  );
}
""")],
  ["`App.tsx` n'importe que les **portes d'entrée** (`../features/catalogue`, `../features/profils`).",
   "`api.ts` des profils importe le client axios depuis `shared/` : c'est la direction autorisée.",
   "`hooks.ts` importe `./api` : à l'intérieur d'une fonctionnalité, on importe librement.",
   "L'`index.ts` ne montre pas `getProfils` : les autres passent par `useProfils`."],
  [
    TD(1, "Ranger le front de Bobine par fonctionnalité",
       "Le front de Bobine est rangé par type (`api/`, `components/`, `hooks/`, `types/`, `schemas/`). Réorganise-le par fonctionnalité, avec `mkdir -p` et `mv`." + TSH,
       ["`src/app/` : `main.tsx`, `App.tsx`, `queryClient.ts`",
        "`src/features/catalogue/` : `components/` (`Catalogue.tsx`, `FilmCard.tsx`, `FiltreGenre.tsx`), `api.ts` (l'ancien `api/films.ts`), `hooks.ts` (l'ancien `hooks/useFilms.ts`), `types.ts` (l'ancien `types/film.ts`)",
        "`src/features/profils/` : `components/` (`FormulaireProfil.tsx`, `ListeProfils.tsx`), `api.ts`, `hooks.ts`, `types.ts`, `schema.ts` (l'ancien `schemas/profilSchema.ts`)",
        "`src/shared/` : `api/client.ts`, `ui/Bouton.tsx`, `ui/Modale.tsx`, `hooks/useDebounce.ts`",
        "À la fin, les anciens dossiers `api/`, `components/`, `hooks/`, `types/`, `schemas/` sont vides et supprimés (`rmdir`)"],
       [F("commandes.sh", "bash", r"""
# tu es dans ~/bobine-front
find src -type f
# à toi
""")],
       ["Crée d'abord tous les dossiers d'un coup : `mkdir -p src/app src/features/catalogue/components src/features/profils/components src/shared/api src/shared/ui src/shared/hooks`.",
        "`mv` déplace **et** renomme : `mv src/api/films.ts src/features/catalogue/api.ts`.",
        "Plusieurs fichiers vers un même dossier : `mv src/components/Catalogue.tsx src/components/FilmCard.tsx src/components/FiltreGenre.tsx src/features/catalogue/components/`.",
        "`rmdir dossier` ne supprime qu'un dossier vide : s'il refuse, un fichier n'a pas été déplacé (`find src -type f` pour vérifier)."],
       [F("commandes.sh", "bash", r"""
find src -type f
mkdir -p src/app src/features/catalogue/components src/features/profils/components src/shared/api src/shared/ui src/shared/hooks
mv src/main.tsx src/App.tsx src/queryClient.ts src/app/
mv src/components/Catalogue.tsx src/components/FilmCard.tsx src/components/FiltreGenre.tsx src/features/catalogue/components/
mv src/api/films.ts src/features/catalogue/api.ts
mv src/hooks/useFilms.ts src/features/catalogue/hooks.ts
mv src/types/film.ts src/features/catalogue/types.ts
mv src/components/FormulaireProfil.tsx src/components/ListeProfils.tsx src/features/profils/components/
mv src/api/profils.ts src/features/profils/api.ts
mv src/hooks/useProfils.ts src/features/profils/hooks.ts
mv src/types/profil.ts src/features/profils/types.ts
mv src/schemas/profilSchema.ts src/features/profils/schema.ts
mv src/api/client.ts src/shared/api/client.ts
mv src/components/Bouton.tsx src/components/Modale.tsx src/shared/ui/
mv src/hooks/useDebounce.ts src/shared/hooks/useDebounce.ts
rmdir src/api src/components src/hooks src/types src/schemas
find src -type f
""")],
       ["Chaque fonctionnalité a tout dans son dossier", "shared ne contient que du générique"],
       run=TERM(r"""
const base = 'bobine-front/src/';
const doit = ['app/main.tsx', 'app/App.tsx', 'app/queryClient.ts',
  'features/catalogue/components/Catalogue.tsx', 'features/catalogue/components/FilmCard.tsx', 'features/catalogue/components/FiltreGenre.tsx',
  'features/catalogue/api.ts', 'features/catalogue/hooks.ts', 'features/catalogue/types.ts',
  'features/profils/components/FormulaireProfil.tsx', 'features/profils/components/ListeProfils.tsx',
  'features/profils/api.ts', 'features/profils/hooks.ts', 'features/profils/types.ts', 'features/profils/schema.ts',
  'shared/api/client.ts', 'shared/ui/Bouton.tsx', 'shared/ui/Modale.tsx', 'shared/hooks/useDebounce.ts'];
const manquants = doit.filter((p) => !term.isFile(base + p));
assert.equal(manquants.length, 0, 'Tous les fichiers sont à leur nouvelle place', manquants.join(', '));
assert(/axios\.create/.test(term.read(base + 'shared/api/client.ts') || ''), 'Le client axios a été déplacé (pas recréé vide)');
for (const d of ['api', 'components', 'hooks', 'types', 'schemas']) assert(!term.exists(base + d), `L'ancien dossier src/${d}/ a disparu`);
const tous = (term.tree('bobine-front/src') || []).filter((p) => !p.endsWith('/'));
assert.equal(tous.length, doit.length, 'Aucun fichier en trop ni perdu (' + doit.length + ' fichiers)', tous.join(', '));
""", PLAT)),
    TD(2, "Une nouvelle fonctionnalité : Ma liste",
       "Le projet est maintenant rangé par fonctionnalité. Tu ajoutes « Ma liste » (les films mis de côté), qui a besoin d'afficher des cartes de films… comme le catalogue. Décide où va chaque fichier." + TSH,
       ["Crée `features/ma-liste/` avec `components/MaListe.tsx`, `api.ts` et `index.ts` (contenu libre, `touch` suffit)",
        "`FilmCard.tsx` est désormais utilisé par **deux** fonctionnalités et ne parle que d'un film : déplace-le dans `shared/ui/`",
        "Le hook `useDebounce` n'est utilisé que par la recherche du catalogue : remets-le dans le catalogue, en `features/catalogue/useDebounce.ts`, et supprime le dossier `shared/hooks/` devenu vide",
        "Ne touche pas au reste"],
       [F("commandes.sh", "bash", r"""
# tu es dans ~/bobine-front
find src -type f
# à toi
""")],
       ["`mkdir -p src/features/ma-liste/components` puis `touch src/features/ma-liste/components/MaListe.tsx src/features/ma-liste/api.ts src/features/ma-liste/index.ts`.",
        "`mv src/features/catalogue/components/FilmCard.tsx src/shared/ui/`",
        "`mv src/shared/hooks/useDebounce.ts src/features/catalogue/useDebounce.ts` puis `rmdir src/shared/hooks`."],
       [F("commandes.sh", "bash", r"""
find src -type f
mkdir -p src/features/ma-liste/components
touch src/features/ma-liste/components/MaListe.tsx src/features/ma-liste/api.ts src/features/ma-liste/index.ts
mv src/features/catalogue/components/FilmCard.tsx src/shared/ui/
mv src/shared/hooks/useDebounce.ts src/features/catalogue/useDebounce.ts
rmdir src/shared/hooks
find src -type f
""")],
       ["FilmCard est partagé", "useDebounce revient près de son seul utilisateur"],
       run=TERM(r"""
const b = 'bobine-front/src/';
assert(term.isFile(b + 'features/ma-liste/components/MaListe.tsx') && term.isFile(b + 'features/ma-liste/api.ts') && term.isFile(b + 'features/ma-liste/index.ts'), 'features/ma-liste/ : components/MaListe.tsx, api.ts, index.ts');
assert(term.isFile(b + 'shared/ui/FilmCard.tsx') && !term.exists(b + 'features/catalogue/components/FilmCard.tsx'), 'FilmCard est dans shared/ui (et plus dans le catalogue)');
assert(term.isFile(b + 'features/catalogue/useDebounce.ts'), 'useDebounce est revenu dans le catalogue');
assert(!term.exists(b + 'shared/hooks'), 'shared/hooks/ (vide) est supprimé');
assert(term.isFile(b + 'shared/ui/Bouton.tsx') && term.isFile(b + 'features/profils/schema.ts') && term.isFile(b + 'features/catalogue/components/Catalogue.tsx'), 'Le reste n\'a pas bougé');
""", r"""
const f = (p) => t.fichier('bobine-front/src/' + p, '// ' + p + '\n');
['app/main.tsx', 'app/App.tsx', 'app/queryClient.ts', 'features/catalogue/components/Catalogue.tsx', 'features/catalogue/components/FilmCard.tsx', 'features/catalogue/components/FiltreGenre.tsx',
 'features/catalogue/api.ts', 'features/catalogue/hooks.ts', 'features/catalogue/types.ts', 'features/catalogue/index.ts', 'features/profils/components/FormulaireProfil.tsx', 'features/profils/components/ListeProfils.tsx',
 'features/profils/api.ts', 'features/profils/hooks.ts', 'features/profils/types.ts', 'features/profils/schema.ts', 'features/profils/index.ts',
 'shared/api/client.ts', 'shared/ui/Bouton.tsx', 'shared/ui/Modale.tsx', 'shared/hooks/useDebounce.ts'].forEach(f);
t.cd('bobine-front');
""")),
    TD(3, "Un vérificateur des règles d'import",
       "Pour que l'équipe respecte les règles sans y penser, tu écris une petite fonction qui lit les imports de chaque fichier et signale ceux qui sont interdits (c'est ce que font des outils comme ESLint avec un plugin de « frontières »)." + JS,
       ["`importsInterdits(fichiers)` reçoit une liste `{ chemin, imports }` : `chemin` part de `src/` (`'features/profils/api.ts'`), `imports` contient des chemins **déjà résolus** depuis `src/` (`'shared/api/client'`, `'features/catalogue'`…)",
        "Interdit 1 : un fichier de `shared/` qui importe quoi que ce soit dans `features/`",
        "Interdit 2 : un fichier de `features/a/` qui importe l'**intérieur** d'une autre fonctionnalité (`features/b/...` avec quelque chose après `features/b`) ; `features/b` seul (l'index) est autorisé, et l'intérieur de sa **propre** fonctionnalité aussi",
        "Interdit 3 : un fichier de `app/` qui importe l'intérieur d'une fonctionnalité",
        "Renvoie la liste des textes `\"<chemin> → <import>\"`, dans l'ordre des fichiers puis des imports"],
       [F("regles.ts", "ts", r"""
type Fichier = { chemin: string; imports: string[] };

/** 'features/profils/api.ts' → 'profils' ; 'shared/ui/Bouton.tsx' → null */
export function fonctionnalite(chemin: string): string | null {
  const m = chemin.match(/^features\/([^/]+)/);
  return m ? m[1] : null;
}

export function importsInterdits(fichiers: Fichier[]): string[] {
  // à toi
  return [];
}
""")],
       ["Pour un import, `/^features\\/[^/]+\\/.+/.test(imp)` est vrai s'il vise l'**intérieur** d'une fonctionnalité.",
        "Utilise `fonctionnalite(chemin)` et `fonctionnalite(imp)` pour savoir si c'est la même fonctionnalité.",
        "Une boucle sur les fichiers, une boucle sur leurs imports, et `resultat.push(`${f.chemin} → ${imp}`)` quand une règle est violée."],
       [F("regles.ts", "ts", r"""
type Fichier = { chemin: string; imports: string[] };

/** 'features/profils/api.ts' → 'profils' ; 'shared/ui/Bouton.tsx' → null */
export function fonctionnalite(chemin: string): string | null {
  const m = chemin.match(/^features\/([^/]+)/);
  return m ? m[1] : null;
}

export function importsInterdits(fichiers: Fichier[]): string[] {
  const resultat: string[] = [];
  for (const f of fichiers) {
    const mienne = fonctionnalite(f.chemin);
    for (const imp of f.imports) {
      const cible = fonctionnalite(imp);
      const interieur = /^features\/[^/]+\/.+/.test(imp);
      const interdit =
        (f.chemin.startsWith('shared/') && cible !== null) ||
        (mienne !== null && cible !== null && cible !== mienne && interieur) ||
        (f.chemin.startsWith('app/') && interieur);
      if (interdit) resultat.push(`${f.chemin} → ${imp}`);
    }
  }
  return resultat;
}
""")],
       ["L'index d'une autre fonctionnalité est autorisé", "shared n'importe jamais une fonctionnalité"],
       run=RUN("js", entry="regles.ts", tests=r"""
const { importsInterdits } = require('./regles');
const ok = [
  { chemin: 'app/App.tsx', imports: ['features/catalogue', 'features/profils', 'shared/ui/Bouton'] },
  { chemin: 'features/profils/api.ts', imports: ['shared/api/client', 'features/profils/types'] },
  { chemin: 'features/lecteur/components/Lecteur.tsx', imports: ['features/profils', 'features/lecteur/hooks'] },
  { chemin: 'shared/ui/Modale.tsx', imports: ['shared/ui/Bouton'] },
];
assert.deepEqual(importsInterdits(ok), [], 'Un projet qui respecte les règles : aucune erreur');
assert.deepEqual(importsInterdits([{ chemin: 'shared/ui/Header.tsx', imports: ['features/profils', 'shared/ui/Bouton'] }]), ['shared/ui/Header.tsx → features/profils'], 'shared qui importe une fonctionnalité (même son index) : interdit');
assert.deepEqual(importsInterdits([{ chemin: 'features/lecteur/hooks.ts', imports: ['features/profils/hooks', 'features/profils'] }]), ['features/lecteur/hooks.ts → features/profils/hooks'], "L'intérieur d'une autre fonctionnalité : interdit ; son index : autorisé");
assert.deepEqual(importsInterdits([{ chemin: 'features/catalogue/components/Catalogue.tsx', imports: ['features/catalogue/hooks', 'features/catalogue/components/FilmCard'] }]), [], 'Sa propre fonctionnalité : autorisé');
assert.deepEqual(importsInterdits([{ chemin: 'app/App.tsx', imports: ['features/catalogue/components/Catalogue'] }]), ['app/App.tsx → features/catalogue/components/Catalogue'], "app qui importe l'intérieur d'une fonctionnalité : interdit");
const tout = importsInterdits([
  { chemin: 'app/main.tsx', imports: ['app/App', 'features/profils/components/ListeProfils'] },
  { chemin: 'shared/hooks/useProfilActif.ts', imports: ['features/profils/types'] },
  { chemin: 'features/ma-liste/api.ts', imports: ['shared/api/client', 'features/catalogue/types'] },
]);
assert.deepEqual(tout, ['app/main.tsx → features/profils/components/ListeProfils', 'shared/hooks/useProfilActif.ts → features/profils/types', 'features/ma-liste/api.ts → features/catalogue/types'], 'Plusieurs fichiers : toutes les erreurs, dans l\'ordre');
""")),
  ])

# =========================================================================== 2. Passer des props, ou pas
props = OM("orga-props", "Passer des props, ou pas : éviter le prop drilling", 40,
  "Savoir, pour chaque donnée, si elle doit descendre en prop, remonter dans le parent, être lue avec React Query, ou passer par un Context ; reconnaître le prop drilling et le corriger avec la bonne solution.",
  "Une prop, c'est simple : un parent donne une valeur à un enfant. Mais dans une vraie appli, on se retrouve vite à passer `profil` de `App` à `Page`, puis à `Layout`, puis à `Sidebar`, puis enfin à `Badge`, le seul qui s'en sert. Les trois du milieu ne font que transmettre. C'est le **prop drilling** : chaque changement oblige à toucher cinq fichiers. Il n'y a pas une solution unique, il y en a quatre, et chacune répond à une situation précise.",
  ["Une donnée a **un seul propriétaire** : le composant qui la crée (un `useState`) ou React Query (les données du serveur).",
   "Un enfant en a besoin ? Le propriétaire la lui passe en **prop** ; l'enfant le prévient d'un changement en appelant une **fonction** reçue en prop.",
   "Deux composants frères en ont besoin ? On **remonte** le state dans leur parent commun le plus proche.",
   "Une prop traverse des composants qui ne s'en servent pas ? On cherche la bonne sortie : **composition** (`children`), **React Query** (données serveur), ou **Context** (donnée vraiment globale)."],
  ["Les props descendent ; les événements remontent (par une fonction passée en prop). Un enfant ne modifie jamais une prop.",
   "Passer une prop à un enfant direct qui s'en sert : c'est **normal**, c'est le cas le plus courant. Le problème n'est pas la prop, c'est la prop qui traverse sans servir.",
   "Les données du serveur (films, profils) ne se passent pas sur 4 niveaux : chaque composant qui en a besoin appelle le même hook (`useProfils()`), React Query ne fait qu'une requête grâce au cache.",
   "Composition : un composant de mise en page reçoit `children` au lieu de recevoir les données de ses enfants. Le parent place lui-même le composant qui a besoin de la donnée.",
   "Context : pour une donnée côté client utilisée un peu partout (le profil actif, le thème, la langue). Pas pour remplacer toutes les props."],
  ["Recopier une prop dans un `useState` de l'enfant : les deux finissent par ne plus être d'accord.",
   "Mettre toutes les données dans un Context « pour ne plus passer de props » : chaque changement redessine tout, et on ne sait plus d'où vient quoi.",
   "Passer la liste des films de `App` jusqu'à `FilmCard` alors que React Query la garde en cache.",
   "Un composant `Layout` qui reçoit `profil` juste pour le donner à un enfant : il devrait recevoir `children`.",
   "Garder le même state en double dans deux frères au lieu de le remonter."],
  [Q("`Layout` reçoit `profil` seulement pour le passer à `Sidebar`, qui le passe à `Badge`. La meilleure correction :", ["un Context pour tout", "`Layout` reçoit `children` ; la page place `<Badge profil={profil} />` elle-même", "dupliquer `profil` dans un useState de Badge", "rien, c'est normal"], 1, "Les composants de mise en page ne devraient pas connaître les données de leurs enfants : la composition supprime les intermédiaires."),
   Q("`Catalogue` et `Compteur` (deux frères) doivent afficher le même genre sélectionné :", ["chacun son useState", "le state dans leur parent commun, passé aux deux", "un Context obligatoire", "localStorage"], 1, "Remonter le state au plus proche parent commun : une seule source de vérité."),
   Q("Trois composants éloignés affichent la liste des profils venue de l'API :", ["la charger dans App et la passer partout", "chacun appelle `useProfils()` ; React Query ne fait qu'une requête", "un Context avec la liste", "trois requêtes, tant pis"], 1, "Les données du serveur ont déjà un propriétaire : le cache de React Query."),
   Q("Le profil **actif** (choisi à l'écran « Qui regarde ? ») sert au header, au catalogue (contrôle parental) et au lecteur :", ["un Context `ProfilActif`", "une prop sur 5 niveaux", "un useState dans chaque composant", "une variable globale `let`"], 0, "Une donnée côté client, choisie une fois, lue un peu partout : c'est le cas d'usage du Context.")],
  [P("Prop", "Un argument d'un composant : `<Badge profil={p} />` donne `p` à `Badge`, qui le lit dans ses paramètres (`function Badge({ profil })`). Une prop est en **lecture seule** pour l'enfant."),
   P("State", "La mémoire d'un composant (`useState`). Le composant qui appelle `useState` est le **propriétaire** de cette donnée : lui seul la modifie."),
   P("Remonter le state (lifting state up)", "Déplacer un `useState` dans le parent commun de deux composants qui en ont besoin, puis le leur passer en props (vu dans le parcours React)."),
   P("`children`", "Une prop spéciale : ce qu'on écrit **entre** les balises d'un composant (`<Layout><Badge /></Layout>`) arrive dans `children`. Le composant l'affiche où il veut avec `{children}`."),
   P("Context", "Un moyen de rendre une valeur disponible à tous les composants d'une partie de l'arbre, sans la passer en props. On le crée avec `createContext`, on le fournit avec `<Ctx.Provider value={…}>`, on le lit avec `useContext(Ctx)`."),
   P("Prop drilling", "Faire traverser une prop à plusieurs composants qui ne s'en servent pas, juste pour qu'elle arrive à un composant plus bas."),
  ],
  D(
    nodes=[
      N("q", 0, 0, "Qui a besoin de la donnée ?", "", kind="pill", color="accent"),
      N("p", 1, 0, "Un enfant direct", "→ prop", kind="pill", color="good"),
      N("f", 1, 1, "Deux frères", "→ remonter le state", kind="pill", color="good"),
      N("s", 2, 0, "Donnée du serveur", "→ useQuery partout (cache)", kind="pill", color="warn"),
      N("c", 2, 1, "Traverse la mise en page", "→ children (composition)", kind="pill", color="warn"),
      N("x", 2, 2, "Donnée client globale", "→ Context", kind="pill", color="bad"),
    ],
    edges=[E("q", "p"), E("q", "f"), E("q", "s", dashed=True), E("q", "c", dashed=True), E("q", "x", dashed=True)],
    caption="De la solution la plus simple (une prop) à la plus lourde (un Context) : on prend la première qui convient."),
  [
    L("Ce qu'est une prop, et le cas normal", r"""
Une **prop** est un argument d'un composant. Le parent l'écrit comme un attribut HTML, l'enfant la reçoit dans ses paramètres (par déstructuration : `function FilmCard({ film, onAjouter })`) :

- une **valeur** descend : `<FilmCard film={film} />` ;
- une **fonction** descend aussi, pour que l'enfant puisse **prévenir** le parent : `<FilmCard onAjouter={(id) => ajouter(id)} />`, et dans l'enfant `onClick={() => onAjouter(film.id)}`.

L'enfant ne modifie **jamais** une prop. S'il faut changer la donnée, c'est son propriétaire (le parent qui a le `useState`) qui la change, quand l'enfant l'appelle.

Passer une prop à un enfant **qui s'en sert** est le cas normal, et le plus fréquent. Ce n'est pas du prop drilling. Il n'y a rien à « éviter » quand `Catalogue` passe `film` à `FilmCard`.

La question à se poser, pour chaque donnée : **qui en est le propriétaire, et qui s'en sert ?**

| Situation | Solution |
|---|---|
| un enfant direct s'en sert | une **prop** |
| deux composants frères s'en servent | **remonter** le state dans leur parent commun |
| c'est une donnée du **serveur** (films, profils) | chaque composant appelle le **hook React Query** |
| elle traverse des composants de **mise en page** qui ne s'en servent pas | **composition** avec `children` |
| c'est une donnée **côté client** utilisée un peu partout (profil actif, thème) | un **Context** |

On prend la **première** ligne qui convient : elles vont de la plus simple à la plus lourde.
"""),
    L("Données du serveur : pas de props, le même hook partout", r"""
Le header affiche le nombre de profils, la page « Qui regarde ? » les liste, le formulaire vérifie qu'il en reste de la place. Réflexe de débutant : charger la liste dans `App` et la passer à tout le monde. Avec React Query, c'est inutile : la liste a déjà un propriétaire, **le cache**.

On écrit un petit hook une fois (dans `features/profils/hooks.ts`), et chaque composant qui en a besoin l'appelle :

```tsx
export function useProfils() {
  return useQuery({ queryKey: ['profils'], queryFn: getProfils });
}

function CompteurProfils() {
  const { data } = useProfils();
  return <span>{data?.length ?? 0} profils</span>;
}

function QuiRegarde() {
  const { data } = useProfils();
  return <ul>{data?.map((p) => <li key={p.id}>{p.nom}</li>)}</ul>;
}
```

Les deux composants utilisent la **même clé** `['profils']` : React Query ne fait qu'**une** requête et leur donne la même réponse. Après une création, `invalidateQueries({ queryKey: ['profils'] })` les met à jour tous les deux. Aucune prop.
"""),
    L("Composition : la mise en page reçoit `children`", r"""
Le cas typique du prop drilling : des composants de **mise en page** (une page, un layout, une barre latérale) reçoivent une donnée seulement pour la transmettre.

```tsx
// Avant : Layout et Sidebar ne se servent pas de profil, ils le transmettent
function Page({ profil }) { return <Layout profil={profil} />; }
function Layout({ profil }) { return <div className="layout"><Sidebar profil={profil} /><main>…</main></div>; }
function Sidebar({ profil }) { return <aside><Badge profil={profil} /></aside>; }
```

La correction : la mise en page ne fabrique plus ses enfants, elle les **reçoit**. La prop spéciale **`children`** contient ce qu'on écrit entre les balises d'un composant ; on peut aussi créer d'autres props qui reçoivent des éléments (`barre={…}`). Le parent, qui a la donnée, place lui-même le composant qui en a besoin :

```tsx
// Après : Layout ne connaît plus profil
function Layout({ barre, children }: { barre: ReactNode; children: ReactNode }) {
  return <div className="layout"><aside>{barre}</aside><main>{children}</main></div>;
}

function Page({ profil }: { profil: Profil }) {
  return (
    <Layout barre={<Badge profil={profil} />}>
      <Catalogue />
    </Layout>
  );
}
```

`ReactNode` est le type de « tout ce que React sait afficher ». `Layout` devient réutilisable avec n'importe quel contenu, et `profil` ne traverse plus qu'un niveau.
"""),
    L("Context : une donnée client utilisée partout", r"""
Le **profil actif** (choisi sur l'écran « Qui regarde ? ») sert au header (son nom), au catalogue (le contrôle parental), au lecteur (la reprise). C'est une donnée **côté client** (pas une réponse du serveur), choisie une fois, lue un peu partout. C'est le vrai cas du **Context**.

Un Context se met en place en trois morceaux, tous rangés dans un seul fichier :

1. **`createContext<Type>(valeurParDéfaut)`** crée le Context. On met `null` par défaut : « pas de fournisseur ».
2. **Un composant fournisseur** (`ProfilActifProvider`) qui possède le state et le **fournit** avec `<Ctx.Provider value={…}>{children}</Ctx.Provider>`. Tous les composants à l'intérieur peuvent le lire.
3. **Un hook** (`useProfilActif`) qui lit la valeur avec **`useContext(Ctx)`**, et lève une erreur claire si on l'utilise en dehors du fournisseur.

```tsx
import { createContext, useContext, useState, type ReactNode } from 'react';

type ProfilActif = { profil: Profil | null; choisir: (p: Profil) => void };
const Ctx = createContext<ProfilActif | null>(null);

export function ProfilActifProvider({ children }: { children: ReactNode }) {
  const [profil, setProfil] = useState<Profil | null>(null);
  return <Ctx.Provider value={{ profil, choisir: setProfil }}>{children}</Ctx.Provider>;
}

export function useProfilActif(): ProfilActif {
  const v = useContext(Ctx);
  if (!v) throw new Error('useProfilActif doit être utilisé dans <ProfilActifProvider>');
  return v;
}
```

Ensuite, n'importe quel composant sous le fournisseur fait `const { profil, choisir } = useProfilActif();`. Quand `choisir` change le profil, **tous** ceux qui le lisent sont redessinés.

Les limites : un Context ne remplace pas les props (on ne voit plus d'où vient la donnée), et il redessine tous ses lecteurs à chaque changement. On le garde pour quelques données vraiment globales : profil actif, thème, langue, utilisateur connecté.
"""),
  ],
  ["Une donnée = un propriétaire. Les props descendent, les événements remontent par une fonction.",
   "Prop vers un enfant qui s'en sert : normal. Prop qui traverse sans servir : prop drilling.",
   "Frères → remonter le state ; données serveur → le même hook React Query ; mise en page → `children` ; donnée client globale → Context.",
   "Context = `createContext` + un Provider qui possède le state + un hook `useXxx` avec `useContext`.",
   "On prend la solution la plus simple qui marche."],
  [F("features/profils/ProfilActif.tsx", "tsx", r"""
import { createContext, useContext, useState, type ReactNode } from 'react';
import type { Profil } from './types';

type ProfilActif = { profil: Profil | null; choisir: (p: Profil) => void };
const Ctx = createContext<ProfilActif | null>(null);

export function ProfilActifProvider({ children }: { children: ReactNode }) {
  const [profil, setProfil] = useState<Profil | null>(null);
  return <Ctx.Provider value={{ profil, choisir: setProfil }}>{children}</Ctx.Provider>;
}

export function useProfilActif(): ProfilActif {
  const v = useContext(Ctx);
  if (!v) throw new Error('useProfilActif doit être utilisé dans <ProfilActifProvider>');
  return v;
}
"""), F("app/Layout.tsx", "tsx", r"""
import type { ReactNode } from 'react';

// La mise en page ne connaît aucune donnée : elle place ce qu'on lui donne.
export function Layout({ barre, children }: { barre: ReactNode; children: ReactNode }) {
  return (
    <div className="layout">
      <header>{barre}</header>
      <main>{children}</main>
    </div>
  );
}
"""), F("app/App.tsx", "tsx", r"""
import { Layout } from './Layout';
import { ProfilActifProvider, useProfilActif } from '../features/profils';
import { Catalogue } from '../features/catalogue';

function Badge() {
  const { profil } = useProfilActif();        // lu dans le Context, pas reçu en prop
  return <span>{profil ? profil.nom : 'Qui regarde ?'}</span>;
}

export default function App() {
  return (
    <ProfilActifProvider>
      <Layout barre={<Badge />}>
        <Catalogue />                          {/* Catalogue lit aussi useProfilActif() */}
      </Layout>
    </ProfilActifProvider>
  );
}
""")],
  ["`ProfilActif.tsx` regroupe les trois morceaux du Context : `createContext`, le Provider (qui possède le state), le hook.",
   "`Layout` ne reçoit que des éléments (`barre`, `children`) : il ne sait rien des profils.",
   "`Badge` et `Catalogue` lisent le profil actif eux-mêmes : aucune prop ne traverse `Layout`.",
   "Le Provider entoure tout ce qui doit pouvoir lire le profil actif."],
  [
    TD(1, "Remonter le state : deux frères d'accord",
       "Sur la page catalogue, `FiltreGenre` (les boutons de genre) et `Resultats` (la liste filtrée) sont frères. Aujourd'hui chacun a son propre `useState` : cliquer sur un genre ne change pas la liste. Corrige en remontant le state." + JS,
       ["Le genre choisi vit **une seule fois**, dans `PageCatalogue` (`useState<Genre | 'tous'>('tous')`)",
        "`FiltreGenre` reçoit `valeur` et `onChange` en props, et n'a plus de `useState`",
        "`Resultats` reçoit `genre` en prop et filtre la liste `FILMS` avec",
        "Le bouton du genre actif a `aria-pressed=\"true\"`"],
       [F("App.tsx", "tsx", r"""
import { useState } from 'react';

type Genre = 'action' | 'animation' | 'drame';
const FILMS = [
  { id: 1, titre: 'Big Buck Bunny', genre: 'animation' as Genre },
  { id: 3, titre: 'Sintel', genre: 'animation' as Genre },
  { id: 6, titre: 'Agent 327', genre: 'action' as Genre },
  { id: 10, titre: 'La Nuit des projecteurs', genre: 'drame' as Genre },
];
const GENRES: (Genre | 'tous')[] = ['tous', 'action', 'animation', 'drame'];

function FiltreGenre() {
  const [genre, setGenre] = useState<Genre | 'tous'>('tous');
  return (
    <div>
      {GENRES.map((g) => (
        <button key={g} aria-pressed={g === genre} onClick={() => setGenre(g)}>{g}</button>
      ))}
    </div>
  );
}

function Resultats() {
  const [genre] = useState<Genre | 'tous'>('tous');
  const visibles = FILMS.filter((f) => genre === 'tous' || f.genre === genre);
  return <ul>{visibles.map((f) => <li key={f.id}>{f.titre}</li>)}</ul>;
}

export default function PageCatalogue() {
  return (
    <>
      <FiltreGenre />
      <Resultats />
    </>
  );
}
""")],
       ["Dans `PageCatalogue` : `const [genre, setGenre] = useState<Genre | 'tous'>('tous');`",
        "`<FiltreGenre valeur={genre} onChange={setGenre} />` et `<Resultats genre={genre} />`.",
        "Dans `FiltreGenre`, `onClick={() => onChange(g)}` et `aria-pressed={g === valeur}`."],
       [F("App.tsx", "tsx", r"""
import { useState } from 'react';

type Genre = 'action' | 'animation' | 'drame';
const FILMS = [
  { id: 1, titre: 'Big Buck Bunny', genre: 'animation' as Genre },
  { id: 3, titre: 'Sintel', genre: 'animation' as Genre },
  { id: 6, titre: 'Agent 327', genre: 'action' as Genre },
  { id: 10, titre: 'La Nuit des projecteurs', genre: 'drame' as Genre },
];
const GENRES: (Genre | 'tous')[] = ['tous', 'action', 'animation', 'drame'];

function FiltreGenre({ valeur, onChange }: { valeur: Genre | 'tous'; onChange: (g: Genre | 'tous') => void }) {
  return (
    <div>
      {GENRES.map((g) => (
        <button key={g} aria-pressed={g === valeur} onClick={() => onChange(g)}>{g}</button>
      ))}
    </div>
  );
}

function Resultats({ genre }: { genre: Genre | 'tous' }) {
  const visibles = FILMS.filter((f) => genre === 'tous' || f.genre === genre);
  return <ul>{visibles.map((f) => <li key={f.id}>{f.titre}</li>)}</ul>;
}

export default function PageCatalogue() {
  const [genre, setGenre] = useState<Genre | 'tous'>('tous');
  return (
    <>
      <FiltreGenre valeur={genre} onChange={setGenre} />
      <Resultats genre={genre} />
    </>
  );
}
""")],
       ["Un seul useState pour le genre", "Le filtre et la liste sont toujours d'accord"],
       run=RUN("react", entry="App.tsx", tests=r"""
const items = () => $$('li').map((li) => li.textContent);
const btn = (t) => $$('button').find((b) => b.textContent === t);
assert.equal(items().length, 4, 'Au départ : les 4 films');
await click(btn('animation'));
assert.deepEqual(items(), ['Big Buck Bunny', 'Sintel'], 'Clic sur « animation » : la liste est filtrée');
assert.equal(btn('animation').getAttribute('aria-pressed'), 'true', 'Le bouton « animation » est actif');
assert.equal(btn('tous').getAttribute('aria-pressed'), 'false', '« tous » n\'est plus actif');
await click(btn('drame'));
assert.deepEqual(items(), ['La Nuit des projecteurs'], 'Clic sur « drame »');
const src = source('App.tsx');
assert.equal((src.match(/useState/g) || []).length - (/import\s*\{[^}]*useState/.test(src) ? 1 : 0), 1, 'Un seul useState dans tout le fichier (le genre vit à un seul endroit)');
assert(/function\s+FiltreGenre\s*\(\s*\{\s*valeur\s*,\s*onChange/.test(src), 'FiltreGenre reçoit valeur et onChange en props');
""")),
    TD(2, "Composition : Layout ne transmet plus rien",
       "`Page` passe `profil` à `Layout`, qui le passe à `Sidebar`, qui le passe à `Badge`, le seul à s'en servir. Supprime ce prop drilling avec la **composition**." + JS,
       ["`Layout` reçoit `barre` et `children` (de type `ReactNode`) et ne connaît plus `profil`",
        "`Sidebar` disparaît (ou ne reçoit plus `profil`) : la barre est donnée par `Page`",
        "`Page` écrit `<Layout barre={<Badge profil={profil} />}> … </Layout>` avec le contenu principal en `children`",
        "L'affichage reste identique : le badge dans `<aside>`, le titre « Catalogue » dans `<main>`"],
       [F("App.tsx", "tsx", r"""
type Profil = { id: number; nom: string; enfant: boolean };

function Badge({ profil }: { profil: Profil }) {
  return <span className="badge">{profil.nom}{profil.enfant ? ' (enfant)' : ''}</span>;
}

function Sidebar({ profil }: { profil: Profil }) {
  return <aside><Badge profil={profil} /></aside>;
}

function Layout({ profil }: { profil: Profil }) {
  return (
    <div className="layout">
      <Sidebar profil={profil} />
      <main><h1>Catalogue</h1></main>
    </div>
  );
}

function Page({ profil }: { profil: Profil }) {
  return <Layout profil={profil} />;
}

export default function App() {
  return <Page profil={{ id: 2, nom: 'Léo', enfant: true }} />;
}
""")],
       ["`import type { ReactNode } from 'react';`",
        "`function Layout({ barre, children }: { barre: ReactNode; children: ReactNode }) { return <div className=\"layout\"><aside>{barre}</aside><main>{children}</main></div>; }`",
        "`<Layout barre={<Badge profil={profil} />}><h1>Catalogue</h1></Layout>`"],
       [F("App.tsx", "tsx", r"""
import type { ReactNode } from 'react';

type Profil = { id: number; nom: string; enfant: boolean };

function Badge({ profil }: { profil: Profil }) {
  return <span className="badge">{profil.nom}{profil.enfant ? ' (enfant)' : ''}</span>;
}

function Layout({ barre, children }: { barre: ReactNode; children: ReactNode }) {
  return (
    <div className="layout">
      <aside>{barre}</aside>
      <main>{children}</main>
    </div>
  );
}

function Page({ profil }: { profil: Profil }) {
  return (
    <Layout barre={<Badge profil={profil} />}>
      <h1>Catalogue</h1>
    </Layout>
  );
}

export default function App() {
  return <Page profil={{ id: 2, nom: 'Léo', enfant: true }} />;
}
""")],
       ["Layout ne parle plus de profil", "Le badge s'affiche au même endroit"],
       run=RUN("react", entry="App.tsx", tests=r"""
assert.equal(($('aside .badge') || {}).textContent, 'Léo (enfant)', 'Le badge est dans <aside>');
assert.equal(($('main h1') || {}).textContent, 'Catalogue', 'Le titre est dans <main>');
const src = source('App.tsx');
const layout = (src.match(/function\s+Layout[\s\S]*?\n\}/) || [''])[0];
assert(layout, 'Le composant Layout existe toujours');
assert(!/profil/i.test(layout), 'Layout ne mentionne plus profil', layout);
assert(/children/.test(layout), 'Layout affiche ses children');
assert(!/function\s+Sidebar\s*\(\s*\{\s*profil/.test(src), 'Sidebar ne reçoit plus profil');
assert(/<Layout[^>]*barre=\{\s*<Badge/.test(src), 'Page donne le Badge à Layout (prop barre)');
""")),
    TD(3, "Un Context pour le profil actif",
       "Le profil actif sert à trois endroits éloignés : le header, le catalogue (contrôle parental) et le bouton « Changer de profil ». Écris le Context et utilise-le partout, sans aucune prop `profil`." + JS,
       ["`ProfilActif.tsx` : `ProfilActifProvider` (possède le profil actif, au départ `null`) et `useProfilActif()` qui renvoie `{ profil, choisir }` et lève l'erreur « useProfilActif doit être utilisé dans <ProfilActifProvider> » en dehors du fournisseur",
        "`Header` affiche le nom du profil actif, ou « Qui regarde ? » s'il n'y en a pas",
        "`QuiRegarde` affiche un bouton par profil de `PROFILS` ; un clic appelle `choisir(p)`",
        "`Catalogue` n'affiche, pour un profil enfant, que les films avec `ageMinimum <= profil.age`",
        "`App` entoure le tout du Provider ; aucun composant ne reçoit `profil` en prop"],
       [F("ProfilActif.tsx", "tsx", r"""
import { createContext, useContext, useState, type ReactNode } from 'react';

export type Profil = { id: number; nom: string; enfant: boolean; age: number | null };

// à toi : createContext, ProfilActifProvider, useProfilActif

export function ProfilActifProvider({ children }: { children: ReactNode }) {
  return <>{children}</>;
}

export function useProfilActif(): { profil: Profil | null; choisir: (p: Profil) => void } {
  return { profil: null, choisir: () => {} };
}
"""), F("App.tsx", "tsx", r"""
import { ProfilActifProvider, useProfilActif, type Profil } from './ProfilActif';

const PROFILS: Profil[] = [
  { id: 1, nom: 'Ana', enfant: false, age: null },
  { id: 2, nom: 'Léo', enfant: true, age: 8 },
];
const FILMS = [
  { id: 1, titre: 'Big Buck Bunny', ageMinimum: 0 },
  { id: 3, titre: 'Sintel', ageMinimum: 12 },
  { id: 8, titre: 'Charge', ageMinimum: 16 },
];

function Header() {
  // à toi
  return <header>?</header>;
}

function QuiRegarde() {
  // à toi
  return <nav />;
}

function Catalogue() {
  // à toi
  return <ul>{FILMS.map((f) => <li key={f.id}>{f.titre}</li>)}</ul>;
}

export default function App() {
  return (
    <>
      <Header />
      <QuiRegarde />
      <Catalogue />
    </>
  );
}
""")],
       ["`const Ctx = createContext<{ profil: Profil | null; choisir: (p: Profil) => void } | null>(null);`",
        "Dans le Provider : `const [profil, setProfil] = useState<Profil | null>(null);` puis `<Ctx.Provider value={{ profil, choisir: setProfil }}>{children}</Ctx.Provider>`.",
        "Dans le hook : `const v = useContext(Ctx); if (!v) throw new Error('…'); return v;`",
        "Filtre : `FILMS.filter((f) => !profil?.enfant || f.ageMinimum <= (profil.age ?? 0))`."],
       [F("ProfilActif.tsx", "tsx", r"""
import { createContext, useContext, useState, type ReactNode } from 'react';

export type Profil = { id: number; nom: string; enfant: boolean; age: number | null };
type ProfilActif = { profil: Profil | null; choisir: (p: Profil) => void };

const Ctx = createContext<ProfilActif | null>(null);

export function ProfilActifProvider({ children }: { children: ReactNode }) {
  const [profil, setProfil] = useState<Profil | null>(null);
  return <Ctx.Provider value={{ profil, choisir: setProfil }}>{children}</Ctx.Provider>;
}

export function useProfilActif(): ProfilActif {
  const v = useContext(Ctx);
  if (!v) throw new Error('useProfilActif doit être utilisé dans <ProfilActifProvider>');
  return v;
}
"""), F("App.tsx", "tsx", r"""
import { ProfilActifProvider, useProfilActif, type Profil } from './ProfilActif';

const PROFILS: Profil[] = [
  { id: 1, nom: 'Ana', enfant: false, age: null },
  { id: 2, nom: 'Léo', enfant: true, age: 8 },
];
const FILMS = [
  { id: 1, titre: 'Big Buck Bunny', ageMinimum: 0 },
  { id: 3, titre: 'Sintel', ageMinimum: 12 },
  { id: 8, titre: 'Charge', ageMinimum: 16 },
];

function Header() {
  const { profil } = useProfilActif();
  return <header>{profil ? profil.nom : 'Qui regarde ?'}</header>;
}

function QuiRegarde() {
  const { choisir } = useProfilActif();
  return <nav>{PROFILS.map((p) => <button key={p.id} onClick={() => choisir(p)}>{p.nom}</button>)}</nav>;
}

function Catalogue() {
  const { profil } = useProfilActif();
  const visibles = FILMS.filter((f) => !profil?.enfant || f.ageMinimum <= (profil.age ?? 0));
  return <ul>{visibles.map((f) => <li key={f.id}>{f.titre}</li>)}</ul>;
}

export default function App() {
  return (
    <ProfilActifProvider>
      <Header />
      <QuiRegarde />
      <Catalogue />
    </ProfilActifProvider>
  );
}
""")],
       ["Changer de profil met à jour le header et le catalogue", "Le hook refuse d'être utilisé hors du Provider"],
       run=RUN("react", entry="App.tsx", tests=r"""
const films = () => $$('li').map((li) => li.textContent);
const btn = (t) => $$('button').find((b) => b.textContent === t);
const head = () => ($('header') || {}).textContent;
assert.equal(head(), 'Qui regarde ?', 'Aucun profil actif : « Qui regarde ? »');
assert.equal(films().length, 3, 'Sans profil : les 3 films');
await click(btn('Léo'));
assert.equal(head(), 'Léo', 'Clic sur Léo : le header affiche Léo');
assert.deepEqual(films(), ['Big Buck Bunny'], 'Léo (8 ans) : seulement les films pour son âge');
await click(btn('Ana'));
assert.equal(head(), 'Ana', 'Clic sur Ana : le header suit');
assert.equal(films().length, 3, 'Ana (adulte) : les 3 films');
const { useProfilActif } = require('./ProfilActif');
let msg = '';
const R = require('react'); const RD = require('react-dom/client');
function Dehors() { try { useProfilActif(); } catch (e) { msg = e.message; } return null; }
const div = document.createElement('div'); const r = RD.createRoot(div); r.render(R.createElement(Dehors)); await tick(150); r.unmount();
assert.includes(msg, 'useProfilActif doit être utilisé dans <ProfilActifProvider>', 'Hors du Provider : erreur claire');
const src = source('App.tsx');
assert(!/profil=\{/.test(src), 'Aucun composant ne reçoit profil en prop');
assert(/<ProfilActifProvider>/.test(src), 'App entoure le tout du Provider');
""")),
  ])

MODULES = [dossiers, props]

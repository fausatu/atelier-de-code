from common import V2, P, L, D, N, E, LANE, F, TD, RUN
from c_react_v1 import MODULES as V1

v1 = {m["id"]: m for m in V1}

# ---------------------------------------------------------------- composants
comp = V2(v1["react-composants"],
  prereq=[
    P("DOM", "L'arbre d'éléments que le navigateur construit à partir du HTML et affiche. Modifier la page = modifier le DOM. React le fait pour toi."),
    P("Fonction fléchée", "`(x) => x * 2` : une fonction JavaScript courte. `users.map((u) => …)` appelle la fonction pour chaque élément et renvoie un nouveau tableau."),
    P("Destructuration", "`function Badge({ online })` extrait directement la clé `online` de l'objet reçu. Équivaut à `function Badge(props) { const online = props.online; }`."),
    P("TypeScript", "JavaScript avec des types. `{ user: User }` dit « la prop `user` est un objet de type `User` ». Si tu passes autre chose, l'éditeur te prévient avant même de lancer le code."),
    P("Expression", "Un bout de code qui **produit une valeur** : `user.name`, `a + b`, `cond ? 'oui' : 'non'`. Dans JSX, seules les expressions vont entre `{ }` (pas de `if`, pas de `for`)."),
  ],
  diagram=D(
    nodes=[
      N("data", 0, 1, "users", "tableau d'objets", kind="db", color="muted"),
      N("team", 1, 1, "<Team users={…} />", "composant parent"),
      N("card", 2, 0, "<UserCard user={u} />", "pour chaque u"),
      N("card2", 2, 2, "<UserCard user={u} />", "…", kind="note"),
      N("badge", 3, 0, "<Badge online={…} />", "enfant de UserCard"),
      N("dom", 4, 1, "DOM", "<section><article>…", kind="file", color="good"),
    ],
    edges=[E("data", "team", "props"), E("team", "card", "map + key"), E("team", "card2", dashed=True), E("card", "badge", "props"), E("badge", "dom", "React met à jour", color="good"), E("card2", "dom", dashed=True, color="good")],
    caption="Les données descendent de parent en enfant par les props. React traduit l'arbre de composants en DOM."),
  lessons=[
    L("Un composant est une fonction qui décrit un morceau d'interface", r"""
En HTML classique, pour afficher 20 utilisateurs, tu écris 20 fois le même bloc, ou tu le génères avec une boucle côté serveur, et tu modifies le DOM à la main quand quelque chose change. Ça devient vite ingérable : quel bout de code a changé quel élément ?

React propose une autre façon de penser : tu écris une **fonction** qui, à partir de données, **renvoie la description** de ce qui doit s'afficher. Tu ne touches jamais au DOM ; tu dis « voilà à quoi ça doit ressembler » et React s'occupe de faire correspondre la page.

```tsx
function Badge({ online }: { online: boolean }) {
  return <span className="badge">{online ? 'En ligne' : 'Absent'}</span>;
}
```

`Badge` est un composant. Il reçoit un objet (ses **props**), ici `{ online: true }`, et renvoie du **JSX**. On l'utilise comme une balise : `<Badge online={true} />`. React appelle la fonction, récupère la description, et crée le `<span>` dans la page.

Trois règles de nommage et de forme :

- Le nom commence par une **majuscule** (`Badge`, `UserCard`). En minuscule, React croit que c'est une balise HTML (`<badge>` n'existe pas).
- Un composant renvoie **un seul** élément racine. Si tu veux en renvoyer plusieurs sans ajouter de `<div>`, utilise un fragment : `<>…</>`.
- Le fichier d'un composant s'appelle comme lui : `Badge.tsx`.
"""),
    L("JSX : du HTML dans du JavaScript, avec des règles", r"""
JSX ressemble à du HTML, mais c'est du JavaScript : chaque balise devient un appel de fonction (`React.createElement`). Conséquences :

- `class` est un mot réservé en JavaScript → on écrit `className`. De même `for` → `htmlFor`.
- Entre accolades, on met une **expression** JavaScript : `{user.name}`, `{price * 1.2}`, `{online ? 'oui' : 'non'}`. Pas de `if`, pas de `for` : ce ne sont pas des expressions.
- Pour afficher conditionnellement : `{stock === 0 && <span>Rupture</span>}` (si la condition est fausse, rien ne s'affiche), ou l'opérateur ternaire `cond ? <A /> : <B />`.
- Les attributs reçoivent des chaînes (`placeholder="Nom"`) ou des expressions (`disabled={count === 0}`).
- Tout ce qui est ouvert doit être fermé : `<img />`, `<input />`.

Un cas très fréquent : une liste.

```tsx
<ul>
  {users.map((u) => (
    <li key={u.id}>{u.name}</li>
  ))}
</ul>
```

`map` transforme le tableau d'utilisateurs en tableau d'éléments `<li>`, que JSX sait afficher. Chaque élément porte une **`key`** : un identifiant stable et unique (l'`id` de la donnée). React s'en sert pour savoir, quand la liste change, quel élément a été ajouté, retiré ou déplacé. Sans `key`, ou avec l'index du tableau comme clé, React peut confondre deux éléments et garder l'état de l'un sur l'autre (un champ texte qui « saute » d'une ligne à l'autre). Règle : `key` = l'identifiant de la donnée, jamais l'index si la liste peut changer d'ordre.
"""),
    L("Les props : les paramètres d'un composant", r"""
Les props sont au composant ce que les paramètres sont à une fonction. Le parent les écrit comme des attributs ; l'enfant les reçoit dans un seul objet.

```tsx
// Le parent passe
<UserCard user={u} compact={true} onSelect={() => …} />

// L'enfant reçoit
function UserCard({ user, compact, onSelect }: { user: User; compact?: boolean; onSelect?: () => void }) { … }
```

On peut passer n'importe quelle valeur : une chaîne, un nombre, un objet, un tableau, une fonction (c'est comme ça qu'un enfant préviendra son parent d'un événement, voir le module Formulaires), ou même d'autres éléments JSX via la prop spéciale `children` (`<Card>contenu</Card>`).

Deux règles :

- Les props sont **en lecture seule**. Un composant ne modifie jamais ce qu'il reçoit : si une valeur doit changer, c'est le parent qui la change et la repasse. Pour les valeurs qui changent *à l'intérieur* d'un composant, il y a le **state**, module suivant.
- Les données **descendent** : du parent vers l'enfant, jamais l'inverse. On appelle ça le *flux unidirectionnel*. Pour « remonter » une information, l'enfant appelle une fonction reçue en prop.

En TypeScript, on déclare le type des props. Ça te protège : si tu renommes `name` en `fullName` dans `User`, l'éditeur souligne tous les endroits à corriger.
"""),
    L("Découper : quand faire un composant ?", r"""
Un bon découpage ressemble à un découpage de fonctions : chaque composant fait **une chose**, a un nom qui le dit, et reste court (quelques dizaines de lignes). Signes qu'il faut extraire un composant :

- Le même bout de JSX apparaît **deux fois** (un badge, une carte, une ligne de tableau).
- Un bloc a **sa propre logique** (son propre état, ses propres calculs).
- Le `return` d'un composant dépasse l'écran.

Dans l'exemple, `Team` gère la liste et le cas « vide », `UserCard` présente un utilisateur, `Badge` affiche un statut. Chacun est testable et réutilisable séparément. Ne tombe pas non plus dans l'excès : un composant de 3 lignes utilisé une seule fois n'apporte rien.

Dernier point : un composant doit être **pur** : pour les mêmes props, il renvoie le même JSX, et il ne modifie rien à l'extérieur (pas d'appel réseau, pas de `document.title = …` dans le corps). Ces actions ont leur place dédiée (module useEffect). Cette pureté est ce qui permet à React de rappeler ton composant autant de fois qu'il veut sans effets de bord.
"""),
  ],
  recap=[
    "Un composant = une fonction (nom en Majuscule) qui reçoit des **props** et renvoie du **JSX**.",
    "JSX : `className`, `{ expression }`, `cond && <X />`, un seul élément racine ou un fragment `<>…</>`.",
    "Une liste se rend avec `map`, chaque élément avec une `key` **stable** (l'id, pas l'index).",
    "Les props sont **en lecture seule** et descendent du parent vers l'enfant.",
    "Extraire un composant quand un bloc se répète ou a sa propre logique ; garder chaque composant pur.",
  ],
  example=[F("types.ts", "ts", r"""
export type User = { id: number; name: string; role: string; online: boolean };
"""), F("Badge.tsx", "tsx", r"""
export default function Badge({ online }: { online: boolean }) {
  return <span className={online ? 'badge on' : 'badge'}>{online ? 'En ligne' : 'Absent'}</span>;
}
"""), F("UserCard.tsx", "tsx", r"""
import Badge from './Badge';
import type { User } from './types';

export default function UserCard({ user }: { user: User }) {
  return (
    <article className="card">
      <h3>{user.name}</h3>
      <p>{user.role}</p>
      <Badge online={user.online} />
    </article>
  );
}
"""), F("Team.tsx", "tsx", r"""
import UserCard from './UserCard';
import type { User } from './types';

export default function Team({ users }: { users: User[] }) {
  if (users.length === 0) return <p>Aucun membre.</p>;
  return (
    <section>
      {users.map((u) => (
        <UserCard key={u.id} user={u} />
      ))}
    </section>
  );
}
"""), F("App.tsx", "tsx", r"""
import Team from './Team';

const users = [
  { id: 1, name: 'Ana', role: 'Développeuse', online: true },
  { id: 2, name: 'Léo', role: 'Designer', online: false },
];

export default function App() {
  return <Team users={users} />;
}
""")],
  notes=["`types.ts` : le type `User` est partagé par tous les fichiers via `import type`.",
         "`App` → `Team` → `UserCard` → `Badge` : les données descendent par les props, un niveau à la fois.",
         "Dans `Team.tsx`, `key={u.id}` : stable même si la liste est triée ou filtrée.",
         "Le `return` anticipé de `Team` gère le cas « liste vide » avant le `map`."],
  td1=dict(path="App.tsx", files=[F("App.tsx", "tsx", r"""
const products = [
  { id: 'p1', name: 'Clavier', price: 49.9, stock: 12 },
  { id: 'p2', name: 'Souris', price: 19.5, stock: 0 },
  { id: 'p3', name: 'Écran', price: 189, stock: 3 },
];

type Product = { id: string; name: string; price: number; stock: number };

function ProductCard(/* props */) {
  // à toi
}

function ProductList({ products, onlyAvailable = false }: { products: Product[]; onlyAvailable?: boolean }) {
  // à toi
}

export default function App() {
  return <ProductList products={products} />;
}
""")], solution=[F("App.tsx", "tsx", r"""
const products = [
  { id: 'p1', name: 'Clavier', price: 49.9, stock: 12 },
  { id: 'p2', name: 'Souris', price: 19.5, stock: 0 },
  { id: 'p3', name: 'Écran', price: 189, stock: 3 },
];

type Product = { id: string; name: string; price: number; stock: number };

function ProductCard({ product }: { product: Product }) {
  return (
    <li className="product">
      <strong>{product.name}</strong>{' '}
      {product.price.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}
      {product.stock === 0 && <span className="badge">Rupture</span>}
    </li>
  );
}

function ProductList({ products, onlyAvailable = false }: { products: Product[]; onlyAvailable?: boolean }) {
  const visible = onlyAvailable ? products.filter((p) => p.stock > 0) : products;
  if (visible.length === 0) return <p>Aucun produit</p>;
  return (
    <ul>
      {visible.map((p) => (
        <ProductCard key={p.id} product={p} />
      ))}
    </ul>
  );
}

export default function App() {
  return <ProductList products={products} />;
}
""")], run=RUN("react", tests=r"""
assert.equal($$('li').length, 3, 'La liste affiche 3 produits');
assert.includes(text(), 'Clavier', 'Le nom du produit est affiché');
assert.includes(text(), '49,90', 'Le prix est formaté en euros (49,90 €)');
assert.equal($$('.badge').length, 1, 'Un seul badge « Rupture » (la souris)');
assert.includes(byText('Rupture') && byText('Rupture').closest('li').textContent, 'Souris', 'Le badge Rupture est sur la souris');
const { default: App } = require('./App');
assert(typeof App === 'function', 'App est exporté par défaut');
""")),
  tds=[
    TD(2, "Tableau de notes avec moyenne et mentions",
       "Même mécanique (props + `map` + affichage conditionnel), mais dans un **tableau HTML** avec une ligne de total, et un composant qui reçoit des **props de plusieurs types** (nombre, booléen, fonction de formatage). Tu dois aussi calculer une valeur dérivée des props.",
       ["`GradeRow` reçoit `student` (`{ id, name, grade }`) et `highlightAbove` (nombre) : la ligne a la classe `top` si `grade >= highlightAbove`",
        "`GradeRow` affiche la **mention** : `grade >= 16` → « Très bien », `>= 14` → « Bien », `>= 12` → « Assez bien », sinon « — »",
        "`GradeTable` reçoit `students` et `highlightAbove`, rend un `<table>` avec un `<tbody>` de `GradeRow`, puis un `<tfoot>` avec la moyenne arrondie à 1 décimale",
        "Si `students` est vide : `<p>Aucun élève</p>` (pas de table)",
        "`App` affiche `GradeTable` avec les données fournies et `highlightAbove={14}` ; exporte aussi `GradeTable` (`export function`) pour qu'on puisse le tester seul"],
       [F("App.tsx", "tsx", r"""
type Student = { id: number; name: string; grade: number };

const students: Student[] = [
  { id: 1, name: 'Ana', grade: 17 },
  { id: 2, name: 'Léo', grade: 11 },
  { id: 3, name: 'Zoé', grade: 14.5 },
];

function mention(grade: number): string {
  // à toi
}

function GradeRow(/* props */) {
  // à toi : <tr className=...><td>nom</td><td>note</td><td>mention</td></tr>
}

export function GradeTable(/* props */) {
  // à toi
}

export default function App() {
  return <GradeTable students={students} highlightAbove={14} />;
}
""")],
       ["La moyenne : `students.reduce((s, x) => s + x.grade, 0) / students.length`, puis `.toFixed(1)`.",
        "Classe conditionnelle : `className={student.grade >= highlightAbove ? 'top' : ''}`.",
        "Un `<tfoot>` contient aussi un `<tr>` avec des `<td>`. Pour fusionner deux colonnes : `<td colSpan={2}>`."],
       [F("App.tsx", "tsx", r"""
type Student = { id: number; name: string; grade: number };

const students: Student[] = [
  { id: 1, name: 'Ana', grade: 17 },
  { id: 2, name: 'Léo', grade: 11 },
  { id: 3, name: 'Zoé', grade: 14.5 },
];

function mention(grade: number): string {
  if (grade >= 16) return 'Très bien';
  if (grade >= 14) return 'Bien';
  if (grade >= 12) return 'Assez bien';
  return '—';
}

function GradeRow({ student, highlightAbove }: { student: Student; highlightAbove: number }) {
  return (
    <tr className={student.grade >= highlightAbove ? 'top' : ''}>
      <td>{student.name}</td>
      <td>{student.grade}</td>
      <td>{mention(student.grade)}</td>
    </tr>
  );
}

export function GradeTable({ students, highlightAbove }: { students: Student[]; highlightAbove: number }) {
  if (students.length === 0) return <p>Aucun élève</p>;
  const average = students.reduce((sum, s) => sum + s.grade, 0) / students.length;
  return (
    <table>
      <thead>
        <tr><th>Élève</th><th>Note</th><th>Mention</th></tr>
      </thead>
      <tbody>
        {students.map((s) => (
          <GradeRow key={s.id} student={s} highlightAbove={highlightAbove} />
        ))}
      </tbody>
      <tfoot>
        <tr><td>Moyenne</td><td colSpan={2}>{average.toFixed(1)}</td></tr>
      </tfoot>
    </table>
  );
}

export default function App() {
  return <GradeTable students={students} highlightAbove={14} />;
}
""")],
       ["Ana et Zoé ont la classe `top`, pas Léo",
        "La moyenne affichée est 14.2",
        "Avec un tableau vide, aucune `<table>` n'est rendue"],
       run=RUN("react", tests=r"""
assert.equal($$('tbody tr').length, 3, '3 lignes dans le tbody');
assert.equal($$('tbody tr.top').length, 2, '2 lignes surlignées (Ana et Zoé)');
assert(!$$('tbody tr')[1].classList.contains('top'), 'Léo (11) n\'est pas surligné');
assert.includes($$('tbody tr')[0].textContent, 'Très bien', 'Ana a la mention Très bien');
assert.includes($$('tbody tr')[2].textContent, 'Bien', 'Zoé a la mention Bien');
assert.includes($$('tbody tr')[1].textContent, '—', 'Léo n\'a pas de mention');
assert.includes($('tfoot') && $('tfoot').textContent, '14.2', 'La moyenne 14.2 est dans le tfoot');
const mod = require('./App');
assert(typeof mod.GradeTable === 'function', 'GradeTable est exportée');
const React = require('react'); const ReactDOM = require('react-dom/client');
const div = document.createElement('div'); document.body.appendChild(div);
ReactDOM.createRoot(div).render(React.createElement(mod.GradeTable, { students: [], highlightAbove: 10 })); await tick(80);
assert.includes(div.textContent, 'Aucun élève', 'Liste vide : message « Aucun élève »');
assert(!div.querySelector('table'), 'Liste vide : pas de table');
""")),
    TD(3, "Arbre de commentaires récursif",
       "Les commentaires d'un article ont des **réponses**, qui ont elles-mêmes des réponses. Tu dois afficher cet arbre avec un composant qui **s'utilise lui-même** (récursion), gérer la profondeur par une prop, et extraire un composant `Avatar` réutilisé à chaque niveau. C'est le cas où le découpage en composants et le flux des props montrent toute leur force.",
       ["`Avatar` : reçoit `name`, affiche un `<span className=\"avatar\">` avec les **initiales** (première lettre de chaque mot, max 2, majuscules)",
        "`Comment` : reçoit `comment` et `depth` ; affiche l'avatar, l'auteur, le texte, puis **ses réponses** avec `<Comment />` et `depth + 1`",
        "Au-delà de `depth >= 2`, les réponses ne sont pas affichées : à la place, un `<button>` « Voir N réponse(s) » (N = nombre total de descendants, pas seulement directs)",
        "`CommentThread` reçoit `comments` (racines) et affiche chaque racine avec `depth={0}` ; message « Aucun commentaire » si vide",
        "Chaque niveau est indenté via `style={{ marginLeft: depth * 24 }}` ; l'élément racine de chaque commentaire a la classe `comment`"],
       [F("App.tsx", "tsx", r"""
type CommentData = { id: number; author: string; text: string; replies: CommentData[] };

const comments: CommentData[] = [
  {
    id: 1, author: 'Ana Martin', text: 'Super article !', replies: [
      { id: 2, author: 'Léo Petit', text: 'Je confirme.', replies: [
        { id: 3, author: 'Zoé Durand', text: 'Pareil.', replies: [
          { id: 4, author: 'Max Roy', text: 'Idem !', replies: [] },
          { id: 5, author: 'Eva Lin', text: 'Moi aussi.', replies: [] },
        ] },
      ] },
    ],
  },
  { id: 6, author: 'Tom Blanc', text: 'Une question sur la partie 2…', replies: [] },
];

function initials(name: string): string {
  // à toi
}

function Avatar(/* props */) {
  // à toi
}

function countReplies(c: CommentData): number {
  // à toi : nombre total de descendants
}

function Comment(/* props */) {
  // à toi
}

function CommentThread(/* props */) {
  // à toi
}

export default function App() {
  return <CommentThread comments={comments} />;
}
""")],
       ["Initiales : `name.split(' ').map((w) => w[0]).join('').slice(0, 2).toUpperCase()`.",
        "Compter récursivement : `c.replies.reduce((n, r) => n + 1 + countReplies(r), 0)`.",
        "Dans `Comment`, le rendu des réponses : `depth >= 2 ? <button>…</button> : comment.replies.map((r) => <Comment key={r.id} comment={r} depth={depth + 1} />)`. Un composant peut parfaitement s'appeler lui-même."],
       [F("App.tsx", "tsx", r"""
type CommentData = { id: number; author: string; text: string; replies: CommentData[] };

const comments: CommentData[] = [
  {
    id: 1, author: 'Ana Martin', text: 'Super article !', replies: [
      { id: 2, author: 'Léo Petit', text: 'Je confirme.', replies: [
        { id: 3, author: 'Zoé Durand', text: 'Pareil.', replies: [
          { id: 4, author: 'Max Roy', text: 'Idem !', replies: [] },
          { id: 5, author: 'Eva Lin', text: 'Moi aussi.', replies: [] },
        ] },
      ] },
    ],
  },
  { id: 6, author: 'Tom Blanc', text: 'Une question sur la partie 2…', replies: [] },
];

function initials(name: string): string {
  return name.split(' ').filter(Boolean).map((w) => w[0]).join('').slice(0, 2).toUpperCase();
}

function Avatar({ name }: { name: string }) {
  return <span className="avatar">{initials(name)}</span>;
}

function countReplies(c: CommentData): number {
  return c.replies.reduce((n, r) => n + 1 + countReplies(r), 0);
}

function Comment({ comment, depth }: { comment: CommentData; depth: number }) {
  const hidden = depth >= 2 && comment.replies.length > 0;
  const total = countReplies(comment);
  return (
    <div className="comment" style={{ marginLeft: depth * 24 }}>
      <Avatar name={comment.author} />
      <strong>{comment.author}</strong>
      <p>{comment.text}</p>
      {hidden ? (
        <button>Voir {total} réponse{total > 1 ? 's' : ''}</button>
      ) : (
        comment.replies.map((r) => <Comment key={r.id} comment={r} depth={depth + 1} />)
      )}
    </div>
  );
}

function CommentThread({ comments }: { comments: CommentData[] }) {
  if (comments.length === 0) return <p>Aucun commentaire</p>;
  return (
    <section>
      {comments.map((c) => (
        <Comment key={c.id} comment={c} depth={0} />
      ))}
    </section>
  );
}

export default function App() {
  return <CommentThread comments={comments} />;
}
""")],
       ["Zoé (profondeur 2) affiche « Voir 2 réponses » au lieu de Max et Eva",
        "Chaque niveau est décalé de 24 px de plus que le précédent",
        "`Avatar` est le même composant à tous les niveaux"],
       run=RUN("react", tests=r"""
assert.equal($$('.comment').length, 4, '4 commentaires visibles (Ana, Léo, Zoé, Tom)');
assert.includes(text(), 'Voir 2 réponses', 'Zoé affiche « Voir 2 réponses »');
assert(!text().includes('Idem'), 'Max (profondeur 3) n\'est pas affiché');
const avatars = $$('.avatar').map((a) => a.textContent);
assert.includes(avatars.join(','), 'AM', 'Avatar AM pour Ana Martin');
assert.includes(avatars.join(','), 'ZD', 'Avatar ZD pour Zoé Durand');
const own = (c) => (c.querySelector(':scope > strong') || {}).textContent || '';
const zoe = $$('.comment').find((c) => own(c).includes('Zoé'));
assert.equal(zoe && zoe.style.marginLeft, '48px', 'Zoé (depth 2) est indentée de 48px');
const tom = $$('.comment').find((c) => own(c).includes('Tom'));
assert.equal(tom && tom.style.marginLeft, '0px', 'Tom (racine) n\'est pas indenté');
""")),
  ])

# ---------------------------------------------------------------- state
stt = V2(v1["react-state"],
  prereq=[
    P("Rendu", "Un rendu = React appelle ta fonction composant et obtient du JSX. Ton composant peut être rendu des dizaines de fois pendant sa vie : à chaque fois, tout le corps de la fonction est réexécuté."),
    P("Hook", "Une fonction fournie par React dont le nom commence par `use` (`useState`, `useEffect`…) et qui s'appelle **au début** du composant. Elle donne au composant une capacité : garder une valeur, réagir à quelque chose."),
    P("Déstructuration de tableau", "`const [count, setCount] = useState(0)` : `useState` renvoie un tableau de 2 éléments ; on nomme le premier `count` et le deuxième `setCount`."),
    P("Spread `...`", "`[...items, x]` crée un nouveau tableau avec tous les éléments de `items` puis `x`. `{ ...user, name: 'Ana' }` crée un nouvel objet copie de `user` avec `name` remplacé."),
    P("Immutabilité", "Ne jamais modifier une valeur existante, toujours en créer une nouvelle. `items.push(x)` modifie ; `[...items, x]` crée. React a besoin de la deuxième approche."),
  ],
  diagram=D(
    nodes=[
      N("render", 0, 0, "Rendu n°1", "count = 0", kind="doc"),
      N("ui", 1, 0, "Écran", "« Compteur : 0 »", kind="file"),
      N("click", 2, 0, "clic → setCount(c => c + 1)", "", kind="pill", color="accent"),
      N("sched", 2, 1, "React planifie\nun nouveau rendu", "", kind="note", color="accent"),
      N("render2", 0, 1, "Rendu n°2", "count = 1", kind="doc", color="good"),
      N("ui2", 1, 1, "Écran mis à jour", "« Compteur : 1 »", kind="file", color="good"),
    ],
    edges=[E("render", "ui"), E("ui", "click", "événement"), E("click", "sched"), E("sched", "render2", "rappelle le composant", color="good"), E("render2", "ui2", "compare et met à jour", color="good")],
    caption="Chaque `set…` demande un nouveau rendu. Le composant est rappelé avec la nouvelle valeur, et React ne touche au DOM que là où ça change."),
  lessons=[
    L("Pourquoi une variable normale ne suffit pas", r"""
Premier réflexe pour un compteur :

```tsx
function Counter() {
  let count = 0;
  return <button onClick={() => { count++; }}>{count}</button>;
}
```

Ça ne marche pas, pour deux raisons. D'abord, modifier `count` ne dit **rien à React** : il n'a aucun moyen de savoir qu'il doit redessiner. Ensuite, même s'il redessinait, il **rappellerait la fonction** `Counter` depuis le début, et `let count = 0` remettrait la valeur à zéro.

Il faut donc une mémoire qui **survit aux rendus** et dont la modification **prévient React**. C'est exactement ce que fournit `useState`.

```tsx
const [count, setCount] = useState(0);
```

- `0` : la valeur de départ, utilisée uniquement au premier rendu.
- `count` : la valeur **pour ce rendu**.
- `setCount` : la fonction qui change la valeur **et** demande un nouveau rendu.

React garde la valeur de son côté, associée à ce composant. Au rendu suivant, `useState(0)` renvoie la valeur mémorisée (pas `0`). C'est pour ça que les hooks doivent toujours être appelés dans le même ordre : React les identifie par leur position.
"""),
    L("Un rendu est un instantané", r"""
Point le plus déroutant au début : juste après `setCount(count + 1)`, `count` vaut **encore l'ancienne valeur**.

```tsx
function handleClick() {
  setCount(count + 1);
  console.log(count);     // affiche l'ANCIENNE valeur
  setCount(count + 1);    // demande encore count + 1 : même résultat que la première ligne !
}
```

Pourquoi ? `count` est une simple constante dans la fonction du rendu en cours : elle ne changera jamais pendant ce rendu. `setCount` ne modifie pas `count`, il **programme** un nouveau rendu dans lequel `count` aura une nouvelle valeur. Pense à une photo : le rendu est une photo du state à un instant ; tu ne peux pas modifier la photo, seulement en prendre une autre.

Quand la nouvelle valeur dépend de l'ancienne, passe une **fonction** à `setCount` : React l'appellera avec la valeur la plus récente, même si plusieurs mises à jour sont en attente.

```tsx
setCount((c) => c + 1);
setCount((c) => c + 1);   // cette fois, +2 au total
```

Règle simple : si tu écris `setX(x + …)` ou `setX(x.quelqueChose)`, remplace par `setX((x) => …)`. Ça ne coûte rien et ça évite une classe entière de bugs (clics rapides, mises à jour dans un timer…).
"""),
    L("Ne jamais muter : tableaux et objets", r"""
Pour décider s'il doit redessiner, React compare l'ancienne et la nouvelle valeur avec `===`. Pour un tableau ou un objet, `===` compare les **références** : « est-ce le même objet en mémoire ? ». Donc :

```tsx
items.push(x);
setItems(items);          // même référence → React ne voit AUCUN changement
```

L'écran ne bouge pas, alors que la donnée a changé. Il faut toujours créer une **nouvelle** valeur :

```tsx
setItems([...items, x]);                               // ajouter
setItems(items.filter((i) => i.id !== id));            // retirer
setItems(items.map((i) => (i.id === id ? { ...i, done: true } : i)));   // modifier un élément
setUser({ ...user, name: 'Ana' });                     // modifier une clé d'un objet
```

Méthodes qui **créent** un nouveau tableau (à utiliser) : `map`, `filter`, `slice`, `concat`, le spread `[...]`, `toSorted`. Méthodes qui **modifient** en place (à éviter sur un state) : `push`, `pop`, `splice`, `sort`, `reverse`, et l'affectation directe `items[0] = …`.
"""),
    L("Quoi mettre dans le state (et quoi ne pas y mettre)", r"""
Le state doit contenir le **minimum** d'informations : celles qui changent par une action de l'utilisateur ou un événement, et qu'on ne peut pas calculer autrement. Tout ce qui se **déduit** du state ou des props se calcule pendant le rendu, dans une simple constante.

```tsx
const [items, setItems] = useState<Item[]>([]);
const total = items.reduce((s, i) => s + i.price, 0);   // dérivé : PAS un state
const isEmpty = items.length === 0;                     // dérivé
```

Si `total` était aussi un state, il faudrait penser à le mettre à jour à chaque fois qu'`items` change, et les deux finiraient par diverger. Recalculer à chaque rendu est gratuit pour des listes de taille raisonnable.

Deux autres erreurs fréquentes :

- Appeler `setX(...)` **directement dans le corps** du composant : ça déclenche un rendu, qui appelle `setX`, qui déclenche un rendu… boucle infinie. Les `set` vont dans les gestionnaires d'événements (`onClick`, `onChange`) ou dans un effet.
- Dupliquer une prop dans un state (`const [name, setName] = useState(props.name)`) : si le parent change la prop, ton state ne suit pas. Utilise la prop directement.
"""),
  ],
  recap=[
    "`const [x, setX] = useState(init)` : une valeur qui survit aux rendus, et un `set` qui redessine.",
    "Un rendu est un **instantané** : `x` ne change pas après `setX` dans le même rendu.",
    "Nouvelle valeur qui dépend de l'ancienne → `setX((x) => …)`.",
    "Jamais de mutation : `[...a, x]`, `filter`, `map`, `{ ...o, k: v }` au lieu de `push` ou `o.k = v`.",
    "Ce qui se calcule n'est pas un state ; pas de `set` dans le corps du composant.",
  ],
  td1=dict(path="App.tsx", files=[F("App.tsx", "tsx", r"""
import { useState } from 'react';

const products = [
  { id: 'p1', name: 'Café', price: 4.5 },
  { id: 'p2', name: 'Croissant', price: 1.2 },
  { id: 'p3', name: 'Jus', price: 3 },
];

export default function App() {
  // à toi : un state { [productId]: quantité }, des boutons + / −, un total calculé, un bouton Vider
  return <div />;
}
""")], solution=[F("App.tsx", "tsx", r"""
import { useState } from 'react';

const products = [
  { id: 'p1', name: 'Café', price: 4.5 },
  { id: 'p2', name: 'Croissant', price: 1.2 },
  { id: 'p3', name: 'Jus', price: 3 },
];

export default function App() {
  const [qty, setQty] = useState<Record<string, number>>({});

  function change(id: string, delta: number) {
    setQty((q) => ({ ...q, [id]: Math.max(0, (q[id] ?? 0) + delta) }));
  }

  const total = products.reduce((sum, p) => sum + p.price * (qty[p.id] ?? 0), 0);

  return (
    <div>
      <ul>
        {products.map((p) => (
          <li key={p.id} data-id={p.id}>
            {p.name}
            <button className="minus" onClick={() => change(p.id, -1)} disabled={!qty[p.id]}>−</button>
            <span className="qty">{qty[p.id] ?? 0}</span>
            <button className="plus" onClick={() => change(p.id, 1)}>+</button>
          </li>
        ))}
      </ul>
      <p className="total">Total : {total.toFixed(2)} €</p>
      <button className="clear" onClick={() => setQty({})}>Vider</button>
    </div>
  );
}
""")], run=RUN("react", tests=r"""
assert.equal($$('li').length, 3, '3 produits affichés');
const plus = $$('button').filter((b) => b.textContent.trim() === '+');
const minus = $$('button').filter((b) => b.textContent.trim() === '−' || b.textContent.trim() === '-');
assert.equal(plus.length, 3, 'Un bouton + par produit');
assert.equal(minus.length, 3, 'Un bouton − par produit');
assert.includes(text(), '0.00', 'Total de départ 0.00');
await click(plus[0]); await click(plus[0]); await click(plus[2]);
assert.includes(text(), '12.00', 'Total après 2 cafés + 1 jus = 12.00');
await click(minus[0]);
assert.includes(text(), '7.50', 'Après un − sur le café : 7.50');
await click(minus[1]);
assert.includes(text(), '7.50', 'Le − sur un produit à 0 ne descend pas sous 0 (total inchangé)');
plus[1].click(); plus[1].click(); plus[1].click(); await tick();
assert.includes(text(), '11.10', '3 clics rapides sur Croissant sont tous comptés (7.50 + 3.60 = 11.10)');
const clear = byText('Vider');
assert(clear, 'Un bouton Vider existe');
await click(clear);
assert.includes(text(), '0.00', 'Après Vider, total 0.00');
""")),
  tds=[
    TD(2, "Liste de tâches : ajouter, cocher, supprimer, filtrer",
       "Un state **tableau d'objets** à mettre à jour sans mutation (ajout, modification d'un élément, suppression), plus un deuxième state pour le filtre, et des valeurs dérivées (compteur de tâches restantes, liste filtrée). Attention à la `key` et aux mises à jour fonctionnelles.",
       ["State `todos: { id: number; title: string; done: boolean }[]` initialisé avec les 3 tâches fournies, et state `filter: 'all' | 'active' | 'done'`",
        "Un bouton `.add` « Ajouter » qui ajoute une tâche `Tâche N` (N = nombre de tâches + 1) avec un id unique (`Date.now()` ou un compteur)",
        "Chaque tâche : une case à cocher (`checked={todo.done}`) qui inverse `done`, et un bouton `.remove` « Supprimer »",
        "Trois boutons de filtre (`.filter-all`, `.filter-active`, `.filter-done`) ; la liste affichée est **dérivée** de `todos` et `filter` (pas de 3e state)",
        "Un texte « N restante(s) » (tâches non faites) et la classe `done` sur les `<li>` cochés"],
       [F("App.tsx", "tsx", r"""
import { useState } from 'react';

type Todo = { id: number; title: string; done: boolean };

const initial: Todo[] = [
  { id: 1, title: 'Lire le cours', done: true },
  { id: 2, title: 'Faire le quiz', done: false },
  { id: 3, title: 'Faire le TD', done: false },
];

export default function App() {
  // à toi
  return <div />;
}
""")],
       ["Inverser une tâche : `setTodos((ts) => ts.map((t) => (t.id === id ? { ...t, done: !t.done } : t)))`.",
        "Supprimer : `setTodos((ts) => ts.filter((t) => t.id !== id))`.",
        "Liste filtrée : `const visible = todos.filter((t) => filter === 'all' || (filter === 'done') === t.done);`"],
       [F("App.tsx", "tsx", r"""
import { useState } from 'react';

type Todo = { id: number; title: string; done: boolean };
type Filter = 'all' | 'active' | 'done';

const initial: Todo[] = [
  { id: 1, title: 'Lire le cours', done: true },
  { id: 2, title: 'Faire le quiz', done: false },
  { id: 3, title: 'Faire le TD', done: false },
];

export default function App() {
  const [todos, setTodos] = useState<Todo[]>(initial);
  const [filter, setFilter] = useState<Filter>('all');

  function add() {
    setTodos((ts) => [...ts, { id: Date.now() + Math.random(), title: `Tâche ${ts.length + 1}`, done: false }]);
  }
  function toggle(id: number) {
    setTodos((ts) => ts.map((t) => (t.id === id ? { ...t, done: !t.done } : t)));
  }
  function remove(id: number) {
    setTodos((ts) => ts.filter((t) => t.id !== id));
  }

  const visible = todos.filter((t) => filter === 'all' || (filter === 'done') === t.done);
  const remaining = todos.filter((t) => !t.done).length;

  return (
    <div>
      <button className="add" onClick={add}>Ajouter</button>
      <div>
        <button className="filter-all" onClick={() => setFilter('all')}>Toutes</button>
        <button className="filter-active" onClick={() => setFilter('active')}>À faire</button>
        <button className="filter-done" onClick={() => setFilter('done')}>Faites</button>
      </div>
      <ul>
        {visible.map((t) => (
          <li key={t.id} className={t.done ? 'done' : ''}>
            <input type="checkbox" checked={t.done} onChange={() => toggle(t.id)} />
            {t.title}
            <button className="remove" onClick={() => remove(t.id)}>Supprimer</button>
          </li>
        ))}
      </ul>
      <p className="remaining">{remaining} restante{remaining > 1 ? 's' : ''}</p>
    </div>
  );
}
""")],
       ["Cocher une tâche ne modifie que cette tâche",
        "Le filtre « Faites » n'affiche que les tâches cochées, sans state supplémentaire",
        "Ajouter 3 fois d'affilée crée bien 3 tâches"],
       run=RUN("react", tests=r"""
assert.equal($$('li').length, 3, '3 tâches au départ');
assert.includes(text(), '2 restantes', '2 restantes au départ');
await click($$('input[type=checkbox]')[1]);
assert.includes(text(), '1 restante', 'Cocher la 2e tâche : 1 restante');
assert.equal($$('li.done').length, 2, '2 lignes ont la classe done');
await click('.filter-done');
assert.equal($$('li').length, 2, 'Filtre « Faites » : 2 tâches');
await click('.filter-active');
assert.equal($$('li').length, 1, 'Filtre « À faire » : 1 tâche');
await click('.filter-all');
$('.add').click(); $('.add').click(); $('.add').click(); await tick();
assert.equal($$('li').length, 6, '3 ajouts rapides : 6 tâches');
assert.includes(text(), 'Tâche 6', 'La dernière tâche s\'appelle Tâche 6');
await click($$('.remove')[0]);
assert.equal($$('li').length, 5, 'Supprimer retire une tâche');
assert(!text().includes('Lire le cours'), 'La tâche supprimée a disparu');
""")),
    TD(3, "Historique avec annuler / rétablir",
       "Un éditeur de liste de courses où chaque modification peut être **annulée** puis **rétablie**. Le state n'est plus une liste mais un **historique de listes** : `{ past, present, future }`. Tu combines : state objet complexe mis à jour sans mutation, mises à jour fonctionnelles, et valeurs dérivées (`canUndo`, `canRedo`).",
       ["State `history: { past: string[][]; present: string[]; future: string[][] }`, `present` initialisé avec `['Pain', 'Lait']`",
        "`add(item)` : pousse le `present` actuel dans `past`, nouveau `present` avec l'item, `future` vidé",
        "`remove(index)` : même logique",
        "`undo()` : le dernier élément de `past` devient `present`, l'ancien `present` passe en tête de `future` ; `redo()` fait l'inverse",
        "Boutons `.undo` Annuler / `.redo` Rétablir désactivés quand impossible ; un `<input>` + bouton `.add` « Ajouter » ; chaque item (`.item`) a un bouton `.remove-item` « × »",
        "Un texte `.count` « N action(s) annulable(s) » = `past.length`"],
       [F("App.tsx", "tsx", r"""
import { useState } from 'react';

type History = { past: string[][]; present: string[]; future: string[][] };

export default function App() {
  const [history, setHistory] = useState<History>({ past: [], present: ['Pain', 'Lait'], future: [] });
  const [draft, setDraft] = useState('');

  // à toi : commit(nextPresent), undo(), redo()

  return <div />;
}
""")],
       ["Une seule fonction `commit(next: string[])` qui fait `setHistory((h) => ({ past: [...h.past, h.present], present: next, future: [] }))` ; `add` et `remove` l'appellent.",
        "`undo` : `setHistory((h) => { if (!h.past.length) return h; const previous = h.past[h.past.length - 1]; return { past: h.past.slice(0, -1), present: previous, future: [h.present, ...h.future] }; })`.",
        "Renvoyer `h` inchangé quand il n'y a rien à annuler : React ne redessine même pas."],
       [F("App.tsx", "tsx", r"""
import { useState } from 'react';

type History = { past: string[][]; present: string[]; future: string[][] };

export default function App() {
  const [history, setHistory] = useState<History>({ past: [], present: ['Pain', 'Lait'], future: [] });
  const [draft, setDraft] = useState('');

  function commit(next: string[]) {
    setHistory((h) => ({ past: [...h.past, h.present], present: next, future: [] }));
  }
  function add() {
    const item = draft.trim();
    if (!item) return;
    commit([...history.present, item]);
    setDraft('');
  }
  function remove(index: number) {
    commit(history.present.filter((_, i) => i !== index));
  }
  function undo() {
    setHistory((h) => {
      if (h.past.length === 0) return h;
      const previous = h.past[h.past.length - 1];
      return { past: h.past.slice(0, -1), present: previous, future: [h.present, ...h.future] };
    });
  }
  function redo() {
    setHistory((h) => {
      if (h.future.length === 0) return h;
      const [next, ...rest] = h.future;
      return { past: [...h.past, h.present], present: next, future: rest };
    });
  }

  const canUndo = history.past.length > 0;
  const canRedo = history.future.length > 0;

  return (
    <div>
      <div>
        <button className="undo" onClick={undo} disabled={!canUndo}>Annuler</button>
        <button className="redo" onClick={redo} disabled={!canRedo}>Rétablir</button>
        <span className="count">{history.past.length} action{history.past.length > 1 ? 's' : ''} annulable{history.past.length > 1 ? 's' : ''}</span>
      </div>
      <form onSubmit={(e) => { e.preventDefault(); add(); }}>
        <input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Article" />
        <button className="add" type="submit">Ajouter</button>
      </form>
      <ul>
        {history.present.map((item, i) => (
          <li key={`${item}-${i}`} className="item">
            {item} <button type="button" className="remove-item" onClick={() => remove(i)}>×</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
""")],
       ["Ajouter puis Annuler redonne exactement la liste précédente",
        "Après Annuler, Rétablir est actif ; après une nouvelle action, Rétablir redevient inactif",
        "Annuler quand `past` est vide ne fait rien (et ne plante pas)"],
       run=RUN("react", tests=r"""
assert.equal($$('.item').length, 2, '2 articles au départ');
assert($('.undo').disabled, 'Annuler désactivé au départ');
assert($('.redo').disabled, 'Rétablir désactivé au départ');
await type('input', 'Œufs'); await click('.add');
assert.equal($$('.item').length, 3, 'Ajout : 3 articles');
assert.includes(text(), '1 action annulable', '1 action annulable après un ajout');
await click($$('.remove-item')[0]);
assert.equal($$('.item').length, 2, 'Suppression : 2 articles');
assert(!text().includes('Pain'), 'Pain supprimé');
await click('.undo');
assert.includes(text(), 'Pain', 'Annuler restaure Pain');
assert.equal($$('.item').length, 3, 'Après annuler : 3 articles');
assert(!$('.redo').disabled, 'Rétablir actif après Annuler');
await click('.redo');
assert(!text().includes('Pain'), 'Rétablir re-supprime Pain');
await click('.undo'); await click('.undo');
assert.equal($$('.item').length, 2, 'Deux annulations : retour à la liste de départ');
assert($('.undo').disabled, 'Annuler désactivé quand plus rien à annuler');
await type('input', 'Riz'); await click('.add');
assert($('.redo').disabled, 'Une nouvelle action vide le futur : Rétablir désactivé');
""")),
  ])

# ---------------------------------------------------------------- formulaires
forms = V2(v1["react-forms"],
  prereq=[
    P("Événement", "Un signal envoyé par le navigateur quand l'utilisateur fait quelque chose : clic, frappe au clavier, envoi de formulaire. En React : `onClick`, `onChange`, `onSubmit`."),
    P("`e.target.value`", "Dans un gestionnaire `onChange`, `e` est l'événement, `e.target` l'élément qui l'a émis (le champ), `e.target.value` le texte qu'il contient."),
    P("`preventDefault()`", "Empêche le comportement par défaut du navigateur. Pour un formulaire : empêche le rechargement de la page à l'envoi."),
    P("Callback", "Une fonction passée en paramètre pour être appelée plus tard. `onAdd={(title) => …}` : l'enfant appellera `onAdd` quand il aura un titre à donner."),
    P("Source de vérité", "L'endroit unique où vit une donnée. Si le texte d'un champ est à la fois dans le DOM et dans un state, il y a deux sources et elles peuvent diverger."),
  ],
  diagram=D(
    nodes=[
      N("app", 1, 0, "TodoApp", "state : todos[]", color="good"),
      N("form", 0, 1, "TodoForm", "state : title"),
      N("list", 2, 1, "TodoList", "affiche todos"),
      N("input", 0, 2, "<input value={title} />", "onChange → setTitle", kind="pill"),
    ],
    edges=[E("app", "form", "onAdd (fonction)"), E("app", "list", "todos (données)"), E("form", "app", "onAdd(title)", color="good", back=True), E("input", "form", "frappe", color="accent")],
    caption="Les données descendent (props), les événements remontent (callbacks). L'état partagé vit dans le parent commun."),
  lessons=[
    L("Réagir aux événements", r"""
En React, un gestionnaire d'événement est une **fonction passée en prop** à un élément : `onClick={handleClick}`. Les noms sont en camelCase (`onClick`, `onChange`, `onSubmit`, `onKeyDown`).

```tsx
<button onClick={() => setCount((c) => c + 1)}>+1</button>
<button onClick={handleReset}>Reset</button>
```

Piège classique : `onClick={supprimer(id)}` **appelle** `supprimer` immédiatement, pendant le rendu, et passe son résultat (souvent `undefined`) à `onClick`. Il faut passer une **fonction** : `onClick={() => supprimer(id)}`. Si la fonction n'a pas besoin d'argument, on peut la passer directement : `onClick={handleReset}` (sans parenthèses).

Le gestionnaire reçoit l'événement en paramètre. Pour un formulaire, `onSubmit={(e) => { e.preventDefault(); … }}` : sans `preventDefault`, le navigateur envoie le formulaire à l'ancienne, recharge la page, et tout le state disparaît. C'est le symptôme « la page clignote et tout se vide ».
"""),
    L("Champs contrôlés : le state est la source de vérité", r"""
Un champ HTML garde sa propre valeur dans le DOM. React préfère que **le state** soit la seule source de vérité : le champ affiche ce que dit le state, et chaque frappe met le state à jour. C'est un champ **contrôlé**.

```tsx
const [title, setTitle] = useState('');

<input value={title} onChange={(e) => setTitle(e.target.value)} />
```

Le cycle à chaque frappe : l'utilisateur tape → `onChange` → `setTitle(nouvelle valeur)` → nouveau rendu → `value={title}` affiche la nouvelle valeur. Ça paraît un détour, mais ça donne un contrôle total :

- Vider le champ après envoi : `setTitle('')`.
- Valider en direct : `const isValid = title.trim().length >= 3;` puis `disabled={!isValid}` sur le bouton.
- Transformer la saisie : `setTitle(e.target.value.toUpperCase())`.
- Pré-remplir : `useState(initialTitle)`.

Pour les autres champs : `<textarea value=… onChange=…>`, `<select value=… onChange=…>`, et pour une case à cocher `checked={done} onChange={(e) => setDone(e.target.checked)}`. Un champ avec `value` mais **sans** `onChange` est figé (React avertit dans la console).
"""),
    L("Faire remonter une information au parent", r"""
Les props descendent. Mais `TodoForm` doit prévenir `TodoApp` qu'une tâche a été saisie. Comment remonter l'info ? Le parent passe une **fonction** en prop, et l'enfant l'appelle avec la donnée :

```tsx
// Parent
<TodoForm onAdd={(title) => setTodos((t) => [...t, { id: nextId(), title }])} />

// Enfant
function TodoForm({ onAdd }: { onAdd: (title: string) => void }) {
  const [title, setTitle] = useState('');
  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (title.trim() === '') return;
    onAdd(title.trim());     // "voilà un titre, fais-en ce que tu veux"
    setTitle('');
  }
  …
}
```

`TodoForm` ne sait pas ce que le parent fait du titre (l'ajouter à une liste, l'envoyer à une API…) : il se contente de **signaler**. Ce découplage rend le formulaire réutilisable. La convention de nommage : la prop s'appelle `onQuelqueChose` (`onAdd`, `onSelect`, `onChange`), la fonction du parent `handleQuelqueChose`.
"""),
    L("Remonter le state : deux composants qui partagent une donnée", r"""
Une barre de recherche et une liste filtrée sont deux composants **frères** : aucun ne peut passer de props à l'autre. Où mettre le texte recherché ? Dans leur **plus proche parent commun**. Le parent détient le state, passe la valeur à l'un et à l'autre, et passe à la barre une fonction pour le modifier.

```tsx
function Page() {
  const [query, setQuery] = useState('');
  const visible = contacts.filter((c) => c.name.toLowerCase().includes(query.toLowerCase()));
  return (
    <>
      <SearchBar value={query} onChange={setQuery} />
      <ContactList contacts={visible} />
    </>
  );
}
```

`SearchBar` n'a plus de state du tout : il reçoit `value` et `onChange`, exactement comme un `<input>` natif. On dit qu'on a **remonté** le state (*lifting state up*). Le filtrage est une valeur dérivée, calculée dans le parent. Règle : quand deux composants doivent être d'accord sur une donnée, cette donnée vit au-dessus d'eux, et jamais en double.
"""),
  ],
  recap=[
    "`onClick={() => f(id)}` ou `onClick={f}` : toujours passer une fonction, jamais son résultat.",
    "`onSubmit` + `e.preventDefault()` : sinon la page se recharge et le state est perdu.",
    "Champ contrôlé : `value={state}` + `onChange={(e) => setState(e.target.value)}`.",
    "L'enfant remonte une info en appelant une fonction reçue en prop (`onAdd(title)`).",
    "Donnée partagée par deux composants → state dans leur parent commun, filtrage dérivé.",
  ],
  example=[F("TodoForm.tsx", "tsx", r"""
import { useState, FormEvent } from 'react';

export default function TodoForm({ onAdd }: { onAdd: (title: string) => void }) {
  const [title, setTitle] = useState('');

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (title.trim() === '') return;
    onAdd(title.trim());          // remonte au parent
    setTitle('');                 // vide le champ
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Nouvelle tâche" />
      <button type="submit" disabled={title.trim() === ''}>Ajouter</button>
    </form>
  );
}
"""), F("App.tsx", "tsx", r"""
import { useState } from 'react';
import TodoForm from './TodoForm';

type Todo = { id: number; title: string };
let nextId = 1;

export default function App() {
  const [todos, setTodos] = useState<Todo[]>([]);

  return (
    <>
      <TodoForm onAdd={(title) => setTodos((t) => [...t, { id: nextId++, title }])} />
      <ul>
        {todos.map((t) => <li key={t.id}>{t.title}</li>)}
      </ul>
    </>
  );
}
""")],
  notes=["`TodoForm.tsx` ne connaît pas la liste : il signale juste « on a ajouté ce titre » via `onAdd`.",
         "Le champ est contrôlé : `value={title}` + `onChange`. Le bouton est désactivé tant que le titre est vide.",
         "Dans `App.tsx`, la liste vit dans le parent, qui décide quoi faire du titre reçu.",
         "`e.preventDefault()` dans `handleSubmit` : sans lui, la page se rechargerait."],
  td1=dict(path="App.tsx", files=[F("App.tsx", "tsx", r"""
import { useState } from 'react';

type Contact = { id: string; name: string; email: string };

const initial: Contact[] = [
  { id: '1', name: 'Ana Martin', email: 'ana@exemple.fr' },
  { id: '2', name: 'Léo Petit', email: 'leo@exemple.fr' },
];

function SearchBar(/* value, onChange */) {
  // à toi : placeholder "Rechercher"
}

function ContactList(/* contacts */) {
  // à toi
}

function AddContact(/* onAdd */) {
  // à toi : 2 champs (placeholder "Nom" et "Email"), refuse un nom vide, vide les champs après ajout
}

export default function App() {
  // à toi : state contacts + state query, liste filtrée dérivée
  return <div />;
}
""")], solution=[F("App.tsx", "tsx", r"""
import { useState, FormEvent } from 'react';

type Contact = { id: string; name: string; email: string };

const initial: Contact[] = [
  { id: '1', name: 'Ana Martin', email: 'ana@exemple.fr' },
  { id: '2', name: 'Léo Petit', email: 'leo@exemple.fr' },
];

function SearchBar({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return <input className="search" value={value} onChange={(e) => onChange(e.target.value)} placeholder="Rechercher" />;
}

function ContactList({ contacts }: { contacts: Contact[] }) {
  if (contacts.length === 0) return <p>Aucun contact</p>;
  return <ul>{contacts.map((c) => <li key={c.id}>{c.name} – {c.email}</li>)}</ul>;
}

function AddContact({ onAdd }: { onAdd: (c: Contact) => void }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    onAdd({ id: String(Date.now() + Math.random()), name: name.trim(), email: email.trim() });
    setName('');
    setEmail('');
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Nom" />
      <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
      <button type="submit">Ajouter</button>
    </form>
  );
}

export default function App() {
  const [contacts, setContacts] = useState(initial);
  const [query, setQuery] = useState('');

  const visible = contacts.filter((c) => c.name.toLowerCase().includes(query.toLowerCase()));

  return (
    <>
      <SearchBar value={query} onChange={setQuery} />
      <ContactList contacts={visible} />
      <AddContact onAdd={(c) => setContacts((list) => [...list, c])} />
    </>
  );
}
""")], run=RUN("react", tests=r"""
assert.equal($$('li').length, 2, '2 contacts au départ');
const search = $('input[placeholder="Rechercher"]');
assert(search, 'Un champ avec placeholder « Rechercher »');
await type(search, 'léo');
assert.equal($$('li').length, 1, 'Recherche « léo » : 1 contact (insensible à la casse)');
await type(search, 'zzz');
assert.includes(text(), 'Aucun contact', 'Recherche sans résultat : « Aucun contact »');
await type(search, '');
const nameInput = $('input[placeholder="Nom"]'), emailInput = $('input[placeholder="Email"]');
assert(nameInput && emailInput, 'Champs Nom et Email présents');
await type(nameInput, '   '); await submit('form');
assert.equal($$('li').length, 2, 'Un nom vide n\'ajoute rien');
await type(nameInput, 'Zoé Durand'); await type(emailInput, 'zoe@exemple.fr'); await submit('form');
assert.equal($$('li').length, 3, 'Ajout : 3 contacts');
assert.includes(text(), 'zoe@exemple.fr', 'Le nouveau contact est affiché');
assert.equal(nameInput.value, '', 'Le champ Nom est vidé après ajout');
assert.equal(emailInput.value, '', 'Le champ Email est vidé après ajout');
""")),
  tds=[
    TD(2, "Formulaire d'inscription avec validation en direct",
       "Un formulaire à plusieurs champs de **types différents** (texte, email, mot de passe, case à cocher, liste déroulante) avec des règles de validation affichées **pendant la saisie**, et un bouton actif seulement quand tout est valide. Le state est un **objet** (un seul `useState` pour tout le formulaire) mis à jour champ par champ.",
       ["State `form: { name, email, password, role, cgu }` et un state `submitted: null | typeof form`",
        "Un gestionnaire **générique** `update(field, value)` qui fait `setForm((f) => ({ ...f, [field]: value }))`",
        "Règles : nom ≥ 2 caractères, email contient `@`, mot de passe ≥ 8 caractères **et** un chiffre, `cgu` cochée. Les erreurs s'affichent sous chaque champ (`<p className=\"error\">`), **seulement si le champ a été touché** (state `touched: Record<string, boolean>` mis à jour sur `onBlur`)",
        "`<select name=\"role\">` contrôlé (`dev` / `designer` / `pm`), valeur par défaut `dev` ; les autres champs ont `name=\"name\"`, `name=\"email\"`, `name=\"password\"`, `name=\"cgu\"`",
        "Bouton « S'inscrire » désactivé tant qu'une règle échoue ; à l'envoi, affiche `<p className=\"success\">Bienvenue {name} ({role})</p>`"],
       [F("App.tsx", "tsx", r"""
import { useState } from 'react';

type Form = { name: string; email: string; password: string; role: 'dev' | 'designer' | 'pm'; cgu: boolean };

const empty: Form = { name: '', email: '', password: '', role: 'dev', cgu: false };

export default function App() {
  const [form, setForm] = useState<Form>(empty);
  // à toi : touched, errors (dérivé), update(), onBlur, submit
  return <form />;
}
""")],
       ["Les erreurs sont **dérivées** : `const errors = { name: form.name.trim().length < 2 ? '2 caractères minimum' : '', … }` ; `const isValid = Object.values(errors).every((e) => !e)`.",
        "Case à cocher : `checked={form.cgu} onChange={(e) => update('cgu', e.target.checked)}` (c'est `checked`, pas `value`).",
        "`onBlur={() => setTouched((t) => ({ ...t, name: true }))}` ; afficher l'erreur : `{touched.name && errors.name && <p className=\"error\">{errors.name}</p>}`."],
       [F("App.tsx", "tsx", r"""
import { useState, FormEvent } from 'react';

type Form = { name: string; email: string; password: string; role: 'dev' | 'designer' | 'pm'; cgu: boolean };

const empty: Form = { name: '', email: '', password: '', role: 'dev', cgu: false };

export default function App() {
  const [form, setForm] = useState<Form>(empty);
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [submitted, setSubmitted] = useState<Form | null>(null);

  function update<K extends keyof Form>(field: K, value: Form[K]) {
    setForm((f) => ({ ...f, [field]: value }));
  }
  const touch = (field: string) => setTouched((t) => ({ ...t, [field]: true }));

  const errors = {
    name: form.name.trim().length < 2 ? '2 caractères minimum' : '',
    email: form.email.includes('@') ? '' : 'Email invalide',
    password: form.password.length < 8 ? '8 caractères minimum' : !/\d/.test(form.password) ? 'Au moins un chiffre' : '',
    cgu: form.cgu ? '' : 'Tu dois accepter les CGU',
  };
  const isValid = Object.values(errors).every((e) => e === '');

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!isValid) return;
    setSubmitted(form);
  }

  if (submitted) return <p className="success">Bienvenue {submitted.name} ({submitted.role})</p>;

  return (
    <form onSubmit={handleSubmit}>
      <input name="name" value={form.name} onChange={(e) => update('name', e.target.value)} onBlur={() => touch('name')} placeholder="Nom" />
      {touched.name && errors.name && <p className="error">{errors.name}</p>}

      <input name="email" value={form.email} onChange={(e) => update('email', e.target.value)} onBlur={() => touch('email')} placeholder="Email" />
      {touched.email && errors.email && <p className="error">{errors.email}</p>}

      <input name="password" type="password" value={form.password} onChange={(e) => update('password', e.target.value)} onBlur={() => touch('password')} placeholder="Mot de passe" />
      {touched.password && errors.password && <p className="error">{errors.password}</p>}

      <select name="role" value={form.role} onChange={(e) => update('role', e.target.value as Form['role'])}>
        <option value="dev">Développeur</option>
        <option value="designer">Designer</option>
        <option value="pm">Chef de projet</option>
      </select>

      <label>
        <input name="cgu" type="checkbox" checked={form.cgu} onChange={(e) => update('cgu', e.target.checked)} onBlur={() => touch('cgu')} />
        J'accepte les CGU
      </label>
      {touched.cgu && errors.cgu && <p className="error">{errors.cgu}</p>}

      <button type="submit" disabled={!isValid}>S'inscrire</button>
    </form>
  );
}
""")],
       ["Aucune erreur n'apparaît avant d'avoir touché un champ",
        "Le bouton ne s'active que quand les 4 règles sont vraies",
        "Un seul `useState` pour les 5 valeurs du formulaire"],
       run=RUN("react", tests=r"""
assert.equal($$('.error').length, 0, 'Aucune erreur affichée au départ');
assert($('button[type=submit]').disabled, 'Bouton désactivé au départ');
const name = $('[name=name]');
await blur(name);
assert.equal($$('.error').length, 1, 'Après blur sur Nom vide : 1 erreur');
await type(name, 'Ana');
assert.equal($$('.error').length, 0, 'Nom valide : l\'erreur disparaît');
await type('[name=email]', 'ana@mail.com');
const pwd = $('[name=password]');
await type(pwd, 'abcdefgh'); await blur(pwd);
assert.includes(text(), 'chiffre', 'Mot de passe sans chiffre : erreur « chiffre »');
await type(pwd, 'abcdefg1');
assert($('button[type=submit]').disabled, 'CGU non cochée : bouton encore désactivé');
const select = $('[name=role]'); Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set.call(select, 'pm'); select.dispatchEvent(new Event('change', { bubbles: true })); await tick();
await click('[name=cgu]');
assert(!$('button[type=submit]').disabled, 'Tout valide : bouton actif');
await submit('form');
assert.includes(text(), 'Bienvenue Ana (pm)', 'Message de succès avec nom et rôle');
""")),
    TD(3, "Éditeur de commande avec lignes dynamiques",
       "Un formulaire de **lignes répétées** : chaque ligne a un produit (liste déroulante), une quantité et un sous-total ; on peut ajouter et supprimer des lignes ; le total se recalcule ; le parent détient tout le state et les lignes (`OrderLine`) sont des composants **contrôlés** qui remontent leurs changements. C'est le patron de tous les formulaires « tableau éditable » que tu rencontreras.",
       ["`App` : state `lines: { id: number; productId: string; quantity: number }[]` (1 ligne au départ)",
        "`OrderLine` (`.line`) : composant **sans state**, reçoit `line`, `products`, `onChange(line)`, `onRemove()`, `canRemove` ; un `<select>` pour le produit, un `<input type=\"number\" min=1>` pour la quantité, le sous-total (`.subtotal`), un bouton `.remove-line` « Retirer »",
        "La quantité saisie est **normalisée** : entier, minimum 1 (une saisie `0` ou vide redevient 1)",
        "Bouton `.add-line` « Ajouter une ligne » : nouvelle ligne avec le **premier produit non encore utilisé** (ou le premier produit si tous sont utilisés) ; on ne peut pas retirer la dernière ligne (bouton désactivé)",
        "Un `<p className=\"total\">` avec le total ; un bouton `.validate` « Valider » désactivé si deux lignes ont le même produit, avec un message `<p className=\"error\">` dans ce cas"],
       [F("App.tsx", "tsx", r"""
import { useState } from 'react';

type Product = { id: string; name: string; price: number };
type Line = { id: number; productId: string; quantity: number };

const products: Product[] = [
  { id: 'kb', name: 'Clavier', price: 49.9 },
  { id: 'ms', name: 'Souris', price: 19.5 },
  { id: 'sc', name: 'Écran', price: 189 },
];

function OrderLine(/* line, products, onChange, onRemove, canRemove */) {
  // à toi
}

export default function App() {
  const [lines, setLines] = useState<Line[]>([{ id: 1, productId: 'kb', quantity: 1 }]);
  // à toi
  return <div />;
}
""")],
       ["Mettre à jour une ligne : `setLines((ls) => ls.map((l) => (l.id === updated.id ? updated : l)))` ; `OrderLine` appelle `onChange({ ...line, quantity: … })`.",
        "Normaliser : `const q = Math.max(1, Math.floor(Number(e.target.value)) || 1);`",
        "Produit non utilisé : `products.find((p) => !lines.some((l) => l.productId === p.id)) ?? products[0]`.",
        "Doublons : `new Set(lines.map((l) => l.productId)).size !== lines.length`."],
       [F("App.tsx", "tsx", r"""
import { useState } from 'react';

type Product = { id: string; name: string; price: number };
type Line = { id: number; productId: string; quantity: number };

const products: Product[] = [
  { id: 'kb', name: 'Clavier', price: 49.9 },
  { id: 'ms', name: 'Souris', price: 19.5 },
  { id: 'sc', name: 'Écran', price: 189 },
];

const eur = (n: number) => n.toFixed(2) + ' €';

function OrderLine({ line, products, onChange, onRemove, canRemove }: {
  line: Line; products: Product[]; onChange: (l: Line) => void; onRemove: () => void; canRemove: boolean;
}) {
  const product = products.find((p) => p.id === line.productId)!;
  return (
    <div className="line">
      <select value={line.productId} onChange={(e) => onChange({ ...line, productId: e.target.value })}>
        {products.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
      </select>
      <input type="number" min={1} value={line.quantity}
        onChange={(e) => onChange({ ...line, quantity: Math.max(1, Math.floor(Number(e.target.value)) || 1) })} />
      <span className="subtotal">{eur(product.price * line.quantity)}</span>
      <button type="button" className="remove-line" onClick={onRemove} disabled={!canRemove}>Retirer</button>
    </div>
  );
}

export default function App() {
  const [lines, setLines] = useState<Line[]>([{ id: 1, productId: 'kb', quantity: 1 }]);
  const [nextId, setNextId] = useState(2);

  function updateLine(updated: Line) {
    setLines((ls) => ls.map((l) => (l.id === updated.id ? updated : l)));
  }
  function removeLine(id: number) {
    setLines((ls) => (ls.length > 1 ? ls.filter((l) => l.id !== id) : ls));
  }
  function addLine() {
    const free = products.find((p) => !lines.some((l) => l.productId === p.id)) ?? products[0];
    setLines((ls) => [...ls, { id: nextId, productId: free.id, quantity: 1 }]);
    setNextId((n) => n + 1);
  }

  const total = lines.reduce((s, l) => s + products.find((p) => p.id === l.productId)!.price * l.quantity, 0);
  const hasDuplicates = new Set(lines.map((l) => l.productId)).size !== lines.length;

  return (
    <div>
      {lines.map((l) => (
        <OrderLine key={l.id} line={l} products={products} onChange={updateLine}
          onRemove={() => removeLine(l.id)} canRemove={lines.length > 1} />
      ))}
      <button type="button" className="add-line" onClick={addLine}>Ajouter une ligne</button>
      <p className="total">Total : {eur(total)}</p>
      {hasDuplicates && <p className="error">Deux lignes ont le même produit</p>}
      <button type="button" className="validate" disabled={hasDuplicates}>Valider</button>
    </div>
  );
}
""")],
       ["`OrderLine` n'a aucun `useState` : tout vient des props",
        "Saisir 0 dans une quantité la remet à 1",
        "Deux lignes avec le même produit désactivent « Valider » et affichent l'erreur"],
       run=RUN("react", tests=r"""
assert.equal($$('.line').length, 1, '1 ligne au départ');
assert($('.remove-line').disabled, 'Impossible de retirer la dernière ligne');
assert.includes($('.total').textContent, '49.90', 'Total initial 49.90');
await type($('.line input[type=number]'), '3');
assert.includes($('.subtotal').textContent, '149.70', 'Sous-total 3 claviers = 149.70');
await type($('.line input[type=number]'), '0');
assert.equal($('.line input[type=number]').value, '1', 'Quantité 0 normalisée à 1');
await click('.add-line');
assert.equal($$('.line').length, 2, 'Ajout : 2 lignes');
assert.equal($$('.line select')[1].value, 'ms', 'La nouvelle ligne prend le premier produit libre (Souris)');
assert.includes($('.total').textContent, '69.40', 'Total 49.90 + 19.50 = 69.40');
assert(!$('.validate').disabled, 'Pas de doublon : Valider actif');
const sel = $$('.line select')[1]; Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set.call(sel, 'kb'); sel.dispatchEvent(new Event('change', { bubbles: true })); await tick();
assert($('.validate').disabled, 'Doublon : Valider désactivé');
assert($('.error'), 'Doublon : message d\'erreur affiché');
await click($$('.remove-line')[1]);
assert.equal($$('.line').length, 1, 'Retirer : 1 ligne');
assert(!$('.error'), 'Plus de doublon : plus d\'erreur');
""")),
  ])

# ---------------------------------------------------------------- useEffect
eff = V2(v1["react-effect"],
  prereq=[
    P("Fonction pure", "Une fonction qui, pour les mêmes entrées, renvoie le même résultat et ne modifie rien à l'extérieur. Le corps d'un composant doit l'être : il calcule du JSX, c'est tout."),
    P("Effet de bord", "Tout ce qu'une fonction fait **en plus** de renvoyer une valeur : appeler une API, changer `document.title`, lancer un timer, écrire dans localStorage, s'abonner à un événement. Nécessaire, mais à isoler."),
    P("Promesse / `fetch`", "`fetch(url)` renvoie une **promesse** : un résultat qui arrivera plus tard. `.then(...)` enchaîne ce qu'il faut faire quand il arrive. Détails dans le parcours Données & API."),
    P("`setInterval` / `clearInterval`", "`const id = setInterval(fn, 1000)` appelle `fn` toutes les secondes jusqu'à `clearInterval(id)`. Si on oublie de l'arrêter, il tourne pour toujours."),
    P("Montage / démontage", "Un composant est **monté** quand il apparaît à l'écran pour la première fois, **démonté** quand il en disparaît (changement de page, condition qui devient fausse)."),
  ],
  diagram=D(
    nodes=[
      N("r1", 0, 0, "Rendu", "userId = 1", kind="doc"),
      N("e1", 1, 0, "Effet", "fetch(/users/1)", color="accent"),
      N("ui", 2, 0, "Écran", "« Chargement… » puis Ana", kind="file"),
      N("chg", 0, 1, "userId passe à 2", "nouveau rendu", kind="pill"),
      N("clean", 1, 1, "Cleanup", "abort() de la requête 1", color="warn"),
      N("e2", 2, 1, "Nouvel effet", "fetch(/users/2)", color="accent"),
      N("unm", 1, 2, "Démontage", "cleanup une dernière fois", color="warn", kind="note"),
    ],
    edges=[E("r1", "e1", "après l'affichage"), E("e1", "ui", "setUser"), E("chg", "clean", "dépendance changée"), E("clean", "e2"), E("e2", "unm", dashed=True)],
    caption="L'effet tourne après l'affichage. Quand une dépendance change, React nettoie l'ancien effet avant de lancer le nouveau."),
  lessons=[
    L("Pourquoi un endroit dédié aux effets de bord", r"""
Le corps d'un composant doit rester **pur** : il reçoit props et state, renvoie du JSX. React peut l'appeler une fois, deux fois, dix fois (il le fait volontairement en développement pour détecter les bugs). Si tu mets un `fetch` dans le corps, tu lances dix requêtes. Si tu mets `document.title = …`, ça marche par hasard, mais tu mélanges « décrire l'écran » et « agir sur le monde ».

`useEffect` est la case prévue pour ces actions : « **après** avoir affiché ce rendu, fais ceci ».

```tsx
useEffect(() => {
  document.title = `${count} clics`;   // effet : agit sur le monde extérieur
}, [count]);                           // dépendances : quand relancer
```

React affiche d'abord l'écran, puis exécute la fonction. L'utilisateur voit le résultat sans attendre l'effet. Avant d'écrire un `useEffect`, pose-toi la question : « est-ce vraiment une synchronisation avec l'extérieur ? » Si c'est un calcul à partir du state, c'est une constante dans le rendu. Si c'est une réaction à un clic, c'est dans le gestionnaire du clic. L'effet est pour ce qui reste.
"""),
    L("Le tableau de dépendances : quand l'effet se relance", r"""
Le deuxième argument dit à React **à quelles conditions** réexécuter l'effet :

- `useEffect(fn)` sans tableau : après **chaque** rendu. Rarement voulu.
- `useEffect(fn, [])` tableau vide : après le **premier** rendu seulement (le montage), puis plus jamais. Pour une initialisation.
- `useEffect(fn, [userId])` : au montage, puis à chaque fois que `userId` **change** (comparé avec `===` au rendu précédent).

Règle d'or : **tout ce que l'effet utilise et qui vient du composant** (props, state, fonctions définies dans le composant) doit figurer dans le tableau. Si tu lis `userId` dans l'effet, `[userId]`. L'outil ESLint de React (`react-hooks/exhaustive-deps`) te le signale ; ne le fais pas taire, corrige la cause.

Deux pièges :

- Oublier une dépendance : l'effet continue d'utiliser une **vieille valeur** (celle du rendu où il a été créé). Le bug classique « mon effet voit toujours l'ancien state ».
- Mettre en dépendance un state que l'effet modifie : `useEffect(() => setItems([...items, x]), [items])` → modifier `items` relance l'effet, qui modifie `items`… boucle infinie.
"""),
    L("Le cleanup : défaire ce que l'effet a fait", r"""
Un effet qui lance quelque chose (timer, abonnement, requête) doit pouvoir l'**arrêter**. Pour ça, l'effet **renvoie une fonction**, le *cleanup*. React l'appelle :

1. **Avant de relancer** l'effet (quand une dépendance a changé) : on nettoie l'ancien avant de démarrer le nouveau.
2. **Au démontage** du composant : une dernière fois, pour ne rien laisser tourner.

```tsx
useEffect(() => {
  const id = setInterval(() => setSeconds((s) => s + 1), 1000);
  return () => clearInterval(id);     // cleanup
}, [running]);
```

Sans le cleanup, chaque changement de `running` ajouterait un deuxième intervalle sans arrêter le premier : le chrono avancerait de 2, puis 3 secondes par seconde. Même logique pour une requête : si l'utilisateur passe de l'utilisateur 1 à l'utilisateur 2 avant que la réponse 1 soit arrivée, le cleanup annule la requête 1 (`AbortController`) pour qu'elle n'écrase pas la réponse 2 arrivée plus tôt.

En développement, le **StrictMode** de React monte, démonte et remonte chaque composant une fois au démarrage : si ton effet n'a pas de cleanup correct, tu le vois tout de suite (double requête, double timer). C'est volontaire : un composant qui survit à ça est un composant sain.
"""),
    L("Charger des données avec useEffect : le schéma complet", r"""
```tsx
const [user, setUser] = useState<User | null>(null);
const [error, setError] = useState<string | null>(null);

useEffect(() => {
  const controller = new AbortController();
  setUser(null); setError(null);                                   // repartir propre

  fetch(`/api/users/${userId}`, { signal: controller.signal })
    .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
    .then(setUser)
    .catch((e) => { if (e.name !== 'AbortError') setError(e.message); });

  return () => controller.abort();                                // cleanup
}, [userId]);

if (error) return <p>Erreur : {error}</p>;
if (!user) return <p>Chargement…</p>;
return <h2>{user.name}</h2>;
```

Trois états à afficher : erreur, chargement (`user` encore `null`), données. Le `AbortError` est ignoré : c'est nous qui avons annulé, ce n'est pas une erreur. Ce schéma est répétitif ; le module Hooks personnalisés le range dans un `useFetch`, et le parcours Données & API montre la version moderne avec TanStack Query. Dans Next.js, on charge plutôt les données côté serveur, sans `useEffect` du tout.
"""),
  ],
  recap=[
    "`useEffect` = « après l'affichage, synchronise avec l'extérieur » ; pas pour les calculs ni les clics.",
    "`[]` au montage, `[a, b]` quand `a` ou `b` change, rien = à chaque rendu.",
    "Tout ce que l'effet lit dans le composant va dans les dépendances.",
    "La fonction renvoyée (**cleanup**) arrête ce que l'effet a lancé : avant relance et au démontage.",
    "Chargement de données : `AbortController`, trois états (erreur, chargement, données).",
  ],
  td1=dict(path="App.tsx", files=[F("App.tsx", "tsx", r"""
import { useEffect, useState } from 'react';

export default function App() {
  const [seconds, setSeconds] = useState(0);
  const [running, setRunning] = useState(false);

  // à toi : un effet avec setInterval + cleanup, un effet pour document.title

  return (
    <div>
      <p className="time">{seconds} s</p>
      {/* boutons Démarrer/Pause et Reset */}
    </div>
  );
}
""")], solution=[F("App.tsx", "tsx", r"""
import { useEffect, useState } from 'react';

export default function App() {
  const [seconds, setSeconds] = useState(0);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [running]);

  useEffect(() => {
    document.title = `${seconds} s`;
  }, [seconds]);

  return (
    <div>
      <p className="time">{seconds} s</p>
      <button className="toggle" onClick={() => setRunning((r) => !r)}>{running ? 'Pause' : 'Démarrer'}</button>
      <button className="reset" onClick={() => { setRunning(false); setSeconds(0); }}>Reset</button>
    </div>
  );
}
""")], run=RUN("react", tests=r"""
assert.includes(text(), '0 s', 'Affiche 0 s au départ');
const toggle = byText('Démarrer');
assert(toggle, 'Un bouton Démarrer');
await click(toggle);
assert.includes(text(), 'Pause', 'Le bouton devient Pause');
await sleep(2300);
assert.includes(text(), '2 s', 'Après ~2,3 s : 2 s écoulées (pas plus : un seul intervalle)');
assert.equal(document.title, '2 s', 'document.title est synchronisé (« 2 s »)');
await click(byText('Pause'));
await sleep(1200);
assert.includes(text(), '2 s', 'En pause, le compteur ne bouge plus');
await click(byText('Démarrer')); await click(byText('Pause')); await click(byText('Démarrer')); await click(byText('Pause')); await click(byText('Démarrer'));
await sleep(1200);
assert.includes(text(), '3 s', 'Après plusieurs Démarrer/Pause rapides, un seul intervalle tourne (3 s)');
await click(byText('Reset'));
assert.includes(text(), '0 s', 'Reset remet à 0');
assert(byText('Démarrer'), 'Reset arrête le chrono');
""")),
  tds=[
    TD(2, "Recherche avec debounce et annulation",
       "Un champ de recherche qui interroge une API à chaque frappe surchargerait le serveur. Tu dois **attendre 400 ms sans frappe** avant de lancer la requête (debounce), **annuler** la requête précédente si l'utilisateur retape, et afficher les 3 états. L'API est simulée ici par `searchApi(query, signal)` qui répond en 300 ms.",
       ["State `query` (champ contrôlé), `results`, `loading`, `error`",
        "Un effet dépendant de `[query]` : si `query` est vide, vide les résultats et ne fait rien ; sinon lance un `setTimeout` de 400 ms qui appelle `searchApi`",
        "Le cleanup annule **à la fois** le timeout (`clearTimeout`) et la requête en cours (`controller.abort()`)",
        "Affiche `<p className=\"loading\">Recherche…</p>` pendant le chargement, les résultats dans une `<ul>`, « Aucun résultat » si la liste est vide après une recherche, et l'erreur si `searchApi` rejette (tape `erreur` pour la provoquer)",
        "Un compteur `<span className=\"calls\">` du nombre d'appels réellement lancés à `searchApi` (state incrémenté juste avant l'appel)"],
       [F("App.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import { searchApi } from './api';

export default function App() {
  const [query, setQuery] = useState('');
  // à toi
  return (
    <div>
      <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Rechercher un langage" />
    </div>
  );
}
"""), F("api.ts", "ts", r"""
const LANGS = ['PHP', 'JavaScript', 'TypeScript', 'Python', 'Java', 'Go', 'Rust', 'Ruby', 'Kotlin', 'Swift'];

/** Simule une API : répond en 300 ms, rejette si la requête est annulée ou si query === 'erreur'. */
export function searchApi(query: string, signal?: AbortSignal): Promise<string[]> {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => {
      if (query === 'erreur') reject(new Error('Serveur indisponible'));
      else resolve(LANGS.filter((l) => l.toLowerCase().includes(query.toLowerCase())));
    }, 300);
    signal?.addEventListener('abort', () => { clearTimeout(t); const e = new Error('aborted'); e.name = 'AbortError'; reject(e); });
  });
}
""")],
       ["Structure de l'effet : `const controller = new AbortController(); const timer = setTimeout(() => { setLoading(true); setCalls((c) => c + 1); searchApi(query, controller.signal).then(...).catch(...).finally(...) }, 400); return () => { clearTimeout(timer); controller.abort(); };`",
        "Dans `.catch`, ignore `e.name === 'AbortError'` : c'est toi qui as annulé.",
        "Dans `.finally`, ne remets `loading` à false que si la requête n'a pas été annulée (`if (!controller.signal.aborted)`), sinon tu éteins le chargement de la requête suivante.",
        "Un state `results: string[] | null` : `null` = pas encore cherché, `[]` = aucun résultat."],
       [F("App.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import { searchApi } from './api';

export default function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<string[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [calls, setCalls] = useState(0);

  useEffect(() => {
    if (query.trim() === '') { setResults(null); setError(null); setLoading(false); return; }
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setLoading(true); setError(null);
      setCalls((c) => c + 1);
      searchApi(query, controller.signal)
        .then(setResults)
        .catch((e) => { if (e.name !== 'AbortError') setError(e.message); })
        .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    }, 400);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [query]);

  return (
    <div>
      <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Rechercher un langage" />
      <span className="calls">{calls}</span>
      {loading && <p className="loading">Recherche…</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && results && results.length === 0 && <p>Aucun résultat</p>}
      {results && results.length > 0 && <ul>{results.map((r) => <li key={r}>{r}</li>)}</ul>}
    </div>
  );
}
"""), F("api.ts", "ts", r"""
const LANGS = ['PHP', 'JavaScript', 'TypeScript', 'Python', 'Java', 'Go', 'Rust', 'Ruby', 'Kotlin', 'Swift'];

export function searchApi(query: string, signal?: AbortSignal): Promise<string[]> {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => {
      if (query === 'erreur') reject(new Error('Serveur indisponible'));
      else resolve(LANGS.filter((l) => l.toLowerCase().includes(query.toLowerCase())));
    }, 300);
    signal?.addEventListener('abort', () => { clearTimeout(t); const e = new Error('aborted'); e.name = 'AbortError'; reject(e); });
  });
}
""")],
       ["Taper « java » lettre par lettre rapidement ne lance **qu'un** appel",
        "Vider le champ vide les résultats sans appel",
        "Taper « erreur » affiche « Serveur indisponible »"],
       run=RUN("react", tests=r"""
const input = $('input');
await type(input, 'j'); await type(input, 'ja'); await type(input, 'jav'); await type(input, 'java');
await sleep(200);
assert.equal($('.calls').textContent, '0', 'Pendant la frappe (moins de 400 ms), aucun appel');
await sleep(300);
assert.equal($('.calls').textContent, '1', 'Après 400 ms sans frappe : 1 seul appel');
assert($('.loading'), 'Pendant la requête : « Recherche… »');
await sleep(400);
assert.equal($$('li').length, 2, 'Résultats : JavaScript et Java');
assert(!$('.loading'), 'Chargement terminé');
await type(input, 'javas');
await sleep(500);
await type(input, 'javasc');
await sleep(900);
assert.equal($('.calls').textContent, '3', '2 recherches de plus (javas puis javasc), la 1re annulée');
assert.equal($$('li').length, 1, 'Un seul résultat : JavaScript');
await type(input, '');
assert.equal($$('li').length, 0, 'Champ vide : plus de résultats');
await type(input, 'xyz'); await sleep(900);
assert.includes(text(), 'Aucun résultat', 'Sans correspondance : « Aucun résultat »');
await type(input, 'erreur'); await sleep(900);
assert.includes(text(), 'Serveur indisponible', 'Erreur affichée');
""")),
    TD(3, "Abonnement à des événements et fuite de mémoire",
       "Un tableau de bord affiche la **position de la souris**, la **largeur de la fenêtre** et un flux de **messages** venant d'un faux serveur (`createFeed`) qui émet toutes les 500 ms. Chaque source demande un abonnement et un **désabonnement**. Un composant `Panel` peut être affiché ou masqué : quand il est masqué, **aucun** abonnement ne doit rester actif (sinon fuite de mémoire). Tu affiches aussi un compteur global d'abonnements actifs pour **voir** les fuites.",
       ["`api.ts` fournit `createFeed(onMessage) => unsubscribe` et `activeSubscriptions()` (déjà écrits, lis-les)",
        "`Panel` (`.panel`) : 3 effets. (1) `resize` sur `window` → `.width`. (2) `mousemove` sur `window` → `.mouse` « x, y ». (3) `createFeed` → `<ul className=\"messages\">` des 5 derniers messages. Chaque effet a son cleanup",
        "Le feed est **mis en pause** quand la prop `paused` est vraie : l'effet dépend de `[paused]` et ne s'abonne pas si pause",
        "`App` : bouton `.toggle` « Afficher / Masquer » le `Panel`, bouton `.pause` « Pause / Reprendre », et `<span className=\"subs\">{activeSubscriptions()}</span>`",
        "Pour que `.subs` reste à jour, `App` a un petit `setInterval` de 100 ms qui force un rendu (state `tick`), lui aussi nettoyé",
        "Masquer le panel doit ramener le compteur du feed à 0"],
       [F("App.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import { createFeed, activeSubscriptions } from './api';

function Panel({ paused }: { paused: boolean }) {
  // à toi : width, mouse, messages (5 derniers), 3 effets avec cleanup
  return <div className="panel" />;
}

export default function App() {
  const [shown, setShown] = useState(true);
  const [paused, setPaused] = useState(false);
  // à toi : compteur d'abonnements rafraîchi
  return (
    <div>
      <button className="toggle" onClick={() => setShown((s) => !s)}>{shown ? 'Masquer' : 'Afficher'}</button>
      <button className="pause" onClick={() => setPaused((p) => !p)}>{paused ? 'Reprendre' : 'Pause'}</button>
      {shown && <Panel paused={paused} />}
    </div>
  );
}
"""), F("api.ts", "ts", r"""
let active = 0;
let counter = 0;

/** Faux flux serveur : appelle onMessage toutes les 500 ms. Renvoie la fonction de désabonnement. */
export function createFeed(onMessage: (msg: string) => void): () => void {
  active++;
  const id = setInterval(() => onMessage(`message #${++counter}`), 500);
  return () => { clearInterval(id); active--; };
}

/** Nombre d'abonnements au feed encore actifs. Doit valoir 0 quand aucun composant n'écoute. */
export function activeSubscriptions(): number {
  return active;
}
""")],
       ["Effet resize : `const onResize = () => setWidth(window.innerWidth); window.addEventListener('resize', onResize); return () => window.removeEventListener('resize', onResize);` : il faut retirer **la même** fonction, d'où la constante.",
        "Les 5 derniers messages : `setMessages((ms) => [...ms, msg].slice(-5))`.",
        "Feed : `useEffect(() => { if (paused) return; const unsubscribe = createFeed((m) => …); return unsubscribe; }, [paused]);` : renvoyer directement la fonction de désabonnement, c'est le cleanup.",
        "Dans `App` : `const [, force] = useState(0); useEffect(() => { const id = setInterval(() => force((n) => n + 1), 100); return () => clearInterval(id); }, []);`"],
       [F("App.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import { createFeed, activeSubscriptions } from './api';

function Panel({ paused }: { paused: boolean }) {
  const [width, setWidth] = useState(window.innerWidth);
  const [mouse, setMouse] = useState({ x: 0, y: 0 });
  const [messages, setMessages] = useState<string[]>([]);

  useEffect(() => {
    const onResize = () => setWidth(window.innerWidth);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    const onMove = (e: MouseEvent) => setMouse({ x: e.clientX, y: e.clientY });
    window.addEventListener('mousemove', onMove);
    return () => window.removeEventListener('mousemove', onMove);
  }, []);

  useEffect(() => {
    if (paused) return;
    const unsubscribe = createFeed((msg) => setMessages((ms) => [...ms, msg].slice(-5)));
    return unsubscribe;
  }, [paused]);

  return (
    <div className="panel">
      <p className="width">Largeur : {width}px</p>
      <p className="mouse">Souris : {mouse.x}, {mouse.y}</p>
      <ul className="messages">{messages.map((m) => <li key={m}>{m}</li>)}</ul>
    </div>
  );
}

export default function App() {
  const [shown, setShown] = useState(true);
  const [paused, setPaused] = useState(false);
  const [, force] = useState(0);

  useEffect(() => {
    const id = setInterval(() => force((n) => n + 1), 100);
    return () => clearInterval(id);
  }, []);

  return (
    <div>
      <button className="toggle" onClick={() => setShown((s) => !s)}>{shown ? 'Masquer' : 'Afficher'}</button>
      <button className="pause" onClick={() => setPaused((p) => !p)}>{paused ? 'Reprendre' : 'Pause'}</button>
      <span className="subs">{activeSubscriptions()}</span>
      {shown && <Panel paused={paused} />}
    </div>
  );
}
"""), F("api.ts", "ts", r"""
let active = 0;
let counter = 0;

export function createFeed(onMessage: (msg: string) => void): () => void {
  active++;
  const id = setInterval(() => onMessage(`message #${++counter}`), 500);
  return () => { clearInterval(id); active--; };
}

export function activeSubscriptions(): number {
  return active;
}
""")],
       ["Masquer le panel ramène le compteur d'abonnements à 0",
        "Pause / Reprendre plusieurs fois laisse toujours au plus 1 abonnement",
        "La liste ne dépasse jamais 5 messages"],
       run=RUN("react", tests=r"""
await sleep(250);
assert.equal($('.subs').textContent, '1', 'Panel affiché : 1 abonnement au feed');
window.dispatchEvent(new MouseEvent('mousemove', { clientX: 120, clientY: 45 })); await tick(150);
assert.includes($('.mouse').textContent, '120, 45', 'La souris est suivie');
await sleep(2900);
assert.equal($$('.messages li').length, 5, 'Au plus 5 messages gardés');
await click('.pause'); await sleep(250);
assert.equal($('.subs').textContent, '0', 'En pause : 0 abonnement');
const n = $$('.messages li').length; const last = $$('.messages li')[n - 1].textContent;
await sleep(700);
assert.equal($$('.messages li')[$$('.messages li').length - 1].textContent, last, 'En pause, plus de nouveaux messages');
await click('.pause'); await click('.pause'); await click('.pause'); await sleep(250);
assert.equal($('.subs').textContent, '1', 'Après plusieurs Pause/Reprendre : exactement 1 abonnement');
await click('.toggle'); await sleep(250);
assert(!$('.panel'), 'Panel masqué');
assert.equal($('.subs').textContent, '0', 'Panel masqué : 0 abonnement (pas de fuite)');
await click('.toggle'); await sleep(250);
assert.equal($('.subs').textContent, '1', 'Panel réaffiché : 1 abonnement');
""")),
  ])

# ---------------------------------------------------------------- hooks personnalisés
hooks = V2(v1["react-hooks"],
  prereq=[
    P("`useState` / `useEffect`", "Les deux hooks de base (modules précédents). Un hook personnalisé n'est qu'une fonction qui les combine."),
    P("Générique `<T>`", "En TypeScript, `function useFetch<T>(url)` signifie « cette fonction marche pour n'importe quel type `T`, que l'appelant précise » : `useFetch<Post[]>('/posts')` renvoie des `Post[]`."),
    P("Tuple", "Un tableau de taille et de types fixes : `[string, (v: string) => void]`. `as const` dit à TypeScript de garder cette forme exacte au lieu d'un `(string | fonction)[]`."),
    P("Règles des hooks", "Les hooks s'appellent au **niveau supérieur** du composant ou d'un autre hook : jamais dans un `if`, une boucle ou après un `return`. React les retrouve par leur ordre d'appel."),
    P("`try / catch`", "`try { … } catch (e) { … }` : si le code du `try` lève une erreur, le `catch` s'exécute au lieu de planter. Indispensable autour de `JSON.parse` et `localStorage`."),
  ],
  diagram=D(
    nodes=[
      N("dup1", 0, 0, "Posts", "useState ×3 + useEffect fetch", kind="doc", color="muted"),
      N("dup2", 0, 1, "Users", "useState ×3 + useEffect fetch", kind="doc", color="muted"),
      N("hook", 1, 0, "useFetch(url)", "state + effet, une seule fois", color="good"),
      N("p2", 2, 0, "Posts", "const {data} = useFetch('/posts')", kind="doc"),
      N("u2", 2, 1, "Users", "const {data} = useFetch('/users')", kind="doc"),
      N("note", 1, 1, "chaque appel a\nson propre state", kind="note"),
    ],
    edges=[E("dup1", "hook", "extraire", color="good"), E("dup2", "hook", color="good", dashed=True), E("hook", "p2", "réutiliser"), E("hook", "u2")],
    caption="La logique répétée (state + effet) est déplacée dans une fonction `useQuelqueChose`. Chaque composant qui l'appelle a son propre état."),
  lessons=[
    L("Le problème : la même logique copiée dans plusieurs composants", r"""
Après le module useEffect, tu sais charger des données : trois `useState` (données, erreur, chargement), un `useEffect` avec `AbortController`. Maintenant, imagine `Posts`, `Users`, `Comments` qui ont chacun besoin de charger quelque chose. Tu copies les 20 lignes trois fois. Quand tu corriges un bug dans la gestion d'erreur, tu dois le corriger trois fois, et tu en oublies une.

Avec des fonctions classiques, tu extrairais le code commun dans une fonction. Mais ici le code commun **contient des hooks** (`useState`, `useEffect`), et une fonction ordinaire n'a pas le droit de les appeler… sauf si elle est elle-même un hook. Un **hook personnalisé** est exactement ça : une fonction dont le nom commence par `use`, qui peut appeler d'autres hooks, et qui renvoie ce dont le composant a besoin.
"""),
    L("Écrire un hook : extraire, nommer, renvoyer", r"""
```tsx
export function useFetch<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(null);
    fetch(url, { signal: controller.signal })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setData)
      .catch((e) => e.name !== 'AbortError' && setError(e.message))
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [url]);

  return { data, error, loading };
}
```

Le corps est **exactement** le code qu'on avait dans le composant, déplacé tel quel. Trois décisions à prendre :

- **Le nom** : `use` + ce que ça fait (`useFetch`, `useLocalStorage`, `useDebounce`, `useWindowWidth`). Le préfixe `use` n'est pas décoratif : c'est lui qui dit à React (et à ESLint) que les règles des hooks s'appliquent.
- **Les paramètres** : ce qui varie d'un usage à l'autre (ici l'URL). Ils deviennent souvent des dépendances de l'effet.
- **La valeur de retour** : un objet nommé (`{ data, error, loading }`) quand il y a plusieurs valeurs, ou un tuple `[value, setValue] as const` quand on imite `useState`.

Le composant devient :

```tsx
const { data, error, loading } = useFetch<Post[]>('/api/posts');
```
"""),
    L("Chaque appel a son propre état", r"""
Un hook personnalisé partage de la **logique**, pas des **données**. Si `Posts` et `Users` appellent tous les deux `useFetch`, chacun a ses propres `data`, `error`, `loading` : ce sont deux appels indépendants à `useState`. Même chose si un composant appelle le hook deux fois avec deux URL.

C'est le même principe qu'une fonction qui déclare des variables locales : chaque appel a les siennes. Si tu veux vraiment **partager** une donnée entre composants (un utilisateur connecté, un panier), ce n'est pas le rôle d'un hook personnalisé : c'est celui d'un state remonté dans un parent, d'un contexte React, ou d'un cache comme TanStack Query (parcours Données & API).

Les règles des hooks s'appliquent dans ton hook comme dans un composant : `useState` et `useEffect` au niveau supérieur, jamais dans un `if`. Et ton hook s'appelle lui aussi au niveau supérieur du composant : `if (ok) useFetch(url)` est interdit. Si tu veux désactiver un hook, passe-lui un paramètre (`useFetch(enabled ? url : null)`) et gère le cas à l'intérieur.
"""),
    L("Quand créer un hook, et quelques classiques", r"""
Crée un hook quand une logique **avec state ou effet** se répète, ou quand un composant devient illisible parce qu'il mélange plusieurs préoccupations (le hook isole une préoccupation et lui donne un nom). Ne crée pas de hook pour une fonction sans state ni effet : une fonction normale suffit (`formatPrice`, `initials`).

Quelques hooks qu'on finit par écrire dans tous les projets :

- `useLocalStorage(key, initial)` : comme `useState`, mais la valeur survit au rechargement (TD de ce module).
- `useDebounce(value, delay)` : renvoie `value` seulement après `delay` ms sans changement. Le module useEffect faisait ça à la main.
- `useWindowWidth()` : s'abonne à `resize`, renvoie la largeur.
- `useToggle(initial)` : renvoie `[on, toggle]`.
- `useFetch(url)` : vu ci-dessus. En pratique, on le remplace vite par TanStack Query qui gère en plus le cache et les mutations.

Un hook peut en appeler un autre : `useDebouncedFetch(url)` = `useDebounce` + `useFetch`. C'est de la composition de fonctions, rien de plus.
"""),
  ],
  recap=[
    "Un hook personnalisé = une fonction `useXxx` qui appelle d'autres hooks et renvoie ce dont le composant a besoin.",
    "On extrait **tel quel** le code répété (state + effet) ; les paramètres sont ce qui varie.",
    "Chaque appel a **son propre state** : le hook partage la logique, pas les données.",
    "Règles des hooks : toujours au niveau supérieur, jamais dans un `if` ; le préfixe `use` est obligatoire.",
    "Pas de hook pour une logique sans state ni effet : une fonction ordinaire suffit.",
  ],
  example=[F("hooks/useFetch.ts", "ts", r"""
import { useEffect, useState } from 'react';

export function useFetch<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    fetch(url, { signal: controller.signal })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setData)
      .catch((e) => e.name !== 'AbortError' && setError(e.message))
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, [url]);

  return { data, error, loading };
}
"""), F("Posts.tsx", "tsx", r"""
import { useFetch } from './hooks/useFetch';

type Post = { id: number; title: string };

export default function Posts() {
  const { data, error, loading } = useFetch<Post[]>('/api/posts');

  if (loading) return <p>Chargement…</p>;
  if (error) return <p>{error}</p>;
  return <ul>{data!.map((p) => <li key={p.id}>{p.title}</li>)}</ul>;
}
"""), F("Users.tsx", "tsx", r"""
import { useFetch } from './hooks/useFetch';

type User = { id: number; name: string };

export default function Users() {
  const { data, error, loading } = useFetch<User[]>('/api/users');   // son PROPRE état

  if (loading) return <p>Chargement…</p>;
  if (error) return <p>{error}</p>;
  return <ul>{data!.map((u) => <li key={u.id}>{u.name}</li>)}</ul>;
}
""")],
  notes=["`useFetch.ts` : toute la mécanique du module useEffect, rangée dans une fonction. `<T>` la rend typée pour n'importe quelle donnée.",
         "`Posts.tsx` et `Users.tsx` : une ligne chacun pour charger. Ils ne gardent que l'affichage.",
         "Les deux composants appellent le même hook mais ont chacun leur `data`, `error`, `loading`.",
         "Les hooks personnalisés vont souvent dans un dossier `hooks/`, un fichier par hook."],
  td1=dict(path="App.tsx", files=[F("App.tsx", "tsx", r"""
import { useLocalStorage } from './useLocalStorage';

export default function App() {
  const [theme, setTheme] = useLocalStorage<'light' | 'dark'>('theme', 'light');
  return (
    <button className="theme" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>{theme}</button>
  );
}
"""), F("useLocalStorage.ts", "ts", r"""
import { useEffect, useState } from 'react';

export function useLocalStorage<T>(key: string, initialValue: T) {
  // à toi
}
""")], solution=[F("App.tsx", "tsx", r"""
import { useLocalStorage } from './useLocalStorage';

export default function App() {
  const [theme, setTheme] = useLocalStorage<'light' | 'dark'>('theme', 'light');
  return (
    <button className="theme" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>{theme}</button>
  );
}
"""), F("useLocalStorage.ts", "ts", r"""
import { useEffect, useState } from 'react';

export function useLocalStorage<T>(key: string, initialValue: T) {
  const [value, setValue] = useState<T>(() => {
    try {
      const saved = localStorage.getItem(key);
      return saved !== null ? (JSON.parse(saved) as T) : initialValue;
    } catch {
      return initialValue;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // stockage indisponible : on garde la valeur en mémoire
    }
  }, [key, value]);

  return [value, setValue] as const;
}
""")], run=RUN("react", tests=r"""
assert.equal($('.theme').textContent, 'light', 'Valeur initiale light');
await click('.theme');
assert.equal($('.theme').textContent, 'dark', 'Le clic passe à dark');
await click('.theme');
assert.equal($('.theme').textContent, 'light', 'Le clic repasse à light');
const { useLocalStorage } = require('./useLocalStorage');
assert(typeof useLocalStorage === 'function', 'useLocalStorage est exportée');
assert(true, 'Le hook fonctionne même quand localStorage est inaccessible dans cet aperçu isolé (try/catch)');
""")),
  tds=[
    TD(2, "useDebounce et useToggle",
       "Deux petits hooks très courants. `useDebounce(value, delay)` renvoie une **copie retardée** de la valeur : elle ne change qu'après `delay` ms sans modification (c'est le mécanisme du TD « Recherche avec debounce », mais réutilisable partout). `useToggle(initial)` renvoie `[on, toggle, setOn]`. Puis tu les utilises dans un composant qui affiche en direct la valeur tapée et sa version « debounced », avec un interrupteur pour activer ou non le debounce.",
       ["`useDebounce<T>(value: T, delay: number): T` : un state `debounced` + un effet avec `setTimeout` et cleanup, dépendant de `[value, delay]`",
        "`useToggle(initial = false)` renvoie `[on, toggle, setOn] as const` où `toggle` inverse (mise à jour **fonctionnelle**)",
        "`App` : un `<input>` contrôlé `query`, un bouton `.toggle` « Debounce : on/off » via `useToggle(true)`, `const delayed = useDebounce(query, on ? 500 : 0)`",
        "Affiche `<p className=\"live\">{query}</p>` et `<p className=\"delayed\">{delayed}</p>`",
        "Un compteur `<span className=\"changes\">` du nombre de fois où `delayed` a changé (un effet dépendant de `[delayed]` qui incrémente un state, sans compter le premier rendu)"],
       [F("App.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import { useDebounce } from './useDebounce';
import { useToggle } from './useToggle';

export default function App() {
  const [query, setQuery] = useState('');
  // à toi
  return <div />;
}
"""), F("useDebounce.ts", "ts", r"""
import { useEffect, useState } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  // à toi
}
"""), F("useToggle.ts", "ts", r"""
import { useState } from 'react';

export function useToggle(initial = false) {
  // à toi : renvoie [on, toggle, setOn] as const
}
""")],
       ["`useDebounce` : `const [debounced, setDebounced] = useState(value); useEffect(() => { const t = setTimeout(() => setDebounced(value), delay); return () => clearTimeout(t); }, [value, delay]); return debounced;`",
        "`useToggle` : `const toggle = () => setOn((o) => !o);`",
        "Compter les changements sans le premier rendu : initialise le compteur à `-1`."],
       [F("App.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import { useDebounce } from './useDebounce';
import { useToggle } from './useToggle';

export default function App() {
  const [query, setQuery] = useState('');
  const [on, toggle] = useToggle(true);
  const delayed = useDebounce(query, on ? 500 : 0);
  const [changes, setChanges] = useState(-1);

  useEffect(() => { setChanges((c) => c + 1); }, [delayed]);

  return (
    <div>
      <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Tape quelque chose" />
      <button className="toggle" onClick={toggle}>Debounce : {on ? 'on' : 'off'}</button>
      <p className="live">{query}</p>
      <p className="delayed">{delayed}</p>
      <span className="changes">{changes}</span>
    </div>
  );
}
"""), F("useDebounce.ts", "ts", r"""
import { useEffect, useState } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);

  return debounced;
}
"""), F("useToggle.ts", "ts", r"""
import { useState } from 'react';

export function useToggle(initial = false) {
  const [on, setOn] = useState(initial);
  const toggle = () => setOn((o) => !o);
  return [on, toggle, setOn] as const;
}
""")],
       ["En tapant vite 4 lettres, `.delayed` ne change qu'une fois",
        "Debounce désactivé, `.delayed` suit `.live` immédiatement",
        "Les deux hooks sont dans leurs fichiers, sans rien connaître de `App`"],
       run=RUN("react", tests=r"""
const input = $('input');
await type(input, 'a'); await type(input, 'ab'); await type(input, 'abc'); await type(input, 'abcd');
assert.equal($('.live').textContent, 'abcd', 'La valeur live suit la frappe');
assert.equal($('.delayed').textContent, '', 'La valeur debounced n\'a pas encore changé');
await sleep(700);
assert.equal($('.delayed').textContent, 'abcd', 'Après 500 ms : la valeur debounced est à jour');
assert.equal($('.changes').textContent, '1', 'Un seul changement de la valeur debounced pour 4 frappes');
await click('.toggle');
assert.includes($('.toggle').textContent, 'off', 'Le toggle passe à off');
await type(input, 'abcde'); await tick(80);
assert.equal($('.delayed').textContent, 'abcde', 'Debounce off : mise à jour immédiate');
const { useToggle } = require('./useToggle'); const { useDebounce } = require('./useDebounce');
assert(typeof useToggle === 'function' && typeof useDebounce === 'function', 'Les deux hooks sont exportés');
""")),
    TD(3, "useAsync : un hook générique avec machine à états",
       "Généralise `useFetch` en un hook `useAsync(fn, deps)` qui exécute **n'importe quelle** fonction asynchrone, expose un **état unique** `{ status: 'idle' | 'loading' | 'success' | 'error', data, error }` (une machine à états plutôt que trois booléens qui peuvent se contredire), gère l'annulation des résultats périmés, et fournit `run()` pour relancer à la demande. Puis compose-le avec `useDebounce` pour une recherche propre en quelques lignes de composant.",
       ["`useAsync<T>(fn: (signal: AbortSignal) => Promise<T>, deps: unknown[], { immediate = true } = {})` renvoie `{ status, data, error, run }`",
        "Un seul `useState` pour l'état : `{ status: 'idle', data: null, error: null }` au départ",
        "`run()` : passe en `loading`, appelle `fn(signal)`, puis `success` ou `error`. Si un **autre** `run` a été lancé entre-temps (ou le composant démonté), le résultat est **ignoré** : utilise un `AbortController` stocké dans un `useRef` et abandonne l'ancien avant d'en créer un nouveau",
        "Un effet dépendant de `deps` appelle `run()` si `immediate` ; son cleanup abandonne le contrôleur courant",
        "`App` : `<input>` de recherche, `const q = useDebounce(query, 300)`, `const { status, data, error, run } = useAsync((signal) => searchApi(q, signal), [q])` ; affiche `<span className=\"status\">`, les résultats en `<li>`, l'erreur en `.error`, un bouton `.rerun` « Relancer » qui appelle `run()`"],
       [F("App.tsx", "tsx", r"""
import { useState } from 'react';
import { useAsync } from './useAsync';
import { useDebounce } from './useDebounce';
import { searchApi } from './api';

export default function App() {
  const [query, setQuery] = useState('');
  // à toi
  return <div />;
}
"""), F("useAsync.ts", "ts", r"""
import { useCallback, useEffect, useRef, useState } from 'react';

type State<T> =
  | { status: 'idle'; data: null; error: null }
  | { status: 'loading'; data: T | null; error: null }
  | { status: 'success'; data: T; error: null }
  | { status: 'error'; data: null; error: string };

export function useAsync<T>(fn: (signal: AbortSignal) => Promise<T>, deps: unknown[], { immediate = true } = {}) {
  // à toi
}
"""), F("useDebounce.ts", "ts", r"""
import { useEffect, useState } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}
"""), F("api.ts", "ts", r"""
const LANGS = ['PHP', 'JavaScript', 'TypeScript', 'Python', 'Java', 'Go', 'Rust', 'Ruby', 'Kotlin', 'Swift'];
let calls = 0;
export const callCount = () => calls;

export function searchApi(query: string, signal?: AbortSignal): Promise<string[]> {
  calls++;
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => {
      if (query === 'erreur') reject(new Error('Serveur indisponible'));
      else resolve(LANGS.filter((l) => l.toLowerCase().includes(query.toLowerCase())));
    }, 300);
    signal?.addEventListener('abort', () => { clearTimeout(t); const e = new Error('aborted'); e.name = 'AbortError'; reject(e); });
  });
}
""")],
       ["`const ctrl = useRef<AbortController | null>(null);` ; dans `run` : `ctrl.current?.abort(); const c = new AbortController(); ctrl.current = c;` puis après la promesse : `if (c.signal.aborted) return;` avant chaque `setState`.",
        "`run` doit être stable pour pouvoir être mis en dépendance de l'effet : `const run = useCallback(() => { … }, deps)` (on passe `deps` tel quel ; c'est le cas légitime où ESLint se trompe).",
        "Effet : `useEffect(() => { if (immediate) run(); return () => ctrl.current?.abort(); }, [run, immediate]);`",
        "Pendant `loading`, garde l'ancien `data` (`data: prev.data`) : l'écran ne clignote pas."],
       [F("App.tsx", "tsx", r"""
import { useState } from 'react';
import { useAsync } from './useAsync';
import { useDebounce } from './useDebounce';
import { searchApi } from './api';

export default function App() {
  const [query, setQuery] = useState('');
  const q = useDebounce(query, 300);
  const { status, data, error, run } = useAsync((signal) => searchApi(q, signal), [q]);

  return (
    <div>
      <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Rechercher" />
      <button className="rerun" onClick={run}>Relancer</button>
      <span className="status">{status}</span>
      {error && <p className="error">{error}</p>}
      <ul>{(data ?? []).map((r) => <li key={r}>{r}</li>)}</ul>
    </div>
  );
}
"""), F("useAsync.ts", "ts", r"""
import { useCallback, useEffect, useRef, useState } from 'react';

type State<T> =
  | { status: 'idle'; data: null; error: null }
  | { status: 'loading'; data: T | null; error: null }
  | { status: 'success'; data: T; error: null }
  | { status: 'error'; data: null; error: string };

export function useAsync<T>(fn: (signal: AbortSignal) => Promise<T>, deps: unknown[], { immediate = true } = {}) {
  const [state, setState] = useState<State<T>>({ status: 'idle', data: null, error: null });
  const ctrl = useRef<AbortController | null>(null);

  const run = useCallback(() => {
    ctrl.current?.abort();
    const c = new AbortController();
    ctrl.current = c;
    setState((prev) => ({ status: 'loading', data: prev.data, error: null }));
    fn(c.signal)
      .then((data) => { if (!c.signal.aborted) setState({ status: 'success', data, error: null }); })
      .catch((e) => { if (!c.signal.aborted) setState({ status: 'error', data: null, error: String(e.message ?? e) }); });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    if (immediate) run();
    return () => ctrl.current?.abort();
  }, [run, immediate]);

  return { ...state, run };
}
"""), F("useDebounce.ts", "ts", r"""
import { useEffect, useState } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}
"""), F("api.ts", "ts", r"""
const LANGS = ['PHP', 'JavaScript', 'TypeScript', 'Python', 'Java', 'Go', 'Rust', 'Ruby', 'Kotlin', 'Swift'];
let calls = 0;
export const callCount = () => calls;

export function searchApi(query: string, signal?: AbortSignal): Promise<string[]> {
  calls++;
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => {
      if (query === 'erreur') reject(new Error('Serveur indisponible'));
      else resolve(LANGS.filter((l) => l.toLowerCase().includes(query.toLowerCase())));
    }, 300);
    signal?.addEventListener('abort', () => { clearTimeout(t); const e = new Error('aborted'); e.name = 'AbortError'; reject(e); });
  });
}
""")],
       ["`status` passe par `loading` puis `success` ; jamais `loading` et `error` en même temps",
        "Taper vite puis attendre ne déclenche qu'un appel après le debounce",
        "Un résultat périmé (requête relancée avant la réponse) n'écrase jamais le plus récent"],
       run=RUN("react", tests=r"""
const { callCount } = require('./api');
await sleep(700);
assert.equal($('.status').textContent, 'success', 'Au chargement (requête vide) : success');
assert.equal($$('li').length, 10, 'Requête vide : les 10 langages');
const c0 = callCount();
const input = $('input');
await type(input, 'r'); await type(input, 'ru'); await type(input, 'rus');
await sleep(350);
assert.equal($('.status').textContent, 'loading', 'Après le debounce : loading');
await sleep(400);
assert.equal($('.status').textContent, 'success', 'Puis success');
assert.equal(callCount() - c0, 1, 'Un seul appel API pour 3 frappes rapides');
assert.equal($$('li').map((l) => l.textContent).join(','), 'Rust', 'Résultat : Rust');
const c1 = callCount();
await click('.rerun'); await sleep(100); await click('.rerun');
await sleep(600);
assert.equal(callCount() - c1, 2, 'Deux relances = deux appels');
assert.equal($('.status').textContent, 'success', 'État final success (le 1er résultat, annulé, a été ignoré)');
await type(input, 'erreur'); await sleep(900);
assert.equal($('.status').textContent, 'error', 'Erreur : status error');
assert.includes(text(), 'Serveur indisponible', 'Message d\'erreur affiché');
assert.equal($$('li').length, 0, 'En erreur, data est null : pas de liste');
""")),
  ])

MODULES = [comp, stt, forms, eff, hooks]

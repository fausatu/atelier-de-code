from common_v1 import M, Q, TD, code

T = "react"

MODULES = [
M("react-composants", T, "Composants, JSX & props", 15,
  "Comprendre ce qu'est un composant et comment les données y entrent.",
  "Sans composants, l'interface est un gros bloc de HTML à mettre à jour à la main. React la découpe en fonctions réutilisables.",
  ["Un **composant** est une fonction qui renvoie du JSX",
   "Le parent lui passe des **props** (ses paramètres)",
   "React **appelle** la fonction et obtient une description de l'UI",
   "React met à jour **le DOM** pour qu'il corresponde"],
  ["JSX ressemble à du HTML mais c'est du JavaScript : `{ }` insère une expression.",
   "Les props sont **en lecture seule** : un composant ne modifie jamais ses props.",
   "Nom en **PascalCase** (`UserCard`), sinon React le prend pour une balise HTML.",
   "Listes : `items.map(item => <Item key={item.id} … />)`. La `key` stable et unique permet à React de savoir quel élément a changé.",
   "`className` au lieu de `class` ; un seul élément racine ou un fragment `<>…</>`."],
  ["Utiliser l'index du tableau comme `key` sur une liste qui se réordonne.",
   "Écrire `Card()` au lieu de `<Card />`."],
  code("tsx", r"""
type User = { id: number; name: string; role: string; online: boolean };

function Badge({ online }: { online: boolean }) {
  return <span className={online ? 'badge on' : 'badge'}>{online ? 'En ligne' : 'Absent'}</span>;
}

function UserCard({ user }: { user: User }) {
  return (
    <article className="card">
      <h3>{user.name}</h3>
      <p>{user.role}</p>
      <Badge online={user.online} />
    </article>
  );
}

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
"""),
  ["`Team` → `UserCard` → `Badge` : les données descendent par les props.",
   "`key={u.id}` : stable même si la liste est triée ou filtrée.",
   "Le `return` anticipé gère le cas « liste vide »."],
  [Q("Un composant peut-il modifier ses props ?",
     ["Oui", "Non, elles sont en lecture seule", "Seulement les objets", "Seulement dans useEffect"], 1,
     "Pour une donnée qui change, on utilise le state (module suivant)."),
   Q("À quoi sert `key` dans une liste ?",
     ["Au style CSS", "À identifier chaque élément d'un rendu à l'autre", "À trier", "À l'accessibilité"], 1,
     "Sans clé stable, React peut mélanger l'état des éléments."),
   Q("Pourquoi `<userCard />` ne fonctionne pas ?",
     ["Il manque des props", "Une minuscule = balise HTML pour React", "Il faut un fragment", "Il manque export"], 1,
     "React cherche une balise HTML `<usercard>`, qui n'existe pas.")],
  TD("Liste de produits",
     "Affiche un catalogue à partir d'un tableau.",
     ["`ProductCard` : nom, prix en euros, badge « Rupture » si stock = 0",
      "`ProductList` reçoit `products` et affiche une carte par produit",
      "Message « Aucun produit » si la liste est vide",
      "Bonus : `ProductList` reçoit `onlyAvailable` (booléen) et filtre"],
     code("tsx", r"""
const products = [
  { id: 'p1', name: 'Clavier', price: 49.9, stock: 12 },
  { id: 'p2', name: 'Souris', price: 19.5, stock: 0 },
  { id: 'p3', name: 'Écran', price: 189, stock: 3 },
];

function ProductCard(/* props */) {
  // à toi
}

export default function ProductList({ products }) {
  // à toi
}
"""),
     ["Prix : `price.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })`",
      "Affichage conditionnel : `{product.stock === 0 && <span>Rupture</span>}`",
      "Filtre : `const visible = onlyAvailable ? products.filter(p => p.stock > 0) : products;`"],
     code("tsx", r"""
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

export default function ProductList({
  products,
  onlyAvailable = false,
}: {
  products: Product[];
  onlyAvailable?: boolean;
}) {
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
"""),
     ["Chaque carte a une `key` stable (l'id)",
      "Aucune prop n'est modifiée (le filtre crée un nouveau tableau)"])),

M("react-state", T, "State & re-rendu", 15,
  "Comprendre ce qui déclenche un nouveau rendu, et pourquoi la valeur ne change pas « tout de suite ».",
  "Une variable normale est remise à zéro à chaque rendu et ne met pas l'écran à jour. Le state, si.",
  ["`useState(0)` donne la **valeur** et une fonction pour la **changer**",
   "`setCount(…)` **demande** un nouveau rendu",
   "React **rappelle ton composant** avec la nouvelle valeur",
   "Le nouveau JSX est comparé à l'ancien et le DOM est **mis à jour**"],
  ["Chaque rendu voit un **instantané** du state : juste après `setCount(count + 1)`, `count` vaut encore l'ancienne valeur.",
   "Si la nouvelle valeur dépend de l'ancienne : `setCount(c => c + 1)`.",
   "Ne jamais muter : tableau → `setItems([...items, x])`, objet → `setUser({ ...user, name })`.",
   "Ce qui se **calcule** à partir du state n'est pas un state (un total à partir des articles)."],
  ["`items.push(x); setItems(items)` : même référence, React ne voit pas le changement.",
   "Appeler `setX` directement dans le corps du composant : boucle infinie."],
  code("tsx", r"""
import { useState } from 'react';

export default function Counter() {
  const [count, setCount] = useState(0);
  const [history, setHistory] = useState<number[]>([]);

  function add(n: number) {
    setCount((c) => c + n);          // basé sur la valeur la plus récente
    setHistory((h) => [...h, n]);    // nouveau tableau, pas de push
  }

  const actions = history.length;    // dérivé : pas besoin de state

  return (
    <div>
      <p>Compteur : {count} ({actions} actions)</p>
      <button onClick={() => add(1)}>+1</button>
      <button onClick={() => add(-1)} disabled={count === 0}>-1</button>
      <button onClick={() => { setCount(0); setHistory([]); }}>Reset</button>
    </div>
  );
}
"""),
  ["Deux states indépendants : `count` et `history`.",
   "`c => c + n` évite de lire un instantané périmé.",
   "`actions` est recalculé à chaque rendu, gratuitement."],
  [Q("`setCount(count + 1); setCount(count + 1);` avec count = 0. Valeur affichée ensuite ?",
     ["2", "1", "0", "Erreur"], 1,
     "Les deux lignes lisent le même instantané (0). Avec `c => c + 1`, on obtiendrait 2."),
   Q("Comment ajouter un élément à un state tableau ?",
     ["`items.push(x)`", "`setItems([...items, x])`", "`items[items.length] = x`", "`setItems(items)`"], 1,
     "Il faut une nouvelle référence pour que React détecte le changement."),
   Q("Un panier a `items` en state. Le total doit-il être un state ?",
     ["Oui, toujours", "Non, on le calcule à partir de `items`", "Seulement s'il est grand", "Dans un useEffect"], 1,
     "Deux sources de vérité finissent toujours par diverger.")],
  TD("Quantités du panier",
     "Gère les quantités d'un petit panier.",
     ["State : un objet `{ [productId]: quantité }`",
      "Boutons + et − par produit, jamais de quantité négative",
      "Total en euros **calculé** (pas de state)",
      "Bouton « Vider »"],
     code("tsx", r"""
import { useState } from 'react';

const products = [
  { id: 'p1', name: 'Café', price: 4.5 },
  { id: 'p2', name: 'Croissant', price: 1.2 },
  { id: 'p3', name: 'Jus', price: 3 },
];

export default function Cart() {
  // à toi
}
"""),
     ["`const [qty, setQty] = useState<Record<string, number>>({});`",
      "Changer : `setQty(q => ({ ...q, [id]: Math.max(0, (q[id] ?? 0) + delta) }))`",
      "Total : `products.reduce((s, p) => s + p.price * (qty[p.id] ?? 0), 0)`"],
     code("tsx", r"""
export default function Cart() {
  const [qty, setQty] = useState<Record<string, number>>({});

  function change(id: string, delta: number) {
    setQty((q) => ({ ...q, [id]: Math.max(0, (q[id] ?? 0) + delta) }));
  }

  const total = products.reduce((sum, p) => sum + p.price * (qty[p.id] ?? 0), 0);

  return (
    <div>
      <ul>
        {products.map((p) => (
          <li key={p.id}>
            {p.name}
            <button onClick={() => change(p.id, -1)} disabled={!qty[p.id]}>−</button>
            {qty[p.id] ?? 0}
            <button onClick={() => change(p.id, 1)}>+</button>
          </li>
        ))}
      </ul>
      <p>Total : {total.toFixed(2)} €</p>
      <button onClick={() => setQty({})}>Vider</button>
    </div>
  );
}
"""),
     ["Cliquer vite sur + plusieurs fois compte chaque clic",
      "Le total n'est pas dans un `useState`"])),

M("react-forms", T, "Événements & formulaires", 15,
  "Gérer les saisies avec des champs contrôlés et faire remonter les données au parent.",
  "Pour valider, vider ou envoyer un formulaire, React doit connaître la valeur des champs à tout moment.",
  ["Le champ affiche une valeur **venant du state** (`value={title}`)",
   "Chaque frappe déclenche **onChange**",
   "onChange **met à jour le state**",
   "Le parent reçoit le résultat via une **fonction en prop** (`onAdd`)"],
  ["Champ contrôlé : `value` + `onChange`. Le state est la seule source de vérité.",
   "`onSubmit` sur le `<form>` + `e.preventDefault()` pour éviter le rechargement de la page.",
   "Les données **descendent** (props), les événements **remontent** (callbacks `onQuelqueChose`).",
   "Deux composants frères ont besoin de la même donnée ? **Remonte le state** dans leur parent commun."],
  ["`onClick={handle()}` appelle la fonction pendant le rendu. Écris `onClick={handle}` ou `onClick={() => handle(id)}`.",
   "Oublier `preventDefault` : la page se recharge et le state est perdu."],
  code("tsx", r"""
import { useState, FormEvent } from 'react';

type Todo = { id: string; title: string };

function TodoForm({ onAdd }: { onAdd: (title: string) => void }) {
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
      <button type="submit">Ajouter</button>
    </form>
  );
}

export default function TodoApp() {
  const [todos, setTodos] = useState<Todo[]>([]);

  return (
    <>
      <TodoForm onAdd={(title) => setTodos((t) => [...t, { id: crypto.randomUUID(), title }])} />
      <ul>
        {todos.map((t) => <li key={t.id}>{t.title}</li>)}
      </ul>
    </>
  );
}
"""),
  ["`TodoForm` ne connaît pas la liste : il signale juste « on a ajouté ce titre ».",
   "La liste vit dans `TodoApp`, qui décide quoi en faire.",
   "Le champ est vidé en remettant le state à `''`."],
  [Q("`<button onClick={supprimer(id)}>` : que se passe-t-il ?",
     ["Ça supprime au clic", "`supprimer` est appelé à chaque rendu", "Erreur de syntaxe", "Rien"], 1,
     "Il faut passer une fonction : `onClick={() => supprimer(id)}`."),
   Q("Une barre de recherche et une liste (frères) partagent le texte recherché. Où vit ce state ?",
     ["Dans la barre de recherche", "Dans la liste", "Dans leur parent commun", "Dans une variable globale"], 2,
     "On remonte le state au plus proche parent commun."),
   Q("Pourquoi `e.preventDefault()` dans `onSubmit` ?",
     ["Pour valider les champs", "Pour empêcher le navigateur de recharger la page", "Pour vider le formulaire", "C'est optionnel en React 19"], 1,
     "Par défaut, un formulaire HTML envoie une requête et recharge la page.")],
  TD("Contacts avec recherche",
     "Construis une page de contacts avec recherche et ajout.",
     ["`ContactsPage` (parent) détient la liste et le texte de recherche",
      "`SearchBar` (champ contrôlé) et `ContactList` sont frères",
      "La liste montre les contacts dont le nom contient le texte (insensible à la casse)",
      "`AddContact` (nom + email) refuse un nom vide et vide les champs après ajout"],
     code("tsx", r"""
import { useState } from 'react';

type Contact = { id: string; name: string; email: string };

const initial: Contact[] = [
  { id: '1', name: 'Ana Martin', email: 'ana@exemple.fr' },
  { id: '2', name: 'Léo Petit', email: 'leo@exemple.fr' },
];

export default function ContactsPage() {
  // à toi
}
"""),
     ["`SearchBar` reçoit `value` et `onChange` en props : c'est le parent qui garde le state.",
      "Filtre dérivé : `contacts.filter(c => c.name.toLowerCase().includes(query.toLowerCase()))`",
      "`AddContact` a son propre state pour ses deux champs, et appelle `onAdd(contact)`."],
     code("tsx", r"""
function SearchBar({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return <input value={value} onChange={(e) => onChange(e.target.value)} placeholder="Rechercher" />;
}

function ContactList({ contacts }: { contacts: Contact[] }) {
  if (contacts.length === 0) return <p>Aucun contact</p>;
  return <ul>{contacts.map((c) => <li key={c.id}>{c.name} – {c.email}</li>)}</ul>;
}

function AddContact({ onAdd }: { onAdd: (c: Contact) => void }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (!name.trim()) return;
        onAdd({ id: crypto.randomUUID(), name: name.trim(), email: email.trim() });
        setName('');
        setEmail('');
      }}
    >
      <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Nom" />
      <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
      <button>Ajouter</button>
    </form>
  );
}

export default function ContactsPage() {
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
"""),
     ["`SearchBar` n'a aucun `useState`",
      "La liste filtrée n'est pas stockée dans un state"])),

M("react-effect", T, "useEffect & synchronisation", 18,
  "Savoir quand utiliser useEffect, et surtout quand ne pas l'utiliser.",
  "Le rendu doit rester pur : il calcule du JSX, c'est tout. Pour parler au monde extérieur (API, timer, titre de la page), il faut un endroit dédié.",
  ["Le composant **s'affiche**",
   "React exécute ensuite l'**effet**",
   "Si une **dépendance** change : **cleanup** de l'ancien effet, puis nouvel effet",
   "Au démontage, le **cleanup** s'exécute une dernière fois"],
  ["Dépendances : `[]` = au montage seulement ; `[id]` = à chaque changement de `id` ; pas de tableau = après chaque rendu.",
   "Le **cleanup** (la fonction retournée) annule ce que l'effet a lancé : timer, abonnement, requête.",
   "Mets dans les dépendances **tout** ce que l'effet utilise et qui vient du composant.",
   "Pas d'effet pour une valeur dérivée ou pour réagir à un clic : fais-le dans le rendu ou dans le handler.",
   "En développement, le StrictMode lance l'effet deux fois pour vérifier ton cleanup.",
   "Avec Next.js, charge plutôt les données côté serveur (parcours Next.js)."],
  ["Un effet qui met à jour un state qu'il a en dépendance : boucle infinie.",
   "Pas de cleanup sur un fetch : une réponse lente peut écraser une plus récente."],
  code("tsx", r"""
import { useEffect, useState } from 'react';

type User = { id: number; name: string; email: string };

export default function UserProfile({ userId }: { userId: number }) {
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setUser(null);
    setError(null);

    fetch(`/api/users/${userId}`, { signal: controller.signal })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setUser)
      .catch((e) => {
        if (e.name !== 'AbortError') setError(e.message);
      });

    return () => controller.abort();   // cleanup : annule si userId change
  }, [userId]);

  if (error) return <p>Erreur : {error}</p>;
  if (!user) return <p>Chargement…</p>;
  return <h2>{user.name} – {user.email}</h2>;
}
"""),
  ["`[userId]` : l'effet se relance quand on change d'utilisateur.",
   "`controller.abort()` empêche l'ancienne réponse d'arriver après la nouvelle.",
   "Trois états affichés : erreur, chargement, données."],
  [Q("`useEffect(fn, [])` s'exécute…",
     ["à chaque rendu", "après le premier rendu seulement (et cleanup au démontage)", "avant le rendu", "jamais en production"], 1,
     "Tableau vide = aucune dépendance qui puisse changer."),
   Q("À quoi sert la fonction retournée par l'effet ?",
     ["Renvoyer une valeur au composant", "Nettoyer avant le prochain effet ou au démontage", "Gérer les erreurs", "Forcer un rendu"], 1,
     "Timer à arrêter, requête à annuler, abonnement à fermer."),
   Q("Tu dois afficher `fullName` à partir de `first` et `last` (deux states). Que faire ?",
     ["Un useEffect qui appelle setFullName", "`const fullName = first + ' ' + last` dans le rendu", "Un troisième state", "useMemo obligatoire"], 1,
     "Une valeur dérivée se calcule pendant le rendu.")],
  TD("Chronomètre",
     "Construis un chronomètre.",
     ["Boutons Démarrer / Pause / Reset",
      "Affiche les secondes écoulées",
      "`setInterval` dans un effet qui dépend de `running`, avec cleanup",
      "Met à jour `document.title` avec le temps",
      "Vérifie qu'il n'y a jamais deux intervalles en même temps"],
     code("tsx", r"""
import { useEffect, useState } from 'react';

export default function Stopwatch() {
  const [seconds, setSeconds] = useState(0);
  const [running, setRunning] = useState(false);

  // à toi

  return <div>{seconds} s</div>;
}
"""),
     ["Si `!running`, l'effet ne fait rien : `if (!running) return;`",
      "`const id = setInterval(() => setSeconds(s => s + 1), 1000); return () => clearInterval(id);`",
      "Le titre est un deuxième effet qui dépend de `[seconds]`."],
     code("tsx", r"""
export default function Stopwatch() {
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
      <p>{seconds} s</p>
      <button onClick={() => setRunning((r) => !r)}>{running ? 'Pause' : 'Démarrer'}</button>
      <button onClick={() => { setRunning(false); setSeconds(0); }}>Reset</button>
    </div>
  );
}
"""),
     ["Démarrer / Pause rapidement n'accélère pas le chrono",
      "`setSeconds(s => s + 1)` et pas `setSeconds(seconds + 1)` (sinon instantané figé)"])),

M("react-hooks", T, "Hooks personnalisés", 15,
  "Extraire une logique avec state dans une fonction réutilisable.",
  "Quand deux composants recopient le même `useState` + `useEffect`, cette logique doit vivre à un seul endroit.",
  ["Tu repères une logique répétée (state + effet)",
   "Tu la déplaces dans une fonction **`useQuelqueChose`**",
   "Elle utilise d'autres hooks et **renvoie** ce dont le composant a besoin",
   "Chaque composant qui l'appelle a **son propre state**"],
  ["Un hook personnalisé commence par `use` et peut appeler d'autres hooks.",
   "Il partage la **logique**, pas les données : deux composants qui l'utilisent ont chacun leur state.",
   "Règles des hooks : appelés au **niveau supérieur** du composant, jamais dans un `if` ou une boucle.",
   "Renvoie un objet nommé (`{ data, error, loading }`) ou un tuple comme `useState`."],
  ["Appeler un hook dans une condition : React mélange les states.",
   "Créer un hook pour une logique sans state ni effet : une fonction normale suffit."],
  code("tsx", r"""
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

// Utilisation : une ligne dans chaque composant
function Posts() {
  const { data, error, loading } = useFetch<{ id: number; title: string }[]>('/api/posts');
  if (loading) return <p>Chargement…</p>;
  if (error) return <p>{error}</p>;
  return <ul>{data!.map((p) => <li key={p.id}>{p.title}</li>)}</ul>;
}
"""),
  ["Toute la mécanique du module précédent est rangée dans `useFetch`.",
   "`<T>` rend le hook typé pour n'importe quelle donnée.",
   "`Posts` ne garde que l'affichage."],
  [Q("Deux composants appellent `useFetch('/api/posts')`. Partagent-ils le même state ?",
     ["Oui", "Non, chaque appel a son propre state", "Seulement si l'URL est identique", "Seulement en production"], 1,
     "Un hook partage la logique, pas les données."),
   Q("Lequel respecte les règles des hooks ?",
     ["`if (ok) { useState(0) }`", "`const [x] = useState(0)` en haut du composant", "`for (...) useEffect(...)`", "useState dans un handler onClick"], 1,
     "Les hooks doivent être appelés dans le même ordre à chaque rendu."),
   Q("Quand créer un hook personnalisé ?",
     ["Pour toute fonction", "Quand une logique avec state et/ou effets est répétée", "Jamais", "Seulement pour fetch"], 1,
     "Sans hook à l'intérieur, une fonction normale suffit.")],
  TD("useLocalStorage",
     "Écris un hook qui fonctionne comme `useState` mais sauvegarde la valeur dans le navigateur.",
     ["`useLocalStorage(key, initialValue)` renvoie `[value, setValue]`",
      "Lit la valeur sauvegardée au premier rendu (JSON)",
      "Sauvegarde à chaque changement",
      "Gère localStorage indisponible ou JSON invalide (retour à `initialValue`)",
      "Utilise-le pour un thème clair / sombre"],
     code("tsx", r"""
import { useEffect, useState } from 'react';

export function useLocalStorage<T>(key: string, initialValue: T) {
  // à toi
}

function ThemeToggle() {
  const [theme, setTheme] = useLocalStorage<'light' | 'dark'>('theme', 'light');
  return <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>{theme}</button>;
}
"""),
     ["Initialisation paresseuse : `useState(() => { ... lire localStorage ... })` ne lit qu'une fois.",
      "Entoure `JSON.parse` et `localStorage` d'un `try/catch`.",
      "Sauvegarde dans un `useEffect` qui dépend de `[key, value]`."],
     code("tsx", r"""
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
      // stockage plein ou indisponible : on garde la valeur en mémoire
    }
  }, [key, value]);

  return [value, setValue] as const;
}
"""),
     ["Le thème est conservé après rechargement",
      "Une valeur corrompue dans localStorage ne fait pas planter la page"])),
]

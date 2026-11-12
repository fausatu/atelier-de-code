from common import V2, P, L, D, N, E, LANE, F, TD, RUN
from c_next_v1 import MODULES as V1

v1 = {m["id"]: m for m in V1}

SIM = "Le bouton Exécuter utilise un **Next.js simulé** : il applique le routage par dossiers, les layouts, les Server et Client Components, les Server Actions et les Route Handlers, et affiche la page dans l'aperçu. Les tests naviguent avec `next.render('/url')`."

def NRUN(tests, start="/", api=None):
    return RUN("next", tests=tests, entry="app/page.tsx", start=start, api=api)

PRODUITS = F("lib/produits.ts", "ts", r"""
// Fausse base de données (en mémoire), utilisée côté serveur
export type Produit = { id: string; nom: string; prix: number; stock: number };

const produits: Produit[] = [
  { id: 'clavier', nom: 'Clavier mécanique', prix: 89, stock: 12 },
  { id: 'souris', nom: 'Souris sans fil', prix: 35, stock: 0 },
  { id: 'ecran', nom: 'Écran 27 pouces', prix: 249, stock: 4 },
];

const attendre = () => new Promise((r) => setTimeout(r, 20));

export async function getProduits(): Promise<Produit[]> {
  await attendre();
  return produits;
}

export async function getProduit(id: string): Promise<Produit | null> {
  await attendre();
  return produits.find((p) => p.id === id) ?? null;
}
""")

ARTICLES = F("lib/articles.ts", "ts", r"""
// Fausse base de données (en mémoire), utilisée côté serveur
export type Article = { id: string; categorie: string; titre: string; contenu: string; likes: number };
export type Commentaire = { id: string; articleId: string; auteur: string; texte: string };

export const articles: Article[] = [
  { id: 'dto', categorie: 'php', titre: 'Les DTO expliqués', contenu: 'Un DTO décrit les données qui traversent l\'API.', likes: 3 },
  { id: 'hooks', categorie: 'react', titre: 'Les hooks sans peur', contenu: 'Un hook est une fonction qui commence par use.', likes: 7 },
];
export const commentaires: Commentaire[] = [
  { id: 'c1', articleId: 'dto', auteur: 'Ana', texte: 'Très clair !' },
  { id: 'c2', articleId: 'dto', auteur: 'Léo', texte: 'Merci pour les exemples.' },
];

const attendre = () => new Promise((r) => setTimeout(r, 20));

export async function getArticle(id: string) { await attendre(); return articles.find((a) => a.id === id) ?? null; }
export async function getArticles() { await attendre(); return articles; }
export async function getCommentaires(articleId: string) { await attendre(); return commentaires.filter((c) => c.articleId === articleId); }
""")

ROOT_LAYOUT = F("app/layout.tsx", "tsx", r"""
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <div className="site">{children}</div>;
}
""")

HOME = F("app/page.tsx", "tsx", "export default function Accueil() {\n  return <h1>Accueil</h1>;\n}\n")

# ---------------------------------------------------------------- Routing
routing = V2(v1["next-routing"],
  prereq=[
    P("Route", "Une URL de ton site (`/produits`, `/produits/clavier`) et le code qui affiche cette page."),
    P("Segment", "Un morceau d'URL entre deux `/` : `/blog/mon-article` a deux segments, `blog` et `mon-article`."),
    P("Segment dynamique", "Un segment variable, écrit entre crochets dans le nom du dossier : `[slug]`. Sa valeur réelle arrive dans `params`."),
    P("Layout", "Un composant qui entoure des pages (en-tête, menu, pied de page). Il reste affiché quand on navigue entre ses pages."),
    P("`async` / Promise", "Une page Next peut être une fonction `async` qui attend ses données avant de s'afficher. `params` est lui-même une promesse : `const { slug } = await params`."),
  ],
  diagram=D(
    nodes=[
      N("f0", 0, 0, "page.tsx", None, kind="file"),
      N("u0", 1, 0, "/", None, kind="pill"),
      N("f1", 0, 1, "produits/page.tsx", None, kind="file"),
      N("u1", 1, 1, "/produits", None, kind="pill"),
      N("f2", 0, 2, "produits/[id]/page.tsx", "segment dynamique", kind="file", color="good"),
      N("u2", 1, 2, "/produits/clavier", None, kind="pill", color="good"),
      N("par", 2, 2, "params", "{ id: 'clavier' }", kind="note", color="good"),
      N("f3", 0, 3, "(compte)/connexion/page.tsx", "groupe : hors URL", kind="file", color="muted"),
      N("u3", 1, 3, "/connexion", None, kind="pill"),
    ],
    edges=[E("f0", "u0"), E("f1", "u1"), E("f2", "u2"), E("u2", "par", "await params"), E("f3", "u3")],
    caption="Fichiers (dans app/) à gauche, URL à droite. Chaque dossier de app/ est un segment d'URL ; page.tsx rend la route accessible ; [id] capture la valeur ; (groupe) organise sans changer l'URL."),
  lessons=[
    L("Le principe : les dossiers sont les routes", r"""
Dans beaucoup de frameworks, on déclare les routes dans un fichier de configuration. Avec l'**App Router** de Next.js, c'est l'**arborescence du dossier `app/`** qui fait office de configuration :

```
app/
├── layout.tsx              enveloppe tout le site
├── page.tsx                /
├── produits/
│   ├── page.tsx            /produits
│   └── [id]/
│       └── page.tsx        /produits/clavier, /produits/souris…
└── a-propos/
    └── page.tsx            /a-propos
```

Deux règles à retenir :

- Un **dossier** = un segment d'URL.
- Un dossier n'est une page **que s'il contient `page.tsx`**. Un dossier sans `page.tsx` peut exister (pour ranger des composants, ou contenir des sous-dossiers) mais n'est pas accessible.

Le fichier `page.tsx` exporte par défaut un composant : c'est ce qui s'affiche à cette URL.
"""),
    L("Les segments dynamiques et `params`", r"""
Pour une page « détail » dont l'URL varie (`/produits/clavier`, `/produits/ecran`), on nomme le dossier entre crochets : `[id]`. La valeur réelle du segment arrive dans la prop `params` :

```tsx
// app/produits/[id]/page.tsx
import { notFound } from 'next/navigation';
import { getProduit } from '@/lib/produits';

export default async function ProduitPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;          // depuis Next 15, params est une promesse
  const produit = await getProduit(id);
  if (!produit) notFound();             // affiche le not-found.tsx le plus proche (404)
  return <h1>{produit.nom}</h1>;
}
```

- La page est `async` : elle attend ses données **avant** d'être envoyée. Pas de `useEffect`, pas d'état de chargement à gérer à la main (voir le module Server Components).
- `notFound()` interrompt le rendu et affiche la page 404. Next cherche un fichier `not-found.tsx` en remontant les dossiers.
- On peut imbriquer plusieurs segments : `app/blog/[categorie]/[slug]/page.tsx` donne `params = { categorie, slug }`.
- La query string (`?q=dune`) arrive dans une autre prop, `searchParams` (une promesse elle aussi).
"""),
    L("Layouts, groupes et fichiers spéciaux", r"""
Un `layout.tsx` **enveloppe** toutes les pages de son dossier et des sous-dossiers. Il reçoit la page dans `children` :

```tsx
// app/layout.tsx : le layout racine (obligatoire) contient <html> et <body>
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>
        <nav>…</nav>
        {children}
      </body>
    </html>
  );
}
```

Les layouts s'**emboîtent** : `/produits/clavier` est rendu dans `app/layout.tsx`, puis `app/produits/layout.tsx` s'il existe, puis la page. Et un layout **reste monté** quand on navigue entre ses pages : idéal pour un menu ou une barre latérale qui garde son état.

Un **groupe** est un dossier entre parenthèses, `(compte)` : il sert à **organiser** (et à partager un layout) **sans apparaître dans l'URL**. `app/(compte)/connexion/page.tsx` répond à `/connexion`.

Les autres fichiers spéciaux d'un dossier :

| Fichier | Rôle |
|---|---|
| `loading.tsx` | affiché pendant que la page charge ses données |
| `error.tsx` | affiché si la page lève une erreur (composant client) |
| `not-found.tsx` | affiché quand `notFound()` est appelé |
"""),
    L("Naviguer : `<Link>` et `redirect`", r"""
Pour aller d'une page à l'autre, on utilise `<Link>` plutôt que `<a>` :

```tsx
import Link from 'next/link';

<Link href="/produits">Tous les produits</Link>
<Link href={`/produits/${p.id}`}>{p.nom}</Link>
```

`<Link>` change de page **sans recharger** tout le site : les layouts restent en place, seule la partie qui change est remplacée, et Next précharge la page cible quand le lien devient visible. Un `<a>` classique recharge tout, et perd l'état des composants.

Côté serveur, pour envoyer l'utilisateur ailleurs (ancienne URL, page protégée…), on utilise `redirect()` :

```tsx
import { redirect } from 'next/navigation';

export default async function AnciennePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  redirect(`/produits/${id}`);
}
```

Comme `notFound()`, `redirect()` interrompt le rendu : le code qui suit ne s'exécute pas.
"""),
  ],
  recap=[
    "Chaque dossier de `app/` = un segment d'URL ; il faut un `page.tsx` pour que la route existe.",
    "`[id]` = segment dynamique ; `const { id } = await params` dans la page.",
    "`layout.tsx` enveloppe les pages en dessous et reste monté ; les layouts s'emboîtent.",
    "`(groupe)` organise sans changer l'URL ; `not-found.tsx`, `error.tsx`, `loading.tsx` sont des fichiers spéciaux.",
    "`notFound()` → 404 ; `redirect('/…')` → autre page ; `<Link>` pour naviguer sans rechargement.",
  ],
  example=[F("app/layout.tsx", "tsx", r"""
import Link from 'next/link';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>
        <nav>
          <Link href="/">Accueil</Link> · <Link href="/produits">Produits</Link>
        </nav>
        {children}
      </body>
    </html>
  );
}
"""), F("app/produits/page.tsx", "tsx", r"""
import Link from 'next/link';
import { getProduits } from '@/lib/produits';

export default async function ProduitsPage() {
  const produits = await getProduits();
  return (
    <ul>
      {produits.map((p) => (
        <li key={p.id}>
          <Link href={`/produits/${p.id}`}>{p.nom}</Link> — {p.prix} €
        </li>
      ))}
    </ul>
  );
}
"""), F("app/produits/[id]/page.tsx", "tsx", r"""
import { notFound } from 'next/navigation';
import { getProduit } from '@/lib/produits';

export default async function ProduitPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const produit = await getProduit(id);
  if (!produit) notFound();

  return (
    <article>
      <h1>{produit.nom}</h1>
      <p>{produit.prix} € · {produit.stock > 0 ? 'en stock' : 'rupture'}</p>
    </article>
  );
}
"""), F("app/produits/[id]/not-found.tsx", "tsx", r"""
import Link from 'next/link';

export default function ProduitIntrouvable() {
  return (
    <div>
      <h1>Ce produit n'existe pas</h1>
      <Link href="/produits">Voir tous les produits</Link>
    </div>
  );
}
""")],
  notes=["Le chemin des fichiers **est** l'URL : compare `app/produits/[id]/page.tsx` et `/produits/clavier`.",
         "Les deux pages sont `async` et chargent leurs données directement (`getProduits()`), sans `useEffect`.",
         "`notFound()` affiche le `not-found.tsx` du même dossier, avec un statut 404.",
         "Le menu est dans le layout racine : il reste affiché sur toutes les pages."],
  td1=dict(path="app/produits/[id]/page.tsx",
    title="Structure d'une boutique",
    enonce="Crée les routes d'une petite boutique : accueil, liste, détail, et un espace compte qui partage un layout centré sans apparaître dans l'URL. " + SIM,
    consignes=["`/` : un titre `<h1>Boutique</h1>` ; le layout racine contient un `<nav>` avec des `<Link>` vers `/`, `/produits`, `/connexion`",
               "`/produits` : un `<li>` par produit, avec un lien vers son détail",
               "`/produits/[id]` : le nom dans un `<h1>` et le prix ; `notFound()` si le produit n'existe pas",
               "Groupe `(compte)` : `/connexion` et `/inscription` (un `<h1>` chacune) partagent `app/(compte)/layout.tsx` qui les enveloppe dans `<div className=\"compte\">`",
               "`/compte/connexion` ne doit **pas** exister"],
    hints=["Les dossiers à créer : `app/produits/[id]/`, `app/(compte)/connexion/`, `app/(compte)/inscription/`.",
           "Dans `[id]/page.tsx` : `const { id } = await params;` puis `const p = await getProduit(id); if (!p) notFound();`",
           "Le layout du groupe : `export default function CompteLayout({ children }) { return <div className=\"compte\">{children}</div>; }`"],
    checks=["`/produits/inconnu` renvoie 404", "`/connexion` est enveloppée par le layout du groupe"],
    files=[PRODUITS, F("app/layout.tsx", "tsx", r"""
import Link from 'next/link';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  // à toi : un <nav> avec 3 liens, puis {children}
  return <div>{children}</div>;
}
"""), F("app/page.tsx", "tsx", r"""
export default function Accueil() {
  return <h1>Boutique</h1>;
}
"""), F("app/produits/page.tsx", "tsx", r"""
// à toi
"""), F("app/produits/[id]/page.tsx", "tsx", r"""
import { notFound } from 'next/navigation';
import { getProduit } from '@/lib/produits';

// à toi
"""), F("app/(compte)/layout.tsx", "tsx", r"""
// à toi
"""), F("app/(compte)/connexion/page.tsx", "tsx", r"""
// à toi
"""), F("app/(compte)/inscription/page.tsx", "tsx", r"""
// à toi
""")],
    solution=[F("app/layout.tsx", "tsx", r"""
import Link from 'next/link';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <div>
      <nav>
        <Link href="/">Accueil</Link> <Link href="/produits">Produits</Link> <Link href="/connexion">Connexion</Link>
      </nav>
      {children}
    </div>
  );
}
"""), F("app/produits/page.tsx", "tsx", r"""
import Link from 'next/link';
import { getProduits } from '@/lib/produits';

export default async function ProduitsPage() {
  const produits = await getProduits();
  return (
    <ul>
      {produits.map((p) => (
        <li key={p.id}><Link href={`/produits/${p.id}`}>{p.nom}</Link> — {p.prix} €</li>
      ))}
    </ul>
  );
}
"""), F("app/produits/[id]/page.tsx", "tsx", r"""
import { notFound } from 'next/navigation';
import { getProduit } from '@/lib/produits';

export default async function ProduitPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const produit = await getProduit(id);
  if (!produit) notFound();
  return (
    <article>
      <h1>{produit.nom}</h1>
      <p>{produit.prix} €</p>
    </article>
  );
}
"""), F("app/(compte)/layout.tsx", "tsx", r"""
export default function CompteLayout({ children }: { children: React.ReactNode }) {
  return <div className="compte">{children}</div>;
}
"""), F("app/(compte)/connexion/page.tsx", "tsx", r"""
export default function Connexion() {
  return <h1>Connexion</h1>;
}
"""), F("app/(compte)/inscription/page.tsx", "tsx", r"""
export default function Inscription() {
  return <h1>Inscription</h1>;
}
""")],
    run=NRUN(r"""
assert.equal(await next.render('/'), 200, '/ → 200');
assert.equal($$('nav a').length, 3, 'Le layout racine contient 3 liens');
await next.render('/produits');
assert.equal($$('li').length, 3, '/produits : 3 produits');
assert($$('li a')[0] && $$('li a')[0].getAttribute('href') === '/produits/clavier', 'Chaque produit a un lien vers son détail');
await click($$('li a')[2]);
await waitFor(() => $('h1') && $('h1').textContent.includes('Écran'), 2000);
assert(true, 'Cliquer sur un lien affiche le détail (navigation sans rechargement)');
assert.includes(text(), '249', 'Le détail affiche le prix');
assert.equal(await next.render('/produits/inconnu'), 404, '/produits/inconnu → 404');
assert.equal(await next.render('/connexion'), 200, '/connexion → 200');
assert($('.compte h1') && $('.compte h1').textContent === 'Connexion', '/connexion est dans le layout du groupe');
assert(await next.render('/inscription') === 200 && $('.compte h1'), '/inscription partage le même layout');
assert.equal(await next.render('/compte/connexion'), 404, '/compte/connexion n\'existe pas (groupe hors URL)');
""")),
  tds=[
    TD(2, "Blog : segments imbriqués et 404 sur mesure",
       "Un blog organise ses articles par catégorie : `/blog/php/dto`. Le layout du blog affiche un fil d'Ariane, et chaque niveau a sa propre gestion du « introuvable ». " + SIM,
       ["`/blog` : la liste des articles (un `<li>` par article, lien vers `/blog/<categorie>/<id>`)",
        "`/blog/[categorie]/[id]` : le titre dans un `<h1>` ; 404 si l'article n'existe pas **ou** n'est pas dans cette catégorie",
        "`app/blog/layout.tsx` enveloppe tout le blog dans `<section className=\"blog\">` avec un `<p className=\"ariane\">Blog</p>`",
        "`app/blog/not-found.tsx` affiche « Article introuvable » (le 404 du blog est différent de celui du site)",
        "`/blog/react/dto` (mauvaise catégorie) → 404 avec « Article introuvable »"],
       [ARTICLES, ROOT_LAYOUT, HOME, F("app/blog/layout.tsx", "tsx", r"""
// à toi
"""), F("app/blog/page.tsx", "tsx", r"""
// à toi
"""), F("app/blog/[categorie]/[id]/page.tsx", "tsx", r"""
// à toi
"""), F("app/blog/not-found.tsx", "tsx", r"""
// à toi
""")],
       ["`params` contient les deux segments : `const { categorie, id } = await params;`",
        "`if (!article || article.categorie !== categorie) notFound();`",
        "Next cherche le `not-found.tsx` le plus proche en remontant : celui de `app/blog/` est trouvé avant celui de `app/`."],
       [F("app/blog/layout.tsx", "tsx", r"""
export default function BlogLayout({ children }: { children: React.ReactNode }) {
  return (
    <section className="blog">
      <p className="ariane">Blog</p>
      {children}
    </section>
  );
}
"""), F("app/blog/page.tsx", "tsx", r"""
import Link from 'next/link';
import { getArticles } from '@/lib/articles';

export default async function BlogPage() {
  const articles = await getArticles();
  return (
    <ul>
      {articles.map((a) => (
        <li key={a.id}><Link href={`/blog/${a.categorie}/${a.id}`}>{a.titre}</Link></li>
      ))}
    </ul>
  );
}
"""), F("app/blog/[categorie]/[id]/page.tsx", "tsx", r"""
import { notFound } from 'next/navigation';
import { getArticle } from '@/lib/articles';

export default async function ArticlePage({ params }: { params: Promise<{ categorie: string; id: string }> }) {
  const { categorie, id } = await params;
  const article = await getArticle(id);
  if (!article || article.categorie !== categorie) notFound();
  return (
    <article>
      <h1>{article.titre}</h1>
      <p>{article.contenu}</p>
    </article>
  );
}
"""), F("app/blog/not-found.tsx", "tsx", r"""
export default function ArticleIntrouvable() {
  return <h1>Article introuvable</h1>;
}
""")],
       ["`/blog/react/dto` affiche « Article introuvable »",
        "Le fil d'Ariane reste affiché sur toutes les pages du blog"],
       run=NRUN(r"""
await next.render('/blog');
assert.equal($$('.blog li').length, 2, '/blog : 2 articles dans le layout du blog');
assert.equal($$('.blog li a')[0].getAttribute('href'), '/blog/php/dto', 'Lien vers /blog/<categorie>/<id>');
assert.equal(await next.render('/blog/php/dto'), 200, '/blog/php/dto → 200');
assert.equal($('h1').textContent, 'Les DTO expliqués', 'Le titre de l\'article est affiché');
assert($('.blog .ariane'), 'Le fil d\'Ariane est affiché sur la page article');
assert.equal(await next.render('/blog/react/dto'), 404, 'Mauvaise catégorie → 404');
assert.includes(text(), 'Article introuvable', 'Le 404 du blog est utilisé');
assert.equal(await next.render('/blog/php/rien'), 404, 'Article inconnu → 404');
""")),
    TD(3, "Recherche, anciennes URL et redirection",
       "La boutique change ses URL : les anciennes pages `/articles/[id]` doivent **rediriger** vers `/produits/[id]`. Et une page de recherche lit la query string (`?q=`). " + SIM,
       ["`/recherche?q=cla` : `searchParams` donne `q` ; affiche un `<li>` par produit dont le nom contient `q` (insensible à la casse), et « Aucun résultat » si rien",
        "Sans `q`, `/recherche` affiche « Tape un mot-clé »",
        "`/articles/[id]` : `redirect('/produits/' + id)`",
        "`/produits/[id]` affiche le nom du produit dans un `<h1>`",
        "Le formulaire de recherche (`<form action=\"/recherche\">` avec un `<input name=\"q\">`) est dans la page de recherche"],
       [PRODUITS, ROOT_LAYOUT, HOME, F("app/recherche/page.tsx", "tsx", r"""
import { getProduits } from '@/lib/produits';

export default async function Recherche({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  // à toi
}
"""), F("app/articles/[id]/page.tsx", "tsx", r"""
import { redirect } from 'next/navigation';
// à toi
"""), F("app/produits/[id]/page.tsx", "tsx", r"""
import { notFound } from 'next/navigation';
import { getProduit } from '@/lib/produits';
// à toi
""")],
       ["`const { q } = await searchParams;` (`q` peut être `undefined`).",
        "Filtre : `produits.filter((p) => p.nom.toLowerCase().includes(q.toLowerCase()))`.",
        "La page de redirection n'affiche rien : `redirect()` interrompt tout."],
       [F("app/recherche/page.tsx", "tsx", r"""
import { getProduits } from '@/lib/produits';

export default async function Recherche({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const { q } = await searchParams;
  const resultats = q ? (await getProduits()).filter((p) => p.nom.toLowerCase().includes(q.toLowerCase())) : [];

  return (
    <div>
      <form action="/recherche">
        <input name="q" defaultValue={q ?? ''} />
        <button>Chercher</button>
      </form>
      {!q && <p>Tape un mot-clé</p>}
      {q && resultats.length === 0 && <p>Aucun résultat</p>}
      <ul>{resultats.map((p) => <li key={p.id}>{p.nom}</li>)}</ul>
    </div>
  );
}
"""), F("app/articles/[id]/page.tsx", "tsx", r"""
import { redirect } from 'next/navigation';

export default async function AncienArticle({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  redirect('/produits/' + id);
}
"""), F("app/produits/[id]/page.tsx", "tsx", r"""
import { notFound } from 'next/navigation';
import { getProduit } from '@/lib/produits';

export default async function ProduitPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const p = await getProduit(id);
  if (!p) notFound();
  return <h1>{p.nom}</h1>;
}
""")],
       ["`/articles/ecran` affiche la page de l'écran",
        "`/recherche?q=zzz` affiche « Aucun résultat »"],
       run=NRUN(r"""
await next.render('/recherche');
assert.includes(text(), 'Tape un mot-clé', 'Sans q : « Tape un mot-clé »');
await next.render('/recherche?q=CLA');
assert.equal($$('li').length, 1, 'q=CLA : 1 résultat (casse ignorée)');
assert.includes($$('li')[0].textContent, 'Clavier', 'Le clavier est trouvé');
await next.render('/recherche?q=zzz');
assert.includes(text(), 'Aucun résultat', 'q=zzz : « Aucun résultat »');
assert($('form input[name=q]'), 'Le formulaire a un champ « q »');
await next.render('/articles/ecran');
assert.equal(next.url, '/produits/ecran', '/articles/ecran redirige vers /produits/ecran');
assert.includes($('h1').textContent, 'Écran', 'La page de l\'écran est affichée');
assert.equal(await next.render('/articles/rien'), 404, 'Ancienne URL d\'un produit inconnu → redirection puis 404');
""")),
  ])

# ---------------------------------------------------------------- Server / Client
sc = V2(v1["next-server-client"],
  prereq=[
    P("Rendu serveur", "Le HTML est fabriqué sur le serveur et envoyé tout prêt au navigateur. L'utilisateur voit la page sans attendre que le JavaScript se charge."),
    P("Bundle JavaScript", "Le code JS téléchargé par le navigateur. Plus il est gros, plus la page met de temps à devenir interactive."),
    P("Interactivité", "Tout ce qui réagit dans la page : clics, saisie, état qui change (`useState`), effets (`useEffect`). Ça demande du JavaScript dans le navigateur."),
    P("Sérialisable", "Qui peut être transformé en texte (JSON) pour voyager du serveur au navigateur : chaînes, nombres, booléens, tableaux, objets simples. Une fonction ne l'est pas."),
  ],
  diagram=D(
    nodes=[
      N("page", 0, 1, "page.tsx", "Server Component\nawait getArticle()", kind="file", color="accent"),
      N("db", 0, 0, "Base / secrets", "accès direct", kind="db", color="muted"),
      N("html", 1, 1, "HTML + données", "envoyés au navigateur", kind="doc"),
      N("like", 2, 0, "LikeButton", "'use client'\nuseState, onClick", kind="file", color="warn"),
      N("com", 2, 2, "Commentaires", "'use client'\nouvrir / fermer", kind="file", color="warn"),
      N("js", 3, 1, "JS du navigateur", "seulement ces 2\ncomposants", kind="pill", color="good"),
    ],
    edges=[E("db", "page"), E("page", "html", "rendu serveur"), E("html", "like", "props simples"), E("html", "com", "props simples"), E("like", "js"), E("com", "js")],
    lanes=[LANE("Serveur", 0, 0, "tc"), LANE("Navigateur", 2, 3, "accent")],
    caption="La page reste sur le serveur (données, secrets). Seuls les petits composants interactifs, marqués 'use client', sont envoyés au navigateur."),
  lessons=[
    L("Deux sortes de composants", r"""
Avec l'App Router, chaque composant est rendu à l'un de ces deux endroits :

**Server Component (par défaut).** Il s'exécute **uniquement sur le serveur**. Il peut :

- être `async` et attendre ses données (`const article = await getArticle(id)`) ;
- lire directement la base de données, des fichiers, des variables d'environnement secrètes ;
- n'envoyer **aucun JavaScript** au navigateur : juste le résultat (le HTML).

Il ne peut **pas** utiliser `useState`, `useEffect`, `onClick`… : il n'existe plus une fois la page envoyée.

**Client Component** (fichier qui commence par `'use client'`). Il est rendu une première fois sur le serveur, puis son JavaScript est envoyé au navigateur pour le rendre **interactif**. C'est le composant React que tu connais : state, effets, événements, APIs du navigateur (`localStorage`…). Il ne peut pas être `async` et n'a pas accès à la base.
"""),
    L("`'use client'` est une frontière", r"""
La directive `'use client'`, tout en haut d'un fichier, dit : « à partir d'ici, on passe côté navigateur ». Ce fichier **et tout ce qu'il importe** deviennent du code client.

D'où la règle la plus importante : **mets `'use client'` le plus bas possible dans l'arbre**, sur le petit composant qui a vraiment besoin d'interactivité :

```tsx
// app/articles/[id]/page.tsx  (serveur : pas de 'use client')
import LikeButton from './LikeButton';

export default async function ArticlePage({ params }) {
  const { id } = await params;
  const article = await getArticle(id);        // directement en base
  return (
    <article>
      <h1>{article.titre}</h1>
      <p>{article.contenu}</p>
      <LikeButton initial={article.likes} />    {/* seul ce bouton part au navigateur */}
    </article>
  );
}
```

```tsx
// app/articles/[id]/LikeButton.tsx
'use client';
import { useState } from 'react';

export default function LikeButton({ initial }: { initial: number }) {
  const [likes, setLikes] = useState(initial);
  return <button onClick={() => setLikes((l) => l + 1)}>{likes} j'aime</button>;
}
```

Si tu mettais `'use client'` dans `page.tsx`, toute la page partirait au navigateur, et tu perdrais l'accès direct à la base.
"""),
    L("Ce qui traverse la frontière : des données simples", r"""
Un Server Component peut afficher un Client Component et lui passer des **props**. Ces props voyagent du serveur au navigateur : elles doivent être **sérialisables**.

- OK : chaînes, nombres, booléens, `null`, tableaux et objets simples, dates (converties), et du **JSX** (via `children`).
- Interdit : une **fonction** (`onSelect={…}`), une instance de classe complexe, une connexion à la base.

Next refuse avec une erreur claire : *Functions cannot be passed directly to Client Components*. La seule exception : une **Server Action** (`'use server'`), qui est une fonction serveur que le client peut appeler (module Server Actions).

Si un composant client a besoin de réagir à un événement, le state et le handler doivent vivre **dans** le composant client, pas être fournis par le serveur.
"""),
    L("Mélanger les deux : le motif `children`", r"""
Un Client Component ne peut pas **importer** un Server Component (l'import le transformerait en code client). Mais il peut en **recevoir un** dans `children`, parce que c'est le parent serveur qui l'assemble :

```tsx
// Onglets.tsx (client) : gère l'onglet ouvert
'use client';
export default function Onglets({ titres, children }: { titres: string[]; children: React.ReactNode[] }) {
  const [actif, setActif] = useState(0);
  return (
    <>
      {titres.map((t, i) => <button key={t} onClick={() => setActif(i)}>{t}</button>)}
      {children[actif]}
    </>
  );
}

// page.tsx (serveur) : charge les données et remplit les onglets
<Onglets titres={['Résumé', 'Avis']}>
  <Resume article={article} />          {/* Server Components, rendus sur le serveur */}
  <Avis articleId={article.id} />
</Onglets>
```

Le client gère l'interaction ; le serveur fournit le contenu. C'est le motif à utiliser pour une modale, des onglets, un accordéon autour de contenu chargé côté serveur.
"""),
  ],
  recap=[
    "Par défaut : **Server Component** (async, accès direct aux données, zéro JS envoyé, pas de hooks).",
    "`'use client'` : Client Component (state, effets, événements) ; le fichier et ses imports partent au navigateur.",
    "Place `'use client'` le plus bas possible, sur le petit composant interactif.",
    "Props serveur → client : seulement des données sérialisables ; jamais de fonction (sauf Server Action).",
    "Un composant client peut recevoir du contenu serveur via `children`.",
  ],
  example=[ARTICLES, F("app/articles/[id]/page.tsx", "tsx", r"""
import { notFound } from 'next/navigation';
import { getArticle } from '@/lib/articles';
import LikeButton from './LikeButton';

export default async function ArticlePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const article = await getArticle(id);      // directement en base, sur le serveur
  if (!article) notFound();

  return (
    <article>
      <h1>{article.titre}</h1>
      <p>{article.contenu}</p>
      <LikeButton initial={article.likes} />
    </article>
  );
}
"""), F("app/articles/[id]/LikeButton.tsx", "tsx", r"""
'use client';

import { useState } from 'react';

export default function LikeButton({ initial }: { initial: number }) {
  const [likes, setLikes] = useState(initial);
  return <button onClick={() => setLikes((l) => l + 1)}>{likes} j'aime</button>;
}
""")],
  notes=["`page.tsx` n'a pas de `'use client'` : elle reste sur le serveur et lit la base directement.",
         "`LikeButton.tsx` commence par `'use client'` : c'est le seul code envoyé au navigateur.",
         "La prop `initial` est un nombre : sérialisable, elle traverse la frontière sans problème.",
         "Le state (`likes`) vit dans le composant client, pas dans la page."],
  td1=dict(path="app/articles/[id]/page.tsx",
    title="Page article interactive",
    enonce="La page article charge l'article et ses commentaires côté serveur. Seuls le bouton « j'aime » et la liste repliable des commentaires sont interactifs. " + SIM,
    consignes=["`app/articles/[id]/page.tsx` (serveur) charge l'article et les commentaires **en parallèle** (`Promise.all`) ; 404 si l'article n'existe pas",
               "`LikeButton` (client) : affiche « N j'aime » et ajoute 1 à chaque clic",
               "`Commentaires` (client) : reçoit la liste ; un bouton « Voir les N commentaires » / « Masquer » ouvre et ferme la liste",
               "Aucun `'use client'` dans `page.tsx`"],
    hints=["Deux fichiers commencent par `'use client'` : `LikeButton.tsx` et `Commentaires.tsx`.",
           "`const [article, commentaires] = await Promise.all([getArticle(id), getCommentaires(id)]);`",
           "Dans `Commentaires`, un state `ouvert` et `{ouvert && <ul>…</ul>}`."],
    checks=["`page.tsx` n'a pas `'use client'`", "Le compteur augmente au clic"],
    files=[ARTICLES, ROOT_LAYOUT, HOME,
           F("app/articles/[id]/page.tsx", "tsx", r"""
import { notFound } from 'next/navigation';
import { getArticle, getCommentaires } from '@/lib/articles';
import LikeButton from './LikeButton';
import Commentaires from './Commentaires';

export default async function ArticlePage({ params }: { params: Promise<{ id: string }> }) {
  // à toi
}
"""), F("app/articles/[id]/LikeButton.tsx", "tsx", r"""
// à toi
"""), F("app/articles/[id]/Commentaires.tsx", "tsx", r"""
// à toi
""")],
    solution=[F("app/articles/[id]/page.tsx", "tsx", r"""
import { notFound } from 'next/navigation';
import { getArticle, getCommentaires } from '@/lib/articles';
import LikeButton from './LikeButton';
import Commentaires from './Commentaires';

export default async function ArticlePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [article, commentaires] = await Promise.all([getArticle(id), getCommentaires(id)]);
  if (!article) notFound();

  return (
    <article>
      <h1>{article.titre}</h1>
      <p>{article.contenu}</p>
      <LikeButton initial={article.likes} />
      <Commentaires items={commentaires} />
    </article>
  );
}
"""), F("app/articles/[id]/LikeButton.tsx", "tsx", r"""
'use client';
import { useState } from 'react';

export default function LikeButton({ initial }: { initial: number }) {
  const [likes, setLikes] = useState(initial);
  return <button className="like" onClick={() => setLikes((l) => l + 1)}>{likes} j'aime</button>;
}
"""), F("app/articles/[id]/Commentaires.tsx", "tsx", r"""
'use client';
import { useState } from 'react';

type Commentaire = { id: string; auteur: string; texte: string };

export default function Commentaires({ items }: { items: Commentaire[] }) {
  const [ouvert, setOuvert] = useState(false);
  return (
    <section>
      <button className="toggle" onClick={() => setOuvert((o) => !o)}>
        {ouvert ? 'Masquer' : `Voir les ${items.length} commentaires`}
      </button>
      {ouvert && <ul>{items.map((c) => <li key={c.id}><b>{c.auteur}</b> : {c.texte}</li>)}</ul>}
    </section>
  );
}
""")],
    run=NRUN(r"""
assert.equal(await next.render('/articles/dto'), 200, '/articles/dto → 200');
assert.equal($('h1').textContent, 'Les DTO expliqués', 'Titre de l\'article');
assert(!/^\s*['"]use client/.test(source('app/articles/[id]/page.tsx')), 'page.tsx n\'a pas \'use client\'');
assert(/^\s*['"]use client/.test(source('app/articles/[id]/LikeButton.tsx')), 'LikeButton.tsx commence par \'use client\'');
const like = $$('button').find((b) => b.textContent.includes("j'aime"));
assert.includes(like.textContent, '3', 'Compteur initial : 3 j\'aime');
await click(like); await click(like);
assert.includes(like.textContent, '5', 'Deux clics : 5 j\'aime');
const tog = $$('button').find((b) => b.textContent.includes('commentaires'));
assert.includes(tog.textContent, '2', 'Bouton « Voir les 2 commentaires »');
assert.equal($$('li').length, 0, 'Commentaires masqués au départ');
await click(tog);
assert.equal($$('li').length, 2, 'Après clic : 2 commentaires');
assert.includes(tog.textContent, 'Masquer', 'Le bouton devient « Masquer »');
assert.equal(await next.render('/articles/rien'), 404, 'Article inconnu → 404');
""")),
  tds=[
    TD(2, "Des onglets clients autour de contenu serveur",
       "La fiche produit a deux onglets : « Description » et « Disponibilité ». Le composant d'onglets est **client** (il retient l'onglet actif), mais le **contenu** de chaque onglet est rendu par des **Server Components** qui lisent les données. Tu utilises le motif `children`. " + SIM,
       ["`Onglets` (client) : reçoit `titres: string[]` et `children` (un tableau), affiche un `<button>` par titre et seulement l'enfant actif",
        "`Description` (serveur, async) : charge le produit et affiche son nom et son prix dans `<div className=\"desc\">`",
        "`Disponibilite` (serveur, async) : affiche « En stock (N) » ou « Rupture » dans `<div className=\"dispo\">`",
        "La page `/produits/[id]` assemble : `<Onglets titres={[…]}><Description id={id} /><Disponibilite id={id} /></Onglets>`",
        "`Onglets` n'importe aucun Server Component"],
       [PRODUITS, ROOT_LAYOUT, HOME,
        F("app/produits/[id]/Onglets.tsx", "tsx", r"""
'use client';
import { useState } from 'react';

export default function Onglets({ titres, children }: { titres: string[]; children: React.ReactNode[] }) {
  // à toi
  return null;
}
"""), F("app/produits/[id]/blocs.tsx", "tsx", r"""
import { getProduit } from '@/lib/produits';

export async function Description({ id }: { id: string }) {
  // à toi
}

export async function Disponibilite({ id }: { id: string }) {
  // à toi
}
"""), F("app/produits/[id]/page.tsx", "tsx", r"""
import Onglets from './Onglets';
import { Description, Disponibilite } from './blocs';

export default async function ProduitPage({ params }: { params: Promise<{ id: string }> }) {
  // à toi
}
""")],
       ["`children` arrive sous forme de tableau quand il y a plusieurs enfants : `children[actif]`.",
        "Les blocs serveur sont `async` et appellent `getProduit(id)` eux-mêmes.",
        "Un bouton actif peut avoir `className={i === actif ? 'actif' : ''}`."],
       [F("app/produits/[id]/Onglets.tsx", "tsx", r"""
'use client';
import { useState } from 'react';

export default function Onglets({ titres, children }: { titres: string[]; children: React.ReactNode[] }) {
  const [actif, setActif] = useState(0);
  return (
    <div>
      {titres.map((t, i) => (
        <button key={t} className={i === actif ? 'actif' : ''} onClick={() => setActif(i)}>{t}</button>
      ))}
      {children[actif]}
    </div>
  );
}
"""), F("app/produits/[id]/blocs.tsx", "tsx", r"""
import { getProduit } from '@/lib/produits';

export async function Description({ id }: { id: string }) {
  const p = await getProduit(id);
  return <div className="desc">{p?.nom} — {p?.prix} €</div>;
}

export async function Disponibilite({ id }: { id: string }) {
  const p = await getProduit(id);
  return <div className="dispo">{p && p.stock > 0 ? `En stock (${p.stock})` : 'Rupture'}</div>;
}
"""), F("app/produits/[id]/page.tsx", "tsx", r"""
import Onglets from './Onglets';
import { Description, Disponibilite } from './blocs';

export default async function ProduitPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <Onglets titres={['Description', 'Disponibilité']}>
      <Description id={id} />
      <Disponibilite id={id} />
    </Onglets>
  );
}
""")],
       ["Le contenu des onglets vient du serveur",
        "Changer d'onglet ne recharge pas la page"],
       run=NRUN(r"""
await next.render('/produits/ecran');
assert.equal($$('button').length, 2, '2 onglets');
assert($('.desc') && $('.desc').textContent.includes('Écran'), 'Onglet 1 : la description (rendue côté serveur)');
assert(!$('.dispo'), 'L\'onglet 2 est caché au départ');
const renders = next.renders;
await click($$('button')[1]);
assert($('.dispo') && $('.dispo').textContent.includes('En stock (4)'), 'Onglet 2 : « En stock (4) »');
assert.equal(next.renders, renders, 'Changer d\'onglet ne refait pas de rendu serveur');
await next.render('/produits/souris'); await click($$('button')[1]);
assert.includes($('.dispo').textContent, 'Rupture', 'Souris : « Rupture »');
assert(!/from '\.\/blocs'/.test(source('app/produits/[id]/Onglets.tsx')), 'Onglets n\'importe pas les blocs serveur');
""")),
    TD(3, "Réparer une frontière mal placée",
       "Cette page plante : le serveur passe une **fonction** `onChoisir` à un composant client. Next le refuse (une fonction n'est pas sérialisable). Tu dois déplacer le state et la logique **dans** le composant client, sans mettre `'use client'` sur la page, et garder le chargement des données sur le serveur. " + SIM,
       ["Lance le code et lis l'erreur affichée",
        "`/produits` charge toujours les produits côté serveur (la page reste un Server Component)",
        "`Selecteur` (client) reçoit seulement la **liste** des produits ; il gère lui-même le produit choisi",
        "Cliquer sur un produit affiche « Choisi : <nom> » dans `<p className=\"choix\">`",
        "Ne passe aucune fonction de la page vers le client"],
       [PRODUITS, ROOT_LAYOUT, HOME,
        F("app/produits/Selecteur.tsx", "tsx", r"""
'use client';

type Produit = { id: string; nom: string; prix: number; stock: number };

export default function Selecteur({ produits, choisi, onChoisir }: { produits: Produit[]; choisi: string | null; onChoisir: (nom: string) => void }) {
  return (
    <div>
      {produits.map((p) => <button key={p.id} onClick={() => onChoisir(p.nom)}>{p.nom}</button>)}
      {choisi && <p className="choix">Choisi : {choisi}</p>}
    </div>
  );
}
"""), F("app/produits/page.tsx", "tsx", r"""
import { getProduits } from '@/lib/produits';
import Selecteur from './Selecteur';

export default async function ProduitsPage() {
  const produits = await getProduits();
  let choisi: string | null = null;
  return <Selecteur produits={produits} choisi={choisi} onChoisir={(nom) => { choisi = nom; }} />;
}
""")],
       ["Une variable dans un Server Component ne peut pas « changer » après coup : la page est déjà envoyée. Le choix est un **état d'interface** : `useState` côté client.",
        "`const [choisi, setChoisi] = useState<string | null>(null);` dans `Selecteur`.",
        "La page devient simplement `return <Selecteur produits={produits} />;`"],
       [F("app/produits/Selecteur.tsx", "tsx", r"""
'use client';
import { useState } from 'react';

type Produit = { id: string; nom: string; prix: number; stock: number };

export default function Selecteur({ produits }: { produits: Produit[] }) {
  const [choisi, setChoisi] = useState<string | null>(null);
  return (
    <div>
      {produits.map((p) => <button key={p.id} onClick={() => setChoisi(p.nom)}>{p.nom}</button>)}
      {choisi && <p className="choix">Choisi : {choisi}</p>}
    </div>
  );
}
"""), F("app/produits/page.tsx", "tsx", r"""
import { getProduits } from '@/lib/produits';
import Selecteur from './Selecteur';

export default async function ProduitsPage() {
  const produits = await getProduits();
  return <Selecteur produits={produits} />;
}
""")],
       ["Plus d'erreur « Functions cannot be passed… »",
        "La page n'a toujours pas `'use client'`"],
       run=NRUN(r"""
const st = await next.render('/produits');
assert.equal(st, 200, '/produits → 200 (plus d\'erreur de frontière)');
assert.equal($$('button').length, 3, '3 produits affichés');
await click($$('button')[2]);
assert($('.choix') && $('.choix').textContent.includes('Écran'), 'Cliquer affiche « Choisi : Écran 27 pouces »');
assert(!/^\s*['"]use client/.test(source('app/produits/page.tsx')), 'La page reste un Server Component');
assert(!/onChoisir/.test(source('app/produits/page.tsx')), 'La page ne passe plus de fonction au client');
""")),
  ])

# ---------------------------------------------------------------- Données & cache
LIB_STATS = r"""
let ventes = 120;
__api["GET /stats"] = () => ({ ventes: ventes++ });
__api["GET /api/posts"] = () => window.__posts;
__api["GET /api/posts/:slug"] = (p) => window.__posts.find((x) => x.slug === p.slug) || [404, { error: 'introuvable' }];
__api["GET /api/posts/:slug/comments"] = (p) => (window.__comments[p.slug] || []);
__api["GET /api/user"] = () => ({ name: 'Ana' });
window.__posts = [
  { slug: 'dto', title: 'Les DTO expliqués', body: 'Un DTO décrit les données.' },
  { slug: 'hooks', title: 'Les hooks sans peur', body: 'Un hook commence par use.' },
  { slug: 'cache', title: 'Le cache de Next', body: 'Revalider au bon moment.' },
];
window.__comments = { dto: [{ id: 1, text: 'Super' }] };
"""

data = V2(v1["next-data"],
  prereq=[
    P("Cache", "Une copie d'un résultat gardée pour être réutilisée sans refaire le travail (sans rappeler l'API, sans relire la base)."),
    P("Statique / dynamique", "Une page **statique** est calculée une fois et resservie à tout le monde ; une page **dynamique** est recalculée à chaque visite."),
    P("Revalider", "Déclarer qu'une donnée en cache est périmée, pour qu'elle soit recalculée : au bout d'un délai (`revalidate: 60`) ou à la demande (`revalidatePath`)."),
    P("`Promise.all`", "Lance plusieurs promesses en même temps et attend qu'elles soient toutes terminées : le temps total est celui de la plus lente, pas la somme."),
    P("Streaming", "Envoyer la page en plusieurs morceaux : ce qui est prêt s'affiche tout de suite, le reste arrive ensuite (avec `<Suspense>`)."),
  ],
  diagram=D(
    nodes=[
      N("p", 0, 1, "Page (serveur)", "await fetch(...)", kind="file", color="accent"),
      N("c", 1, 1, "Cache Next", "par URL + options", kind="db", color="warn"),
      N("api", 2, 1, "API / base", "requête réelle", color="muted"),
      N("hit", 1, 2, "Réponse en cache", "si encore fraîche", kind="pill", color="good"),
      N("rv", 1, 0, "revalidate: 60 · revalidatePath()", "rend la donnée périmée", kind="note", color="warn"),
    ],
    edges=[E("p", "c"), E("c", "api", "absente ou périmée"), E("c", "hit", "fraîche", color="good"), E("rv", "c", dashed=True)],
    caption="Chaque fetch peut être mis en cache. Une donnée fraîche est resservie ; périmée (délai écoulé ou revalidation), elle est rechargée."),
  lessons=[
    L("Charger les données côté serveur", r"""
Dans le parcours React, on chargeait les données **dans le navigateur** : `useEffect`, trois states, un `AbortController`… Avec les Server Components, c'est beaucoup plus simple : le composant est `async`, il **attend** ses données et s'affiche avec.

```tsx
export default async function Dashboard() {
  const res = await fetch('https://api.exemple.com/stats');
  if (!res.ok) throw new Error('Stats indisponibles');   // affiche le error.tsx le plus proche
  const stats = await res.json();
  return <p>{stats.ventes} ventes</p>;
}
```

Pas d'état de chargement à gérer dans le composant : pendant l'attente, Next affiche `loading.tsx` s'il existe. Pas de risque d'exposer une clé d'API : le code ne part jamais au navigateur.

Et si les données sont dans **ta** base, on n'appelle pas sa propre API HTTP depuis un Server Component : on appelle **directement** la fonction d'accès aux données (`await db.produit.findMany()`, `await getProduits()`).
"""),
    L("Le cache : statique, revalidé ou dynamique", r"""
Next peut garder le résultat d'un `fetch` en cache pour ne pas rappeler l'API à chaque visite. Depuis **Next 15**, `fetch` n'est **plus** mis en cache par défaut : on le demande explicitement.

```ts
fetch(url)                                  // pas de cache : à chaque rendu
fetch(url, { cache: 'force-cache' })        // en cache jusqu'à revalidation
fetch(url, { next: { revalidate: 60 } })    // en cache, rechargé au plus toutes les 60 s
fetch(url, { cache: 'force-cache', next: { tags: ['posts'] } })   // en cache, étiqueté pour revalidateTag('posts')
```

Et au niveau de la page : `export const revalidate = 60;` applique ce délai à toute la page.

Comment choisir :

- Contenu qui change rarement (articles, fiches produit) : `revalidate` de quelques minutes, ou cache + revalidation **à la demande** après modification.
- Données personnelles ou temps réel (panier, tableau de bord) : pas de cache.

Après une écriture (nouvel article, produit modifié), on invalide le cache concerné avec `revalidatePath('/blog')` ou `revalidateTag('posts')` : la prochaine visite recalcule la page.

Attention, les versions bougent : Next 16 introduit la directive `'use cache'` (« Cache Components »). Les principes restent les mêmes ; vérifie la documentation de ta version.
"""),
    L("En parallèle, pas en série", r"""
Deux `await` à la suite attendent **l'un après l'autre** :

```ts
const stats = await getStats();   // 1 s
const user = await getUser();     // + 1 s  => 2 s
```

Si les deux requêtes sont **indépendantes**, lance-les en même temps avec `Promise.all` :

```ts
const [stats, user] = await Promise.all([getStats(), getUser()]);   // 1 s
```

C'est l'optimisation la plus simple et la plus efficace d'une page serveur. Garde les `await` successifs seulement quand la 2e requête **dépend** du résultat de la 1re (charger l'article, puis l'auteur de cet article).
"""),
    L("Afficher vite avec `<Suspense>`", r"""
Même en parallèle, une page attend sa donnée **la plus lente** avant de s'afficher. Si une partie est lente mais secondaire (les commentaires sous un article), on peut l'isoler dans son propre composant async entouré de `<Suspense>` :

```tsx
import { Suspense } from 'react';

export default async function PostPage({ params }) {
  const { slug } = await params;
  const post = await getPost(slug);                  // rapide : affiché tout de suite
  return (
    <article>
      <h1>{post.title}</h1>
      <Suspense fallback={<p>Chargement des commentaires…</p>}>
        <Commentaires slug={slug} />                  {/* lent : arrive ensuite */}
      </Suspense>
    </article>
  );
}

async function Commentaires({ slug }: { slug: string }) {
  const comments = await getComments(slug);
  return <ul>{comments.map((c) => <li key={c.id}>{c.text}</li>)}</ul>;
}
```

Next envoie d'abord l'article et le `fallback`, puis **diffuse** (streaming) les commentaires dès qu'ils sont prêts. `loading.tsx` fait la même chose pour une page entière.

Enfin, `generateStaticParams` permet de **pré-générer** au build les pages dynamiques les plus visitées (les 20 derniers articles), qui sont alors servies instantanément.
"""),
  ],
  recap=[
    "Un Server Component `async` charge ses données directement ; pas de `useEffect`, pas de clé exposée.",
    "Next 15 : `fetch` sans cache par défaut ; `next: { revalidate }`, `cache: 'force-cache'`, `tags` pour l'activer.",
    "Après une écriture : `revalidatePath` / `revalidateTag` pour invalider.",
    "Requêtes indépendantes → `Promise.all` (temps = la plus lente, pas la somme).",
    "`<Suspense>` + composant async : afficher l'essentiel tout de suite, le lent ensuite.",
    "Ta propre base : appelle la fonction d'accès aux données, pas ta propre API HTTP.",
  ],
  example=[F("app/dashboard/page.tsx", "tsx", r"""
import { Suspense } from 'react';

async function getStats() {
  const res = await fetch('https://api.exemple.com/stats', { next: { revalidate: 60 } });
  if (!res.ok) throw new Error('Stats indisponibles');
  return res.json();
}

async function getUser() {
  const res = await fetch('https://api.exemple.com/user', { cache: 'no-store' });   // personnel
  return res.json();
}

export default async function Dashboard() {
  const [stats, user] = await Promise.all([getStats(), getUser()]);   // en parallèle

  return (
    <main>
      <h1>Bonjour {user.name}</h1>
      <p>{stats.ventes} ventes</p>
      <Suspense fallback={<p>Chargement des commandes…</p>}>
        <DernieresCommandes />
      </Suspense>
    </main>
  );
}

async function DernieresCommandes() {
  const res = await fetch('https://api.exemple.com/commandes?limit=5', { cache: 'no-store' });
  const commandes: { id: number; total: number }[] = await res.json();
  return <ul>{commandes.map((c) => <li key={c.id}>Commande {c.id} : {c.total} €</li>)}</ul>;
}
""")],
  notes=["`getStats` : en cache 60 s ; `getUser` et les commandes : jamais en cache (données personnelles).",
         "`Promise.all` : stats et utilisateur sont demandés en même temps.",
         "`DernieresCommandes` est isolé dans `<Suspense>` : la page s'affiche sans l'attendre.",
         "Une erreur dans `getStats` affiche le `error.tsx` le plus proche."],
  td1=dict(path="app/blog/[slug]/page.tsx",
    title="Blog avec cache",
    enonce="Règle le chargement et le cache d'un blog qui lit ses articles depuis une API. Les tests avancent une **horloge simulée** (`next.advance(secondes)`) pour vérifier quand l'API est rappelée. " + SIM,
    consignes=["`/blog` : un `<li>` par article (titre), données de `fetch('https://api.exemple.com/api/posts', { next: { revalidate: 300 } })`",
               "Deux visites dans les 5 minutes = **un seul** appel à l'API ; après 5 minutes, un nouvel appel",
               "`/blog/[slug]` : le titre en `<h1>` et le texte ; 404 si l'API répond 404",
               "Les commentaires (`/api/posts/<slug>/comments`, **sans** cache) sont dans un composant async entouré de `<Suspense>`",
               "`generateStaticParams` (dans `[slug]/page.tsx`) renvoie `[{ slug }, …]` pour tous les articles"],
    hints=["`const res = await fetch(url, { next: { revalidate: 300 } }); const posts = await res.json();`",
           "404 : `if (res.status === 404) return null;` puis `notFound()` dans la page.",
           "`export async function generateStaticParams() { const posts = await getPosts(); return posts.map((p) => ({ slug: p.slug })); }`"],
    checks=["Deux visites rapprochées n'appellent l'API qu'une fois", "Les commentaires sont dans un `<Suspense>`"],
    files=[ROOT_LAYOUT, HOME,
           F("lib/posts.ts", "ts", r"""
const API = 'https://api.exemple.com/api/posts';
export type Post = { slug: string; title: string; body: string };

// à toi : getPosts() avec revalidate 300, getPost(slug) (null si 404), getComments(slug) sans cache
"""), F("app/blog/page.tsx", "tsx", r"""
import { getPosts } from '@/lib/posts';
// à toi
"""), F("app/blog/[slug]/page.tsx", "tsx", r"""
import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import { getPost, getPosts, getComments } from '@/lib/posts';
// à toi
""")],
    solution=[F("lib/posts.ts", "ts", r"""
const API = 'https://api.exemple.com/api/posts';
export type Post = { slug: string; title: string; body: string };

export async function getPosts(): Promise<Post[]> {
  const res = await fetch(API, { next: { revalidate: 300 } });
  return res.json();
}

export async function getPost(slug: string): Promise<Post | null> {
  const res = await fetch(`${API}/${slug}`, { next: { revalidate: 300 } });
  if (res.status === 404) return null;
  return res.json();
}

export async function getComments(slug: string): Promise<{ id: number; text: string }[]> {
  const res = await fetch(`${API}/${slug}/comments`, { cache: 'no-store' });
  return res.json();
}
"""), F("app/blog/page.tsx", "tsx", r"""
import Link from 'next/link';
import { getPosts } from '@/lib/posts';

export default async function BlogPage() {
  const posts = await getPosts();
  return <ul>{posts.map((p) => <li key={p.slug}><Link href={`/blog/${p.slug}`}>{p.title}</Link></li>)}</ul>;
}
"""), F("app/blog/[slug]/page.tsx", "tsx", r"""
import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import { getPost, getPosts, getComments } from '@/lib/posts';

export async function generateStaticParams() {
  const posts = await getPosts();
  return posts.map((p) => ({ slug: p.slug }));
}

async function Commentaires({ slug }: { slug: string }) {
  const comments = await getComments(slug);
  return <ul className="comments">{comments.map((c) => <li key={c.id}>{c.text}</li>)}</ul>;
}

export default async function PostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await getPost(slug);
  if (!post) notFound();
  return (
    <article>
      <h1>{post.title}</h1>
      <p>{post.body}</p>
      <Suspense fallback={<p>Chargement des commentaires…</p>}>
        <Commentaires slug={slug} />
      </Suspense>
    </article>
  );
}
""")],
    run=NRUN(r"""
await next.render('/blog');
assert.equal($$('li').length, 3, '/blog : 3 articles');
const n1 = next.fetchCalls;
next.advance(120); await next.render('/blog');
assert.equal(next.fetchCalls, n1, 'Revisite après 2 min : pas de nouvel appel (cache)');
next.advance(200); await next.render('/blog');
assert.equal(next.fetchCalls, n1 + 1, 'Après plus de 5 min : un nouvel appel');
assert.equal(await next.render('/blog/dto'), 200, '/blog/dto → 200');
assert.equal($('h1').textContent, 'Les DTO expliqués', 'Titre de l\'article');
assert.includes(text(), 'Super', 'Les commentaires sont affichés');
window.__comments.dto.push({ id: 2, text: 'Nouveau commentaire' });
next.advance(10); await next.render('/blog/dto');
assert.includes(text(), 'Nouveau commentaire', 'Commentaires sans cache : le nouveau apparaît tout de suite');
assert(/<Suspense/.test(source('app/blog/[slug]/page.tsx')), 'Les commentaires sont dans un <Suspense>');
assert.equal(await next.render('/blog/inconnu'), 404, 'Slug inconnu → 404');
const mod = require('./app/blog/[slug]/page');
const params = await mod.generateStaticParams();
assert(Array.isArray(params) && params.length === 3 && params[0].slug === 'dto', 'generateStaticParams renvoie les 3 slugs');
""", api=LIB_STATS)),
  tds=[
    TD(2, "Paralléliser un tableau de bord",
       "Ce tableau de bord enchaîne trois requêtes **indépendantes** avec trois `await` : il attend la somme des trois. Réécris-le pour qu'elles partent **en même temps**, et règle le cache de chacune selon sa nature. " + SIM,
       ["Les trois requêtes (stats, utilisateur, articles) partent en parallèle (`Promise.all`)",
        "`stats` : cache de 60 s ; `user` : jamais en cache (`no-store`) ; `posts` : en cache (`force-cache`) avec le tag `'posts'`",
        "La page affiche `Bonjour <nom>`, `<N> ventes` et le nombre d'articles",
        "Deux rendus à 10 s d'intervalle : le nombre de ventes ne change pas (cache), le nom est redemandé",
        "Ne change pas ce que la page affiche"],
       [ROOT_LAYOUT, HOME,
        F("app/dashboard/page.tsx", "tsx", r"""
const API = 'https://api.exemple.com';

export default async function Dashboard() {
  const stats = await fetch(`${API}/stats`).then((r) => r.json());
  const user = await fetch(`${API}/api/user`).then((r) => r.json());
  const posts = await fetch(`${API}/api/posts`).then((r) => r.json());

  return (
    <main>
      <h1>Bonjour {user.name}</h1>
      <p className="ventes">{stats.ventes} ventes</p>
      <p className="articles">{posts.length} articles</p>
    </main>
  );
}
""")],
       ["`const [stats, user, posts] = await Promise.all([fetch(...).then(...), ...]);`",
        "Options : `{ next: { revalidate: 60 } }`, `{ cache: 'no-store' }`, `{ cache: 'force-cache', next: { tags: ['posts'] } }`.",
        "Depuis Next 15, `tags` seul ne met pas en cache : il faut `cache: 'force-cache'`. Sans délai, la donnée reste en cache jusqu'à `revalidateTag('posts')`."],
       [F("app/dashboard/page.tsx", "tsx", r"""
const API = 'https://api.exemple.com';

export default async function Dashboard() {
  const [stats, user, posts] = await Promise.all([
    fetch(`${API}/stats`, { next: { revalidate: 60 } }).then((r) => r.json()),
    fetch(`${API}/api/user`, { cache: 'no-store' }).then((r) => r.json()),
    fetch(`${API}/api/posts`, { cache: 'force-cache', next: { tags: ['posts'] } }).then((r) => r.json()),
  ]);

  return (
    <main>
      <h1>Bonjour {user.name}</h1>
      <p className="ventes">{stats.ventes} ventes</p>
      <p className="articles">{posts.length} articles</p>
    </main>
  );
}
""")],
       ["Les 3 requêtes sont en vol en même temps",
        "Le nombre de ventes reste en cache 60 s"],
       run=NRUN(r"""
next.maxInflight = 0;
await next.render('/dashboard');
assert.includes(text(), 'Bonjour Ana', 'Bonjour Ana');
assert(next.maxInflight >= 3, 'Les 3 requêtes partent en parallèle (' + next.maxInflight + ' en même temps)');
const v1 = $('.ventes').textContent;
const n = next.fetchCalls;
next.advance(10); await next.render('/dashboard');
assert.equal($('.ventes').textContent, v1, 'À +10 s : ventes identiques (cache 60 s)');
assert.equal(next.fetchCalls, n + 1, 'À +10 s : seul l\'utilisateur est redemandé');
next.advance(60); await next.render('/dashboard');
assert($('.ventes').textContent !== v1, 'Après 60 s : les ventes sont rechargées');
assert.includes($('.articles').textContent, '3', '3 articles');
""", api=LIB_STATS)),
    TD(3, "Invalider le bon cache après une écriture",
       "Les articles sont en cache sans délai (tag `'posts'`). Quand un admin publie un article via une **Server Action**, la liste doit se mettre à jour immédiatement, et seulement elle : les stats, en cache elles aussi, ne doivent **pas** être rechargées. " + SIM,
       ["`getPosts()` : `fetch(..., { cache: 'force-cache', next: { tags: ['posts'] } })` ; `getStats()` : pareil avec le tag `'stats'`",
        "`app/admin/actions.ts` (`'use server'`) : `publier(formData)` ajoute l'article (fonction `ajouterPost` fournie) puis `revalidateTag('posts')`",
        "`/admin` affiche le nombre d'articles (`<p className=\"nb\">`), les ventes (`<p className=\"ventes\">`) et un formulaire `<form action={publier}>` avec un champ `titre`",
        "Après publication, `nb` augmente **sans** recharger la page à la main, et `ventes` ne change pas",
        "N'utilise pas `revalidatePath('/')` (trop large)"],
       [ROOT_LAYOUT, HOME,
        F("lib/blog.ts", "ts", r"""
const API = 'https://api.exemple.com';

// Fourni : simule l'écriture en base
export async function ajouterPost(title: string) {
  (window as any).__posts.push({ slug: title.toLowerCase().replace(/\W+/g, '-'), title, body: '' });
}

// à toi : getPosts(), getStats()
"""), F("app/admin/actions.ts", "ts", r"""
'use server';
import { revalidateTag } from 'next/cache';
import { ajouterPost } from '@/lib/blog';

// à toi : publier(formData)
"""), F("app/admin/page.tsx", "tsx", r"""
import { getPosts, getStats } from '@/lib/blog';
import { publier } from './actions';

export default async function Admin() {
  // à toi
}
""")],
       ["`export async function publier(formData: FormData) { await ajouterPost(String(formData.get('titre'))); revalidateTag('posts'); }`",
        "`revalidateTag` supprime du cache seulement les fetch qui ont ce tag ; la page est recalculée, et les stats restent en cache.",
        "Le formulaire : `<form action={publier}><input name=\"titre\" /><button>Publier</button></form>`."],
       [F("lib/blog.ts", "ts", r"""
const API = 'https://api.exemple.com';

export async function ajouterPost(title: string) {
  (window as any).__posts.push({ slug: title.toLowerCase().replace(/\W+/g, '-'), title, body: '' });
}

export async function getPosts(): Promise<{ slug: string; title: string }[]> {
  return fetch(`${API}/api/posts`, { cache: 'force-cache', next: { tags: ['posts'] } }).then((r) => r.json());
}

export async function getStats(): Promise<{ ventes: number }> {
  return fetch(`${API}/stats`, { cache: 'force-cache', next: { tags: ['stats'] } }).then((r) => r.json());
}
"""), F("app/admin/actions.ts", "ts", r"""
'use server';
import { revalidateTag } from 'next/cache';
import { ajouterPost } from '@/lib/blog';

export async function publier(formData: FormData) {
  await ajouterPost(String(formData.get('titre') ?? ''));
  revalidateTag('posts');
}
"""), F("app/admin/page.tsx", "tsx", r"""
import { getPosts, getStats } from '@/lib/blog';
import { publier } from './actions';

export default async function Admin() {
  const [posts, stats] = await Promise.all([getPosts(), getStats()]);
  return (
    <main>
      <p className="nb">{posts.length} articles</p>
      <p className="ventes">{stats.ventes} ventes</p>
      <form action={publier}>
        <input name="titre" />
        <button>Publier</button>
      </form>
    </main>
  );
}
""")],
       ["Le compteur d'articles augmente après publication",
        "Le compteur de ventes ne bouge pas"],
       run=NRUN(r"""
await next.render('/admin');
assert.includes($('.nb').textContent, '3', '3 articles au départ');
const ventes = $('.ventes').textContent;
next.advance(1000); await next.render('/admin');
assert.equal($('.ventes').textContent, ventes, 'Sans revalidation, les ventes restent en cache');
await type('input[name=titre]', 'Nouvel article');
await submit('form');
await waitFor(() => $('.nb') && $('.nb').textContent.includes('4'), 3000);
assert(true, 'Après publication : 4 articles, sans rechargement manuel');
assert.equal($('.ventes').textContent, ventes, 'Les ventes ne sont pas rechargées (bon tag invalidé)');
assert(next.log.includes('revalidateTag posts'), 'revalidateTag(\'posts\') a été appelé');
assert(!next.log.some((l) => l === 'revalidatePath /'), 'Pas de revalidatePath(\'/\')');
""", api=LIB_STATS)),
  ])

# ---------------------------------------------------------------- Server Actions
DB_COMMENTS = F("lib/db.ts", "ts", r"""
// Fausse base (en mémoire), côté serveur
export type Commentaire = { id: number; articleId: string; auteur: string; texte: string; userId: number };

export const db = {
  commentaires: [
    { id: 1, articleId: 'dto', auteur: 'Ana', texte: 'Très clair !', userId: 1 },
    { id: 2, articleId: 'dto', auteur: 'Léo', texte: 'Merci pour les exemples.', userId: 2 },
  ] as Commentaire[],
  nextId: 3,
};

// Fourni : l'utilisateur connecté (en vrai : la session / un cookie)
export const session = { userId: 1 as number | null, nom: 'Ana' };
export async function getSession() { return session.userId ? { userId: session.userId, nom: session.nom } : null; }
""")

actions = V2(v1["next-actions"],
  prereq=[
    P("FormData", "L'objet que le navigateur construit à l'envoi d'un formulaire : `formData.get('auteur')` donne la valeur du champ `name=\"auteur\"`. Les valeurs sont des chaînes."),
    P("Server Action", "Une fonction `async` marquée `'use server'` : elle s'exécute **sur le serveur**, mais un formulaire ou un composant client peut l'appeler comme une fonction normale."),
    P("`useActionState`", "Hook de React 19 qui relie une action à un formulaire et garde son **résultat** (erreurs, message) et son état d'envoi (`pending`)."),
    P("`.bind(null, x)`", "Crée une copie d'une fonction avec un premier argument déjà fixé : `ajouter.bind(null, 'dto')` appellera `ajouter('dto', …)`."),
    P("Amélioration progressive", "Un formulaire avec Server Action fonctionne même si le JavaScript n'est pas encore chargé : c'est un vrai `<form>` HTML."),
  ],
  diagram=D(
    nodes=[
      N("form", 0, 1, "<form action>", "composant client", kind="file", color="accent"),
      N("act", 1, 1, "addComment()", "'use server'\nvalide + enregistre", color="warn"),
      N("db", 2, 0, "Base", "INSERT", kind="db", color="muted"),
      N("rv", 2, 2, "revalidatePath", "/articles/dto", kind="pill", color="good"),
      N("page", 3, 2, "Page recalculée", "le commentaire apparaît", kind="doc", color="good"),
    ],
    edges=[E("form", "act", "FormData"), E("act", "db"), E("act", "rv"), E("rv", "page", color="good"), E("act", "form", "erreurs (state)", dashed=True, color="bad", back=True)],
    caption="Le formulaire appelle directement une fonction serveur. Elle valide, écrit, invalide la page ; en cas d'erreur, elle renvoie un état que le formulaire affiche."),
  lessons=[
    L("Le problème que ça résout", r"""
Pour enregistrer un commentaire depuis React sans Server Actions, il faut :

1. une **route d'API** côté serveur (`POST /api/commentaires`) qui lit le JSON, valide, enregistre ;
2. côté client : un `fetch`/axios, des states `saving`/`error`, le `preventDefault` ;
3. puis recharger la liste pour afficher le nouveau commentaire.

Avec une **Server Action**, on écrit une simple fonction serveur, et le formulaire l'appelle directement :

```ts
// app/articles/[id]/actions.ts
'use server';

export async function addComment(formData: FormData) {
  const texte = String(formData.get('texte') ?? '').trim();
  await db.comment.create({ data: { texte } });
  revalidatePath('/articles/dto');
}
```

```tsx
<form action={addComment}>
  <textarea name="texte" />
  <button>Publier</button>
</form>
```

Next s'occupe de l'aller-retour HTTP. Pas de route, pas de `fetch`, et la page se met à jour grâce à `revalidatePath`.
"""),
    L("Valider et renvoyer des erreurs avec `useActionState`", r"""
Une Server Action est **un point d'entrée public** : n'importe qui peut l'appeler avec n'importe quelles données (comme une route d'API). On valide donc **toujours** dans l'action, même si le formulaire a `required` ou `maxLength`.

Pour renvoyer les erreurs au formulaire, l'action reçoit un **état précédent** et renvoie le **nouvel état** :

```ts
export type State = { errors?: { auteur?: string; texte?: string } };

export async function addComment(_prev: State, formData: FormData): Promise<State> {
  const auteur = String(formData.get('auteur') ?? '').trim();
  const errors: State['errors'] = {};
  if (auteur.length < 2) errors.auteur = 'Entre 2 et 50 caractères';
  if (Object.keys(errors).length) return { errors };   // rien n'est enregistré
  // ... enregistrer, revalider
  return {};
}
```

Côté client, `useActionState` branche l'action et donne trois choses :

```tsx
'use client';
const [state, formAction, pending] = useActionState(addComment, {});

<form action={formAction}>
  <input name="auteur" />
  {state.errors?.auteur && <p role="alert">{state.errors.auteur}</p>}
  <button disabled={pending}>{pending ? 'Envoi…' : 'Publier'}</button>
</form>
```

- `state` : ce que l'action a renvoyé la dernière fois (les erreurs).
- `formAction` : à passer au `<form action>`.
- `pending` : vrai pendant l'envoi.
"""),
    L("Passer un id sans champ caché : `.bind`", r"""
L'action a souvent besoin d'un identifiant (l'article commenté). Tentation : un `<input type="hidden" name="articleId">`. Problème : un utilisateur peut modifier ce champ dans son navigateur.

On **lie** plutôt l'argument côté serveur avec `.bind` :

```tsx
// composant client, qui reçoit articleId du Server Component parent
const action = addComment.bind(null, articleId);
const [state, formAction, pending] = useActionState(action, {});
```

```ts
export async function addComment(articleId: string, _prev: State, formData: FormData) { … }
```

Mais attention : même avec `.bind`, **l'action reste appelable** avec d'autres valeurs par quelqu'un de malveillant. La vraie protection est ailleurs : dans l'action, **vérifie l'utilisateur connecté et ses droits** (est-ce bien son commentaire ? a-t-il le droit de publier ?).
"""),
    L("Après l'action : revalider ou rediriger", r"""
Une fois l'écriture faite, deux suites possibles :

- **Rester sur la page** et l'actualiser : `revalidatePath('/articles/dto')`. Next recalcule les Server Components de la page ; les composants client gardent leur state.
- **Aller ailleurs** : `redirect('/articles/' + id)` après une création. Comme dans une page, `redirect` interrompt l'action.

```ts
export async function creerArticle(_prev: State, formData: FormData): Promise<State> {
  const titre = String(formData.get('titre') ?? '').trim();
  if (titre.length < 5) return { error: '5 caractères minimum' };
  const article = await db.article.create({ data: { titre } });
  revalidatePath('/articles');
  redirect(`/articles/${article.id}`);       // ne renvoie jamais
}
```

Ordre à respecter : **valider → vérifier les droits → écrire → revalider → (rediriger)**. Si la validation échoue, on renvoie l'erreur **avant** toute écriture.
"""),
  ],
  recap=[
    "Une Server Action (`'use server'`) est une fonction serveur appelée directement par un formulaire.",
    "C'est un point d'entrée public : **valider** et **vérifier les droits** dans l'action, toujours.",
    "`useActionState(action, état)` → `[state, formAction, pending]` ; l'action reçoit `(prev, formData)` et renvoie le nouvel état.",
    "Fixer un id avec `.bind(null, id)` plutôt qu'un champ caché, sans oublier le contrôle des droits.",
    "Après l'écriture : `revalidatePath` pour rafraîchir, ou `redirect` pour changer de page.",
  ],
  example=[DB_COMMENTS, F("app/articles/[id]/actions.ts", "ts", r"""
'use server';
import { revalidatePath } from 'next/cache';
import { db } from '@/lib/db';

export type CommentState = { errors?: { auteur?: string; texte?: string } };

export async function addComment(articleId: string, _prev: CommentState, formData: FormData): Promise<CommentState> {
  const auteur = String(formData.get('auteur') ?? '').trim();
  const texte = String(formData.get('texte') ?? '').trim();

  const errors: CommentState['errors'] = {};
  if (auteur.length < 2 || auteur.length > 50) errors.auteur = 'Entre 2 et 50 caractères';
  if (texte.length < 5 || texte.length > 500) errors.texte = 'Entre 5 et 500 caractères';
  if (Object.keys(errors).length > 0) return { errors };

  db.commentaires.push({ id: db.nextId++, articleId, auteur, texte, userId: 1 });
  revalidatePath(`/articles/${articleId}`);
  return {};
}
"""), F("app/articles/[id]/CommentForm.tsx", "tsx", r"""
'use client';
import { useActionState } from 'react';
import { addComment, type CommentState } from './actions';

export default function CommentForm({ articleId }: { articleId: string }) {
  const action = addComment.bind(null, articleId);
  const [state, formAction, pending] = useActionState<CommentState, FormData>(action, {});

  return (
    <form action={formAction}>
      <input name="auteur" placeholder="Ton nom" />
      {state.errors?.auteur && <p role="alert">{state.errors.auteur}</p>}
      <textarea name="texte" placeholder="Ton commentaire" />
      {state.errors?.texte && <p role="alert">{state.errors.texte}</p>}
      <button disabled={pending}>{pending ? 'Envoi…' : 'Publier'}</button>
    </form>
  );
}
"""), F("app/articles/[id]/page.tsx", "tsx", r"""
import { db } from '@/lib/db';
import CommentForm from './CommentForm';

export default async function ArticlePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const commentaires = db.commentaires.filter((c) => c.articleId === id);
  return (
    <article>
      <ul>{commentaires.map((c) => <li key={c.id}><b>{c.auteur}</b> : {c.texte}</li>)}</ul>
      <CommentForm articleId={id} />
    </article>
  );
}
""")],
  notes=["`actions.ts` commence par `'use server'` : ses fonctions s'exécutent sur le serveur.",
         "L'action valide d'abord et renvoie les erreurs **sans rien enregistrer** si besoin.",
         "`CommentForm` (client) fixe `articleId` avec `.bind` et affiche `state.errors` sous chaque champ.",
         "`revalidatePath` recalcule la page : la liste (Server Component) affiche le nouveau commentaire."],
  td1=dict(path="app/articles/[id]/actions.ts",
    title="Commentaires avec Server Action",
    enonce="Ajoute un formulaire de commentaire à la page article : validation dans l'action, erreurs sous les champs, mise à jour de la liste sans recharger. " + SIM,
    consignes=["`addComment(articleId, prev, formData)` : auteur 2 à 50 caractères, texte 5 à 500 ; erreurs par champ renvoyées dans l'état",
               "Valide → ajout dans `db.commentaires`, puis `revalidatePath` de la page de l'article",
               "`CommentForm` (client) : `useActionState`, un `<p role=\"alert\">` sous chaque champ en erreur",
               "Le bouton affiche « Envoi… » et est désactivé pendant l'envoi",
               "`articleId` est fixé avec `.bind`, pas avec un champ caché"],
    hints=["Signature : `export async function addComment(articleId: string, _prev: CommentState, formData: FormData): Promise<CommentState>`",
           "`const action = addComment.bind(null, articleId);` puis `useActionState(action, {})`.",
           "La page liste `db.commentaires.filter((c) => c.articleId === id)` : après `revalidatePath`, elle est recalculée."],
    checks=["Un texte de 3 caractères affiche une erreur sous le champ", "Le nouveau commentaire apparaît sans recharger"],
    files=[DB_COMMENTS, ROOT_LAYOUT, HOME,
           F("app/articles/[id]/page.tsx", "tsx", r"""
import { db } from '@/lib/db';
import CommentForm from './CommentForm';

export default async function ArticlePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const commentaires = db.commentaires.filter((c) => c.articleId === id);
  return (
    <article>
      <ul>{commentaires.map((c) => <li key={c.id}><b>{c.auteur}</b> : {c.texte}</li>)}</ul>
      <CommentForm articleId={id} />
    </article>
  );
}
"""), F("app/articles/[id]/actions.ts", "ts", r"""
'use server';
import { revalidatePath } from 'next/cache';
import { db } from '@/lib/db';

export type CommentState = { errors?: { auteur?: string; texte?: string } };

// à toi : addComment
"""), F("app/articles/[id]/CommentForm.tsx", "tsx", r"""
'use client';
import { useActionState } from 'react';
import { addComment, type CommentState } from './actions';

export default function CommentForm({ articleId }: { articleId: string }) {
  // à toi
  return null;
}
""")],
    solution=[F("app/articles/[id]/actions.ts", "ts", r"""
'use server';
import { revalidatePath } from 'next/cache';
import { db } from '@/lib/db';

export type CommentState = { errors?: { auteur?: string; texte?: string } };

export async function addComment(articleId: string, _prev: CommentState, formData: FormData): Promise<CommentState> {
  const auteur = String(formData.get('auteur') ?? '').trim();
  const texte = String(formData.get('texte') ?? '').trim();
  const errors: CommentState['errors'] = {};
  if (auteur.length < 2 || auteur.length > 50) errors.auteur = 'Entre 2 et 50 caractères';
  if (texte.length < 5 || texte.length > 500) errors.texte = 'Entre 5 et 500 caractères';
  if (Object.keys(errors).length > 0) return { errors };

  db.commentaires.push({ id: db.nextId++, articleId, auteur, texte, userId: 1 });
  revalidatePath(`/articles/${articleId}`);
  return {};
}
"""), F("app/articles/[id]/CommentForm.tsx", "tsx", r"""
'use client';
import { useActionState } from 'react';
import { addComment, type CommentState } from './actions';

export default function CommentForm({ articleId }: { articleId: string }) {
  const action = addComment.bind(null, articleId);
  const [state, formAction, pending] = useActionState<CommentState, FormData>(action, {});
  return (
    <form action={formAction}>
      <input name="auteur" placeholder="Ton nom" />
      {state.errors?.auteur && <p role="alert">{state.errors.auteur}</p>}
      <textarea name="texte" placeholder="Ton commentaire" />
      {state.errors?.texte && <p role="alert">{state.errors.texte}</p>}
      <button disabled={pending}>{pending ? 'Envoi…' : 'Publier'}</button>
    </form>
  );
}
""")],
    run=NRUN(r"""
await next.render('/articles/dto');
assert.equal($$('li').length, 2, '2 commentaires au départ');
await type('input[name=auteur]', 'Zoé');
await type('textarea[name=texte]', 'abc');
await submit('form');
await waitFor(() => $$('[role=alert]').length === 1, 3000);
assert.includes($('[role=alert]').textContent, '5', 'Texte trop court : erreur sous le champ texte');
assert.equal($$('li').length, 2, 'Rien n\'a été enregistré');
await type('input[name=auteur]', 'Zoé');
await type('textarea[name=texte]', 'Un commentaire valide');
await submit('form');
await waitFor(() => $$('li').length === 3, 3000);
assert.includes($$('li')[2].textContent, 'Un commentaire valide', 'Le nouveau commentaire apparaît sans recharger');
assert(next.log.includes('revalidatePath /articles/dto'), 'revalidatePath(\'/articles/dto\') appelé');
assert(!/type=["']hidden["']/.test(source('app/articles/[id]/CommentForm.tsx')), 'Pas de champ caché pour l\'id');
const { addComment } = require('./app/articles/[id]/actions');
const fd = new FormData(); fd.set('auteur', 'X'); fd.set('texte', 'ok');
const r = await addComment('dto', {}, fd);
assert(r.errors && r.errors.auteur && r.errors.texte, 'L\'action elle-même refuse des données invalides');
""", start="/articles/dto")),
  tds=[
    TD(2, "Supprimer : vérifier les droits dans l'action",
       "Chaque commentaire a un bouton « Supprimer ». L'interface ne l'affiche que pour l'auteur, mais ce n'est **pas** une protection : l'action peut être appelée par n'importe qui, avec n'importe quel id. La vérification doit se faire **dans l'action**. " + SIM,
       ["`supprimer(id: number)` (`'use server'`) : récupère la session ; pas connecté → `{ error: 'Connecte-toi' }`",
        "Commentaire introuvable → `{ error: 'Introuvable' }` ; pas l'auteur (`userId` différent) → `{ error: 'Interdit' }`",
        "Sinon : supprime, `revalidatePath('/articles/dto')`, renvoie `{ ok: true }`",
        "`BoutonSupprimer` (client) appelle l'action au clic et affiche `result.error` dans `<p role=\"alert\">`",
        "La page n'affiche le bouton que pour les commentaires de l'utilisateur connecté"],
       [DB_COMMENTS, ROOT_LAYOUT, HOME,
        F("app/articles/[id]/actions.ts", "ts", r"""
'use server';
import { revalidatePath } from 'next/cache';
import { db, getSession } from '@/lib/db';

// à toi : supprimer(id)
"""), F("app/articles/[id]/BoutonSupprimer.tsx", "tsx", r"""
'use client';
import { useState } from 'react';
import { supprimer } from './actions';

export default function BoutonSupprimer({ id }: { id: number }) {
  // à toi
  return null;
}
"""), F("app/articles/[id]/page.tsx", "tsx", r"""
import { db, getSession } from '@/lib/db';
import BoutonSupprimer from './BoutonSupprimer';

export default async function ArticlePage({ params }: { params: Promise<{ id: string }> }) {
  // à toi
}
""")],
       ["Ordre : session → commentaire existe → droits → suppression.",
        "Supprimer d'un tableau : `const i = db.commentaires.findIndex((c) => c.id === id); db.commentaires.splice(i, 1);`",
        "Une Server Action peut être appelée comme une fonction depuis un client : `const r = await supprimer(id);`."],
       [F("app/articles/[id]/actions.ts", "ts", r"""
'use server';
import { revalidatePath } from 'next/cache';
import { db, getSession } from '@/lib/db';

export async function supprimer(id: number): Promise<{ ok?: true; error?: string }> {
  const session = await getSession();
  if (!session) return { error: 'Connecte-toi' };
  const i = db.commentaires.findIndex((c) => c.id === id);
  if (i === -1) return { error: 'Introuvable' };
  if (db.commentaires[i].userId !== session.userId) return { error: 'Interdit' };
  db.commentaires.splice(i, 1);
  revalidatePath('/articles/dto');
  return { ok: true };
}
"""), F("app/articles/[id]/BoutonSupprimer.tsx", "tsx", r"""
'use client';
import { useState } from 'react';
import { supprimer } from './actions';

export default function BoutonSupprimer({ id }: { id: number }) {
  const [error, setError] = useState<string | null>(null);
  return (
    <>
      <button onClick={async () => { const r = await supprimer(id); if (r.error) setError(r.error); }}>Supprimer</button>
      {error && <p role="alert">{error}</p>}
    </>
  );
}
"""), F("app/articles/[id]/page.tsx", "tsx", r"""
import { db, getSession } from '@/lib/db';
import BoutonSupprimer from './BoutonSupprimer';

export default async function ArticlePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const session = await getSession();
  const commentaires = db.commentaires.filter((c) => c.articleId === id);
  return (
    <ul>
      {commentaires.map((c) => (
        <li key={c.id}>
          {c.auteur} : {c.texte}
          {session?.userId === c.userId && <BoutonSupprimer id={c.id} />}
        </li>
      ))}
    </ul>
  );
}
""")],
       ["Appeler l'action sur le commentaire de quelqu'un d'autre renvoie « Interdit »",
        "Le bouton n'apparaît que sur ses propres commentaires"],
       run=NRUN(r"""
await next.render('/articles/dto');
assert.equal($$('li button').length, 1, 'Un seul bouton : sur le commentaire d\'Ana (connectée)');
const { supprimer } = require('./app/articles/[id]/actions');
const { session, db } = require('./lib/db');
assert.equal((await supprimer(2)).error, 'Interdit', 'Supprimer le commentaire de Léo → « Interdit »');
assert.equal(db.commentaires.length, 2, 'Rien n\'a été supprimé');
assert.equal((await supprimer(99)).error, 'Introuvable', 'Id inconnu → « Introuvable »');
session.userId = null;
assert.equal((await supprimer(1)).error, 'Connecte-toi', 'Non connecté → « Connecte-toi »');
session.userId = 1;
await click($('li button'));
await waitFor(() => $$('li').length === 1, 3000);
assert.includes($('li').textContent, 'Léo', 'Après suppression, il reste le commentaire de Léo');
""", start="/articles/dto")),
    TD(3, "Créer puis rediriger",
       "Un formulaire de création d'article : validation dans l'action, erreurs affichées, et en cas de succès **redirection** vers la page du nouvel article. L'action doit suivre l'ordre : valider → droits → écrire → revalider → rediriger. " + SIM,
       ["`creerArticle(prev, formData)` : titre 5 à 120 caractères, contenu 20 caractères minimum ; erreurs dans `{ errors }`",
        "Non connecté → `{ errors: { titre: 'Connecte-toi' } }` (rien n'est créé)",
        "Succès : ajout dans `articles` (fourni), `revalidatePath('/articles')`, puis `redirect('/articles/' + id)`",
        "`/articles/[id]` affiche le titre dans un `<h1>` ; `/articles/nouveau` affiche le formulaire (client, `useActionState`)",
        "Le champ titre garde sa valeur après une erreur (`defaultValue` depuis l'état)"],
       [F("lib/data.ts", "ts", r"""
export const articles: { id: string; titre: string; contenu: string }[] = [];
export const session = { connecte: true };
"""), ROOT_LAYOUT, HOME,
        F("app/articles/actions.ts", "ts", r"""
'use server';
import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { articles, session } from '@/lib/data';

export type State = { errors?: { titre?: string; contenu?: string }; titre?: string };

// à toi : creerArticle(prev, formData)
"""), F("app/articles/nouveau/page.tsx", "tsx", r"""
import FormNouveau from './FormNouveau';

export default function Nouveau() {
  return <FormNouveau />;
}
"""), F("app/articles/nouveau/FormNouveau.tsx", "tsx", r"""
'use client';
import { useActionState } from 'react';
import { creerArticle, type State } from '../actions';

export default function FormNouveau() {
  // à toi
  return null;
}
"""), F("app/articles/[id]/page.tsx", "tsx", r"""
import { notFound } from 'next/navigation';
import { articles } from '@/lib/data';
// à toi
""")],
       ["`redirect()` se met en dernier : il interrompt la fonction et ne renvoie jamais.",
        "Renvoie aussi le titre saisi dans l'état d'erreur (`{ errors, titre }`) et utilise `defaultValue={state.titre}`.",
        "Id simple : `String(articles.length + 1)`."],
       [F("app/articles/actions.ts", "ts", r"""
'use server';
import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { articles, session } from '@/lib/data';

export type State = { errors?: { titre?: string; contenu?: string }; titre?: string };

export async function creerArticle(_prev: State, formData: FormData): Promise<State> {
  const titre = String(formData.get('titre') ?? '').trim();
  const contenu = String(formData.get('contenu') ?? '').trim();

  const errors: State['errors'] = {};
  if (titre.length < 5 || titre.length > 120) errors.titre = 'Entre 5 et 120 caractères';
  if (contenu.length < 20) errors.contenu = '20 caractères minimum';
  if (Object.keys(errors).length) return { errors, titre };
  if (!session.connecte) return { errors: { titre: 'Connecte-toi' }, titre };

  const id = String(articles.length + 1);
  articles.push({ id, titre, contenu });
  revalidatePath('/articles');
  redirect('/articles/' + id);
}
"""), F("app/articles/nouveau/FormNouveau.tsx", "tsx", r"""
'use client';
import { useActionState } from 'react';
import { creerArticle, type State } from '../actions';

export default function FormNouveau() {
  const [state, formAction, pending] = useActionState<State, FormData>(creerArticle, {});
  return (
    <form action={formAction}>
      <input name="titre" defaultValue={state.titre ?? ''} key={state.titre} />
      {state.errors?.titre && <p role="alert">{state.errors.titre}</p>}
      <textarea name="contenu" />
      {state.errors?.contenu && <p role="alert">{state.errors.contenu}</p>}
      <button disabled={pending}>Créer</button>
    </form>
  );
}
"""), F("app/articles/[id]/page.tsx", "tsx", r"""
import { notFound } from 'next/navigation';
import { articles } from '@/lib/data';

export default async function ArticlePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const a = articles.find((x) => x.id === id);
  if (!a) notFound();
  return <h1>{a.titre}</h1>;
}
""")],
       ["Après création, l'URL est celle du nouvel article",
        "Une erreur garde le titre saisi"],
       run=NRUN(r"""
await next.render('/articles/nouveau');
await type('input[name=titre]', 'Court');
await type('textarea[name=contenu]', 'trop court');
await submit('form');
await waitFor(() => $('[role=alert]'), 3000);
assert.includes($('[role=alert]').textContent, '20', 'Contenu trop court : erreur affichée');
assert.equal($('input[name=titre]').value, 'Court', 'Le titre saisi est conservé');
const { articles, session } = require('./lib/data');
assert.equal(articles.length, 0, 'Rien n\'a été créé');
session.connecte = false;
const { creerArticle } = require('./app/articles/actions');
const fd = new FormData(); fd.set('titre', 'Un bon titre'); fd.set('contenu', 'Un contenu suffisamment long ici.');
const r = await creerArticle({}, fd);
assert(r.errors && r.errors.titre === 'Connecte-toi' && articles.length === 0, 'Non connecté : « Connecte-toi », rien de créé');
session.connecte = true;
await type('input[name=titre]', 'Mon premier article');
await type('textarea[name=contenu]', 'Un contenu suffisamment long pour passer.');
await submit('form');
await waitFor(() => next.url === '/articles/1', 3000);
assert.equal(next.url, '/articles/1', 'Redirection vers /articles/1');
assert.equal($('h1').textContent, 'Mon premier article', 'La page du nouvel article est affichée');
assert(next.log.includes('revalidatePath /articles'), 'revalidatePath(\'/articles\') appelé');
""", start="/articles/nouveau")),
  ])

# ---------------------------------------------------------------- Route Handlers
NOTES = F("lib/notes.ts", "ts", r"""
// Stockage en mémoire (perdu au redémarrage : normal pour l'exercice)
export type Note = { id: string; titre: string; creeLe: string };
export const notes: Note[] = [];
""")

api = V2(v1["next-api"],
  prereq=[
    P("Endpoint", "Une URL + une méthode HTTP qui répond à des clients (application mobile, webhook, autre service) : `POST /api/notes`."),
    P("`Request` / `Response`", "Les objets standards du web : `request.json()` lit le corps, `new URL(request.url).searchParams` lit la query string ; `Response.json(data, { status })` répond."),
    P("Webhook", "Un service externe (paiement, GitHub…) qui appelle **ton** endpoint pour te prévenir d'un événement."),
    P("HMAC / signature", "Une empreinte calculée avec un secret partagé : elle prouve que la requête vient bien du service attendu et n'a pas été modifiée."),
    P("Idempotence", "Recevoir deux fois la même requête produit le même résultat qu'une seule fois (pas de double paiement si le webhook est renvoyé)."),
  ],
  diagram=D(
    nodes=[
      N("cli", 0, 1, "Client externe", "app mobile, webhook, curl", kind="actor", color="muted"),
      N("route", 1, 1, "app/api/notes/route.ts", "export GET, POST", kind="file", color="accent"),
      N("val", 2, 0, "Valider", "corps JSON", kind="pill", color="warn"),
      N("data", 2, 2, "Données", "lib/notes.ts", kind="db", color="muted"),
      N("res", 3, 1, "Response.json(...)", "201 · 400 · 404", kind="doc", color="good"),
    ],
    edges=[E("cli", "route", "HTTP"), E("route", "val"), E("route", "data"), E("val", "res"), E("data", "res"), E("res", "cli", "JSON", dashed=True, color="good", back=True)],
    caption="Un fichier route.ts exporte une fonction par méthode HTTP. Elle reçoit une Request standard et renvoie une Response."),
  lessons=[
    L("Quand faut-il une API dans Next ?", r"""
Pour **ton propre front Next**, tu n'as presque jamais besoin d'écrire une API : les Server Components lisent les données directement, et les Server Actions les écrivent.

Une vraie **URL d'API** devient nécessaire quand c'est **quelqu'un d'autre** qui appelle :

- une application mobile ou un autre front ;
- un **webhook** (Stripe te prévient qu'un paiement a réussi, GitHub qu'un commit a été poussé) ;
- un service partenaire, un script, `curl`.

Dans l'App Router, on les écrit avec des **Route Handlers** : un fichier `route.ts` dans `app/`.
"""),
    L("Écrire un Route Handler", r"""
Le dossier donne l'URL, et le fichier `route.ts` exporte **une fonction par méthode HTTP** :

```ts
// app/api/notes/route.ts  →  /api/notes
import { notes } from '@/lib/notes';

export async function GET(request: Request) {
  const q = new URL(request.url).searchParams.get('q');      // ?q=...
  return Response.json(q ? notes.filter((n) => n.titre.includes(q)) : notes);
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);       // JSON invalide → null
  if (!body || typeof body.titre !== 'string' || !body.titre.trim()) {
    return Response.json({ error: 'titre requis' }, { status: 400 });
  }
  const note = { id: crypto.randomUUID(), titre: body.titre.trim(), creeLe: new Date().toISOString() };
  notes.push(note);
  return Response.json(note, { status: 201 });
}
```

Pour une ressource précise, un segment dynamique, comme pour les pages :

```ts
// app/api/notes/[id]/route.ts  →  /api/notes/abc
export async function DELETE(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  ...
  return new Response(null, { status: 204 });
}
```

Un même dossier ne peut pas avoir à la fois `page.tsx` et `route.ts` : c'est soit une page, soit une API.
"""),
    L("Valider et répondre proprement", r"""
Un Route Handler est une porte d'entrée publique : on ne fait **jamais** confiance au corps reçu.

- `request.json()` lève une erreur si le corps n'est pas du JSON : `.catch(() => null)` puis 400.
- Vérifie le type et les bornes de chaque champ (`typeof`, longueur, valeurs permises). Des librairies comme **Zod** aident beaucoup sur un vrai projet.
- Renvoie des **statuts précis** et un format d'erreur stable :

| Statut | Quand |
|---|---|
| 200 | lecture réussie |
| 201 | création réussie (renvoie l'objet créé) |
| 204 | succès sans contenu (suppression) |
| 400 / 422 | corps invalide |
| 401 / 403 | pas authentifié / pas autorisé |
| 404 | ressource introuvable |
| 409 | conflit (doublon) |

Les en-têtes se lisent avec `request.headers.get('authorization')` : c'est là qu'on vérifie un token ou une signature.
"""),
    L("Un cas réel : recevoir un webhook", r"""
Un service de paiement appelle `POST /api/webhooks/paiement` à chaque paiement. Deux dangers :

1. **N'importe qui** peut appeler cette URL et prétendre qu'un paiement a réussi.
2. Le service peut **renvoyer** le même événement plusieurs fois (réseau instable).

Les réponses :

1. **Vérifier la signature.** Le service signe le corps avec un secret partagé (HMAC-SHA256) et l'envoie dans un en-tête. Tu recalcules la signature sur le **corps brut** (`await request.text()`, pas `json()`), et tu compares. Différent → 401.
2. **Être idempotent.** Chaque événement a un id : garde la liste des ids déjà traités, et réponds 200 sans rien refaire si l'id est déjà connu.

```ts
export async function POST(request: Request) {
  const brut = await request.text();
  const signature = request.headers.get('x-signature');
  if (signature !== (await hmacSha256Hex(SECRET, brut))) {
    return Response.json({ error: 'Signature invalide' }, { status: 401 });
  }
  const event = JSON.parse(brut);
  if (dejaTraites.has(event.id)) return Response.json({ ok: true, duplicate: true });
  dejaTraites.add(event.id);
  // ... traiter le paiement
  return Response.json({ ok: true });
}
```

Le calcul HMAC se fait avec `crypto.subtle` (disponible dans Node et dans les navigateurs), comme dans le TD de niveau 3.
"""),
  ],
  recap=[
    "Ton front Next n'a pas besoin d'API (Server Components + Server Actions) ; les Route Handlers servent aux clients **externes**.",
    "`app/.../route.ts` exporte `GET`, `POST`, `PATCH`, `DELETE`… qui reçoivent une `Request` et renvoient une `Response`.",
    "`request.json().catch(() => null)`, valider chaque champ, statuts précis (201, 204, 400, 404…).",
    "`[id]` dans le chemin → `await params` dans le 2e argument.",
    "Webhook : vérifier la **signature** sur le corps brut, et être **idempotent** (ids déjà traités).",
  ],
  example=[NOTES, F("app/api/notes/route.ts", "ts", r"""
import { notes } from '@/lib/notes';

export async function GET(request: Request) {
  const q = new URL(request.url).searchParams.get('q')?.toLowerCase();
  const result = q ? notes.filter((n) => n.titre.toLowerCase().includes(q)) : notes;
  return Response.json(result);
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const titre = typeof body?.titre === 'string' ? body.titre.trim() : '';
  if (titre.length < 1 || titre.length > 100) {
    return Response.json({ error: 'titre : 1 à 100 caractères' }, { status: 400 });
  }
  const note = { id: crypto.randomUUID(), titre, creeLe: new Date().toISOString() };
  notes.push(note);
  return Response.json(note, { status: 201 });
}
"""), F("app/api/notes/[id]/route.ts", "ts", r"""
import { notes } from '@/lib/notes';

type Ctx = { params: Promise<{ id: string }> };

export async function GET(_req: Request, { params }: Ctx) {
  const { id } = await params;
  const note = notes.find((n) => n.id === id);
  return note ? Response.json(note) : Response.json({ error: 'Introuvable' }, { status: 404 });
}

export async function DELETE(_req: Request, { params }: Ctx) {
  const { id } = await params;
  const i = notes.findIndex((n) => n.id === id);
  if (i === -1) return Response.json({ error: 'Introuvable' }, { status: 404 });
  notes.splice(i, 1);
  return new Response(null, { status: 204 });
}
"""), F("terminal", "bash", r"""
$ curl -X POST localhost:3000/api/notes -H 'Content-Type: application/json' -d '{"titre":"Courses"}'
{"id":"5f1c…","titre":"Courses","creeLe":"2026-11-12T10:00:00.000Z"}

$ curl 'localhost:3000/api/notes?q=cour'
[{"id":"5f1c…","titre":"Courses",…}]

$ curl -X POST localhost:3000/api/notes -d 'pas du json'
{"error":"titre : 1 à 100 caractères"}        # 400
""")],
  notes=["Le chemin du fichier donne l'URL ; le nom de la fonction exportée donne la méthode.",
         "`request.json().catch(() => null)` : un corps invalide devient `null`, puis 400.",
         "`[id]/route.ts` lit l'id dans `params`, comme une page dynamique.",
         "DELETE répond 204 avec `new Response(null, …)` : pas de corps."],
  td1=dict(path="app/api/notes/route.ts",
    title="API de notes",
    enonce="Écris une petite API de notes pour une application mobile. Les tests l'appellent comme le ferait `curl` : `next.request('POST', '/api/notes', { titre: '…' })`. " + SIM,
    consignes=["`GET /api/notes` avec filtre optionnel `?q=` sur le titre (insensible à la casse)",
               "`POST /api/notes` : titre de 1 à 100 caractères (après `trim`), sinon 400 ; corps non JSON → 400 ; succès → 201 avec la note",
               "`GET /api/notes/[id]` et `DELETE /api/notes/[id]` : 404 si absente ; DELETE → 204"],
    hints=["`const body = await request.json().catch(() => null);`",
           "`crypto.randomUUID()` pour l'id.",
           "Dans `[id]/route.ts` : `export async function DELETE(_req: Request, { params }: { params: Promise<{ id: string }> })`."],
    checks=["Un POST sans titre renvoie 400", "Un DELETE sur un id inconnu renvoie 404"],
    files=[NOTES, ROOT_LAYOUT, F("app/page.tsx", "tsx", "export default function Accueil() {\n  return <h1>API de notes</h1>;\n}\n"),
           F("app/api/notes/route.ts", "ts", r"""
import { notes } from '@/lib/notes';
// à toi : GET, POST
"""), F("app/api/notes/[id]/route.ts", "ts", r"""
import { notes } from '@/lib/notes';
// à toi : GET, DELETE
""")],
    solution=[F("app/api/notes/route.ts", "ts", r"""
import { notes } from '@/lib/notes';

export async function GET(request: Request) {
  const q = new URL(request.url).searchParams.get('q')?.toLowerCase();
  return Response.json(q ? notes.filter((n) => n.titre.toLowerCase().includes(q)) : notes);
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const titre = typeof body?.titre === 'string' ? body.titre.trim() : '';
  if (titre.length < 1 || titre.length > 100) {
    return Response.json({ error: 'titre : 1 à 100 caractères' }, { status: 400 });
  }
  const note = { id: crypto.randomUUID(), titre, creeLe: new Date().toISOString() };
  notes.push(note);
  return Response.json(note, { status: 201 });
}
"""), F("app/api/notes/[id]/route.ts", "ts", r"""
import { notes } from '@/lib/notes';

type Ctx = { params: Promise<{ id: string }> };

export async function GET(_req: Request, { params }: Ctx) {
  const { id } = await params;
  const note = notes.find((n) => n.id === id);
  return note ? Response.json(note) : Response.json({ error: 'Introuvable' }, { status: 404 });
}

export async function DELETE(_req: Request, { params }: Ctx) {
  const { id } = await params;
  const i = notes.findIndex((n) => n.id === id);
  if (i === -1) return Response.json({ error: 'Introuvable' }, { status: 404 });
  notes.splice(i, 1);
  return new Response(null, { status: 204 });
}
""")],
    run=NRUN(r"""
const a = await next.request('POST', '/api/notes', { titre: '  Courses  ' });
assert(a.status === 201 && a.json && a.json.titre === 'Courses' && a.json.id, 'POST valide → 201 avec titre nettoyé et id');
await next.request('POST', '/api/notes', { titre: 'Réviser Doctrine' });
assert.equal((await next.request('POST', '/api/notes', {})).status, 400, 'POST sans titre → 400');
assert.equal((await next.request('POST', '/api/notes', 'pas du json')).status, 400, 'Corps non JSON → 400');
assert.equal((await next.request('POST', '/api/notes', { titre: 'x'.repeat(101) })).status, 400, 'Titre de 101 caractères → 400');
const all = await next.request('GET', '/api/notes');
assert(all.status === 200 && all.json.length === 2, 'GET → 2 notes');
const f = await next.request('GET', '/api/notes?q=COUR');
assert(f.json.length === 1 && f.json[0].titre === 'Courses', '?q=COUR → seulement Courses');
assert.equal((await next.request('GET', '/api/notes/' + a.json.id)).json.titre, 'Courses', 'GET /api/notes/[id] → la note');
assert.equal((await next.request('DELETE', '/api/notes/' + a.json.id)).status, 204, 'DELETE → 204');
assert.equal((await next.request('GET', '/api/notes/' + a.json.id)).status, 404, 'Après suppression : 404');
assert.equal((await next.request('DELETE', '/api/notes/inconnu')).status, 404, 'DELETE id inconnu → 404');
""")),
  tds=[
    TD(2, "Protéger et paginer l'API",
       "L'API de notes est utilisée par une application mobile. Elle doit maintenant exiger un **token**, refuser les doublons, et paginer la liste. " + SIM,
       ["Toutes les routes exigent l'en-tête `Authorization: Bearer secret-mobile` ; sinon 401 `{ error: 'Non autorisé' }` (écris une fonction `autorise(request)` réutilisée partout)",
        "`POST` : un titre déjà existant (insensible à la casse) → 409 `{ error: 'Doublon' }`",
        "`GET ?page=&parPage=` (défauts 1 et 10, `parPage` max 50, sinon 400) → `{ items, total, page, pages }`",
        "`PATCH /api/notes/[id]` avec `{ titre }` : 404 si absente, 400 si titre invalide, 200 avec la note modifiée"],
       [NOTES, ROOT_LAYOUT, HOME,
        F("lib/auth.ts", "ts", r"""
// à toi : export function autorise(request: Request): boolean
"""), F("app/api/notes/route.ts", "ts", r"""
import { notes } from '@/lib/notes';
import { autorise } from '@/lib/auth';
// à toi
"""), F("app/api/notes/[id]/route.ts", "ts", r"""
import { notes } from '@/lib/notes';
import { autorise } from '@/lib/auth';
// à toi : PATCH
""")],
       ["`request.headers.get('authorization') === 'Bearer secret-mobile'`",
        "Pagination : `notes.slice((page - 1) * parPage, page * parPage)` et `pages = Math.max(1, Math.ceil(total / parPage))`.",
        "Lire un nombre : `Number(searchParams.get('page') ?? 1)` puis vérifier `Number.isInteger(...) && ... >= 1`."],
       [F("lib/auth.ts", "ts", r"""
export function autorise(request: Request): boolean {
  return request.headers.get('authorization') === 'Bearer secret-mobile';
}
"""), F("app/api/notes/route.ts", "ts", r"""
import { notes } from '@/lib/notes';
import { autorise } from '@/lib/auth';

const refus = () => Response.json({ error: 'Non autorisé' }, { status: 401 });

export async function GET(request: Request) {
  if (!autorise(request)) return refus();
  const sp = new URL(request.url).searchParams;
  const page = Number(sp.get('page') ?? 1);
  const parPage = Number(sp.get('parPage') ?? 10);
  if (!Number.isInteger(page) || page < 1 || !Number.isInteger(parPage) || parPage < 1 || parPage > 50) {
    return Response.json({ error: 'Pagination invalide' }, { status: 400 });
  }
  const total = notes.length;
  return Response.json({
    items: notes.slice((page - 1) * parPage, page * parPage),
    total,
    page,
    pages: Math.max(1, Math.ceil(total / parPage)),
  });
}

export async function POST(request: Request) {
  if (!autorise(request)) return refus();
  const body = await request.json().catch(() => null);
  const titre = typeof body?.titre === 'string' ? body.titre.trim() : '';
  if (titre.length < 1 || titre.length > 100) return Response.json({ error: 'titre : 1 à 100 caractères' }, { status: 400 });
  if (notes.some((n) => n.titre.toLowerCase() === titre.toLowerCase())) return Response.json({ error: 'Doublon' }, { status: 409 });
  const note = { id: crypto.randomUUID(), titre, creeLe: new Date().toISOString() };
  notes.push(note);
  return Response.json(note, { status: 201 });
}
"""), F("app/api/notes/[id]/route.ts", "ts", r"""
import { notes } from '@/lib/notes';
import { autorise } from '@/lib/auth';

export async function PATCH(request: Request, { params }: { params: Promise<{ id: string }> }) {
  if (!autorise(request)) return Response.json({ error: 'Non autorisé' }, { status: 401 });
  const { id } = await params;
  const note = notes.find((n) => n.id === id);
  if (!note) return Response.json({ error: 'Introuvable' }, { status: 404 });
  const body = await request.json().catch(() => null);
  const titre = typeof body?.titre === 'string' ? body.titre.trim() : '';
  if (titre.length < 1 || titre.length > 100) return Response.json({ error: 'titre : 1 à 100 caractères' }, { status: 400 });
  note.titre = titre;
  return Response.json(note);
}
""")],
       ["Sans token : 401 partout",
        "La pagination renvoie le bon nombre de pages"],
       run=NRUN(r"""
const H = { Authorization: 'Bearer secret-mobile' };
assert.equal((await next.request('GET', '/api/notes')).status, 401, 'Sans token → 401');
assert.equal((await next.request('POST', '/api/notes', { titre: 'x' }, { Authorization: 'Bearer faux' })).status, 401, 'Mauvais token → 401');
for (let i = 1; i <= 12; i++) await next.request('POST', '/api/notes', { titre: 'Note ' + i }, H);
assert.equal((await next.request('POST', '/api/notes', { titre: 'note 3' }, H)).status, 409, 'Doublon (casse ignorée) → 409');
const p1 = await next.request('GET', '/api/notes', undefined, H);
assert(p1.json.items.length === 10 && p1.json.total === 12 && p1.json.pages === 2, 'Défauts : 10 par page, total 12, 2 pages');
const p2 = await next.request('GET', '/api/notes?page=2&parPage=5', undefined, H);
assert(p2.json.items.length === 5 && p2.json.items[0].titre === 'Note 6' && p2.json.pages === 3, 'page=2&parPage=5 : Note 6 à 10, 3 pages');
assert.equal((await next.request('GET', '/api/notes?parPage=500', undefined, H)).status, 400, 'parPage=500 → 400');
const id = p1.json.items[0].id;
const up = await next.request('PATCH', '/api/notes/' + id, { titre: 'Modifiée' }, H);
assert(up.status === 200 && up.json.titre === 'Modifiée', 'PATCH → 200 avec le nouveau titre');
assert.equal((await next.request('PATCH', '/api/notes/inconnu', { titre: 'x' }, H)).status, 404, 'PATCH id inconnu → 404');
assert.equal((await next.request('PATCH', '/api/notes/' + id, { titre: '' }, H)).status, 400, 'PATCH titre vide → 400');
assert(/autorise\(/.test(source('app/api/notes/[id]/route.ts')), 'La même fonction autorise() est réutilisée');
""")),
    TD(3, "Recevoir un webhook signé",
       "Un service de paiement appelle `POST /api/webhooks/paiement` à chaque paiement réussi. Tu dois vérifier la **signature HMAC-SHA256** du corps brut, ignorer les événements **déjà traités**, et marquer la commande payée. " + SIM,
       ["Lis le corps **brut** avec `await request.text()` (la signature porte sur le texte exact)",
        "Calcule `HMAC-SHA256(SECRET, corps)` en hexadécimal avec `crypto.subtle` (fonction `signer` dans `lib/hmac.ts`) ; si différent de l'en-tête `x-signature` → 401",
        "Corps : `{ id, type: 'paiement.reussi', commandeId }` ; type inconnu → 200 `{ ignore: true }`",
        "Événement déjà traité (même `id`) → 200 `{ duplicate: true }` sans rien refaire",
        "Sinon : `commandes[commandeId].payee = true` → 200 `{ ok: true }` ; commande inconnue → 404"],
       [F("lib/commandes.ts", "ts", r"""
export const SECRET = 'whsec_atelier';
export const commandes: Record<string, { payee: boolean; paiements: number }> = {
  c1: { payee: false, paiements: 0 },
  c2: { payee: false, paiements: 0 },
};
export const evenementsTraites = new Set<string>();
"""), F("lib/hmac.ts", "ts", r"""
// à toi : export async function signer(secret: string, message: string): Promise<string>  (hexadécimal)
"""), ROOT_LAYOUT, F("app/page.tsx", "tsx", "export default function Accueil() {\n  return <h1>Webhooks</h1>;\n}\n"),
        F("app/api/webhooks/paiement/route.ts", "ts", r"""
import { SECRET, commandes, evenementsTraites } from '@/lib/commandes';
import { signer } from '@/lib/hmac';
// à toi : POST
""")],
       ["`const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);`",
        "`const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(message));` puis `[...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, '0')).join('')`.",
        "Marque l'événement comme traité seulement **après** avoir vérifié la signature."],
       [F("lib/hmac.ts", "ts", r"""
export async function signer(secret: string, message: string): Promise<string> {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(message));
  return [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, '0')).join('');
}
"""), F("app/api/webhooks/paiement/route.ts", "ts", r"""
import { SECRET, commandes, evenementsTraites } from '@/lib/commandes';
import { signer } from '@/lib/hmac';

export async function POST(request: Request) {
  const brut = await request.text();
  const signature = request.headers.get('x-signature');
  if (!signature || signature !== (await signer(SECRET, brut))) {
    return Response.json({ error: 'Signature invalide' }, { status: 401 });
  }

  const event = JSON.parse(brut) as { id: string; type: string; commandeId: string };
  if (event.type !== 'paiement.reussi') return Response.json({ ignore: true });
  if (evenementsTraites.has(event.id)) return Response.json({ duplicate: true });

  const commande = commandes[event.commandeId];
  if (!commande) return Response.json({ error: 'Commande inconnue' }, { status: 404 });

  evenementsTraites.add(event.id);
  commande.payee = true;
  commande.paiements++;
  return Response.json({ ok: true });
}
""")],
       ["Une signature fausse renvoie 401",
        "Le même événement envoyé deux fois ne compte qu'un paiement"],
       run=NRUN(r"""
const { signer } = require('./lib/hmac');
const { commandes } = require('./lib/commandes');
const s = await signer('key', 'The quick brown fox jumps over the lazy dog');
assert.equal(s, 'f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8', 'signer() calcule le bon HMAC-SHA256 (valeur de référence)');
const envoyer = async (ev, sig) => { const b = JSON.stringify(ev); return next.request('POST', '/api/webhooks/paiement', b, { 'x-signature': sig ?? (await signer('whsec_atelier', b)) }); };
const ev = { id: 'evt_1', type: 'paiement.reussi', commandeId: 'c1' };
assert.equal((await envoyer(ev, 'fausse')).status, 401, 'Signature fausse → 401');
assert.equal(commandes.c1.payee, false, 'Rien n\'est payé après une fausse signature');
const r1 = await envoyer(ev);
assert(r1.status === 200 && r1.json.ok === true, 'Signature valide → 200 { ok: true }');
assert.equal(commandes.c1.payee, true, 'La commande c1 est payée');
const r2 = await envoyer(ev);
assert(r2.status === 200 && r2.json.duplicate === true, 'Même événement renvoyé → { duplicate: true }');
assert.equal(commandes.c1.paiements, 1, 'Un seul paiement compté');
assert.equal((await envoyer({ id: 'evt_2', type: 'remboursement', commandeId: 'c2' })).json.ignore, true, 'Type inconnu → { ignore: true }');
assert.equal((await envoyer({ id: 'evt_3', type: 'paiement.reussi', commandeId: 'zz' })).status, 404, 'Commande inconnue → 404');
const b = JSON.stringify({ id: 'evt_4', type: 'paiement.reussi', commandeId: 'c2' });
const sig = await signer('whsec_atelier', b);
assert.equal((await next.request('POST', '/api/webhooks/paiement', b.replace('c2', 'c1'), { 'x-signature': sig })).status, 401, 'Corps modifié après signature → 401');
""")),
  ])

MODULES = [routing, sc, data, actions, api]

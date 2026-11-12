from common_v1 import M, Q, TD, code

T = "next"

MODULES = [
M("next-routing", T, "App Router : dossiers = routes", 15,
  "Savoir quelle URL produit quel fichier, et à quoi servent layout, loading et error.",
  "Next.js remplace la configuration des routes par une convention de dossiers : sans la connaître, on ne s'y retrouve pas.",
  ["Chaque **dossier** de `app/` = un segment d'URL",
   "`page.tsx` rend ce segment **accessible**",
   "`layout.tsx` **enveloppe** les pages du dossier et de ses sous-dossiers",
   "`[slug]` = segment **dynamique**, reçu dans `params`"],
  ["`app/blog/page.tsx` → `/blog` ; `app/blog/[slug]/page.tsx` → `/blog/mon-article`.",
   "Un layout **reste monté** quand on navigue entre ses pages enfants.",
   "Fichiers spéciaux : `loading.tsx` (pendant le chargement), `error.tsx` (en cas d'erreur, composant client), `not-found.tsx`.",
   "`(groupe)` : un dossier entre parenthèses organise sans changer l'URL.",
   "Depuis Next 15, `params` est une **Promise** : `const { slug } = await params`.",
   "Navigation interne : `<Link href=\"/blog\">` (préchargement, pas de rechargement complet)."],
  ["Un dossier sans `page.tsx` n'est pas une route.",
   "`<a>` pour la navigation interne : rechargement complet de l'app."],
  code("tsx", r"""
// Arborescence
// app/
// ├── layout.tsx          -> enveloppe tout le site
// ├── page.tsx            -> /
// └── blog/
//     ├── layout.tsx      -> enveloppe /blog et /blog/*
//     ├── page.tsx        -> /blog
//     ├── loading.tsx     -> affiché pendant le chargement
//     └── [slug]/
//         ├── page.tsx    -> /blog/n-importe-quoi
//         └── not-found.tsx

// app/blog/[slug]/page.tsx
import { notFound } from 'next/navigation';
import { getPost } from '@/lib/posts';

export default async function PostPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = await getPost(slug);
  if (!post) notFound();

  return (
    <article>
      <h1>{post.title}</h1>
      <p>{post.body}</p>
    </article>
  );
}
"""),
  ["La page est `async` : elle attend ses données côté serveur.",
   "`notFound()` affiche le `not-found.tsx` le plus proche.",
   "`@/` est un alias vers la racine du projet (configuré dans tsconfig)."],
  [Q("Quel fichier crée la route `/compte/parametres` ?",
     ["app/compte/parametres.tsx", "app/compte/parametres/page.tsx", "pages/compte.tsx", "app/(compte)/page.tsx"], 1,
     "Un dossier par segment, et un `page.tsx` pour le rendre accessible."),
   Q("`app/(marketing)/a-propos/page.tsx` donne quelle URL ?",
     ["/marketing/a-propos", "/a-propos", "Aucune", "Une erreur"], 1,
     "Les parenthèses n'apparaissent pas dans l'URL."),
   Q("De /blog/a vers /blog/b, `app/blog/layout.tsx`…",
     ["est re-monté", "reste monté, seule la page change", "est supprimé", "recharge la page"], 1,
     "C'est pour ça qu'un layout est idéal pour une navigation ou une sidebar.")],
  TD("Structure d'une boutique",
     "Crée l'arborescence d'une petite boutique.",
     ["`/` accueil, `/produits` liste, `/produits/[id]` détail",
      "Un layout commun avec une barre de navigation (`<Link>`)",
      "`/produits/[id]` appelle `notFound()` si le produit n'existe pas",
      "Un `loading.tsx` pour `/produits`",
      "Groupe `(compte)` avec `/connexion` et `/inscription` qui partagent un layout centré"],
     code("plaintext", r"""
app/
├── layout.tsx
├── page.tsx
└── ...  (à toi)
"""),
     ["Le layout centré va dans `app/(compte)/layout.tsx`.",
      "Données de test : un tableau `produits` dans `lib/produits.ts` avec une fonction `getProduit(id)`."],
     code("tsx", r"""
// app/
// ├── layout.tsx                 nav avec <Link>
// ├── page.tsx                   /
// ├── produits/
// │   ├── page.tsx               /produits
// │   ├── loading.tsx
// │   └── [id]/page.tsx          /produits/:id
// └── (compte)/
//     ├── layout.tsx             layout centré
//     ├── connexion/page.tsx     /connexion
//     └── inscription/page.tsx   /inscription

// app/layout.tsx
import Link from 'next/link';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>
        <nav>
          <Link href="/">Accueil</Link> <Link href="/produits">Produits</Link>{' '}
          <Link href="/connexion">Connexion</Link>
        </nav>
        {children}
      </body>
    </html>
  );
}

// app/produits/[id]/page.tsx
import { notFound } from 'next/navigation';
import { getProduit } from '@/lib/produits';

export default async function ProduitPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const produit = await getProduit(id);
  if (!produit) notFound();
  return <h1>{produit.nom}</h1>;
}

// app/(compte)/layout.tsx
export default function CompteLayout({ children }: { children: React.ReactNode }) {
  return <div style={{ maxWidth: 400, margin: '4rem auto' }}>{children}</div>;
}
"""),
     ["`/produits/inexistant` affiche la page 404",
      "L'URL `/connexion` ne contient pas « compte »"])),

M("next-server-client", T, "Server & Client Components", 15,
  "Savoir où s'exécute chaque composant et où placer `'use client'`.",
  "Par défaut, tout est rendu côté serveur : rapide et sûr, mais `useState` et `onClick` n'y fonctionnent pas.",
  ["Par défaut, un composant est un **Server Component** : exécuté sur le serveur, aucun JS envoyé",
   "`'use client'` en haut d'un fichier crée une **frontière** : ce fichier et ce qu'il importe partent au navigateur",
   "Les props qui traversent la frontière doivent être **sérialisables**",
   "Un Server Component peut **contenir** des Client Components"],
  ["Serveur : accès direct à la base et aux secrets, `async/await` dans le composant.",
   "Client : state, effets, événements, APIs du navigateur.",
   "Place `'use client'` **le plus bas possible** : sur le bouton, pas sur toute la page.",
   "Props vers un Client Component : données simples (pas de fonctions, sauf les Server Actions).",
   "`children` permet de mettre du contenu serveur **à l'intérieur** d'un composant client."],
  ["`'use client'` dans le layout racine : tout le site devient client.",
   "Importer un module qui contient des secrets dans un fichier client."],
  code("tsx", r"""
// app/produits/page.tsx  (Server Component)
import { db } from '@/lib/db';
import AddToCart from './AddToCart';

export default async function ProduitsPage() {
  const produits = await db.produit.findMany();   // directement en base

  return (
    <ul>
      {produits.map((p) => (
        <li key={p.id}>
          {p.nom} – {p.prix} €
          <AddToCart produitId={p.id} />
        </li>
      ))}
    </ul>
  );
}

// app/produits/AddToCart.tsx  (Client Component)
'use client';
import { useState } from 'react';

export default function AddToCart({ produitId }: { produitId: string }) {
  const [ajoute, setAjoute] = useState(false);
  return (
    <button onClick={() => setAjoute(true)} disabled={ajoute}>
      {ajoute ? 'Ajouté' : 'Ajouter'}
    </button>
  );
}
"""),
  ["La liste et l'accès à la base restent sur le serveur.",
   "Seul le petit bouton est envoyé au navigateur.",
   "`produitId` est une chaîne : sérialisable, donc il traverse la frontière."],
  [Q("Un composant sans `'use client'` peut-il utiliser `useState` ?",
     ["Oui", "Non, c'est un Server Component", "Oui en dev", "Seulement s'il est async"], 1,
     "Le state n'existe que dans le navigateur."),
   Q("Où placer `'use client'` idéalement ?",
     ["Dans le layout racine", "Sur le plus petit composant qui a besoin d'interactivité", "Dans chaque fichier", "Dans next.config"], 1,
     "Moins de code client = page plus légère."),
   Q("Peut-on passer une fonction `onSelect` d'un Server Component à un Client Component ?",
     ["Oui", "Non, une fonction n'est pas sérialisable (sauf Server Action)", "Oui avec JSON.stringify", "Seulement en async"], 1,
     "Le serveur envoie des données au navigateur, pas du code arbitraire.")],
  TD("Page article interactive",
     "Construis une page article où seuls les morceaux interactifs sont côté client.",
     ["`app/articles/[id]/page.tsx` (serveur) charge l'article et ses commentaires",
      "`LikeButton` (client) avec un compteur local",
      "`Commentaires` repliable (client) qui reçoit la liste chargée côté serveur",
      "Aucun `'use client'` dans `page.tsx`"],
     code("tsx", r"""
// app/articles/[id]/page.tsx
import { getArticle, getCommentaires } from '@/lib/articles';

export default async function ArticlePage({ params }: { params: Promise<{ id: string }> }) {
  // à toi
}
"""),
     ["`LikeButton` et `Commentaires` vont dans deux fichiers avec `'use client'` en première ligne.",
      "Passe les commentaires en prop : `<Commentaires items={commentaires} />` (tableau d'objets simples)."],
     code("tsx", r"""
// app/articles/[id]/page.tsx  (serveur)
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

// app/articles/[id]/LikeButton.tsx
'use client';
import { useState } from 'react';

export default function LikeButton({ initial }: { initial: number }) {
  const [likes, setLikes] = useState(initial);
  return <button onClick={() => setLikes((l) => l + 1)}>{likes} j'aime</button>;
}

// app/articles/[id]/Commentaires.tsx
'use client';
import { useState } from 'react';

type Commentaire = { id: string; auteur: string; texte: string };

export default function Commentaires({ items }: { items: Commentaire[] }) {
  const [ouvert, setOuvert] = useState(false);
  return (
    <section>
      <button onClick={() => setOuvert((o) => !o)}>
        {ouvert ? 'Masquer' : `Voir les ${items.length} commentaires`}
      </button>
      {ouvert && <ul>{items.map((c) => <li key={c.id}><b>{c.auteur}</b> : {c.texte}</li>)}</ul>}
    </section>
  );
}
"""),
     ["`page.tsx` n'a pas `'use client'`",
      "Les deux requêtes partent en parallèle"])),

M("next-data", T, "Données & cache", 15,
  "Charger les données côté serveur et choisir entre statique, revalidé et dynamique.",
  "Mal réglé, le cache affiche des données périmées, ou au contraire recalcule tout à chaque visite.",
  ["Le Server Component **attend** ses données (`await`)",
   "Next décide si la page est **statique** (générée une fois) ou **dynamique** (à chaque requête)",
   "`revalidate` = statique, **regénérée** au plus toutes les N secondes",
   "`revalidatePath` / `revalidateTag` **invalident** à la demande après une écriture"],
  ["Lire les cookies, les headers ou `searchParams` rend la page dynamique.",
   "`fetch(url, { next: { revalidate: 60 } })` ou `export const revalidate = 60` dans la page.",
   "Depuis Next 15, `fetch` n'est **plus mis en cache par défaut**. Next 16 ajoute la directive `'use cache'` (Cache Components) : vérifie la doc de ta version.",
   "Lance les requêtes indépendantes **en parallèle** avec `Promise.all`.",
   "`<Suspense>` affiche la page tout de suite et diffuse la partie lente quand elle est prête."],
  ["Enchaîner des `await` indépendants : les temps s'additionnent.",
   "Appeler sa propre route `/api` depuis un Server Component : appelle directement la fonction."],
  code("tsx", r"""
// app/dashboard/page.tsx
import { Suspense } from 'react';
import { getUser } from '@/lib/auth';
import DernieresCommandes from './DernieresCommandes';

export const revalidate = 60; // page regénérée au plus toutes les 60 s

async function getStats() {
  const res = await fetch('https://api.exemple.com/stats', { next: { revalidate: 60 } });
  if (!res.ok) throw new Error('Stats indisponibles');
  return res.json();
}

export default async function Dashboard() {
  const [stats, user] = await Promise.all([getStats(), getUser()]); // en parallèle

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
"""),
  ["`Promise.all` : le temps total = la requête la plus lente, pas la somme.",
   "`DernieresCommandes` est un composant async : il arrive quand il est prêt.",
   "Si `getStats` lève une erreur, le `error.tsx` le plus proche s'affiche."],
  [Q("Depuis Next 15, `fetch(url)` sans option dans un Server Component est…",
     ["mis en cache pour toujours", "non mis en cache par défaut", "interdit", "mis en cache 60 s"], 1,
     "Il faut maintenant demander le cache explicitement."),
   Q("Deux requêtes indépendantes de 1 s chacune. Avec deux `await` à la suite, la page attend…",
     ["1 s", "2 s", "0,5 s", "Ça dépend du cache"], 1,
     "Avec `Promise.all`, ce serait 1 s."),
   Q("Après avoir ajouté un article via une Server Action, comment rafraîchir `/blog` ?",
     ["Recharger le serveur", "`revalidatePath('/blog')`", "Vider le navigateur", "`router.refresh()` côté serveur"], 1,
     "Ça invalide le cache de cette route.")],
  TD("Blog avec cache",
     "Règle le chargement et le cache d'un blog.",
     ["`/blog` : liste revalidée toutes les 5 minutes",
      "`/blog/[slug]` : `generateStaticParams` pré-génère les 20 derniers articles",
      "Article et commentaires chargés **en parallèle**… sauf si tu mets les commentaires dans un `<Suspense>` (choisis et explique)",
      "Les commentaires s'affichent après l'article, sans bloquer la page"],
     code("tsx", r"""
// app/blog/page.tsx
import { getPosts } from '@/lib/posts';

export default async function BlogPage() {
  // à toi
}

// app/blog/[slug]/page.tsx
// à toi
"""),
     ["`export const revalidate = 300;` dans `app/blog/page.tsx`.",
      "`export async function generateStaticParams() { return (await getPosts(20)).map(p => ({ slug: p.slug })); }`",
      "Un composant async `Commentaires` dans un `<Suspense>` laisse l'article s'afficher d'abord."],
     code("tsx", r"""
// app/blog/page.tsx
import Link from 'next/link';
import { getPosts } from '@/lib/posts';

export const revalidate = 300; // 5 minutes

export default async function BlogPage() {
  const posts = await getPosts();
  return (
    <ul>
      {posts.map((p) => <li key={p.slug}><Link href={`/blog/${p.slug}`}>{p.title}</Link></li>)}
    </ul>
  );
}

// app/blog/[slug]/page.tsx
import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import { getPost, getPosts, getComments } from '@/lib/posts';

export async function generateStaticParams() {
  const posts = await getPosts(20);
  return posts.map((p) => ({ slug: p.slug }));
}

async function Commentaires({ slug }: { slug: string }) {
  const comments = await getComments(slug);
  return <ul>{comments.map((c) => <li key={c.id}>{c.text}</li>)}</ul>;
}

export default async function PostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await getPost(slug);
  if (!post) notFound();

  // Choix : Suspense plutôt que Promise.all.
  // L'article s'affiche dès qu'il est prêt ; les commentaires arrivent ensuite.
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
"""),
     ["Tu sais dire quand `/blog` sera recalculée",
      "Un commentaire lent ne bloque pas l'affichage de l'article"])),

M("next-actions", T, "Server Actions & formulaires", 15,
  "Modifier des données depuis un formulaire sans écrire d'API.",
  "Avant, il fallait une route API, un fetch côté client et la gestion des états. Une Server Action est une fonction serveur que le formulaire appelle directement.",
  ["Une fonction `async` marquée **`'use server'`**",
   "est passée à `<form action={…}>`",
   "À l'envoi, Next **l'exécute sur le serveur** avec le `FormData`",
   "Elle écrit en base puis appelle **`revalidatePath`** pour rafraîchir l'affichage"],
  ["Ça fonctionne même avant que le JavaScript soit chargé.",
   "**Valide toujours** les données dans l'action (par exemple avec Zod) : c'est un point d'entrée public.",
   "Vérifie aussi l'**authentification** dans l'action.",
   "`useActionState` (React 19) récupère erreurs et état ; il donne aussi `pending` pour le bouton.",
   "`redirect('/…')` après une création réussie."],
  ["Faire confiance aux champs cachés (`userId` dans un `<input type=\"hidden\">`).",
   "Oublier `revalidatePath` : la liste n'affiche pas le nouvel élément."],
  code("tsx", r"""
// app/todos/actions.ts
'use server';
import { revalidatePath } from 'next/cache';
import { db } from '@/lib/db';

export type State = { error?: string };

export async function addTodo(_prev: State, formData: FormData): Promise<State> {
  const title = String(formData.get('title') ?? '').trim();
  if (title.length < 3) return { error: '3 caractères minimum' };

  await db.todo.create({ data: { title } });
  revalidatePath('/todos');
  return {};
}

// app/todos/TodoForm.tsx
'use client';
import { useActionState } from 'react';
import { addTodo } from './actions';

export default function TodoForm() {
  const [state, formAction, pending] = useActionState(addTodo, {});
  return (
    <form action={formAction}>
      <input name="title" required />
      <button disabled={pending}>{pending ? 'Ajout…' : 'Ajouter'}</button>
      {state.error && <p role="alert">{state.error}</p>}
    </form>
  );
}
"""),
  ["`name=\"title\"` : c'est la clé lue avec `formData.get('title')`.",
   "L'action renvoie un état (erreur ou rien) que le formulaire affiche.",
   "`revalidatePath('/todos')` : la liste (Server Component) se recharge."],
  [Q("Où s'exécute une fonction marquée `'use server'` ?",
     ["Dans le navigateur", "Sur le serveur", "Les deux", "Dans un worker"], 1,
     "Le navigateur envoie juste une requête ; le code reste sur le serveur."),
   Q("Faut-il valider les données dans une Server Action si le champ a `required` ?",
     ["Non", "Oui, toujours : n'importe qui peut appeler l'action", "Seulement en production", "Seulement avec TypeScript"], 1,
     "`required` est une aide côté navigateur, pas une sécurité."),
   Q("Après l'ajout, la liste ne montre pas le nouvel élément. Il manque probablement…",
     ["`'use client'`", "`revalidatePath`", "`useEffect`", "`preventDefault`"], 1,
     "Sans invalidation, la page garde sa version en cache.")],
  TD("Commentaires d'article",
     "Ajoute un formulaire de commentaire à une page article.",
     ["Action `addComment(articleId, prevState, formData)` : auteur (2–50 caractères) et texte (5–500)",
      "Erreurs par champ renvoyées au formulaire",
      "`revalidatePath` de la page de l'article",
      "Le bouton affiche « Envoi… » pendant l'envoi",
      "L'`articleId` ne vient **pas** d'un champ caché : utilise `.bind`"],
     code("tsx", r"""
// app/articles/[id]/actions.ts
'use server';

export async function addComment(/* à toi */) {}

// app/articles/[id]/CommentForm.tsx
'use client';

export default function CommentForm({ articleId }: { articleId: string }) {
  // à toi
}
"""),
     ["`const action = addComment.bind(null, articleId);` lie l'id côté serveur.",
      "État : `{ errors?: { auteur?: string; texte?: string } }`",
      "`useActionState(action, {})`"],
     code("tsx", r"""
// app/articles/[id]/actions.ts
'use server';
import { revalidatePath } from 'next/cache';
import { db } from '@/lib/db';

export type CommentState = { errors?: { auteur?: string; texte?: string } };

export async function addComment(
  articleId: string,
  _prev: CommentState,
  formData: FormData,
): Promise<CommentState> {
  const auteur = String(formData.get('auteur') ?? '').trim();
  const texte = String(formData.get('texte') ?? '').trim();

  const errors: CommentState['errors'] = {};
  if (auteur.length < 2 || auteur.length > 50) errors.auteur = 'Entre 2 et 50 caractères';
  if (texte.length < 5 || texte.length > 500) errors.texte = 'Entre 5 et 500 caractères';
  if (Object.keys(errors).length > 0) return { errors };

  await db.comment.create({ data: { articleId, auteur, texte } });
  revalidatePath(`/articles/${articleId}`);
  return {};
}

// app/articles/[id]/CommentForm.tsx
'use client';
import { useActionState } from 'react';
import { addComment, CommentState } from './actions';

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
"""),
     ["Un texte de 3 caractères affiche une erreur sous le champ",
      "Le nouveau commentaire apparaît sans recharger la page"])),

M("next-api", T, "Route Handlers (API)", 12,
  "Créer des endpoints HTTP dans l'App Router.",
  "Pour un webhook, une app mobile ou un service externe, il faut une vraie URL d'API : c'est le rôle des Route Handlers.",
  ["Un fichier **`route.ts`** dans un dossier de `app/`",
   "exporte une fonction par **méthode HTTP** (`GET`, `POST`…)",
   "qui reçoit la **Request** (et les `params`)",
   "et renvoie une **Response** (`Response.json(...)`)"],
  ["`app/api/todos/route.ts` → `/api/todos`. Pas de `page.tsx` dans le même dossier.",
   "Objets web standard : `request.json()`, `new URL(request.url).searchParams`.",
   "Codes HTTP explicites : 201 créé, 204 sans contenu, 400 entrée invalide, 404 introuvable.",
   "Pour ton propre front Next, préfère les **Server Actions** ; les Route Handlers servent aux clients externes."],
  ["Ne pas valider le corps de la requête.",
   "Créer une route API juste pour l'appeler depuis un Server Component."],
  code("tsx", r"""
// app/api/todos/route.ts
import { db } from '@/lib/db';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const done = searchParams.get('done');
  const todos = await db.todo.findMany({
    where: done === null ? {} : { done: done === 'true' },
  });
  return Response.json(todos);
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (!body || typeof body.title !== 'string' || body.title.trim() === '') {
    return Response.json({ error: 'title requis' }, { status: 400 });
  }
  const todo = await db.todo.create({ data: { title: body.title.trim() } });
  return Response.json(todo, { status: 201 });
}

// app/api/todos/[id]/route.ts
export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  await db.todo.delete({ where: { id } });
  return new Response(null, { status: 204 });
}
"""),
  ["Un JSON invalide est rattrapé par `.catch(() => null)` → 400.",
   "Le `[id]` dynamique fonctionne comme pour les pages.",
   "204 : succès sans corps de réponse."],
  [Q("Quel fichier répond à `POST /api/contact` ?",
     ["app/api/contact/page.tsx", "app/api/contact/route.ts avec `export async function POST`", "pages/api/contact.ts uniquement", "app/contact/route.ts"], 1,
     "Le dossier donne l'URL, le nom de la fonction exportée donne la méthode."),
   Q("Corps de requête invalide : quel code renvoyer ?",
     ["200", "400", "404", "500"], 1,
     "400 = l'erreur vient du client."),
   Q("Ton propre formulaire Next doit créer un élément. Que préférer ?",
     ["Un Route Handler + fetch", "Une Server Action", "Un useEffect", "Un middleware"], 1,
     "Moins de code, et la revalidation est intégrée.")],
  TD("API de notes",
     "Écris une petite API de notes, stockée en mémoire pour l'exercice.",
     ["`GET /api/notes` avec filtre optionnel `?q=` sur le titre",
      "`POST /api/notes` : titre de 1 à 100 caractères, sinon 400",
      "`GET /api/notes/[id]` et `DELETE /api/notes/[id]` avec 404 si absente",
      "Teste avec `curl`"],
     code("tsx", r"""
// lib/notes.ts
export type Note = { id: string; titre: string; creeLe: string };
export const notes: Note[] = [];

// app/api/notes/route.ts
// à toi

// app/api/notes/[id]/route.ts
// à toi

// Tests :
// curl -X POST localhost:3000/api/notes -H 'Content-Type: application/json' -d '{"titre":"Courses"}'
// curl 'localhost:3000/api/notes?q=cour'
"""),
     ["`crypto.randomUUID()` pour l'id.",
      "Suppression : `const i = notes.findIndex(n => n.id === id); if (i === -1) return 404; notes.splice(i, 1);`",
      "Le stockage en mémoire est perdu au redémarrage : c'est normal pour l'exercice."],
     code("tsx", r"""
// app/api/notes/route.ts
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

// app/api/notes/[id]/route.ts
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
"""),
     ["Un POST sans titre renvoie 400",
      "Un DELETE sur un id inconnu renvoie 404"])),
]

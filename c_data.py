from common_v1 import M, Q, TD, code

T = "data"

MODULES = [
M("data-http", T, "Une requête HTTP, de A à Z", 12,
  "Comprendre ce qui se passe vraiment quand le front « récupère » ou « envoie » des données.",
  "Fetch, axios, mutations… ça paraît compliqué parce qu'on voit le code avant le mécanisme. Or tout repose sur une seule idée : le navigateur pose une question au serveur, le serveur répond. Comme au restaurant : tu passes commande (requête), la cuisine prépare, le serveur t'apporte le plat ou te dit « plus de dessert » (réponse).",
  ["Le front **envoie une requête** : une méthode (GET, POST…), une URL, parfois un corps JSON",
   "Le serveur (Symfony, Next…) **traite** : lit la base, valide, enregistre",
   "Il renvoie une **réponse** : un code de statut (200, 404…) + un corps JSON",
   "Le front **attend** cette réponse (c'est asynchrone), puis met l'écran à jour"],
  ["**GET** = lire (pas de corps). **POST** = créer. **PUT/PATCH** = modifier. **DELETE** = supprimer. Ces envois qui modifient des données s'appellent des **mutations**.",
   "Codes : 2xx = ça a marché (200 OK, 201 créé, 204 sans contenu) ; 4xx = le client s'est trompé (400, 401 non connecté, 403 interdit, 404, 422 données invalides) ; 5xx = le serveur a planté.",
   "Le corps voyage en **JSON** : du texte. Il faut le convertir en objet JS (fetch : `res.json()`, axios le fait tout seul).",
   "La réponse prend du temps : pendant ce temps, ton écran est dans un état **chargement**. Ensuite, **succès** ou **erreur**. Toujours ces 3 états.",
   "Onglet **Réseau** (Network) des outils de développement (F12) : tu y vois chaque requête, son statut et son contenu. C'est ton meilleur outil pour comprendre."],
  ["Croire que la donnée est là « tout de suite » : elle arrive plus tard, il faut gérer le chargement.",
   "Ignorer les codes 4xx/5xx : une réponse 404 n'est pas « des données »."],
  code("plaintext", r"""
NAVIGATEUR (React)                           SERVEUR (Symfony / Next)
------------------                           ------------------------
GET /api/articles            ------------->  lit la base
                             <-------------  200 OK
                                             [{"id":1,"titre":"Hello"}, ...]

POST /api/articles           ------------->  valide (DTO), enregistre
Content-Type: application/json
{"titre":"Nouveau","contenu":"..."}
                             <-------------  201 Created
                                             {"id":42,"titre":"Nouveau", ...}

POST /api/articles           ------------->  validation échoue
{"titre":""}
                             <-------------  422 Unprocessable Entity
                                             {"violations":[{"propertyPath":"titre", ...}]}

DELETE /api/articles/42      ------------->  supprime
                             <-------------  204 No Content   (pas de corps)
"""),
  ["Chaque échange = une requête et une réponse, rien de plus.",
   "Le même `POST` peut réussir (201) ou échouer (422) selon les données envoyées.",
   "Ouvre F12 > Réseau sur n'importe quel site et retrouve ces éléments : méthode, URL, statut, réponse."],
  [Q("Tu veux enregistrer un nouveau commentaire. Quelle méthode ?",
     ["GET", "POST", "DELETE", "HEAD"], 1,
     "POST crée une ressource : c'est une mutation."),
   Q("Le serveur répond 422. Ça veut dire…",
     ["Tout va bien", "Les données envoyées sont invalides", "Le serveur a planté", "La page n'existe pas"], 1,
     "4xx = erreur côté client ; 422 = validation échouée (ton DTO Symfony)."),
   Q("Pendant qu'on attend la réponse, l'écran doit…",
     ["ne rien afficher", "afficher un état de chargement", "planter", "afficher les anciennes données comme si de rien n'était"], 1,
     "Trois états à gérer : chargement, succès, erreur.")],
  TD("Lire le trafic réseau",
     "Exercice d'observation, sans code : ouvre un site que tu utilises (ou ton propre projet), F12 > onglet Réseau > filtre « Fetch/XHR ».",
     ["Trouve une requête GET : note son URL, son statut et un extrait de la réponse",
      "Fais une action qui enregistre quelque chose (like, commentaire, panier) : trouve le POST/PUT/PATCH, note le corps envoyé (onglet Payload)",
      "Provoque une erreur (formulaire vide, mauvaise page) et note le statut",
      "Pour chacune, écris en une phrase : qui demande quoi, et qu'a répondu le serveur"],
     code("plaintext", r"""
Requête 1 (lecture)
  Méthode / URL :
  Statut :
  Réponse (extrait) :
  En une phrase :

Requête 2 (mutation)
  Méthode / URL :
  Corps envoyé :
  Statut :
  En une phrase :

Requête 3 (erreur)
  Méthode / URL :
  Statut :
  En une phrase :
"""),
     ["Coche « Preserve log » pour garder les requêtes quand la page change.",
      "Clique sur une requête : onglets Headers (méthode, statut), Payload (ce qui part), Response (ce qui revient)."],
     code("plaintext", r"""
Exemple sur un réseau social :

Requête 1 : GET /api/feed?page=1 -> 200
  Réponse : [{"id": 981, "auteur": "...", "likes": 12}, ...]
  "Le front demande la page 1 du fil, le serveur renvoie la liste des posts."

Requête 2 : POST /api/posts/981/like -> 201
  Corps : {}   (l'id est dans l'URL)
  "Le front signale un like sur le post 981, le serveur l'enregistre."

Requête 3 : POST /api/comments -> 422
  Corps : {"postId": 981, "texte": ""}
  "Le front envoie un commentaire vide, le serveur refuse : données invalides."
"""),
     ["Tu as identifié au moins une lecture et une mutation",
      "Tu sais où lire le statut et le corps d'une requête"])),

M("data-get", T, "Récupérer des données : fetch & axios", 15,
  "Charger une liste depuis une API dans un composant React, avec chargement et erreur.",
  "Le composant s'affiche avant que les données arrivent. Il faut donc lancer la requête, attendre, puis ranger le résultat dans le state pour que React redessine.",
  ["Le composant s'affiche avec `loading = true`",
   "Un **effet** lance la requête (`axios.get`)",
   "La réponse arrive : on la range dans le **state** (`setArticles`)",
   "React **redessine** avec les données, ou avec l'erreur"],
  ["**fetch** est intégré au navigateur. **axios** est une librairie (`npm i axios`) qui simplifie : JSON automatique, erreurs automatiques sur 4xx/5xx, `baseURL`.",
   "Avec fetch, un 404 n'est **pas** une erreur : il faut vérifier `res.ok`. Avec axios, un 404 **lève** une erreur : tu la reçois dans `catch`.",
   "Avec axios, les données sont dans `response.data`.",
   "Crée une **instance** : `axios.create({ baseURL: '/api' })`, puis `api.get('/articles')` partout.",
   "Annule la requête si le composant disparaît (`AbortController`), comme vu dans le module useEffect."],
  ["Oublier le tableau de dépendances de `useEffect` : requête à chaque rendu, en boucle.",
   "Afficher `articles.map` alors que `articles` est encore `null`."],
  code("tsx", r"""
// api/client.ts : une seule configuration pour tout le projet
import axios from 'axios';

export const api = axios.create({
  baseURL: 'http://localhost:8000/api',   // ton back Symfony
  headers: { 'Content-Type': 'application/json' },
});

// ArticleList.tsx
import { useEffect, useState } from 'react';
import axios from 'axios';
import { api } from './api/client';

type Article = { id: number; titre: string; auteur: string };

export default function ArticleList() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    api.get<Article[]>('/articles', { signal: controller.signal })
      .then((res) => setArticles(res.data))            // les données sont dans .data
      .catch((err) => {
        if (axios.isCancel(err)) return;               // requête annulée : on ignore
        setError(err.response?.status === 404 ? 'Introuvable' : 'Erreur de chargement');
      })
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, []);                                              // une seule fois au montage

  if (loading) return <p>Chargement…</p>;
  if (error) return <p role="alert">{error}</p>;
  return <ul>{articles.map((a) => <li key={a.id}>{a.titre} — {a.auteur}</li>)}</ul>;
}

// Même chose avec fetch :
// const res = await fetch('/api/articles');
// if (!res.ok) throw new Error(`HTTP ${res.status}`);   // à faire soi-même
// const data = await res.json();                          // à faire soi-même
"""),
  ["Trois states : les données, le chargement, l'erreur.",
   "`err.response?.status` : axios donne le code HTTP de l'erreur.",
   "Le bloc fetch en commentaire montre les deux étapes qu'axios fait à ta place."],
  [Q("Avec axios, où sont les données JSON renvoyées par le serveur ?",
     ["`res.json()`", "`res.data`", "`res.body`", "`res`"], 1,
     "axios a déjà décodé le JSON."),
   Q("Le serveur répond 404. Avec `fetch`, que se passe-t-il ?",
     ["fetch lève une erreur", "fetch résout normalement : il faut tester `res.ok`", "fetch réessaie", "La page plante"], 1,
     "fetch ne rejette que si le réseau échoue. axios, lui, rejette sur 4xx/5xx."),
   Q("Pourquoi `useEffect(..., [])` et pas le fetch directement dans le corps du composant ?",
     ["C'est plus joli", "Sinon la requête repart à chaque rendu, et chaque réponse provoque un nouveau rendu : boucle", "axios l'impose", "Pour le SEO"], 1,
     "Le corps du composant s'exécute à chaque rendu.")],
  TD("Afficher le catalogue de livres",
     "Affiche la liste de `GET /api/livres` (ton API Symfony du parcours DTO, ou une API de test comme `https://jsonplaceholder.typicode.com/posts`).",
     ["Une instance `api` avec `baseURL`",
      "Les 3 états : chargement, erreur, liste",
      "Un bouton « Recharger » qui relance la requête",
      "Message « Aucun livre » si la liste est vide"],
     code("tsx", r"""
import { useEffect, useState } from 'react';
import { api } from './api/client';

type Livre = { id: number; titre: string; auteur: string; disponible: boolean };

export default function Catalogue() {
  // à toi
}
"""),
     ["Pour « Recharger » : un state `reloadKey` que tu incrémentes, et que tu mets dans les dépendances de l'effet.",
      "Remets `loading` à `true` et `error` à `null` au début de l'effet."],
     code("tsx", r"""
import axios from 'axios';

export default function Catalogue() {
  const [livres, setLivres] = useState<Livre[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    api.get<Livre[]>('/livres', { signal: controller.signal })
      .then((res) => setLivres(res.data))
      .catch((err) => { if (!axios.isCancel(err)) setError('Impossible de charger les livres'); })
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, [reloadKey]);

  return (
    <section>
      <button onClick={() => setReloadKey((k) => k + 1)} disabled={loading}>Recharger</button>
      {loading && <p>Chargement…</p>}
      {error && <p role="alert">{error}</p>}
      {!loading && !error && livres.length === 0 && <p>Aucun livre</p>}
      <ul>
        {livres.map((l) => (
          <li key={l.id}>{l.titre} — {l.auteur} {l.disponible ? '' : '(emprunté)'}</li>
        ))}
      </ul>
    </section>
  );
}
"""),
     ["Dans F12 > Réseau, tu vois un seul GET au chargement et un par clic sur « Recharger »",
      "Couper le serveur affiche ton message d'erreur au lieu de planter"])),

M("data-mutations", T, "Envoyer des données : les mutations", 18,
  "Créer, modifier, supprimer depuis React, et mettre l'écran à jour ensuite.",
  "Lire, c'est une seule étape. Envoyer, c'en est deux : faire la requête, PUIS mettre à jour ce que l'écran affiche. C'est la deuxième étape qu'on oublie, et l'écran ne bouge pas.",
  ["L'utilisateur **déclenche** l'action (submit, clic)",
   "On envoie la **mutation** : `api.post` / `put` / `patch` / `delete`, avec un état **envoi en cours**",
   "Le serveur **valide et enregistre**, puis renvoie l'objet créé/modifié (ou une erreur 422)",
   "On **met à jour l'écran** : ajouter la réponse à la liste, ou recharger la liste"],
  ["`api.post('/articles', { titre, contenu })` : axios transforme l'objet en JSON tout seul.",
   "Mutation = événement de l'utilisateur, donc **dans le handler** (`onSubmit`, `onClick`), **pas** dans un `useEffect`.",
   "Après succès, deux façons de mettre à jour : **ajouter la réponse** au state (`setArticles(a => [...a, res.data])`) ou **recharger** la liste.",
   "Erreurs 422 : `err.response.data` contient les violations ; affiche-les sous les champs.",
   "Pendant l'envoi : désactive le bouton (`disabled={saving}`) pour éviter les doubles clics."],
  ["Envoyer puis oublier de mettre à jour le state : la donnée est en base mais pas à l'écran.",
   "Modifier le state AVANT de savoir si le serveur a accepté (sauf mise à jour optimiste volontaire, voir TanStack Query)."],
  code("tsx", r"""
import { useState, FormEvent } from 'react';
import axios from 'axios';
import { api } from './api/client';

type Article = { id: number; titre: string };

export default function Articles({ initial }: { initial: Article[] }) {
  const [articles, setArticles] = useState(initial);
  const [titre, setTitre] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const res = await api.post<Article>('/articles', { titre, contenu: '...' }); // 1. envoyer
      setArticles((list) => [res.data, ...list]);                                // 2. mettre à jour l'écran
      setTitre('');
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 422) {
        setError('Titre invalide (5 caractères minimum)');
      } else {
        setError("L'enregistrement a échoué");
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    await api.delete(`/articles/${id}`);
    setArticles((list) => list.filter((a) => a.id !== id));
  }

  return (
    <>
      <form onSubmit={handleCreate}>
        <input value={titre} onChange={(e) => setTitre(e.target.value)} />
        <button disabled={saving}>{saving ? 'Envoi…' : 'Publier'}</button>
        {error && <p role="alert">{error}</p>}
      </form>
      <ul>
        {articles.map((a) => (
          <li key={a.id}>{a.titre} <button onClick={() => handleDelete(a.id)}>Supprimer</button></li>
        ))}
      </ul>
    </>
  );
}
"""),
  ["`async/await` + `try/catch/finally` : plus lisible que `.then()` pour une mutation.",
   "On ajoute `res.data` (la version du serveur, avec son `id`), pas ce qu'on a tapé.",
   "Supprimer : on retire l'élément du state une fois le serveur d'accord."],
  [Q("Où lancer un `api.post` qui crée un commentaire ?",
     ["Dans un useEffect", "Dans le handler `onSubmit`", "Dans le corps du composant", "Dans le return"], 1,
     "C'est une réaction à une action de l'utilisateur."),
   Q("Le POST réussit mais la liste à l'écran ne change pas. Que manque-t-il ?",
     ["Un `useEffect`", "La mise à jour du state avec la réponse (ou un rechargement)", "`preventDefault`", "Un header"], 1,
     "Le serveur a la donnée, mais React ne le sait pas."),
   Q("Pourquoi ajouter `res.data` à la liste plutôt que `{ titre }` ?",
     ["C'est pareil", "La réponse contient l'`id` et les champs calculés par le serveur", "Pour la performance", "axios l'impose"], 1,
     "Sans id, impossible de supprimer ou modifier ensuite.")],
  TD("Gérer les emprunts",
     "Sur la liste des livres, ajoute les actions d'emprunt (endpoint `POST /api/emprunts` du parcours DTO, ou simule-le).",
     ["Un bouton « Emprunter » par livre disponible → `api.post('/emprunts', { livreId, rendreLe })`",
      "Pendant l'envoi, seul le bouton de CE livre est désactivé",
      "Succès : le livre passe à « emprunté » dans la liste sans recharger",
      "409 : message « Déjà emprunté » ; autre erreur : message générique"],
     code("tsx", r"""
type Livre = { id: number; titre: string; disponible: boolean };

export default function Emprunts({ livres: initial }: { livres: Livre[] }) {
  const [livres, setLivres] = useState(initial);
  // à toi
}
"""),
     ["Un state `pendingId: number | null` suffit pour savoir quel bouton désactiver.",
      "Mise à jour : `setLivres(ls => ls.map(l => l.id === id ? { ...l, disponible: false } : l))`",
      "Date de retour dans 14 jours : `new Date(Date.now() + 14 * 864e5).toISOString().slice(0, 10)`"],
     code("tsx", r"""
export default function Emprunts({ livres: initial }: { livres: Livre[] }) {
  const [livres, setLivres] = useState(initial);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function emprunter(id: number) {
    setPendingId(id);
    setMessage(null);
    try {
      const rendreLe = new Date(Date.now() + 14 * 864e5).toISOString().slice(0, 10);
      await api.post('/emprunts', { livreId: id, rendreLe });
      setLivres((ls) => ls.map((l) => (l.id === id ? { ...l, disponible: false } : l)));
    } catch (err) {
      const status = axios.isAxiosError(err) ? err.response?.status : undefined;
      setMessage(status === 409 ? 'Déjà emprunté' : "L'emprunt a échoué");
    } finally {
      setPendingId(null);
    }
  }

  return (
    <>
      {message && <p role="alert">{message}</p>}
      <ul>
        {livres.map((l) => (
          <li key={l.id}>
            {l.titre}{' '}
            {l.disponible ? (
              <button onClick={() => emprunter(l.id)} disabled={pendingId === l.id}>
                {pendingId === l.id ? 'Envoi…' : 'Emprunter'}
              </button>
            ) : (
              <em>emprunté</em>
            )}
          </li>
        ))}
      </ul>
    </>
  );
}
"""),
     ["F12 > Réseau : un seul POST par clic, avec le bon corps JSON",
      "Le livre change d'état sans recharger la page"])),

M("data-organiser", T, "Organiser : couche API & hook", 15,
  "Sortir les appels HTTP des composants pour que tout reste lisible.",
  "Quand chaque composant contient ses `api.get`, ses URLs et ses `try/catch`, le moindre changement d'API oblige à modifier 15 fichiers.",
  ["Un fichier **`api/articles.ts`** regroupe les fonctions (`getArticles`, `createArticle`…) et leurs types",
   "Un **hook** `useArticles()` gère state, chargement, erreur et mutations",
   "Le **composant** appelle juste le hook et affiche",
   "Changer l'API = modifier **un seul fichier**"],
  ["Trois couches : client HTTP (`api/client.ts`) → fonctions par ressource (`api/articles.ts`) → hooks (`useArticles`).",
   "Les types TypeScript (`Article`, `CreateArticleInput`) reflètent tes **DTO Symfony** : c'est le même contrat des deux côtés.",
   "Le hook expose des actions nommées : `create`, `remove`, `reload`.",
   "Les **intercepteurs** axios ajoutent le token d'authentification à chaque requête, à un seul endroit."],
  ["Mettre les URLs en dur dans les composants.",
   "Un hook qui fait tout pour toute l'appli : un hook par ressource."],
  code("tsx", r"""
// api/client.ts
import axios from 'axios';
export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// api/articles.ts : les mêmes champs que tes DTO Symfony
export type Article = { id: number; titre: string; extrait: string; auteur: string };
export type CreateArticleInput = { titre: string; contenu: string };

export const getArticles = () => api.get<Article[]>('/articles').then((r) => r.data);
export const createArticle = (input: CreateArticleInput) => api.post<Article>('/articles', input).then((r) => r.data);
export const deleteArticle = (id: number) => api.delete(`/articles/${id}`);

// hooks/useArticles.ts
export function useArticles() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try { setArticles(await getArticles()); }
    catch { setError('Erreur de chargement'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { reload(); }, [reload]);

  async function create(input: CreateArticleInput) {
    const created = await createArticle(input);
    setArticles((a) => [created, ...a]);
  }

  async function remove(id: number) {
    await deleteArticle(id);
    setArticles((a) => a.filter((x) => x.id !== id));
  }

  return { articles, loading, error, reload, create, remove };
}

// ArticlesPage.tsx : le composant ne parle plus HTTP
export default function ArticlesPage() {
  const { articles, loading, error, remove } = useArticles();
  if (loading) return <p>Chargement…</p>;
  if (error) return <p role="alert">{error}</p>;
  return <ul>{articles.map((a) => <li key={a.id}>{a.titre} <button onClick={() => remove(a.id)}>×</button></li>)}</ul>;
}
"""),
  ["`.then((r) => r.data)` : les fonctions renvoient directement les données, pas la réponse axios.",
   "L'intercepteur ajoute le token partout, sans y penser dans chaque appel.",
   "`ArticlesPage` fait 5 lignes et ne contient aucune URL."],
  [Q("L'URL `/articles` devient `/v2/articles`. Combien de fichiers modifier ?",
     ["Tous les composants", "Un seul : `api/articles.ts`", "Le hook et les composants", "Aucun"], 1,
     "C'est tout l'intérêt de la couche API."),
   Q("À quoi sert un intercepteur de requête axios ?",
     ["À annuler les requêtes", "À modifier chaque requête avant l'envoi (ex. ajouter le token)", "À mettre en cache", "À valider le JSON"], 1,
     "Un seul endroit pour l'authentification."),
   Q("D'où viennent idéalement les types `Article` du front ?",
     ["On les invente", "Ils reflètent les DTO de sortie de l'API", "De la base de données", "D'axios"], 1,
     "Le DTO est le contrat ; le type TypeScript en est le miroir.")],
  TD("Refactoriser le catalogue",
     "Reprends tes TD Catalogue et Emprunts, et range-les en couches.",
     ["`api/livres.ts` : `getLivres()`, `emprunter(livreId, rendreLe)` et les types",
      "`hooks/useLivres.ts` : `{ livres, loading, error, reload, emprunter, pendingId }`",
      "Le composant `Catalogue` n'importe plus `api` ni `axios`"],
     code("tsx", r"""
// api/livres.ts
// hooks/useLivres.ts
// components/Catalogue.tsx
// à toi
"""),
     ["La logique `pendingId` et la mise à jour du livre déménagent dans le hook.",
      "Le hook renvoie aussi le message d'erreur d'emprunt."],
     code("tsx", r"""
// api/livres.ts
export type Livre = { id: number; titre: string; auteur: string; disponible: boolean };
export const getLivres = () => api.get<Livre[]>('/livres').then((r) => r.data);
export const emprunterLivre = (livreId: number, rendreLe: string) =>
  api.post('/emprunts', { livreId, rendreLe }).then((r) => r.data);

// hooks/useLivres.ts
export function useLivres() {
  const [livres, setLivres] = useState<Livre[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<number | null>(null);

  const reload = useCallback(async () => {
    setLoading(true); setError(null);
    try { setLivres(await getLivres()); } catch { setError('Impossible de charger les livres'); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { reload(); }, [reload]);

  async function emprunter(id: number) {
    setPendingId(id); setError(null);
    try {
      const rendreLe = new Date(Date.now() + 14 * 864e5).toISOString().slice(0, 10);
      await emprunterLivre(id, rendreLe);
      setLivres((ls) => ls.map((l) => (l.id === id ? { ...l, disponible: false } : l)));
    } catch (err) {
      setError(axios.isAxiosError(err) && err.response?.status === 409 ? 'Déjà emprunté' : "L'emprunt a échoué");
    } finally { setPendingId(null); }
  }

  return { livres, loading, error, reload, emprunter, pendingId };
}

// components/Catalogue.tsx
export default function Catalogue() {
  const { livres, loading, error, reload, emprunter, pendingId } = useLivres();
  if (loading) return <p>Chargement…</p>;
  return (
    <section>
      {error && <p role="alert">{error}</p>}
      <button onClick={reload}>Recharger</button>
      <ul>
        {livres.map((l) => (
          <li key={l.id}>
            {l.titre}{' '}
            {l.disponible
              ? <button disabled={pendingId === l.id} onClick={() => emprunter(l.id)}>Emprunter</button>
              : <em>emprunté</em>}
          </li>
        ))}
      </ul>
    </section>
  );
}
"""),
     ["`Catalogue.tsx` n'importe ni `axios` ni `api`",
      "Changer l'URL des emprunts ne touche qu'un fichier"])),

M("data-tanstack", T, "TanStack Query : le cache des données", 18,
  "Utiliser la librairie standard qui gère chargement, cache, rechargement et mutations à ta place.",
  "Dans les modules précédents, tu as écrit à la main loading, error, reload, mise à jour après mutation… Dans une vraie appli, ça se multiplie. TanStack Query (ex-React Query) fait tout ça, avec un cache partagé.",
  ["`useQuery` **lit** : une clé (`['articles']`) + une fonction qui va chercher (`getArticles`)",
   "Le résultat est mis en **cache** sous cette clé, partagé par tous les composants",
   "`useMutation` **écrit** : il appelle ta fonction (`createArticle`)",
   "En cas de succès, `invalidateQueries(['articles'])` dit « ces données sont périmées » → **rechargement automatique**"],
  ["Installation : `npm i @tanstack/react-query`, puis `<QueryClientProvider client={queryClient}>` autour de l'appli.",
   "`useQuery` renvoie `data`, `isPending`, `isError`, `error`, `refetch` : tu n'écris plus ces states.",
   "Deux composants avec la même clé = **une seule requête** : ils partagent le cache.",
   "La clé contient les paramètres : `['articles', { page, q }]` → un cache par combinaison.",
   "Tes fonctions de la couche API (`getArticles`…) se branchent telles quelles : axios fait la requête, TanStack Query gère l'état."],
  ["Mettre les données de `useQuery` dans un `useState` : tu recrées le problème. Utilise `data` directement.",
   "Oublier d'invalider après une mutation : l'écran garde l'ancienne liste."],
  code("tsx", r"""
// main.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
const queryClient = new QueryClient();

createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>,
);

// ArticlesPage.tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getArticles, createArticle, deleteArticle } from './api/articles';

export default function ArticlesPage() {
  const queryClient = useQueryClient();

  const { data: articles, isPending, isError } = useQuery({
    queryKey: ['articles'],
    queryFn: getArticles,                 // ta fonction axios
  });

  const create = useMutation({
    mutationFn: createArticle,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['articles'] }),
  });

  const remove = useMutation({
    mutationFn: deleteArticle,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['articles'] }),
  });

  if (isPending) return <p>Chargement…</p>;
  if (isError) return <p role="alert">Erreur de chargement</p>;

  return (
    <>
      <button
        onClick={() => create.mutate({ titre: 'Nouvel article', contenu: '...' })}
        disabled={create.isPending}
      >
        {create.isPending ? 'Envoi…' : 'Ajouter'}
      </button>
      {create.isError && <p role="alert">L'ajout a échoué</p>}
      <ul>
        {articles.map((a) => (
          <li key={a.id}>{a.titre} <button onClick={() => remove.mutate(a.id)}>×</button></li>
        ))}
      </ul>
    </>
  );
}
"""),
  ["Plus aucun `useState` ni `useEffect` pour les données.",
   "`create.mutate(...)` lance la mutation ; `create.isPending` remplace ton `saving`.",
   "Après succès, la clé `['articles']` est invalidée : la liste se recharge seule, partout où elle est affichée."],
  [Q("Deux composants appellent `useQuery({ queryKey: ['articles'], ... })` en même temps. Combien de requêtes ?",
     ["Deux", "Une, le cache est partagé", "Aucune", "Une par rendu"], 1,
     "La clé identifie la donnée dans le cache."),
   Q("Après `createArticle` réussi, comment rafraîchir la liste ?",
     ["`window.location.reload()`", "`queryClient.invalidateQueries({ queryKey: ['articles'] })`", "Un useEffect", "Rien, c'est automatique sans rien faire"], 1,
     "Invalider = marquer comme périmé, TanStack Query recharge."),
   Q("La liste dépend d'un filtre `page`. Quelle clé ?",
     ["`['articles']`", "`['articles', { page }]`", "`page`", "Pas de clé"], 1,
     "La clé contient tout ce dont dépend la requête.")],
  TD("Catalogue avec TanStack Query",
     "Réécris `Catalogue` avec TanStack Query, en réutilisant `api/livres.ts`.",
     ["`useQuery` avec la clé `['livres', { page }]` et un bouton page suivante / précédente",
      "`useMutation` pour emprunter, qui invalide `['livres']` en cas de succès",
      "Message « Déjà emprunté » si la mutation échoue avec 409",
      "Aucun `useState` pour les données, le chargement ou l'erreur (un `useState` pour `page` est normal)"],
     code("tsx", r"""
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getLivresPage, emprunterLivre } from './api/livres';
// getLivresPage(page) -> { items: Livre[], pages: number }

export default function Catalogue() {
  const [page, setPage] = useState(1);
  // à toi
}
"""),
     ["`invalidateQueries({ queryKey: ['livres'] })` invalide aussi `['livres', { page: 2 }]` : la correspondance se fait par préfixe.",
      "Erreur de mutation : `emprunt.error` ; avec axios, `axios.isAxiosError(emprunt.error) && emprunt.error.response?.status === 409`.",
      "`placeholderData: keepPreviousData` (import depuis `@tanstack/react-query`) garde la page précédente affichée pendant le chargement de la suivante."],
     code("tsx", r"""
import { useState } from 'react';
import axios from 'axios';
import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import { getLivresPage, emprunterLivre } from './api/livres';

export default function Catalogue() {
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();

  const { data, isPending, isError } = useQuery({
    queryKey: ['livres', { page }],
    queryFn: () => getLivresPage(page),
    placeholderData: keepPreviousData,
  });

  const emprunt = useMutation({
    mutationFn: (livreId: number) =>
      emprunterLivre(livreId, new Date(Date.now() + 14 * 864e5).toISOString().slice(0, 10)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['livres'] }),
  });

  if (isPending) return <p>Chargement…</p>;
  if (isError) return <p role="alert">Impossible de charger les livres</p>;

  const conflit = axios.isAxiosError(emprunt.error) && emprunt.error.response?.status === 409;

  return (
    <section>
      {emprunt.isError && <p role="alert">{conflit ? 'Déjà emprunté' : "L'emprunt a échoué"}</p>}
      <ul>
        {data.items.map((l) => (
          <li key={l.id}>
            {l.titre}{' '}
            {l.disponible ? (
              <button
                onClick={() => emprunt.mutate(l.id)}
                disabled={emprunt.isPending && emprunt.variables === l.id}
              >
                Emprunter
              </button>
            ) : (
              <em>emprunté</em>
            )}
          </li>
        ))}
      </ul>
      <button onClick={() => setPage((p) => p - 1)} disabled={page === 1}>Précédent</button>
      <span> {page} / {data.pages} </span>
      <button onClick={() => setPage((p) => p + 1)} disabled={page >= data.pages}>Suivant</button>
    </section>
  );
}
"""),
     ["Revenir à une page déjà vue s'affiche instantanément (cache)",
      "Après un emprunt, le livre passe à « emprunté » sans code de mise à jour manuelle"])),
]

"""Parcours Données & API : module « axios de A à Z » (après « HTTP », avant « Lire des données »)."""
from common import M, P, L, D, N, E, LANE, F, TD, RUN, Q
from c_data import LIB_API

CLIENT = F("api/client.ts", "ts", r"""
import axios from 'axios';

// Le client du projet : toutes les requêtes partent de lui.
export const api = axios.create({
  baseURL: '/api',                                   // ajouté devant chaque URL
  headers: { 'Content-Type': 'application/json' },   // envoyé avec chaque requête
  timeout: 5000,                                     // abandonne après 5 s sans réponse
});
""")

MOD = M("data-axios", "data", "axios de A à Z", 35,
  "Savoir envoyer n'importe quelle requête avec axios (lire, créer, modifier, supprimer), lire la réponse, transformer chaque erreur en message clair, et brancher des intercepteurs.",
  "Dans ton projet, React Query décide **quand** charger et garde les réponses en cache, mais ce n'est pas lui qui parle au serveur : il appelle une fonction que tu écris, et cette fonction utilise **axios**. Tous les modules suivants s'en servent. Ici, on le voit seul, sans React, pour que chaque morceau soit clair avant de le mélanger avec des composants.",
  [
    P("Librairie", "Du code écrit par d'autres, qu'on installe dans le projet (`npm install axios`) puis qu'on importe : `import axios from 'axios'`."),
    P("Promesse et `await`", "Une requête prend du temps : axios renvoie une **promesse** (un résultat qui arrivera plus tard). Dans une fonction `async`, `await` attend ce résultat. Si la promesse échoue, `await` **lève une erreur**, qu'on attrape avec `try { … } catch (err) { … }`."),
    P("Statut HTTP", "Le nombre qui résume la réponse : 2xx réussi (200 OK, 201 créé, 204 sans contenu), 4xx erreur du client (400, 401 non connecté, 403 interdit, 404 introuvable, 409 conflit, 422 données invalides), 5xx erreur du serveur."),
    P("Corps (body)", "Les données envoyées avec une requête (`POST`, `PUT`, `PATCH`) ou reçues dans une réponse, en JSON."),
    P("Paramètres d'URL", "La partie après `?` : `/livres?q=dune&page=2`. Ils servent à filtrer ou paginer une lecture."),
    P("En-tête `Authorization`", "L'en-tête qui transporte la preuve que tu es connectée, le plus souvent un jeton : `Authorization: Bearer abc123`."),
  ],
  ["On crée **un seul client** pour le projet : `api = axios.create({ baseURL: '/api' })`.",
   "On envoie une requête avec la méthode du verbe HTTP : `api.get`, `api.post`, `api.put`, `api.patch`, `api.delete`.",
   "La réponse arrive dans un objet `res` : les données sont dans `res.data`, le statut dans `res.status`.",
   "Si le statut est 4xx ou 5xx, axios **lève une erreur** : `err.response.status` et `err.response.data` disent ce qui s'est passé.",
   "Les **intercepteurs** ajoutent un comportement à toutes les requêtes (le jeton) ou à toutes les réponses (gérer un 401) à un seul endroit."],
  D(
    nodes=[
      N("fn", 0, 0, "Ta fonction", "getLivres(q)", kind="file", color="accent"),
      N("ri", 1, 0, "Intercepteur requête", "ajoute le jeton", kind="pill", color="warn"),
      N("srv", 2, 0, "Serveur", "GET /api/livres?q=…"),
      N("ok", 1, 1, "2xx", "res.data", kind="pill", color="good"),
      N("ko", 1, 2, "4xx / 5xx", "throw err (err.response)", kind="pill", color="bad"),
      N("call", 0, 1, "Qui appelle", "await / React Query", kind="file"),
    ],
    edges=[E("fn", "ri", "api.get"), E("ri", "srv", "HTTP"), E("srv", "ok", color="good"), E("srv", "ko", dashed=True, color="bad"), E("ok", "call", "renvoie"), E("ko", "call", "lève", dashed=True)],
    lanes=[LANE("Ton code", 0, 0, "accent"), LANE("axios", 1, 1, "tc"), LANE("Réseau", 2, 2)],
    caption="Une requête axios : elle passe par les intercepteurs, part au serveur, puis revient soit en réponse (2xx), soit en erreur (4xx/5xx)."),
  [
    L("Qui fait quoi : axios et React Query", r"""
Deux outils, deux rôles qu'il ne faut pas confondre :

| | axios | React Query (TanStack Query) |
|---|---|---|
| Son travail | **envoyer** une requête et rapporter la réponse | décider **quand** charger, garder en **cache**, recharger |
| Ce qu'il connaît | URL, verbe, corps, en-têtes, statut | des clés (`['livres', 3]`) et des fonctions qui chargent |
| Où on l'écrit | dans des fonctions du dossier `api/` | dans les composants (`useQuery`, `useMutation`) |

Concrètement, React Query reçoit une fonction (`queryFn`) et l'appelle quand il en a besoin. C'est **toi** qui écris cette fonction, avec axios dedans. Donc pour bien utiliser React Query, il faut d'abord savoir écrire ces fonctions-là : c'est l'objet de ce module.
"""),
    L("Un client pour tout le projet : `axios.create`", r"""
Tu pourrais écrire `axios.get('/api/livres')` partout. Le problème : le jour où l'adresse de l'API change, ou qu'il faut ajouter un en-tête à toutes les requêtes, tu dois modifier chaque appel. On crée donc **un client** une seule fois, et tout le projet l'importe.

`axios.create(options)` fabrique ce client. Les trois options qu'on utilise le plus :

- `baseURL` : un début d'adresse ajouté automatiquement. Avec `baseURL: '/api'`, `api.get('/livres')` appelle `/api/livres`.
- `headers` : des en-têtes envoyés avec **chaque** requête.
- `timeout` : un délai en millisecondes au-delà duquel axios abandonne et lève une erreur (sans lui, une requête bloquée peut attendre indéfiniment).

Le client est rangé dans son propre fichier, `api/client.ts`, et exporté sous le nom `api` :

```ts
import axios from 'axios';

export const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 5000,
});
```

Ensuite, tous les autres fichiers font `import { api } from './client'` et n'utilisent plus jamais `axios.get` directement.
"""),
    L("Les cinq verbes, et ce qu'ils renvoient", r"""
Le client a une méthode par verbe HTTP. Ce qui change entre elles, c'est la place du **corps** :

- `api.get(url, config?)` et `api.delete(url, config?)` : pas de corps.
- `api.post(url, corps, config?)`, `api.put(url, corps, config?)` et `api.patch(url, corps, config?)` : le corps est le **deuxième** argument. Tu donnes un objet JavaScript, axios le transforme en JSON.

Le dernier argument, `config`, est facultatif. Son option la plus utile est `params` : un objet transformé en paramètres d'URL. `api.get('/livres', { params: { q: 'dune', page: 2 } })` appelle `/api/livres?q=dune&page=2`, en encodant les caractères spéciaux pour toi.

Chaque méthode renvoie une promesse d'un objet **réponse** `res`, qui contient :

- `res.data` : le corps de la réponse, **déjà converti** de JSON en objet (pas de `res.json()` comme avec `fetch`) ;
- `res.status` : le statut (200, 201…) ;
- `res.headers` : les en-têtes reçus.

En TypeScript, on indique le type attendu de `res.data` entre chevrons : `api.get<Livre[]>(...)`. Comme on ne s'intéresse presque toujours qu'aux données, chaque fonction renvoie `res.data` :

```ts
import { api } from './client';

export type Livre = { id: number; titre: string; auteur: string; disponible: boolean };
export type Emprunt = { id: number; livreId: number; rendreLe: string };

export async function getLivres(q?: string): Promise<Livre[]> {
  const res = await api.get<Livre[]>('/livres', { params: { q } });   // GET /api/livres?q=...
  return res.data;
}

export async function getLivre(id: number): Promise<Livre> {
  const res = await api.get<Livre>(`/livres/${id}`);                  // GET /api/livres/3
  return res.data;
}

export async function emprunter(livreId: number, rendreLe: string): Promise<Emprunt> {
  const res = await api.post<Emprunt>('/emprunts', { livreId, rendreLe });   // corps en 2e argument
  return res.data;
}

export async function supprimerArticle(id: number): Promise<void> {
  await api.delete(`/articles/${id}`);                                // 204 : rien à renvoyer
}
```

Un paramètre qui vaut `undefined` (ici `q` quand on n'a rien tapé) n'est pas ajouté à l'URL : `getLivres()` appelle simplement `/api/livres`.
"""),
    L("Quand ça échoue : lire l'erreur", r"""
Différence importante avec `fetch` : avec axios, une réponse **4xx ou 5xx fait échouer la promesse**. `await` lève alors une erreur, et le code après lui ne s'exécute pas. On la récupère avec `try / catch`.

Cette erreur est un objet qui contient :

- `err.response` : la réponse du serveur, **si** il y en a eu une. Dedans, `err.response.status` (404, 409, 422…) et `err.response.data` (le corps JSON d'erreur que le serveur a envoyé, par exemple `{ error: 'Livre introuvable' }` ou `{ violations: [...] }` pour un 422 de Symfony).
- Pas de `err.response` du tout : la requête n'a **jamais reçu de réponse** (pas de réseau, serveur éteint, délai `timeout` dépassé).

Comme un `catch` attrape **toutes** les erreurs (y compris une faute de frappe dans ton code), on vérifie d'abord qu'elle vient bien d'axios avec `axios.isAxiosError(err)` : la fonction renvoie `true` ou `false`, et TypeScript sait ensuite que `err.response` existe peut-être. Le `?.` lit `status` seulement si `response` existe (sinon on obtient `undefined` au lieu d'un plantage).

On centralise la traduction dans une seule fonction, utilisée par tous les écrans :

```ts
import axios from 'axios';

export function messageErreur(err: unknown): string {
  if (!axios.isAxiosError(err)) return 'Erreur inattendue';           // pas une erreur de requête
  if (!err.response) return 'Connexion impossible, réessaie';           // aucune réponse reçue
  const { status, data } = err.response;
  if (status === 404) return data.error ?? 'Introuvable';
  if (status === 409) return data.error ?? 'Conflit';
  if (status === 422) return data.violations?.[0]?.title ?? 'Données invalides';
  if (status === 401) return 'Connecte-toi';
  return `Erreur serveur (${status})`;
}

try {
  await emprunter(2, '2026-12-01');
} catch (err) {
  console.log(messageErreur(err));   // « Déjà emprunté » (409)
}
```

`err: unknown` : en TypeScript, ce qu'attrape un `catch` est de type `unknown` (« on ne sait pas »), d'où le test `isAxiosError` avant de lire quoi que ce soit.
"""),
    L("Les intercepteurs : un réglage pour toutes les requêtes", r"""
Un **intercepteur** est une fonction qu'axios appelle **automatiquement** à chaque requête (avant qu'elle parte) ou à chaque réponse (avant qu'elle arrive à ton code). On l'ajoute une fois, sur le client, avec `use` :

- `api.interceptors.request.use((config) => { …; return config; })` : reçoit la configuration de la requête (URL, en-têtes…), peut la modifier, et **doit la renvoyer**. Usage classique : ajouter le jeton de connexion.
- `api.interceptors.response.use(siOk, siErreur)` : deux fonctions. `siOk(res)` reçoit les réponses 2xx (on renvoie `res` tel quel le plus souvent) ; `siErreur(err)` reçoit les erreurs, et doit **relancer** l'erreur avec `return Promise.reject(err)` pour que le `catch` de l'appelant la reçoive quand même. Usage classique : sur un 401, déconnecter l'utilisateur.

```ts
import { api } from './client';
import { session } from './session';   // { jeton: string | null, deconnecter(): void }

api.interceptors.request.use((config) => {
  if (session.jeton) config.headers.Authorization = `Bearer ${session.jeton}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) session.deconnecter();   // jeton expiré
    return Promise.reject(err);                                 // l'appelant reçoit quand même l'erreur
  },
);
```

Sans intercepteur, il faudrait passer `headers: { Authorization: ... }` à chaque appel, et tester le 401 dans chaque écran. Avec, c'est écrit une fois.
"""),
    L("Avec React Query : la `queryFn`, c'est ta fonction axios", r"""
Pour finir, voici comment tes fonctions se branchent sur React Query (vu en détail dans le module TanStack Query). On passe la fonction en `queryFn` (pour lire) ou en `mutationFn` (pour écrire) :

```ts
useQuery({ queryKey: ['livres', q], queryFn: () => getLivres(q) });
useMutation({ mutationFn: ({ id, date }) => emprunter(id, date) });
```

Ce qui se passe : React Query appelle `getLivres(q)`, qui renvoie `res.data` ; ces données deviennent `data` dans le composant. Si axios lève une erreur (4xx/5xx), React Query la range dans `error`, et tu l'affiches avec `messageErreur(error)`. C'est pour ça que tes fonctions doivent **renvoyer `res.data`** et **laisser passer les erreurs** (pas de `catch` qui les avale) : React Query a besoin des deux.
"""),
  ],
  ["`api = axios.create({ baseURL, headers, timeout })` une seule fois, dans `api/client.ts`.",
   "`get(url, config)` / `delete(url, config)` ; `post(url, corps, config)` / `put` / `patch` : le corps est le 2e argument.",
   "`{ params: { q } }` construit `?q=...` ; un paramètre `undefined` n'apparaît pas.",
   "Les données sont dans `res.data`, déjà en objet ; on renvoie `res.data` depuis chaque fonction.",
   "4xx/5xx → l'appel **lève une erreur** ; `axios.isAxiosError(err)`, puis `err.response?.status` et `err.response.data`.",
   "Pas de `err.response` = aucune réponse (réseau, serveur éteint, timeout).",
   "Intercepteur de requête : modifier puis **renvoyer** `config` ; de réponse : `return Promise.reject(err)` pour relancer."],
  ["Mettre le corps en 3e argument d'un `post` ou l'oublier : `api.post('/emprunts', { params: … })` envoie `params` comme **corps**.",
   "Écrire `res.json()` ou lire `res` au lieu de `res.data`.",
   "Lire `err.status` au lieu de `err.response.status` (c'est `fetch` qui a un `res.status` direct).",
   "Un `catch` qui renvoie `null` dans une fonction de `api/` : React Query croit que tout s'est bien passé et n'affiche jamais l'erreur.",
   "Un intercepteur de requête qui oublie `return config` : la requête part sans configuration.",
   "Un intercepteur d'erreur qui oublie `return Promise.reject(err)` : l'erreur est « avalée » et l'appelant reçoit `undefined`."],
  ["Un seul client `api` (axios.create) pour tout le projet, importé partout.",
   "Le verbe = la méthode ; le corps est le 2e argument de post/put/patch ; `params` pour l'URL.",
   "On renvoie `res.data` ; on laisse passer les erreurs vers l'appelant (ou React Query).",
   "Erreur : `isAxiosError`, puis `response?.status` et `response.data` ; pas de `response` = réseau.",
   "Les intercepteurs règlent le jeton et le 401 à un seul endroit."],
  [CLIENT, F("api/livres.ts", "ts", r"""
import { api } from './client';

export type Livre = { id: number; titre: string; auteur: string; disponible: boolean };
export type Emprunt = { id: number; livreId: number; rendreLe: string };

export async function getLivres(q?: string): Promise<Livre[]> {
  const res = await api.get<Livre[]>('/livres', { params: { q } });
  return res.data;
}

export async function emprunter(livreId: number, rendreLe: string): Promise<Emprunt> {
  const res = await api.post<Emprunt>('/emprunts', { livreId, rendreLe });
  return res.data;
}
"""), F("api/erreurs.ts", "ts", r"""
import axios from 'axios';

export function messageErreur(err: unknown): string {
  if (!axios.isAxiosError(err)) return 'Erreur inattendue';
  if (!err.response) return 'Connexion impossible, réessaie';
  const { status, data } = err.response;
  if (status === 404 || status === 409) return data.error ?? 'Action impossible';
  if (status === 422) return data.violations?.[0]?.title ?? 'Données invalides';
  return `Erreur serveur (${status})`;
}
"""), F("demo.ts", "ts", r"""
import { getLivres, emprunter } from './api/livres';
import { messageErreur } from './api/erreurs';

const livres = await getLivres('dune');
console.log(livres.map((l) => l.titre));      // ['Dune']

try {
  await emprunter(2, '2026-12-01');           // Dune est déjà emprunté → 409
} catch (err) {
  console.log(messageErreur(err));            // 'Déjà emprunté'
}
""")],
  ["`api/client.ts` crée le client une fois ; `livres.ts` et `erreurs.ts` l'importent ou importent axios pour `isAxiosError`.",
   "Chaque fonction de `livres.ts` fait `await api.verbe(...)` puis renvoie `res.data` : l'appelant reçoit directement les livres.",
   "`emprunter` passe l'objet `{ livreId, rendreLe }` en **2e argument** : c'est le corps du `POST`.",
   "Dans `demo.ts`, le 409 fait échouer `await emprunter(...)` : on saute dans le `catch`, où `messageErreur` lit `err.response.data.error`.",
   "Aucune fonction de `api/` n'attrape les erreurs : c'est l'écran (ou React Query) qui décide quoi en faire."],
  [Q("`api.post('/emprunts', { livreId: 3 })` : où est `{ livreId: 3 }` ?", ["dans l'URL", "dans le corps de la requête", "dans les en-têtes", "nulle part"], 1, "Pour post, put et patch, le 2e argument est le corps, envoyé en JSON."),
   Q("Le serveur répond 404 à `await api.get('/livres/999')` :", ["`res.data` vaut `null`", "`res.status` vaut 404", "l'appel lève une erreur, avec `err.response.status === 404`", "axios réessaie"], 2, "Avec axios, tout statut 4xx/5xx fait échouer la promesse."),
   Q("`err.response` vaut `undefined` dans le `catch` :", ["le serveur a répondu 500", "aucune réponse n'est arrivée (réseau, serveur éteint, timeout)", "la réponse était vide (204)", "c'est un 401"], 1, "Une réponse, même d'erreur, remplit `err.response`. Son absence veut dire qu'il n'y en a pas eu."),
   Q("Un intercepteur de réponse fait `(err) => { if (…) deconnecter(); }` sans rien renvoyer :", ["tout va bien", "l'erreur est avalée : l'appelant reçoit `undefined` comme si ça avait marché", "axios plante", "la requête est renvoyée"], 1, "Il faut `return Promise.reject(err)` pour que l'erreur continue jusqu'au `catch` de l'appelant.")],
  [
    TD(1, "Un client et quatre fonctions",
       "Tu écris la couche `api/` d'une bibliothèque : un client, puis une fonction par appel. Le faux serveur répond déjà (les livres 1 à 5, Dune (id 2) est emprunté).",
       ["`client.ts` : exporte `api`, créé avec `axios.create` et `baseURL: '/api'`",
        "`livres.ts` : `getLivres(q?)` → `GET /livres` avec le paramètre `q` (via `params`), renvoie le tableau",
        "`getLivre(id)` → `GET /livres/:id`, renvoie le livre",
        "`emprunter(livreId, rendreLe)` → `POST /emprunts` avec le corps `{ livreId, rendreLe }`, renvoie l'emprunt créé",
        "`supprimerArticle(id)` → `DELETE /articles/:id`, ne renvoie rien",
        "Chaque fonction renvoie `res.data` (pas `res`) et n'attrape aucune erreur"],
       [F("client.ts", "ts", r"""
import axios from 'axios';

// export const api = ...
"""), F("livres.ts", "ts", r"""
import { api } from './client';

export type Livre = { id: number; titre: string; auteur: string; disponible: boolean };
export type Emprunt = { id: number; livreId: number; rendreLe: string };

export async function getLivres(q?: string): Promise<Livre[]> {
  // à toi
  return [];
}

export async function getLivre(id: number): Promise<Livre | undefined> {
  // à toi
  return undefined;
}

export async function emprunter(livreId: number, rendreLe: string): Promise<Emprunt | undefined> {
  // à toi
  return undefined;
}

export async function supprimerArticle(id: number): Promise<void> {
  // à toi
}

getLivres('dune').then((l) => console.log(l));
""")],
       ["`export const api = axios.create({ baseURL: '/api' });`",
        "Avec des paramètres : `api.get<Livre[]>('/livres', { params: { q } })`.",
        "Le corps du POST est le 2e argument : `api.post<Emprunt>('/emprunts', { livreId, rendreLe })`.",
        "`const res = await api.get(...); return res.data;`"],
       [F("client.ts", "ts", r"""
import axios from 'axios';

export const api = axios.create({ baseURL: '/api' });
"""), F("livres.ts", "ts", r"""
import { api } from './client';

export type Livre = { id: number; titre: string; auteur: string; disponible: boolean };
export type Emprunt = { id: number; livreId: number; rendreLe: string };

export async function getLivres(q?: string): Promise<Livre[]> {
  const res = await api.get<Livre[]>('/livres', { params: { q } });
  return res.data;
}

export async function getLivre(id: number): Promise<Livre | undefined> {
  const res = await api.get<Livre>(`/livres/${id}`);
  return res.data;
}

export async function emprunter(livreId: number, rendreLe: string): Promise<Emprunt | undefined> {
  const res = await api.post<Emprunt>('/emprunts', { livreId, rendreLe });
  return res.data;
}

export async function supprimerArticle(id: number): Promise<void> {
  await api.delete(`/articles/${id}`);
}

getLivres('dune').then((l) => console.log(l));
""")],
       ["`getLivres('dune')` renvoie seulement Dune", "Le POST crée vraiment l'emprunt côté serveur", "Un 404 n'est pas transformé en `undefined`"],
       run=RUN("js", entry="livres.ts", api=LIB_API, tests=r"""
const { getLivres, getLivre, emprunter, supprimerArticle } = require('./livres');
const { api } = require('./client');
assert(api && typeof api.get === 'function', 'client.ts exporte api (axios.create)');
await tick(400);
window.__db.calls.length = 0;
const tous = await getLivres();
assert(Array.isArray(tous) && tous.length === 5, 'getLivres() renvoie les 5 livres (res.data, pas res)');
const d = await getLivres('dune');
assert(Array.isArray(d) && d.length === 1 && d[0].titre === 'Dune', "getLivres('dune') filtre grâce au paramètre q");
const l = await getLivre(3);
assert(l && l.titre === 'Fondation', 'getLivre(3) renvoie Fondation');
let leve = false; try { await getLivre(999); } catch (e) { leve = !!(e && e.response && e.response.status === 404); }
assert(leve, "getLivre(999) laisse passer l'erreur 404 (pas de catch)");
const e = await emprunter(4, '2026-12-01');
assert(e && e.livreId === 4 && e.rendreLe === '2026-12-01', "emprunter renvoie l'emprunt créé");
assert.equal(window.__db.livres.find((x) => x.id === 4).disponible, false, 'Le serveur a reçu le corps { livreId, rendreLe }');
await supprimerArticle(2);
assert(!window.__db.articles.some((a) => a.id === 2), 'supprimerArticle(2) envoie DELETE /api/articles/2');
""")),
    TD(2, "Transformer chaque erreur en message",
       "L'écran d'emprunt doit afficher un message compréhensible quel que soit le problème. Tu écris la fonction de traduction, puis une fonction qui l'utilise.",
       ["`messageErreur(err)` : si ce n'est pas une erreur axios → `'Erreur inattendue'`",
        "Erreur axios **sans** `response` → `'Connexion impossible, réessaie'`",
        "404 ou 409 → le champ `error` du corps (`{ error: 'Déjà emprunté' }`)",
        "422 → le `title` de la première violation (`data.violations[0].title`)",
        "Autre statut → `'Erreur serveur (500)'` avec le vrai statut",
        "`tenterEmprunt(livreId, rendreLe)` : appelle `emprunter` ; succès → `{ ok: true, message: 'Emprunt enregistré' }`, erreur → `{ ok: false, message: messageErreur(err) }`"],
       [F("client.ts", "ts", r"""
import axios from 'axios';

export const api = axios.create({ baseURL: '/api' });
"""), F("livres.ts", "ts", r"""
import { api } from './client';

export async function emprunter(livreId: number, rendreLe: string) {
  const res = await api.post('/emprunts', { livreId, rendreLe });
  return res.data;
}
"""), F("erreurs.ts", "ts", r"""
import axios from 'axios';
import { emprunter } from './livres';

export function messageErreur(err: unknown): string {
  // à toi
  return '';
}

export async function tenterEmprunt(livreId: number, rendreLe: string): Promise<{ ok: boolean; message: string }> {
  // à toi
  return { ok: false, message: '' };
}

tenterEmprunt(2, '2026-12-01').then((r) => console.log(r));
""")],
       ["Commence par les deux cas sans statut : `if (!axios.isAxiosError(err)) …` puis `if (!err.response) …`.",
        "`const { status, data } = err.response;` évite de répéter `err.response`.",
        "`data.violations?.[0]?.title` ne plante pas si `violations` manque.",
        "Dans `tenterEmprunt`, le `try` contient `await emprunter(...)` ; le `catch (err)` renvoie le message."],
       [F("erreurs.ts", "ts", r"""
import axios from 'axios';
import { emprunter } from './livres';

export function messageErreur(err: unknown): string {
  if (!axios.isAxiosError(err)) return 'Erreur inattendue';
  if (!err.response) return 'Connexion impossible, réessaie';
  const { status, data } = err.response;
  if (status === 404 || status === 409) return data.error;
  if (status === 422) return data.violations?.[0]?.title ?? 'Données invalides';
  return `Erreur serveur (${status})`;
}

export async function tenterEmprunt(livreId: number, rendreLe: string): Promise<{ ok: boolean; message: string }> {
  try {
    await emprunter(livreId, rendreLe);
    return { ok: true, message: 'Emprunt enregistré' };
  } catch (err) {
    return { ok: false, message: messageErreur(err) };
  }
}

tenterEmprunt(2, '2026-12-01').then((r) => console.log(r));
""")],
       ["Dune (déjà emprunté) → « Déjà emprunté »", "Une date vide → le message de validation du serveur", "Une erreur réseau → « Connexion impossible »"],
       run=RUN("js", entry="erreurs.ts", api=LIB_API, tests=r"""
const { messageErreur, tenterEmprunt } = require('./erreurs');
await tick(400);
assert.equal(messageErreur(new Error('oups')), 'Erreur inattendue', 'Erreur non axios → « Erreur inattendue »');
assert.equal(messageErreur({ isAxiosError: true, message: 'Network Error' }), 'Connexion impossible, réessaie', 'Pas de response → « Connexion impossible, réessaie »');
assert.equal(messageErreur({ isAxiosError: true, response: { status: 503, data: {} } }), 'Erreur serveur (503)', '503 → « Erreur serveur (503) »');
const r1 = await tenterEmprunt(2, '2026-12-01');
assert(r1.ok === false && r1.message === 'Déjà emprunté', '409 → le champ error : « Déjà emprunté »');
const r2 = await tenterEmprunt(999, '2026-12-01');
assert(r2.ok === false && r2.message === 'Livre introuvable', '404 → « Livre introuvable »');
const r3 = await tenterEmprunt(5, '');
assert(r3.ok === false && /ne doit pas être vide/.test(r3.message), '422 → le title de la première violation');
const r4 = await tenterEmprunt(1, '2026-12-01');
assert(r4.ok === true && r4.message === 'Emprunt enregistré', 'Succès → { ok: true, message: « Emprunt enregistré » }');
""")),
    TD(3, "Le jeton et le 401 avec des intercepteurs",
       "La route `GET /api/me` (« qui suis-je ? ») exige l'en-tête `Authorization: Bearer secret-123`, sinon elle répond 401. Plutôt que d'ajouter l'en-tête à chaque appel, tu branches deux intercepteurs sur le client.",
       ["`session.ts` est fourni : `session.jeton` (texte ou `null`) et `session.deconnecter()` (remet le jeton à `null` et compte les déconnexions)",
        "Intercepteur de **requête** : si `session.jeton` existe, ajoute `Authorization: Bearer <jeton>` ; renvoie toujours `config`",
        "Intercepteur de **réponse** : laisse passer les réponses ; sur une erreur 401, appelle `session.deconnecter()` ; dans tous les cas, relance l'erreur",
        "`getMe()` → `GET /me`, renvoie `res.data`"],
       [F("session.ts", "ts", r"""
// Fourni : la session de l'utilisatrice (dans une vraie appli, lue depuis le stockage du navigateur).
export const session = {
  jeton: null as string | null,
  deconnexions: 0,
  deconnecter() { this.jeton = null; this.deconnexions++; },
};
"""), F("client.ts", "ts", r"""
import axios from 'axios';
import { session } from './session';

export const api = axios.create({ baseURL: '/api' });

// 1. intercepteur de requête : le jeton

// 2. intercepteur de réponse : le 401

export async function getMe() {
  const res = await api.get('/me');
  return res.data;
}
""")],
       ["`api.interceptors.request.use((config) => { … return config; });`",
        "`config.headers.Authorization = `Bearer ${session.jeton}`;`",
        "`api.interceptors.response.use((res) => res, (err) => { … return Promise.reject(err); });`",
        "Le statut est dans `err.response?.status` (le `?.` protège des erreurs sans réponse)."],
       [F("client.ts", "ts", r"""
import axios from 'axios';
import { session } from './session';

export const api = axios.create({ baseURL: '/api' });

api.interceptors.request.use((config) => {
  if (session.jeton) config.headers.Authorization = `Bearer ${session.jeton}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) session.deconnecter();
    return Promise.reject(err);
  },
);

export async function getMe() {
  const res = await api.get('/me');
  return res.data;
}
""")],
       ["Avec le bon jeton, `getMe()` renvoie le profil", "Un mauvais jeton déconnecte la session", "L'appelant reçoit quand même l'erreur 401"],
       run=RUN("js", entry="client.ts", api=LIB_API, tests=r"""
const { getMe } = require('./client');
const { session } = require('./session');
await tick(300);
session.jeton = 'secret-123';
const me = await getMe();
assert(me && me.pseudo === 'fausatu', 'Avec le jeton, GET /api/me répond le profil (en-tête Authorization ajouté)');
assert.equal(session.deconnexions, 0, "Une réponse 200 ne déconnecte pas");
session.jeton = 'perime';
let statut = null; try { await getMe(); } catch (e) { statut = e && e.response ? e.response.status : 'autre'; }
assert.equal(statut, 401, "L'appelant reçoit l'erreur 401 (Promise.reject)");
assert.equal(session.deconnexions, 1, 'Sur un 401, session.deconnecter() est appelé');
assert.equal(session.jeton, null, 'Le jeton est effacé');
let statut2 = null; try { await getMe(); } catch (e) { statut2 = e && e.response ? e.response.status : 'autre'; }
assert.equal(statut2, 401, 'Sans jeton : pas d\'en-tête, 401');
""")),
  ])

MODULES = [MOD]

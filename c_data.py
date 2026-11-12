from common import V2, P, L, D, N, E, LANE, F, TD, RUN
from c_data_v1 import MODULES as V1

v1 = {m["id"]: m for m in V1}

# Faux serveur partagé par les exercices : une petite bibliothèque.
LIB_API = r"""
const db = window.__db = {
  livres: [
    { id: 1, titre: 'Terremer', auteur: 'Ursula K. Le Guin', disponible: true },
    { id: 2, titre: 'Dune', auteur: 'Frank Herbert', disponible: false },
    { id: 3, titre: 'Fondation', auteur: 'Isaac Asimov', disponible: true },
    { id: 4, titre: 'Hypérion', auteur: 'Dan Simmons', disponible: true },
    { id: 5, titre: 'Le Problème à trois corps', auteur: 'Liu Cixin', disponible: true },
  ],
  articles: [
    { id: 1, titre: 'Bienvenue sur le blog', auteur: 'Ana' },
    { id: 2, titre: 'Les DTO expliqués', auteur: 'Léo' },
  ],
  emprunts: [],
  nextId: 100,
  calls: [],
};
const log = (k) => db.calls.push(k);
__api["GET /api/livres"] = (p) => {
  log('GET /api/livres');
  let l = db.livres;
  if (p.q) l = l.filter((x) => x.titre.toLowerCase().includes(String(p.q).toLowerCase()));
  if (p.page) {
    const per = Number(p.parPage || 2), page = Number(p.page);
    return { items: l.slice((page - 1) * per, page * per), total: l.length, page, pages: Math.max(1, Math.ceil(l.length / per)) };
  }
  return l;
};
__api["GET /api/livres/:id"] = (p) => { log('GET /api/livres/' + p.id); return db.livres.find((l) => l.id == p.id) || [404, { error: 'Livre introuvable' }]; };
__api["POST /api/emprunts"] = (p, b) => {
  log('POST /api/emprunts');
  b = b || {};
  const l = db.livres.find((x) => x.id == b.livreId);
  if (!l) return [404, { error: 'Livre introuvable' }];
  if (!b.rendreLe) return [422, { violations: [{ propertyPath: 'rendreLe', title: 'Cette valeur ne doit pas être vide.' }] }];
  if (!l.disponible) return [409, { code: 'LIVRE_INDISPONIBLE', error: 'Déjà emprunté' }];
  l.disponible = false;
  const e = { id: ++db.nextId, livreId: l.id, rendreLe: b.rendreLe };
  db.emprunts.push(e);
  return [201, e];
};
__api["GET /api/articles"] = () => { log('GET /api/articles'); return db.articles; };
__api["POST /api/articles"] = (p, b) => {
  log('POST /api/articles');
  b = b || {};
  const t = String(b.titre || '').trim();
  if (t.length < 5) return [422, { violations: [{ propertyPath: 'titre', title: 'Le titre doit faire au moins 5 caractères.' }] }];
  const a = { id: ++db.nextId, titre: t, auteur: b.auteur || 'Moi' };
  db.articles.unshift(a);
  return [201, a];
};
__api["PATCH /api/articles/:id"] = (p, b) => {
  log('PATCH /api/articles/' + p.id);
  const a = db.articles.find((x) => x.id == p.id);
  if (!a) return [404, { error: 'Article introuvable' }];
  if (b && b.titre !== undefined && String(b.titre).trim().length < 5) return [422, { violations: [{ propertyPath: 'titre', title: 'Le titre doit faire au moins 5 caractères.' }] }];
  Object.assign(a, b || {});
  return a;
};
__api["DELETE /api/articles/:id"] = (p) => {
  log('DELETE /api/articles/' + p.id);
  const i = db.articles.findIndex((x) => x.id == p.id);
  if (i < 0) return [404, { error: 'Article introuvable' }];
  db.articles.splice(i, 1);
  return [204, null];
};
__api["GET /api/me"] = (p, b, headers) => {
  log('GET /api/me');
  const h = headers.Authorization || headers.authorization;
  if (h !== 'Bearer secret-123') return [401, { error: 'Non connecté' }];
  return { id: 7, pseudo: 'fausatu' };
};
"""

# ---------------------------------------------------------------- HTTP
http = V2(v1["data-http"], td1=dict(path="observations.txt"),
  prereq=[
    P("Client / serveur", "Le **client** est le programme qui demande (ton navigateur, ton appli React). Le **serveur** est le programme qui répond (Symfony, Next.js…), souvent sur une autre machine."),
    P("URL", "L'adresse d'une ressource : `https://monsite.fr/api/livres?page=2`. On y trouve le domaine (`monsite.fr`), le chemin (`/api/livres`) et la *query string* (`?page=2`), des paramètres optionnels."),
    P("JSON", "Un format texte pour échanger des données : `{\"id\": 1, \"titre\": \"Dune\"}`. Ressemble à un objet JavaScript, mais c'est du **texte** : il faut le convertir (`JSON.parse`) pour l'utiliser comme objet."),
    P("Asynchrone", "Une opération qui se termine **plus tard**. Le code ne s'arrête pas pour l'attendre : il continue, et on dit quoi faire « quand la réponse arrivera »."),
    P("Promesse (Promise)", "L'objet JavaScript qui représente un résultat futur. On attend son résultat avec `await` (dans une fonction `async`) ou avec `.then(...)`."),
    P("En-tête (header)", "Une information attachée à une requête ou une réponse, sous forme `Nom: valeur`. Exemples : `Content-Type: application/json` (« le corps est du JSON »), `Authorization: Bearer xxx` (« voici ma preuve d'identité »)."),
  ],
  diagram=D(
    nodes=[
      N("react", 0, 0, "React", "clic → api.post(...)", color="accent"),
      N("req", 1, 0, "Requête", "POST /api/emprunts\n{livreId: 3}", kind="doc"),
      N("srv", 2, 0, "Serveur", "valide, enregistre"),
      N("db", 3, 0, "Base", "table emprunt", kind="db", color="muted"),
      N("rep", 2, 1, "Serveur répond", "statut + JSON", kind="pill"),
      N("res", 1, 1, "Réponse", "201 Created\n{id: 101, ...}", kind="doc", color="good"),
      N("ecran", 0, 1, "Écran", "mis à jour", kind="file", color="good"),
    ],
    edges=[E("react", "req"), E("req", "srv", "HTTP"), E("srv", "db", "INSERT"), E("srv", "rep"), E("rep", "res", color="good"), E("res", "ecran", "setState", color="good")],
    lanes=[LANE("Navigateur", 0, 1, "accent"), LANE("Serveur", 2, 3, "tc")],
    caption="Chaque échange avec un serveur, c'est une requête (méthode, URL, corps) et une réponse (statut, corps). Rien de plus."),
  lessons=[
    L("Pourquoi le front doit-il « demander » les données ?", r"""
Ton application React tourne **dans le navigateur** de l'utilisateur. Les données (les livres, les articles, les comptes), elles, sont stockées **sur le serveur**, dans une base de données. Le navigateur n'a pas accès à cette base : il serait impensable que n'importe quel visiteur puisse lire ou modifier directement la base.

La seule façon d'obtenir ou de modifier des données, c'est donc de **demander au serveur**, qui décide de répondre ou non. Cette conversation suit un protocole très simple, **HTTP** : le client envoie une **requête**, le serveur renvoie une **réponse**. Une requête = une réponse. Le serveur ne parle jamais en premier.

Quand tu fais `fetch(...)` ou `axios.get(...)`, tu ne fais rien d'autre qu'**écrire une requête HTTP** depuis JavaScript.
"""),
    L("Anatomie d'une requête", r"""
Une requête contient :

- Une **méthode** (le verbe) : ce que tu veux faire.
- Une **URL** : sur quoi.
- Des **en-têtes** : des informations annexes (format du corps, authentification…).
- Parfois un **corps** (*body*) : les données envoyées, en JSON.

```
POST /api/emprunts HTTP/1.1
Host: bibliotheque.fr
Content-Type: application/json
Authorization: Bearer secret-123

{"livreId": 3, "rendreLe": "2026-12-01"}
```

Les méthodes à connaître :

- **GET** : lire. Pas de corps. Les filtres passent dans l'URL : `GET /api/livres?q=dune&page=2`.
- **POST** : créer quelque chose (un emprunt, un article, un compte).
- **PUT** : remplacer entièrement une ressource. **PATCH** : en modifier une partie.
- **DELETE** : supprimer.

Toutes les requêtes qui **modifient** des données (POST, PUT, PATCH, DELETE) s'appellent des **mutations**. C'est juste un mot pour dire « écriture ». Une requête GET ne doit jamais rien modifier : on doit pouvoir la répéter sans conséquence.
"""),
    L("Anatomie d'une réponse : le statut d'abord", r"""
La réponse contient un **code de statut** (un nombre à 3 chiffres), des en-têtes et souvent un corps JSON.

```
HTTP/1.1 201 Created
Content-Type: application/json

{"id": 101, "livreId": 3, "rendreLe": "2026-12-01"}
```

Le premier chiffre du statut dit qui a raison :

- **2xx : succès.** `200 OK` (voici les données), `201 Created` (créé, voici l'objet), `204 No Content` (fait, rien à renvoyer, typique d'un DELETE).
- **4xx : le client s'est trompé.** `400` requête mal formée, `401` pas connecté, `403` connecté mais pas le droit, `404` introuvable, `409` conflit avec l'état actuel (livre déjà emprunté), `422` données invalides (titre trop court).
- **5xx : le serveur a planté.** `500` : bug côté serveur. Ce n'est pas la faute du client.

Réflexe à prendre : **toujours regarder le statut** avant le corps. Une réponse 404 contient souvent un corps JSON (`{"error": "Livre introuvable"}`) : ce ne sont pas des données, c'est une erreur.
"""),
    L("Asynchrone : la réponse arrive plus tard", r"""
Une requête met du temps : quelques millisecondes à plusieurs secondes. JavaScript ne bloque pas la page pendant ce temps : il **lance** la requête et continue. La réponse arrive plus tard, dans une **promesse**.

```js
console.log('1. avant');
fetch('/api/livres').then(() => console.log('3. réponse reçue'));
console.log('2. après');
// Affiche 1, 2, puis 3
```

Avec `async` / `await`, le code se lit de haut en bas, comme s'il attendait :

```js
async function charger() {
  console.log('1. avant');
  const res = await fetch('/api/livres');   // "attends ici que la réponse arrive"
  console.log('2. réponse reçue', res.status);
}
```

Conséquence directe pour l'interface : entre le moment où tu demandes et celui où tu reçois, ton écran doit afficher **quelque chose** : un état de **chargement**. Puis, selon la réponse, un état **succès** (les données) ou **erreur** (un message). Ces trois états sont la base de tous les modules suivants.
"""),
    L("L'outil indispensable : l'onglet Réseau", r"""
Dans ton navigateur, **F12 → onglet Réseau (Network) → filtre Fetch/XHR**. Chaque requête que fait la page y apparaît. En cliquant dessus :

- **Headers** : la méthode, l'URL, le statut, les en-têtes.
- **Payload** : le corps envoyé (pour un POST).
- **Response** / **Preview** : ce que le serveur a répondu.

Quand quelque chose ne marche pas, c'est là que tu regardes **en premier**. Il répond immédiatement à la question « le problème est-il avant ou après le serveur ? » :

- Pas de requête du tout → le problème est dans ton code front (le `fetch` n'est jamais appelé).
- Requête en 4xx → ce que tu envoies est faux (URL, corps, authentification).
- Requête en 5xx → bug côté serveur.
- Requête en 200 avec les bonnes données, mais l'écran ne change pas → le problème est dans ton composant (state pas mis à jour).

Dans les exercices de ce parcours, le panneau « Console » sous l'aperçu affiche aussi chaque requête (`GET /api/livres → 200`), comme un mini onglet Réseau.
"""),
  ],
  recap=[
    "Le front n'a pas accès à la base : il **demande** au serveur via HTTP. Une requête → une réponse.",
    "Requête = méthode + URL + en-têtes + corps éventuel. GET lit ; POST/PUT/PATCH/DELETE sont des **mutations**.",
    "Réponse = **statut** + corps. 2xx succès, 4xx erreur du client (401, 403, 404, 409, 422), 5xx bug serveur.",
    "La réponse arrive plus tard (asynchrone) : l'écran passe par **chargement → succès ou erreur**.",
    "F12 → Réseau te dit toujours si le problème est avant ou après le serveur.",
  ],
  example=[F("requetes.js", "javascript", r"""
// 1. Lire : GET, pas de corps
const res = await fetch('/api/livres/3');
console.log(res.status);          // 200
const livre = await res.json();   // le corps JSON -> objet JS
console.log(livre.titre);         // "Fondation"

// 2. Créer : POST avec un corps JSON
const res2 = await fetch('/api/emprunts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ livreId: 3, rendreLe: '2026-12-01' }),
});
console.log(res2.status);         // 201

// 3. Le même POST sur un livre déjà emprunté
const res3 = await fetch('/api/emprunts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ livreId: 2, rendreLe: '2026-12-01' }),
});
console.log(res3.status);         // 409
console.log(await res3.json());   // { code: "LIVRE_INDISPONIBLE", error: "Déjà emprunté" }
"""), F("ce-qui-passe-sur-le-reseau.txt", "plaintext", r"""
> GET /api/livres/3
< 200 OK
< {"id":3,"titre":"Fondation","auteur":"Isaac Asimov","disponible":true}

> POST /api/emprunts
> Content-Type: application/json
> {"livreId":3,"rendreLe":"2026-12-01"}
< 201 Created
< {"id":101,"livreId":3,"rendreLe":"2026-12-01"}

> POST /api/emprunts
> {"livreId":2,"rendreLe":"2026-12-01"}
< 409 Conflict
< {"code":"LIVRE_INDISPONIBLE","error":"Déjà emprunté"}
""")],
  notes=["Le code JS (`requetes.js`) et ce qui circule vraiment sur le réseau (le fichier `.txt`) : c'est la même chose vue de deux côtés.",
         "`JSON.stringify` transforme l'objet en texte pour l'envoyer ; `res.json()` fait l'inverse à la réception.",
         "Le 3e appel est identique au 2e sauf le livre : le serveur répond 409 car l'état actuel (livre déjà emprunté) empêche l'action.",
         "Chaque `await` attend une réponse réseau : sans lui, tu manipulerais une promesse, pas les données."],
  tds=[
    TD(2, "Interpréter les réponses du serveur",
       "Tu écris les deux fonctions qu'on retrouve dans toute appli : une qui **traduit un statut HTTP** en message pour l'utilisateur, et une qui **lit un livre** en gérant le cas « introuvable ». L'API simulée de la bibliothèque répond comme un vrai serveur.",
       ["`messageStatut(status)` renvoie : `'OK'` pour 200 à 299, `'Connecte-toi'` pour 401, `'Accès refusé'` pour 403, `'Introuvable'` pour 404, `'Conflit'` pour 409, `'Données invalides'` pour 422, `'Erreur serveur'` pour 500 et plus, `'Erreur'` sinon",
        "`chargerLivre(id)` (async) fait `fetch('/api/livres/' + id)`",
        "Si la réponse est OK, renvoie l'objet livre ; sinon renvoie `null`",
        "Exporte les deux fonctions"],
       [F("api.js", "javascript", r"""
export function messageStatut(status) {
  // à toi
}

export async function chargerLivre(id) {
  // à toi
}

// Essai : regarde la console
chargerLivre(3).then((l) => console.log('livre 3 :', l));
chargerLivre(999).then((l) => console.log('livre 999 :', l));
""")],
       ["Teste les plages d'abord : `if (status >= 200 && status < 300) return 'OK';`",
        "`res.ok` vaut `true` pour les statuts 2xx : `if (!res.ok) return null;`",
        "Le corps se lit avec `await res.json()`."],
       [F("api.js", "javascript", r"""
export function messageStatut(status) {
  if (status >= 200 && status < 300) return 'OK';
  if (status === 401) return 'Connecte-toi';
  if (status === 403) return 'Accès refusé';
  if (status === 404) return 'Introuvable';
  if (status === 409) return 'Conflit';
  if (status === 422) return 'Données invalides';
  if (status >= 500) return 'Erreur serveur';
  return 'Erreur';
}

export async function chargerLivre(id) {
  const res = await fetch('/api/livres/' + id);
  if (!res.ok) return null;
  return await res.json();
}

chargerLivre(3).then((l) => console.log('livre 3 :', l));
chargerLivre(999).then((l) => console.log('livre 999 :', l));
""")],
       ["`messageStatut(201)` renvoie `'OK'`",
        "`chargerLivre(999)` renvoie `null` sans planter"],
       run=RUN("js", entry="api.js", api=LIB_API, tests=r"""
const { messageStatut, chargerLivre } = require('./api');
assert.equal(messageStatut(200), 'OK', '200 → OK');
assert.equal(messageStatut(204), 'OK', '204 → OK');
assert.equal(messageStatut(401), 'Connecte-toi', '401 → Connecte-toi');
assert.equal(messageStatut(404), 'Introuvable', '404 → Introuvable');
assert.equal(messageStatut(409), 'Conflit', '409 → Conflit');
assert.equal(messageStatut(422), 'Données invalides', '422 → Données invalides');
assert.equal(messageStatut(503), 'Erreur serveur', '503 → Erreur serveur');
assert.equal(messageStatut(418), 'Erreur', '418 → Erreur');
const l = await chargerLivre(3);
assert(l && l.titre === 'Fondation', 'chargerLivre(3) renvoie Fondation');
const n = await chargerLivre(999);
assert.equal(n, null, 'chargerLivre(999) renvoie null');
""")),
    TD(3, "Un emprunt de A à Z, avec fetch uniquement",
       "Tu enchaînes plusieurs requêtes dépendantes, exactement comme le ferait une appli : **lire** le livre, **vérifier** qu'il est disponible, **envoyer** la mutation avec un corps JSON et les bons en-têtes, puis **interpréter** le statut. Pas d'axios ici : tout à la main, pour voir chaque étape.",
       ["`emprunter(livreId, rendreLe)` (async) commence par `GET /api/livres/:id` ; si 404 → renvoie `{ ok: false, message: 'Livre introuvable' }`",
        "Si le livre n'est pas disponible → renvoie `{ ok: false, message: 'Déjà emprunté' }` **sans envoyer de POST**",
        "Sinon, `POST /api/emprunts` avec `Content-Type: application/json` et le corps `{ livreId, rendreLe }`",
        "201 → `{ ok: true, emprunt }` (l'objet renvoyé) ; 422 → `{ ok: false, message }` avec le `title` de la première violation ; autre → `{ ok: false, message: 'Erreur ' + status }`"],
       [F("emprunt.js", "javascript", r"""
export async function emprunter(livreId, rendreLe) {
  // 1. lire le livre
  // 2. vérifier la disponibilité
  // 3. envoyer le POST
  // 4. interpréter la réponse
}

emprunter(3, '2026-12-01').then((r) => console.log(r));
""")],
       ["Corps : `body: JSON.stringify({ livreId, rendreLe })`, avec `method: 'POST'` et `headers: { 'Content-Type': 'application/json' }`.",
        "Le corps d'une réponse 422 contient `violations` : `(await res.json()).violations[0].title`.",
        "Teste le statut 201 avec `res.status === 201`."],
       [F("emprunt.js", "javascript", r"""
export async function emprunter(livreId, rendreLe) {
  const resLivre = await fetch('/api/livres/' + livreId);
  if (resLivre.status === 404) return { ok: false, message: 'Livre introuvable' };
  const livre = await resLivre.json();
  if (!livre.disponible) return { ok: false, message: 'Déjà emprunté' };

  const res = await fetch('/api/emprunts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ livreId, rendreLe }),
  });
  if (res.status === 201) return { ok: true, emprunt: await res.json() };
  if (res.status === 422) {
    const data = await res.json();
    return { ok: false, message: data.violations[0].title };
  }
  return { ok: false, message: 'Erreur ' + res.status };
}

emprunter(3, '2026-12-01').then((r) => console.log(r));
""")],
       ["Emprunter Dune (id 2) ne déclenche aucun POST",
        "Une date vide renvoie le message de validation du serveur"],
       run=RUN("js", entry="emprunt.js", api=LIB_API, tests=r"""
const { emprunter } = require('./emprunt');
await tick(400);
window.__db.calls.length = 0;
const r1 = await emprunter(4, '2026-12-01');
assert(r1 && r1.ok === true && r1.emprunt && r1.emprunt.livreId === 4, 'Livre 4 : emprunt créé (ok + emprunt)');
assert.equal(window.__db.livres.find((l) => l.id === 4).disponible, false, 'Le serveur a bien enregistré l\'emprunt');
window.__db.calls.length = 0;
const r2 = await emprunter(2, '2026-12-01');
assert(r2 && r2.ok === false && r2.message === 'Déjà emprunté', 'Dune : message « Déjà emprunté »');
assert(!window.__db.calls.includes('POST /api/emprunts'), 'Dune : aucun POST envoyé');
const r3 = await emprunter(999, '2026-12-01');
assert(r3 && r3.message === 'Livre introuvable', 'Livre 999 : « Livre introuvable »');
const r4 = await emprunter(5, '');
assert(r4 && r4.ok === false && /ne doit pas être vide/.test(r4.message), 'Date vide : message de validation du serveur (422)');
""")),
  ])

# ---------------------------------------------------------------- GET
get = V2(v1["data-get"],
  prereq=[
    P("`useState`", "La mémoire d'un composant : `const [livres, setLivres] = useState([])`. Appeler `setLivres` redessine le composant avec la nouvelle valeur (parcours React)."),
    P("`useEffect`", "Exécute du code **après** l'affichage. Avec `[]` en dépendances : une seule fois, au montage. C'est là qu'on lance un chargement (parcours React)."),
    P("axios", "Une librairie (`npm i axios`) qui simplifie les requêtes : conversion JSON automatique, erreur levée sur 4xx/5xx, configuration commune (`baseURL`)."),
    P("`async` / `await`", "`await` attend le résultat d'une promesse ; il n'est autorisé que dans une fonction marquée `async`."),
    P("`try / catch / finally`", "`try` : le code qui peut échouer. `catch (err)` : ce qu'on fait si une erreur est levée. `finally` : exécuté dans tous les cas (parfait pour « fin du chargement »)."),
    P("Générique TypeScript", "`api.get<Livre[]>(...)` indique le type des données attendues : `res.data` sera typé `Livre[]` et l'éditeur t'aidera."),
  ],
  diagram=D(
    nodes=[
      N("r1", 0, 0, "1er rendu", "loading = true", kind="doc"),
      N("eff", 1, 0, "useEffect", "api.get('/livres')", color="accent"),
      N("srv", 2, 0, "Serveur", "200 + [livres]", color="muted"),
      N("set", 2, 1, "setLivres(res.data)", "setLoading(false)", color="good"),
      N("r2", 1, 1, "2e rendu", "la liste s'affiche", kind="doc", color="good"),
      N("err", 2, 2, "catch", "setError('…')", color="bad"),
      N("r3", 1, 2, "2e rendu", "message d'erreur", kind="doc", color="bad"),
    ],
    edges=[E("r1", "eff", "après affichage"), E("eff", "srv", "requête"), E("srv", "set", "succès", color="good"), E("set", "r2", color="good"), E("srv", "err", dashed=True, color="bad"), E("err", "r3", color="bad")],
    caption="Le composant s'affiche d'abord vide (chargement), lance la requête, puis se redessine avec les données ou avec l'erreur."),
  lessons=[
    L("Le problème : le composant s'affiche avant que les données arrivent", r"""
Un composant React est une fonction qui doit renvoyer du JSX **immédiatement**. Or les données viennent du serveur, **plus tard**. Impossible donc d'écrire :

```tsx
function Catalogue() {
  const livres = await api.get('/livres');   // interdit : un composant n'est pas async
  return <ul>…</ul>;
}
```

La solution se fait en trois temps :

1. Le composant s'affiche une première fois **sans données**, avec `loading = true` (« Chargement… »).
2. **Après** cet affichage, un `useEffect` lance la requête.
3. Quand la réponse arrive, on **range** les données dans le state. Changer le state redessine le composant, qui affiche alors la liste.

Le state sert donc de **boîte aux lettres** entre le monde asynchrone (la requête) et le rendu (le JSX).
"""),
    L("fetch et axios : deux façons d'écrire la même requête", r"""
`fetch` est intégré au navigateur. Il demande deux étapes et une vérification manuelle :

```ts
const res = await fetch('/api/livres');
if (!res.ok) throw new Error('HTTP ' + res.status);   // fetch ne lève PAS d'erreur sur 404 ou 500
const livres = await res.json();                       // il faut décoder le JSON soi-même
```

axios fait ces étapes pour toi :

```ts
const res = await axios.get('/api/livres');   // lève une erreur si 4xx/5xx
const livres = res.data;                       // déjà décodé
```

Les différences qui comptent :

| | fetch | axios |
|---|---|---|
| Données | `await res.json()` | `res.data` |
| Erreur 404/500 | **pas** d'erreur, tester `res.ok` | erreur levée → `catch` |
| Envoyer du JSON | `JSON.stringify` + en-tête à la main | objet passé directement |
| Configuration commune | à toi de la faire | `axios.create({ baseURL })` |

Dans un vrai projet on crée une **instance** configurée une fois :

```ts
// api/client.ts
export const api = axios.create({ baseURL: '/api' });
// partout ailleurs :
api.get('/livres')   // → GET /api/livres
```
"""),
    L("Les trois états : chargement, erreur, données", r"""
Toute donnée chargée a trois états possibles, et ton écran doit gérer les trois :

```tsx
const [livres, setLivres] = useState<Livre[]>([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);

if (loading) return <p>Chargement…</p>;
if (error) return <p role="alert">{error}</p>;
return <ul>{livres.map(…)}</ul>;
```

Le chargement lui-même s'écrit avec `try / catch / finally` :

```tsx
useEffect(() => {
  async function charger() {
    try {
      const res = await api.get<Livre[]>('/livres');
      setLivres(res.data);
    } catch (err) {
      setError('Impossible de charger les livres');
    } finally {
      setLoading(false);          // dans tous les cas, on n'est plus en chargement
    }
  }
  charger();
}, []);
```

Remarque : la fonction passée à `useEffect` ne peut pas être `async` elle-même (elle doit pouvoir renvoyer une fonction de nettoyage). On déclare donc une fonction `async` **à l'intérieur** et on l'appelle.

N'oublie pas le **4e cas** souvent oublié : la requête a réussi mais la liste est **vide**. Un écran blanc fait croire à un bug ; affiche « Aucun livre ».
"""),
    L("Recharger, filtrer : les dépendances de l'effet", r"""
Le tableau de dépendances décide **quand** l'effet se relance :

- `[]` : une seule fois, au montage.
- `[q]` : à chaque fois que `q` change. Parfait pour une recherche : on tape, `q` change, la requête repart avec `?q=...`.

```tsx
useEffect(() => {
  setLoading(true);
  api.get('/livres', { params: { q } })    // axios construit ?q=... pour toi
    .then((res) => setLivres(res.data))
    .finally(() => setLoading(false));
}, [q]);
```

Pour un bouton « Recharger », astuce classique : un compteur dans le state, ajouté aux dépendances. Chaque clic l'incrémente, ce qui relance l'effet.

**Le piège des réponses dans le désordre.** Tu tapes « d », puis « du », puis « dun ». Trois requêtes partent. Si la réponse de « d » arrive **après** celle de « dun », la liste affiche les mauvais résultats. La parade : annuler l'ancienne requête dans le **cleanup** de l'effet.

```tsx
useEffect(() => {
  const controller = new AbortController();
  api.get('/livres', { params: { q }, signal: controller.signal })
    .then((res) => setLivres(res.data))
    .catch((err) => { if (!axios.isCancel(err)) setError('Erreur'); });
  return () => controller.abort();          // annule la requête précédente
}, [q]);
```
"""),
  ],
  recap=[
    "Un composant s'affiche avant les données : on charge dans un `useEffect`, on range le résultat dans le state.",
    "fetch : tester `res.ok` et faire `res.json()`. axios : `res.data`, et les 4xx/5xx arrivent dans `catch`.",
    "Toujours trois états (chargement, erreur, données) + le cas « liste vide ».",
    "`try / catch / finally` : `finally` remet `loading` à `false` dans tous les cas.",
    "Dépendances `[q]` pour relancer quand un filtre change ; `AbortController` dans le cleanup pour les réponses dans le désordre.",
  ],
  example=[F("api/client.ts", "ts", r"""
import axios from 'axios';

// Une seule configuration pour tout le projet
export const api = axios.create({ baseURL: '/api' });
"""), F("types.ts", "ts", r"""
// Le même contrat que le DTO de sortie côté Symfony (LivreListItem)
export type Livre = { id: number; titre: string; auteur: string; disponible: boolean };
"""), F("Catalogue.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import axios from 'axios';
import { api } from './api/client';
import type { Livre } from './types';

export default function Catalogue() {
  const [livres, setLivres] = useState<Livre[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function charger() {
      try {
        const res = await api.get<Livre[]>('/livres', { signal: controller.signal });
        setLivres(res.data);
      } catch (err) {
        if (axios.isCancel(err)) return;               // annulée : on ignore
        setError('Impossible de charger les livres');
      } finally {
        setLoading(false);
      }
    }
    charger();

    return () => controller.abort();
  }, []);

  if (loading) return <p>Chargement…</p>;
  if (error) return <p role="alert">{error}</p>;
  if (livres.length === 0) return <p>Aucun livre</p>;

  return (
    <ul>
      {livres.map((l) => (
        <li key={l.id}>{l.titre} — {l.auteur}</li>
      ))}
    </ul>
  );
}
""")],
  notes=["`api/client.ts` : l'URL de base est écrite une seule fois ; `api.get('/livres')` appelle `/api/livres`.",
         "`types.ts` reflète le JSON renvoyé par le serveur : `res.data` est typé `Livre[]`.",
         "Dans `Catalogue.tsx`, la fonction `async` est déclarée **dans** l'effet puis appelée.",
         "Les quatre `return` gèrent dans l'ordre : chargement, erreur, liste vide, données."],
  td1=dict(path="Catalogue.tsx",
    files=[F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });
"""), F("Catalogue.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import axios from 'axios';
import { api } from './api/client';

type Livre = { id: number; titre: string; auteur: string; disponible: boolean };

export default function Catalogue() {
  // à toi : 3 states, un effet qui charge GET /livres, un bouton « Recharger »
  return <p>À compléter</p>;
}
""")],
    solution=[F("Catalogue.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import axios from 'axios';
import { api } from './api/client';

type Livre = { id: number; titre: string; auteur: string; disponible: boolean };

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
""")],
    run=RUN("react", entry="Catalogue.tsx", api=LIB_API, tests=r"""
assert(/Chargement/.test(source('Catalogue.tsx')), 'Un état « Chargement… » est prévu');
await waitFor(() => $$('li').length === 5, 3000);
assert.equal($$('li').length, 5, 'Les 5 livres sont affichés');
assert.includes(text(), 'Terremer', 'Le titre Terremer est affiché');
assert.includes($$('li')[1].textContent, 'emprunté', 'Dune est marqué « emprunté »');
const avant = window.__db.calls.filter((c) => c === 'GET /api/livres').length;
await click(byText('Recharger'));
await waitFor(() => window.__db.calls.filter((c) => c === 'GET /api/livres').length > avant, 2000);
assert(true, 'Le bouton Recharger relance la requête');
await waitFor(() => $$('li').length === 5, 3000);
window.__api['GET /api/livres'] = () => [500, { error: 'boom' }];
await click(byText('Recharger'));
await waitFor(() => $('[role=alert]'), 3000);
assert.includes($('[role=alert]').textContent, 'charger', 'Erreur 500 : message d\'erreur affiché');
""")),
  tds=[
    TD(2, "Recherche en direct",
       "Même mécanique, mais l'effet doit **se relancer** quand l'utilisateur tape dans un champ de recherche. Tu passes le texte en paramètre d'URL et tu gères le cas « aucun résultat ».",
       ["Un `<input>` contrôlé (placeholder « Rechercher ») stocke `q` dans le state",
        "L'effet dépend de `[q]` et appelle `api.get('/livres', { params: { q } })`",
        "Chaque livre s'affiche dans un `<li>` avec son titre",
        "Si la réponse est une liste vide : `<p>Aucun résultat pour « q »</p>`",
        "Annule la requête précédente avec un `AbortController` dans le cleanup"],
       [F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });
"""), F("Recherche.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import axios from 'axios';
import { api } from './api/client';

type Livre = { id: number; titre: string; auteur: string; disponible: boolean };

export default function Recherche() {
  // à toi
  return <p>À compléter</p>;
}
""")],
       ["`params: { q }` produit l'URL `/api/livres?q=...` ; avec `q = ''`, le serveur renvoie tout.",
        "Le message vide doit attendre la fin du chargement : `!loading && livres.length === 0`.",
        "Dans le cleanup : `return () => controller.abort();`, et ignore l'erreur si `axios.isCancel(err)`."],
       [F("Recherche.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import axios from 'axios';
import { api } from './api/client';

type Livre = { id: number; titre: string; auteur: string; disponible: boolean };

export default function Recherche() {
  const [q, setQ] = useState('');
  const [livres, setLivres] = useState<Livre[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    api.get<Livre[]>('/livres', { params: { q }, signal: controller.signal })
      .then((res) => { setLivres(res.data); setLoading(false); })
      .catch((err) => { if (!axios.isCancel(err)) setLoading(false); });
    return () => controller.abort();
  }, [q]);

  return (
    <section>
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Rechercher" />
      {loading && <p>Chargement…</p>}
      {!loading && livres.length === 0 && <p>Aucun résultat pour « {q} »</p>}
      <ul>
        {livres.map((l) => <li key={l.id}>{l.titre}</li>)}
      </ul>
    </section>
  );
}
""")],
       ["Taper « dun » n'affiche que Dune",
        "Taper « zzz » affiche le message « Aucun résultat »"],
       run=RUN("react", entry="Recherche.tsx", api=LIB_API, tests=r"""
await waitFor(() => $$('li').length === 5, 3000);
assert.equal($$('li').length, 5, 'Sans recherche : 5 livres');
await type('input', 'dun');
await waitFor(() => $$('li').length === 1, 3000);
assert.includes($$('li')[0].textContent, 'Dune', '« dun » → seulement Dune');
await type('input', 'zzz');
await waitFor(() => text().includes('Aucun résultat'), 3000);
assert.includes(text(), 'zzz', 'Le message reprend le texte cherché');
assert.equal($$('li').length, 0, 'Plus aucun livre affiché');
const src = source('Recherche.tsx');
assert(/abort\(\)/.test(src), 'Le cleanup annule la requête précédente (abort)');
""")),
    TD(3, "Liste + détail, deux requêtes liées",
       "Une vraie page catalogue : la liste à gauche, le détail du livre sélectionné à droite. Le détail est chargé **à la demande** avec une seconde requête qui dépend de la sélection. Tu gères deux cycles chargement/erreur indépendants, et le cas du livre supprimé entre-temps (404).",
       ["`Liste` charge `GET /livres` et affiche un `<button>` par livre ; cliquer sélectionne son id (state dans `App`)",
        "`Detail` reçoit `id` (ou `null`) : si `null`, affiche « Choisis un livre » ; sinon charge `GET /livres/:id`",
        "`Detail` affiche le titre dans un `<h2>`, l'auteur, et « Disponible » ou « Emprunté »",
        "Si le serveur répond 404 : `<p role=\"alert\">Ce livre n'existe plus</p>`",
        "Changer de sélection relance le chargement du détail (dépendance `[id]`)"],
       [F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });
"""), F("Liste.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import { api } from './api/client';

type Livre = { id: number; titre: string };

export default function Liste({ onSelect }: { onSelect: (id: number) => void }) {
  // à toi
  return null;
}
"""), F("Detail.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import axios from 'axios';
import { api } from './api/client';

type Livre = { id: number; titre: string; auteur: string; disponible: boolean };

export default function Detail({ id }: { id: number | null }) {
  // à toi
  return null;
}
"""), F("App.tsx", "tsx", r"""
import { useState } from 'react';
import Liste from './Liste';
import Detail from './Detail';

export default function App() {
  const [selected, setSelected] = useState<number | null>(null);
  return (
    <div style={{ display: 'flex', gap: 24 }}>
      <Liste onSelect={setSelected} />
      <Detail id={selected} />
    </div>
  );
}
""")],
       ["Dans `Detail`, l'effet commence par `if (id === null) return;`.",
        "Statut de l'erreur axios : `axios.isAxiosError(err) && err.response?.status === 404`.",
        "Remets `livre` à `null` et `error` à `null` au début de chaque chargement, sinon l'ancien livre reste affiché."],
       [F("Liste.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import { api } from './api/client';

type Livre = { id: number; titre: string };

export default function Liste({ onSelect }: { onSelect: (id: number) => void }) {
  const [livres, setLivres] = useState<Livre[]>([]);
  useEffect(() => {
    api.get<Livre[]>('/livres').then((res) => setLivres(res.data));
  }, []);
  return (
    <nav>
      {livres.map((l) => (
        <button key={l.id} onClick={() => onSelect(l.id)}>{l.titre}</button>
      ))}
    </nav>
  );
}
"""), F("Detail.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import axios from 'axios';
import { api } from './api/client';

type Livre = { id: number; titre: string; auteur: string; disponible: boolean };

export default function Detail({ id }: { id: number | null }) {
  const [livre, setLivre] = useState<Livre | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id === null) return;
    const controller = new AbortController();
    setLivre(null);
    setError(null);
    setLoading(true);
    api.get<Livre>('/livres/' + id, { signal: controller.signal })
      .then((res) => setLivre(res.data))
      .catch((err) => {
        if (axios.isCancel(err)) return;
        setError(axios.isAxiosError(err) && err.response?.status === 404 ? "Ce livre n'existe plus" : 'Erreur de chargement');
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [id]);

  if (id === null) return <p>Choisis un livre</p>;
  if (loading) return <p>Chargement…</p>;
  if (error) return <p role="alert">{error}</p>;
  if (!livre) return null;
  return (
    <article>
      <h2>{livre.titre}</h2>
      <p>{livre.auteur}</p>
      <p>{livre.disponible ? 'Disponible' : 'Emprunté'}</p>
    </article>
  );
}
""")],
       ["Cliquer Dune affiche « Emprunté »",
        "Un livre supprimé côté serveur affiche « Ce livre n'existe plus »"],
       run=RUN("react", entry="App.tsx", api=LIB_API, tests=r"""
assert.includes(text(), 'Choisis un livre', 'Sans sélection : « Choisis un livre »');
await waitFor(() => $$('button').length === 5, 3000);
assert.equal($$('button').length, 5, 'Un bouton par livre');
await click(byText('Dune'));
await waitFor(() => $('h2'), 3000);
assert.equal($('h2').textContent, 'Dune', 'Le détail de Dune s\'affiche');
assert.includes(text(), 'Emprunté', 'Dune est « Emprunté »');
await click(byText('Fondation'));
await waitFor(() => $('h2') && $('h2').textContent === 'Fondation', 3000);
assert.includes(text(), 'Disponible', 'Fondation est « Disponible »');
window.__db.livres = window.__db.livres.filter((l) => l.id !== 4);
await click(byText('Hypérion'));
await waitFor(() => $('[role=alert]'), 3000);
assert.includes($('[role=alert]').textContent, "n'existe plus", '404 : « Ce livre n\'existe plus »');
""")),
  ])

# ---------------------------------------------------------------- mutations
mut = V2(v1["data-mutations"],
  prereq=[
    P("Mutation", "Toute requête qui **modifie** des données côté serveur : POST (créer), PUT/PATCH (modifier), DELETE (supprimer)."),
    P("Handler", "La fonction appelée par un événement : `onSubmit={handleCreate}`, `onClick={() => supprimer(id)}`."),
    P("`e.preventDefault()`", "Empêche le comportement par défaut du navigateur. Sur un `<form>`, ça évite le rechargement de la page à l'envoi."),
    P("Immutabilité", "On ne modifie pas un tableau du state : on en crée un nouveau. Ajouter : `[nouveau, ...liste]`. Retirer : `liste.filter(...)`. Modifier : `liste.map(...)`."),
    P("422 et violations", "Quand les données envoyées sont invalides, Symfony répond 422 avec une liste `violations` : `[{ propertyPath: 'titre', title: 'Message' }]`."),
  ],
  diagram=D(
    nodes=[
      N("clic", 0, 1, "Submit", "handleCreate()", kind="actor", color="muted"),
      N("saving", 1, 1, "saving = true", "bouton désactivé", kind="pill"),
      N("post", 2, 1, "api.post", "/articles {titre}", color="accent"),
      N("ok", 3, 0, "Succès : 201", "res.data = l'article", color="good"),
      N("ko", 3, 2, "Échec : 422", "err.response.data", color="bad"),
      N("list", 4, 0, "setArticles", "[res.data, ...liste]", color="good"),
      N("msg", 4, 2, "setError", "message sous le champ", color="bad"),
    ],
    edges=[E("clic", "saving"), E("saving", "post"), E("post", "ok", color="good"), E("post", "ko", color="bad"), E("ok", "list", "2e étape !", color="good"), E("ko", "msg", color="bad")],
    caption="Une mutation se fait en deux temps : envoyer la requête, PUIS mettre à jour l'écran avec la réponse. C'est la 2e étape qu'on oublie."),
  lessons=[
    L("Lire et écrire ne fonctionnent pas pareil", r"""
Lire des données, c'est **une** étape : demander, puis afficher ce qui arrive. Écrire, c'en est **deux** :

1. **Envoyer** la mutation au serveur (`api.post`, `api.patch`, `api.delete`).
2. **Mettre à jour l'écran** pour qu'il reflète le nouvel état.

Pourquoi la 2e étape ? Parce que ton state React est une **copie locale** des données du serveur. Quand tu ajoutes un article en base, ta copie ne le sait pas : React affiche toujours l'ancienne liste. C'est l'erreur n°1 des débutants : « le POST marche (201 dans l'onglet Réseau) mais rien ne change à l'écran ».

Deux façons de faire la 2e étape :

- **Mettre à jour le state avec la réponse** : `setArticles((liste) => [res.data, ...liste])`. Rapide, pas de requête en plus.
- **Recharger la liste** : relancer le GET. Plus simple, toujours exact, mais une requête de plus.

Autre différence : une mutation est une réponse à une **action de l'utilisateur** (clic, envoi de formulaire). Elle se lance donc **dans le handler**, jamais dans un `useEffect` (qui sert à synchroniser, pas à réagir à un clic).
"""),
    L("Écrire une mutation proprement", r"""
Le modèle à reproduire :

```tsx
async function handleCreate(e: FormEvent) {
  e.preventDefault();                 // pas de rechargement de page
  setSaving(true);                    // désactive le bouton : pas de double envoi
  setError(null);
  try {
    const res = await api.post<Article>('/articles', { titre });   // 1. envoyer
    setArticles((liste) => [res.data, ...liste]);                    // 2. mettre à jour l'écran
    setTitre('');                                                    // vider le champ
  } catch (err) {
    setError("L'enregistrement a échoué");
  } finally {
    setSaving(false);
  }
}
```

Trois détails importants :

- On ajoute **`res.data`**, l'objet renvoyé par le serveur, pas ce qu'on a tapé. Seul le serveur connaît l'`id` du nouvel article (et les champs calculés : date, auteur…). Sans `id`, impossible de le modifier ou le supprimer ensuite.
- On utilise la **forme fonction** `setArticles((liste) => …)` : elle part toujours de la valeur la plus récente, même si une autre mise à jour a eu lieu pendant l'attente.
- `saving` désactive le bouton pendant l'envoi. Sinon un double-clic crée deux articles.
"""),
    L("Afficher les erreurs du serveur", r"""
Le serveur est le juge final : même si ton formulaire vérifie déjà le titre, le serveur peut refuser (règle que tu ne connais pas, donnée déjà prise, etc.). Avec axios, une réponse 4xx/5xx arrive dans le `catch`, et l'erreur contient la réponse :

```tsx
catch (err) {
  if (axios.isAxiosError(err) && err.response?.status === 422) {
    // Symfony : { violations: [{ propertyPath: 'titre', title: '...' }] }
    setError(err.response.data.violations[0].title);
  } else if (axios.isAxiosError(err) && err.response?.status === 409) {
    setError('Déjà emprunté');
  } else {
    setError("L'enregistrement a échoué");
  }
}
```

`axios.isAxiosError(err)` vérifie que l'erreur vient bien d'axios (et pas d'un bug dans ton code) ; TypeScript sait alors que `err.response` existe.

Bonne pratique : afficher le message **à côté du champ concerné** (`propertyPath` te dit lequel), et garder ce que l'utilisateur a tapé pour qu'il corrige, au lieu de tout vider.
"""),
    L("Modifier et supprimer : `map` et `filter`", r"""
Pour un PATCH, le serveur renvoie l'objet modifié : on **remplace** l'ancien dans la liste avec `map`.

```tsx
async function renommer(id: number, titre: string) {
  const res = await api.patch<Article>(`/articles/${id}`, { titre });
  setArticles((liste) => liste.map((a) => (a.id === id ? res.data : a)));
}
```

Pour un DELETE, le serveur répond souvent `204` sans corps : on **retire** l'élément avec `filter`.

```tsx
async function supprimer(id: number) {
  await api.delete(`/articles/${id}`);
  setArticles((liste) => liste.filter((a) => a.id !== id));
}
```

Pour un bouton par ligne (supprimer, emprunter), on veut désactiver **seulement** le bouton concerné : un state `pendingId` (l'id en cours d'envoi, ou `null`) suffit. `disabled={pendingId === a.id}`.

**Et la mise à jour optimiste ?** On peut modifier l'écran **avant** la réponse (l'élément disparaît tout de suite), puis revenir en arrière si le serveur refuse. C'est plus réactif mais plus complexe ; TanStack Query le gère proprement (dernier module).
"""),
  ],
  recap=[
    "Une mutation = **envoyer** puis **mettre à jour l'écran**. Sans la 2e étape, la base change mais pas l'affichage.",
    "On la lance dans le **handler** (onSubmit, onClick), pas dans un useEffect.",
    "Ajouter `res.data` (avec son id), via `setX((liste) => …)`. Modifier avec `map`, supprimer avec `filter`.",
    "`saving` / `pendingId` désactivent le bon bouton et empêchent les doubles envois.",
    "Les erreurs 4xx arrivent dans `catch` : `axios.isAxiosError(err)`, `err.response.status`, `err.response.data`.",
  ],
  example=[F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });
"""), F("Articles.tsx", "tsx", r"""
import { useEffect, useState, FormEvent } from 'react';
import axios from 'axios';
import { api } from './api/client';

type Article = { id: number; titre: string; auteur: string };

export default function Articles() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [titre, setTitre] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<Article[]>('/articles').then((res) => setArticles(res.data));
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const res = await api.post<Article>('/articles', { titre });   // 1. envoyer
      setArticles((liste) => [res.data, ...liste]);                    // 2. mettre à jour
      setTitre('');
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 422) {
        setError(err.response.data.violations[0].title);
      } else {
        setError("L'enregistrement a échoué");
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    await api.delete(`/articles/${id}`);
    setArticles((liste) => liste.filter((a) => a.id !== id));
  }

  return (
    <>
      <form onSubmit={handleCreate}>
        <input value={titre} onChange={(e) => setTitre(e.target.value)} placeholder="Titre" />
        <button disabled={saving}>{saving ? 'Envoi…' : 'Publier'}</button>
        {error && <p role="alert">{error}</p>}
      </form>
      <ul>
        {articles.map((a) => (
          <li key={a.id}>
            {a.titre} <button onClick={() => handleDelete(a.id)}>Supprimer</button>
          </li>
        ))}
      </ul>
    </>
  );
}
""")],
  notes=["Le GET (lecture) est dans le `useEffect` ; les mutations sont dans les handlers.",
         "`handleCreate` suit exactement les 2 étapes : `api.post`, puis `setArticles` avec `res.data`.",
         "La 422 affiche le message exact du serveur (`violations[0].title`).",
         "`handleDelete` : le serveur répond 204 (pas de corps), on retire l'article avec `filter`."],
  td1=dict(path="Emprunts.tsx",
    files=[F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });
"""), F("Emprunts.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import axios from 'axios';
import { api } from './api/client';

type Livre = { id: number; titre: string; disponible: boolean };

export default function Emprunts() {
  const [livres, setLivres] = useState<Livre[]>([]);

  useEffect(() => {
    api.get<Livre[]>('/livres').then((res) => setLivres(res.data));
  }, []);

  // à toi : emprunter(id), pendingId, message

  return (
    <ul>
      {livres.map((l) => (
        <li key={l.id}>{l.titre}</li>
      ))}
    </ul>
  );
}
""")],
    solution=[F("Emprunts.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import axios from 'axios';
import { api } from './api/client';

type Livre = { id: number; titre: string; disponible: boolean };

export default function Emprunts() {
  const [livres, setLivres] = useState<Livre[]>([]);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    api.get<Livre[]>('/livres').then((res) => setLivres(res.data));
  }, []);

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
""")],
    run=RUN("react", entry="Emprunts.tsx", api=LIB_API, tests=r"""
await waitFor(() => $$('li').length === 5, 3000);
assert.equal($$('li button').length, 4, '4 boutons « Emprunter » (Dune est déjà emprunté)');
const ligne = () => $$('li').find((li) => li.textContent.includes('Fondation'));
await click(ligne().querySelector('button'));
assert(ligne().querySelector('button') && ligne().querySelector('button').disabled, 'Pendant l\'envoi, le bouton de Fondation est désactivé');
assert(!$$('li').find((li) => li.textContent.includes('Terremer')).querySelector('button').disabled, 'Les autres boutons restent actifs');
await waitFor(() => !ligne().querySelector('button'), 3000);
assert.includes(ligne().textContent, 'emprunté', 'Fondation passe à « emprunté » sans recharger');
assert.equal(window.__db.emprunts.length, 1, 'Le serveur a reçu un emprunt');
window.__db.livres.find((l) => l.id === 1).disponible = false;
await click($$('li').find((li) => li.textContent.includes('Terremer')).querySelector('button'));
await waitFor(() => $('[role=alert]'), 3000);
assert.includes($('[role=alert]').textContent, 'Déjà emprunté', '409 : message « Déjà emprunté »');
""")),
  tds=[
    TD(2, "Créer et renommer des articles",
       "Tu combines un **POST** (création, avec affichage de l'erreur 422 renvoyée par le serveur) et un **PATCH** (renommer un article existant, en remplaçant l'élément dans la liste avec `map`).",
       ["Formulaire : champ `titre` (placeholder « Titre ») + bouton « Publier » ; le nouvel article apparaît **en tête** de liste",
        "En cas de 422 : afficher le `title` de la première violation dans `<p role=\"alert\">` et **garder** le texte saisi",
        "Chaque article a un bouton « Renommer » qui envoie `PATCH /articles/:id` avec `{ titre: titre + ' (modifié)' }`",
        "Après le PATCH, remplacer l'article dans la liste par `res.data` (avec `map`)",
        "Le bouton « Publier » est désactivé pendant l'envoi"],
       [F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });
"""), F("Articles.tsx", "tsx", r"""
import { useEffect, useState, FormEvent } from 'react';
import axios from 'axios';
import { api } from './api/client';

type Article = { id: number; titre: string; auteur: string };

export default function Articles() {
  const [articles, setArticles] = useState<Article[]>([]);

  useEffect(() => {
    api.get<Article[]>('/articles').then((res) => setArticles(res.data));
  }, []);

  // à toi

  return (
    <ul>
      {articles.map((a) => <li key={a.id}>{a.titre}</li>)}
    </ul>
  );
}
""")],
       ["Erreur 422 : `err.response.data.violations[0].title` (vérifie d'abord `axios.isAxiosError(err)`).",
        "Ne vide le champ (`setTitre('')`) que dans le cas de succès.",
        "Renommer : `setArticles((l) => l.map((x) => (x.id === id ? res.data : x)))`."],
       [F("Articles.tsx", "tsx", r"""
import { useEffect, useState, FormEvent } from 'react';
import axios from 'axios';
import { api } from './api/client';

type Article = { id: number; titre: string; auteur: string };

export default function Articles() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [titre, setTitre] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<Article[]>('/articles').then((res) => setArticles(res.data));
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const res = await api.post<Article>('/articles', { titre });
      setArticles((l) => [res.data, ...l]);
      setTitre('');
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 422) {
        setError(err.response.data.violations[0].title);
      } else {
        setError("L'enregistrement a échoué");
      }
    } finally {
      setSaving(false);
    }
  }

  async function renommer(a: Article) {
    const res = await api.patch<Article>(`/articles/${a.id}`, { titre: a.titre + ' (modifié)' });
    setArticles((l) => l.map((x) => (x.id === a.id ? res.data : x)));
  }

  return (
    <>
      <form onSubmit={handleCreate}>
        <input value={titre} onChange={(e) => setTitre(e.target.value)} placeholder="Titre" />
        <button disabled={saving}>Publier</button>
        {error && <p role="alert">{error}</p>}
      </form>
      <ul>
        {articles.map((a) => (
          <li key={a.id}>
            {a.titre} <button onClick={() => renommer(a)}>Renommer</button>
          </li>
        ))}
      </ul>
    </>
  );
}
""")],
       ["Un titre de 3 lettres affiche le message du serveur et reste dans le champ",
        "« Renommer » change le texte de la bonne ligne seulement"],
       run=RUN("react", entry="Articles.tsx", api=LIB_API, tests=r"""
await waitFor(() => $$('li').length === 2, 3000);
await type('input', 'Abc');
await submit('form');
await waitFor(() => $('[role=alert]'), 3000);
assert.includes($('[role=alert]').textContent, '5 caractères', '422 : le message du serveur est affiché');
assert.equal($('input').value, 'Abc', 'Le texte saisi est conservé après une erreur');
await type('input', 'Mon nouvel article');
await submit('form');
assert($('form button').disabled, 'Le bouton Publier est désactivé pendant l\'envoi');
await waitFor(() => $$('li').length === 3, 3000);
assert.includes($$('li')[0].textContent, 'Mon nouvel article', 'Le nouvel article est en tête de liste');
assert.equal($('input').value, '', 'Le champ est vidé après succès');
const ligne = $$('li').find((li) => li.textContent.includes('Les DTO expliqués'));
await click(ligne.querySelector('button'));
await waitFor(() => text().includes('Les DTO expliqués (modifié)'), 3000);
assert.equal(window.__db.articles.find((a) => a.id === 2).titre, 'Les DTO expliqués (modifié)', 'Le PATCH a modifié le serveur');
assert(!text().includes('Bienvenue sur le blog (modifié)'), 'Les autres articles ne changent pas');
""")),
    TD(3, "Suppression optimiste avec retour arrière",
       "Pour une interface réactive, l'article **disparaît immédiatement** au clic, avant même la réponse du serveur. Si le serveur refuse, il faut le **remettre à sa place** et prévenir l'utilisateur. Tu dois garder une copie de l'état d'avant et gérer l'ordre des opérations avec soin.",
       ["« Supprimer » retire l'article de la liste **tout de suite** (avant la réponse)",
        "Puis `DELETE /articles/:id`",
        "Si le serveur échoue : remettre la liste **exactement** comme avant (même position) et afficher `<p role=\"alert\">Suppression impossible</p>`",
        "Si succès : rien de plus à faire (l'article est déjà parti)",
        "Un compteur « N article(s) » au-dessus de la liste reste juste dans tous les cas"],
       [F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });
"""), F("Articles.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import { api } from './api/client';

type Article = { id: number; titre: string; auteur: string };

export default function Articles() {
  const [articles, setArticles] = useState<Article[]>([]);

  useEffect(() => {
    api.get<Article[]>('/articles').then((res) => setArticles(res.data));
  }, []);

  // à toi : supprimer(id) en mode optimiste

  return (
    <ul>
      {articles.map((a) => <li key={a.id}>{a.titre}</li>)}
    </ul>
  );
}
""")],
       ["Avant de modifier le state : `const avant = articles;` (le tableau n'est jamais modifié sur place, la copie est donc sûre).",
        "Dans le `catch` : `setArticles(avant)`.",
        "Le compteur est une valeur **dérivée** : `articles.length`, pas un state."],
       [F("Articles.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import { api } from './api/client';

type Article = { id: number; titre: string; auteur: string };

export default function Articles() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<Article[]>('/articles').then((res) => setArticles(res.data));
  }, []);

  async function supprimer(id: number) {
    const avant = articles;
    setError(null);
    setArticles(avant.filter((a) => a.id !== id));   // optimiste : tout de suite
    try {
      await api.delete(`/articles/${id}`);
    } catch {
      setArticles(avant);                              // retour arrière
      setError('Suppression impossible');
    }
  }

  return (
    <>
      <p>{articles.length} article(s)</p>
      {error && <p role="alert">{error}</p>}
      <ul>
        {articles.map((a) => (
          <li key={a.id}>
            {a.titre} <button onClick={() => supprimer(a.id)}>Supprimer</button>
          </li>
        ))}
      </ul>
    </>
  );
}
""")],
       ["L'article disparaît avant la réponse",
        "En cas d'échec, il revient à la même place"],
       run=RUN("react", entry="Articles.tsx", api=LIB_API, tests=r"""
await waitFor(() => $$('li').length === 2, 3000);
assert.includes(text(), '2 article', 'Compteur initial : 2 articles');
await click($$('li')[1].querySelector('button'));
assert.equal($$('li').length, 1, 'L\'article disparaît immédiatement (avant la réponse)');
assert.includes(text(), '1 article', 'Le compteur passe à 1');
await waitFor(() => window.__db.articles.length === 1, 3000);
assert(true, 'Le DELETE a été envoyé au serveur');
await tick(200);
window.__api['DELETE /api/articles/:id'] = () => [500, { error: 'boom' }];
await click($$('li')[0].querySelector('button'));
assert.equal($$('li').length, 0, 'Le 2e article disparaît aussi tout de suite');
await waitFor(() => $('[role=alert]'), 3000);
assert.equal($$('li').length, 1, 'Échec serveur : l\'article revient');
assert.includes($$('li')[0].textContent, 'Bienvenue', 'C\'est bien le même article');
assert.includes($('[role=alert]').textContent, 'Suppression impossible', 'Message « Suppression impossible »');
""")),
  ])

# ---------------------------------------------------------------- organiser
org = V2(v1["data-organiser"],
  prereq=[
    P("Module (import / export)", "Chaque fichier est un module. `export const api = …` le rend disponible ; `import { api } from './api/client'` l'utilise ailleurs."),
    P("Hook personnalisé", "Une fonction `useQuelqueChose` qui utilise d'autres hooks (`useState`, `useEffect`) et renvoie ce dont le composant a besoin (parcours React, dernier module)."),
    P("`useCallback`", "Garde la **même** fonction d'un rendu à l'autre tant que ses dépendances ne changent pas. Utile quand une fonction sert de dépendance à un `useEffect`."),
    P("Intercepteur", "Une fonction qu'axios appelle **avant chaque requête** (pour l'enrichir, ex. ajouter un token) ou **après chaque réponse** (pour réagir, ex. un 401 global)."),
    P("Token / Bearer", "Une chaîne secrète que le serveur donne après connexion. Le client la renvoie à chaque requête dans `Authorization: Bearer <token>` pour prouver qui il est."),
  ],
  diagram=D(
    nodes=[
      N("comp", 0, 1, "Composant", "Catalogue.tsx\naffiche", kind="doc"),
      N("hook", 1, 1, "Hook", "useLivres()\nstate + actions", color="accent"),
      N("fn", 2, 1, "Fonctions API", "api/livres.ts\ngetLivres(), emprunter()"),
      N("client", 3, 1, "Client HTTP", "api/client.ts\nbaseURL, intercepteurs", color="muted"),
      N("srv", 4, 1, "Serveur", "/api/livres", kind="db", color="muted"),
      N("type", 2, 0, "Types", "Livre = DTO Symfony", kind="note"),
    ],
    edges=[E("comp", "hook", "appelle"), E("hook", "fn", "appelle"), E("fn", "client", "utilise"), E("client", "srv", "HTTP"), E("type", "fn", dashed=True)],
    caption="Chaque couche ne connaît que celle d'à côté. Le composant ne voit jamais une URL ; changer l'API ne touche qu'un fichier."),
  lessons=[
    L("Le problème : du HTTP partout", r"""
Dans les modules précédents, chaque composant contenait son `api.get`, ses URLs, ses `try/catch`, ses `useState` de chargement. Sur un petit exemple, ça va. Sur une vraie application avec 30 écrans :

- La même requête (`GET /livres`) est écrite dans 5 composants, chacun un peu différemment.
- L'API change (`/livres` devient `/v2/livres`, ou il faut ajouter un token) : il faut modifier tous ces fichiers.
- Les composants font 150 lignes, dont 100 de plomberie réseau. On ne voit plus ce qu'ils **affichent**.

La solution est la même qu'en back (contrôleur / service / repository, parcours Architecture) : **séparer les rôles** en couches.
"""),
    L("Les trois couches", r"""
**1. Le client HTTP** (`api/client.ts`) : la configuration commune, écrite une seule fois.

```ts
export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL });
```

**2. Les fonctions par ressource** (`api/livres.ts`) : une fonction par opération, avec ses types. Elles renvoient **directement les données**, pas la réponse axios.

```ts
export type Livre = { id: number; titre: string; auteur: string; disponible: boolean };

export const getLivres = () => api.get<Livre[]>('/livres').then((r) => r.data);
export const getLivre = (id: number) => api.get<Livre>(`/livres/${id}`).then((r) => r.data);
export const emprunterLivre = (livreId: number, rendreLe: string) =>
  api.post('/emprunts', { livreId, rendreLe }).then((r) => r.data);
```

C'est l'équivalent front d'un **repository** : la seule couche qui connaît les URLs. Les types `Livre` reflètent les **DTO de sortie** de ton back : c'est le même contrat, vu des deux côtés.

**3. Le hook** (`hooks/useLivres.ts`) : le state, le chargement, l'erreur et les actions (mutations). C'est l'équivalent front d'un **service**.

```ts
export function useLivres() {
  const [livres, setLivres] = useState<Livre[]>([]);
  // ... loading, error, reload, emprunter
  return { livres, loading, error, reload, emprunter };
}
```

Le **composant** n'a plus qu'à afficher :

```tsx
const { livres, loading, error, emprunter } = useLivres();
```
"""),
    L("Écrire le hook : `useCallback` et actions", r"""
Le hook réunit ce que tu écrivais dans le composant. Une subtilité : la fonction `reload` sert à la fois au premier chargement (dans `useEffect`) et au bouton « Recharger ». Comme elle est une dépendance de l'effet, elle doit rester **la même** d'un rendu à l'autre, sinon l'effet se relancerait à chaque rendu (boucle). `useCallback` garantit ça :

```ts
const reload = useCallback(async () => {
  setLoading(true);
  setError(null);
  try { setLivres(await getLivres()); }
  catch { setError('Impossible de charger les livres'); }
  finally { setLoading(false); }
}, []);                                   // ne change jamais

useEffect(() => { reload(); }, [reload]); // une seule fois
```

Les mutations deviennent des **actions nommées** qui font les deux étapes (envoyer, puis mettre à jour le state) :

```ts
async function emprunter(id: number) {
  await emprunterLivre(id, dans14Jours());
  setLivres((ls) => ls.map((l) => (l.id === id ? { ...l, disponible: false } : l)));
}
```

Un hook par **ressource** (`useLivres`, `useArticles`), pas un hook géant pour toute l'appli. Deux composants qui appellent `useLivres()` ont **chacun** leur propre state (le hook partage la logique, pas les données ; pour partager les données, voir TanStack Query).
"""),
    L("Les intercepteurs : un seul endroit pour l'authentification", r"""
Quand l'API demande un token, chaque requête doit porter l'en-tête `Authorization`. Plutôt que de l'ajouter dans chaque fonction, on le fait **une fois** dans le client, avec un intercepteur de requête :

```ts
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;                       // toujours renvoyer la config
});
```

De même, un intercepteur de **réponse** peut réagir à une erreur pour toute l'application, par exemple un 401 (session expirée) :

```ts
api.interceptors.response.use(
  (res) => res,                        // succès : on laisse passer
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      // rediriger vers la page de connexion...
    }
    return Promise.reject(err);        // l'erreur continue jusqu'au catch du composant
  },
);
```

Attention à bien **renvoyer** la config (requête) et à **rejeter** l'erreur (réponse) : sinon la requête part sans configuration, ou l'erreur disparaît et ton composant croit que tout s'est bien passé.
"""),
  ],
  recap=[
    "Trois couches : **client** (config axios), **fonctions API** (URLs + types), **hook** (state + actions). Le composant affiche.",
    "Les fonctions API renvoient `r.data` directement ; leurs types reflètent les DTO du back.",
    "Le hook expose `{ données, loading, error, reload, actions }` ; `useCallback` stabilise `reload`.",
    "Un intercepteur de requête ajoute le token partout ; un intercepteur de réponse gère le 401 globalement.",
    "Changer une URL ou l'authentification = modifier **un seul** fichier.",
  ],
  example=[F("api/client.ts", "ts", r"""
import axios from 'axios';

export const api = axios.create({ baseURL: '/api' });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
"""), F("api/livres.ts", "ts", r"""
import { api } from './client';

export type Livre = { id: number; titre: string; auteur: string; disponible: boolean };

export const getLivres = () => api.get<Livre[]>('/livres').then((r) => r.data);

export const emprunterLivre = (livreId: number, rendreLe: string) =>
  api.post('/emprunts', { livreId, rendreLe }).then((r) => r.data);
"""), F("hooks/useLivres.ts", "ts", r"""
import { useCallback, useEffect, useState } from 'react';
import { getLivres, emprunterLivre, type Livre } from '../api/livres';

const dans14Jours = () => new Date(Date.now() + 14 * 864e5).toISOString().slice(0, 10);

export function useLivres() {
  const [livres, setLivres] = useState<Livre[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try { setLivres(await getLivres()); }
    catch { setError('Impossible de charger les livres'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { reload(); }, [reload]);

  async function emprunter(id: number) {
    await emprunterLivre(id, dans14Jours());
    setLivres((ls) => ls.map((l) => (l.id === id ? { ...l, disponible: false } : l)));
  }

  return { livres, loading, error, reload, emprunter };
}
"""), F("Catalogue.tsx", "tsx", r"""
import { useLivres } from './hooks/useLivres';

export default function Catalogue() {
  const { livres, loading, error, emprunter } = useLivres();

  if (loading) return <p>Chargement…</p>;
  if (error) return <p role="alert">{error}</p>;

  return (
    <ul>
      {livres.map((l) => (
        <li key={l.id}>
          {l.titre}{' '}
          {l.disponible ? <button onClick={() => emprunter(l.id)}>Emprunter</button> : <em>emprunté</em>}
        </li>
      ))}
    </ul>
  );
}
""")],
  notes=["Lis les fichiers de droite à gauche : le composant (`Catalogue.tsx`) n'importe que le hook.",
         "`api/livres.ts` est le seul fichier qui contient des URLs.",
         "`hooks/useLivres.ts` contient tout le state et les actions ; `useCallback` évite de relancer l'effet en boucle.",
         "L'intercepteur de `api/client.ts` ajoute le token à **toutes** les requêtes, y compris celles écrites plus tard."],
  td1=dict(path="Catalogue.tsx",
    files=[F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });
"""), F("api/livres.ts", "ts", r"""
import { api } from './client';

export type Livre = { id: number; titre: string; auteur: string; disponible: boolean };

// à toi : getLivres(), emprunterLivre(livreId, rendreLe)
"""), F("hooks/useLivres.ts", "ts", r"""
import { useCallback, useEffect, useState } from 'react';
import axios from 'axios';
import { getLivres, emprunterLivre, type Livre } from '../api/livres';

export function useLivres() {
  // à toi : { livres, loading, error, reload, emprunter, pendingId }
}
"""), F("Catalogue.tsx", "tsx", r"""
import { useLivres } from './hooks/useLivres';

export default function Catalogue() {
  // à toi : uniquement de l'affichage
  return <p>À compléter</p>;
}
""")],
    solution=[F("api/livres.ts", "ts", r"""
import { api } from './client';

export type Livre = { id: number; titre: string; auteur: string; disponible: boolean };

export const getLivres = () => api.get<Livre[]>('/livres').then((r) => r.data);
export const emprunterLivre = (livreId: number, rendreLe: string) =>
  api.post('/emprunts', { livreId, rendreLe }).then((r) => r.data);
"""), F("hooks/useLivres.ts", "ts", r"""
import { useCallback, useEffect, useState } from 'react';
import axios from 'axios';
import { getLivres, emprunterLivre, type Livre } from '../api/livres';

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
"""), F("Catalogue.tsx", "tsx", r"""
import { useLivres } from './hooks/useLivres';

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
""")],
    run=RUN("react", entry="Catalogue.tsx", api=LIB_API, tests=r"""
const src = source('Catalogue.tsx');
assert(!/axios|api\//.test(src), 'Catalogue.tsx n\'importe ni axios ni api/');
assert(!/['"`]\/(livres|emprunts)/.test(source('hooks/useLivres.ts')), 'Le hook ne contient aucune URL');
const fns = require('./api/livres');
assert(typeof fns.getLivres === 'function' && typeof fns.emprunterLivre === 'function', 'api/livres.ts exporte getLivres et emprunterLivre');
const data = await fns.getLivres();
assert(Array.isArray(data) && data.length === 5, 'getLivres() renvoie directement le tableau (r.data)');
await waitFor(() => $$('li').length === 5, 3000);
assert.equal($$('li').length, 5, 'Le catalogue affiche 5 livres');
const ligne = () => $$('li').find((li) => li.textContent.includes('Hypérion'));
await click(ligne().querySelector('button'));
await waitFor(() => ligne().textContent.includes('emprunté'), 3000);
assert(true, 'Emprunter via le hook met à jour l\'affichage');
""")),
  tds=[
    TD(2, "Un intercepteur pour l'authentification",
       "La route `/api/me` exige un token. Au lieu d'ajouter l'en-tête dans chaque appel, tu écris un **intercepteur de requête** dans le client, puis un **intercepteur de réponse** qui gère le 401 pour toute l'application.",
       ["Dans `api/client.ts` : un intercepteur de requête ajoute `Authorization: Bearer <token>` si `localStorage.getItem('token')` existe",
        "Un intercepteur de réponse : sur 401, supprime le token du localStorage puis **rejette** l'erreur",
        "`api/me.ts` exporte `getMe()` qui renvoie directement les données de `GET /me`",
        "`Profil.tsx` affiche « Bonjour <pseudo> » si `getMe()` réussit, sinon « Non connecté »",
        "Le composant ne manipule jamais le token"],
       [F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });

// à toi : intercepteurs
"""), F("api/me.ts", "ts", r"""
import { api } from './client';
// à toi : getMe()
"""), F("Profil.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import { getMe } from './api/me';

export default function Profil() {
  // à toi
  return <p>…</p>;
}
""")],
       ["Requête : `api.interceptors.request.use((config) => { ...; return config; })`.",
        "Réponse : `api.interceptors.response.use((r) => r, (err) => { ...; return Promise.reject(err); })`.",
        "Pour tester toi-même dans l'aperçu : `localStorage.setItem('token', 'secret-123')` dans la console du navigateur n'est pas possible ici, les tests le font pour toi."],
       [F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) localStorage.removeItem('token');
    return Promise.reject(err);
  },
);
"""), F("api/me.ts", "ts", r"""
import { api } from './client';

export type Me = { id: number; pseudo: string };
export const getMe = () => api.get<Me>('/me').then((r) => r.data);
"""), F("Profil.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import { getMe, type Me } from './api/me';

export default function Profil() {
  const [me, setMe] = useState<Me | null>(null);
  const [done, setDone] = useState(false);
  useEffect(() => {
    getMe().then(setMe).catch(() => setMe(null)).finally(() => setDone(true));
  }, []);
  if (!done) return <p>…</p>;
  return <p>{me ? `Bonjour ${me.pseudo}` : 'Non connecté'}</p>;
}
""")],
       ["Avec un token valide, « Bonjour fausatu » s'affiche",
        "Un token invalide est supprimé du localStorage après le 401"],
       run=RUN("react", entry="Profil.tsx", api=LIB_API, tests=r"""
await waitFor(() => text().includes('Non connecté'), 3000);
assert(true, 'Sans token : « Non connecté »');
const { getMe } = require('./api/me');
localStorage.setItem('token', 'secret-123');
const me = await getMe();
assert(me && me.pseudo === 'fausatu', 'Avec le bon token, getMe() renvoie le profil (en-tête ajouté par l\'intercepteur)');
localStorage.setItem('token', 'mauvais');
let rejected = false;
try { await getMe(); } catch (e) { rejected = true; }
assert(rejected, 'Un 401 est toujours rejeté (l\'erreur arrive au catch)');
assert.equal(localStorage.getItem('token'), null, 'Après un 401, le token est supprimé');
assert(!/localStorage|Authorization/.test(source('Profil.tsx')), 'Profil.tsx ne manipule pas le token');
""")),
    TD(3, "Un hook générique `useRessource`",
       "`useLivres`, `useArticles`, `useMe`… se ressemblent tous. Tu écris un hook **générique** qui prend n'importe quelle fonction de chargement et gère chargement, erreur et rechargement, puis tu l'utilises pour deux ressources différentes dans la même page.",
       ["`useRessource<T>(charger: () => Promise<T>)` renvoie `{ data, loading, error, reload }` (`data` vaut `null` au départ)",
        "Le chargement se lance au montage ; `reload()` le relance",
        "L'erreur contient `'Erreur ' + status` si c'est une erreur HTTP, sinon `'Erreur réseau'`",
        "`App` affiche les livres et les articles avec **deux** appels à `useRessource`",
        "Le hook ne contient aucune URL et ne dépend d'aucune ressource précise"],
       [F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });
"""), F("api/ressources.ts", "ts", r"""
import { api } from './client';

export type Livre = { id: number; titre: string };
export type Article = { id: number; titre: string };

export const getLivres = () => api.get<Livre[]>('/livres').then((r) => r.data);
export const getArticles = () => api.get<Article[]>('/articles').then((r) => r.data);
"""), F("hooks/useRessource.ts", "ts", r"""
import { useCallback, useEffect, useState } from 'react';
import axios from 'axios';

export function useRessource<T>(charger: () => Promise<T>) {
  // à toi
}
"""), F("App.tsx", "tsx", r"""
import { useRessource } from './hooks/useRessource';
import { getLivres, getArticles } from './api/ressources';

export default function App() {
  // à toi : deux sections, « Livres » et « Articles »
  return null;
}
""")],
       ["Garde `charger` dans une ref (`useRef`) ou passe-la au `useCallback` : si le composant passe une fonction définie hors du composant (`getLivres`), elle est déjà stable.",
        "Erreur : `axios.isAxiosError(err) && err.response ? 'Erreur ' + err.response.status : 'Erreur réseau'`.",
        "Dans `App`, renomme à la destructuration : `const { data: livres, loading: l1 } = useRessource(getLivres);`."],
       [F("hooks/useRessource.ts", "ts", r"""
import { useCallback, useEffect, useState } from 'react';
import axios from 'axios';

export function useRessource<T>(charger: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await charger());
    } catch (err) {
      setError(axios.isAxiosError(err) && err.response ? 'Erreur ' + err.response.status : 'Erreur réseau');
    } finally {
      setLoading(false);
    }
  }, [charger]);

  useEffect(() => { reload(); }, [reload]);

  return { data, loading, error, reload };
}
"""), F("App.tsx", "tsx", r"""
import { useRessource } from './hooks/useRessource';
import { getLivres, getArticles } from './api/ressources';

export default function App() {
  const livres = useRessource(getLivres);
  const articles = useRessource(getArticles);

  return (
    <>
      <section className="livres">
        <h2>Livres</h2>
        {livres.loading && <p>Chargement…</p>}
        {livres.error && <p role="alert">{livres.error}</p>}
        <ul>{livres.data?.map((l) => <li key={l.id}>{l.titre}</li>)}</ul>
        <button onClick={livres.reload}>Recharger les livres</button>
      </section>
      <section className="articles">
        <h2>Articles</h2>
        {articles.loading && <p>Chargement…</p>}
        {articles.error && <p role="alert">{articles.error}</p>}
        <ul>{articles.data?.map((a) => <li key={a.id}>{a.titre}</li>)}</ul>
      </section>
    </>
  );
}
""")],
       ["Les deux listes se chargent indépendamment",
        "Une erreur 500 sur les articles n'empêche pas l'affichage des livres"],
       run=RUN("react", entry="App.tsx", api=LIB_API, tests=r"""
await waitFor(() => $$('.livres li').length === 5 && $$('.articles li').length === 2, 3000);
assert.equal($$('.livres li').length, 5, 'Section livres : 5 éléments');
assert.equal($$('.articles li').length, 2, 'Section articles : 2 éléments');
assert(!/['"`]\/(livres|articles)/.test(source('hooks/useRessource.ts')), 'Le hook ne contient aucune URL');
const { useRessource } = require('./hooks/useRessource');
const React = require('react'); const ReactDOM = require('react-dom/client');
let last = null;
const echoue = () => Promise.reject({ isAxiosError: true, response: { status: 503 } });
function T() { last = useRessource(echoue); return null; }
const div = document.createElement('div'); document.body.appendChild(div);
ReactDOM.createRoot(div).render(React.createElement(T));
await waitFor(() => last && !last.loading, 2000);
assert.equal(last.error, 'Erreur 503', 'Erreur HTTP : « Erreur 503 »');
assert.equal(last.data, null, 'data reste null en cas d\'erreur');
window.__db.livres.push({ id: 6, titre: 'Solaris', auteur: 'S. Lem', disponible: true });
await click(byText('Recharger les livres'));
await waitFor(() => $$('.livres li').length === 6, 3000);
assert(true, 'reload() recharge la ressource');
""")),
  ])

# ---------------------------------------------------------------- TanStack
tq = V2(v1["data-tanstack"],
  prereq=[
    P("Cache", "Une mémoire des réponses déjà reçues. Si on redemande la même chose, on la ressort tout de suite au lieu de refaire la requête."),
    P("Clé de requête (queryKey)", "Un tableau qui identifie une donnée dans le cache : `['livres']`, `['livres', { page: 2 }]`, `['livre', 7]`. Même clé = même donnée."),
    P("Invalider", "Marquer une donnée du cache comme **périmée**. TanStack Query la recharge alors automatiquement là où elle est affichée."),
    P("Provider", "Un composant placé tout en haut de l'appli (`<QueryClientProvider>`) qui rend un objet (ici le cache) accessible à tous les composants en dessous."),
    P("Données « serveur » vs « client »", "Données serveur : elles vivent en base, ta page n'en a qu'une copie (livres, articles). Données client : elles n'existent que dans la page (onglet ouvert, texte d'un champ). TanStack Query gère les premières ; `useState` les secondes."),
  ],
  diagram=D(
    nodes=[
      N("a", 0, 0, "Catalogue", "useQuery(['livres'])", kind="doc"),
      N("b", 0, 2, "Compteur", "useQuery(['livres'])", kind="doc"),
      N("cache", 1, 1, "Cache", "['livres'] → [...]", kind="db", color="accent"),
      N("srv", 2, 1, "Serveur", "GET /api/livres\n(1 seule fois)", color="muted"),
      N("mut", 3, 0, "useMutation", "emprunter(3)", color="warn"),
      N("inv", 3, 2, "invalidateQueries", "['livres'] périmé", color="good"),
    ],
    edges=[E("a", "cache"), E("b", "cache"), E("cache", "srv", "si absent\nou périmé"), E("mut", "srv", "POST"), E("mut", "inv", "onSuccess", color="good"), E("inv", "cache", "recharge", color="good", dashed=True)],
    caption="Les composants lisent le cache par sa clé. Une mutation réussie invalide la clé : tout ce qui l'affiche se met à jour, sans code de ta part."),
  lessons=[
    L("Ce que tu écrivais à la main", r"""
Dans les modules précédents, chaque chargement demandait : 3 `useState` (données, chargement, erreur), un `useEffect`, un `AbortController`, un `reload`, et après chaque mutation, une mise à jour manuelle de la liste (`map`, `filter`). Et deux composants qui affichent les livres faisaient **deux** requêtes, chacun avec sa copie.

C'est le même code à chaque fois, et il manque encore beaucoup de choses : garder les données quand on revient sur une page, recharger quand l'utilisateur revient sur l'onglet, réessayer après une erreur réseau, éviter les doublons de requêtes…

**TanStack Query** (anciennement React Query) est la librairie standard qui fait tout ça. L'idée centrale : les données du serveur vivent dans un **cache partagé**, identifié par des **clés**. Les composants **lisent** le cache ; les mutations **l'invalident**.
"""),
    L("Lire : `useQuery`", r"""
Installation : `npm i @tanstack/react-query`, puis un provider autour de l'application :

```tsx
const queryClient = new QueryClient();

<QueryClientProvider client={queryClient}>
  <App />
</QueryClientProvider>
```

Ensuite, dans n'importe quel composant :

```tsx
const { data, isPending, isError, error, refetch } = useQuery({
  queryKey: ['livres'],      // l'identifiant dans le cache
  queryFn: getLivres,        // ta fonction de la couche API (module précédent)
});

if (isPending) return <p>Chargement…</p>;
if (isError) return <p role="alert">Erreur</p>;
return <ul>{data.map(…)}</ul>;
```

Plus de `useState`, plus de `useEffect`. `isPending` est vrai tant qu'il n'y a pas encore de données ; `data` contient ce que `queryFn` a renvoyé.

La **clé** contient tout ce dont dépend la requête. Pour une liste paginée :

```tsx
useQuery({ queryKey: ['livres', { page }], queryFn: () => getLivresPage(page) });
```

Quand `page` change, la clé change : TanStack Query charge la nouvelle page **et garde** l'ancienne en cache. Revenir à la page 1 est instantané.

Deux composants avec la même clé partagent **la même** entrée de cache : une seule requête, et les deux sont toujours d'accord.
"""),
    L("Écrire : `useMutation` et l'invalidation", r"""
Une mutation se déclare avec `useMutation`, et se lance avec `.mutate(...)` :

```tsx
const queryClient = useQueryClient();

const emprunt = useMutation({
  mutationFn: (livreId: number) => emprunterLivre(livreId, dans14Jours()),
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ['livres'] }),
});

<button onClick={() => emprunt.mutate(l.id)} disabled={emprunt.isPending}>Emprunter</button>
{emprunt.isError && <p role="alert">L'emprunt a échoué</p>}
```

La 2e étape d'une mutation (mettre à jour l'écran) devient une seule ligne : **invalider** la clé. TanStack Query recharge alors `['livres']`, et **tous** les composants qui l'affichent se mettent à jour. Plus de `map` ou `filter` à la main, plus de risque d'oublier un écran.

L'invalidation fonctionne par **préfixe** : invalider `['livres']` invalide aussi `['livres', { page: 2 }]`.

Ce que fournit l'objet mutation :

- `mutate(variables)` : lance la mutation ; `variables` est passé à `mutationFn`.
- `isPending` : envoi en cours (désactiver le bouton). `variables` : la dernière valeur envoyée (utile pour savoir **quelle** ligne est en cours).
- `isError`, `error` : l'erreur (une erreur axios, avec `error.response.status`).
- `onSuccess`, `onError`, `onSettled` : réagir à la fin.
"""),
    L("Quand l'utiliser, et le piège classique", r"""
Règle simple : **données serveur → TanStack Query ; données d'interface → useState**.

- Liste des livres, détail d'un article, profil connecté : `useQuery`.
- Onglet actif, texte d'un champ, modale ouverte, numéro de page : `useState`.

Le piège le plus fréquent : recopier `data` dans un `useState`.

```tsx
const { data } = useQuery({ queryKey: ['livres'], queryFn: getLivres });
const [livres, setLivres] = useState([]);
useEffect(() => { if (data) setLivres(data); }, [data]);   // NON
```

Tu recrées le problème d'avant : une copie qui ne suit plus le cache, et que les invalidations ne mettront pas à jour. Utilise `data` **directement**, et calcule ce qui en dérive (filtre, tri, total) pendant le rendu.

Enfin, TanStack Query ne remplace pas ta couche API : il **utilise** tes fonctions (`getLivres`, `emprunterLivre`). axios fait les requêtes ; TanStack Query gère l'état, le cache et le rafraîchissement.
"""),
  ],
  recap=[
    "Les données serveur vivent dans un **cache partagé**, identifié par des **clés** (`['livres', { page }]`).",
    "`useQuery({ queryKey, queryFn })` → `data`, `isPending`, `isError` : plus de useState/useEffect pour charger.",
    "`useMutation({ mutationFn, onSuccess })` puis `.mutate(v)` ; `isPending` et `variables` pour l'état d'envoi.",
    "Après une mutation, `invalidateQueries({ queryKey })` recharge tout ce qui affiche cette clé (par préfixe).",
    "Ne jamais recopier `data` dans un useState ; useState reste pour l'état d'interface (page, onglet, champ).",
  ],
  example=[F("main.tsx", "tsx", r"""
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createRoot } from 'react-dom/client';
import App from './App';

const queryClient = new QueryClient();

createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>,
);
"""), F("api/livres.ts", "ts", r"""
import { api } from './client';

export type Livre = { id: number; titre: string; auteur: string; disponible: boolean };

export const getLivres = () => api.get<Livre[]>('/livres').then((r) => r.data);
export const emprunterLivre = (livreId: number, rendreLe: string) =>
  api.post('/emprunts', { livreId, rendreLe }).then((r) => r.data);
"""), F("Catalogue.tsx", "tsx", r"""
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getLivres, emprunterLivre } from './api/livres';

const dans14Jours = () => new Date(Date.now() + 14 * 864e5).toISOString().slice(0, 10);

export default function Catalogue() {
  const queryClient = useQueryClient();

  const { data: livres, isPending, isError } = useQuery({
    queryKey: ['livres'],
    queryFn: getLivres,
  });

  const emprunt = useMutation({
    mutationFn: (id: number) => emprunterLivre(id, dans14Jours()),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['livres'] }),
  });

  if (isPending) return <p>Chargement…</p>;
  if (isError) return <p role="alert">Erreur de chargement</p>;

  return (
    <ul>
      {livres.map((l) => (
        <li key={l.id}>
          {l.titre}{' '}
          {l.disponible ? (
            <button onClick={() => emprunt.mutate(l.id)} disabled={emprunt.isPending && emprunt.variables === l.id}>
              Emprunter
            </button>
          ) : (
            <em>emprunté</em>
          )}
        </li>
      ))}
    </ul>
  );
}
""")],
  notes=["`main.tsx` : le provider est posé une seule fois, autour de toute l'appli.",
         "`api/livres.ts` est inchangé par rapport au module précédent : TanStack Query réutilise ta couche API.",
         "Dans `Catalogue.tsx`, aucun `useState` ni `useEffect` : tout vient de `useQuery` et `useMutation`.",
         "`emprunt.variables === l.id` désactive uniquement le bouton de la ligne en cours d'envoi."],
  td1=dict(path="Catalogue.tsx",
    files=[F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });
"""), F("api/livres.ts", "ts", r"""
import { api } from './client';

export type Livre = { id: number; titre: string; auteur: string; disponible: boolean };
export type Page = { items: Livre[]; total: number; page: number; pages: number };

export const getLivresPage = (page: number) =>
  api.get<Page>('/livres', { params: { page, parPage: 2 } }).then((r) => r.data);
export const emprunterLivre = (livreId: number, rendreLe: string) =>
  api.post('/emprunts', { livreId, rendreLe }).then((r) => r.data);
"""), F("Catalogue.tsx", "tsx", r"""
import { useState } from 'react';
import axios from 'axios';
import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import { getLivresPage, emprunterLivre } from './api/livres';

export function Catalogue() {
  const [page, setPage] = useState(1);
  // à toi
  return <p>À compléter</p>;
}
"""), F("App.tsx", "tsx", r"""
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Catalogue } from './Catalogue';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Catalogue />
    </QueryClientProvider>
  );
}
""")],
    solution=[F("Catalogue.tsx", "tsx", r"""
import { useState } from 'react';
import axios from 'axios';
import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import { getLivresPage, emprunterLivre } from './api/livres';

export function Catalogue() {
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
              <button onClick={() => emprunt.mutate(l.id)} disabled={emprunt.isPending && emprunt.variables === l.id}>
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
""")],
    run=RUN("react", entry="App.tsx", api=LIB_API, tests=r"""
await waitFor(() => $$('li').length === 2, 4000);
assert.includes(text(), 'Terremer', 'Page 1 : Terremer');
assert.includes(text(), '1 / 3', 'Pagination : 1 / 3');
await click(byText('Suivant'));
await waitFor(() => text().includes('2 / 3') && text().includes('Fondation'), 4000);
assert(true, 'Suivant charge la page 2');
const n = window.__db.calls.filter((c) => c === 'GET /api/livres').length;
await click(byText('Précédent'));
await waitFor(() => text().includes('Terremer'), 1500);
assert(true, 'Retour à la page 1 : affichée depuis le cache');
const ligne = () => $$('li').find((li) => li.textContent.includes('Terremer'));
await click(ligne().querySelector('button'));
await waitFor(() => ligne() && ligne().textContent.includes('emprunté'), 4000);
assert(true, 'Après un emprunt, la liste est rechargée (invalidation)');
assert(!/useState<\s*Livre|setLivres/.test(source('Catalogue.tsx')), 'Les livres ne sont pas recopiés dans un useState');
window.__db.livres[0].disponible = true;
await click(byText('Suivant'));
await waitFor(() => text().includes('Fondation'), 4000);
window.__db.livres.find((l) => l.id === 3).disponible = false;
await click($$('li').find((li) => li.textContent.includes('Fondation')).querySelector('button'));
await waitFor(() => $('[role=alert]'), 4000);
assert.includes($('[role=alert]').textContent, 'Déjà emprunté', '409 : « Déjà emprunté »');
""")),
  tds=[
    TD(2, "Le cache partagé entre deux composants",
       "Deux composants affichent les mêmes données : une liste d'articles et un compteur dans l'en-tête. Avec TanStack Query, ils partagent le cache : **une seule requête**, et une mutation les met à jour **tous les deux** grâce à l'invalidation.",
       ["`api/articles.ts` : `getArticles()`, `createArticle(titre)`, `deleteArticle(id)` qui renvoient `r.data`",
        "`Compteur` : `useQuery(['articles'])` et affiche « N article(s) » dans un `<span className=\"compteur\">`",
        "`Liste` : même clé ; un bouton « Supprimer » par article (`useMutation` + invalidation)",
        "`Ajout` : un formulaire (champ + bouton « Ajouter ») qui crée l'article et invalide `['articles']`",
        "Au chargement, `GET /api/articles` ne doit partir **qu'une fois** malgré les deux composants"],
       [F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });
"""), F("api/articles.ts", "ts", r"""
import { api } from './client';

export type Article = { id: number; titre: string; auteur: string };
// à toi
"""), F("Articles.tsx", "tsx", r"""
import { useState, FormEvent } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getArticles, createArticle, deleteArticle } from './api/articles';

export function Compteur() {
  // à toi
  return null;
}

export function Liste() {
  // à toi
  return null;
}

export function Ajout() {
  // à toi
  return null;
}
"""), F("App.tsx", "tsx", r"""
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Compteur, Liste, Ajout } from './Articles';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <header><Compteur /></header>
      <Ajout />
      <Liste />
    </QueryClientProvider>
  );
}
""")],
       ["Les deux `useQuery` utilisent exactement `queryKey: ['articles']` et `queryFn: getArticles`.",
        "Dans `Ajout`, `mutation.mutate(titre, { onSuccess: () => setTitre('') })` permet de vider le champ seulement en cas de succès.",
        "`deleteArticle` : `api.delete(...).then(() => undefined)` (le serveur répond 204 sans corps)."],
       [F("api/articles.ts", "ts", r"""
import { api } from './client';

export type Article = { id: number; titre: string; auteur: string };

export const getArticles = () => api.get<Article[]>('/articles').then((r) => r.data);
export const createArticle = (titre: string) => api.post<Article>('/articles', { titre }).then((r) => r.data);
export const deleteArticle = (id: number) => api.delete(`/articles/${id}`).then(() => undefined);
"""), F("Articles.tsx", "tsx", r"""
import { useState, FormEvent } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getArticles, createArticle, deleteArticle } from './api/articles';

export function Compteur() {
  const { data } = useQuery({ queryKey: ['articles'], queryFn: getArticles });
  if (!data) return null;
  return <span className="compteur">{data.length} article(s)</span>;
}

export function Liste() {
  const qc = useQueryClient();
  const { data, isPending } = useQuery({ queryKey: ['articles'], queryFn: getArticles });
  const remove = useMutation({
    mutationFn: deleteArticle,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['articles'] }),
  });
  if (isPending) return <p>Chargement…</p>;
  return (
    <ul>
      {data?.map((a) => (
        <li key={a.id}>{a.titre} <button onClick={() => remove.mutate(a.id)}>Supprimer</button></li>
      ))}
    </ul>
  );
}

export function Ajout() {
  const qc = useQueryClient();
  const [titre, setTitre] = useState('');
  const create = useMutation({
    mutationFn: createArticle,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['articles'] }),
  });
  function onSubmit(e: FormEvent) {
    e.preventDefault();
    create.mutate(titre, { onSuccess: () => setTitre('') });
  }
  return (
    <form onSubmit={onSubmit}>
      <input value={titre} onChange={(e) => setTitre(e.target.value)} placeholder="Titre" />
      <button disabled={create.isPending}>Ajouter</button>
      {create.isError && <p role="alert">Titre invalide</p>}
    </form>
  );
}
""")],
       ["Le compteur et la liste changent ensemble après un ajout ou une suppression",
        "Une seule requête GET au chargement"],
       run=RUN("react", entry="App.tsx", api=LIB_API, tests=r"""
await waitFor(() => $$('li').length === 2 && $('.compteur'), 4000);
assert.includes($('.compteur').textContent, '2', 'Compteur : 2 articles');
await tick(300);
assert.equal(window.__db.calls.filter((c) => c === 'GET /api/articles').length, 1, 'Une seule requête GET malgré deux composants');
await type('input', 'Un article tout neuf');
await submit('form');
await waitFor(() => $$('li').length === 3, 4000);
await waitFor(() => $('.compteur').textContent.includes('3'), 3000);
assert(true, 'Après ajout : liste ET compteur à 3');
assert.equal($('input').value, '', 'Le champ est vidé après succès');
await click($$('li')[0].querySelector('button'));
await waitFor(() => $$('li').length === 2 && $('.compteur').textContent.includes('2'), 4000);
assert(true, 'Après suppression : liste ET compteur à 2');
await type('input', 'Ab');
await submit('form');
await waitFor(() => $('[role=alert]'), 4000);
assert(true, 'Titre trop court : erreur affichée');
""")),
    TD(3, "Mise à jour optimiste avec TanStack Query",
       "Le bouton « Emprunter » doit changer l'affichage **instantanément**, avant la réponse du serveur, et revenir en arrière en cas d'erreur. TanStack Query fournit tout ce qu'il faut : lire et écrire le cache à la main (`getQueryData` / `setQueryData`), garder une copie dans `onMutate`, la restaurer dans `onError`, et resynchroniser dans `onSettled`.",
       ["`onMutate(id)` : annule les rechargements en cours (`cancelQueries`), garde une copie de `['livres']`, puis écrit dans le cache le livre avec `disponible: false`",
        "`onMutate` renvoie `{ avant }` ; `onError(err, id, ctx)` restaure `ctx.avant` dans le cache",
        "`onError` affiche aussi `<p role=\"alert\">Emprunt annulé</p>` (via un state ou `mutation.isError`)",
        "`onSettled` invalide `['livres']` pour se resynchroniser avec le serveur",
        "Le livre affiche « emprunté » **immédiatement** après le clic"],
       [F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });
"""), F("api/livres.ts", "ts", r"""
import { api } from './client';

export type Livre = { id: number; titre: string; auteur: string; disponible: boolean };
export const getLivres = () => api.get<Livre[]>('/livres').then((r) => r.data);
export const emprunterLivre = (livreId: number) =>
  api.post('/emprunts', { livreId, rendreLe: '2026-12-31' }).then((r) => r.data);
"""), F("Catalogue.tsx", "tsx", r"""
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getLivres, emprunterLivre, type Livre } from './api/livres';

export function Catalogue() {
  const qc = useQueryClient();
  const { data: livres, isPending } = useQuery({ queryKey: ['livres'], queryFn: getLivres });

  // à toi : useMutation avec onMutate / onError / onSettled

  if (isPending) return <p>Chargement…</p>;
  return (
    <ul>
      {livres?.map((l) => <li key={l.id}>{l.titre}</li>)}
    </ul>
  );
}
"""), F("App.tsx", "tsx", r"""
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Catalogue } from './Catalogue';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Catalogue />
    </QueryClientProvider>
  );
}
""")],
       ["`onMutate: async (id) => { await qc.cancelQueries({ queryKey: ['livres'] }); const avant = qc.getQueryData<Livre[]>(['livres']); ... }`",
        "Écrire : `qc.setQueryData<Livre[]>(['livres'], (old) => old?.map((l) => (l.id === id ? { ...l, disponible: false } : l)))`.",
        "`onError: (_err, _id, ctx) => { if (ctx?.avant) qc.setQueryData(['livres'], ctx.avant); }`"],
       [F("Catalogue.tsx", "tsx", r"""
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getLivres, emprunterLivre, type Livre } from './api/livres';

export function Catalogue() {
  const qc = useQueryClient();
  const { data: livres, isPending } = useQuery({ queryKey: ['livres'], queryFn: getLivres });

  const emprunt = useMutation({
    mutationFn: emprunterLivre,
    onMutate: async (id: number) => {
      await qc.cancelQueries({ queryKey: ['livres'] });
      const avant = qc.getQueryData<Livre[]>(['livres']);
      qc.setQueryData<Livre[]>(['livres'], (old) =>
        old?.map((l) => (l.id === id ? { ...l, disponible: false } : l)),
      );
      return { avant };
    },
    onError: (_err, _id, ctx) => {
      if (ctx?.avant) qc.setQueryData(['livres'], ctx.avant);
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ['livres'] }),
  });

  if (isPending) return <p>Chargement…</p>;
  return (
    <>
      {emprunt.isError && <p role="alert">Emprunt annulé</p>}
      <ul>
        {livres?.map((l) => (
          <li key={l.id}>
            {l.titre}{' '}
            {l.disponible ? <button onClick={() => emprunt.mutate(l.id)}>Emprunter</button> : <em>emprunté</em>}
          </li>
        ))}
      </ul>
    </>
  );
}
""")],
       ["Le livre passe à « emprunté » avant la réponse",
        "Si le serveur refuse, le bouton revient et « Emprunt annulé » s'affiche"],
       run=RUN("react", entry="App.tsx", api=LIB_API, tests=r"""
await waitFor(() => $$('li').length === 5, 4000);
const ligne = (t) => $$('li').find((li) => li.textContent.includes(t));
await click(ligne('Terremer').querySelector('button'));
await tick(40);
assert.includes(ligne('Terremer').textContent, 'emprunté', 'Affichage « emprunté » immédiat (avant la réponse)');
await waitFor(() => window.__db.emprunts.length === 1, 4000);
assert(true, 'Le POST a bien été envoyé');
await tick(500);
window.__api['POST /api/emprunts'] = () => [500, { error: 'boom' }];
await click(ligne('Hypérion').querySelector('button'));
await tick(40);
assert.includes(ligne('Hypérion').textContent, 'emprunté', 'Hypérion : affichage immédiat aussi');
await waitFor(() => $('[role=alert]'), 4000);
await waitFor(() => ligne('Hypérion').querySelector('button'), 3000);
assert(true, 'Échec serveur : Hypérion redevient empruntable (retour arrière)');
assert.includes($('[role=alert]').textContent, 'Emprunt annulé', 'Message « Emprunt annulé »');
""")),
  ])

MODULES = [http, get, mut, org, tq]

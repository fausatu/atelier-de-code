from common import P, L, D, N, E, LANE, F, TD, RUN
from symfony_sim import SYMFONY_SETUP
from httpclient_sim import HTTPCLIENT_SETUP

T = "api"


def DM(id, title, minutes, goal, why, flow, points, pitfalls, quiz, prereq, diagram, lessons, recap, example, notes, tds):
    return {"id": id, "track": T, "title": title, "minutes": minutes, "goal": goal, "why": why,
            "flow": flow, "points": points, "pitfalls": pitfalls, "quiz": quiz, "prereq": prereq,
            "diagram": diagram, "lessons": lessons, "recap": recap,
            "example": {"files": example if isinstance(example, list) else [example], "notes": notes}, "tds": tds}


def Q(q, options, answer, why):
    return {"q": q, "options": options, "answer": answer, "why": why}


def SRUN(tests):
    return RUN("php", tests="Atelier\\App::$echo = false;\nAtelier\\App::reset();\n" + tests, setup=SYMFONY_SETUP)


def HRUN(tests):
    return RUN("php", tests="Symfony\\Component\\HttpClient\\MockHttpClient::$echo = false;\n" + tests, setup=HTTPCLIENT_SETUP)


SF = (" Le bouton Exécuter utilise le **Symfony simulé** : `App::request('POST', '/api/…', $json, $entetes)` envoie une requête "
      "à tes contrôleurs et affiche la réponse avec ses en-têtes (`HTTP> …`).")
HC = (" Le bouton Exécuter utilise un **HttpClient simulé**, identique à celui de Symfony : `MockHttpClient` joue le rôle de l'API "
      "distante et affiche chaque appel (`CLIENT> GET … → 200`).")
JS = " Le bouton Exécuter lance ton module JavaScript avec une **fausse API** (les appels apparaissent dans la sortie) ; les tests appellent tes fonctions."

USES = r"""<?php
declare(strict_types=1);

use Atelier\App;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\EventDispatcher\Attribute\AsEventListener;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpKernel\Attribute\MapRequestPayload;
use Symfony\Component\HttpKernel\Event\ExceptionEvent;
use Symfony\Component\HttpKernel\Event\RequestEvent;
use Symfony\Component\HttpKernel\Event\ResponseEvent;
use Symfony\Component\HttpKernel\Exception\HttpException;
use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;
use Symfony\Component\Routing\Attribute\Route;
use Symfony\Component\Validator\Constraints as Assert;
"""

HC_USES = r"""<?php
declare(strict_types=1);

use Symfony\Component\HttpClient\MockHttpClient;
use Symfony\Component\HttpClient\Response\MockResponse;
use Symfony\Contracts\Cache\CacheInterface;
use Symfony\Contracts\Cache\ItemInterface;
use Symfony\Contracts\HttpClient\Exception\ClientExceptionInterface;
use Symfony\Contracts\HttpClient\Exception\ServerExceptionInterface;
use Symfony\Contracts\HttpClient\Exception\TransportExceptionInterface;
use Symfony\Contracts\HttpClient\HttpClientInterface;
"""

TACHES = r"""
// --- Fourni : un stockage en mémoire (en vrai : Doctrine) ---
final class Tache
{
    public function __construct(public int $id, public string $titre, public bool $faite = false) {}
}

final class TacheStore
{
    private array $taches = [];
    private int $prochainId = 3;

    public function __construct()
    {
        $this->taches = [1 => new Tache(1, 'Lire la doc'), 2 => new Tache(2, 'Écrire les tests', true)];
    }

    /** @return list<Tache> */
    public function tous(): array { return array_values($this->taches); }
    public function trouver(int $id): ?Tache { return $this->taches[$id] ?? null; }
    public function parTitre(string $titre): ?Tache { foreach ($this->taches as $t) if (strcasecmp($t->titre, $titre) === 0) return $t; return null; }
    public function ajouter(string $titre): Tache { $t = new Tache($this->prochainId++, $titre); $this->taches[$t->id] = $t; return $t; }
    public function supprimer(int $id): void { unset($this->taches[$id]); }
}
"""

# =========================================================================== 1. Concevoir
rest = DM("api-rest", "Concevoir une API REST", 25,
  "Choisir des URL, des méthodes et des codes de statut qui disent clairement ce que fait chaque endpoint.",
  "Une API bien conçue se comprend sans documentation et ne surprend personne : le front, l'appli mobile et les partenaires l'utilisent sans te poser de questions.",
  ["Identifier les **ressources** (noms au pluriel)", "Choisir la **méthode** selon l'effet (lire, créer, remplacer, modifier, supprimer)",
   "Choisir le **code de statut** selon le résultat", "Renvoyer la ressource utile (201 + `Location`, 204 sans corps)"],
  ["URL = des noms (`/api/taches/3`), jamais des verbes (`/api/getTache?id=3`).",
   "GET ne modifie rien ; PUT et DELETE sont idempotents ; POST ne l'est pas.",
   "Le statut porte le résultat : pas de `200 { \"success\": false }`.",
   "Création : 201, en-tête `Location` vers la nouvelle ressource, et la ressource dans le corps.",
   "Une action métier qui n'est pas un CRUD devient une sous-ressource : `POST /api/taches/3/terminer`."],
  ["Mettre des verbes dans les URL.", "Toujours répondre 200 avec un champ `success`.", "Utiliser GET pour supprimer (un robot qui suit les liens efface tout)."],
  [Q("Supprimer la tâche 3 :", ["GET /api/deleteTache?id=3", "POST /api/taches/delete/3", "DELETE /api/taches/3", "PATCH /api/taches/3 {\"deleted\": true}"], 2, "La méthode porte l'action, l'URL désigne la ressource."),
   Q("Après une création réussie :", ["200 + { success: true }", "201 + Location + la ressource", "204", "302 vers la liste"], 1, "201 Created dit « une ressource est née », Location dit où."),
   Q("Quelle méthode est idempotente ?", ["POST", "PUT", "aucune", "toutes"], 1, "Envoyer deux fois le même PUT donne le même état qu'une seule fois.")],
  prereq=[
    P("Ressource", "Une « chose » exposée par l'API : une tâche, un projet, un utilisateur. Chaque ressource a une URL (`/api/taches/3`)."),
    P("Collection", "L'ensemble des ressources d'un type : `/api/taches`. On y lit la liste (GET) et on y crée (POST)."),
    P("Idempotent", "Répéter la requête produit le même état que l'envoyer une fois (DELETE deux fois = toujours supprimé)."),
    P("En-tête `Location`", "En-tête de réponse qui donne l'URL d'une ressource, en particulier celle qu'on vient de créer."),
    P("Endpoint", "Une méthode + une URL : `POST /api/taches`."),
  ],
  diagram=D(
    nodes=[
      N("col", 0, 1, "/api/taches", "collection", kind="db", color="accent"),
      N("get", 1, 0, "GET", "200 + liste", kind="pill", color="good"),
      N("post", 1, 2, "POST", "201 + Location", kind="pill", color="warn"),
      N("one", 2, 1, "/api/taches/3", "une ressource", kind="doc", color="accent"),
      N("g1", 3, 0, "GET · PUT · PATCH", "200 · 404", kind="pill", color="good"),
      N("d1", 3, 2, "DELETE", "204 · 404", kind="pill", color="bad"),
    ],
    edges=[E("col", "get"), E("col", "post"), E("col", "one", "/{id}"), E("one", "g1"), E("one", "d1")],
    caption="Deux sortes d'URL : la collection et une ressource. La méthode dit l'action, le statut dit le résultat."),
  lessons=[
    L("Des noms dans l'URL, l'action dans la méthode", r"""
REST part d'une idée simple : l'API expose des **ressources**, chacune avec une URL, et on agit dessus avec les **méthodes HTTP** :

| Action | Requête | Réponse |
|---|---|---|
| Lister | `GET /api/taches` | 200 + tableau |
| Lire | `GET /api/taches/3` | 200, ou 404 |
| Créer | `POST /api/taches` + JSON | 201 + `Location: /api/taches/4` + la tâche |
| Remplacer | `PUT /api/taches/3` + JSON complet | 200 (ou 204) |
| Modifier une partie | `PATCH /api/taches/3` + champs à changer | 200 |
| Supprimer | `DELETE /api/taches/3` | 204 sans corps, ou 404 |

Règles d'écriture : noms au **pluriel**, en minuscules, avec des tirets (`/api/notes-de-frais`), **jamais de verbe** (`/api/getTaches`, `/api/deleteTache`). L'imbrication montre une appartenance (`/api/projets/7/taches`) ; au-delà de deux niveaux, on revient à la ressource seule (`/api/taches/42`).
"""),
    L("Les méthodes et leurs garanties", r"""
Chaque méthode promet quelque chose au client (et aux proxies, caches, navigateurs) :

| Méthode | Modifie ? | Idempotente ? | Usage |
|---|---|---|---|
| GET | non (**sûre**) | oui | lire ; peut être mise en cache, préchargée, rejouée |
| POST | oui | **non** | créer, déclencher une action |
| PUT | oui | oui | remplacer entièrement |
| PATCH | oui | pas forcément | modifier certains champs |
| DELETE | oui | oui | supprimer |

**Idempotent** : envoyer deux fois la même requête laisse le même état qu'une seule fois. Un `DELETE /api/taches/3` répété : la tâche reste supprimée. Un `POST /api/taches` répété : **deux** tâches. C'est pour ça qu'un client peut réessayer un PUT ou un DELETE après une coupure, mais pas un POST sans précaution (voir le module Robustesse).

Une GET qui modifie (`GET /api/deleteTache?id=3`) est dangereuse : un robot, un préchargement du navigateur ou un antivirus qui suit les liens la déclenche.
"""),
    L("Le code de statut porte le résultat", r"""
| Code | Quand |
|---|---|
| 200 OK | lecture ou modification réussie, avec un corps |
| 201 Created | création ; en-tête `Location` + la ressource |
| 204 No Content | succès sans corps (suppression, PUT sans retour) |
| 400 Bad Request | requête mal formée (JSON illisible) |
| 401 Unauthorized | pas authentifié |
| 403 Forbidden | authentifié mais pas le droit |
| 404 Not Found | la ressource n'existe pas |
| 405 Method Not Allowed | la méthode n'existe pas pour cette URL |
| 409 Conflict | conflit avec l'état actuel (doublon, déjà fait) |
| 422 Unprocessable Content | données valides en JSON mais refusées (validation) |
| 500 Internal Server Error | bug serveur |

L'anti-modèle à éviter : `200 { "success": false, "error": "introuvable" }`. Le client doit lire le corps pour savoir si ça a marché, les outils (logs, monitoring, caches) croient que tout va bien, et chaque endpoint invente son format.

En Symfony :

```php
return $this->json($tache, 201, ['Location' => '/api/taches/' . $tache->id]);
return new Response(null, 204);
throw $this->createNotFoundException('Tâche introuvable');   // 404
throw new ConflictHttpException('Ce titre existe déjà');      // 409
```
"""),
    L("Ce qui n'est pas du CRUD", r"""
Beaucoup d'actions métier ne sont ni « créer » ni « modifier un champ » : terminer une tâche, publier un article, annuler une commande. Deux bonnes options :

1. **Une sous-ressource d'action** : `POST /api/taches/3/terminer`. Claire, et le serveur garde la main sur les règles (impossible de « terminer » deux fois → 409).
2. **Un changement d'état** : `PATCH /api/taches/3 {"statut": "terminee"}`, si la transition est vraiment libre.

Préfère la première dès qu'il y a une règle métier : `PATCH {"publie": true}` laisse croire qu'on peut écrire n'importe quoi dans `publie`.

Les **sous-collections** expriment l'appartenance : `GET /api/projets/7/taches` (les tâches du projet 7), `POST /api/projets/7/taches` (créer une tâche **dans** le projet 7 ; 404 si le projet n'existe pas).
"""),
  ],
  recap=["Ressources au pluriel, pas de verbes dans les URL.",
         "GET lit (sûre), POST crée, PUT remplace, PATCH modifie, DELETE supprime.",
         "PUT et DELETE sont idempotents ; POST non.",
         "201 + Location à la création, 204 sans corps, 404/409/422 pour les échecs ; jamais `200 { success: false }`.",
         "Action métier → `POST /ressource/{id}/action`."],
  example=F("TacheController.php", "php", USES + r"""
#[Route('/api/taches')]
final class TacheController extends AbstractController
{
    public function __construct(private TacheStore $store) {}

    #[Route('', methods: ['POST'])]
    public function creer(#[MapRequestPayload] CreerTache $dto): JsonResponse
    {
        $tache = $this->store->ajouter($dto->titre);
        return $this->json($tache, 201, ['Location' => '/api/taches/' . $tache->id]);
    }

    #[Route('/{id}', methods: ['DELETE'])]
    public function supprimer(int $id): Response
    {
        if (!$this->store->trouver($id)) {
            throw $this->createNotFoundException('Tâche introuvable');
        }
        $this->store->supprimer($id);
        return new Response(null, 204);
    }
}
"""),
  notes=["Le préfixe `#[Route('/api/taches')]` sur la classe évite de le répéter.",
         "201 avec l'en-tête `Location` et la tâche créée dans le corps.",
         "204 : succès, sans corps."],
  tds=[
    TD(1, "Le CRUD des tâches, dans les règles",
       "Écris le contrôleur REST complet des tâches. Le stockage est fourni (`TacheStore`)." + SF,
       ["`GET /api/taches` → 200 + la liste ; `GET /api/taches/{id}` → 200 ou 404",
        "`POST /api/taches {\"titre\": …}` → 201 + en-tête `Location: /api/taches/{id}` + la tâche ; titre vide → 422",
        "`PATCH /api/taches/{id}` avec `titre` et/ou `faite` (seulement les champs envoyés) → 200 + la tâche ; 404 si absente",
        "`DELETE /api/taches/{id}` → 204 sans corps ; 404 si absente",
        "Préfixe `/api/taches` sur la classe"],
       [F("Taches.php", "php", USES + TACHES + r"""
final class CreerTache
{
    public function __construct(
        #[Assert\NotBlank]
        #[Assert\Length(max: 100)]
        public string $titre = '',
    ) {}
}

final class ModifierTache
{
    public function __construct(public ?string $titre = null, public ?bool $faite = null) {}
}

// à toi : TacheController

App::request('GET', '/api/taches');
App::request('POST', '/api/taches', ['titre' => 'Déployer']);
""")],
       ["`#[Route('/api/taches')]` sur la classe, puis `#[Route('', methods: ['GET'])]`, `#[Route('/{id}', methods: ['GET'])]`…",
        "`return $this->json($t, 201, ['Location' => '/api/taches/' . $t->id]);`",
        "PATCH : `if ($dto->titre !== null) $t->titre = $dto->titre;` (idem pour `faite`) ; DELETE : `return new Response(null, 204);`"],
       [F("Taches.php", "php", USES + TACHES + r"""
final class CreerTache
{
    public function __construct(
        #[Assert\NotBlank]
        #[Assert\Length(max: 100)]
        public string $titre = '',
    ) {}
}

final class ModifierTache
{
    public function __construct(public ?string $titre = null, public ?bool $faite = null) {}
}

#[Route('/api/taches')]
final class TacheController extends AbstractController
{
    public function __construct(private TacheStore $store) {}

    #[Route('', methods: ['GET'])]
    public function liste(): JsonResponse
    {
        return $this->json($this->store->tous());
    }

    #[Route('/{id}', methods: ['GET'])]
    public function voir(int $id): JsonResponse
    {
        return $this->json($this->trouver($id));
    }

    #[Route('', methods: ['POST'])]
    public function creer(#[MapRequestPayload] CreerTache $dto): JsonResponse
    {
        $t = $this->store->ajouter($dto->titre);
        return $this->json($t, 201, ['Location' => '/api/taches/' . $t->id]);
    }

    #[Route('/{id}', methods: ['PATCH'])]
    public function modifier(int $id, #[MapRequestPayload] ModifierTache $dto): JsonResponse
    {
        $t = $this->trouver($id);
        if ($dto->titre !== null) $t->titre = $dto->titre;
        if ($dto->faite !== null) $t->faite = $dto->faite;
        return $this->json($t);
    }

    #[Route('/{id}', methods: ['DELETE'])]
    public function supprimer(int $id): Response
    {
        $this->trouver($id);
        $this->store->supprimer($id);
        return new Response(null, 204);
    }

    private function trouver(int $id): Tache
    {
        return $this->store->trouver($id) ?? throw $this->createNotFoundException('Tâche introuvable');
    }
}

App::request('GET', '/api/taches');
App::request('POST', '/api/taches', ['titre' => 'Déployer']);
""")],
       ["La création renvoie 201 et `Location`", "La suppression renvoie 204 sans corps"],
       run=SRUN(r"""
$r = App::request('GET', '/api/taches');
check('GET /api/taches → 200 + 2 tâches', $r->status === 200 && count($r->json()) === 2, (string) $r);
check('GET /api/taches/2 → 200', App::request('GET', '/api/taches/2')->json()['titre'] === 'Écrire les tests');
check('GET /api/taches/99 → 404', App::request('GET', '/api/taches/99')->status === 404);
$c = App::request('POST', '/api/taches', ['titre' => 'Déployer']);
check('POST → 201', $c->status === 201, (string) $c);
check('POST → en-tête Location: /api/taches/3', $c->header('Location') === '/api/taches/3', (string) $c);
check('POST → la tâche dans le corps', ($c->json()['titre'] ?? null) === 'Déployer' && ($c->json()['id'] ?? null) === 3);
check('POST titre vide → 422', App::request('POST', '/api/taches', ['titre' => ''])->status === 422);
$p = App::request('PATCH', '/api/taches/1', ['faite' => true]);
check('PATCH faite → 200, titre inchangé', $p->status === 200 && $p->json()['faite'] === true && $p->json()['titre'] === 'Lire la doc', (string) $p);
check('PATCH tâche absente → 404', App::request('PATCH', '/api/taches/99', ['faite' => true])->status === 404);
$d = App::request('DELETE', '/api/taches/1');
check('DELETE → 204 sans corps', $d->status === 204 && $d->json() === null, (string) $d);
check('… et la tâche n\'existe plus', App::request('GET', '/api/taches/1')->status === 404);
check('DELETE tâche absente → 404', App::request('DELETE', '/api/taches/1')->status === 404);
check('PUT /api/taches/2 n\'existe pas → 405', App::request('PUT', '/api/taches/2', ['titre' => 'x'])->status === 405);
""")),
    TD(2, "Réparer une API mal conçue",
       "Cette API marche… mais elle a des verbes dans les URL, supprime avec un GET, et répond **toujours 200** avec `{\"success\": false}` en cas d'erreur. Le front doit lire chaque corps pour savoir si ça a marché. Réécris-la proprement, en gardant le même stockage." + SF,
       ["Plus aucune des anciennes URL (`/api/getTaches`, `/api/getTache`, `/api/createTache`, `/api/deleteTache`) ne doit exister",
        "`GET /api/taches` renvoie directement le tableau (sans enveloppe `success` / `data`)",
        "`GET /api/taches/{id}` → 200 / 404 ; `DELETE /api/taches/{id}` → 204 / 404",
        "`POST /api/taches` → 201 + `Location` ; titre vide → 422 ; **titre déjà existant → 409**"],
       [F("Taches.php", "php", USES + TACHES + r"""
final class TacheController extends AbstractController
{
    public function __construct(private TacheStore $store) {}

    #[Route('/api/getTaches', methods: ['GET'])]
    public function liste(): JsonResponse
    {
        return $this->json(['success' => true, 'data' => $this->store->tous()]);
    }

    #[Route('/api/getTache', methods: ['GET'])]
    public function voir(Request $request): JsonResponse
    {
        $t = $this->store->trouver($request->query->getInt('id'));
        if (!$t) return $this->json(['success' => false, 'error' => 'Tâche introuvable']);
        return $this->json(['success' => true, 'data' => $t]);
    }

    #[Route('/api/createTache', methods: ['POST'])]
    public function creer(Request $request): JsonResponse
    {
        $titre = trim($request->toArray()['titre'] ?? '');
        if ($titre === '') return $this->json(['success' => false, 'error' => 'Titre requis']);
        return $this->json(['success' => true, 'data' => $this->store->ajouter($titre)]);
    }

    #[Route('/api/deleteTache', methods: ['GET'])]
    public function supprimer(Request $request): JsonResponse
    {
        $this->store->supprimer($request->query->getInt('id'));
        return $this->json(['success' => true]);
    }
}

App::request('GET', '/api/getTache?id=99');
App::request('POST', '/api/createTache', ['titre' => '']);
""")],
       ["Une seule classe avec `#[Route('/api/taches')]` et des routes `''` / `'/{id}'` selon la méthode.",
        "Doublon : `$this->store->parTitre($titre)` existe ; lève `new ConflictHttpException('…')` (namespace `Symfony\\Component\\HttpKernel\\Exception`).",
        "Pour le 422, un DTO `CreerTache` avec `#[Assert\\NotBlank]` et `#[MapRequestPayload]` fait le travail."],
       [F("Taches.php", "php", USES + TACHES + r"""
use Symfony\Component\HttpKernel\Exception\ConflictHttpException;

final class CreerTache
{
    public function __construct(#[Assert\NotBlank] public string $titre = '') {}
}

#[Route('/api/taches')]
final class TacheController extends AbstractController
{
    public function __construct(private TacheStore $store) {}

    #[Route('', methods: ['GET'])]
    public function liste(): JsonResponse
    {
        return $this->json($this->store->tous());
    }

    #[Route('/{id}', methods: ['GET'])]
    public function voir(int $id): JsonResponse
    {
        return $this->json($this->store->trouver($id) ?? throw $this->createNotFoundException('Tâche introuvable'));
    }

    #[Route('', methods: ['POST'])]
    public function creer(#[MapRequestPayload] CreerTache $dto): JsonResponse
    {
        $titre = trim($dto->titre);
        if ($this->store->parTitre($titre)) {
            throw new ConflictHttpException('Une tâche porte déjà ce titre');
        }
        $t = $this->store->ajouter($titre);
        return $this->json($t, 201, ['Location' => '/api/taches/' . $t->id]);
    }

    #[Route('/{id}', methods: ['DELETE'])]
    public function supprimer(int $id): Response
    {
        if (!$this->store->trouver($id)) {
            throw $this->createNotFoundException('Tâche introuvable');
        }
        $this->store->supprimer($id);
        return new Response(null, 204);
    }
}

App::request('GET', '/api/taches/99');
App::request('POST', '/api/taches', ['titre' => '']);
""")],
       ["Les erreurs ont enfin de vrais codes", "Plus de verbes dans les URL"],
       run=SRUN(r"""
foreach (['GET /api/getTaches', 'GET /api/getTache?id=1', 'POST /api/createTache', 'GET /api/deleteTache?id=1'] as $old) {
    [$m, $u] = explode(' ', $old);
    check("$old n'existe plus (404)", App::request($m, $u, $m === 'POST' ? ['titre' => 'x'] : null)->status === 404);
}
$l = App::request('GET', '/api/taches');
check('GET /api/taches → le tableau directement', $l->status === 200 && array_is_list($l->json()) && count($l->json()) === 2, (string) $l);
check('GET /api/taches/99 → 404', App::request('GET', '/api/taches/99')->status === 404);
$c = App::request('POST', '/api/taches', ['titre' => 'Déployer']);
check('POST → 201 + Location', $c->status === 201 && $c->header('Location') === '/api/taches/3', (string) $c);
check('POST titre vide → 422', App::request('POST', '/api/taches', ['titre' => ''])->status === 422);
check('POST titre déjà existant → 409', App::request('POST', '/api/taches', ['titre' => 'lire la doc'])->status === 409);
check('DELETE → 204', App::request('DELETE', '/api/taches/2')->status === 204);
check('DELETE absente → 404', App::request('DELETE', '/api/taches/2')->status === 404);
check('aucune réponse ne contient « success »', !str_contains((string) App::request('GET', '/api/taches/1'), 'success'));
""")),
    TD(3, "Sous-ressources et actions métier",
       "Les tâches appartiennent à des **projets**, ont des **étiquettes**, et on peut les **terminer** (une seule fois). Expose ces règles avec des URL REST : sous-collections, action, et opérations idempotentes." + SF,
       ["`GET /api/projets/{id}/taches` → les tâches du projet (404 si le projet n'existe pas) ; `POST` sur la même URL crée une tâche **dans** le projet → 201 + `Location: /api/taches/{id}`",
        "`POST /api/taches/{id}/terminer` → 200 + la tâche ; déjà terminée → **409**",
        "`PUT /api/taches/{id}/etiquettes/{nom}` → 204 (l'appeler deux fois ne crée pas de doublon) ; `DELETE` sur la même URL → 204, **même si l'étiquette n'y était pas** (idempotent)",
        "`GET /api/taches/{id}` → la tâche avec ses étiquettes"],
       [F("Projets.php", "php", USES + r"""
use Symfony\Component\HttpKernel\Exception\ConflictHttpException;

// --- Fourni ---
final class Tache
{
    public array $etiquettes = [];
    public function __construct(public int $id, public int $projetId, public string $titre, public bool $faite = false) {}
}

final class Store
{
    public array $projets = [1 => 'Site vitrine', 2 => 'Appli mobile'];
    public array $taches = [];
    private int $prochainId = 4;

    public function __construct()
    {
        $this->taches = [1 => new Tache(1, 1, 'Maquette'), 2 => new Tache(2, 1, 'Intégration'), 3 => new Tache(3, 2, 'Écran de connexion')];
    }

    public function ajouter(int $projetId, string $titre): Tache { $t = new Tache($this->prochainId++, $projetId, $titre); $this->taches[$t->id] = $t; return $t; }
}

final class CreerTache
{
    public function __construct(#[Assert\NotBlank] public string $titre = '') {}
}

// à toi : ProjetController, TacheController
""")],
       ["Deux contrôleurs : `#[Route('/api/projets/{id}/taches', methods: ['GET'])]`, et `#[Route('/api/taches')]` avec `'/{id}/terminer'`, `'/{id}/etiquettes/{nom}'`.",
        "Les tâches d'un projet : `array_values(array_filter($store->taches, fn(Tache $t) => $t->projetId === $id))`.",
        "PUT d'étiquette : `if (!in_array($nom, $t->etiquettes, true)) $t->etiquettes[] = $nom;` ; DELETE : `array_values(array_diff($t->etiquettes, [$nom]))`."],
       [F("Projets.php", "php", USES + r"""
use Symfony\Component\HttpKernel\Exception\ConflictHttpException;

final class Tache
{
    public array $etiquettes = [];
    public function __construct(public int $id, public int $projetId, public string $titre, public bool $faite = false) {}
}

final class Store
{
    public array $projets = [1 => 'Site vitrine', 2 => 'Appli mobile'];
    public array $taches = [];
    private int $prochainId = 4;

    public function __construct()
    {
        $this->taches = [1 => new Tache(1, 1, 'Maquette'), 2 => new Tache(2, 1, 'Intégration'), 3 => new Tache(3, 2, 'Écran de connexion')];
    }

    public function ajouter(int $projetId, string $titre): Tache { $t = new Tache($this->prochainId++, $projetId, $titre); $this->taches[$t->id] = $t; return $t; }
}

final class CreerTache
{
    public function __construct(#[Assert\NotBlank] public string $titre = '') {}
}

#[Route('/api/projets/{id}/taches')]
final class ProjetController extends AbstractController
{
    public function __construct(private Store $store) {}

    #[Route('', methods: ['GET'])]
    public function taches(int $id): JsonResponse
    {
        $this->projet($id);
        return $this->json(array_values(array_filter($this->store->taches, fn(Tache $t) => $t->projetId === $id)));
    }

    #[Route('', methods: ['POST'])]
    public function creer(int $id, #[MapRequestPayload] CreerTache $dto): JsonResponse
    {
        $this->projet($id);
        $t = $this->store->ajouter($id, $dto->titre);
        return $this->json($t, 201, ['Location' => '/api/taches/' . $t->id]);
    }

    private function projet(int $id): void
    {
        if (!isset($this->store->projets[$id])) {
            throw $this->createNotFoundException('Projet introuvable');
        }
    }
}

#[Route('/api/taches')]
final class TacheController extends AbstractController
{
    public function __construct(private Store $store) {}

    #[Route('/{id}', methods: ['GET'])]
    public function voir(int $id): JsonResponse
    {
        return $this->json($this->tache($id));
    }

    #[Route('/{id}/terminer', methods: ['POST'])]
    public function terminer(int $id): JsonResponse
    {
        $t = $this->tache($id);
        if ($t->faite) {
            throw new ConflictHttpException('Cette tâche est déjà terminée');
        }
        $t->faite = true;
        return $this->json($t);
    }

    #[Route('/{id}/etiquettes/{nom}', methods: ['PUT'])]
    public function etiqueter(int $id, string $nom): Response
    {
        $t = $this->tache($id);
        if (!in_array($nom, $t->etiquettes, true)) {
            $t->etiquettes[] = $nom;
        }
        return new Response(null, 204);
    }

    #[Route('/{id}/etiquettes/{nom}', methods: ['DELETE'])]
    public function retirerEtiquette(int $id, string $nom): Response
    {
        $t = $this->tache($id);
        $t->etiquettes = array_values(array_diff($t->etiquettes, [$nom]));
        return new Response(null, 204);
    }

    private function tache(int $id): Tache
    {
        return $this->store->taches[$id] ?? throw $this->createNotFoundException('Tâche introuvable');
    }
}
""")],
       ["Terminer deux fois → 409", "PUT et DELETE d'étiquette sont idempotents"],
       run=SRUN(r"""
$r = App::request('GET', '/api/projets/1/taches');
check('GET /api/projets/1/taches → les 2 tâches du projet 1', $r->status === 200 && array_column($r->json(), 'id') === [1, 2], (string) $r);
check('projet inconnu → 404', App::request('GET', '/api/projets/9/taches')->status === 404);
$c = App::request('POST', '/api/projets/2/taches', ['titre' => 'Notifications']);
check('POST dans le projet 2 → 201 + Location /api/taches/4', $c->status === 201 && $c->header('Location') === '/api/taches/4' && $c->json()['projetId'] === 2, (string) $c);
check('POST dans un projet inconnu → 404', App::request('POST', '/api/projets/9/taches', ['titre' => 'x'])->status === 404);
$t = App::request('POST', '/api/taches/1/terminer');
check('terminer → 200 + faite', $t->status === 200 && $t->json()['faite'] === true, (string) $t);
check('terminer une 2e fois → 409', App::request('POST', '/api/taches/1/terminer')->status === 409);
check('PUT étiquette → 204', App::request('PUT', '/api/taches/2/etiquettes/urgent')->status === 204);
App::request('PUT', '/api/taches/2/etiquettes/urgent');
check('PUT deux fois : une seule étiquette (idempotent)', App::request('GET', '/api/taches/2')->json()['etiquettes'] === ['urgent']);
check('DELETE étiquette → 204', App::request('DELETE', '/api/taches/2/etiquettes/urgent')->status === 204);
check('DELETE d\'une étiquette absente → 204 aussi (idempotent)', App::request('DELETE', '/api/taches/2/etiquettes/urgent')->status === 204);
check('tâche inconnue → 404', App::request('PUT', '/api/taches/99/etiquettes/x')->status === 404);
""")),
  ])

# =========================================================================== 2. Erreurs
PROB = r"""
// --- Fourni : exceptions métier et contrôleur ---
final class TacheIntrouvable extends DomainException
{
    public function __construct(public readonly int $id) { parent::__construct("La tâche $id n'existe pas."); }
}

final class LimiteAtteinte extends DomainException {}

final class TacheController extends AbstractController
{
    #[Route('/api/taches/{id}', methods: ['GET'])]
    public function voir(int $id): JsonResponse
    {
        if ($id !== 1) throw new TacheIntrouvable($id);
        return $this->json(['id' => 1, 'titre' => 'Lire la doc']);
    }

    #[Route('/api/taches/{id}/dupliquer', methods: ['POST'])]
    public function dupliquer(int $id): JsonResponse
    {
        throw new LimiteAtteinte('Ton offre gratuite est limitée à 10 tâches.');
    }

    #[Route('/api/boum', methods: ['GET'])]
    public function boum(): JsonResponse
    {
        throw new RuntimeException('SQLSTATE[HY000] [1045] Access denied for user root@10.0.3.7 (password: YES)');
    }
}
"""

erreurs = DM("api-erreurs", "Erreurs : un format standard", 25,
  "Renvoyer toutes les erreurs de l'API dans un format unique et standard (Problem Details), et les exploiter côté front.",
  "Si chaque endpoint invente son format d'erreur, le front écrit un cas particulier par écran. Avec un format unique, une seule fonction affiche toutes les erreurs.",
  ["Lister les erreurs possibles (validation, introuvable, conflit, interdit, bug)", "Les traduire **à un seul endroit** (un listener `kernel.exception`)",
   "Renvoyer `application/problem+json` : `type`, `title`, `status`, `detail`", "Côté front : une classe `ApiError` et un message lisible par cas"],
  ["Problem Details (RFC 9457) : `{ type, title, status, detail, instance }` + des champs à toi (`errors`).",
   "En-tête `Content-Type: application/problem+json`.",
   "Les exceptions **métier** (TacheIntrouvable) deviennent des statuts HTTP dans un listener, pas dans chaque contrôleur.",
   "Une erreur inattendue → 500 avec un message **générique** : jamais le message interne (SQL, chemins, mots de passe).",
   "Le front lit `status` pour décider, `detail` pour afficher, `errors` pour placer les messages sous les champs."],
  ["Renvoyer `$e->getMessage()` d'une exception inattendue.", "Un format différent par contrôleur.", "Des `try/catch` partout dans les contrôleurs."],
  [Q("Quel champ Problem Details donne une explication pour CETTE occurrence ?", ["type", "title", "detail", "status"], 2, "title est générique, detail est spécifique."),
   Q("Une PDOException inattendue doit produire…", ["500 + le message SQL", "500 + un message générique", "200", "422"], 1, "Le détail technique va dans les logs, pas au client."),
   Q("Où transformer TacheIntrouvable en 404 ?", ["dans chaque contrôleur", "dans un listener kernel.exception", "dans le front", "dans l'entité"], 1, "Un seul endroit pour toute l'API.")],
  prereq=[
    P("Problem Details", "Format standard d'erreur HTTP (RFC 9457) : un objet JSON avec `type`, `title`, `status`, `detail`, `instance`, servi en `application/problem+json`."),
    P("Exception métier", "Exception qui porte une règle du domaine (`TacheIntrouvable`, `LimiteAtteinte`), sans rien savoir de HTTP."),
    P("Listener `kernel.exception`", "Classe appelée par Symfony quand une exception sort d'un contrôleur ; elle peut fabriquer la réponse."),
    P("Fuite d'information", "Renvoyer au client des détails internes (requête SQL, chemin de fichier, mot de passe) qui aident un attaquant."),
  ],
  diagram=D(
    nodes=[
      N("c", 0, 1, "Contrôleur", "throw TacheIntrouvable", kind="file", color="accent"),
      N("l", 1, 1, "Listener", "kernel.exception", kind="box", color="warn"),
      N("r", 2, 1, "problem+json", "type, title, status…", kind="doc", color="good"),
      N("f", 3, 1, "Front : ApiError", "un message par cas", kind="file", color="accent"),
      N("log", 1, 0, "Logs", "le détail technique", kind="db", color="muted"),
    ],
    edges=[E("c", "l"), E("l", "r"), E("r", "f"), E("l", "log", dashed=True)],
    caption="Les exceptions remontent jusqu'à un seul listener qui fabrique la réponse standard ; le détail technique va dans les logs, jamais dans la réponse."),
  lessons=[
    L("Un format pour toutes les erreurs", r"""
Problem Details (RFC 9457) est le format standard d'erreur des API HTTP :

```http
HTTP/1.1 404 Not Found
Content-Type: application/problem+json

{
  "type": "https://api.exemple.com/problemes/tache-introuvable",
  "title": "Tâche introuvable",
  "status": 404,
  "detail": "La tâche 42 n'existe pas.",
  "instance": "/api/taches/42"
}
```

| Champ | Rôle |
|---|---|
| `type` | identifiant **stable** du genre d'erreur (une URL, ou `about:blank` pour une erreur HTTP générique) ; le front peut s'y fier |
| `title` | résumé humain du type, toujours le même |
| `status` | le code HTTP (répété pour les clients qui ne voient que le corps) |
| `detail` | explication de **cette** occurrence |
| `instance` | l'URL concernée |

On peut ajouter ses propres champs : `"errors": [{"champ": "email", "message": "…"}]` pour la validation, `"limite": 10`…

Symfony sait produire ce format pour ses propres erreurs (validation de `#[MapRequestPayload]`, avec `violations`).
"""),
    L("Traduire les exceptions à un seul endroit", r"""
Les contrôleurs et services lèvent des **exceptions métier**, sans penser à HTTP. Un listener les traduit toutes :

```php
#[AsEventListener(event: 'kernel.exception')]
final class ProblemeListener
{
    public function __invoke(ExceptionEvent $event): void
    {
        $e = $event->getThrowable();
        [$status, $type, $titre, $detail] = match (true) {
            $e instanceof TacheIntrouvable => [404, 'tache-introuvable', 'Tâche introuvable', $e->getMessage()],
            $e instanceof HttpException    => [$e->getStatusCode(), null, self::TITRES[$e->getStatusCode()] ?? 'Erreur', $e->getMessage()],
            default                        => [500, null, 'Erreur interne', 'Une erreur interne est survenue.'],
        };
        $event->setResponse(new JsonResponse([
            'type' => $type ? "https://api.exemple.com/problemes/$type" : 'about:blank',
            'title' => $titre, 'status' => $status, 'detail' => $detail,
            'instance' => $event->getRequest()->getPathInfo(),
        ], $status, ['Content-Type' => 'application/problem+json']));
    }
}
```

La règle de sécurité : pour une erreur **inattendue** (le `default`), on n'envoie **jamais** `$e->getMessage()`. Il peut contenir une requête SQL, un chemin, un identifiant de base. Le détail va dans les logs (`$this->logger->error(...)`), le client reçoit un message générique.

(Le module Architecture montrait le même mécanisme avec un format maison `{ code, message }` ; Problem Details est la version standard.)
"""),
    L("Exploiter les erreurs côté front", r"""
Avec un format unique, une seule fonction suffit :

```js
export class ApiError extends Error {
  constructor(status, probleme) {
    super(probleme?.detail || probleme?.title || `Erreur HTTP ${status}`);
    this.status = status;
    this.type = probleme?.type ?? 'about:blank';
    this.errors = probleme?.errors ?? [];
  }
}

export async function appel(url, init) {
  const res = await fetch(url, init);
  if (res.ok) return res.status === 204 ? null : res.json();
  const probleme = await res.json().catch(() => null);     // une 502 du proxy n'est pas du JSON
  throw new ApiError(res.status, probleme);
}
```

Ensuite, chaque écran décide quoi montrer selon le **statut** ou le **type** :

- 401 : renvoyer vers la connexion ; 403 : « tu n'as pas le droit » ;
- 404 : « introuvable » ; 409 : afficher `detail` (c'est un message métier) ;
- 422 : placer chaque message de `errors` sous son champ ;
- 5xx ou coupure réseau : « le service a un souci, réessaie » (et ne jamais afficher un message technique).
"""),
  ],
  recap=["Problem Details : `type`, `title`, `status`, `detail`, `instance`, en `application/problem+json`.",
         "Exceptions métier dans le code, traduction HTTP dans **un** listener.",
         "Erreur inattendue → 500 + message générique ; le détail technique dans les logs.",
         "Champs à toi pour le reste (`errors` pour la validation).",
         "Front : une classe `ApiError` + un message par statut."],
  example=F("ProblemeListener.php", "php", USES + r"""
#[AsEventListener(event: 'kernel.exception')]
final class ProblemeListener
{
    public function __invoke(ExceptionEvent $event): void
    {
        $e = $event->getThrowable();
        [$status, $titre, $detail] = match (true) {
            $e instanceof TacheIntrouvable => [404, 'Tâche introuvable', $e->getMessage()],
            $e instanceof HttpException => [$e->getStatusCode(), 'Erreur HTTP', $e->getMessage()],
            default => [500, 'Erreur interne', 'Une erreur interne est survenue.'],   // jamais $e->getMessage()
        };
        $event->setResponse(new JsonResponse(
            ['type' => 'about:blank', 'title' => $titre, 'status' => $status, 'detail' => $detail, 'instance' => $event->getRequest()->getPathInfo()],
            $status,
            ['Content-Type' => 'application/problem+json'],
        ));
    }
}
"""),
  notes=["Un `match (true)` choisit le statut selon la classe de l'exception.", "Le cas `default` ne révèle rien.", "L'en-tête annonce le format Problem Details."],
  tds=[
    TD(1, "Un listener Problem Details",
       "Aujourd'hui, l'API renvoie `{\"error\": \"…\"}` avec le message brut de l'exception, y compris pour une erreur SQL **qui révèle un identifiant de base de données**. Écris un listener qui transforme toutes les exceptions en Problem Details." + SF,
       ["`TacheIntrouvable` → 404, type `https://api.exemple.com/problemes/tache-introuvable`, title `Tâche introuvable`, detail = message de l'exception",
        "`LimiteAtteinte` → 409, type `…/problemes/limite-atteinte`, title `Limite atteinte`",
        "`HttpException` (route inconnue, etc.) → son statut, type `about:blank`, title selon le tableau `TITRES`",
        "Toute autre exception → 500, title `Erreur interne`, detail `Une erreur interne est survenue.` (rien du message d'origine)",
        "Toujours : `instance` = chemin de la requête, en-tête `Content-Type: application/problem+json`"],
       [F("Api.php", "php", USES + PROB + r"""
// à toi : ProblemeListener

App::request('GET', '/api/taches/42');
App::request('GET', '/api/boum');
"""), F("Titres.php", "php", r"""
<?php
// Fourni : les titres des statuts HTTP courants
const TITRES = [400 => 'Bad Request', 401 => 'Unauthorized', 403 => 'Forbidden', 404 => 'Not Found', 405 => 'Method Not Allowed', 409 => 'Conflict', 422 => 'Unprocessable Content', 500 => 'Internal Server Error'];
""")],
       ["`#[AsEventListener(event: 'kernel.exception')]` sur une classe avec `__invoke(ExceptionEvent $event)`.",
        "`match (true) { $e instanceof TacheIntrouvable => […], … default => […] }`.",
        "`$event->setResponse(new JsonResponse($probleme, $status, ['Content-Type' => 'application/problem+json']));` et `$event->getRequest()->getPathInfo()`."],
       [F("Api.php", "php", USES + PROB + r"""
#[AsEventListener(event: 'kernel.exception')]
final class ProblemeListener
{
    private const BASE = 'https://api.exemple.com/problemes/';

    public function __invoke(ExceptionEvent $event): void
    {
        $e = $event->getThrowable();
        [$status, $type, $titre, $detail] = match (true) {
            $e instanceof TacheIntrouvable => [404, self::BASE . 'tache-introuvable', 'Tâche introuvable', $e->getMessage()],
            $e instanceof LimiteAtteinte => [409, self::BASE . 'limite-atteinte', 'Limite atteinte', $e->getMessage()],
            $e instanceof HttpException => [$e->getStatusCode(), 'about:blank', TITRES[$e->getStatusCode()] ?? 'Erreur', $e->getMessage()],
            default => [500, 'about:blank', 'Erreur interne', 'Une erreur interne est survenue.'],
        };
        $event->setResponse(new JsonResponse([
            'type' => $type,
            'title' => $titre,
            'status' => $status,
            'detail' => $detail,
            'instance' => $event->getRequest()->getPathInfo(),
        ], $status, ['Content-Type' => 'application/problem+json']));
    }
}

App::request('GET', '/api/taches/42');
App::request('GET', '/api/boum');
""")],
       ["La 500 ne révèle plus rien", "Toutes les erreurs ont le même format"],
       run=SRUN(r"""
$r = App::request('GET', '/api/taches/42');
check('TacheIntrouvable → 404', $r->status === 404, (string) $r);
check('Content-Type: application/problem+json', $r->header('Content-Type') === 'application/problem+json', (string) $r);
check('corps Problem Details complet', $r->json() === ['type' => 'https://api.exemple.com/problemes/tache-introuvable', 'title' => 'Tâche introuvable', 'status' => 404, 'detail' => "La tâche 42 n'existe pas.", 'instance' => '/api/taches/42'], (string) $r);
$l = App::request('POST', '/api/taches/1/dupliquer');
check('LimiteAtteinte → 409 limite-atteinte', $l->status === 409 && str_ends_with($l->json()['type'] ?? '', '/limite-atteinte') && $l->json()['title'] === 'Limite atteinte', (string) $l);
$n = App::request('GET', '/api/inexistant');
check('route inconnue → 404 about:blank, title Not Found', $n->status === 404 && $n->json()['type'] === 'about:blank' && $n->json()['title'] === 'Not Found', (string) $n);
$b = App::request('GET', '/api/boum');
check('erreur inattendue → 500 générique', $b->status === 500 && $b->json()['detail'] === 'Une erreur interne est survenue.', (string) $b);
check('… sans aucune fuite (SQL, IP, utilisateur)', !preg_match('/SQLSTATE|root|10\.0\.3\.7|password/i', (string) $b), (string) $b);
check('la réponse normale reste intacte', App::request('GET', '/api/taches/1')->json() === ['id' => 1, 'titre' => 'Lire la doc']);
""")),
    TD(2, "Erreurs de validation détaillées",
       "L'inscription valide des règles **métier** que les attributs ne savent pas exprimer (âge minimum, pseudo déjà pris). Le front veut afficher chaque message **sous le bon champ** : renvoie une 422 Problem Details avec une liste `errors`." + SF,
       ["`Validateur::verifier(array $donnees)` lève `DonneesInvalides` avec **toutes** les erreurs d'un coup : `email` invalide (`Adresse email invalide`), `age` < 16 (`Il faut avoir 16 ans`), `pseudo` déjà pris (`Ce pseudo est déjà pris`, pseudos pris : `admin`, `ana`)",
        "Le listener transforme `DonneesInvalides` en 422 : type `…/problemes/donnees-invalides`, title `Données invalides`, detail `2 champs sont invalides.` (nombre réel, au singulier si 1), et `errors: [{\"champ\": …, \"message\": …}]`",
        "Données valides → 201 `{\"pseudo\": …}`",
        "Content-Type `application/problem+json`"],
       [F("Inscription.php", "php", USES + r"""
final class DonneesInvalides extends DomainException
{
    /** @param array<string, string> $erreurs  champ => message */
    public function __construct(public readonly array $erreurs)
    {
        parent::__construct(count($erreurs) . ' champ(s) invalide(s)');
    }
}

final class Validateur
{
    private const PRIS = ['admin', 'ana'];

    public function verifier(array $d): void
    {
        // à toi : accumuler les erreurs, puis lever DonneesInvalides s'il y en a
    }
}

final class InscriptionController extends AbstractController
{
    #[Route('/api/inscriptions', methods: ['POST'])]
    public function inscrire(Request $request, Validateur $validateur): JsonResponse
    {
        $d = $request->toArray();
        $validateur->verifier($d);
        return $this->json(['pseudo' => $d['pseudo']], 201);
    }
}

// à toi : le listener

App::request('POST', '/api/inscriptions', ['email' => 'ana@', 'age' => 14, 'pseudo' => 'ana']);
""")],
       ["`$erreurs = []; if (!filter_var($d['email'] ?? '', FILTER_VALIDATE_EMAIL)) $erreurs['email'] = '…';` puis les autres règles ; à la fin `if ($erreurs) throw new DonneesInvalides($erreurs);`.",
        "`errors` : `array_map(fn($champ, $msg) => ['champ' => $champ, 'message' => $msg], array_keys($e->erreurs), $e->erreurs)`.",
        "Pluriel : `$n === 1 ? '1 champ est invalide.' : \"$n champs sont invalides.\"`."],
       [F("Inscription.php", "php", USES + r"""
final class DonneesInvalides extends DomainException
{
    /** @param array<string, string> $erreurs  champ => message */
    public function __construct(public readonly array $erreurs)
    {
        parent::__construct(count($erreurs) . ' champ(s) invalide(s)');
    }
}

final class Validateur
{
    private const PRIS = ['admin', 'ana'];

    public function verifier(array $d): void
    {
        $erreurs = [];
        if (!filter_var($d['email'] ?? '', FILTER_VALIDATE_EMAIL)) $erreurs['email'] = 'Adresse email invalide';
        if (!is_int($d['age'] ?? null) || $d['age'] < 16) $erreurs['age'] = 'Il faut avoir 16 ans';
        if (in_array(strtolower($d['pseudo'] ?? ''), self::PRIS, true)) $erreurs['pseudo'] = 'Ce pseudo est déjà pris';
        if ($erreurs) {
            throw new DonneesInvalides($erreurs);
        }
    }
}

final class InscriptionController extends AbstractController
{
    #[Route('/api/inscriptions', methods: ['POST'])]
    public function inscrire(Request $request, Validateur $validateur): JsonResponse
    {
        $d = $request->toArray();
        $validateur->verifier($d);
        return $this->json(['pseudo' => $d['pseudo']], 201);
    }
}

#[AsEventListener(event: 'kernel.exception')]
final class ProblemeListener
{
    public function __invoke(ExceptionEvent $event): void
    {
        $e = $event->getThrowable();
        if (!$e instanceof DonneesInvalides) {
            return;
        }
        $n = count($e->erreurs);
        $event->setResponse(new JsonResponse([
            'type' => 'https://api.exemple.com/problemes/donnees-invalides',
            'title' => 'Données invalides',
            'status' => 422,
            'detail' => $n === 1 ? '1 champ est invalide.' : "$n champs sont invalides.",
            'instance' => $event->getRequest()->getPathInfo(),
            'errors' => array_map(fn(string $champ, string $msg) => ['champ' => $champ, 'message' => $msg], array_keys($e->erreurs), $e->erreurs),
        ], 422, ['Content-Type' => 'application/problem+json']));
    }
}

App::request('POST', '/api/inscriptions', ['email' => 'ana@', 'age' => 14, 'pseudo' => 'ana']);
""")],
       ["Les 3 erreurs arrivent ensemble", "Une seule erreur → « 1 champ est invalide. »"],
       run=SRUN(r"""
$r = App::request('POST', '/api/inscriptions', ['email' => 'ana@', 'age' => 14, 'pseudo' => 'Ana']);
check('422 + problem+json', $r->status === 422 && $r->header('Content-Type') === 'application/problem+json', (string) $r);
check('les 3 erreurs, chacune sous son champ', ($r->json()['errors'] ?? null) === [['champ' => 'email', 'message' => 'Adresse email invalide'], ['champ' => 'age', 'message' => 'Il faut avoir 16 ans'], ['champ' => 'pseudo', 'message' => 'Ce pseudo est déjà pris']], (string) $r);
check('detail : « 3 champs sont invalides. »', ($r->json()['detail'] ?? '') === '3 champs sont invalides.');
check('type et title', ($r->json()['type'] ?? '') === 'https://api.exemple.com/problemes/donnees-invalides' && $r->json()['title'] === 'Données invalides');
$u = App::request('POST', '/api/inscriptions', ['email' => 'zoe@mail.fr', 'age' => 15, 'pseudo' => 'zoe']);
check('une seule erreur : « 1 champ est invalide. »', $u->status === 422 && $u->json()['detail'] === '1 champ est invalide.' && count($u->json()['errors']) === 1, (string) $u);
$ok = App::request('POST', '/api/inscriptions', ['email' => 'zoe@mail.fr', 'age' => 30, 'pseudo' => 'zoe']);
check('données valides → 201', $ok->status === 201 && $ok->json() === ['pseudo' => 'zoe'], (string) $ok);
""")),
    TD(3, "Côté front : une erreur, un message",
       "Le front appelle une API qui renvoie des Problem Details. Écris le module qui transforme **toute** réponse en erreur exploitable, puis la fonction qui choisit le message à afficher." + JS,
       ["`appel(url, init)` : renvoie le JSON (ou `null` pour 204) ; sinon lève une `ApiError` avec `status`, `type`, `detail`, `errors` (tableau vide par défaut)",
        "Une réponse d'erreur qui n'est **pas** du JSON (proxy en panne) doit quand même donner une `ApiError` (detail par défaut `Erreur HTTP 502`)",
        "Une coupure réseau (fetch qui rejette) → `ApiError` avec `status: 0`",
        "`messagePour(err)` : 0 → `Pas de connexion`, 401 → `Connecte-toi pour continuer`, 403 → `Tu n'as pas le droit de faire ça`, 404 → `Introuvable`, 409 et 422 → le `detail` du serveur, ≥ 500 → `Le service a un souci, réessaie dans un instant`"],
       [F("api.js", "js", r"""
export class ApiError extends Error {
  // à toi
}

export async function appel(url, init) {
  // à toi
}

export function messagePour(err) {
  // à toi
}
""")],
       ["`const res = await fetch(url, init)` dans un `try/catch` : le `catch` = coupure réseau → `new ApiError(0, { detail: 'Pas de connexion' })`.",
        "`const probleme = await res.json().catch(() => null);` évite de planter sur un corps non JSON.",
        "Dans le constructeur : `super(probleme?.detail || probleme?.title || 'Erreur HTTP ' + status);`"],
       [F("api.js", "js", r"""
export class ApiError extends Error {
  constructor(status, probleme) {
    super((probleme && (probleme.detail || probleme.title)) || 'Erreur HTTP ' + status);
    this.name = 'ApiError';
    this.status = status;
    this.type = (probleme && probleme.type) || 'about:blank';
    this.detail = this.message;
    this.errors = (probleme && probleme.errors) || [];
  }
}

export async function appel(url, init) {
  let res;
  try {
    res = await fetch(url, init);
  } catch (e) {
    throw new ApiError(0, { detail: 'Pas de connexion' });
  }
  if (res.ok) return res.status === 204 ? null : res.json();
  const probleme = await res.json().catch(() => null);
  throw new ApiError(res.status, probleme);
}

export function messagePour(err) {
  if (!(err instanceof ApiError)) return 'Erreur inattendue';
  if (err.status === 0) return 'Pas de connexion';
  if (err.status === 401) return 'Connecte-toi pour continuer';
  if (err.status === 403) return "Tu n'as pas le droit de faire ça";
  if (err.status === 404) return 'Introuvable';
  if (err.status === 409 || err.status === 422) return err.detail;
  if (err.status >= 500) return 'Le service a un souci, réessaie dans un instant';
  return err.detail;
}
""")],
       ["Les 422 gardent leurs `errors`", "Une 502 non JSON ne fait pas planter"],
       run=RUN("js", entry="api.js", api=r"""
const prob = (status, extra) => [status, Object.assign({ type: 'about:blank', title: 'Erreur', status, detail: 'Détail ' + status }, extra || {}), { 'content-type': 'application/problem+json' }];
__api["GET /api/taches/1"] = () => ({ id: 1, titre: 'Lire la doc' });
__api["DELETE /api/taches/1"] = () => [204, null];
__api["GET /api/taches/9"] = () => prob(404, { title: 'Tâche introuvable', detail: "La tâche 9 n'existe pas." });
__api["POST /api/inscriptions"] = () => prob(422, { detail: '2 champs sont invalides.', errors: [{ champ: 'email', message: 'Adresse email invalide' }, { champ: 'age', message: 'Il faut avoir 16 ans' }] });
__api["POST /api/taches/1/terminer"] = () => prob(409, { detail: 'Cette tâche est déjà terminée' });
__api["GET /api/prive"] = () => prob(401);
__api["GET /api/admin"] = () => prob(403);
__api["GET /api/boum"] = () => [502, null];
""", tests=r"""
const { ApiError, appel, messagePour } = require('./api');
const t = await appel('/api/taches/1');
assert(t && t.titre === 'Lire la doc', 'Réponse 200 : le JSON');
assert.equal(await appel('/api/taches/1', { method: 'DELETE' }), null, '204 → null');
const essai = async (url, init) => { try { await appel(url, init); return null; } catch (e) { return e; } };
const e404 = await essai('/api/taches/9');
assert(e404 instanceof ApiError && e404 instanceof Error, '404 → une ApiError (qui est aussi une Error)');
assert(e404.status === 404 && e404.detail === "La tâche 9 n'existe pas.", 'ApiError porte status et detail');
const e422 = await essai('/api/inscriptions', { method: 'POST', body: JSON.stringify({}) });
assert(e422.status === 422 && e422.errors.length === 2 && e422.errors[0].champ === 'email', '422 : errors conservées');
const e502 = await essai('/api/boum');
assert(e502 instanceof ApiError && e502.status === 502 && e502.detail === 'Erreur HTTP 502', '502 sans JSON → ApiError « Erreur HTTP 502 »');
const realFetch = window.fetch;
window.fetch = () => Promise.reject(new TypeError('Failed to fetch'));
const e0 = await essai('/api/taches/1');
window.fetch = realFetch;
assert(e0 instanceof ApiError && e0.status === 0, 'Coupure réseau → ApiError status 0');
assert.equal(messagePour(e0), 'Pas de connexion', '0 → Pas de connexion');
assert.equal(messagePour(await essai('/api/prive')), 'Connecte-toi pour continuer', '401');
assert.equal(messagePour(await essai('/api/admin')), "Tu n'as pas le droit de faire ça", '403');
assert.equal(messagePour(e404), 'Introuvable', '404');
assert.equal(messagePour(await essai('/api/taches/1/terminer', { method: 'POST' })), 'Cette tâche est déjà terminée', '409 → detail du serveur');
assert.equal(messagePour(e422), '2 champs sont invalides.', '422 → detail du serveur');
assert.equal(messagePour(e502), 'Le service a un souci, réessaie dans un instant', '5xx → message générique');
""")),
  ])

# =========================================================================== 3. Auth
TOKENS = r"""
// --- Fourni : jetons valides (en vrai : base de données, ou JWT signés) ---
final class Utilisateur
{
    public function __construct(public int $id, public string $nom, public array $roles = ['ROLE_USER']) {}
    public function estAdmin(): bool { return in_array('ROLE_ADMIN', $this->roles, true); }
}

final class Jetons
{
    private array $parJeton;

    public function __construct()
    {
        $this->parJeton = [
            'jeton-ana' => new Utilisateur(1, 'Ana'),
            'jeton-leo' => new Utilisateur(2, 'Léo'),
            'jeton-admin' => new Utilisateur(3, 'Admin', ['ROLE_USER', 'ROLE_ADMIN']),
        ];
    }

    public function utilisateur(string $jeton): ?Utilisateur { return $this->parJeton[$jeton] ?? null; }
}
"""

auth = DM("api-auth", "Authentifier et autoriser", 25,
  "Protéger une API : savoir qui appelle (authentification), ce qu'il a le droit de faire (autorisation), et vérifier un jeton.",
  "Une API publique sur Internet est appelée par n'importe qui. Distinguer 401 et 403, vérifier les droits sur chaque ressource et valider un jeton correctement, c'est la base de la sécurité.",
  ["Lire l'identité dans l'en-tête `Authorization: Bearer …`", "Pas d'identité ou jeton invalide → **401** (+ `WWW-Authenticate`)",
   "Identité connue mais pas le droit → **403** ; ressource absente → 404", "Vérifier les droits **sur la ressource** (propriétaire, rôle), à chaque requête"],
  ["401 = « qui es-tu ? » ; 403 = « je sais qui tu es, et c'est non ».",
   "Le jeton voyage dans `Authorization: Bearer <jeton>`, jamais dans l'URL (elle finit dans les logs).",
   "Un JWT se **vérifie** (signature + expiration) avant d'être cru ; le décoder ne suffit pas.",
   "Les droits se vérifient côté serveur, sur chaque ressource : cacher un bouton côté front n'est pas une protection.",
   "Symfony : firewall + `#[IsGranted]` + Voters ; ici on écrit la mécanique à la main pour la comprendre."],
  ["Renvoyer 403 quand personne n'est connecté.", "Mettre le jeton dans l'URL (`?token=`).", "Croire le contenu d'un JWT sans vérifier sa signature."],
  [Q("Requête sans en-tête Authorization sur une route protégée :", ["400", "401", "403", "404"], 1, "On ne sait pas qui appelle : 401."),
   Q("Léo modifie une note d'Ana :", ["401", "403", "404", "409"], 1, "Léo est identifié mais n'a pas le droit."),
   Q("Un JWT dont la signature est fausse mais le contenu lisible :", ["on lit le contenu quand même", "on le refuse (401)", "on renvoie 403", "on le renouvelle"], 1, "N'importe qui peut fabriquer un contenu ; seule la signature prouve l'origine.")],
  prereq=[
    P("Authentification", "Savoir **qui** fait la requête (via un mot de passe, un jeton, une session)."),
    P("Autorisation", "Savoir si cette personne a **le droit** de faire cette action sur cette ressource."),
    P("Jeton (token)", "Une chaîne remise après connexion, renvoyée à chaque requête dans `Authorization: Bearer <jeton>`."),
    P("JWT", "Un jeton en trois parties `entête.contenu.signature` (base64url). Le contenu est lisible par tous ; la signature prouve qu'il vient du serveur et n'a pas été modifié."),
    P("HMAC", "Une signature calculée avec un secret partagé : sans le secret, impossible de produire la bonne signature."),
  ],
  diagram=D(
    nodes=[
      N("rq", 0, 1, "Requête", "Bearer …", kind="doc"),
      N("q1", 1, 1, "Jeton valide ?", "signature, expiration", kind="note", color="warn"),
      N("e401", 1, 0, "401", "WWW-Authenticate", kind="pill", color="bad"),
      N("q2", 2, 1, "Droit sur l'objet ?", "propriétaire, rôle", kind="note", color="warn"),
      N("e403", 2, 0, "403", "interdit", kind="pill", color="bad"),
      N("ok", 3, 1, "Contrôleur", "200 / 201 / 204", kind="pill", color="good"),
    ],
    edges=[E("rq", "q1"), E("q1", "e401", "non"), E("q1", "q2", "oui"), E("q2", "e403", "non"), E("q2", "ok", "oui")],
    caption="Deux questions, dans cet ordre : qui es-tu (401 sinon), puis as-tu le droit sur cette ressource (403 sinon)."),
  lessons=[
    L("401 ou 403 ?", r"""
- **401 Unauthorized** (le nom est trompeur) : la requête n'est **pas authentifiée**. Pas de jeton, jeton inconnu, expiré, mal signé. La réponse inclut `WWW-Authenticate: Bearer` pour dire comment s'authentifier. Le front réagit en renvoyant vers la connexion (ou en rafraîchissant le jeton).
- **403 Forbidden** : la requête est authentifiée, mais **pas autorisée**. Léo veut modifier la note d'Ana, un utilisateur normal veut supprimer un compte. Se reconnecter ne changera rien.

Cas particulier : pour une ressource privée, on renvoie parfois **404** au lieu de 403, pour ne pas révéler qu'elle existe (« la commande 1234 d'un autre client »).

Ordre des vérifications : 401 d'abord (avant même de chercher la ressource), puis 404, puis 403.
"""),
    L("Le jeton dans l'en-tête Authorization", r"""
Après connexion (`POST /api/connexion` avec email + mot de passe), l'API remet un **jeton**. Le client le renvoie à chaque requête :

```http
GET /api/moi HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOjF9.4f2c…
```

Côté serveur, la vérification se fait **une fois, avant les contrôleurs** : un listener `kernel.request` (ou, dans un vrai projet, le **firewall** de Symfony avec un authenticator) lit l'en-tête, retrouve l'utilisateur, et le range dans la requête :

```php
#[AsEventListener(event: 'kernel.request')]
final class Authentification
{
    public function __invoke(RequestEvent $event): void
    {
        $h = $event->getRequest()->headers->get('Authorization', '');
        if (!preg_match('/^Bearer (\S+)$/', $h, $m) || !($u = $this->jetons->utilisateur($m[1]))) {
            throw new UnauthorizedHttpException('Bearer', 'Jeton manquant ou invalide');
        }
        $event->getRequest()->attributes->set('utilisateur', $u);
    }
}
```

Règles : jamais de jeton dans l'URL (`?token=…` finit dans les logs et l'historique), toujours HTTPS, et côté navigateur, de préférence un cookie `HttpOnly` plutôt que `localStorage` (inaccessible au JavaScript, donc à une faille XSS).
"""),
    L("Les droits se vérifient sur la ressource", r"""
« Seul l'auteur peut modifier sa note, un admin peut tout faire » : cette règle se vérifie **dans le serveur, pour chaque ressource**, après l'avoir chargée :

```php
$note = $this->notes->trouver($id) ?? throw $this->createNotFoundException();
if ($note->auteurId !== $moi->id && !$moi->estAdmin()) {
    throw new AccessDeniedHttpException('Ce n\'est pas ta note');
}
```

Cacher le bouton « Modifier » dans le front n'empêche rien : n'importe qui peut envoyer la requête avec curl. Les failles les plus fréquentes des API (OWASP « Broken Object Level Authorization ») viennent exactement de là : l'API vérifie qu'on est connecté, mais pas qu'on a le droit sur **cet** objet.

En Symfony, cette logique va dans un **Voter** (`#[IsGranted('EDIT', 'note')]`), qui centralise les règles par type de ressource.
"""),
    L("JWT : lire n'est pas vérifier", r"""
Un JWT, c'est trois morceaux en base64url séparés par des points :

```
eyJhbGciOiJIUzI1NiJ9 . eyJzdWIiOjEsIm5vbSI6IkFuYSIsImV4cCI6MTc5OTk5OTk5OX0 . 4f2c9e…
     entête                         contenu (« claims »)                       signature
{"alg":"HS256"}        {"sub":1,"nom":"Ana","exp":1799999999}       HMAC-SHA256(entête.contenu, secret)
```

Le contenu est **lisible par tout le monde** (ce n'est pas chiffré) : n'y mets jamais de secret. Et n'importe qui peut fabriquer un contenu `{"role": "admin"}`. Ce qui prouve l'origine, c'est la **signature**.

Vérifier un JWT :

1. découper en 3 parties ;
2. recalculer `HMAC-SHA256(entête + "." + contenu, secret)` et comparer avec la signature (sinon 401) ;
3. vérifier que l'entête annonce bien l'algorithme attendu (`HS256`) ; refuser `"alg": "none"` ;
4. vérifier `exp` (expiration) et `nbf` (pas avant) par rapport à l'heure actuelle ;
5. seulement alors, utiliser `sub`, `roles`…

En PHP : `lcobucci/jwt` ou `firebase/php-jwt` ; en Symfony : `LexikJWTAuthenticationBundle`. Ne réécris pas ça en production : comprends-le pour bien l'utiliser.
"""),
  ],
  recap=["401 = pas authentifié (+ WWW-Authenticate) ; 403 = authentifié mais pas le droit.",
         "Jeton dans `Authorization: Bearer …`, jamais dans l'URL.",
         "Authentifier une fois avant les contrôleurs (listener / firewall).",
         "Autoriser sur chaque ressource, côté serveur.",
         "JWT : vérifier signature, algorithme et expiration avant de croire le contenu."],
  example=F("Authentification.php", "php", USES + r"""
use Symfony\Component\HttpKernel\Exception\UnauthorizedHttpException;

#[AsEventListener(event: 'kernel.request')]
final class Authentification
{
    public function __construct(private Jetons $jetons) {}

    public function __invoke(RequestEvent $event): void
    {
        $requete = $event->getRequest();
        if (str_starts_with($requete->getPathInfo(), '/api/public')) {
            return;                                                    // routes ouvertes
        }
        $h = $requete->headers->get('Authorization', '');
        if (!preg_match('/^Bearer (\S+)$/', $h, $m) || !($u = $this->jetons->utilisateur($m[1]))) {
            throw new UnauthorizedHttpException('Bearer', 'Jeton manquant ou invalide');
        }
        $requete->attributes->set('utilisateur', $u);                  // pour les contrôleurs
    }
}
"""),
  notes=["Le listener s'exécute avant tous les contrôleurs.", "`UnauthorizedHttpException` produit un 401 avec `WWW-Authenticate: Bearer`.", "L'utilisateur est rangé dans les attributs de la requête."],
  tds=[
    TD(1, "Un listener d'authentification",
       "Toutes les routes `/api/…` doivent exiger un jeton, sauf `/api/public/…`. Écris le listener et la route `GET /api/moi`." + SF,
       ["Listener `kernel.request` : lit `Authorization: Bearer <jeton>` ; absent, mal formé ou inconnu → **401** avec l'en-tête `WWW-Authenticate: Bearer`",
        "Les routes qui commencent par `/api/public` restent accessibles sans jeton",
        "L'utilisateur trouvé est rangé dans `$request->attributes` (clé `utilisateur`)",
        "`GET /api/moi` → `{\"id\": …, \"nom\": …}` de l'utilisateur connecté"],
       [F("Auth.php", "php", USES + TOKENS + r"""
use Symfony\Component\HttpKernel\Exception\UnauthorizedHttpException;

final class PublicController extends AbstractController
{
    #[Route('/api/public/statut', methods: ['GET'])]
    public function statut(): JsonResponse { return $this->json(['ok' => true]); }
}

// à toi : le listener Authentification, et MoiController (GET /api/moi)

App::request('GET', '/api/moi');
App::request('GET', '/api/moi', null, ['Authorization' => 'Bearer jeton-ana']);
""")],
       ["`#[AsEventListener(event: 'kernel.request')]` + `__invoke(RequestEvent $event)` ; le constructeur reçoit `Jetons` (autowiring).",
        "`throw new UnauthorizedHttpException('Bearer', 'Jeton manquant ou invalide');` produit le 401 et l'en-tête.",
        "Dans le contrôleur : `public function moi(Request $request)` puis `$request->attributes->get('utilisateur')`."],
       [F("Auth.php", "php", USES + TOKENS + r"""
use Symfony\Component\HttpKernel\Exception\UnauthorizedHttpException;

final class PublicController extends AbstractController
{
    #[Route('/api/public/statut', methods: ['GET'])]
    public function statut(): JsonResponse { return $this->json(['ok' => true]); }
}

#[AsEventListener(event: 'kernel.request')]
final class Authentification
{
    public function __construct(private Jetons $jetons) {}

    public function __invoke(RequestEvent $event): void
    {
        $requete = $event->getRequest();
        if (str_starts_with($requete->getPathInfo(), '/api/public')) {
            return;
        }
        $h = $requete->headers->get('Authorization', '');
        if (!preg_match('/^Bearer (\S+)$/', $h, $m) || !($u = $this->jetons->utilisateur($m[1]))) {
            throw new UnauthorizedHttpException('Bearer', 'Jeton manquant ou invalide');
        }
        $requete->attributes->set('utilisateur', $u);
    }
}

final class MoiController extends AbstractController
{
    #[Route('/api/moi', methods: ['GET'])]
    public function moi(Request $request): JsonResponse
    {
        $u = $request->attributes->get('utilisateur');
        return $this->json(['id' => $u->id, 'nom' => $u->nom]);
    }
}

App::request('GET', '/api/moi');
App::request('GET', '/api/moi', null, ['Authorization' => 'Bearer jeton-ana']);
""")],
       ["Sans jeton : 401 + WWW-Authenticate", "Avec jeton : l'utilisateur"],
       run=SRUN(r"""
$r = App::request('GET', '/api/moi');
check('sans jeton → 401', $r->status === 401, (string) $r);
check('… avec WWW-Authenticate: Bearer', $r->header('WWW-Authenticate') === 'Bearer', (string) $r);
check('jeton inconnu → 401', App::request('GET', '/api/moi', null, ['Authorization' => 'Bearer faux'])->status === 401);
check('en-tête mal formé → 401', App::request('GET', '/api/moi', null, ['Authorization' => 'jeton-ana'])->status === 401);
$ok = App::request('GET', '/api/moi', null, ['Authorization' => 'Bearer jeton-ana']);
check('jeton valide → 200 { id: 1, nom: Ana }', $ok->status === 200 && $ok->json() === ['id' => 1, 'nom' => 'Ana'], (string) $ok);
check('en-tête insensible à la casse (authorization)', App::request('GET', '/api/moi', null, ['authorization' => 'Bearer jeton-leo'])->json()['nom'] === 'Léo');
check('/api/public/statut reste ouvert', App::request('GET', '/api/public/statut')->status === 200);
""")),
    TD(2, "403 : des droits sur chaque ressource",
       "Chacun peut lire les notes, mais **seul l'auteur** peut les modifier, et **seul un admin** peut les supprimer. L'authentification est déjà en place (le listener du niveau 1 est fourni). Ajoute les vérifications de droits." + SF,
       ["`PATCH /api/notes/{id}` `{\"texte\": …}` : auteur ou admin → 200 ; autre utilisateur → **403** ; note absente → 404",
        "`DELETE /api/notes/{id}` : admin → 204 ; sinon → 403",
        "Sans jeton : 401 (déjà géré par le listener)",
        "L'ordre : 401, puis 404, puis 403"],
       [F("Notes.php", "php", USES + TOKENS + r"""
use Symfony\Component\HttpKernel\Exception\AccessDeniedHttpException;
use Symfony\Component\HttpKernel\Exception\UnauthorizedHttpException;

#[AsEventListener(event: 'kernel.request')]
final class Authentification
{
    public function __construct(private Jetons $jetons) {}
    public function __invoke(RequestEvent $event): void
    {
        $r = $event->getRequest();
        if (!preg_match('/^Bearer (\S+)$/', $r->headers->get('Authorization', ''), $m) || !($u = $this->jetons->utilisateur($m[1]))) {
            throw new UnauthorizedHttpException('Bearer', 'Jeton manquant ou invalide');
        }
        $r->attributes->set('utilisateur', $u);
    }
}

final class Note
{
    public function __construct(public int $id, public int $auteurId, public string $texte) {}
}

final class Notes
{
    public array $notes;
    public function __construct() { $this->notes = [1 => new Note(1, 1, 'Note d\'Ana'), 2 => new Note(2, 2, 'Note de Léo')]; }
}

final class NoteController extends AbstractController
{
    public function __construct(private Notes $notes) {}

    #[Route('/api/notes/{id}', methods: ['GET'])]
    public function voir(int $id): JsonResponse
    {
        return $this->json($this->notes->notes[$id] ?? throw $this->createNotFoundException());
    }

    // à toi : PATCH et DELETE avec les vérifications de droits
}

App::request('PATCH', '/api/notes/1', ['texte' => 'piraté'], ['Authorization' => 'Bearer jeton-leo']);
""")],
       ["L'utilisateur courant : `$request->attributes->get('utilisateur')` (un `Utilisateur`).",
        "`if ($note->auteurId !== $moi->id && !$moi->estAdmin()) throw new AccessDeniedHttpException('…');`",
        "Charge la note **avant** de vérifier les droits : une note absente doit donner 404."],
       [F("Notes.php", "php", USES + TOKENS + r"""
use Symfony\Component\HttpKernel\Exception\AccessDeniedHttpException;
use Symfony\Component\HttpKernel\Exception\UnauthorizedHttpException;

#[AsEventListener(event: 'kernel.request')]
final class Authentification
{
    public function __construct(private Jetons $jetons) {}
    public function __invoke(RequestEvent $event): void
    {
        $r = $event->getRequest();
        if (!preg_match('/^Bearer (\S+)$/', $r->headers->get('Authorization', ''), $m) || !($u = $this->jetons->utilisateur($m[1]))) {
            throw new UnauthorizedHttpException('Bearer', 'Jeton manquant ou invalide');
        }
        $r->attributes->set('utilisateur', $u);
    }
}

final class Note
{
    public function __construct(public int $id, public int $auteurId, public string $texte) {}
}

final class Notes
{
    public array $notes;
    public function __construct() { $this->notes = [1 => new Note(1, 1, 'Note d\'Ana'), 2 => new Note(2, 2, 'Note de Léo')]; }
}

final class NoteController extends AbstractController
{
    public function __construct(private Notes $notes) {}

    #[Route('/api/notes/{id}', methods: ['GET'])]
    public function voir(int $id): JsonResponse
    {
        return $this->json($this->note($id));
    }

    #[Route('/api/notes/{id}', methods: ['PATCH'])]
    public function modifier(int $id, Request $request): JsonResponse
    {
        $note = $this->note($id);
        $moi = $request->attributes->get('utilisateur');
        if ($note->auteurId !== $moi->id && !$moi->estAdmin()) {
            throw new AccessDeniedHttpException("Seul l'auteur peut modifier cette note");
        }
        $note->texte = (string) ($request->toArray()['texte'] ?? $note->texte);
        return $this->json($note);
    }

    #[Route('/api/notes/{id}', methods: ['DELETE'])]
    public function supprimer(int $id, Request $request): Response
    {
        $this->note($id);
        if (!$request->attributes->get('utilisateur')->estAdmin()) {
            throw new AccessDeniedHttpException('Réservé aux administrateurs');
        }
        unset($this->notes->notes[$id]);
        return new Response(null, 204);
    }

    private function note(int $id): Note
    {
        return $this->notes->notes[$id] ?? throw $this->createNotFoundException('Note introuvable');
    }
}

App::request('PATCH', '/api/notes/1', ['texte' => 'piraté'], ['Authorization' => 'Bearer jeton-leo']);
""")],
       ["Léo ne peut pas modifier la note d'Ana", "Seul l'admin supprime"],
       run=SRUN(r"""
$h = fn(string $qui) => ['Authorization' => "Bearer jeton-$qui"];
check('sans jeton → 401', App::request('PATCH', '/api/notes/1', ['texte' => 'x'])->status === 401);
$l = App::request('PATCH', '/api/notes/1', ['texte' => 'piraté'], $h('leo'));
check('Léo modifie la note d\'Ana → 403', $l->status === 403, (string) $l);
check('… et la note n\'a pas changé', App::request('GET', '/api/notes/1', null, $h('ana'))->json()['texte'] === "Note d'Ana");
$a = App::request('PATCH', '/api/notes/1', ['texte' => 'Corrigée'], $h('ana'));
check('Ana modifie sa note → 200', $a->status === 200 && $a->json()['texte'] === 'Corrigée', (string) $a);
check('l\'admin modifie la note de Léo → 200', App::request('PATCH', '/api/notes/2', ['texte' => 'Modérée'], $h('admin'))->status === 200);
check('note absente → 404 (même pour Léo)', App::request('PATCH', '/api/notes/9', ['texte' => 'x'], $h('leo'))->status === 404);
check('Ana supprime → 403', App::request('DELETE', '/api/notes/1', null, $h('ana'))->status === 403);
check('l\'admin supprime → 204', App::request('DELETE', '/api/notes/1', null, $h('admin'))->status === 204);
check('… note supprimée', App::request('GET', '/api/notes/1', null, $h('admin'))->status === 404);
""")),
    TD(3, "Vérifier un JWT (HS256)",
       "Écris la vérification d'un JWT signé en HS256, comme le fait une bibliothèque, pour comprendre ce qui protège vraiment. Les tests fabriquent des jetons valides, falsifiés, expirés et « alg: none »." + JS,
       ["`verifierJwt(jeton, secret, maintenant)` renvoie le contenu (objet) si tout est bon ; `maintenant` est en secondes",
        "Lève une `Error` dont le message commence par `format` (pas 3 parties / JSON illisible), `alg` (entête autre que `{\"alg\": \"HS256\"…}`), `signature` (HMAC incorrect), `expiré` (`exp` ≤ maintenant), `pas encore valide` (`nbf` > maintenant)",
        "La signature se vérifie **avant** de faire confiance au contenu",
        "`decoderBase64Url(s)` renvoie la chaîne décodée (UTF-8)"],
       [F("jwt.js", "js", r"""
// Rappels : base64url = base64 avec - et _ à la place de + et /, sans « = » final.
// HMAC-SHA256 avec crypto.subtle :
//   const cle = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
//   const sig = new Uint8Array(await crypto.subtle.sign('HMAC', cle, new TextEncoder().encode(texte)));

export function decoderBase64Url(s) {
  // à toi
}

export async function verifierJwt(jeton, secret, maintenant = Math.floor(Date.now() / 1000)) {
  // à toi
}
""")],
       ["Décoder : `s.replace(/-/g, '+').replace(/_/g, '/')`, compléter avec `=` jusqu'à une longueur multiple de 4, puis `atob`, puis `new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)))`.",
        "Pour comparer la signature : encode ta signature calculée en base64url (`btoa(String.fromCharCode(...sig))` puis remplacer `+`, `/`, retirer `=`) et compare les chaînes.",
        "Ordre : format → entête (alg) → signature → exp / nbf → renvoyer le contenu."],
       [F("jwt.js", "js", r"""
export function decoderBase64Url(s) {
  let b = s.replace(/-/g, '+').replace(/_/g, '/');
  while (b.length % 4) b += '=';
  const bin = atob(b);
  return new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
}

function encoderBase64Url(octets) {
  return btoa(String.fromCharCode(...octets)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function hmac(secret, texte) {
  const enc = new TextEncoder();
  const cle = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  return new Uint8Array(await crypto.subtle.sign('HMAC', cle, enc.encode(texte)));
}

export async function verifierJwt(jeton, secret, maintenant = Math.floor(Date.now() / 1000)) {
  const parties = String(jeton).split('.');
  if (parties.length !== 3) throw new Error('format : un JWT a 3 parties');
  const [e, c, s] = parties;
  let entete, contenu;
  try {
    entete = JSON.parse(decoderBase64Url(e));
    contenu = JSON.parse(decoderBase64Url(c));
  } catch {
    throw new Error('format : entête ou contenu illisible');
  }
  if (!entete || entete.alg !== 'HS256') throw new Error('alg : algorithme refusé (' + (entete && entete.alg) + ')');
  if (encoderBase64Url(await hmac(secret, e + '.' + c)) !== s) throw new Error('signature : invalide');
  if (typeof contenu.exp === 'number' && contenu.exp <= maintenant) throw new Error('expiré');
  if (typeof contenu.nbf === 'number' && contenu.nbf > maintenant) throw new Error('pas encore valide');
  return contenu;
}
""")],
       ["Un contenu modifié est refusé (signature)", "`alg: none` est refusé"],
       run=RUN("js", entry="jwt.js", tests=r"""
const { verifierJwt, decoderBase64Url } = require('./jwt');
const enc = new TextEncoder();
const b64u = (bytes) => btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const part = (obj) => b64u(enc.encode(JSON.stringify(obj)));
const signer = async (entete, contenu, secret) => {
  const e = part(entete), c = part(contenu);
  const cle = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = new Uint8Array(await crypto.subtle.sign('HMAC', cle, enc.encode(e + '.' + c)));
  return e + '.' + c + '.' + b64u(sig);
};
const S = 'secret-de-test', NOW = 1800000000;
const erreur = async (p) => { try { await p; return ''; } catch (e) { return String(e.message || e); } };
assert.equal(decoderBase64Url(part({ nom: 'Léa' })), '{"nom":"Léa"}', 'decoderBase64Url gère l\'UTF-8 (é)');
const ok = await signer({ alg: 'HS256', typ: 'JWT' }, { sub: 1, nom: 'Ana', exp: NOW + 60 }, S);
const c = await verifierJwt(ok, S, NOW);
assert(c && c.sub === 1 && c.nom === 'Ana', 'JWT valide → le contenu');
const [e0, , s0] = ok.split('.');
const falsifie = e0 + '.' + part({ sub: 1, nom: 'Ana', role: 'admin', exp: NOW + 60 }) + '.' + s0;
assert((await erreur(verifierJwt(falsifie, S, NOW))).startsWith('signature'), 'Contenu modifié → erreur « signature »');
assert((await erreur(verifierJwt(ok, 'autre-secret', NOW))).startsWith('signature'), 'Mauvais secret → « signature »');
assert((await erreur(verifierJwt(await signer({ alg: 'HS256' }, { sub: 1, exp: NOW - 1 }, S), S, NOW))).startsWith('expiré'), 'exp passé → « expiré »');
assert((await erreur(verifierJwt(await signer({ alg: 'HS256' }, { sub: 1, nbf: NOW + 100 }, S), S, NOW))).startsWith('pas encore valide'), 'nbf futur → « pas encore valide »');
const none = part({ alg: 'none' }) + '.' + part({ sub: 1, role: 'admin' }) + '.';
assert((await erreur(verifierJwt(none, S, NOW))).startsWith('alg'), 'alg « none » → refusé (« alg »)');
assert((await erreur(verifierJwt('abc.def', S, NOW))).startsWith('format'), '2 parties → « format »');
assert((await erreur(verifierJwt('%%%.%%%.%%%', S, NOW))).startsWith('format'), 'contenu illisible → « format »');
""")),
  ])

# =========================================================================== 4. Robustesse
robuste = DM("api-robuste", "Rendre une API robuste", 25,
  "Ajouter à une API ce qui la rend fiable en production : cache HTTP (ETag), requêtes rejouables sans risque (Idempotency-Key) et limitation du débit (429).",
  "Les vraies conditions d'Internet : réseaux qui coupent, clients qui réessaient, robots qui martèlent. Sans ces mécanismes, on obtient des doubles paiements, des serveurs saturés et des écrasements de données.",
  ["Lectures : `ETag` + `If-None-Match` → 304 si rien n'a changé", "Écritures concurrentes : `If-Match` → 412 si quelqu'un a modifié entre-temps",
   "POST rejouable : `Idempotency-Key` → même réponse, une seule exécution", "Trop de requêtes : 429 + `Retry-After`"],
  ["ETag = empreinte de la version de la ressource ; le client la renvoie dans `If-None-Match`.",
   "304 Not Modified : pas de corps, le client réutilise sa copie.",
   "`If-Match` sur PUT/PATCH évite d'écraser la modification d'un autre (verrou optimiste) : 412 sinon.",
   "Idempotency-Key : le serveur mémorise la réponse par clé ; même clé + même corps → même réponse ; même clé + autre corps → 422.",
   "429 + `Retry-After` dit au client quand revenir ; Symfony a le composant RateLimiter."],
  ["Recalculer et renvoyer tout le corps à chaque lecture.", "Réessayer un POST de paiement sans clé d'idempotence.", "Limiter le débit sans dire quand réessayer."],
  [Q("Le client envoie If-None-Match avec l'ETag actuel :", ["200 + corps", "304 sans corps", "412", "204"], 1, "Rien n'a changé : le client garde sa copie."),
   Q("Même Idempotency-Key, même corps, rejoué après une coupure :", ["un 2e paiement", "la même réponse, sans nouvelle exécution", "409", "400"], 1, "C'est tout l'intérêt de la clé."),
   Q("429 doit être accompagné de…", ["Location", "Retry-After", "ETag", "WWW-Authenticate"], 1, "Retry-After dit quand réessayer.")],
  prereq=[
    P("ETag", "En-tête de réponse : une empreinte de la version de la ressource (souvent un hash du contenu ou un numéro de version)."),
    P("Requête conditionnelle", "Requête avec `If-None-Match` (lecture) ou `If-Match` (écriture) : le serveur répond selon que la version correspond ou non."),
    P("Idempotency-Key", "En-tête choisi par le client (un UUID) pour qu'un POST rejoué ne s'exécute qu'une fois."),
    P("Rate limiting", "Limiter le nombre de requêtes par client et par période (ex. 5 par minute) pour protéger le serveur."),
  ],
  diagram=D(
    nodes=[
      N("g", 0, 0, "GET", "If-None-Match", kind="doc"),
      N("g2", 0, 1, "304", "pas de corps", kind="pill", color="good"),
      N("p", 1, 0, "POST rejoué", "Idempotency-Key", kind="doc"),
      N("p2", 1, 1, "Même réponse", "une seule exécution", kind="pill", color="good"),
      N("r", 2, 0, "6e requête / min", "même clé d'API", kind="doc"),
      N("r2", 2, 1, "429", "Retry-After: 42", kind="pill", color="warn"),
    ],
    edges=[E("g", "g2"), E("p", "p2"), E("r", "r2")],
    caption="Trois mécanismes HTTP standards : économiser les lectures, rendre les créations rejouables, protéger le serveur."),
  lessons=[
    L("Cache HTTP : ETag et 304", r"""
Le serveur ajoute à chaque lecture une **empreinte** de la version :

```http
GET /api/articles/7            →  200   ETag: "a1b2c3"    { …l'article… }
```

Le client garde l'article et son ETag. La fois suivante, il demande « seulement si ça a changé » :

```http
GET /api/articles/7
If-None-Match: "a1b2c3"        →  304 Not Modified   (pas de corps)
```

Si l'article a été modifié, le serveur répond 200 avec le nouveau corps et un nouvel ETag. Gain : moins de données transférées, et le navigateur fait ça tout seul pour les requêtes `fetch`.

En Symfony : `$response->setEtag(md5($json)); if ($response->isNotModified($request)) return $response;`. On peut ajouter `Cache-Control: private, max-age=60` pour éviter même la requête pendant 60 s.
"""),
    L("Écritures concurrentes : If-Match et 412", r"""
Ana et Léo ouvrent le même article (ETag `"v1"`). Léo enregistre (`"v2"`). Ana enregistre ensuite : sans précaution, elle **écrase** la modification de Léo sans le savoir.

Le **verrou optimiste** : le client envoie la version qu'il a modifiée :

```http
PUT /api/articles/7
If-Match: "v1"                 →  412 Precondition Failed   (la version actuelle est "v2")
```

Ana recharge, voit les changements de Léo, et refait sa modification. Si `If-Match` est absent alors qu'on l'exige : **428 Precondition Required**.

Avec Doctrine, le même principe existe côté base : `#[ORM\Version]` sur une colonne entière.
"""),
    L("Rejouer un POST sans risque : Idempotency-Key", r"""
Le client envoie `POST /api/paiements`, le serveur débite… et la réponse se perd (réseau coupé). Le client ne sait pas si c'est passé. S'il réessaie : **double paiement**.

Solution (utilisée par Stripe, Adyen…) : le client génère une **clé unique par opération** et la renvoie à chaque essai :

```http
POST /api/paiements
Idempotency-Key: 7c3e9f0a-…
{ "montant": 4990 }
```

Côté serveur :

1. clé jamais vue → exécuter, **mémoriser** (clé → empreinte du corps + réponse), répondre ;
2. clé déjà vue avec le **même** corps → renvoyer la réponse mémorisée, sans rien exécuter (souvent avec un en-tête `Idempotent-Replayed: true`) ;
3. clé déjà vue avec un **autre** corps → 422 (erreur du client : clé réutilisée pour autre chose) ;
4. pas de clé sur une route qui l'exige → 400.
"""),
    L("Limiter le débit : 429", r"""
Pour éviter qu'un client (ou un robot) sature l'API : au plus N requêtes par période et par client (clé d'API, utilisateur, IP).

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 42                       ← dans 42 secondes
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
```

L'algorithme le plus simple est la **fenêtre fixe** : un compteur par client et par minute ; quand la minute change, il repart à zéro. `Retry-After` = secondes restantes avant la prochaine fenêtre.

En production, on utilise le composant **RateLimiter** de Symfony (fenêtre fixe, fenêtre glissante, seau à jetons) avec un stockage partagé (Redis), et souvent une limite au niveau du proxy (Nginx, API gateway).

Et pour tester une logique qui dépend du temps : injecter une **horloge** au lieu d'appeler `time()` (comme dans le module DDD).
"""),
  ],
  recap=["ETag + If-None-Match → 304 sans corps.",
         "If-Match sur les écritures : 412 si la version a changé, 428 s'il manque.",
         "Idempotency-Key : même clé + même corps → même réponse, une seule exécution.",
         "429 + Retry-After (+ X-RateLimit-*) ; une horloge injectée pour tester."],
  example=F("ArticleController.php", "php", USES + r"""
final class ArticleController extends AbstractController
{
    #[Route('/api/articles/{id}', methods: ['GET'])]
    public function voir(int $id, Request $request, Articles $articles): JsonResponse
    {
        $article = $articles->trouver($id) ?? throw $this->createNotFoundException();
        $etag = '"' . md5(json_encode($article)) . '"';

        if ($request->headers->get('If-None-Match') === $etag) {
            return new JsonResponse(null, 304, ['ETag' => $etag]);    // rien n'a changé
        }
        return $this->json($article, 200, ['ETag' => $etag]);
    }
}
"""),
  notes=["L'ETag est une empreinte du contenu, entre guillemets (c'est la norme).", "Même ETag → 304 sans corps.", "Sinon 200 avec le corps et l'ETag à garder."],
  tds=[
    TD(1, "ETag, 304 et verrou optimiste",
       "Deux personnes éditent les mêmes articles et se marchent dessus. Ajoute le cache HTTP en lecture et le verrou optimiste en écriture." + SF,
       ["`GET /api/articles/{id}` → 200 + en-tête `ETag: \"<md5 du JSON de l'article>\"` ; avec `If-None-Match` égal → **304** sans corps (et l'ETag)",
        "`PUT /api/articles/{id}` `{\"titre\": …, \"texte\": …}` : sans `If-Match` → **428** ; `If-Match` différent de l'ETag actuel → **412** ; sinon → 200 + nouvel `ETag`",
        "Article absent → 404",
        "L'empreinte : `'\"' . md5(json_encode($article)) . '\"'` (fonction `etag()` fournie)"],
       [F("Articles.php", "php", USES + r"""
final class Article
{
    public function __construct(public int $id, public string $titre, public string $texte) {}
}

final class Articles
{
    public array $articles;
    public function __construct() { $this->articles = [7 => new Article(7, 'Les ETag', 'Version 1')]; }
}

function etag(Article $a): string
{
    return '"' . md5(json_encode($a)) . '"';
}

final class ArticleController extends AbstractController
{
    public function __construct(private Articles $articles) {}

    // à toi : GET et PUT /api/articles/{id}
}

$r = App::request('GET', '/api/articles/7');
App::request('GET', '/api/articles/7', null, ['If-None-Match' => $r->header('ETag') ?? '']);
""")],
       ["Lecture : `if ($request->headers->get('If-None-Match') === $etag) return new JsonResponse(null, 304, ['ETag' => $etag]);`",
        "Écriture : `$if = $request->headers->get('If-Match'); if ($if === null) throw new HttpException(428, 'If-Match requis');`",
        "Après modification, recalcule l'ETag et renvoie-le."],
       [F("Articles.php", "php", USES + r"""
final class Article
{
    public function __construct(public int $id, public string $titre, public string $texte) {}
}

final class Articles
{
    public array $articles;
    public function __construct() { $this->articles = [7 => new Article(7, 'Les ETag', 'Version 1')]; }
}

function etag(Article $a): string
{
    return '"' . md5(json_encode($a)) . '"';
}

final class ArticleController extends AbstractController
{
    public function __construct(private Articles $articles) {}

    #[Route('/api/articles/{id}', methods: ['GET'])]
    public function voir(int $id, Request $request): JsonResponse
    {
        $a = $this->article($id);
        $etag = etag($a);
        if ($request->headers->get('If-None-Match') === $etag) {
            return new JsonResponse(null, 304, ['ETag' => $etag]);
        }
        return $this->json($a, 200, ['ETag' => $etag]);
    }

    #[Route('/api/articles/{id}', methods: ['PUT'])]
    public function remplacer(int $id, Request $request): JsonResponse
    {
        $a = $this->article($id);
        $if = $request->headers->get('If-Match');
        if ($if === null) {
            throw new HttpException(428, 'En-tête If-Match requis');
        }
        if ($if !== etag($a)) {
            throw new HttpException(412, "L'article a été modifié entre-temps : recharge-le");
        }
        $d = $request->toArray();
        $a->titre = (string) ($d['titre'] ?? $a->titre);
        $a->texte = (string) ($d['texte'] ?? $a->texte);
        return $this->json($a, 200, ['ETag' => etag($a)]);
    }

    private function article(int $id): Article
    {
        return $this->articles->articles[$id] ?? throw $this->createNotFoundException('Article introuvable');
    }
}

$r = App::request('GET', '/api/articles/7');
App::request('GET', '/api/articles/7', null, ['If-None-Match' => $r->header('ETag') ?? '']);
""")],
       ["304 sans corps quand rien n'a changé", "412 si quelqu'un a modifié entre-temps"],
       run=SRUN(r"""
$r = App::request('GET', '/api/articles/7');
$v1 = $r->header('ETag');
check('GET → 200 + ETag', $r->status === 200 && $v1 === '"' . md5(json_encode(['id' => 7, 'titre' => 'Les ETag', 'texte' => 'Version 1'])) . '"', (string) $r);
$n = App::request('GET', '/api/articles/7', null, ['If-None-Match' => $v1]);
check('If-None-Match identique → 304 sans corps', $n->status === 304 && $n->json() === null, (string) $n);
check('If-None-Match différent → 200', App::request('GET', '/api/articles/7', null, ['If-None-Match' => '"vieux"'])->status === 200);
check('PUT sans If-Match → 428', App::request('PUT', '/api/articles/7', ['titre' => 'x', 'texte' => 'y'])->status === 428);
$leo = App::request('PUT', '/api/articles/7', ['titre' => 'Les ETag', 'texte' => 'Version de Léo'], ['If-Match' => $v1]);
check('Léo (If-Match à jour) → 200 + nouvel ETag', $leo->status === 200 && $leo->header('ETag') !== $v1 && $leo->header('ETag') !== null, (string) $leo);
$ana = App::request('PUT', '/api/articles/7', ['titre' => 'Les ETag', 'texte' => "Version d'Ana"], ['If-Match' => $v1]);
check('Ana (version périmée) → 412', $ana->status === 412, (string) $ana);
check('… la modification de Léo n\'est pas écrasée', App::request('GET', '/api/articles/7')->json()['texte'] === 'Version de Léo');
check('article absent → 404', App::request('GET', '/api/articles/9')->status === 404);
""")),
    TD(2, "Paiements rejouables : Idempotency-Key",
       "Le front réessaie automatiquement quand le réseau coupe. Résultat : des clients débités **deux fois**. Rends `POST /api/paiements` idempotent avec l'en-tête `Idempotency-Key`." + SF,
       ["Sans `Idempotency-Key` → **400**",
        "Nouvelle clé → exécute le paiement (`Banque::debiter()` fourni), 201 + `{\"id\": …, \"montant\": …}`, et mémorise la réponse",
        "Même clé **et** même corps → renvoie exactement la même réponse (même statut, même corps), avec l'en-tête `Idempotent-Replayed: true`, **sans** débiter à nouveau",
        "Même clé mais **autre** corps → **422**"],
       [F("Paiements.php", "php", USES + r"""
// --- Fourni ---
final class Banque
{
    public array $debits = [];
    public function debiter(int $montant): int { $this->debits[] = $montant; return count($this->debits); }
}

final class Idempotence
{
    /** clé => ['empreinte' => string, 'statut' => int, 'corps' => array] */
    public array $reponses = [];
}

final class PaiementController extends AbstractController
{
    public function __construct(private Banque $banque, private Idempotence $memoire) {}

    #[Route('/api/paiements', methods: ['POST'])]
    public function payer(Request $request): JsonResponse
    {
        $montant = (int) ($request->toArray()['montant'] ?? 0);
        $id = $this->banque->debiter($montant);
        return $this->json(['id' => $id, 'montant' => $montant], 201);
    }
}

$cle = ['Idempotency-Key' => '7c3e9f0a-0001'];
App::request('POST', '/api/paiements', ['montant' => 4990], $cle);
App::request('POST', '/api/paiements', ['montant' => 4990], $cle);   // le réseau a coupé, le front réessaie
""")],
       ["L'empreinte du corps : `md5($request->getContent())`.",
        "Si la clé est connue : comparer l'empreinte ; identique → `return $this->json($m['corps'], $m['statut'], ['Idempotent-Replayed' => 'true']);`",
        "Mémoriser **après** l'exécution réussie : `$this->memoire->reponses[$cle] = ['empreinte' => …, 'statut' => 201, 'corps' => $corps];`"],
       [F("Paiements.php", "php", USES + r"""
use Symfony\Component\HttpKernel\Exception\BadRequestHttpException;
use Symfony\Component\HttpKernel\Exception\UnprocessableEntityHttpException;

final class Banque
{
    public array $debits = [];
    public function debiter(int $montant): int { $this->debits[] = $montant; return count($this->debits); }
}

final class Idempotence
{
    /** clé => ['empreinte' => string, 'statut' => int, 'corps' => array] */
    public array $reponses = [];
}

final class PaiementController extends AbstractController
{
    public function __construct(private Banque $banque, private Idempotence $memoire) {}

    #[Route('/api/paiements', methods: ['POST'])]
    public function payer(Request $request): JsonResponse
    {
        $cle = $request->headers->get('Idempotency-Key');
        if (!$cle) {
            throw new BadRequestHttpException('En-tête Idempotency-Key requis');
        }
        $empreinte = md5($request->getContent());
        if (isset($this->memoire->reponses[$cle])) {
            $m = $this->memoire->reponses[$cle];
            if ($m['empreinte'] !== $empreinte) {
                throw new UnprocessableEntityHttpException('Cette clé a déjà servi pour une autre requête');
            }
            return $this->json($m['corps'], $m['statut'], ['Idempotent-Replayed' => 'true']);
        }

        $montant = (int) ($request->toArray()['montant'] ?? 0);
        $corps = ['id' => $this->banque->debiter($montant), 'montant' => $montant];
        $this->memoire->reponses[$cle] = ['empreinte' => $empreinte, 'statut' => 201, 'corps' => $corps];
        return $this->json($corps, 201);
    }
}

$cle = ['Idempotency-Key' => '7c3e9f0a-0001'];
App::request('POST', '/api/paiements', ['montant' => 4990], $cle);
App::request('POST', '/api/paiements', ['montant' => 4990], $cle);
""")],
       ["Un seul débit pour deux essais", "Même clé, autre montant → 422"],
       run=SRUN(r"""
$k = fn(string $v) => ['Idempotency-Key' => $v];
check('sans clé → 400', App::request('POST', '/api/paiements', ['montant' => 100])->status === 400);
$a = App::request('POST', '/api/paiements', ['montant' => 4990], $k('k-1'));
check('1er essai → 201 { id: 1, montant: 4990 }', $a->status === 201 && $a->json() === ['id' => 1, 'montant' => 4990], (string) $a);
$b = App::request('POST', '/api/paiements', ['montant' => 4990], $k('k-1'));
check('rejeu → même statut et même corps', $b->status === 201 && $b->json() === $a->json(), (string) $b);
check('rejeu → Idempotent-Replayed: true', $b->header('Idempotent-Replayed') === 'true', (string) $b);
check('un seul débit en banque', App::get(Banque::class)->debits === [4990]);
check('même clé, autre montant → 422', App::request('POST', '/api/paiements', ['montant' => 1], $k('k-1'))->status === 422);
$c = App::request('POST', '/api/paiements', ['montant' => 1500], $k('k-2'));
check('nouvelle clé → nouveau paiement (id 2)', $c->status === 201 && $c->json()['id'] === 2 && App::get(Banque::class)->debits === [4990, 1500]);
""")),
    TD(3, "Limiter le débit : 429 et Retry-After",
       "Un partenaire appelle l'API en boucle. Limite chaque clé d'API (`X-Api-Key`) à **5 requêtes par minute** (fenêtre fixe), dans un listener. Pour pouvoir tester, l'heure vient d'un service `Horloge` (fourni) et non de `time()`." + SF,
       ["Listener `kernel.request` : compte les requêtes par clé et par minute (`intdiv($maintenant, 60)`)",
        "Au-delà de 5 dans la même minute → **429** avec `Retry-After` = secondes restantes avant la minute suivante",
        "Listener `kernel.response` : ajoute `X-RateLimit-Limit: 5` et `X-RateLimit-Remaining: <restantes>` aux réponses réussies",
        "Sans `X-Api-Key` → 401 ; chaque clé a son propre compteur ; la minute suivante, le compteur repart à zéro"],
       [F("Limite.php", "php", USES + r"""
use Symfony\Component\HttpKernel\Exception\TooManyRequestsHttpException;
use Symfony\Component\HttpKernel\Exception\UnauthorizedHttpException;

// --- Fourni ---
final class Horloge
{
    public int $maintenant = 1_800_000_000;     // secondes ; les tests la font avancer
}

final class Compteurs
{
    /** "clé|minute" => nombre de requêtes */
    public array $parFenetre = [];
}

final class MeteoController extends AbstractController
{
    #[Route('/api/meteo', methods: ['GET'])]
    public function meteo(): JsonResponse { return $this->json(['ville' => 'Lyon', 'temperature' => 12]); }
}

// à toi : LimiteDebit (kernel.request) et EntetesLimite (kernel.response)

for ($i = 0; $i < 7; $i++) App::request('GET', '/api/meteo', null, ['X-Api-Key' => 'partenaire']);
""")],
       ["Fenêtre : `$fenetre = intdiv($h->maintenant, 60);` ; clé de compteur : `\"$cle|$fenetre\"`.",
        "Dépassement : `throw new TooManyRequestsHttpException(60 - $h->maintenant % 60, 'Trop de requêtes');`",
        "Pour les en-têtes : range le nombre restant dans `$request->attributes` (kernel.request), puis lis-le dans `ResponseEvent` et fais `$event->getResponse()->headers->set(…)`."],
       [F("Limite.php", "php", USES + r"""
use Symfony\Component\HttpKernel\Exception\TooManyRequestsHttpException;
use Symfony\Component\HttpKernel\Exception\UnauthorizedHttpException;

final class Horloge
{
    public int $maintenant = 1_800_000_000;
}

final class Compteurs
{
    public array $parFenetre = [];
}

final class MeteoController extends AbstractController
{
    #[Route('/api/meteo', methods: ['GET'])]
    public function meteo(): JsonResponse { return $this->json(['ville' => 'Lyon', 'temperature' => 12]); }
}

#[AsEventListener(event: 'kernel.request')]
final class LimiteDebit
{
    public const LIMITE = 5;

    public function __construct(private Horloge $horloge, private Compteurs $compteurs) {}

    public function __invoke(RequestEvent $event): void
    {
        $requete = $event->getRequest();
        $cle = $requete->headers->get('X-Api-Key');
        if (!$cle) {
            throw new UnauthorizedHttpException('ApiKey', 'En-tête X-Api-Key requis');
        }
        $t = $this->horloge->maintenant;
        $k = $cle . '|' . intdiv($t, 60);
        $n = ($this->compteurs->parFenetre[$k] ?? 0) + 1;
        $this->compteurs->parFenetre[$k] = $n;
        if ($n > self::LIMITE) {
            throw new TooManyRequestsHttpException(60 - $t % 60, 'Trop de requêtes : réessaie plus tard');
        }
        $requete->attributes->set('restantes', self::LIMITE - $n);
    }
}

#[AsEventListener(event: 'kernel.response')]
final class EntetesLimite
{
    public function __invoke(ResponseEvent $event): void
    {
        $restantes = $event->getRequest()->attributes->get('restantes');
        if ($restantes === null) {
            return;
        }
        $event->getResponse()->headers->set('X-RateLimit-Limit', (string) LimiteDebit::LIMITE);
        $event->getResponse()->headers->set('X-RateLimit-Remaining', (string) $restantes);
    }
}

for ($i = 0; $i < 7; $i++) App::request('GET', '/api/meteo', null, ['X-Api-Key' => 'partenaire']);
""")],
       ["La 6e requête de la minute reçoit 429", "Retry-After indique les secondes restantes"],
       run=SRUN(r"""
$h = App::get(Horloge::class); $h->maintenant = 1_800_000_030;    // 30 s après le début d'une minute
$k = ['X-Api-Key' => 'p1'];
$st = [];
for ($i = 0; $i < 5; $i++) $st[] = App::request('GET', '/api/meteo', null, $k);
check('5 premières requêtes → 200', array_map(fn($r) => $r->status, $st) === [200, 200, 200, 200, 200]);
check('X-RateLimit-Limit: 5', $st[0]->header('X-RateLimit-Limit') === '5', (string) $st[0]);
check('X-RateLimit-Remaining décroît : 4 puis 0', $st[0]->header('X-RateLimit-Remaining') === '4' && $st[4]->header('X-RateLimit-Remaining') === '0', (string) $st[4]);
$six = App::request('GET', '/api/meteo', null, $k);
check('6e requête → 429', $six->status === 429, (string) $six);
check('Retry-After = 30 (secondes avant la minute suivante)', $six->header('Retry-After') === '30', (string) $six);
check('une autre clé n\'est pas bloquée', App::request('GET', '/api/meteo', null, ['X-Api-Key' => 'p2'])->status === 200);
check('sans clé → 401', App::request('GET', '/api/meteo')->status === 401);
$h->maintenant = 1_800_000_065;
check('minute suivante → de nouveau 200', App::request('GET', '/api/meteo', null, $k)->status === 200);
""")),
  ])

# =========================================================================== 5. Consommer en PHP
METEO_FIXE = r"""
// --- Fourni : la réponse réelle de l'API météo (format du fournisseur) ---
const METEO_LYON = [
    'location' => ['name' => 'Lyon', 'country' => 'France'],
    'current' => ['temp_c' => 12.4, 'humidity' => 71, 'condition' => ['text' => 'Partiellement nuageux', 'code' => 1003]],
];
"""

client_php = DM("api-client-php", "Consommer une API depuis Symfony", 25,
  "Appeler une API externe depuis Symfony avec HttpClient : construire la requête, gérer les erreurs, convertir la réponse dans ton propre modèle, et tester sans réseau.",
  "Paiement, météo, envoi d'emails, géocodage : tout projet appelle des API externes. Elles sont lentes, tombent en panne et changent de format : le code qui les appelle doit être solide et isolé.",
  ["Un service dédié par API (`MeteoClient`), qui reçoit `HttpClientInterface`", "Requête : `base_uri`, `query`, `headers`, `auth_bearer`, `json`, `timeout`",
   "Réponse : vérifier le statut, puis convertir le JSON en **tes** objets", "Erreurs : 4xx, 5xx, coupure réseau → tes exceptions ; tester avec `MockHttpClient`"],
  ["`$client->request()` ne bloque pas : l'appel part vraiment à la lecture (`getStatusCode()`, `toArray()`).",
   "`toArray()` lève `ClientException` (4xx) ou `ServerException` (5xx) ; `toArray(false)` ne lève pas.",
   "Une coupure réseau ou un timeout lève une `TransportExceptionInterface`.",
   "Ne laisse jamais le format du fournisseur se répandre dans ton code : convertis-le en un DTO à toi à la frontière.",
   "La clé d'API vient de l'environnement (`%env(METEO_API_KEY)%`), jamais du code."],
  ["Renvoyer directement le tableau JSON du fournisseur au reste de l'application.", "Pas de timeout (une API lente bloque tes pages).", "Réessayer sur une 4xx (ça ne changera rien)."],
  [Q("`$response->toArray()` sur une 404…", ["renvoie []", "lève une ClientException", "renvoie null", "lève une TransportException"], 1, "4xx → ClientException, sauf toArray(false)."),
   Q("Quand réessayer automatiquement ?", ["sur 400", "sur 404", "sur 503 et coupure réseau", "jamais"], 2, "Les erreurs temporaires peuvent passer au 2e essai ; une 4xx non."),
   Q("Où convertir le JSON du fournisseur en objet métier ?", ["dans le contrôleur", "dans le client de l'API (la frontière)", "dans le template", "dans l'entité"], 1, "Une seule classe connaît le format du fournisseur.")],
  prereq=[
    P("HttpClient", "Le composant Symfony pour faire des requêtes HTTP sortantes : `HttpClientInterface::request($méthode, $url, $options)`."),
    P("Réponse paresseuse", "La requête part réellement quand on lit la réponse (`getStatusCode()`, `toArray()`) : on peut lancer plusieurs requêtes en parallèle."),
    P("MockHttpClient", "Un faux client fourni par Symfony pour les tests : il renvoie des `MockResponse` préparées, sans réseau."),
    P("Couche anti-corruption", "La classe qui traduit le modèle d'un système externe dans le tien, pour que le reste du code n'en dépende pas."),
  ],
  diagram=D(
    nodes=[
      N("ctl", 0, 1, "Ton code", "veut une Meteo", kind="file", color="accent"),
      N("cl", 1, 1, "MeteoClient", "requête + conversion", kind="box", color="warn"),
      N("http", 2, 1, "HttpClientInterface", "timeout, en-têtes", kind="pill"),
      N("ext", 3, 1, "API météo", "format du fournisseur", kind="db", color="muted"),
      N("dto", 1, 0, "Meteo (ton DTO)", "ville, temperature…", kind="doc", color="good"),
      N("exc", 1, 2, "Tes exceptions", "VilleInconnue…", kind="note", color="bad"),
    ],
    edges=[E("ctl", "cl"), E("cl", "http"), E("http", "ext"), E("cl", "dto"), E("cl", "exc")],
    caption="Seul MeteoClient connaît l'API externe : il renvoie tes objets et lève tes exceptions. En test, MockHttpClient remplace le réseau."),
  lessons=[
    L("Faire une requête avec HttpClient", r"""
```php
final class MeteoClient
{
    public function __construct(
        private HttpClientInterface $client,
        #[Autowire('%env(METEO_API_KEY)%')] private string $cle,
    ) {}

    public function actuelle(string $ville): Meteo
    {
        $reponse = $this->client->request('GET', 'https://api.meteo.exemple/v1/current', [
            'query' => ['city' => $ville, 'units' => 'metric'],   // → ?city=Lyon&units=metric
            'headers' => ['X-Api-Key' => $this->cle],
            'timeout' => 3,                                       // secondes : ne jamais attendre indéfiniment
        ]);
        $d = $reponse->toArray();                                 // l'appel part ici ; lève sur 4xx/5xx
        return new Meteo($d['location']['name'], $d['current']['temp_c'], $d['current']['condition']['text']);
    }
}
```

Options utiles : `query` (paramètres d'URL, encodés pour toi), `headers`, `auth_bearer` (→ `Authorization: Bearer …`), `json` (corps JSON + Content-Type), `timeout`, `base_uri`.

Dans un vrai projet, on déclare un **client nommé** par API dans `config/packages/framework.yaml` (`scoped_clients`), avec son `base_uri` et ses en-têtes, et on l'injecte par son nom (`HttpClientInterface $meteoClient`).
"""),
    L("Les erreurs d'une API externe", r"""
Trois familles, trois exceptions :

| Situation | Exception (interface) | Que faire |
|---|---|---|
| 4xx (404, 401, 422…) | `ClientExceptionInterface` | **ne pas réessayer** ; 404 → souvent « n'existe pas » ; 401 → clé invalide (bug de config) |
| 5xx (500, 503…) | `ServerExceptionInterface` | erreur **temporaire** : réessayer un peu plus tard |
| coupure, DNS, timeout | `TransportExceptionInterface` | temporaire aussi : réessayer |

```php
try {
    $d = $reponse->toArray();
} catch (ClientExceptionInterface $e) {
    if ($e->getResponse()->getStatusCode() === 404) throw new VilleInconnue($ville);
    throw $e;
} catch (ServerExceptionInterface | TransportExceptionInterface) {
    throw new MeteoIndisponible();                     // ton exception, que ton code sait afficher
}
```

Le reste de l'application ne voit que **tes** exceptions (`VilleInconnue`, `MeteoIndisponible`), jamais celles de HttpClient. Pour réessayer, Symfony fournit `RetryableHttpClient` (réessais avec délai croissant sur 5xx et coupures) ; on peut aussi écrire une petite boucle.
"""),
    L("Convertir et isoler le format du fournisseur", r"""
Le JSON du fournisseur (`temp_c`, `condition.text`, `location.name`) ne doit **pas** se répandre dans ton code. Sinon, le jour où il change de format (ou que tu changes de fournisseur), il faut tout modifier.

Le client de l'API est une **couche anti-corruption** : il convertit tout de suite vers **ton** modèle (un DTO immuable), avec tes noms et tes types :

```php
final class Meteo
{
    public function __construct(
        public readonly string $ville,
        public readonly float $temperature,
        public readonly string $description,
    ) {}
}
```

Et pour aller plus loin :

- **Cache** : une API météo ou un catalogue changent rarement → `CacheInterface::get($cle, fn(ItemInterface $i) => …)` avec `expiresAfter(600)`. Moins d'appels, plus rapide, et ça marche encore quand l'API est lente.
- **Pagination** : beaucoup d'API renvoient les résultats par pages (`links.next`) : on boucle tant qu'il y a une page suivante.
- **Tests** : `new MockHttpClient(fn($méthode, $url, $options) => MockResponse::json([...]))` remplace le réseau ; on vérifie aussi l'URL et les en-têtes envoyés.
"""),
  ],
  recap=["Un service par API externe, qui reçoit `HttpClientInterface`.",
         "Options : `query`, `headers`, `auth_bearer`, `json`, `timeout`, `base_uri`.",
         "`toArray()` lève sur 4xx/5xx ; coupure → TransportException.",
         "4xx : ne pas réessayer ; 5xx/coupure : réessayer, puis ton exception.",
         "Convertir le JSON en **ton** DTO ; cache et pagination dans le client ; tests avec MockHttpClient."],
  example=F("MeteoClient.php", "php", HC_USES + r"""
final class Meteo
{
    public function __construct(public readonly string $ville, public readonly float $temperature, public readonly string $description) {}
}

final class MeteoClient
{
    public function __construct(private HttpClientInterface $client, private string $cle) {}

    public function actuelle(string $ville): Meteo
    {
        $d = $this->client->request('GET', 'https://api.meteo.exemple/v1/current', [
            'query' => ['city' => $ville, 'units' => 'metric'],
            'headers' => ['X-Api-Key' => $this->cle],
            'timeout' => 3,
        ])->toArray();

        return new Meteo($d['location']['name'], (float) $d['current']['temp_c'], $d['current']['condition']['text']);
    }
}

// Test sans réseau :
$client = new MockHttpClient(fn(string $m, string $url) => MockResponse::json([
    'location' => ['name' => 'Lyon'], 'current' => ['temp_c' => 12.4, 'condition' => ['text' => 'Nuageux']],
]));
var_dump((new MeteoClient($client, 'cle-test'))->actuelle('Lyon'));
"""),
  notes=["`query` construit `?city=Lyon&units=metric` pour toi.", "La conversion vers `Meteo` se fait dans le client, nulle part ailleurs.", "`MockHttpClient` permet de lancer le code sans réseau."],
  tds=[
    TD(1, "Un client météo propre",
       "Écris le client de l'API météo et convertis sa réponse dans ton propre DTO." + HC,
       ["`MeteoClient::actuelle(string $ville): Meteo` appelle `GET https://api.meteo.exemple/v1/current?city=<ville>&units=metric`",
        "En-tête `X-Api-Key` avec la clé reçue au constructeur ; `timeout` de 3 secondes",
        "`Meteo` (fourni) : `ville` (location.name), `temperature` (current.temp_c, float), `description` (current.condition.text), `humidite` (current.humidity, int)",
        "Les noms du fournisseur (`temp_c`, `condition`…) n'apparaissent que dans `MeteoClient`"],
       [F("Meteo.php", "php", HC_USES + METEO_FIXE + r"""
final class Meteo
{
    public function __construct(
        public readonly string $ville,
        public readonly float $temperature,
        public readonly string $description,
        public readonly int $humidite,
    ) {}
}

final class MeteoClient
{
    public function __construct(private HttpClientInterface $client, private string $cle) {}

    public function actuelle(string $ville): Meteo
    {
        // à toi
    }
}

$client = new MockHttpClient(fn() => MockResponse::json(METEO_LYON));
var_dump((new MeteoClient($client, 'cle-secrete'))->actuelle('Lyon'));
""")],
       ["`$this->client->request('GET', 'https://api.meteo.exemple/v1/current', ['query' => […], 'headers' => […], 'timeout' => 3])`.",
        "`->toArray()` renvoie le tableau du fournisseur.",
        "`new Meteo($d['location']['name'], (float) $d['current']['temp_c'], …)`."],
       [F("Meteo.php", "php", HC_USES + METEO_FIXE + r"""
final class Meteo
{
    public function __construct(
        public readonly string $ville,
        public readonly float $temperature,
        public readonly string $description,
        public readonly int $humidite,
    ) {}
}

final class MeteoClient
{
    public function __construct(private HttpClientInterface $client, private string $cle) {}

    public function actuelle(string $ville): Meteo
    {
        $d = $this->client->request('GET', 'https://api.meteo.exemple/v1/current', [
            'query' => ['city' => $ville, 'units' => 'metric'],
            'headers' => ['X-Api-Key' => $this->cle],
            'timeout' => 3,
        ])->toArray();

        return new Meteo(
            $d['location']['name'],
            (float) $d['current']['temp_c'],
            $d['current']['condition']['text'],
            (int) $d['current']['humidity'],
        );
    }
}

$client = new MockHttpClient(fn() => MockResponse::json(METEO_LYON));
var_dump((new MeteoClient($client, 'cle-secrete'))->actuelle('Lyon'));
""")],
       ["L'URL et la clé envoyées sont les bonnes", "Le DTO a les bonnes valeurs"],
       run=HRUN(r"""
use Symfony\Component\HttpClient\MockHttpClient as MHC;
use Symfony\Component\HttpClient\Response\MockResponse as MR;
$c = new MHC(fn() => MR::json(METEO_LYON));
$m = (new MeteoClient($c, 'cle-123'))->actuelle('Saint-Étienne');
check('un seul appel', $c->getRequestsCount() === 1);
$a = $c->appels[0];
check('GET', $a['method'] === 'GET');
check('URL avec city et units', $a['url'] === 'https://api.meteo.exemple/v1/current?' . http_build_query(['city' => 'Saint-Étienne', 'units' => 'metric']), $a['url']);
check('en-tête X-Api-Key', ($a['options']['normalized_headers']['x-api-key'] ?? null) === 'cle-123');
check('timeout de 3 s', ($a['options']['timeout'] ?? null) === 3);
check('Meteo : ville, température (float), description, humidité', $m instanceof Meteo && $m->ville === 'Lyon' && $m->temperature === 12.4 && $m->description === 'Partiellement nuageux' && $m->humidite === 71);
""")),
    TD(2, "Pannes, réessais et exceptions à toi",
       "L'API météo tombe parfois (503), coupe la connexion, ou répond 404 pour une ville inconnue. Ton code ne doit voir que **tes** exceptions, et réessayer seulement quand ça a du sens." + HC,
       ["404 → `VilleInconnue` (aucun réessai)",
        "401 → `LogicException` « Clé API météo invalide » (aucun réessai : c'est un problème de configuration)",
        "5xx ou coupure réseau → réessaie, **3 essais au total** ; si tous échouent → `MeteoIndisponible`",
        "Une réussite au 2e ou 3e essai renvoie normalement la `Meteo`"],
       [F("Meteo.php", "php", HC_USES + METEO_FIXE + r"""
final class Meteo
{
    public function __construct(public readonly string $ville, public readonly float $temperature, public readonly string $description) {}
}

final class VilleInconnue extends DomainException {}
final class MeteoIndisponible extends RuntimeException {}

final class MeteoClient
{
    public function __construct(private HttpClientInterface $client, private string $cle) {}

    public function actuelle(string $ville): Meteo
    {
        $d = $this->client->request('GET', 'https://api.meteo.exemple/v1/current', [
            'query' => ['city' => $ville, 'units' => 'metric'],
            'headers' => ['X-Api-Key' => $this->cle],
            'timeout' => 3,
        ])->toArray();
        return new Meteo($d['location']['name'], (float) $d['current']['temp_c'], $d['current']['condition']['text']);
    }
}

// L'API répond 503 deux fois, puis 200 :
$client = new MockHttpClient([new MockResponse('', ['http_code' => 503]), new MockResponse('', ['error' => 'Connection reset']), MockResponse::json(METEO_LYON)]);
var_dump((new MeteoClient($client, 'cle'))->actuelle('Lyon'));
""")],
       ["Une boucle `for ($essai = 1; $essai <= 3; $essai++) { try { … return …; } catch (ServerExceptionInterface | TransportExceptionInterface) { … } }`.",
        "La 404 et la 401 se reconnaissent dans `catch (ClientExceptionInterface $e)` avec `$e->getResponse()->getStatusCode()`.",
        "Attention : le `toArray()` doit être **dans** le `try` (c'est lui qui déclenche l'appel)."],
       [F("Meteo.php", "php", HC_USES + METEO_FIXE + r"""
final class Meteo
{
    public function __construct(public readonly string $ville, public readonly float $temperature, public readonly string $description) {}
}

final class VilleInconnue extends DomainException {}
final class MeteoIndisponible extends RuntimeException {}

final class MeteoClient
{
    private const ESSAIS = 3;

    public function __construct(private HttpClientInterface $client, private string $cle) {}

    public function actuelle(string $ville): Meteo
    {
        for ($essai = 1; $essai <= self::ESSAIS; $essai++) {
            try {
                $d = $this->client->request('GET', 'https://api.meteo.exemple/v1/current', [
                    'query' => ['city' => $ville, 'units' => 'metric'],
                    'headers' => ['X-Api-Key' => $this->cle],
                    'timeout' => 3,
                ])->toArray();
                return new Meteo($d['location']['name'], (float) $d['current']['temp_c'], $d['current']['condition']['text']);
            } catch (ClientExceptionInterface $e) {
                $statut = $e->getResponse()->getStatusCode();
                if ($statut === 404) throw new VilleInconnue("Ville inconnue : $ville");
                if ($statut === 401) throw new LogicException('Clé API météo invalide');
                throw $e;
            } catch (ServerExceptionInterface | TransportExceptionInterface) {
                // erreur temporaire : on réessaie (en vrai, avec une petite attente croissante)
            }
        }
        throw new MeteoIndisponible('Service météo indisponible');
    }
}

$client = new MockHttpClient([new MockResponse('', ['http_code' => 503]), new MockResponse('', ['error' => 'Connection reset']), MockResponse::json(METEO_LYON)]);
var_dump((new MeteoClient($client, 'cle'))->actuelle('Lyon'));
""")],
       ["503 puis coupure puis 200 → la météo", "404 : un seul appel"],
       run=HRUN(r"""
use Symfony\Component\HttpClient\MockHttpClient as MHC;
use Symfony\Component\HttpClient\Response\MockResponse as MR;
$c = new MHC([new MR('', ['http_code' => 503]), new MR('', ['error' => 'Connection reset']), MR::json(METEO_LYON)]);
$m = (new MeteoClient($c, 'k'))->actuelle('Lyon');
check('503, coupure, puis 200 → la Meteo', $m instanceof Meteo && $m->ville === 'Lyon');
check('… en 3 appels', $c->getRequestsCount() === 3);
$c2 = new MHC(fn() => new MR('{"error":"not found"}', ['http_code' => 404]));
check('404 → VilleInconnue', throws(fn() => (new MeteoClient($c2, 'k'))->actuelle('Atlantide'), VilleInconnue::class));
check('404 : un seul appel (pas de réessai)', $c2->getRequestsCount() === 1);
$c3 = new MHC(fn() => new MR('', ['http_code' => 401]));
check('401 → LogicException', throws(fn() => (new MeteoClient($c3, 'mauvaise'))->actuelle('Lyon'), LogicException::class));
check('401 : un seul appel', $c3->getRequestsCount() === 1);
$c4 = new MHC(fn() => new MR('', ['http_code' => 500]));
check('500 à chaque fois → MeteoIndisponible', throws(fn() => (new MeteoClient($c4, 'k'))->actuelle('Lyon'), MeteoIndisponible::class));
check('… après exactement 3 essais', $c4->getRequestsCount() === 3);
$c5 = new MHC(fn() => new MR('', ['error' => 'Timeout']));
check('coupures répétées → MeteoIndisponible', throws(fn() => (new MeteoClient($c5, 'k'))->actuelle('Lyon'), MeteoIndisponible::class) && $c5->getRequestsCount() === 3);
""")),
    TD(3, "Pagination et cache",
       "L'API du catalogue d'un fournisseur renvoie les livres **page par page** (`links.next`). Et la fiche d'un livre change rarement : inutile de l'appeler à chaque affichage. Écris un client qui parcourt toutes les pages et met les fiches en cache une heure." + HC,
       ["`tous(): array` suit `links.next` (URL complète ou `null`) depuis `https://livres.exemple/api/livres?page=1` et renvoie la liste de **tous** les titres",
        "`parId(int $id): array` renvoie `['id' => …, 'titre' => …]` via `GET https://livres.exemple/api/livres/{id}`, mis en cache **3600 s** (clé `livre_{id}`)",
        "Deux appels à `parId(7)` dans l'heure → **un seul** appel HTTP ; après plus d'une heure → un nouvel appel",
        "Utilise `CacheInterface::get()` et `ItemInterface::expiresAfter()`"],
       [F("Catalogue.php", "php", HC_USES + r"""
final class CatalogueClient
{
    public function __construct(private HttpClientInterface $client, private CacheInterface $cache) {}

    /** @return list<string> */
    public function tous(): array
    {
        // à toi
    }

    public function parId(int $id): array
    {
        // à toi
    }
}
""")],
       ["`$url = 'https://livres.exemple/api/livres?page=1'; while ($url) { $d = $this->client->request('GET', $url)->toArray(); …; $url = $d['links']['next'] ?? null; }`",
        "Chaque page : `$d['data']` est une liste de `['id' => …, 'title' => …]`.",
        "`return $this->cache->get(\"livre_$id\", function (ItemInterface $item) use ($id) { $item->expiresAfter(3600); … });`"],
       [F("Catalogue.php", "php", HC_USES + r"""
final class CatalogueClient
{
    private const BASE = 'https://livres.exemple/api/livres';

    public function __construct(private HttpClientInterface $client, private CacheInterface $cache) {}

    /** @return list<string> */
    public function tous(): array
    {
        $titres = [];
        $url = self::BASE . '?page=1';
        while ($url) {
            $d = $this->client->request('GET', $url, ['timeout' => 5])->toArray();
            foreach ($d['data'] as $livre) {
                $titres[] = $livre['title'];
            }
            $url = $d['links']['next'] ?? null;
        }
        return $titres;
    }

    public function parId(int $id): array
    {
        return $this->cache->get("livre_$id", function (ItemInterface $item) use ($id) {
            $item->expiresAfter(3600);
            $d = $this->client->request('GET', self::BASE . '/' . $id, ['timeout' => 5])->toArray();
            return ['id' => $d['id'], 'titre' => $d['title']];
        });
    }
}
""")],
       ["Toutes les pages sont parcourues", "Le cache évite les appels répétés"],
       run=HRUN(r"""
use Symfony\Component\HttpClient\MockHttpClient as MHC;
use Symfony\Component\HttpClient\Response\MockResponse as MR;
use Symfony\Component\Cache\Adapter\ArrayAdapter;
$pages = [
    1 => ['data' => [['id' => 1, 'title' => 'Dune'], ['id' => 2, 'title' => 'Fondation']], 'links' => ['next' => 'https://livres.exemple/api/livres?page=2']],
    2 => ['data' => [['id' => 3, 'title' => 'Hypérion'], ['id' => 4, 'title' => 'Ubik']], 'links' => ['next' => 'https://livres.exemple/api/livres?page=3']],
    3 => ['data' => [['id' => 7, 'title' => 'Solaris']], 'links' => ['next' => null]],
];
$client = new MHC(function (string $m, string $url) use ($pages) {
    if (preg_match('#/api/livres\?page=(\d+)$#', $url, $mm)) return MR::json($pages[(int) $mm[1]]);
    if (preg_match('#/api/livres/(\d+)$#', $url, $mm)) return MR::json(['id' => (int) $mm[1], 'title' => 'Livre ' . $mm[1]]);
    return new MR('', ['http_code' => 404]);
});
$cache = new ArrayAdapter();
$cat = new CatalogueClient($client, $cache);
check('tous() parcourt les 3 pages', $cat->tous() === ['Dune', 'Fondation', 'Hypérion', 'Ubik', 'Solaris']);
check('… en 3 appels', $client->getRequestsCount() === 3);
$n = $client->getRequestsCount();
check('parId(7) → { id, titre }', $cat->parId(7) === ['id' => 7, 'titre' => 'Livre 7']);
$cat->parId(7); $cat->parId(7);
check('3 appels à parId(7) → 1 seul appel HTTP (cache)', $client->getRequestsCount() === $n + 1);
check('URL de la fiche', end($client->appels)['url'] === 'https://livres.exemple/api/livres/7');
$cache->avancer(3599); $cat->parId(7);
check('après 59 min 59 s : toujours en cache', $client->getRequestsCount() === $n + 1);
$cache->avancer(2); $cat->parId(7);
check('après plus d\'une heure : nouvel appel', $client->getRequestsCount() === $n + 2);
""")),
  ])

# =========================================================================== 6. Consommer en JS
client_js = DM("api-client-js", "Consommer une API côté front, solidement", 25,
  "Écrire le module qui fait tous les appels HTTP du front : en-têtes communs, erreurs, délai maximum, réessais raisonnables et POST rejouables.",
  "Le réseau mobile coupe, les serveurs ont des pics de charge, les utilisateurs cliquent deux fois. Un client HTTP naïf transforme ces incidents en écrans figés et en doublons.",
  ["Un seul module (`client.js`) par API : base URL, JSON, jeton", "Toujours un **délai maximum** (`AbortSignal.timeout`)",
   "Réessayer seulement ce qui peut l'être : GET/PUT/DELETE, sur 5xx/429/réseau, avec délai croissant", "POST rejouable : la même `Idempotency-Key` à chaque essai"],
  ["`fetch` n'a pas de timeout par défaut : un serveur qui ne répond pas fige l'écran.",
   "Ne jamais réessayer une 4xx (sauf 429) : le résultat sera le même.",
   "Délai croissant (100 ms, 200 ms, 400 ms…) pour ne pas achever un serveur déjà en difficulté.",
   "429 : respecter `Retry-After`.",
   "Un POST ne se réessaie que s'il porte une clé d'idempotence, **la même** à chaque essai."],
  ["Un `fetch` sans timeout.", "Réessayer en boucle sans attente.", "Générer une nouvelle clé d'idempotence à chaque essai (elle ne sert plus à rien)."],
  [Q("Une requête GET reçoit 404. On réessaie ?", ["oui, 3 fois", "non", "oui, une fois", "seulement en POST"], 1, "La ressource n'existera pas plus au 2e essai."),
   Q("Comment limiter la durée d'un fetch à 5 s ?", ["setTimeout autour", "{ signal: AbortSignal.timeout(5000) }", "{ timeout: 5000 }", "c'est automatique"], 1, "fetch n'a pas d'option timeout ; on l'annule par un signal."),
   Q("Un POST de paiement réessayé après une coupure doit…", ["générer une nouvelle Idempotency-Key", "réutiliser la même Idempotency-Key", "ne pas en avoir", "passer en GET"], 1, "C'est la même opération : le serveur la reconnaît et ne la rejoue pas.")],
  prereq=[
    P("`AbortSignal.timeout(ms)`", "Un signal qui annule la requête au bout de `ms` millisecondes : `fetch(url, { signal: AbortSignal.timeout(5000) })` rejette avec une `TimeoutError`."),
    P("Réessai avec délai croissant (backoff)", "Attendre de plus en plus longtemps entre deux essais (100, 200, 400 ms…) pour laisser le serveur récupérer."),
    P("Erreur temporaire", "Une erreur qui peut disparaître toute seule : 502, 503, 504, 429, coupure réseau, délai dépassé."),
    P("UUID", "Identifiant unique aléatoire (`crypto.randomUUID()`), idéal pour une clé d'idempotence."),
  ],
  diagram=D(
    nodes=[
      N("app", 0, 1, "Écrans React", "client.get('/taches')", kind="file", color="accent"),
      N("cl", 1, 1, "client.js", "base URL · JSON · jeton", kind="box", color="warn"),
      N("to", 1, 0, "Délai maximum", "AbortSignal.timeout", kind="pill"),
      N("re", 2, 1, "Réessais", "5xx · 429 · réseau", kind="pill"),
      N("ik", 1, 2, "Idempotency-Key", "POST rejouable", kind="pill"),
      N("api", 3, 1, "API", "", kind="db", color="muted"),
    ],
    edges=[E("app", "cl"), E("cl", "re"), E("re", "api"), E("cl", "to", dashed=True), E("cl", "ik", dashed=True)],
    caption="Les écrans ne font jamais fetch eux-mêmes : un seul module gère les en-têtes, les erreurs, le délai maximum et les réessais."),
  lessons=[
    L("Un client unique", r"""
Plutôt que des `fetch` éparpillés dans les composants, un module qui centralise tout ce qui est commun :

```js
export function creerClient({ baseUrl, getToken }) {
  async function requete(methode, chemin, corps) {
    const headers = { Accept: 'application/json' };
    if (corps !== undefined) headers['Content-Type'] = 'application/json';
    const jeton = getToken?.();
    if (jeton) headers.Authorization = `Bearer ${jeton}`;

    const res = await fetch(baseUrl + chemin, { method: methode, headers, body: corps === undefined ? undefined : JSON.stringify(corps) });
    if (!res.ok) throw new ApiError(res.status, await res.json().catch(() => null));
    return res.status === 204 ? null : res.json();
  }
  return {
    get: (c) => requete('GET', c),
    post: (c, corps) => requete('POST', c, corps),
    patch: (c, corps) => requete('PATCH', c, corps),
    del: (c) => requete('DELETE', c),
  };
}
```

Changer l'URL de l'API, ajouter un en-tête, gérer le 401 globalement : une seule modification. (Le parcours « Données & API » faisait pareil avec axios et ses intercepteurs.)
"""),
    L("Délai maximum et réessais", r"""
`fetch` attend **indéfiniment** par défaut. On lui donne un délai :

```js
const res = await fetch(url, { signal: AbortSignal.timeout(5000) });   // TimeoutError après 5 s
```

Ensuite, réessayer **seulement** ce qui peut réussir au 2e essai :

| Situation | Réessayer ? |
|---|---|
| coupure réseau, délai dépassé | oui |
| 502, 503, 504 | oui |
| 429 | oui, après `Retry-After` secondes |
| 400, 401, 403, 404, 409, 422 | **non** |
| POST sans clé d'idempotence | **non** (risque de doublon) |

Avec un **délai croissant** entre les essais (100 ms, 200 ms, 400 ms…, souvent avec un peu d'aléatoire) et un nombre d'essais limité :

```js
for (let essai = 0; ; essai++) {
  try { return await unEssai(); }
  catch (e) {
    if (!temporaire(e) || essai + 1 >= max) throw e;
    await attendre(e.retryAfter ? e.retryAfter * 1000 : 100 * 2 ** essai);
  }
}
```

TanStack Query fait ça pour toi en lecture (`retry: 3` par défaut), mais pas pour les mutations.
"""),
    L("Rejouer un POST sans doublon", r"""
Le scénario classique : l'utilisateur clique « Payer », la requête part, le serveur débite, puis le réseau coupe **avant** la réponse. Le front ne sait pas si c'est passé.

Avec une **clé d'idempotence** générée **une fois par opération** (pas par essai) :

```js
export async function payer(client, montant) {
  const cle = crypto.randomUUID();                         // une seule clé pour cette opération
  return client.post('/api/paiements', { montant }, { idempotencyKey: cle, essais: 3 });
}
```

À chaque essai, la même clé part dans `Idempotency-Key`. Le serveur (module Robustesse) reconnaît l'opération et renvoie la réponse mémorisée au lieu de débiter à nouveau.

Côté interface, on complète par : désactiver le bouton pendant l'envoi, et afficher clairement « paiement en cours » plutôt qu'un écran figé.
"""),
  ],
  recap=["Un module client unique : base URL, JSON, jeton, erreurs.",
         "Toujours `AbortSignal.timeout(ms)`.",
         "Réessayer : réseau, délai dépassé, 502/503/504, 429 (Retry-After) ; jamais les autres 4xx.",
         "Délai croissant et nombre d'essais limité.",
         "POST rejouable seulement avec une clé d'idempotence, identique à chaque essai."],
  example=F("client.js", "js", r"""
const attendre = (ms) => new Promise((r) => setTimeout(r, ms));
const temporaire = (status) => status === 0 || status === 429 || status >= 502;

export async function avecReessais(unEssai, { essais = 3, base = 100 } = {}) {
  for (let i = 0; ; i++) {
    try {
      return await unEssai();
    } catch (e) {
      if (!temporaire(e.status) || i + 1 >= essais) throw e;
      await attendre(e.retryAfter ? e.retryAfter * 1000 : base * 2 ** i);   // 100, 200, 400…
    }
  }
}

// usage : avecReessais(() => getJson('/api/taches', { timeoutMs: 5000 }))
"""),
  notes=["`temporaire()` décide ce qui mérite un 2e essai.", "Le délai double à chaque essai, ou suit `Retry-After`.", "Le nombre d'essais est limité."],
  tds=[
    TD(1, "Un client HTTP pour toute l'appli",
       "Écris `creerClient()`, le module par lequel passeront tous les appels du front." + JS,
       ["`creerClient({ baseUrl, getToken })` renvoie `{ get, post, patch, del }`",
        "Chaque requête envoie `Accept: application/json` ; avec un corps : `Content-Type: application/json` et le corps en JSON",
        "Si `getToken()` renvoie un jeton : `Authorization: Bearer <jeton>` (relu **à chaque** requête : il peut changer)",
        "Réponse OK → le JSON (ou `null` pour 204) ; sinon → `ApiError` (fournie) avec `status` et le corps du problème"],
       [F("client.js", "js", r"""
export class ApiError extends Error {
  constructor(status, probleme) {
    super((probleme && (probleme.detail || probleme.title)) || 'Erreur HTTP ' + status);
    this.status = status;
    this.probleme = probleme;
  }
}

export function creerClient({ baseUrl, getToken }) {
  // à toi
}
""")],
       ["Une fonction interne `requete(methode, chemin, corps)` utilisée par les 4 méthodes.",
        "`body: corps === undefined ? undefined : JSON.stringify(corps)`.",
        "`const probleme = await res.json().catch(() => null); throw new ApiError(res.status, probleme);`"],
       [F("client.js", "js", r"""
export class ApiError extends Error {
  constructor(status, probleme) {
    super((probleme && (probleme.detail || probleme.title)) || 'Erreur HTTP ' + status);
    this.status = status;
    this.probleme = probleme;
  }
}

export function creerClient({ baseUrl, getToken }) {
  async function requete(methode, chemin, corps) {
    const headers = { Accept: 'application/json' };
    if (corps !== undefined) headers['Content-Type'] = 'application/json';
    const jeton = getToken ? getToken() : null;
    if (jeton) headers.Authorization = 'Bearer ' + jeton;

    const res = await fetch(baseUrl + chemin, {
      method: methode,
      headers,
      body: corps === undefined ? undefined : JSON.stringify(corps),
    });
    if (!res.ok) {
      const probleme = await res.json().catch(() => null);
      throw new ApiError(res.status, probleme);
    }
    return res.status === 204 ? null : res.json();
  }

  return {
    get: (chemin) => requete('GET', chemin),
    post: (chemin, corps) => requete('POST', chemin, corps),
    patch: (chemin, corps) => requete('PATCH', chemin, corps),
    del: (chemin) => requete('DELETE', chemin),
  };
}
""")],
       ["Le jeton est relu à chaque appel", "Les erreurs deviennent des ApiError"],
       run=RUN("js", entry="client.js", api=r"""
window.__recu = [];
const garder = (m) => (p, body, h) => { window.__recu.push({ m, body, h }); return null; };
__api["GET /v2/taches"] = (p, b, h) => { window.__recu.push({ m: 'GET', h }); return h.authorization ? [{ id: 1, titre: 'Lire' }] : [401, { title: 'Unauthorized', detail: 'Jeton manquant' }]; };
__api["POST /v2/taches"] = (p, b, h) => { window.__recu.push({ m: 'POST', body: b, h }); return [201, Object.assign({ id: 2 }, b)]; };
__api["PATCH /v2/taches/2"] = (p, b, h) => { window.__recu.push({ m: 'PATCH', body: b, h }); return Object.assign({ id: 2, titre: 'x' }, b); };
__api["DELETE /v2/taches/2"] = (p, b, h) => { window.__recu.push({ m: 'DELETE', h }); return [204, null]; };
__api["GET /v2/taches/9"] = () => [404, { type: 'about:blank', title: 'Not Found', status: 404, detail: 'Tâche 9 introuvable' }];
""", tests=r"""
const { creerClient, ApiError } = require('./client');
let jeton = 'j1';
const api = creerClient({ baseUrl: '/v2', getToken: () => jeton });
const l = await api.get('/taches');
assert(Array.isArray(l) && l[0].titre === 'Lire', 'get → le JSON');
const r0 = window.__recu[0].h;
assert(r0.authorization === 'Bearer j1', 'Authorization: Bearer <jeton>');
assert(r0.accept === 'application/json', 'Accept: application/json');
assert(!r0['content-type'], 'GET sans corps : pas de Content-Type');
const c = await api.post('/taches', { titre: 'Écrire' });
assert(c.id === 2 && c.titre === 'Écrire', 'post → le JSON créé');
const r1 = window.__recu[1];
assert(r1.h['content-type'] === 'application/json' && r1.body && r1.body.titre === 'Écrire', 'POST : Content-Type JSON + corps');
jeton = 'j2';
await api.patch('/taches/2', { faite: true });
assert(window.__recu[2].h.authorization === 'Bearer j2', 'Le jeton est relu à chaque requête');
assert.equal(await api.del('/taches/2'), null, 'del → null (204)');
jeton = null;
let err = null; try { await api.get('/taches'); } catch (e) { err = e; }
assert(err instanceof ApiError && err.status === 401, 'Sans jeton : pas d\'en-tête, et le 401 devient une ApiError');
err = null; try { await api.get('/taches/9'); } catch (e) { err = e; }
assert(err instanceof ApiError && err.status === 404 && err.message === 'Tâche 9 introuvable', '404 → ApiError avec le detail');
""")),
    TD(2, "Délai maximum et réessais raisonnables",
       "L'API est parfois lente ou renvoie 503 pendant un déploiement. Écris `getJson()` avec un délai maximum et des réessais **seulement** quand ça a du sens." + JS,
       ["`getJson(url, { timeoutMs = 5000, essais = 3, base = 100 })` : fait un GET et renvoie le JSON",
        "Délai dépassé (`AbortSignal.timeout`) ou coupure réseau → erreur `{ status: 0 }` temporaire",
        "Réessaie sur status 0, 429, 502, 503, 504 ; attend `base * 2 ** n` ms entre les essais, ou `Retry-After` secondes pour une 429",
        "Ne réessaie **jamais** sur une autre erreur (400, 404…) ; après le dernier essai, lève la dernière erreur (un objet `Error` avec `status`)"],
       [F("reseau.js", "js", r"""
export const attendre = (ms) => new Promise((r) => setTimeout(r, ms));

export async function getJson(url, { timeoutMs = 5000, essais = 3, base = 100 } = {}) {
  // à toi
}
""")],
       ["Un essai : `const res = await fetch(url, { signal: AbortSignal.timeout(timeoutMs) });` dans un `try` ; le `catch` (TimeoutError, TypeError) → `Object.assign(new Error('réseau'), { status: 0 })`.",
        "Pour une 429 : `Number(res.headers.get('Retry-After'))` secondes.",
        "Boucle `for (let i = 0; ; i++)` : `if (!temporaire(e.status) || i + 1 >= essais) throw e;`"],
       [F("reseau.js", "js", r"""
export const attendre = (ms) => new Promise((r) => setTimeout(r, ms));

const TEMPORAIRES = [0, 429, 502, 503, 504];

async function unEssai(url, timeoutMs) {
  let res;
  try {
    res = await fetch(url, { signal: AbortSignal.timeout(timeoutMs) });
  } catch (e) {
    throw Object.assign(new Error(e && e.name === 'TimeoutError' ? 'délai dépassé' : 'réseau'), { status: 0 });
  }
  if (res.ok) return res.json();
  const retry = Number(res.headers.get('Retry-After'));
  throw Object.assign(new Error('HTTP ' + res.status), { status: res.status, retryAfter: Number.isFinite(retry) && retry > 0 ? retry : null });
}

export async function getJson(url, { timeoutMs = 5000, essais = 3, base = 100 } = {}) {
  for (let i = 0; ; i++) {
    try {
      return await unEssai(url, timeoutMs);
    } catch (e) {
      if (!TEMPORAIRES.includes(e.status) || i + 1 >= essais) throw e;
      await attendre(e.retryAfter ? e.retryAfter * 1000 : base * 2 ** i);
    }
  }
}
""")],
       ["503, 503, 200 → le JSON en 3 appels", "404 : un seul appel"],
       run=RUN("js", entry="reseau.js", api=r"""
window.__n = {};
const compter = (k) => (window.__n[k] = (window.__n[k] || 0) + 1);
__api["GET /flaky"] = () => compter('flaky') < 3 ? [503, { title: 'Service Unavailable' }] : { ok: 1 };
__api["GET /absent"] = () => { compter('absent'); return [404, { title: 'Not Found' }]; };
__api["GET /toujours503"] = () => { compter('t503'); return [503, null]; };
__api["GET /lent"] = async () => { compter('lent'); await new Promise((r) => setTimeout(r, 1500)); return { ok: 1 }; };
__api["GET /limite"] = () => compter('limite') < 2 ? [429, { title: 'Too Many Requests' }, { 'Retry-After': '1' }] : { ok: 2 };
""", tests=r"""
const { getJson } = require('./reseau');
const t0 = Date.now();
const r = await getJson('/flaky', { base: 50 });
assert(r && r.ok === 1, '503, 503 puis 200 → le JSON');
assert.equal(window.__n.flaky, 3, '… en 3 appels');
let e = null; try { await getJson('/absent', { base: 10 }); } catch (x) { e = x; }
assert(e && e.status === 404, '404 → erreur avec status 404');
assert.equal(window.__n.absent, 1, '404 : un seul appel, pas de réessai');
e = null; try { await getJson('/toujours503', { essais: 3, base: 10 }); } catch (x) { e = x; }
assert(e && e.status === 503 && window.__n.t503 === 3, 'Toujours 503 → lève après 3 essais');
e = null; const t1 = Date.now();
try { await getJson('/lent', { timeoutMs: 300, essais: 2, base: 10 }); } catch (x) { e = x; }
assert(e && e.status === 0, 'Délai dépassé → status 0');
assert(window.__n.lent === 2 && Date.now() - t1 < 1400, 'Délai dépassé : réessayé (2 essais), sans attendre la réponse lente');
const t2 = Date.now();
const lim = await getJson('/limite', { base: 10 });
assert(lim.ok === 2 && Date.now() - t2 >= 950, '429 + Retry-After: 1 → attend ~1 s puis réussit');
""")),
    TD(3, "Un paiement rejouable sans doublon",
       "Le serveur de paiement accepte une `Idempotency-Key`. Le réseau coupe parfois **après** que le serveur a débité (la réponse se perd). Écris `payer()` pour réessayer sans jamais débiter deux fois." + JS,
       ["`payer(montant, { essais = 3 })` : `POST /api/paiements` avec `{ montant }` et l'en-tête `Idempotency-Key`",
        "Une seule clé (`crypto.randomUUID()`) **pour toute l'opération**, réutilisée à chaque essai",
        "Réessaie sur status 0 (coupure) et 5xx ; renvoie le paiement (`{ id, montant }`) ; erreur 4xx → levée immédiatement",
        "Deux appels distincts à `payer()` = deux paiements (deux clés différentes)"],
       [F("paiement.js", "js", r"""
const attendre = (ms) => new Promise((r) => setTimeout(r, ms));

export async function payer(montant, { essais = 3 } = {}) {
  // à toi
}
""")],
       ["`const cle = crypto.randomUUID();` **avant** la boucle.",
        "Chaque essai : `fetch('/api/paiements', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Idempotency-Key': cle }, body: JSON.stringify({ montant }) })`.",
        "Coupure : le `fetch` rejette (TypeError) → considère-le comme `status: 0`."],
       [F("paiement.js", "js", r"""
const attendre = (ms) => new Promise((r) => setTimeout(r, ms));

export async function payer(montant, { essais = 3 } = {}) {
  const cle = crypto.randomUUID();                  // une clé pour TOUTE l'opération
  for (let i = 0; ; i++) {
    let status;
    try {
      const res = await fetch('/api/paiements', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Idempotency-Key': cle },
        body: JSON.stringify({ montant }),
      });
      if (res.ok) return res.json();
      status = res.status;
    } catch (e) {
      status = 0;                                    // coupure : on ne sait pas si c'est passé
    }
    if (!(status === 0 || status >= 500) || i + 1 >= essais) {
      throw Object.assign(new Error('Paiement impossible (' + status + ')'), { status });
    }
    await attendre(50 * 2 ** i);
  }
}
""")],
       ["Une coupure après débit ne crée pas de 2e paiement", "Deux paiements volontaires = deux clés"],
       run=RUN("js", entry="paiement.js", api=r"""
window.__banque = { debits: [], memo: {}, cles: [], coupure: 0 };
__api["POST /api/paiements"] = (p, body, h) => {
  const B = window.__banque; const cle = h['idempotency-key'];
  B.cles.push(cle);
  if (!cle) return [400, { title: 'Idempotency-Key requis' }];
  if (!B.memo[cle]) { B.debits.push(body.montant); B.memo[cle] = { id: B.debits.length, montant: body.montant }; }
  if (B.coupure > 0) { B.coupure--; return [503, null]; }      // la réponse « se perd » après le débit
  return [201, B.memo[cle]];
};
__api["POST /api/refuse"] = () => [422, { title: 'Montant invalide' }];
""", tests=r"""
const { payer } = require('./paiement');
const B = window.__banque;
B.coupure = 2;                                  // débité au 1er essai, mais 2 réponses perdues
const p = await payer(4990);
assert(p && p.montant === 4990 && p.id === 1, 'Le paiement finit par réussir');
assert.equal(B.debits.length, 1, 'Un seul débit malgré 3 essais');
assert(B.cles.length === 3 && B.cles.every((k) => k && k === B.cles[0]), 'La même Idempotency-Key à chaque essai');
const p2 = await payer(1500);
assert(B.debits.length === 2 && p2.id === 2, 'Un 2e paiement volontaire → un 2e débit');
assert(B.cles[3] !== B.cles[0], '… avec une nouvelle clé');
const realFetch = window.fetch; let n = 0;
window.fetch = (u, i) => { n++; if (n === 1) return Promise.reject(new TypeError('Failed to fetch')); return realFetch(u, i); };
const p3 = await payer(700);
window.fetch = realFetch;
assert(p3.montant === 700 && B.debits.length === 3, 'Coupure réseau (fetch rejette) → réessai réussi, un seul débit');
""")),
  ])

MODULES = [rest, erreurs, auth, robuste, client_php, client_js]

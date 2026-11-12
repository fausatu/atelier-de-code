from common import V2, P, L, D, N, E, LANE, F, TD, RUN
from c_arch_v1 import MODULES as V1
from symfony_sim import SYMFONY_SETUP
from c_dto import USES, SIM
from c_data import LIB_API

v1 = {m["id"]: m for m in V1}

def SRUN(tests):
    return RUN("php", tests="Atelier\\App::$echo = false;\nAtelier\\App::reset();\n" + tests, setup=SYMFONY_SETUP)

def lines(cls, meth):
    return f"((new ReflectionMethod({cls}::class, '{meth}'))->getEndLine() - (new ReflectionMethod({cls}::class, '{meth}'))->getStartLine() - 1)"

# Boutique : produits en mémoire, utilisée par les TD "rôles"
BOUTIQUE = F("boutique.php", "php", USES + r"""
// ---- Fourni : les données de la boutique (en mémoire) ----
final class Produit
{
    public function __construct(private int $id, private string $nom, private int $prix, private int $stock) {}
    public function getId(): int { return $this->id; }
    public function getNom(): string { return $this->nom; }
    public function getPrix(): int { return $this->prix; }
    public function getStock(): int { return $this->stock; }
    public function setStock(int $s): void { $this->stock = $s; }   // à remplacer par une méthode métier
}

final class ProduitRepository
{
    private array $produits;
    public function __construct()
    {
        $this->produits = [1 => new Produit(1, 'Clavier', 4990, 10), 2 => new Produit(2, 'Écran', 18900, 1)];
    }
    public function find(int $id): ?Produit { return $this->produits[$id] ?? null; }
}

final class Commande
{
    private string $statut = 'payee';
    public function __construct(private int $id, private Produit $produit, private int $quantite, private string $client) {}
    public function getId(): int { return $this->id; }
    public function getProduit(): Produit { return $this->produit; }
    public function getQuantite(): int { return $this->quantite; }
    public function getTotal(): int { return $this->produit->getPrix() * $this->quantite; }
    public function getStatut(): string { return $this->statut; }
    public function getClient(): string { return $this->client; }
    public function expedier(): void { $this->statut = 'expediee'; }
}

final class CommandeRepository
{
    /** @var array<int, Commande> */
    public array $commandes = [];
    public function save(Commande $c): void { $this->commandes[$c->getId()] = $c; }
    public function find(int $id): ?Commande { return $this->commandes[$id] ?? null; }
    public function nextId(): int { return count($this->commandes) + 1; }
}
""")

# ---------------------------------------------------------------- Rôles
roles = V2(v1["arch-roles"],
  prereq=[
    P("Couche", "Un ensemble de classes qui ont le même rôle (toutes les classes « contrôleur », toutes les classes « repository »…). On empile les couches : chacune ne parle qu'à la suivante."),
    P("Responsabilité unique", "Une classe = une raison de changer. Si tu dois la modifier à la fois quand le format JSON change ET quand une règle métier change, elle fait deux choses."),
    P("Cas d'usage", "Une action que l'utilisateur veut accomplir : « passer une commande », « emprunter un livre ». En code, c'est souvent une méthode de service."),
    P("Logique métier", "Les règles du domaine, indépendantes de la technique : « pas de stock négatif », « 3 emprunts maximum ». Elles existeraient même sans site web."),
  ],
  diagram=D(
    nodes=[
      N("http", 0, 1, "Requête HTTP", "POST /api/commandes", kind="doc", color="accent"),
      N("ctrl", 1, 1, "Contrôleur", "reçoit · délègue · répond"),
      N("dto", 1, 0, "DTO", "forme des données", kind="file", color="muted"),
      N("svc", 2, 1, "Service", "exécute le cas d'usage", color="warn"),
      N("ent", 3, 0, "Entité", "porte ses règles", kind="pill", color="good"),
      N("repo", 3, 2, "Repository", "lit / range en base", kind="db", color="muted"),
    ],
    edges=[E("http", "ctrl"), E("dto", "ctrl", dashed=True), E("ctrl", "svc", "appelle"), E("svc", "ent", "méthode métier"), E("svc", "repo", "find / save")],
    lanes=[LANE("HTTP", 0, 1, "accent"), LANE("Métier & données", 2, 3, "tc")],
    caption="Chaque rôle a un seul travail. Les flèches vont toujours de HTTP vers les données, jamais l'inverse."),
  lessons=[
    L("Le contrôleur qui fait tout", r"""
Sans organisation, toute la logique d'une route finit dans le contrôleur :

```php
#[Route('/api/commandes', methods: ['POST'])]
public function create(Request $request, EntityManagerInterface $em): JsonResponse
{
    $data = json_decode($request->getContent(), true);                 // lire le JSON
    if (empty($data['produitId']) || ($data['quantite'] ?? 0) < 1) {    // valider
        return new JsonResponse(['error' => 'Données invalides'], 422);
    }
    $produit = $em->getRepository(Produit::class)->find($data['produitId']);   // lire la base
    if ($produit->getStock() < $data['quantite']) {                     // règle métier
        return new JsonResponse(['error' => 'Stock insuffisant'], 409);
    }
    $produit->setStock($produit->getStock() - $data['quantite']);       // modifier
    $commande = new Commande($produit, $data['quantite'], $this->getUser());
    $em->persist($commande);                                            // enregistrer
    $em->flush();
    return new JsonResponse(['id' => $commande->getId(), 'total' => $commande->getTotal() / 100 . ' €'], 201);   // formater
}
```

Ça fonctionne, mais : on ne peut pas réutiliser « passer une commande » ailleurs (une commande console, une autre route), on ne peut pas le tester sans simuler HTTP, la règle du stock est cachée au milieu, et chaque nouvelle route recopie une partie de ce code. Le contrôleur fait **sept** choses.
"""),
    L("Les cinq rôles, comme dans un restaurant", r"""
Dans un restaurant, personne ne fait tout : le serveur prend la commande et rapporte le plat, le chef cuisine, le magasinier gère la réserve, le bon de commande décrit ce qui est demandé. En Symfony :

- **Contrôleur** (le serveur) : parle **HTTP**. Il reçoit la requête, appelle le bon service, choisit le statut et renvoie le JSON. Idéalement 2 à 5 lignes par action, sans `if` métier.
- **DTO** (le bon de commande) : décrit la **forme** des données qui entrent et sortent. Pas de logique.
- **Service** (le chef) : exécute **le cas d'usage**. Il charge ce qu'il faut, applique les règles (souvent en appelant l'entité), enregistre. Il ne connaît **pas** HTTP : ni `Request`, ni `JsonResponse`, ni statuts.
- **Entité** (l'ingrédient avec sa fiche) : les données **et leurs règles** (`retirerDuStock()` refuse un stock négatif).
- **Repository** (le magasinier) : **lit** les entités en base (`find`, requêtes). Pas de règles.

Le test pour savoir si une classe est bien découpée : peux-tu la décrire en une phrase **sans « et »** ?
"""),
    L("Ranger chaque ligne au bon endroit", r"""
Reprenons le contrôleur ci-dessus, ligne par ligne :

| Ce que fait le code | Où ça va |
|---|---|
| lire et valider le JSON | **DTO** `CommandeInput` + `#[MapRequestPayload]` |
| trouver le produit | **Repository** (`find`) appelé par le service |
| « pas assez de stock » + retirer du stock | **Entité** `Produit::retirerDuStock()` (une seule règle) |
| créer la commande, enregistrer | **Service** `CommandeService::passer()` |
| choisir les champs et le format de sortie | **DTO** `CommandeOutput::fromEntity()` |
| statut 201 et JSON | **Contrôleur** |

Le contrôleur devient :

```php
#[Route('/api/commandes', methods: ['POST'])]
public function create(#[MapRequestPayload] CommandeInput $input, CommandeService $commandes): JsonResponse
{
    return $this->json(CommandeOutput::fromEntity($commandes->passer($input)), 201);
}
```

Et la règle du stock a un nom, un endroit, et peut être testée seule.
"""),
    L("Pourquoi le service ne connaît pas HTTP", r"""
Un même cas d'usage est souvent déclenché de plusieurs façons : une route d'API, une commande console (`bin/console app:relancer`), une tâche planifiée, un message asynchrone, un test automatisé. Si le service renvoie une `JsonResponse` ou lit `$request`, il ne fonctionne que dans le premier cas.

Règle : le service **reçoit des données** (un DTO, des ids) et **renvoie des objets métier** (une entité, un résultat). Quand une règle est violée, il **lève une exception métier** (`StockInsuffisant`) au lieu de renvoyer un statut HTTP. C'est le rôle de la couche HTTP de traduire cette exception en 409 (module « Les erreurs à travers les couches »).

Ainsi, `passer()` peut être appelé depuis n'importe où, et testé avec un simple appel de méthode.
"""),
  ],
  recap=[
    "Contrôleur = HTTP (reçoit, délègue, répond). Quelques lignes, pas de `if` métier.",
    "DTO = forme des données. Service = cas d'usage. Entité = données + règles. Repository = lectures.",
    "Le service ne connaît pas HTTP : il reçoit des données, renvoie des objets, lève des exceptions métier.",
    "Une règle = un endroit, avec un nom (`retirerDuStock()`).",
    "Test : décrire la classe en une phrase sans « et ».",
  ],
  example=[F("src/Dto/CommandeInput.php", "php", r"""
<?php

namespace App\Dto;

use Symfony\Component\Validator\Constraints as Assert;

final class CommandeInput
{
    public function __construct(
        #[Assert\Positive] public readonly int $produitId = 0,
        #[Assert\Range(min: 1, max: 20)] public readonly int $quantite = 0,
    ) {}
}
"""), F("src/Entity/Produit.php", "php", r"""
<?php

namespace App\Entity;

use App\Exception\StockInsuffisant;

class Produit
{
    // ... id, nom, prix, stock (mapping Doctrine)

    public function retirerDuStock(int $quantite): void
    {
        if ($quantite > $this->stock) {
            throw new StockInsuffisant("Stock insuffisant pour {$this->nom}");
        }
        $this->stock -= $quantite;
    }
}
"""), F("src/Service/CommandeService.php", "php", r"""
<?php

namespace App\Service;

use App\Dto\CommandeInput;
use App\Entity\Commande;
use App\Entity\User;
use App\Exception\ProduitIntrouvable;
use App\Repository\ProduitRepository;
use Doctrine\ORM\EntityManagerInterface;

final class CommandeService
{
    public function __construct(
        private ProduitRepository $produits,
        private EntityManagerInterface $em,
    ) {}

    public function passer(CommandeInput $in, User $client): Commande
    {
        $produit = $this->produits->find($in->produitId) ?? throw new ProduitIntrouvable();
        $produit->retirerDuStock($in->quantite);          // la règle est dans l'entité
        $commande = new Commande($produit, $in->quantite, $client);
        $this->em->persist($commande);
        $this->em->flush();
        return $commande;
    }
}
"""), F("src/Controller/CommandeController.php", "php", r"""
<?php

namespace App\Controller;

use App\Dto\CommandeInput;
use App\Dto\CommandeOutput;
use App\Entity\User;
use App\Service\CommandeService;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpKernel\Attribute\MapRequestPayload;
use Symfony\Component\Routing\Attribute\Route;
use Symfony\Component\Security\Http\Attribute\CurrentUser;

final class CommandeController extends AbstractController
{
    #[Route('/api/commandes', methods: ['POST'])]
    public function create(
        #[MapRequestPayload] CommandeInput $input,
        #[CurrentUser] User $user,
        CommandeService $commandes,
    ): JsonResponse {
        return $this->json(CommandeOutput::fromEntity($commandes->passer($input, $user)), 201);
    }
}
""")],
  notes=["Chaque fichier a un seul rôle : lis-les dans l'ordre DTO → Entité → Service → Contrôleur.",
         "La règle « pas de stock négatif » n'existe qu'à un endroit : `Produit::retirerDuStock()`.",
         "`CommandeService::passer()` ne contient ni `Request`, ni `JsonResponse`, ni statut HTTP.",
         "Le contrôleur fait une ligne : DTO en entrée, service, DTO en sortie, 201."],
  td1=dict(path="Commande.php",
    title="Refactoriser un contrôleur qui fait tout",
    enonce="Ce contrôleur lit le JSON, valide, cherche le produit, applique la règle du stock, crée la commande et formate la réponse. Range chaque morceau à sa place, sans changer le comportement HTTP. " + SIM,
    consignes=["`CommandeInput` (DTO) remplace la lecture et la validation manuelles (`produitId` et `quantite` positifs)",
               "La règle « stock suffisant, puis retirer » vit à **un seul** endroit (une méthode dédiée) et lève `StockInsuffisant` (409)",
               "`ProduitIntrouvable` (404) ; `CommandeService::passer(CommandeInput): Commande` orchestre tout, sans rien connaître de HTTP",
               "`CommandeOutput::fromEntity()` choisit les champs `id` et `total`",
               "L'action du contrôleur ne fait plus que 1 à 3 lignes"],
    hints=["Le corps arrive maintenant via `#[MapRequestPayload] CommandeInput $input` : plus besoin de `$GLOBALS['__body']`.",
           "Tu peux modifier `boutique.php` pour ajouter `Produit::retirerDuStock()`, ou écrire la règle dans une petite classe dédiée.",
           "`$produit = $this->produits->find($in->produitId) ?? throw new ProduitIntrouvable('Produit introuvable');`"],
    checks=["Mêmes statuts qu'avant : 201, 422, 404, 409", "Le contrôleur ne contient plus aucun `if`"],
    files=[BOUTIQUE, F("Commande.php", "php", r"""
<?php
// Ce contrôleur fait tout. Refactorise-le en : CommandeInput (DTO), Produit::retirerDuStock() (règle),
// StockInsuffisant (409), CommandeService::passer(), CommandeOutput::fromEntity().
// Le comportement HTTP doit rester identique.

final class CommandeController extends AbstractController
{
    #[Route('/api/commandes', methods: ['POST'])]
    public function create(ProduitRepository $produits, CommandeRepository $commandes): JsonResponse
    {
        $data = $GLOBALS['__body'] ?? [];   // (dans le simulateur, le corps brut)
        if (empty($data['produitId']) || ($data['quantite'] ?? 0) < 1) {
            return $this->json(['error' => 'Données invalides'], 422);
        }
        $produit = $produits->find($data['produitId']);
        if (!$produit) {
            return $this->json(['error' => 'Produit introuvable'], 404);
        }
        if ($produit->getStock() < $data['quantite']) {
            return $this->json(['error' => 'Stock insuffisant'], 409);
        }
        $produit->setStock($produit->getStock() - $data['quantite']);
        $commande = new Commande($commandes->nextId(), $produit, $data['quantite'], 'client');
        $commandes->save($commande);
        return $this->json(['id' => $commande->getId(), 'total' => $commande->getTotal()], 201);
    }
}

$GLOBALS['__body'] = ['produitId' => 1, 'quantite' => 2];
App::request('POST', '/api/commandes', $GLOBALS['__body']);
""")],
    solution=[F("Commande.php", "php", r"""
<?php
final class CommandeInput
{
    public function __construct(
        #[Assert\Positive] public readonly int $produitId = 0,
        #[Assert\Positive] public readonly int $quantite = 0,
    ) {}
}

#[WithHttpStatus(409)] final class StockInsuffisant extends \DomainException {}
#[WithHttpStatus(404)] final class ProduitIntrouvable extends \DomainException {}

final class Stock
{
    /** La règle du stock, sur le produit fourni (qu'on ne peut pas modifier ici). */
    public static function retirer(Produit $p, int $quantite): void
    {
        if ($quantite > $p->getStock()) throw new StockInsuffisant('Stock insuffisant');
        $p->setStock($p->getStock() - $quantite);
    }
}

final class CommandeService
{
    public function __construct(private ProduitRepository $produits, private CommandeRepository $commandes) {}

    public function passer(CommandeInput $in): Commande
    {
        $produit = $this->produits->find($in->produitId) ?? throw new ProduitIntrouvable('Produit introuvable');
        Stock::retirer($produit, $in->quantite);
        $commande = new Commande($this->commandes->nextId(), $produit, $in->quantite, 'client');
        $this->commandes->save($commande);
        return $commande;
    }
}

final class CommandeOutput
{
    public function __construct(public readonly int $id, public readonly int $total) {}
    public static function fromEntity(Commande $c): self { return new self($c->getId(), $c->getTotal()); }
}

final class CommandeController extends AbstractController
{
    #[Route('/api/commandes', methods: ['POST'])]
    public function create(#[MapRequestPayload] CommandeInput $input, CommandeService $service): JsonResponse
    {
        return $this->json(CommandeOutput::fromEntity($service->passer($input)), 201);
    }
}

App::request('POST', '/api/commandes', ['produitId' => 1, 'quantite' => 2]);
""")],
    run=SRUN(r"""
$r = App::request('POST', '/api/commandes', ['produitId' => 1, 'quantite' => 2]);
check('Commande valide → 201 {id, total: 9980}', $r->status === 201 && ($r->json['total'] ?? 0) === 9980, (string) $r);
check('Le stock du clavier passe à 8', App::get(ProduitRepository::class)->find(1)->getStock() === 8);
check('Quantité 0 → 422', App::request('POST', '/api/commandes', ['produitId' => 1, 'quantite' => 0])->status === 422);
check('Produit 9 → 404', App::request('POST', '/api/commandes', ['produitId' => 9, 'quantite' => 1])->status === 404);
check('2 écrans (stock 1) → 409', App::request('POST', '/api/commandes', ['produitId' => 2, 'quantite' => 2])->status === 409);
check('Le stock de l\'écran n\'a pas bougé', App::get(ProduitRepository::class)->find(2)->getStock() === 1);
check('Un CommandeService existe et se construit seul', class_exists('CommandeService') && App::get('CommandeService') instanceof CommandeService);
$m = new ReflectionMethod('CommandeController', 'create');
check('L\'action du contrôleur est très courte (3 instructions max)', ($m->getEndLine() - $m->getStartLine() - 1) <= 5, ($m->getEndLine() - $m->getStartLine() - 1) . ' lignes');
check('Le service ne connaît pas HTTP (pas de JsonResponse en retour)', (string) (new ReflectionMethod('CommandeService', 'passer'))->getReturnType() !== JsonResponse::class);
""")),
  tds=[
    TD(2, "Ajouter une fonctionnalité dans une architecture propre",
       "Le code est déjà bien découpé. Tu ajoutes l'**annulation** d'une commande en mettant chaque morceau à sa place : la règle dans l'entité, l'orchestration dans le service, le HTTP dans le contrôleur. " + SIM,
       ["Règle (dans une méthode de `Commande`) : une commande **expédiée** ne peut pas être annulée → `CommandeExpediee` (409) ; annuler remet la quantité en stock",
        "Comme `Commande` est fournie, écris la règle dans une sous-classe ou une classe dédiée `Annulation::appliquer(Commande $c)` qui contient **toute** la règle",
        "`CommandeService::annuler(int $id): Commande` : 404 si introuvable (`CommandeIntrouvable`)",
        "`POST /api/commandes/{id}/annulation` → 200 `{ id, statut: 'annulee' }`",
        "L'action du contrôleur fait 1 ligne"],
       [BOUTIQUE, F("Annulation.php", "php", r"""
<?php
// Pour l'exercice : une commande annulée garde son objet, on suit le statut à côté.
final class StatutCommandes
{
    public array $annulees = [];
}

// à toi : CommandeExpediee (409), CommandeIntrouvable (404), Annulation, CommandeService, AnnulationController

// Données de test
$repo = App::get(CommandeRepository::class);
$p = App::get(ProduitRepository::class)->find(1);
$repo->save(new Commande(1, $p, 3, 'ana'));
App::request('POST', '/api/commandes/1/annulation');
""")],
       ["`Annulation` reçoit `StatutCommandes` et `ProduitRepository` par injection.",
        "Remettre en stock : `$p->setStock($p->getStock() + $c->getQuantite())`.",
        "Le contrôleur : `return $this->json(['id' => $c->getId(), 'statut' => 'annulee']);` après `$service->annuler($id)`."],
       [F("Annulation.php", "php", r"""
<?php
final class StatutCommandes
{
    public array $annulees = [];
}

#[WithHttpStatus(409)] final class CommandeExpediee extends \DomainException {}
#[WithHttpStatus(404)] final class CommandeIntrouvable extends \DomainException {}

final class Annulation
{
    public function __construct(private StatutCommandes $statuts) {}

    public function appliquer(Commande $c): void
    {
        if ($c->getStatut() === 'expediee') throw new CommandeExpediee('Commande déjà expédiée');
        if (isset($this->statuts->annulees[$c->getId()])) return;   // déjà annulée : rien à refaire
        $p = $c->getProduit();
        $p->setStock($p->getStock() + $c->getQuantite());
        $this->statuts->annulees[$c->getId()] = true;
    }
}

final class CommandeService
{
    public function __construct(private CommandeRepository $commandes, private Annulation $annulation) {}

    public function annuler(int $id): Commande
    {
        $c = $this->commandes->find($id) ?? throw new CommandeIntrouvable('Commande introuvable');
        $this->annulation->appliquer($c);
        return $c;
    }
}

final class AnnulationController extends AbstractController
{
    #[Route('/api/commandes/{id}/annulation', methods: ['POST'])]
    public function annuler(int $id, CommandeService $service): JsonResponse
    {
        return $this->json(['id' => $service->annuler($id)->getId(), 'statut' => 'annulee']);
    }
}

$repo = App::get(CommandeRepository::class);
$p = App::get(ProduitRepository::class)->find(1);
$repo->save(new Commande(1, $p, 3, 'ana'));
App::request('POST', '/api/commandes/1/annulation');
""")],
       ["Annuler remet 3 claviers en stock",
        "Une commande expédiée renvoie 409"],
       run=SRUN(r"""
$repo = App::get(CommandeRepository::class); $p = App::get(ProduitRepository::class)->find(1);
$repo->save(new Commande(1, $p, 3, 'ana'));
$c2 = new Commande(2, $p, 1, 'leo'); $c2->expedier(); $repo->save($c2);
$r = App::request('POST', '/api/commandes/1/annulation');
check('Annulation → 200 { id: 1, statut: annulee }', $r->status === 200 && $r->json === ['id' => 1, 'statut' => 'annulee'], (string) $r);
check('Stock remis : 10 + 3 = 13', $p->getStock() === 13, (string) $p->getStock());
App::request('POST', '/api/commandes/1/annulation');
check('Annuler deux fois ne remet pas deux fois en stock', $p->getStock() === 13);
check('Commande expédiée → 409', App::request('POST', '/api/commandes/2/annulation')->status === 409);
check('Commande 99 → 404', App::request('POST', '/api/commandes/99/annulation')->status === 404);
$m = new ReflectionMethod('AnnulationController', 'annuler');
check('Action du contrôleur : une seule instruction', ($m->getEndLine() - $m->getStartLine() - 1) <= 3);
check('La règle est hors du contrôleur et du service (classe Annulation)', method_exists('Annulation', 'appliquer'));
""")),
    TD(3, "Le même cas d'usage, deux points d'entrée",
       "La preuve qu'un service est bien découpé : on peut l'appeler **sans HTTP**. Tu écris un service de relance des commandes non expédiées, appelé à la fois par une **route d'API** et par une **commande console** (comme `bin/console app:relancer`). " + SIM,
       ["`RelanceService::relancer(int $joursMax): array` renvoie les ids des commandes `payee` (non expédiées) et enregistre un message par client dans `Messagerie` (fournie)",
        "Pour simplifier, toutes les commandes du repository sont considérées « anciennes » : `$joursMax` est juste transmis (et affiché dans le message)",
        "`POST /api/relances?jours=3` → 200 `{ relancees: [ids] }` ; `jours` vient d'un DTO `#[MapQueryString]` (défaut 7, entre 1 et 30)",
        "`RelancerCommand::execute(array $args): int` (ex. `['--jours=3']`) appelle **le même** service et renvoie `0`",
        "Le service n'utilise aucune classe de `Symfony\\Component\\HttpFoundation` ni de console"],
       [BOUTIQUE, F("messagerie.php", "php", r"""
<?php
// ---- Fourni ----
final class Messagerie
{
    public array $envoyes = [];
    public function envoyer(string $client, string $texte): void { $this->envoyes[] = [$client, $texte]; }
}
"""), F("Relance.php", "php", r"""
<?php
// à toi : RelanceService, RelanceFiltre (DTO), RelanceController, RelancerCommand

$repo = App::get(CommandeRepository::class); $p = App::get(ProduitRepository::class)->find(1);
$repo->save(new Commande(1, $p, 1, 'ana'));
$exp = new Commande(2, $p, 1, 'leo'); $exp->expedier(); $repo->save($exp);
App::request('POST', '/api/relances?jours=3');
echo (App::get(RelancerCommand::class))->execute(['--jours=5']), "\n";
""")],
       ["La commande console reçoit ses dépendances comme un contrôleur : `public function __construct(private RelanceService $relance) {}`.",
        "Lire l'option : `preg_match('/^--jours=(\\d+)$/', $arg, $m)`.",
        "Route : `relancer(#[MapQueryString] ?RelanceFiltre $f, RelanceService $s)` puis `$f ??= new RelanceFiltre();`."],
       [F("Relance.php", "php", r"""
<?php
final class RelanceService
{
    public function __construct(private CommandeRepository $commandes, private Messagerie $messagerie) {}

    /** @return int[] */
    public function relancer(int $joursMax): array
    {
        $ids = [];
        foreach ($this->commandes->commandes as $c) {
            if ($c->getStatut() !== 'payee') continue;
            $this->messagerie->envoyer($c->getClient(), "Ta commande {$c->getId()} attend depuis plus de $joursMax jours.");
            $ids[] = $c->getId();
        }
        return $ids;
    }
}

final class RelanceFiltre
{
    public function __construct(#[Assert\Range(min: 1, max: 30)] public readonly int $jours = 7) {}
}

final class RelanceController extends AbstractController
{
    #[Route('/api/relances', methods: ['POST'])]
    public function relancer(#[MapQueryString] ?RelanceFiltre $f, RelanceService $service): JsonResponse
    {
        $f ??= new RelanceFiltre();
        return $this->json(['relancees' => $service->relancer($f->jours)]);
    }
}

final class RelancerCommand
{
    public function __construct(private RelanceService $relance) {}

    public function execute(array $args): int
    {
        $jours = 7;
        foreach ($args as $a) if (preg_match('/^--jours=(\d+)$/', $a, $m)) $jours = (int) $m[1];
        $ids = $this->relance->relancer($jours);
        echo count($ids), " commande(s) relancée(s)\n";
        return 0;
    }
}

$repo = App::get(CommandeRepository::class); $p = App::get(ProduitRepository::class)->find(1);
$repo->save(new Commande(1, $p, 1, 'ana'));
$exp = new Commande(2, $p, 1, 'leo'); $exp->expedier(); $repo->save($exp);
App::request('POST', '/api/relances?jours=3');
echo (App::get(RelancerCommand::class))->execute(['--jours=5']), "\n";
""")],
       ["La route et la commande utilisent le même service",
        "Le service n'a aucune dépendance HTTP"],
       run=SRUN(r"""
$repo = App::get(CommandeRepository::class); $p = App::get(ProduitRepository::class)->find(1);
$repo->save(new Commande(1, $p, 1, 'ana')); $repo->save(new Commande(3, $p, 2, 'zoe'));
$exp = new Commande(2, $p, 1, 'leo'); $exp->expedier(); $repo->save($exp);
$r = App::request('POST', '/api/relances?jours=3');
check('POST /api/relances?jours=3 → 200 { relancees: [1, 3] }', $r->status === 200 && ($r->json['relancees'] ?? null) === [1, 3], (string) $r);
$msg = App::get(Messagerie::class);
check('2 messages envoyés, mentionnant 3 jours', count($msg->envoyes) === 2 && str_contains($msg->envoyes[0][1], '3'));
check('jours=90 → 422', App::request('POST', '/api/relances?jours=90')->status === 422);
ob_start(); $code = App::get(RelancerCommand::class)->execute(['--jours=5']); ob_end_clean();
check('La commande console renvoie 0', $code === 0);
check('La console a utilisé le même service (2 nouveaux messages, 5 jours)', count($msg->envoyes) === 4 && str_contains($msg->envoyes[3][1], '5'));
$deps = array_map(fn($p) => (string) $p->getType(), (new ReflectionMethod('RelanceService', '__construct'))->getParameters());
check('RelanceService ne dépend d\'aucune classe HTTP', !array_filter($deps, fn($t) => str_contains($t, 'HttpFoundation') || str_contains($t, 'Request')));
$cdeps = array_map(fn($p) => (string) $p->getType(), (new ReflectionMethod('RelancerCommand', '__construct'))->getParameters());
check('RelancerCommand dépend de RelanceService', in_array('RelanceService', $cdeps, true));
""")),
  ])

# ---------------------------------------------------------------- Liens
liens = V2(v1["arch-liens"],
  prereq=[
    P("Injection de dépendances", "Une classe reçoit ce dont elle a besoin dans son constructeur au lieu de le créer avec `new` (parcours PHP, dernier module)."),
    P("Conteneur de services", "L'objet de Symfony qui crée tous les services, une seule fois chacun, et les donne à ceux qui en ont besoin."),
    P("Autowiring", "Le conteneur lit les **types** des paramètres du constructeur (`LivreRepository $livres`) et devine tout seul quel service fournir."),
    P("Interface", "Un contrat (des signatures de méthodes) que plusieurs classes peuvent implémenter. Dépendre d'une interface permet de changer d'implémentation sans toucher au code qui l'utilise."),
    P("Dépendance circulaire", "A a besoin de B, qui a besoin de A : impossible à construire. C'est toujours le signe que les rôles sont mal découpés."),
  ],
  diagram=D(
    nodes=[
      N("cont", 0, 1, "Conteneur", "lit les constructeurs", kind="db", color="accent"),
      N("ctrl", 1, 0, "EmpruntController", "__construct(EmpruntService)", kind="file"),
      N("svc", 2, 0, "EmpruntService", "__construct(LivreRepository,\nEntityManager)", kind="file"),
      N("repo", 3, 0, "LivreRepository", "__construct(ManagerRegistry)", kind="file"),
      N("note", 2, 1, "créés une seule fois,\nreliés automatiquement", kind="note", color="muted"),
    ],
    edges=[E("cont", "ctrl", "new …"), E("ctrl", "svc", "dépend de"), E("svc", "repo", "dépend de")],
    caption="Chaque classe déclare ses besoins dans son constructeur ; le conteneur construit la chaîne de bas en haut. Les flèches de dépendance ne remontent jamais."),
  lessons=[
    L("Qui crée les objets ?", r"""
On voit partout des constructeurs comme `public function __construct(private EmpruntService $emprunts) {}`, mais on n'écrit jamais `new EmpruntService(...)`. Qui le fait ?

C'est le **conteneur de services** de Symfony. Au démarrage, il connaît toutes tes classes de `src/` (sauf les entités, les DTO…). Quand il doit créer un contrôleur, il lit son constructeur, voit qu'il faut un `EmpruntService`, crée d'abord celui-ci (en lisant à son tour son constructeur), et ainsi de suite jusqu'en bas. C'est l'**autowiring** : le câblage automatique d'après les types.

En gros, il fait pour toi :

```php
$registry   = /* fourni par Doctrine */;
$em         = /* fourni par Doctrine */;
$livres     = new LivreRepository($registry);
$service    = new EmpruntService($livres, $em);
$controller = new EmpruntController($service);
```

Chaque service est créé **une seule fois** et partagé : tous ceux qui demandent `LivreRepository` reçoivent le même objet.
"""),
    L("Services et non-services", r"""
Le conteneur gère les **services** : les objets qui **font** quelque chose et n'ont pas d'état propre à une requête (contrôleurs, services, repositories, mailer, clients HTTP).

Il ne gère pas les objets qui **portent des données** :

- les **entités** : créées par toi (`new Livre(...)`) ou chargées par Doctrine ;
- les **DTO** : remplis par Symfony (`#[MapRequestPayload]`) ou créés par toi (`LivreOutput::fromEntity()`) ;
- les **value objects** (`Email`, `Money`) : `new` partout où il faut.

Règle : un service ne fait jamais `new` d'un autre service (il le reçoit), mais peut faire `new` d'une entité ou d'un DTO.

Commandes utiles :

```bash
php bin/console debug:autowiring Livre      # ce que tu peux injecter qui contient "Livre"
php bin/console debug:container EmpruntService
```
"""),
    L("Le sens des dépendances", r"""
Les dépendances suivent toujours le même sens : de la couche **HTTP** vers les **données**.

```
Contrôleur  →  Service  →  Repository / EntityManager
                     ↘  Entité (via ses méthodes)
```

- Un contrôleur peut dépendre d'un service. L'inverse, jamais.
- Un service peut dépendre de repositories et d'autres services « plus bas ». Un repository ne dépend jamais d'un service.
- Une entité ne dépend d'aucun service (pas d'EntityManager, pas de mailer dedans).

Quand on respecte ce sens, chaque couche peut être testée en remplaçant celles du dessous par des fausses versions, et aucune boucle n'est possible.

Une **dépendance circulaire** (A a besoin de B qui a besoin de A) est refusée par le conteneur. Elle signale presque toujours qu'une des deux classes fait deux choses : la solution est d'extraire la partie commune dans une **troisième** classe dont A et B dépendent.
"""),
    L("Dépendre d'une interface", r"""
Quand un service a besoin d'une capacité qui peut changer (envoyer une notification par email aujourd'hui, par SMS demain), il dépend d'une **interface** plutôt que d'une classe :

```php
interface Notifier
{
    public function notifier(string $destinataire, string $message): void;
}

final class EmpruntService
{
    public function __construct(private Notifier $notifier) {}
}
```

Si une seule classe implémente `Notifier` dans `src/`, l'autowiring la trouve tout seul. S'il y en a plusieurs, on choisit dans `config/services.yaml` :

```yaml
services:
    App\Notification\Notifier: '@App\Notification\EmailNotifier'
```

Bonus : en test, on injecte une fausse implémentation qui enregistre les messages au lieu de les envoyer.
"""),
  ],
  recap=[
    "Chaque classe déclare ses besoins dans son **constructeur** ; le conteneur crée et relie tout (autowiring).",
    "Chaque service est créé une seule fois et partagé.",
    "Entités, DTO, value objects ne sont pas des services : `new` est permis pour eux.",
    "Sens unique : Contrôleur → Service → Repository. Jamais l'inverse.",
    "Dépendance circulaire = rôles mal découpés : extraire une 3e classe.",
    "Dépendre d'une **interface** pour pouvoir changer d'implémentation (ou la remplacer en test).",
  ],
  example=[F("src/Controller/EmpruntController.php", "php", r"""
<?php

namespace App\Controller;

use App\Service\EmpruntService;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;

final class EmpruntController extends AbstractController
{
    public function __construct(private EmpruntService $emprunts) {}   // injecté par Symfony
}
"""), F("src/Service/EmpruntService.php", "php", r"""
<?php

namespace App\Service;

use App\Notification\Notifier;
use App\Repository\LivreRepository;
use Doctrine\ORM\EntityManagerInterface;

final class EmpruntService
{
    public function __construct(
        private LivreRepository $livres,          // pour LIRE
        private EntityManagerInterface $em,       // pour ÉCRIRE (persist/flush)
        private Notifier $notifier,               // une interface : l'implémentation peut changer
    ) {}
}
"""), F("src/Repository/LivreRepository.php", "php", r"""
<?php

namespace App\Repository;

use App\Entity\Livre;
use Doctrine\Bundle\DoctrineBundle\Repository\ServiceEntityRepository;
use Doctrine\Persistence\ManagerRegistry;

final class LivreRepository extends ServiceEntityRepository
{
    public function __construct(ManagerRegistry $registry)
    {
        parent::__construct($registry, Livre::class);
    }
}
"""), F("config/services.yaml", "yaml", r"""
services:
    _defaults:
        autowire: true        # injecter d'après les types
        autoconfigure: true

    App\:
        resource: '../src/'
        exclude:
            - '../src/Entity/'
            - '../src/Dto/'

    # plusieurs implémentations de Notifier ? on choisit ici
    App\Notification\Notifier: '@App\Notification\EmailNotifier'
""")],
  notes=["Lis du contrôleur vers le repository : chaque constructeur ne demande que l'étage du dessous.",
         "`EmpruntService` dépend de `Notifier` (une interface), pas d'une classe précise.",
         "`services.yaml` : tout `src/` est enregistré, sauf les entités et les DTO (ce ne sont pas des services).",
         "Personne n'écrit les `new` : le conteneur les fait dans le bon ordre."],
  td1=dict(path="Retour.php",
    title="Câbler « rendre un livre »",
    enonce="Écris les trois classes de la fonctionnalité « rendre un livre », chacune ne demandant dans son constructeur que l'étage du dessous. Le conteneur doit pouvoir tout construire seul. " + SIM,
    consignes=["`EmpruntRepository` (en mémoire, emprunts 1 → membre 7, 2 → membre 8) avec `findEnCoursPourMembre(int $id, Membre $m): ?Emprunt`",
               "`RetourService` dépend du repository ; `rendre(int $id, Membre $m)` lève `EmpruntIntrouvable` (404) si l'emprunt n'est pas en cours pour ce membre, sinon appelle `cloturer()`",
               "`RetourController` dépend du service ; `POST /api/emprunts/{id}/retour` → 200 `{ id, rendu: true }`",
               "Aucun `new` d'un service dans ton code",
               "Aucune dépendance qui « remonte » (repository → service, service → contrôleur)"],
    hints=["Le membre connecté arrive par `#[CurrentUser] Membre $membre`.",
           "`findEnCoursPourMembre` renvoie `null` si l'emprunt n'existe pas, appartient à un autre membre, ou est déjà rendu.",
           "`?? throw new EmpruntIntrouvable('Emprunt introuvable')` dans le service."],
    checks=["Le conteneur construit `RetourController` tout seul", "Rendre l'emprunt d'un autre membre donne 404"],
    files=[F("donnees.php", "php", USES + r"""
// ---- Fourni ----
#[WithHttpStatus(404)] final class EmpruntIntrouvable extends \DomainException {}

final class Emprunt
{
    private bool $rendu = false;
    public function __construct(public readonly int $id, public readonly int $membreId, public readonly string $livre) {}
    public function estRendu(): bool { return $this->rendu; }
    public function cloturer(): void { $this->rendu = true; }
}

final class Membre
{
    public function __construct(public readonly int $id, public readonly string $pseudo) {}
}
"""), F("Retour.php", "php", r"""
<?php
// à toi : EmpruntRepository (en mémoire, avec findEnCoursPourMembre), RetourService, RetourController
// POST /api/emprunts/{id}/retour : 200 { id, rendu: true } ; 404 si l'emprunt n'est pas en cours pour ce membre

App::$user = new Membre(7, 'ana');
App::request('POST', '/api/emprunts/1/retour');
""")],
    solution=[F("Retour.php", "php", r"""
<?php
final class EmpruntRepository
{
    /** @var array<int, Emprunt> */
    private array $emprunts;

    public function __construct()
    {
        $this->emprunts = [1 => new Emprunt(1, 7, 'Dune'), 2 => new Emprunt(2, 8, 'Fondation')];
    }

    public function findEnCoursPourMembre(int $id, Membre $membre): ?Emprunt
    {
        $e = $this->emprunts[$id] ?? null;
        return $e && $e->membreId === $membre->id && !$e->estRendu() ? $e : null;
    }
}

final class RetourService
{
    public function __construct(private EmpruntRepository $emprunts) {}

    public function rendre(int $empruntId, Membre $membre): Emprunt
    {
        $e = $this->emprunts->findEnCoursPourMembre($empruntId, $membre) ?? throw new EmpruntIntrouvable('Emprunt introuvable');
        $e->cloturer();
        return $e;
    }
}

final class RetourController extends AbstractController
{
    public function __construct(private RetourService $retours) {}

    #[Route('/api/emprunts/{id}/retour', methods: ['POST'])]
    public function rendre(int $id, #[CurrentUser] Membre $membre): JsonResponse
    {
        $e = $this->retours->rendre($id, $membre);
        return $this->json(['id' => $e->id, 'rendu' => $e->estRendu()]);
    }
}

App::$user = new Membre(7, 'ana');
App::request('POST', '/api/emprunts/1/retour');
""")],
    run=SRUN(r"""
App::$user = new Membre(7, 'ana');
$r = App::request('POST', '/api/emprunts/1/retour');
check('Rendre son emprunt → 200 { id: 1, rendu: true }', $r->status === 200 && $r->json === ['id' => 1, 'rendu' => true], (string) $r);
check('Le rendre une 2e fois → 404 (plus en cours)', App::request('POST', '/api/emprunts/1/retour')->status === 404);
check('Rendre l\'emprunt d\'un autre membre → 404', App::request('POST', '/api/emprunts/2/retour')->status === 404);
$t = fn(string $c) => array_map(fn($p) => (string) $p->getType(), (new ReflectionClass($c))->getConstructor()?->getParameters() ?? []);
check('RetourController dépend de RetourService', $t('RetourController') === ['RetourService']);
check('RetourService dépend de EmpruntRepository', in_array('EmpruntRepository', $t('RetourService'), true));
check('EmpruntRepository ne dépend d\'aucun service', !array_filter($t('EmpruntRepository'), fn($x) => str_contains($x, 'Service') || str_contains($x, 'Controller')));
check('Le conteneur construit toute la chaîne', App::get('RetourController') instanceof RetourController);
""")),
  tds=[
    TD(2, "Dépendre d'une interface",
       "Quand un livre réservé est rendu, le membre suivant doit être prévenu. Aujourd'hui par email, demain peut-être par SMS. Le service doit dépendre d'une **interface**, et les tests remplacent l'implémentation par une fausse, sans toucher au service. " + SIM,
       ["Interface `Notifier` avec `notifier(string $destinataire, string $message): void`",
        "`EmailNotifier implements Notifier` (affiche `EMAIL à … : …` avec `echo`)",
        "`ReservationService` (constructeur : `Notifier` uniquement) : `livreRendu(string $titre, array $fileAttente): ?string` prévient le **premier** de la file (message contenant le titre) et renvoie son pseudo, ou `null` si la file est vide",
        "Route `POST /api/livres/{titre}/rendu` → 200 `{ prevenu: ... }` avec une file fournie par `FileAttente` (fournie)",
        "Enregistre l'implémentation par défaut avec `App::set(Notifier::class, new EmailNotifier())`"],
       [F("file.php", "php", USES + r"""
// ---- Fourni ----
final class FileAttente
{
    public array $files = ['Dune' => ['leo', 'zoe'], 'Fondation' => []];
    public function pour(string $titre): array { return $this->files[$titre] ?? []; }
}
"""), F("Notification.php", "php", r"""
<?php
// à toi : Notifier, EmailNotifier, ReservationService, RenduController

App::set(Notifier::class, new EmailNotifier());
App::request('POST', '/api/livres/Dune/rendu');
""")],
       ["Le type du paramètre du constructeur est `Notifier`, pas `EmailNotifier`.",
        "`$premier = $fileAttente[0] ?? null;`",
        "Dans le contrôleur : `livreRendu($titre, $file->pour($titre))`."],
       [F("Notification.php", "php", r"""
<?php
interface Notifier
{
    public function notifier(string $destinataire, string $message): void;
}

final class EmailNotifier implements Notifier
{
    public function notifier(string $destinataire, string $message): void
    {
        echo "EMAIL à $destinataire : $message\n";
    }
}

final class ReservationService
{
    public function __construct(private Notifier $notifier) {}

    public function livreRendu(string $titre, array $fileAttente): ?string
    {
        $premier = $fileAttente[0] ?? null;
        if ($premier !== null) {
            $this->notifier->notifier($premier, "« $titre » est disponible pour toi.");
        }
        return $premier;
    }
}

final class RenduController extends AbstractController
{
    #[Route('/api/livres/{titre}/rendu', methods: ['POST'])]
    public function rendu(string $titre, ReservationService $service, FileAttente $file): JsonResponse
    {
        return $this->json(['prevenu' => $service->livreRendu($titre, $file->pour($titre))]);
    }
}

App::set(Notifier::class, new EmailNotifier());
App::request('POST', '/api/livres/Dune/rendu');
""")],
       ["En test, un faux `Notifier` reçoit le message",
        "File vide : personne n'est prévenu"],
       run=SRUN(r"""
$faux = new class implements Notifier { public array $msgs = []; public function notifier(string $d, string $m): void { $this->msgs[] = [$d, $m]; } };
App::set(Notifier::class, $faux);
$r = App::request('POST', '/api/livres/Dune/rendu');
check('Dune rendu → { prevenu: leo }', $r->status === 200 && ($r->json['prevenu'] ?? null) === 'leo', (string) $r);
check('Le faux notifier a reçu un message pour leo mentionnant Dune', count($faux->msgs) === 1 && $faux->msgs[0][0] === 'leo' && str_contains($faux->msgs[0][1], 'Dune'));
$r2 = App::request('POST', '/api/livres/Fondation/rendu');
check('File vide → prevenu: null, aucun message', array_key_exists('prevenu', $r2->json ?? []) && $r2->json['prevenu'] === null && count($faux->msgs) === 1);
$types = array_map(fn($p) => (string) $p->getType(), (new ReflectionMethod('ReservationService', '__construct'))->getParameters());
check('ReservationService dépend de l\'interface Notifier', $types === ['Notifier']);
check('EmailNotifier implémente Notifier', in_array('Notifier', class_implements('EmailNotifier'), true));
""")),
    TD(3, "Casser une dépendance circulaire",
       "Ce code ne démarre pas : `FactureService` a besoin de `CommandeService`, qui a besoin de `FactureService`. Le conteneur refuse (« Dépendance circulaire »). Tu dois trouver la responsabilité partagée, l'extraire dans une **troisième** classe, et faire en sorte que les deux services en dépendent. " + SIM,
       ["Lance le code tel quel et lis l'erreur",
        "Le calcul du montant TTC est utilisé par les deux : extrais-le dans `CalculPrix::ttc(int $ht): int` (TVA 20 %, arrondi à l'entier)",
        "`CommandeService` ne dépend plus de `FactureService`, et inversement ; tous deux dépendent de `CalculPrix`",
        "Le comportement des routes `GET /api/commandes/{ht}/ttc` et `GET /api/factures/{ht}` ne change pas",
        "`App::get(FactureController::class)` doit fonctionner"],
       [F("Circulaire.php", "php", USES + r"""
final class CommandeService
{
    public function __construct(private FactureService $factures) {}

    public function ttc(int $ht): int { return (int) round($ht * 1.2); }

    public function totalCommande(int $ht): int { return $this->ttc($ht); }
}

final class FactureService
{
    public function __construct(private CommandeService $commandes) {}

    public function facturer(int $ht): array
    {
        return ['ht' => $ht, 'ttc' => $this->commandes->ttc($ht)];
    }
}

final class CommandeController extends AbstractController
{
    #[Route('/api/commandes/{ht}/ttc', methods: ['GET'])]
    public function ttc(int $ht, CommandeService $s): JsonResponse { return $this->json(['ttc' => $s->totalCommande($ht)]); }
}

final class FactureController extends AbstractController
{
    #[Route('/api/factures/{ht}', methods: ['GET'])]
    public function show(int $ht, FactureService $s): JsonResponse { return $this->json($s->facturer($ht)); }
}

App::request('GET', '/api/factures/1000');
""")],
       ["`CommandeService` ne se sert de `FactureService` nulle part : la dépendance était inutile en plus d'être circulaire.",
        "`final class CalculPrix { public function ttc(int $ht): int { return (int) round($ht * 1.2); } }`",
        "Chaque service reçoit `private CalculPrix $prix` dans son constructeur."],
       [F("Circulaire.php", "php", USES + r"""
final class CalculPrix
{
    public function ttc(int $ht): int { return (int) round($ht * 1.2); }
}

final class CommandeService
{
    public function __construct(private CalculPrix $prix) {}

    public function totalCommande(int $ht): int { return $this->prix->ttc($ht); }
}

final class FactureService
{
    public function __construct(private CalculPrix $prix) {}

    public function facturer(int $ht): array
    {
        return ['ht' => $ht, 'ttc' => $this->prix->ttc($ht)];
    }
}

final class CommandeController extends AbstractController
{
    #[Route('/api/commandes/{ht}/ttc', methods: ['GET'])]
    public function ttc(int $ht, CommandeService $s): JsonResponse { return $this->json(['ttc' => $s->totalCommande($ht)]); }
}

final class FactureController extends AbstractController
{
    #[Route('/api/factures/{ht}', methods: ['GET'])]
    public function show(int $ht, FactureService $s): JsonResponse { return $this->json($s->facturer($ht)); }
}

App::request('GET', '/api/factures/1000');
""")],
       ["Plus d'erreur « Dépendance circulaire »",
        "Les deux services dépendent de `CalculPrix`"],
       run=SRUN(r"""
$f = App::request('GET', '/api/factures/1000');
check('GET /api/factures/1000 → { ht: 1000, ttc: 1200 }', $f->status === 200 && $f->json === ['ht' => 1000, 'ttc' => 1200], (string) $f);
$c = App::request('GET', '/api/commandes/999/ttc');
check('GET /api/commandes/999/ttc → { ttc: 1199 }', $c->status === 200 && $c->json === ['ttc' => 1199], (string) $c);
$t = fn(string $cl) => array_map(fn($p) => (string) $p->getType(), (new ReflectionClass($cl))->getConstructor()?->getParameters() ?? []);
check('CommandeService ne dépend plus de FactureService', !in_array('FactureService', $t('CommandeService'), true));
check('FactureService ne dépend plus de CommandeService', !in_array('CommandeService', $t('FactureService'), true));
check('Les deux dépendent de CalculPrix', in_array('CalculPrix', $t('CommandeService'), true) && in_array('CalculPrix', $t('FactureService'), true));
check('Le conteneur construit FactureController', App::get('FactureController') instanceof FactureController);
""")),
  ])

# ---------------------------------------------------------------- Erreurs
err = V2(v1["arch-erreurs"],
  prereq=[
    P("Exception", "Un objet « lancé » (`throw`) pour signaler qu'on ne peut pas continuer. Il remonte les appels jusqu'à un `catch`, ou jusqu'à Symfony qui le transforme en réponse."),
    P("Exception métier", "Une exception qui nomme une règle du métier : `LivreIndisponible`, `QuotaEmpruntsAtteint`. Elle ne parle pas de HTTP."),
    P("`#[WithHttpStatus]`", "Attribut posé sur une classe d'exception (Symfony 6.3+) : quand elle remonte jusqu'à Symfony, la réponse a ce statut."),
    P("Listener", "Une classe que Symfony appelle quand un événement se produit. L'événement `kernel.exception` survient quand une exception n'a pas été attrapée."),
    P("Codes 4xx", "400 requête mal formée, 401 non connecté, 403 interdit, 404 introuvable, 409 conflit avec l'état actuel, 422 données invalides."),
  ],
  diagram=D(
    nodes=[
      N("dto", 0, 0, "DTO", "forme invalide", kind="file", color="muted"),
      N("svc", 0, 1, "Service", "introuvable", color="muted"),
      N("ent", 0, 2, "Entité", "règle violée", kind="pill", color="muted"),
      N("e1", 1, 0, "Validation", "violations", kind="doc", color="warn"),
      N("e2", 1, 1, "LivreIntrouvable", "#[WithHttpStatus(404)]", kind="doc", color="warn"),
      N("e3", 1, 2, "LivreIndisponible", "#[WithHttpStatus(409)]", kind="doc", color="warn"),
      N("k", 2, 1, "Symfony", "(+ listener éventuel)", color="accent"),
      N("r", 3, 1, "Réponse JSON", "422 · 404 · 409", kind="file", color="good"),
    ],
    edges=[E("dto", "e1"), E("svc", "e2"), E("ent", "e3"), E("e1", "k"), E("e2", "k"), E("e3", "k"), E("k", "r", color="good")],
    caption="Chaque couche détecte ses propres erreurs et lève une exception qui ne parle pas de HTTP. La traduction en statut se fait à un seul endroit."),
  lessons=[
    L("Le problème : chaque couche signale ses erreurs à sa façon", r"""
Sans convention, on trouve de tout : une méthode qui renvoie `false`, une autre `null`, une autre une chaîne d'erreur, un service qui renvoie directement une `JsonResponse` 409… Le contrôleur se remplit de `if` pour traduire chaque cas, et le front reçoit des réponses de formes différentes selon la route.

La convention qui marche :

1. Chaque couche **détecte** les erreurs qui la concernent.
2. Elle **lève une exception** qui porte un nom métier.
3. La traduction exception → statut HTTP se fait **à un seul endroit**.
4. Le contrôleur n'a **aucun** `try/catch`.
"""),
    L("Qui détecte quoi", r"""
- **DTO + validation** : la **forme** des données (champ vide, email invalide, nombre hors limites). Symfony répond **422** automatiquement, avant ton code.
- **Service** : ce qui manque (« livre introuvable » → **404**), ce qui dépend du système (« quota de 3 emprunts atteint » → **409**), les droits (« ce n'est pas ton emprunt » → **403**).
- **Entité** : ses propres règles (« déjà emprunté » → **409**, « contenu trop court pour publier » → **422**).

Le **repository**, lui, ne lève pas d'exception pour « rien trouvé » : `find()` renvoie `null`. C'est le service qui décide si l'absence est une erreur :

```php
$livre = $this->livres->find($id) ?? throw new LivreIntrouvable("Livre $id introuvable");
```

(`?? throw` : si la valeur de gauche est `null`, on lève l'exception.)
"""),
    L("Des exceptions métier, traduites par un attribut", r"""
Une exception par cas, avec un nom clair, qui hérite de `\DomainException` :

```php
use Symfony\Component\HttpKernel\Attribute\WithHttpStatus;

#[WithHttpStatus(409)]
final class LivreIndisponible extends \DomainException {}

#[WithHttpStatus(404)]
final class LivreIntrouvable extends \DomainException {}
```

L'entité et le service lèvent ces exceptions sans rien savoir de HTTP. Quand elles remontent jusqu'à Symfony, l'attribut indique le statut à renvoyer. Le contrôleur reste en une ligne :

```php
public function create(#[MapRequestPayload] EmpruntInput $input, EmpruntService $s): JsonResponse
{
    return $this->json(EmpruntOutput::fromEntity($s->emprunter($input)), 201);
}
```

Pourquoi ne pas lever directement une `ConflictHttpException` dans l'entité ? Parce que l'entité serait alors liée à HTTP : impossible de la réutiliser dans une commande console ou un traitement asynchrone sans « faire semblant » d'être dans une requête.
"""),
    L("Un format d'erreur stable pour le front : le listener", r"""
Pour que le front affiche le bon message, deux 409 doivent être distinguables (« déjà emprunté » ≠ « quota atteint »). Comparer les textes est fragile (ils changent, ils sont traduits). Mieux : un **code** stable dans chaque réponse d'erreur.

On centralise le format avec un **listener** sur l'événement `kernel.exception` :

```php
use Symfony\Component\EventDispatcher\Attribute\AsEventListener;
use Symfony\Component\HttpKernel\Event\ExceptionEvent;

#[AsEventListener(event: 'kernel.exception')]
final class ErreurMetierListener
{
    public function __invoke(ExceptionEvent $event): void
    {
        $e = $event->getThrowable();
        if (!$e instanceof ErreurMetier) return;            // on ne touche qu'à nos erreurs
        $event->setResponse(new JsonResponse(
            ['code' => $e->code(), 'message' => $e->getMessage()],
            $e->statut(),
        ));
    }
}
```

Côté React (parcours Données & API), on teste alors `err.response.data.code === 'QUOTA_ATTEINT'` au lieu du texte. Les autres exceptions (bugs) continuent vers la page d'erreur 500 normale ; en production, leur message n'est jamais montré.
"""),
  ],
  recap=[
    "Chaque couche détecte ses erreurs et lève une **exception métier** (pas de `return false`, pas de réponse HTTP).",
    "DTO → 422 automatique ; service → 404 / 403 / 409 ; entité → ses propres règles.",
    "Le repository renvoie `null` ; le service décide : `find($id) ?? throw new XIntrouvable()`.",
    "`#[WithHttpStatus(409)]` sur la classe d'exception : statut choisi à un seul endroit, contrôleur sans `try/catch`.",
    "Un listener `kernel.exception` donne un format stable `{ code, message }` que le front peut tester.",
  ],
  example=[F("src/Exception/LivreIndisponible.php", "php", r"""
<?php

namespace App\Exception;

use Symfony\Component\HttpKernel\Attribute\WithHttpStatus;

#[WithHttpStatus(409)]
final class LivreIndisponible extends \DomainException
{
    public function __construct(int $livreId)
    {
        parent::__construct("Le livre $livreId est déjà emprunté");
    }
}
"""), F("src/Entity/Livre.php", "php", r"""
<?php

namespace App\Entity;

use App\Exception\LivreIndisponible;

class Livre
{
    // ...

    public function emprunter(): void
    {
        if (!$this->disponible) {
            throw new LivreIndisponible($this->id);   // aucune notion de HTTP ici
        }
        $this->disponible = false;
    }
}
"""), F("src/Service/EmpruntService.php", "php", r"""
<?php

namespace App\Service;

use App\Exception\LivreIntrouvable;

final class EmpruntService
{
    // ...

    public function emprunter(EmpruntInput $in, User $membre): Emprunt
    {
        $livre = $this->livres->find($in->livreId) ?? throw new LivreIntrouvable();
        $livre->emprunter();                               // peut lever LivreIndisponible
        // ...
    }
}
"""), F("reponses.http", "plaintext", r"""
POST /api/emprunts {"livreId": 0}            -> 422 (DTO : Positive)
POST /api/emprunts {"livreId": 99}           -> 404 {"error": "Livre introuvable"}
POST /api/emprunts {"livreId": 2}            -> 409 {"error": "Le livre 2 est déjà emprunté"}
POST /api/emprunts {"livreId": 3}            -> 201 {...}
""")],
  notes=["L'exception porte un nom métier et son statut ; c'est le seul lien avec HTTP.",
         "`Livre::emprunter()` lève l'exception sans connaître HTTP.",
         "Le service transforme le `null` du repository en `LivreIntrouvable`.",
         "Dans `reponses.http`, chaque erreur vient d'une couche différente, sans aucun `try/catch` dans le contrôleur."],
  td1=dict(path="Quota.php",
    title="Quota d'emprunts",
    enonce="Un membre ne peut pas avoir plus de 3 emprunts en cours. Ajoute cette règle au bon endroit, avec une exception métier, sans aucun `try/catch` dans le contrôleur. " + SIM,
    consignes=["`QuotaEmpruntsAtteint` → 409 via `#[WithHttpStatus]`, message contenant « Quota »",
               "`EmpruntService::emprunter(EmpruntInput, Membre): Livre` vérifie le quota **avant** toute autre action",
               "Livre introuvable → `LivreIntrouvable` (404) ; déjà emprunté → `LivreIndisponible` (409, levée par l'entité)",
               "`POST /api/emprunts` → 201 `{ livreId }` ; l'action du contrôleur fait une ligne"],
    hints=["Le compteur d'emprunts en cours est dans `Bibliotheque::$empruntsEnCours[membreId]`.",
           "Vérifier le quota en premier évite de marquer un livre emprunté pour rien.",
           "`return $this->json(['livreId' => $s->emprunter($in, $m)->id], 201);`"],
    checks=["Le 4e emprunt renvoie 409", "Le livre refusé reste disponible pour un autre membre"],
    files=[F("bibliotheque.php", "php", USES + r"""
// ---- Fourni ----
#[WithHttpStatus(409)] final class LivreIndisponible extends \DomainException {}
#[WithHttpStatus(404)] final class LivreIntrouvable extends \DomainException {}

final class Membre { public function __construct(public readonly int $id) {} }

final class Livre
{
    private bool $disponible = true;
    public function __construct(public readonly int $id) {}
    public function emprunter(): void { if (!$this->disponible) throw new LivreIndisponible("Livre {$this->id} déjà emprunté"); $this->disponible = false; }
}

final class Bibliotheque
{
    public array $livres = [];
    public array $empruntsEnCours = [];   // membreId => nombre
    public function __construct() { foreach (range(1, 6) as $i) $this->livres[$i] = new Livre($i); }
}

final class EmpruntInput
{
    public function __construct(#[Assert\Positive] public readonly int $livreId = 0) {}
}
"""), F("Quota.php", "php", r"""
<?php
// à toi : QuotaEmpruntsAtteint (409), EmpruntService::emprunter() (quota de 3 vérifié AVANT tout),
// EmpruntController (POST /api/emprunts → 201 { livreId }) sans try/catch

App::$user = new Membre(1);
foreach ([1, 2, 3, 4] as $id) App::request('POST', '/api/emprunts', ['livreId' => $id]);
""")],
    solution=[F("Quota.php", "php", r"""
<?php
#[WithHttpStatus(409)]
final class QuotaEmpruntsAtteint extends \DomainException
{
    public function __construct(int $max)
    {
        parent::__construct("Quota de $max emprunts atteint");
    }
}

final class EmpruntService
{
    private const MAX = 3;

    public function __construct(private Bibliotheque $bib) {}

    public function emprunter(EmpruntInput $in, Membre $m): Livre
    {
        if (($this->bib->empruntsEnCours[$m->id] ?? 0) >= self::MAX) {
            throw new QuotaEmpruntsAtteint(self::MAX);
        }
        $livre = $this->bib->livres[$in->livreId] ?? throw new LivreIntrouvable('Livre introuvable');
        $livre->emprunter();
        $this->bib->empruntsEnCours[$m->id] = ($this->bib->empruntsEnCours[$m->id] ?? 0) + 1;
        return $livre;
    }
}

final class EmpruntController extends AbstractController
{
    #[Route('/api/emprunts', methods: ['POST'])]
    public function create(#[MapRequestPayload] EmpruntInput $in, #[CurrentUser] Membre $m, EmpruntService $s): JsonResponse
    {
        return $this->json(['livreId' => $s->emprunter($in, $m)->id], 201);
    }
}

App::$user = new Membre(1);
foreach ([1, 2, 3, 4] as $id) App::request('POST', '/api/emprunts', ['livreId' => $id]);
""")],
    run=SRUN(r"""
App::$user = new Membre(1);
$st = [];
foreach ([1, 2, 3] as $id) $st[] = App::request('POST', '/api/emprunts', ['livreId' => $id])->status;
check('3 premiers emprunts → 201', $st === [201, 201, 201], json_encode($st));
$q = App::request('POST', '/api/emprunts', ['livreId' => 4]);
check('4e emprunt → 409 avec « Quota »', $q->status === 409 && str_contains($q->json['error'] ?? '', 'Quota'), (string) $q);
check('Le livre 4 n\'a pas été marqué emprunté (quota vérifié avant)', App::request('POST', '/api/emprunts', ['livreId' => 4])->status === 409 && (function () { App::$user = new Membre(2); return App::request('POST', '/api/emprunts', ['livreId' => 4])->status === 201; })());
App::$user = new Membre(3);
check('Livre déjà emprunté → 409', App::request('POST', '/api/emprunts', ['livreId' => 1])->status === 409);
check('Livre 99 → 404', App::request('POST', '/api/emprunts', ['livreId' => 99])->status === 404);
$m = new ReflectionMethod('EmpruntController', 'create');
check('Contrôleur en une instruction (pas de try/catch)', ($m->getEndLine() - $m->getStartLine() - 1) <= 3);
""")),
  tds=[
    TD(2, "Un format d'erreur `{ code, message }` avec un listener",
       "Le front doit distinguer « déjà emprunté » de « quota atteint » sans lire le texte. Tu crées une classe de base pour toutes les erreurs métier, chacune avec un **code** stable, et un **listener** qui formate leurs réponses. Les erreurs qui ne sont pas métier (bugs) ne doivent pas être touchées. " + SIM,
       ["Classe abstraite `ErreurMetier extends \\DomainException` avec `abstract public function code(): string` et `abstract public function statut(): int`",
        "`LivreIndisponible` (`LIVRE_INDISPONIBLE`, 409) et `QuotaAtteint` (`QUOTA_ATTEINT`, 409) en héritent",
        "Listener `#[AsEventListener(event: 'kernel.exception')]` : pour une `ErreurMetier`, répond `{ code, message }` avec son statut ; sinon ne fait rien",
        "Route fournie `POST /api/test/{cas}` qui lève l'une ou l'autre selon `cas` (`indispo`, `quota`, `bug`)",
        "Le cas `bug` (une `\\RuntimeException`) donne toujours une 500"],
       [F("Erreurs.php", "php", USES + r"""
use Symfony\Component\EventDispatcher\Attribute\AsEventListener;
use Symfony\Component\HttpKernel\Event\ExceptionEvent;

// à toi : ErreurMetier, LivreIndisponible, QuotaAtteint, ErreurMetierListener

// ---- Fourni : une route qui lève les erreurs ----
final class TestController extends AbstractController
{
    #[Route('/api/test/{cas}', methods: ['POST'])]
    public function test(string $cas): JsonResponse
    {
        throw match ($cas) {
            'indispo' => new LivreIndisponible('Le livre 2 est déjà emprunté'),
            'quota' => new QuotaAtteint('3 emprunts maximum'),
            default => new \RuntimeException('Bug inattendu'),
        };
    }
}

App::request('POST', '/api/test/indispo');
App::request('POST', '/api/test/quota');
App::request('POST', '/api/test/bug');
""")],
       ["`final class QuotaAtteint extends ErreurMetier { public function code(): string { return 'QUOTA_ATTEINT'; } public function statut(): int { return 409; } }`",
        "Dans le listener : `if (!$e instanceof ErreurMetier) return;`",
        "`$event->setResponse(new JsonResponse(['code' => $e->code(), 'message' => $e->getMessage()], $e->statut()));`"],
       [F("Erreurs.php", "php", USES + r"""
use Symfony\Component\EventDispatcher\Attribute\AsEventListener;
use Symfony\Component\HttpKernel\Event\ExceptionEvent;

abstract class ErreurMetier extends \DomainException
{
    abstract public function code(): string;
    abstract public function statut(): int;
}

final class LivreIndisponible extends ErreurMetier
{
    public function code(): string { return 'LIVRE_INDISPONIBLE'; }
    public function statut(): int { return 409; }
}

final class QuotaAtteint extends ErreurMetier
{
    public function code(): string { return 'QUOTA_ATTEINT'; }
    public function statut(): int { return 409; }
}

#[AsEventListener(event: 'kernel.exception')]
final class ErreurMetierListener
{
    public function __invoke(ExceptionEvent $event): void
    {
        $e = $event->getThrowable();
        if (!$e instanceof ErreurMetier) return;
        $event->setResponse(new JsonResponse(['code' => $e->code(), 'message' => $e->getMessage()], $e->statut()));
    }
}

final class TestController extends AbstractController
{
    #[Route('/api/test/{cas}', methods: ['POST'])]
    public function test(string $cas): JsonResponse
    {
        throw match ($cas) {
            'indispo' => new LivreIndisponible('Le livre 2 est déjà emprunté'),
            'quota' => new QuotaAtteint('3 emprunts maximum'),
            default => new \RuntimeException('Bug inattendu'),
        };
    }
}

App::request('POST', '/api/test/indispo');
App::request('POST', '/api/test/quota');
App::request('POST', '/api/test/bug');
""")],
       ["Les deux 409 ont des codes différents",
        "Le bug reste une 500"],
       run=SRUN(r"""
$a = App::request('POST', '/api/test/indispo');
check('indispo → 409 { code: LIVRE_INDISPONIBLE, message }', $a->status === 409 && ($a->json['code'] ?? '') === 'LIVRE_INDISPONIBLE' && isset($a->json['message']), (string) $a);
$b = App::request('POST', '/api/test/quota');
check('quota → 409 { code: QUOTA_ATTEINT }', $b->status === 409 && ($b->json['code'] ?? '') === 'QUOTA_ATTEINT', (string) $b);
check('Le format est exactement { code, message }', array_keys($b->json) === ['code', 'message']);
check('bug → 500 (non traité par le listener)', App::request('POST', '/api/test/bug')->status === 500);
check('ErreurMetier est abstraite', (new ReflectionClass('ErreurMetier'))->isAbstract());
""")),
    TD(3, "Afficher les erreurs côté React grâce au code",
       "Le back renvoie désormais `{ code, message }`. Côté React, tu écris une fonction qui traduit **n'importe quelle** erreur d'appel en message pour l'utilisateur, en s'appuyant sur le **code** (stable) et le **statut**, jamais sur le texte. L'API simulée répond comme ton back Symfony.",
       ["`messageErreur(err)` dans `api/erreurs.ts` : `LIVRE_INDISPONIBLE` → « Ce livre vient d'être emprunté. », `QUOTA_ATTEINT` → « Tu as déjà 3 livres. Rends-en un d'abord. »",
        "Statut 422 → le `title` de la première violation ; 401 → « Connecte-toi pour emprunter. » ; 404 → « Ce livre n'existe plus. »",
        "Toute autre erreur (500, réseau) → « Une erreur est survenue, réessaie. »",
        "`Emprunter.tsx` : un bouton par livre ; au clic, `POST /emprunts` ; affiche `messageErreur` dans `<p role=\"alert\">` ou « Emprunté ! » en cas de succès",
        "Le composant ne contient aucun texte d'erreur en dur"],
       [F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });
"""), F("api/erreurs.ts", "ts", r"""
import axios from 'axios';

export function messageErreur(err: unknown): string {
  // à toi
  return '';
}
"""), F("Emprunter.tsx", "tsx", r"""
import { useState } from 'react';
import { api } from './api/client';
import { messageErreur } from './api/erreurs';

const livres = [
  { id: 1, titre: 'Terremer' },
  { id: 2, titre: 'Dune' },
  { id: 99, titre: 'Livre supprimé' },
];

export default function Emprunter() {
  // à toi
  return null;
}
""")],
       ["`if (!axios.isAxiosError(err) || !err.response) return 'Une erreur est survenue, réessaie.';`",
        "Lis d'abord `err.response.data?.code`, puis le statut.",
        "Un seul state `message` suffit pour le composant."],
       [F("api/erreurs.ts", "ts", r"""
import axios from 'axios';

const PAR_CODE: Record<string, string> = {
  LIVRE_INDISPONIBLE: "Ce livre vient d'être emprunté.",
  QUOTA_ATTEINT: 'Tu as déjà 3 livres. Rends-en un d\'abord.',
};

export function messageErreur(err: unknown): string {
  if (!axios.isAxiosError(err) || !err.response) return 'Une erreur est survenue, réessaie.';
  const { status, data } = err.response;
  if (data?.code && PAR_CODE[data.code]) return PAR_CODE[data.code];
  if (status === 422 && data?.violations?.length) return data.violations[0].title;
  if (status === 401) return 'Connecte-toi pour emprunter.';
  if (status === 404) return "Ce livre n'existe plus.";
  return 'Une erreur est survenue, réessaie.';
}
"""), F("Emprunter.tsx", "tsx", r"""
import { useState } from 'react';
import { api } from './api/client';
import { messageErreur } from './api/erreurs';

const livres = [
  { id: 1, titre: 'Terremer' },
  { id: 2, titre: 'Dune' },
  { id: 99, titre: 'Livre supprimé' },
];

export default function Emprunter() {
  const [message, setMessage] = useState<string | null>(null);

  async function emprunter(id: number) {
    setMessage(null);
    try {
      await api.post('/emprunts', { livreId: id, rendreLe: '2030-01-01' });
      setMessage('Emprunté !');
    } catch (err) {
      setMessage(messageErreur(err));
    }
  }

  return (
    <>
      {livres.map((l) => (
        <button key={l.id} onClick={() => emprunter(l.id)}>{l.titre}</button>
      ))}
      {message && <p role="alert">{message}</p>}
    </>
  );
}
""")],
       ["Dune affiche « Ce livre vient d'être emprunté. »",
        "Le composant n'a aucun message d'erreur écrit en dur"],
       run=RUN("react", entry="Emprunter.tsx", api=LIB_API + r"""
__api["POST /api/emprunts"] = (p, b) => {
  const nb = (window.__nb = (window.__nb || 0) + 1);
  if (window.__mode === 'quota') return [409, { code: 'QUOTA_ATTEINT', message: '3 max' }];
  if (window.__mode === 'auth') return [401, { error: 'Non connecté' }];
  if (window.__mode === 'boom') return [500, { error: 'boom' }];
  if (window.__mode === '422') return [422, { violations: [{ propertyPath: 'rendreLe', title: 'Date invalide.' }] }];
  const l = db.livres.find((x) => x.id == b.livreId);
  if (!l) return [404, { error: 'introuvable' }];
  if (!l.disponible) return [409, { code: 'LIVRE_INDISPONIBLE', message: 'déjà emprunté' }];
  l.disponible = false; return [201, { id: 100 + nb }];
};
""", tests=r"""
const msg = async () => { await waitFor(() => $('[role=alert]'), 3000); return $('[role=alert]').textContent; };
await click(byText('Terremer'));
assert.equal(await msg(), 'Emprunté !', 'Succès : « Emprunté ! »');
await click(byText('Dune'));
await waitFor(() => $('[role=alert]') && $('[role=alert]').textContent.includes('vient'), 3000);
assert.includes($('[role=alert]').textContent, "vient d'être emprunté", 'LIVRE_INDISPONIBLE → message dédié');
await click(byText('Livre supprimé'));
await waitFor(() => $('[role=alert]') && $('[role=alert]').textContent.includes('existe'), 3000);
assert(true, '404 → « Ce livre n\'existe plus. »');
const { messageErreur } = require('./api/erreurs');
const ax = (status, data) => ({ isAxiosError: true, response: { status, data } });
assert.includes(messageErreur(ax(409, { code: 'QUOTA_ATTEINT', message: 'x' })), '3 livres', 'QUOTA_ATTEINT → « Tu as déjà 3 livres… »');
assert.equal(messageErreur(ax(422, { violations: [{ propertyPath: 'x', title: 'Date invalide.' }] })), 'Date invalide.', '422 → première violation');
assert.includes(messageErreur(ax(401, {})), 'Connecte-toi', '401 → « Connecte-toi… »');
assert.includes(messageErreur(ax(500, {})), 'réessaie', '500 → message générique');
assert.includes(messageErreur(new Error('réseau')), 'réessaie', 'Erreur non axios → message générique');
assert.includes(messageErreur(ax(409, { code: 'INCONNU' })), 'réessaie', 'Code inconnu → message générique');
assert(!/existe plus|vient d|Connecte-toi/.test(source('Emprunter.tsx')), 'Aucun message d\'erreur en dur dans le composant');
""")),
  ])

# ---------------------------------------------------------------- Bout en bout
bout = V2(v1["arch-bout-en-bout"],
  prereq=[
    P("Full stack", "Une fonctionnalité qui touche le front (React) **et** le back (Symfony) : un formulaire, une requête, une route, une base."),
    P("Contrat d'API", "La route, la méthode, le JSON envoyé (DTO d'entrée) et le JSON reçu (DTO de sortie). Front et back doivent être d'accord dessus."),
    P("Onglet Réseau", "F12 → Réseau : la frontière entre le front et le back. Il dit tout de suite de quel côté chercher un bug."),
    P("Couches miroir", "Le front et le back ont la même organisation : une couche qui parle à l'extérieur, une couche de logique, une couche d'accès aux données."),
  ],
  diagram=D(
    nodes=[
      N("comp", 0, 0, "Composant", "NoterLivre.tsx", kind="file", color="accent"),
      N("hook", 0, 1, "Hook / mutation", "useNoter()", color="accent"),
      N("apif", 0, 2, "api/notes.ts", "axios.post", kind="doc", color="accent"),
      N("ctrl", 2, 2, "Contrôleur", "NoteController", kind="file"),
      N("svc", 2, 1, "Service", "NoteService::noter()"),
      N("repo", 2, 0, "Repository", "EmpruntRepository", kind="db", color="muted"),
    ],
    edges=[E("comp", "hook"), E("hook", "apif"), E("apif", "ctrl", "POST /api/livres/7/notes"), E("ctrl", "svc"), E("svc", "repo"), E("ctrl", "apif", "201 + JSON", dashed=True, color="good", back=True)],
    lanes=[LANE("Navigateur (React)", 0, 0, "accent"), LANE("Serveur (Symfony)", 2, 2, "tc")],
    caption="Les deux côtés en miroir : composant ↔ contrôleur, hook ↔ service, api/ ↔ repository. Le DTO est le contrat au milieu."),
  lessons=[
    L("Le trajet complet d'un clic", r"""
L'utilisateur clique sur « 4 étoiles » pour noter un livre. Voici tout ce qui se passe, dans l'ordre :

1. **Composant** `NoterLivre` : le `onClick` appelle `noter.mutate(4)`.
2. **Hook / mutation** : appelle la fonction de la couche API.
3. **api/notes.ts** : `api.post('/livres/7/notes', { note: 4 })`. La requête part.
4. **Réseau** : `POST /api/livres/7/notes` avec `{"note": 4}`.
5. **Route Symfony** → `NoteController::noter()`.
6. **DTO d'entrée** `NoteInput` rempli et validé (`Range(1, 5)`). Invalide ? 422, fin.
7. **Service** `NoteService::noter()` : vérifie que le membre a emprunté le livre (via le **repository**), sinon exception → 403.
8. Création de l'**entité** `Note`, `persist`, `flush` → `INSERT`.
9. **DTO de sortie** `NoteOutput` → JSON, statut 201.
10. **Retour** : axios reçoit `res.data`, la mutation invalide `['livres', 7]`, React redessine.

Chaque étape est courte et ne fait qu'une chose. C'est ce découpage qui rend l'ensemble compréhensible et réparable.
"""),
    L("Les deux côtés en miroir", r"""
Le front et le back appliquent la **même** séparation des rôles :

| Rôle | Front (React) | Back (Symfony) |
|---|---|---|
| Parle à l'extérieur | Composant (l'utilisateur) | Contrôleur (HTTP) |
| Logique du cas d'usage | Hook / mutation | Service |
| Accès aux données | `api/*.ts` | Repository / EntityManager |
| Forme des données | Types TypeScript | DTO |

Le **DTO** et le **type TypeScript** décrivent le même JSON : c'est le contrat. Changer l'un sans l'autre est la cause n°1 des bugs entre front et back (un champ renommé `note` → `valeur` d'un côté seulement donne un 422 incompréhensible).
"""),
    L("Débugger en suivant le trajet", r"""
Quand « ça ne marche pas », ne cherche pas au hasard. Ouvre **F12 → Réseau**, qui est la frontière entre les deux mondes, et regarde la requête :

| Ce que tu vois | Où chercher |
|---|---|
| Aucune requête | Front : le handler n'est pas appelé, mauvaise URL, `mutate` jamais déclenché |
| 404 sur la route | URL ou méthode HTTP différente entre `api/notes.ts` et `#[Route]` |
| 422 | Le JSON envoyé (onglet Payload) ne correspond pas au DTO : nom de champ, type, contrainte |
| 401 / 403 | Authentification (token, intercepteur) ou règle d'accès dans le service |
| 500 | Back : lis le message dans la réponse ou les logs Symfony |
| 201 correct, mais l'écran ne change pas | Front : state non mis à jour, invalidation oubliée |

Une fois le côté trouvé, remonte les couches de **ce côté-là** dans l'ordre du trajet.
"""),
    L("Ajouter une fonctionnalité, couche par couche", r"""
Pour une nouvelle fonctionnalité, on avance dans l'ordre du contrat, pas au hasard :

1. **Le contrat** : route, méthode, JSON d'entrée et de sortie. Écris-le d'abord (même dans un commentaire).
2. **Back** : DTO d'entrée et de sortie, règle dans l'entité, service, contrôleur. Teste avec un client HTTP (ou le simulateur).
3. **Front** : type TypeScript, fonction dans `api/`, hook ou mutation, composant.

Chaque couche reçoit **une petite pièce**. Si une pièce devient grosse (un contrôleur de 40 lignes, un composant qui fait des `axios.post`), c'est qu'elle fait le travail d'une autre couche.
"""),
  ],
  recap=[
    "Un clic traverse ~10 étapes courtes : composant → hook → api → HTTP → contrôleur → DTO → service → entité/base → DTO → JSON → state.",
    "Front et back en miroir : composant ↔ contrôleur, hook ↔ service, api ↔ repository, type TS ↔ DTO.",
    "Le DTO et le type TS sont le même contrat : les changer ensemble.",
    "Débugger : F12 → Réseau d'abord, pour savoir de quel côté chercher, puis remonter les couches de ce côté.",
    "Nouvelle fonctionnalité : contrat → back → front, une petite pièce par couche.",
  ],
  example=[F("back/NoteController.php", "php", r"""
<?php

#[Route('/api/livres/{id}/notes', methods: ['POST'])]
public function noter(
    Livre $livre,
    #[MapRequestPayload] NoteInput $input,
    #[CurrentUser] User $membre,
    NoteService $notes,
): JsonResponse {
    return $this->json(NoteOutput::fromEntity($notes->noter($livre, $membre, $input)), 201);
}
"""), F("back/NoteService.php", "php", r"""
<?php

final class NoteService
{
    public function __construct(private EmpruntRepository $emprunts, private EntityManagerInterface $em) {}

    public function noter(Livre $livre, User $membre, NoteInput $in): Note
    {
        if (!$this->emprunts->aDejaEmprunte($membre, $livre)) {
            throw new PasEmprunte('Emprunte ce livre avant de le noter');   // 403
        }
        $note = new Note($livre, $membre, $in->note, $in->commentaire);
        $this->em->persist($note);
        $this->em->flush();
        return $note;
    }
}
"""), F("front/api/notes.ts", "ts", r"""
import { api } from './client';

// Le miroir de NoteInput et NoteOutput
export type NoteInput = { note: number; commentaire?: string };
export type NoteOutput = { id: number; note: number; commentaire: string | null };

export const noterLivre = (livreId: number, body: NoteInput) =>
  api.post<NoteOutput>(`/livres/${livreId}/notes`, body).then((r) => r.data);
"""), F("front/NoterLivre.tsx", "tsx", r"""
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { noterLivre } from './api/notes';

export default function NoterLivre({ livreId }: { livreId: number }) {
  const qc = useQueryClient();
  const noter = useMutation({
    mutationFn: (note: number) => noterLivre(livreId, { note }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['livres', livreId] }),
  });

  return (
    <div>
      {[1, 2, 3, 4, 5].map((n) => (
        <button key={n} onClick={() => noter.mutate(n)} disabled={noter.isPending}>{n}</button>
      ))}
    </div>
  );
}
""")],
  notes=["Lis les 4 fichiers dans l'ordre du trajet inverse : composant → api → contrôleur → service.",
         "`NoteInput` (PHP) et `NoteInput` (TS) ont les mêmes champs : c'est le contrat.",
         "Le contrôleur et le composant font chacun quelques lignes : ils ne font que relier.",
         "La règle « avoir emprunté le livre » est dans le service, qui lève une exception (403)."],
  td1=dict(path="Notes.php",
    title="Noter un livre : le back",
    enonce="Un membre peut noter (1 à 5) un livre qu'il a déjà emprunté, une seule fois. Écris tout le côté Symfony, une petite pièce par couche. Le front viendra au niveau 2. " + SIM,
    consignes=["`NoteInput` : `note` (1 à 5), `commentaire` optionnel (300 caractères max)",
               "`NoteService::noter()` : `PasEmprunte` (403) si le membre n'a jamais emprunté le livre, `DejaNote` (409) s'il l'a déjà noté",
               "`NoteOutput` : `id`, `note`, `commentaire`",
               "`POST /api/livres/{id}/notes` → 201 ; livre inconnu → 404 ; non connecté → 401",
               "Le contrôleur fait une ligne"],
    hints=["`EmpruntRepository::aDejaEmprunte($membre, $livre)` est fourni.",
           "Stocke les notes dans `NoteStore::$notes` avec une clé `membreId-livreId` pour détecter les doublons.",
           "`Livre $livre` en argument de l'action : le simulateur le charge via `App::$entities`, 404 sinon."],
    checks=["Noter deux fois le même livre renvoie 409", "Un livre jamais emprunté renvoie 403"],
    files=[F("donnees.php", "php", USES + r"""
// ---- Fourni ----
final class Membre { public function __construct(public readonly int $id, public readonly string $pseudo) {} }
final class Livre { public function __construct(public readonly int $id, public readonly string $titre) {} }

final class EmpruntRepository
{
    /** membreId => [livreIds empruntés un jour] */
    private array $historique = [1 => [7, 8], 2 => []];
    public function aDejaEmprunte(Membre $m, Livre $l): bool { return in_array($l->id, $this->historique[$m->id] ?? [], true); }
}

final class LivreRepository
{
    public function find(int $id): ?Livre { return [7 => new Livre(7, 'Dune'), 8 => new Livre(8, 'Fondation'), 9 => new Livre(9, 'Terremer')][$id] ?? null; }
}

final class NoteStore { public array $notes = []; }
"""), F("Notes.php", "php", r"""
<?php
// à toi : NoteInput (note 1 à 5, commentaire optionnel ≤ 300), PasEmprunte (403), DejaNote (409),
// NoteService::noter(), NoteOutput, NoteController : POST /api/livres/{id}/notes → 201 { id, note, commentaire }
// Un membre ne peut noter un livre qu'une fois.

App::$entities[Livre::class] = fn(int $id) => App::get(LivreRepository::class)->find($id);
App::$user = new Membre(1, 'ana');
App::request('POST', '/api/livres/7/notes', ['note' => 4, 'commentaire' => 'Superbe']);
""")],
    solution=[F("Notes.php", "php", r"""
<?php
final class NoteInput
{
    public function __construct(
        #[Assert\Range(min: 1, max: 5)] public readonly int $note = 0,
        #[Assert\Length(max: 300)] public readonly ?string $commentaire = null,
    ) {}
}

#[WithHttpStatus(403)] final class PasEmprunte extends \DomainException {}
#[WithHttpStatus(409)] final class DejaNote extends \DomainException {}

final class NoteService
{
    public function __construct(private EmpruntRepository $emprunts, private NoteStore $store) {}

    public function noter(Livre $livre, Membre $m, NoteInput $in): array
    {
        if (!$this->emprunts->aDejaEmprunte($m, $livre)) throw new PasEmprunte('Emprunte ce livre avant de le noter');
        $cle = $m->id . '-' . $livre->id;
        if (isset($this->store->notes[$cle])) throw new DejaNote('Tu as déjà noté ce livre');
        return $this->store->notes[$cle] = ['id' => count($this->store->notes) + 1, 'note' => $in->note, 'commentaire' => $in->commentaire];
    }
}

final class NoteOutput
{
    public function __construct(public readonly int $id, public readonly int $note, public readonly ?string $commentaire) {}
    public static function fromArray(array $n): self { return new self($n['id'], $n['note'], $n['commentaire']); }
}

final class NoteController extends AbstractController
{
    #[Route('/api/livres/{id}/notes', methods: ['POST'])]
    public function noter(Livre $livre, #[MapRequestPayload] NoteInput $input, #[CurrentUser] Membre $m, NoteService $s): JsonResponse
    {
        return $this->json(NoteOutput::fromArray($s->noter($livre, $m, $input)), 201);
    }
}

App::$entities[Livre::class] = fn(int $id) => App::get(LivreRepository::class)->find($id);
App::$user = new Membre(1, 'ana');
App::request('POST', '/api/livres/7/notes', ['note' => 4, 'commentaire' => 'Superbe']);
""")],
    run=SRUN(r"""
App::$entities[Livre::class] = fn(int $id) => App::get(LivreRepository::class)->find($id);
App::$user = new Membre(1, 'ana');
$r = App::request('POST', '/api/livres/7/notes', ['note' => 4, 'commentaire' => 'Superbe']);
check('Noter Dune → 201 { id, note: 4, commentaire }', $r->status === 201 && ($r->json['note'] ?? 0) === 4 && array_keys($r->json) === ['id', 'note', 'commentaire'], (string) $r);
check('Noter Dune une 2e fois → 409', App::request('POST', '/api/livres/7/notes', ['note' => 5])->status === 409);
check('Note 6 → 422', App::request('POST', '/api/livres/8/notes', ['note' => 6])->status === 422);
check('Commentaire de 301 caractères → 422', App::request('POST', '/api/livres/8/notes', ['note' => 3, 'commentaire' => str_repeat('a', 301)])->status === 422);
check('Livre jamais emprunté (Terremer) → 403', App::request('POST', '/api/livres/9/notes', ['note' => 3])->status === 403);
check('Livre 99 → 404', App::request('POST', '/api/livres/99/notes', ['note' => 3])->status === 404);
check('Sans commentaire → 201 avec commentaire null', App::request('POST', '/api/livres/8/notes', ['note' => 2])->json['commentaire'] === null);
App::$user = null;
check('Non connecté → 401', App::request('POST', '/api/livres/7/notes', ['note' => 3])->status === 401);
""")),
  tds=[
    TD(2, "Le côté front de la même fonctionnalité",
       "Le back du niveau 1 est en place. Tu écris le front, couche par couche, en respectant **exactement** le contrat : la même route, les mêmes champs, les mêmes codes d'erreur. L'API simulée se comporte comme ton contrôleur Symfony.",
       ["`api/notes.ts` : types `NoteInput` / `NoteOutput` (miroir des DTO) et `noterLivre(livreId, body)` qui renvoie `r.data`",
        "`NoterLivre.tsx` reçoit `livreId` : 5 boutons (1 à 5) + un champ commentaire (placeholder « Commentaire »)",
        "Succès : affiche « Merci pour ta note de N/5 » (avec la note renvoyée par le serveur) et cache les boutons",
        "403 → « Emprunte ce livre avant de le noter » ; 409 → « Tu as déjà noté ce livre » ; 422 → `title` de la 1re violation",
        "Les boutons sont désactivés pendant l'envoi"],
       [F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });
"""), F("api/notes.ts", "ts", r"""
import { api } from './client';
// à toi
"""), F("NoterLivre.tsx", "tsx", r"""
import { useState } from 'react';
import axios from 'axios';
import { noterLivre } from './api/notes';

export function NoterLivre({ livreId }: { livreId: number }) {
  // à toi
  return null;
}

export default function App() {
  return <NoterLivre livreId={7} />;
}
""")],
       ["`noterLivre = (livreId: number, body: NoteInput) => api.post<NoteOutput>(`/livres/${livreId}/notes`, body).then((r) => r.data)`",
        "Garde la réponse dans un state `resultat: NoteOutput | null` ; s'il existe, n'affiche que le message de remerciement.",
        "N'envoie `commentaire` que s'il n'est pas vide : `commentaire.trim() ? { note, commentaire } : { note }`."],
       [F("api/notes.ts", "ts", r"""
import { api } from './client';

export type NoteInput = { note: number; commentaire?: string };
export type NoteOutput = { id: number; note: number; commentaire: string | null };

export const noterLivre = (livreId: number, body: NoteInput) =>
  api.post<NoteOutput>(`/livres/${livreId}/notes`, body).then((r) => r.data);
"""), F("NoterLivre.tsx", "tsx", r"""
import { useState } from 'react';
import axios from 'axios';
import { noterLivre, type NoteOutput } from './api/notes';

export function NoterLivre({ livreId }: { livreId: number }) {
  const [commentaire, setCommentaire] = useState('');
  const [resultat, setResultat] = useState<NoteOutput | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [envoi, setEnvoi] = useState(false);

  async function noter(note: number) {
    setEnvoi(true);
    setErreur(null);
    try {
      setResultat(await noterLivre(livreId, commentaire.trim() ? { note, commentaire } : { note }));
    } catch (err) {
      const s = axios.isAxiosError(err) ? err.response?.status : undefined;
      if (s === 403) setErreur('Emprunte ce livre avant de le noter');
      else if (s === 409) setErreur('Tu as déjà noté ce livre');
      else if (s === 422 && axios.isAxiosError(err)) setErreur(err.response?.data.violations[0].title);
      else setErreur('Erreur, réessaie');
    } finally {
      setEnvoi(false);
    }
  }

  if (resultat) return <p>Merci pour ta note de {resultat.note}/5</p>;

  return (
    <div>
      {[1, 2, 3, 4, 5].map((n) => (
        <button key={n} onClick={() => noter(n)} disabled={envoi}>{n}</button>
      ))}
      <input value={commentaire} onChange={(e) => setCommentaire(e.target.value)} placeholder="Commentaire" />
      {erreur && <p role="alert">{erreur}</p>}
    </div>
  );
}

export default function App() {
  return <NoterLivre livreId={7} />;
}
""")],
       ["Une note réussie remplace les boutons par le remerciement",
        "Chaque erreur du back a son message"],
       run=RUN("react", entry="NoterLivre.tsx", api=r"""
const notes = window.__notes = {};
window.__emprunte = [7, 8];
__api["POST /api/livres/:id/notes"] = (p, b) => {
  b = b || {};
  if (!(b.note >= 1 && b.note <= 5)) return [422, { title: 'Validation Failed', violations: [{ propertyPath: 'note', title: 'Cette valeur doit être comprise entre 1 et 5.' }] }];
  if (b.commentaire !== undefined && String(b.commentaire).length > 300) return [422, { violations: [{ propertyPath: 'commentaire', title: 'Trop long.' }] }];
  if (!window.__emprunte.includes(Number(p.id))) return [403, { error: 'Emprunte ce livre avant de le noter' }];
  if (notes[p.id]) return [409, { error: 'Tu as déjà noté ce livre' }];
  window.__last = b;
  return [201, (notes[p.id] = { id: Object.keys(notes).length + 1, note: b.note, commentaire: b.commentaire ?? null })];
};
""", tests=r"""
assert.equal($$('button').length, 5, '5 boutons de note');
await type('input', 'Superbe livre');
await click($$('button')[3]);
assert($$('button')[0].disabled, 'Boutons désactivés pendant l\'envoi');
await waitFor(() => text().includes('Merci'), 3000);
assert.includes(text(), '4/5', 'Succès : « Merci pour ta note de 4/5 »');
assert.equal($$('button').length, 0, 'Les boutons sont cachés après la note');
assert(window.__last && window.__last.commentaire === 'Superbe livre', 'Le commentaire a été envoyé au serveur');
const React = require('react'); const ReactDOM = require('react-dom/client');
const { NoterLivre } = require('./NoterLivre');
async function essai(livreId) {
  const d = document.createElement('div'); document.body.appendChild(d);
  ReactDOM.createRoot(d).render(React.createElement(NoterLivre, { livreId }));
  await tick(50); d.querySelectorAll('button')[2].click();
  await waitFor(() => d.querySelector('[role=alert]'), 3000);
  return d.querySelector('[role=alert]').textContent;
}
assert.includes(await essai(9), 'Emprunte ce livre', '403 → « Emprunte ce livre avant de le noter »');
assert.includes(await essai(7), 'déjà noté', '409 → « Tu as déjà noté ce livre »');
window.__api['POST /api/livres/:id/notes'] = () => [422, { violations: [{ propertyPath: 'note', title: 'Note invalide.' }] }];
assert.equal(await essai(8), 'Note invalide.', '422 → titre de la 1re violation');
const { noterLivre } = require('./api/notes');
assert(typeof noterLivre === 'function', 'api/notes.ts exporte noterLivre');
""")),
    TD(3, "Débugger une fonctionnalité cassée",
       "La fonctionnalité « Ajouter aux favoris » ne marche pas, et l'équipe ne sait pas où chercher. Le code contient **3 bugs**, à des étapes différentes du trajet. Utilise la console de l'aperçu (comme l'onglet Réseau) pour localiser chaque bug, corrige-le, et écris en commentaire en haut du fichier où il était et comment tu l'as trouvé.",
       ["Contrat : `POST /api/favoris` avec `{ livreId }` → 201 `{ id, livreId }` ; `GET /api/favoris` → liste des favoris",
        "Corrige le bug qui donne un **422** (regarde le corps envoyé)",
        "Corrige le bug qui fait que **l'écran ne change pas** alors que le serveur répond 201",
        "Corrige le bug qui fait que le message d'erreur 409 (« déjà en favori ») **ne s'affiche jamais**",
        "Ne modifie pas l'API simulée : seul le code front est fautif"],
       [F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });
"""), F("api/favoris.ts", "ts", r"""
import { api } from './client';

export type Favori = { id: number; livreId: number };

export const getFavoris = () => api.get<Favori[]>('/favoris').then((r) => r.data);
export const ajouterFavori = (livreId: number) =>
  api.post<Favori>('/favoris', { livre_id: livreId }).then((r) => r.data);
"""), F("Favoris.tsx", "tsx", r"""
import { useEffect, useState } from 'react';
import axios from 'axios';
import { getFavoris, ajouterFavori, type Favori } from './api/favoris';

const livres = [{ id: 1, titre: 'Terremer' }, { id: 2, titre: 'Dune' }, { id: 3, titre: 'Fondation' }];

export default function Favoris() {
  const [favoris, setFavoris] = useState<Favori[]>([]);
  const [erreur, setErreur] = useState<string | null>(null);

  useEffect(() => { getFavoris().then(setFavoris); }, []);

  async function ajouter(livreId: number) {
    setErreur(null);
    try {
      await ajouterFavori(livreId);
    } catch (err) {
      if (axios.isAxiosError(err) && (err as any).status === 409) setErreur('Déjà dans tes favoris');
      else setErreur('Erreur');
    }
  }

  return (
    <>
      <p className="compteur">{favoris.length} favori(s)</p>
      {livres.map((l) => (
        <button key={l.id} onClick={() => ajouter(l.id)}>{l.titre}</button>
      ))}
      {erreur && <p role="alert">{erreur}</p>}
    </>
  );
}
""")],
       ["Bug 1 : compare le nom du champ envoyé dans `api/favoris.ts` avec le contrat (`livreId`).",
        "Bug 2 : une mutation, c'est 2 étapes (parcours Données & API). La 2e manque.",
        "Bug 3 : avec axios, le statut d'une erreur n'est pas dans `err.status` mais dans…"],
       [F("api/favoris.ts", "ts", r"""
// Bug 1 (couche api) : le champ s'appelait livre_id au lieu de livreId (contrat).
// Trouvé : la console montrait POST /api/favoris → 422.
import { api } from './client';

export type Favori = { id: number; livreId: number };

export const getFavoris = () => api.get<Favori[]>('/favoris').then((r) => r.data);
export const ajouterFavori = (livreId: number) =>
  api.post<Favori>('/favoris', { livreId }).then((r) => r.data);
"""), F("Favoris.tsx", "tsx", r"""
// Bug 2 (composant) : après le 201, le state n'était pas mis à jour (2e étape de la mutation oubliée).
// Trouvé : la console montrait 201 mais le compteur restait à 0.
// Bug 3 (composant) : le statut d'une erreur axios est dans err.response.status, pas err.status.
// Trouvé : un 409 dans la console, mais le message générique « Erreur » s'affichait.
import { useEffect, useState } from 'react';
import axios from 'axios';
import { getFavoris, ajouterFavori, type Favori } from './api/favoris';

const livres = [{ id: 1, titre: 'Terremer' }, { id: 2, titre: 'Dune' }, { id: 3, titre: 'Fondation' }];

export default function Favoris() {
  const [favoris, setFavoris] = useState<Favori[]>([]);
  const [erreur, setErreur] = useState<string | null>(null);

  useEffect(() => { getFavoris().then(setFavoris); }, []);

  async function ajouter(livreId: number) {
    setErreur(null);
    try {
      const f = await ajouterFavori(livreId);
      setFavoris((l) => [...l, f]);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) setErreur('Déjà dans tes favoris');
      else setErreur('Erreur');
    }
  }

  return (
    <>
      <p className="compteur">{favoris.length} favori(s)</p>
      {livres.map((l) => (
        <button key={l.id} onClick={() => ajouter(l.id)}>{l.titre}</button>
      ))}
      {erreur && <p role="alert">{erreur}</p>}
    </>
  );
}
""")],
       ["Les 3 bugs sont corrigés et commentés",
        "Tu sais dire, pour chacun, ce que montrait la console"],
       run=RUN("react", entry="Favoris.tsx", api=r"""
const favs = window.__favs = [];
__api["GET /api/favoris"] = () => favs;
__api["POST /api/favoris"] = (p, b) => {
  b = b || {};
  if (!(Number(b.livreId) > 0)) return [422, { violations: [{ propertyPath: 'livreId', title: 'Cette valeur doit être strictement positive.' }] }];
  if (favs.some((f) => f.livreId === b.livreId)) return [409, { error: 'Déjà en favori' }];
  const f = { id: favs.length + 1, livreId: b.livreId };
  favs.push(f);
  return [201, f];
};
""", tests=r"""
await waitFor(() => $('.compteur'), 2000);
await click(byText('Dune'));
await waitFor(() => window.__favs.length === 1 || $('[role=alert]'), 3000);
assert.equal(window.__favs.length, 1, 'Bug 1 corrigé : le serveur accepte le favori (plus de 422)');
await waitFor(() => $('.compteur').textContent.startsWith('1'), 3000);
assert.includes($('.compteur').textContent, '1 favori', 'Bug 2 corrigé : le compteur passe à 1 sans recharger');
await click(byText('Dune'));
await waitFor(() => $('[role=alert]'), 3000);
assert.includes($('[role=alert]').textContent, 'Déjà dans tes favoris', 'Bug 3 corrigé : le 409 affiche « Déjà dans tes favoris »');
assert(/Bug 1/.test(source('api/favoris.ts') + source('Favoris.tsx')) && /Bug 2/.test(source('Favoris.tsx')) && /Bug 3/.test(source('Favoris.tsx')), 'Les 3 bugs sont expliqués en commentaire');
""")),
  ])

MODULES = [roles, liens, err, bout]

from common import V2, P, L, D, N, E, LANE, F, TD, RUN
from c_dto_v1 import MODULES as V1
from symfony_sim import SYMFONY_SETUP

v1 = {m["id"]: m for m in V1}

SIM = "Le bouton Exécuter utilise un **Symfony simulé** : `App::request('POST', '/api/...', [...])` envoie une fausse requête HTTP à tes contrôleurs (routes, `#[MapRequestPayload]`, validation, statuts) et affiche la réponse (`HTTP> ...`). Les classes sont sans `namespace` pour tourner dans le navigateur."

def SRUN(tests):
    return RUN("php", tests="Atelier\\App::$echo = false;\n" + tests, setup=SYMFONY_SETUP)

USES = r"""<?php
declare(strict_types=1);

use Atelier\App;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpKernel\Attribute\MapQueryString;
use Symfony\Component\HttpKernel\Attribute\MapRequestPayload;
use Symfony\Component\HttpKernel\Attribute\WithHttpStatus;
use Symfony\Component\Routing\Attribute\Route;
use Symfony\Component\Security\Http\Attribute\CurrentUser;
use Symfony\Component\Validator\Constraints as Assert;
"""

# Données de la bibliothèque : entités "déjà en base" + repository en mémoire.
BIBLIO = F("bibliotheque.php", "php", USES + r"""
// ---- Données fournies (comme si elles venaient de Doctrine) ----

#[WithHttpStatus(409)]
final class LivreIndisponible extends \DomainException {}

final class Auteur
{
    public function __construct(private int $id, private string $nom) {}
    public function getId(): int { return $this->id; }
    public function getNom(): string { return $this->nom; }
}

final class Livre
{
    private bool $disponible = true;
    /** @var Emprunt[] */
    private array $emprunts = [];

    public function __construct(
        private int $id,
        private string $titre,
        private Auteur $auteur,
        private string $isbn,
        private \DateTimeImmutable $publieLe,
    ) {}

    public function getId(): int { return $this->id; }
    public function getTitre(): string { return $this->titre; }
    public function getAuteur(): Auteur { return $this->auteur; }
    public function getIsbn(): string { return $this->isbn; }
    public function getPublieLe(): \DateTimeImmutable { return $this->publieLe; }
    public function isDisponible(): bool { return $this->disponible; }
    public function getEmprunts(): array { return $this->emprunts; }

    public function emprunter(Membre $m, \DateTimeImmutable $rendreLe): Emprunt
    {
        if (!$this->disponible) throw new LivreIndisponible("Le livre {$this->id} est déjà emprunté");
        $this->disponible = false;
        return $this->emprunts[] = new Emprunt(count($this->emprunts) + 100 * $this->id, $this, $m, $rendreLe);
    }
}

final class Membre
{
    public function __construct(private int $id, private string $pseudo, private string $email) {}
    public function getId(): int { return $this->id; }
    public function getPseudo(): string { return $this->pseudo; }
    public function getEmail(): string { return $this->email; }
}

final class Emprunt
{
    public function __construct(private int $id, private Livre $livre, private Membre $membre, private \DateTimeImmutable $rendreLe) {}
    public function getId(): int { return $this->id; }
    public function getLivre(): Livre { return $this->livre; }
    public function getMembre(): Membre { return $this->membre; }
    public function getRendreLe(): \DateTimeImmutable { return $this->rendreLe; }
}

final class LivreRepository
{
    /** @var array<int, Livre> */
    private array $livres = [];

    public function __construct()
    {
        $leGuin = new Auteur(1, 'Ursula K. Le Guin');
        $herbert = new Auteur(2, 'Frank Herbert');
        $asimov = new Auteur(3, 'Isaac Asimov');
        foreach ([
            [1, 'Terremer', $leGuin, '9782253023418', '1968-01-01'],
            [2, 'Dune', $herbert, '9782266320481', '1965-08-01'],
            [3, 'Fondation', $asimov, '9782070360536', '1951-05-01'],
            [4, 'Les Dépossédés', $leGuin, '9782253072201', '1974-05-01'],
            [5, 'Les Robots', $asimov, '9782290055953', '1950-12-02'],
        ] as [$id, $t, $a, $isbn, $d]) {
            $this->livres[$id] = new Livre($id, $t, $a, $isbn, new \DateTimeImmutable($d));
        }
        $this->livres[2]->emprunter(new Membre(9, 'zoe', 'zoe@exemple.fr'), new \DateTimeImmutable('2026-12-01'));
    }

    /** @return Livre[] */
    public function findAll(): array { return array_values($this->livres); }
    public function find(int $id): ?Livre { return $this->livres[$id] ?? null; }
}
""")

def biblio_setup():
    """Code de test qui relie le repository au simulateur (paramètres de route typés Livre)."""
    return "App::reset(); $__repo = App::get(LivreRepository::class); App::$entities[Livre::class] = fn(int $id) => $__repo->find($id);\n"

# ---------------------------------------------------------------- Pourquoi
pq = V2(v1["dto-pourquoi"],
  prereq=[
    P("API JSON", "Une application serveur qui répond en JSON au lieu de pages HTML. Ton front React l'appelle avec axios (parcours Données & API)."),
    P("Sérialiser", "Transformer un objet PHP en texte JSON pour l'envoyer. Désérialiser = l'inverse : JSON reçu → objet PHP."),
    P("Entité", "Une classe mappée sur une table avec Doctrine (`#[ORM\\Entity]`), avec ses relations et ses règles (parcours Doctrine)."),
    P("`readonly`", "Une propriété qu'on ne peut écrire qu'une fois, à la construction (PHP 8.1). `public readonly string $titre` se lit partout mais ne se modifie jamais."),
    P("Contrat", "L'accord entre le front et le back sur la forme exacte des données : noms des champs, types, champs obligatoires."),
  ],
  diagram=D(
    nodes=[
      N("front", 0, 0, "React envoie", "axios.post(...)", color="accent"),
      N("in", 1, 0, "DTO d'entrée", "ce que le client\na le droit de choisir", kind="file"),
      N("svc", 2, 0, "Service", "crée / modifie"),
      N("ent", 3, 0, "Entité", "relations, règles,\nmot de passe…", kind="db", color="muted"),
      N("fe", 3, 1, "fromEntity()", "choisit les champs", kind="pill", color="good"),
      N("out", 1, 1, "DTO de sortie", "ce que le client\na le droit de voir", kind="file", color="good"),
      N("front2", 0, 1, "React reçoit", "res.data", color="accent"),
    ],
    edges=[E("front", "in", "JSON"), E("in", "svc"), E("svc", "ent"), E("ent", "fe"), E("fe", "out", color="good"), E("out", "front2", "JSON", color="good")],
    lanes=[LANE("Front", 0, 0, "accent"), LANE("Frontière de l'API", 1, 1, "warn"), LANE("Back", 2, 3, "tc")],
    caption="Les DTO forment la frontière de l'API. L'entité reste à l'intérieur ; seul ce que les DTO décrivent entre et sort."),
  lessons=[
    L("Le problème : renvoyer l'entité telle quelle", r"""
Le réflexe naturel, quand on débute une API Symfony, c'est de renvoyer directement l'entité :

```php
#[Route('/api/users/{id}')]
public function show(User $user): JsonResponse
{
    return $this->json($user);   // tout l'objet part en JSON
}
```

Trois problèmes apparaissent vite :

1. **Fuite de données.** Le sérialiseur appelle tous les getters : `getPassword()`, `getRoles()`, `getEmail()`… Le mot de passe haché part dans la réponse.
2. **Boucles infinies.** `User` a des `Commande`, chaque commande a son `User`, qui a des commandes… Le sérialiseur tourne en rond et finit en erreur 500 (« circular reference »).
3. **Couplage.** Le JSON reproduit la structure de ta base. Renommer une colonne, découper une table, ajouter une relation : le JSON change, et le front casse sans prévenir.

Dans l'autre sens, c'est pareil : remplir une entité directement depuis le JSON reçu permettrait au client d'envoyer `"roles": ["ROLE_ADMIN"]` ou `"id": 42` si l'on n'y prend pas garde.
"""),
    L("La solution : un DTO à chaque frontière", r"""
Un **DTO** (*Data Transfer Object*) est une petite classe qui décrit **exactement** les données qui traversent la frontière de l'API. Rien de plus, rien de moins.

```php
final class UserOutput
{
    public function __construct(
        public readonly int $id,
        public readonly string $pseudo,
        public readonly string $inscritLe,
    ) {}
}
```

Caractéristiques d'un DTO :

- **Pas de logique métier** : des propriétés, éventuellement une méthode de construction (`fromEntity`), c'est tout.
- **Propriétés `public readonly`** : faciles à lire et à sérialiser, impossibles à modifier par erreur.
- **Types simples** : `string`, `int`, `bool`, `array`, d'autres DTO. Pas d'entités dedans (sinon les problèmes reviennent).
- **Un DTO par usage**, pas un DTO par entité. Créer un article n'attend pas les mêmes champs que le modifier, et la liste n'affiche pas les mêmes champs que le détail.

On nomme souvent : `CreateArticleInput`, `UpdateArticleInput` (entrée), `ArticleOutput`, `ArticleListItem` (sortie).
"""),
    L("Entrée et sortie n'ont pas les mêmes champs", r"""
Compare ce que le client **envoie** pour créer un article et ce qu'il **reçoit** :

| Champ | Envoyé (Input) | Reçu (Output) |
|---|---|---|
| `id` | non : c'est la base qui le choisit | oui |
| `titre`, `contenu` | oui | oui (le contenu parfois tronqué) |
| `auteur` | non : c'est l'utilisateur connecté | oui, juste le nom |
| `creeLe` | non : c'est le serveur qui date | oui, en texte (`2026-11-12T10:00:00+01:00`) |
| `motDePasse` (inscription) | oui | **jamais** |

Le DTO d'entrée décrit **ce que le client a le droit de choisir**. Le DTO de sortie décrit **ce que le client a le droit de voir**. Tout le reste est décidé par le serveur.
"""),
    L("Le DTO, c'est le contrat avec le front", r"""
Ton front React a ses types TypeScript (parcours Données & API) :

```ts
type ArticleOutput = { id: number; titre: string; extrait: string; auteur: string; creeLe: string };
```

C'est le **miroir** de ton DTO de sortie PHP. Tant que le DTO ne change pas, le front fonctionne, quoi que tu fasses dans tes entités et ta base. C'est ce qui rend le back et le front **indépendants**.

En pratique : quand tu changes un DTO, tu changes le contrat. Préviens le front (ou fais-le évoluer en même temps), et évite de renommer un champ existant : ajoute plutôt un nouveau champ.
"""),
  ],
  recap=[
    "Renvoyer l'entité = fuite de données, boucles infinies et front couplé à la base.",
    "Un DTO décrit exactement ce qui entre (Input) ou sort (Output) de l'API.",
    "Pas de logique, `public readonly`, types simples, **pas d'entité dedans**.",
    "Un DTO **par usage** (créer, modifier, liste, détail), pas par entité.",
    "Le DTO de sortie est le contrat avec le front : son miroir est le type TypeScript.",
  ],
  example=[F("src/Dto/CreateArticleInput.php", "php", r"""
<?php

namespace App\Dto;

/** Ce que le front ENVOIE pour créer un article. */
final class CreateArticleInput
{
    public function __construct(
        public readonly string $titre,
        public readonly string $contenu,
        public readonly array $tags = [],
    ) {}
}
"""), F("src/Dto/ArticleOutput.php", "php", r"""
<?php

namespace App\Dto;

use App\Entity\Article;

/** Ce que l'API RENVOIE : on choisit chaque champ exposé. */
final class ArticleOutput
{
    public function __construct(
        public readonly int $id,
        public readonly string $titre,
        public readonly string $extrait,
        public readonly string $auteur,   // juste le nom, pas l'objet User
        public readonly string $creeLe,   // date en texte
    ) {}

    public static function fromEntity(Article $a): self
    {
        return new self(
            id: $a->getId(),
            titre: $a->getTitre(),
            extrait: mb_substr($a->getContenu(), 0, 140),
            auteur: $a->getAuteur()->getPseudo(),
            creeLe: $a->getCreeLe()->format(DATE_ATOM),
        );
    }
}
"""), F("front/types.ts", "ts", r"""
// Le miroir exact de ArticleOutput côté React
export type ArticleOutput = {
  id: number;
  titre: string;
  extrait: string;
  auteur: string;
  creeLe: string;
};

export type CreateArticleInput = { titre: string; contenu: string; tags?: string[] };
""")],
  notes=["`CreateArticleInput` ne contient ni `id`, ni auteur, ni date : le client ne choisit pas ces valeurs.",
         "`ArticleOutput::fromEntity()` est le seul endroit qui sait passer de l'entité au JSON.",
         "`auteur` est une chaîne : aucune relation n'est sérialisée, donc pas de boucle possible.",
         "`front/types.ts` reprend les mêmes champs : c'est le contrat entre les deux applications."],
  td1=dict(path="dto.php",
    files=[F("dto.php", "php", r"""
<?php
declare(strict_types=1);

final class RegisterInput
{
    // à toi : ce que le formulaire React envoie
}

final class UserOutput
{
    // à toi : ce que l'API renvoie après inscription
    // Explique en commentaire pourquoi le mot de passe n'est que dans l'un des deux.
}
""")],
    solution=[F("dto.php", "php", r"""
<?php
declare(strict_types=1);

final class RegisterInput
{
    public function __construct(
        public readonly string $email,
        public readonly string $motDePasse,   // en clair à l'entrée uniquement : haché tout de suite
        public readonly string $pseudo,
        public readonly bool $accepteCgu,
    ) {}
}

final class UserOutput
{
    // Pas de mot de passe : une réponse d'API ne renvoie jamais un secret, même haché.
    public function __construct(
        public readonly int $id,
        public readonly string $email,
        public readonly string $pseudo,
        public readonly string $inscritLe,
    ) {}
}
""")],
    run=RUN("php", tests=r"""
$in = new ReflectionClass(RegisterInput::class); $out = new ReflectionClass(UserOutput::class);
$names = fn($rc) => array_map(fn($p) => $p->getName(), $rc->getProperties());
check('RegisterInput contient email, motDePasse, pseudo, accepteCgu', !array_diff(['email', 'motDePasse', 'pseudo', 'accepteCgu'], $names($in)));
check('RegisterInput ne contient pas d\'id', !in_array('id', $names($in), true));
check('UserOutput contient id, email, pseudo', !array_diff(['id', 'email', 'pseudo'], $names($out)));
check('UserOutput ne contient aucun mot de passe', !array_filter($names($out), fn($n) => stripos($n, 'pass') !== false || stripos($n, 'mot') !== false));
$allRo = fn($rc) => !array_filter($rc->getProperties(), fn($p) => !$p->isPublic() || !$p->isReadOnly());
check('Toutes les propriétés sont public readonly', $allRo($in) && $allRo($out));
check('Aucune méthode à part le constructeur', count($in->getMethods()) === 1 && count($out->getMethods()) === 1);
""")),
  tds=[
    TD(2, "Réparer une API qui renvoie l'entité",
       "Cette route renvoie l'entité `Livre` directement. Lance-la : l'API répond **500** (référence circulaire Livre → Emprunt → Livre…). Tu dois la réparer avec un DTO de sortie, sans toucher aux entités. " + SIM,
       ["Crée `LivreOutput` avec `id`, `titre`, `auteur` (le **nom**), `disponible`",
        "Ajoute `public static function fromEntity(Livre $l): self`",
        "Le contrôleur renvoie `LivreOutput::fromEntity($livre)` au lieu de `$livre`",
        "`GET /api/livres/2` doit répondre 200 avec exactement ces 4 champs (Dune est emprunté : `disponible` vaut `false`)",
        "Aucune information sur l'emprunteur ne doit apparaître"],
       [BIBLIO, F("LivreController.php", "php", r"""
<?php
// à toi : LivreOutput

final class LivreController extends AbstractController
{
    #[Route('/api/livres/{id}', methods: ['GET'])]
    public function show(Livre $livre): JsonResponse
    {
        return $this->json($livre);   // à corriger
    }
}

// Essai
App::$entities[Livre::class] = fn(int $id) => App::get(LivreRepository::class)->find($id);
App::request('GET', '/api/livres/2');
""")],
       ["`auteur: $l->getAuteur()->getNom()`",
        "Les arguments nommés rendent `fromEntity` lisible : `new self(id: ..., titre: ..., ...)`.",
        "Regarde le message d'erreur 500 avant de corriger : il explique le problème."],
       [F("LivreController.php", "php", r"""
<?php
final class LivreOutput
{
    public function __construct(
        public readonly int $id,
        public readonly string $titre,
        public readonly string $auteur,
        public readonly bool $disponible,
    ) {}

    public static function fromEntity(Livre $l): self
    {
        return new self(
            id: $l->getId(),
            titre: $l->getTitre(),
            auteur: $l->getAuteur()->getNom(),
            disponible: $l->isDisponible(),
        );
    }
}

final class LivreController extends AbstractController
{
    #[Route('/api/livres/{id}', methods: ['GET'])]
    public function show(Livre $livre): JsonResponse
    {
        return $this->json(LivreOutput::fromEntity($livre));
    }
}

App::$entities[Livre::class] = fn(int $id) => App::get(LivreRepository::class)->find($id);
App::request('GET', '/api/livres/2');
""")],
       ["La réponse est 200 et ne contient que 4 champs",
        "Le mot « zoe » n'apparaît nulle part dans le JSON"],
       run=SRUN(biblio_setup() + r"""
$r = App::request('GET', '/api/livres/2');
check('GET /api/livres/2 → 200', $r->status === 200, (string) $r);
check('Exactement id, titre, auteur, disponible', is_array($r->json) && array_keys($r->json) === ['id', 'titre', 'auteur', 'disponible'], json_encode($r->json, JSON_UNESCAPED_UNICODE));
check('auteur = "Frank Herbert" (une chaîne)', ($r->json['auteur'] ?? null) === 'Frank Herbert');
check('disponible = false pour Dune', ($r->json['disponible'] ?? null) === false);
check('Aucune donnée de l\'emprunteur', !str_contains(json_encode($r->json), 'zoe'));
check('GET /api/livres/99 → 404', App::request('GET', '/api/livres/99')->status === 404);
""")),
    TD(3, "Respecter le contrat du front",
       "L'équipe front t'envoie le type TypeScript qu'elle attend pour la page catalogue. Ton DTO doit le respecter **à la lettre** : mêmes noms, mêmes types, rien de plus. Certains champs n'existent pas tels quels dans l'entité : il faut les **calculer**. " + SIM,
       ["Type attendu : `type LivreCarte = { id: number; titre: string; auteur: string; annee: number; nbEmprunts: number; badge: 'nouveau' | 'classique' | null }`",
        "`annee` : l'année de publication (entier) ; `nbEmprunts` : le nombre d'emprunts du livre",
        "`badge` : `'classique'` si publié avant 1960, `'nouveau'` si publié il y a moins de 2 ans, sinon `null`",
        "`GET /api/livres` renvoie la liste de `LivreCarte` pour tous les livres",
        "Le calcul du badge prend la date du jour en paramètre de `fromEntity()` (pour être testable)"],
       [BIBLIO, F("CatalogueController.php", "php", r"""
<?php
final class LivreCarte
{
    // à toi
}

final class CatalogueController extends AbstractController
{
    public function __construct(private LivreRepository $livres) {}

    #[Route('/api/livres', methods: ['GET'])]
    public function index(): JsonResponse
    {
        // à toi
    }
}

App::request('GET', '/api/livres');
""")],
       ["`annee: (int) $l->getPublieLe()->format('Y')`",
        "`nbEmprunts: count($l->getEmprunts())`",
        "`array_map(fn(Livre $l) => LivreCarte::fromEntity($l, $today), $this->livres->findAll())`"],
       [F("CatalogueController.php", "php", r"""
<?php
final class LivreCarte
{
    public function __construct(
        public readonly int $id,
        public readonly string $titre,
        public readonly string $auteur,
        public readonly int $annee,
        public readonly int $nbEmprunts,
        public readonly ?string $badge,
    ) {}

    public static function fromEntity(Livre $l, \DateTimeImmutable $today): self
    {
        $publie = $l->getPublieLe();
        $badge = null;
        if ((int) $publie->format('Y') < 1960) {
            $badge = 'classique';
        } elseif ($publie > $today->modify('-2 years')) {
            $badge = 'nouveau';
        }
        return new self(
            id: $l->getId(),
            titre: $l->getTitre(),
            auteur: $l->getAuteur()->getNom(),
            annee: (int) $publie->format('Y'),
            nbEmprunts: count($l->getEmprunts()),
            badge: $badge,
        );
    }
}

final class CatalogueController extends AbstractController
{
    public function __construct(private LivreRepository $livres) {}

    #[Route('/api/livres', methods: ['GET'])]
    public function index(): JsonResponse
    {
        $today = new \DateTimeImmutable('today');
        return $this->json(array_map(fn(Livre $l) => LivreCarte::fromEntity($l, $today), $this->livres->findAll()));
    }
}

App::request('GET', '/api/livres');
""")],
       ["Chaque élément a exactement les 6 clés du type TypeScript",
        "Fondation (1951) a le badge « classique »"],
       run=SRUN(biblio_setup() + r"""
$r = App::request('GET', '/api/livres');
check('GET /api/livres → 200 avec 5 livres', $r->status === 200 && is_array($r->json) && count($r->json) === 5, (string) $r);
$keys = ['id', 'titre', 'auteur', 'annee', 'nbEmprunts', 'badge'];
check('Chaque élément a exactement les clés du contrat', !array_filter($r->json, fn($x) => array_keys($x) !== $keys), json_encode(array_keys($r->json[0] ?? [])));
$dune = $r->json[1];
check('Dune : annee 1965 (int), nbEmprunts 1', $dune['annee'] === 1965 && $dune['nbEmprunts'] === 1);
check('Fondation (1951) : badge classique', $r->json[2]['badge'] === 'classique');
check('Terremer (1968) : badge null', $r->json[0]['badge'] === null);
$recent = new Livre(9, 'Récent', new Auteur(5, 'X'), '1', (new DateTimeImmutable('today'))->modify('-3 months'));
check('Un livre de moins de 2 ans : badge nouveau', LivreCarte::fromEntity($recent, new DateTimeImmutable('today'))->badge === 'nouveau');
""")),
  ])

# ---------------------------------------------------------------- Entrée
entree = V2(v1["dto-entree"],
  prereq=[
    P("Corps de requête", "Les données envoyées avec un POST/PUT/PATCH, en JSON : `{\"titre\": \"Hello\"}`. Côté React : le 2e argument de `api.post(url, data)`."),
    P("Contrainte de validation", "Un attribut `#[Assert\\...]` qui décrit une règle sur une propriété : `NotBlank`, `Length(min: 5)`, `Email`… Le composant Validator de Symfony les vérifie."),
    P("Statut 422", "*Unprocessable Content* : la requête est bien formée, mais les données ne respectent pas les règles. Le corps contient la liste des **violations**."),
    P("Violation", "Une règle non respectée, sous la forme `{ propertyPath: 'titre', title: 'Cette valeur ne doit pas être vide.' }`."),
    P("Argument resolver", "Le mécanisme de Symfony qui fournit les arguments de ton action de contrôleur (le DTO, l'utilisateur connecté, l'entité de la route…) avant de l'appeler."),
  ],
  diagram=D(
    nodes=[
      N("req", 0, 1, "POST /api/register", "{email, motDePasse, …}", kind="doc", color="accent"),
      N("deser", 1, 1, "MapRequestPayload", "JSON → RegisterInput", kind="pill"),
      N("val", 2, 1, "Validator", "#[Assert\\...]", color="warn"),
      N("ctrl", 3, 0, "Contrôleur", "reçoit un DTO valide", color="good"),
      N("e422", 3, 2, "422 automatique", "violations[]", kind="doc", color="bad"),
      N("svc", 4, 0, "Service", "inscrire($input)"),
    ],
    edges=[E("req", "deser"), E("deser", "val"), E("val", "ctrl", "valide", color="good"), E("val", "e422", "invalide", color="bad"), E("ctrl", "svc")],
    caption="Avant même d'entrer dans ton contrôleur, Symfony transforme le JSON en DTO et le valide. Si c'est invalide, il répond 422 tout seul."),
  lessons=[
    L("Recevoir du JSON sans écrire de plomberie", r"""
Sans aide, un contrôleur qui reçoit du JSON ressemble à ça :

```php
$data = json_decode($request->getContent(), true);
if (!is_array($data) || empty($data['titre']) || mb_strlen($data['titre']) < 5) {
    return new JsonResponse(['error' => 'titre invalide'], 422);
}
if (isset($data['tags']) && (!is_array($data['tags']) || count($data['tags']) > 5)) { ... }
// ... et ainsi de suite pour chaque champ
```

C'est long, répétitif, et on oublie toujours un cas (un champ envoyé en nombre au lieu de texte, un tableau vide…).

Depuis Symfony 6.3, un seul attribut fait tout :

```php
#[Route('/api/articles', methods: ['POST'])]
public function create(#[MapRequestPayload] CreateArticleInput $input): JsonResponse
{
    // ici, $input est un objet CreateArticleInput rempli ET valide
}
```

`#[MapRequestPayload]` lit le corps JSON, crée le DTO en faisant correspondre les **clés JSON** aux **paramètres du constructeur**, vérifie les types, puis lance la **validation**. Si une étape échoue, Symfony répond 422 et ton action n'est jamais appelée.
"""),
    L("Décrire les règles avec des contraintes", r"""
Les règles se posent directement sur les propriétés du DTO :

```php
use Symfony\Component\Validator\Constraints as Assert;

final class CreateArticleInput
{
    public function __construct(
        #[Assert\NotBlank]
        #[Assert\Length(min: 5, max: 180)]
        public readonly string $titre = '',

        #[Assert\NotBlank]
        public readonly string $contenu = '',

        #[Assert\Count(max: 5)]
        #[Assert\All([new Assert\Length(max: 30)])]
        public readonly array $tags = [],
    ) {}
}
```

Les contraintes les plus utiles :

| Contrainte | Vérifie |
|---|---|
| `NotBlank` | pas vide (`''`, `null`, `[]`) |
| `Length(min:, max:)` | longueur d'une chaîne |
| `Email` | format d'email |
| `Positive`, `PositiveOrZero`, `Range(min:, max:)` | nombres |
| `Regex('/^[a-z0-9_]+$/')` | motif |
| `IsTrue` | case cochée (CGU) |
| `Choice(['a', 'b'])` | valeur parmi une liste |
| `Count(min:, max:)` | taille d'un tableau |
| `All([...])` | applique des contraintes à **chaque** élément d'un tableau |
| `Date` | chaîne au format `Y-m-d` |
| `Valid` | valide aussi un DTO imbriqué |

Chacune accepte un `message:` personnalisé : `#[Assert\IsTrue(message: 'Tu dois accepter les CGU')]`.
"""),
    L("Pourquoi des valeurs par défaut (`= ''`) ?", r"""
Si le client **oublie** un champ, Symfony ne peut pas appeler le constructeur sans valeur pour ce paramètre : il répondrait par une erreur générique peu claire. Avec une valeur par défaut (`= ''`), le DTO se construit, puis `NotBlank` produit un message précis sur le bon champ : « titre : Cette valeur ne doit pas être vide. ».

Et pourquoi `NotBlank` alors que le type est `string` ? Parce que le type vérifie que c'est une chaîne, pas qu'elle contient quelque chose : `''` est une chaîne parfaitement valide pour PHP.

Deux niveaux d'erreur à distinguer :

- **Type faux** (`"titre": 5`) : refusé à la désérialisation, avant même la validation.
- **Règle non respectée** (`"titre": "abc"`) : refusé par le Validator, avec la liste des violations.

Dans les deux cas : 422, et ton contrôleur n'est pas appelé.
"""),
    L("La réponse 422 et le front", r"""
Quand la validation échoue, Symfony renvoie :

```json
{
  "title": "Validation Failed",
  "violations": [
    { "propertyPath": "titre", "title": "Cette chaîne est trop courte. Elle doit avoir au minimum 5 caractères." },
    { "propertyPath": "tags", "title": "Cette collection doit contenir 5 éléments ou moins." }
  ]
}
```

Côté React (parcours Données & API), ces erreurs arrivent dans le `catch` d'axios : `err.response.status === 422` et `err.response.data.violations`. Grâce à `propertyPath`, tu peux afficher chaque message **sous le bon champ** du formulaire.

Ce que la validation du DTO ne fait **pas** : les règles qui dépendent de la base ou de l'état du système (« cet email est déjà pris », « ce livre est déjà emprunté »). Le DTO vérifie la **forme** des données ; ces règles-là vivent dans le service ou l'entité, et produisent d'autres statuts (409 par exemple). C'est l'objet du TD de niveau 3.
"""),
  ],
  recap=[
    "`#[MapRequestPayload] MonInput $input` : JSON → DTO + validation, avant d'entrer dans l'action.",
    "Les clés JSON correspondent aux paramètres du constructeur du DTO.",
    "Contraintes `#[Assert\\...]` sur les propriétés ; `All` pour chaque élément d'un tableau, `Valid` pour un DTO imbriqué.",
    "Valeurs par défaut (`= ''`) + `NotBlank` : un champ manquant donne un message clair.",
    "Invalide → **422** avec `violations[]` (`propertyPath`, `title`) ; le contrôleur n'est pas appelé.",
    "Le DTO valide la **forme** ; les règles qui dépendent de la base vont dans le service.",
  ],
  example=[F("src/Dto/CreateArticleInput.php", "php", r"""
<?php

namespace App\Dto;

use Symfony\Component\Validator\Constraints as Assert;

final class CreateArticleInput
{
    public function __construct(
        #[Assert\NotBlank]
        #[Assert\Length(min: 5, max: 180)]
        public readonly string $titre = '',

        #[Assert\NotBlank]
        public readonly string $contenu = '',

        #[Assert\Count(max: 5)]
        #[Assert\All([new Assert\Length(max: 30)])]
        public readonly array $tags = [],
    ) {}
}
"""), F("src/Controller/ArticleController.php", "php", r"""
<?php

namespace App\Controller;

use App\Dto\ArticleOutput;
use App\Dto\CreateArticleInput;
use App\Service\ArticleService;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpKernel\Attribute\MapRequestPayload;
use Symfony\Component\Routing\Attribute\Route;

final class ArticleController extends AbstractController
{
    #[Route('/api/articles', methods: ['POST'])]
    public function create(#[MapRequestPayload] CreateArticleInput $input, ArticleService $articles): JsonResponse
    {
        $article = $articles->creer($input);      // que des données valides ici
        return $this->json(ArticleOutput::fromEntity($article), 201);
    }
}
"""), F("echanges.http", "plaintext", r"""
POST /api/articles
{"titre": "Hello world", "contenu": "Premier article", "tags": ["php"]}
-> 201 {"id": 1, "titre": "Hello world", ...}

POST /api/articles
{"titre": "Abc", "tags": ["un-tag-beaucoup-trop-long-pour-etre-accepte"]}
-> 422 {"title": "Validation Failed", "violations": [
     {"propertyPath": "titre", "title": "Cette chaîne est trop courte. Elle doit avoir au minimum 5 caractères."},
     {"propertyPath": "contenu", "title": "Cette valeur ne doit pas être vide."},
     {"propertyPath": "tags", "title": "Cette chaîne est trop longue. Elle doit avoir au maximum 30 caractères."}
   ]}

POST /api/articles
{"titre": 42, "contenu": "x"}
-> 422 (titre doit être une chaîne)
""")],
  notes=["`CreateArticleInput` : chaque propriété porte ses règles ; les valeurs par défaut permettent des messages précis si un champ manque.",
         "`ArticleController::create` fait 2 lignes : toute la vérification a eu lieu avant.",
         "Dans `echanges.http`, la 2e requête montre plusieurs violations d'un coup, chacune avec son champ.",
         "La 3e requête est refusée pour le **type**, avant même les contraintes."],
  td1=dict(path="InscriptionController.php",
    files=[F("services.php", "php", USES + r"""
// ---- Fourni : le service d'inscription (en mémoire) ----
final class InscriptionService
{
    public array $inscrits = [];

    public function inscrire(RegisterInput $in): array
    {
        $user = ['id' => count($this->inscrits) + 1, 'email' => $in->email, 'pseudo' => $in->pseudo, 'hash' => password_hash($in->motDePasse, PASSWORD_DEFAULT)];
        $this->inscrits[] = $user;
        return $user;
    }
}
"""), F("InscriptionController.php", "php", r"""
<?php
final class RegisterInput
{
    public function __construct(
        public readonly string $email = '',
        public readonly string $motDePasse = '',
        public readonly string $pseudo = '',
        public readonly bool $accepteCgu = false,
    ) {}
}

final class UserOutput
{
    public function __construct(
        public readonly int $id,
        public readonly string $email,
        public readonly string $pseudo,
    ) {}
}

final class InscriptionController extends AbstractController
{
    // à toi : POST /api/register
}

App::request('POST', '/api/register', ['email' => 'ana@exemple.fr', 'motDePasse' => 'secret123', 'pseudo' => 'ana_42', 'accepteCgu' => true]);
App::request('POST', '/api/register', ['email' => 'pas-un-email', 'motDePasse' => '123', 'pseudo' => 'a b', 'accepteCgu' => false]);
""")],
    solution=[F("InscriptionController.php", "php", r"""
<?php
final class RegisterInput
{
    public function __construct(
        #[Assert\NotBlank, Assert\Email]
        public readonly string $email = '',

        #[Assert\NotBlank, Assert\Length(min: 8)]
        public readonly string $motDePasse = '',

        #[Assert\NotBlank, Assert\Length(min: 3, max: 20), Assert\Regex('/^[a-zA-Z0-9_]+$/')]
        public readonly string $pseudo = '',

        #[Assert\IsTrue(message: 'Tu dois accepter les CGU')]
        public readonly bool $accepteCgu = false,
    ) {}
}

final class UserOutput
{
    public function __construct(
        public readonly int $id,
        public readonly string $email,
        public readonly string $pseudo,
    ) {}
}

final class InscriptionController extends AbstractController
{
    #[Route('/api/register', methods: ['POST'])]
    public function register(#[MapRequestPayload] RegisterInput $input, InscriptionService $inscription): JsonResponse
    {
        $user = $inscription->inscrire($input);
        return $this->json(new UserOutput($user['id'], $user['email'], $user['pseudo']), 201);
    }
}

App::request('POST', '/api/register', ['email' => 'ana@exemple.fr', 'motDePasse' => 'secret123', 'pseudo' => 'ana_42', 'accepteCgu' => true]);
App::request('POST', '/api/register', ['email' => 'pas-un-email', 'motDePasse' => '123', 'pseudo' => 'a b', 'accepteCgu' => false]);
""")],
    run=SRUN(r"""
App::reset();
$ok = ['email' => 'leo@exemple.fr', 'motDePasse' => 'motdepasse', 'pseudo' => 'leo_99', 'accepteCgu' => true];
$r = App::request('POST', '/api/register', $ok);
check('Inscription valide → 201', $r->status === 201, (string) $r);
check('La réponse ne contient pas de mot de passe', !preg_match('/motDePasse|hash|pass/i', json_encode($r->json)));
$bad = fn(array $diff) => App::request('POST', '/api/register', array_merge($ok, $diff));
$paths = fn($r) => array_column($r->json['violations'] ?? [], 'propertyPath');
check('Email invalide → 422 sur email', in_array('email', $paths($bad(['email' => 'nope'])), true));
check('Mot de passe de 7 caractères → 422', in_array('motDePasse', $paths($bad(['motDePasse' => '1234567'])), true));
check('Pseudo avec espace → 422', in_array('pseudo', $paths($bad(['pseudo' => 'a b'])), true));
check('Pseudo de 2 caractères → 422', in_array('pseudo', $paths($bad(['pseudo' => 'ab'])), true));
$cgu = $bad(['accepteCgu' => false]);
check('CGU non acceptées → message « Tu dois accepter les CGU »', in_array('Tu dois accepter les CGU', array_column($cgu->json['violations'] ?? [], 'title'), true));
check('Champ email manquant → 422 sur email', in_array('email', $paths(App::request('POST', '/api/register', ['motDePasse' => 'motdepasse', 'pseudo' => 'x_x', 'accepteCgu' => true])), true));
check('Le service n\'a été appelé que pour l\'inscription valide', count(App::get(InscriptionService::class)->inscrits) === 1);
""")),
  tds=[
    TD(2, "Commande : DTO imbriqué et tableaux",
       "Une commande contient une **adresse** (un DTO dans le DTO) et une **liste de lignes**. Il faut valider chaque niveau, avec des messages qui pointent vers le bon champ (`adresse.codePostal`). " + SIM,
       ["`AdresseInput` : `rue` (non vide), `codePostal` (5 chiffres, `Regex`), `ville` (non vide)",
        "`CommandeInput` : `adresse` (`AdresseInput`, avec `#[Assert\\Valid]`), `produitIds` (tableau : au moins 1, au plus 10, chaque id strictement positif), `codePromo` (optionnel, `?string`, majuscules et chiffres, 4 à 10 caractères)",
        "`POST /api/commandes` → 201 avec `{ nbProduits, ville }`",
        "Un code postal invalide doit produire une violation sur `adresse.codePostal`",
        "Un code promo absent (`null`) est accepté"],
       [F("CommandeController.php", "php", USES + r"""
final class AdresseInput
{
    // à toi
}

final class CommandeInput
{
    // à toi
}

final class CommandeController extends AbstractController
{
    // à toi
}

App::request('POST', '/api/commandes', [
    'adresse' => ['rue' => '1 rue de la Paix', 'codePostal' => '75002', 'ville' => 'Paris'],
    'produitIds' => [3, 7],
]);
""")],
       ["`#[Assert\\Valid] public readonly ?AdresseInput $adresse = null` : sans `Valid`, l'adresse ne serait pas validée.",
        "Pour `produitIds` : `#[Assert\\Count(min: 1, max: 10), Assert\\All([new Assert\\Positive()])]`.",
        "Les contraintes ignorent `null` (sauf `NotBlank`/`NotNull`) : `codePromo` optionnel n'a donc besoin que de `Regex`."],
       [F("CommandeController.php", "php", USES + r"""
final class AdresseInput
{
    public function __construct(
        #[Assert\NotBlank] public readonly string $rue = '',
        #[Assert\Regex('/^\d{5}$/', message: 'Code postal invalide')] public readonly string $codePostal = '',
        #[Assert\NotBlank] public readonly string $ville = '',
    ) {}
}

final class CommandeInput
{
    public function __construct(
        #[Assert\NotNull, Assert\Valid]
        public readonly ?AdresseInput $adresse = null,

        #[Assert\Count(min: 1, max: 10), Assert\All([new Assert\Positive()])]
        public readonly array $produitIds = [],

        #[Assert\Regex('/^[A-Z0-9]{4,10}$/')]
        public readonly ?string $codePromo = null,
    ) {}
}

final class CommandeController extends AbstractController
{
    #[Route('/api/commandes', methods: ['POST'])]
    public function create(#[MapRequestPayload] CommandeInput $input): JsonResponse
    {
        return $this->json(['nbProduits' => count($input->produitIds), 'ville' => $input->adresse->ville], 201);
    }
}

App::request('POST', '/api/commandes', [
    'adresse' => ['rue' => '1 rue de la Paix', 'codePostal' => '75002', 'ville' => 'Paris'],
    'produitIds' => [3, 7],
]);
""")],
       ["`adresse.codePostal` apparaît dans les violations quand il est faux",
        "10 produits passent, 11 sont refusés"],
       run=SRUN(r"""
App::reset();
$base = ['adresse' => ['rue' => '1 rue X', 'codePostal' => '69001', 'ville' => 'Lyon'], 'produitIds' => [1, 2, 3]];
$r = App::request('POST', '/api/commandes', $base);
check('Commande valide → 201 { nbProduits: 3, ville: Lyon }', $r->status === 201 && $r->json === ['nbProduits' => 3, 'ville' => 'Lyon'], (string) $r);
$paths = fn($r) => array_column($r->json['violations'] ?? [], 'propertyPath');
$cp = $base; $cp['adresse']['codePostal'] = '6900';
check('Code postal 6900 → violation sur adresse.codePostal', in_array('adresse.codePostal', $paths(App::request('POST', '/api/commandes', $cp)), true));
$v = $base; $v['adresse']['ville'] = '';
check('Ville vide → violation sur adresse.ville', in_array('adresse.ville', $paths(App::request('POST', '/api/commandes', $v)), true));
check('Aucun produit → 422', App::request('POST', '/api/commandes', array_merge($base, ['produitIds' => []]))->status === 422);
check('11 produits → 422', App::request('POST', '/api/commandes', array_merge($base, ['produitIds' => range(1, 11)]))->status === 422);
check('Un id négatif → 422', App::request('POST', '/api/commandes', array_merge($base, ['produitIds' => [1, -4]]))->status === 422);
check('Code promo NOEL2026 accepté', App::request('POST', '/api/commandes', array_merge($base, ['codePromo' => 'NOEL2026']))->status === 201);
check('Code promo « noel » refusé', App::request('POST', '/api/commandes', array_merge($base, ['codePromo' => 'noel']))->status === 422);
check('Adresse absente → 422', App::request('POST', '/api/commandes', ['produitIds' => [1]])->status === 422);
""")),
    TD(3, "Réservation : forme dans le DTO, règles dans le service",
       "Réserver une salle demande deux sortes de vérifications : la **forme** (dates au bon format, nombre de personnes) que le DTO valide, et les **règles** qui dépendent des données (la fin après le début, la salle assez grande, le créneau libre) qui vont dans le service et produisent des statuts différents. " + SIM,
       ["`ReservationInput` : `salleId` (positif), `debut` et `fin` (`Date` au format Y-m-d), `personnes` (entre 1 et 50)",
        "Exceptions métier : `DatesIncoherentes` → 422, `SalleIntrouvable` → 404, `SalleTropPetite` → 422, `CreneauPris` → 409 (avec `#[WithHttpStatus]`)",
        "`ReservationService::reserver()` applique les règles **dans cet ordre** : dates, salle existe, capacité, créneau libre (deux réservations de la même salle se chevauchent si `debut1 <= fin2 && debut2 <= fin1`)",
        "`POST /api/reservations` → 201 avec `{ id, salle, debut, fin }`",
        "Le contrôleur ne contient aucun `if` ni `try/catch`"],
       [F("salles.php", "php", USES + r"""
// ---- Fourni : les salles (en mémoire) ----
final class Salle
{
    public function __construct(public readonly int $id, public readonly string $nom, public readonly int $capacite) {}
}

final class SalleRepository
{
    private array $salles;
    public function __construct()
    {
        $this->salles = [1 => new Salle(1, 'Atelier', 8), 2 => new Salle(2, 'Amphi', 40)];
    }
    public function find(int $id): ?Salle { return $this->salles[$id] ?? null; }
}
"""), F("Reservation.php", "php", r"""
<?php
final class ReservationInput
{
    // à toi
}

// à toi : les 4 exceptions métier

final class ReservationService
{
    /** @var list<array{id: int, salle: int, debut: string, fin: string}> */
    private array $reservations = [];

    public function __construct(private SalleRepository $salles) {}

    public function reserver(ReservationInput $in): array
    {
        // à toi
    }
}

final class ReservationController extends AbstractController
{
    // à toi
}

App::request('POST', '/api/reservations', ['salleId' => 1, 'debut' => '2026-12-01', 'fin' => '2026-12-02', 'personnes' => 5]);
""")],
       ["Des dates `Y-m-d` se comparent directement en chaînes : `'2026-12-01' < '2026-12-02'`.",
        "`#[WithHttpStatus(409)] final class CreneauPris extends \\DomainException {}`",
        "Le service renvoie le tableau de la réservation ; le contrôleur fait `return $this->json($service->reserver($input), 201);`"],
       [F("Reservation.php", "php", r"""
<?php
final class ReservationInput
{
    public function __construct(
        #[Assert\Positive] public readonly int $salleId = 0,
        #[Assert\NotBlank, Assert\Date] public readonly string $debut = '',
        #[Assert\NotBlank, Assert\Date] public readonly string $fin = '',
        #[Assert\Range(min: 1, max: 50)] public readonly int $personnes = 0,
    ) {}
}

#[WithHttpStatus(422)] final class DatesIncoherentes extends \DomainException {}
#[WithHttpStatus(404)] final class SalleIntrouvable extends \DomainException {}
#[WithHttpStatus(422)] final class SalleTropPetite extends \DomainException {}
#[WithHttpStatus(409)] final class CreneauPris extends \DomainException {}

final class ReservationService
{
    /** @var list<array{id: int, salle: int, debut: string, fin: string}> */
    private array $reservations = [];

    public function __construct(private SalleRepository $salles) {}

    public function reserver(ReservationInput $in): array
    {
        if ($in->fin < $in->debut) throw new DatesIncoherentes('La fin doit être après le début');
        $salle = $this->salles->find($in->salleId) ?? throw new SalleIntrouvable('Salle introuvable');
        if ($in->personnes > $salle->capacite) throw new SalleTropPetite("La salle {$salle->nom} accueille {$salle->capacite} personnes au maximum");
        foreach ($this->reservations as $r) {
            if ($r['salle'] === $salle->id && $in->debut <= $r['fin'] && $r['debut'] <= $in->fin) {
                throw new CreneauPris('Créneau déjà réservé');
            }
        }
        return $this->reservations[] = ['id' => count($this->reservations) + 1, 'salle' => $salle->id, 'debut' => $in->debut, 'fin' => $in->fin];
    }
}

final class ReservationController extends AbstractController
{
    #[Route('/api/reservations', methods: ['POST'])]
    public function create(#[MapRequestPayload] ReservationInput $input, ReservationService $service): JsonResponse
    {
        return $this->json($service->reserver($input), 201);
    }
}

App::request('POST', '/api/reservations', ['salleId' => 1, 'debut' => '2026-12-01', 'fin' => '2026-12-02', 'personnes' => 5]);
""")],
       ["Chaque erreur a son propre statut : 422, 404, 409",
        "Le contrôleur fait une seule ligne"],
       run=SRUN(r"""
App::reset();
$res = fn(array $b) => App::request('POST', '/api/reservations', array_merge(['salleId' => 1, 'debut' => '2026-12-01', 'fin' => '2026-12-03', 'personnes' => 4], $b));
$ok = $res([]);
check('Réservation valide → 201', $ok->status === 201 && ($ok->json['salle'] ?? null) === 1, (string) $ok);
check('Date mal formée (2026-13-01) → 422 (DTO)', $res(['debut' => '2026-13-01'])->status === 422);
check('50+ personnes → 422 (DTO)', $res(['personnes' => 80])->status === 422);
check('Fin avant début → 422 (service)', $res(['debut' => '2026-12-10', 'fin' => '2026-12-05'])->status === 422);
check('Salle 99 → 404', $res(['salleId' => 99, 'debut' => '2027-01-01', 'fin' => '2027-01-02'])->status === 404);
$pt = $res(['personnes' => 12, 'debut' => '2027-02-01', 'fin' => '2027-02-02']);
check('12 personnes dans l\'Atelier (8) → 422 avec un message clair', $pt->status === 422 && str_contains($pt->json['error'] ?? '', '8'), (string) $pt);
check('Créneau qui chevauche → 409', $res(['debut' => '2026-12-03', 'fin' => '2026-12-04'])->status === 409);
check('Même dates, autre salle → 201', $res(['salleId' => 2])->status === 201);
$src = (new ReflectionMethod(ReservationController::class, 'create'));
check('Le contrôleur n\'a qu\'un paramètre DTO et un service', $src->getNumberOfParameters() === 2);
""")),
  ])

# ---------------------------------------------------------------- Sortie
sortie = V2(v1["dto-sortie"],
  prereq=[
    P("Méthode statique", "Une méthode qu'on appelle sur la classe, pas sur un objet : `ArticleOutput::fromEntity($a)`. Souvent utilisée pour des « constructeurs nommés »."),
    P("Arguments nommés", "`new self(id: 1, titre: 'Dune')` : on nomme chaque argument. Plus lisible quand il y en a beaucoup, et l'ordre ne compte plus."),
    P("`array_map`", "Applique une fonction à chaque élément d'un tableau et renvoie le nouveau tableau : `array_map(fn($l) => LivreOutput::fromEntity($l), $livres)`."),
    P("Format ATOM", "Le format de date standard pour les API : `2026-11-12T10:00:00+01:00`. JavaScript le lit directement avec `new Date(...)`."),
    P("First-class callable", "`LivreOutput::fromEntity(...)` (avec `...`) transforme la méthode en fonction qu'on peut passer à `array_map` (PHP 8.1)."),
  ],
  diagram=D(
    nodes=[
      N("ctrl", 0, 1, "Contrôleur", "récupère des entités", kind="doc"),
      N("ent", 1, 1, "Livre (entité)", "getAuteur(), getEmprunts()…", kind="db", color="muted"),
      N("list", 2, 0, "LivreListItem", "id, titre, auteur, dispo", kind="file", color="good"),
      N("det", 2, 2, "LivreDetail", "+ isbn, publieLe", kind="file", color="good"),
      N("j1", 3, 0, "GET /api/livres", "[ {…}, {…} ]", kind="doc", color="accent"),
      N("j2", 3, 2, "GET /api/livres/2", "{ … }", kind="doc", color="accent"),
    ],
    edges=[E("ctrl", "ent"), E("ent", "list", "fromEntity()", color="good"), E("ent", "det", "fromEntity()", color="good"), E("list", "j1", "json()"), E("det", "j2", "json()")],
    caption="Une même entité alimente plusieurs DTO de sortie : un léger pour les listes, un complet pour le détail."),
  lessons=[
    L("Transformer une entité en DTO, à un seul endroit", r"""
Le contrôleur récupère des entités (via un repository), puis doit les transformer en DTO. Si chaque contrôleur fait sa transformation à la main, elles finissent toutes légèrement différentes (une date formatée ici, pas là). La règle : **un seul endroit** par DTO.

Le plus simple est une méthode statique `fromEntity()` dans le DTO :

```php
final class LivreListItem
{
    public function __construct(
        public readonly int $id,
        public readonly string $titre,
        public readonly string $auteur,
        public readonly bool $disponible,
    ) {}

    public static function fromEntity(Livre $l): self
    {
        return new self(
            id: $l->getId(),
            titre: $l->getTitre(),
            auteur: $l->getAuteur()->getNom(),
            disponible: $l->isDisponible(),
        );
    }
}
```

Dans le contrôleur :

```php
return $this->json(array_map(LivreListItem::fromEntity(...), $repo->findAll()));
```

Quand la transformation a besoin de services (traduire un libellé, générer une URL d'image), on la met plutôt dans une classe dédiée, un **mapper** (`LivreMapper`), injectée dans le contrôleur.
"""),
    L("Aplatir, formater, calculer", r"""
Le DTO de sortie n'est pas une copie de l'entité : il est taillé pour l'écran qui va l'afficher. Trois opérations reviennent tout le temps :

- **Aplatir** les relations : `auteur: $l->getAuteur()->getNom()` au lieu de l'objet `Auteur`. Le front reçoit une chaîne, pas un objet à fouiller, et aucune boucle n'est possible.
- **Formater** : dates en texte (`->format(DATE_ATOM)` ou `'Y-m-d'` pour une date sans heure), montants en centimes (entiers) plutôt qu'en `float`.
- **Calculer** : un nombre (`nbEmprunts: count($l->getEmprunts())`), un booléen (`enRetard`), un extrait (`mb_substr($contenu, 0, 140)`). Le front n'a pas à refaire ces calculs.

Une seule exception à « pas d'objets dans un DTO » : un DTO peut contenir **d'autres DTO**. Par exemple `LivreDetail` peut contenir `public readonly AuteurOutput $auteur` si l'écran de détail a besoin de plusieurs infos sur l'auteur.
"""),
    L("Liste ≠ détail", r"""
Une page liste affiche 50 livres ; une page détail en affiche un seul, avec tout. Envoyer le détail complet dans la liste, c'est gaspiller de la bande passante (50 résumés de 2 000 caractères) et parfois du temps de base de données.

On fait donc **deux DTO** :

- `LivreListItem` : le minimum pour une ligne de liste.
- `LivreDetail` : tout ce que montre la page détail.

Côté routes :

```php
#[Route('/api/livres', methods: ['GET'])]
public function index(LivreRepository $repo): JsonResponse
{
    return $this->json(array_map(LivreListItem::fromEntity(...), $repo->findAll()));
}

#[Route('/api/livres/{id}', methods: ['GET'])]
public function show(Livre $livre): JsonResponse    // Symfony charge le livre, 404 sinon
{
    return $this->json(LivreDetail::fromEntity($livre));
}
```

Dans `show(Livre $livre)`, Symfony (l'*EntityValueResolver*) prend l'`{id}` de l'URL, appelle `find()` et répond 404 tout seul si le livre n'existe pas.
"""),
    L("Ce que reçoit le front", r"""
`$this->json($dto)` sérialise les propriétés publiques du DTO. Pour un `LivreListItem` :

```json
{"id": 2, "titre": "Dune", "auteur": "Frank Herbert", "disponible": false}
```

Côté React, c'est exactement ce que tu reçois dans `res.data` avec axios, et ce que décrit ton type TypeScript `Livre`. Les noms des propriétés PHP **sont** les clés JSON : choisis-les pour le front (camelCase), pas pour la base.

Dernier conseil : renvoie toujours des **types stables**. Un champ qui vaut parfois `"12"` (chaîne) et parfois `12` (nombre), ou parfois absent, oblige le front à se méfier de tout. Avec des propriétés typées (`int`, `?string`), le DTO te le garantit.
"""),
  ],
  recap=[
    "Entité → DTO à **un seul endroit** : `fromEntity()` dans le DTO, ou un mapper si on a besoin de services.",
    "Aplatir les relations, formater les dates, calculer ce dont l'écran a besoin.",
    "Un DTO peut contenir d'autres DTO, jamais d'entités.",
    "Deux DTO : un léger pour les listes, un complet pour le détail.",
    "`show(Livre $livre)` : Symfony charge l'entité de l'`{id}` et répond 404 tout seul.",
    "Les propriétés du DTO **sont** les clés JSON que reçoit le front.",
  ],
  example=[F("src/Dto/LivreListItem.php", "php", r"""
<?php

namespace App\Dto;

use App\Entity\Livre;

final class LivreListItem
{
    public function __construct(
        public readonly int $id,
        public readonly string $titre,
        public readonly string $auteur,
        public readonly bool $disponible,
    ) {}

    public static function fromEntity(Livre $l): self
    {
        return new self(
            id: $l->getId(),
            titre: $l->getTitre(),
            auteur: $l->getAuteur()->getNom(),
            disponible: $l->isDisponible(),
        );
    }
}
"""), F("src/Dto/LivreDetail.php", "php", r"""
<?php

namespace App\Dto;

use App\Entity\Livre;

final class LivreDetail
{
    public function __construct(
        public readonly int $id,
        public readonly string $titre,
        public readonly string $auteur,
        public readonly bool $disponible,
        public readonly string $isbn,
        public readonly string $publieLe,
        public readonly int $nbEmprunts,
    ) {}

    public static function fromEntity(Livre $l): self
    {
        return new self(
            id: $l->getId(),
            titre: $l->getTitre(),
            auteur: $l->getAuteur()->getNom(),
            disponible: $l->isDisponible(),
            isbn: $l->getIsbn(),
            publieLe: $l->getPublieLe()->format('Y-m-d'),
            nbEmprunts: count($l->getEmprunts()),
        );
    }
}
"""), F("src/Controller/LivreController.php", "php", r"""
<?php

namespace App\Controller;

use App\Dto\LivreDetail;
use App\Dto\LivreListItem;
use App\Entity\Livre;
use App\Repository\LivreRepository;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\Routing\Attribute\Route;

final class LivreController extends AbstractController
{
    #[Route('/api/livres', methods: ['GET'])]
    public function index(LivreRepository $repo): JsonResponse
    {
        return $this->json(array_map(LivreListItem::fromEntity(...), $repo->findAll()));
    }

    #[Route('/api/livres/{id}', methods: ['GET'])]
    public function show(Livre $livre): JsonResponse
    {
        return $this->json(LivreDetail::fromEntity($livre));
    }
}
""")],
  notes=["`LivreListItem` : 4 champs, de quoi afficher une ligne de liste.",
         "`LivreDetail` reprend ces champs et ajoute ce que montre la page détail, dont un champ **calculé** (`nbEmprunts`).",
         "Le contrôleur ne fait que choisir le bon DTO ; aucune transformation n'y est écrite.",
         "`show(Livre $livre)` : pas de `find()` ni de 404 à écrire, Symfony s'en charge."],
  td1=dict(path="LivreController.php",
    files=[BIBLIO, F("LivreController.php", "php", r"""
<?php
final class LivreListItem
{
    // à toi
}

final class LivreDetail
{
    // à toi
}

final class LivreController extends AbstractController
{
    // à toi : GET /api/livres et GET /api/livres/{id}
}

App::$entities[Livre::class] = fn(int $id) => App::get(LivreRepository::class)->find($id);
App::request('GET', '/api/livres');
App::request('GET', '/api/livres/2');
""")],
    solution=[F("LivreController.php", "php", r"""
<?php
final class LivreListItem
{
    public function __construct(
        public readonly int $id,
        public readonly string $titre,
        public readonly string $auteur,
        public readonly bool $disponible,
    ) {}

    public static function fromEntity(Livre $l): self
    {
        return new self($l->getId(), $l->getTitre(), $l->getAuteur()->getNom(), $l->isDisponible());
    }
}

final class LivreDetail
{
    public function __construct(
        public readonly int $id,
        public readonly string $titre,
        public readonly string $auteur,
        public readonly bool $disponible,
        public readonly string $isbn,
        public readonly string $publieLe,
    ) {}

    public static function fromEntity(Livre $l): self
    {
        return new self(
            $l->getId(), $l->getTitre(), $l->getAuteur()->getNom(), $l->isDisponible(),
            $l->getIsbn(), $l->getPublieLe()->format('Y-m-d'),
        );
    }
}

final class LivreController extends AbstractController
{
    #[Route('/api/livres', methods: ['GET'])]
    public function list(LivreRepository $repo): JsonResponse
    {
        return $this->json(array_map(LivreListItem::fromEntity(...), $repo->findAll()));
    }

    #[Route('/api/livres/{id}', methods: ['GET'])]
    public function show(Livre $livre): JsonResponse
    {
        return $this->json(LivreDetail::fromEntity($livre));
    }
}

App::$entities[Livre::class] = fn(int $id) => App::get(LivreRepository::class)->find($id);
App::request('GET', '/api/livres');
App::request('GET', '/api/livres/2');
""")],
    run=SRUN(biblio_setup() + r"""
$l = App::request('GET', '/api/livres');
check('GET /api/livres → 200, 5 éléments', $l->status === 200 && count($l->json ?? []) === 5, (string) $l);
check('Élément de liste : id, titre, auteur, disponible', array_keys($l->json[0] ?? []) === ['id', 'titre', 'auteur', 'disponible']);
check('Pas d\'objet imbriqué (auteur est une chaîne)', is_string($l->json[0]['auteur'] ?? null));
$d = App::request('GET', '/api/livres/2');
check('GET /api/livres/2 → 200', $d->status === 200, (string) $d);
check('Détail : isbn et publieLe en Y-m-d', ($d->json['isbn'] ?? '') === '9782266320481' && ($d->json['publieLe'] ?? '') === '1965-08-01');
check('GET /api/livres/999 → 404', App::request('GET', '/api/livres/999')->status === 404);
""")),
  tds=[
    TD(2, "Emprunts en cours : champs calculés",
       "La page « Mes emprunts » a besoin d'informations qui **n'existent pas** dans l'entité : est-il en retard ? combien de jours restent ? Tu les calcules dans le DTO, en recevant la date du jour en paramètre pour que le calcul soit testable. " + SIM,
       ["`EmpruntOutput` : `id`, `livre` (titre), `rendreLe` (Y-m-d), `joursRestants` (int, négatif si en retard), `enRetard` (bool)",
        "`EmpruntOutput::fromEntity(Emprunt $e, \\DateTimeImmutable $today)`",
        "`GET /api/emprunts` renvoie les emprunts de tous les livres (utilise `getEmprunts()` de chaque livre), triés par `rendreLe` croissant",
        "Le contrôleur fixe `$today` à partir de `new \\DateTimeImmutable('today')`"],
       [BIBLIO, F("EmpruntController.php", "php", r"""
<?php
final class EmpruntOutput
{
    // à toi
}

final class EmpruntController extends AbstractController
{
    public function __construct(private LivreRepository $livres) {}

    // à toi : GET /api/emprunts
}

App::request('GET', '/api/emprunts');
""")],
       ["Jours entre deux dates : `(int) $today->diff($e->getRendreLe())->format('%r%a')` (`%r` ajoute le signe moins).",
        "Récupérer tous les emprunts : `array_merge(...array_map(fn(Livre $l) => $l->getEmprunts(), $this->livres->findAll()))`.",
        "Trier : `usort($emprunts, fn($a, $b) => $a->getRendreLe() <=> $b->getRendreLe())`."],
       [F("EmpruntController.php", "php", r"""
<?php
final class EmpruntOutput
{
    public function __construct(
        public readonly int $id,
        public readonly string $livre,
        public readonly string $rendreLe,
        public readonly int $joursRestants,
        public readonly bool $enRetard,
    ) {}

    public static function fromEntity(Emprunt $e, \DateTimeImmutable $today): self
    {
        $jours = (int) $today->diff($e->getRendreLe())->format('%r%a');
        return new self(
            id: $e->getId(),
            livre: $e->getLivre()->getTitre(),
            rendreLe: $e->getRendreLe()->format('Y-m-d'),
            joursRestants: $jours,
            enRetard: $jours < 0,
        );
    }
}

final class EmpruntController extends AbstractController
{
    public function __construct(private LivreRepository $livres) {}

    #[Route('/api/emprunts', methods: ['GET'])]
    public function index(): JsonResponse
    {
        $today = new \DateTimeImmutable('today');
        $emprunts = array_merge(...array_map(fn(Livre $l) => $l->getEmprunts(), $this->livres->findAll()));
        usort($emprunts, fn(Emprunt $a, Emprunt $b) => $a->getRendreLe() <=> $b->getRendreLe());
        return $this->json(array_map(fn(Emprunt $e) => EmpruntOutput::fromEntity($e, $today), $emprunts));
    }
}

App::request('GET', '/api/emprunts');
""")],
       ["Un emprunt dont la date est passée a `enRetard: true` et des jours négatifs",
        "La liste est triée par date de retour"],
       run=SRUN(biblio_setup() + r"""
$m = new Membre(1, 'ana', 'ana@x.fr');
$__repo->find(1)->emprunter($m, (new DateTimeImmutable('today'))->modify('-3 days'));
$__repo->find(3)->emprunter($m, (new DateTimeImmutable('today'))->modify('+10 days'));
$r = App::request('GET', '/api/emprunts');
check('GET /api/emprunts → 200, 3 emprunts', $r->status === 200 && count($r->json ?? []) === 3, (string) $r);
check('Clés : id, livre, rendreLe, joursRestants, enRetard', array_keys($r->json[0] ?? []) === ['id', 'livre', 'rendreLe', 'joursRestants', 'enRetard']);
check('Trié par date de retour (Terremer, en retard, en premier)', ($r->json[0]['livre'] ?? '') === 'Terremer');
check('Terremer : enRetard et -3 jours', ($r->json[0]['enRetard'] ?? null) === true && ($r->json[0]['joursRestants'] ?? 0) === -3);
$f = array_values(array_filter($r->json, fn($x) => $x['livre'] === 'Fondation'))[0] ?? [];
check('Fondation : 10 jours restants, pas en retard', ($f['joursRestants'] ?? 0) === 10 && ($f['enRetard'] ?? true) === false);
$e = new Emprunt(1, $__repo->find(5), $m, new DateTimeImmutable('2030-01-11'));
check('fromEntity() utilise la date reçue (testable)', EmpruntOutput::fromEntity($e, new DateTimeImmutable('2030-01-01'))->joursRestants === 10);
""")),
    TD(3, "Une sortie différente selon qui regarde",
       "Le bibliothécaire (admin) voit l'email de l'emprunteur ; un membre ordinaire ne voit que le pseudo. Au lieu de deux routes ou de `if` dans le contrôleur, tu crées un **mapper** injecté qui choisit le bon DTO, et un DTO **imbriqué** pour le membre. " + SIM,
       ["`MembreOutput` (`id`, `pseudo`) et `MembreAdminOutput` (`id`, `pseudo`, `email`)",
        "`EmpruntDetail` : `id`, `livre` (titre), `rendreLe`, `membre` (un des deux DTO ci-dessus)",
        "`EmpruntMapper::toDetail(Emprunt $e, Utilisateur $viewer): EmpruntDetail` choisit le DTO du membre selon `$viewer->estAdmin()`",
        "`GET /api/livres/{id}/emprunt` renvoie le détail de l'emprunt en cours du livre (le dernier de `getEmprunts()`) ; 404 si aucun ; 401 si personne n'est connecté (`#[CurrentUser]`)",
        "Le contrôleur reçoit le mapper par injection et ne contient pas de `if` sur le rôle"],
       [BIBLIO, F("utilisateur.php", "php", r"""
<?php
// ---- Fourni : l'utilisateur connecté ----
final class Utilisateur
{
    public function __construct(public readonly string $nom, private array $roles = ['ROLE_USER']) {}
    public function estAdmin(): bool { return in_array('ROLE_ADMIN', $this->roles, true); }
}
"""), F("EmpruntDetail.php", "php", r"""
<?php
// à toi : MembreOutput, MembreAdminOutput, EmpruntDetail, EmpruntMapper

final class EmpruntController extends AbstractController
{
    // à toi : GET /api/livres/{id}/emprunt
}

App::$entities[Livre::class] = fn(int $id) => App::get(LivreRepository::class)->find($id);
App::$user = new Utilisateur('Bibliothécaire', ['ROLE_ADMIN']);
App::request('GET', '/api/livres/2/emprunt');
App::$user = new Utilisateur('Ana');
App::request('GET', '/api/livres/2/emprunt');
""")],
       ["`public readonly MembreOutput|MembreAdminOutput $membre` : un type union.",
        "Le 404 : `$e = end($emprunts) ?: throw $this->createNotFoundException('Aucun emprunt');` (`end()` renvoie `false` sur un tableau vide).",
        "`#[CurrentUser] Utilisateur $viewer` : non nullable, donc 401 si personne n'est connecté."],
       [F("EmpruntDetail.php", "php", r"""
<?php
final class MembreOutput
{
    public function __construct(public readonly int $id, public readonly string $pseudo) {}
}

final class MembreAdminOutput
{
    public function __construct(public readonly int $id, public readonly string $pseudo, public readonly string $email) {}
}

final class EmpruntDetail
{
    public function __construct(
        public readonly int $id,
        public readonly string $livre,
        public readonly string $rendreLe,
        public readonly MembreOutput|MembreAdminOutput $membre,
    ) {}
}

final class EmpruntMapper
{
    public function toDetail(Emprunt $e, Utilisateur $viewer): EmpruntDetail
    {
        $m = $e->getMembre();
        $membre = $viewer->estAdmin()
            ? new MembreAdminOutput($m->getId(), $m->getPseudo(), $m->getEmail())
            : new MembreOutput($m->getId(), $m->getPseudo());

        return new EmpruntDetail($e->getId(), $e->getLivre()->getTitre(), $e->getRendreLe()->format('Y-m-d'), $membre);
    }
}

final class EmpruntController extends AbstractController
{
    public function __construct(private EmpruntMapper $mapper) {}

    #[Route('/api/livres/{id}/emprunt', methods: ['GET'])]
    public function show(Livre $livre, #[CurrentUser] Utilisateur $viewer): JsonResponse
    {
        $emprunts = $livre->getEmprunts();
        $e = end($emprunts) ?: throw $this->createNotFoundException('Aucun emprunt');
        return $this->json($this->mapper->toDetail($e, $viewer));
    }
}

App::$entities[Livre::class] = fn(int $id) => App::get(LivreRepository::class)->find($id);
App::$user = new Utilisateur('Bibliothécaire', ['ROLE_ADMIN']);
App::request('GET', '/api/livres/2/emprunt');
App::$user = new Utilisateur('Ana');
App::request('GET', '/api/livres/2/emprunt');
""")],
       ["L'admin voit `membre.email`, un membre ordinaire non",
        "Livre sans emprunt → 404 ; personne de connecté → 401"],
       run=SRUN(biblio_setup() + r"""
App::$user = new Utilisateur('Admin', ['ROLE_ADMIN']);
$a = App::request('GET', '/api/livres/2/emprunt');
check('Admin : 200', $a->status === 200, (string) $a);
check('Admin : membre.email visible', ($a->json['membre']['email'] ?? null) === 'zoe@exemple.fr');
check('Clés du détail : id, livre, rendreLe, membre', array_keys($a->json ?? []) === ['id', 'livre', 'rendreLe', 'membre']);
App::$user = new Utilisateur('Ana');
$u = App::request('GET', '/api/livres/2/emprunt');
check('Membre ordinaire : pas d\'email', $u->status === 200 && !isset($u->json['membre']['email']) && ($u->json['membre']['pseudo'] ?? '') === 'zoe', (string) $u);
check('Livre sans emprunt → 404', App::request('GET', '/api/livres/1/emprunt')->status === 404);
App::$user = null;
check('Personne de connecté → 401', App::request('GET', '/api/livres/2/emprunt')->status === 401);
check('Le mapper est une classe injectable', class_exists(EmpruntMapper::class));
""")),
  ])

# ---------------------------------------------------------------- Modifier
modif = V2(v1["dto-modifier"],
  prereq=[
    P("PUT / PATCH", "PUT **remplace** toute la ressource (tous les champs requis). PATCH en modifie **une partie** (on n'envoie que ce qui change)."),
    P("Service", "La classe qui réalise un cas d'usage (« emprunter un livre ») : elle reçoit le DTO, charge les entités, applique les règles, enregistre (parcours Architecture)."),
    P("Méthode métier", "Une méthode d'entité qui exprime une action du métier et protège ses règles : `$livre->emprunter()` plutôt que `$livre->setDisponible(false)`."),
    P("`#[CurrentUser]`", "Attribut Symfony qui donne l'utilisateur connecté en argument d'une action de contrôleur."),
    P("Exception métier", "Une exception qui porte une règle du métier (`LivreIndisponible`). Avec `#[WithHttpStatus(409)]`, Symfony la transforme en réponse HTTP."),
  ],
  diagram=D(
    nodes=[
      N("http", 0, 0, "PATCH /api/articles/7", "{\"titre\": \"…\"}", kind="doc", color="accent"),
      N("ctrl", 1, 0, "Contrôleur", "HTTP → DTO", kind="pill"),
      N("svc", 2, 0, "Service", "modifier($article, $in)"),
      N("ent", 3, 0, "Entité", "$article->modifier()\naccepte ou refuse", color="warn"),
      N("db", 2, 1, "flush()", "UPDATE article …", kind="db", color="muted"),
      N("out", 1, 1, "ArticleOutput", "fromEntity()", kind="file", color="good"),
      N("res", 0, 1, "200", "JSON", kind="doc", color="good"),
    ],
    edges=[E("http", "ctrl"), E("ctrl", "svc", "DTO"), E("svc", "ent", "méthode métier"), E("svc", "db"), E("db", "out", color="good"), E("out", "res", color="good")],
    caption="Le DTO transporte la demande ; le service orchestre ; l'entité décide si le changement est permis ; on renvoie un DTO de sortie."),
  lessons=[
    L("Du DTO à l'entité : qui fait quoi", r"""
Le contrôleur a reçu un DTO valide. Comment arrive-t-on à une entité créée ou modifiée en base ? En séparant les rôles :

- Le **contrôleur** : HTTP uniquement. Il reçoit le DTO, appelle le service, renvoie la réponse.
- Le **service** : le cas d'usage. Il charge ce qu'il faut, appelle les méthodes de l'entité, enregistre (`persist`, `flush`).
- L'**entité** : les règles. Elle accepte ou refuse le changement.

```php
// Création : le constructeur de l'entité reçoit les valeurs du DTO
$article = new Article($input->titre, $input->contenu, $auteur);
$this->em->persist($article);
$this->em->flush();

// Modification : une méthode métier de l'entité
$article->modifier($input->titre, $input->contenu);
$this->em->flush();          // l'article vient de la base : pas de persist
```

Pourquoi ne pas écrire `$article->setTitre($input->titre)` dans le contrôleur ? Parce qu'il n'y aurait plus d'endroit pour les règles (« un article publié ne peut plus changer de titre »), et que le contrôleur grossirait à chaque nouveau champ.
"""),
    L("Créer : le constructeur fait le travail", r"""
Pour une création, le DTO d'entrée apporte ce que le client choisit, et le service ajoute ce qu'il ne choisit pas :

```php
public function creer(CreateArticleInput $in, User $auteur): Article
{
    $article = new Article(
        titre: $in->titre,
        contenu: $in->contenu,
        auteur: $auteur,            // l'utilisateur connecté, pas une valeur du JSON
    );
    $this->em->persist($article);
    $this->em->flush();
    return $article;
}
```

Le contrôleur fournit l'utilisateur connecté avec `#[CurrentUser]` et renvoie **201** avec le DTO de sortie (l'`id` est maintenant connu).

Ne fais jamais d'héritage entre un DTO et une entité (`class Article extends ArticleInput`) : ils changeraient pour des raisons différentes et finiraient par se gêner.
"""),
    L("Modifier : PUT ou PATCH ?", r"""
- **PUT** : le client envoie la ressource **complète**. Tous les champs sont obligatoires, comme à la création. Simple à valider (le même genre de DTO), mais le front doit tout renvoyer, même ce qu'il ne modifie pas.
- **PATCH** : le client n'envoie **que ce qui change**. Le DTO a des champs **nullables** : `null` veut dire « pas fourni, ne touche pas ».

```php
final class UpdateArticleInput
{
    public function __construct(
        #[Assert\Length(min: 5, max: 180)]
        public readonly ?string $titre = null,    // null = inchangé
        public readonly ?string $contenu = null,
    ) {}
}
```

Et dans le service :

```php
$article->modifier(
    titre: $in->titre ?? $article->getTitre(),
    contenu: $in->contenu ?? $article->getContenu(),
);
```

Les contraintes ignorent `null` (sauf `NotBlank`/`NotNull`) : un PATCH sans titre passe, un PATCH avec un titre trop court est refusé. Si tu as besoin de distinguer « pas envoyé » de « mettre à vide », tu dois exclure `NotBlank` des champs qu'on peut vider et gérer ce cas explicitement.
"""),
    L("Les actions qui ne sont pas des modifications de champs", r"""
Toutes les mutations ne sont pas « changer un champ ». Emprunter un livre, publier un article, annuler une commande : ce sont des **actions** avec leurs règles. On leur donne une route dédiée, souvent un POST sur une sous-ressource :

```
POST /api/emprunts                 {"livreId": 3, "rendreLe": "2026-12-01"}
POST /api/articles/7/publication   (pas de corps)
POST /api/commandes/12/annulation  {"motif": "..."}
```

Plutôt que `PATCH /api/articles/7 {"publie": true}`, qui laisserait croire qu'on peut écrire n'importe quoi dans `publie`.

Les refus de l'entité passent par des **exceptions métier**. Avec `#[WithHttpStatus(409)]` sur la classe d'exception, Symfony renvoie le bon statut sans `try/catch` dans le contrôleur :

```php
#[WithHttpStatus(409)]
final class LivreIndisponible extends \DomainException {}
```

Le front reçoit alors un 409 qu'il sait afficher (« Déjà emprunté », parcours Données & API).
"""),
  ],
  recap=[
    "Contrôleur : HTTP. Service : le cas d'usage (charger, appeler l'entité, flush). Entité : les règles.",
    "Création : constructeur de l'entité avec les valeurs du DTO + ce que le serveur décide (auteur, date).",
    "Modification : méthode métier de l'entité, puis `flush()` (pas de `persist`).",
    "PUT = tout renvoyer ; PATCH = champs nullables, `null` = inchangé (`$in->titre ?? $actuel`).",
    "Actions métier → routes dédiées (`POST /articles/7/publication`) ; refus → exceptions avec `#[WithHttpStatus]`.",
  ],
  example=[F("src/Dto/UpdateArticleInput.php", "php", r"""
<?php

namespace App\Dto;

use Symfony\Component\Validator\Constraints as Assert;

final class UpdateArticleInput
{
    public function __construct(
        #[Assert\Length(min: 5, max: 180)]
        public readonly ?string $titre = null,
        public readonly ?string $contenu = null,
    ) {}
}
"""), F("src/Service/ArticleService.php", "php", r"""
<?php

namespace App\Service;

use App\Dto\CreateArticleInput;
use App\Dto\UpdateArticleInput;
use App\Entity\Article;
use App\Entity\User;
use Doctrine\ORM\EntityManagerInterface;

final class ArticleService
{
    public function __construct(private EntityManagerInterface $em) {}

    public function creer(CreateArticleInput $in, User $auteur): Article
    {
        $article = new Article($in->titre, $in->contenu, $auteur);
        $this->em->persist($article);
        $this->em->flush();
        return $article;
    }

    public function modifier(Article $article, UpdateArticleInput $in): Article
    {
        $article->modifier(
            titre: $in->titre ?? $article->getTitre(),
            contenu: $in->contenu ?? $article->getContenu(),
        );
        $this->em->flush();
        return $article;
    }
}
"""), F("src/Controller/ArticleController.php", "php", r"""
<?php

namespace App\Controller;

use App\Dto\ArticleOutput;
use App\Dto\CreateArticleInput;
use App\Dto\UpdateArticleInput;
use App\Entity\Article;
use App\Entity\User;
use App\Service\ArticleService;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpKernel\Attribute\MapRequestPayload;
use Symfony\Component\Routing\Attribute\Route;
use Symfony\Component\Security\Http\Attribute\CurrentUser;

final class ArticleController extends AbstractController
{
    public function __construct(private ArticleService $articles) {}

    #[Route('/api/articles', methods: ['POST'])]
    public function create(#[MapRequestPayload] CreateArticleInput $input, #[CurrentUser] User $user): JsonResponse
    {
        return $this->json(ArticleOutput::fromEntity($this->articles->creer($input, $user)), 201);
    }

    #[Route('/api/articles/{id}', methods: ['PATCH'])]
    public function update(Article $article, #[MapRequestPayload] UpdateArticleInput $input): JsonResponse
    {
        return $this->json(ArticleOutput::fromEntity($this->articles->modifier($article, $input)));
    }
}
""")],
  notes=["`UpdateArticleInput` : tous les champs sont nullables, c'est un DTO de PATCH.",
         "`ArticleService::modifier()` garde la valeur actuelle quand le champ n'est pas fourni (`??`).",
         "Le contrôleur ne touche à aucune entité : il passe le DTO au service et renvoie un DTO de sortie.",
         "L'auteur vient de `#[CurrentUser]`, jamais du JSON."],
  td1=dict(path="Emprunt.php",
    files=[BIBLIO, F("Emprunt.php", "php", r"""
<?php
final class EmpruntInput
{
    // à toi : livreId (positif), rendreLe (date Y-m-d)
}

#[WithHttpStatus(404)] final class LivreIntrouvable extends \DomainException {}
#[WithHttpStatus(422)] final class DateRetourInvalide extends \DomainException {}

final class EmpruntService
{
    public function __construct(private LivreRepository $livres) {}

    public function emprunter(EmpruntInput $in, Membre $membre): Emprunt
    {
        // à toi : livre introuvable → 404 ; date pas dans le futur → 422 ; puis $livre->emprunter(...)
    }
}

final class EmpruntOutput
{
    public function __construct(public readonly int $id, public readonly string $livre, public readonly string $rendreLe) {}
}

final class EmpruntController extends AbstractController
{
    // à toi : POST /api/emprunts → 201
}

App::$user = new Membre(7, 'ana', 'ana@exemple.fr');
App::request('POST', '/api/emprunts', ['livreId' => 3, 'rendreLe' => '2030-01-15']);
App::request('POST', '/api/emprunts', ['livreId' => 3, 'rendreLe' => '2030-01-15']);
""")],
    solution=[F("Emprunt.php", "php", r"""
<?php
final class EmpruntInput
{
    public function __construct(
        #[Assert\Positive] public readonly int $livreId = 0,
        #[Assert\NotBlank, Assert\Date] public readonly string $rendreLe = '',
    ) {}
}

#[WithHttpStatus(404)] final class LivreIntrouvable extends \DomainException {}
#[WithHttpStatus(422)] final class DateRetourInvalide extends \DomainException {}

final class EmpruntService
{
    public function __construct(private LivreRepository $livres) {}

    public function emprunter(EmpruntInput $in, Membre $membre): Emprunt
    {
        $livre = $this->livres->find($in->livreId) ?? throw new LivreIntrouvable('Livre introuvable');
        $retour = new \DateTimeImmutable($in->rendreLe);
        if ($retour <= new \DateTimeImmutable('today')) {
            throw new DateRetourInvalide('La date de retour doit être dans le futur');
        }
        return $livre->emprunter($membre, $retour);    // LivreIndisponible (409) si déjà emprunté
    }
}

final class EmpruntOutput
{
    public function __construct(public readonly int $id, public readonly string $livre, public readonly string $rendreLe) {}
}

final class EmpruntController extends AbstractController
{
    #[Route('/api/emprunts', methods: ['POST'])]
    public function create(#[MapRequestPayload] EmpruntInput $input, #[CurrentUser] Membre $membre, EmpruntService $service): JsonResponse
    {
        $e = $service->emprunter($input, $membre);
        return $this->json(new EmpruntOutput($e->getId(), $e->getLivre()->getTitre(), $e->getRendreLe()->format('Y-m-d')), 201);
    }
}

App::$user = new Membre(7, 'ana', 'ana@exemple.fr');
App::request('POST', '/api/emprunts', ['livreId' => 3, 'rendreLe' => '2030-01-15']);
App::request('POST', '/api/emprunts', ['livreId' => 3, 'rendreLe' => '2030-01-15']);
""")],
    run=SRUN(biblio_setup() + r"""
App::$user = new Membre(7, 'ana', 'ana@exemple.fr');
$r = App::request('POST', '/api/emprunts', ['livreId' => 4, 'rendreLe' => '2031-03-01']);
check('Emprunt valide → 201', $r->status === 201, (string) $r);
check('Réponse : livre et rendreLe', ($r->json['livre'] ?? '') === 'Les Dépossédés' && ($r->json['rendreLe'] ?? '') === '2031-03-01');
check('Le livre est maintenant indisponible', $__repo->find(4)->isDisponible() === false);
check('Emprunter Dune (déjà emprunté) → 409', App::request('POST', '/api/emprunts', ['livreId' => 2, 'rendreLe' => '2031-03-01'])->status === 409);
check('Livre 99 → 404', App::request('POST', '/api/emprunts', ['livreId' => 99, 'rendreLe' => '2031-03-01'])->status === 404);
check('Date passée → 422', App::request('POST', '/api/emprunts', ['livreId' => 1, 'rendreLe' => '2020-01-01'])->status === 422);
check('Date mal formée → 422', App::request('POST', '/api/emprunts', ['livreId' => 1, 'rendreLe' => '01/02/2031'])->status === 422);
App::$user = null;
check('Sans utilisateur connecté → 401', App::request('POST', '/api/emprunts', ['livreId' => 1, 'rendreLe' => '2031-03-01'])->status === 401);
""")),
  tds=[
    TD(2, "PATCH : ne modifier que ce qui est envoyé",
       "Le front envoie seulement les champs modifiés. Il faut un DTO aux champs **nullables**, un service qui garde les valeurs actuelles pour les champs absents, et une entité qui refuse les modifications interdites. " + SIM,
       ["`Article` (fourni) a une méthode `modifier(string $titre, string $contenu)` qui refuse de changer le titre d'un article **publié** (`ArticlePublie` → 409)",
        "`UpdateArticleInput` : `titre` (`?string`, 5 à 180 caractères) et `contenu` (`?string`, au moins 10 caractères)",
        "`ArticleService::modifier()` : `null` = inchangé",
        "`PATCH /api/articles/{id}` → 200 avec `{ id, titre, contenu }`",
        "`PATCH` sans aucun champ → 200, rien ne change"],
       [F("articles.php", "php", USES + r"""
// ---- Fourni ----
#[WithHttpStatus(409)] final class ArticlePublie extends \DomainException {}

final class Article
{
    public function __construct(private int $id, private string $titre, private string $contenu, private bool $publie = false) {}
    public function getId(): int { return $this->id; }
    public function getTitre(): string { return $this->titre; }
    public function getContenu(): string { return $this->contenu; }

    public function modifier(string $titre, string $contenu): void
    {
        if ($this->publie && $titre !== $this->titre) throw new ArticlePublie('Le titre d\'un article publié ne peut plus changer');
        $this->titre = $titre;
        $this->contenu = $contenu;
    }
}

final class ArticleRepository
{
    private array $articles;
    public function __construct()
    {
        $this->articles = [
            1 => new Article(1, 'Brouillon du jour', 'Un contenu pas encore publié.'),
            2 => new Article(2, 'Les DTO expliqués', 'Un article déjà en ligne.', true),
        ];
    }
    public function find(int $id): ?Article { return $this->articles[$id] ?? null; }
}
"""), F("ArticleController.php", "php", r"""
<?php
final class UpdateArticleInput
{
    // à toi
}

final class ArticleService
{
    public function modifier(Article $a, UpdateArticleInput $in): Article
    {
        // à toi
    }
}

final class ArticleController extends AbstractController
{
    // à toi : PATCH /api/articles/{id}
}

App::$entities[Article::class] = fn(int $id) => App::get(ArticleRepository::class)->find($id);
App::request('PATCH', '/api/articles/1', ['titre' => 'Nouveau titre']);
""")],
       ["`#[Assert\\Length(min: 5, max: 180)] public readonly ?string $titre = null`",
        "Service : `$a->modifier($in->titre ?? $a->getTitre(), $in->contenu ?? $a->getContenu());`",
        "Route : `update(Article $article, #[MapRequestPayload] UpdateArticleInput $input, ArticleService $service)`."],
       [F("ArticleController.php", "php", r"""
<?php
final class UpdateArticleInput
{
    public function __construct(
        #[Assert\Length(min: 5, max: 180)] public readonly ?string $titre = null,
        #[Assert\Length(min: 10)] public readonly ?string $contenu = null,
    ) {}
}

final class ArticleService
{
    public function modifier(Article $a, UpdateArticleInput $in): Article
    {
        $a->modifier($in->titre ?? $a->getTitre(), $in->contenu ?? $a->getContenu());
        return $a;
    }
}

final class ArticleController extends AbstractController
{
    #[Route('/api/articles/{id}', methods: ['PATCH'])]
    public function update(Article $article, #[MapRequestPayload] UpdateArticleInput $input, ArticleService $service): JsonResponse
    {
        $a = $service->modifier($article, $input);
        return $this->json(['id' => $a->getId(), 'titre' => $a->getTitre(), 'contenu' => $a->getContenu()]);
    }
}

App::$entities[Article::class] = fn(int $id) => App::get(ArticleRepository::class)->find($id);
App::request('PATCH', '/api/articles/1', ['titre' => 'Nouveau titre']);
""")],
       ["Un PATCH avec seulement `titre` garde le contenu",
        "Changer le titre de l'article publié renvoie 409"],
       run=SRUN(r"""
App::reset(); $__r = App::get(ArticleRepository::class); App::$entities[Article::class] = fn(int $id) => $__r->find($id);
$r = App::request('PATCH', '/api/articles/1', ['titre' => 'Titre modifié']);
check('PATCH titre → 200', $r->status === 200, (string) $r);
check('Le titre change, le contenu reste', ($r->json['titre'] ?? '') === 'Titre modifié' && ($r->json['contenu'] ?? '') === 'Un contenu pas encore publié.');
$r2 = App::request('PATCH', '/api/articles/1', ['contenu' => 'Un tout nouveau contenu.']);
check('PATCH contenu seul : le titre reste « Titre modifié »', ($r2->json['titre'] ?? '') === 'Titre modifié');
check('PATCH vide → 200 sans changement', App::request('PATCH', '/api/articles/1', [])->json['titre'] === 'Titre modifié');
check('Titre de 3 caractères → 422', App::request('PATCH', '/api/articles/1', ['titre' => 'Abc'])->status === 422);
check('Article publié : changer le titre → 409', App::request('PATCH', '/api/articles/2', ['titre' => 'Autre titre'])->status === 409);
check('Article publié : changer seulement le contenu → 200', App::request('PATCH', '/api/articles/2', ['contenu' => 'Correction d\'une coquille.'])->status === 200);
check('Article 9 → 404', App::request('PATCH', '/api/articles/9', ['titre' => 'Peu importe'])->status === 404);
""")),
    TD(3, "Une action métier : publier un article",
       "Publier n'est pas « modifier un champ » : c'est une **action** avec ses règles (contenu assez long, pas déjà publié, seul l'auteur peut publier) et ses effets (date de publication). Tu crées une route dédiée, une méthode métier dans l'entité, et des exceptions avec le bon statut. " + SIM,
       ["Entité `Article` : `publier(Utilisateur $par, \\DateTimeImmutable $le)` — `PasLAuteur` (403) si `$par` n'est pas l'auteur, `DejaPublie` (409), `ContenuTropCourt` (422, moins de 50 caractères)",
        "`POST /api/articles/{id}/publication` (sans corps) → 200 avec `{ id, publieLe }` (format Y-m-d)",
        "L'utilisateur vient de `#[CurrentUser]`",
        "La date vient d'un service `Horloge` injecté (pour les tests) ; fournis `HorlogeSysteme` qui renvoie `new \\DateTimeImmutable('today')`",
        "Le contrôleur ne contient ni `if` ni `try/catch`"],
       [F("publication.php", "php", USES + r"""
// ---- Fourni ----
final class Utilisateur
{
    public function __construct(public readonly int $id, public readonly string $nom) {}
}

interface Horloge { public function aujourdhui(): \DateTimeImmutable; }
"""), F("Article.php", "php", r"""
<?php
// à toi : exceptions PasLAuteur (403), DejaPublie (409), ContenuTropCourt (422)

final class Article
{
    private ?\DateTimeImmutable $publieLe = null;

    public function __construct(private int $id, private Utilisateur $auteur, private string $contenu) {}

    public function getId(): int { return $this->id; }
    public function getPublieLe(): ?\DateTimeImmutable { return $this->publieLe; }

    // à toi : publier(Utilisateur $par, \DateTimeImmutable $le)
}

final class ArticleRepository
{
    public array $articles;
    public function __construct()
    {
        $ana = new Utilisateur(1, 'Ana');
        $this->articles = [
            1 => new Article(1, $ana, str_repeat('Un contenu suffisamment long. ', 3)),
            2 => new Article(2, $ana, 'Trop court.'),
        ];
    }
    public function find(int $id): ?Article { return $this->articles[$id] ?? null; }
}

// à toi : HorlogeSysteme, PublicationController

App::$entities[Article::class] = fn(int $id) => App::get(ArticleRepository::class)->find($id);
App::$user = new Utilisateur(1, 'Ana');
App::request('POST', '/api/articles/1/publication');
App::request('POST', '/api/articles/1/publication');
""")],
       ["Comparer l'auteur par id : `$par->id !== $this->auteur->id`.",
        "Vérifie dans l'ordre : auteur, déjà publié, longueur. Un utilisateur non autorisé ne doit rien apprendre d'autre.",
        "Le contrôleur reçoit `Horloge $horloge` ; avec une seule implémentation, l'autowiring la trouve (dans le simulateur, enregistre-la avec `App::set(Horloge::class, new HorlogeSysteme())` si besoin)."],
       [F("Article.php", "php", r"""
<?php
#[WithHttpStatus(403)] final class PasLAuteur extends \DomainException {}
#[WithHttpStatus(409)] final class DejaPublie extends \DomainException {}
#[WithHttpStatus(422)] final class ContenuTropCourt extends \DomainException {}

final class Article
{
    private ?\DateTimeImmutable $publieLe = null;

    public function __construct(private int $id, private Utilisateur $auteur, private string $contenu) {}

    public function getId(): int { return $this->id; }
    public function getPublieLe(): ?\DateTimeImmutable { return $this->publieLe; }

    public function publier(Utilisateur $par, \DateTimeImmutable $le): void
    {
        if ($par->id !== $this->auteur->id) throw new PasLAuteur('Seul l\'auteur peut publier cet article');
        if ($this->publieLe !== null) throw new DejaPublie('Article déjà publié');
        if (mb_strlen($this->contenu) < 50) throw new ContenuTropCourt('Le contenu doit faire au moins 50 caractères');
        $this->publieLe = $le;
    }
}

final class ArticleRepository
{
    public array $articles;
    public function __construct()
    {
        $ana = new Utilisateur(1, 'Ana');
        $this->articles = [
            1 => new Article(1, $ana, str_repeat('Un contenu suffisamment long. ', 3)),
            2 => new Article(2, $ana, 'Trop court.'),
        ];
    }
    public function find(int $id): ?Article { return $this->articles[$id] ?? null; }
}

final class HorlogeSysteme implements Horloge
{
    public function aujourdhui(): \DateTimeImmutable { return new \DateTimeImmutable('today'); }
}

final class PublicationController extends AbstractController
{
    #[Route('/api/articles/{id}/publication', methods: ['POST'])]
    public function publier(Article $article, #[CurrentUser] Utilisateur $user, Horloge $horloge): JsonResponse
    {
        $article->publier($user, $horloge->aujourdhui());
        return $this->json(['id' => $article->getId(), 'publieLe' => $article->getPublieLe()->format('Y-m-d')]);
    }
}

App::set(Horloge::class, new HorlogeSysteme());
App::$entities[Article::class] = fn(int $id) => App::get(ArticleRepository::class)->find($id);
App::$user = new Utilisateur(1, 'Ana');
App::request('POST', '/api/articles/1/publication');
App::request('POST', '/api/articles/1/publication');
""")],
       ["Chaque refus a son statut : 403, 409, 422",
        "La date de publication vient de l'horloge injectée"],
       run=SRUN(r"""
App::reset(); $__r = App::get(ArticleRepository::class); App::$entities[Article::class] = fn(int $id) => $__r->find($id);
App::set(Horloge::class, new class implements Horloge { public function aujourdhui(): DateTimeImmutable { return new DateTimeImmutable('2030-06-15'); } });
App::$user = new Utilisateur(2, 'Léo');
check('Pas l\'auteur → 403', App::request('POST', '/api/articles/1/publication')->status === 403);
check('L\'article n\'a pas été publié par ce refus', $__r->find(1)->getPublieLe() === null);
App::$user = new Utilisateur(1, 'Ana');
$r = App::request('POST', '/api/articles/1/publication');
check('Auteur → 200 avec publieLe = date de l\'horloge', $r->status === 200 && ($r->json['publieLe'] ?? '') === '2030-06-15', (string) $r);
check('Publier deux fois → 409', App::request('POST', '/api/articles/1/publication')->status === 409);
check('Contenu trop court → 422', App::request('POST', '/api/articles/2/publication')->status === 422);
App::$user = null;
check('Non connecté → 401', App::request('POST', '/api/articles/2/publication')->status === 401);
check('La route n\'accepte pas GET (405)', App::request('GET', '/api/articles/1/publication')->status === 405);
""")),
  ])

# ---------------------------------------------------------------- Query string
qs = V2(v1["dto-query"],
  prereq=[
    P("Query string", "La partie de l'URL après `?` : `/api/livres?q=dune&page=2`. Des paires `clé=valeur` séparées par `&`, toujours des **chaînes** à l'arrivée."),
    P("Pagination", "Découper une longue liste en pages : `page` (numéro) et `parPage` (taille). Le serveur renvoie aussi le total pour que le front affiche « page 2 sur 7 »."),
    P("Paginator (Doctrine)", "La classe de Doctrine qui exécute une requête paginée et donne à la fois la page de résultats et le nombre total."),
    P("Enveloppe de réponse", "Un objet JSON qui entoure la liste avec des métadonnées : `{ items: [...], total: 134, page: 2, pages: 7 }`."),
  ],
  diagram=D(
    nodes=[
      N("url", 0, 1, "GET /api/livres", "?q=le&dispo=true&page=2", kind="doc", color="accent"),
      N("map", 1, 1, "MapQueryString", "chaînes → int/bool\n→ LivreFilters", kind="pill"),
      N("val", 2, 1, "Validator", "page ≥ 1, parPage ≤ 50", color="warn"),
      N("repo", 3, 0, "Repository", "rechercher($filtres)"),
      N("e422", 3, 2, "422", "parPage=5000", kind="doc", color="bad"),
      N("env", 4, 0, "Enveloppe", "{items, total,\npage, pages}", kind="file", color="good"),
    ],
    edges=[E("url", "map"), E("map", "val"), E("val", "repo", "valide", color="good"), E("val", "e422", "invalide", color="bad"), E("repo", "env", color="good")],
    caption="Les paramètres d'URL deviennent un DTO de filtres typé et validé ; le repository n'applique que les filtres fournis."),
  lessons=[
    L("Le problème : des paramètres d'URL non typés", r"""
Une liste a presque toujours des filtres, un tri et une pagination : `GET /api/livres?q=dune&disponible=true&page=2&parPage=20`. Les lire à la main donne :

```php
$q = $request->query->get('q');
$page = max(1, (int) $request->query->get('page', 1));
$parPage = min(100, (int) $request->query->get('parPage', 20));
$disponible = $request->query->has('disponible') ? filter_var(...) : null;
```

Tout arrive en **chaînes** (`"2"`, `"true"`), il faut convertir, mettre des valeurs par défaut, borner… et rien n'est validé de façon uniforme avec le reste de l'API.
"""),
    L("`#[MapQueryString]` : un DTO pour les filtres", r"""
Même principe que `#[MapRequestPayload]`, mais pour l'URL :

```php
final class LivreFilters
{
    public function __construct(
        #[Assert\Length(max: 50)]
        public readonly ?string $q = null,
        public readonly ?bool $disponible = null,      // null = pas de filtre
        #[Assert\Positive]
        public readonly int $page = 1,
        #[Assert\Range(min: 1, max: 50)]
        public readonly int $parPage = 20,
    ) {}
}

#[Route('/api/livres', methods: ['GET'])]
public function list(#[MapQueryString] ?LivreFilters $filtres, LivreRepository $repo): JsonResponse
{
    $filtres ??= new LivreFilters();      // aucune query string : valeurs par défaut
    ...
}
```

Symfony convertit `"2"` en `2` et `"true"` en `true` selon les types du constructeur, puis valide. Un `parPage=5000` donne un 422, comme un mauvais corps JSON.

Le paramètre est **nullable** (`?LivreFilters`) : sans aucune query string, Symfony passe `null`, d'où le `??=` pour repartir des valeurs par défaut.
"""),
    L("Des filtres optionnels, une seule méthode", r"""
Chaque filtre `null` est simplement **ignoré** par le repository. Avec le QueryBuilder (parcours Doctrine) :

```php
public function rechercher(LivreFilters $f): array
{
    $qb = $this->createQueryBuilder('l')->leftJoin('l.auteur', 'a')->addSelect('a');
    if ($f->q) {
        $qb->andWhere('LOWER(l.titre) LIKE :q')->setParameter('q', '%' . mb_strtolower($f->q) . '%');
    }
    if ($f->disponible !== null) {
        $qb->andWhere('l.disponible = :d')->setParameter('d', $f->disponible);
    }
    $qb->orderBy('l.titre', 'ASC')
       ->setFirstResult(($f->page - 1) * $f->parPage)
       ->setMaxResults($f->parPage);

    $paginator = new Paginator($qb);
    return [iterator_to_array($paginator), count($paginator)];   // la page + le total
}
```

Attention à `$f->disponible !== null` et non `if ($f->disponible)` : `false` est un vrai filtre (« les livres empruntés »), différent de « pas de filtre ».

Pour le **tri**, n'insère jamais la valeur reçue dans la requête (`orderBy($f->tri)`) : valide-la avec `Choice` et fais correspondre chaque valeur autorisée à un tri précis.
"""),
    L("Une réponse paginée exploitable", r"""
Renvoyer seulement la page ne suffit pas : le front doit savoir combien il y a de pages pour afficher la navigation. On renvoie une **enveloppe** :

```json
{
  "items": [ {"id": 3, "titre": "Fondation", ...}, ... ],
  "total": 134,
  "page": 2,
  "parPage": 20,
  "pages": 7
}
```

`pages = ceil(total / parPage)`, avec un minimum de 1 (une liste vide a quand même une page).

Côté React, axios construit la query string pour toi : `api.get('/livres', { params: { q, page, disponible: true } })`, et la clé TanStack Query devient `['livres', { q, page }]` (parcours Données & API).
"""),
  ],
  recap=[
    "Les paramètres d'URL arrivent en chaînes ; `#[MapQueryString] ?LivreFilters` les convertit et les valide.",
    "Paramètre nullable + `$f ??= new LivreFilters()` quand l'URL n'a aucun paramètre.",
    "Valeurs par défaut (`page = 1`) et bornes (`Range(max: 50)`) pour protéger la base.",
    "Le repository ignore les filtres `null` ; teste `!== null` pour les booléens.",
    "Tri : liste blanche avec `Choice`, jamais la valeur brute dans la requête.",
    "Réponse en enveloppe : `{ items, total, page, parPage, pages }`.",
  ],
  example=[F("src/Dto/LivreFilters.php", "php", r"""
<?php

namespace App\Dto;

use Symfony\Component\Validator\Constraints as Assert;

final class LivreFilters
{
    public function __construct(
        #[Assert\Length(max: 50)]
        public readonly ?string $q = null,
        public readonly ?bool $disponible = null,
        #[Assert\Positive]
        public readonly int $page = 1,
        #[Assert\Range(min: 1, max: 50)]
        public readonly int $parPage = 20,
    ) {}
}
"""), F("src/Controller/LivreController.php", "php", r"""
<?php

namespace App\Controller;

use App\Dto\LivreFilters;
use App\Dto\LivreListItem;
use App\Repository\LivreRepository;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpKernel\Attribute\MapQueryString;
use Symfony\Component\Routing\Attribute\Route;

final class LivreController extends AbstractController
{
    #[Route('/api/livres', methods: ['GET'])]
    public function list(#[MapQueryString] ?LivreFilters $filtres, LivreRepository $repo): JsonResponse
    {
        $filtres ??= new LivreFilters();
        [$livres, $total] = $repo->rechercher($filtres);

        return $this->json([
            'items' => array_map(LivreListItem::fromEntity(...), $livres),
            'total' => $total,
            'page' => $filtres->page,
            'parPage' => $filtres->parPage,
            'pages' => max(1, (int) ceil($total / $filtres->parPage)),
        ]);
    }
}
"""), F("echanges.http", "plaintext", r"""
GET /api/livres
-> 200 {"items": [...20 livres...], "total": 134, "page": 1, "parPage": 20, "pages": 7}

GET /api/livres?q=dune&disponible=false
-> 200 {"items": [{"id": 2, "titre": "Dune", "auteur": "Frank Herbert", "disponible": false}], "total": 1, ...}

GET /api/livres?parPage=5000
-> 422 {"violations": [{"propertyPath": "parPage", "title": "Cette valeur doit être comprise entre 1 et 50."}]}
""")],
  notes=["`LivreFilters` : tout est optionnel, avec des valeurs par défaut sûres.",
         "Le contrôleur ne lit jamais `$request->query` : il reçoit un objet typé.",
         "`pages` est calculé côté serveur, avec un minimum de 1.",
         "`?disponible=false` est un vrai filtre ; l'absence du paramètre veut dire « tous »."],
  td1=dict(path="CatalogueController.php",
    files=[BIBLIO, F("CatalogueController.php", "php", r"""
<?php
final class LivreFilters
{
    // à toi : q, disponible, page, parPage (max 50)
}

final class Recherche
{
    /** Le filtrage en mémoire remplace ici le QueryBuilder. @return array{0: Livre[], 1: int} */
    public function rechercher(array $livres, LivreFilters $f): array
    {
        // à toi : filtrer (q sur le titre, insensible à la casse ; disponible si non null), puis découper la page
    }
}

final class CatalogueController extends AbstractController
{
    // à toi : GET /api/livres → { items, total, page, pages }
}

App::request('GET', '/api/livres?q=les&parPage=1&page=2');
App::request('GET', '/api/livres?disponible=false');
""")],
    solution=[F("CatalogueController.php", "php", r"""
<?php
final class LivreFilters
{
    public function __construct(
        #[Assert\Length(max: 50)] public readonly ?string $q = null,
        public readonly ?bool $disponible = null,
        #[Assert\Positive] public readonly int $page = 1,
        #[Assert\Range(min: 1, max: 50)] public readonly int $parPage = 20,
    ) {}
}

final class Recherche
{
    /** @return array{0: Livre[], 1: int} */
    public function rechercher(array $livres, LivreFilters $f): array
    {
        if ($f->q) {
            $livres = array_filter($livres, fn(Livre $l) => str_contains(mb_strtolower($l->getTitre()), mb_strtolower($f->q)));
        }
        if ($f->disponible !== null) {
            $livres = array_filter($livres, fn(Livre $l) => $l->isDisponible() === $f->disponible);
        }
        $livres = array_values($livres);
        return [array_slice($livres, ($f->page - 1) * $f->parPage, $f->parPage), count($livres)];
    }
}

final class CatalogueController extends AbstractController
{
    #[Route('/api/livres', methods: ['GET'])]
    public function list(#[MapQueryString] ?LivreFilters $f, LivreRepository $repo, Recherche $recherche): JsonResponse
    {
        $f ??= new LivreFilters();
        [$livres, $total] = $recherche->rechercher($repo->findAll(), $f);
        return $this->json([
            'items' => array_map(fn(Livre $l) => ['id' => $l->getId(), 'titre' => $l->getTitre(), 'disponible' => $l->isDisponible()], $livres),
            'total' => $total,
            'page' => $f->page,
            'pages' => max(1, (int) ceil($total / $f->parPage)),
        ]);
    }
}

App::request('GET', '/api/livres?q=les&parPage=1&page=2');
App::request('GET', '/api/livres?disponible=false');
""")],
    run=SRUN(biblio_setup() + r"""
$all = App::request('GET', '/api/livres');
check('Sans filtre : 200, total 5, page 1, pages 1', $all->status === 200 && ($all->json['total'] ?? 0) === 5 && ($all->json['page'] ?? 0) === 1 && ($all->json['pages'] ?? 0) === 1, (string) $all);
$q = App::request('GET', '/api/livres?q=LES');
check('q=LES (casse ignorée) : 2 livres', ($q->json['total'] ?? 0) === 2);
$d = App::request('GET', '/api/livres?disponible=false');
check('disponible=false : seulement Dune', ($d->json['total'] ?? 0) === 1 && ($d->json['items'][0]['titre'] ?? '') === 'Dune');
$p = App::request('GET', '/api/livres?parPage=2&page=3');
check('parPage=2&page=3 : 1 élément, pages = 3', count($p->json['items'] ?? []) === 1 && ($p->json['pages'] ?? 0) === 3);
check('parPage=200 → 422', App::request('GET', '/api/livres?parPage=200')->status === 422);
check('page=0 → 422', App::request('GET', '/api/livres?page=0')->status === 422);
$none = App::request('GET', '/api/livres?q=zzz');
check('Aucun résultat : total 0, pages 1', ($none->json['total'] ?? -1) === 0 && ($none->json['pages'] ?? 0) === 1);
""")),
  tds=[
    TD(2, "Tri sûr et liens de navigation",
       "Le front veut trier la liste et recevoir directement les **URL** des pages précédente et suivante. Le paramètre de tri doit être validé par une liste blanche : jamais de valeur libre. " + SIM,
       ["Ajoute `tri` à `LivreFilters` : `Choice(['titre', '-titre', 'annee', '-annee'])`, défaut `'titre'` (`-` = décroissant)",
        "Tri appliqué avec un `match` sur les valeurs autorisées",
        "Réponse : `{ items, total, page, pages, precedente, suivante }` ; `precedente`/`suivante` sont des URL comme `/api/livres?page=1&parPage=2&tri=-annee`, ou `null` en bout de liste",
        "Les URL de navigation conservent les filtres (`tri`, `parPage`) et n'incluent pas les paramètres absents",
        "`?tri=titre;DROP` → 422"],
       [BIBLIO, F("CatalogueController.php", "php", r"""
<?php
final class LivreFilters
{
    public function __construct(
        #[Assert\Positive] public readonly int $page = 1,
        #[Assert\Range(min: 1, max: 50)] public readonly int $parPage = 20,
        // à toi : tri
    ) {}
}

final class CatalogueController extends AbstractController
{
    // à toi
}

App::request('GET', '/api/livres?tri=-annee&parPage=2&page=2');
""")],
       ["`usort($livres, match ($f->tri) { 'titre' => fn($a, $b) => strcmp($a->getTitre(), $b->getTitre()), ... })`",
        "Construire une URL : `'/api/livres?' . http_build_query(['page' => $p, 'parPage' => $f->parPage, 'tri' => $f->tri])`.",
        "`precedente` vaut `null` si `page === 1` ; `suivante` vaut `null` si `page >= pages`."],
       [F("CatalogueController.php", "php", r"""
<?php
final class LivreFilters
{
    public function __construct(
        #[Assert\Positive] public readonly int $page = 1,
        #[Assert\Range(min: 1, max: 50)] public readonly int $parPage = 20,
        #[Assert\Choice(['titre', '-titre', 'annee', '-annee'])] public readonly string $tri = 'titre',
    ) {}
}

final class CatalogueController extends AbstractController
{
    #[Route('/api/livres', methods: ['GET'])]
    public function list(#[MapQueryString] ?LivreFilters $f, LivreRepository $repo): JsonResponse
    {
        $f ??= new LivreFilters();
        $livres = $repo->findAll();
        usort($livres, match ($f->tri) {
            'titre' => fn(Livre $a, Livre $b) => strcmp($a->getTitre(), $b->getTitre()),
            '-titre' => fn(Livre $a, Livre $b) => strcmp($b->getTitre(), $a->getTitre()),
            'annee' => fn(Livre $a, Livre $b) => $a->getPublieLe() <=> $b->getPublieLe(),
            '-annee' => fn(Livre $a, Livre $b) => $b->getPublieLe() <=> $a->getPublieLe(),
        });
        $total = count($livres);
        $pages = max(1, (int) ceil($total / $f->parPage));
        $url = fn(int $p) => '/api/livres?' . http_build_query(['page' => $p, 'parPage' => $f->parPage, 'tri' => $f->tri]);

        return $this->json([
            'items' => array_map(fn(Livre $l) => ['id' => $l->getId(), 'titre' => $l->getTitre()], array_slice($livres, ($f->page - 1) * $f->parPage, $f->parPage)),
            'total' => $total,
            'page' => $f->page,
            'pages' => $pages,
            'precedente' => $f->page > 1 ? $url($f->page - 1) : null,
            'suivante' => $f->page < $pages ? $url($f->page + 1) : null,
        ]);
    }
}

App::request('GET', '/api/livres?tri=-annee&parPage=2&page=2');
""")],
       ["`-annee` met Les Dépossédés (1974) en premier",
        "Sur la dernière page, `suivante` vaut `null`"],
       run=SRUN(biblio_setup() + r"""
$r = App::request('GET', '/api/livres?tri=-annee&parPage=2&page=1');
check('-annee : Les Dépossédés (1974) en premier', ($r->json['items'][0]['titre'] ?? '') === 'Les Dépossédés', (string) $r);
check('Page 1 : precedente null', array_key_exists('precedente', $r->json ?? []) && $r->json['precedente'] === null);
check('Page 1 : suivante conserve tri et parPage', ($r->json['suivante'] ?? '') === '/api/livres?page=2&parPage=2&tri=-annee');
$last = App::request('GET', '/api/livres?tri=-annee&parPage=2&page=3');
check('Dernière page : suivante null, precedente page 2', $last->json['suivante'] === null && str_contains($last->json['precedente'] ?? '', 'page=2'));
$t = App::request('GET', '/api/livres?tri=-titre');
check('-titre : Terremer en premier', ($t->json['items'][0]['titre'] ?? '') === 'Terremer');
check('tri invalide → 422', App::request('GET', '/api/livres?tri=titre;DROP')->status === 422);
check('Défaut : tri par titre (Dune en premier)', (App::request('GET', '/api/livres')->json['items'][0]['titre'] ?? '') === 'Dune');
""")),
    TD(3, "Recherche avancée : plages de dates et listes d'ids",
       "La recherche avancée accepte une **plage d'années** et **plusieurs auteurs** (`?auteurs=1,3`). Une liste dans une query string arrive en une seule chaîne : il faut la valider (format) puis la convertir. Et une plage incohérente (`depuis` > `jusqua`) doit être refusée proprement. " + SIM,
       ["`RechercheAvancee` : `depuis` et `jusqua` (`?int`, entre 1800 et 2100), `auteurs` (`?string`, regex `/^\\d+(,\\d+)*$/`)",
        "Méthode `auteurIds(): array` dans le DTO qui transforme `\"1,3\"` en `[1, 3]` (tableau vide si `null`) : c'est la seule « logique » admise, une simple conversion",
        "`depuis > jusqua` → `PlageInvalide` (422) levée par le service de recherche",
        "Réponse : `{ filtres: { depuis, jusqua, auteurs }, items: [titres] }` ; `filtres.auteurs` est le tableau d'entiers",
        "Sans aucun paramètre, tous les livres sont renvoyés"],
       [BIBLIO, F("RechercheController.php", "php", r"""
<?php
final class RechercheAvancee
{
    // à toi
}

// à toi : PlageInvalide, RechercheService, RechercheController (GET /api/recherche)

App::request('GET', '/api/recherche?depuis=1960&auteurs=1,3');
""")],
       ["`array_map('intval', explode(',', $this->auteurs))`",
        "Filtrer par année : `(int) $l->getPublieLe()->format('Y')`.",
        "La plage se vérifie dans le service, car elle concerne **deux** champs à la fois."],
       [F("RechercheController.php", "php", r"""
<?php
final class RechercheAvancee
{
    public function __construct(
        #[Assert\Range(min: 1800, max: 2100)] public readonly ?int $depuis = null,
        #[Assert\Range(min: 1800, max: 2100)] public readonly ?int $jusqua = null,
        #[Assert\Regex('/^\d+(,\d+)*$/')] public readonly ?string $auteurs = null,
    ) {}

    /** @return int[] */
    public function auteurIds(): array
    {
        return $this->auteurs === null ? [] : array_map('intval', explode(',', $this->auteurs));
    }
}

#[WithHttpStatus(422)] final class PlageInvalide extends \DomainException {}

final class RechercheService
{
    public function __construct(private LivreRepository $livres) {}

    /** @return Livre[] */
    public function chercher(RechercheAvancee $r): array
    {
        if ($r->depuis !== null && $r->jusqua !== null && $r->depuis > $r->jusqua) {
            throw new PlageInvalide('« depuis » doit être inférieur ou égal à « jusqua »');
        }
        $ids = $r->auteurIds();
        return array_values(array_filter($this->livres->findAll(), function (Livre $l) use ($r, $ids) {
            $annee = (int) $l->getPublieLe()->format('Y');
            return ($r->depuis === null || $annee >= $r->depuis)
                && ($r->jusqua === null || $annee <= $r->jusqua)
                && ($ids === [] || in_array($l->getAuteur()->getId(), $ids, true));
        }));
    }
}

final class RechercheController extends AbstractController
{
    #[Route('/api/recherche', methods: ['GET'])]
    public function index(#[MapQueryString] ?RechercheAvancee $r, RechercheService $service): JsonResponse
    {
        $r ??= new RechercheAvancee();
        return $this->json([
            'filtres' => ['depuis' => $r->depuis, 'jusqua' => $r->jusqua, 'auteurs' => $r->auteurIds()],
            'items' => array_map(fn(Livre $l) => $l->getTitre(), $service->chercher($r)),
        ]);
    }
}

App::request('GET', '/api/recherche?depuis=1960&auteurs=1,3');
""")],
       ["`?auteurs=1,3` filtre sur Le Guin et Asimov",
        "`?depuis=1970&jusqua=1960` renvoie 422"],
       run=SRUN(biblio_setup() + r"""
$r = App::request('GET', '/api/recherche?depuis=1960&auteurs=1,3');
check('depuis=1960&auteurs=1,3 : Terremer et Les Dépossédés', $r->status === 200 && ($r->json['items'] ?? []) === ['Terremer', 'Les Dépossédés'], (string) $r);
check('filtres.auteurs est un tableau d\'entiers [1, 3]', ($r->json['filtres']['auteurs'] ?? null) === [1, 3]);
check('Sans paramètre : 5 livres', count(App::request('GET', '/api/recherche')->json['items'] ?? []) === 5);
check('jusqua=1955 : Fondation et Les Robots', (App::request('GET', '/api/recherche?jusqua=1955')->json['items'] ?? []) === ['Fondation', 'Les Robots']);
check('Plage inversée → 422', App::request('GET', '/api/recherche?depuis=1970&jusqua=1960')->status === 422);
check('auteurs=1,,3 → 422 (format)', App::request('GET', '/api/recherche?auteurs=1,,3')->status === 422);
check('auteurs=abc → 422', App::request('GET', '/api/recherche?auteurs=abc')->status === 422);
check('depuis=1500 → 422 (Range)', App::request('GET', '/api/recherche?depuis=1500')->status === 422);
check('auteurIds() sans auteurs : []', (new RechercheAvancee())->auteurIds() === []);
""")),
  ])

MODULES = [pq, entree, sortie, modif, qs]

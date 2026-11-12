from common import V2, P, L, D, N, E, LANE, F, TD, RUN
from c_doctrine_v1 import MODULES as V1
from doctrine_sim import DOCTRINE_SETUP

v1 = {m["id"]: m for m in V1}

SIM = "Le bouton Exécuter utilise un **Doctrine simulé** : il lit tes attributs `#[ORM\\...]` et affiche le SQL que Doctrine enverrait (`SQL> ...`). Les classes sont sans `namespace` pour pouvoir tourner dans le navigateur ; dans ton projet Symfony, elles seraient dans `namespace App\\Entity;`."

def SRUN(tests):
    return RUN("php", tests=tests, setup=DOCTRINE_SETUP)

# ---------------------------------------------------------------- ORM / entités
orm = V2(v1["doc-orm"],
  prereq=[
    P("Base de données relationnelle", "Des **tables** (livre, auteur…) faites de **lignes** (un livre) et de **colonnes** (titre, isbn). MySQL et PostgreSQL en sont deux."),
    P("SQL", "Le langage des bases de données : `SELECT * FROM livre WHERE id = 3`, `INSERT INTO livre (titre) VALUES ('Dune')`."),
    P("Clé primaire (id)", "La colonne qui identifie une ligne de façon unique, en général un entier auto-incrémenté par la base : 1, 2, 3…"),
    P("Attribut PHP", "Une annotation `#[...]` posée sur une classe, une propriété ou une méthode. Elle ne fait rien seule : un outil (ici Doctrine) la lit pour savoir quoi faire."),
    P("ORM", "*Object-Relational Mapper* : un outil qui traduit des objets PHP en lignes SQL, et inversement. Doctrine est l'ORM de Symfony."),
    P("Migration", "Un fichier PHP versionné qui contient le SQL pour faire évoluer la structure de la base (créer une table, ajouter une colonne). On le lance sur chaque environnement."),
  ],
  diagram=D(
    nodes=[
      N("cls", 0, 0, "class Livre", "#[ORM\\Entity]\n$titre, $isbn", kind="file"),
      N("map", 1, 0, "Mapping", "attributs lus par\nDoctrine", kind="note"),
      N("tbl", 2, 0, "Table livre", "id | titre | isbn", kind="db", color="muted"),
      N("mig", 1, 1, "Migration", "CREATE TABLE livre", kind="doc", color="warn"),
      N("obj", 0, 2, "new Livre('Dune')", "objet PHP", color="accent"),
      N("em", 1, 2, "EntityManager", "persist + flush"),
      N("row", 2, 2, "Ligne", "1 | Dune | 978…", kind="pill", color="good"),
    ],
    edges=[E("cls", "map"), E("map", "tbl", "classe → table"), E("map", "mig", "make:migration"), E("mig", "tbl", "migrate", dashed=True), E("obj", "em"), E("em", "row", "INSERT", color="good")],
    caption="En haut, la structure : la classe décrit la table, la migration la crée. En bas, les données : un objet devient une ligne."),
  lessons=[
    L("Le problème : deux mondes qui ne parlent pas la même langue", r"""
Ton code PHP manipule des **objets** : `$livre->getTitre()`, `$auteur->ecrire(...)`, des relations entre objets. La base de données stocke des **tables** : des lignes et des colonnes, reliées par des identifiants.

Sans ORM, tu écris toi-même la traduction, pour chaque classe et chaque opération :

```php
$stmt = $pdo->prepare('INSERT INTO livre (titre, isbn, publie_le) VALUES (?, ?, ?)');
$stmt->execute([$livre->getTitre(), $livre->getIsbn(), $livre->getPublieLe()->format('Y-m-d')]);
$livre->setId((int) $pdo->lastInsertId());
```

Et l'inverse pour relire : un `SELECT`, puis remplir un objet champ par champ. Multiplié par chaque entité et chaque requête, c'est long, répétitif, et une colonne renommée casse tout en silence.

**Doctrine** fait cette traduction pour toi. Tu décris **une fois** comment la classe correspond à la table (le *mapping*), et ensuite tu ne manipules que des objets.
"""),
    L("L'entité et son mapping", r"""
Une **entité** est une classe PHP dont les objets sont stockés en base. On la marque avec des attributs :

```php
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity(repositoryClass: LivreRepository::class)]   // cette classe = une table
class Livre
{
    #[ORM\Id]                       // clé primaire
    #[ORM\GeneratedValue]           // générée par la base (auto-incrément)
    #[ORM\Column]
    private ?int $id = null;

    #[ORM\Column(length: 255)]      // VARCHAR(255)
    private string $titre;

    #[ORM\Column(length: 13, unique: true)]   // VARCHAR(13) + index UNIQUE
    private string $isbn;

    #[ORM\Column(type: Types::DATE_IMMUTABLE)] // DATE
    private \DateTimeImmutable $publieLe;
}
```

Règles de traduction par défaut :

- **Nom de table** = nom de la classe en *snake_case* : `Livre` → `livre`, `LigneCommande` → `ligne_commande`. Pour changer : `#[ORM\Table(name: 'livres')]`.
- **Nom de colonne** = nom de la propriété en snake_case : `$publieLe` → `publie_le`.
- **Type SQL** déduit du type PHP : `string` → VARCHAR, `int` → INT, `bool` → BOOLEAN, `\DateTimeImmutable` → DATETIME. On précise avec `type:` quand il faut (`Types::TEXT` pour un texte long, `Types::DATE_IMMUTABLE` pour une date sans heure).
- **Nullable** : une colonne est `NOT NULL` par défaut. Pour autoriser `NULL` : `#[ORM\Column(nullable: true)]` **et** un type PHP nullable (`?string`).

Seules les propriétés qui ont un attribut de mapping (`Column`, relation…) sont stockées. Une propriété sans attribut reste purement PHP.
"""),
    L("Pourquoi `$id` vaut `null`, et pourquoi pas de setters", r"""
Avec `GeneratedValue`, c'est la **base** qui choisit l'identifiant au moment de l'INSERT. Avant ça, l'objet n'a pas d'id : d'où `private ?int $id = null`. Après `flush()`, Doctrine remplit `$id` tout seul.

Conséquence : pas de `setId()`. Personne d'autre que la base ne doit choisir l'id.

Plus généralement, **Doctrine n'a pas besoin de setters**. Pour enregistrer, il lit les propriétés directement (par réflexion, même privées). Pour recharger un objet depuis la base, il les remplit directement aussi, **sans appeler ton constructeur**. Tu es donc libre d'écrire une entité propre :

- un **constructeur** qui exige les données obligatoires (`new Livre($titre, $isbn, $date)`) ;
- des **méthodes métier** (`emprunter()`, `rendre()`) qui protègent les règles, comme dans le parcours PHP POO ;
- des getters seulement pour ce qui doit être lu.

Le `make:entity` de Symfony génère des setters pour tout : c'est pratique pour démarrer, mais supprime ceux qui ne correspondent à aucune action réelle du métier.
"""),
    L("Les migrations : faire évoluer la base", r"""
Le mapping décrit la structure **souhaitée**. La base, elle, a une structure **réelle**. Une **migration** est le script SQL qui fait passer de l'une à l'autre.

```bash
php bin/console make:migration              # compare entités et base, écrit le fichier
php bin/console doctrine:migrations:migrate # exécute les migrations pas encore jouées
```

Le fichier généré (dans `migrations/`) ressemble à :

```php
public function up(Schema $schema): void
{
    $this->addSql('CREATE TABLE livre (id INT AUTO_INCREMENT NOT NULL, titre VARCHAR(255) NOT NULL,
        isbn VARCHAR(13) NOT NULL, publie_le DATE NOT NULL, disponible TINYINT(1) NOT NULL,
        UNIQUE INDEX UNIQ_ISBN (isbn), PRIMARY KEY(id))');
}
```

Les règles d'or :

- **Relis** toujours la migration générée avant de la lancer (un renommage de propriété peut devenir « supprimer la colonne + en créer une autre » : perte de données).
- Les migrations sont **commitées** dans Git : chaque environnement (ton poste, celui d'un collègue, la production) joue les mêmes, dans le même ordre.
- Ne modifie **jamais** la base à la main : ton schéma divergerait de celui des autres.
- Ne modifie jamais une migration déjà jouée ailleurs : crée-en une nouvelle.
"""),
  ],
  recap=[
    "Une **entité** = une classe marquée `#[ORM\\Entity]` ; ses propriétés mappées deviennent des colonnes.",
    "Table et colonnes en snake_case par défaut ; type SQL déduit du type PHP ; NOT NULL par défaut.",
    "`?int $id = null` + `GeneratedValue` : la base choisit l'id au flush. Pas de `setId()`.",
    "Doctrine lit et remplit les propriétés directement : constructeur et méthodes métier libres, setters inutiles.",
    "`make:migration` puis `doctrine:migrations:migrate` ; relire, commiter, ne jamais toucher la base à la main.",
  ],
  example=[F("src/Entity/Article.php", "php", r"""
<?php

namespace App\Entity;

use App\Repository\ArticleRepository;
use Doctrine\DBAL\Types\Types;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity(repositoryClass: ArticleRepository::class)]
class Article
{
    #[ORM\Id]
    #[ORM\GeneratedValue]
    #[ORM\Column]
    private ?int $id = null;

    #[ORM\Column(length: 180)]
    private string $titre;

    #[ORM\Column(type: Types::TEXT)]
    private string $contenu;

    #[ORM\Column]
    private bool $publie = false;

    #[ORM\Column]
    private \DateTimeImmutable $creeLe;

    public function __construct(string $titre, string $contenu)
    {
        $this->titre = $titre;
        $this->contenu = $contenu;
        $this->creeLe = new \DateTimeImmutable();
    }

    public function getId(): ?int { return $this->id; }
    public function getTitre(): string { return $this->titre; }

    public function publier(): void
    {
        $this->publie = true;
    }
}
"""), F("migrations/Version20261112093000.php", "php", r"""
<?php

declare(strict_types=1);

namespace DoctrineMigrations;

use Doctrine\DBAL\Schema\Schema;
use Doctrine\Migrations\AbstractMigration;

final class Version20261112093000 extends AbstractMigration
{
    public function up(Schema $schema): void
    {
        $this->addSql('CREATE TABLE article (
            id INT AUTO_INCREMENT NOT NULL,
            titre VARCHAR(180) NOT NULL,
            contenu LONGTEXT NOT NULL,
            publie TINYINT(1) NOT NULL,
            cree_le DATETIME NOT NULL COMMENT \'(DC2Type:datetime_immutable)\',
            PRIMARY KEY(id)
        )');
    }

    public function down(Schema $schema): void
    {
        $this->addSql('DROP TABLE article');
    }
}
"""), F("terminal", "bash", r"""
$ php bin/console make:migration
 Success!
 Next: Review the new migration "migrations/Version20261112093000.php"

$ php bin/console doctrine:migrations:migrate
 [notice] Migrating up to DoctrineMigrations\Version20261112093000
 [notice] finished in 31.2ms, used 20M memory, 1 migrations executed, 1 sql queries
""")],
  notes=["`Article.php` : chaque propriété mappée correspond à une colonne de la migration ; compare-les ligne à ligne.",
         "`$creeLe` → `cree_le`, `string` sans `length` → `TEXT` grâce à `Types::TEXT`.",
         "La migration a un `up()` (appliquer) et un `down()` (annuler).",
         "Pas de `setId()`, pas de `setPublie()` : on passe par `publier()`."],
  td1=dict(path="Livre.php",
    files=[F("Livre.php", "php", r"""
<?php
declare(strict_types=1);

use Doctrine\DBAL\Types\Types;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Livre
{
    // à toi : id, titre (255), isbn (13, unique), publieLe (date), disponible (true par défaut)
    // constructeur (titre, isbn, date) + emprunter() + rendre() + isDisponible()
}

// Essai : regarde le SQL produit
$em = new Doctrine\ORM\FakeEntityManager();
$livre = new Livre('Dune', '9782266320481', new DateTimeImmutable('1965-08-01'));
$em->persist($livre);
$em->flush();
""")],
    solution=[F("Livre.php", "php", r"""
<?php
declare(strict_types=1);

use Doctrine\DBAL\Types\Types;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Livre
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    #[ORM\Column(length: 255)]
    private string $titre;

    #[ORM\Column(length: 13, unique: true)]
    private string $isbn;

    #[ORM\Column(type: Types::DATE_IMMUTABLE)]
    private \DateTimeImmutable $publieLe;

    #[ORM\Column]
    private bool $disponible = true;

    public function __construct(string $titre, string $isbn, \DateTimeImmutable $publieLe)
    {
        $this->titre = $titre;
        $this->isbn = $isbn;
        $this->publieLe = $publieLe;
    }

    public function getId(): ?int { return $this->id; }
    public function isDisponible(): bool { return $this->disponible; }

    public function emprunter(): void
    {
        if (!$this->disponible) {
            throw new \DomainException('Livre déjà emprunté');
        }
        $this->disponible = false;
    }

    public function rendre(): void
    {
        $this->disponible = true;
    }
}

$em = new Doctrine\ORM\FakeEntityManager();
$livre = new Livre('Dune', '9782266320481', new DateTimeImmutable('1965-08-01'));
$em->persist($livre);
$em->flush();
""")],
    run=SRUN(r"""
$rc = new ReflectionClass(Livre::class);
$attr = fn(string $prop, string $a) => (new ReflectionProperty(Livre::class, $prop))->getAttributes('Doctrine\ORM\Mapping\\' . $a)[0] ?? null;
check('Livre est une entité (#[ORM\Entity])', (bool) $rc->getAttributes('Doctrine\ORM\Mapping\Entity'));
check('$id porte Id + GeneratedValue', $attr('id', 'Id') && $attr('id', 'GeneratedValue'));
$isbn = $attr('isbn', 'Column');
check('isbn : length 13 et unique', $isbn && ($isbn->getArguments()['length'] ?? null) === 13 && ($isbn->getArguments()['unique'] ?? false) === true);
check('titre : length 255', ($attr('titre', 'Column')?->getArguments()['length'] ?? null) === 255);
check('publieLe est une colonne', (bool) $attr('publieLe', 'Column'));
check('Pas de setId() ni setDisponible()', !$rc->hasMethod('setId') && !$rc->hasMethod('setDisponible'));
$em2 = new Doctrine\ORM\FakeEntityManager(); $em2->echo = false;
$l = new Livre('Terremer', '9782253023418', new DateTimeImmutable('1968-01-01'));
check('Avant flush, getId() vaut null', $l->getId() === null);
$em2->persist($l); $em2->flush();
check('Après flush, getId() vaut 1', $l->getId() === 1);
check('INSERT avec isbn, publie_le et disponible', (bool) preg_match("/INSERT INTO livre .*isbn.*publie_le.*disponible/", implode("\n", $em2->log)));
$l->emprunter();
check('emprunter() rend le livre indisponible', $l->isDisponible() === false);
check('emprunter() deux fois lève DomainException', throws(fn() => $l->emprunter(), DomainException::class));
$l->rendre();
check('rendre() le rend disponible', $l->isDisponible() === true);
""")),
  tds=[
    TD(2, "Entité Membre : enum, valeurs par défaut et nom de table",
       "Une entité plus riche : un **statut** stocké via une `enum` PHP, une date d'inscription fixée par le constructeur, un email **normalisé** (minuscules, sans espaces) avant d'être stocké, et une table au nom imposé par l'équipe. " + SIM,
       ["`enum StatutMembre: string` avec `Actif = 'actif'` et `Suspendu = 'suspendu'`",
        "Entité `Membre` stockée dans la table **`membres`** (`#[ORM\\Table(name: 'membres')]`)",
        "Colonnes : `id`, `email` (180, unique), `pseudo` (50), `statut` (`StatutMembre`, défaut `Actif`), `inscritLe` (`DateTimeImmutable`, fixée dans le constructeur)",
        "Le constructeur reçoit email et pseudo ; l'email est stocké en minuscules et sans espaces autour",
        "Méthodes `suspendre()` et `getStatut()` ; un `flush()` après `suspendre()` produit un `UPDATE membres SET statut = 'suspendu'`"],
       [F("Membre.php", "php", r"""
<?php
declare(strict_types=1);

use Doctrine\ORM\Mapping as ORM;

enum StatutMembre: string
{
    // à toi
}

#[ORM\Entity]
class Membre
{
    // à toi
}

$em = new Doctrine\ORM\FakeEntityManager();
$m = new Membre('  Ana@Exemple.FR ', 'ana');
$em->persist($m);
$em->flush();
$m->suspendre();
$em->flush();
""")],
       ["Une colonne enum : `#[ORM\\Column(enumType: StatutMembre::class)] private StatutMembre $statut = StatutMembre::Actif;`",
        "Normaliser : `mb_strtolower(trim($email))`.",
        "Le nom de table se met sur la classe, sous `#[ORM\\Entity]`."],
       [F("Membre.php", "php", r"""
<?php
declare(strict_types=1);

use Doctrine\ORM\Mapping as ORM;

enum StatutMembre: string
{
    case Actif = 'actif';
    case Suspendu = 'suspendu';
}

#[ORM\Entity]
#[ORM\Table(name: 'membres')]
class Membre
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    #[ORM\Column(length: 180, unique: true)]
    private string $email;

    #[ORM\Column(length: 50)]
    private string $pseudo;

    #[ORM\Column(enumType: StatutMembre::class)]
    private StatutMembre $statut = StatutMembre::Actif;

    #[ORM\Column]
    private \DateTimeImmutable $inscritLe;

    public function __construct(string $email, string $pseudo)
    {
        $this->email = mb_strtolower(trim($email));
        $this->pseudo = $pseudo;
        $this->inscritLe = new \DateTimeImmutable();
    }

    public function getEmail(): string { return $this->email; }
    public function getStatut(): StatutMembre { return $this->statut; }

    public function suspendre(): void
    {
        $this->statut = StatutMembre::Suspendu;
    }
}

$em = new Doctrine\ORM\FakeEntityManager();
$m = new Membre('  Ana@Exemple.FR ', 'ana');
$em->persist($m);
$em->flush();
$m->suspendre();
$em->flush();
""")],
       ["Le premier INSERT vise la table `membres` avec `statut = 'actif'`",
        "Le second flush n'envoie qu'un UPDATE de `statut`"],
       run=SRUN(r"""
$em2 = new Doctrine\ORM\FakeEntityManager(); $em2->echo = false;
$m2 = new Membre(' Leo@MAIL.com ', 'leo');
check('email normalisé : leo@mail.com', $m2->getEmail() === 'leo@mail.com');
check('statut par défaut : Actif', $m2->getStatut() === StatutMembre::Actif);
$em2->persist($m2); $em2->flush();
$sql = implode("\n", $em2->log);
check('INSERT INTO membres (table imposée)', str_contains($sql, 'INSERT INTO membres'));
check("la colonne statut vaut 'actif'", str_contains($sql, "'actif'"));
check('inscrit_le est renseigné à la création', (bool) preg_match("/inscrit_le.*VALUES.*'\d{4}-\d\d-\d\d/", $sql));
$em2->clearLog(); $m2->suspendre(); $em2->flush();
check("flush après suspendre() : UPDATE membres SET statut = 'suspendu'", in_array("UPDATE membres SET statut = 'suspendu' WHERE id = 1", $em2->log, true));
$ec = (new ReflectionProperty(Membre::class, 'email'))->getAttributes('Doctrine\ORM\Mapping\Column')[0]->getArguments();
check('email : unique et length 180', ($ec['unique'] ?? false) === true && ($ec['length'] ?? 0) === 180);
check('Pas de setStatut()', !method_exists(Membre::class, 'setStatut'));
""")),
    TD(3, "Dates automatiques avec les callbacks de cycle de vie",
       "Beaucoup d'entités ont `creeLe` et `modifieLe`. Plutôt que d'y penser dans chaque méthode, Doctrine peut appeler des méthodes **automatiquement** juste avant l'INSERT (`PrePersist`) et avant chaque UPDATE (`PreUpdate`). Tu dois aussi garantir qu'un article ne peut pas être publié sans contenu. " + SIM,
       ["Entité `Article` avec `#[ORM\\HasLifecycleCallbacks]` : `titre`, `contenu` (`Types::TEXT`), `publie` (bool, défaut false), `creeLe` et `modifieLe` (`?DateTimeImmutable`, nullable)",
        "Une méthode `#[ORM\\PrePersist]` remplit `creeLe` **et** `modifieLe`",
        "Une méthode `#[ORM\\PreUpdate]` met à jour `modifieLe`",
        "`modifier(string $titre, string $contenu)` et `publier()` ; `publier()` lève `DomainException` si le contenu fait moins de 20 caractères",
        "Les dates ne sont **jamais** remplies dans le constructeur ni dans `modifier()`"],
       [F("Article.php", "php", r"""
<?php
declare(strict_types=1);

use Doctrine\DBAL\Types\Types;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Article
{
    // à toi
}

$em = new Doctrine\ORM\FakeEntityManager();
$a = new Article('Hello', 'Un premier contenu assez long');
$em->persist($a);
$em->flush();
$a->modifier('Hello v2', 'Un premier contenu assez long, modifié');
$em->flush();
""")],
       ["Les deux attributs vont sur la classe : `#[ORM\\Entity, ORM\\HasLifecycleCallbacks]`.",
        "`#[ORM\\Column(nullable: true)] private ?\\DateTimeImmutable $creeLe = null;`",
        "`#[ORM\\PrePersist] public function onCreate(): void { $now = new \\DateTimeImmutable(); ... }`"],
       [F("Article.php", "php", r"""
<?php
declare(strict_types=1);

use Doctrine\DBAL\Types\Types;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity, ORM\HasLifecycleCallbacks]
class Article
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    #[ORM\Column(length: 180)]
    private string $titre;

    #[ORM\Column(type: Types::TEXT)]
    private string $contenu;

    #[ORM\Column]
    private bool $publie = false;

    #[ORM\Column(nullable: true)]
    private ?\DateTimeImmutable $creeLe = null;

    #[ORM\Column(nullable: true)]
    private ?\DateTimeImmutable $modifieLe = null;

    public function __construct(string $titre, string $contenu)
    {
        $this->titre = $titre;
        $this->contenu = $contenu;
    }

    #[ORM\PrePersist]
    public function onCreate(): void
    {
        $now = new \DateTimeImmutable();
        $this->creeLe = $now;
        $this->modifieLe = $now;
    }

    #[ORM\PreUpdate]
    public function onUpdate(): void
    {
        $this->modifieLe = new \DateTimeImmutable('+1 second');
    }

    public function modifier(string $titre, string $contenu): void
    {
        $this->titre = $titre;
        $this->contenu = $contenu;
    }

    public function publier(): void
    {
        if (mb_strlen($this->contenu) < 20) {
            throw new \DomainException('Contenu trop court pour être publié');
        }
        $this->publie = true;
    }

    public function getCreeLe(): ?\DateTimeImmutable { return $this->creeLe; }
    public function getModifieLe(): ?\DateTimeImmutable { return $this->modifieLe; }
}

$em = new Doctrine\ORM\FakeEntityManager();
$a = new Article('Hello', 'Un premier contenu assez long');
$em->persist($a);
$em->flush();
$a->modifier('Hello v2', 'Un premier contenu assez long, modifié');
$em->flush();
""")],
       ["L'INSERT contient déjà `cree_le` et `modifie_le`",
        "L'UPDATE contient `modifie_le` en plus des champs modifiés"],
       run=SRUN(r"""
$em2 = new Doctrine\ORM\FakeEntityManager(); $em2->echo = false;
$x = new Article('Titre', 'Contenu suffisamment long ici');
check('Avant persist : creeLe est null (pas rempli dans le constructeur)', $x->getCreeLe() === null);
$em2->persist($x); $em2->flush();
check('Après flush : creeLe et modifieLe remplis par PrePersist', $x->getCreeLe() !== null && $x->getModifieLe() !== null);
$em2->clearLog();
$x->modifier('Titre 2', 'Contenu suffisamment long ici aussi');
check('modifier() ne touche pas modifieLe lui-même', $x->getModifieLe() == $x->getCreeLe());
$em2->flush();
$up = $em2->log[1] ?? '';
check('Le flush produit un UPDATE avec modifie_le (PreUpdate)', str_starts_with($up, 'UPDATE article') && str_contains($up, 'modifie_le'));
check('modifieLe a changé après le flush', $x->getModifieLe() > $x->getCreeLe());
$court = new Article('Court', 'trop court');
check('publier() refuse un contenu de moins de 20 caractères', throws(fn() => $court->publier(), DomainException::class));
$rc = new ReflectionClass(Article::class);
check('HasLifecycleCallbacks est déclaré', (bool) $rc->getAttributes('Doctrine\ORM\Mapping\HasLifecycleCallbacks'));
""")),
  ])

# ---------------------------------------------------------------- Unit of Work
uow = V2(v1["doc-uow"],
  prereq=[
    P("EntityManager", "Le service central de Doctrine (`EntityManagerInterface` en Symfony). C'est lui qu'on appelle pour enregistrer (`persist`, `flush`), supprimer (`remove`) ou charger (`find`)."),
    P("Transaction", "Un groupe de requêtes SQL exécutées « tout ou rien » : si l'une échoue, aucune n'est appliquée (`START TRANSACTION` … `COMMIT`)."),
    P("Entité suivie (managed)", "Un objet que Doctrine connaît : soit il vient de la base (`find`, une requête), soit tu lui as dit de le suivre avec `persist()`."),
    P("Identity map", "Le registre de Doctrine : pour une même ligne (classe + id), il ne crée qu'**un seul** objet. Deux `find()` du même id renvoient le même objet, sans seconde requête."),
    P("Injection de dépendances", "En Symfony, on reçoit l'EntityManager dans le constructeur d'un service (`private EntityManagerInterface $em`) au lieu de le créer (parcours PHP, dernier module)."),
  ],
  diagram=D(
    nodes=[
      N("new", 0, 0, "new Article()", "inconnu de Doctrine", kind="note", color="muted"),
      N("p", 1, 0, "persist($a)", "« à insérer »", kind="pill"),
      N("find", 0, 2, "find(Article, 42)", "SELECT …", color="accent"),
      N("uow", 2, 1, "Unit of Work", "objets suivis\n+ état d'origine", kind="db"),
      N("mod", 1, 2, "$a->renommer()", "modif en mémoire", kind="pill"),
      N("flush", 3, 1, "flush()", "compare tout", color="warn"),
      N("sql", 4, 1, "1 transaction", "INSERT / UPDATE /\nDELETE", kind="doc", color="good"),
    ],
    edges=[E("new", "p"), E("p", "uow"), E("find", "mod"), E("mod", "uow", "déjà suivi"), E("uow", "flush"), E("flush", "sql", "SQL", color="good")],
    caption="persist() et find() inscrivent des objets dans la Unit of Work. Rien n'est écrit avant flush(), qui compare chaque objet à son état d'origine et envoie tout en une transaction."),
  lessons=[
    L("Doctrine ne sauvegarde pas « tout de suite »", r"""
Instinctivement, on pense que `persist()` enregistre en base. Ce n'est pas le cas, et c'est la source de la plupart des surprises avec Doctrine.

Doctrine travaille comme un carnet de notes appelé **Unit of Work** (unité de travail) :

- `persist($objet)` : « note cet objet, il faudra l'**insérer** ». Aucune requête.
- `remove($objet)` : « note qu'il faudra le **supprimer** ». Aucune requête.
- Modifier un objet suivi (`$article->renommer(...)`) : tu ne dis rien à Doctrine, il s'en rendra compte.
- `flush()` : « maintenant, applique tout ». Doctrine calcule les requêtes nécessaires et les envoie **dans une seule transaction**.

Pourquoi ce fonctionnement ? Parce qu'une action utilisateur modifie souvent plusieurs objets (une commande, ses lignes, le stock). Les écrire ensemble, en une transaction, garantit que la base n'est jamais à moitié à jour : soit tout passe, soit rien.
"""),
    L("Deux façons d'être « suivi »", r"""
Doctrine ne surveille que les objets qu'il connaît (**managed**). Il y a deux façons d'en faire partie :

**1. L'objet vient de la base.** Tout ce que retournent `find()`, `findBy()`, une requête de repository est automatiquement suivi. Doctrine garde une copie de son état d'origine.

```php
$article = $em->find(Article::class, 42);   // SELECT ... ; l'objet est suivi
$article->renommer('Nouveau titre');          // juste en mémoire
$em->flush();                                 // UPDATE article SET titre = ... WHERE id = 42
```

Pas de `persist()` ici : il est inutile (l'appeler ne fait rien de mal, mais ça montre qu'on n'a pas compris).

**2. Tu le crées et tu appelles `persist()`.**

```php
$article = new Article('Hello', '...');
$em->persist($article);                       // suivi, "à insérer"
$em->flush();                                 // INSERT INTO article ...
```

Un objet créé avec `new` **sans** `persist()` n'existera jamais en base, même après dix `flush()`.

Au `flush()`, pour chaque objet suivi, Doctrine **compare** l'état actuel à l'état d'origine (le *change set*). Seuls les champs qui ont changé apparaissent dans l'`UPDATE`. Si rien n'a changé : aucune requête du tout.
"""),
    L("L'identity map : un seul objet par ligne", r"""
Quand Doctrine charge la ligne `article #42`, il la range dans son **identity map**. Si tu redemandes l'article 42 pendant la même requête HTTP, il te rend **le même objet**, sans refaire de `SELECT` :

```php
$a = $em->find(Article::class, 42);   // SELECT
$b = $em->find(Article::class, 42);   // pas de requête
var_dump($a === $b);                  // true : c'est le même objet
```

Conséquence pratique : si deux parties du code modifient « l'article 42 », elles modifient le même objet. Pas de risque qu'une version écrase l'autre au flush.

Ce registre vit le temps d'une requête HTTP (en Symfony, l'EntityManager est remis à zéro entre deux requêtes).
"""),
    L("Où et quand appeler `flush()`", r"""
**Une fois, à la fin de l'action.** Typiquement dans le service qui réalise le cas d'usage (parcours Architecture), après avoir appliqué toutes les règles :

```php
public function passerCommande(Panier $panier): Commande
{
    $commande = Commande::depuisPanier($panier);   // peut lever une exception métier
    foreach ($panier->lignes() as $ligne) {
        $ligne->produit()->retirerDuStock($ligne->quantite());
    }
    $this->em->persist($commande);
    $this->em->flush();                            // tout ou rien
    return $commande;
}
```

Si une exception est levée **avant** le flush, rien n'est écrit : la base reste propre. C'est voulu.

Les pièges classiques :

- **`flush()` dans une boucle** : une transaction par tour. Sur 1 000 objets, c'est très lent. Pour un gros import, on flush **par lots** (tous les 100 objets par exemple), puis `$em->clear()` pour libérer la mémoire.
- **`flush()` dans une entité** : une entité ne connaît pas l'EntityManager. Le flush appartient au service.
- **Oublier `persist()`** sur un nouvel objet : pas d'erreur, juste rien en base. Vérifie avec le profiler (onglet Doctrine) ou les logs.
"""),
  ],
  recap=[
    "`persist()` et `remove()` ne font que **noter** ; seul `flush()` écrit, en **une transaction**.",
    "Objet venu de la base = déjà suivi : le modifier puis `flush()` suffit (pas de `persist`).",
    "Nouvel objet : `persist()` obligatoire, sinon il n'est jamais inséré.",
    "Au flush, Doctrine compare chaque objet à son état d'origine : UPDATE des seuls champs modifiés, rien si rien n'a changé.",
    "Identity map : un seul objet par ligne ; `find()` du même id ne refait pas de SELECT.",
    "Un `flush()` à la fin de l'action (ou par lots pour un import), jamais dans une boucle ni dans une entité.",
  ],
  example=[F("src/Service/ArticleService.php", "php", r"""
<?php

namespace App\Service;

use App\Entity\Article;
use Doctrine\ORM\EntityManagerInterface;

final class ArticleService
{
    public function __construct(private EntityManagerInterface $em) {}

    public function creer(string $titre, string $contenu): Article
    {
        $article = new Article($titre, $contenu);
        $this->em->persist($article);   // noté "à insérer"
        $this->em->flush();             // INSERT
        return $article;                // l'id est maintenant rempli
    }

    public function renommer(int $id, string $titre): void
    {
        $article = $this->em->find(Article::class, $id);   // SELECT, objet suivi
        $article->renommer($titre);
        $this->em->flush();                                  // UPDATE (pas de persist)
    }

    public function supprimer(int $id): void
    {
        $article = $this->em->find(Article::class, $id);
        $this->em->remove($article);    // noté "à supprimer"
        $this->em->flush();             // DELETE
    }
}
"""), F("sql-envoye.txt", "plaintext", r"""
creer('Hello', '...')
  START TRANSACTION
  INSERT INTO article (titre, contenu, publie, cree_le) VALUES ('Hello', '...', 0, '2026-11-12 10:00:00')
  COMMIT

renommer(1, 'Bonjour')
  SELECT * FROM article WHERE id = 1
  START TRANSACTION
  UPDATE article SET titre = 'Bonjour' WHERE id = 1      <- seul le champ modifié
  COMMIT

supprimer(1)                                              <- pas de SELECT : identity map
  START TRANSACTION
  DELETE FROM article WHERE id = 1
  COMMIT
""")],
  notes=["Le service reçoit l'EntityManager par injection ; l'entité, elle, ne le connaît pas.",
         "`renommer()` n'appelle pas `persist()` : l'article vient de `find()`, il est déjà suivi.",
         "Dans le SQL, l'UPDATE ne contient que `titre` : Doctrine a comparé avec l'état d'origine.",
         "Le 2e `find(…, 1)` (dans `supprimer`) ne refait pas de SELECT : l'objet est dans l'identity map."],
  td1=dict(path="predictions.php",
    files=[F("Article.php", "php", r"""
<?php
declare(strict_types=1);

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Article
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    public function __construct(#[ORM\Column] private string $titre) {}

    public function renommer(string $t): void { $this->titre = $t; }
}
"""), F("predictions.php", "php", r"""
<?php
// Pour chaque flush du scénario, prédis ce que Doctrine envoie :
// 'INSERT', 'UPDATE', 'DELETE', 'INSERT+DELETE' ou 'rien'.
// Ne lance pas le code avant d'avoir rempli tes prédictions !
$predictions = [
    1 => '?',
    2 => '?',
    3 => '?',
    4 => '?',
    5 => '?',
];

// ---- scénario (ne pas modifier) ----
$em = new Doctrine\ORM\FakeEntityManager();
$a = new Article('A');
$b = new Article('B');
$em->persist($a);
echo "# flush 1\n"; $em->flush();
$b->renommer('B2');
echo "# flush 2\n"; $em->flush();
$a->renommer('A2');
echo "# flush 3\n"; $em->flush();
$em->persist($b);
$em->remove($a);
echo "# flush 4\n"; $em->flush();
echo "# flush 5\n"; $em->flush();
""")],
    solution=[F("predictions.php", "php", r"""
<?php
$predictions = [
    1 => 'INSERT',        // $a est persisté
    2 => 'rien',          // $b n'est pas suivi : Doctrine ignore sa modification
    3 => 'UPDATE',        // $a est suivi depuis le flush 1
    4 => 'INSERT+DELETE', // $b est enfin persisté (avec le titre B2), $a est supprimé
    5 => 'rien',          // aucun changement depuis le dernier flush
];

$em = new Doctrine\ORM\FakeEntityManager();
$a = new Article('A');
$b = new Article('B');
$em->persist($a);
echo "# flush 1\n"; $em->flush();
$b->renommer('B2');
echo "# flush 2\n"; $em->flush();
$a->renommer('A2');
echo "# flush 3\n"; $em->flush();
$em->persist($b);
$em->remove($a);
echo "# flush 4\n"; $em->flush();
echo "# flush 5\n"; $em->flush();
""")],
    run=SRUN(r"""
$sim = new Doctrine\ORM\FakeEntityManager(); $sim->echo = false;
$x = new Article('A'); $y = new Article('B');
$res = [];
$step = function () use ($sim, &$res) {
  $before = count($sim->log); $sim->flush(); $new = array_slice($sim->log, $before);
  $verbs = []; foreach (['INSERT', 'UPDATE', 'DELETE'] as $v) foreach ($new as $q) if (str_starts_with($q, $v)) { $verbs[] = $v; break; }
  $res[] = $verbs ? implode('+', $verbs) : 'rien';
};
$sim->persist($x); $step(); $y->renommer('B2'); $step(); $x->renommer('A2'); $step(); $sim->persist($y); $sim->remove($x); $step(); $step();
foreach ($res as $i => $r) {
  $p = strtoupper(trim((string) ($predictions[$i + 1] ?? '?')));
  check('Flush ' . ($i + 1) . ' : ' . $r, $p === strtoupper($r), 'ta prédiction : ' . ($predictions[$i + 1] ?? '?'));
}
""")),
  tds=[
    TD(2, "Import par lots",
       "Tu importes des livres depuis un tableau (comme un fichier CSV). Il faut éviter un flush par livre, mais aussi mettre à jour les livres **déjà en base** (même ISBN) au lieu de les dupliquer. " + SIM,
       ["`ImportLivres::importer(array $lignes): array` reçoit des lignes `['isbn' => ..., 'titre' => ...]` et renvoie `['crees' => n, 'maj' => n]`",
        "Pour savoir si un livre existe, utilise `$this->catalogue` (un tableau `isbn => Livre` déjà chargé, fourni au constructeur)",
        "Livre existant : `renommer()` seulement si le titre est différent (pas de `persist`)",
        "Nouveau livre : `new Livre(...)` + `persist()`, et ajoute-le au catalogue (au cas où le même ISBN revienne plus loin)",
        "Flush **tous les 2 livres traités**, plus un flush final : 5 lignes = 3 transactions au maximum"],
       [F("Livre.php", "php", r"""
<?php
declare(strict_types=1);

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Livre
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    public function __construct(
        #[ORM\Column(length: 13, unique: true)] private string $isbn,
        #[ORM\Column] private string $titre,
    ) {}

    public function getIsbn(): string { return $this->isbn; }
    public function getTitre(): string { return $this->titre; }
    public function renommer(string $t): void { $this->titre = $t; }
}
"""), F("ImportLivres.php", "php", r"""
<?php
use Doctrine\ORM\EntityManagerInterface;

final class ImportLivres
{
    private const LOT = 2;

    /** @param array<string, Livre> $catalogue */
    public function __construct(private EntityManagerInterface $em, private array $catalogue) {}

    public function importer(array $lignes): array
    {
        // à toi
    }
}

// Essai
$em = new Doctrine\ORM\FakeEntityManager();
$existant = $em->seed(new Livre('111', 'Dune'));
$import = new ImportLivres($em, ['111' => $existant]);
print_r($import->importer([
    ['isbn' => '111', 'titre' => 'Dune (nouvelle édition)'],
    ['isbn' => '222', 'titre' => 'Fondation'],
    ['isbn' => '333', 'titre' => 'Hypérion'],
]));
""")],
       ["Compte les livres traités dans `$i` ; `if (++$i % self::LOT === 0) $this->em->flush();`",
        "Après la boucle, un dernier `$this->em->flush()` (s'il ne reste rien, il n'envoie aucune requête).",
        "Un livre `seed()` est \"en base\" mais pas encore suivi ; dans l'exercice, le catalogue fourni contient des livres suivis (comme s'ils venaient d'un `findAll()`)."],
       [F("ImportLivres.php", "php", r"""
<?php
use Doctrine\ORM\EntityManagerInterface;

final class ImportLivres
{
    private const LOT = 2;

    /** @param array<string, Livre> $catalogue */
    public function __construct(private EntityManagerInterface $em, private array $catalogue) {}

    public function importer(array $lignes): array
    {
        $crees = 0;
        $maj = 0;
        $i = 0;
        foreach ($lignes as $ligne) {
            $livre = $this->catalogue[$ligne['isbn']] ?? null;
            if ($livre) {
                if ($livre->getTitre() !== $ligne['titre']) {
                    $livre->renommer($ligne['titre']);
                    $maj++;
                }
            } else {
                $livre = new Livre($ligne['isbn'], $ligne['titre']);
                $this->em->persist($livre);
                $this->catalogue[$ligne['isbn']] = $livre;
                $crees++;
            }
            if (++$i % self::LOT === 0) {
                $this->em->flush();
            }
        }
        $this->em->flush();
        return ['crees' => $crees, 'maj' => $maj];
    }
}

$em = new Doctrine\ORM\FakeEntityManager();
$existant = $em->seed(new Livre('111', 'Dune'));
$import = new ImportLivres($em, ['111' => $existant]);
print_r($import->importer([
    ['isbn' => '111', 'titre' => 'Dune (nouvelle édition)'],
    ['isbn' => '222', 'titre' => 'Fondation'],
    ['isbn' => '333', 'titre' => 'Hypérion'],
]));
""")],
       ["5 lignes donnent au plus 3 transactions",
        "Un ISBN qui revient deux fois n'est inséré qu'une fois"],
       run=SRUN(r"""
$em2 = new Doctrine\ORM\FakeEntityManager(); $em2->echo = false;
$em2->seed(new Livre('111', 'Dune'), 1); $d = $em2->find(Livre::class, 1);
$em2->seed(new Livre('444', 'Solaris'), 2); $s = $em2->find(Livre::class, 2);
$em2->clearLog();
$imp = new ImportLivres($em2, ['111' => $d, '444' => $s]);
$r = $imp->importer([
  ['isbn' => '111', 'titre' => 'Dune (poche)'],
  ['isbn' => '222', 'titre' => 'Fondation'],
  ['isbn' => '444', 'titre' => 'Solaris'],
  ['isbn' => '333', 'titre' => 'Hypérion'],
  ['isbn' => '222', 'titre' => 'Fondation (intégrale)'],
]);
check('Résultat : 2 créés, 2 mis à jour', $r === ['crees' => 2, 'maj' => 2], json_encode($r));
check('3 transactions au maximum', $em2->transactions <= 3 && $em2->transactions >= 2, $em2->transactions . ' transaction(s)');
check('2 INSERT seulement (ISBN 222 pas dupliqué)', $em2->count('INSERT') === 2, $em2->count('INSERT') . ' INSERT');
check('Solaris inchangé : aucun UPDATE inutile', !in_array("UPDATE livre SET titre = 'Solaris' WHERE id = 2", $em2->log, true));
check("UPDATE de Dune", in_array("UPDATE livre SET titre = 'Dune (poche)' WHERE id = 1", $em2->log, true));
check('Aucun SELECT pendant l\'import', $em2->count('SELECT') === 0);
""")),
    TD(3, "Virement : tout ou rien",
       "Un virement modifie **deux** comptes. Si une règle échoue au milieu, la base ne doit **jamais** se retrouver avec un compte débité et l'autre pas crédité. Tu dois organiser le service pour que les règles soient vérifiées **avant** toute écriture, et que les deux modifications partent dans **la même** transaction. " + SIM,
       ["`Compte` (entité) : `solde` en centimes (int), `debiter(int)` lève `DomainException` si le solde devient négatif, `crediter(int)`",
        "`VirementService::virer(int $deId, int $versId, int $montant)` charge les deux comptes avec `find()`",
        "Montant ≤ 0, compte introuvable ou même compte → `InvalidArgumentException`, **sans aucune écriture**",
        "Solde insuffisant → l'exception remonte, **sans aucune écriture**",
        "Virement valide → exactement **une** transaction contenant les deux UPDATE"],
       [F("Compte.php", "php", r"""
<?php
declare(strict_types=1);

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Compte
{
    // à toi
}
"""), F("VirementService.php", "php", r"""
<?php
use Doctrine\ORM\EntityManagerInterface;

final class VirementService
{
    public function __construct(private EntityManagerInterface $em) {}

    public function virer(int $deId, int $versId, int $montant): void
    {
        // à toi
    }
}

$em = new Doctrine\ORM\FakeEntityManager();
$em->seed(new Compte('Ana', 10000), 1);
$em->seed(new Compte('Léo', 500), 2);
(new VirementService($em))->virer(1, 2, 2500);
""")],
       ["`Compte` : `#[ORM\\Column] private int $solde;` et un constructeur `(string $titulaire, int $solde = 0)`.",
        "Débite en premier : si `debiter()` lève une exception, `crediter()` n'est jamais appelé et le flush non plus.",
        "Avec Doctrine, une modification en mémoire non flushée n'est pas en base ; mais l'objet reste modifié en mémoire. Ici l'exception est levée **avant** toute modification du solde (le test du solde est fait avant de le changer)."],
       [F("Compte.php", "php", r"""
<?php
declare(strict_types=1);

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Compte
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    public function __construct(
        #[ORM\Column(length: 80)] private string $titulaire,
        #[ORM\Column] private int $solde = 0,
    ) {}

    public function getSolde(): int { return $this->solde; }

    public function debiter(int $montant): void
    {
        if ($montant > $this->solde) {
            throw new \DomainException('Solde insuffisant');
        }
        $this->solde -= $montant;
    }

    public function crediter(int $montant): void
    {
        $this->solde += $montant;
    }
}
"""), F("VirementService.php", "php", r"""
<?php
use Doctrine\ORM\EntityManagerInterface;

final class VirementService
{
    public function __construct(private EntityManagerInterface $em) {}

    public function virer(int $deId, int $versId, int $montant): void
    {
        if ($montant <= 0) throw new \InvalidArgumentException('Montant invalide');
        if ($deId === $versId) throw new \InvalidArgumentException('Même compte');

        $de = $this->em->find(Compte::class, $deId) ?? throw new \InvalidArgumentException('Compte source introuvable');
        $vers = $this->em->find(Compte::class, $versId) ?? throw new \InvalidArgumentException('Compte destination introuvable');

        $de->debiter($montant);      // peut lever DomainException : rien n'a encore changé
        $vers->crediter($montant);
        $this->em->flush();          // une seule transaction pour les deux UPDATE
    }
}

$em = new Doctrine\ORM\FakeEntityManager();
$em->seed(new Compte('Ana', 10000), 1);
$em->seed(new Compte('Léo', 500), 2);
(new VirementService($em))->virer(1, 2, 2500);
""")],
       ["Un virement valide = 1 transaction, 2 UPDATE",
        "Un virement refusé n'envoie ni UPDATE ni transaction"],
       run=SRUN(r"""
$em2 = new Doctrine\ORM\FakeEntityManager(); $em2->echo = false;
$em2->seed(new Compte('A', 10000), 1); $em2->seed(new Compte('B', 500), 2);
$svc = new VirementService($em2);
$em2->clearLog();
$svc->virer(1, 2, 2500);
check('Virement valide : 1 transaction', $em2->transactions === 1, $em2->transactions . ' transaction(s)');
check('Virement valide : 2 UPDATE', $em2->count('UPDATE') === 2);
check('Soldes : 7500 et 3000', $em2->find(Compte::class, 1)->getSolde() === 7500 && $em2->find(Compte::class, 2)->getSolde() === 3000);
$em2->clearLog();
check('Solde insuffisant : DomainException', throws(fn() => $svc->virer(2, 1, 999999), DomainException::class));
check('Solde insuffisant : aucune écriture', $em2->transactions === 0 && $em2->count('UPDATE') === 0);
check('Soldes inchangés en mémoire', $em2->find(Compte::class, 2)->getSolde() === 3000 && $em2->find(Compte::class, 1)->getSolde() === 7500);
check('Montant négatif : InvalidArgumentException', throws(fn() => $svc->virer(1, 2, -5), InvalidArgumentException::class));
check('Compte introuvable : InvalidArgumentException', throws(fn() => $svc->virer(1, 99, 100), InvalidArgumentException::class));
check('Même compte : InvalidArgumentException', throws(fn() => $svc->virer(1, 1, 100), InvalidArgumentException::class));
$em2->flush();
check('Après tous ces refus : toujours aucune écriture', $em2->transactions === 0);
""")),
  ])

# ---------------------------------------------------------------- Repositories
repo = V2(v1["doc-repo"],
  prereq=[
    P("Repository", "La classe dédiée aux **lectures** d'une entité (`LivreRepository` pour `Livre`). Elle regroupe toutes les requêtes pour qu'aucune ne traîne dans les contrôleurs."),
    P("DQL", "*Doctrine Query Language* : ressemble au SQL, mais on y écrit des **noms d'entités et de propriétés** (`Livre l`, `l.publieLe`) au lieu de tables et colonnes."),
    P("QueryBuilder", "Un objet qui construit une requête DQL morceau par morceau (`->andWhere(...)`, `->orderBy(...)`), pratique quand les filtres sont optionnels."),
    P("Paramètre nommé", "`:titre` dans la requête, remplacé par `->setParameter('titre', $valeur)`. La valeur n'est jamais collée dans le texte de la requête."),
    P("Injection SQL", "Une attaque où une valeur saisie par l'utilisateur est interprétée comme du code SQL (`' OR 1=1 --`). Les paramètres l'empêchent."),
  ],
  diagram=D(
    nodes=[
      N("ctrl", 0, 0, "Contrôleur", "findPubliesDepuis()", kind="doc"),
      N("repo", 1, 0, "ArticleRepository", "méthode nommée", color="accent"),
      N("qb", 2, 0, "QueryBuilder → DQL", "a.creeLe >= :depuis", kind="pill"),
      N("sql", 3, 0, "SQL", "cree_le >= ?", kind="doc", color="muted"),
      N("db", 4, 0, "Base", "lignes", kind="db", color="muted"),
      N("hyd", 4, 1, "Hydratation", "lignes → objets", color="good"),
      N("res", 0, 1, "Article[]", "reçus par le contrôleur", kind="file", color="good"),
    ],
    edges=[E("ctrl", "repo"), E("repo", "qb", "construit"), E("qb", "sql", "traduit"), E("sql", "db"), E("db", "hyd"), E("hyd", "res", "objets suivis", color="good")],
    caption="Le contrôleur appelle une méthode nommée. Le repository construit la requête ; Doctrine traduit le DQL en SQL et renvoie des objets."),
  lessons=[
    L("Pourquoi un repository ?", r"""
Sans repository, les requêtes finissent un peu partout : dans les contrôleurs, dans les services, recopiées et modifiées à chaque fois. Quand une règle change (« un article publié doit aussi avoir une date passée »), il faut retrouver toutes les copies.

Le repository est **le seul endroit** où l'on écrit les lectures d'une entité. Le reste du code appelle des **méthodes nommées** qui disent ce qu'elles font :

```php
$articleRepository->findPubliesDepuis(new \DateTimeImmutable('-7 days'));
$livreRepository->compterDisponibles();
```

En Symfony, `make:entity` crée le repository pour toi (`src/Repository/ArticleRepository.php`). Il hérite de `ServiceEntityRepository` et s'injecte comme n'importe quel service.
"""),
    L("Les méthodes toutes prêtes", r"""
Pour les recherches simples par égalité, pas besoin d'écrire de requête :

```php
$repo->find(3);                                        // par id, ou null
$repo->findAll();                                      // tout (attention aux grosses tables)
$repo->findBy(['disponible' => true], ['titre' => 'ASC'], 10);   // critères, tri, limite
$repo->findOneBy(['isbn' => '9782266320481']);         // un seul, ou null
$repo->count(['disponible' => true]);                  // un nombre
```

Les clés du tableau sont des **noms de propriétés** (pas de colonnes). Dès que tu as besoin d'autre chose qu'une égalité (`LIKE`, `>=`, une jointure, un `COUNT` groupé), passe au QueryBuilder.
"""),
    L("Le QueryBuilder et le DQL", r"""
```php
public function findPubliesDepuis(\DateTimeImmutable $depuis, int $max = 10): array
{
    return $this->createQueryBuilder('a')              // "SELECT a FROM Article a"
        ->andWhere('a.publie = true')
        ->andWhere('a.creeLe >= :depuis')
        ->setParameter('depuis', $depuis)
        ->orderBy('a.creeLe', 'DESC')
        ->setMaxResults($max)
        ->getQuery()
        ->getResult();
}
```

- `createQueryBuilder('a')` : `a` est l'**alias** de l'entité. Toutes les conditions parlent de `a.propriete`.
- On écrit des **propriétés** (`a.creeLe`), Doctrine les traduit en colonnes (`cree_le`).
- `andWhere` s'empile : chaque appel ajoute une condition. Pratique pour les filtres optionnels :

```php
$qb = $this->createQueryBuilder('l');
if ($q) {
    $qb->andWhere('LOWER(l.titre) LIKE :q')->setParameter('q', '%' . mb_strtolower($q) . '%');
}
if ($disponible !== null) {
    $qb->andWhere('l.disponible = :d')->setParameter('d', $disponible);
}
```

Ce que renvoie la requête dépend de la méthode finale :

- `getResult()` : un tableau d'objets.
- `getOneOrNullResult()` : un objet ou `null` (exception s'il y en a plusieurs).
- `getSingleScalarResult()` : une seule valeur (avec `->select('COUNT(l.id)')`). Elle arrive souvent en chaîne : caste en `int`.
"""),
    L("Toujours des paramètres", r"""
Ne colle **jamais** une valeur dans le texte de la requête :

```php
// DANGEREUX : si $q vaut  ' OR 1=1 --  la requête change de sens
->andWhere("l.titre LIKE '%$q%'")

// CORRECT
->andWhere('l.titre LIKE :q')->setParameter('q', '%' . $q . '%')
```

Avec un paramètre, la valeur est envoyée **séparément** du texte de la requête : la base ne peut jamais l'interpréter comme du code. Bonus : Doctrine convertit les types (une `DateTimeImmutable` devient une date SQL, un booléen devient 0/1).

Enfin, ne charge pas toute la table pour filtrer en PHP (`array_filter($repo->findAll(), ...)`) : la base sait filtrer, trier et compter bien plus vite, et ne t'envoie que ce dont tu as besoin.
"""),
  ],
  recap=[
    "Toutes les lectures d'une entité vivent dans **son repository**, sous forme de méthodes nommées.",
    "`find`, `findBy`, `findOneBy`, `count` pour les égalités simples ; QueryBuilder pour le reste.",
    "DQL : alias + **propriétés** (`l.publieLe`), traduits en colonnes par Doctrine.",
    "`andWhere` s'empile : idéal pour des filtres optionnels.",
    "Toujours `:parametre` + `setParameter` ; jamais de valeur collée dans la requête.",
    "`getResult`, `getOneOrNullResult`, `getSingleScalarResult` selon ce qu'on attend.",
  ],
  example=[F("src/Repository/ArticleRepository.php", "php", r"""
<?php

namespace App\Repository;

use App\Entity\Article;
use Doctrine\Bundle\DoctrineBundle\Repository\ServiceEntityRepository;
use Doctrine\Persistence\ManagerRegistry;

/** @extends ServiceEntityRepository<Article> */
class ArticleRepository extends ServiceEntityRepository
{
    public function __construct(ManagerRegistry $registry)
    {
        parent::__construct($registry, Article::class);
    }

    /** @return Article[] */
    public function findPubliesDepuis(\DateTimeImmutable $depuis, int $max = 10): array
    {
        return $this->createQueryBuilder('a')
            ->andWhere('a.publie = true')
            ->andWhere('a.creeLe >= :depuis')
            ->setParameter('depuis', $depuis)
            ->orderBy('a.creeLe', 'DESC')
            ->setMaxResults($max)
            ->getQuery()
            ->getResult();
    }

    public function compterPublies(): int
    {
        return (int) $this->createQueryBuilder('a')
            ->select('COUNT(a.id)')
            ->andWhere('a.publie = true')
            ->getQuery()
            ->getSingleScalarResult();
    }
}
"""), F("src/Controller/BlogController.php", "php", r"""
<?php

namespace App\Controller;

use App\Repository\ArticleRepository;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;

final class BlogController extends AbstractController
{
    #[Route('/blog', name: 'blog')]
    public function index(ArticleRepository $articles): Response
    {
        return $this->render('blog/index.html.twig', [
            'recents' => $articles->findPubliesDepuis(new \DateTimeImmutable('-7 days')),
            'total' => $articles->compterPublies(),
            'une' => $articles->findOneBy(['publie' => true], ['creeLe' => 'DESC']),
        ]);
    }
}
"""), F("sql-genere.sql", "sql", r"""
-- findPubliesDepuis(-7 days)
SELECT a0_.id, a0_.titre, a0_.contenu, a0_.publie, a0_.cree_le
FROM article a0_
WHERE a0_.publie = 1 AND a0_.cree_le >= ?
ORDER BY a0_.cree_le DESC
LIMIT 10
-- paramètre : '2026-11-05 10:00:00'

-- compterPublies()
SELECT COUNT(a0_.id) AS sclr_0 FROM article a0_ WHERE a0_.publie = 1
""")],
  notes=["Le contrôleur ne contient aucune requête : il appelle trois méthodes au nom explicite.",
         "`findOneBy` suffit pour « le dernier publié » : critère d'égalité + tri.",
         "Dans le SQL, `:depuis` est devenu `?` : la valeur voyage à part (pas d'injection possible).",
         "`compterPublies()` caste en `int` : `getSingleScalarResult()` renvoie souvent une chaîne."],
  td1=dict(path="src/Repository/LivreRepository.php"),
  tds=[
    TD(2, "Filtres optionnels et tri",
       "La page de recherche du catalogue a des filtres **facultatifs**. Une seule méthode doit gérer toutes les combinaisons, en n'ajoutant que les conditions utiles. Exercice à faire dans ton projet Symfony ; compare le SQL affiché par le profiler avec le résultat attendu.",
       ["`rechercher(?string $q, ?bool $disponible, ?int $auteurId, string $tri = 'titre'): array`",
        "`$q` : titre **ou** auteur contenant le texte (insensible à la casse) ; ignoré si vide",
        "`$disponible` et `$auteurId` : ignorés s'ils valent `null`",
        "`$tri` accepte `'titre'` ou `'recent'` (publieLe décroissant) ; toute autre valeur → `'titre'` (jamais injecter `$tri` dans la requête)",
        "Jointure sur l'auteur pour pouvoir filtrer par son nom"],
       [F("src/Repository/LivreRepository.php", "php", r"""
<?php

namespace App\Repository;

use App\Entity\Livre;
use Doctrine\Bundle\DoctrineBundle\Repository\ServiceEntityRepository;
use Doctrine\Persistence\ManagerRegistry;

class LivreRepository extends ServiceEntityRepository
{
    public function __construct(ManagerRegistry $registry)
    {
        parent::__construct($registry, Livre::class);
    }

    /** @return Livre[] */
    public function rechercher(?string $q, ?bool $disponible, ?int $auteurId, string $tri = 'titre'): array
    {
        // à toi
    }
}
""")],
       ["« titre ou auteur » : `->andWhere('LOWER(l.titre) LIKE :q OR LOWER(a.nom) LIKE :q')`.",
        "Tri sûr : `$tri === 'recent' ? $qb->orderBy('l.publieLe', 'DESC') : $qb->orderBy('l.titre', 'ASC');`",
        "Filtre sur l'auteur : `->andWhere('a.id = :auteur')`."],
       [F("src/Repository/LivreRepository.php", "php", r"""
<?php

namespace App\Repository;

use App\Entity\Livre;
use Doctrine\Bundle\DoctrineBundle\Repository\ServiceEntityRepository;
use Doctrine\Persistence\ManagerRegistry;

class LivreRepository extends ServiceEntityRepository
{
    public function __construct(ManagerRegistry $registry)
    {
        parent::__construct($registry, Livre::class);
    }

    /** @return Livre[] */
    public function rechercher(?string $q, ?bool $disponible, ?int $auteurId, string $tri = 'titre'): array
    {
        $qb = $this->createQueryBuilder('l')
            ->leftJoin('l.auteur', 'a')->addSelect('a');

        if ($q !== null && trim($q) !== '') {
            $qb->andWhere('LOWER(l.titre) LIKE :q OR LOWER(a.nom) LIKE :q')
               ->setParameter('q', '%' . mb_strtolower(trim($q)) . '%');
        }
        if ($disponible !== null) {
            $qb->andWhere('l.disponible = :d')->setParameter('d', $disponible);
        }
        if ($auteurId !== null) {
            $qb->andWhere('a.id = :auteur')->setParameter('auteur', $auteurId);
        }

        $tri === 'recent'
            ? $qb->orderBy('l.publieLe', 'DESC')
            : $qb->orderBy('l.titre', 'ASC');

        return $qb->getQuery()->getResult();
    }
}
""")],
       ["`rechercher(null, null, null)` n'a aucun `WHERE`",
        "`rechercher('le guin', true, null, 'recent')` a deux conditions et un tri par date",
        "`$tri = 'titre; DROP TABLE livre'` donne un tri par titre"],
       expected=r"""
-- rechercher('le guin', true, null, 'recent')
SELECT l0_.*, a1_.*
FROM livre l0_
LEFT JOIN auteur a1_ ON l0_.auteur_id = a1_.id
WHERE (LOWER(l0_.titre) LIKE ? OR LOWER(a1_.nom) LIKE ?) AND l0_.disponible = ?
ORDER BY l0_.publie_le DESC
-- paramètres : '%le guin%', '%le guin%', 1
"""),
    TD(3, "Statistiques avec GROUP BY",
       "Le tableau de bord du bibliothécaire affiche, pour chaque auteur, son nombre de livres et combien sont empruntés, trié par popularité. Ce ne sont plus des **entités** qu'on récupère, mais des **valeurs calculées** : il faut un `select` personnalisé, un `GROUP BY`, et récupérer des tableaux plutôt que des objets.",
       ["`statsParAuteur(): array` renvoie des lignes `['auteur' => 'Le Guin', 'livres' => 4, 'empruntes' => 1]`",
        "Compter les livres avec `COUNT(l.id)` et les empruntés avec `SUM(CASE WHEN l.disponible = false THEN 1 ELSE 0 END)`",
        "Grouper par auteur, trier par `empruntes` décroissant puis nom",
        "Ne garder que les auteurs ayant au moins 1 livre (`HAVING`)",
        "Caster les nombres en `int` avant de renvoyer"],
       [F("src/Repository/AuteurRepository.php", "php", r"""
<?php

namespace App\Repository;

use App\Entity\Auteur;
use Doctrine\Bundle\DoctrineBundle\Repository\ServiceEntityRepository;
use Doctrine\Persistence\ManagerRegistry;

class AuteurRepository extends ServiceEntityRepository
{
    public function __construct(ManagerRegistry $registry)
    {
        parent::__construct($registry, Auteur::class);
    }

    /** @return list<array{auteur: string, livres: int, empruntes: int}> */
    public function statsParAuteur(): array
    {
        // à toi
    }
}
""")],
       ["Point de départ : `$this->createQueryBuilder('a')->select('a.nom AS auteur', 'COUNT(l.id) AS livres', ...)->leftJoin('a.livres', 'l')`.",
        "`->groupBy('a.id')->having('COUNT(l.id) > 0')`",
        "`getArrayResult()` renvoie des tableaux ; un `array_map` caste ensuite `livres` et `empruntes` en `int`."],
       [F("src/Repository/AuteurRepository.php", "php", r"""
<?php

namespace App\Repository;

use App\Entity\Auteur;
use Doctrine\Bundle\DoctrineBundle\Repository\ServiceEntityRepository;
use Doctrine\Persistence\ManagerRegistry;

class AuteurRepository extends ServiceEntityRepository
{
    public function __construct(ManagerRegistry $registry)
    {
        parent::__construct($registry, Auteur::class);
    }

    /** @return list<array{auteur: string, livres: int, empruntes: int}> */
    public function statsParAuteur(): array
    {
        $rows = $this->createQueryBuilder('a')
            ->select(
                'a.nom AS auteur',
                'COUNT(l.id) AS livres',
                'SUM(CASE WHEN l.disponible = false THEN 1 ELSE 0 END) AS empruntes',
            )
            ->leftJoin('a.livres', 'l')
            ->groupBy('a.id')
            ->having('COUNT(l.id) > 0')
            ->orderBy('empruntes', 'DESC')
            ->addOrderBy('a.nom', 'ASC')
            ->getQuery()
            ->getArrayResult();

        return array_map(fn(array $r) => [
            'auteur' => $r['auteur'],
            'livres' => (int) $r['livres'],
            'empruntes' => (int) $r['empruntes'],
        ], $rows);
    }
}
""")],
       ["Une seule requête SQL pour tout le tableau",
        "Les valeurs renvoyées sont des `int`, pas des chaînes"],
       expected=r"""
SELECT a0_.nom AS sclr_0, COUNT(l1_.id) AS sclr_1,
       SUM(CASE WHEN l1_.disponible = 0 THEN 1 ELSE 0 END) AS sclr_2
FROM auteur a0_
LEFT JOIN livre l1_ ON a0_.id = l1_.auteur_id
GROUP BY a0_.id
HAVING COUNT(l1_.id) > 0
ORDER BY sclr_2 DESC, a0_.nom ASC

-- résultat PHP :
-- [ ['auteur' => 'Herbert', 'livres' => 2, 'empruntes' => 2],
--   ['auteur' => 'Le Guin', 'livres' => 4, 'empruntes' => 1], ... ]
"""),
  ])

# ---------------------------------------------------------------- Relations
rel = V2(v1["doc-relations"],
  prereq=[
    P("Clé étrangère", "Une colonne qui contient l'id d'une ligne d'une autre table : `livre.auteur_id = 3` relie le livre à l'auteur n°3."),
    P("Cardinalité", "Combien d'objets de chaque côté : un auteur a **plusieurs** livres (OneToMany), un livre a **un** auteur (ManyToOne)."),
    P("Collection", "L'objet que Doctrine utilise pour une liste liée (`Collection`, implémentée par `ArrayCollection`) : `add()`, `removeElement()`, `contains()`, `count()`, et on peut faire un `foreach` dessus."),
    P("Cascade", "Propager une opération d'un objet à ceux qui lui sont liés : `cascade: ['persist']` = persister un auteur persiste aussi ses nouveaux livres."),
    P("Bidirectionnel", "Quand les deux classes connaissent la relation (`$livre->auteur` **et** `$auteur->livres`). Pratique pour naviguer, mais il faut garder les deux côtés cohérents."),
  ],
  diagram=D(
    nodes=[
      N("aut", 0, 0, "Auteur", "$livres : Collection\nOneToMany (inverse)", kind="file", color="accent"),
      N("liv", 0, 2, "Livre", "$auteur : Auteur\nManyToOne (propriétaire)", kind="file"),
      N("ta", 2, 0, "table auteur", "id | nom", kind="db", color="muted"),
      N("tl", 2, 2, "table livre", "id | titre | auteur_id", kind="db", color="muted"),
      N("note", 1, 1, "Seul le côté propriétaire\nest lu au flush", kind="note", color="warn"),
    ],
    edges=[E("aut", "ta"), E("liv", "tl", "auteur_id", color="good"), E("tl", "ta", "clé étrangère", dashed=True), E("aut", "liv", "mappedBy", dashed=True)],
    caption="En base, la relation n'existe qu'à un endroit : la colonne `auteur_id` de la table livre. Le côté qui la porte (ManyToOne) est le propriétaire."),
  lessons=[
    L("Une relation en base vs en objets", r"""
En base de données, une relation « un auteur a plusieurs livres » se représente d'**une seule** façon : une colonne `auteur_id` dans la table `livre`.

```
auteur                 livre
id | nom               id | titre       | auteur_id
1  | Le Guin           1  | Terremer    | 1
2  | Herbert           2  | Dune        | 2
                       3  | Les Dépossédés | 1
```

En PHP, on aimerait naviguer dans les deux sens : `$livre->getAuteur()` **et** `$auteur->getLivres()`. Doctrine le permet, avec deux attributs :

- **`ManyToOne`** sur `Livre::$auteur` : « plusieurs livres pour un auteur ». C'est ce côté qui correspond à la colonne `auteur_id`.
- **`OneToMany`** sur `Auteur::$livres` : « un auteur, plusieurs livres ». Ce côté n'a **aucune colonne** : c'est une vue calculée à partir des `auteur_id`.
"""),
    L("Côté propriétaire, côté inverse", r"""
C'est LA notion à comprendre :

- Le **côté propriétaire** (*owning side*) est celui qui porte la clé étrangère : le `ManyToOne`. On le reconnaît à `inversedBy`.
- Le **côté inverse** est le `OneToMany`. On le reconnaît à `mappedBy`.

```php
// Livre.php : côté PROPRIÉTAIRE
#[ORM\ManyToOne(inversedBy: 'livres')]
#[ORM\JoinColumn(nullable: false)]       // un livre a forcément un auteur
private Auteur $auteur;

// Auteur.php : côté INVERSE
#[ORM\OneToMany(targetEntity: Livre::class, mappedBy: 'auteur')]
private Collection $livres;
```

**Au flush, Doctrine ne regarde que le côté propriétaire.** Si tu fais seulement :

```php
$auteur->getLivres()->add($livre);   // côté inverse uniquement
$em->flush();
```

… et que `$livre->auteur` n'est pas renseigné, la colonne `auteur_id` reste vide : le lien n'est **pas** enregistré (ou l'INSERT échoue si la colonne est `NOT NULL`). Le côté inverse sert à **naviguer**, pas à enregistrer.

La solution : ne jamais modifier une relation « à la main » des deux côtés, mais écrire **une méthode** qui garde tout cohérent :

```php
// Auteur.php
public function ecrire(string $titre): Livre
{
    $livre = new Livre($this, $titre);   // côté propriétaire rempli par le constructeur
    $this->livres->add($livre);          // côté inverse mis à jour pour la navigation
    return $livre;
}
```
"""),
    L("Initialiser la collection, et cascade", r"""
La propriété `OneToMany` est une `Collection`, à **initialiser dans le constructeur** :

```php
public function __construct(string $nom)
{
    $this->nom = $nom;
    $this->livres = new ArrayCollection();
}
```

Sans ça, `$this->livres->add(...)` plante sur un objet neuf (propriété non initialisée). Pour un objet chargé depuis la base, Doctrine remplit lui-même la collection.

Par défaut, `persist($auteur)` ne persiste **que** l'auteur. Si tu crées un auteur avec deux livres et ne persistes que l'auteur, Doctrine refuse au flush (« une nouvelle entité a été trouvée via la relation… non persistée »). Deux solutions :

- persister chaque livre toi-même ;
- ou déclarer `cascade: ['persist']` sur la relation : persister l'auteur persiste aussi ses nouveaux livres.

```php
#[ORM\OneToMany(targetEntity: Livre::class, mappedBy: 'auteur', cascade: ['persist'])]
```

Utilise `cascade` quand les enfants **appartiennent** au parent (les lignes d'une commande, les commentaires d'un article). Évite-le pour des objets indépendants (un livre et sa catégorie partagée par d'autres livres).
"""),
    L("Retirer un élément : orphanRemoval", r"""
Retirer un commentaire de la collection d'un article (`$article->getCommentaires()->removeElement($c)`) ne fait, par défaut, **rien** en base : on a modifié le côté inverse.

Si un commentaire n'a aucun sens sans son article, déclare `orphanRemoval: true` : tout élément retiré de la collection devient « orphelin » et est **supprimé** au flush.

```php
#[ORM\OneToMany(targetEntity: Commentaire::class, mappedBy: 'article', cascade: ['persist'], orphanRemoval: true)]
private Collection $commentaires;

public function retirerCommentaire(Commentaire $c): void
{
    $this->commentaires->removeElement($c);   // au flush : DELETE FROM commentaire WHERE id = ...
}
```

Les autres types de relations suivent la même logique :

- **OneToOne** (un utilisateur, un profil) : le propriétaire porte la colonne `profil_id`.
- **ManyToMany** (des articles, des tags) : Doctrine crée une **table de jointure** `article_tag (article_id, tag_id)`. Le propriétaire est le côté sans `mappedBy`. Si la liaison porte des informations (date d'ajout, quantité), transforme-la en vraie entité avec deux `ManyToOne`.
"""),
  ],
  recap=[
    "En base, une relation = une **clé étrangère** (`livre.auteur_id`).",
    "`ManyToOne` (avec `inversedBy`) = **côté propriétaire** : c'est le seul lu au flush.",
    "`OneToMany` (avec `mappedBy`) = côté inverse, pour naviguer ; initialiser la `Collection` dans le constructeur.",
    "Une méthode métier (`ecrire()`, `commenter()`) remplit le côté propriétaire **et** met à jour la collection.",
    "`cascade: ['persist']` pour les enfants qui appartiennent au parent ; `orphanRemoval: true` pour supprimer ceux qu'on retire.",
  ],
  example=[F("src/Entity/Article.php", "php", r"""
<?php

namespace App\Entity;

use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Article
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    #[ORM\Column(length: 180)]
    private string $titre;

    /** @var Collection<int, Commentaire> */
    #[ORM\OneToMany(targetEntity: Commentaire::class, mappedBy: 'article', cascade: ['persist'], orphanRemoval: true)]
    private Collection $commentaires;

    public function __construct(string $titre)
    {
        $this->titre = $titre;
        $this->commentaires = new ArrayCollection();
    }

    public function commenter(string $auteur, string $texte): Commentaire
    {
        $c = new Commentaire($this, $auteur, $texte);
        $this->commentaires->add($c);
        return $c;
    }

    public function retirerCommentaire(Commentaire $c): void
    {
        $this->commentaires->removeElement($c);
    }

    /** @return Collection<int, Commentaire> */
    public function getCommentaires(): Collection { return $this->commentaires; }
}
"""), F("src/Entity/Commentaire.php", "php", r"""
<?php

namespace App\Entity;

use Doctrine\DBAL\Types\Types;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Commentaire
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    #[ORM\ManyToOne(inversedBy: 'commentaires')]
    #[ORM\JoinColumn(nullable: false)]
    private Article $article;

    #[ORM\Column(length: 80)]
    private string $auteur;

    #[ORM\Column(type: Types::TEXT)]
    private string $texte;

    public function __construct(Article $article, string $auteur, string $texte)
    {
        $this->article = $article;
        $this->auteur = $auteur;
        $this->texte = $texte;
    }
}
"""), F("utilisation.php", "php", r"""
<?php
$article = new Article('Les DTO expliqués');
$article->commenter('Ana', 'Très clair !');
$c2 = $article->commenter('Léo', 'Merci');

$em->persist($article);   // cascade : les 2 commentaires aussi
$em->flush();
// INSERT INTO article (titre) VALUES ('Les DTO expliqués')
// INSERT INTO commentaire (article_id, auteur, texte) VALUES (1, 'Ana', 'Très clair !')
// INSERT INTO commentaire (article_id, auteur, texte) VALUES (1, 'Léo', 'Merci')

$article->retirerCommentaire($c2);
$em->flush();
// DELETE FROM commentaire WHERE id = 2      <- orphanRemoval
""")],
  notes=["`Commentaire.php` porte la clé étrangère (`ManyToOne` + `JoinColumn(nullable: false)`) : c'est le côté propriétaire.",
         "`Article::commenter()` crée le commentaire **avec** son article : les deux côtés sont toujours cohérents.",
         "`cascade: ['persist']` : un seul `persist($article)` suffit pour insérer les commentaires.",
         "`orphanRemoval: true` : retirer un commentaire de la collection le supprime au flush."],
  td1=dict(path="Auteur.php",
    files=[F("Livre.php", "php", r"""
<?php
declare(strict_types=1);

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Livre
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    // à toi : la relation vers Auteur (côté propriétaire, obligatoire)

    public function __construct(/* à toi */ #[ORM\Column] private string $titre)
    {
    }

    public function getTitre(): string { return $this->titre; }
}
"""), F("Auteur.php", "php", r"""
<?php
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Auteur
{
    // à toi : id, nom, collection livres (OneToMany, cascade persist), ecrire(), getLivres()
}

$em = new Doctrine\ORM\FakeEntityManager();
$auteur = new Auteur('Ursula K. Le Guin');
$auteur->ecrire('Terremer');
$auteur->ecrire('Les Dépossédés');
$em->persist($auteur);
$em->flush();
""")],
    solution=[F("Livre.php", "php", r"""
<?php
declare(strict_types=1);

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Livre
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    #[ORM\ManyToOne(inversedBy: 'livres')]
    #[ORM\JoinColumn(nullable: false)]
    private Auteur $auteur;

    public function __construct(Auteur $auteur, #[ORM\Column] private string $titre)
    {
        $this->auteur = $auteur;
    }

    public function getTitre(): string { return $this->titre; }
    public function getAuteur(): Auteur { return $this->auteur; }
}
"""), F("Auteur.php", "php", r"""
<?php
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Auteur
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    /** @var Collection<int, Livre> */
    #[ORM\OneToMany(targetEntity: Livre::class, mappedBy: 'auteur', cascade: ['persist'])]
    private Collection $livres;

    public function __construct(#[ORM\Column(length: 120)] private string $nom)
    {
        $this->livres = new ArrayCollection();
    }

    public function ecrire(string $titre): Livre
    {
        $livre = new Livre($this, $titre);
        $this->livres->add($livre);
        return $livre;
    }

    public function getLivres(): Collection { return $this->livres; }
}

$em = new Doctrine\ORM\FakeEntityManager();
$auteur = new Auteur('Ursula K. Le Guin');
$auteur->ecrire('Terremer');
$auteur->ecrire('Les Dépossédés');
$em->persist($auteur);
$em->flush();
""")],
    run=SRUN(r"""
$em2 = new Doctrine\ORM\FakeEntityManager(); $em2->echo = false;
$a = new Auteur('Herbert');
$l = $a->ecrire('Dune');
check('ecrire() renvoie un Livre', $l instanceof Livre);
check('Le livre connaît son auteur (côté propriétaire)', $l->getAuteur() === $a);
check('La collection contient le livre (côté inverse)', $a->getLivres()->contains($l));
$a->ecrire('Les Enfants de Dune');
$em2->persist($a); $em2->flush();
check('Un seul persist : 1 INSERT auteur + 2 INSERT livre', $em2->count('INSERT INTO auteur') === 1 && $em2->count('INSERT INTO livre') === 2);
check('Les livres ont auteur_id = 1', count(array_filter($em2->log, fn($q) => str_starts_with($q, 'INSERT INTO livre') && str_ends_with($q, ', 1)'))) === 2);
$ja = (new ReflectionProperty(Livre::class, 'auteur'))->getAttributes('Doctrine\ORM\Mapping\JoinColumn')[0] ?? null;
check('JoinColumn(nullable: false) sur Livre::$auteur', $ja && ($ja->getArguments()['nullable'] ?? true) === false);
check('Un livre sans auteur est impossible (constructeur)', throws(fn() => new Livre(null, 'x'), TypeError::class));
""")),
  tds=[
    TD(2, "Commentaires : ajouter, retirer, orphelins",
       "Les commentaires appartiennent à leur article : on les crée et on les retire **uniquement** via l'article. Retirer un commentaire doit le supprimer en base, sans `remove()` explicite. " + SIM,
       ["`Commentaire` : ManyToOne vers `Article`, non nullable, + `auteur` et `texte`",
        "`Article` : OneToMany `commentaires` avec `cascade: ['persist']` et `orphanRemoval: true`",
        "`Article::commenter(string $auteur, string $texte): Commentaire` et `retirer(Commentaire $c): void`",
        "`Article::nombreDeCommentaires(): int`",
        "Scénario : article + 3 commentaires → un flush ; retirer le 2e → un flush qui produit **uniquement** `DELETE FROM commentaire WHERE id = 2`"],
       [F("Commentaire.php", "php", r"""
<?php
declare(strict_types=1);

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Commentaire
{
    // à toi
}
"""), F("Article.php", "php", r"""
<?php
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Article
{
    // à toi
}

$em = new Doctrine\ORM\FakeEntityManager();
$a = new Article('Les DTO expliqués');
$a->commenter('Ana', 'Très clair');
$c2 = $a->commenter('Léo', 'Merci');
$a->commenter('Zoé', 'Super');
$em->persist($a);
$em->flush();
$a->retirer($c2);
$em->flush();
""")],
       ["`orphanRemoval: true` se met dans le même attribut que `mappedBy` et `cascade`.",
        "`retirer()` : `$this->commentaires->removeElement($c);` et rien d'autre.",
        "`nombreDeCommentaires()` : `count($this->commentaires)` (une Collection est comptable)."],
       [F("Commentaire.php", "php", r"""
<?php
declare(strict_types=1);

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Commentaire
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    #[ORM\ManyToOne(inversedBy: 'commentaires')]
    #[ORM\JoinColumn(nullable: false)]
    private Article $article;

    public function __construct(
        Article $article,
        #[ORM\Column(length: 80)] private string $auteur,
        #[ORM\Column] private string $texte,
    ) {
        $this->article = $article;
    }
}
"""), F("Article.php", "php", r"""
<?php
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Article
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    /** @var Collection<int, Commentaire> */
    #[ORM\OneToMany(targetEntity: Commentaire::class, mappedBy: 'article', cascade: ['persist'], orphanRemoval: true)]
    private Collection $commentaires;

    public function __construct(#[ORM\Column(length: 180)] private string $titre)
    {
        $this->commentaires = new ArrayCollection();
    }

    public function commenter(string $auteur, string $texte): Commentaire
    {
        $c = new Commentaire($this, $auteur, $texte);
        $this->commentaires->add($c);
        return $c;
    }

    public function retirer(Commentaire $c): void
    {
        $this->commentaires->removeElement($c);
    }

    public function nombreDeCommentaires(): int
    {
        return count($this->commentaires);
    }
}

$em = new Doctrine\ORM\FakeEntityManager();
$a = new Article('Les DTO expliqués');
$a->commenter('Ana', 'Très clair');
$c2 = $a->commenter('Léo', 'Merci');
$a->commenter('Zoé', 'Super');
$em->persist($a);
$em->flush();
$a->retirer($c2);
$em->flush();
""")],
       ["Le 2e flush ne contient qu'un DELETE",
        "Le compteur passe de 3 à 2"],
       run=SRUN(r"""
$em2 = new Doctrine\ORM\FakeEntityManager(); $em2->echo = false;
$x = new Article('T');
$x->commenter('a', 'un'); $k = $x->commenter('b', 'deux'); $x->commenter('c', 'trois');
check('3 commentaires', $x->nombreDeCommentaires() === 3);
$em2->persist($x); $em2->flush();
check('1er flush : 1 article + 3 commentaires insérés', $em2->count('INSERT INTO article') === 1 && $em2->count('INSERT INTO commentaire') === 3);
$em2->clearLog();
$x->retirer($k);
check('Après retirer() : 2 commentaires', $x->nombreDeCommentaires() === 2);
$em2->flush();
$w = array_values(array_filter($em2->log, fn($q) => !in_array($q, ['START TRANSACTION', 'COMMIT'], true)));
check('2e flush : uniquement DELETE FROM commentaire WHERE id = 2', $w === ['DELETE FROM commentaire WHERE id = 2'], implode(' | ', $w));
$rp = (new ReflectionProperty(Article::class, 'commentaires'))->getAttributes('Doctrine\ORM\Mapping\OneToMany')[0]->getArguments();
check('orphanRemoval et cascade persist déclarés', ($rp['orphanRemoval'] ?? false) === true && in_array('persist', $rp['cascade'] ?? [], true));
""")),
    TD(3, "Commande, lignes et produits : deux relations",
       "Une commande a des **lignes** (qui lui appartiennent : cascade + orphelins), et chaque ligne pointe vers un **produit** existant (partagé, sans cascade). Tu dois choisir la bonne configuration pour chaque relation, empêcher deux lignes pour le même produit, et observer ce qui arrive si un produit **n'est pas** en base. " + SIM,
       ["`Produit` : id, nom, prix en centimes (int)",
        "`LigneCommande` : ManyToOne `commande` (non nullable), ManyToOne `produit` (non nullable, **sans** cascade), `quantite`, `prixUnitaire` (copié depuis le produit à la création)",
        "`Commande` : OneToMany `lignes` (cascade persist, orphanRemoval) ; `ajouter(Produit $p, int $q)` augmente la quantité si le produit est déjà présent",
        "`Commande::total(): int` (somme quantité × prix unitaire) ; `retirer(Produit $p)`",
        "Ajouter un produit **jamais persisté** puis flusher doit lever une `Doctrine\\ORM\\ORMException` (pas de cascade vers les produits)"],
       [F("Produit.php", "php", r"""
<?php
declare(strict_types=1);

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Produit
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    public function __construct(
        #[ORM\Column] private string $nom,
        #[ORM\Column] private int $prix,
    ) {}

    public function getPrix(): int { return $this->prix; }
}
"""), F("LigneCommande.php", "php", r"""
<?php
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class LigneCommande
{
    // à toi
}
"""), F("Commande.php", "php", r"""
<?php
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Commande
{
    // à toi
}

$em = new Doctrine\ORM\FakeEntityManager();
$clavier = $em->seed(new Produit('Clavier', 4990), 1);
$clavier = $em->find(Produit::class, 1);
$c = new Commande();
$c->ajouter($clavier, 1);
$c->ajouter($clavier, 2);
$em->persist($c);
$em->flush();
echo 'Total : ', $c->total(), "\n";
""")],
       ["Pour retrouver une ligne : `foreach ($this->lignes as $l) if ($l->getProduit() === $p) ...` (identity map : même objet).",
        "Le prix est copié dans la ligne : si le produit change de prix demain, la commande passée ne doit pas changer.",
        "`LigneCommande` a besoin d'une méthode `augmenter(int $q)`."],
       [F("LigneCommande.php", "php", r"""
<?php
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class LigneCommande
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    #[ORM\ManyToOne(inversedBy: 'lignes')]
    #[ORM\JoinColumn(nullable: false)]
    private Commande $commande;

    #[ORM\ManyToOne]
    #[ORM\JoinColumn(nullable: false)]
    private Produit $produit;

    #[ORM\Column]
    private int $quantite;

    #[ORM\Column]
    private int $prixUnitaire;

    public function __construct(Commande $commande, Produit $produit, int $quantite)
    {
        if ($quantite < 1) throw new \InvalidArgumentException('Quantité invalide');
        $this->commande = $commande;
        $this->produit = $produit;
        $this->quantite = $quantite;
        $this->prixUnitaire = $produit->getPrix();
    }

    public function getProduit(): Produit { return $this->produit; }
    public function augmenter(int $q): void { $this->quantite += $q; }
    public function sousTotal(): int { return $this->quantite * $this->prixUnitaire; }
}
"""), F("Commande.php", "php", r"""
<?php
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Commande
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    /** @var Collection<int, LigneCommande> */
    #[ORM\OneToMany(targetEntity: LigneCommande::class, mappedBy: 'commande', cascade: ['persist'], orphanRemoval: true)]
    private Collection $lignes;

    public function __construct()
    {
        $this->lignes = new ArrayCollection();
    }

    public function ajouter(Produit $p, int $q): void
    {
        foreach ($this->lignes as $ligne) {
            if ($ligne->getProduit() === $p) {
                $ligne->augmenter($q);
                return;
            }
        }
        $this->lignes->add(new LigneCommande($this, $p, $q));
    }

    public function retirer(Produit $p): void
    {
        foreach ($this->lignes as $ligne) {
            if ($ligne->getProduit() === $p) {
                $this->lignes->removeElement($ligne);
                return;
            }
        }
    }

    public function total(): int
    {
        $t = 0;
        foreach ($this->lignes as $ligne) $t += $ligne->sousTotal();
        return $t;
    }

    public function nombreDeLignes(): int { return count($this->lignes); }
}

$em = new Doctrine\ORM\FakeEntityManager();
$clavier = $em->seed(new Produit('Clavier', 4990), 1);
$clavier = $em->find(Produit::class, 1);
$c = new Commande();
$c->ajouter($clavier, 1);
$c->ajouter($clavier, 2);
$em->persist($c);
$em->flush();
echo 'Total : ', $c->total(), "\n";
""")],
       ["Le même produit ajouté deux fois donne une seule ligne de quantité 3",
        "Un produit jamais persisté provoque une erreur au flush"],
       run=SRUN(r"""
$em2 = new Doctrine\ORM\FakeEntityManager(); $em2->echo = false;
$em2->seed(new Produit('Clavier', 4990), 1); $em2->seed(new Produit('Souris', 1990), 2);
$k = $em2->find(Produit::class, 1); $s = $em2->find(Produit::class, 2);
$em2->clearLog();
$cmd = new Commande();
$cmd->ajouter($k, 1); $cmd->ajouter($k, 2); $cmd->ajouter($s, 1);
check('Même produit deux fois : une seule ligne (2 lignes au total)', $cmd->nombreDeLignes() === 2);
check('Total = 3×4990 + 1990 = 16960', $cmd->total() === 16960, (string) $cmd->total());
$em2->persist($cmd); $em2->flush();
check('1 INSERT commande + 2 INSERT ligne_commande', $em2->count('INSERT INTO commande') === 1 && $em2->count('INSERT INTO ligne_commande') === 2);
check('Aucun INSERT de produit (pas de cascade)', $em2->count('INSERT INTO produit') === 0);
$em2->clearLog();
$cmd->retirer($s); $em2->flush();
check('Retirer la souris : DELETE de sa ligne', $em2->count('DELETE FROM ligne_commande') === 1);
$pa = (new ReflectionProperty(LigneCommande::class, 'produit'))->getAttributes('Doctrine\ORM\Mapping\ManyToOne')[0]->getArguments();
check('Pas de cascade vers Produit', empty($pa['cascade']));
$nouveau = new Produit('Écran', 18900);
$cmd->ajouter($nouveau, 1);
check('Produit jamais persisté : ORMException au flush', throws(fn() => $em2->flush(), Doctrine\ORM\ORMException::class));
""")),
  ])

# ---------------------------------------------------------------- N+1
n1 = V2(v1["doc-n1"],
  prereq=[
    P("Lazy loading", "Chargement paresseux : Doctrine ne charge une entité liée (l'auteur d'un livre) qu'au moment où on y accède, pas avant."),
    P("Proxy", "Un objet « coquille » que Doctrine met à la place de l'entité liée. Il a le bon type (`Auteur`) mais est vide ; il se remplit (une requête) au premier appel de méthode."),
    P("Jointure (JOIN)", "En SQL, combiner deux tables dans une seule requête : `SELECT ... FROM livre JOIN auteur ON livre.auteur_id = auteur.id`."),
    P("Profiler Symfony", "La barre de debug en bas des pages en développement. L'onglet **Doctrine** liste toutes les requêtes de la page, leur nombre et leur durée."),
  ],
  diagram=D(
    nodes=[
      N("all", 0, 0, "findAll()", "1 requête : les livres", color="accent"),
      N("loop", 1, 0, "foreach livre", "->getAuteur()->getNom()", kind="pill"),
      N("q", 2, 0, "+1 requête", "par auteur (proxy)", color="bad"),
      N("tot", 3, 0, "50 livres", "= 51 requêtes", kind="note", color="bad"),
      N("join", 0, 2, "leftJoin + addSelect", "livres ET auteurs", color="good"),
      N("loop2", 1, 2, "foreach livre", "auteur déjà chargé", kind="pill"),
      N("tot2", 3, 2, "50 livres", "= 1 requête", kind="note", color="good"),
    ],
    edges=[E("all", "loop"), E("loop", "q", "chaque tour", color="bad"), E("q", "tot", color="bad"), E("join", "loop2"), E("loop2", "tot2", "aucune requête", color="good")],
    caption="En haut, le problème N+1 : une requête par élément de la boucle. En bas, le fetch join charge tout d'un coup."),
  lessons=[
    L("Le lazy loading, une bonne idée… sauf dans une boucle", r"""
Quand Doctrine charge un livre, il ne charge pas son auteur : il met à la place un **proxy**, un objet de type `Auteur` encore vide. Dès que tu appelles une méthode dessus (`$livre->getAuteur()->getNom()`), le proxy lance **une requête** pour se remplir.

C'est une bonne idée par défaut : si tu n'as besoin que des titres, pourquoi charger les auteurs ?

Le problème apparaît dans une boucle :

```php
$livres = $repo->findAll();                   // 1 requête : SELECT * FROM livre
foreach ($livres as $livre) {
    echo $livre->getAuteur()->getNom();       // 1 requête par auteur pas encore chargé
}
```

Pour 50 livres de 50 auteurs différents : **1 + 50 = 51 requêtes**. C'est le **problème N+1** (1 requête pour la liste, N pour les éléments). Chaque requête prend quelques millisecondes ; à 51, la page devient lente, et ça empire avec les données. Le piège : le code a l'air parfaitement normal, et en Twig c'est encore plus discret (`{{ livre.auteur.nom }}`).

À noter : grâce à l'identity map, deux livres du même auteur ne déclenchent qu'une requête pour cet auteur. Le pire cas est quand chaque élément pointe vers un objet différent.
"""),
    L("Le repérer", r"""
En développement, la barre de debug Symfony affiche le **nombre de requêtes** de la page. Clique dessus (onglet Doctrine) : tu vois la liste. Le signe d'un N+1 : la **même requête** répétée avec un id différent.

```
SELECT * FROM livre                         (1)
SELECT * FROM auteur WHERE id = 1           (2)
SELECT * FROM auteur WHERE id = 2           (3)
SELECT * FROM auteur WHERE id = 3           (4)
...
```

Le profiler regroupe même ces requêtes identiques (« 50 requêtes similaires »). Prends le réflexe de regarder ce compteur sur chaque page qui affiche une liste.
"""),
    L("Le corriger : fetch join", r"""
On écrit une méthode de repository qui charge les livres **et** leurs auteurs en une requête, avec une jointure :

```php
public function findAvecAuteur(): array
{
    return $this->createQueryBuilder('l')
        ->leftJoin('l.auteur', 'a')
        ->addSelect('a')                   // indispensable : charge vraiment les auteurs
        ->orderBy('l.titre', 'ASC')
        ->getQuery()
        ->getResult();
}
```

`leftJoin` seul ne suffit **pas** : il joint la table (utile pour filtrer, `->andWhere('a.nom = ...')`), mais ne sélectionne pas ses colonnes. C'est **`addSelect('a')`** qui dit « remplis aussi les objets Auteur avec ces colonnes ». Sans lui, tu as une jointure ET toujours des proxies vides.

Le même principe vaut pour une collection (`OneToMany`) :

```php
->leftJoin('l.emprunts', 'e')->addSelect('e')
```

Attention à combiner une jointure de collection avec `setMaxResults()` (pagination) : la limite s'appliquerait aux **lignes SQL** (un livre avec 3 emprunts = 3 lignes), pas aux livres. Dans ce cas, utilise le `Paginator` de Doctrine, qui gère ça correctement.
"""),
    L("Charger seulement ce qu'il faut", r"""
Parfois, tu n'as pas besoin des objets liés, seulement d'un **nombre** ou d'un champ. Charger 300 emprunts pour afficher « 300 » est du gaspillage. Une requête agrégée est bien plus légère :

```php
public function catalogueAvecNbEmprunts(): array
{
    return $this->createQueryBuilder('l')
        ->select('l.id', 'l.titre', 'a.nom AS auteur', 'COUNT(e.id) AS nbEmprunts')
        ->leftJoin('l.auteur', 'a')
        ->leftJoin('l.emprunts', 'e')
        ->groupBy('l.id, a.id')
        ->getQuery()
        ->getArrayResult();   // des tableaux, pas des entités
}
```

Et pour les cas où une relation est **toujours** nécessaire, on peut changer le mode de chargement dans le mapping (`fetch: 'EAGER'`). C'est rarement une bonne idée : la relation serait chargée partout, même là où elle ne sert à rien. Préfère des méthodes de repository adaptées à chaque écran.
"""),
  ],
  recap=[
    "Les relations sont **lazy** : un proxy se charge (1 requête) au premier accès.",
    "Dans une boucle, ça donne **1 + N** requêtes : le problème N+1.",
    "Repère-le dans le profiler : même requête répétée avec des ids différents.",
    "Corrige avec `leftJoin(...)` **+ `addSelect(...)`** dans une méthode de repository.",
    "Pour un simple compte, une requête `COUNT` + `GROUP BY` plutôt que charger les collections.",
    "Jointure de collection + pagination → `Paginator` ; éviter `fetch: 'EAGER'` global.",
  ],
  example=[F("src/Repository/LivreRepository.php", "php", r"""
<?php

namespace App\Repository;

use App\Entity\Livre;
use Doctrine\Bundle\DoctrineBundle\Repository\ServiceEntityRepository;
use Doctrine\Persistence\ManagerRegistry;

class LivreRepository extends ServiceEntityRepository
{
    public function __construct(ManagerRegistry $registry)
    {
        parent::__construct($registry, Livre::class);
    }

    /** @return Livre[] livres + auteurs en UNE requête */
    public function findAvecAuteur(): array
    {
        return $this->createQueryBuilder('l')
            ->leftJoin('l.auteur', 'a')
            ->addSelect('a')
            ->orderBy('l.titre', 'ASC')
            ->getQuery()
            ->getResult();
    }
}
"""), F("templates/livre/index.html.twig", "twig", r"""
{# Avec findAll() : 1 + N requêtes. Avec findAvecAuteur() : 1 requête. #}
<ul>
  {% for livre in livres %}
    <li>{{ livre.titre }} — {{ livre.auteur.nom }}</li>
  {% endfor %}
</ul>
"""), F("profiler.txt", "plaintext", r"""
AVANT  ($repo->findAll())                      51 requêtes · 38 ms
  SELECT ... FROM livre l0_
  SELECT ... FROM auteur a0_ WHERE a0_.id = ?   x 50  (requêtes similaires)

APRÈS  ($repo->findAvecAuteur())               1 requête · 2 ms
  SELECT l0_.*, a1_.* FROM livre l0_ LEFT JOIN auteur a1_ ON l0_.auteur_id = a1_.id ORDER BY l0_.titre ASC
""")],
  notes=["Le template ne change pas : `livre.auteur.nom` est le même code avant et après.",
         "Seule la méthode du repository change : `leftJoin` + `addSelect`.",
         "Le profiler passe de 51 requêtes (dont 50 « similaires ») à 1.",
         "Choisis la méthode de repository selon l'écran : la page liste n'a pas les mêmes besoins que la page détail."],
  td1=dict(path="src/Repository/LivreRepository.php", expected=r"""
-- catalogue() : une seule requête
SELECT l0_.*, a1_.*, e2_.*
FROM livre l0_
LEFT JOIN auteur a1_ ON l0_.auteur_id = a1_.id
LEFT JOIN emprunt e2_ ON l0_.id = e2_.livre_id
ORDER BY l0_.titre ASC
"""),
  tds=[
    TD(2, "Compter les requêtes, sans base de données",
       "Avant de corriger un N+1, il faut savoir le **prévoir**. Pour chaque morceau de code, écris le nombre de requêtes SQL envoyées, en tenant compte du lazy loading et de l'identity map. Les données : 4 livres ; Terremer et Les Dépossédés sont de Le Guin, Dune de Herbert, Fondation d'Asimov. Chaque livre a 2 emprunts.",
       ["Pour chaque cas de A à E, écris le nombre de requêtes dans `$reponses`",
        "Justifie chaque réponse en une ligne de commentaire",
        "Lance : les tests comparent tes réponses au bon nombre"],
       [F("reponses.php", "php", r"""
<?php
/*
A) $livres = $repo->findAll();
   foreach ($livres as $l) echo $l->getTitre();

B) $livres = $repo->findAll();
   foreach ($livres as $l) echo $l->getAuteur()->getNom();

C) $livres = $repo->findAvecAuteur();          // leftJoin + addSelect auteur
   foreach ($livres as $l) echo $l->getAuteur()->getNom();

D) $livres = $repo->findAvecAuteur();
   foreach ($livres as $l) echo count($l->getEmprunts());

E) $l1 = $repo->find(1); $l2 = $repo->find(1);
   echo $l1->getAuteur()->getNom(), $l2->getAuteur()->getNom();
*/

$reponses = [
    'A' => 0,
    'B' => 0,
    'C' => 0,
    'D' => 0,
    'E' => 0,
];
""")],
       ["`getTitre()` ne touche à aucune relation.",
        "Identity map : 3 auteurs différents, pas 4.",
        "Dans D, les auteurs sont chargés, pas les emprunts : chaque collection d'emprunts est lazy."],
       [F("reponses.php", "php", r"""
<?php
$reponses = [
    'A' => 1,  // une requête pour la liste, aucune relation touchée
    'B' => 4,  // 1 liste + 3 auteurs différents (Le Guin n'est chargé qu'une fois)
    'C' => 1,  // les auteurs arrivent avec les livres
    'D' => 5,  // 1 (livres + auteurs) + 4 collections d'emprunts chargées une par une
    'E' => 2,  // 1 find (le 2e find(1) utilise l'identity map) + 1 auteur
];
""")],
       ["Tu sais expliquer pourquoi B vaut 4 et pas 5",
        "Tu sais quelle jointure ajouter pour que D passe à 1"],
       run=RUN("php", tests=r"""
$ok = ['A' => 1, 'B' => 4, 'C' => 1, 'D' => 5, 'E' => 2];
foreach ($ok as $k => $v) check("Cas $k : $v requête(s)", (int) ($reponses[$k] ?? -1) === $v, 'ta réponse : ' . ($reponses[$k] ?? '?'));
""")),
    TD(3, "Page tableau de bord : le bon chargement pour chaque bloc",
       "La page d'accueil du bibliothécaire a 3 blocs. Écrit naïvement, elle lance plus de 100 requêtes. Pour chaque bloc, choisis la bonne stratégie (fetch join, requête agrégée, ou rien) et écris la méthode de repository. Objectif : **3 requêtes** pour toute la page. À faire dans ton projet ; vérifie avec le profiler.",
       ["Bloc 1 : les 10 derniers emprunts avec le titre du livre et le pseudo du membre → `EmpruntRepository::derniers(int $n)` (fetch join sur livre et membre)",
        "Bloc 2 : les 5 livres les plus empruntés avec leur nombre d'emprunts → `LivreRepository::plusEmpruntes(int $n)` (requête agrégée, sans charger les emprunts)",
        "Bloc 3 : nombre de livres disponibles → `LivreRepository::compterDisponibles()`",
        "Le contrôleur appelle les 3 méthodes et ne fait aucune autre requête",
        "Explique en commentaire pourquoi le bloc 1 n'a pas besoin de `Paginator` (ManyToOne uniquement)"],
       [F("src/Repository/EmpruntRepository.php", "php", r"""
<?php

namespace App\Repository;

class EmpruntRepository extends ServiceEntityRepository
{
    /** @return Emprunt[] */
    public function derniers(int $n): array
    {
        // à toi
    }
}
"""), F("src/Repository/LivreRepository.php", "php", r"""
<?php

namespace App\Repository;

class LivreRepository extends ServiceEntityRepository
{
    /** @return list<array{titre: string, nb: int}> */
    public function plusEmpruntes(int $n): array
    {
        // à toi
    }

    public function compterDisponibles(): int
    {
        // à toi
    }
}
""")],
       ["Bloc 1 : `->join('e.livre', 'l')->addSelect('l')->join('e.membre', 'm')->addSelect('m')->orderBy('e.creeLe', 'DESC')->setMaxResults($n)`.",
        "Bloc 2 : `->select('l.titre', 'COUNT(e.id) AS nb')->join('l.emprunts', 'e')->groupBy('l.id')->orderBy('nb', 'DESC')`.",
        "`setMaxResults` est sans danger quand toutes les jointures sont des ManyToOne : une ligne SQL = un emprunt."],
       [F("src/Repository/EmpruntRepository.php", "php", r"""
<?php

namespace App\Repository;

class EmpruntRepository extends ServiceEntityRepository
{
    /** @return Emprunt[] */
    public function derniers(int $n): array
    {
        // Uniquement des ManyToOne (livre, membre) : une ligne SQL = un emprunt,
        // donc setMaxResults() limite bien des emprunts. Pas besoin de Paginator.
        return $this->createQueryBuilder('e')
            ->join('e.livre', 'l')->addSelect('l')
            ->join('e.membre', 'm')->addSelect('m')
            ->orderBy('e.creeLe', 'DESC')
            ->setMaxResults($n)
            ->getQuery()
            ->getResult();
    }
}
"""), F("src/Repository/LivreRepository.php", "php", r"""
<?php

namespace App\Repository;

class LivreRepository extends ServiceEntityRepository
{
    /** @return list<array{titre: string, nb: int}> */
    public function plusEmpruntes(int $n): array
    {
        $rows = $this->createQueryBuilder('l')
            ->select('l.titre', 'COUNT(e.id) AS nb')
            ->join('l.emprunts', 'e')
            ->groupBy('l.id')
            ->orderBy('nb', 'DESC')
            ->setMaxResults($n)
            ->getQuery()
            ->getArrayResult();

        return array_map(fn(array $r) => ['titre' => $r['titre'], 'nb' => (int) $r['nb']], $rows);
    }

    public function compterDisponibles(): int
    {
        return (int) $this->createQueryBuilder('l')
            ->select('COUNT(l.id)')
            ->andWhere('l.disponible = true')
            ->getQuery()
            ->getSingleScalarResult();
    }
}
""")],
       ["Le profiler affiche 3 requêtes pour la page",
        "Aucune requête « similaire » répétée"],
       expected=r"""
Profiler · onglet Doctrine : 3 requêtes

1. SELECT e0_.*, l1_.*, m2_.* FROM emprunt e0_
   INNER JOIN livre l1_ ON e0_.livre_id = l1_.id
   INNER JOIN membre m2_ ON e0_.membre_id = m2_.id
   ORDER BY e0_.cree_le DESC LIMIT 10
2. SELECT l0_.titre, COUNT(e1_.id) AS sclr_1 FROM livre l0_
   INNER JOIN emprunt e1_ ON l0_.id = e1_.livre_id
   GROUP BY l0_.id ORDER BY sclr_1 DESC LIMIT 5
3. SELECT COUNT(l0_.id) FROM livre l0_ WHERE l0_.disponible = 1
"""),
  ])

MODULES = [orm, uow, repo, rel, n1]

from common import M, Q, TD, code

T = "doctrine"

MODULES = [
M("doc-orm", T, "ORM, entités & migrations", 15,
  "Comprendre ce que Doctrine fait entre tes objets et la base de données.",
  "Écrire du SQL à la main pour chaque objet est long et fragile. Doctrine traduit tes objets en lignes, et inversement.",
  ["Tu écris une **entité** : une classe PHP + des attributs de mapping",
   "Doctrine lit le **mapping** : classe → table, propriété → colonne",
   "Une **migration** crée ou modifie la table",
   "L'**EntityManager** sauvegarde et recharge tes objets"],
  ["Entité = classe dont les objets sont stockés en base, avec un identifiant.",
   "`#[ORM\\Column]` décrit chaque colonne ; le type est souvent déduit du type PHP.",
   "`php bin/console make:migration` génère le SQL à partir de la différence entre tes entités et la base. `php bin/console doctrine:migrations:migrate` l'exécute.",
   "Doctrine **hydrate** les objets : il remplit les propriétés directement, sans appeler ton constructeur."],
  ["Modifier la base à la main au lieu de passer par une migration : tes environnements divergent.",
   "Ajouter des setters partout « parce que Doctrine en a besoin » : il n'en a pas besoin."],
  code("php", r"""
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
    private \DateTimeImmutable $creeLe;

    public function __construct(string $titre, string $contenu)
    {
        $this->titre = $titre;
        $this->contenu = $contenu;
        $this->creeLe = new \DateTimeImmutable();
    }

    public function getId(): ?int { return $this->id; }
    public function getTitre(): string { return $this->titre; }

    public function renommer(string $titre): void
    {
        $this->titre = $titre;
    }
}
"""),
  ["`?int $id = null` : l'id n'existe qu'après l'insertion en base.",
   "`string` → VARCHAR, `DateTimeImmutable` → DATETIME : Doctrine déduit le type.",
   "Pas de `setId()` : c'est la base qui génère l'id."],
  [Q("Quand Doctrine recharge un `Article` depuis la base, il…",
     ["appelle le constructeur", "remplit les propriétés directement, sans le constructeur", "appelle les setters", "renvoie un tableau"], 1,
     "C'est pour ça que ton constructeur peut exiger des paramètres métier."),
   Q("Quelle commande génère le fichier de migration ?",
     ["doctrine:schema:update --force", "make:migration", "make:entity --regenerate", "cache:clear"], 1,
     "`make:migration` compare tes entités et la base, puis écrit le SQL dans un fichier versionné."),
   Q("Pourquoi `$id` vaut `null` juste après `new Article(...)` ?",
     ["Bug de Doctrine", "L'id est généré par la base à l'insertion (au flush)", "Il faut appeler setId", "Le constructeur l'oublie"], 1,
     "Avec `GeneratedValue`, l'id vient de la base.")],
  TD("Entité Livre",
     "Crée une entité `Livre` pour une bibliothèque, puis sa migration.",
     ["Champs : `id`, `titre` (255), `isbn` (13, unique), `publieLe` (date immuable), `disponible` (bool, `true` par défaut)",
      "Constructeur avec titre, isbn et date",
      "Méthodes métier `emprunter()` (exception si déjà indisponible) et `rendre()`",
      "Génère puis lance la migration"],
     code("php", r"""
namespace App\Entity;

use Doctrine\DBAL\Types\Types;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Livre
{
    // à toi
}
"""),
     ["Unique : `#[ORM\\Column(length: 13, unique: true)]`",
      "Date sans heure : `#[ORM\\Column(type: Types::DATE_IMMUTABLE)]`",
      "Valeur par défaut : `private bool $disponible = true;`"],
     code("php", r"""
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

// Terminal :
// php bin/console make:migration
// php bin/console doctrine:migrations:migrate
"""),
     ["La migration contient un index UNIQUE sur `isbn`",
      "Aucun `setDisponible()` : on passe par `emprunter()` et `rendre()`"])),

M("doc-uow", T, "persist, flush & Unit of Work", 12,
  "Savoir exactement quand Doctrine écrit en base.",
  "Beaucoup de bugs viennent de là : « j'ai modifié l'objet mais rien n'est en base », ou l'inverse.",
  ["`persist($obj)` : Doctrine **commence à suivre** un nouvel objet",
   "Les objets chargés depuis la base sont **déjà suivis** (managed)",
   "Tu modifies tes objets normalement",
   "`flush()` **compare** et envoie tous les INSERT / UPDATE / DELETE dans une transaction"],
  ["`persist` n'écrit rien. Seul `flush` exécute du SQL.",
   "Un objet récupéré via `find()` est déjà suivi : le modifier puis `flush()` suffit.",
   "La **Unit of Work** garde l'état d'origine de chaque objet suivi et calcule les différences au flush.",
   "`remove($obj)` marque pour suppression, effective au `flush`.",
   "Un seul `flush()` à la fin d'une action, pas un par objet."],
  ["`flush()` dans une boucle : une transaction par tour, très lent.",
   "Oublier `persist` sur un **nouvel** objet : il n'est jamais inséré (sauf cascade)."],
  code("php", r"""
// Créer
$article = new Article('Hello', 'Premier article');
$em->persist($article);   // suivi, rien en base
$em->flush();             // INSERT INTO article ...

// Modifier
$article = $em->find(Article::class, 42); // déjà suivi
$article->renommer('Nouveau titre');
$em->flush();             // UPDATE article SET titre = ... WHERE id = 42

// Supprimer
$em->remove($article);
$em->flush();             // DELETE FROM article WHERE id = 42
"""),
  ["En Symfony, `$em` est un `EntityManagerInterface` injecté.",
   "Le bloc « Modifier » n'a pas de `persist` : l'objet vient de la base.",
   "Si rien n'a changé, `flush()` n'envoie aucune requête."],
  [Q("Après `$em->persist($a)` sans `flush`, la ligne est-elle en base ?",
     ["Oui", "Non", "Seulement en dev", "Oui, mais sans id"], 1,
     "`persist` ne fait qu'inscrire l'objet dans la Unit of Work."),
   Q("Tu charges un article avec `find`, changes son titre, puis `flush()`. Résultat ?",
     ["Rien, il manque persist", "Un UPDATE automatique", "Un INSERT en double", "Une exception"], 1,
     "L'objet est déjà suivi : Doctrine détecte le changement."),
   Q("Tu importes 1000 produits. Où placer `flush()` ?",
     ["Après chaque persist", "Une fois à la fin, ou par lots d'environ 100", "Jamais", "Avant les persist"], 1,
     "Les lots évitent à la fois 1000 transactions et une mémoire qui explose.")],
  TD("Prédire le SQL",
     "Sans exécuter, écris en commentaire les requêtes envoyées à chaque `flush()`. Vérifie ensuite dans le profiler Symfony (onglet Doctrine).",
     ["Pour chaque flush, écris INSERT, UPDATE, DELETE ou « rien »",
      "Justifie chaque réponse en une phrase"],
     code("php", r"""
$a = new Article('A', '...');
$b = new Article('B', '...');
$em->persist($a);
$em->flush();          // 1) ?

$b->renommer('B2');
$em->flush();          // 2) ?

$a->renommer('A2');
$em->flush();          // 3) ?

$em->persist($b);
$em->remove($a);
$em->flush();          // 4) ?

$em->flush();          // 5) ?
"""),
     ["`$b` n'a pas encore été persisté au 2e flush.",
      "Au 4e flush, `$b` porte déjà le titre « B2 »."],
     code("php", r"""
// 1) INSERT article (A) : $a est persisté
// 2) Rien : $b n'est pas suivi par Doctrine
// 3) UPDATE article SET titre = 'A2' WHERE id = <id de A> : $a est suivi
// 4) INSERT article (B2) + DELETE article WHERE id = <id de A>, dans une transaction
// 5) Rien : aucun changement depuis le dernier flush
"""),
     ["Tu sais expliquer pourquoi le 2) n'envoie rien",
      "Tu as vérifié dans le profiler"])),

M("doc-repo", T, "Repositories & requêtes", 15,
  "Récupérer des entités proprement : find, findBy, QueryBuilder.",
  "Des requêtes éparpillées dans les contrôleurs sont dupliquées et dures à modifier. Le repository les rassemble.",
  ["Chaque entité a un **repository**",
   "Méthodes prêtes : `find`, `findBy`, `findOneBy`",
   "Pour le reste : une **méthode nommée** avec le QueryBuilder",
   "Le QueryBuilder produit du **DQL** (sur les entités), traduit en SQL"],
  ["Le DQL parle d'**entités et de propriétés** (`a.creeLe`), pas de tables et de colonnes.",
   "Toujours des **paramètres** (`:depuis`) : jamais de concaténation, sinon injection SQL.",
   "Nomme les méthodes selon le besoin : `findPubliesDepuis()` plutôt que `findByStatusAndDate()`.",
   "`getResult()` : liste d'objets. `getOneOrNullResult()` : un objet ou null. `getSingleScalarResult()` : une valeur."],
  ["Écrire du QueryBuilder dans un contrôleur.",
   "Charger toute la table puis filtrer en PHP avec `array_filter`."],
  code("php", r"""
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
}

// Utilisation
$recents = $articleRepository->findPubliesDepuis(new \DateTimeImmutable('-7 days'));
$un = $articleRepository->findOneBy(['titre' => 'Hello']);
"""),
  ["`'a'` est l'alias de l'entité dans la requête.",
   "`:depuis` + `setParameter` : Doctrine échappe et type la valeur.",
   "Pour des filtres d'égalité simples, `findBy([...])` suffit."],
  [Q("En DQL, on écrit…",
     ["le nom des tables SQL", "le nom des entités et de leurs propriétés", "du SQL brut", "du JSON"], 1,
     "Doctrine traduit ensuite vers les vraies tables et colonnes."),
   Q("Pourquoi `setParameter` plutôt que concaténer la valeur ?",
     ["C'est plus court", "Éviter l'injection SQL et gérer les types", "Obligatoire seulement en DQL", "Pour le cache"], 1,
     "La valeur n'est jamais interprétée comme du code."),
   Q("Quelle méthode renvoie un objet ou null ?",
     ["getResult()", "getOneOrNullResult()", "getArrayResult()", "execute()"], 1,
     "Elle lève une exception s'il y a plusieurs résultats.")],
  TD("Recherche de livres",
     "Dans `LivreRepository`, écris les méthodes dont la page de recherche a besoin.",
     ["`rechercher(string $terme): array` : titres contenant le terme (insensible à la casse), triés par titre",
      "`compterDisponibles(): int`",
      "`plusRecents(int $n): array` : les n livres publiés le plus récemment"],
     code("php", r"""
class LivreRepository extends ServiceEntityRepository
{
    public function __construct(ManagerRegistry $registry)
    {
        parent::__construct($registry, Livre::class);
    }

    // à toi
}
"""),
     ["LIKE : `->andWhere('LOWER(l.titre) LIKE :t')->setParameter('t', '%' . mb_strtolower($terme) . '%')`",
      "Compter : `->select('COUNT(l.id)')` puis `getSingleScalarResult()`, à caster en int.",
      "Tri : `->orderBy('l.publieLe', 'DESC')->setMaxResults($n)`"],
     code("php", r"""
/** @return Livre[] */
public function rechercher(string $terme): array
{
    return $this->createQueryBuilder('l')
        ->andWhere('LOWER(l.titre) LIKE :t')
        ->setParameter('t', '%' . mb_strtolower($terme) . '%')
        ->orderBy('l.titre', 'ASC')
        ->getQuery()
        ->getResult();
}

public function compterDisponibles(): int
{
    return (int) $this->createQueryBuilder('l')
        ->select('COUNT(l.id)')
        ->andWhere('l.disponible = true')
        ->getQuery()
        ->getSingleScalarResult();
}

/** @return Livre[] */
public function plusRecents(int $n): array
{
    return $this->createQueryBuilder('l')
        ->orderBy('l.publieLe', 'DESC')
        ->setMaxResults($n)
        ->getQuery()
        ->getResult();
}
"""),
     ["`$terme` n'est jamais concaténé dans la chaîne DQL",
      "`compterDisponibles()` renvoie un `int`"])),

M("doc-relations", T, "Relations entre entités", 18,
  "Mapper un ManyToOne / OneToMany et comprendre le côté propriétaire.",
  "Les relations sont la première source de confusion avec Doctrine : on modifie un côté et rien n'est enregistré.",
  ["En base, une relation = **une clé étrangère** dans une table",
   "Le côté qui porte la clé est le **côté propriétaire** (ManyToOne)",
   "L'autre côté (OneToMany) est l'**inverse** : il sert juste à naviguer",
   "Au flush, Doctrine ne lit **que le côté propriétaire**"],
  ["`commentaire.article_id` existe en base → `Commentaire::$article` est propriétaire (`inversedBy`).",
   "`Article::$commentaires` est inverse (`mappedBy`) : une `Collection`, initialisée dans le constructeur.",
   "Écris des méthodes qui **gardent les deux côtés cohérents** (`commenter()`).",
   "`cascade: ['persist']` : persister l'article persiste aussi ses nouveaux commentaires.",
   "`orphanRemoval: true` : retirer un commentaire de la collection le supprime en base."],
  ["`$article->getCommentaires()->add($c)` sans fixer `$c->article` : le lien n'est pas enregistré.",
   "Mettre du `cascade` partout sans savoir pourquoi."],
  code("php", r"""
#[ORM\Entity]
class Article
{
    // ... id, titre

    /** @var Collection<int, Commentaire> */
    #[ORM\OneToMany(targetEntity: Commentaire::class, mappedBy: 'article', cascade: ['persist'], orphanRemoval: true)]
    private Collection $commentaires;

    public function __construct(/* ... */)
    {
        $this->commentaires = new ArrayCollection();
    }

    public function commenter(string $auteur, string $texte): Commentaire
    {
        $commentaire = new Commentaire($this, $auteur, $texte);
        $this->commentaires->add($commentaire);
        return $commentaire;
    }
}

#[ORM\Entity]
class Commentaire
{
    // ... id

    #[ORM\ManyToOne(inversedBy: 'commentaires')]
    #[ORM\JoinColumn(nullable: false)]
    private Article $article;

    public function __construct(
        Article $article,
        #[ORM\Column(length: 80)] private string $auteur,
        #[ORM\Column(type: 'text')] private string $texte,
    ) {
        $this->article = $article;
    }
}
"""),
  ["`commenter()` crée le commentaire avec son article : les deux côtés sont cohérents.",
   "`cascade: ['persist']` : `persist($article)` + `flush()` insère aussi le commentaire.",
   "`JoinColumn(nullable: false)` : un commentaire sans article est interdit en base."],
  [Q("Article (1) ↔ Commentaire (N) : quel côté est propriétaire ?",
     ["Article", "Commentaire (ManyToOne, il porte la clé étrangère)", "Les deux", "Aucun"], 1,
     "Le propriétaire est toujours le côté qui a la colonne `..._id`."),
   Q("Tu fais seulement `$article->getCommentaires()->add($c)` puis `flush()`. Le lien est-il enregistré ?",
     ["Oui", "Non : Doctrine ignore le côté inverse", "Oui, en double", "Seulement avec cascade"], 1,
     "Seul `$c->article` (propriétaire) compte au flush."),
   Q("`orphanRemoval: true` fait quoi ?",
     ["Supprime l'article quand il n'a plus de commentaires", "Supprime un commentaire retiré de la collection", "Supprime les doublons", "Rien depuis Doctrine 3"], 1,
     "Un commentaire sans article n'a pas de sens : il est supprimé.")],
  TD("Auteurs et livres",
     "Un auteur écrit plusieurs livres ; un livre a un seul auteur.",
     ["Entité `Auteur` (id, nom) avec une collection `livres` (OneToMany)",
      "`Livre` a un `ManyToOne` vers `Auteur`, non nullable, reçu dans son constructeur",
      "`Auteur::ecrire(string $titre, string $isbn, \\DateTimeImmutable $date): Livre` crée le livre et l'ajoute à la collection",
      "Un seul `persist($auteur)` + `flush()` doit insérer l'auteur et ses livres"],
     code("php", r"""
#[ORM\Entity]
class Auteur
{
    // à toi
}

#[ORM\Entity]
class Livre
{
    // ajoute la relation vers Auteur
}

$auteur = new Auteur('Ursula K. Le Guin');
$auteur->ecrire('Terremer', '9782253023418', new \DateTimeImmutable('1968-01-01'));
$em->persist($auteur);
$em->flush(); // INSERT auteur + INSERT livre
"""),
     ["Côté `Auteur` : `#[ORM\\OneToMany(targetEntity: Livre::class, mappedBy: 'auteur', cascade: ['persist'])]`",
      "Côté `Livre` : `#[ORM\\ManyToOne(inversedBy: 'livres')]` + `#[ORM\\JoinColumn(nullable: false)]`",
      "Initialise `$this->livres = new ArrayCollection();` dans le constructeur d'`Auteur`."],
     code("php", r"""
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

    public function ecrire(string $titre, string $isbn, \DateTimeImmutable $date): Livre
    {
        $livre = new Livre($this, $titre, $isbn, $date);
        $this->livres->add($livre);
        return $livre;
    }
}

#[ORM\Entity]
class Livre
{
    // ... id, titre, isbn, publieLe, disponible

    #[ORM\ManyToOne(inversedBy: 'livres')]
    #[ORM\JoinColumn(nullable: false)]
    private Auteur $auteur;

    public function __construct(Auteur $auteur, string $titre, string $isbn, \DateTimeImmutable $publieLe)
    {
        $this->auteur = $auteur;
        // ...
    }
}
"""),
     ["On ne peut pas créer de `Livre` sans `Auteur`",
      "La migration ajoute `auteur_id` à la table `livre`"])),

M("doc-n1", T, "Lazy loading & problème N+1", 12,
  "Repérer et corriger le problème N+1.",
  "Une page qui affiche 50 articles et leurs auteurs peut lancer 51 requêtes sans que tu le voies.",
  ["Doctrine charge les relations en **lazy** : un **proxy** vide remplace l'objet",
   "Le proxy se charge **au premier accès** (une requête)",
   "Dans une boucle : 1 requête pour la liste **+ N** pour les relations",
   "Solution : un **fetch join** charge tout en une requête"],
  ["Lazy = pratique par défaut, piège dans les boucles.",
   "Repère le N+1 dans le **profiler Symfony** : nombre de requêtes et requêtes identiques répétées.",
   "`leftJoin('a.auteur', 'au')->addSelect('au')` : c'est `addSelect` qui charge vraiment l'auteur.",
   "OneToMany joint + `setMaxResults` : utilise le `Paginator` de Doctrine, sinon la limite porte sur les lignes SQL et pas sur les entités."],
  ["`leftJoin` sans `addSelect` : la jointure filtre, mais l'auteur reste lazy.",
   "Passer toutes les relations en `fetch: 'EAGER'` : tu charges trop, partout."],
  code("php", r"""
// Contrôleur ou template
$articles = $repo->findAll();              // 1 requête
foreach ($articles as $a) {
    echo $a->getAuteur()->getNom();        // +1 requête par auteur !
}

// Repository : version corrigée
public function findAvecAuteur(): array
{
    return $this->createQueryBuilder('a')
        ->leftJoin('a.auteur', 'au')
        ->addSelect('au')                  // charge l'auteur dans la même requête
        ->orderBy('a.creeLe', 'DESC')
        ->getQuery()
        ->getResult();                     // 1 seule requête au total
}
"""),
  ["Sans `addSelect`, `getAuteur()` renvoie un proxy qui déclenche une requête.",
   "Avec, les auteurs sont déjà en mémoire.",
   "Doctrine ne recharge pas deux fois le même auteur (identity map)."],
  [Q("50 articles affichent leur auteur (lazy). Combien de requêtes au maximum ?",
     ["1", "2", "51", "50"], 2,
     "1 pour la liste, puis 1 par auteur différent."),
   Q("Quelle ligne charge réellement l'auteur avec l'article ?",
     ["`leftJoin` seul", "`addSelect('au')`", "`orderBy`", "`getResult`"], 1,
     "La jointure sans `addSelect` ne sélectionne pas les colonnes de l'auteur."),
   Q("Où voir le nombre de requêtes d'une page Symfony ?",
     ["Dans les logs Apache", "Dans le profiler (barre de debug, onglet Doctrine)", "Dans composer.json", "Impossible"], 1,
     "Le profiler signale aussi les requêtes répétées.")],
  TD("Corriger la page catalogue",
     "La page catalogue affiche chaque livre, son auteur et son nombre d'emprunts. Elle lance 101 requêtes pour 50 livres.",
     ["Explique d'où viennent les 101 requêtes",
      "Écris `LivreRepository::catalogue()` qui charge auteur et emprunts en une requête",
      "Bonus : pour juste afficher un nombre, compare avec une requête qui renvoie un COUNT"],
     code("php", r"""
// LivreController
$livres = $livreRepository->findBy([], ['titre' => 'ASC']);

// templates/livre/catalogue.html.twig
// {% for livre in livres %}
//   {{ livre.titre }} - {{ livre.auteur.nom }} - {{ livre.emprunts|length }} emprunts
// {% endfor %}
"""),
     ["101 = 1 (livres) + 50 (auteurs) + 50 (collections d'emprunts).",
      "Deux jointures, chacune avec son `addSelect`."],
     code("php", r"""
// 101 requêtes = 1 (liste) + 50 (auteur de chaque livre) + 50 (emprunts de chaque livre)

/** @return Livre[] */
public function catalogue(): array
{
    return $this->createQueryBuilder('l')
        ->leftJoin('l.auteur', 'a')->addSelect('a')
        ->leftJoin('l.emprunts', 'e')->addSelect('e')
        ->orderBy('l.titre', 'ASC')
        ->getQuery()
        ->getResult();
}

// Bonus : si on veut juste le nombre, pas besoin de charger les emprunts
public function catalogueAvecNbEmprunts(): array
{
    return $this->createQueryBuilder('l')
        ->select('l AS livre', 'a', 'COUNT(e.id) AS nbEmprunts')
        ->leftJoin('l.auteur', 'a')
        ->leftJoin('l.emprunts', 'e')
        ->groupBy('l.id, a.id')
        ->orderBy('l.titre', 'ASC')
        ->getQuery()
        ->getResult(); // [['livre' => Livre, 'nbEmprunts' => 3], ...]
}
"""),
     ["Le profiler affiche 1 requête pour la page",
      "Tu sais expliquer pourquoi `addSelect` est nécessaire"])),
]

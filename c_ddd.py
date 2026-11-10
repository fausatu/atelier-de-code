from common import M, Q, TD, code

T = "ddd"

MODULES = [
M("ddd-langage", T, "Langage commun & bounded contexts", 15,
  "Découper un domaine en contextes où chaque mot a un sens précis.",
  "Dans une même entreprise, « Client » ne veut pas dire la même chose pour la compta et pour le support. Un seul modèle pour tout devient un monstre.",
  ["On parle avec les **experts métier**",
   "On fixe un **vocabulaire commun**, que le code reprend tel quel",
   "On repère où un même mot **change de sens**",
   "Chaque sens = un **bounded context** avec son propre modèle"],
  ["Langage ubiquitaire : si le métier dit « valider une commande », le code a `$commande->valider()`, pas `setStatus(2)`.",
   "Un bounded context a ses propres classes. Le `Produit` du Catalogue (description, photos) n'est pas celui de l'Entrepôt (poids, emplacement).",
   "Les contextes communiquent par **identifiants** et **événements**, pas en partageant leurs entités.",
   "En code : souvent un dossier par contexte (`src/Catalogue`, `src/Facturation`)."],
  ["Une seule entité `User` de 60 champs utilisée partout.",
   "Des noms techniques (`OrderManager`, `DataProcessor`) au lieu des mots du métier."],
  code("plaintext", r"""
Domaine : boutique en ligne

CATALOGUE               COMMANDE                LIVRAISON
- Produit               - Commande              - Colis
  nom, description,       lignes, total,          adresse, poids,
  photos, prix affiché    statut                  transporteur, suivi
- Catégorie             - Client (qui paie)     - Destinataire (qui reçoit)

Une même personne réelle :
  dans Commande  -> "Client"
  dans Livraison -> "Destinataire"

Liens entre contextes : produitId, commandeId
Événement : CommandePayee  ->  Livraison crée un Colis
"""),
  ["Chaque colonne est un contexte avec son vocabulaire.",
   "« Client » et « Destinataire » peuvent être la même personne, mais pas le même modèle.",
   "Les contextes ne se partagent que des ids et des événements."],
  [Q("Dans le contexte Livraison, que doit contenir `Produit` ?",
     ["Tout ce que contient le Catalogue", "Seulement ce dont la livraison a besoin (poids, dimensions…)", "Rien : on réutilise l'entité du Catalogue", "Les photos"], 1,
     "Chaque contexte ne modélise que ce qui lui est utile."),
   Q("Le métier dit « annuler une réservation ». Quel code respecte le langage commun ?",
     ["`$r->setEtat(3)`", "`$r->annuler()`", "`ReservationManager::update($r)`", "`$r->etat = 'X'`"], 1,
     "Le code reprend les verbes du métier."),
   Q("Comment deux contextes se référencent-ils ?",
     ["En partageant les entités Doctrine", "Par identifiants et événements", "Par héritage", "Avec une table commune"], 1,
     "Ça garde chaque contexte libre d'évoluer.")],
  TD("Découper une salle de sport",
     "Une salle de sport gère : abonnements et paiements, planning des cours, réservation de places, accès par badge. Exercice d'analyse, sans code.",
     ["Liste 3 ou 4 bounded contexts",
      "Pour chacun, écris 3 à 5 mots de son langage",
      "Trouve un mot qui change de sens selon le contexte",
      "Décris un événement qui passe d'un contexte à un autre"],
     code("plaintext", r"""
Contexte 1 : ...
  mots : ...

Contexte 2 : ...
  mots : ...

Mot qui change de sens : ...

Événement : ... -> ...
"""),
     ["Pense à qui utilise chaque partie : la compta, le coach, l'accueil, la porte d'entrée.",
      "« Membre » ne contient pas les mêmes infos pour la facturation et pour le contrôle d'accès."],
     code("plaintext", r"""
ABONNEMENT (compta)
  mots : Abonné, Formule, Échéance, Prélèvement, Suspension

PLANNING (coachs)
  mots : Cours, Créneau, Coach, Salle, Capacité

RÉSERVATION (membres)
  mots : Réservation, Place, Liste d'attente, Annulation

ACCÈS (porte d'entrée)
  mots : Badge, Passage, Autorisation, Horaire d'ouverture

Mot qui change de sens : "Membre"
  Abonnement : qui paie, IBAN, formule
  Accès      : un numéro de badge + autorisé oui/non

Événement : AbonnementSuspendu (Abonnement) -> Accès bloque le badge
            CoursAnnule (Planning) -> Réservation prévient les inscrits
"""),
     ["Chaque contexte a un vocabulaire distinct",
      "Tu as au moins un événement entre deux contextes"])),

M("ddd-vo", T, "Value Objects", 15,
  "Remplacer les types primitifs par des objets qui portent les règles.",
  "Un `float $prix` accepte -12 et ne connaît pas sa devise. Un `Money` refuse les valeurs absurdes et sait s'additionner.",
  ["Un concept métier **sans identité propre** (montant, email, période)",
   "devient une **classe immuable**",
   "qui se **valide** à la création",
   "Deux VO sont **égaux si leurs valeurs** sont égales"],
  ["Immuable : aucune méthode ne modifie l'objet, elle en **renvoie un nouveau**.",
   "Pas d'identité : deux billets de 10 € sont interchangeables.",
   "Le VO attire le comportement : `$prix->appliquerRemise(10)` plutôt qu'un calcul recopié partout.",
   "Avec Doctrine : `#[ORM\\Embeddable]` sur le VO + `#[ORM\\Embedded]` dans l'entité pour le stocker dans ses colonnes."],
  ["Des setters sur un VO.",
   "Comparer avec `===` (même instance) au lieu d'une méthode `equals()`."],
  code("php", r"""
final class Money
{
    private function __construct(
        public readonly int $centimes,
        public readonly string $devise,
    ) {
        if ($centimes < 0) {
            throw new InvalidArgumentException('Montant négatif');
        }
    }

    public static function eur(int $centimes): self
    {
        return new self($centimes, 'EUR');
    }

    public function plus(Money $autre): self
    {
        if ($autre->devise !== $this->devise) {
            throw new LogicException('Devises différentes');
        }
        return new self($this->centimes + $autre->centimes, $this->devise);
    }

    public function multiplier(int $n): self
    {
        return new self($this->centimes * $n, $this->devise);
    }

    public function equals(Money $autre): bool
    {
        return $this->centimes === $autre->centimes
            && $this->devise === $autre->devise;
    }
}

$total = Money::eur(1999)->multiplier(2)->plus(Money::eur(500)); // 44,98 €
"""),
  ["Constructeur privé + `Money::eur()` : une création lisible.",
   "`plus()` renvoie un nouvel objet : l'original n'est jamais modifié.",
   "La règle « même devise » est écrite une seule fois."],
  [Q("Qu'est-ce qui distingue un value object d'une entité ?",
     ["Il est stocké en base", "Il n'a pas d'identité : il est défini par ses valeurs", "Il a plus de méthodes", "C'est toujours une interface"], 1,
     "Deux `Money::eur(100)` sont interchangeables ; deux commandes identiques ne le sont pas."),
   Q("`$a = Money::eur(100); $b = $a->plus(Money::eur(50));` Combien vaut `$a` ?",
     ["150", "100", "50", "Erreur"], 1,
     "Immuable : `$a` reste à 100, `$b` vaut 150."),
   Q("Comment comparer deux `Money` ?",
     ["`$a === $b`", "`$a->equals($b)`", "`$a == null`", "`spl_object_id`"], 1,
     "`===` compare les instances, pas les valeurs.")],
  TD("Période de réservation",
     "Crée un value object `Periode` pour un système de réservation.",
     ["`debut` et `fin` (`DateTimeImmutable`), immuables",
      "Exception si `fin` ≤ `debut`",
      "`dureeEnMinutes(): int`",
      "`chevauche(Periode $autre): bool`",
      "`equals(Periode $autre): bool`"],
     code("php", r"""
final class Periode
{
    // à toi
}

$a = new Periode(new DateTimeImmutable('2026-03-01 10:00'), new DateTimeImmutable('2026-03-01 11:00'));
$b = new Periode(new DateTimeImmutable('2026-03-01 10:30'), new DateTimeImmutable('2026-03-01 12:00'));
var_dump($a->chevauche($b)); // true
echo $a->dureeEnMinutes();   // 60
"""),
     ["Deux périodes se chevauchent si `$a->debut < $b->fin && $b->debut < $a->fin`.",
      "Durée : `intdiv($fin->getTimestamp() - $debut->getTimestamp(), 60)`.",
      "`DateTimeImmutable` se compare avec `<`, `>`, `==`."],
     code("php", r"""
final class Periode
{
    public function __construct(
        public readonly DateTimeImmutable $debut,
        public readonly DateTimeImmutable $fin,
    ) {
        if ($fin <= $debut) {
            throw new InvalidArgumentException('La fin doit être après le début');
        }
    }

    public function dureeEnMinutes(): int
    {
        return intdiv($this->fin->getTimestamp() - $this->debut->getTimestamp(), 60);
    }

    public function chevauche(Periode $autre): bool
    {
        return $this->debut < $autre->fin && $autre->debut < $this->fin;
    }

    public function equals(Periode $autre): bool
    {
        return $this->debut == $autre->debut && $this->fin == $autre->fin;
    }
}
"""),
     ["[10h–11h] et [11h–12h] ne se chevauchent pas",
      "Aucune méthode ne modifie `debut` ou `fin`"])),

M("ddd-entite", T, "Entités riches", 15,
  "Mettre les règles métier dans l'entité plutôt que dans des services qui appellent des setters.",
  "Avec un modèle « anémique » (que des getters et setters), les règles sont dispersées et n'importe qui peut mettre l'objet dans un état impossible.",
  ["L'entité a une **identité** stable (un id)",
   "Son état change via des **méthodes métier** (`confirmer()`, `annuler()`)",
   "Chaque méthode **vérifie** que le changement est permis",
   "Les services **orchestrent**, l'entité **décide**"],
  ["Identité : deux commandes au contenu identique restent deux commandes différentes.",
   "Un id typé (`CommandeId`, un VO) empêche de passer un `ClientId` là où on attend un `CommandeId`.",
   "Générer l'id dans le domaine (UUID) permet de le connaître avant d'écrire en base.",
   "Une `enum` PHP rend explicites les statuts possibles."],
  ["`setStatut()` public : n'importe qui passe de « annulée » à « expédiée ».",
   "Un `CommandeService` de 800 lignes qui contient toutes les règles."],
  code("php", r"""
enum Statut: string
{
    case Brouillon = 'brouillon';
    case Confirmee = 'confirmee';
    case Annulee = 'annulee';
}

final class Commande
{
    private Statut $statut = Statut::Brouillon;
    private array $lignes = [];

    public function __construct(public readonly CommandeId $id) {}

    public function ajouterLigne(string $produitId, int $quantite): void
    {
        $this->exigerStatut(Statut::Brouillon);
        $this->lignes[] = ['produit' => $produitId, 'quantite' => $quantite];
    }

    public function confirmer(): void
    {
        $this->exigerStatut(Statut::Brouillon);
        if ($this->lignes === []) {
            throw new DomainException('Commande vide');
        }
        $this->statut = Statut::Confirmee;
    }

    public function annuler(): void
    {
        if ($this->statut === Statut::Annulee) {
            return; // déjà annulée : rien à faire
        }
        $this->statut = Statut::Annulee;
    }

    private function exigerStatut(Statut $attendu): void
    {
        if ($this->statut !== $attendu) {
            throw new DomainException("Impossible : commande {$this->statut->value}");
        }
    }
}
"""),
  ["Aucun setter : seules les méthodes métier changent l'état.",
   "`exigerStatut()` centralise la règle « seulement en brouillon ».",
   "`annuler()` deux fois ne casse rien (idempotent)."],
  [Q("Qu'est-ce qu'un modèle anémique ?",
     ["Un modèle sans base de données", "Des entités avec seulement getters/setters, la logique est ailleurs", "Un modèle avec trop de méthodes", "Un value object"], 1,
     "L'objet ne protège plus ses propres règles."),
   Q("Qui doit refuser de confirmer une commande vide ?",
     ["Le contrôleur", "La base de données", "L'entité `Commande` elle-même", "Le template"], 2,
     "La règle vit là où se trouvent les données qu'elle protège."),
   Q("Avantage d'un `CommandeId` typé plutôt qu'un `string` ?",
     ["Plus rapide", "PHP et l'IDE empêchent de le confondre avec un autre id", "Obligatoire pour Doctrine", "Aucun"], 1,
     "Une erreur de paramètre devient une erreur de type.")],
  TD("Abonnement de salle de sport",
     "Transforme ce modèle anémique en entité riche.",
     ["Statut en `enum`",
      "`suspendre()` : seulement si actif, 2 suspensions max par abonnement",
      "`reactiver()` : seulement si suspendu",
      "`resilier(DateTimeImmutable $le)` : impossible si déjà résilié, fixe `finLe`",
      "Plus aucune propriété publique modifiable"],
     code("php", r"""
class Abonnement
{
    public string $id;
    public string $statut;   // 'actif', 'suspendu', 'resilie'
    public ?DateTimeImmutable $finLe = null;
    public int $suspensionsUtilisees = 0;
}

// dans un service...
$abo->statut = 'suspendu';
$abo->suspensionsUtilisees++;
"""),
     ["Commence par l'enum `StatutAbonnement` avec 3 cas.",
      "Une méthode privée `exiger(StatutAbonnement $s)` évite de répéter les vérifications.",
      "La limite de 2 se vérifie avant d'incrémenter."],
     code("php", r"""
enum StatutAbonnement
{
    case Actif;
    case Suspendu;
    case Resilie;
}

final class Abonnement
{
    private const MAX_SUSPENSIONS = 2;

    private StatutAbonnement $statut = StatutAbonnement::Actif;
    private ?DateTimeImmutable $finLe = null;
    private int $suspensions = 0;

    public function __construct(public readonly AbonnementId $id) {}

    public function suspendre(): void
    {
        $this->exiger(StatutAbonnement::Actif);
        if ($this->suspensions >= self::MAX_SUSPENSIONS) {
            throw new DomainException('Nombre maximum de suspensions atteint');
        }
        $this->suspensions++;
        $this->statut = StatutAbonnement::Suspendu;
    }

    public function reactiver(): void
    {
        $this->exiger(StatutAbonnement::Suspendu);
        $this->statut = StatutAbonnement::Actif;
    }

    public function resilier(DateTimeImmutable $le): void
    {
        if ($this->statut === StatutAbonnement::Resilie) {
            throw new DomainException('Déjà résilié');
        }
        $this->statut = StatutAbonnement::Resilie;
        $this->finLe = $le;
    }

    public function statut(): StatutAbonnement
    {
        return $this->statut;
    }

    private function exiger(StatutAbonnement $attendu): void
    {
        if ($this->statut !== $attendu) {
            throw new DomainException('Action impossible dans ce statut');
        }
    }
}
"""),
     ["Une 3e suspension lève une exception",
      "Impossible de réactiver un abonnement résilié"])),

M("ddd-agregat", T, "Agrégats & invariants", 18,
  "Savoir quels objets modifier ensemble, et par où passer.",
  "Si on modifie une ligne de commande directement, la règle « 10 produits maximum » de la commande peut être contournée.",
  ["Un **agrégat** = un groupe d'objets qui doivent rester cohérents ensemble",
   "Une seule porte d'entrée : la **racine** (aggregate root)",
   "La racine **protège les règles** du groupe entier",
   "On sauvegarde **un agrégat par transaction** et on référence les autres **par id**"],
  ["Exemple : `Commande` (racine) + ses `LigneCommande`. On ne touche jamais une ligne sans passer par la commande.",
   "Un repository **par racine** seulement : pas de `LigneCommandeRepository`.",
   "Garde les agrégats **petits** : `Commande` référence le client par `ClientId`, pas par l'objet `Client`.",
   "Une règle qui touche plusieurs agrégats se gère par **événements** (cohérence à terme)."],
  ["Un agrégat géant (Client → Commandes → Lignes → Produits) : lent et plein de conflits.",
   "Exposer une collection modifiable : `getLignes()->add(...)` contourne la racine."],
  code("php", r"""
final class Commande
{
    private const MAX_LIGNES = 10;

    /** @var LigneCommande[] */
    private array $lignes = [];

    public function __construct(
        public readonly CommandeId $id,
        public readonly ClientId $clientId,   // référence par id
    ) {}

    public function ajouter(ProduitId $produit, int $quantite, Money $prixUnitaire): void
    {
        foreach ($this->lignes as $ligne) {
            if ($ligne->produit->equals($produit)) {
                $ligne->augmenter($quantite);
                return;
            }
        }
        if (count($this->lignes) >= self::MAX_LIGNES) {
            throw new DomainException('10 produits différents maximum');
        }
        $this->lignes[] = new LigneCommande($produit, $quantite, $prixUnitaire);
    }

    public function total(): Money
    {
        return array_reduce(
            $this->lignes,
            fn(Money $t, LigneCommande $l) => $t->plus($l->sousTotal()),
            Money::eur(0),
        );
    }
}
"""),
  ["Toute modification passe par `Commande::ajouter()`.",
   "La règle des 10 lignes est vérifiée à un seul endroit.",
   "`ClientId` plutôt que `Client` : la commande ne charge pas le client entier."],
  [Q("Par où modifier une `LigneCommande` ?",
     ["Directement via son repository", "Via la racine `Commande`", "Via du SQL", "Via le contrôleur"], 1,
     "Seule la racine peut garantir les règles du groupe."),
   Q("Pourquoi `Commande` garde `ClientId` et pas l'objet `Client` ?",
     ["Pour économiser de la mémoire", "Pour garder l'agrégat petit et indépendant", "Doctrine ne gère pas les objets", "Par convention de nommage"], 1,
     "Client et Commande sont deux agrégats, modifiés dans des transactions séparées."),
   Q("Combien de repositories pour l'agrégat Commande + Lignes ?",
     ["Deux", "Un, pour la racine", "Aucun", "Un par ligne"], 1,
     "On charge et sauvegarde l'agrégat entier par sa racine.")],
  TD("Panier avec règles",
     "Modélise l'agrégat `Panier` d'une boutique (réutilise `Money` du module Value Objects).",
     ["Racine `Panier` (id `PanierId`, `ClientId`), lignes internes",
      "Ajouter un produit déjà présent augmente sa quantité",
      "Quantité par ligne entre 1 et 20",
      "Total ≤ 1 000 € (sinon exception, et le panier reste inchangé)",
      "`retirer(ProduitId)` et `total(): Money`",
      "Aucun accès en écriture aux lignes depuis l'extérieur"],
     code("php", r"""
final class Panier
{
    // à toi
}

final class LignePanier
{
    // à toi
}
"""),
     ["Pour « le panier reste inchangé », calcule le futur total AVANT de modifier quoi que ce soit.",
      "Indexe les lignes par id produit : `$this->lignes[(string) $produit] = ...`",
      "`LignePanier` peut être immuable : `avecQuantite(int $q): self`."],
     code("php", r"""
final class LignePanier
{
    public function __construct(
        public readonly ProduitId $produit,
        public readonly int $quantite,
        public readonly Money $prixUnitaire,
    ) {
        if ($quantite < 1 || $quantite > 20) {
            throw new DomainException('Quantité entre 1 et 20');
        }
    }

    public function avecQuantite(int $q): self
    {
        return new self($this->produit, $q, $this->prixUnitaire);
    }

    public function sousTotal(): Money
    {
        return $this->prixUnitaire->multiplier($this->quantite);
    }
}

final class Panier
{
    private const PLAFOND = 100000; // centimes

    /** @var array<string, LignePanier> */
    private array $lignes = [];

    public function __construct(
        public readonly PanierId $id,
        public readonly ClientId $clientId,
    ) {}

    public function ajouter(ProduitId $produit, int $quantite, Money $prix): void
    {
        $cle = (string) $produit;
        $nouvelle = isset($this->lignes[$cle])
            ? $this->lignes[$cle]->avecQuantite($this->lignes[$cle]->quantite + $quantite)
            : new LignePanier($produit, $quantite, $prix);

        $lignes = $this->lignes;
        $lignes[$cle] = $nouvelle;
        if ($this->totalDe($lignes)->centimes > self::PLAFOND) {
            throw new DomainException('Panier limité à 1 000 €');
        }
        $this->lignes = $lignes;
    }

    public function retirer(ProduitId $produit): void
    {
        unset($this->lignes[(string) $produit]);
    }

    public function total(): Money
    {
        return $this->totalDe($this->lignes);
    }

    private function totalDe(array $lignes): Money
    {
        return array_reduce($lignes, fn(Money $t, LignePanier $l) => $t->plus($l->sousTotal()), Money::eur(0));
    }
}
"""),
     ["Un ajout qui dépasse 1 000 € laisse le panier intact",
      "21 unités d'un même produit sont refusées"])),

M("ddd-couches", T, "Couches & repositories", 18,
  "Séparer domaine, application et infrastructure, et brancher Doctrine sans polluer le domaine.",
  "Si ton domaine dépend de Doctrine, de Symfony ou de HTTP, tu ne peux plus le tester ni le faire évoluer seul.",
  ["**Domain** : entités, VO, interfaces de repository, sans dépendance technique",
   "**Application** : les cas d'usage (handlers) qui orchestrent le domaine",
   "**Infrastructure** : Doctrine, API, mail, qui **implémentent** les interfaces",
   "Les dépendances pointent **vers le domaine**, jamais l'inverse"],
  ["L'interface `CommandeRepository` vit dans Domain ; `DoctrineCommandeRepository` vit dans Infrastructure.",
   "Un handler = un cas d'usage : charger, appeler une méthode métier, sauvegarder.",
   "Le contrôleur ne fait que traduire HTTP → appel du handler → réponse.",
   "Symfony relie automatiquement l'interface à son implémentation s'il n'y en a qu'une."],
  ["Utiliser `EntityManagerInterface` dans une entité.",
   "Un handler qui contient les règles métier : elles doivent être dans le domaine."],
  code("php", r"""
// src/Commande/Domain/CommandeRepository.php
namespace App\Commande\Domain;

interface CommandeRepository
{
    public function get(CommandeId $id): Commande;   // exception si absente
    public function save(Commande $commande): void;
}

// src/Commande/Application/ConfirmerCommandeHandler.php
namespace App\Commande\Application;

final class ConfirmerCommandeHandler
{
    public function __construct(private CommandeRepository $commandes) {}

    public function __invoke(string $commandeId): void
    {
        $commande = $this->commandes->get(new CommandeId($commandeId));
        $commande->confirmer();          // la règle est dans le domaine
        $this->commandes->save($commande);
    }
}

// src/Commande/Infrastructure/DoctrineCommandeRepository.php
namespace App\Commande\Infrastructure;

final class DoctrineCommandeRepository implements CommandeRepository
{
    public function __construct(private EntityManagerInterface $em) {}

    public function get(CommandeId $id): Commande
    {
        return $this->em->find(Commande::class, $id->valeur)
            ?? throw new CommandeIntrouvable($id);
    }

    public function save(Commande $commande): void
    {
        $this->em->persist($commande);
        $this->em->flush();
    }
}
"""),
  ["Les `use` sont omis pour la lisibilité.",
   "Le handler ne connaît que l'interface : en test, on lui passe une version en mémoire.",
   "Doctrine n'apparaît que dans Infrastructure."],
  [Q("Où vit l'interface `CommandeRepository` ?",
     ["Infrastructure", "Domain", "Controller", "vendor"], 1,
     "Le domaine définit le besoin, l'infrastructure le réalise."),
   Q("Que fait un handler applicatif ?",
     ["Il contient les règles métier", "Il charge l'agrégat, appelle une méthode métier, sauvegarde", "Il rend le HTML", "Il mappe les tables"], 1,
     "Il orchestre ; le domaine décide."),
   Q("Quelle dépendance est interdite ?",
     ["Infrastructure → Domain", "Application → Domain", "Domain → Doctrine", "Controller → Application"], 2,
     "Le domaine ne dépend de rien de technique.")],
  TD("Réserver un cours",
     "Salle de sport : un membre réserve une place dans un cours.",
     ["Domain : agrégat `Cours` (capacité, liste des `MembreId` inscrits), `reserver(MembreId)` refuse si complet ou déjà inscrit",
      "Domain : interface `CoursRepository` (`get`, `save`)",
      "Application : `ReserverPlaceHandler`",
      "Infrastructure : `InMemoryCoursRepository` (Doctrine en bonus)",
      "Test : 2 places, 3 réservations → la 3e échoue"],
     code("plaintext", r"""
src/Reservation/
├── Domain/
│   ├── Cours.php
│   ├── CoursId.php
│   ├── MembreId.php
│   └── CoursRepository.php
├── Application/
│   └── ReserverPlaceHandler.php
└── Infrastructure/
    └── InMemoryCoursRepository.php
"""),
     ["`MembreId` peut avoir une méthode `equals()` ; garde les inscrits indexés par leur valeur.",
      "`InMemoryCoursRepository` : un simple tableau `[id => Cours]`.",
      "Le handler ne contient aucun `if` métier."],
     code("php", r"""
// Domain
final class Cours
{
    /** @var array<string, MembreId> */
    private array $inscrits = [];

    public function __construct(public readonly CoursId $id, private int $capacite) {}

    public function reserver(MembreId $membre): void
    {
        if (isset($this->inscrits[$membre->valeur])) {
            throw new DomainException('Déjà inscrit');
        }
        if (count($this->inscrits) >= $this->capacite) {
            throw new DomainException('Cours complet');
        }
        $this->inscrits[$membre->valeur] = $membre;
    }
}

interface CoursRepository
{
    public function get(CoursId $id): Cours;
    public function save(Cours $cours): void;
}

// Application
final class ReserverPlaceHandler
{
    public function __construct(private CoursRepository $cours) {}

    public function __invoke(string $coursId, string $membreId): void
    {
        $cours = $this->cours->get(new CoursId($coursId));
        $cours->reserver(new MembreId($membreId));
        $this->cours->save($cours);
    }
}

// Infrastructure
final class InMemoryCoursRepository implements CoursRepository
{
    private array $items = [];

    public function get(CoursId $id): Cours
    {
        return $this->items[$id->valeur] ?? throw new RuntimeException('Cours introuvable');
    }

    public function save(Cours $cours): void
    {
        $this->items[$cours->id->valeur] = $cours;
    }
}

// Test
$repo = new InMemoryCoursRepository();
$repo->save(new Cours(new CoursId('yoga'), 2));
$reserver = new ReserverPlaceHandler($repo);
$reserver('yoga', 'ana');
$reserver('yoga', 'leo');
try {
    $reserver('yoga', 'zoe');
    echo 'ERREUR : la 3e réservation aurait dû échouer';
} catch (DomainException $e) {
    echo 'OK : ' . $e->getMessage(); // OK : Cours complet
}
"""),
     ["Domain ne contient aucun `use Doctrine\\...`",
      "Le test tourne sans base de données"])),
]

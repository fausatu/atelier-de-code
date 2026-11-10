from common import M, Q, TD, code

T = "php"

MODULES = [
M("php-classes", T, "Classes & objets", 15,
  "Savoir créer une classe, l'instancier et comprendre ce que contient un objet.",
  "Sans objets, les données et les fonctions qui les manipulent vivent séparément : n'importe quel code peut tout modifier, et ça finit par casser.",
  ["Tu écris la **classe** : le plan (propriétés + méthodes)",
   "`new Produit(...)` crée un **objet** en mémoire",
   "Le **constructeur** remplit son état initial",
   "Les **méthodes** lisent et modifient cet état via `$this`"],
  ["Une classe ne fait rien seule. Chaque `new` crée un objet **indépendant** avec ses propres valeurs.",
   "`$this` = l'objet sur lequel la méthode est appelée.",
   "Depuis PHP 8, la **promotion de constructeur** déclare et remplit une propriété en une ligne : `public function __construct(private string $nom) {}`.",
   "Un objet passé à une fonction n'est **pas copié** : si la fonction le modifie, l'original est modifié. Pour une copie : `clone`."],
  ["Oublier `$this->` : `$nom` tout seul est une variable locale, pas la propriété.",
   "Confondre `->` (objet) et `::` (statique, constante)."],
  code("php", r"""
<?php
declare(strict_types=1);

class Produit
{
    public function __construct(
        private string $nom,
        private float $prixHT,
    ) {}

    public function prixTTC(float $tva = 0.2): float
    {
        return round($this->prixHT * (1 + $tva), 2);
    }

    public function nom(): string
    {
        return $this->nom;
    }
}

$clavier = new Produit('Clavier', 50.0);
$souris  = new Produit('Souris', 20.0);

echo $clavier->prixTTC(); // 60
echo $souris->nom();      // Souris
"""),
  ["`declare(strict_types=1)` : PHP refuse un mauvais type au lieu de le convertir en silence.",
   "`private string $nom` dans le constructeur déclare ET assigne la propriété.",
   "`$clavier` et `$souris` : même plan, deux états différents."],
  [Q("Que se passe-t-il à chaque `new Produit(...)` ?",
     ["La classe est rechargée", "Un nouvel objet indépendant est créé et son constructeur est appelé", "Le même objet est réutilisé", "Les propriétés statiques sont remises à zéro"], 1,
     "Chaque `new` crée un objet distinct puis exécute `__construct`."),
   Q("Dans une méthode, `$this` désigne…",
     ["La classe", "L'objet sur lequel la méthode est appelée", "La classe parente", "Le dernier objet créé"], 1,
     "`$clavier->prixTTC()` : dans `prixTTC`, `$this` est `$clavier`."),
   Q("Une fonction reçoit l'objet `$p` et appelle `$p->renommer('X')`. L'objet d'origine…",
     ["reste inchangé, PHP a copié l'objet", "est modifié : c'est le même objet", "provoque une erreur", "est détruit"], 1,
     "Les objets ne sont pas copiés au passage en paramètre. Pour une copie, il faut `clone`.")],
  TD("Compte bancaire",
     "Crée une classe `CompteBancaire` qui gère un solde en respectant des règles simples.",
     ["Constructeur : `titulaire` (string), solde de départ à 0",
      "`deposer(float $montant)` refuse un montant ≤ 0 (`InvalidArgumentException`)",
      "`retirer(float $montant)` refuse si le solde est insuffisant (`DomainException`)",
      "`solde(): float` pour lire le solde",
      "Le solde ne doit **pas** être modifiable depuis l'extérieur"],
     code("php", r"""
<?php
declare(strict_types=1);

class CompteBancaire
{
    // à toi
}

$c = new CompteBancaire('Ana');
$c->deposer(100);
$c->retirer(30);
echo $c->solde(); // 70
"""),
     ["Le solde est une propriété `private float $solde = 0;`.",
      "Exception : `throw new DomainException('Solde insuffisant');`",
      "Vérifie la condition AVANT de modifier le solde."],
     code("php", r"""
class CompteBancaire
{
    private float $solde = 0;

    public function __construct(private string $titulaire) {}

    public function deposer(float $montant): void
    {
        if ($montant <= 0) {
            throw new InvalidArgumentException('Montant invalide');
        }
        $this->solde += $montant;
    }

    public function retirer(float $montant): void
    {
        if ($montant <= 0) {
            throw new InvalidArgumentException('Montant invalide');
        }
        if ($montant > $this->solde) {
            throw new DomainException('Solde insuffisant');
        }
        $this->solde -= $montant;
    }

    public function solde(): float
    {
        return $this->solde;
    }
}
"""),
     ["`$c->solde = 1000;` provoque une erreur",
      "`retirer(500)` sur un compte à 70 lève une exception et le solde reste à 70",
      "`deposer(-5)` lève une exception"])),

M("php-encapsulation", T, "Encapsulation & visibilité", 15,
  "Protéger l'état d'un objet pour qu'il soit toujours valide.",
  "Si n'importe qui peut écrire `$user->email = 'nimporte quoi'`, ton objet peut devenir invalide n'importe où dans le code.",
  ["L'état est **private**",
   "On ne le modifie que par des **méthodes** publiques",
   "Chaque méthode **vérifie les règles** (invariants)",
   "L'objet est donc **toujours valide**"],
  ["`public` : accessible partout. `protected` : la classe et ses enfants. `private` : la classe seule.",
   "Un **invariant** est une règle toujours vraie pour l'objet (un email contient un @, un prix n'est pas négatif).",
   "Valide dans le **constructeur** : un objet invalide ne doit jamais exister.",
   "`readonly` (PHP 8.1) : la propriété ne s'écrit qu'une fois, à l'initialisation.",
   "Préfère des méthodes métier (`changerEmail()`) aux setters génériques (`setEmail()`) : le nom dit l'intention."],
  ["Un getter ET un setter pour chaque propriété : c'est une propriété publique avec plus de code.",
   "Valider en dehors de l'objet : la règle finit dupliquée ou oubliée."],
  code("php", r"""
final class Email
{
    public readonly string $valeur;

    public function __construct(string $valeur)
    {
        $valeur = strtolower(trim($valeur));
        if (!filter_var($valeur, FILTER_VALIDATE_EMAIL)) {
            throw new InvalidArgumentException("Email invalide : $valeur");
        }
        $this->valeur = $valeur;
    }
}

final class Utilisateur
{
    public function __construct(private Email $email) {}

    public function changerEmail(Email $nouveau): void
    {
        $this->email = $nouveau;
    }

    public function email(): Email
    {
        return $this->email;
    }
}

$u = new Utilisateur(new Email('Ana@Mail.com'));
echo $u->email()->valeur; // ana@mail.com
"""),
  ["`Email` valide dans son constructeur : un `Email` invalide ne peut pas exister.",
   "`readonly` : on lit `->valeur`, on ne peut pas la réécrire.",
   "`Utilisateur` n'a plus à valider l'email : le type `Email` le garantit."],
  [Q("Où placer la validation d'un objet ?",
     ["Dans le contrôleur", "Dans le constructeur et dans les méthodes qui modifient l'état", "Dans la base de données", "Dans un setter public"], 1,
     "C'est l'objet qui connaît ses règles : il les vérifie à chaque changement d'état."),
   Q("`protected` signifie…",
     ["visible partout", "visible dans la classe et ses classes enfants", "visible dans le même fichier", "modifiable une seule fois"], 1,
     "`protected` ouvre l'accès aux enfants, pas à l'extérieur."),
   Q("Avantage de `changerEmail(Email $e)` sur `setEmail(string $e)` ?",
     ["Aucun", "Il est plus rapide", "Le type garantit la validité et le nom exprime l'intention", "Il évite d'écrire un constructeur"], 2,
     "Le type `Email` est forcément valide, et le nom de la méthode parle le langage du métier.")],
  TD("Prix et panier",
     "Crée un objet `Prix` qui ne peut jamais être négatif, et un `Panier` qui l'utilise.",
     ["`Prix` : propriété `readonly int $centimes` (on stocke en centimes pour éviter les erreurs d'arrondi)",
      "Exception si `$centimes < 0`",
      "`ajouter(Prix $autre): Prix` **renvoie un nouveau** `Prix` sans modifier l'actuel",
      "`Panier` : `ajouterArticle(Prix $p)` et `total(): Prix`, aucune propriété publique"],
     code("php", r"""
<?php
declare(strict_types=1);

final class Prix
{
    // à toi
}

final class Panier
{
    // à toi
}

$panier = new Panier();
$panier->ajouterArticle(new Prix(1999));
$panier->ajouterArticle(new Prix(500));
echo $panier->total()->centimes; // 2499
"""),
     ["`ajouter` fait `return new Prix($this->centimes + $autre->centimes);`",
      "Dans `Panier`, garde une liste `private array $articles = [];`",
      "Calcule le total à la demande en partant de `new Prix(0)`."],
     code("php", r"""
final class Prix
{
    public function __construct(public readonly int $centimes)
    {
        if ($centimes < 0) {
            throw new InvalidArgumentException('Prix négatif');
        }
    }

    public function ajouter(Prix $autre): Prix
    {
        return new Prix($this->centimes + $autre->centimes);
    }
}

final class Panier
{
    /** @var Prix[] */
    private array $articles = [];

    public function ajouterArticle(Prix $prix): void
    {
        $this->articles[] = $prix;
    }

    public function total(): Prix
    {
        $total = new Prix(0);
        foreach ($this->articles as $prix) {
            $total = $total->ajouter($prix);
        }
        return $total;
    }
}
"""),
     ["`new Prix(-1)` lève une exception",
      "`$p->centimes = 5;` provoque une erreur",
      "`ajouter` ne modifie pas l'objet d'origine"])),

M("php-heritage", T, "Héritage & classes abstraites", 15,
  "Savoir quand hériter, et à quoi sert une classe abstraite.",
  "Plusieurs classes partagent une structure et du code. L'héritage évite de le dupliquer, mais mal utilisé il rigidifie tout.",
  ["Une classe **abstraite** définit ce qui est commun",
   "Elle déclare des méthodes **abstraites**, sans corps",
   "Chaque **enfant** (`extends`) les implémente",
   "Le code appelant manipule le **parent** sans connaître l'enfant"],
  ["`extends` : l'enfant récupère les méthodes `public` et `protected` du parent.",
   "Une classe `abstract` ne s'instancie pas : elle sert de base.",
   "`parent::__construct(...)` appelle le constructeur du parent.",
   "Test « est-un » : un `Cercle` **est une** `Forme` → héritage. Une `Voiture` **a un** `Moteur` → composition (une propriété).",
   "`final` interdit d'hériter : bon réflexe par défaut pour les classes non prévues pour ça."],
  ["Hériter juste pour réutiliser une méthode : préfère la composition.",
   "Des hiérarchies sur 3 niveaux ou plus deviennent vite illisibles."],
  code("php", r"""
abstract class Forme
{
    public function __construct(protected string $nom) {}

    abstract public function aire(): float;

    public function decrire(): string
    {
        return sprintf('%s : %.2f m²', $this->nom, $this->aire());
    }
}

final class Cercle extends Forme
{
    public function __construct(private float $rayon)
    {
        parent::__construct('Cercle');
    }

    public function aire(): float
    {
        return M_PI * $this->rayon ** 2;
    }
}

final class Rectangle extends Forme
{
    public function __construct(private float $l, private float $h)
    {
        parent::__construct('Rectangle');
    }

    public function aire(): float
    {
        return $this->l * $this->h;
    }
}

foreach ([new Cercle(1), new Rectangle(2, 3)] as $forme) {
    echo $forme->decrire(), PHP_EOL;
}
"""),
  ["`decrire()` est écrit une seule fois dans le parent, mais appelle l'`aire()` de l'enfant.",
   "La boucle ne sait pas si c'est un cercle ou un rectangle : c'est le **polymorphisme**.",
   "`protected $nom` : visible dans les enfants, pas depuis l'extérieur."],
  [Q("`Forme` est abstraite. Peut-on faire `new Forme('x')` ?",
     ["Oui", "Non, une classe abstraite ne s'instancie pas", "Oui si elle a un constructeur", "Seulement en PHP 8"], 1,
     "Elle sert uniquement de base aux classes enfants."),
   Q("Une `Commande` a une `Adresse`. Que choisir ?",
     ["`Commande extends Adresse`", "`Adresse extends Commande`", "Composition : une propriété `Adresse` dans `Commande`", "Un trait"], 2,
     "« A un » = composition. L'héritage est réservé au « est un »."),
   Q("Dans `decrire()`, `$this->aire()` appelle…",
     ["toujours la méthode abstraite", "la méthode de la classe réelle de l'objet", "une erreur", "la méthode du parent"], 1,
     "PHP choisit la méthode selon la classe réelle de l'objet au moment de l'appel.")],
  TD("Employés et salaires",
     "Modélise des employés dont le salaire se calcule différemment selon leur type.",
     ["Classe abstraite `Employe` avec `nom` et une méthode abstraite `salaireMensuel(): float`",
      "`Salarie` : salaire annuel / 12",
      "`Freelance` : taux journalier × jours travaillés",
      "Méthode commune `fiche(): string` dans `Employe` → « Ana : 2500.00 € »",
      "Calcule la masse salariale d'un tableau d'employés"],
     code("php", r"""
<?php
declare(strict_types=1);

abstract class Employe
{
    // à toi
}

// Salarie, Freelance...

$equipe = [new Salarie('Ana', 30000), new Freelance('Léo', 400, 10)];
// affiche chaque fiche + le total
"""),
     ["`abstract public function salaireMensuel(): float;`",
      "`fiche()` : `sprintf('%s : %.2f €', $this->nom, $this->salaireMensuel())`",
      "Total : `array_sum(array_map(fn(Employe $e) => $e->salaireMensuel(), $equipe))`"],
     code("php", r"""
abstract class Employe
{
    public function __construct(protected string $nom) {}

    abstract public function salaireMensuel(): float;

    public function fiche(): string
    {
        return sprintf('%s : %.2f €', $this->nom, $this->salaireMensuel());
    }
}

final class Salarie extends Employe
{
    public function __construct(string $nom, private float $annuel)
    {
        parent::__construct($nom);
    }

    public function salaireMensuel(): float
    {
        return $this->annuel / 12;
    }
}

final class Freelance extends Employe
{
    public function __construct(string $nom, private float $tjm, private int $jours)
    {
        parent::__construct($nom);
    }

    public function salaireMensuel(): float
    {
        return $this->tjm * $this->jours;
    }
}

$equipe = [new Salarie('Ana', 30000), new Freelance('Léo', 400, 10)];
foreach ($equipe as $e) {
    echo $e->fiche(), PHP_EOL;
}
$total = array_sum(array_map(fn(Employe $e) => $e->salaireMensuel(), $equipe));
echo "Total : $total €";
"""),
     ["Ajouter un nouveau type d'employé ne demande pas de toucher à `fiche()`",
      "`new Employe('x')` est impossible"])),

M("php-interfaces", T, "Interfaces & polymorphisme", 15,
  "Programmer contre un contrat plutôt que contre une classe précise.",
  "Si ton service dépend de `MailjetMailer`, changer de fournisseur oblige à modifier le service. Avec une interface, tu changes seulement l'implémentation.",
  ["L'**interface** décrit le contrat (des méthodes, sans code)",
   "Des classes l'**implémentent** (`implements`)",
   "Ton service **demande l'interface**, pas une classe",
   "On peut **brancher** n'importe quelle implémentation"],
  ["Une interface = une liste de méthodes publiques à fournir. Pas d'état, pas de code.",
   "Une classe peut implémenter **plusieurs** interfaces, mais n'hérite que d'**une** classe.",
   "Interface : ce que ça sait faire. Classe abstraite : ce que c'est, avec du code partagé.",
   "C'est la base de l'injection de dépendances et des repositories en DDD."],
  ["Une interface pour chaque classe « au cas où » : crée-la quand tu as plusieurs implémentations ou besoin de tester.",
   "Mettre dans l'interface des méthodes qu'une seule implémentation utilise."],
  code("php", r"""
interface Notifier
{
    public function envoyer(string $destinataire, string $message): void;
}

final class EmailNotifier implements Notifier
{
    public function envoyer(string $destinataire, string $message): void
    {
        echo "Email à $destinataire : $message\n";
    }
}

final class SmsNotifier implements Notifier
{
    public function envoyer(string $destinataire, string $message): void
    {
        echo "SMS à $destinataire : $message\n";
    }
}

final class AlerteStock
{
    public function __construct(private Notifier $notifier) {}

    public function verifier(string $produit, int $stock): void
    {
        if ($stock < 5) {
            $this->notifier->envoyer('gerant', "Stock bas : $produit ($stock)");
        }
    }
}

(new AlerteStock(new SmsNotifier()))->verifier('Clavier', 2);
"""),
  ["`AlerteStock` ne sait pas si c'est un email ou un SMS.",
   "Pour passer à l'email, on change uniquement la ligne de création.",
   "En test, on passe un faux `Notifier` qui enregistre les messages."],
  [Q("Combien d'interfaces une classe peut-elle implémenter ?",
     ["Une seule", "Deux maximum", "Autant qu'elle veut", "Aucune si elle hérite déjà"], 2,
     "`class A extends B implements C, D, E` est valide."),
   Q("Pourquoi `AlerteStock` reçoit-il un `Notifier` et pas un `SmsNotifier` ?",
     ["Pour la performance", "Pour changer d'implémentation sans modifier `AlerteStock`", "Parce que `SmsNotifier` est final", "C'est obligatoire en PHP"], 1,
     "Il dépend du contrat, pas d'un fournisseur précis."),
   Q("Une interface peut contenir…",
     ["des propriétés privées", "des signatures de méthodes publiques (et des constantes)", "le code des méthodes", "un constructeur avec du code"], 1,
     "Une interface décrit, elle n'implémente pas.")],
  TD("Moyens de paiement",
     "Ton site accepte plusieurs moyens de paiement. Le service de commande ne doit pas savoir lequel est utilisé.",
     ["Interface `PaymentGateway` avec `payer(int $centimes): string` (renvoie un id de transaction)",
      "`StripeGateway` : id préfixé `stripe_`",
      "`FakeGateway` (pour les tests) : mémorise les montants payés dans `public array $paiements`",
      "`CheckoutService` reçoit une `PaymentGateway`, méthode `checkout(int $centimes): string`",
      "`checkout` refuse un montant ≤ 0"],
     code("php", r"""
<?php
declare(strict_types=1);

interface PaymentGateway
{
    // à toi
}

// StripeGateway, FakeGateway, CheckoutService

$fake = new FakeGateway();
$service = new CheckoutService($fake);
$service->checkout(4200);
var_dump($fake->paiements); // [4200]
"""),
     ["`uniqid('stripe_')` génère un id simple.",
      "`FakeGateway` ajoute chaque montant à `$this->paiements[]`.",
      "`public function __construct(private PaymentGateway $gateway) {}`"],
     code("php", r"""
interface PaymentGateway
{
    public function payer(int $centimes): string;
}

final class StripeGateway implements PaymentGateway
{
    public function payer(int $centimes): string
    {
        // appel à l'API Stripe ici
        return uniqid('stripe_');
    }
}

final class FakeGateway implements PaymentGateway
{
    public array $paiements = [];

    public function payer(int $centimes): string
    {
        $this->paiements[] = $centimes;
        return 'fake_' . count($this->paiements);
    }
}

final class CheckoutService
{
    public function __construct(private PaymentGateway $gateway) {}

    public function checkout(int $centimes): string
    {
        if ($centimes <= 0) {
            throw new InvalidArgumentException('Montant invalide');
        }
        return $this->gateway->payer($centimes);
    }
}
"""),
     ["`CheckoutService` ne mentionne jamais Stripe",
      "Tu peux tester `checkout` sans réseau grâce à `FakeGateway`"])),

M("php-namespaces", T, "Namespaces & autoload", 12,
  "Organiser le code en dossiers et laisser Composer charger les classes.",
  "Sans namespace, ta classe `User` entre en conflit avec celle d'une librairie, et tu dois écrire des `require` partout.",
  ["Chaque fichier déclare un **namespace** (`App\\Catalogue`)",
   "Le namespace **suit les dossiers** (norme PSR-4)",
   "`composer.json` associe `App\\` au dossier `src/`",
   "Quand tu utilises une classe, l'**autoloader** trouve et charge le fichier"],
  ["PSR-4 : `App\\Catalogue\\Produit` → `src/Catalogue/Produit.php`. Une classe par fichier, nom du fichier = nom de la classe.",
   "`use App\\Catalogue\\Produit;` permet d'écrire `Produit` sans le chemin complet.",
   "`require __DIR__ . '/vendor/autoload.php';` une seule fois, au point d'entrée.",
   "Après avoir changé la section `autoload` : `composer dump-autoload`.",
   "Symfony le fait déjà : `src/` correspond à `App\\`."],
  ["Namespace qui ne correspond pas au dossier → « Class not found ».",
   "Dans un namespace, `new DateTimeImmutable()` sans `use` cherche `App\\...\\DateTimeImmutable`. Ajoute `use DateTimeImmutable;` ou écris `\\DateTimeImmutable`."],
  code("php", r"""
// composer.json
// {
//   "autoload": { "psr-4": { "App\\": "src/" } }
// }

// src/Catalogue/Produit.php
namespace App\Catalogue;

use DateTimeImmutable;

final class Produit
{
    public function __construct(
        private string $nom,
        private DateTimeImmutable $creeLe = new DateTimeImmutable(),
    ) {}
}

// public/index.php
require __DIR__ . '/../vendor/autoload.php';

use App\Catalogue\Produit;

$produit = new Produit('Clavier');
"""),
  ["Le dossier `src/Catalogue` correspond au namespace `App\\Catalogue`.",
   "`use DateTimeImmutable;` importe la classe globale de PHP.",
   "`index.php` ne fait aucun `require` de `Produit.php` : l'autoloader s'en charge."],
  [Q("Avec `App\\` → `src/`, où se trouve `App\\Infra\\Doctrine\\OrderRepo` ?",
     ["src/App/Infra/Doctrine/OrderRepo.php", "src/Infra/Doctrine/OrderRepo.php", "Infra/Doctrine/OrderRepo.php", "vendor/App/OrderRepo.php"], 1,
     "Le préfixe `App\\` est remplacé par `src/`, le reste suit les dossiers."),
   Q("Tu viens d'ajouter un mapping PSR-4 dans composer.json. Que lancer ?",
     ["composer install --force", "composer dump-autoload", "php -l", "Rien"], 1,
     "`dump-autoload` régénère la table de chargement."),
   Q("Dans `namespace App\\Domain;`, `new DateTimeImmutable()` sans `use`…",
     ["trouve la classe globale", "cherche `App\\Domain\\DateTimeImmutable` → erreur", "cherche dans vendor", "cherche dans le namespace parent"], 1,
     "Pour les classes, PHP ne retombe pas sur l'espace global : il faut `use` ou `\\`.")],
  TD("Ranger un mini-projet",
     "Organise un petit projet avec Composer et PSR-4, sans aucun `require` de classe.",
     ["`composer.json` avec le préfixe `App\\` vers `src/`",
      "`src/Catalogue/Produit.php` (namespace `App\\Catalogue`)",
      "`src/Catalogue/Catalogue.php` qui stocke des `Produit`, avec `ajouter()` et `compter()`",
      "`index.php` qui charge l'autoload et utilise les deux classes",
      "Lance `composer dump-autoload` puis `php index.php`"],
     code("plaintext", r"""
mon-projet/
├── composer.json
├── index.php
└── src/
    └── Catalogue/
        ├── Produit.php
        └── Catalogue.php
"""),
     ["`composer.json` minimal : `{\"autoload\": {\"psr-4\": {\"App\\\\\": \"src/\"}}}`",
      "Dans `Catalogue.php`, `Produit` est dans le même namespace : pas besoin de `use`.",
      "`index.php` est à la racine : `require __DIR__ . '/vendor/autoload.php';`"],
     code("php", r"""
// composer.json
// { "autoload": { "psr-4": { "App\\": "src/" } } }

// src/Catalogue/Produit.php
namespace App\Catalogue;

final class Produit
{
    public function __construct(public readonly string $nom) {}
}

// src/Catalogue/Catalogue.php
namespace App\Catalogue;

final class Catalogue
{
    /** @var Produit[] */
    private array $produits = [];

    public function ajouter(Produit $p): void
    {
        $this->produits[] = $p;
    }

    public function compter(): int
    {
        return count($this->produits);
    }
}

// index.php
require __DIR__ . '/vendor/autoload.php';

use App\Catalogue\Catalogue;
use App\Catalogue\Produit;

$catalogue = new Catalogue();
$catalogue->ajouter(new Produit('Clavier'));
echo $catalogue->compter(); // 1
"""),
     ["`php index.php` fonctionne sans `require` de tes classes",
      "Renomme le dossier `Catalogue` sans changer le namespace : tu obtiens « Class not found » (essaie)"])),

M("php-di", T, "Injection de dépendances", 15,
  "Comprendre pourquoi on passe les dépendances au constructeur au lieu de les créer.",
  "Une classe qui fait `new PDO(...)` ou `new Mailer()` à l'intérieur est impossible à tester et à reconfigurer.",
  ["La classe **déclare** ce dont elle a besoin dans son constructeur",
   "Quelqu'un d'autre **crée** les dépendances",
   "et les **injecte** à la création",
   "En Symfony, le **conteneur** le fait automatiquement (autowiring)"],
  ["Une classe de service ne fait pas `new` de ses services : elle les reçoit.",
   "Les objets valeur (`Email`, `Prix`, `DateTimeImmutable`) peuvent être créés avec `new` partout : ce ne sont pas des services.",
   "Interface + injection = changer d'implémentation sans toucher la classe.",
   "En Symfony, type-hinter le constructeur suffit : le conteneur trouve le service."],
  ["Injecter le conteneur lui-même et piocher dedans : ça cache les vraies dépendances.",
   "Un constructeur avec 8 dépendances : la classe fait trop de choses, découpe-la."],
  code("php", r"""
// AVANT : couplé, impossible à tester sans vraie base ni vrai serveur mail
final class InscriptionService
{
    public function inscrire(string $email): void
    {
        $repo = new MysqlUserRepository(new PDO('mysql:...'));
        $repo->save($email);
        (new SmtpMailer())->send($email, 'Bienvenue');
    }
}

// APRÈS : les dépendances arrivent de l'extérieur
final class InscriptionService
{
    public function __construct(
        private UserRepository $users,
        private Mailer $mailer,
    ) {}

    public function inscrire(string $email): void
    {
        $this->users->save($email);
        $this->mailer->send($email, 'Bienvenue');
    }
}

// En test :
$service = new InscriptionService(new InMemoryUserRepository(), new FakeMailer());
"""),
  ["`UserRepository` et `Mailer` sont des interfaces.",
   "En production, Symfony injecte les vraies implémentations.",
   "En test, on injecte des versions en mémoire : rapide et sans effets de bord."],
  [Q("Quelle classe peut raisonnablement être créée avec `new` dans un service ?",
     ["Un repository Doctrine", "Un client HTTP", "Un objet valeur comme `Email` ou `DateTimeImmutable`", "Le mailer"], 2,
     "Les objets valeur n'ont pas de dépendances externes à remplacer."),
   Q("Avantage principal de l'injection ?",
     ["Le code est plus court", "On peut remplacer les dépendances (tests, autre implémentation) sans modifier la classe", "PHP va plus vite", "On évite les namespaces"], 1,
     "La classe ne décide plus quelle implémentation utiliser."),
   Q("En Symfony, comment un service reçoit-il un autre service ?",
     ["`$this->get('service')`", "En le type-hintant dans son constructeur (autowiring)", "Avec `new`", "Via une variable globale"], 1,
     "Le conteneur lit les types du constructeur et injecte ce qui correspond.")],
  TD("Rendre testable",
     "Ce service est impossible à tester. Refactorise-le avec l'injection de dépendances.",
     ["Extrais l'accès aux données dans une interface `VentesRepository` : `totalDu(DateTimeImmutable $jour): float`",
      "Extrais l'horloge dans une interface `Horloge` : `aujourdhui(): DateTimeImmutable` (sinon le test dépend du jour)",
      "Injecte les deux dans le constructeur de `RapportService`",
      "Écris un petit test à la main avec de fausses implémentations"],
     code("php", r"""
final class RapportService
{
    public function genererDuJour(): string
    {
        $date = new DateTimeImmutable('today');
        $pdo = new PDO('mysql:host=localhost;dbname=shop', 'root', '');
        $stmt = $pdo->prepare('SELECT SUM(total) FROM commandes WHERE DATE(passee_le) = ?');
        $stmt->execute([$date->format('Y-m-d')]);
        $total = (float) $stmt->fetchColumn();

        return sprintf('Ventes du %s : %.2f €', $date->format('d/m/Y'), $total);
    }
}
"""),
     ["La requête SQL part dans une classe `PdoVentesRepository implements VentesRepository`.",
      "Fausse horloge en une ligne : une classe anonyme `new class implements Horloge { ... }`.",
      "Vérifie le résultat avec `assert(...)`."],
     code("php", r"""
interface VentesRepository
{
    public function totalDu(DateTimeImmutable $jour): float;
}

interface Horloge
{
    public function aujourdhui(): DateTimeImmutable;
}

final class RapportService
{
    public function __construct(
        private VentesRepository $ventes,
        private Horloge $horloge,
    ) {}

    public function genererDuJour(): string
    {
        $jour = $this->horloge->aujourdhui();
        $total = $this->ventes->totalDu($jour);

        return sprintf('Ventes du %s : %.2f €', $jour->format('d/m/Y'), $total);
    }
}

// Test à la main
$service = new RapportService(
    new class implements VentesRepository {
        public function totalDu(DateTimeImmutable $jour): float { return 1234.5; }
    },
    new class implements Horloge {
        public function aujourdhui(): DateTimeImmutable { return new DateTimeImmutable('2026-01-15'); }
    },
);
assert($service->genererDuJour() === 'Ventes du 15/01/2026 : 1234.50 €');
"""),
     ["`RapportService` ne contient plus `new PDO` ni `new DateTimeImmutable('today')`",
      "Le test donne le même résultat quel que soit le jour"])),
]

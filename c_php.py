from common import V2, P, L, D, N, E, LANE, F, TD, RUN
from c_php_v1 import MODULES as V1

v1 = {m["id"]: m for m in V1}

# ---------------------------------------------------------------- classes
classes = V2(v1["php-classes"],
  prereq=[
    P("Variable", "Une boîte avec un nom qui contient une valeur : `$prix = 50;`. En PHP, les variables commencent par `$`."),
    P("Fonction", "Un bloc de code réutilisable qui reçoit des paramètres et renvoie un résultat : `function tva(float $p): float { return $p * 0.2; }`."),
    P("Type", "La nature d'une valeur : `string` (texte), `int` (entier), `float` (décimal), `bool` (vrai/faux), `array` (liste). On peut l'écrire devant un paramètre pour que PHP vérifie."),
    P("Tableau associatif", "Un tableau dont les cases ont un nom : `['nom' => 'Clavier', 'prix' => 50]`. C'est ce qu'on utilisait avant les objets pour regrouper des données."),
    P("Exception", "Une erreur qu'on **lance** (`throw`) pour arrêter le code quand quelque chose est impossible. On la rattrape avec `try / catch`."),
  ],
  diagram=D(
    nodes=[
      N("cls", 0, 0, "class Produit", "le plan", kind="doc"),
      N("new1", 1, 0, "new Produit('Clavier', 50)", "", kind="pill"),
      N("obj1", 2, 0, "$clavier", "nom = Clavier\nprixHT = 50"),
      N("new2", 1, 1, "new Produit('Souris', 20)", "", kind="pill"),
      N("obj2", 2, 1, "$souris", "nom = Souris\nprixHT = 20"),
      N("call", 3, 0, "$clavier->prixTTC()", "60", kind="pill", color="good"),
    ],
    edges=[E("cls", "new1", "1 plan"), E("new1", "obj1", "2 crée"), E("cls", "new2"), E("new2", "obj2"), E("obj1", "call", "3 méthode")],
    caption="Une classe, deux objets indépendants. La méthode travaille sur l'objet qui l'appelle (`$this`)."),
  lessons=[
    L("Pourquoi des objets ?", r"""
Imagine que tu gères des produits avec des tableaux :

```php
$clavier = ['nom' => 'Clavier', 'prixHT' => 50.0];
$souris  = ['nom' => 'Souris',  'prixHT' => 20.0];

function prixTTC(array $produit): float
{
    return $produit['prixHT'] * 1.2;
}
```

Ça marche, mais rien n'empêche quelqu'un d'écrire `$clavier['prixHT'] = -5;` ou d'oublier la clé `prixHT` dans un nouveau produit. Les **données** (le tableau) et le **code qui les manipule** (la fonction) vivent séparément : n'importe qui peut casser l'un sans que l'autre s'en aperçoive.

Un **objet** regroupe les deux : ses données (les **propriétés**) et les opérations qu'on a le droit de faire dessus (les **méthodes**). La **classe** est le plan de construction : elle décrit ce que chaque objet contiendra et saura faire.
"""),
    L("Classe, objet, constructeur", r"""
La classe se déclare une fois. Chaque `new` fabrique un **objet** à partir du plan, en appelant le **constructeur** `__construct`, qui remplit l'état de départ.

```php
class Produit
{
    private string $nom;
    private float $prixHT;

    public function __construct(string $nom, float $prixHT)
    {
        $this->nom = $nom;        // "dans CET objet, la propriété nom vaut $nom"
        $this->prixHT = $prixHT;
    }
}

$clavier = new Produit('Clavier', 50.0);   // appelle __construct('Clavier', 50.0)
$souris  = new Produit('Souris', 20.0);    // un deuxième objet, indépendant
```

Deux objets de la même classe ont la **même forme** (les mêmes propriétés) mais chacun a **ses propres valeurs**. Modifier `$clavier` ne touche jamais `$souris`.

Depuis PHP 8, la **promotion de constructeur** raccourcit tout ça : écrire `private string $nom` directement dans les paramètres déclare la propriété et l'assigne en une ligne. Le code de l'exemple utilise cette forme courte ; les deux sont équivalentes.
"""),
    L("$this : « l'objet sur lequel on travaille »", r"""
Dans une méthode, `$this` désigne l'objet qui a reçu l'appel. Quand tu écris `$clavier->prixTTC()`, à l'intérieur de `prixTTC`, `$this` **est** `$clavier`. Quand tu écris `$souris->prixTTC()`, `$this` est `$souris`. La méthode n'est écrite qu'une fois, mais elle s'adapte à l'objet qui l'appelle.

- `$this->prixHT` : la propriété de l'objet courant.
- `$prixHT` tout seul : une variable **locale** à la méthode, qui n'a rien à voir avec la propriété. C'est l'erreur n°1 des débutants.
- `->` sert à accéder à une propriété ou une méthode **d'un objet** ; `::` sert pour ce qui appartient à la **classe** elle-même (constantes, méthodes statiques, `parent::`).
"""),
    L("Les objets ne sont pas copiés", r"""
Avec un tableau, passer la valeur à une fonction en fait une **copie** : la fonction peut modifier sa copie sans toucher l'original. Avec un objet, c'est différent : la variable contient une **référence** vers l'objet. Si tu passes `$clavier` à une fonction et que celle-ci appelle `$p->renommer('X')`, c'est **le même objet** qui est modifié.

```php
function renommerEnX(Produit $p): void { $p->renommer('X'); }

renommerEnX($clavier);
echo $clavier->nom(); // X  (l'original a changé)
```

C'est voulu : ça évite de copier de gros objets. Quand tu veux vraiment une copie indépendante, tu l'écris explicitement : `$copie = clone $clavier;`.

`declare(strict_types=1);` en haut d'un fichier demande à PHP de refuser un mauvais type (par exemple la chaîne `"50"` là où on attend un `float`) au lieu de le convertir en silence. Mets-le toujours : les erreurs apparaissent tout de suite au lieu de se cacher.
"""),
  ],
  recap=[
    "Une **classe** est un plan ; `new` fabrique un **objet** à partir de ce plan en appelant `__construct`.",
    "Chaque objet a ses **propres valeurs** ; deux `new` donnent deux objets indépendants.",
    "`$this` = l'objet qui reçoit l'appel. `$this->nom` est la propriété, `$nom` une variable locale.",
    "`->` pour un objet, `::` pour la classe (constantes, statique, `parent::`).",
    "Un objet passé en paramètre **n'est pas copié** ; pour une copie, `clone`.",
  ],
  example=F("src/Produit.php", "php", v1["php-classes"]["example"]["code"]),
  td1=dict(path="CompteBancaire.php", run=RUN("php", tests=r"""
$c = new CompteBancaire('Ana');
check('Le solde de départ est 0', $c->solde() === 0.0 || $c->solde() === 0);
$c->deposer(100);
check('deposer(100) donne un solde de 100', (float) $c->solde() === 100.0);
$c->retirer(30);
check('retirer(30) donne un solde de 70', (float) $c->solde() === 70.0);
check('retirer(500) lève une DomainException', throws(fn() => $c->retirer(500), DomainException::class));
check('le solde reste à 70 après le refus', (float) $c->solde() === 70.0);
check('deposer(-5) lève une InvalidArgumentException', throws(fn() => $c->deposer(-5), InvalidArgumentException::class));
$rp = new ReflectionProperty(CompteBancaire::class, 'solde');
check('la propriété solde est private', $rp->isPrivate());
""")),
  tds=[
    TD(2, "Panier avec quantités",
       "Un panier contient des lignes (produit + quantité). Ajouter deux fois le même produit doit **augmenter la quantité** au lieu de créer une deuxième ligne. C'est le même principe que le compte bancaire, mais l'état est une liste, pas un nombre.",
       ["`Ligne` : propriétés `nom`, `prixUnitaire` (float), `quantite` (int), méthode `ajouter(int $n)` et `sousTotal(): float`",
        "`Panier::ajouter(string $nom, float $prix, int $quantite = 1)` : si une ligne porte déjà ce nom, augmente sa quantité ; sinon crée la ligne",
        "`Panier::total(): float` et `Panier::nombreDArticles(): int` (somme des quantités)",
        "Une quantité ≤ 0 lève une `InvalidArgumentException`",
        "Les lignes ne sont pas accessibles de l'extérieur"],
       [F("Panier.php", "php", r"""
<?php
declare(strict_types=1);

final class Ligne
{
    // à toi
}

final class Panier
{
    // à toi
}

$p = new Panier();
$p->ajouter('Clavier', 50.0);
$p->ajouter('Souris', 20.0, 2);
$p->ajouter('Clavier', 50.0);     // même produit : quantité 2
echo $p->total(), PHP_EOL;        // 140
echo $p->nombreDArticles();       // 4
""")],
       ["Garde les lignes dans un tableau indexé par le nom : `$this->lignes[$nom]`. `isset($this->lignes[$nom])` dit si le produit est déjà là.",
        "`sousTotal()` = `prixUnitaire * quantite` ; le total du panier additionne les sous-totaux avec une boucle `foreach`.",
        "La vérification de la quantité se fait à **un seul endroit** : dans `Ligne` (constructeur et `ajouter`). `Panier` lui fait confiance."],
       [F("Panier.php", "php", r"""
<?php
declare(strict_types=1);

final class Ligne
{
    private int $quantite;

    public function __construct(
        private string $nom,
        private float $prixUnitaire,
        int $quantite,
    ) {
        $this->quantite = 0;
        $this->ajouter($quantite);
    }

    public function ajouter(int $n): void
    {
        if ($n <= 0) {
            throw new InvalidArgumentException('Quantité invalide');
        }
        $this->quantite += $n;
    }

    public function quantite(): int { return $this->quantite; }

    public function sousTotal(): float
    {
        return $this->prixUnitaire * $this->quantite;
    }
}

final class Panier
{
    /** @var array<string, Ligne> */
    private array $lignes = [];

    public function ajouter(string $nom, float $prix, int $quantite = 1): void
    {
        if (isset($this->lignes[$nom])) {
            $this->lignes[$nom]->ajouter($quantite);
            return;
        }
        $this->lignes[$nom] = new Ligne($nom, $prix, $quantite);
    }

    public function total(): float
    {
        $total = 0.0;
        foreach ($this->lignes as $ligne) {
            $total += $ligne->sousTotal();
        }
        return $total;
    }

    public function nombreDArticles(): int
    {
        $n = 0;
        foreach ($this->lignes as $ligne) {
            $n += $ligne->quantite();
        }
        return $n;
    }
}

$p = new Panier();
$p->ajouter('Clavier', 50.0);
$p->ajouter('Souris', 20.0, 2);
$p->ajouter('Clavier', 50.0);
echo $p->total(), PHP_EOL;        // 140
echo $p->nombreDArticles();       // 4
""")],
       ["Ajouter deux fois « Clavier » donne une seule ligne avec quantité 2",
        "`ajouter('X', 10.0, 0)` lève une exception",
        "`$p->lignes` provoque une erreur depuis l'extérieur"],
       run=RUN("php", tests=r"""
$p = new Panier();
$p->ajouter('Clavier', 50.0);
$p->ajouter('Souris', 20.0, 2);
$p->ajouter('Clavier', 50.0);
check('total() vaut 140', abs($p->total() - 140.0) < 0.001, 'obtenu : ' . $p->total());
check('nombreDArticles() vaut 4', $p->nombreDArticles() === 4, 'obtenu : ' . $p->nombreDArticles());
check('une quantité de 0 est refusée', throws(fn() => $p->ajouter('X', 10.0, 0), InvalidArgumentException::class));
check('une quantité négative est refusée', throws(fn() => $p->ajouter('Y', 10.0, -2), InvalidArgumentException::class));
check('les lignes sont privées', (new ReflectionProperty(Panier::class, 'lignes'))->isPrivate());
$vide = new Panier();
check('un panier vide a un total de 0', (float) $vide->total() === 0.0);
"""), expected="140\n4"),
    TD(3, "Historique d'opérations et relevé",
       "Reprends le `CompteBancaire` du niveau 1 et fais-lui **mémoriser chaque opération** sous forme d'objets `Operation`. Le compte doit pouvoir produire un relevé. Tu combines ici : objets qui contiennent d'autres objets, `DateTimeImmutable`, et un calcul dérivé de l'historique (le solde n'est plus stocké : il est **recalculé**).",
       ["`Operation` : `type` (`'depot'` ou `'retrait'`), `montant` (float), `date` (`DateTimeImmutable`), méthode `montantSigne(): float` (+ pour un dépôt, − pour un retrait)",
        "`CompteBancaire` ne stocke **plus** `$solde` : `solde()` additionne les `montantSigne()` de l'historique",
        "`deposer()` et `retirer()` ajoutent une `Operation` (mêmes règles qu'au niveau 1 : montants > 0, retrait ≤ solde)",
        "`releve(): string` renvoie une ligne par opération au format `JJ/MM/AAAA  depot    +100.00` puis une dernière ligne `Solde : 70.00`",
        "`operations(): array` renvoie une **copie** de l'historique (le code extérieur ne doit pas pouvoir le modifier)"],
       [F("CompteBancaire.php", "php", r"""
<?php
declare(strict_types=1);

final class Operation
{
    // à toi
}

final class CompteBancaire
{
    // à toi : plus de propriété $solde !

    public function __construct(private string $titulaire) {}
}

$c = new CompteBancaire('Ana');
$c->deposer(100);
$c->retirer(30);
echo $c->releve();
""")],
       ["`new DateTimeImmutable()` donne la date du moment ; `$date->format('d/m/Y')` l'affiche.",
        "`solde()` : `array_sum(array_map(fn(Operation $o) => $o->montantSigne(), $this->operations))`.",
        "`sprintf('%s  %-8s %+.2f', ...)` : `%-8s` cale le type sur 8 caractères, `%+.2f` affiche le signe et 2 décimales.",
        "Renvoyer un tableau d'objets avec `return $this->operations;` renvoie une copie du **tableau** : l'extérieur ne peut pas ajouter de ligne à ton historique. C'est suffisant ici."],
       [F("CompteBancaire.php", "php", r"""
<?php
declare(strict_types=1);

final class Operation
{
    public function __construct(
        private string $type,
        private float $montant,
        private DateTimeImmutable $date,
    ) {
        if (!in_array($type, ['depot', 'retrait'], true)) {
            throw new InvalidArgumentException("Type inconnu : $type");
        }
        if ($montant <= 0) {
            throw new InvalidArgumentException('Montant invalide');
        }
    }

    public function montantSigne(): float
    {
        return $this->type === 'depot' ? $this->montant : -$this->montant;
    }

    public function ligne(): string
    {
        return sprintf('%s  %-8s %+.2f', $this->date->format('d/m/Y'), $this->type, $this->montantSigne());
    }
}

final class CompteBancaire
{
    /** @var Operation[] */
    private array $operations = [];

    public function __construct(private string $titulaire) {}

    public function deposer(float $montant): void
    {
        $this->operations[] = new Operation('depot', $montant, new DateTimeImmutable());
    }

    public function retirer(float $montant): void
    {
        if ($montant <= 0) {
            throw new InvalidArgumentException('Montant invalide');
        }
        if ($montant > $this->solde()) {
            throw new DomainException('Solde insuffisant');
        }
        $this->operations[] = new Operation('retrait', $montant, new DateTimeImmutable());
    }

    public function solde(): float
    {
        return array_sum(array_map(fn(Operation $o) => $o->montantSigne(), $this->operations));
    }

    /** @return Operation[] */
    public function operations(): array
    {
        return $this->operations;
    }

    public function releve(): string
    {
        $lignes = array_map(fn(Operation $o) => $o->ligne(), $this->operations);
        $lignes[] = sprintf('Solde : %.2f', $this->solde());
        return implode(PHP_EOL, $lignes) . PHP_EOL;
    }
}

$c = new CompteBancaire('Ana');
$c->deposer(100);
$c->retirer(30);
echo $c->releve();
""")],
       ["Le relevé affiche 2 lignes d'opérations puis « Solde : 70.00 »",
        "Il n'y a plus de propriété `$solde` : supprime-la et vérifie que tout marche encore",
        "Un retrait supérieur au solde ne crée **pas** d'opération"],
       run=RUN("php", tests=r"""
$c = new CompteBancaire('Ana');
$c->deposer(100);
$c->retirer(30);
check('solde() recalculé vaut 70', abs($c->solde() - 70.0) < 0.001, 'obtenu : ' . $c->solde());
check('2 opérations enregistrées', count($c->operations()) === 2);
check('operations() contient des Operation', $c->operations()[0] instanceof Operation);
check('montantSigne() du retrait est négatif', $c->operations()[1]->montantSigne() < 0);
$r = $c->releve();
check('le relevé se termine par "Solde : 70.00"', str_contains($r, 'Solde : 70.00'), $r);
check('le relevé contient +100.00', str_contains($r, '+100.00'), $r);
check('le relevé contient -30.00', str_contains($r, '-30.00'), $r);
check('retirer(500) est refusé', throws(fn() => $c->retirer(500), DomainException::class));
check('le refus n\'a pas ajouté d\'opération', count($c->operations()) === 2);
check('plus de propriété $solde', !property_exists(CompteBancaire::class, 'solde'));
$ops = $c->operations(); $ops[] = 'intrus';
check('modifier le tableau renvoyé ne change pas le compte', count($c->operations()) === 2);
"""), expected="12/11/2026  depot    +100.00\n12/11/2026  retrait  -30.00\nSolde : 70.00"),
  ])

# ---------------------------------------------------------------- encapsulation
encaps = V2(v1["php-encapsulation"],
  prereq=[
    P("Propriété / méthode", "Une propriété est une variable qui appartient à un objet (`$this->email`) ; une méthode est une fonction qui appartient à l'objet (`$this->changerEmail()`). Vu au module Classes & objets."),
    P("Getter / setter", "Un *getter* est une méthode qui lit une propriété (`getEmail()`), un *setter* une méthode qui la modifie (`setEmail($e)`). Pratique, mais on va voir que les setters génériques sont un piège."),
    P("Invariant", "Une règle qui doit **toujours** être vraie pour un objet : « un prix n'est jamais négatif », « un email contient un @ ». Si un objet viole un invariant, il est dans un état impossible et tout le code qui l'utilise devient faux."),
    P("`final`", "Mot-clé devant `class` qui interdit d'en hériter. Bon réflexe par défaut : tu lèves l'interdiction plus tard si besoin."),
    P("`filter_var`", "Fonction PHP qui vérifie ou nettoie une valeur selon un filtre : `filter_var($s, FILTER_VALIDATE_EMAIL)` renvoie l'email ou `false`."),
  ],
  diagram=D(
    nodes=[
      N("ext", 0, 0, "Code extérieur", "contrôleur, service…", kind="actor"),
      N("set", 1, 0, "$u->email = 'x'", "accès direct", kind="pill", color="bad"),
      N("meth", 1, 1, "$u->changerEmail(new Email('x'))", "", kind="pill", color="good"),
      N("obj", 3, 0, "Utilisateur", "private Email $email", span=1),
      N("rule", 3, 1, "Email valide ?", "vérifié dans le constructeur d'Email", kind="note", color="good"),
    ],
    edges=[E("ext", "set"), E("set", "obj", "refusé (private)", color="bad", dashed=True), E("ext", "meth"), E("meth", "rule", "1 valide"), E("rule", "obj", "2 modifie", color="good")],
    caption="L'état est privé : la seule porte d'entrée est une méthode, qui vérifie les règles avant de modifier."),
  lessons=[
    L("Le problème des propriétés publiques", r"""
Reprends le `Produit` du module précédent, mais avec une propriété publique :

```php
class Produit
{
    public float $prixHT;
}

$p = new Produit();
$p->prixHT = -50;        // personne ne peut l'empêcher
```

À partir de là, `prixTTC()` renvoie un nombre négatif, le total du panier est faux, la facture est fausse… et l'erreur se voit trois écrans plus loin, là où on ne cherche pas. Le code qui a écrit `-50` peut être n'importe où dans le projet.

L'**encapsulation** consiste à cacher l'état de l'objet (`private`) et à n'autoriser sa modification qu'à travers des **méthodes**, qui vérifient que la règle est respectée. L'objet devient responsable de sa propre validité : un `Produit` ne peut tout simplement pas exister avec un prix négatif.
"""),
    L("Les trois niveaux de visibilité", r"""
Chaque propriété ou méthode a une **visibilité** :

- `public` : accessible depuis n'importe où. À réserver aux méthodes qui forment l'« interface » de l'objet, ce qu'il sait faire.
- `protected` : accessible depuis la classe **et ses classes enfants** (voir le module Héritage), mais pas depuis l'extérieur.
- `private` : accessible uniquement depuis la classe elle-même. C'est la visibilité par défaut à choisir pour les propriétés.

Règle pratique : **toutes les propriétés en `private`**, et on n'ouvre que ce qui est nécessaire. Si tu hésites, mets `private` : passer en `protected` ou `public` plus tard est facile ; l'inverse casse du code.

PHP 8.1 ajoute `readonly` : une propriété qu'on ne peut écrire **qu'une seule fois**, à l'initialisation. Idéal pour une valeur qui ne doit jamais changer après la création (un identifiant, une adresse email validée). On peut la lire librement (`$email->valeur`) sans getter : puisqu'elle ne peut pas être modifiée, la rendre publique en lecture ne présente aucun risque.
"""),
    L("Valider dans le constructeur : un objet invalide n'existe pas", r"""
Le meilleur endroit pour vérifier une règle, c'est au moment où l'objet est créé. Si le constructeur lève une exception quand la valeur est mauvaise, alors **aucun** objet invalide ne peut exister dans tout le programme : tout code qui tient un `Email` en main sait qu'il est valide, sans avoir à revérifier.

```php
final class Email
{
    public readonly string $valeur;

    public function __construct(string $valeur)
    {
        $valeur = strtolower(trim($valeur));                 // 1. normaliser
        if (!filter_var($valeur, FILTER_VALIDATE_EMAIL)) {   // 2. vérifier
            throw new InvalidArgumentException("Email invalide : $valeur");
        }
        $this->valeur = $valeur;                             // 3. seulement si OK
    }
}
```

Note l'enchaînement : on **normalise** (minuscules, espaces retirés), on **vérifie**, et on n'assigne qu'après. Si la vérification échoue, l'exception sort du constructeur et le `new` ne renvoie rien : la variable ne reçoit jamais d'objet cassé.

Les règles qui ne concernent pas qu'une valeur mais un **changement** d'état se vérifient dans la méthode qui fait ce changement (par exemple « on ne peut retirer que si le solde suffit » dans `retirer()`).
"""),
    L("Méthodes métier plutôt que setters", r"""
Comparer ces deux versions :

```php
// Version setter : décrit la mécanique
$commande->setStatut('expediee');
$commande->setDateExpedition(new DateTimeImmutable());

// Version métier : décrit l'intention
$commande->expedier();
```

La deuxième est meilleure pour trois raisons. Elle **dit ce qui se passe** avec les mots du métier. Elle **garde les règles ensemble** : `expedier()` peut vérifier que la commande est payée, fixer la date et changer le statut en une seule opération cohérente, alors qu'avec des setters, rien n'empêche de changer le statut sans la date. Et elle est **plus facile à retrouver** : chercher « qui expédie des commandes ? » revient à chercher `->expedier(`.

Un objet qui n'a qu'un getter et un setter par propriété s'appelle un **modèle anémique** : c'est une propriété publique avec plus de lignes. On y reviendra en DDD (module Entités riches). Pour l'instant, retiens : quand tu es tenté d'écrire `setX()`, demande-toi quelle **action métier** change X, et nomme la méthode d'après cette action.
"""),
  ],
  recap=[
    "Toutes les propriétés en `private` ; on n'ouvre que ce qui est nécessaire.",
    "Un **invariant** se vérifie là où l'état change : constructeur et méthodes de modification.",
    "Si le constructeur refuse les valeurs invalides, un objet invalide **ne peut pas exister**.",
    "`readonly` : écrite une fois, lisible partout, impossible à modifier.",
    "Préfère une **méthode métier** (`expedier()`) à des setters (`setStatut()`).",
  ],
  example=[F("src/Email.php", "php", r"""
<?php
declare(strict_types=1);

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
"""), F("src/Utilisateur.php", "php", r"""
<?php
declare(strict_types=1);

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
"""), F("demo.php", "php", r"""
<?php
$u = new Utilisateur(new Email('Ana@Mail.com'));
echo $u->email()->valeur; // ana@mail.com

try {
    $u->changerEmail(new Email('pas un email'));
} catch (InvalidArgumentException $e) {
    echo $e->getMessage();  // Email invalide : pas un email
}
""")],
  notes=["`Email` valide dans son constructeur : un `Email` invalide ne peut pas exister (fichier `Email.php`).",
         "`readonly` : on lit `->valeur` directement, on ne peut pas la réécrire.",
         "`Utilisateur` n'a plus à valider l'email : le type `Email` le garantit. `changerEmail` est une méthode métier, pas un setter.",
         "Dans `demo.php`, le `new Email('pas un email')` échoue **avant** d'atteindre `changerEmail` : l'utilisateur garde son ancien email."],
  td1=dict(path="Prix.php", run=RUN("php", tests=r"""
check('new Prix(-1) lève une exception', throws(fn() => new Prix(-1), InvalidArgumentException::class));
$a = new Prix(1999); $b = new Prix(500);
$c = $a->ajouter($b);
check('ajouter renvoie un nouveau Prix', $c instanceof Prix && $c !== $a);
check('la somme vaut 2499', $c->centimes === 2499);
check('ajouter ne modifie pas l\'original', $a->centimes === 1999);
$rp = new ReflectionProperty(Prix::class, 'centimes');
check('centimes est readonly', $rp->isReadOnly());
$panier = new Panier();
$panier->ajouterArticle(new Prix(1999));
$panier->ajouterArticle(new Prix(500));
check('total() du panier vaut 2499', $panier->total()->centimes === 2499);
check('aucune propriété publique dans Panier', count((new ReflectionClass(Panier::class))->getProperties(ReflectionProperty::IS_PUBLIC)) === 0);
""")),
  tds=[
    TD(2, "Mot de passe et utilisateur",
       "Un `Utilisateur` a un mot de passe. Le mot de passe en clair ne doit **jamais** être stocké : seule son empreinte (hash) l'est. Tu écris un objet `MotDePasse` qui applique les règles de complexité, et un `Utilisateur` qui l'utilise. C'est l'encapsulation appliquée à un cas où une fuite d'état serait grave.",
       ["`MotDePasse::depuisClair(string $clair): self` : refuse moins de 8 caractères ou sans chiffre (`InvalidArgumentException`), stocke `password_hash($clair, PASSWORD_DEFAULT)`",
        "`MotDePasse::depuisHash(string $hash): self` : recrée l'objet depuis la base (pas de vérification de complexité, le hash est déjà là)",
        "`MotDePasse::verifier(string $clair): bool` avec `password_verify`",
        "Le constructeur est `private` : on ne crée l'objet **que** par les deux méthodes nommées",
        "`Utilisateur::changerMotDePasse(string $ancien, string $nouveau)` : refuse si `$ancien` ne correspond pas (`DomainException`)",
        "Aucun getter ne renvoie le hash ni le clair, sauf `hash(): string` pour la sauvegarde en base"],
       [F("MotDePasse.php", "php", r"""
<?php
declare(strict_types=1);

final class MotDePasse
{
    // constructeur private + 2 méthodes statiques de création
}

final class Utilisateur
{
    public function __construct(private string $email, private MotDePasse $motDePasse) {}

    // changerMotDePasse(...)
}

$u = new Utilisateur('ana@mail.com', MotDePasse::depuisClair('secret123'));
var_dump($u->verifierMotDePasse('secret123'));  // true
$u->changerMotDePasse('secret123', 'nouveau456');
var_dump($u->verifierMotDePasse('secret123'));  // false
""")],
       ["Une méthode statique de création : `public static function depuisClair(string $clair): self { ... return new self($hash); }`. Elle peut appeler le constructeur privé car elle est **dans** la classe.",
        "Chiffre présent : `preg_match('/\\d/', $clair) === 1`.",
        "`Utilisateur::verifierMotDePasse(string $clair)` délègue à `$this->motDePasse->verifier($clair)`."],
       [F("MotDePasse.php", "php", r"""
<?php
declare(strict_types=1);

final class MotDePasse
{
    private function __construct(private string $hash) {}

    public static function depuisClair(string $clair): self
    {
        if (strlen($clair) < 8) {
            throw new InvalidArgumentException('8 caractères minimum');
        }
        if (preg_match('/\d/', $clair) !== 1) {
            throw new InvalidArgumentException('Au moins un chiffre');
        }
        return new self(password_hash($clair, PASSWORD_DEFAULT));
    }

    public static function depuisHash(string $hash): self
    {
        return new self($hash);
    }

    public function verifier(string $clair): bool
    {
        return password_verify($clair, $this->hash);
    }

    public function hash(): string
    {
        return $this->hash;
    }
}

final class Utilisateur
{
    public function __construct(private string $email, private MotDePasse $motDePasse) {}

    public function verifierMotDePasse(string $clair): bool
    {
        return $this->motDePasse->verifier($clair);
    }

    public function changerMotDePasse(string $ancien, string $nouveau): void
    {
        if (!$this->motDePasse->verifier($ancien)) {
            throw new DomainException('Ancien mot de passe incorrect');
        }
        $this->motDePasse = MotDePasse::depuisClair($nouveau);
    }
}

$u = new Utilisateur('ana@mail.com', MotDePasse::depuisClair('secret123'));
var_dump($u->verifierMotDePasse('secret123'));  // true
$u->changerMotDePasse('secret123', 'nouveau456');
var_dump($u->verifierMotDePasse('secret123'));  // false
""")],
       ["`new MotDePasse('x')` est impossible depuis l'extérieur",
        "`depuisClair('court1')` lève une exception, `depuisClair('sansChiffre')` aussi",
        "Changer le mot de passe avec un mauvais ancien mot de passe est refusé"],
       run=RUN("php", tests=r"""
check('le constructeur est private', (new ReflectionMethod(MotDePasse::class, '__construct'))->isPrivate());
check('depuisClair("court1") est refusé', throws(fn() => MotDePasse::depuisClair('court1'), InvalidArgumentException::class));
check('depuisClair("sansChiffreIci") est refusé', throws(fn() => MotDePasse::depuisClair('sansChiffreIci'), InvalidArgumentException::class));
$m = MotDePasse::depuisClair('secret123');
check('verifier() accepte le bon mot de passe', $m->verifier('secret123'));
check('verifier() refuse un mauvais mot de passe', !$m->verifier('autre'));
check('hash() ne contient pas le mot de passe en clair', !str_contains($m->hash(), 'secret123'));
check('depuisHash() recrée un objet qui vérifie encore', MotDePasse::depuisHash($m->hash())->verifier('secret123'));
$u = new Utilisateur('ana@mail.com', $m);
check('changer avec un mauvais ancien est refusé', throws(fn() => $u->changerMotDePasse('faux', 'nouveau456'), DomainException::class));
$u->changerMotDePasse('secret123', 'nouveau456');
check('après changement, le nouveau fonctionne', $u->verifierMotDePasse('nouveau456'));
check('après changement, l\'ancien ne fonctionne plus', !$u->verifierMotDePasse('secret123'));
"""), expected="bool(true)\nbool(false)"),
    TD(3, "Créneau de réservation sans chevauchement",
       "Une salle de réunion se réserve par créneaux. Tu modélises un `Creneau` immuable qui garantit ses règles (fin après début, dans les heures d'ouverture), puis une `Salle` qui refuse deux créneaux qui se chevauchent. Approfondissement : invariants sur **plusieurs** valeurs à la fois, immuabilité, et un invariant qui porte sur **une collection**.",
       ["`Creneau` : `debut` et `fin` en `DateTimeImmutable`, `readonly`. Exceptions si `fin <= debut`, si la durée dépasse 4 h, ou si le créneau sort de 8 h–20 h",
        "`Creneau::chevauche(Creneau $autre): bool`",
        "`Creneau::decaler(int $minutes): Creneau` renvoie un **nouveau** créneau (l'objet d'origine ne change pas) et repasse par les mêmes règles",
        "`Salle::reserver(Creneau $c)` : `DomainException` si chevauchement avec un créneau déjà réservé",
        "`Salle::creneaux(): array` trié par début"],
       [F("Salle.php", "php", r"""
<?php
declare(strict_types=1);

final class Creneau
{
    // à toi
}

final class Salle
{
    // à toi
}

$salle = new Salle('A101');
$salle->reserver(new Creneau(new DateTimeImmutable('2026-03-02 09:00'), new DateTimeImmutable('2026-03-02 10:00')));
$salle->reserver(new Creneau(new DateTimeImmutable('2026-03-02 10:00'), new DateTimeImmutable('2026-03-02 11:30')));
try {
    $salle->reserver(new Creneau(new DateTimeImmutable('2026-03-02 09:30'), new DateTimeImmutable('2026-03-02 10:30')));
} catch (DomainException $e) {
    echo 'Refusé : ', $e->getMessage(), PHP_EOL;
}
echo count($salle->creneaux());  // 2
""")],
       ["Deux créneaux se chevauchent si `$this->debut < $autre->fin && $autre->debut < $this->fin`. Deux créneaux qui se touchent (10:00–11:00 et 11:00–12:00) ne se chevauchent **pas**.",
        "Durée en minutes : `($fin->getTimestamp() - $debut->getTimestamp()) / 60`. Heure : `(int) $debut->format('G')`.",
        "`decaler()` : `return new self($this->debut->modify(\"+$minutes minutes\"), $this->fin->modify(\"+$minutes minutes\"));` : le constructeur revalide tout.",
        "Pour trier : `usort($liste, fn(Creneau $a, Creneau $b) => $a->debut <=> $b->debut);`"],
       [F("Salle.php", "php", r"""
<?php
declare(strict_types=1);

final class Creneau
{
    private const DUREE_MAX_MINUTES = 240;
    private const OUVERTURE = 8;
    private const FERMETURE = 20;

    public function __construct(
        public readonly DateTimeImmutable $debut,
        public readonly DateTimeImmutable $fin,
    ) {
        if ($fin <= $debut) {
            throw new InvalidArgumentException('La fin doit être après le début');
        }
        $minutes = ($fin->getTimestamp() - $debut->getTimestamp()) / 60;
        if ($minutes > self::DUREE_MAX_MINUTES) {
            throw new InvalidArgumentException('4 heures maximum');
        }
        $hDebut = (int) $debut->format('G');
        $hFin = (int) $fin->format('G') + ((int) $fin->format('i') > 0 ? 1 : 0);
        if ($hDebut < self::OUVERTURE || $hFin > self::FERMETURE || $debut->format('Y-m-d') !== $fin->format('Y-m-d')) {
            throw new InvalidArgumentException('Créneau hors des heures d\'ouverture (8 h – 20 h)');
        }
    }

    public function chevauche(Creneau $autre): bool
    {
        return $this->debut < $autre->fin && $autre->debut < $this->fin;
    }

    public function decaler(int $minutes): Creneau
    {
        return new self(
            $this->debut->modify("$minutes minutes"),
            $this->fin->modify("$minutes minutes"),
        );
    }
}

final class Salle
{
    /** @var Creneau[] */
    private array $creneaux = [];

    public function __construct(private string $nom) {}

    public function reserver(Creneau $nouveau): void
    {
        foreach ($this->creneaux as $existant) {
            if ($existant->chevauche($nouveau)) {
                throw new DomainException(sprintf(
                    'Chevauchement avec le créneau %s–%s',
                    $existant->debut->format('H:i'),
                    $existant->fin->format('H:i'),
                ));
            }
        }
        $this->creneaux[] = $nouveau;
        usort($this->creneaux, fn(Creneau $a, Creneau $b) => $a->debut <=> $b->debut);
    }

    /** @return Creneau[] */
    public function creneaux(): array
    {
        return $this->creneaux;
    }
}

$salle = new Salle('A101');
$salle->reserver(new Creneau(new DateTimeImmutable('2026-03-02 09:00'), new DateTimeImmutable('2026-03-02 10:00')));
$salle->reserver(new Creneau(new DateTimeImmutable('2026-03-02 10:00'), new DateTimeImmutable('2026-03-02 11:30')));
try {
    $salle->reserver(new Creneau(new DateTimeImmutable('2026-03-02 09:30'), new DateTimeImmutable('2026-03-02 10:30')));
} catch (DomainException $e) {
    echo 'Refusé : ', $e->getMessage(), PHP_EOL;
}
echo count($salle->creneaux());  // 2
""")],
       ["Un créneau 10:00–11:00 puis 11:00–12:00 est accepté (ils se touchent sans se chevaucher)",
        "`decaler()` ne modifie pas l'objet d'origine",
        "Un créneau de 5 h ou qui commence à 7 h est refusé"],
       run=RUN("php", tests=r"""
$d = fn(string $h) => new DateTimeImmutable("2026-03-02 $h");
check('fin avant début refusé', throws(fn() => new Creneau($d('10:00'), $d('09:00')), InvalidArgumentException::class));
check('5 heures refusées', throws(fn() => new Creneau($d('09:00'), $d('14:00')), InvalidArgumentException::class));
check('début à 7 h refusé', throws(fn() => new Creneau($d('07:00'), $d('08:00')), InvalidArgumentException::class));
check('fin à 21 h refusée', throws(fn() => new Creneau($d('19:00'), $d('21:00')), InvalidArgumentException::class));
$a = new Creneau($d('09:00'), $d('10:00'));
$b = new Creneau($d('10:00'), $d('11:00'));
$c = new Creneau($d('09:30'), $d('10:30'));
check('09–10 et 10–11 ne se chevauchent pas', !$a->chevauche($b) && !$b->chevauche($a));
check('09–10 et 09:30–10:30 se chevauchent', $a->chevauche($c) && $c->chevauche($a));
$dec = $a->decaler(30);
check('decaler renvoie un nouveau créneau décalé', $dec->debut->format('H:i') === '09:30' && $dec->fin->format('H:i') === '10:30');
check('decaler ne modifie pas l\'original', $a->debut->format('H:i') === '09:00');
check('decaler qui sort des horaires est refusé', throws(fn() => (new Creneau($d('18:00'), $d('19:30')))->decaler(60), InvalidArgumentException::class));
$s = new Salle('A101');
$s->reserver($b); $s->reserver($a);
check('deux créneaux qui se touchent sont acceptés', count($s->creneaux()) === 2);
check('la liste est triée par début', $s->creneaux()[0]->debut->format('H:i') === '09:00');
check('un chevauchement est refusé', throws(fn() => $s->reserver($c), DomainException::class));
check('le refus n\'a rien ajouté', count($s->creneaux()) === 2);
check('debut est readonly', (new ReflectionProperty(Creneau::class, 'debut'))->isReadOnly());
"""), expected="Refusé : Chevauchement avec le créneau 09:00–10:00\n2"),
  ])

# ---------------------------------------------------------------- héritage
herit = V2(v1["php-heritage"],
  prereq=[
    P("`protected`", "Visibilité intermédiaire : accessible dans la classe **et** ses enfants, pas depuis l'extérieur (module Encapsulation)."),
    P("Signature", "Le nom d'une méthode + ses paramètres typés + son type de retour : `public function aire(): float`. Une méthode abstraite n'a **que** sa signature, pas de corps."),
    P("Polymorphisme", "Mot savant pour « plusieurs formes » : un même appel (`$forme->aire()`) exécute un code différent selon la classe réelle de l'objet. C'est PHP qui choisit, au moment de l'appel."),
    P("`sprintf`", "Construit une chaîne avec des emplacements : `sprintf('%s : %.2f m²', $nom, $aire)` → `%s` texte, `%.2f` nombre à 2 décimales."),
    P("Composition", "Mettre un objet **dans** un autre comme propriété (`Voiture` a un `Moteur`), par opposition à l'héritage (`Voiture` est un `Vehicule`)."),
  ],
  diagram=D(
    nodes=[
      N("forme", 1, 0, "abstract Forme", "nom · decrire()\nabstract aire()", kind="doc"),
      N("cercle", 0, 1, "Cercle", "rayon · aire() = πr²"),
      N("rect", 2, 1, "Rectangle", "l, h · aire() = l×h"),
      N("call", 1, 2, "$forme->decrire()", "appelle aire() de la classe réelle", kind="pill", color="good"),
    ],
    edges=[E("cercle", "forme", "extends"), E("rect", "forme", "extends"), E("call", "cercle", "si Cercle", dashed=True, color="good"), E("call", "rect", "si Rectangle", dashed=True, color="good")],
    caption="Le parent définit le commun ; chaque enfant fournit sa propre `aire()`. Le code appelant ne connaît que `Forme`."),
  lessons=[
    L("Partager du code sans le dupliquer", r"""
Tu as un `Cercle` et un `Rectangle`. Les deux ont un nom et une méthode `decrire()` qui affiche « Nom : aire m² ». Sans héritage, tu écris `decrire()` deux fois, à l'identique. Au troisième type de forme, tu la copies encore. Le jour où tu changes le format, tu dois le changer partout.

L'**héritage** permet d'écrire ce qui est commun une seule fois dans une classe **parente** (`Forme`), et de laisser chaque classe **enfant** (`Cercle extends Forme`) hériter de ce code. L'enfant récupère toutes les propriétés et méthodes `public` et `protected` du parent, et peut en ajouter ou en redéfinir.

```php
class Forme
{
    public function __construct(protected string $nom) {}

    public function decrire(): string
    {
        return sprintf('%s : %.2f m²', $this->nom, $this->aire());
    }
}

class Cercle extends Forme
{
    public function __construct(private float $rayon)
    {
        parent::__construct('Cercle');    // on remplit la partie "Forme" de l'objet
    }

    public function aire(): float { return M_PI * $this->rayon ** 2; }
}
```

`parent::__construct(...)` appelle le constructeur du parent : l'enfant est responsable de bien initialiser la partie héritée. Un `Cercle` **est une** `Forme` : partout où on attend une `Forme`, on peut passer un `Cercle`.
"""),
    L("Classe abstraite : un plan incomplet, à compléter", r"""
Dans le code ci-dessus, `Forme::decrire()` appelle `$this->aire()`. Mais `Forme` ne sait pas calculer une aire : ça dépend de la forme. Deux problèmes : d'abord rien n'oblige un enfant à écrire `aire()` (on s'en rendrait compte par une erreur à l'exécution) ; ensuite `new Forme('x')` ne devrait pas avoir de sens.

Une classe **abstraite** résout les deux :

```php
abstract class Forme
{
    abstract public function aire(): float;   // signature seule : "à toi de l'écrire"
    // ... decrire() comme avant
}
```

- `abstract class` : impossible de faire `new Forme(...)`. Elle sert uniquement de base.
- `abstract public function aire(): float;` : chaque enfant **doit** implémenter cette méthode avec cette signature, sinon PHP refuse de charger la classe. L'oubli est détecté immédiatement.

Une classe abstraite peut mélanger du code concret (`decrire()`) et des méthodes abstraites (`aire()`). C'est ce qui la distingue d'une interface (module suivant), qui ne contient **que** des signatures.
"""),
    L("Le polymorphisme : un appel, plusieurs comportements", r"""
```php
$formes = [new Cercle(1), new Rectangle(2, 3)];
foreach ($formes as $forme) {
    echo $forme->decrire(), PHP_EOL;
}
```

La boucle ne sait pas si `$forme` est un cercle ou un rectangle, et elle n'a pas besoin de le savoir. Quand `decrire()` appelle `$this->aire()`, PHP regarde la **classe réelle** de l'objet et exécute la bonne version. C'est le **polymorphisme**.

L'intérêt : ajouter un `Triangle` demande d'écrire une classe de 10 lignes, et **zéro** modification de la boucle ni de `decrire()`. Le code qui utilise les formes est fermé aux modifications, mais ouvert aux extensions. Chaque fois que tu vois un `if ($type === 'cercle') ... elseif ($type === 'rectangle') ...`, c'est un endroit où le polymorphisme ferait mieux le travail.
"""),
    L("Quand hériter, et quand ne pas le faire", r"""
L'héritage est tentant, parce qu'il permet de réutiliser du code. Mais il crée un lien **très fort** : l'enfant dépend de tous les détails du parent. Le test à faire avant d'écrire `extends` :

- **« est un »** → héritage. Un `Cercle` *est une* `Forme`. Un `Salarie` *est un* `Employe`.
- **« a un »** → composition : une propriété. Une `Voiture` *a un* `Moteur`. Une `Commande` *a une* `Adresse`. Écrire `Commande extends Adresse` n'aurait aucun sens, même si ça « réutiliserait » les champs de l'adresse.

Autres règles pratiques :

- Une hiérarchie de plus de 2 niveaux (`A extends B extends C`) devient vite illisible : on ne sait plus d'où vient chaque méthode.
- Marque `final` les classes que tu n'as pas conçues pour être étendues. Tu enlèveras le `final` le jour où tu en auras besoin ; le contraire (découvrir que 5 classes héritent de la tienne) est beaucoup plus pénible.
- Si tu hérites **juste pour piquer une méthode**, c'est de la composition déguisée : mets plutôt cette logique dans un objet à part et donne-le aux classes qui en ont besoin.
"""),
  ],
  recap=[
    "`extends` : l'enfant récupère le `public` et le `protected` du parent, et peut redéfinir des méthodes.",
    "`parent::__construct()` initialise la partie héritée.",
    "`abstract class` : pas de `new` ; `abstract function` : signature seule, l'enfant **doit** l'implémenter.",
    "Polymorphisme : `$forme->aire()` exécute la version de la **classe réelle** de l'objet.",
    "« est un » → héritage ; « a un » → composition. Au doute : composition, et `final` par défaut.",
  ],
  example=[F("src/Forme.php", "php", r"""
<?php
declare(strict_types=1);

abstract class Forme
{
    public function __construct(protected string $nom) {}

    abstract public function aire(): float;

    public function decrire(): string
    {
        return sprintf('%s : %.2f m²', $this->nom, $this->aire());
    }
}
"""), F("src/Cercle.php", "php", r"""
<?php
declare(strict_types=1);

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
"""), F("src/Rectangle.php", "php", r"""
<?php
declare(strict_types=1);

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
"""), F("demo.php", "php", r"""
<?php
foreach ([new Cercle(1), new Rectangle(2, 3)] as $forme) {
    echo $forme->decrire(), PHP_EOL;
}
// Cercle : 3.14 m²
// Rectangle : 6.00 m²
""")],
  notes=["`decrire()` est écrit une seule fois dans `Forme.php`, mais appelle l'`aire()` de l'enfant.",
         "Chaque enfant appelle `parent::__construct('…')` pour remplir le nom.",
         "La boucle de `demo.php` ne connaît que `Forme` : ajouter un `Triangle` ne la change pas.",
         "`protected $nom` : visible dans `Cercle` et `Rectangle`, pas depuis `demo.php`."],
  td1=dict(path="Employes.php", run=RUN("php", tests=r"""
check('Employe est abstraite', (new ReflectionClass(Employe::class))->isAbstract());
check('salaireMensuel est abstraite dans Employe', (new ReflectionMethod(Employe::class, 'salaireMensuel'))->isAbstract());
check('Salarie étend Employe', is_subclass_of(Salarie::class, Employe::class));
check('Freelance étend Employe', is_subclass_of(Freelance::class, Employe::class));
$s = new Salarie('Ana', 30000);
check('Salarie : 30000/12 = 2500', abs($s->salaireMensuel() - 2500) < 0.01, 'obtenu : ' . $s->salaireMensuel());
$f = new Freelance('Léo', 400, 10);
check('Freelance : 400 × 10 = 4000', abs($f->salaireMensuel() - 4000) < 0.01);
check('fiche() formate "Ana : 2500.00 €"', $s->fiche() === 'Ana : 2500.00 €', 'obtenu : ' . $s->fiche());
check('fiche() est définie dans Employe (pas dupliquée)', (new ReflectionMethod(Salarie::class, 'fiche'))->getDeclaringClass()->getName() === 'Employe');
""")),
  tds=[
    TD(2, "Notifications : SMS, email, push",
       "Une application envoie des notifications par plusieurs canaux. Chaque canal **formate** le message différemment (un SMS est limité à 160 caractères, un email a un sujet), mais tous suivent les mêmes étapes : vérifier le destinataire, formater, envoyer, journaliser. Tu mets les étapes communes dans le parent et tu laisses les enfants ne définir que ce qui change (c'est le patron *Template Method*).",
       ["`abstract class Notification` avec `envoyer(string $destinataire, string $message): string` **concrète** qui : vérifie que le destinataire n'est pas vide (`InvalidArgumentException`), appelle `formater($message)`, puis renvoie `'[' . static::class . '] ' . $destinataire . ' <= ' . $formaté`",
        "`abstract protected function formater(string $message): string;`",
        "`Sms` : si le message dépasse 160 caractères, garde les 157 premiers et ajoute `...` (160 au total)",
        "`Email` : constructeur avec `$sujet`, formate en `\"Sujet: $sujet | $message\"`",
        "`Push` : met en majuscules",
        "`envoyer()` ne doit **pas** être redéfinie dans les enfants (marque-la `final`)"],
       [F("Notification.php", "php", r"""
<?php
declare(strict_types=1);

abstract class Notification
{
    // à toi
}

// Sms, Email, Push

$canaux = [new Sms(), new Email('Bienvenue'), new Push()];
foreach ($canaux as $canal) {
    echo $canal->envoyer('ana', 'Ton compte est pret'), PHP_EOL;
}
""")],
       ["`static::class` dans le parent donne le nom de la classe **réelle** (`Sms`, `Email`…), pas `Notification`.",
        "`strlen($message) > 160` puis `substr($message, 0, 157) . '...'` : le résultat fait exactement 160 caractères.",
        "`final public function envoyer(...)` : le mot-clé `final` sur une **méthode** interdit aux enfants de la redéfinir."],
       [F("Notification.php", "php", r"""
<?php
declare(strict_types=1);

abstract class Notification
{
    final public function envoyer(string $destinataire, string $message): string
    {
        if (trim($destinataire) === '') {
            throw new InvalidArgumentException('Destinataire manquant');
        }
        $formate = $this->formater($message);
        return '[' . static::class . '] ' . $destinataire . ' <= ' . $formate;
    }

    abstract protected function formater(string $message): string;
}

final class Sms extends Notification
{
    protected function formater(string $message): string
    {
        return strlen($message) > 160 ? substr($message, 0, 157) . '...' : $message;
    }
}

final class Email extends Notification
{
    public function __construct(private string $sujet) {}

    protected function formater(string $message): string
    {
        return "Sujet: {$this->sujet} | $message";
    }
}

final class Push extends Notification
{
    protected function formater(string $message): string
    {
        return strtoupper($message);
    }
}

$canaux = [new Sms(), new Email('Bienvenue'), new Push()];
foreach ($canaux as $canal) {
    echo $canal->envoyer('ana', 'Ton compte est pret'), PHP_EOL;
}
""")],
       ["Ajouter un canal `Slack` demande une classe de 6 lignes et rien d'autre",
        "Un destinataire vide est refusé par **tous** les canaux grâce au parent",
        "Un enfant qui redéfinit `envoyer()` provoque une erreur"],
       run=RUN("php", tests=r"""
check('Notification est abstraite', (new ReflectionClass(Notification::class))->isAbstract());
check('envoyer() est final', (new ReflectionMethod(Notification::class, 'envoyer'))->isFinal());
check('formater() est abstraite et protected', (new ReflectionMethod(Notification::class, 'formater'))->isAbstract() && (new ReflectionMethod(Notification::class, 'formater'))->isProtected());
$sms = new Sms();
check('Sms : message court intact', $sms->envoyer('ana', 'Salut') === '[Sms] ana <= Salut', $sms->envoyer('ana', 'Salut'));
$long = str_repeat('a', 200);
$out = $sms->envoyer('ana', $long);
check('Sms : message long coupé à 160 avec ...', strlen(explode(' <= ', $out)[1]) === 160 && str_ends_with($out, '...'), 'longueur : ' . strlen(explode(' <= ', $out)[1]));
check('Email : sujet ajouté', (new Email('Bienvenue'))->envoyer('ana', 'ok') === '[Email] ana <= Sujet: Bienvenue | ok');
check('Push : majuscules', (new Push())->envoyer('ana', 'ok') === '[Push] ana <= OK');
check('destinataire vide refusé (règle du parent)', throws(fn() => (new Push())->envoyer('  ', 'x'), InvalidArgumentException::class));
"""), expected="[Sms] ana <= Ton compte est pret\n[Email] ana <= Sujet: Bienvenue | Ton compte est pret\n[Push] ana <= TON COMPTE EST PRET"),
    TD(3, "Héritage ou composition ? Refactoriser un mauvais design",
       "Un développeur a modélisé une boutique avec de l'héritage partout. Résultat : `ProduitEnPromo extends Produit`, `ProduitEnPromoLivraisonGratuite extends ProduitEnPromo`… et impossible d'avoir un produit en livraison gratuite **sans** promo. Ton travail : garder l'héritage là où il est justifié (« est un ») et remplacer le reste par de la composition, sans changer les résultats affichés.",
       ["Supprime `ProduitEnPromo` et `ProduitEnPromoLivraisonGratuite`",
        "Crée un objet `Remise` (pourcentage, validé entre 0 et 100) et un objet `Livraison` (`estGratuite(): bool`, `frais(): float`) que `Produit` reçoit en **composition** (avec des valeurs par défaut : pas de remise, livraison 4,90 €)",
        "`Produit::prixFinal(): float` = prix remisé + frais de livraison",
        "Garde `ProduitNumerique extends Produit` (un produit numérique **est un** produit sans livraison : il force une `Livraison` gratuite et interdit d'en changer)",
        "Le script de démo doit afficher exactement le même résultat qu'avant"],
       [F("Boutique.php", "php", r"""
<?php
declare(strict_types=1);

// ---- AVANT : à refactoriser ----
class Produit
{
    public function __construct(protected string $nom, protected float $prix) {}
    public function prixFinal(): float { return $this->prix + 4.90; }
    public function nom(): string { return $this->nom; }
}

class ProduitEnPromo extends Produit
{
    public function __construct(string $nom, float $prix, protected float $remise) { parent::__construct($nom, $prix); }
    public function prixFinal(): float { return $this->prix * (1 - $this->remise / 100) + 4.90; }
}

class ProduitEnPromoLivraisonGratuite extends ProduitEnPromo
{
    public function prixFinal(): float { return $this->prix * (1 - $this->remise / 100); }
}

class ProduitNumerique extends Produit
{
    public function prixFinal(): float { return $this->prix; }
}

// ---- Démo : le résultat doit rester identique après refactor ----
$produits = [
    new Produit('Clavier', 50.0),
    new ProduitEnPromo('Souris', 20.0, 10),
    new ProduitEnPromoLivraisonGratuite('Écran', 200.0, 15),
    new ProduitNumerique('Ebook PHP', 12.0),
];
foreach ($produits as $p) {
    printf("%-10s %7.2f €\n", $p->nom(), $p->prixFinal());
}
""")],
       ["La version refactorisée du script de démo : `new Produit('Souris', 20.0, new Remise(10))`, `new Produit('Écran', 200.0, new Remise(15), Livraison::gratuite())`.",
        "`Livraison` avec deux constructeurs nommés : `Livraison::standard()` (4,90) et `Livraison::gratuite()` (0).",
        "Dans `ProduitNumerique`, le constructeur ne prend pas de livraison et appelle `parent::__construct($nom, $prix, $remise, Livraison::gratuite())`.",
        "Le `printf` et les montants ne doivent pas bouger : c'est ton test de non-régression."],
       [F("Boutique.php", "php", r"""
<?php
declare(strict_types=1);

final class Remise
{
    public function __construct(public readonly float $pourcentage = 0)
    {
        if ($pourcentage < 0 || $pourcentage > 100) {
            throw new InvalidArgumentException('Remise entre 0 et 100');
        }
    }

    public function appliquer(float $prix): float
    {
        return $prix * (1 - $this->pourcentage / 100);
    }
}

final class Livraison
{
    private function __construct(private float $frais) {}

    public static function standard(): self { return new self(4.90); }
    public static function gratuite(): self { return new self(0.0); }

    public function estGratuite(): bool { return $this->frais === 0.0; }
    public function frais(): float { return $this->frais; }
}

class Produit
{
    protected Livraison $livraison;

    public function __construct(
        protected string $nom,
        protected float $prix,
        protected Remise $remise = new Remise(0),
        ?Livraison $livraison = null,
    ) {
        $this->livraison = $livraison ?? Livraison::standard();
    }

    public function prixFinal(): float
    {
        return $this->remise->appliquer($this->prix) + $this->livraison->frais();
    }

    public function nom(): string { return $this->nom; }
}

final class ProduitNumerique extends Produit
{
    public function __construct(string $nom, float $prix, Remise $remise = new Remise(0))
    {
        parent::__construct($nom, $prix, $remise, Livraison::gratuite());
    }
}

$produits = [
    new Produit('Clavier', 50.0),
    new Produit('Souris', 20.0, new Remise(10)),
    new Produit('Écran', 200.0, new Remise(15), Livraison::gratuite()),
    new ProduitNumerique('Ebook PHP', 12.0),
];
foreach ($produits as $p) {
    printf("%-10s %7.2f €\n", $p->nom(), $p->prixFinal());
}
""")],
       ["Il ne reste que **deux** classes de produit : `Produit` et `ProduitNumerique`",
        "On peut créer un produit en livraison gratuite **sans** remise, ce qui était impossible avant",
        "La sortie du script est identique à l'avant"],
       run=RUN("php", tests=r"""
check('ProduitEnPromo a disparu', !class_exists('ProduitEnPromo'));
check('ProduitEnPromoLivraisonGratuite a disparu', !class_exists('ProduitEnPromoLivraisonGratuite'));
check('Remise existe', class_exists('Remise'));
check('Livraison existe', class_exists('Livraison'));
check('ProduitNumerique est toujours un Produit', is_subclass_of(ProduitNumerique::class, Produit::class));
check('Remise(150) refusée', throws(fn() => new Remise(150), InvalidArgumentException::class));
$p = new Produit('Clavier', 50.0);
check('Clavier : 54.90', abs($p->prixFinal() - 54.90) < 0.001, 'obtenu : ' . $p->prixFinal());
$s = new Produit('Souris', 20.0, new Remise(10));
check('Souris -10% : 22.90', abs($s->prixFinal() - 22.90) < 0.001, 'obtenu : ' . $s->prixFinal());
$e = new Produit('Écran', 200.0, new Remise(15), Livraison::gratuite());
check('Écran -15% livraison gratuite : 170.00', abs($e->prixFinal() - 170.0) < 0.001, 'obtenu : ' . $e->prixFinal());
$g = new Produit('Câble', 10.0, new Remise(0), Livraison::gratuite());
check('livraison gratuite SANS remise possible : 10.00', abs($g->prixFinal() - 10.0) < 0.001);
$n = new ProduitNumerique('Ebook PHP', 12.0);
check('Ebook : 12.00', abs($n->prixFinal() - 12.0) < 0.001);
"""), expected="Clavier      54.90 €\nSouris       22.90 €\nÉcran       170.00 €\nEbook PHP    12.00 €"),
  ])

# ---------------------------------------------------------------- interfaces
interf = V2(v1["php-interfaces"],
  prereq=[
    P("Classe abstraite", "Classe qu'on ne peut pas instancier, qui contient du code commun et des méthodes abstraites à implémenter (module Héritage). L'interface en est la version « sans aucun code »."),
    P("Contrat", "Une promesse sur **ce qu'une classe sait faire** (ses méthodes publiques), indépendamment de **comment** elle le fait. Une interface est un contrat écrit dans le langage."),
    P("Couplage", "Le degré de dépendance entre deux morceaux de code. Fort couplage : changer l'un oblige à changer l'autre. Les interfaces servent à **découpler**."),
    P("Classe anonyme", "Une classe sans nom créée sur place : `new class implements Notifier { ... }`. Pratique pour un faux objet dans un test."),
  ],
  diagram=D(
    nodes=[
      N("svc", 0, 1, "AlerteStock", "dépend de Notifier"),
      N("iface", 1, 1, "interface Notifier", "envoyer(…)", kind="doc", color="accent"),
      N("email", 2, 0, "EmailNotifier", "implements"),
      N("sms", 2, 1, "SmsNotifier", "implements"),
      N("fake", 2, 2, "FakeNotifier", "pour les tests", color="good"),
    ],
    edges=[E("svc", "iface", "utilise"), E("email", "iface", dashed=True), E("sms", "iface", dashed=True), E("fake", "iface", dashed=True)],
    caption="Le service ne connaît que le contrat. On branche l'implémentation qu'on veut, y compris une fausse pour tester."),
  lessons=[
    L("Le problème : dépendre d'une classe précise", r"""
```php
final class AlerteStock
{
    private SmsNotifier $notifier;

    public function __construct()
    {
        $this->notifier = new SmsNotifier();   // couplage fort
    }
}
```

`AlerteStock` est soudée à `SmsNotifier`. Conséquences : impossible de passer à l'email sans **modifier** `AlerteStock` ; impossible de tester `AlerteStock` sans envoyer de vrais SMS ; et si demain on veut envoyer SMS **et** email, il faut encore la modifier.

Ce que `AlerteStock` veut vraiment, ce n'est pas « un SmsNotifier », c'est « quelque chose qui sait envoyer un message ». C'est ce besoin, et uniquement lui, qu'une **interface** décrit.
"""),
    L("Une interface est un contrat sans code", r"""
```php
interface Notifier
{
    public function envoyer(string $destinataire, string $message): void;
}
```

Une interface liste des **signatures** de méthodes publiques (et éventuellement des constantes). Pas de propriétés, pas de corps de méthode. Elle dit « toute classe qui m'implémente **promet** de fournir ces méthodes ».

```php
final class EmailNotifier implements Notifier
{
    public function envoyer(string $destinataire, string $message): void
    {
        // envoi par email
    }
}
```

Si `EmailNotifier` oublie `envoyer()` ou change sa signature, PHP refuse de charger la classe : le contrat est vérifié par le langage, pas par la bonne volonté.

Différences avec une classe abstraite :

- Une classe n'hérite que d'**une** classe (`extends`), mais peut implémenter **plusieurs** interfaces (`implements A, B`).
- La classe abstraite dit « ce que c'est » et partage du **code** ; l'interface dit « ce que ça sait faire » et ne partage **rien**.
- En pratique : interface pour décrire un **rôle** qu'on branche (`Notifier`, `Repository`, `PaymentGateway`), classe abstraite pour factoriser du code entre des enfants proches (`Forme`).
"""),
    L("Programmer contre l'interface", r"""
```php
final class AlerteStock
{
    public function __construct(private Notifier $notifier) {}   // le type est l'INTERFACE

    public function verifier(string $produit, int $stock): void
    {
        if ($stock < 5) {
            $this->notifier->envoyer('gerant', "Stock bas : $produit ($stock)");
        }
    }
}

new AlerteStock(new SmsNotifier());      // en prod, aujourd'hui
new AlerteStock(new EmailNotifier());    // demain : zéro changement dans AlerteStock
```

`AlerteStock` ne contient plus aucun `new` de notifier : il **reçoit** un objet qui respecte le contrat, et il s'en sert. Qui décide de l'implémentation ? Le code qui construit `AlerteStock` (dans Symfony, le conteneur de services, voir le module Injection de dépendances).

C'est le même polymorphisme que dans le module Héritage : `$this->notifier->envoyer()` exécute la version de la classe réelle. La différence, c'est que les implémentations n'ont **aucun code en commun** ni de parent commun : juste le contrat.
"""),
    L("Le bonus : des tests sans effets de bord", r"""
Comment vérifier qu'`AlerteStock` envoie bien une alerte quand le stock passe sous 5, sans envoyer un vrai SMS à chaque exécution des tests ? Avec une **fausse implémentation** qui se contente de mémoriser ce qu'on lui demande :

```php
final class FakeNotifier implements Notifier
{
    public array $envoyes = [];

    public function envoyer(string $destinataire, string $message): void
    {
        $this->envoyes[] = [$destinataire, $message];
    }
}

$fake = new FakeNotifier();
(new AlerteStock($fake))->verifier('Clavier', 2);
assert(count($fake->envoyes) === 1);
assert(str_contains($fake->envoyes[0][1], 'Clavier'));
```

Le test est instantané, ne dépend d'aucun réseau, et vérifie précisément le comportement d'`AlerteStock`. Sans interface, ce test est impossible à écrire proprement.

Quand créer une interface ? Pas « au cas où » pour chaque classe : quand tu as (ou prévois très probablement) **plusieurs implémentations**, ou quand tu as besoin de **remplacer** une dépendance dans les tests (tout ce qui touche au réseau, à la base, au temps, au hasard).
"""),
  ],
  recap=[
    "Une interface = une liste de signatures publiques. Aucun code, aucune propriété.",
    "`implements` engage la classe : méthode manquante ou signature différente = erreur au chargement.",
    "Un service **demande l'interface** dans son constructeur, jamais une classe concrète.",
    "Une classe implémente **plusieurs** interfaces, mais n'hérite que d'**une** classe.",
    "Interface + fausse implémentation = tests rapides, sans réseau ni base.",
  ],
  example=[F("src/Notifier.php", "php", r"""
<?php
declare(strict_types=1);

interface Notifier
{
    public function envoyer(string $destinataire, string $message): void;
}
"""), F("src/EmailNotifier.php", "php", r"""
<?php
declare(strict_types=1);

final class EmailNotifier implements Notifier
{
    public function envoyer(string $destinataire, string $message): void
    {
        echo "Email à $destinataire : $message\n";
    }
}
"""), F("src/SmsNotifier.php", "php", r"""
<?php
declare(strict_types=1);

final class SmsNotifier implements Notifier
{
    public function envoyer(string $destinataire, string $message): void
    {
        echo "SMS à $destinataire : $message\n";
    }
}
"""), F("src/AlerteStock.php", "php", r"""
<?php
declare(strict_types=1);

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
"""), F("demo.php", "php", r"""
<?php
(new AlerteStock(new SmsNotifier()))->verifier('Clavier', 2);
// SMS à gerant : Stock bas : Clavier (2)

(new AlerteStock(new EmailNotifier()))->verifier('Clavier', 2);
// Email à gerant : Stock bas : Clavier (2)
""")],
  notes=["`Notifier.php` ne contient qu'une signature : c'est le contrat.",
         "`AlerteStock.php` ne mentionne ni SMS ni email : il demande un `Notifier`.",
         "Dans `demo.php`, la seule différence entre les deux appels est l'objet passé au constructeur.",
         "Un `FakeNotifier` qui enregistre les messages permettrait de tester `AlerteStock` sans rien envoyer."],
  td1=dict(path="Paiement.php", run=RUN("php", tests=r"""
check('PaymentGateway est une interface', interface_exists('PaymentGateway'));
check('StripeGateway implémente PaymentGateway', in_array('PaymentGateway', class_implements(StripeGateway::class)));
check('FakeGateway implémente PaymentGateway', in_array('PaymentGateway', class_implements(FakeGateway::class)));
$fake = new FakeGateway();
$service = new CheckoutService($fake);
$id = $service->checkout(4200);
check('checkout renvoie un id non vide', is_string($id) && $id !== '');
check('FakeGateway a mémorisé le montant 4200', $fake->paiements === [4200], json_encode($fake->paiements));
check('un montant de 0 est refusé', throws(fn() => $service->checkout(0), InvalidArgumentException::class));
check('un montant négatif est refusé', throws(fn() => $service->checkout(-5), InvalidArgumentException::class));
check('StripeGateway renvoie un id préfixé stripe_', str_starts_with((new StripeGateway())->payer(100), 'stripe_'));
$src = file_get_contents(__FILE__) ?: '';
check('CheckoutService ne mentionne pas Stripe', !preg_match('/class CheckoutService.*?\n}/s', $src, $mm) || !str_contains($mm[0], 'Stripe'));
""")),
  tds=[
    TD(2, "Plusieurs interfaces pour un même objet",
       "Un objet peut jouer plusieurs rôles. Un `Document` doit pouvoir être **exporté** (en texte, en JSON) et **comparé** à un autre. Tu définis deux interfaces et un service de tri qui ne connaît que le contrat de comparaison. Tu verras aussi `instanceof` pour vérifier qu'un objet respecte un contrat.",
       ["`interface Exportable { public function exporter(): string; }` et `interface Comparable { public function comparerA(Comparable $autre): int; }` (−1, 0 ou 1)",
        "`Document` (titre, nbPages) implémente **les deux** : exporte en `\"Titre (12 p.)\"`, compare par nombre de pages",
        "`Image` (nom, largeur, hauteur) implémente seulement `Exportable` : `\"nom 800x600\"`",
        "`Trieur::trier(array $elements): array` : refuse (`InvalidArgumentException`) tout élément qui n'est pas `Comparable`, et renvoie la liste triée",
        "`Exporteur::toutExporter(array $elements): string` : une ligne par élément exportable (les autres sont ignorés)"],
       [F("Documents.php", "php", r"""
<?php
declare(strict_types=1);

interface Exportable
{
    // à toi
}

interface Comparable
{
    // à toi
}

// Document, Image, Trieur, Exporteur

$docs = [new Document('Rapport', 12), new Document('Note', 2), new Document('Thèse', 300)];
foreach ((new Trieur())->trier($docs) as $d) {
    echo $d->exporter(), PHP_EOL;
}
echo (new Exporteur())->toutExporter([new Image('logo', 800, 600), new Document('Note', 2)]);
""")],
       ["`class Document implements Exportable, Comparable` : les interfaces se séparent par une virgule.",
        "Dans `comparerA`, `$autre` est typé `Comparable` : pour accéder à `nbPages`, vérifie `$autre instanceof Document` et lève une exception sinon.",
        "`usort($elements, fn(Comparable $a, Comparable $b) => $a->comparerA($b));` : `usort` attend exactement −1 / 0 / 1 ; l'opérateur `<=>` les renvoie."],
       [F("Documents.php", "php", r"""
<?php
declare(strict_types=1);

interface Exportable
{
    public function exporter(): string;
}

interface Comparable
{
    public function comparerA(Comparable $autre): int;
}

final class Document implements Exportable, Comparable
{
    public function __construct(private string $titre, private int $nbPages) {}

    public function exporter(): string
    {
        return sprintf('%s (%d p.)', $this->titre, $this->nbPages);
    }

    public function comparerA(Comparable $autre): int
    {
        if (!$autre instanceof Document) {
            throw new InvalidArgumentException('Comparaison impossible');
        }
        return $this->nbPages <=> $autre->nbPages;
    }
}

final class Image implements Exportable
{
    public function __construct(private string $nom, private int $largeur, private int $hauteur) {}

    public function exporter(): string
    {
        return sprintf('%s %dx%d', $this->nom, $this->largeur, $this->hauteur);
    }
}

final class Trieur
{
    /** @param Comparable[] $elements */
    public function trier(array $elements): array
    {
        foreach ($elements as $e) {
            if (!$e instanceof Comparable) {
                throw new InvalidArgumentException('Élément non comparable');
            }
        }
        usort($elements, fn(Comparable $a, Comparable $b) => $a->comparerA($b));
        return $elements;
    }
}

final class Exporteur
{
    public function toutExporter(array $elements): string
    {
        $out = '';
        foreach ($elements as $e) {
            if ($e instanceof Exportable) {
                $out .= $e->exporter() . PHP_EOL;
            }
        }
        return $out;
    }
}

$docs = [new Document('Rapport', 12), new Document('Note', 2), new Document('Thèse', 300)];
foreach ((new Trieur())->trier($docs) as $d) {
    echo $d->exporter(), PHP_EOL;
}
echo (new Exporteur())->toutExporter([new Image('logo', 800, 600), new Document('Note', 2)]);
""")],
       ["`Document` implémente deux interfaces, `Image` une seule",
        "Trier une liste contenant une `Image` lève une exception",
        "`Exporteur` ne connaît ni `Document` ni `Image`, seulement `Exportable`"],
       run=RUN("php", tests=r"""
check('Exportable et Comparable sont des interfaces', interface_exists('Exportable') && interface_exists('Comparable'));
$impl = class_implements(Document::class);
check('Document implémente les deux interfaces', in_array('Exportable', $impl) && in_array('Comparable', $impl));
check('Image implémente seulement Exportable', in_array('Exportable', class_implements(Image::class)) && !in_array('Comparable', class_implements(Image::class)));
$tries = (new Trieur())->trier([new Document('Rapport', 12), new Document('Note', 2), new Document('Thèse', 300)]);
check('tri par pages croissantes', array_map(fn($d) => $d->exporter(), $tries) === ['Note (2 p.)', 'Rapport (12 p.)', 'Thèse (300 p.)'], json_encode(array_map(fn($d) => $d->exporter(), $tries)));
check('trier une Image est refusé', throws(fn() => (new Trieur())->trier([new Image('x', 1, 1)]), InvalidArgumentException::class));
$out = (new Exporteur())->toutExporter([new Image('logo', 800, 600), new Document('Note', 2), 'intrus']);
check('toutExporter ignore ce qui n\'est pas Exportable', $out === "logo 800x600\nNote (2 p.)\n", json_encode($out));
"""), expected="Note (2 p.)\nRapport (12 p.)\nThèse (300 p.)\nlogo 800x600\nNote (2 p.)"),
    TD(3, "Stratégie de livraison et tests sans réseau",
       "Un site calcule les frais de port via des transporteurs externes. Chaque transporteur a sa propre API (on la **simule** ici), ses propres règles, et parfois il tombe en panne. Tu écris un `CalculateurFraisDePort` qui interroge plusieurs transporteurs, ignore ceux en panne, et choisit le moins cher. Tu combines interface, polymorphisme, exceptions, et une fausse implémentation pour tester chaque cas (panne, aucun transporteur, égalité).",
       ["`interface Transporteur { public function nom(): string; public function devis(float $poidsKg): float; }` ; un transporteur **en panne** lève `TransporteurIndisponible` (classe d'exception à créer, qui étend `RuntimeException`)",
        "`Colissimo` : 4,90 + 1,20 €/kg ; `Chronopost` : 9,00 + 0,80 €/kg, refuse (`InvalidArgumentException`) au-delà de 30 kg",
        "`CalculateurFraisDePort::__construct(Transporteur ...$transporteurs)` (variadique : autant de transporteurs qu'on veut)",
        "`meilleurDevis(float $poids): Devis` : `Devis` est un petit objet (`transporteur`, `montant`) ; ignore les transporteurs indisponibles ou qui refusent ; si aucun ne répond, `DomainException`",
        "`FakeTransporteur` configurable : `new FakeTransporteur('Test', montant: 5.0)` ou `new FakeTransporteur('Test', panne: true)`",
        "Écris 3 scénarios de test à la fin du fichier avec `assert()` : moins cher choisi, panne ignorée, aucun disponible"],
       [F("Livraison.php", "php", r"""
<?php
declare(strict_types=1);

final class TransporteurIndisponible extends RuntimeException {}

interface Transporteur
{
    // à toi
}

// Colissimo, Chronopost, FakeTransporteur, Devis, CalculateurFraisDePort

$calc = new CalculateurFraisDePort(new Colissimo(), new Chronopost());
$d = $calc->meilleurDevis(2.0);
printf("%s : %.2f €\n", $d->transporteur, $d->montant);   // Colissimo : 7.30 €
$d = $calc->meilleurDevis(20.0);
printf("%s : %.2f €\n", $d->transporteur, $d->montant);   // Chronopost : 25.00 €
""")],
       ["Variadique : `public function __construct(Transporteur ...$transporteurs) { $this->transporteurs = $transporteurs; }`.",
        "Dans la boucle : `try { $m = $t->devis($poids); } catch (TransporteurIndisponible | InvalidArgumentException $e) { continue; }` : le `|` attrape deux types d'exception.",
        "Garde le meilleur au fur et à mesure : `if ($meilleur === null || $m < $meilleur->montant) $meilleur = new Devis($t->nom(), $m);`.",
        "`FakeTransporteur` : `public function __construct(private string $nom, private float $montant = 0, private bool $panne = false) {}` et `devis()` lève si `$this->panne`."],
       [F("Livraison.php", "php", r"""
<?php
declare(strict_types=1);

final class TransporteurIndisponible extends RuntimeException {}

interface Transporteur
{
    public function nom(): string;
    public function devis(float $poidsKg): float;
}

final class Colissimo implements Transporteur
{
    public function nom(): string { return 'Colissimo'; }

    public function devis(float $poidsKg): float
    {
        return 4.90 + 1.20 * $poidsKg;
    }
}

final class Chronopost implements Transporteur
{
    public function nom(): string { return 'Chronopost'; }

    public function devis(float $poidsKg): float
    {
        if ($poidsKg > 30) {
            throw new InvalidArgumentException('30 kg maximum');
        }
        return 9.00 + 0.80 * $poidsKg;
    }
}

final class FakeTransporteur implements Transporteur
{
    public function __construct(private string $nom, private float $montant = 0.0, private bool $panne = false) {}

    public function nom(): string { return $this->nom; }

    public function devis(float $poidsKg): float
    {
        if ($this->panne) {
            throw new TransporteurIndisponible($this->nom . ' en panne');
        }
        return $this->montant;
    }
}

final class Devis
{
    public function __construct(public readonly string $transporteur, public readonly float $montant) {}
}

final class CalculateurFraisDePort
{
    /** @var Transporteur[] */
    private array $transporteurs;

    public function __construct(Transporteur ...$transporteurs)
    {
        $this->transporteurs = $transporteurs;
    }

    public function meilleurDevis(float $poids): Devis
    {
        $meilleur = null;
        foreach ($this->transporteurs as $t) {
            try {
                $montant = $t->devis($poids);
            } catch (TransporteurIndisponible | InvalidArgumentException $e) {
                continue;
            }
            if ($meilleur === null || $montant < $meilleur->montant) {
                $meilleur = new Devis($t->nom(), $montant);
            }
        }
        if ($meilleur === null) {
            throw new DomainException('Aucun transporteur disponible');
        }
        return $meilleur;
    }
}

$calc = new CalculateurFraisDePort(new Colissimo(), new Chronopost());
$d = $calc->meilleurDevis(2.0);
printf("%s : %.2f €\n", $d->transporteur, $d->montant);   // Colissimo : 7.30 €
$d = $calc->meilleurDevis(20.0);
printf("%s : %.2f €\n", $d->transporteur, $d->montant);   // Chronopost : 25.00 €

// Scénarios de test
$c = new CalculateurFraisDePort(new FakeTransporteur('A', 10.0), new FakeTransporteur('B', 7.0));
assert($c->meilleurDevis(1.0)->transporteur === 'B');

$c = new CalculateurFraisDePort(new FakeTransporteur('A', 10.0), new FakeTransporteur('B', panne: true));
assert($c->meilleurDevis(1.0)->transporteur === 'A');

$c = new CalculateurFraisDePort(new FakeTransporteur('A', panne: true));
try { $c->meilleurDevis(1.0); assert(false); } catch (DomainException $e) { /* attendu */ }
""")],
       ["Le calculateur ne contient aucun nom de transporteur réel",
        "Un transporteur en panne n'empêche pas d'obtenir un devis des autres",
        "Tes 3 scénarios passent avec `FakeTransporteur` sans toucher à Colissimo ni Chronopost"],
       run=RUN("php", tests=r"""
check('TransporteurIndisponible étend RuntimeException', is_subclass_of(TransporteurIndisponible::class, RuntimeException::class));
check('Transporteur est une interface avec nom() et devis()', interface_exists('Transporteur') && method_exists('Transporteur', 'nom') && method_exists('Transporteur', 'devis'));
$calc = new CalculateurFraisDePort(new Colissimo(), new Chronopost());
$d = $calc->meilleurDevis(2.0);
check('2 kg : Colissimo à 7.30', $d->transporteur === 'Colissimo' && abs($d->montant - 7.30) < 0.001, $d->transporteur . ' ' . $d->montant);
$d = $calc->meilleurDevis(20.0);
check('20 kg : Chronopost à 25.00', $d->transporteur === 'Chronopost' && abs($d->montant - 25.0) < 0.001);
$d = $calc->meilleurDevis(40.0);
check('40 kg : Chronopost refuse, Colissimo choisi', $d->transporteur === 'Colissimo');
$c = new CalculateurFraisDePort(new FakeTransporteur('A', 10.0), new FakeTransporteur('B', 7.0));
check('fake : le moins cher gagne', $c->meilleurDevis(1.0)->transporteur === 'B');
$c = new CalculateurFraisDePort(new FakeTransporteur('A', 10.0), new FakeTransporteur('B', panne: true));
check('fake : la panne est ignorée', $c->meilleurDevis(1.0)->transporteur === 'A');
$c = new CalculateurFraisDePort(new FakeTransporteur('A', panne: true));
check('aucun disponible : DomainException', throws(fn() => $c->meilleurDevis(1.0), DomainException::class));
check('constructeur variadique', (new ReflectionMethod(CalculateurFraisDePort::class, '__construct'))->isVariadic());
"""), expected="Colissimo : 7.30 €\nChronopost : 25.00 €"),
  ])

# ---------------------------------------------------------------- namespaces
ns = V2(v1["php-namespaces"],
  prereq=[
    P("`require`", "Instruction qui charge un autre fichier PHP : `require 'Produit.php';`. Avant l'autoload, il fallait en écrire un par classe utilisée."),
    P("Composer", "Le gestionnaire de dépendances de PHP. Il installe les librairies dans `vendor/` et génère `vendor/autoload.php`, le fichier qui sait charger toutes les classes."),
    P("FQCN", "*Fully Qualified Class Name* : le nom complet d'une classe avec son namespace, `App\\Catalogue\\Produit`. C'est ce nom que PHP utilise réellement."),
    P("PSR-4", "Une norme de la communauté PHP qui dit comment faire correspondre un namespace à un dossier. Composer et Symfony la suivent."),
    P("`__DIR__`", "Constante magique qui vaut le dossier du fichier courant. `__DIR__ . '/vendor/autoload.php'` marche quel que soit l'endroit d'où on lance le script."),
  ],
  diagram=D(
    nodes=[
      N("code", 0, 0, "new Produit('Clavier')", "dans index.php", kind="pill"),
      N("use", 1, 0, "use App\\Catalogue\\Produit", "→ App\\Catalogue\\Produit", kind="note"),
      N("auto", 2, 0, "Autoloader", "vendor/autoload.php"),
      N("map", 2, 1, "composer.json", "\"App\\\\\" : \"src/\"", kind="doc"),
      N("file", 3, 0, "src/Catalogue/Produit.php", "", kind="file", color="good"),
    ],
    edges=[E("code", "use", "1 nom complet"), E("use", "auto", "2 classe inconnue ?"), E("map", "auto", "règle", dashed=True), E("auto", "file", "3 require")],
    caption="À la première utilisation d'une classe, l'autoloader traduit son nom complet en chemin de fichier et le charge."),
  lessons=[
    L("Deux problèmes que les namespaces règlent", r"""
**Les collisions de noms.** Ton projet a une classe `User`. La librairie d'authentification que tu installes a aussi une classe `User`. En PHP, deux classes ne peuvent pas porter le même nom : l'une des deux casse l'autre. Avec des namespaces, elles s'appellent `App\Security\User` et `Vendor\Auth\User` : plus de conflit.

**Les `require` à la main.** Sans namespace ni autoload, chaque fichier commence par une liste de `require 'Produit.php'; require 'Catalogue.php'; …` qu'il faut maintenir. On oublie un fichier, on en charge deux fois, on crée des chemins relatifs fragiles. L'**autoloader** supprime tout ça : tu utilises une classe, PHP la charge tout seul.

Les deux mécanismes vont ensemble : le namespace donne à chaque classe un nom complet unique, et c'est ce nom complet que l'autoloader traduit en chemin de fichier.
"""),
    L("Déclarer et utiliser un namespace", r"""
```php
<?php
// src/Catalogue/Produit.php
namespace App\Catalogue;

final class Produit { /* ... */ }
```

La ligne `namespace` est la première instruction du fichier. Le nom complet de cette classe est désormais `App\Catalogue\Produit`. Pour l'utiliser ailleurs, trois façons :

```php
// 1. le nom complet, à chaque fois (lourd)
$p = new \App\Catalogue\Produit('Clavier');

// 2. importer une fois en haut du fichier, puis le nom court (la norme)
use App\Catalogue\Produit;
$p = new Produit('Clavier');

// 3. renommer en cas de conflit
use App\Catalogue\Produit as ProduitCatalogue;
```

Le piège classique : **dans** un fichier qui a un namespace, les classes natives de PHP (`DateTimeImmutable`, `Exception`, `InvalidArgumentException`…) ne sont plus trouvées automatiquement. `new DateTimeImmutable()` cherche `App\Catalogue\DateTimeImmutable`, qui n'existe pas. Deux solutions : `use DateTimeImmutable;` en haut, ou le préfixe `\` : `new \DateTimeImmutable()`. Les **fonctions** natives (`strlen`, `array_map`), elles, sont trouvées sans rien faire.
"""),
    L("PSR-4 : le namespace suit les dossiers", r"""
L'autoloader a besoin d'une règle pour passer du nom `App\Catalogue\Produit` au fichier. La norme PSR-4 dit :

1. On déclare un **préfixe** et le dossier qui lui correspond, dans `composer.json` : `"App\\"` → `"src/"`.
2. Le reste du namespace devient des **sous-dossiers** : `Catalogue` → `src/Catalogue/`.
3. Le nom de la classe devient le **nom du fichier** : `Produit` → `Produit.php`.

Donc `App\Catalogue\Produit` → `src/Catalogue/Produit.php`. Conséquences pratiques :

- **Une classe par fichier**, fichier nommé exactement comme la classe (majuscules comprises).
- Le namespace d'un fichier **doit** correspondre à son dossier. Si tu déplaces un fichier, tu changes son namespace, et les `use` qui le référencent.
- Si tu modifies la section `autoload` de `composer.json`, lance `composer dump-autoload` pour régénérer la table de correspondance.

Dans un projet Symfony, tout est déjà configuré : `src/` ↔ `App\`. Quand tu crées `src/Service/Facturation.php`, tu écris `namespace App\Service;` et c'est tout.
"""),
    L("Ce qui se passe au moment du `new`", r"""
Dans `index.php`, tu écris `require __DIR__ . '/vendor/autoload.php';` **une seule fois**. Ce fichier enregistre une fonction d'autoload auprès de PHP. Ensuite :

1. PHP rencontre `new Produit(...)`, résout le nom complet grâce au `use` : `App\Catalogue\Produit`.
2. La classe n'est pas encore chargée → PHP appelle l'autoloader avec ce nom.
3. L'autoloader applique la règle PSR-4 : préfixe `App\` → `src/`, reste → `Catalogue/Produit.php`.
4. Il fait le `require` du fichier. La classe existe maintenant, le `new` continue.

La fois suivante, la classe est déjà chargée : rien à faire. C'est pour ça que « Class not found » veut presque toujours dire : le namespace ne correspond pas au dossier, le nom du fichier n'est pas exactement celui de la classe, ou `composer dump-autoload` n'a pas été relancé.
"""),
  ],
  recap=[
    "Un namespace donne à chaque classe un nom complet unique : `App\\Catalogue\\Produit`.",
    "`use` importe une classe en haut du fichier pour écrire son nom court.",
    "Dans un namespace, les classes natives demandent `use` ou `\\` ; les fonctions natives, non.",
    "PSR-4 : `App\\` ↔ `src/`, puis le namespace suit les dossiers et la classe donne le nom du fichier.",
    "« Class not found » = namespace ≠ dossier, nom de fichier ≠ nom de classe, ou `dump-autoload` oublié.",
  ],
  example=[F("composer.json", "json", r"""
{
  "autoload": {
    "psr-4": { "App\\": "src/" }
  }
}
"""), F("src/Catalogue/Produit.php", "php", r"""
<?php
declare(strict_types=1);

namespace App\Catalogue;

use DateTimeImmutable;

final class Produit
{
    public function __construct(
        private string $nom,
        private DateTimeImmutable $creeLe = new DateTimeImmutable(),
    ) {}

    public function nom(): string { return $this->nom; }
}
"""), F("public/index.php", "php", r"""
<?php
declare(strict_types=1);

require __DIR__ . '/../vendor/autoload.php';

use App\Catalogue\Produit;

$produit = new Produit('Clavier');   // l'autoloader charge src/Catalogue/Produit.php
echo $produit->nom();
""")],
  notes=["`composer.json` : la seule règle, `App\\` → `src/`. Lance `composer dump-autoload` après l'avoir ajoutée.",
         "`Produit.php` : le dossier `src/Catalogue` correspond au namespace `App\\Catalogue`. `use DateTimeImmutable;` importe la classe native.",
         "`index.php` : un seul `require` (l'autoload). Aucun `require` de `Produit.php`.",
         "`__DIR__ . '/../vendor/autoload.php'` : chemin construit depuis le dossier de `index.php`, donc valable d'où qu'on lance le script."],
  td1=dict(path="arborescence.txt", expected="1"),
  tds=[
    TD(2, "Diagnostiquer des « Class not found »",
       "Voici l'arborescence d'un projet et quatre erreurs rencontrées par un collègue. Pour chacune, trouve la cause précise et la correction. Exercice de lecture : pas de code à exécuter, mais tu dois raisonner exactement comme l'autoloader.",
       ["Pour chaque cas 1 à 4 : écris la cause en une phrase et la correction (fichier à modifier, ligne)",
        "Indique le nom complet (FQCN) que PHP a réellement cherché",
        "Bonus : pour le cas 4, propose deux corrections différentes"],
       [F("diagnostic.txt", "plaintext", r"""
composer.json : { "autoload": { "psr-4": { "App\\": "src/" } } }

src/
├── Catalogue/
│   ├── Produit.php          namespace App\Catalogue;   final class Produit
│   └── categorie.php        namespace App\Catalogue;   final class Categorie
├── Panier/
│   └── Panier.php           namespace App\Catalog;     final class Panier
└── Service/
    └── Facture.php          namespace App\Service;     final class Facture
                              -> contient : $date = new DateTimeImmutable();

public/index.php :
    require __DIR__ . '/../vendor/autoload.php';
    use App\Catalogue\Produit;
    use App\Panier\Panier;
    $p = new Produit('x');            // OK
    $c = new Categorie('y');          // 1) Class "Categorie" not found
    $panier = new Panier();           // 2) Class "App\Panier\Panier" not found
    $f = new App\Service\Facture();   // 3) Class "App\Service\Facture" not found ... puis après correction :
                                      // 4) Class "App\Service\DateTimeImmutable" not found

Cas 1 :
Cas 2 :
Cas 3 :
Cas 4 :
""")],
       ["Cas 1 : il y a deux problèmes, un dans `index.php` et un dans le nom du fichier.",
        "Cas 2 : compare le namespace déclaré dans `Panier.php` avec le dossier.",
        "Cas 3 : relis la ligne `$f = new App\\Service\\Facture();` : elle est écrite **sans** `\\` initial, dans un fichier… qui n'a pas de namespace. Alors pourquoi l'erreur ? Regarde bien la casse."],
       [F("diagnostic.txt", "plaintext", r"""
Cas 1 : index.php n'importe pas Categorie (pas de "use App\Catalogue\Categorie;"), donc PHP cherche
        "\Categorie" dans l'espace global -> introuvable.
        Après ajout du use, deuxième erreur : le fichier s'appelle categorie.php (minuscule) alors que
        PSR-4 exige Categorie.php. Renommer le fichier.
        FQCN cherché : Categorie (puis App\Catalogue\Categorie -> src/Catalogue/Categorie.php).

Cas 2 : index.php demande App\Panier\Panier -> src/Panier/Panier.php. Le fichier existe, mais il
        déclare "namespace App\Catalog;" : la classe chargée s'appelle App\Catalog\Panier,
        pas App\Panier\Panier. Corriger la ligne namespace en "namespace App\Panier;".

Cas 3 : (piège) la ligne est correcte dans un fichier sans namespace : App\Service\Facture est bien le
        nom complet. L'erreur vient d'ailleurs : vérifier que composer dump-autoload a été lancé après
        la création du dossier Service, ou que le fichier n'est pas Facture.PHP / facture.php.
        Si tout est bon, c'est le cache de l'autoloader : composer dump-autoload.

Cas 4 : dans Facture.php (namespace App\Service), "new DateTimeImmutable()" est résolu en
        App\Service\DateTimeImmutable. Correction A : ajouter "use DateTimeImmutable;" en haut du
        fichier. Correction B : écrire "new \DateTimeImmutable()".
""")],
       ["Tu as donné le FQCN réellement cherché pour chaque cas",
        "Le cas 4 a deux corrections valides"]),
    TD(3, "Deux librairies, même nom de classe",
       "Ton projet utilise deux librairies qui exposent chacune une classe `Client` : `Acme\\Http\\Client` et `Shop\\Crm\\Client`. Tu dois les utiliser **toutes les deux dans le même fichier**, puis écrire un adaptateur dans ton propre namespace. Exercice à faire dans un vrai projet avec Composer : il entraîne les alias, l'organisation en dossiers et `dump-autoload`.",
       ["Crée un projet vide avec `composer init` (ou un `composer.json` minimal) et le mapping `App\\` → `src/`",
        "Simule les deux librairies dans `lib/acme/Client.php` et `lib/shop/Client.php` (namespaces `Acme\\Http` et `Shop\\Crm`), avec un mapping PSR-4 pour chacune (`Acme\\Http\\` → `lib/acme/`, `Shop\\Crm\\` → `lib/shop/`)",
        "`src/Crm/SynchroClients.php` (namespace `App\\Crm`) utilise les deux `Client` grâce à des **alias** `use … as …`",
        "`index.php` instancie `SynchroClients` et appelle `synchroniser()` qui affiche `HTTP -> CRM : ok`",
        "Lance `composer dump-autoload` puis `php index.php` ; ensuite, casse volontairement un namespace et observe l'erreur"],
       [F("composer.json", "json", r"""
{
  "autoload": {
    "psr-4": {
      "App\\": "src/"
    }
  }
}
"""), F("structure.txt", "plaintext", r"""
projet/
├── composer.json
├── index.php
├── lib/
│   ├── acme/Client.php      namespace Acme\Http
│   └── shop/Client.php      namespace Shop\Crm
└── src/
    └── Crm/
        └── SynchroClients.php   namespace App\Crm
""")],
       ["Plusieurs préfixes PSR-4 dans le même `composer.json` : une clé par préfixe dans l'objet `psr-4`.",
        "`use Acme\\Http\\Client as HttpClient; use Shop\\Crm\\Client as CrmClient;` puis `new HttpClient()` et `new CrmClient()`.",
        "Après toute modification de `composer.json` : `composer dump-autoload`."],
       [F("composer.json", "json", r"""
{
  "autoload": {
    "psr-4": {
      "App\\": "src/",
      "Acme\\Http\\": "lib/acme/",
      "Shop\\Crm\\": "lib/shop/"
    }
  }
}
"""), F("lib/acme/Client.php", "php", r"""
<?php
namespace Acme\Http;

final class Client
{
    public function get(string $url): string { return "HTTP"; }
}
"""), F("lib/shop/Client.php", "php", r"""
<?php
namespace Shop\Crm;

final class Client
{
    public function importer(string $donnees): string { return "$donnees -> CRM : ok"; }
}
"""), F("src/Crm/SynchroClients.php", "php", r"""
<?php
declare(strict_types=1);

namespace App\Crm;

use Acme\Http\Client as HttpClient;
use Shop\Crm\Client as CrmClient;

final class SynchroClients
{
    public function __construct(
        private HttpClient $http = new HttpClient(),
        private CrmClient $crm = new CrmClient(),
    ) {}

    public function synchroniser(): string
    {
        $donnees = $this->http->get('/clients');
        return $this->crm->importer($donnees);
    }
}
"""), F("index.php", "php", r"""
<?php
require __DIR__ . '/vendor/autoload.php';

use App\Crm\SynchroClients;

echo (new SynchroClients())->synchroniser(), PHP_EOL;   // HTTP -> CRM : ok
""")],
       ["`php index.php` affiche `HTTP -> CRM : ok` sans aucun `require` de classe",
        "Les deux classes `Client` cohabitent dans `SynchroClients.php`",
        "Changer `namespace Shop\\Crm;` en `namespace Shop\\CRM;` provoque « Class not found » : tu sais expliquer pourquoi"],
       expected="HTTP -> CRM : ok"),
  ])

# ---------------------------------------------------------------- injection de dépendances
di = V2(v1["php-di"],
  prereq=[
    P("Dépendance", "Tout objet dont une classe a besoin pour faire son travail : un repository, un mailer, une connexion à la base, une horloge…"),
    P("Interface", "Un contrat sans code que plusieurs classes peuvent implémenter (module précédent). L'injection prend tout son sens quand on injecte des interfaces."),
    P("Service", "Dans Symfony, un objet qui **fait** quelque chose (envoyer un mail, calculer, enregistrer) et dont on a besoin d'une seule instance. Par opposition aux objets de **données** (entités, DTO, value objects)."),
    P("Conteneur de services", "L'objet de Symfony qui connaît tous les services, sait les construire dans le bon ordre et les fournir à qui en a besoin. On ne l'appelle presque jamais directement."),
    P("Autowiring", "La capacité du conteneur à deviner quoi injecter en lisant les **types** du constructeur. `private Mailer $mailer` suffit : il cherche le service de type `Mailer`."),
  ],
  diagram=D(
    nodes=[
      N("cont", 1, 0, "Conteneur Symfony", "lit les types des constructeurs", color="accent"),
      N("repo", 0, 1, "MysqlUserRepository", "implements UserRepository"),
      N("mail", 2, 1, "SmtpMailer", "implements Mailer"),
      N("svc", 1, 2, "InscriptionService", "(UserRepository, Mailer)", color="good"),
      N("ctrl", 1, 3, "Contrôleur", "reçoit InscriptionService", kind="pill"),
    ],
    edges=[E("cont", "repo", "1 crée", color="accent"), E("cont", "mail", "1 crée", color="accent"), E("repo", "svc", "2 injecte"), E("mail", "svc", "2 injecte"), E("svc", "ctrl", "3 injecte")],
    lanes=[LANE("Construit automatiquement par Symfony", 0, 2, "accent")],
    caption="Personne n'écrit ces `new` : le conteneur construit chaque service une fois et le passe à ceux qui le demandent."),
  lessons=[
    L("Le problème : une classe qui construit ses propres outils", r"""
```php
final class InscriptionService
{
    public function inscrire(string $email): void
    {
        $repo = new MysqlUserRepository(new PDO('mysql:host=db;dbname=shop', 'root', 'secret'));
        $repo->save($email);
        (new SmtpMailer('smtp.exemple.com'))->send($email, 'Bienvenue');
    }
}
```

Cette classe **décide** elle-même de ses outils. Trois conséquences :

- **Impossible à tester** sans une vraie base MySQL et un vrai serveur SMTP. Chaque test envoie un mail.
- **Impossible à reconfigurer** : passer à PostgreSQL ou à Mailjet oblige à modifier `InscriptionService`, qui n'a pourtant rien à voir avec ces choix.
- **Les secrets se baladent** dans le code métier (`'root', 'secret'`).

Le principe de l'**injection de dépendances** est simple : une classe ne construit pas ses dépendances, elle les **reçoit**. Elle déclare ce dont elle a besoin, et quelqu'un d'autre les lui fournit.
"""),
    L("Injecter par le constructeur", r"""
```php
final class InscriptionService
{
    public function __construct(
        private UserRepository $users,   // une interface
        private Mailer $mailer,          // une interface
    ) {}

    public function inscrire(string $email): void
    {
        $this->users->save($email);
        $this->mailer->send($email, 'Bienvenue');
    }
}
```

Le constructeur est la liste des besoins de la classe. Elle n'a plus aucun `new` de service, aucun secret, aucune idée de l'implémentation utilisée. Celui qui la construit choisit :

```php
// En production
$service = new InscriptionService(new MysqlUserRepository($pdo), new SmtpMailer($config));

// En test : instantané, sans réseau
$service = new InscriptionService(new InMemoryUserRepository(), new FakeMailer());
```

Pourquoi le constructeur plutôt qu'un setter ? Parce qu'un objet dont le constructeur a réussi est **prêt à l'emploi** : il ne peut pas exister à moitié configuré. Les dépendances obligatoires passent toujours par le constructeur.
"""),
    L("Ce qui s'injecte et ce qui se crée avec `new`", r"""
Tout ne doit pas être injecté. La distinction :

- **Services** : objets qui *font* quelque chose, souvent branchés sur l'extérieur (base, réseau, fichiers, horloge), dont une seule instance suffit. `UserRepository`, `Mailer`, `Logger`, `HttpClient`, `PaymentGateway`. → **injectés**.
- **Objets de données** : entités, DTO, value objects (`Email`, `Prix`, `DateTimeImmutable`, `Commande`). Ils n'ont pas de dépendances externes, on en crée autant qu'on veut, avec des valeurs différentes à chaque fois. → **`new` partout, c'est normal**.

Un cas limite : le **temps**. `new DateTimeImmutable('today')` dans un service rend les tests dépendants du jour où ils tournent. On injecte alors une interface `Horloge` (Symfony fournit `ClockInterface`), dont la fausse version renvoie une date fixe. Même logique pour le hasard (`random_int`) : si un test doit être reproductible, la source d'aléa s'injecte.
"""),
    L("Le conteneur Symfony fait les `new` pour toi", r"""
Dans un vrai projet, écrire à la main `new InscriptionService(new MysqlUserRepository(new PDO(...)), new SmtpMailer(...))` serait vite ingérable. C'est le travail du **conteneur de services**.

Au démarrage, Symfony parcourt `src/`, enregistre chaque classe comme service, puis lit les **types** de leurs constructeurs. Pour construire `InscriptionService`, il voit qu'il faut un `UserRepository` et un `Mailer` ; il cherche quel service a ce type, le construit (en construisant d'abord **ses** dépendances), et l'injecte. C'est l'**autowiring**. Il ne construit chaque service qu'une fois et le réutilise.

Deux règles pour que ça marche :

- Type-hinter avec l'**interface** quand il y en a une. Si une seule classe l'implémente, Symfony fait le lien tout seul. S'il y en a plusieurs, tu indiques laquelle dans `config/services.yaml` (un alias).
- Les valeurs qui ne sont pas des services (une chaîne de connexion, une clé d'API) se passent par des **paramètres** liés dans la configuration, ou par des variables d'environnement.

`php bin/console debug:autowiring Mailer` te montre ce que tu peux injecter en tapant un nom. Et si tu vois une classe injecter le conteneur lui-même (`ContainerInterface`) pour y piocher des services, c'est un anti-pattern : ça cache ses vraies dépendances, et on perd tout l'intérêt de la lisibilité du constructeur.
"""),
  ],
  recap=[
    "Une classe **reçoit** ses dépendances par le constructeur ; elle n'en fait pas le `new`.",
    "Les dépendances sont typées par des **interfaces** : en test on injecte une fausse implémentation.",
    "Services (font quelque chose, une instance) → injectés. Objets de données (entités, VO, DTO) → `new`.",
    "Le temps et le hasard sont des dépendances comme les autres quand ils influencent le résultat.",
    "Symfony construit et injecte tout seul en lisant les types : c'est l'autowiring.",
  ],
  example=[F("src/Service/InscriptionService.php", "php", r"""
<?php
declare(strict_types=1);

namespace App\Service;

use App\Repository\UserRepository;
use App\Mail\Mailer;

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
"""), F("src/Repository/UserRepository.php", "php", r"""
<?php
namespace App\Repository;

interface UserRepository
{
    public function save(string $email): void;
}
"""), F("src/Mail/Mailer.php", "php", r"""
<?php
namespace App\Mail;

interface Mailer
{
    public function send(string $to, string $subject): void;
}
"""), F("tests/InscriptionServiceTest.php", "php", r"""
<?php
// Les fausses implémentations : rapides, sans base ni réseau
final class InMemoryUserRepository implements UserRepository
{
    public array $saved = [];
    public function save(string $email): void { $this->saved[] = $email; }
}

final class FakeMailer implements Mailer
{
    public array $sent = [];
    public function send(string $to, string $subject): void { $this->sent[] = [$to, $subject]; }
}

$repo = new InMemoryUserRepository();
$mailer = new FakeMailer();
$service = new InscriptionService($repo, $mailer);

$service->inscrire('ana@mail.com');

assert($repo->saved === ['ana@mail.com']);
assert($mailer->sent === [['ana@mail.com', 'Bienvenue']]);
""")],
  notes=["`InscriptionService.php` : deux dépendances déclarées dans le constructeur, typées par des interfaces. Aucun `new`.",
         "Les deux interfaces ne contiennent que le contrat. En production, Symfony injecte `MysqlUserRepository` et `SmtpMailer` (non montrés).",
         "`InscriptionServiceTest.php` : on construit le service **à la main** avec des fausses implémentations, puis on vérifie ce qu'elles ont reçu.",
         "Le service n'a pas changé d'une ligne entre la prod et le test."],
  td1=dict(path="RapportService.php", run=RUN("php", tests=r"""
check('VentesRepository est une interface', interface_exists('VentesRepository'));
check('Horloge est une interface', interface_exists('Horloge'));
$ctor = new ReflectionMethod(RapportService::class, '__construct');
$types = array_map(fn($p) => (string) $p->getType(), $ctor->getParameters());
check('le constructeur reçoit VentesRepository et Horloge', in_array('VentesRepository', $types) && in_array('Horloge', $types), implode(', ', $types));
$service = new RapportService(
    new class implements VentesRepository { public function totalDu(DateTimeImmutable $jour): float { return 1234.5; } },
    new class implements Horloge { public function aujourdhui(): DateTimeImmutable { return new DateTimeImmutable('2026-01-15'); } },
);
check('genererDuJour() utilise l\'horloge et le repository injectés', $service->genererDuJour() === 'Ventes du 15/01/2026 : 1234.50 €', $service->genererDuJour());
$src = (new ReflectionClass(RapportService::class));
$body = implode("\n", array_slice(file(__FILE__), $src->getStartLine() - 1, $src->getEndLine() - $src->getStartLine() + 1));
check('RapportService ne contient plus "new PDO"', !str_contains($body, 'new PDO'));
check('RapportService ne contient plus new DateTimeImmutable(\'today\')', !str_contains($body, "DateTimeImmutable('today')"));
""")),
  tds=[
    TD(2, "Horloge et générateur d'identifiants",
       "Un service crée des commandes avec un numéro `CMD-AAAAMMJJ-XXXX` (date du jour + 4 caractères aléatoires) et refuse les commandes passées le dimanche. Impossible à tester tel quel : le résultat change chaque jour et à chaque exécution. Injecte le temps et le hasard.",
       ["Interface `Horloge { public function maintenant(): DateTimeImmutable; }` et interface `GenerateurId { public function generer(int $longueur): string; }`",
        "`HorlogeSysteme` et `GenerateurAleatoire` : les vraies implémentations (`new DateTimeImmutable()`, `bin2hex(random_bytes(...))` tronqué)",
        "`CommandeService::__construct(Horloge $horloge, GenerateurId $ids)` et `creer(string $client): string` qui renvoie le numéro",
        "`DomainException` si `maintenant()` tombe un dimanche (`format('N') === '7'`)",
        "Fausses implémentations pour le test : `HorlogeFixe(DateTimeImmutable $date)` et `GenerateurFixe(string $valeur)`"],
       [F("CommandeService.php", "php", r"""
<?php
declare(strict_types=1);

// AVANT : impossible à tester
final class CommandeServiceAvant
{
    public function creer(string $client): string
    {
        $now = new DateTimeImmutable();
        if ($now->format('N') === '7') {
            throw new DomainException('Pas de commande le dimanche');
        }
        return 'CMD-' . $now->format('Ymd') . '-' . strtoupper(substr(bin2hex(random_bytes(2)), 0, 4));
    }
}

// APRÈS : à toi (interfaces, vraies implémentations, fausses, service)

$service = new CommandeService(new HorlogeFixe(new DateTimeImmutable('2026-03-02')), new GenerateurFixe('AB12'));
echo $service->creer('ana');   // CMD-20260302-AB12
""")],
       ["Une fausse horloge : `final class HorlogeFixe implements Horloge { public function __construct(private DateTimeImmutable $d) {} public function maintenant(): DateTimeImmutable { return $this->d; } }`.",
        "Le test du dimanche : `new HorlogeFixe(new DateTimeImmutable('2026-03-01'))` (un dimanche) doit faire lever l'exception.",
        "Le service ne fait plus aucun `new DateTimeImmutable()` ni `random_bytes` : tout passe par les interfaces."],
       [F("CommandeService.php", "php", r"""
<?php
declare(strict_types=1);

interface Horloge
{
    public function maintenant(): DateTimeImmutable;
}

interface GenerateurId
{
    public function generer(int $longueur): string;
}

final class HorlogeSysteme implements Horloge
{
    public function maintenant(): DateTimeImmutable { return new DateTimeImmutable(); }
}

final class GenerateurAleatoire implements GenerateurId
{
    public function generer(int $longueur): string
    {
        return strtoupper(substr(bin2hex(random_bytes((int) ceil($longueur / 2))), 0, $longueur));
    }
}

final class HorlogeFixe implements Horloge
{
    public function __construct(private DateTimeImmutable $date) {}
    public function maintenant(): DateTimeImmutable { return $this->date; }
}

final class GenerateurFixe implements GenerateurId
{
    public function __construct(private string $valeur) {}
    public function generer(int $longueur): string { return $this->valeur; }
}

final class CommandeService
{
    public function __construct(private Horloge $horloge, private GenerateurId $ids) {}

    public function creer(string $client): string
    {
        $now = $this->horloge->maintenant();
        if ($now->format('N') === '7') {
            throw new DomainException('Pas de commande le dimanche');
        }
        return 'CMD-' . $now->format('Ymd') . '-' . $this->ids->generer(4);
    }
}

$service = new CommandeService(new HorlogeFixe(new DateTimeImmutable('2026-03-02')), new GenerateurFixe('AB12'));
echo $service->creer('ana');   // CMD-20260302-AB12
""")],
       ["Le même test donne le même résultat quel que soit le jour où il tourne",
        "Le cas « dimanche » est testable sans attendre dimanche",
        "`new CommandeService(new HorlogeSysteme(), new GenerateurAleatoire())` fonctionne en production"],
       run=RUN("php", tests=r"""
check('Horloge et GenerateurId sont des interfaces', interface_exists('Horloge') && interface_exists('GenerateurId'));
$s = new CommandeService(new HorlogeFixe(new DateTimeImmutable('2026-03-02')), new GenerateurFixe('AB12'));
check('numéro déterministe CMD-20260302-AB12', $s->creer('ana') === 'CMD-20260302-AB12', $s->creer('ana'));
$dim = new CommandeService(new HorlogeFixe(new DateTimeImmutable('2026-03-01')), new GenerateurFixe('AB12'));
check('dimanche refusé', throws(fn() => $dim->creer('ana'), DomainException::class));
$real = new CommandeService(new HorlogeSysteme(), new GenerateurAleatoire());
try { $num = $real->creer('x'); check('vraies implémentations : format CMD-AAAAMMJJ-XXXX', preg_match('/^CMD-\d{8}-[A-Z0-9]{4}$/', $num) === 1, $num); }
catch (DomainException $e) { check('vraies implémentations : dimanche refusé (on est dimanche)', true); }
check('GenerateurAleatoire::generer(4) fait 4 caractères', strlen((new GenerateurAleatoire())->generer(4)) === 4);
$body = implode("\n", array_slice(file(__FILE__), (new ReflectionClass(CommandeService::class))->getStartLine() - 1, (new ReflectionClass(CommandeService::class))->getEndLine() - (new ReflectionClass(CommandeService::class))->getStartLine() + 1));
check('CommandeService ne fait plus new DateTimeImmutable()', !str_contains($body, 'new DateTimeImmutable'));
check('CommandeService n\'appelle plus random_bytes', !str_contains($body, 'random_bytes'));
"""), expected="CMD-20260302-AB12"),
    TD(3, "Un mini-conteneur avec autowiring",
       "Pour comprendre ce que Symfony fait pour toi, écris un **mini-conteneur** : une classe `Conteneur` capable de construire n'importe quel service en lisant les types de son constructeur avec la Reflection, en construisant d'abord ses dépendances, et en gardant une seule instance de chaque. Tu lui ajoutes la possibilité de lier une interface à une implémentation. C'est, en 60 lignes, le cœur de l'autowiring.",
       ["`Conteneur::lier(string $interface, string $classe)` : « quand on demande cette interface, construis cette classe »",
        "`Conteneur::get(string $id): object` : renvoie toujours la **même** instance pour un même id",
        "Construction : via `new ReflectionClass($classe)`, lire les paramètres du constructeur ; pour chaque paramètre typé par une classe ou une interface, appeler récursivement `get()` ; un paramètre avec valeur par défaut et sans type d'objet prend sa valeur par défaut",
        "Exceptions claires : interface non liée → `LogicException('Aucune implémentation pour X')` ; paramètre scalaire sans défaut → `LogicException`",
        "Détecte une **dépendance circulaire** (A a besoin de B qui a besoin de A) et lève une `LogicException` au lieu de boucler",
        "Fais-le fonctionner sur `InscriptionService(UserRepository, Mailer)` du cours"],
       [F("Conteneur.php", "php", r"""
<?php
declare(strict_types=1);

interface UserRepository { public function save(string $email): void; }
interface Mailer { public function send(string $to, string $subject): void; }

final class InMemoryUserRepository implements UserRepository
{
    public array $saved = [];
    public function save(string $email): void { $this->saved[] = $email; }
}

final class FakeMailer implements Mailer
{
    public array $sent = [];
    public function __construct(private Logger $logger) {}
    public function send(string $to, string $subject): void { $this->sent[] = [$to, $subject]; $this->logger->log("mail à $to"); }
}

final class Logger
{
    public array $lignes = [];
    public function __construct(private string $prefixe = '[log]') {}
    public function log(string $m): void { $this->lignes[] = "$this->prefixe $m"; }
}

final class InscriptionService
{
    public function __construct(private UserRepository $users, private Mailer $mailer) {}
    public function inscrire(string $email): void { $this->users->save($email); $this->mailer->send($email, 'Bienvenue'); }
}

final class Conteneur
{
    // à toi
}

$c = new Conteneur();
$c->lier(UserRepository::class, InMemoryUserRepository::class);
$c->lier(Mailer::class, FakeMailer::class);

$service = $c->get(InscriptionService::class);
$service->inscrire('ana@mail.com');

echo count($c->get(InMemoryUserRepository::class)->saved), PHP_EOL;   // 1 : même instance
echo $c->get(Logger::class)->lignes[0], PHP_EOL;                       // [log] mail à ana@mail.com
""")],
       ["`$ref = new ReflectionClass($classe); $ctor = $ref->getConstructor(); $params = $ctor ? $ctor->getParameters() : [];`",
        "Pour un paramètre : `$type = $p->getType(); if ($type instanceof ReflectionNamedType && !$type->isBuiltin()) $args[] = $this->get($type->getName()); elseif ($p->isDefaultValueAvailable()) $args[] = $p->getDefaultValue(); else throw ...`.",
        "Instance unique : un tableau `private array $instances = []` consulté au début de `get()`.",
        "Circularité : un tableau `$enCours` ; si `$id` y est déjà quand on entre dans `get()`, c'est une boucle. Pense à le retirer à la sortie."],
       [F("Conteneur.php", "php", r"""
<?php
declare(strict_types=1);

interface UserRepository { public function save(string $email): void; }
interface Mailer { public function send(string $to, string $subject): void; }

final class InMemoryUserRepository implements UserRepository
{
    public array $saved = [];
    public function save(string $email): void { $this->saved[] = $email; }
}

final class FakeMailer implements Mailer
{
    public array $sent = [];
    public function __construct(private Logger $logger) {}
    public function send(string $to, string $subject): void { $this->sent[] = [$to, $subject]; $this->logger->log("mail à $to"); }
}

final class Logger
{
    public array $lignes = [];
    public function __construct(private string $prefixe = '[log]') {}
    public function log(string $m): void { $this->lignes[] = "$this->prefixe $m"; }
}

final class InscriptionService
{
    public function __construct(private UserRepository $users, private Mailer $mailer) {}
    public function inscrire(string $email): void { $this->users->save($email); $this->mailer->send($email, 'Bienvenue'); }
}

final class Conteneur
{
    /** @var array<string, string> interface => classe */
    private array $liaisons = [];
    /** @var array<string, object> */
    private array $instances = [];
    /** @var array<string, true> */
    private array $enCours = [];

    public function lier(string $interface, string $classe): void
    {
        $this->liaisons[$interface] = $classe;
    }

    public function get(string $id): object
    {
        if (isset($this->instances[$id])) {
            return $this->instances[$id];
        }
        if (isset($this->enCours[$id])) {
            throw new LogicException("Dépendance circulaire détectée sur $id");
        }
        $classe = $this->liaisons[$id] ?? $id;
        if (interface_exists($classe)) {
            throw new LogicException("Aucune implémentation pour $classe");
        }
        if (!class_exists($classe)) {
            throw new LogicException("Classe inconnue : $classe");
        }

        $this->enCours[$id] = true;
        try {
            $instance = $this->construire($classe);
        } finally {
            unset($this->enCours[$id]);
        }
        return $this->instances[$id] = $this->instances[$classe] = $instance;
    }

    private function construire(string $classe): object
    {
        $ref = new ReflectionClass($classe);
        $ctor = $ref->getConstructor();
        if ($ctor === null) {
            return new $classe();
        }
        $args = [];
        foreach ($ctor->getParameters() as $p) {
            $type = $p->getType();
            if ($type instanceof ReflectionNamedType && !$type->isBuiltin()) {
                $args[] = $this->get($type->getName());
            } elseif ($p->isDefaultValueAvailable()) {
                $args[] = $p->getDefaultValue();
            } else {
                throw new LogicException(sprintf('Impossible de résoudre le paramètre $%s de %s', $p->getName(), $classe));
            }
        }
        return $ref->newInstanceArgs($args);
    }
}

$c = new Conteneur();
$c->lier(UserRepository::class, InMemoryUserRepository::class);
$c->lier(Mailer::class, FakeMailer::class);

$service = $c->get(InscriptionService::class);
$service->inscrire('ana@mail.com');

echo count($c->get(InMemoryUserRepository::class)->saved), PHP_EOL;   // 1 : même instance
echo $c->get(Logger::class)->lignes[0], PHP_EOL;                       // [log] mail à ana@mail.com
""")],
       ["`$c->get(X::class) === $c->get(X::class)` : toujours la même instance",
        "Demander une interface non liée donne un message clair, pas une erreur PHP obscure",
        "Deux classes qui se demandent mutuellement lèvent une exception au lieu de planter par récursion infinie"],
       run=RUN("php", tests=r"""
$c = new Conteneur();
$c->lier(UserRepository::class, InMemoryUserRepository::class);
$c->lier(Mailer::class, FakeMailer::class);
$s = $c->get(InscriptionService::class);
check('get() construit InscriptionService avec ses dépendances', $s instanceof InscriptionService);
$s->inscrire('ana@mail.com');
check('le repository est partagé (même instance)', $c->get(InMemoryUserRepository::class)->saved === ['ana@mail.com']);
check('get() renvoie toujours la même instance', $c->get(Logger::class) === $c->get(Logger::class));
check('la dépendance transitive Logger est construite avec sa valeur par défaut', ($c->get(Logger::class)->lignes[0] ?? '') === '[log] mail à ana@mail.com', json_encode($c->get(Logger::class)->lignes));
check('interface non liée : LogicException', throws(fn() => (new Conteneur())->get(Mailer::class), LogicException::class));
final class BesoinScalaire { public function __construct(public string $dsn) {} }
check('paramètre scalaire sans défaut : LogicException', throws(fn() => (new Conteneur())->get(BesoinScalaire::class), LogicException::class));
final class CircA { public function __construct(public CircB $b) {} }
final class CircB { public function __construct(public CircA $a) {} }
check('dépendance circulaire détectée', throws(fn() => (new Conteneur())->get(CircA::class), LogicException::class));
"""), expected="1\n[log] mail à ana@mail.com"),
  ])

MODULES = [classes, encaps, herit, interf, ns, di]

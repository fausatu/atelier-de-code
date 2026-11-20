from common import P, L, D, N, E, F, TD, RUN


def Q(q, options, answer, why):
    return {"q": q, "options": options, "answer": answer, "why": why}


PRODUIT = r"""
<?php
declare(strict_types=1);

// Ce fichier est fourni : lis-le, tu t'en sers dans exercice.php.
class Produit
{
    public const TVA = 0.2;                 // constante de CLASSE
    private static int $compteur = 0;       // propriété STATIQUE : une seule pour toute la classe

    public function __construct(
        public string $nom,                 // propriétés d'OBJET : une par produit
        public float $prixHT,
    ) {
        self::$compteur++;                  // à chaque new Produit(...), on compte
    }

    public function prixTTC(): float        // méthode d'OBJET : travaille sur CE produit
    {
        return round($this->prixHT * (1 + self::TVA), 2);
    }

    public static function combien(): int   // méthode STATIQUE : ne dépend d'aucun produit
    {
        return self::$compteur;
    }
}
"""

module = {
  "id": "php-symboles", "track": "php", "title": "Lire le PHP : -> :: [] => et static", "minutes": 25,
  "goal": "Savoir lire et choisir les symboles de PHP sans hésiter : `$`, `->`, `::`, `[]`, `=>`, `?->`, `??`, et comprendre la différence entre ce qui est `static` (à la classe) et ce qui ne l'est pas (à chaque objet).",
  "why": "Ces quelques symboles reviennent à chaque ligne de PHP (et de Symfony, Doctrine, Laravel). Tant qu'on hésite entre `->` et `::`, ou qu'on ne sait pas pourquoi une méthode est `static`, on lit le code au hasard. Une fois la règle comprise, tout devient lisible.",
  "flow": [
    "Se demander d'abord : **est-ce que je parle d'un OBJET précis, ou de la CLASSE elle-même ?**",
    "Objet → `->` (`$produit->nom`, `$this->prixTTC()`)",
    "Classe → `::` (`Produit::TVA`, `Produit::combien()`, `self::`, `static::`, `parent::`)",
    "Case d'un tableau → `[]` ; association clé ⇒ valeur → `=>`",
  ],
  "points": [
    "`$` marque une variable : `$prix`, `$this`. Après `->`, pas de `$` : `$this->prix`.",
    "`->` va dans un **objet** (créé avec `new`) : propriété ou méthode de CET objet.",
    "`::` va dans une **classe** : constante, propriété ou méthode `static`, et aussi `self::`, `parent::`, `Classe::class`.",
    "`static` = qui appartient à la classe entière, pas à un objet. Dans une méthode `static`, `$this` n'existe pas.",
    "`[]` lit ou ajoute une case de tableau ; `=>` associe une clé à une valeur (tableaux, `foreach`, `fn`, `match`).",
  ],
  "pitfalls": [
    "`$this->$prix` au lieu de `$this->prix` (un `$` en trop).",
    "Appeler une méthode d'objet avec `::` (`Produit::prixTTC()`) : PHP ne sait pas de quel produit il s'agit.",
    "Utiliser `$this` dans une méthode `static` : « Using $this when not in object context ».",
    "Confondre `=>` (clé ⇒ valeur) et `->` (aller dans un objet).",
  ],
  "quiz": [
    Q("`$panier->total()` : à quoi sert `->` ?", ["accéder à une case de tableau", "appeler une méthode de l'objet $panier", "appeler une méthode static", "comparer deux valeurs"], 1, "`->` va dans un objet : ici on appelle la méthode total() de CE panier."),
    Q("Comment lire la constante `TVA` de la classe `Produit` ?", ["$Produit->TVA", "Produit->TVA", "Produit::TVA", "Produit['TVA']"], 2, "Une constante appartient à la classe : `::`."),
    Q("Pourquoi `public static function depuisJson(string $json): self` est-elle static ?", ["pour aller plus vite", "parce qu'elle sert à CRÉER un objet : il n'en existe pas encore", "parce qu'elle est publique", "parce qu'elle renvoie self"], 1, "Une « fabrique » s'appelle avant d'avoir un objet : `Produit::depuisJson('…')`."),
    Q("Dans `['nom' => 'Clavier']`, que fait `=>` ?", ["il appelle une méthode", "il associe la clé 'nom' à la valeur 'Clavier'", "il compare", "il crée un objet"], 1, "`=>` = clé ⇒ valeur, dans un tableau."),
    Q("`$client?->adresse` veut dire…", ["une erreur de syntaxe", "si $client est null, donne null au lieu de planter", "adresse est optionnelle dans la classe", "on lit une constante"], 1, "C'est l'opérateur nullsafe (PHP 8)."),
  ],
  "prereq": [
    P("Classe / objet", "La classe est le plan (`class Produit {…}`) ; un objet est un exemplaire fabriqué avec `new Produit(…)`. On peut avoir beaucoup d'objets pour une seule classe."),
    P("Propriété / méthode", "Une propriété est une donnée rangée dans l'objet (`$nom`) ; une méthode est une fonction de la classe (`prixTTC()`)."),
    P("Tableau", "Une liste de cases : `[10, 20]` (cases 0, 1…) ou avec des noms : `['nom' => 'Ana']`."),
    P("Constante", "Une valeur qui ne change jamais, écrite en MAJUSCULES : `const TVA = 0.2;`."),
  ],
  "diagram": D(
    nodes=[
      N("cls", 0, 0, "class Produit", "TVA, $compteur, combien()", kind="doc", color="accent"),
      N("o1", 1, 1, "$clavier", "nom, prixHT, prixTTC()", kind="box", color="good"),
      N("o2", 2, 1, "$souris", "nom, prixHT, prixTTC()", kind="box", color="good"),
      N("dc", 1, 0, "Produit::TVA", "Produit::combien()", kind="pill", color="accent"),
      N("dobj", 3, 1, "$clavier->nom", "$clavier->prixTTC()", kind="pill", color="good"),
    ],
    edges=[E("cls", "dc", "::"), E("cls", "o1", "new"), E("cls", "o2", "new"), E("o2", "dobj", "->")],
    caption="Ce qui est à la CLASSE (static, constantes) se lit avec `::` ; ce qui est à chaque OBJET se lit avec `->`."),
  "lessons": [
    L("La seule question à se poser : objet ou classe ?", r"""
Une **classe** est un plan. Un **objet** est un exemplaire fabriqué avec `new`. Chaque objet a **ses propres** valeurs :

```php
$clavier = new Produit('Clavier', 50.0);
$souris  = new Produit('Souris', 20.0);
```

| Je veux… | J'écris | Symbole |
|---|---|---|
| le nom de **ce** produit-là | `$clavier->nom` | `->` (objet) |
| le prix TTC de **ce** produit-là | `$clavier->prixTTC()` | `->` (objet) |
| le taux de TVA (le même pour tous) | `Produit::TVA` | `::` (classe) |
| le nombre de produits créés (un seul compteur) | `Produit::combien()` | `::` (classe) |

Astuce de lecture : **à gauche de `->` il y a toujours une variable** (`$clavier`, `$this`, `$this->panier`) ; **à gauche de `::` il y a un nom de classe** (`Produit`, `self`, `static`, `parent`).
"""),
    L("Le $ et la flèche ->", r"""
- `$` marque une **variable** : `$prix`, `$produits`, `$this`.
- `$this` = « l'objet sur lequel on est en train de travailler », utilisable dans les méthodes **non static**.
- Après `->`, **pas de `$`** : on écrit le nom de la propriété tout court.

```php
$this->prixHT        // ✅ la propriété prixHT de cet objet
$this->$prixHT       // ❌ (autre chose : le nom de la propriété serait dans la variable $prixHT)
$this->prixTTC()     // ✅ appeler une méthode : avec des parenthèses
$this->prixTTC       // ❌ sans () PHP cherche une PROPRIÉTÉ prixTTC
```

On peut enchaîner : `$commande->client->adresse->ville` (la commande a un client, qui a une adresse, qui a une ville).

**`?->` (nullsafe, PHP 8)** : si ce qui est à gauche vaut `null`, le résultat est `null` au lieu d'une erreur.

```php
$ville = $commande->client?->adresse?->ville;   // null si pas de client ou pas d'adresse
```
"""),
    L("Les deux-points :: et le mot static", r"""
`static` veut dire : **ça appartient à la classe, pas à un objet**. Il n'y en a qu'**un** pour toute la classe.

| | Pas static (d'objet) | static (de classe) |
|---|---|---|
| combien en existe-t-il ? | un par objet | un seul pour toute la classe |
| déclaration | `public float $prixHT;` | `private static int $compteur = 0;` |
| depuis l'extérieur | `$clavier->prixTTC()` | `Produit::combien()` |
| depuis la classe | `$this->prixHT` | `self::$compteur` (avec le `$` !) |
| `$this` disponible ? | oui | **non** (il n'y a pas d'objet) |

**Quand rendre une méthode static ?** Quand elle n'a besoin d'**aucun objet** :
- une **fabrique** qui crée l'objet : `Temperature::depuisFahrenheit(212)`, `Email::depuis('a@b.fr')`, `Uuid::v4()` ;
- un **outil** sans mémoire : `Str::slug('Mon Titre')` ;
- un **compteur** ou une info partagée par tous.

Dans le doute : **pas static**. Si ta méthode utilise `$this`, elle ne peut pas être static.

Les autres usages de `::` :

| Écriture | Sens |
|---|---|
| `Produit::TVA`, `self::TVA` | une constante de classe |
| `self::` | « cette classe-ci » (là où le code est écrit) |
| `static::` | « la classe réelle de l'objet » (utile avec l'héritage) |
| `parent::__construct(...)` | appeler la version de la classe parente |
| `Produit::class` | le nom complet de la classe en texte (`'App\Entity\Produit'`) |
| `Statut::Paye` | un cas d'enum |
"""),
    L("Crochets [] et double flèche =>", r"""
**`[]` = les tableaux**

| Écriture | Sens |
|---|---|
| `$notes = [12, 15];` | créer un tableau (cases 0, 1) |
| `$notes[0]` | lire la case 0 → `12` |
| `$notes[] = 18;` | **ajouter** à la fin (pas de numéro entre les crochets) |
| `$user['email']` | lire la case nommée `email` |
| `[$a, $b] = [1, 2];` | « déballer » : `$a` vaut 1, `$b` vaut 2 |

**`=>` = « clé ⇒ valeur »** (jamais pour aller dans un objet) :

| Où | Exemple |
|---|---|
| dans un tableau | `['nom' => 'Clavier', 'prix' => 50]` |
| dans un `foreach` | `foreach ($prix as $nom => $montant)` |
| fonction fléchée | `fn($p) => $p->prixHT` (« reçoit $p, renvoie $p->prixHT ») |
| `match` | `match ($code) { 404 => 'Introuvable', default => 'Erreur' }` |

Ne pas confondre : **`->`** (tiret) = aller dans un objet ; **`=>`** (égal) = associer.
"""),
    L("Le mémo des autres symboles", r"""
| Symbole | Nom | Exemple | Sens |
|---|---|---|---|
| `.` / `.=` | concaténation | `'Bonjour ' . $nom` | coller des textes |
| `??` | coalescence nulle | `$_GET['page'] ?? 1` | la valeur de gauche, ou celle de droite si elle est `null` / absente |
| `??=` | | `$cache[$id] ??= charger($id)` | remplir seulement si vide |
| `?:` | ternaire court | `$nom ?: 'Anonyme'` | la gauche si elle est « vraie », sinon la droite |
| `? :` | ternaire | `$age >= 18 ? 'majeur' : 'mineur'` | un if/else en une ligne |
| `?string` | type nullable | `function f(?string $x)` | une chaîne **ou** `null` |
| `===` / `!==` | égalité stricte | `$a === '5'` | même valeur **et** même type (à préférer à `==`) |
| `<=>` | vaisseau spatial | `usort($t, fn($a, $b) => $a <=> $b)` | -1, 0 ou 1 (pour trier) |
| `...` | décomposition | `[...$a, ...$b]`, `function f(int ...$n)` | étaler un tableau / recevoir plusieurs arguments |
| `&` | référence | `foreach ($t as &$v)` | modifier l'original, pas une copie |
| `#[...]` | attribut | `#[Route('/api')]` | une étiquette lue par Symfony/Doctrine |
| `\` | namespace | `App\Entity\Produit`, `\DateTime` | le « dossier » d'une classe |
| `@var` dans `/** */` | PHPDoc | `/** @var list<Produit> */` | commentaire de type pour l'éditeur |
"""),
  ],
  "recap": [
    "Objet → `->` ; classe → `::`. À gauche de `->` une variable, à gauche de `::` un nom de classe.",
    "Pas de `$` après `->` ; mais `self::$compteur` garde son `$` (propriété static).",
    "`static` = un seul pour toute la classe, pas de `$this` ; idéal pour les fabriques et les outils.",
    "`[]` = case de tableau (et `$t[] = x` pour ajouter) ; `=>` = clé ⇒ valeur (tableau, foreach, fn, match).",
    "`?->` et `??` protègent des `null`.",
  ],
  "example": {"files": [F("exemple.php", "php", r"""
<?php
class Temperature
{
    public const ZERO_ABSOLU = -273.15;          // constante : Temperature::ZERO_ABSOLU
    private static int $nb = 0;                  // static : un seul compteur

    public function __construct(public float $celsius)
    {
        self::$nb++;                             // self:: + $ pour une propriété static
    }

    public static function depuisFahrenheit(float $f): self   // fabrique : pas besoin d'objet
    {
        return new self(($f - 32) * 5 / 9);
    }

    public function enFahrenheit(): float        // d'objet : utilise $this
    {
        return $this->celsius * 9 / 5 + 32;
    }
}

$eau = Temperature::depuisFahrenheit(212);       // :: → la classe
echo $eau->celsius, "\n";                        // -> → cet objet : 100
echo $eau->enFahrenheit(), "\n";                 // 212
$mesures = ['lundi' => 12.5, 'mardi' => 14.0];   // => : clé ⇒ valeur
$mesures['mercredi'] = 9.0;                      // [] : écrire une case
foreach ($mesures as $jour => $c) echo "$jour : $c\n";
""")], "notes": ["`::` pour la classe (fabrique, constante), `->` pour l'objet.", "`=>` dans le tableau et le foreach, `[]` pour écrire une case."]},
  "tds": [
    TD(1, "Choisir le bon symbole",
       "`Produit.php` est fourni (lis-le !). Dans `exercice.php`, complète chaque fonction avec **une seule ligne** : à toi de choisir entre `->`, `::` et `[]`.",
       ["`nomDe(Produit $p)` renvoie le nom du produit", "`ttcDe(Produit $p)` renvoie son prix TTC (avec la méthode de la classe)",
        "`tauxTva()` renvoie la constante TVA ; `nbProduitsCrees()` renvoie le compteur (avec la méthode static)",
        "`premier(array $produits)` renvoie le premier produit de la liste ; `ajouter(array $produits, Produit $p)` renvoie la liste avec `$p` ajouté à la fin"],
       [F("exercice.php", "php", r"""
<?php
declare(strict_types=1);

function nomDe(Produit $p): string
{
    // à toi
}

function ttcDe(Produit $p): float
{
    // à toi
}

function tauxTva(): float
{
    // à toi
}

function nbProduitsCrees(): int
{
    // à toi
}

/** @param list<Produit> $produits */
function premier(array $produits): Produit
{
    // à toi
}

/** @param list<Produit> $produits */
function ajouter(array $produits, Produit $p): array
{
    // à toi (ajoute $p à la fin, puis renvoie le tableau)
}

$clavier = new Produit('Clavier', 50.0);
echo nomDe($clavier), ' : ', ttcDe($clavier), " € TTC\n";
"""), F("Produit.php", "php", PRODUIT)],
       ["Un produit précis (`$p`) → `->` ; la classe `Produit` → `::`.", "Une méthode s'appelle avec des parenthèses : `$p->prixTTC()`, `Produit::combien()`.", "La première case d'une liste est la case `0`. Pour ajouter : `$produits[] = $p;` puis `return $produits;`."],
       [F("exercice.php", "php", r"""
<?php
declare(strict_types=1);

function nomDe(Produit $p): string
{
    return $p->nom;                 // propriété de CET objet
}

function ttcDe(Produit $p): float
{
    return $p->prixTTC();           // méthode de CET objet
}

function tauxTva(): float
{
    return Produit::TVA;            // constante de la classe
}

function nbProduitsCrees(): int
{
    return Produit::combien();      // méthode static
}

/** @param list<Produit> $produits */
function premier(array $produits): Produit
{
    return $produits[0];            // case 0 du tableau
}

/** @param list<Produit> $produits */
function ajouter(array $produits, Produit $p): array
{
    $produits[] = $p;               // [] vide = ajouter à la fin
    return $produits;
}

$clavier = new Produit('Clavier', 50.0);
echo nomDe($clavier), ' : ', ttcDe($clavier), " € TTC\n";
"""), F("Produit.php", "php", PRODUIT)],
       ["`->` pour l'objet, `::` pour la classe", "`$t[0]` pour lire, `$t[] = x` pour ajouter"],
       run=RUN("php", tests=r"""
$a = new Produit('Souris', 20.0); $b = new Produit('Écran', 150.0);
check('nomDe() renvoie le nom', nomDe($a) === 'Souris');
check('ttcDe() renvoie le prix TTC (24)', abs(ttcDe($a) - 24.0) < 0.001);
check('tauxTva() renvoie la constante TVA (0.2)', tauxTva() === 0.2);
$n = nbProduitsCrees(); new Produit('Câble', 5.0);
check('nbProduitsCrees() suit le compteur static', nbProduitsCrees() === $n + 1 && $n >= 3, 'compteur : ' . $n);
check('premier() renvoie la case 0', premier([$b, $a]) === $b);
$l = ajouter([$a], $b);
check('ajouter() met le produit à la fin', count($l) === 2 && $l[1] === $b);
""")),
    TD(2, "Static ou pas static ?",
       "Écris la classe `Temperature`. Pour chaque élément, demande-toi : **appartient-il à la classe entière, ou à chaque température ?**",
       ["Une constante `ZERO_ABSOLU` qui vaut `-273.15`, et une propriété publique `celsius` (float) remplie par le constructeur",
        "Le constructeur lance une `DomainException` si la valeur est sous le zéro absolu ; sinon il augmente un compteur **static** `nbCreees` (public, commence à 0)",
        "`depuisFahrenheit(float $f)` : une **fabrique static** qui renvoie une nouvelle Temperature (°C = (°F − 32) × 5 / 9)",
        "`enFahrenheit()` : une méthode **d'objet** qui renvoie la température en °F (°F = °C × 9 / 5 + 32)"],
       [F("Temperature.php", "php", r"""
<?php
declare(strict_types=1);

class Temperature
{
    // à toi : la constante, le compteur static, la propriété celsius

    public function __construct(float $celsius)
    {
        // à toi
    }

    // à toi : depuisFahrenheit (static) et enFahrenheit (pas static)
}

$eau = Temperature::depuisFahrenheit(212);
echo $eau->celsius, " °C\n";
""")],
       ["`public const ZERO_ABSOLU = -273.15;` et `public static int $nbCreees = 0;`. Dans la classe : `self::ZERO_ABSOLU`, `self::$nbCreees++`.",
        "La fabrique : `public static function depuisFahrenheit(float $f): self { return new self(($f - 32) * 5 / 9); }`",
        "`enFahrenheit()` utilise `$this->celsius` : elle ne peut donc PAS être static."],
       [F("Temperature.php", "php", r"""
<?php
declare(strict_types=1);

class Temperature
{
    public const ZERO_ABSOLU = -273.15;     // à la classe : la même pour toutes
    public static int $nbCreees = 0;        // à la classe : un seul compteur
    public float $celsius;                  // à chaque objet

    public function __construct(float $celsius)
    {
        if ($celsius < self::ZERO_ABSOLU) {
            throw new DomainException('Impossible : sous le zéro absolu');
        }
        $this->celsius = $celsius;
        self::$nbCreees++;
    }

    public static function depuisFahrenheit(float $f): self
    {
        return new self(($f - 32) * 5 / 9);   // pas d'objet avant : static
    }

    public function enFahrenheit(): float
    {
        return $this->celsius * 9 / 5 + 32;   // utilise $this : pas static
    }
}

$eau = Temperature::depuisFahrenheit(212);
echo $eau->celsius, " °C\n";
""")],
       ["Fabrique et compteur : static ; ce qui utilise `$this` : pas static", "`self::` dans la classe, `Temperature::` dehors"],
       run=RUN("php", tests=r"""
check('Temperature::ZERO_ABSOLU vaut -273.15', defined('Temperature::ZERO_ABSOLU') && Temperature::ZERO_ABSOLU === -273.15);
$t = new Temperature(0.0);
check('(new Temperature(0))->enFahrenheit() vaut 32', abs($t->enFahrenheit() - 32.0) < 0.001);
check('Temperature::depuisFahrenheit(212)->celsius vaut 100', abs(Temperature::depuisFahrenheit(212)->celsius - 100.0) < 0.001);
check('sous le zéro absolu → DomainException', throws(fn() => new Temperature(-300.0), DomainException::class));
$avant = Temperature::$nbCreees; new Temperature(20.0); Temperature::depuisFahrenheit(50);
check('le compteur static nbCreees augmente à chaque création', Temperature::$nbCreees === $avant + 2, 'avant ' . $avant . ', après ' . Temperature::$nbCreees);
check('depuisFahrenheit est static', (new ReflectionMethod(Temperature::class, 'depuisFahrenheit'))->isStatic());
check('enFahrenheit n\'est PAS static', !(new ReflectionMethod(Temperature::class, 'enFahrenheit'))->isStatic());
check('nbCreees est une propriété static', (new ReflectionProperty(Temperature::class, 'nbCreees'))->isStatic());
""")),
    TD(3, "Tableaux, => et null",
       "Des commandes arrivent sous forme de tableaux associatifs. Écris trois fonctions qui utilisent `[]`, `=>`, `fn`, `??` et `?->`.",
       ["`totalParClient(array $commandes)` : chaque commande ressemble à `['client' => 'Ana', 'total' => 30]` ; renvoie `['Ana' => 50, 'Bob' => 20]` (somme par client, avec `foreach` et `[]`)",
        "`totaux(array $commandes)` : renvoie seulement la liste des totaux `[30, 20, 20]`, avec `array_map` et une fonction fléchée `fn(...) => ...`",
        "`ville(?Client $c)` : renvoie la ville de l'adresse du client, ou `'inconnue'` s'il n'y a pas de client ou pas d'adresse, en **une ligne** avec `?->` et `??`",
        "Les classes `Client` et `Adresse` sont fournies en bas du fichier"],
       [F("commandes.php", "php", r"""
<?php
declare(strict_types=1);

function totalParClient(array $commandes): array
{
    $totaux = [];
    // à toi : foreach, puis ajoute au total du client
    return $totaux;
}

function totaux(array $commandes): array
{
    // à toi : array_map(fn(...) => ..., $commandes)
}

function ville(?Client $c): string
{
    // à toi : une seule ligne
}

// fourni
class Adresse { public function __construct(public string $ville) {} }
class Client { public function __construct(public string $nom, public ?Adresse $adresse = null) {} }

$commandes = [
    ['client' => 'Ana', 'total' => 30],
    ['client' => 'Bob', 'total' => 20],
    ['client' => 'Ana', 'total' => 20],
];
print_r(totalParClient($commandes));
""")],
       ["Dans le foreach : `$totaux[$c['client']] = ($totaux[$c['client']] ?? 0) + $c['total'];` (le `?? 0` gère la première commande d'un client).",
        "`return array_map(fn($c) => $c['total'], $commandes);`",
        "`return $c?->adresse?->ville ?? 'inconnue';`"],
       [F("commandes.php", "php", r"""
<?php
declare(strict_types=1);

function totalParClient(array $commandes): array
{
    $totaux = [];
    foreach ($commandes as $c) {
        $nom = $c['client'];                          // [] : lire une case
        $totaux[$nom] = ($totaux[$nom] ?? 0) + $c['total'];
    }
    return $totaux;                                   // ['Ana' => 50, 'Bob' => 20]
}

function totaux(array $commandes): array
{
    return array_map(fn($c) => $c['total'], $commandes);   // fn : reçoit $c => renvoie le total
}

function ville(?Client $c): string
{
    return $c?->adresse?->ville ?? 'inconnue';
}

// fourni
class Adresse { public function __construct(public string $ville) {} }
class Client { public function __construct(public string $nom, public ?Adresse $adresse = null) {} }

$commandes = [
    ['client' => 'Ana', 'total' => 30],
    ['client' => 'Bob', 'total' => 20],
    ['client' => 'Ana', 'total' => 20],
];
print_r(totalParClient($commandes));
""")],
       ["`??` donne une valeur par défaut", "`?->` s'arrête sans erreur sur un null"],
       run=RUN("php", tests=r"""
$cmd = [['client' => 'Ana', 'total' => 30], ['client' => 'Bob', 'total' => 20], ['client' => 'Ana', 'total' => 20], ['client' => 'Chloé', 'total' => 5]];
check('totalParClient() additionne par client', totalParClient($cmd) === ['Ana' => 50, 'Bob' => 20, 'Chloé' => 5], json_encode(totalParClient($cmd)));
check('totalParClient([]) renvoie []', totalParClient([]) === []);
check('totaux() renvoie la liste des totaux', totaux($cmd) === [30, 20, 20, 5], json_encode(totaux($cmd)));
check('ville() avec une adresse → la ville', ville(new Client('Ana', new Adresse('Lyon'))) === 'Lyon');
check('ville() sans adresse → inconnue', ville(new Client('Bob')) === 'inconnue');
check('ville(null) → inconnue', ville(null) === 'inconnue');
$src = (new ReflectionFunction('ville'));
check('ville() tient en une ligne (pas de if)', $src->getEndLine() - $src->getStartLine() <= 3);
""")),
  ],
}

MODULES = [module]

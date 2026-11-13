from common import P, L, D, N, E, LANE, F, TD, RUN
from doctrine_sim import DOCTRINE_SETUP
from symfony_sim import SYMFONY_SETUP

T = "debug"

METHODE = ("**La méthode, à chaque bug :** lis le message (type, texte, fichier:ligne), reproduis-le en lançant le code, "
           "formule une hypothèse précise, vérifie-la (un `var_dump`, un `console.log`, un test), corrige, puis relance pour confirmer.")


def DM(id, title, minutes, goal, why, flow, points, pitfalls, quiz, prereq, diagram, lessons, recap, example, notes, tds):
    return {
        "id": id, "track": T, "title": title, "minutes": minutes, "goal": goal, "why": why,
        "flow": flow, "points": points, "pitfalls": pitfalls, "quiz": quiz,
        "prereq": prereq, "diagram": diagram, "lessons": lessons, "recap": recap,
        "example": {"files": example if isinstance(example, list) else [example], "notes": notes},
        "tds": tds,
    }


def Q(q, options, answer, why):
    return {"q": q, "options": options, "answer": answer, "why": why}


def PRUN(tests, setup=None):
    return RUN("php", tests=tests, setup=setup)


def DRUN(tests):
    return RUN("php", tests=tests, setup=DOCTRINE_SETUP)


def SRUN(tests):
    return RUN("php", tests="Atelier\\App::$echo = false;\nAtelier\\App::reset();\n" + tests, setup=SYMFONY_SETUP)


NO_WARN = r"""
function sansAvertissement(callable $f, ?string &$avert = null): mixed {
    $avert = null;
    set_error_handler(function (int $n, string $s) use (&$avert) { $avert = $avert ?? $s; return true; });
    try { return $f(); } finally { restore_error_handler(); }
}
"""

USES = r"""<?php
declare(strict_types=1);

use Atelier\App;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpKernel\Attribute\MapRequestPayload;
use Symfony\Component\Routing\Attribute\Route;
use Symfony\Component\Validator\Constraints as Assert;
"""

# =========================================================================== PHP
php = DM("dbg-php", "Lire une erreur PHP", 20,
  "Savoir lire un message d'erreur PHP et suivre une méthode pour trouver la cause, même quand rien ne s'affiche.",
  "La moitié du temps de développement passe à comprendre pourquoi ça ne marche pas. Lire correctement une erreur fait souvent gagner une heure.",
  ["Lire le **type** et le **message** : ils disent quoi", "Lire **fichier:ligne** et la **pile d'appels** : ils disent où",
   "**Reproduire**, puis formuler une hypothèse précise", "**Vérifier** l'hypothèse (`var_dump`, test) avant de corriger"],
  ["Le type compte : `Fatal error` arrête tout, `Warning` continue avec une valeur fausse.",
   "La pile d'appels se lit de haut en bas : la 1re ligne de **ton** code est presque toujours l'endroit à regarder.",
   "« on null » veut dire qu'une variable vaut `null` alors que tu attendais un objet : remonte d'où elle vient.",
   "Un bug sans message (mauvais résultat) se traque en affichant les valeurs intermédiaires.",
   "Corriger le symptôme (ajouter un `if`) n'est pas corriger la cause : demande-toi pourquoi la valeur est fausse."],
  ["Lire seulement la dernière ligne de l'erreur.", "Modifier le code au hasard sans hypothèse.", "Ignorer les `Warning` parce que « ça marche quand même »."],
  [Q("« Call to a member function nom() on null » signifie…", ["la méthode nom() n'existe pas", "la variable sur laquelle on appelle nom() vaut null", "nom() a renvoyé null", "la classe est introuvable"], 1, "« on null » décrit l'objet à gauche de la flèche : il vaut null."),
   Q("Dans une pile d'appels, quelle ligne regarder en premier ?", ["la dernière", "la première ligne qui pointe vers ton code", "celle du framework", "aucune"], 1, "Les lignes du framework montrent le chemin ; ton bug est dans ton code."),
   Q("Un `Warning: Undefined array key 3`…", ["arrête le script", "continue avec null à la place de la valeur", "est sans importance", "vient toujours de PHP lui-même"], 1, "Le script continue avec une valeur fausse : le vrai bug apparaît souvent plus loin.")],
  prereq=[
    P("Message d'erreur", "Ce que PHP affiche quand quelque chose se passe mal : un **type** (Fatal error, Warning…), un **texte**, et un **emplacement** (fichier et ligne)."),
    P("Pile d'appels (stack trace)", "La liste des fonctions en cours au moment de l'erreur, de la plus récente (en haut) à la plus ancienne. Elle montre le chemin qui a mené au bug."),
    P("`null`", "La valeur « rien ». Beaucoup de fonctions renvoient `null` quand elles ne trouvent pas ce qu'on cherche."),
    P("Hypothèse", "Une explication précise et vérifiable : « `$client` vaut null parce que l'id 99 n'existe pas », pas « ça bug »."),
  ],
  diagram=D(
    nodes=[
      N("t", 0, 0, "Type", "Fatal error · Warning", kind="pill", color="bad"),
      N("m", 1, 0, "Message", "Call to a member\nfunction nom() on null", kind="doc"),
      N("l", 2, 0, "Où", "Client.php:12", kind="pill", color="warn"),
      N("s", 3, 0, "Pile d'appels", "#0 afficherNom()\n#1 index.php", kind="doc", color="muted"),
      N("h", 1, 1, "Hypothèse", "« $client vaut null\nquand l'id n'existe pas »", kind="note", color="accent"),
      N("v", 2, 1, "Vérifier", "var_dump($client)", kind="pill", color="good"),
      N("c", 3, 1, "Corriger la cause", "puis relancer", kind="pill", color="good"),
    ],
    edges=[E("t", "m"), E("m", "l"), E("l", "s"), E("h", "v"), E("v", "c")],
    caption="En haut : ce que le message te dit, dans l'ordre de lecture. En bas : la méthode pour passer du message à la correction."),
  lessons=[
    L("Anatomie d'une erreur PHP", r"""
```
PHP Fatal error:  Uncaught Error: Call to a member function nom() on null in /app/src/Clients.php:12
Stack trace:
#0 /app/src/Clients.php(18): afficherNom(99)
#1 /app/public/index.php(7): Facture->entete()
#2 {main}
  thrown in /app/src/Clients.php on line 12
```

Lis-la dans cet ordre :

1. **Le type** : `Fatal error` (le script s'arrête), `Uncaught TypeError`, `Warning` (le script continue, avec une valeur fausse), `Deprecated` (ça marchera moins longtemps).
2. **Le message** : ici, on appelle `nom()` sur quelque chose qui vaut `null`.
3. **Où** : `Clients.php` ligne 12.
4. **Le chemin** (stack trace) : `afficherNom(99)` a été appelée depuis `Clients.php` ligne 18, elle-même appelée depuis `index.php`. Les arguments sont visibles : `99`. C'est un indice énorme : l'id 99 existe-t-il ?

Dans Symfony, la page d'erreur en développement montre la même chose, en plus lisible, avec le code autour de chaque ligne.
"""),
    L("La méthode : ne jamais corriger au hasard", r"""
1. **Lire** le message en entier (voir ci-dessus).
2. **Reproduire** : trouver comment déclencher l'erreur à coup sûr. Un bug qu'on ne sait pas reproduire, on ne sait pas s'il est corrigé.
3. **Formuler une hypothèse précise** : « `$client` vaut `null` parce que `trouverClient(99)` ne trouve personne ».
4. **Vérifier** l'hypothèse avant de toucher au code : `var_dump($client);`, `dump($client)` dans Symfony, `dd()` pour arrêter là, un point d'arrêt avec Xdebug, ou un test.
5. **Corriger la cause**, pas le symptôme, puis **relancer** pour confirmer.

Corriger le symptôme, c'est ajouter `if ($client !== null)` partout. Corriger la cause, c'est décider ce qui doit se passer quand le client n'existe pas (afficher « Client inconnu », renvoyer une 404…) et le faire **à un seul endroit**.
"""),
    L("Les erreurs PHP les plus fréquentes", r"""
| Message | Ce que ça veut dire | Piste |
|---|---|---|
| `Call to a member function x() on null` | l'objet vaut `null` | d'où vient la variable ? une recherche qui n'a rien trouvé ? |
| `Undefined variable $x` | la variable n'a jamais été définie | faute de frappe, ou définie dans un autre bloc |
| `Undefined array key "nom"` | la clé n'existe pas dans le tableau | `var_dump` du tableau ; clé mal orthographiée ? boucle qui va un cran trop loin ? |
| `TypeError: Argument #1 must be of type int, string given` | mauvais type passé à une fonction typée | d'où vient la valeur ? un champ de formulaire est toujours une chaîne |
| `Cannot modify readonly property` | on écrit une propriété `readonly` après le constructeur | créer un nouvel objet au lieu de modifier |
| `Class "X" not found` | classe inconnue | `use` manquant, namespace ou nom de fichier faux (autoload) |
| `Allowed memory size exhausted` | mémoire épuisée | boucle infinie ou récursion sans fin |
| `Division by zero` | division par 0 | cas « liste vide » non prévu |

Et le pire : **pas d'erreur du tout**, mais un mauvais résultat. Là, on affiche les valeurs intermédiaires (`var_dump` dans la boucle) jusqu'à trouver l'endroit où elles deviennent fausses.
"""),
  ],
  recap=["Lire dans l'ordre : type, message, fichier:ligne, pile d'appels.",
         "La 1re ligne de **ton** code dans la pile est l'endroit à regarder.",
         "Méthode : lire → reproduire → hypothèse précise → vérifier → corriger la cause → relancer.",
         "Un `Warning` n'est jamais anodin : la valeur fausse ressort plus loin.",
         "Sans message d'erreur : afficher les valeurs intermédiaires."],
  example=F("terminal", "bash", r"""
$ php public/index.php
PHP Fatal error:  Uncaught Error: Call to a member function nom() on null in /app/src/Clients.php:12
Stack trace:
#0 /app/src/Clients.php(18): afficherNom(99)      <- ton code, avec l'argument : 99
#1 /app/public/index.php(7): Facture->entete()
#2 {main}

# Hypothèse : trouverClient(99) renvoie null (l'id 99 n'existe pas).
# Vérification, juste avant la ligne 12 :
var_dump($client);    // NULL   -> hypothèse confirmée
"""),
  notes=["Le message dit **quoi** (« on null »), l'emplacement dit **où**, la pile dit **comment on y est arrivé**.",
         "L'argument `99` dans la pile donne la piste.",
         "On vérifie avec `var_dump` **avant** de corriger."],
  tds=[
    TD(1, "Call to a member function on null",
       "La page facture plante pour certains clients avec : `Fatal error: Uncaught Error: Call to a member function nom() on null`. Lance le code, lis l'erreur, trouve la cause et corrige-la **à un seul endroit**. " + METHODE,
       ["Lance le code et lis le message (quelle ligne, quel argument ?)",
        "`afficherNom(int $id)` doit renvoyer le nom du client, ou `'Client inconnu'` s'il n'existe pas",
        "`trouverClient()` ne doit pas changer : renvoyer `null` quand on ne trouve pas est son rôle",
        "Pas d'erreur ni d'avertissement à l'exécution"],
       [F("Clients.php", "php", r"""
<?php
declare(strict_types=1);

final class Client
{
    public function __construct(private int $id, private string $nom) {}
    public function id(): int { return $this->id; }
    public function nom(): string { return $this->nom; }
}

function trouverClient(int $id): ?Client
{
    $clients = [1 => new Client(1, 'Ana'), 2 => new Client(2, 'Léo')];
    return $clients[$id] ?? null;
}

function afficherNom(int $id): string
{
    $client = trouverClient($id);
    return $client->nom();
}

echo afficherNom(1), PHP_EOL;
echo afficherNom(99), PHP_EOL;
""")],
       ["La ligne de l'erreur est dans `afficherNom()` ; l'argument est `99`.",
        "`var_dump(trouverClient(99));` affiche `NULL`.",
        "`if ($client === null) { return 'Client inconnu'; }` avant d'appeler `nom()`."],
       [F("Clients.php", "php", r"""
<?php
declare(strict_types=1);

final class Client
{
    public function __construct(private int $id, private string $nom) {}
    public function id(): int { return $this->id; }
    public function nom(): string { return $this->nom; }
}

function trouverClient(int $id): ?Client
{
    $clients = [1 => new Client(1, 'Ana'), 2 => new Client(2, 'Léo')];
    return $clients[$id] ?? null;
}

function afficherNom(int $id): string
{
    $client = trouverClient($id);
    if ($client === null) {
        return 'Client inconnu';
    }
    return $client->nom();
}

echo afficherNom(1), PHP_EOL;
echo afficherNom(99), PHP_EOL;
""")],
       ["L'id 99 affiche « Client inconnu »", "`trouverClient()` est inchangée"],
       run=PRUN(r"""
check('afficherNom(1) = Ana', afficherNom(1) === 'Ana');
check('afficherNom(2) = Léo', afficherNom(2) === 'Léo');
check('afficherNom(99) = Client inconnu (plus de Fatal error)', afficherNom(99) === 'Client inconnu');
check('trouverClient(99) renvoie toujours null', trouverClient(99) === null);
""")),
    TD(2, "Un Warning qui fausse le total",
       "Le total du panier est faux, et les logs affichent `Warning: Undefined array key 3` et `Warning: Undefined array key \"quantite\"`. Le script ne plante pas : c'est justement le piège. Trouve **les deux** causes. " + METHODE,
       ["Lance le code : lis les deux avertissements (quelle ligne, quelle clé ?)",
        "`total()` doit renvoyer `9000 + 2 × 1500 + 3 × 500 = 13500` pour le panier d'exemple",
        "Plus aucun avertissement",
        "`total([])` renvoie 0"],
       [F("Panier.php", "php", r"""
<?php
declare(strict_types=1);

/** @param list<array{nom: string, prix: int, qte: int}> $lignes  prix en centimes */
function total(array $lignes): int
{
    $total = 0;
    for ($i = 0; $i <= count($lignes); $i++) {
        $l = $lignes[$i];
        $total += $l['prix'] * $l['quantite'];
    }
    return $total;
}

$panier = [
    ['nom' => 'Clavier', 'prix' => 9000, 'qte' => 1],
    ['nom' => 'Souris', 'prix' => 1500, 'qte' => 2],
    ['nom' => 'Tapis', 'prix' => 500, 'qte' => 3],
];
echo total($panier), PHP_EOL;
""")],
       ["« Undefined array key 3 » : le tableau a 3 éléments (indices 0, 1, 2). Que vaut `$i` au dernier tour ?",
        "« Undefined array key \"quantite\" » : `var_dump($l);` montre les vraies clés.",
        "Un `foreach ($lignes as $l)` évite toute erreur d'indice."],
       [F("Panier.php", "php", r"""
<?php
declare(strict_types=1);

/** @param list<array{nom: string, prix: int, qte: int}> $lignes  prix en centimes */
function total(array $lignes): int
{
    $total = 0;
    foreach ($lignes as $l) {
        $total += $l['prix'] * $l['qte'];
    }
    return $total;
}

$panier = [
    ['nom' => 'Clavier', 'prix' => 9000, 'qte' => 1],
    ['nom' => 'Souris', 'prix' => 1500, 'qte' => 2],
    ['nom' => 'Tapis', 'prix' => 500, 'qte' => 3],
];
echo total($panier), PHP_EOL;
""")],
       ["Le total vaut 13500", "Aucun Warning"],
       run=PRUN(NO_WARN + r"""
$panier = [['nom' => 'Clavier', 'prix' => 9000, 'qte' => 1], ['nom' => 'Souris', 'prix' => 1500, 'qte' => 2], ['nom' => 'Tapis', 'prix' => 500, 'qte' => 3]];
$r = sansAvertissement(fn() => total($panier), $w);
check('total = 13500', $r === 13500, (string) $r);
check('aucun avertissement', $w === null, (string) $w);
check('total([]) = 0', sansAvertissement(fn() => total([]), $w2) === 0 && $w2 === null);
""")),
    TD(3, "Un bug sans aucun message",
       "Le récapitulatif de commande affiche le **dernier produit deux fois** (et l'avant-dernier disparaît). Aucune erreur, aucun avertissement. Il faut afficher les valeurs intermédiaires pour comprendre. " + METHODE,
       ["Lance : compare la sortie au tableau `$produits`",
        "Ajoute des `var_dump` / `echo` dans les boucles pour voir à quel moment le tableau change",
        "Corrige : `recap()` doit renvoyer les noms en majuscules, dans l'ordre, sans doublon",
        "Explique (en commentaire) la cause en une phrase"],
       [F("Recap.php", "php", r"""
<?php
declare(strict_types=1);

function recap(array $produits): array
{
    // 1. mettre les noms en majuscules
    foreach ($produits as &$p) {
        $p['nom'] = strtoupper($p['nom']);
    }

    // 2. ne garder que les noms
    $noms = [];
    foreach ($produits as $p) {
        $noms[] = $p['nom'];
    }
    return $noms;
}

$produits = [['nom' => 'clavier'], ['nom' => 'souris'], ['nom' => 'ecran']];
print_r(recap($produits));
""")],
       ["Affiche `$produits` après la 1re boucle, puis à chaque tour de la 2e : quel élément change ?",
        "Après `foreach (… as &$p)`, `$p` reste une **référence** vers le dernier élément. La 2e boucle réutilise le nom `$p`…",
        "`unset($p);` juste après la 1re boucle casse la référence (ou évite `&` : `array_map`)."],
       [F("Recap.php", "php", r"""
<?php
declare(strict_types=1);

function recap(array $produits): array
{
    // Cause : après « foreach (… as &$p) », $p restait une référence vers le dernier élément ;
    // la 2e boucle écrivait donc chaque produit dans ce dernier élément.
    return array_map(fn(array $p) => strtoupper($p['nom']), $produits);
}

$produits = [['nom' => 'clavier'], ['nom' => 'souris'], ['nom' => 'ecran']];
print_r(recap($produits));
""")],
       ["La sortie contient CLAVIER, SOURIS, ECRAN", "Un commentaire explique la cause"],
       run=PRUN(r"""
$r = recap([['nom' => 'clavier'], ['nom' => 'souris'], ['nom' => 'ecran']]);
check('recap() = CLAVIER, SOURIS, ECRAN', $r === ['CLAVIER', 'SOURIS', 'ECRAN'], json_encode($r));
$r2 = recap([['nom' => 'a'], ['nom' => 'b']]);
check('fonctionne avec 2 produits', $r2 === ['A', 'B'], json_encode($r2));
check('liste vide', recap([]) === []);
""")),
  ])

# =========================================================================== Doctrine
DOC_SIM = " Le bouton Exécuter utilise le **Doctrine simulé** de l'atelier : il affiche le SQL envoyé (`SQL> …`) et lève les mêmes erreurs que Doctrine."

doctrine = DM("dbg-doctrine", "Erreurs Doctrine", 20,
  "Reconnaître les erreurs Doctrine les plus courantes et savoir où chercher leur cause.",
  "Les erreurs Doctrine sont longues et en anglais, mais il en existe une dizaine qui reviennent tout le temps : les connaître, c'est les corriger en deux minutes.",
  ["Lire le **nom de l'entité** et de la **propriété** citées dans le message", "Vérifier le **mapping** (attributs `#[ORM\\…]`) de cette propriété",
   "Vérifier ce qui est **persisté** et **flushé**, et à quel moment", "Regarder le **SQL** réellement envoyé (profiler, logs)"],
  ["« A new entity was found through the relationship » : un objet relié n'a pas été persisté.",
   "« Column cannot be null » sur une clé étrangère : le côté propriétaire de la relation n'a pas été renseigné.",
   "Rien ne s'enregistre et aucune erreur : `flush()` oublié, ou modification d'un objet que Doctrine ne suit pas.",
   "Le profiler Symfony (onglet Doctrine) montre toutes les requêtes d'une page.",
   "`php bin/console doctrine:schema:validate` vérifie que le mapping et la base sont d'accord."],
  ["Ajouter `cascade: ['persist']` partout « pour que ça marche ».", "Appeler `persist()` sur un objet qui vient de `find()` en croyant que ça enregistre.", "Mettre `flush()` dans une boucle."],
  [Q("« A new entity was found through the relationship Livre#auteur »…", ["l'auteur n'a pas été persisté", "la table auteur n'existe pas", "le livre est en double", "il manque un getter"], 0, "Le livre est persisté, mais l'auteur relié est nouveau et personne ne l'a confié à Doctrine."),
   Q("Une modification d'entité n'arrive pas en base, sans erreur. Première piste ?", ["le cache", "un flush() manquant", "la migration", "le serializer"], 1, "Sans flush(), Doctrine n'envoie rien."),
   Q("Dans une relation OneToMany / ManyToOne, quel côté écrit la clé étrangère ?", ["le côté OneToMany (la collection)", "le côté ManyToOne (propriétaire)", "les deux", "aucun"], 1, "Seul le côté propriétaire (ManyToOne) est lu par Doctrine pour écrire auteur_id.")],
  prereq=[
    P("persist / flush", "`persist()` dit à Doctrine « suis ce nouvel objet » ; `flush()` envoie réellement le SQL (INSERT, UPDATE, DELETE)."),
    P("Entité suivie (managed)", "Un objet que Doctrine connaît : chargé par `find()` ou passé à `persist()`. Ses modifications sont détectées au `flush()`."),
    P("Côté propriétaire", "Dans une relation, le côté qui porte la clé étrangère (souvent le ManyToOne). C'est lui que Doctrine lit pour écrire la colonne `auteur_id`."),
    P("Cascade", "Option d'une relation : `cascade: ['persist']` persiste automatiquement les objets reliés."),
  ],
  diagram=D(
    nodes=[
      N("e1", 0, 0, "A new entity was found", "message", kind="doc", color="bad"),
      N("c1", 1, 0, "Objet relié non persisté", "cause", kind="note"),
      N("f1", 2, 0, "persist() ou cascade", "remède", kind="pill", color="good"),
      N("e2", 0, 1, "auteur_id cannot be null", "message", kind="doc", color="bad"),
      N("c2", 1, 1, "Côté propriétaire vide", "cause", kind="note"),
      N("f2", 2, 1, "$livre->setAuteur($a)", "remède", kind="pill", color="good"),
      N("e3", 0, 2, "Rien en base", "aucun message", kind="doc", color="warn"),
      N("c3", 1, 2, "flush oublié / copie", "cause", kind="note"),
      N("f3", 2, 2, "Modifier l'objet chargé", "puis flush()", kind="pill", color="good"),
    ],
    edges=[E("e1", "c1"), E("c1", "f1"), E("e2", "c2"), E("c2", "f2"), E("e3", "c3"), E("c3", "f3")],
    caption="Les trois pannes Doctrine les plus fréquentes et leur remède."),
  lessons=[
    L("Lire une erreur Doctrine", r"""
Les messages Doctrine sont longs, mais ils citent presque toujours **une entité et une propriété** :

```
A new entity was found through the relationship 'App\Entity\Livre#auteur' that was not configured
to cascade persist operations for entity: App\Entity\Auteur@123. To solve this issue: Either
explicitly call EntityManager#persist() on this unknown entity or configure cascade persist …
```

- `Livre#auteur` : la propriété `$auteur` de la classe `Livre`. C'est là qu'il faut regarder.
- La fin du message propose souvent **la** solution (ici : `persist()` ou cascade).

Autre réflexe : regarder le **SQL**. En développement, l'onglet Doctrine du profiler Symfony montre chaque requête de la page. Une requête manquante (pas d'UPDATE) ou en trop (50 SELECT) explique beaucoup de bugs.
"""),
    L("Les pannes classiques", r"""
| Symptôme | Cause habituelle | Correction |
|---|---|---|
| `A new entity was found through the relationship` | un objet relié est nouveau et n'a pas été persisté | `persist()` cet objet, ou `cascade: ['persist']` si l'un n'existe jamais sans l'autre |
| `Column 'auteur_id' cannot be null` | on a rempli la collection (`$auteur->livres`) mais pas le côté propriétaire (`$livre->auteur`) | une méthode `ajouterLivre()` qui met à jour **les deux** côtés |
| Rien ne s'enregistre, aucune erreur | `flush()` oublié, ou on modifie une **copie** / un objet non suivi | modifier l'objet obtenu par `find()`, puis `flush()` |
| `Entity of type X was not found` / 404 | l'id n'existe pas, ou mauvais paramètre de route | vérifier l'id reçu (`dump()`) |
| `The class X was not found in the chain configured namespaces` | entité hors du dossier mappé, namespace faux | namespace `App\Entity`, attribut `#[ORM\Entity]` |
| `SQLSTATE[42S22]: Column not found` | la base n'est pas à jour avec les entités | `make:migration` puis `doctrine:migrations:migrate` |
"""),
    L("Les pièges silencieux", r"""
Les bugs Doctrine les plus coûteux ne font **aucune erreur** :

- **`flush()` oublié** : tout semble marcher, mais rien n'est en base. Une méthode de service qui modifie des entités doit finir par un `flush()` (ou le laisser explicitement à l'appelant).
- **Modifier une copie** : `clone $produit`, ou `new Produit()` avec le même id, crée un objet que Doctrine ne suit pas. Il faut modifier **l'objet chargé**.
- **`persist()` inutile** : un objet venant de `find()` est déjà suivi ; `persist()` ne sert à rien (ce n'est pas « save »).
- **`flush()` dans une boucle** : une transaction par tour ; un seul `flush()` après la boucle suffit.

Pour vérifier : compter les requêtes. Une promotion sur 2 produits doit produire exactement 2 `UPDATE` dans une seule transaction.
"""),
  ],
  recap=["Le message cite `Entite#propriete` : c'est là qu'on regarde.",
         "Nouvel objet relié → `persist()` ou cascade.",
         "Clé étrangère NULL → renseigner le côté propriétaire (ManyToOne).",
         "Rien en base sans erreur → flush oublié ou objet non suivi.",
         "Le SQL envoyé (profiler) est la meilleure preuve."],
  example=F("terminal", "bash", r"""
In UnitOfWork.php line 3870:
  A new entity was found through the relationship 'App\Entity\Livre#auteur' that was not
  configured to cascade persist operations for entity: App\Entity\Auteur@58.

# Lecture : Livre#auteur = la propriété $auteur de Livre.
# L'auteur est un objet NOUVEAU (new Auteur(...)) que personne n'a persisté.
# Correction la plus simple, dans le service :
$em->persist($auteur);
$em->persist($livre);
$em->flush();
"""),
  notes=["`Livre#auteur` désigne la propriété fautive.", "Le message propose lui-même deux solutions.", "Sans `persist($auteur)`, Doctrine refuse d'enregistrer un livre qui pointe vers un auteur inconnu."],
  tds=[
    TD(1, "A new entity was found through the relationship",
       "L'import de livres plante au `flush()` avec une `ORMException` : *une nouvelle entité Auteur a été trouvée via la relation $auteur de Livre*. Corrige le service d'import." + DOC_SIM,
       ["Lance le code et lis l'erreur : quelle entité, quelle propriété ?",
        "Corrige `ImportLivres::importer()` pour que le livre **et** son auteur soient enregistrés",
        "Un seul `flush()`",
        "Résultat attendu : `INSERT INTO auteur` puis `INSERT INTO livre`"],
       [F("Entites.php", "php", r"""
<?php
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Auteur
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    #[ORM\Column]
    private string $nom;

    public function __construct(string $nom) { $this->nom = $nom; }
    public function getId(): ?int { return $this->id; }
}

#[ORM\Entity]
class Livre
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    #[ORM\Column]
    private string $titre;

    #[ORM\ManyToOne]
    #[ORM\JoinColumn(nullable: false)]
    private Auteur $auteur;

    public function __construct(string $titre, Auteur $auteur) { $this->titre = $titre; $this->auteur = $auteur; }
    public function getAuteur(): Auteur { return $this->auteur; }
}
"""), F("ImportLivres.php", "php", r"""
<?php
use Doctrine\ORM\EntityManagerInterface;

final class ImportLivres
{
    public function __construct(private EntityManagerInterface $em) {}

    public function importer(string $titre, string $nomAuteur): Livre
    {
        $auteur = new Auteur($nomAuteur);
        $livre = new Livre($titre, $auteur);
        $this->em->persist($livre);
        $this->em->flush();
        return $livre;
    }
}

$em = new Doctrine\ORM\FakeEntityManager();
(new ImportLivres($em))->importer('Dune', 'Frank Herbert');
""")],
       ["« via la relation $auteur de Livre » : c'est l'auteur qui est inconnu de Doctrine.",
        "Ajoute `$this->em->persist($auteur);` avant le `flush()`.",
        "Autre solution : `#[ORM\\ManyToOne(cascade: ['persist'])]` sur `Livre::$auteur`. Ici, persister explicitement est plus clair."],
       [F("ImportLivres.php", "php", r"""
<?php
use Doctrine\ORM\EntityManagerInterface;

final class ImportLivres
{
    public function __construct(private EntityManagerInterface $em) {}

    public function importer(string $titre, string $nomAuteur): Livre
    {
        $auteur = new Auteur($nomAuteur);
        $livre = new Livre($titre, $auteur);
        $this->em->persist($auteur);
        $this->em->persist($livre);
        $this->em->flush();
        return $livre;
    }
}

$em = new Doctrine\ORM\FakeEntityManager();
(new ImportLivres($em))->importer('Dune', 'Frank Herbert');
""")],
       ["Plus d'ORMException", "Un INSERT auteur et un INSERT livre"],
       run=DRUN(r"""
$em2 = new Doctrine\ORM\FakeEntityManager(); $em2->echo = false;
$ok = !throws(fn() => (new ImportLivres($em2))->importer('Fondation', 'Isaac Asimov'), Throwable::class);
check('importer() ne lève plus d\'erreur', $ok);
check('INSERT INTO auteur : 1', $em2->count('INSERT INTO auteur') === 1);
check('INSERT INTO livre : 1', $em2->count('INSERT INTO livre') === 1);
check('un seul flush (une transaction)', $em2->transactions === 1);
""")),
    TD(2, "Column cannot be null : le côté propriétaire",
       "Ajouter un livre à un auteur échoue : *INSERT impossible dans livre : la colonne auteur_id ne peut pas être NULL*. Pourtant le livre est bien dans la collection de l'auteur… Trouve pourquoi." + DOC_SIM,
       ["Lance et lis l'erreur : quelle colonne, quel « côté propriétaire » ?",
        "Corrige `Auteur::ajouterLivre()` pour que la relation soit renseignée **des deux côtés**",
        "Ajouter deux fois le même livre ne doit pas le dupliquer",
        "Ne touche pas au mapping"],
       [F("Entites.php", "php", r"""
<?php
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Auteur
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    #[ORM\Column]
    private string $nom;

    /** @var Collection<int, Livre> */
    #[ORM\OneToMany(targetEntity: Livre::class, mappedBy: 'auteur', cascade: ['persist'])]
    private Collection $livres;

    public function __construct(string $nom) { $this->nom = $nom; $this->livres = new ArrayCollection(); }

    public function ajouterLivre(Livre $livre): void
    {
        $this->livres->add($livre);
    }

    public function getLivres(): Collection { return $this->livres; }
}

#[ORM\Entity]
class Livre
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    #[ORM\Column]
    private string $titre;

    #[ORM\ManyToOne(inversedBy: 'livres')]
    #[ORM\JoinColumn(nullable: false)]
    private ?Auteur $auteur = null;

    public function __construct(string $titre) { $this->titre = $titre; }
    public function getAuteur(): ?Auteur { return $this->auteur; }
    public function setAuteur(?Auteur $auteur): void { $this->auteur = $auteur; }
}

$em = new Doctrine\ORM\FakeEntityManager();
$herbert = new Auteur('Frank Herbert');
$herbert->ajouterLivre(new Livre('Dune'));
$em->persist($herbert);
$em->flush();
""")],
       ["La colonne `auteur_id` est écrite d'après `Livre::$auteur` (le ManyToOne), pas d'après la collection.",
        "`var_dump($livre->getAuteur());` après `ajouterLivre()` affiche `NULL`.",
        "Dans `ajouterLivre()` : `if (!$this->livres->contains($livre)) { $this->livres->add($livre); $livre->setAuteur($this); }`"],
       [F("Entites.php", "php", r"""
<?php
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Auteur
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    #[ORM\Column]
    private string $nom;

    /** @var Collection<int, Livre> */
    #[ORM\OneToMany(targetEntity: Livre::class, mappedBy: 'auteur', cascade: ['persist'])]
    private Collection $livres;

    public function __construct(string $nom) { $this->nom = $nom; $this->livres = new ArrayCollection(); }

    public function ajouterLivre(Livre $livre): void
    {
        if (!$this->livres->contains($livre)) {
            $this->livres->add($livre);
            $livre->setAuteur($this);     // le côté propriétaire, celui qui écrit auteur_id
        }
    }

    public function getLivres(): Collection { return $this->livres; }
}

#[ORM\Entity]
class Livre
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    #[ORM\Column]
    private string $titre;

    #[ORM\ManyToOne(inversedBy: 'livres')]
    #[ORM\JoinColumn(nullable: false)]
    private ?Auteur $auteur = null;

    public function __construct(string $titre) { $this->titre = $titre; }
    public function getAuteur(): ?Auteur { return $this->auteur; }
    public function setAuteur(?Auteur $auteur): void { $this->auteur = $auteur; }
}

$em = new Doctrine\ORM\FakeEntityManager();
$herbert = new Auteur('Frank Herbert');
$herbert->ajouterLivre(new Livre('Dune'));
$em->persist($herbert);
$em->flush();
""")],
       ["`$livre->getAuteur()` renvoie l'auteur", "Le flush passe"],
       run=DRUN(r"""
$em2 = new Doctrine\ORM\FakeEntityManager(); $em2->echo = false;
$a = new Auteur('Asimov'); $l = new Livre('Fondation');
$a->ajouterLivre($l); $a->ajouterLivre($l);
check('le livre connaît son auteur', $l->getAuteur() === $a);
check('pas de doublon dans la collection', count($a->getLivres()) === 1);
check('flush sans erreur', !throws(function () use ($em2, $a) { $em2->persist($a); $em2->flush(); }, Throwable::class));
check('INSERT livre avec auteur_id', count(array_filter($em2->log, fn($q) => str_starts_with($q, 'INSERT INTO livre') && str_contains($q, 'auteur_id'))) === 1);
""")),
    TD(3, "Rien ne s'enregistre, aucune erreur",
       "La promotion « -10 % » ne s'applique jamais en base. Aucune erreur, aucune trace dans les logs. Le SQL affiché (ou plutôt son absence) est ton seul indice." + DOC_SIM,
       ["Lance : quelles requêtes SQL sont envoyées ? (`SQL> …`)",
        "Corrige `Promotion::appliquer()` : 2 produits → exactement 2 `UPDATE produit`, dans **une seule** transaction, aucun INSERT",
        "Le prix de 4990 devient 4491 (arrondi à l'entier inférieur)",
        "Pas de `persist()` inutile"],
       [F("Produit.php", "php", r"""
<?php
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Produit
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    #[ORM\Column]
    private string $nom;

    #[ORM\Column]
    private int $prix;

    public function __construct(string $nom, int $prix) { $this->nom = $nom; $this->prix = $prix; }
    public function getPrix(): int { return $this->prix; }
    public function setPrix(int $prix): void { $this->prix = $prix; }
}
"""), F("Promotion.php", "php", r"""
<?php
use Doctrine\ORM\EntityManagerInterface;

final class Promotion
{
    public function __construct(private EntityManagerInterface $em) {}

    /** @param list<int> $ids */
    public function appliquer(array $ids, int $pourcent): void
    {
        foreach ($ids as $id) {
            $produit = $this->em->find(Produit::class, $id);
            $copie = clone $produit;
            $copie->setPrix(intdiv($copie->getPrix() * (100 - $pourcent), 100));
            $this->em->persist($copie);
        }
    }
}

$em = new Doctrine\ORM\FakeEntityManager();
$em->seed(new Produit('Clavier', 4990), 1);
$em->seed(new Produit('Souris', 1990), 2);
(new Promotion($em))->appliquer([1, 2], 10);
echo "Fin de la promo\n";
""")],
       ["Deux problèmes : on modifie une **copie** (que Doctrine ne suit pas) et il n'y a **aucun** `flush()`.",
        "Un objet obtenu par `find()` est déjà suivi : modifie-le directement, `persist()` est inutile.",
        "Un seul `$this->em->flush();` **après** la boucle."],
       [F("Promotion.php", "php", r"""
<?php
use Doctrine\ORM\EntityManagerInterface;

final class Promotion
{
    public function __construct(private EntityManagerInterface $em) {}

    /** @param list<int> $ids */
    public function appliquer(array $ids, int $pourcent): void
    {
        foreach ($ids as $id) {
            $produit = $this->em->find(Produit::class, $id);      // déjà suivi par Doctrine
            $produit->setPrix(intdiv($produit->getPrix() * (100 - $pourcent), 100));
        }
        $this->em->flush();                                       // une seule transaction
    }
}

$em = new Doctrine\ORM\FakeEntityManager();
$em->seed(new Produit('Clavier', 4990), 1);
$em->seed(new Produit('Souris', 1990), 2);
(new Promotion($em))->appliquer([1, 2], 10);
echo "Fin de la promo\n";
""")],
       ["2 UPDATE dans 1 transaction", "Aucun INSERT"],
       run=DRUN(r"""
$em2 = new Doctrine\ORM\FakeEntityManager(); $em2->echo = false;
$em2->seed(new Produit('Clavier', 4990), 1); $em2->seed(new Produit('Souris', 1990), 2);
(new Promotion($em2))->appliquer([1, 2], 10);
check('2 UPDATE produit', $em2->count('UPDATE produit') === 2, implode(' | ', $em2->log));
check('aucun INSERT (pas de copie enregistrée)', $em2->count('INSERT') === 0);
check('une seule transaction (un flush après la boucle)', $em2->transactions === 1);
check('Clavier : 4990 → 4491', $em2->find(Produit::class, 1)->getPrix() === 4491);
check('Souris : 1990 → 1791', $em2->find(Produit::class, 2)->getPrix() === 1791);
""")),
  ])

# =========================================================================== Symfony
SF_SIM = " Le bouton Exécuter utilise le **Symfony simulé** : `App::request()` envoie une requête à tes contrôleurs et affiche la réponse (`HTTP> …`)."

symfony = DM("dbg-symfony", "Erreurs Symfony", 20,
  "Comprendre d'où viennent les 422, les 500 et les erreurs de services d'une API Symfony.",
  "Une API qui répond 422 ou 500 sans qu'on comprenne pourquoi bloque le front comme le back : il faut savoir lire la réponse et remonter à la cause.",
  ["Lire le **statut** : 4xx = la requête, 5xx = le serveur", "Lire le **corps** de la réponse : violations, message d'exception",
   "Comparer ce que le front **envoie** et ce que le DTO **attend**", "Pour un 500 : lire l'exception (autowiring, sérialisation…)"],
  ["422 de `#[MapRequestPayload]` : le JSON ne correspond pas au DTO (nom de champ, type, contrainte).",
   "Les noms de champs JSON doivent correspondre **exactement** aux propriétés du DTO.",
   "« Circular reference » à l'autowiring : deux services se demandent mutuellement.",
   "« A circular reference has been detected » à la sérialisation : on renvoie une entité avec une relation bidirectionnelle ; renvoyer un DTO de sortie.",
   "`php bin/console debug:router` et `debug:autowiring` aident à vérifier routes et services."],
  ["Renvoyer directement des entités Doctrine en JSON.", "Lire seulement le statut sans le corps de la réponse.", "Contourner une dépendance circulaire avec `new` dans le service."],
  [Q("Le front reçoit 422 avec `propertyPath: title` alors qu'il envoie `titre`…", ["la base est vide", "le DTO attend title, le JSON envoie titre", "la route n'existe pas", "le serveur est en panne"], 1, "Le champ manque côté DTO, qui garde sa valeur par défaut, et NotBlank échoue."),
   Q("Un 500 « Référence circulaire en sérialisant Auteur »…", ["renvoyer un DTO de sortie au lieu de l'entité", "augmenter la mémoire", "ajouter cascade", "passer en 422"], 0, "L'entité Auteur pointe vers Livre qui pointe vers Auteur : un DTO de sortie coupe la boucle."),
   Q("A dépend de B qui dépend de A : la bonne correction ?", ["faire new A() dans B", "extraire ou passer la donnée en paramètre pour casser le cycle", "mettre les deux dans un seul fichier", "désactiver l'autowiring"], 1, "Un cycle de dépendances révèle une responsabilité mal découpée.")],
  prereq=[
    P("Code de statut HTTP", "Le nombre en tête de réponse : 2xx succès, 4xx erreur de la requête (le client), 5xx erreur du serveur (ton code)."),
    P("DTO d'entrée", "Classe qui reçoit le JSON de la requête (`#[MapRequestPayload]`) et porte les contraintes de validation."),
    P("Autowiring", "Symfony construit tes services tout seul en lisant les types des paramètres de leur constructeur."),
    P("Sérialisation", "Transformer un objet PHP en JSON (et l'inverse). Le serializer suit les getters et les propriétés publiques."),
  ],
  diagram=D(
    nodes=[
      N("rq", 0, 1, "Requête JSON", "{ \"titre\": \"Dune\" }", kind="doc"),
      N("dto", 1, 1, "DTO + validation", "#[MapRequestPayload]", kind="file", color="accent"),
      N("e422", 1, 0, "422", "champ / type / contrainte", kind="pill", color="warn"),
      N("svc", 2, 1, "Contrôleur + services", "autowiring", kind="file"),
      N("e500a", 2, 2, "500", "dépendance circulaire", kind="pill", color="bad"),
      N("ser", 3, 1, "Sérialisation", "$this->json(...)", kind="file"),
      N("e500b", 3, 2, "500", "référence circulaire", kind="pill", color="bad"),
    ],
    edges=[E("rq", "dto"), E("dto", "e422", "invalide"), E("dto", "svc"), E("svc", "e500a"), E("svc", "ser"), E("ser", "e500b")],
    caption="Où naissent les erreurs d'une API Symfony : à l'entrée (422), dans les services (500), à la sortie (500)."),
  lessons=[
    L("4xx ou 5xx : qui doit corriger ?", r"""
- **4xx** : la **requête** est refusée. 400 (mal formée), 401 (pas connecté), 403 (pas le droit), 404 (introuvable), 422 (données invalides). Le serveur fonctionne ; il faut regarder ce que le client envoie.
- **5xx** : le **serveur** a planté. C'est une exception dans ton code PHP, visible dans `var/log/dev.log` ou sur la page d'erreur Symfony.

Toujours lire le **corps** de la réponse (onglet Réseau du navigateur, ou `curl -i`). Une 422 de `#[MapRequestPayload]` dit exactement quel champ pose problème :

```json
{
  "title": "Validation Failed",
  "violations": [{ "propertyPath": "title", "title": "Cette valeur ne doit pas être vide." }]
}
```

Ici, `propertyPath: title` alors que le front envoie `titre` : les noms ne correspondent pas.
"""),
    L("Les 422 : ce que le front envoie vs ce que le DTO attend", r"""
`#[MapRequestPayload]` remplit le DTO **par nom de propriété**. Un champ JSON mal nommé est simplement ignoré ; la propriété garde sa valeur par défaut, et une contrainte (`NotBlank`) échoue.

À comparer, champ par champ :

| Front (`JSON.stringify(...)`) | DTO PHP |
|---|---|
| `titre` | `$titre` (même nom, même casse) |
| `"1965"` (chaîne) | `int $annee` → 422 « doit être de type int » |
| champ absent | propriété sans défaut → 422 « obligatoire » |

L'onglet Réseau du navigateur montre le corps réellement envoyé ; `dump($dto)` dans le contrôleur montre ce que Symfony en a fait.
"""),
    L("Les 500 classiques", r"""
**Dépendance circulaire (autowiring).** `CommandeService` demande `Notificateur` au constructeur, qui demande `CommandeService`. Symfony ne peut construire ni l'un ni l'autre :

```
Circular reference detected for service "App\Service\CommandeService",
path: "CommandeService -> Notificateur -> CommandeService".
```

Ce n'est pas un problème de configuration, c'est un problème de **découpage** : souvent, l'un des deux n'a besoin que d'une **donnée** (on la lui passe en paramètre de méthode), ou une partie commune doit être extraite dans un troisième service.

**Référence circulaire (sérialisation).** `$this->json($auteur)` : le serializer lit `Auteur::getLivres()`, puis `Livre::getAuteur()`, puis `Auteur::getLivres()`… à l'infini. La correction propre : un **DTO de sortie** qui ne contient que ce que le front doit voir.

```php
return $this->json(new AuteurOutput($a->id, $a->nom, array_map(fn($l) => $l->titre, $a->livres)));
```
"""),
  ],
  recap=["4xx : regarder la requête ; 5xx : regarder l'exception côté serveur.",
         "Toujours lire le corps de la réponse (violations, message).",
         "422 : comparer noms et types du JSON avec le DTO.",
         "Dépendance circulaire : redécouper ou passer la donnée en paramètre.",
         "Référence circulaire au JSON : renvoyer un DTO de sortie, jamais l'entité."],
  example=F("terminal", "bash", r"""
$ curl -i -X POST localhost:8000/api/livres -H 'Content-Type: application/json' -d '{"titre":"Dune","annee":1965}'
HTTP/1.1 422 Unprocessable Content
{"title":"Validation Failed","violations":[{"propertyPath":"title","title":"This value should not be blank."}]}

# Le front envoie « titre », le DTO attend « title » : le champ est ignoré, NotBlank échoue.
# Correction : renommer la propriété du DTO (ou adapter le front), puis relancer la requête.
"""),
  notes=["`curl -i` affiche le statut et le corps.", "`propertyPath` donne le nom attendu côté PHP.", "Le JSON envoyé contient `titre` : les deux noms divergent."],
  tds=[
    TD(1, "422 : le front et le DTO ne parlent pas pareil",
       "Le formulaire React envoie `{\"titre\": \"Dune\", \"annee\": 1965}` et reçoit **422** à chaque fois. Le back « a l'air bon ». Lis la réponse et corrige." + SF_SIM,
       ["Lance : lis le statut **et** les violations (`propertyPath`)",
        "Corrige le back pour accepter le JSON du front tel qu'il est (le front ne change pas)",
        "La réponse 201 renvoie `{\"titre\": \"Dune\", \"annee\": 1965}`",
        "Un titre vide doit toujours donner 422 sur `titre`"],
       [F("Livres.php", "php", USES + r"""
final class CreerLivre
{
    public function __construct(
        #[Assert\NotBlank]
        public string $title = '',
        #[Assert\Range(min: 1450, max: 2100)]
        public int $annee = 0,
    ) {}
}

final class LivreController extends AbstractController
{
    #[Route('/api/livres', methods: ['POST'])]
    public function creer(#[MapRequestPayload] CreerLivre $dto): JsonResponse
    {
        return $this->json(['titre' => $dto->title, 'annee' => $dto->annee], 201);
    }
}

App::request('POST', '/api/livres', ['titre' => 'Dune', 'annee' => 1965]);
""")],
       ["`propertyPath: title` : c'est le nom que le DTO attend.",
        "Le JSON contient `titre` : `title` reste à sa valeur par défaut `''`, et `NotBlank` échoue.",
        "Renomme la propriété `$title` en `$titre` (et son usage dans le contrôleur)."],
       [F("Livres.php", "php", USES + r"""
final class CreerLivre
{
    public function __construct(
        #[Assert\NotBlank]
        public string $titre = '',
        #[Assert\Range(min: 1450, max: 2100)]
        public int $annee = 0,
    ) {}
}

final class LivreController extends AbstractController
{
    #[Route('/api/livres', methods: ['POST'])]
    public function creer(#[MapRequestPayload] CreerLivre $dto): JsonResponse
    {
        return $this->json(['titre' => $dto->titre, 'annee' => $dto->annee], 201);
    }
}

App::request('POST', '/api/livres', ['titre' => 'Dune', 'annee' => 1965]);
""")],
       ["Le JSON du front donne 201", "Un titre vide donne 422 sur `titre`"],
       run=SRUN(r"""
$r = App::request('POST', '/api/livres', ['titre' => 'Dune', 'annee' => 1965]);
check('le JSON du front donne 201', $r->status === 201, (string) $r);
check('réponse { titre: Dune, annee: 1965 }', $r->json() === ['titre' => 'Dune', 'annee' => 1965], (string) $r);
$r2 = App::request('POST', '/api/livres', ['titre' => '', 'annee' => 1965]);
check('titre vide : 422 sur « titre »', $r2->status === 422 && ($r2->json()['violations'][0]['propertyPath'] ?? '') === 'titre', (string) $r2);
""")),
    TD(2, "500 : dépendance circulaire",
       "Passer une commande renvoie **500** : *Dépendance circulaire : CommandeService -> Notificateur -> CommandeService*. Corrige le découpage des services sans contourner l'autowiring (pas de `new` caché)." + SF_SIM,
       ["Lance et lis le chemin de la dépendance circulaire",
        "Le `Notificateur` n'a besoin que des **données** de la commande : passe-les-lui en paramètre",
        "`POST /api/commandes {\"total\": 42}` → 201 `{\"id\": 1, \"total\": 42}`",
        "Le notificateur garde le message `Commande 1 confirmée : 42 €`"],
       [F("Commandes.php", "php", USES + r"""
final class PasserCommande
{
    public function __construct(#[Assert\Positive] public int $total = 0) {}
}

final class Notificateur
{
    public array $envoyes = [];

    public function __construct(private CommandeService $commandes) {}

    public function confirmer(int $id): void
    {
        $c = $this->commandes->trouver($id);
        $this->envoyes[] = "Commande {$c['id']} confirmée : {$c['total']} €";
    }
}

final class CommandeService
{
    private array $commandes = [];

    public function __construct(private Notificateur $notificateur) {}

    public function passer(int $total): array
    {
        $id = count($this->commandes) + 1;
        $this->commandes[$id] = ['id' => $id, 'total' => $total];
        $this->notificateur->confirmer($id);
        return $this->commandes[$id];
    }

    public function trouver(int $id): array { return $this->commandes[$id]; }
}

final class CommandeController extends AbstractController
{
    #[Route('/api/commandes', methods: ['POST'])]
    public function passer(#[MapRequestPayload] PasserCommande $dto, CommandeService $service): JsonResponse
    {
        return $this->json($service->passer($dto->total), 201);
    }
}

App::request('POST', '/api/commandes', ['total' => 42]);
""")],
       ["Le chemin dit qui demande qui : CommandeService → Notificateur → CommandeService.",
        "Pourquoi le Notificateur a-t-il besoin du service ? Seulement pour relire la commande qu'on vient de créer.",
        "`confirmer(array $commande)` sans dépendance au constructeur ; le service appelle `$this->notificateur->confirmer($this->commandes[$id])`."],
       [F("Commandes.php", "php", USES + r"""
final class PasserCommande
{
    public function __construct(#[Assert\Positive] public int $total = 0) {}
}

final class Notificateur
{
    public array $envoyes = [];

    /** @param array{id: int, total: int} $commande */
    public function confirmer(array $commande): void
    {
        $this->envoyes[] = "Commande {$commande['id']} confirmée : {$commande['total']} €";
    }
}

final class CommandeService
{
    private array $commandes = [];

    public function __construct(private Notificateur $notificateur) {}

    public function passer(int $total): array
    {
        $id = count($this->commandes) + 1;
        $this->commandes[$id] = ['id' => $id, 'total' => $total];
        $this->notificateur->confirmer($this->commandes[$id]);
        return $this->commandes[$id];
    }

    public function trouver(int $id): array { return $this->commandes[$id]; }
}

final class CommandeController extends AbstractController
{
    #[Route('/api/commandes', methods: ['POST'])]
    public function passer(#[MapRequestPayload] PasserCommande $dto, CommandeService $service): JsonResponse
    {
        return $this->json($service->passer($dto->total), 201);
    }
}

App::request('POST', '/api/commandes', ['total' => 42]);
""")],
       ["Plus de 500", "Le Notificateur ne dépend plus de CommandeService"],
       run=SRUN(r"""
$r = App::request('POST', '/api/commandes', ['total' => 42]);
check('POST /api/commandes → 201', $r->status === 201, (string) $r);
check('réponse { id: 1, total: 42 }', $r->json() === ['id' => 1, 'total' => 42], (string) $r);
check('message de confirmation envoyé', App::get(Notificateur::class)->envoyes === ['Commande 1 confirmée : 42 €'], json_encode(App::get(Notificateur::class)->envoyes, JSON_UNESCAPED_UNICODE));
$params = (new ReflectionClass(Notificateur::class))->getConstructor()?->getParameters() ?? [];
check('Notificateur ne dépend plus de CommandeService', !array_filter($params, fn($p) => (string) $p->getType() === 'CommandeService'));
""")),
    TD(3, "500 : référence circulaire en JSON",
       "`GET /api/auteurs/1` renvoie **500** : *Référence circulaire détectée en sérialisant Auteur*. Le front a seulement besoin de l'id, du nom et des titres des livres. Corrige proprement (et gère l'auteur inexistant)." + SF_SIM,
       ["Lance : quel objet pointe vers quel objet ?",
        "Crée un DTO de sortie `AuteurOutput` (id, nom, `livres` = liste des titres) et renvoie-le",
        "`GET /api/auteurs/1` → 200 `{\"id\":1,\"nom\":\"Frank Herbert\",\"livres\":[\"Dune\",\"Le Messie de Dune\"]}`",
        "`GET /api/auteurs/9` → 404"],
       [F("Auteurs.php", "php", USES + r"""
// « Entités » (simplifiées : en vrai, ce seraient des entités Doctrine)
final class Auteur
{
    public array $livres = [];
    public function __construct(public int $id, public string $nom) {}
}

final class Livre
{
    public function __construct(public string $titre, public Auteur $auteur) {}
}

final class AuteurRepository
{
    private array $auteurs = [];

    public function __construct()
    {
        $h = new Auteur(1, 'Frank Herbert');
        $h->livres[] = new Livre('Dune', $h);
        $h->livres[] = new Livre('Le Messie de Dune', $h);
        $this->auteurs[1] = $h;
    }

    public function find(int $id): ?Auteur { return $this->auteurs[$id] ?? null; }
}

final class AuteurController extends AbstractController
{
    #[Route('/api/auteurs/{id}', methods: ['GET'])]
    public function show(int $id, AuteurRepository $repo): JsonResponse
    {
        return $this->json($repo->find($id));
    }
}

App::request('GET', '/api/auteurs/1');
""")],
       ["Auteur → livres → Livre → auteur → Auteur → … : le serializer tourne en rond.",
        "`final class AuteurOutput { public function __construct(public int $id, public string $nom, public array $livres) {} }`",
        "`if (!$a) throw $this->createNotFoundException('Auteur introuvable');` puis `array_map(fn(Livre $l) => $l->titre, $a->livres)`."],
       [F("Auteurs.php", "php", USES + r"""
final class Auteur
{
    public array $livres = [];
    public function __construct(public int $id, public string $nom) {}
}

final class Livre
{
    public function __construct(public string $titre, public Auteur $auteur) {}
}

final class AuteurRepository
{
    private array $auteurs = [];

    public function __construct()
    {
        $h = new Auteur(1, 'Frank Herbert');
        $h->livres[] = new Livre('Dune', $h);
        $h->livres[] = new Livre('Le Messie de Dune', $h);
        $this->auteurs[1] = $h;
    }

    public function find(int $id): ?Auteur { return $this->auteurs[$id] ?? null; }
}

final class AuteurOutput
{
    /** @param list<string> $livres */
    public function __construct(public int $id, public string $nom, public array $livres) {}
}

final class AuteurController extends AbstractController
{
    #[Route('/api/auteurs/{id}', methods: ['GET'])]
    public function show(int $id, AuteurRepository $repo): JsonResponse
    {
        $a = $repo->find($id);
        if (!$a) {
            throw $this->createNotFoundException('Auteur introuvable');
        }
        return $this->json(new AuteurOutput($a->id, $a->nom, array_map(fn(Livre $l) => $l->titre, $a->livres)));
    }
}

App::request('GET', '/api/auteurs/1');
""")],
       ["200 avec la forme attendue", "404 pour un auteur inconnu"],
       run=SRUN(r"""
$r = App::request('GET', '/api/auteurs/1');
check('GET /api/auteurs/1 → 200', $r->status === 200, (string) $r);
check('forme { id, nom, livres: [titres] }', $r->json() === ['id' => 1, 'nom' => 'Frank Herbert', 'livres' => ['Dune', 'Le Messie de Dune']], (string) $r);
check('GET /api/auteurs/9 → 404', App::request('GET', '/api/auteurs/9')->status === 404);
check('une classe AuteurOutput existe', class_exists('AuteurOutput'));
""")),
  ])

# =========================================================================== React
react = DM("dbg-react", "Erreurs React", 20,
  "Reconnaître les erreurs React typiques (rendus infinis, effets qui bouclent, clés) et les corriger à la source.",
  "React affiche des erreurs claires… quand on sait les lire. Et ses bugs les plus pénibles (boucles, état qui saute d'un élément à l'autre) n'en affichent aucune.",
  ["Lire l'erreur **et** le composant cité (« The above error occurred in <Compteur> »)", "Ouvrir la **console** et l'onglet **Réseau** du navigateur",
   "Pour une boucle : chercher ce qui **change à chaque rendu**", "Vérifier avec React DevTools (props, state) ou un `console.log` dans le composant"],
  ["« Too many re-renders » : un `setState` est **appelé** pendant le rendu (souvent `onClick={setX(1)}` au lieu de `onClick={() => setX(1)}`).",
   "Un `useEffect` qui relance sans fin : une dépendance qui est un objet ou un tableau recréé à chaque rendu.",
   "« Each child in a list should have a unique key » : utiliser un **id stable**, pas l'index quand la liste change.",
   "« Cannot read properties of undefined (reading 'map') » : la donnée n'est pas encore là ou n'a pas la forme attendue.",
   "Un `console.log` en tête de composant montre combien de fois il se rend."],
  ["Désactiver le StrictMode pour « régler » un double appel.", "Mettre `// eslint-disable-next-line` sur les dépendances d'un effet.", "Utiliser l'index comme `key` dans une liste qu'on peut modifier."],
  [Q("`<button onClick={setN(n + 1)}>` provoque…", ["un clic qui ne fait rien", "un rendu infini (Too many re-renders)", "une erreur de syntaxe", "rien de spécial"], 1, "setN est appelé pendant le rendu, qui redéclenche un rendu, etc."),
   Q("Un effet avec `[filtres]` où `const filtres = { q }`…", ["s'exécute une fois", "s'exécute à chaque rendu : l'objet est nouveau à chaque fois", "ne s'exécute jamais", "plante"], 1, "React compare par référence : un nouvel objet = dépendance changée."),
   Q("Après suppression d'un élément, la saisie d'une ligne « saute » sur la ligne voisine. Cause probable ?", ["key={index}", "useMemo manquant", "le CSS", "un fetch"], 0, "Avec l'index, React associe l'état de la ligne 0 à la nouvelle ligne 0.")],
  prereq=[
    P("Rendu", "React appelle ta fonction composant pour calculer ce qu'il faut afficher. Un `setState` provoque un nouveau rendu."),
    P("Dépendances d'un effet", "Le tableau `[a, b]` de `useEffect` : l'effet se relance quand une de ces valeurs change (comparaison par référence pour les objets)."),
    P("`key`", "Identifiant donné à chaque élément d'une liste pour que React sache quel élément est lequel d'un rendu à l'autre."),
    P("Console / onglet Réseau", "Outils du navigateur (F12) : la console affiche les erreurs, le Réseau liste chaque requête HTTP."),
  ],
  diagram=D(
    nodes=[
      N("a1", 0, 0, "onClick={setN(n + 1)}", "dans le JSX", kind="file", color="bad"),
      N("a2", 1, 0, "setN appelé au rendu", "pas au clic", kind="pill", color="warn"),
      N("a3", 2, 0, "Nouveau rendu", "et ainsi de suite", kind="note", color="bad"),
      N("b1", 0, 1, "const f = { q }", "nouvel objet à chaque rendu", kind="file", color="bad"),
      N("b2", 1, 1, "useEffect(…, [f])", "relancé à chaque rendu", kind="pill", color="warn"),
      N("b3", 2, 1, "setState → rendu", "et ainsi de suite", kind="note", color="bad"),
    ],
    edges=[E("a1", "a2"), E("a2", "a3"), E("b1", "b2"), E("b2", "b3")],
    caption="Deux façons de fabriquer une boucle infinie de rendus : appeler setState pendant le rendu, ou un effet dont une dépendance change à chaque rendu."),
  lessons=[
    L("Lire une erreur React", r"""
Dans la console (F12), React affiche le message **et le composant** :

```
Uncaught Error: Too many re-renders. React limits the number of renders to prevent an infinite loop.
The above error occurred in the <Compteur> component:
    at Compteur (Compteur.jsx:4)
    at App (App.jsx:12)
```

- Le message dit **quoi** ; « occurred in the `<Compteur>` component » dit **où** ; la liste `at …` donne l'arbre des composants.
- Les **avertissements** (`Warning: Each child in a list should have a unique "key" prop`) ne plantent pas mais annoncent un bug.
- L'onglet **Réseau** montre les requêtes : une requête répétée en boucle se voit immédiatement.
- Un `console.log('rendu', props)` en tête de composant montre combien de fois il se rend (deux fois en développement avec StrictMode : c'est normal).
"""),
    L("Les boucles infinies", r"""
**1. setState appelé pendant le rendu.**

```jsx
<button onClick={setN(n + 1)}>+</button>       // appelle setN tout de suite, à chaque rendu
<button onClick={() => setN(n + 1)}>+</button> // passe une fonction, appelée au clic
```

**2. Un effet dont une dépendance change à chaque rendu.**

```jsx
const filtres = { q, tri };                     // nouvel objet à CHAQUE rendu
useEffect(() => { charger(filtres).then(setLivres); }, [filtres]);   // relancé à chaque rendu
```

`setLivres` provoque un rendu, qui crée un nouvel objet `filtres`, qui relance l'effet… Corrections : dépendre des **valeurs simples** (`[q, tri]`), créer l'objet **dans** l'effet, ou `useMemo`.
"""),
    L("Les clés et l'état qui « saute »", r"""
React utilise la `key` pour savoir quel composant correspond à quel élément. Avec `key={index}` :

```
avant : [A (index 0), B (index 1)]      B a un champ rempli : « urgent »
on supprime A
après : [B (index 0)]                   React croit que c'est l'ancien composant 0 (A) : B récupère l'état de A
```

L'état interne (un `useState` dans la ligne, un `<input>` non contrôlé) reste attaché à la **position**, pas à l'élément. Toujours une **clé stable** issue des données : `key={tache.id}`.

Autres erreurs fréquentes :

| Message | Cause |
|---|---|
| `Cannot read properties of undefined (reading 'map')` | la donnée n'est pas encore chargée, ou ce n'est pas un tableau (ex. réponse axios entière au lieu de `res.data`) |
| `Objects are not valid as a React child` | afficher un objet `{…}` au lieu d'un de ses champs |
| `Rendered more hooks than during the previous render` | un hook appelé dans un `if` ou après un `return` |
"""),
  ],
  recap=["Console : message + composant cité ; onglet Réseau pour les requêtes.",
         "`onClick={() => …}`, jamais `onClick={setX(…)}`.",
         "Dépendances d'effet : valeurs simples, pas d'objet recréé à chaque rendu.",
         "`key` = id stable, jamais l'index d'une liste modifiable.",
         "`console.log` en tête de composant pour compter les rendus."],
  example=F("Compteur.jsx", "jsx", r"""
import { useState } from 'react';

export default function Compteur() {
  const [n, setN] = useState(0);
  console.log('rendu', n);                       // pour voir combien de fois on se rend

  // ✗ setN(n + 1) est APPELÉ pendant le rendu → Too many re-renders
  // return <button onClick={setN(n + 1)}>{n}</button>;

  // ✓ on passe une fonction, appelée au clic
  return <button onClick={() => setN((x) => x + 1)}>{n}</button>;
}
"""),
  notes=["Le `console.log` révèle une boucle (des centaines de « rendu »).", "La version cassée appelle `setN` immédiatement.", "La version correcte passe une fonction."],
  tds=[
    TD(1, "Too many re-renders",
       "L'application plante dès l'affichage : *Too many re-renders. React limits the number of renders to prevent an infinite loop.* Trouve les lignes fautives (il y en a **deux**) et corrige. " + METHODE,
       ["Lance : lis l'erreur dans la sortie",
        "Corrige les deux boutons : `+1` ajoute 1, `Remettre à zéro` remet à 0",
        "Le titre affiche `Compteur : N`"],
       [F("App.jsx", "jsx", r"""
import { useState } from 'react';

export default function App() {
  const [n, setN] = useState(0);
  return (
    <div>
      <h1>Compteur : {n}</h1>
      <button className="plus" onClick={setN(n + 1)}>+1</button>
      <button className="zero" onClick={setN(0)}>Remettre à zéro</button>
    </div>
  );
}
""")],
       ["`onClick={setN(n + 1)}` appelle `setN` pendant le rendu.",
        "Il faut passer une **fonction** : `onClick={() => setN(n + 1)}`.",
        "Le 2e bouton a le même problème."],
       [F("App.jsx", "jsx", r"""
import { useState } from 'react';

export default function App() {
  const [n, setN] = useState(0);
  return (
    <div>
      <h1>Compteur : {n}</h1>
      <button className="plus" onClick={() => setN((x) => x + 1)}>+1</button>
      <button className="zero" onClick={() => setN(0)}>Remettre à zéro</button>
    </div>
  );
}
""")],
       ["Plus d'erreur au démarrage", "Les deux boutons marchent"],
       run=RUN("react", entry="App.jsx", tests=r"""
await waitFor(() => $('h1'), 2000);
assert($('h1').textContent === 'Compteur : 0', 'Affichage initial : Compteur : 0');
await click('.plus'); await click('.plus'); await click('.plus');
assert($('h1').textContent === 'Compteur : 3', '3 clics : Compteur : 3');
await click('.zero');
assert($('h1').textContent === 'Compteur : 0', 'Remettre à zéro');
""")),
    TD(2, "Un effet qui ne s'arrête jamais",
       "La liste de livres s'affiche, mais l'onglet Réseau (ici, la sortie) montre `GET /api/livres` **en boucle**, des dizaines de fois par seconde. Trouve ce qui relance l'effet et corrige. " + METHODE,
       ["Lance : compte les requêtes dans la sortie",
        "Au chargement : **une seule** requête",
        "Taper dans la recherche relance la requête avec `?q=…` (une requête par changement)",
        "La liste affiche les titres reçus"],
       [F("App.jsx", "jsx", r"""
import { useEffect, useState } from 'react';

export default function App() {
  const [q, setQ] = useState('');
  const [livres, setLivres] = useState([]);
  const filtres = { q };

  useEffect(() => {
    fetch('/api/livres?q=' + encodeURIComponent(filtres.q))
      .then((r) => r.json())
      .then(setLivres);
  }, [filtres]);

  return (
    <div>
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Rechercher" />
      <ul>{livres.map((l) => <li key={l.id}>{l.titre}</li>)}</ul>
    </div>
  );
}
""")],
       ["Ajoute `console.log('effet')` dans l'effet : il s'affiche sans arrêt.",
        "`filtres` est un **nouvel objet** à chaque rendu ; React le voit comme une dépendance qui a changé.",
        "Dépends de la valeur simple : `[q]`, et utilise `q` dans l'effet."],
       [F("App.jsx", "jsx", r"""
import { useEffect, useState } from 'react';

export default function App() {
  const [q, setQ] = useState('');
  const [livres, setLivres] = useState([]);

  useEffect(() => {
    fetch('/api/livres?q=' + encodeURIComponent(q))
      .then((r) => r.json())
      .then(setLivres);
  }, [q]);

  return (
    <div>
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Rechercher" />
      <ul>{livres.map((l) => <li key={l.id}>{l.titre}</li>)}</ul>
    </div>
  );
}
""")],
       ["Une seule requête au chargement", "Une requête par frappe"],
       run=RUN("react", entry="App.jsx", api=r"""
window.__appels = 0;
const LIVRES = [{ id: 1, titre: 'Dune' }, { id: 2, titre: 'Fondation' }, { id: 3, titre: 'Hypérion' }];
__api["GET /api/livres"] = (p) => { window.__appels++; const q = (p.q || '').toLowerCase(); return LIVRES.filter((l) => l.titre.toLowerCase().includes(q)); };
""", tests=r"""
await waitFor(() => $$('li').length === 3, 3000);
await sleep(1500);
assert(window.__appels <= 2, 'Au chargement : une seule requête (' + window.__appels + ' reçues ; 2 tolérées en mode StrictMode)');
const avant = window.__appels;
await type('input', 'du');
await waitFor(() => $$('li').length === 1, 3000);
await sleep(1200);
assert(window.__appels - avant <= 2, 'Après la frappe : une requête par changement (' + (window.__appels - avant) + ')');
assert($('li').textContent === 'Dune', 'La recherche « du » affiche Dune');
""")),
    TD(3, "L'état qui saute d'une ligne à l'autre",
       "Chaque tâche a un champ « note ». Bug signalé : *quand je supprime la première tâche, la note que j'avais écrite sur la deuxième disparaît (ou passe sur une autre)*. Aucune erreur, juste un avertissement… ou même pas. " + METHODE,
       ["Reproduis : écris une note sur « Courses », supprime « Ménage » : où est passée la note ?",
        "Trouve la cause et corrige-la (une seule ligne)",
        "Supprimer une tâche ne doit jamais déplacer la note d'une autre"],
       [F("App.jsx", "jsx", r"""
import { useState } from 'react';

function Tache({ titre, onSupprimer }) {
  const [note, setNote] = useState('');
  return (
    <li>
      <b>{titre}</b>
      <input className="note" value={note} onChange={(e) => setNote(e.target.value)} placeholder="note" />
      <button onClick={onSupprimer}>Supprimer</button>
    </li>
  );
}

export default function App() {
  const [taches, setTaches] = useState([
    { id: 'm', titre: 'Ménage' },
    { id: 'c', titre: 'Courses' },
    { id: 'r', titre: 'Révisions' },
  ]);
  const supprimer = (id) => setTaches((ts) => ts.filter((t) => t.id !== id));

  return (
    <ul>
      {taches.map((t, i) => (
        <Tache key={i} titre={t.titre} onSupprimer={() => supprimer(t.id)} />
      ))}
    </ul>
  );
}
""")],
       ["La note est un `useState` **dans** `Tache` : elle est attachée au composant que React associe à chaque position.",
        "Avec `key={i}`, après suppression, « Courses » devient la position 0 et récupère l'état de l'ancien composant 0.",
        "`key={t.id}`."],
       [F("App.jsx", "jsx", r"""
import { useState } from 'react';

function Tache({ titre, onSupprimer }) {
  const [note, setNote] = useState('');
  return (
    <li>
      <b>{titre}</b>
      <input className="note" value={note} onChange={(e) => setNote(e.target.value)} placeholder="note" />
      <button onClick={onSupprimer}>Supprimer</button>
    </li>
  );
}

export default function App() {
  const [taches, setTaches] = useState([
    { id: 'm', titre: 'Ménage' },
    { id: 'c', titre: 'Courses' },
    { id: 'r', titre: 'Révisions' },
  ]);
  const supprimer = (id) => setTaches((ts) => ts.filter((t) => t.id !== id));

  return (
    <ul>
      {taches.map((t) => (
        <Tache key={t.id} titre={t.titre} onSupprimer={() => supprimer(t.id)} />
      ))}
    </ul>
  );
}
""")],
       ["La note reste sur « Courses » après suppression de « Ménage »"],
       run=RUN("react", entry="App.jsx", tests=r"""
await waitFor(() => $$('li').length === 3, 2000);
await type($$('.note')[1], 'lait, pain');
await click($$('li button')[0]);
await waitFor(() => $$('li').length === 2, 2000);
const ligne = $$('li').find((li) => li.textContent.includes('Courses'));
assert(ligne && ligne.querySelector('.note').value === 'lait, pain', 'Après suppression de « Ménage », la note reste sur « Courses »');
const rev = $$('li').find((li) => li.textContent.includes('Révisions'));
assert(rev && rev.querySelector('.note').value === '', '« Révisions » n\'a pas récupéré de note');
assert(!/key=\{i\}|key=\{index\}/.test(source('App.jsx')), 'La clé n\'est plus l\'index');
""")),
  ])

# =========================================================================== Données & API
data = DM("dbg-data", "Erreurs réseau et API", 20,
  "Diagnostiquer les problèmes entre React et une API : mauvaise forme de réponse, erreurs HTTP ignorées, réponses dans le désordre.",
  "Le front et le back peuvent être corrects chacun de leur côté et pourtant mal fonctionner ensemble. L'onglet Réseau est l'outil qui tranche.",
  ["Ouvrir l'onglet **Réseau** : URL, méthode, statut, corps envoyé et reçu", "Comparer la **forme** de la réponse avec ce que le code attend",
   "Vérifier que les **erreurs HTTP** sont bien traitées (fetch ne lève rien sur 4xx/5xx)", "Penser au **temps** : deux requêtes peuvent répondre dans le désordre"],
  ["axios renvoie un objet réponse : les données sont dans `res.data`.",
   "`fetch` ne lève **pas** d'erreur sur 404 ou 422 : il faut tester `res.ok`.",
   "`Unexpected token '<'… is not valid JSON` : l'API a renvoyé du HTML (souvent une page d'erreur ou une mauvaise URL).",
   "Recherche qui affiche de vieux résultats : une réponse lente arrive après une plus récente ; annuler l'ancienne (`AbortController`).",
   "CORS : l'erreur est dans la console, la correction est côté serveur (en-têtes), pas dans React."],
  ["Afficher « Enregistré ! » sans vérifier le statut.", "Mettre `res` (axios) directement dans le state.", "Ignorer les réponses arrivées dans le désordre."],
  [Q("`const res = await axios.get('/api/livres'); setLivres(res)` puis `livres.map`…", ["marche", "plante : res est un objet réponse, les données sont dans res.data", "renvoie une promesse", "fait 2 requêtes"], 1, "axios enveloppe la réponse : status, headers, data…"),
   Q("`fetch` reçoit une 422 :", ["il lève une exception", "il résout normalement, res.ok vaut false", "il réessaie", "il renvoie undefined"], 1, "fetch ne rejette que sur une erreur réseau ; à toi de tester res.ok."),
   Q("En tapant vite « d » puis « du », la liste affiche les résultats de « d ». Cause ?", ["le cache", "la réponse de « d » est arrivée après celle de « du »", "React est lent", "une clé manquante"], 1, "Il faut ignorer ou annuler les réponses obsolètes.")],
  prereq=[
    P("Onglet Réseau", "Outil du navigateur (F12) qui liste chaque requête : URL, méthode, statut, en-têtes, corps envoyé et reçu."),
    P("`res.ok`", "Booléen de `fetch` : vrai pour un statut 200 à 299. Faux pour 404, 422, 500… sans lever d'erreur."),
    P("Réponse axios", "Un objet `{ data, status, headers, config }` ; les données JSON sont dans `data`. axios **lève** une erreur pour les statuts ≥ 400."),
    P("Requête obsolète", "Une requête dont on n'a plus besoin (l'utilisateur a changé la recherche). Sa réponse doit être ignorée ou la requête annulée."),
  ],
  diagram=D(
    nodes=[
      N("ui", 0, 1, "Composant React", "fetch / axios", kind="file", color="accent"),
      N("net", 1, 1, "Onglet Réseau", "URL · statut · corps", kind="note", color="warn"),
      N("api", 2, 1, "API", "200 · 404 · 422 · 500", kind="db", color="muted"),
      N("shape", 1, 0, "Forme de la réponse", "res.data ? tableau ?", kind="pill"),
      N("err", 1, 2, "Erreurs HTTP", "res.ok / catch", kind="pill", color="bad"),
    ],
    edges=[E("ui", "net"), E("net", "api"), E("net", "shape"), E("net", "err")],
    caption="L'onglet Réseau est l'arbitre : il montre ce qui est vraiment parti et revenu. Ensuite, on vérifie la forme des données et le traitement des erreurs."),
  lessons=[
    L("L'onglet Réseau d'abord", r"""
Avant de toucher au code, ouvre l'onglet **Réseau** (F12 → Network, filtre Fetch/XHR) et clique sur la requête :

- **URL et méthode** : est-ce la bonne route ? (`/api/livre` au lieu de `/api/livres` → 404)
- **Statut** : 200 ? 404 ? 422 ? 500 ?
- **Payload** (corps envoyé) : les bons noms de champs ? les bons types ?
- **Response** : du JSON ? quelle forme ? ou une page HTML d'erreur ?

Un `Unexpected token '<', "<!DOCTYPE "... is not valid JSON` veut dire : on a appelé `res.json()` sur une page **HTML**. L'onglet Réseau montre laquelle (souvent une 404 du serveur de dev, ou une page d'erreur Symfony).
"""),
    L("fetch et axios ne réagissent pas pareil", r"""
| | `fetch` | axios |
|---|---|---|
| Données | `await res.json()` | `res.data` |
| Statut 4xx/5xx | **pas d'exception** : tester `res.ok` | exception (`err.response.status`) |
| Corps d'erreur | `await res.json()` aussi | `err.response.data` |

Les deux pièges qui en découlent :

```js
// axios : on stocke l'objet réponse au lieu des données
const res = await axios.get('/api/livres');
setLivres(res);            // ✗ livres.map is not a function
setLivres(res.data);       // ✓

// fetch : on affiche « succès » même pour une 422
const res = await fetch('/api/livres', { method: 'POST', body });
setMessage('Livre créé !');           // ✗ même si res.status === 422
if (!res.ok) { setErreurs((await res.json()).violations); return; }   // ✓
```
"""),
    L("Les réponses dans le désordre", r"""
L'utilisateur tape « d » puis « du ». Deux requêtes partent. Si celle de « d » est plus **lente**, elle arrive **après** celle de « du » et écrase le bon résultat :

```
t=0    GET ?q=d    ─────────────────────────► (répond à t=600)
t=100  GET ?q=du   ──────► (répond à t=150)
écran : résultats de « du » à t=150, puis de « d » à t=600   ✗
```

La correction : quand la recherche change, **annuler** (ou ignorer) la requête précédente, dans le nettoyage de l'effet :

```jsx
useEffect(() => {
  const ctrl = new AbortController();
  fetch('/api/livres?q=' + q, { signal: ctrl.signal })
    .then((r) => r.json())
    .then(setLivres)
    .catch((e) => { if (e.name !== 'AbortError') throw e; });
  return () => ctrl.abort();          // appelé quand q change : l'ancienne requête est annulée
}, [q]);
```

(TanStack Query gère ce problème tout seul, avec une clé par recherche.)
"""),
  ],
  recap=["Onglet Réseau : URL, statut, corps envoyé, corps reçu.",
         "axios : `res.data` ; fetch : `await res.json()`.",
         "fetch ne lève rien sur 4xx/5xx : tester `res.ok`.",
         "`Unexpected token '<'` : on a reçu du HTML, pas du JSON.",
         "Réponses dans le désordre : annuler la requête précédente (AbortController)."],
  example=F("Recherche.jsx", "jsx", r"""
import { useEffect, useState } from 'react';

export default function Recherche() {
  const [q, setQ] = useState('');
  const [livres, setLivres] = useState([]);
  const [erreur, setErreur] = useState(null);

  useEffect(() => {
    const ctrl = new AbortController();
    fetch('/api/livres?q=' + encodeURIComponent(q), { signal: ctrl.signal })
      .then(async (res) => {
        if (!res.ok) throw new Error('HTTP ' + res.status);   // fetch ne le fait pas pour nous
        setLivres(await res.json());
      })
      .catch((e) => { if (e.name !== 'AbortError') setErreur(e.message); });
    return () => ctrl.abort();                                // requête obsolète annulée
  }, [q]);

  return (/* … */ null);
}
"""),
  notes=["`res.ok` est testé explicitement.", "L'`AbortController` annule la requête quand `q` change.", "Une annulation n'est pas une vraie erreur : on l'ignore."],
  tds=[
    TD(1, "livres.map is not a function",
       "La page plante au chargement : *TypeError: livres.map is not a function*. L'onglet Réseau (la sortie) montre pourtant `GET /api/livres → 200`. Trouve pourquoi. " + METHODE,
       ["Lance et lis l'erreur ; l'API répond bien 200",
        "Ajoute un `console.log` de ce que tu mets dans le state : quelle forme ?",
        "Corrige : la liste affiche les 3 titres"],
       [F("App.jsx", "jsx", r"""
import { useEffect, useState } from 'react';
import axios from 'axios';

export default function App() {
  const [livres, setLivres] = useState([]);

  useEffect(() => {
    axios.get('/api/livres').then((res) => setLivres(res));
  }, []);

  return <ul>{livres.map((l) => <li key={l.id}>{l.titre}</li>)}</ul>;
}
""")],
       ["`console.log(res)` affiche un objet `{ data, status, headers, config }`.",
        "Les données JSON sont dans `res.data`.",
        "`.then((res) => setLivres(res.data))`."],
       [F("App.jsx", "jsx", r"""
import { useEffect, useState } from 'react';
import axios from 'axios';

export default function App() {
  const [livres, setLivres] = useState([]);

  useEffect(() => {
    axios.get('/api/livres').then((res) => setLivres(res.data));
  }, []);

  return <ul>{livres.map((l) => <li key={l.id}>{l.titre}</li>)}</ul>;
}
""")],
       ["Les 3 titres s'affichent", "Plus de TypeError"],
       run=RUN("react", entry="App.jsx", api=r"""
__api["GET /api/livres"] = () => [{ id: 1, titre: 'Dune' }, { id: 2, titre: 'Fondation' }, { id: 3, titre: 'Hypérion' }];
""", tests=r"""
await waitFor(() => $$('li').length === 3, 3000);
assert($$('li').map((l) => l.textContent).join(',') === 'Dune,Fondation,Hypérion', 'Les 3 titres s\'affichent');
""")),
    TD(2, "« Livre créé ! »… même quand c'est refusé",
       "Le formulaire affiche toujours *Livre créé !*, même avec un titre vide, alors que l'API répond **422**. Les utilisateurs croient que c'est enregistré. Corrige le traitement de la réponse. " + METHODE,
       ["Lance avec un titre vide : regarde le statut dans la sortie",
        "422 → afficher les messages de `violations` dans `<p className=\"erreur\">` (un par violation), et **pas** le message de succès",
        "201 → afficher `Livre créé !` dans `<p className=\"ok\">` et vider le champ",
        "Garde `fetch`"],
       [F("App.jsx", "jsx", r"""
import { useState } from 'react';

export default function App() {
  const [titre, setTitre] = useState('');
  const [message, setMessage] = useState(null);

  async function envoyer(e) {
    e.preventDefault();
    await fetch('/api/livres', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ titre }),
    });
    setMessage('Livre créé !');
    setTitre('');
  }

  return (
    <form onSubmit={envoyer}>
      <input name="titre" value={titre} onChange={(e) => setTitre(e.target.value)} />
      <button>Créer</button>
      {message && <p className="ok">{message}</p>}
    </form>
  );
}
""")],
       ["`fetch` ne lève pas d'erreur sur une 422 : `res.ok` vaut `false`.",
        "`const data = await res.json();` contient `violations: [{ propertyPath, title }]`.",
        "Un state `erreurs` (tableau) : rempli si `!res.ok`, vidé en cas de succès."],
       [F("App.jsx", "jsx", r"""
import { useState } from 'react';

export default function App() {
  const [titre, setTitre] = useState('');
  const [message, setMessage] = useState(null);
  const [erreurs, setErreurs] = useState([]);

  async function envoyer(e) {
    e.preventDefault();
    setMessage(null);
    const res = await fetch('/api/livres', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ titre }),
    });
    const data = await res.json();
    if (!res.ok) {
      setErreurs((data.violations || []).map((v) => v.title));
      return;
    }
    setErreurs([]);
    setMessage('Livre créé !');
    setTitre('');
  }

  return (
    <form onSubmit={envoyer}>
      <input name="titre" value={titre} onChange={(e) => setTitre(e.target.value)} />
      <button>Créer</button>
      {erreurs.map((m) => <p className="erreur" key={m}>{m}</p>)}
      {message && <p className="ok">{message}</p>}
    </form>
  );
}
""")],
       ["Titre vide : message d'erreur, pas de succès", "Titre valide : « Livre créé ! »"],
       run=RUN("react", entry="App.jsx", api=r"""
__api["POST /api/livres"] = (p, body) => (body && body.titre && body.titre.trim()) ? [201, { id: 7, titre: body.titre }] : [422, { title: 'Validation Failed', violations: [{ propertyPath: 'titre', title: 'Le titre est obligatoire.' }] }];
""", tests=r"""
await waitFor(() => $('form'), 2000);
await submit('form');
await waitFor(() => $('.erreur') || $('.ok'), 3000);
assert(!$('.ok'), 'Titre vide : PAS de « Livre créé ! »');
assert($('.erreur') && $('.erreur').textContent.includes('obligatoire'), 'Titre vide : le message de violation s\'affiche');
await type('input[name=titre]', 'Dune');
await submit('form');
await waitFor(() => $('.ok'), 3000);
assert($('.ok').textContent === 'Livre créé !', 'Titre valide : « Livre créé ! »');
assert(!$('.erreur'), 'Les erreurs précédentes ont disparu');
assert($('input[name=titre]').value === '', 'Le champ est vidé');
""")),
    TD(3, "Les vieux résultats écrasent les nouveaux",
       "Recherche « en direct » : quand on tape vite « d » puis « du », la liste affiche **parfois** les résultats de « d ». Le bug n'arrive pas à chaque fois : c'est un problème de **timing** (la réponse de « d » est plus lente). " + METHODE,
       ["Reproduis avec la sortie : dans quel ordre les réponses arrivent-elles ?",
        "Corrige l'effet pour qu'une réponse obsolète ne soit jamais affichée",
        "Après avoir tapé « du », la liste affiche uniquement `Dune` et le reste"],
       [F("App.jsx", "jsx", r"""
import { useEffect, useState } from 'react';

export default function App() {
  const [q, setQ] = useState('');
  const [livres, setLivres] = useState([]);

  useEffect(() => {
    fetch('/api/livres?q=' + encodeURIComponent(q))
      .then((r) => r.json())
      .then(setLivres);
  }, [q]);

  return (
    <div>
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Rechercher" />
      <ul>{livres.map((l) => <li key={l.id}>{l.titre}</li>)}</ul>
    </div>
  );
}
""")],
       ["Ajoute un `console.log('réponse pour', q)` dans le `.then` : « d » arrive après « du ».",
        "La fonction de nettoyage de l'effet (`return () => …`) est appelée quand `q` change.",
        "`const ctrl = new AbortController();` + `{ signal: ctrl.signal }` + `return () => ctrl.abort();` (et ignorer `AbortError`). Ou un drapeau `let actif = true; … if (actif) setLivres(d); return () => { actif = false; };`."],
       [F("App.jsx", "jsx", r"""
import { useEffect, useState } from 'react';

export default function App() {
  const [q, setQ] = useState('');
  const [livres, setLivres] = useState([]);

  useEffect(() => {
    const ctrl = new AbortController();
    fetch('/api/livres?q=' + encodeURIComponent(q), { signal: ctrl.signal })
      .then((r) => r.json())
      .then(setLivres)
      .catch((e) => { if (e.name !== 'AbortError') console.error(e); });
    return () => ctrl.abort();
  }, [q]);

  return (
    <div>
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Rechercher" />
      <ul>{livres.map((l) => <li key={l.id}>{l.titre}</li>)}</ul>
    </div>
  );
}
""")],
       ["La liste finale correspond toujours à la dernière recherche"],
       run=RUN("react", entry="App.jsx", api=r"""
const LIVRES = [{ id: 1, titre: 'Dune' }, { id: 2, titre: 'Le Messie de Dune' }, { id: 3, titre: 'Fondation' }, { id: 4, titre: 'Hypérion' }, { id: 5, titre: 'Le Désert des Tartares' }];
__api["GET /api/livres"] = async (p) => {
  const q = (p.q || '').toLowerCase();
  await new Promise((r) => setTimeout(r, q === 'd' ? 900 : 50));   // « d » répond lentement
  return LIVRES.filter((l) => l.titre.toLowerCase().includes(q));
};
""", tests=r"""
await waitFor(() => $$('li').length === 5, 3000);
const input = $('input');
await type(input, 'd');
await sleep(30);
await type(input, 'du');
await sleep(2200);
const titres = $$('li').map((l) => l.textContent);
assert(titres.length === 2 && titres.every((t) => t.toLowerCase().includes('du')), 'Après « du » : seulement Dune et Le Messie de Dune (affiché : ' + titres.join(', ') + ')');
""")),
  ])

# =========================================================================== Next.js
NSIM = " Le bouton Exécuter utilise le **Next.js simulé** de l'atelier ; les tests naviguent avec `next.render('/url')`."

def NRUN(tests, start="/", api=None):
    return RUN("next", tests=tests, entry="app/page.tsx", start=start, api=api)

ROOT = F("app/layout.tsx", "tsx", r"""
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <div className="site">{children}</div>;
}
""")

nextjs = DM("dbg-next", "Erreurs Next.js", 20,
  "Reconnaître les erreurs propres à Next.js : frontière serveur/client, params asynchrones, cache qui ne se met pas à jour.",
  "Next.js mélange du code serveur et du code client : beaucoup d'erreurs viennent d'un code exécuté du mauvais côté, ou d'un cache qu'on n'a pas invalidé.",
  ["Lire l'erreur : elle cite souvent **le fichier** et le **côté** (serveur/client)", "Se demander : ce code s'exécute-t-il sur le **serveur** ou dans le **navigateur** ?",
   "Vérifier la version : `params` et `searchParams` sont des **promesses** depuis Next 15", "Données pas à jour : chercher le **cache** (fetch, revalidate) et ce qui l'invalide"],
  ["Hook (`useState`, `useEffect`) dans un Server Component : il faut un composant `'use client'`.",
   "`params.slug` vaut `undefined` : `params` est une promesse, il faut `await params`.",
   "Après une Server Action, la page ne change pas : `revalidatePath` du **bon chemin** (ou `revalidateTag`) manquant.",
   "`window is not defined` / `localStorage is not defined` : code navigateur exécuté sur le serveur.",
   "Les logs d'un Server Component apparaissent dans le **terminal** de `next dev`, pas dans la console du navigateur."],
  ["Mettre `'use client'` sur toute la page pour faire taire une erreur.", "Désactiver le cache partout au lieu d'invalider le bon chemin.", "Chercher les `console.log` serveur dans le navigateur."],
  [Q("`useState` dans `app/page.tsx` (sans directive) provoque…", ["rien", "une erreur : c'est un Server Component", "un warning", "un rendu infini"], 1, "Les hooks n'existent que dans les Client Components."),
   Q("Next 15 : `<h1>{params.slug}</h1>` affiche…", ["le slug", "rien : params est une promesse", "une erreur 404", "« slug »"], 1, "Il faut `const { slug } = await params`."),
   Q("Un `console.log` dans un Server Component apparaît…", ["dans la console du navigateur", "dans le terminal de next dev", "nulle part", "dans les deux"], 1, "Le code serveur s'exécute dans le process Node.")],
  prereq=[
    P("Server Component", "Composant exécuté sur le serveur (par défaut dans `app/`). Peut être `async`, lire des données ; pas de hooks ni d'événements."),
    P("Client Component", "Fichier qui commence par `'use client'` : envoyé au navigateur, peut utiliser `useState`, `onClick`…"),
    P("Promesse", "Valeur « pas encore disponible ». On l'attend avec `await` dans une fonction `async`."),
    P("Revalider", "Dire à Next qu'une page ou une donnée en cache est périmée, pour qu'elle soit recalculée."),
  ],
  diagram=D(
    nodes=[
      N("s", 0, 0, "Serveur", "async, données, secrets", kind="box", color="accent"),
      N("c", 1, 0, "Client ('use client')", "hooks, onClick, window", kind="box", color="warn"),
      N("e1", 0, 1, "useState côté serveur", "→ composant client", kind="pill", color="bad"),
      N("e2", 1, 1, "window côté serveur", "→ code dans un effet client", kind="pill", color="bad"),
      N("e3", 2, 1, "Page pas à jour", "→ revalidatePath", kind="pill", color="bad"),
      N("k", 2, 0, "Cache", "fetch, pages", kind="db", color="muted"),
    ],
    edges=[E("s", "e1"), E("c", "e2"), E("k", "e3")],
    caption="Trois familles d'erreurs Next.js : du code client sur le serveur, du code serveur côté client, et un cache qu'on n'a pas invalidé."),
  lessons=[
    L("Serveur ou client ? La question à se poser", r"""
Pour chaque erreur Next.js, demande-toi **où** le code s'exécute :

- Un fichier de `app/` **sans** `'use client'` est un **Server Component** : il tourne sur le serveur (Node). Pas de `useState`, pas de `onClick`, pas de `window`.
- Un fichier qui commence par `'use client'` est envoyé au navigateur (mais il est **aussi** rendu une première fois sur le serveur : `window` n'y existe pas pendant ce premier rendu, d'où `useEffect`).

Erreurs typiques :

| Message | Cause | Correction |
|---|---|---|
| `useState only works in Client Components` | hook dans un Server Component | extraire la partie interactive dans un composant `'use client'` |
| `Event handlers cannot be passed to Client Component props` / `Functions cannot be passed…` | une fonction passée du serveur au client | mettre le handler **dans** le composant client |
| `window is not defined` | code navigateur exécuté pendant le rendu serveur | le déplacer dans un `useEffect` |
| `async/await is not yet supported in Client Components` | composant client `async` | charger côté serveur, passer les données en props |

Où lire les logs : `console.log` d'un Server Component → **terminal** de `next dev` ; d'un Client Component → console du **navigateur**.
"""),
    L("Next 15 : params et searchParams sont des promesses", r"""
Depuis Next 15, `params` (segments dynamiques) et `searchParams` (query string) sont des **promesses** :

```tsx
// ✗ Next 14 : marchait ; Next 15 : params.slug vaut undefined (avertissement dans le terminal)
export default function Page({ params }) {
  return <h1>{params.slug}</h1>;
}

// ✓
export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <h1>{slug}</h1>;
}
```

Si un tutoriel ou une réponse trouvée en ligne date d'avant Next 15, c'est un piège fréquent : vérifie la version dans `package.json`.
"""),
    L("La page ne se met pas à jour", r"""
Après une **Server Action** (ajout, modification), Next ne recalcule une page en cache que si on le lui dit :

```ts
'use server';
export async function ajouterProduit(formData: FormData) {
  await db.produit.create({ … });
  revalidatePath('/produits');        // le chemin de la page QUI AFFICHE la liste
}
```

Les causes classiques :

- `revalidatePath` **oublié** ;
- `revalidatePath` du **mauvais chemin** (la page du formulaire, pas celle de la liste ; une faute de frappe) ;
- la liste vient d'un `fetch` étiqueté (`next: { tags: ['produits'] }`) : il faut `revalidateTag('produits')`.

Pour vérifier : le terminal de `next dev` indique si une page est servie depuis le cache ; en dernier recours, `export const dynamic = 'force-dynamic'` sur la page confirme que c'est bien un problème de cache (à ne pas laisser comme « correction »).
"""),
  ],
  recap=["Toujours se demander : serveur ou client ?",
         "Hooks et événements → composant `'use client'`, le plus bas possible.",
         "Next 15 : `await params`, `await searchParams`.",
         "Après une écriture : `revalidatePath` du chemin qui **affiche** la donnée, ou `revalidateTag`.",
         "Logs serveur : dans le terminal, pas dans le navigateur."],
  example=F("terminal", "bash", r"""
$ npm run dev
 ⨯ ./app/produits/page.tsx
Error: You're importing a component that needs `useState`. This React Hook only works in a
Client Component. To fix, mark the file (or its parent) with the "use client" directive.

# Lecture : app/produits/page.tsx est un Server Component (pas de 'use client').
# Bonne correction : garder la page côté serveur (elle charge les produits),
# et déplacer le filtre interactif dans app/produits/Filtre.tsx qui commence par 'use client'.
"""),
  notes=["Le message cite le fichier fautif.", "La solution proposée (`use client` sur le fichier) n'est pas toujours la meilleure : on garde la page serveur.", "On extrait la petite partie interactive."],
  tds=[
    TD(1, "useState dans un Server Component",
       "La page `/produits` plante : *<ProduitsPage> utilise un hook React (useState…) alors que c'est un Server Component*. La page charge les produits (`async`) **et** a un filtre « en stock seulement ». Corrige sans transformer toute la page en composant client." + NSIM,
       ["Lance et lis l'erreur : quel composant, quel hook ?",
        "La page reste un Server Component `async` qui charge les produits",
        "Le filtre devient un composant client `Filtre` (dans son propre fichier) qui reçoit les produits en props",
        "Cocher « en stock seulement » masque les produits à 0"],
       [F("lib/produits.ts", "ts", r"""
export type Produit = { id: string; nom: string; stock: number };
export async function getProduits(): Promise<Produit[]> {
  await new Promise((r) => setTimeout(r, 20));
  return [
    { id: 'clavier', nom: 'Clavier', stock: 12 },
    { id: 'souris', nom: 'Souris', stock: 0 },
    { id: 'ecran', nom: 'Écran', stock: 4 },
  ];
}
"""), ROOT, F("app/page.tsx", "tsx", "export default function Accueil() {\n  return <h1>Accueil</h1>;\n}\n"),
        F("app/produits/page.tsx", "tsx", r"""
import { useState } from 'react';
import { getProduits } from '@/lib/produits';

export default async function ProduitsPage() {
  const produits = await getProduits();
  const [enStock, setEnStock] = useState(false);
  const visibles = enStock ? produits.filter((p) => p.stock > 0) : produits;

  return (
    <div>
      <label><input type="checkbox" checked={enStock} onChange={(e) => setEnStock(e.target.checked)} /> En stock seulement</label>
      <ul>{visibles.map((p) => <li key={p.id}>{p.nom}</li>)}</ul>
    </div>
  );
}
"""), F("app/produits/Filtre.tsx", "tsx", r"""
// à toi
""")],
       ["La page ne peut pas être à la fois `async` (serveur) et utiliser `useState` (client).",
        "`Filtre.tsx` commence par `'use client'` et reçoit `produits` en prop.",
        "La page devient : `const produits = await getProduits(); return <Filtre produits={produits} />;`"],
       [F("app/produits/page.tsx", "tsx", r"""
import { getProduits } from '@/lib/produits';
import Filtre from './Filtre';

export default async function ProduitsPage() {
  const produits = await getProduits();
  return <Filtre produits={produits} />;
}
"""), F("app/produits/Filtre.tsx", "tsx", r"""
'use client';
import { useState } from 'react';

type Produit = { id: string; nom: string; stock: number };

export default function Filtre({ produits }: { produits: Produit[] }) {
  const [enStock, setEnStock] = useState(false);
  const visibles = enStock ? produits.filter((p) => p.stock > 0) : produits;
  return (
    <div>
      <label><input type="checkbox" checked={enStock} onChange={(e) => setEnStock(e.target.checked)} /> En stock seulement</label>
      <ul>{visibles.map((p) => <li key={p.id}>{p.nom}</li>)}</ul>
    </div>
  );
}
""")],
       ["La page reste serveur", "Le filtre marche"],
       run=NRUN(r"""
assert.equal(await next.render('/produits'), 200, '/produits → 200 (plus d\'erreur)');
assert.equal($$('li').length, 3, '3 produits affichés');
await click('input[type=checkbox]');
assert.equal($$('li').length, 2, 'En stock seulement : 2 produits');
assert(!/^\s*['"]use client/.test(source('app/produits/page.tsx')), 'La page reste un Server Component');
assert(/^\s*['"]use client/.test(source('app/produits/Filtre.tsx')), 'Filtre.tsx est un Client Component');
""", start="/produits")),
    TD(2, "Le titre est vide (Next 15)",
       "Cette page vient d'un tutoriel Next 14. Sur ton projet en Next 15, `/blog/dto` affiche un titre **vide** et la recherche ne filtre rien. Pas d'erreur dans le navigateur, seulement un avertissement dans le terminal." + NSIM,
       ["Lance : que vaut `params.slug` ? (ajoute un `console.log`)",
        "`/blog/[slug]` affiche `Article : dto` dans un `<h1>`",
        "`/blog?tag=php` affiche `Tag : php` dans un `<p>` ; sans tag : `Tous les articles`"],
       [ROOT, F("app/page.tsx", "tsx", "export default function Accueil() {\n  return <h1>Accueil</h1>;\n}\n"),
        F("app/blog/[slug]/page.tsx", "tsx", r"""
export default function Article({ params }: { params: any }) {
  return <h1>Article : {params.slug}</h1>;
}
"""), F("app/blog/page.tsx", "tsx", r"""
export default function Blog({ searchParams }: { searchParams: any }) {
  return <p>{searchParams.tag ? 'Tag : ' + searchParams.tag : 'Tous les articles'}</p>;
}
""")],
       ["Depuis Next 15, `params` et `searchParams` sont des **promesses**.",
        "La page devient `async` et fait `const { slug } = await params;`.",
        "Même chose pour `const { tag } = await searchParams;`."],
       [F("app/blog/[slug]/page.tsx", "tsx", r"""
export default async function Article({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <h1>Article : {slug}</h1>;
}
"""), F("app/blog/page.tsx", "tsx", r"""
export default async function Blog({ searchParams }: { searchParams: Promise<{ tag?: string }> }) {
  const { tag } = await searchParams;
  return <p>{tag ? 'Tag : ' + tag : 'Tous les articles'}</p>;
}
""")],
       ["Le slug s'affiche", "Le tag s'affiche"],
       run=NRUN(r"""
await next.render('/blog/dto');
assert.equal($('h1').textContent, 'Article : dto', '/blog/dto : « Article : dto »');
await next.render('/blog?tag=php');
assert.equal($('p').textContent, 'Tag : php', '/blog?tag=php : « Tag : php »');
await next.render('/blog');
assert.equal($('p').textContent, 'Tous les articles', '/blog : « Tous les articles »');
""", start="/blog/dto")),
    TD(3, "Le nouveau produit n'apparaît pas",
       "Sur `/produits`, le formulaire ajoute bien le produit (il est en base), mais la liste **ne change pas** : il faut attendre ou relancer le serveur. Trouve pourquoi le cache n'est pas invalidé." + NSIM,
       ["Lance, ajoute un produit, observe la liste",
        "Lis la Server Action : quel chemin est revalidé ? Quelle page affiche la liste ?",
        "Après ajout, la liste de `/produits` montre le nouveau produit sans recharger",
        "Ne désactive pas le cache (`force-cache` reste sur le fetch)"],
       [F("lib/db.ts", "ts", r"""
export const db = { produits: ['Clavier', 'Souris'] };
// Fausse API de l'atelier : https://api.exemple.com/produits renvoie cette « base »
(window as any).__db = db;
"""), ROOT, F("app/page.tsx", "tsx", "export default function Accueil() {\n  return <h1>Accueil</h1>;\n}\n"),
        F("app/produits/actions.ts", "ts", r"""
'use server';
import { revalidatePath } from 'next/cache';
import { db } from '@/lib/db';

export async function ajouterProduit(formData: FormData) {
  const nom = String(formData.get('nom') ?? '').trim();
  if (!nom) return;
  db.produits.push(nom);
  revalidatePath('/produit');
}
"""), F("app/produits/page.tsx", "tsx", r"""
import { ajouterProduit } from './actions';

async function getProduits(): Promise<string[]> {
  return fetch('https://api.exemple.com/produits', { cache: 'force-cache' }).then((r) => r.json());
}

export default async function ProduitsPage() {
  const produits = await getProduits();
  return (
    <div>
      <ul>{produits.map((p) => <li key={p}>{p}</li>)}</ul>
      <form action={ajouterProduit}>
        <input name="nom" />
        <button>Ajouter</button>
      </form>
    </div>
  );
}
""")],
       ["La liste vient d'un `fetch` en `force-cache` : elle reste en cache tant qu'on ne l'invalide pas.",
        "`revalidatePath('/produit')` : il manque un **s**. La page s'appelle `/produits`.",
        "Corrige le chemin (ou utilise un tag : `next: { tags: ['produits'] }` + `revalidateTag('produits')`)."],
       [F("app/produits/actions.ts", "ts", r"""
'use server';
import { revalidatePath } from 'next/cache';
import { db } from '@/lib/db';

export async function ajouterProduit(formData: FormData) {
  const nom = String(formData.get('nom') ?? '').trim();
  if (!nom) return;
  db.produits.push(nom);
  revalidatePath('/produits');
}
""")],
       ["Le nouveau produit apparaît après l'ajout", "Le fetch reste en cache"],
       run=NRUN(r"""
await next.render('/produits');
assert.equal($$('li').length, 2, '2 produits au départ');
await type('input[name=nom]', 'Écran');
await submit('form');
await waitFor(() => $$('li').length === 3, 3000);
assert($$('li')[2].textContent === 'Écran', 'Le nouveau produit apparaît sans recharger');
assert(/force-cache/.test(source('app/produits/page.tsx')), 'Le cache est conservé (force-cache)');
""", start="/produits", api=r"""
__api["GET /produits"] = () => window.__db ? window.__db.produits : ['Clavier', 'Souris'];
""")),
  ])

# =========================================================================== Git
GSIM = (" Le bouton **Lancer les commandes** exécute ton script dans le **Git simulé** (dépôt recréé à chaque fois). "
        "Lance d'abord seulement `git status` / `git log --oneline --graph --all` pour lire la situation, puis écris la suite.")

def GRUN(tests, setup):
    return RUN("git", tests=tests, entry="commandes.sh", start=setup)

def SH(code):
    return [F("commandes.sh", "bash", code)]

# (les TD Git sont assemblés ci-dessous pour garder la lisibilité)
GIT_TD1 = TD(1, "Conflit pendant git pull --rebase",
   "Tu as corrigé l'arrondi des prix et tu veux pousser. Refus : *fetch first*. Après `git pull --rebase`, Git s'arrête sur un **conflit** dans `prix.js` : Léa a modifié la même ligne. Termine proprement et pousse." + GSIM,
   ["Lis le refus, puis récupère le travail de Léa en gardant un historique linéaire",
    "Résous `prix.js` pour obtenir : `export const ttc = (ht) => Math.round(ht * (1 + 0.2) * 100) / 100;` (ta correction **et** l'écriture de Léa)",
    "Termine le rebase et pousse",
    "Aucun `--force`"],
   SH(r"""
git status
git log --oneline --graph --all
git push
# à toi
"""),
   ["`git pull --rebase` → `CONFLICT` : c'est normal, Git attend que tu choisisses.",
    "`echo \"export const ttc = (ht) => Math.round(ht * (1 + 0.2) * 100) / 100;\" > prix.js`",
    "`git add prix.js`, `git rebase --continue`, `git push`."],
   SH(r"""
git push
git pull --rebase
cat prix.js
echo "export const ttc = (ht) => Math.round(ht * (1 + 0.2) * 100) / 100;" > prix.js
git add prix.js
git rebase --continue
git push
git log --oneline --graph --all
"""),
   ["Plus de rebase en cours", "Ton commit est sur GitHub, au-dessus de celui de Léa"],
   run=GRUN(r"""
assert.equal(git.op, null, 'Le rebase est terminé');
assert(git.transcript.some((t) => /CONFLICT/.test(t.out)), 'Le conflit a bien eu lieu');
assert.equal(git.at('main', 'prix.js'), 'export const ttc = (ht) => Math.round(ht * (1 + 0.2) * 100) / 100;\n', 'prix.js combine les deux changements, sans marqueurs');
assert.equal(git.rev('main'), git.remote.branches.main, 'Poussé : main local = main sur GitHub');
assert.equal(git.merges('main'), 0, 'Historique linéaire');
assert.equal(git.remoteLog('main')[1], 'refactor: taux de TVA explicite', 'Le commit de Léa est juste sous le tien');
assert(!git.used(/--force|push -f/), 'Aucun --force');
""", r"""
git.sh('git init');
git.write('prix.js', 'export const ttc = (ht) => ht * 1.2;\n');
git.sh('git add .\ngit commit -m "feat: calcul du TTC"');
git.cloneRemote();
git.write('prix.js', 'export const ttc = (ht) => Math.round(ht * 1.2 * 100) / 100;\n');
git.sh('git commit -am "fix: arrondit les prix au centime"');
git.remoteCommit('main', 'refactor: taux de TVA explicite', { 'prix.js': 'export const ttc = (ht) => ht * (1 + 0.2);\n' }, 'Léa');
"""))

GIT_TD2 = TD(2, "Push refusé après ton propre rebase",
   "Tu as rebasé ta branche `feat/export` (déjà poussée) sur le dernier `main` : l'historique est propre en local. Mais `git push` est refusé (*non-fast-forward*). Un collègue te conseille `git pull`… Ne fais pas ça : lis la situation et pousse correctement." + GSIM,
   ["Regarde le graphe : `feat/export` et `origin/feat/export` ont les **mêmes** commits, en deux versions",
    "Pousse ta version rebasée **sans risquer** d'écraser un travail inconnu",
    "Sur GitHub, `feat/export` doit avoir exactement tes 2 commits au-dessus de `main`, sans doublon ni commit de fusion"],
   SH(r"""
git status
git log --oneline --graph --all
git push
# à toi
"""),
   ["`git pull` fusionnerait les anciennes et les nouvelles copies de tes commits : 4 commits au lieu de 2, plus une fusion.",
    "L'historique a été réécrit volontairement : il faut forcer, **prudemment**.",
    "`git push --force-with-lease`."],
   SH(r"""
git log --oneline --graph --all
git push
git push --force-with-lease
git log --oneline --graph --all
"""),
   ["Pas de doublon", "`--force-with-lease`, pas `--force`"],
   run=GRUN(r"""
assert.equal(git.remote.branches['feat/export'], git.rev('feat/export'), 'GitHub a ta version rebasée');
const L = git.remoteLog('feat/export');
assert.equal(L.filter((m) => m === 'feat(export): exporte en CSV').length, 1, 'Pas de doublon de commit');
assert.equal(git.merges('feat/export'), 0, 'Aucun commit de fusion');
assert(git.isAncestor('main', 'feat/export'), 'La branche est au-dessus du dernier main');
assert(git.used(/--force-with-lease/), 'Poussé avec --force-with-lease');
assert(!git.used(/--force(?!-with-lease)|push -f|git pull(?! --rebase)/), 'Ni --force simple, ni git pull');
""", r"""
git.sh('git init');
git.write('app.js', 'export const app = 1;\n');
git.sh('git add .\ngit commit -m "chore: initialise"');
git.cloneRemote();
git.sh('git switch -c feat/export');
git.write('export.js', 'export const exporter = () => {};\n');
git.sh('git add .\ngit commit -m "feat(export): ajoute l\'export"');
git.write('export.js', 'export const exporter = (l) => l.join(";");\n');
git.sh('git commit -am "feat(export): exporte en CSV"\ngit push -u origin feat/export\ngit switch main');
git.remoteCommit('main', 'feat: ajoute la recherche', { 'recherche.js': 'export const r = 1;\n' }, 'Léa');
git.sh('git pull\ngit switch feat/export\ngit rebase main');
"""))

GIT_TD3 = TD(3, "Commits faits sur la mauvaise branche",
   "Tu as fait 2 commits d'export **directement sur `main`** (pas encore poussés) au lieu d'une branche `feat/export`. Déplace-les sur la bonne branche, et remets `main` comme sur GitHub. Rien ne doit être perdu." + GSIM,
   ["Crée `feat/export` qui contient tes 2 commits",
    "Remets `main` exactement sur `origin/main`",
    "Termine sur `feat/export`, dossier propre",
    "Aucun commit perdu, rien poussé sur `main`"],
   SH(r"""
git status
git log --oneline --graph --all
# à toi
"""),
   ["L'ordre compte : d'abord poser l'étiquette `feat/export` sur tes commits.",
    "`git branch feat/export` puis `git reset --hard origin/main` (sur main).",
    "`git switch feat/export` pour continuer."],
   SH(r"""
git branch feat/export
git reset --hard origin/main
git switch feat/export
git log --oneline --graph --all
"""),
   ["`main` = `origin/main`", "`feat/export` a les 2 commits"],
   run=GRUN(r"""
assert.equal(git.rev('main'), git.rev('origin/main'), 'main est revenu sur origin/main');
assert(git.branches['feat/export'], 'La branche feat/export existe');
assert.equal(JSON.stringify(git.range('main', 'feat/export')), JSON.stringify(['feat(export): ajoute l\'export', 'feat(export): exporte en CSV']), 'feat/export contient tes 2 commits');
assert.equal(git.branch, 'feat/export', 'Tu es sur feat/export');
assert(git.clean(), 'Dossier propre');
assert.equal(git.remoteLog('main')[0], 'chore: initialise', 'Rien n\'a été poussé sur main');
""", r"""
git.sh('git init');
git.write('app.js', 'export const app = 1;\n');
git.sh('git add .\ngit commit -m "chore: initialise"');
git.cloneRemote();
git.write('export.js', 'export const exporter = () => {};\n');
git.sh('git add .\ngit commit -m "feat(export): ajoute l\'export"');
git.write('export.js', 'export const exporter = (l) => l.join(";");\n');
git.sh('git commit -am "feat(export): exporte en CSV"');
"""))

git = DM("dbg-git", "Erreurs Git", 20,
  "Lire les messages de Git et choisir la bonne commande pour s'en sortir, sans perdre de travail ni écraser celui des autres.",
  "Les messages de Git disent presque toujours quoi faire (les lignes `hint:`). Les lire évite les réflexes dangereux comme `--force` ou supprimer le dossier.",
  ["Lire le message **et** les lignes `hint:`", "Regarder la situation : `git status`, `git log --oneline --graph --all`",
   "Choisir la commande qui **n'écrase rien** (pull --rebase, --force-with-lease, branch avant reset)", "Vérifier le résultat dans le graphe"],
  ["`rejected (fetch first)` : le distant a des commits que tu n'as pas → `git pull --rebase`, puis push.",
   "`rejected (non-fast-forward)` après **ton** rebase : `git push --force-with-lease`, surtout pas `git pull` (doublons).",
   "`CONFLICT` pendant un rebase : résoudre, `git add`, `git rebase --continue`.",
   "Commits faits sur la mauvaise branche : créer la bonne branche **là**, puis ramener l'autre en arrière.",
   "En cas de doute : `git status` dit toujours dans quel état tu es et quoi faire."],
  ["`git push --force` pour « forcer » après un refus.", "`git pull` après avoir rebasé sa branche déjà poussée.", "Supprimer le dossier et recloner."],
  [Q("Push refusé avec « fetch first »…", ["git push --force", "git pull --rebase puis git push", "supprimer la branche", "git reset --hard"], 1, "Quelqu'un a poussé : on intègre son travail avant de pousser."),
   Q("Tu viens de rebaser TA branche déjà poussée ; le push est refusé. Que faire ?", ["git pull", "git push --force-with-lease", "git merge origin/ta-branche", "rien"], 1, "git pull mélangerait anciennes et nouvelles copies des commits."),
   Q("Deux commits faits sur main au lieu d'une branche (pas poussés). D'abord ?", ["git reset --hard", "git branch nouvelle-branche (pour les garder)", "git push", "git revert"], 1, "On pose d'abord une étiquette sur ces commits, ensuite on peut reculer main.")],
  prereq=[
    P("`hint:`", "Les lignes de conseil que Git ajoute sous ses erreurs. Elles proposent souvent la bonne commande."),
    P("Fast-forward", "Avancer une branche sans fusion. Un push est refusé quand il n'est pas fast-forward (le distant a autre chose)."),
    P("`origin/main`", "Ta copie locale de ce que tu sais de `main` sur GitHub ; mise à jour par `git fetch`."),
    P("Réécrire l'historique", "rebase, amend, reset : les commits changent d'identifiant. Il faut alors forcer le push, prudemment."),
  ],
  diagram=D(
    nodes=[
      N("r1", 0, 0, "rejected (fetch first)", "message", kind="doc", color="bad"),
      N("c1", 1, 0, "Le distant a avancé", "cause", kind="note"),
      N("f1", 2, 0, "pull --rebase, push", "remède", kind="pill", color="good"),
      N("r2", 0, 1, "rejected après rebase", "message", kind="doc", color="bad"),
      N("c2", 1, 1, "Historique réécrit", "cause", kind="note"),
      N("f2", 2, 1, "push --force-with-lease", "jamais git pull", kind="pill", color="good"),
      N("r3", 0, 2, "Mauvaise branche", "pas encore poussé", kind="doc", color="warn"),
      N("c3", 1, 2, "Commits au mauvais endroit", "cause", kind="note"),
      N("f3", 2, 2, "branch, puis reset", "--hard origin/main", kind="pill", color="good"),
    ],
    edges=[E("r1", "c1"), E("c1", "f1"), E("r2", "c2"), E("c2", "f2"), E("r3", "c3"), E("c3", "f3")],
    caption="Trois situations qui font paniquer, et la commande qui n'écrase le travail de personne."),
  lessons=[
    L("Lire un refus de push", r"""
```
 ! [rejected]        main -> main (fetch first)
error: failed to push some refs to 'github.com:toi/projet.git'
hint: Updates were rejected because the remote contains work that you do not
hint: have locally. … You may want to first integrate the remote changes
hint: (e.g., 'git pull ...') before pushing again.
```

Deux variantes à distinguer :

- **`fetch first`** : quelqu'un a poussé des commits que tu n'as pas. → `git pull --rebase` (récupère et rejoue tes commits par-dessus), puis `git push`.
- **`non-fast-forward`** alors que tu viens de **rebaser ou amender** ta propre branche : le distant a les **anciennes** versions de tes commits. → `git push --force-with-lease`. Un `git pull` ici fusionnerait les anciennes et les nouvelles copies : historique en double.

`--force-with-lease` refuse d'écraser si quelqu'un a poussé entre-temps ; `--force` écrase toujours. On n'utilise jamais `--force` seul.
"""),
    L("Conflit pendant un pull --rebase", r"""
```
CONFLICT (content): Merge conflict in prix.js
error: could not apply 3f2c1d0... fix: arrondit les prix
hint: Resolve all conflicts manually, mark them as resolved with
hint: "git add/rm <conflicted_files>", then run "git rebase --continue".
```

Pas de panique, Git attend :

1. `git status` : liste les fichiers en conflit (« both modified »).
2. Ouvrir le fichier, choisir ou combiner les deux versions, **retirer les marqueurs** `<<<<<<<`, `=======`, `>>>>>>>`.
3. `git add prix.js`, puis `git rebase --continue`.
4. `git push`.

À tout moment : `git rebase --abort` remet tout comme avant le pull.

Rappel : pendant un rebase, `HEAD` dans les marqueurs = la version **distante** ; l'autre côté = **ton** commit.
"""),
    L("« J'ai commité au mauvais endroit »", r"""
Tu as fait 2 commits sur `main` au lieu de `feat/export` (pas encore poussés). Les commits sont bons, ils sont juste au mauvais endroit :

```bash
git branch feat/export          # 1. une étiquette sur ces commits : ils sont en sécurité
git reset --hard origin/main    # 2. main revient là où il était sur GitHub
git switch feat/export          # 3. on continue sur la bonne branche
```

L'ordre est essentiel : **d'abord** la branche (sinon le reset ferait « disparaître » les commits ; le reflog les retrouverait, mais autant ne pas en arriver là).

Autres messages fréquents :

| Message | Signification |
|---|---|
| `Your local changes would be overwritten by checkout` | modifications non commitées qui gênent : `git stash` ou commit |
| `You are in 'detached HEAD' state` | tu es sur un commit, pas une branche : `git switch -c nom` pour garder ce que tu fais |
| `There is no tracking information for the current branch` | branche jamais poussée : `git push -u origin nom` |
| `Need to specify how to reconcile divergent branches` | choisir : `git pull --rebase` (ou `--no-rebase`) |
"""),
  ],
  recap=["Lire le message ET les `hint:`.",
         "`fetch first` → `git pull --rebase` puis push.",
         "Refus après ton propre rebase → `--force-with-lease`, jamais `git pull`.",
         "Conflit en rebase : résoudre → `git add` → `git rebase --continue`.",
         "Mauvaise branche : `git branch` d'abord, `git reset --hard origin/main` ensuite."],
  example=F("terminal", "bash", r"""
$ git push
 ! [rejected]        main -> main (fetch first)
hint: Updates were rejected because the remote contains work that you do not have locally.

$ git pull --rebase          # récupère le commit du collègue, rejoue le mien par-dessus
Successfully rebased and updated refs/heads/main.

$ git push
   4c2a1b0..9e8f7d6  main -> main
"""),
  notes=["« fetch first » : le distant a avancé.", "`pull --rebase` garde un historique linéaire.", "Aucun `--force`."],
  tds=[GIT_TD1, GIT_TD2, GIT_TD3])

MODULES = [php, doctrine, symfony, react, data, nextjs, git]

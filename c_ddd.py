from common import V2, P, L, D, N, E, LANE, F, TD, RUN
from c_ddd_v1 import MODULES as V1

v1 = {m["id"]: m for m in V1}

SIM = "Le bouton Exécuter lance PHP 8.4 dans ton navigateur ; les fichiers sont réunis dans l'ordre des onglets. Les tests appellent tes classes directement."

MONEY = F("Money.php", "php", r"""
<?php
declare(strict_types=1);

// Fourni : value object Money (montants en centimes, jamais de float)
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

    public static function zero(): self
    {
        return new self(0, 'EUR');
    }

    public function plus(Money $autre): self
    {
        $this->memeDevise($autre);
        return new self($this->centimes + $autre->centimes, $this->devise);
    }

    public function multiplier(int $n): self
    {
        return new self($this->centimes * $n, $this->devise);
    }

    public function depasse(Money $autre): bool
    {
        $this->memeDevise($autre);
        return $this->centimes > $autre->centimes;
    }

    public function equals(Money $autre): bool
    {
        return $this->centimes === $autre->centimes && $this->devise === $autre->devise;
    }

    private function memeDevise(Money $autre): void
    {
        if ($autre->devise !== $this->devise) {
            throw new LogicException('Devises différentes');
        }
    }
}
""")

# ============================================================ 1. Langage
langage = V2(v1["ddd-langage"],
  prereq=[
    P("Domaine", "Le métier que le logiciel sert : une salle de sport, une boutique, une banque. Ses règles existent avant le code."),
    P("Expert métier", "La personne qui connaît les règles (gérant, comptable, coach). Le code doit parler **sa** langue."),
    P("Langage ubiquitaire", "Le vocabulaire commun, fixé avec les experts, utilisé **partout** : dans les discussions, les tickets, les noms de classes et de méthodes."),
    P("Bounded context", "Une frontière à l'intérieur de laquelle chaque mot a **un seul** sens précis, et qui a son propre modèle (ses propres classes)."),
    P("Événement de domaine", "Un fait métier passé, nommé au passé : `AbonnementResilie`, `ReservationConfirmee`. Il sert à prévenir les autres contextes."),
  ],
  diagram=D(
    nodes=[
      N("fa", 0, 0, "Facturation", "Membre = qui paie\nabonnement, IBAN", kind="box", color="accent"),
      N("pl", 1, 0, "Planning", "Membre = participant\ncours, réservations", kind="box", color="good"),
      N("ac", 2, 0, "Accès", "Membre = badge\nhoraires, blocage", kind="box", color="warn"),
      N("ev", 0, 1, "AbonnementResilie", "événement + membreId", kind="note", color="bad"),
    ],
    edges=[E("fa", "ev", "publie"), E("ev", "ac", "bloque le badge")],
    lanes=[LANE("Salle de sport", 0, 2, "muted")],
    caption="Le même mot « Membre » a trois sens, donc trois modèles. Les contextes ne partagent pas leurs classes : ils échangent des identifiants et des événements."),
  lessons=[
    L("Parler la langue du métier, jusque dans le code", r"""
Le Domain-Driven Design (DDD) part d'un constat : les bugs les plus coûteux viennent de **malentendus** entre ce que le métier veut et ce que le code fait. Le remède : un vocabulaire commun, fixé avec les experts, et repris **tel quel** dans le code.

```php
// Code « technique » : il faut un traducteur pour comprendre
$reservation->setStatus(3);
$manager->process($reservation);

// Code dans la langue du métier : un coach peut le relire
$reservation->annuler(motif: 'cours supprimé');
```

Concrètement :

- les **classes** portent les noms du métier (`Cours`, `Reservation`, `Abonnement`), pas `DataManager` ou `Helper` ;
- les **méthodes** sont des actions métier (`reserver`, `annuler`, `suspendre`), pas des setters ;
- les **exceptions** disent la règle violée (`CoursComplet`, `AbonnementDejaResilie`).

Quand un mot gêne dans le code (« on dit annuler ou supprimer ? »), c'est une question à poser à l'expert, pas un détail.
"""),
    L("Un mot, plusieurs sens : les bounded contexts", r"""
Dans une salle de sport, « membre » veut dire :

- pour la **facturation** : quelqu'un qui paie un abonnement (IBAN, tarif, échéances) ;
- pour le **planning** : quelqu'un qui réserve des cours (réservations, absences) ;
- pour l'**accès** : un badge qui ouvre ou non la porte (horaires, blocage).

Un seul `Membre` qui ferait tout aurait 40 propriétés, et chaque équipe le casserait pour l'autre. Le DDD découpe le domaine en **bounded contexts** : dans chacun, `Membre` a un sens précis et sa propre classe, avec seulement ce dont ce contexte a besoin.

En code, un contexte = en général un dossier et un namespace : `App\Facturation\Domain\Membre`, `App\Acces\Domain\Membre`. (Dans les exercices, tout est dans un seul fichier PHP : on écrit `MembreFacturation` et `MembreAcces` pour les distinguer.)
"""),
    L("Comment les contextes communiquent", r"""
Les contextes ne s'échangent **jamais leurs objets**. Deux moyens :

1. **Des identifiants.** Le planning stocke un `membreId`, pas l'objet `Membre` de la facturation.
2. **Des événements.** Quand quelque chose d'important arrive, le contexte le **publie** ; les autres réagissent à leur façon :

```php
// Facturation
final class AbonnementResilie
{
    public function __construct(public readonly string $membreId, public readonly DateTimeImmutable $le) {}
}

// Accès : réagit dans SA langue
final class SurAbonnementResilie
{
    public function __invoke(AbonnementResilie $e): void
    {
        $this->membres->get($e->membreId)->bloquer();
    }
}
```

La facturation ne sait pas que l'accès existe. Demain, un contexte « Fidélité » pourra écouter le même événement sans toucher à la facturation.

La **traduction** d'un contexte à l'autre (un événement de la facturation devient une action « bloquer » dans l'accès) se fait à la frontière, dans un petit adaptateur : on parle d'**anti-corruption layer** quand il protège un modèle d'un autre modèle (souvent externe) qu'on ne contrôle pas.
"""),
  ],
  recap=[
    "Le code reprend le vocabulaire du métier : classes, méthodes et exceptions aux noms métier.",
    "Un mot qui change de sens = des bounded contexts différents, chacun avec son modèle.",
    "Les contextes partagent des **identifiants** et des **événements**, jamais leurs entités.",
    "Les événements sont nommés au passé et transportent des données simples.",
  ],
  example=[F("Planning.php", "php", r"""
<?php
// Contexte Planning : vocabulaire du coach
enum StatutCours: string { case Planifie = 'planifie'; case Annule = 'annule'; }

final class Cours
{
    private StatutCours $statut = StatutCours::Planifie;

    public function __construct(
        public readonly string $id,
        private DateTimeImmutable $debut,
    ) {}

    public function deplacer(DateTimeImmutable $nouveauDebut): void
    {
        if ($this->statut === StatutCours::Annule) {
            throw new DomainException('Un cours annulé ne peut pas être déplacé');
        }
        $this->debut = $nouveauDebut;
    }

    public function annuler(): CoursAnnule
    {
        $this->statut = StatutCours::Annule;
        return new CoursAnnule($this->id);    // fait métier, pour les autres contextes
    }
}

final class CoursAnnule
{
    public function __construct(public readonly string $coursId) {}
}
"""), F("Notifications.php", "php", r"""
<?php
// Contexte Notifications : ne connaît pas la classe Cours, seulement l'événement
final class PrevenirLesInscrits
{
    public array $envoyes = [];

    public function __invoke(CoursAnnule $e): void
    {
        $this->envoyes[] = "Le cours {$e->coursId} est annulé";
    }
}
""")],
  notes=["`deplacer()` et `annuler()` : les mots du coach, pas `setDebut()` / `setStatut()`.",
         "La règle « un cours annulé ne se déplace pas » vit dans la classe, avec un message métier.",
         "`annuler()` renvoie un événement au passé ; Notifications réagit sans dépendre de `Cours`."],
  td1=dict(path="Cours.php",
    title="Du vocabulaire au code",
    enonce="Le gérant de la salle t'explique : « Un coach **planifie** un cours avec une capacité. Un membre **réserve** une place ; s'il n'y en a plus, le cours est **complet**. Un membre peut **annuler** sa réservation jusqu'à 2 heures avant le début. Le gérant peut **annuler le cours**, et alors plus personne ne peut réserver. » Traduis ça en code, avec ses mots. " + SIM,
    consignes=["`Cours::planifier(string $id, DateTimeImmutable $debut, int $capacite): self` (capacité ≥ 1)",
               "`reserver(string $membreId, DateTimeImmutable $maintenant)` : lève `CoursComplet` s'il n'y a plus de place, `DomainException` si le cours est annulé ou si le membre a déjà réservé",
               "`annulerReservation(string $membreId, DateTimeImmutable $maintenant)` : refusée (`DomainException`) à moins de 2 h du début",
               "`annuler()` (le cours) ; `placesRestantes(): int` ; `estComplet(): bool`",
               "Aucun setter, aucune propriété publique modifiable"],
    hints=["`final class CoursComplet extends DomainException {}` : une exception qui porte le nom de la règle.",
           "Stocke les réservations dans un tableau privé indexé par `membreId`.",
           "« Moins de 2 h » : `$maintenant > $this->debut->modify('-2 hours')`."],
    checks=["`CoursComplet` est levée quand il n'y a plus de place", "Pas de méthode `set…`"],
    files=[F("Cours.php", "php", r"""
<?php
declare(strict_types=1);

final class CoursComplet extends DomainException {}

final class Cours
{
    // à toi : constructeur privé + planifier(), reserver(), annulerReservation(), annuler(),
    // placesRestantes(), estComplet()
}
""")],
    solution=[F("Cours.php", "php", r"""
<?php
declare(strict_types=1);

final class CoursComplet extends DomainException {}

final class Cours
{
    private array $reservations = [];
    private bool $annule = false;

    private function __construct(
        public readonly string $id,
        private readonly DateTimeImmutable $debut,
        private readonly int $capacite,
    ) {}

    public static function planifier(string $id, DateTimeImmutable $debut, int $capacite): self
    {
        if ($capacite < 1) {
            throw new InvalidArgumentException('Un cours a au moins une place');
        }
        return new self($id, $debut, $capacite);
    }

    public function reserver(string $membreId, DateTimeImmutable $maintenant): void
    {
        if ($this->annule) {
            throw new DomainException('Ce cours est annulé');
        }
        if (isset($this->reservations[$membreId])) {
            throw new DomainException('Déjà réservé');
        }
        if ($this->estComplet()) {
            throw new CoursComplet('Plus de place');
        }
        $this->reservations[$membreId] = $maintenant;
    }

    public function annulerReservation(string $membreId, DateTimeImmutable $maintenant): void
    {
        if ($maintenant > $this->debut->modify('-2 hours')) {
            throw new DomainException('Trop tard pour annuler (moins de 2 h)');
        }
        unset($this->reservations[$membreId]);
    }

    public function annuler(): void
    {
        $this->annule = true;
    }

    public function placesRestantes(): int
    {
        return $this->capacite - count($this->reservations);
    }

    public function estComplet(): bool
    {
        return $this->placesRestantes() === 0;
    }
}
""")],
    run=RUN("php", tests=r"""
$debut = new DateTimeImmutable('2026-11-20 18:00');
$avant = new DateTimeImmutable('2026-11-19 10:00');
check('capacité 0 refusée', throws(fn() => Cours::planifier('c0', $debut, 0), InvalidArgumentException::class));
$c = Cours::planifier('yoga', $debut, 2);
$c->reserver('ana', $avant);
check('1 place restante après une réservation', $c->placesRestantes() === 1);
check('réserver deux fois : DomainException', throws(fn() => $c->reserver('ana', $avant), DomainException::class));
$c->reserver('leo', $avant);
check('estComplet() après 2 réservations', $c->estComplet());
check('3e réservation : CoursComplet', throws(fn() => $c->reserver('zoe', $avant), CoursComplet::class));
check('annuler à 1 h du début : refusé', throws(fn() => $c->annulerReservation('ana', new DateTimeImmutable('2026-11-20 17:00')), DomainException::class));
$c->annulerReservation('ana', $avant);
check('annuler la veille : une place se libère', $c->placesRestantes() === 1);
$c->annuler();
check('cours annulé : plus de réservation', throws(fn() => $c->reserver('zoe', $avant), DomainException::class));
$setters = array_filter(get_class_methods(Cours::class), fn($m) => str_starts_with($m, 'set'));
check('aucune méthode set…', $setters === []);
$pub = array_filter((new ReflectionClass(Cours::class))->getProperties(ReflectionProperty::IS_PUBLIC), fn($p) => !$p->isReadOnly());
check('aucune propriété publique modifiable', $pub === []);
""")),
  tds=[
    TD(2, "Un mot, deux contextes",
       "« Membre » n'a pas le même sens pour la **facturation** (qui paie un abonnement) et pour l'**accès** (un badge qui ouvre la porte). Modélise les deux séparément, puis relie-les par un **événement**. " + SIM,
       ["`MembreFacturation` : `id`, `tarifMensuel` (centimes), `resilier(DateTimeImmutable $le): AbonnementResilie` (exception si déjà résilié)",
        "`AbonnementResilie` : événement avec `membreId` et `le`",
        "`MembreAcces` : `id`, `badge`, `peutEntrer(DateTimeImmutable $quand): bool` (vrai entre 6 h et 23 h, et seulement si non bloqué), `bloquer()`",
        "`SurAbonnementResilie` (côté accès) : reçoit l'événement et bloque le bon `MembreAcces` dans un tableau `[id => MembreAcces]` qu'on lui passe au constructeur",
        "Aucune classe d'un contexte ne contient d'objet de l'autre"],
       [F("Facturation.php", "php", r"""
<?php
declare(strict_types=1);

// Contexte Facturation
// à toi : AbonnementResilie, MembreFacturation
"""), F("Acces.php", "php", r"""
<?php
// Contexte Accès
// à toi : MembreAcces, SurAbonnementResilie
""")],
       ["L'événement ne transporte que des données simples : l'id du membre et la date.",
        "`(int) $quand->format('G')` donne l'heure (0 à 23).",
        "`SurAbonnementResilie::__invoke(AbonnementResilie $e)` : `$this->membres[$e->membreId]->bloquer();`"],
       [F("Facturation.php", "php", r"""
<?php
declare(strict_types=1);

final class AbonnementResilie
{
    public function __construct(
        public readonly string $membreId,
        public readonly DateTimeImmutable $le,
    ) {}
}

final class MembreFacturation
{
    private ?DateTimeImmutable $resilieLe = null;

    public function __construct(
        public readonly string $id,
        public readonly int $tarifMensuel,
    ) {}

    public function resilier(DateTimeImmutable $le): AbonnementResilie
    {
        if ($this->resilieLe !== null) {
            throw new DomainException('Abonnement déjà résilié');
        }
        $this->resilieLe = $le;
        return new AbonnementResilie($this->id, $le);
    }
}
"""), F("Acces.php", "php", r"""
<?php

final class MembreAcces
{
    private bool $bloque = false;

    public function __construct(
        public readonly string $id,
        public readonly string $badge,
    ) {}

    public function peutEntrer(DateTimeImmutable $quand): bool
    {
        $heure = (int) $quand->format('G');
        return !$this->bloque && $heure >= 6 && $heure < 23;
    }

    public function bloquer(): void
    {
        $this->bloque = true;
    }
}

final class SurAbonnementResilie
{
    /** @param array<string, MembreAcces> $membres */
    public function __construct(private array $membres) {}

    public function __invoke(AbonnementResilie $e): void
    {
        $this->membres[$e->membreId]->bloquer();
    }
}
""")],
       ["Le badge est bloqué après la résiliation", "Les deux classes Membre sont indépendantes"],
       run=RUN("php", tests=r"""
$jour = new DateTimeImmutable('2026-11-20 10:00');
$f = new MembreFacturation('m1', 3990);
$a = new MembreAcces('m1', 'B-0042');
check('peutEntrer à 10 h', $a->peutEntrer($jour));
check('pas à 23 h 30', !$a->peutEntrer(new DateTimeImmutable('2026-11-20 23:30')));
check('pas à 5 h', !$a->peutEntrer(new DateTimeImmutable('2026-11-20 05:00')));
$e = $f->resilier($jour);
check('resilier() renvoie un AbonnementResilie', $e instanceof AbonnementResilie && $e->membreId === 'm1');
check('résilier deux fois : DomainException', throws(fn() => $f->resilier($jour), DomainException::class));
$autre = new MembreAcces('m2', 'B-0043');
(new SurAbonnementResilie(['m1' => $a, 'm2' => $autre]))($e);
check('le badge du membre résilié est bloqué', !$a->peutEntrer($jour));
check('les autres membres ne sont pas touchés', $autre->peutEntrer($jour));
$types = fn(string $c) => array_map(fn($p) => (string) $p->getType(), (new ReflectionClass($c))->getProperties());
check('MembreAcces ne contient rien de la facturation', !array_intersect($types(MembreAcces::class), ['MembreFacturation', '?MembreFacturation']));
check('MembreFacturation ne contient rien de l\'accès', !array_intersect($types(MembreFacturation::class), ['MembreAcces', '?MembreAcces']));
""")),
    TD(3, "Une couche anti-corruption",
       "La salle utilise un **vieux logiciel de badges** (qu'on ne contrôle pas) qui renvoie des tableaux étranges : `['BDG_NO' => '42', 'ST' => 'A', 'H_OPEN' => '0600', 'H_CLOSE' => '2300']` (`ST` : `A` actif, `S` suspendu, `X` supprimé). Ton contexte Accès ne doit **jamais** voir ce format : écris un traducteur à la frontière. " + SIM,
       ["`Badge` (value object de ton modèle) : `numero` (string sur 4 chiffres, `'0042'`), `actif` (bool), `ouverture` et `fermeture` (heures entières)",
        "`TraducteurBadgeLegacy::versBadge(array $brut): Badge` : convertit le format legacy ; `X` → exception `BadgeInconnu`, champ manquant → `InvalidArgumentException`",
        "`TraducteurBadgeLegacy::versLegacy(Badge $b): array` : l'opération inverse, pour écrire dans le vieux système",
        "Aucune autre classe ne manipule les clés `BDG_NO`, `ST`…"],
       [F("Badge.php", "php", r"""
<?php
declare(strict_types=1);

final class BadgeInconnu extends DomainException {}

// à toi : Badge (value object)
"""), F("TraducteurBadgeLegacy.php", "php", r"""
<?php
// à toi : la couche anti-corruption
""")],
       ["`str_pad($n, 4, '0', STR_PAD_LEFT)` pour le numéro.",
        "`(int) substr('0600', 0, 2)` donne 6.",
        "Vérifie les 4 clés avec `array_key_exists` avant de traduire."],
       [F("Badge.php", "php", r"""
<?php
declare(strict_types=1);

final class BadgeInconnu extends DomainException {}

final class Badge
{
    public function __construct(
        public readonly string $numero,
        public readonly bool $actif,
        public readonly int $ouverture,
        public readonly int $fermeture,
    ) {
        if (!preg_match('/^\d{4}$/', $numero)) {
            throw new InvalidArgumentException('Numéro de badge invalide');
        }
    }
}
"""), F("TraducteurBadgeLegacy.php", "php", r"""
<?php

final class TraducteurBadgeLegacy
{
    public function versBadge(array $brut): Badge
    {
        foreach (['BDG_NO', 'ST', 'H_OPEN', 'H_CLOSE'] as $cle) {
            if (!array_key_exists($cle, $brut)) {
                throw new InvalidArgumentException("Champ legacy manquant : $cle");
            }
        }
        if ($brut['ST'] === 'X') {
            throw new BadgeInconnu('Badge supprimé dans le système legacy');
        }
        return new Badge(
            str_pad((string) $brut['BDG_NO'], 4, '0', STR_PAD_LEFT),
            $brut['ST'] === 'A',
            (int) substr($brut['H_OPEN'], 0, 2),
            (int) substr($brut['H_CLOSE'], 0, 2),
        );
    }

    public function versLegacy(Badge $b): array
    {
        return [
            'BDG_NO' => ltrim($b->numero, '0'),
            'ST' => $b->actif ? 'A' : 'S',
            'H_OPEN' => sprintf('%02d00', $b->ouverture),
            'H_CLOSE' => sprintf('%02d00', $b->fermeture),
        ];
    }
}
""")],
       ["Le format legacy ne sort pas du traducteur", "L'aller-retour redonne les mêmes données"],
       run=RUN("php", tests=r"""
$t = new TraducteurBadgeLegacy();
$b = $t->versBadge(['BDG_NO' => '42', 'ST' => 'A', 'H_OPEN' => '0600', 'H_CLOSE' => '2300']);
check('numéro sur 4 chiffres', $b->numero === '0042');
check('ST=A → actif', $b->actif === true);
check('horaires en heures entières', $b->ouverture === 6 && $b->fermeture === 23);
check('ST=S → inactif', $t->versBadge(['BDG_NO' => '7', 'ST' => 'S', 'H_OPEN' => '0800', 'H_CLOSE' => '2000'])->actif === false);
check('ST=X → BadgeInconnu', throws(fn() => $t->versBadge(['BDG_NO' => '9', 'ST' => 'X', 'H_OPEN' => '0600', 'H_CLOSE' => '2300']), BadgeInconnu::class));
check('champ manquant → InvalidArgumentException', throws(fn() => $t->versBadge(['BDG_NO' => '9', 'ST' => 'A']), InvalidArgumentException::class));
$retour = $t->versLegacy($b);
check('versLegacy() redonne le format d\'origine', $retour == ['BDG_NO' => '42', 'ST' => 'A', 'H_OPEN' => '0600', 'H_CLOSE' => '2300']);
check('Badge refuse un numéro invalide', throws(fn() => new Badge('42', true, 6, 23), InvalidArgumentException::class));
$props = array_map(fn($p) => $p->getName(), (new ReflectionClass(Badge::class))->getProperties());
check('Badge parle la langue du domaine (pas de BDG_NO, ST…)', !array_intersect($props, ['BDG_NO', 'ST', 'H_OPEN', 'H_CLOSE']));
""")),
  ])

# ============================================================ 2. Value Objects
vo = V2(v1["ddd-vo"],
  prereq=[
    P("Valeur", "Quelque chose qui se décrit entièrement par son contenu : 20 €, l'adresse « 3 rue Haute », la période 10 h–11 h. Deux valeurs identiques sont interchangeables."),
    P("Immuable", "Qui ne change jamais après sa création. Pour « modifier », on crée une nouvelle valeur."),
    P("`readonly`", "Mot-clé PHP (8.1+) : la propriété ne peut être écrite qu'une fois, dans le constructeur."),
    P("Obsession des primitives", "Tout représenter avec `string`, `int`, `float` : un email, un prix, un téléphone. Les règles (format, devise) sont alors dupliquées partout, ou oubliées."),
    P("Constructeur nommé", "Une méthode statique qui crée l'objet avec un nom parlant : `Money::eur(1999)`, `Email::depuis($saisie)`."),
  ],
  diagram=D(
    nodes=[
      N("raw", 0, 0, "'  Ana@Mail.FR '", "string brute", kind="doc", color="muted"),
      N("vo", 1, 0, "Email::depuis()", "valide + normalise", kind="box", color="accent"),
      N("ok", 2, 0, "Email", "'ana@mail.fr'\ntoujours valide", kind="pill", color="good"),
      N("ko", 1, 1, "InvalidArgumentException", "refusé à l'entrée", kind="pill", color="bad"),
      N("use", 3, 0, "Le reste du code", "n'a plus à vérifier", kind="note"),
    ],
    edges=[E("raw", "vo"), E("vo", "ok", "valide"), E("vo", "ko", "invalide"), E("ok", "use")],
    caption="Un value object vérifie ses règles une seule fois, à la création. Ensuite, toute variable de type Email est forcément valide."),
  lessons=[
    L("Le problème des primitives", r"""
```php
function inscrire(string $email, float $prix, string $devise) { ... }

inscrire('pas-un-email', -12.5, 'EUROS');   // PHP accepte tout
0.1 + 0.2 === 0.3;                            // false : les float sont approximatifs
```

Avec des types primitifs :

- chaque fonction doit **revérifier** le format (ou l'oublie) ;
- on peut **inverser** deux paramètres de même type sans que rien ne le signale ;
- les règles (« un prix n'est jamais négatif », « on n'additionne pas des euros et des dollars ») sont **dispersées**.

Un **value object** est une petite classe qui représente une valeur du métier et qui porte ses règles. On l'utilise à la place de la primitive : `inscrire(Email $email, Money $prix)`.
"""),
    L("Les trois règles d'un value object", r"""
**1. Toujours valide.** Le constructeur vérifie tout et refuse ce qui est absurde. Une fois créé, l'objet est forcément correct.

**2. Immuable.** Propriétés `readonly`, aucune méthode qui modifie. Une « modification » renvoie un **nouvel** objet :

```php
$prix = Money::eur(1000);
$avecLivraison = $prix->plus(Money::eur(490));   // $prix vaut toujours 10,00 €
```

Pourquoi ? Un VO peut être partagé sans risque : personne ne peut le modifier dans ton dos.

**3. Égalité par valeur.** Deux VO sont égaux si leurs valeurs sont égales. `===` compare les **instances** ; il faut une méthode :

```php
public function equals(Money $autre): bool
{
    return $this->centimes === $autre->centimes && $this->devise === $autre->devise;
}
```
"""),
    L("Écrire un value object en PHP", r"""
```php
final class Email
{
    private function __construct(public readonly string $valeur) {}

    public static function depuis(string $saisie): self
    {
        $normalise = strtolower(trim($saisie));
        if (!filter_var($normalise, FILTER_VALIDATE_EMAIL)) {
            throw new InvalidArgumentException("Email invalide : $saisie");
        }
        return new self($normalise);
    }

    public function domaine(): string
    {
        return substr($this->valeur, strpos($this->valeur, '@') + 1);
    }

    public function equals(Email $autre): bool
    {
        return $this->valeur === $autre->valeur;
    }
}
```

- `final` : on n'hérite pas d'une valeur.
- Constructeur **privé** + constructeur nommé : un seul chemin de création, qui valide.
- Le VO **attire le comportement** : `domaine()` est écrit une fois, au bon endroit.

Pour l'argent : toujours en **centimes** (`int`), jamais en `float`, avec la devise. Pour une durée ou une période : `DateTimeImmutable`, jamais `DateTime` (qui est modifiable).

Avec Doctrine, un VO se stocke dans les colonnes de l'entité grâce à `#[ORM\Embeddable]` / `#[ORM\Embedded]`, ou via un type personnalisé.
"""),
  ],
  recap=[
    "Un value object remplace une primitive et porte ses règles.",
    "Toujours valide (vérifié dans le constructeur), immuable (`readonly`), égalité par valeur (`equals`).",
    "Constructeur privé + constructeur nommé (`Money::eur()`, `Email::depuis()`).",
    "Les « modifications » renvoient un nouvel objet.",
    "L'argent en centimes `int` + devise ; les dates en `DateTimeImmutable`.",
  ],
  example=[F("Email.php", "php", r"""
<?php
declare(strict_types=1);

final class Email
{
    private function __construct(public readonly string $valeur) {}

    public static function depuis(string $saisie): self
    {
        $normalise = strtolower(trim($saisie));
        if (!filter_var($normalise, FILTER_VALIDATE_EMAIL)) {
            throw new InvalidArgumentException("Email invalide : $saisie");
        }
        return new self($normalise);
    }

    public function domaine(): string
    {
        return substr($this->valeur, strpos($this->valeur, '@') + 1);
    }

    public function equals(Email $autre): bool
    {
        return $this->valeur === $autre->valeur;
    }
}
"""), F("demo.php", "php", r"""
<?php
$a = Email::depuis('  Ana@Mail.FR ');
$b = Email::depuis('ana@mail.fr');

var_dump($a->valeur);        // "ana@mail.fr"
var_dump($a->equals($b));    // true  : mêmes valeurs
var_dump($a === $b);         // false : deux instances
echo $a->domaine();          // mail.fr

Email::depuis('pas-un-email');   // InvalidArgumentException
""")],
  notes=["La normalisation (trim, minuscules) a lieu une seule fois, à la création.",
         "`equals()` compare les valeurs ; `===` compare les instances.",
         "Une saisie invalide ne peut pas devenir un `Email`."],
  td1=dict(path="Periode.php",
    files=[F("Periode.php", "php", r"""
<?php
declare(strict_types=1);

final class Periode
{
    // à toi : debut, fin (DateTimeImmutable, readonly), validation,
    // dureeEnMinutes(), chevauche(), equals()
}
""")],
    solution=[F("Periode.php", "php", r"""
<?php
declare(strict_types=1);

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
""")],
    run=RUN("php", tests=r"""
$d = fn(string $s) => new DateTimeImmutable("2026-11-20 $s");
$p = new Periode($d('10:00'), $d('11:30'));
check('durée de 10:00 à 11:30 = 90 minutes', $p->dureeEnMinutes() === 90);
check('fin avant début : InvalidArgumentException', throws(fn() => new Periode($d('11:00'), $d('10:00')), InvalidArgumentException::class));
check('fin = début : refusé aussi', throws(fn() => new Periode($d('10:00'), $d('10:00')), InvalidArgumentException::class));
check('10:00–11:30 chevauche 11:00–12:00', $p->chevauche(new Periode($d('11:00'), $d('12:00'))));
check('10:00–11:30 ne chevauche pas 11:30–12:00 (bout à bout)', !$p->chevauche(new Periode($d('11:30'), $d('12:00'))));
check('10:00–11:30 chevauche 10:15–10:45 (inclus)', $p->chevauche(new Periode($d('10:15'), $d('10:45'))));
check('equals : mêmes dates, autres instances', $p->equals(new Periode($d('10:00'), $d('11:30'))));
check('equals : autres dates', !$p->equals(new Periode($d('10:00'), $d('11:00'))));
check('propriétés readonly', (new ReflectionProperty(Periode::class, 'debut'))->isReadOnly() && (new ReflectionProperty(Periode::class, 'fin'))->isReadOnly());
""")),
  tds=[
    TD(2, "Money : en finir avec les float",
       "La boutique calcule ses prix en `float` et les clients voient parfois `29.999999 €`. Écris un value object `Money` correct : centimes entiers, devise, opérations sûres et affichage français. " + SIM,
       ["`Money::de(int $centimes, string $devise = 'EUR')` ; centimes négatifs → `InvalidArgumentException` ; devise sur 3 lettres majuscules",
        "`plus()`, `moins()` (résultat négatif → `DomainException`), `fois(float $facteur)` arrondi au centime le plus proche",
        "Opération entre devises différentes → `LogicException`",
        "`equals()` et `format(): string` → `'1 234,50 €'` pour EUR, `'12,00 USD'` sinon",
        "Immuable : chaque opération renvoie un nouvel objet"],
       [F("Money.php", "php", r"""
<?php
declare(strict_types=1);

final class Money
{
    // à toi
}
""")],
       ["`(int) round($this->centimes * $facteur)` pour `fois()`.",
        "`number_format($c / 100, 2, ',', ' ')` donne « 1 234,50 » (espace insécable possible selon la version : utilise un espace normal en 4e argument).",
        "Une méthode privée `memeDevise(Money $autre)` évite de répéter la vérification."],
       [F("Money.php", "php", r"""
<?php
declare(strict_types=1);

final class Money
{
    private function __construct(
        public readonly int $centimes,
        public readonly string $devise,
    ) {
        if ($centimes < 0) {
            throw new InvalidArgumentException('Montant négatif');
        }
        if (!preg_match('/^[A-Z]{3}$/', $devise)) {
            throw new InvalidArgumentException("Devise invalide : $devise");
        }
    }

    public static function de(int $centimes, string $devise = 'EUR'): self
    {
        return new self($centimes, $devise);
    }

    public function plus(Money $autre): self
    {
        $this->memeDevise($autre);
        return new self($this->centimes + $autre->centimes, $this->devise);
    }

    public function moins(Money $autre): self
    {
        $this->memeDevise($autre);
        if ($autre->centimes > $this->centimes) {
            throw new DomainException('Résultat négatif');
        }
        return new self($this->centimes - $autre->centimes, $this->devise);
    }

    public function fois(float $facteur): self
    {
        return new self((int) round($this->centimes * $facteur), $this->devise);
    }

    public function equals(Money $autre): bool
    {
        return $this->centimes === $autre->centimes && $this->devise === $autre->devise;
    }

    public function format(): string
    {
        $n = number_format($this->centimes / 100, 2, ',', ' ');
        return $this->devise === 'EUR' ? "$n €" : "$n {$this->devise}";
    }

    private function memeDevise(Money $autre): void
    {
        if ($autre->devise !== $this->devise) {
            throw new LogicException('Devises différentes');
        }
    }
}
""")],
       ["10 × 0,10 € donne exactement 1,00 €", "Les devises ne se mélangent pas"],
       run=RUN("php", tests=r"""
$dix = Money::de(10);
$t = Money::de(0); for ($i = 0; $i < 10; $i++) { $t = $t->plus($dix); }
check('10 × 0,10 € = exactement 100 centimes', $t->centimes === 100);
check('montant négatif refusé', throws(fn() => Money::de(-1), InvalidArgumentException::class));
check('devise invalide refusée', throws(fn() => Money::de(100, 'euro'), InvalidArgumentException::class));
$a = Money::de(2999);
$b = $a->plus(Money::de(1));
check('plus() ne modifie pas l\'original', $a->centimes === 2999 && $b->centimes === 3000);
check('moins()', Money::de(500)->moins(Money::de(200))->centimes === 300);
check('moins() négatif → DomainException', throws(fn() => Money::de(100)->moins(Money::de(200)), DomainException::class));
check('fois(0.2) arrondi au centime : 2999 × 0,2 = 600', Money::de(2999)->fois(0.2)->centimes === 600);
check('EUR + USD → LogicException', throws(fn() => Money::de(100)->plus(Money::de(100, 'USD')), LogicException::class));
check('equals par valeur', Money::de(100)->equals(Money::de(100)) && !Money::de(100)->equals(Money::de(100, 'USD')));
check('format EUR', Money::de(123450)->format() === '1 234,50 €', Money::de(123450)->format());
check('format USD', Money::de(1200, 'USD')->format() === '12,00 USD', Money::de(1200, 'USD')->format());
check('propriétés readonly', (new ReflectionProperty(Money::class, 'centimes'))->isReadOnly());
""")),
    TD(3, "Remplacer les primitives d'un formulaire",
       "Le service d'inscription reçoit trois `string` (email, téléphone, code postal) et les vérifie… à moitié. Crée trois value objects, puis réécris `inscrire()` pour qu'il ne reçoive plus que des objets **déjà valides**. " + SIM,
       ["`Email::depuis()` : trim + minuscules + format valide",
        "`Telephone::depuis()` : accepte `06 12 34 56 78`, `06.12.34.56.78`, `+33 6 12 34 56 78` ; stocke `+33612345678` ; refuse le reste ; `formatFrancais()` → `06 12 34 56 78`",
        "`CodePostal::depuis()` : 5 chiffres exactement (`'01000'` reste une chaîne) ; `departement()` → `'01'`",
        "`ServiceInscription::inscrire(Email, Telephone, CodePostal): array` renvoie `['email' => …, 'telephone' => …, 'departement' => …]`",
        "Tous immuables, avec `equals()`"],
       [F("Valeurs.php", "php", r"""
<?php
declare(strict_types=1);

// à toi : Email, Telephone, CodePostal
"""), F("ServiceInscription.php", "php", r"""
<?php

final class ServiceInscription
{
    // Avant : public function inscrire(string $email, string $tel, string $cp): array
    // à toi : ne plus recevoir que des value objects
}
""")],
       ["Téléphone : retire espaces, points et tirets (`preg_replace('/[\\s.\\-]/', '', $s)`), puis remplace un `0` initial par `+33`.",
        "Format attendu après nettoyage : `/^\\+33[1-9]\\d{8}$/`.",
        "`formatFrancais()` : `'0' . substr($v, 3)` puis `chunk_split(..., 2, ' ')` et `trim`."],
       [F("Valeurs.php", "php", r"""
<?php
declare(strict_types=1);

final class Email
{
    private function __construct(public readonly string $valeur) {}

    public static function depuis(string $saisie): self
    {
        $v = strtolower(trim($saisie));
        if (!filter_var($v, FILTER_VALIDATE_EMAIL)) {
            throw new InvalidArgumentException("Email invalide : $saisie");
        }
        return new self($v);
    }

    public function equals(Email $autre): bool { return $this->valeur === $autre->valeur; }
}

final class Telephone
{
    private function __construct(public readonly string $valeur) {}

    public static function depuis(string $saisie): self
    {
        $v = preg_replace('/[\s.\-]/', '', $saisie);
        if (str_starts_with($v, '0')) {
            $v = '+33' . substr($v, 1);
        }
        if (!preg_match('/^\+33[1-9]\d{8}$/', $v)) {
            throw new InvalidArgumentException("Téléphone invalide : $saisie");
        }
        return new self($v);
    }

    public function formatFrancais(): string
    {
        return trim(chunk_split('0' . substr($this->valeur, 3), 2, ' '));
    }

    public function equals(Telephone $autre): bool { return $this->valeur === $autre->valeur; }
}

final class CodePostal
{
    private function __construct(public readonly string $valeur) {}

    public static function depuis(string $saisie): self
    {
        $v = trim($saisie);
        if (!preg_match('/^\d{5}$/', $v)) {
            throw new InvalidArgumentException("Code postal invalide : $saisie");
        }
        return new self($v);
    }

    public function departement(): string { return substr($this->valeur, 0, 2); }

    public function equals(CodePostal $autre): bool { return $this->valeur === $autre->valeur; }
}
"""), F("ServiceInscription.php", "php", r"""
<?php

final class ServiceInscription
{
    public function inscrire(Email $email, Telephone $telephone, CodePostal $cp): array
    {
        return [
            'email' => $email->valeur,
            'telephone' => $telephone->valeur,
            'departement' => $cp->departement(),
        ];
    }
}
""")],
       ["Trois écritures du même numéro donnent le même Telephone", "inscrire() n'accepte plus de string"],
       run=RUN("php", tests=r"""
check('Email normalisé', Email::depuis('  Ana@Mail.FR ')->valeur === 'ana@mail.fr');
check('Email invalide refusé', throws(fn() => Email::depuis('ana@'), InvalidArgumentException::class));
$t1 = Telephone::depuis('06 12 34 56 78'); $t2 = Telephone::depuis('06.12.34.56.78'); $t3 = Telephone::depuis('+33 6 12 34 56 78');
check('stocké en +33612345678', $t1->valeur === '+33612345678', $t1->valeur);
check('trois écritures → même téléphone', $t1->equals($t2) && $t2->equals($t3));
check('formatFrancais()', $t1->formatFrancais() === '06 12 34 56 78', $t1->formatFrancais());
check('téléphone trop court refusé', throws(fn() => Telephone::depuis('06 12 34'), InvalidArgumentException::class));
check('lettres refusées', throws(fn() => Telephone::depuis('06 12 AB 56 78'), InvalidArgumentException::class));
check('code postal 01000 reste une chaîne', CodePostal::depuis('01000')->valeur === '01000');
check('département 01', CodePostal::depuis('01000')->departement() === '01');
check('code postal à 4 chiffres refusé', throws(fn() => CodePostal::depuis('1000'), InvalidArgumentException::class));
$r = (new ServiceInscription())->inscrire(Email::depuis('leo@site.fr'), $t1, CodePostal::depuis('75011'));
check('inscrire() renvoie les valeurs', $r === ['email' => 'leo@site.fr', 'telephone' => '+33612345678', 'departement' => '75']);
$types = array_map(fn($p) => (string) $p->getType(), (new ReflectionMethod(ServiceInscription::class, 'inscrire'))->getParameters());
check('inscrire() reçoit des value objects', $types === ['Email', 'Telephone', 'CodePostal'], implode(', ', $types));
""")),
  ])

# ============================================================ 3. Entités
entite = V2(v1["ddd-entite"],
  prereq=[
    P("Entité", "Un objet qui a une **identité** durable : un abonnement reste « le même » même si son statut ou sa date changent. Deux entités sont égales si elles ont le même identifiant."),
    P("Modèle anémique", "Des classes qui ne contiennent que des données avec getters/setters ; toutes les règles sont ailleurs (dans des services). Rien n'empêche de mettre l'objet dans un état absurde."),
    P("Invariant", "Une règle qui doit **toujours** être vraie pour l'objet : « un abonnement résilié ne peut plus être suspendu »."),
    P("`enum`", "Type PHP (8.1+) à valeurs fixées : `enum Statut { case Actif; case Suspendu; }`. Impossible d'y mettre une valeur inventée."),
    P("Tell, don't ask", "« Dis à l'objet quoi faire » (`$compte->debiter($m)`) plutôt que « lui demander son état pour décider à sa place » (`if ($compte->getSolde() > …) $compte->setSolde(…)`)."),
  ],
  diagram=D(
    nodes=[
      N("act", 0, 1, "Actif", None, kind="pill", color="good"),
      N("sus", 1, 0, "Suspendu", "2 fois max", kind="pill", color="warn"),
      N("res", 2, 1, "Résilié", "état final", kind="pill", color="bad"),
    ],
    edges=[E("act", "sus", "suspendre()"), E("sus", "act", "reactiver()", dashed=True), E("act", "res"), E("sus", "res", "resilier()")],
    caption="Une entité riche expose des transitions métier (suspendre, réactiver, résilier) et refuse celles qui n'existent pas : on ne peut pas « suspendre » un abonnement résilié."),
  lessons=[
    L("Du modèle anémique à l'entité riche", r"""
Le modèle **anémique** :

```php
class Abonnement
{
    public function getStatut(): string { ... }
    public function setStatut(string $s): void { ... }
    public function getNbSuspensions(): int { ... }
    public function setNbSuspensions(int $n): void { ... }
}

// les règles sont dans un service… ou recopiées dans 3 contrôleurs, ou oubliées
if ($a->getStatut() === 'actif' && $a->getNbSuspensions() < 2) {
    $a->setStatut('suspendu');
    $a->setNbSuspensions($a->getNbSuspensions() + 1);
}
```

N'importe quel code peut écrire `$a->setStatut('banane')`. L'**entité riche** inverse les rôles : elle expose des **actions métier** et garde ses règles :

```php
$a->suspendre();   // vérifie, change le statut, compte la suspension : tout ou rien
```

Le code appelant devient simple, et il est **impossible** de mettre l'objet dans un état invalide.
"""),
    L("Construire une entité riche", r"""
```php
enum StatutAbonnement: string
{
    case Actif = 'actif';
    case Suspendu = 'suspendu';
    case Resilie = 'resilie';
}

final class Abonnement
{
    private StatutAbonnement $statut = StatutAbonnement::Actif;
    private int $suspensions = 0;

    public function __construct(public readonly string $id) {}

    public function suspendre(): void
    {
        if ($this->statut !== StatutAbonnement::Actif) {
            throw new DomainException('Seul un abonnement actif peut être suspendu');
        }
        if ($this->suspensions >= 2) {
            throw new DomainException('2 suspensions maximum');
        }
        $this->statut = StatutAbonnement::Suspendu;
        $this->suspensions++;
    }

    public function statut(): StatutAbonnement { return $this->statut; }
}
```

Les recettes :

- propriétés **privées** ; getters seulement pour ce que les autres ont besoin de lire ;
- **pas de setter** : des méthodes nommées avec les mots du métier ;
- chaque méthode **vérifie d'abord**, puis modifie : si une règle échoue, rien n'a changé ;
- un `enum` pour les états : impossible d'inventer une valeur.
"""),
    L("Identité et égalité", r"""
Un value object est égal à un autre si ses **valeurs** sont égales. Une entité est égale à une autre si elle a la **même identité**, quelles que soient ses valeurs :

```php
public function estLaMemeQue(Abonnement $autre): bool
{
    return $this->id === $autre->id;
}
```

L'identité est souvent elle-même un petit value object (`AbonnementId`), pour ne pas confondre un id d'abonnement avec un id de membre.

Bonus courant : l'entité **enregistre ce qui s'est passé** sous forme d'événements, que le code applicatif récupère après coup :

```php
private array $evenements = [];

public function resilier(DateTimeImmutable $le): void
{
    // … règles …
    $this->evenements[] = new AbonnementResilie($this->id, $le);
}

public function extraireEvenements(): array
{
    [$e, $this->evenements] = [$this->evenements, []];
    return $e;
}
```
"""),
  ],
  recap=[
    "Entité = identité durable ; égalité par identifiant.",
    "Modèle anémique (getters/setters) → les règles fuient ; entité riche → méthodes métier qui protègent leurs invariants.",
    "Propriétés privées, pas de setters, `enum` pour les états.",
    "Chaque méthode vérifie avant de modifier : tout ou rien.",
    "« Tell, don't ask » ; l'entité peut enregistrer des événements de domaine.",
  ],
  example=[F("Abonnement.php", "php", r"""
<?php
declare(strict_types=1);

enum StatutAbonnement: string
{
    case Actif = 'actif';
    case Suspendu = 'suspendu';
    case Resilie = 'resilie';
}

final class Abonnement
{
    private StatutAbonnement $statut = StatutAbonnement::Actif;
    private int $suspensions = 0;
    private ?DateTimeImmutable $finLe = null;

    public function __construct(public readonly string $id) {}

    public function suspendre(): void
    {
        if ($this->statut !== StatutAbonnement::Actif) {
            throw new DomainException('Seul un abonnement actif peut être suspendu');
        }
        if ($this->suspensions >= 2) {
            throw new DomainException('2 suspensions maximum');
        }
        $this->statut = StatutAbonnement::Suspendu;
        $this->suspensions++;
    }

    public function reactiver(): void
    {
        if ($this->statut !== StatutAbonnement::Suspendu) {
            throw new DomainException('Seul un abonnement suspendu peut être réactivé');
        }
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

    public function statut(): StatutAbonnement { return $this->statut; }
    public function finLe(): ?DateTimeImmutable { return $this->finLe; }
}
""")],
  notes=["Trois transitions, chacune avec ses conditions : impossible de sauter une règle.",
         "`$suspensions` est privé : personne ne peut le remettre à zéro.",
         "Les getters exposent l'état en lecture seule ; aucune méthode `set…`."],
  td1=dict(path="Abonnement.php",
    enonce="Ce modèle anémique laisse n'importe qui écrire `setStatut('banane')`. Transforme-le en entité riche qui protège ses règles. " + SIM,
    consignes=["Statut en `enum StatutAbonnement` (Actif, Suspendu, Resilie)",
               "`suspendre()` : seulement si actif, 2 suspensions maximum sur toute la vie de l'abonnement",
               "`reactiver()` : seulement si suspendu",
               "`resilier(DateTimeImmutable $le)` : impossible si déjà résilié, fixe la date de fin",
               "Getters `statut()` et `finLe()` ; plus aucun setter ni propriété publique modifiable ; chaque refus lève une `DomainException`"],
    files=[F("Abonnement.php", "php", r"""
<?php
declare(strict_types=1);

// Modèle anémique à transformer
class Abonnement
{
    public string $id;
    public string $statut = 'actif';   // 'actif', 'suspendu', 'resilie'
    public int $nbSuspensions = 0;
    public ?DateTimeImmutable $finLe = null;

    public function __construct(string $id) { $this->id = $id; }
    public function setStatut(string $s): void { $this->statut = $s; }
}

// à toi : enum StatutAbonnement + entité riche (suspendre, reactiver, resilier, statut(), finLe())
""")],
    solution=[F("Abonnement.php", "php", r"""
<?php
declare(strict_types=1);

enum StatutAbonnement: string
{
    case Actif = 'actif';
    case Suspendu = 'suspendu';
    case Resilie = 'resilie';
}

final class Abonnement
{
    private StatutAbonnement $statut = StatutAbonnement::Actif;
    private int $suspensions = 0;
    private ?DateTimeImmutable $finLe = null;

    public function __construct(public readonly string $id) {}

    public function suspendre(): void
    {
        if ($this->statut !== StatutAbonnement::Actif) {
            throw new DomainException('Seul un abonnement actif peut être suspendu');
        }
        if ($this->suspensions >= 2) {
            throw new DomainException('2 suspensions maximum');
        }
        $this->statut = StatutAbonnement::Suspendu;
        $this->suspensions++;
    }

    public function reactiver(): void
    {
        if ($this->statut !== StatutAbonnement::Suspendu) {
            throw new DomainException('Seul un abonnement suspendu peut être réactivé');
        }
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

    public function statut(): StatutAbonnement { return $this->statut; }
    public function finLe(): ?DateTimeImmutable { return $this->finLe; }
}
""")],
    run=RUN("php", tests=r"""
$a = new Abonnement('a1');
check('statut initial : Actif (enum)', $a->statut() === StatutAbonnement::Actif);
check('réactiver un actif : refusé', throws(fn() => $a->reactiver(), DomainException::class));
$a->suspendre();
check('suspendre() → Suspendu', $a->statut() === StatutAbonnement::Suspendu);
check('suspendre deux fois de suite : refusé', throws(fn() => $a->suspendre(), DomainException::class));
$a->reactiver(); $a->suspendre(); $a->reactiver();
check('3e suspension : refusée', throws(fn() => $a->suspendre(), DomainException::class));
check('… et le statut reste Actif', $a->statut() === StatutAbonnement::Actif);
$le = new DateTimeImmutable('2026-12-31');
$a->resilier($le);
check('resilier() fixe finLe', $a->finLe() == $le && $a->statut() === StatutAbonnement::Resilie);
check('résilier deux fois : refusé', throws(fn() => $a->resilier($le), DomainException::class));
check('suspendre un résilié : refusé', throws(fn() => (function () use ($a) { $a->suspendre(); })(), DomainException::class));
check('plus de setter', !method_exists(Abonnement::class, 'setStatut'));
$pub = array_filter((new ReflectionClass(Abonnement::class))->getProperties(ReflectionProperty::IS_PUBLIC), fn($p) => !$p->isReadOnly());
check('aucune propriété publique modifiable', $pub === []);
""")),
  tds=[
    TD(2, "Le cycle de vie d'une commande",
       "Une commande passe par des étapes : **brouillon** → **validée** → **payée** → **expédiée**. On peut l'**annuler** tant qu'elle n'est pas expédiée. On ne peut ajouter des lignes qu'au brouillon. Chaque transition importante est enregistrée comme **événement**. " + SIM,
       ["`enum EtatCommande` : Brouillon, Validee, Payee, Expediee, Annulee",
        "`ajouterLigne(string $produit, int $quantite, int $prixCentimes)` : seulement au brouillon, quantité ≥ 1",
        "`valider()` : brouillon non vide uniquement ; `payer()` : validée uniquement ; `expedier()` : payée uniquement ; `annuler()` : tout sauf expédiée (et pas deux fois)",
        "`total(): int` (centimes) ; `etat(): EtatCommande`",
        "Événements : `valider()` enregistre `CommandeValidee`, `payer()` enregistre `CommandePayee` ; `extraireEvenements()` les renvoie puis vide la liste"],
       [F("Commande.php", "php", r"""
<?php
declare(strict_types=1);

final class CommandeValidee { public function __construct(public readonly string $commandeId, public readonly int $total) {} }
final class CommandePayee { public function __construct(public readonly string $commandeId) {} }

// à toi : enum EtatCommande + entité Commande
"""), F("demo.php", "php", r"""
<?php
// Essaie ici, par exemple :
// $c = new Commande('c1');
// $c->ajouterLigne('Clavier', 2, 4500);
// $c->valider();
// var_dump($c->etat(), $c->total());
""")],
       ["Une méthode privée `exiger(EtatCommande $attendu, string $action)` évite de répéter les `if`.",
        "Les lignes : un tableau privé de `['produit' => …, 'quantite' => …, 'prix' => …]`.",
        "`extraireEvenements()` : `$e = $this->evenements; $this->evenements = []; return $e;`"],
       [F("Commande.php", "php", r"""
<?php
declare(strict_types=1);

final class CommandeValidee { public function __construct(public readonly string $commandeId, public readonly int $total) {} }
final class CommandePayee { public function __construct(public readonly string $commandeId) {} }

enum EtatCommande
{
    case Brouillon;
    case Validee;
    case Payee;
    case Expediee;
    case Annulee;
}

final class Commande
{
    private EtatCommande $etat = EtatCommande::Brouillon;
    private array $lignes = [];
    private array $evenements = [];

    public function __construct(public readonly string $id) {}

    public function ajouterLigne(string $produit, int $quantite, int $prixCentimes): void
    {
        $this->exiger(EtatCommande::Brouillon, 'ajouter une ligne');
        if ($quantite < 1) {
            throw new InvalidArgumentException('Quantité minimale : 1');
        }
        $this->lignes[] = ['produit' => $produit, 'quantite' => $quantite, 'prix' => $prixCentimes];
    }

    public function valider(): void
    {
        $this->exiger(EtatCommande::Brouillon, 'valider');
        if ($this->lignes === []) {
            throw new DomainException('Une commande vide ne peut pas être validée');
        }
        $this->etat = EtatCommande::Validee;
        $this->evenements[] = new CommandeValidee($this->id, $this->total());
    }

    public function payer(): void
    {
        $this->exiger(EtatCommande::Validee, 'payer');
        $this->etat = EtatCommande::Payee;
        $this->evenements[] = new CommandePayee($this->id);
    }

    public function expedier(): void
    {
        $this->exiger(EtatCommande::Payee, 'expédier');
        $this->etat = EtatCommande::Expediee;
    }

    public function annuler(): void
    {
        if ($this->etat === EtatCommande::Expediee || $this->etat === EtatCommande::Annulee) {
            throw new DomainException('Impossible d\'annuler une commande ' . strtolower($this->etat->name));
        }
        $this->etat = EtatCommande::Annulee;
    }

    public function total(): int
    {
        return array_sum(array_map(fn($l) => $l['quantite'] * $l['prix'], $this->lignes));
    }

    public function etat(): EtatCommande { return $this->etat; }

    public function extraireEvenements(): array
    {
        $e = $this->evenements;
        $this->evenements = [];
        return $e;
    }

    private function exiger(EtatCommande $attendu, string $action): void
    {
        if ($this->etat !== $attendu) {
            throw new DomainException("Impossible de $action : la commande est {$this->etat->name}");
        }
    }
}
""")],
       ["Chaque transition interdite lève une DomainException", "Les événements sont extraits une seule fois"],
       run=RUN("php", tests=r"""
$c = new Commande('c1');
check('état initial : Brouillon', $c->etat() === EtatCommande::Brouillon);
check('valider une commande vide : refusé', throws(fn() => $c->valider(), DomainException::class));
check('quantité 0 refusée', throws(fn() => $c->ajouterLigne('X', 0, 100), InvalidArgumentException::class));
$c->ajouterLigne('Clavier', 2, 4500); $c->ajouterLigne('Souris', 1, 2000);
check('total = 11 000 centimes', $c->total() === 11000);
check('payer avant de valider : refusé', throws(fn() => $c->payer(), DomainException::class));
$c->valider();
check('ajouter une ligne après validation : refusé', throws(fn() => $c->ajouterLigne('Écran', 1, 1), DomainException::class));
check('expédier avant paiement : refusé', throws(fn() => $c->expedier(), DomainException::class));
$c->payer();
$ev = $c->extraireEvenements();
check('événements CommandeValidee puis CommandePayee', count($ev) === 2 && $ev[0] instanceof CommandeValidee && $ev[1] instanceof CommandePayee && $ev[0]->total === 11000);
check('extraireEvenements() vide la liste', $c->extraireEvenements() === []);
$c->expedier();
check('annuler une commande expédiée : refusé', throws(fn() => $c->annuler(), DomainException::class));
$d = new Commande('c2'); $d->ajouterLigne('A', 1, 100); $d->valider(); $d->annuler();
check('annuler une commande validée : OK', $d->etat() === EtatCommande::Annulee);
check('annuler deux fois : refusé', throws(fn() => $d->annuler(), DomainException::class));
check('aucune méthode set…', array_filter(get_class_methods(Commande::class), fn($m) => str_starts_with($m, 'set')) === []);
""")),
    TD(3, "Tell, don't ask : le compte et son découvert",
       "Ce service bancaire **demande** l'état du compte pour décider à sa place (`getSolde`, `setSolde`) : la règle du découvert est recopiée dans deux méthodes, avec un bug dans l'une d'elles. Déplace les règles **dans** l'entité `Compte` et simplifie le service. " + SIM,
       ["`Compte` : `crediter(int $centimes)`, `debiter(int $centimes, string $libelle)` ; montants > 0",
        "Règle : le solde ne peut pas descendre sous `-decouvertAutorise` (sinon `DecouvertDepasse`, et rien ne change)",
        "`historique(): array` : liste de `['libelle' => …, 'montant' => ±centimes]`",
        "`ServiceVirement::virer(Compte $de, Compte $vers, int $centimes)` : débit puis crédit, sans lire le solde ; si le débit échoue, le crédit n'a pas lieu",
        "Plus de `getSolde()` utilisé pour décider, plus de `setSolde()` du tout"],
       [F("Compte.php", "php", r"""
<?php
declare(strict_types=1);

final class DecouvertDepasse extends DomainException {}

// Version actuelle (anémique) : à transformer
class Compte
{
    private int $solde = 0;
    public function __construct(public readonly string $id, public readonly int $decouvertAutorise = 0) {}
    public function getSolde(): int { return $this->solde; }
    public function setSolde(int $s): void { $this->solde = $s; }
}
"""), F("ServiceVirement.php", "php", r"""
<?php

final class ServiceVirement
{
    public function retirer(Compte $c, int $m): void
    {
        if ($c->getSolde() - $m < -$c->decouvertAutorise) {
            throw new DecouvertDepasse('Découvert dépassé');
        }
        $c->setSolde($c->getSolde() - $m);
    }

    public function virer(Compte $de, Compte $vers, int $m): void
    {
        $vers->setSolde($vers->getSolde() + $m);          // bug : crédité avant la vérification…
        if ($de->getSolde() - $m < 0) {                   // … et le découvert est oublié ici
            throw new DecouvertDepasse('Découvert dépassé');
        }
        $de->setSolde($de->getSolde() - $m);
    }
}
""")],
       ["`debiter()` : vérifie le montant, puis `if ($this->solde - $m < -$this->decouvertAutorise) throw …`, puis modifie et ajoute à l'historique.",
        "Un getter `solde()` en lecture peut rester (pour afficher), mais le service n'en a plus besoin.",
        "`virer()` : `$de->debiter($m, \"Virement vers {$vers->id}\"); $vers->crediter($m, …);` : l'ordre protège."],
       [F("Compte.php", "php", r"""
<?php
declare(strict_types=1);

final class DecouvertDepasse extends DomainException {}

final class Compte
{
    private int $solde = 0;
    private array $historique = [];

    public function __construct(public readonly string $id, public readonly int $decouvertAutorise = 0) {}

    public function crediter(int $centimes, string $libelle = 'Dépôt'): void
    {
        $this->exigerPositif($centimes);
        $this->solde += $centimes;
        $this->historique[] = ['libelle' => $libelle, 'montant' => $centimes];
    }

    public function debiter(int $centimes, string $libelle): void
    {
        $this->exigerPositif($centimes);
        if ($this->solde - $centimes < -$this->decouvertAutorise) {
            throw new DecouvertDepasse("Découvert dépassé sur {$this->id}");
        }
        $this->solde -= $centimes;
        $this->historique[] = ['libelle' => $libelle, 'montant' => -$centimes];
    }

    public function solde(): int { return $this->solde; }
    public function historique(): array { return $this->historique; }

    private function exigerPositif(int $centimes): void
    {
        if ($centimes <= 0) {
            throw new InvalidArgumentException('Le montant doit être positif');
        }
    }
}
"""), F("ServiceVirement.php", "php", r"""
<?php

final class ServiceVirement
{
    public function virer(Compte $de, Compte $vers, int $centimes): void
    {
        $de->debiter($centimes, "Virement vers {$vers->id}");
        $vers->crediter($centimes, "Virement de {$de->id}");
    }
}
""")],
       ["Un virement refusé ne crédite rien", "Le découvert autorisé est respecté partout"],
       run=RUN("php", tests=r"""
$a = new Compte('A', 5000); $b = new Compte('B');
$a->crediter(10000);
$s = new ServiceVirement();
$s->virer($a, $b, 14000);
check('virement dans la limite du découvert : OK', $a->solde() === -4000 && $b->solde() === 14000);
check('virement au-delà du découvert : DecouvertDepasse', throws(fn() => $s->virer($a, $b, 2000), DecouvertDepasse::class));
check('… et rien n\'a bougé (ni débit, ni crédit)', $a->solde() === -4000 && $b->solde() === 14000);
check('montant ≤ 0 refusé', throws(fn() => $a->crediter(0), InvalidArgumentException::class) && throws(fn() => $a->debiter(-5, 'x'), InvalidArgumentException::class));
check('historique de A', $a->historique() === [['libelle' => 'Dépôt', 'montant' => 10000], ['libelle' => 'Virement vers B', 'montant' => -14000]], json_encode($a->historique(), JSON_UNESCAPED_UNICODE));
check('plus de setSolde()', !method_exists(Compte::class, 'setSolde'));
check('plus de getSolde()', !method_exists(Compte::class, 'getSolde'));
check('le service n\'a plus que virer()', array_values(array_diff(get_class_methods(ServiceVirement::class), ['__construct'])) === ['virer']);
""")),
  ])

# ============================================================ 4. Agrégats
agregat = V2(v1["ddd-agregat"],
  prereq=[
    P("Agrégat", "Un petit groupe d'objets (une entité racine et ses éléments internes) qui forme **une unité de cohérence** : ses règles sont vraies après chaque opération."),
    P("Racine d'agrégat", "La seule entité accessible de l'extérieur. Tout passe par elle : `$panier->ajouter(...)`, jamais `$panier->lignes[0]->quantite = 5`."),
    P("Transaction", "Un ensemble de modifications enregistrées « tout ou rien ». Règle DDD : une transaction ne modifie qu'**un** agrégat."),
    P("Cohérence éventuelle", "Quand deux agrégats doivent réagir l'un à l'autre, le second se met à jour **un peu après**, via un événement, plutôt que dans la même transaction."),
  ],
  diagram=D(
    nodes=[
      N("ext", 0, 1, "Code extérieur", "contrôleur, handler", kind="actor", color="muted"),
      N("root", 1, 1, "Panier (racine)", "ajouter(), retirer(), total()", kind="box", color="accent"),
      N("l1", 1, 0, "Ligne", "interne", kind="doc", color="muted"),
      N("l2", 1, 2, "Ligne", "interne", kind="doc", color="muted"),
      N("cli", 2, 1, "ClientId", "référence par id\n(autre agrégat)", kind="pill", color="good"),
    ],
    edges=[E("ext", "root", "seule porte d'entrée"), E("root", "l1"), E("root", "l2"), E("root", "cli", dashed=True)],
    lanes=[LANE("Agrégat Panier", 1, 1, "accent")],
    caption="L'extérieur ne parle qu'à la racine, qui garantit les règles de tout le groupe. Les autres agrégats (le client) sont référencés par leur identifiant, pas par l'objet."),
  lessons=[
    L("Pourquoi regrouper", r"""
Règle métier : « un panier ne dépasse pas 1 000 € ». Si n'importe quel code peut modifier une ligne directement :

```php
$panier->lignes()[0]->changerQuantite(500);   // personne ne vérifie le total
```

la règle est contournée. Un **agrégat** règle ça : la ligne n'est modifiable **que par la racine** (`Panier`), qui vérifie toutes les règles du groupe à chaque opération.

```php
$panier->changerQuantite($produitId, 500);   // le panier vérifie le plafond avant d'accepter
```

Le groupe est petit et pensé autour d'**un invariant** : « le total ne dépasse pas 1 000 € » implique que panier et lignes changent ensemble.
"""),
    L("Les règles d'un agrégat", r"""
1. **Une seule porte d'entrée** : la racine. Les objets internes ne sont jamais renvoyés modifiables (renvoie des copies, des tableaux ou des value objects).
2. **Invariants vérifiés à chaque méthode** de la racine, **avant** de modifier quoi que ce soit (tout ou rien).
3. **Références par identifiant** vers les autres agrégats : `ClientId`, pas `Client`. Sinon, charger un panier chargerait le client, ses commandes, ses adresses…
4. **Une transaction = un agrégat.** On charge un agrégat, on appelle une méthode, on le sauvegarde.
5. **Petit.** Un agrégat de 2 à 5 objets. « Le client et toutes ses commandes » n'est pas un agrégat : c'est trop gros, et deux personnes ne pourraient plus travailler en même temps.

Le repository travaille **par agrégat entier** : `$paniers->get($id)` rend le panier avec ses lignes, `$paniers->save($panier)` enregistre tout.
"""),
    L("Quand deux agrégats doivent réagir : les événements", r"""
« Quand une commande est passée, le stock diminue. » Commande et Stock sont deux agrégats différents. Les modifier dans la même transaction crée des blocages et des agrégats énormes.

On passe par un **événement** :

```php
// 1. Transaction 1 : seulement la commande
$commande = Commande::passer($id, $clientId, $lignes);
$commandes->save($commande);
$bus->publier(...$commande->extraireEvenements());   // CommandePassee

// 2. Transaction 2 (juste après, ou en asynchrone) : seulement le stock
final class ReserverStock
{
    public function __invoke(CommandePassee $e): void
    {
        $stock = $this->stocks->get($e->produitId);
        $stock->reserver($e->quantite);
        $this->stocks->save($stock);
    }
}
```

Le stock est à jour **un instant après** : c'est la **cohérence éventuelle**. Si la réservation échoue (rupture), un autre événement (`StockInsuffisant`) permet de compenser, par exemple en annulant la commande.
"""),
  ],
  recap=[
    "Agrégat = petit groupe cohérent autour d'un invariant ; on n'y entre que par la racine.",
    "Les objets internes ne sortent jamais modifiables.",
    "Références par identifiant vers les autres agrégats.",
    "Une transaction = un agrégat ; entre agrégats : événements et cohérence éventuelle.",
  ],
  example=[MONEY, F("Panier.php", "php", r"""
<?php

final class Panier
{
    private const PLAFOND = 100000; // 1 000 €
    /** @var array<string, array{prix: Money, quantite: int}> */
    private array $lignes = [];

    public function __construct(public readonly string $id, public readonly string $clientId) {}

    public function ajouter(string $produitId, Money $prix, int $quantite = 1): void
    {
        $nouvelle = ($this->lignes[$produitId]['quantite'] ?? 0) + $quantite;
        if ($nouvelle < 1 || $nouvelle > 20) {
            throw new DomainException('Quantité entre 1 et 20');
        }
        $avant = $this->lignes;                                 // on simule, puis on vérifie
        $this->lignes[$produitId] = ['prix' => $prix, 'quantite' => $nouvelle];
        if ($this->total()->depasse(Money::eur(self::PLAFOND))) {
            $this->lignes = $avant;                             // tout ou rien
            throw new DomainException('Plafond de 1 000 € dépassé');
        }
    }

    public function total(): Money
    {
        $t = Money::zero();
        foreach ($this->lignes as $l) {
            $t = $t->plus($l['prix']->multiplier($l['quantite']));
        }
        return $t;
    }

    /** Lecture seule : un tableau de valeurs, pas les objets internes */
    public function lignes(): array
    {
        return array_map(fn($id, $l) => ['produitId' => $id, 'quantite' => $l['quantite']], array_keys($this->lignes), $this->lignes);
    }
}
""")],
  notes=["`clientId` est une chaîne : le panier ne contient pas le client.",
         "`ajouter()` annule tout si le plafond est dépassé : l'agrégat reste valide.",
         "`lignes()` renvoie des valeurs : impossible de modifier une ligne de l'extérieur."],
  td1=dict(path="Panier.php",
    enonce="Modélise l'agrégat `Panier` d'une boutique. `Money` est fourni (onglet Money.php). " + SIM,
    consignes=["Racine `Panier` construite avec un `PanierId` et un `ClientId` (le client est référencé par son id)",
               "`ajouter(ProduitId, Money $prixUnitaire, int $quantite = 1)` : un produit déjà présent voit sa quantité augmenter",
               "Quantité par ligne entre 1 et 20 ; total ≤ 1 000 € ; sinon `DomainException` **et** le panier reste inchangé",
               "`retirer(ProduitId)`, `total(): Money`, `quantiteDe(ProduitId): int`",
               "Aucun accès en écriture aux lignes depuis l'extérieur"],
    files=[MONEY, F("Panier.php", "php", r"""
<?php

final class PanierId { public function __construct(public readonly string $valeur) {} }
final class ClientId { public function __construct(public readonly string $valeur) {} }
final class ProduitId { public function __construct(public readonly string $valeur) {} }

final class Panier
{
    // à toi : ajouter(ProduitId, Money $prixUnitaire, int $quantite = 1), retirer(ProduitId),
    // total(): Money, quantiteDe(ProduitId): int
}
""")],
    solution=[F("Panier.php", "php", r"""
<?php

final class PanierId { public function __construct(public readonly string $valeur) {} }
final class ClientId { public function __construct(public readonly string $valeur) {} }
final class ProduitId { public function __construct(public readonly string $valeur) {} }

final class Panier
{
    private const PLAFOND = 100000;
    private array $lignes = [];

    public function __construct(public readonly PanierId $id, public readonly ClientId $clientId) {}

    public function ajouter(ProduitId $produit, Money $prixUnitaire, int $quantite = 1): void
    {
        $k = $produit->valeur;
        $nouvelle = ($this->lignes[$k]['quantite'] ?? 0) + $quantite;
        if ($quantite < 1 || $nouvelle > 20) {
            throw new DomainException('Quantité par ligne entre 1 et 20');
        }
        $avant = $this->lignes;
        $this->lignes[$k] = ['prix' => $prixUnitaire, 'quantite' => $nouvelle];
        if ($this->total()->depasse(Money::eur(self::PLAFOND))) {
            $this->lignes = $avant;
            throw new DomainException('Le total ne peut pas dépasser 1 000 €');
        }
    }

    public function retirer(ProduitId $produit): void
    {
        unset($this->lignes[$produit->valeur]);
    }

    public function quantiteDe(ProduitId $produit): int
    {
        return $this->lignes[$produit->valeur]['quantite'] ?? 0;
    }

    public function total(): Money
    {
        $t = Money::zero();
        foreach ($this->lignes as $l) {
            $t = $t->plus($l['prix']->multiplier($l['quantite']));
        }
        return $t;
    }
}
""")],
    run=RUN("php", tests=r"""
$p = new Panier(new PanierId('p1'), new ClientId('c1'));
$clavier = new ProduitId('clavier'); $ecran = new ProduitId('ecran');
$p->ajouter($clavier, Money::eur(4500));
$p->ajouter($clavier, Money::eur(4500), 2);
check('ajouter un produit présent augmente sa quantité', $p->quantiteDe($clavier) === 3);
check('total = 135 €', $p->total()->equals(Money::eur(13500)));
check('quantité 0 refusée', throws(fn() => $p->ajouter($ecran, Money::eur(100), 0), DomainException::class));
check('plus de 20 par ligne refusé', throws(fn() => $p->ajouter($clavier, Money::eur(4500), 18), DomainException::class));
check('… et la quantité est inchangée', $p->quantiteDe($clavier) === 3);
check('dépasser 1 000 € refusé', throws(fn() => $p->ajouter($ecran, Money::eur(90000)), DomainException::class));
check('… et le panier est inchangé', $p->total()->equals(Money::eur(13500)) && $p->quantiteDe($ecran) === 0);
$p->retirer($clavier);
check('retirer()', $p->quantiteDe($clavier) === 0 && $p->total()->equals(Money::zero()));
check('le client est référencé par ClientId', (string) (new ReflectionProperty(Panier::class, 'clientId'))->getType() === 'ClientId');
$pub = array_filter((new ReflectionClass(Panier::class))->getProperties(ReflectionProperty::IS_PUBLIC), fn($x) => !$x->isReadOnly());
check('aucun accès en écriture depuis l\'extérieur', $pub === []);
""")),
  tds=[
    TD(2, "Cours avec liste d'attente",
       "Un cours a une capacité. Quand il est complet, les membres passent sur une **liste d'attente** ; quand quelqu'un annule, le **premier** de la liste prend sa place automatiquement. Tout doit rester cohérent : personne deux fois, personne à la fois inscrit et en attente. " + SIM,
       ["`Cours::reserver(string $membreId)` : inscrit s'il reste de la place, sinon ajoute à la liste d'attente ; déjà inscrit ou en attente → `DomainException`",
        "`annuler(string $membreId)` : retire l'inscrit (ou l'attente) ; si une place se libère, le premier en attente est inscrit et un événement `PlaceAttribuee` est enregistré",
        "`inscrits(): array`, `enAttente(): array` (dans l'ordre), `extraireEvenements(): array`",
        "Invariant : jamais plus d'inscrits que la capacité"],
       [F("Cours.php", "php", r"""
<?php
declare(strict_types=1);

final class PlaceAttribuee
{
    public function __construct(public readonly string $coursId, public readonly string $membreId) {}
}

final class Cours
{
    public function __construct(public readonly string $id, private readonly int $capacite) {}

    // à toi
}
""")],
       ["Deux tableaux privés : `$inscrits` et `$attente` (listes d'ids).",
        "`array_shift($this->attente)` sort le premier de la liste.",
        "`in_array($id, $this->inscrits, true)` pour tester la présence."],
       [F("Cours.php", "php", r"""
<?php
declare(strict_types=1);

final class PlaceAttribuee
{
    public function __construct(public readonly string $coursId, public readonly string $membreId) {}
}

final class Cours
{
    private array $inscrits = [];
    private array $attente = [];
    private array $evenements = [];

    public function __construct(public readonly string $id, private readonly int $capacite) {}

    public function reserver(string $membreId): void
    {
        if (in_array($membreId, $this->inscrits, true) || in_array($membreId, $this->attente, true)) {
            throw new DomainException('Déjà inscrit ou en attente');
        }
        if (count($this->inscrits) < $this->capacite) {
            $this->inscrits[] = $membreId;
        } else {
            $this->attente[] = $membreId;
        }
    }

    public function annuler(string $membreId): void
    {
        if (in_array($membreId, $this->attente, true)) {
            $this->attente = array_values(array_diff($this->attente, [$membreId]));
            return;
        }
        if (!in_array($membreId, $this->inscrits, true)) {
            throw new DomainException('Ce membre n\'est pas inscrit');
        }
        $this->inscrits = array_values(array_diff($this->inscrits, [$membreId]));
        if ($this->attente !== []) {
            $suivant = array_shift($this->attente);
            $this->inscrits[] = $suivant;
            $this->evenements[] = new PlaceAttribuee($this->id, $suivant);
        }
    }

    public function inscrits(): array { return $this->inscrits; }
    public function enAttente(): array { return $this->attente; }

    public function extraireEvenements(): array
    {
        $e = $this->evenements;
        $this->evenements = [];
        return $e;
    }
}
""")],
       ["Le premier en attente récupère la place", "Personne n'apparaît deux fois"],
       run=RUN("php", tests=r"""
$c = new Cours('yoga', 2);
foreach (['ana', 'leo', 'zoe', 'max'] as $m) { $c->reserver($m); }
check('2 inscrits, 2 en attente (dans l\'ordre)', $c->inscrits() === ['ana', 'leo'] && $c->enAttente() === ['zoe', 'max']);
check('réserver deux fois : refusé', throws(fn() => $c->reserver('zoe'), DomainException::class));
$c->annuler('ana');
check('zoe (1re en attente) prend la place', $c->inscrits() === ['leo', 'zoe'] && $c->enAttente() === ['max']);
$ev = $c->extraireEvenements();
check('événement PlaceAttribuee pour zoe', count($ev) === 1 && $ev[0] instanceof PlaceAttribuee && $ev[0]->membreId === 'zoe');
$c->annuler('max');
check('annuler depuis la liste d\'attente', $c->enAttente() === [] && $c->extraireEvenements() === []);
$c->annuler('leo');
check('annuler sans attente : une place libre', $c->inscrits() === ['zoe']);
check('annuler quelqu\'un d\'inconnu : refusé', throws(fn() => $c->annuler('bob'), DomainException::class));
check('jamais plus d\'inscrits que la capacité', count($c->inscrits()) <= 2);
""")),
    TD(3, "Deux agrégats, un événement",
       "Quand une **commande** est passée, il faut réserver le **stock**. Ce sont deux agrégats différents : on ne les modifie pas ensemble. La commande publie `CommandePassee` ; un abonné réserve le stock ; si le stock manque, il publie `StockInsuffisant` et un autre abonné **annule** la commande. " + SIM,
       ["`Commande::passer(string $id, string $produitId, int $quantite): self` enregistre `CommandePassee` ; `annuler()` ; `estAnnulee()`",
        "`Stock` (agrégat) : `reserver(int $quantite)` → `StockInsuffisant` (exception) si pas assez ; `disponible(): int`",
        "`Bus` fourni : `abonner(string $classe, callable $f)` et `publier(object ...$evenements)`",
        "`ReserverStockSurCommandePassee` : réserve ; en cas d'échec, publie l'événement `ReservationEchouee($commandeId)`",
        "`AnnulerCommandeSurEchec` : annule la commande correspondante. Aucune classe Commande ne contient de Stock, et inversement"],
       [F("Bus.php", "php", r"""
<?php
declare(strict_types=1);

// Fourni : un bus d'événements en mémoire
final class Bus
{
    private array $abonnes = [];

    public function abonner(string $classe, callable $f): void { $this->abonnes[$classe][] = $f; }

    public function publier(object ...$evenements): void
    {
        foreach ($evenements as $e) {
            foreach ($this->abonnes[$e::class] ?? [] as $f) { $f($e); }
        }
    }
}

// Fournis : des « repositories » en mémoire
final class Commandes { public array $parId = []; }
final class Stocks { public array $parProduit = []; }
"""), F("Commande.php", "php", r"""
<?php

final class CommandePassee { public function __construct(public readonly string $commandeId, public readonly string $produitId, public readonly int $quantite) {} }
final class ReservationEchouee { public function __construct(public readonly string $commandeId) {} }

// à toi : Commande
"""), F("Stock.php", "php", r"""
<?php

final class StockInsuffisant extends DomainException {}

// à toi : Stock
"""), F("Abonnes.php", "php", r"""
<?php

// à toi : ReserverStockSurCommandePassee, AnnulerCommandeSurEchec
""")],
       ["`ReserverStockSurCommandePassee` reçoit `Stocks` et `Bus` au constructeur ; dans `__invoke`, un `try { … } catch (StockInsuffisant) { $this->bus->publier(new ReservationEchouee(...)); }`.",
        "Les abonnés sont des objets invocables : `$bus->abonner(CommandePassee::class, new ReserverStockSurCommandePassee($stocks, $bus));`.",
        "Le test publie lui-même les événements extraits de la commande, comme le ferait le handler applicatif."],
       [F("Commande.php", "php", r"""
<?php

final class CommandePassee { public function __construct(public readonly string $commandeId, public readonly string $produitId, public readonly int $quantite) {} }
final class ReservationEchouee { public function __construct(public readonly string $commandeId) {} }

final class Commande
{
    private bool $annulee = false;
    private array $evenements = [];

    private function __construct(public readonly string $id, public readonly string $produitId, public readonly int $quantite) {}

    public static function passer(string $id, string $produitId, int $quantite): self
    {
        if ($quantite < 1) {
            throw new InvalidArgumentException('Quantité minimale : 1');
        }
        $c = new self($id, $produitId, $quantite);
        $c->evenements[] = new CommandePassee($id, $produitId, $quantite);
        return $c;
    }

    public function annuler(): void { $this->annulee = true; }
    public function estAnnulee(): bool { return $this->annulee; }

    public function extraireEvenements(): array
    {
        $e = $this->evenements;
        $this->evenements = [];
        return $e;
    }
}
"""), F("Stock.php", "php", r"""
<?php

final class StockInsuffisant extends DomainException {}

final class Stock
{
    public function __construct(public readonly string $produitId, private int $disponible) {}

    public function reserver(int $quantite): void
    {
        if ($quantite > $this->disponible) {
            throw new StockInsuffisant("Stock insuffisant pour {$this->produitId}");
        }
        $this->disponible -= $quantite;
    }

    public function disponible(): int { return $this->disponible; }
}
"""), F("Abonnes.php", "php", r"""
<?php

final class ReserverStockSurCommandePassee
{
    public function __construct(private Stocks $stocks, private Bus $bus) {}

    public function __invoke(CommandePassee $e): void
    {
        try {
            $this->stocks->parProduit[$e->produitId]->reserver($e->quantite);
        } catch (StockInsuffisant) {
            $this->bus->publier(new ReservationEchouee($e->commandeId));
        }
    }
}

final class AnnulerCommandeSurEchec
{
    public function __construct(private Commandes $commandes) {}

    public function __invoke(ReservationEchouee $e): void
    {
        $this->commandes->parId[$e->commandeId]->annuler();
    }
}
""")],
       ["Le stock baisse après une commande", "Une commande sans stock est annulée par compensation"],
       run=RUN("php", tests=r"""
$bus = new Bus(); $commandes = new Commandes(); $stocks = new Stocks();
$stocks->parProduit['clavier'] = new Stock('clavier', 3);
$bus->abonner(CommandePassee::class, new ReserverStockSurCommandePassee($stocks, $bus));
$bus->abonner(ReservationEchouee::class, new AnnulerCommandeSurEchec($commandes));
$c1 = Commande::passer('c1', 'clavier', 2); $commandes->parId['c1'] = $c1;
check('passer() enregistre CommandePassee', ($ev = $c1->extraireEvenements()) && $ev[0] instanceof CommandePassee);
$bus->publier(...$ev);
check('le stock est réservé (3 → 1)', $stocks->parProduit['clavier']->disponible() === 1);
check('c1 n\'est pas annulée', !$c1->estAnnulee());
$c2 = Commande::passer('c2', 'clavier', 5); $commandes->parId['c2'] = $c2;
$bus->publier(...$c2->extraireEvenements());
check('stock insuffisant : c2 est annulée (compensation)', $c2->estAnnulee());
check('… et le stock n\'a pas bougé', $stocks->parProduit['clavier']->disponible() === 1);
check('Stock::reserver() lève StockInsuffisant', throws(fn() => (new Stock('x', 1))->reserver(2), StockInsuffisant::class));
$t = fn(string $cl) => array_map(fn($p) => (string) $p->getType(), (new ReflectionClass($cl))->getProperties());
check('Commande ne contient pas de Stock', !in_array('Stock', $t(Commande::class), true));
check('Stock ne contient pas de Commande', !in_array('Commande', $t(Stock::class), true));
""")),
  ])

# ============================================================ 5. Couches
couches = V2(v1["ddd-couches"],
  prereq=[
    P("Couche", "Une partie du code avec une responsabilité : **Domain** (les règles), **Application** (les cas d'usage), **Infrastructure** (base, email, HTTP, framework)."),
    P("Port", "Une interface définie par le domaine ou l'application pour dire « j'ai besoin de ça » : `CoursRepository`, `Horloge`, `Notificateur`."),
    P("Adaptateur", "Une implémentation concrète d'un port : `DoctrineCoursRepository`, `InMemoryCoursRepository`, `HorlogeSysteme`."),
    P("Handler (cas d'usage)", "Une classe qui exécute **une** action de l'utilisateur : charger l'agrégat, appeler sa méthode, sauvegarder, publier les événements."),
    P("Inversion des dépendances", "Le domaine ne dépend de rien ; c'est l'infrastructure qui dépend des interfaces du domaine (et pas l'inverse)."),
  ],
  diagram=D(
    nodes=[
      N("ctl", 0, 0, "Contrôleur / CLI", "reçoit la requête", kind="file", color="muted"),
      N("h", 1, 0, "ReserverPlaceHandler", "Application : cas d'usage", kind="box", color="warn"),
      N("dom", 2, 0, "Cours (agrégat)", "Domain : règles métier", kind="box", color="accent"),
      N("port", 1, 1, "CoursRepository", "Domain : interface (port)", kind="note", color="accent"),
      N("ad", 2, 1, "DoctrineCoursRepository", "Infrastructure : adaptateur", kind="db", color="muted"),
    ],
    edges=[E("ctl", "h", "commande"), E("h", "dom", "reserver()"), E("h", "port", "get / save"), E("ad", "port", "implémente", dashed=True)],
    caption="Les dépendances pointent vers le domaine : le handler utilise le domaine et ses interfaces ; l'infrastructure implémente ces interfaces. Le domaine ne connaît ni Doctrine ni Symfony."),
  lessons=[
    L("Trois couches, une règle de dépendance", r"""
```
src/Planning/
├── Domain/           Cours, MembreId, CoursComplet, CoursRepository (interface)
├── Application/      ReserverPlace (commande), ReserverPlaceHandler
└── Infrastructure/   DoctrineCoursRepository, ReserverPlaceController
```

- **Domain** : les règles du métier, en PHP pur. Aucun `use Doctrine…`, aucun `use Symfony…`.
- **Application** : les cas d'usage. Elle orchestre : charger, appeler le domaine, sauvegarder, publier. Pas de règle métier ici.
- **Infrastructure** : tout ce qui touche au monde extérieur (base, HTTP, emails, horloge système).

La règle : **les dépendances pointent vers le domaine.** L'infrastructure connaît le domaine ; le domaine ne connaît pas l'infrastructure. On peut ainsi tester tout le métier sans base de données, et changer d'ORM sans toucher aux règles.

C'est la même idée que le module Architecture (contrôleur / service / repository), poussée plus loin : le « service » devient un handler mince, et les règles descendent dans les entités et agrégats.
"""),
    L("Ports et adaptateurs", r"""
Le domaine a besoin de choses qu'il ne doit pas implémenter lui-même : enregistrer un agrégat, connaître l'heure, envoyer un email. Il **déclare une interface** (un port) :

```php
// Domain
interface CoursRepository
{
    public function get(string $id): Cours;     // lève CoursIntrouvable
    public function save(Cours $cours): void;
}

interface Horloge
{
    public function maintenant(): DateTimeImmutable;
}
```

L'infrastructure fournit les **adaptateurs** :

```php
// Infrastructure
final class DoctrineCoursRepository implements CoursRepository { /* EntityManager */ }
final class InMemoryCoursRepository implements CoursRepository { private array $cours = []; /* … */ }
final class HorlogeSysteme implements Horloge { public function maintenant(): DateTimeImmutable { return new DateTimeImmutable(); } }
```

En production, Symfony injecte les adaptateurs Doctrine ; dans les tests, on injecte les versions en mémoire et une **horloge fixe** : les tests sont rapides et déterministes.

(Remarque : `new DateTimeImmutable()` au milieu d'une règle métier rend le code impossible à tester « le 31 décembre » : l'horloge injectée règle ce problème.)
"""),
    L("Un handler typique", r"""
```php
// Application
final class ReserverPlace
{
    public function __construct(public readonly string $coursId, public readonly string $membreId) {}
}

final class ReserverPlaceHandler
{
    public function __construct(private CoursRepository $cours, private Horloge $horloge) {}

    public function __invoke(ReserverPlace $commande): void
    {
        $cours = $this->cours->get($commande->coursId);                       // 1. charger
        $cours->reserver($commande->membreId, $this->horloge->maintenant());  // 2. le domaine décide
        $this->cours->save($cours);                                           // 3. sauvegarder
    }
}
```

Trois étapes, aucune règle métier : si tu écris un `if` métier dans un handler, il est probablement mal placé. La **commande** (`ReserverPlace`) est un simple objet de données, souvent construit depuis un DTO de requête par le contrôleur.

Le domaine ne connaît pas la base, mais la base doit pouvoir **reconstruire** le domaine : un repository fait la traduction dans les deux sens (ligne de base ↔ agrégat), sans repasser par les règles de création (`Cours::reconstituer(...)` plutôt que `Cours::planifier(...)`).
"""),
  ],
  recap=[
    "Domain (règles, PHP pur) ← Application (cas d'usage) ← Infrastructure (base, HTTP, framework).",
    "Le domaine déclare des **ports** (interfaces) ; l'infrastructure fournit des **adaptateurs**.",
    "Handler = charger → appeler le domaine → sauvegarder (+ publier). Aucune règle métier.",
    "Horloge et repositories injectés : tests rapides et déterministes, en mémoire.",
    "Le repository traduit base ↔ agrégat ; reconstituer ≠ créer.",
  ],
  example=[F("Domain.php", "php", r"""
<?php
declare(strict_types=1);

// ---- Domain ----
final class CoursComplet extends DomainException {}
final class CoursIntrouvable extends DomainException {}

final class Cours
{
    private array $inscrits = [];

    public function __construct(public readonly string $id, private readonly int $capacite) {}

    public function reserver(string $membreId): void
    {
        if (count($this->inscrits) >= $this->capacite) {
            throw new CoursComplet("Le cours {$this->id} est complet");
        }
        $this->inscrits[] = $membreId;
    }
}

interface CoursRepository
{
    public function get(string $id): Cours;
    public function save(Cours $cours): void;
}
"""), F("Application.php", "php", r"""
<?php

// ---- Application ----
final class ReserverPlace
{
    public function __construct(public readonly string $coursId, public readonly string $membreId) {}
}

final class ReserverPlaceHandler
{
    public function __construct(private CoursRepository $cours) {}

    public function __invoke(ReserverPlace $c): void
    {
        $cours = $this->cours->get($c->coursId);
        $cours->reserver($c->membreId);
        $this->cours->save($cours);
    }
}
"""), F("Infrastructure.php", "php", r"""
<?php

// ---- Infrastructure ----
final class InMemoryCoursRepository implements CoursRepository
{
    private array $cours = [];

    public function get(string $id): Cours
    {
        return $this->cours[$id] ?? throw new CoursIntrouvable($id);
    }

    public function save(Cours $cours): void
    {
        $this->cours[$cours->id] = $cours;
    }
}
""")],
  notes=["Domain : la règle « complet » et l'interface du repository, sans rien d'autre.",
         "Application : le handler orchestre en 3 lignes.",
         "Infrastructure : une implémentation en mémoire ; une version Doctrine aurait la même interface."],
  td1=dict(path="Domain.php",
    enonce="Salle de sport : un membre réserve une place dans un cours. Range le code dans les trois couches (un onglet par couche). " + SIM,
    consignes=["Domain : agrégat `Cours` (id, capacité, membres inscrits) ; `reserver(string $membreId)` lève `CoursComplet` si complet, `DejaInscrit` si déjà inscrit ; `inscrits(): array`",
               "Domain : interface `CoursRepository` (`get(string $id): Cours` qui lève `CoursIntrouvable`, `save(Cours)`)",
               "Application : `ReserverPlaceHandler` (invocable) qui reçoit l'**interface** au constructeur : charger, réserver, sauvegarder",
               "Infrastructure : `InMemoryCoursRepository`",
               "Les tests jouent le scénario : 2 places, 3 réservations → la 3e échoue"],
    files=[F("Domain.php", "php", r"""
<?php
declare(strict_types=1);

// ---- Domain ----
final class CoursComplet extends DomainException {}
final class DejaInscrit extends DomainException {}
final class CoursIntrouvable extends DomainException {}

// à toi : agrégat Cours (id, capacite, inscrits), interface CoursRepository (get, save)
"""), F("Application.php", "php", r"""
<?php

// ---- Application ----
final class ReserverPlace
{
    public function __construct(public readonly string $coursId, public readonly string $membreId) {}
}

// à toi : ReserverPlaceHandler
"""), F("Infrastructure.php", "php", r"""
<?php

// ---- Infrastructure ----
// à toi : InMemoryCoursRepository
""")],
    solution=[F("Domain.php", "php", r"""
<?php
declare(strict_types=1);

final class CoursComplet extends DomainException {}
final class DejaInscrit extends DomainException {}
final class CoursIntrouvable extends DomainException {}

final class Cours
{
    private array $inscrits = [];

    public function __construct(public readonly string $id, private readonly int $capacite) {}

    public function reserver(string $membreId): void
    {
        if (in_array($membreId, $this->inscrits, true)) {
            throw new DejaInscrit("$membreId est déjà inscrit");
        }
        if (count($this->inscrits) >= $this->capacite) {
            throw new CoursComplet("Le cours {$this->id} est complet");
        }
        $this->inscrits[] = $membreId;
    }

    public function inscrits(): array { return $this->inscrits; }
}

interface CoursRepository
{
    public function get(string $id): Cours;
    public function save(Cours $cours): void;
}
"""), F("Application.php", "php", r"""
<?php

final class ReserverPlace
{
    public function __construct(public readonly string $coursId, public readonly string $membreId) {}
}

final class ReserverPlaceHandler
{
    public function __construct(private CoursRepository $cours) {}

    public function __invoke(ReserverPlace $c): void
    {
        $cours = $this->cours->get($c->coursId);
        $cours->reserver($c->membreId);
        $this->cours->save($cours);
    }
}
"""), F("Infrastructure.php", "php", r"""
<?php

final class InMemoryCoursRepository implements CoursRepository
{
    private array $cours = [];

    public function get(string $id): Cours
    {
        return $this->cours[$id] ?? throw new CoursIntrouvable("Cours $id introuvable");
    }

    public function save(Cours $cours): void
    {
        $this->cours[$cours->id] = $cours;
    }
}
""")],
    run=RUN("php", tests=r"""
$repo = new InMemoryCoursRepository();
check('InMemoryCoursRepository implémente CoursRepository', $repo instanceof CoursRepository);
$repo->save(new Cours('yoga', 2));
$h = new ReserverPlaceHandler($repo);
$h(new ReserverPlace('yoga', 'ana'));
$h(new ReserverPlace('yoga', 'leo'));
check('2 réservations enregistrées', $repo->get('yoga')->inscrits() === ['ana', 'leo']);
check('3e réservation : CoursComplet', throws(fn() => $h(new ReserverPlace('yoga', 'zoe')), CoursComplet::class));
$repo->save(new Cours('pilates', 5));
$h(new ReserverPlace('pilates', 'ana'));
check('réserver deux fois : DejaInscrit', throws(fn() => $h(new ReserverPlace('pilates', 'ana')), DejaInscrit::class));
check('cours inconnu : CoursIntrouvable', throws(fn() => $h(new ReserverPlace('boxe', 'ana')), CoursIntrouvable::class));
check('CoursRepository est une interface', (new ReflectionClass('CoursRepository'))->isInterface());
$params = array_map(fn($p) => (string) $p->getType(), (new ReflectionMethod(ReserverPlaceHandler::class, '__construct'))->getParameters());
check('le handler dépend de l\'interface, pas de l\'implémentation', $params === ['CoursRepository'], implode(', ', $params));
""")),
  tds=[
    TD(2, "Inscription avec horloge et notification",
       "Cas d'usage : un visiteur s'inscrit à la salle. Règle métier : il doit avoir **16 ans révolus** à la date du jour. Après l'inscription, il reçoit un email de bienvenue. Le domaine ne doit dépendre ni de l'heure système, ni d'un vrai envoi d'email. " + SIM,
       ["Domain : `Membre::inscrire(string $id, string $email, DateTimeImmutable $naissance, DateTimeImmutable $aujourdhui)` → `TropJeune` si moins de 16 ans",
        "Domain : ports `MembreRepository` (`save`, `existe(string $email): bool`) et `Horloge` (`maintenant()`)",
        "Application : port `Notificateur` (`bienvenue(string $email)`), commande `InscrireMembre` et `InscrireMembreHandler` ; email déjà pris → `EmailDejaUtilise`",
        "Infrastructure : `InMemoryMembreRepository`, `HorlogeFixe` (date donnée au constructeur), `FauxNotificateur` (garde les emails dans un tableau public `$envoyes`)",
        "Le handler ne fait aucun calcul d'âge lui-même"],
       [F("Domain.php", "php", r"""
<?php
declare(strict_types=1);

final class TropJeune extends DomainException {}
final class EmailDejaUtilise extends DomainException {}

// à toi : Membre, MembreRepository, Horloge
"""), F("Application.php", "php", r"""
<?php

final class InscrireMembre
{
    public function __construct(public readonly string $id, public readonly string $email, public readonly string $naissance) {}
}

// à toi : Notificateur, InscrireMembreHandler
"""), F("Infrastructure.php", "php", r"""
<?php

// à toi : InMemoryMembreRepository, HorlogeFixe, FauxNotificateur
""")],
       ["Âge : `$naissance->diff($aujourdhui)->y` donne le nombre d'années révolues.",
        "Le handler : vérifier l'email (`existe`), `Membre::inscrire(…, $this->horloge->maintenant())`, `save`, puis `bienvenue`.",
        "Le handler reçoit trois interfaces au constructeur."],
       [F("Domain.php", "php", r"""
<?php
declare(strict_types=1);

final class TropJeune extends DomainException {}
final class EmailDejaUtilise extends DomainException {}

final class Membre
{
    private function __construct(public readonly string $id, public readonly string $email) {}

    public static function inscrire(string $id, string $email, DateTimeImmutable $naissance, DateTimeImmutable $aujourdhui): self
    {
        if ($naissance->diff($aujourdhui)->y < 16) {
            throw new TropJeune('Il faut avoir 16 ans pour s\'inscrire');
        }
        return new self($id, $email);
    }
}

interface MembreRepository
{
    public function save(Membre $m): void;
    public function existe(string $email): bool;
}

interface Horloge
{
    public function maintenant(): DateTimeImmutable;
}
"""), F("Application.php", "php", r"""
<?php

final class InscrireMembre
{
    public function __construct(public readonly string $id, public readonly string $email, public readonly string $naissance) {}
}

interface Notificateur
{
    public function bienvenue(string $email): void;
}

final class InscrireMembreHandler
{
    public function __construct(
        private MembreRepository $membres,
        private Horloge $horloge,
        private Notificateur $notificateur,
    ) {}

    public function __invoke(InscrireMembre $c): void
    {
        if ($this->membres->existe($c->email)) {
            throw new EmailDejaUtilise($c->email);
        }
        $membre = Membre::inscrire($c->id, $c->email, new DateTimeImmutable($c->naissance), $this->horloge->maintenant());
        $this->membres->save($membre);
        $this->notificateur->bienvenue($c->email);
    }
}
"""), F("Infrastructure.php", "php", r"""
<?php

final class InMemoryMembreRepository implements MembreRepository
{
    public array $membres = [];

    public function save(Membre $m): void { $this->membres[$m->id] = $m; }

    public function existe(string $email): bool
    {
        foreach ($this->membres as $m) {
            if ($m->email === $email) {
                return true;
            }
        }
        return false;
    }
}

final class HorlogeFixe implements Horloge
{
    public function __construct(private DateTimeImmutable $date) {}
    public function maintenant(): DateTimeImmutable { return $this->date; }
}

final class FauxNotificateur implements Notificateur
{
    public array $envoyes = [];
    public function bienvenue(string $email): void { $this->envoyes[] = $email; }
}
""")],
       ["Le test choisit la date du jour", "Aucun email n'est envoyé en cas de refus"],
       run=RUN("php", tests=r"""
$repo = new InMemoryMembreRepository(); $notif = new FauxNotificateur();
$h = new InscrireMembreHandler($repo, new HorlogeFixe(new DateTimeImmutable('2026-11-12')), $notif);
$h(new InscrireMembre('m1', 'ana@mail.fr', '2010-11-12'));
check('16 ans le jour même : inscrit', isset($repo->membres['m1']));
check('email de bienvenue envoyé', $notif->envoyes === ['ana@mail.fr']);
check('16 ans demain : TropJeune', throws(fn() => $h(new InscrireMembre('m2', 'leo@mail.fr', '2010-11-13')), TropJeune::class));
check('… et aucun email envoyé', $notif->envoyes === ['ana@mail.fr']);
check('email déjà utilisé : EmailDejaUtilise', throws(fn() => $h(new InscrireMembre('m3', 'ana@mail.fr', '1990-01-01')), EmailDejaUtilise::class));
foreach (['MembreRepository', 'Horloge', 'Notificateur'] as $i) { check("$i est une interface", (new ReflectionClass($i))->isInterface()); }
$params = array_map(fn($p) => (string) $p->getType(), (new ReflectionMethod(InscrireMembreHandler::class, '__construct'))->getParameters());
check('le handler ne dépend que d\'interfaces', $params === ['MembreRepository', 'Horloge', 'Notificateur'], implode(', ', $params));
check('Membre::inscrire reçoit la date du jour (pas d\'heure système cachée)', (new ReflectionMethod(Membre::class, 'inscrire'))->getNumberOfParameters() === 4);
""")),
    TD(3, "Persister sans polluer le domaine",
       "L'entité `Membre` a un value object `Email` et un `enum` de statut. La « base de données » (simulée) ne stocke que des **lignes** de scalaires. Écris le repository qui traduit dans les deux sens, sans ajouter le moindre détail de stockage dans le domaine, et sans repasser par les règles de création au chargement. " + SIM,
       ["Domain : `Email` (VO), `enum StatutMembre: string` (`actif`, `suspendu`), `Membre` avec `inscrire()` (règles de création) et `reconstituer()` (rechargement, sans règle ni événement), `suspendre()`",
        "Domain : interface `MembreRepository` (`get(string $id): Membre`, `save(Membre $m)`)",
        "Infrastructure : `TableMembresRepository` stocke dans `FausseTable` (fournie) des lignes `['id' => …, 'email' => …, 'statut' => 'actif' | 'suspendu', 'inscrit_le' => 'Y-m-d']`",
        "`get()` d'un id inconnu → `MembreIntrouvable`",
        "Aller-retour : sauvegarder puis recharger donne un membre identique (même email, même statut, même date)"],
       [F("FausseTable.php", "php", r"""
<?php
declare(strict_types=1);

// Fourni : une « table » qui n'accepte que des scalaires
final class FausseTable
{
    public array $lignes = [];

    public function upsert(array $ligne): void
    {
        foreach ($ligne as $k => $v) {
            if (!is_scalar($v) && $v !== null) {
                throw new LogicException("La colonne $k doit être un scalaire");
            }
        }
        $this->lignes[$ligne['id']] = $ligne;
    }

    public function trouver(string $id): ?array { return $this->lignes[$id] ?? null; }
}
"""), F("Domain.php", "php", r"""
<?php

final class MembreIntrouvable extends DomainException {}

// à toi : Email, StatutMembre, Membre (inscrire, reconstituer, suspendre, getters), MembreRepository
"""), F("Infrastructure.php", "php", r"""
<?php

// à toi : TableMembresRepository
""")],
       ["`reconstituer()` est un constructeur nommé qui prend toutes les valeurs telles quelles (y compris le statut et la date).",
        "Côté repository : `StatutMembre::from($ligne['statut'])` et `$m->statut()->value` pour la conversion.",
        "Les dates : `->format('Y-m-d')` à l'écriture, `new DateTimeImmutable($ligne['inscrit_le'])` à la lecture."],
       [F("Domain.php", "php", r"""
<?php

final class MembreIntrouvable extends DomainException {}

final class Email
{
    private function __construct(public readonly string $valeur) {}

    public static function depuis(string $s): self
    {
        $v = strtolower(trim($s));
        if (!filter_var($v, FILTER_VALIDATE_EMAIL)) {
            throw new InvalidArgumentException("Email invalide : $s");
        }
        return new self($v);
    }
}

enum StatutMembre: string
{
    case Actif = 'actif';
    case Suspendu = 'suspendu';
}

final class Membre
{
    private function __construct(
        public readonly string $id,
        private Email $email,
        private StatutMembre $statut,
        private DateTimeImmutable $inscritLe,
    ) {}

    public static function inscrire(string $id, Email $email, DateTimeImmutable $le): self
    {
        return new self($id, $email, StatutMembre::Actif, $le);
    }

    public static function reconstituer(string $id, Email $email, StatutMembre $statut, DateTimeImmutable $inscritLe): self
    {
        return new self($id, $email, $statut, $inscritLe);
    }

    public function suspendre(): void
    {
        if ($this->statut === StatutMembre::Suspendu) {
            throw new DomainException('Déjà suspendu');
        }
        $this->statut = StatutMembre::Suspendu;
    }

    public function email(): Email { return $this->email; }
    public function statut(): StatutMembre { return $this->statut; }
    public function inscritLe(): DateTimeImmutable { return $this->inscritLe; }
}

interface MembreRepository
{
    public function get(string $id): Membre;
    public function save(Membre $m): void;
}
"""), F("Infrastructure.php", "php", r"""
<?php

final class TableMembresRepository implements MembreRepository
{
    public function __construct(private FausseTable $table) {}

    public function get(string $id): Membre
    {
        $l = $this->table->trouver($id) ?? throw new MembreIntrouvable("Membre $id introuvable");
        return Membre::reconstituer(
            $l['id'],
            Email::depuis($l['email']),
            StatutMembre::from($l['statut']),
            new DateTimeImmutable($l['inscrit_le']),
        );
    }

    public function save(Membre $m): void
    {
        $this->table->upsert([
            'id' => $m->id,
            'email' => $m->email()->valeur,
            'statut' => $m->statut()->value,
            'inscrit_le' => $m->inscritLe()->format('Y-m-d'),
        ]);
    }
}
""")],
       ["La table ne contient que des scalaires", "Le domaine ignore tout de la table"],
       run=RUN("php", tests=r"""
$table = new FausseTable(); $repo = new TableMembresRepository($table);
check('TableMembresRepository implémente MembreRepository', $repo instanceof MembreRepository);
$m = Membre::inscrire('m1', Email::depuis('Ana@Mail.fr'), new DateTimeImmutable('2026-01-15'));
$m->suspendre();
$repo->save($m);
check('ligne stockée en scalaires', $table->lignes['m1'] === ['id' => 'm1', 'email' => 'ana@mail.fr', 'statut' => 'suspendu', 'inscrit_le' => '2026-01-15'], json_encode($table->lignes['m1'] ?? null));
$r = $repo->get('m1');
check('aller-retour : même email', $r->email()->valeur === 'ana@mail.fr');
check('aller-retour : même statut (enum)', $r->statut() === StatutMembre::Suspendu);
check('aller-retour : même date', $r->inscritLe()->format('Y-m-d') === '2026-01-15');
check('membre inconnu : MembreIntrouvable', throws(fn() => $repo->get('zz'), MembreIntrouvable::class));
check('reconstituer() existe et est statique', (new ReflectionMethod(Membre::class, 'reconstituer'))->isStatic());
$types = array_map(fn($p) => (string) $p->getType(), (new ReflectionClass(Membre::class))->getProperties());
check('Membre utilise Email et StatutMembre (pas des string)', in_array('Email', $types, true) && in_array('StatutMembre', $types, true));
check('le domaine ne connaît pas la table', !in_array('FausseTable', $types, true));
check('constructeur de Membre privé', (new ReflectionMethod(Membre::class, '__construct'))->isPrivate());
""")),
  ])

MODULES = [langage, vo, entite, agregat, couches]

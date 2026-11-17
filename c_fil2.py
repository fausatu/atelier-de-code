"""Parcours « Projet fil rouge : Bobine », modules 4 à 6 : profils (API en écriture), reprise de lecture, front React."""
from common import P, L, D, N, E, LANE, F, TD, RUN
from c_fil import FM, Q, JS, SSIM, SRUN

USES = r"""<?php
declare(strict_types=1);

use Atelier\App;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpKernel\Attribute\MapQueryString;
use Symfony\Component\HttpKernel\Attribute\MapRequestPayload;
use Symfony\Component\HttpKernel\Attribute\WithHttpStatus;
use Symfony\Component\HttpKernel\Exception\AccessDeniedHttpException;
use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;
use Symfony\Component\Routing\Attribute\Route;
use Symfony\Component\Security\Http\Attribute\CurrentUser;
use Symfony\Component\Validator\Constraints as Assert;
"""

# =========================================================================== 4. Profils : l'API en écriture
PROFILS_BASE = F("bobine.php", "php", USES + r"""
// ---- Fourni : forfaits, profils, exceptions, stockage ----

enum Forfait: string
{
    case Essentiel = 'essentiel';
    case Standard = 'standard';
    case Premium = 'premium';

    public function maxProfils(): int { return match ($this) { Forfait::Essentiel => 2, Forfait::Standard => 4, Forfait::Premium => 5 }; }
    public function libelle(): string { return match ($this) { Forfait::Essentiel => 'Essentiel', Forfait::Standard => 'Standard', Forfait::Premium => 'Premium' }; }
}

final class Profil
{
    private static int $suivant = 1;
    private int $id;

    public function __construct(private Compte $compte, private string $nom, private ?int $age = null)
    {
        $this->id = self::$suivant++;
    }

    public function getId(): int { return $this->id; }
    public function getCompte(): Compte { return $this->compte; }
    public function getNom(): string { return $this->nom; }
    public function getAge(): ?int { return $this->age; }
    public function estEnfant(): bool { return $this->age !== null; }
}

#[WithHttpStatus(409)]
final class ForfaitPleinException extends \DomainException {}

#[WithHttpStatus(409)]
final class NomDejaPrisException extends \DomainException {}

/** Remplace l'EntityManager : garde la trace de ce qui est enregistré ou supprimé. */
final class Stockage
{
    public array $enregistres = [];
    public array $supprimes = [];
    public function enregistrer(object $o): void { $this->enregistres[] = $o; }
    public function supprimer(object $o): void { $this->supprimes[] = $o; }
}
""")

COMPTE_V1 = r"""
<?php
final class Compte
{
    /** @var Profil[] */
    private array $profils = [];

    public function __construct(private string $email, private Forfait $forfait, string $nomPremierProfil)
    {
        $this->ajouterProfil($nomPremierProfil);
    }

    public function ajouterProfil(string $nom, ?int $age = null): Profil
    {
        $nom = trim($nom);
        if (count($this->profils) >= $this->forfait->maxProfils()) {
            throw new ForfaitPleinException('Ton forfait ' . $this->forfait->libelle() . ' permet ' . $this->forfait->maxProfils() . ' profils');
        }
        foreach ($this->profils as $p) {
            if (mb_strtolower($p->getNom()) === mb_strtolower($nom)) throw new NomDejaPrisException("Le profil $nom existe déjà");
        }
        return $this->profils[] = new Profil($this, $nom, $age);
    }

    /** @return Profil[] */
    public function getProfils(): array { return array_values($this->profils); }
    public function getForfait(): Forfait { return $this->forfait; }

    public function trouverProfil(int $id): ?Profil
    {
        foreach ($this->profils as $p) if ($p->getId() === $id) return $p;
        return null;
    }
"""

COMPTE_V2_ADD = r"""
    public function retirerProfil(Profil $profil): void
    {
        $adultes = array_filter($this->profils, fn(Profil $p) => !$p->estEnfant());
        if (!$profil->estEnfant() && count($adultes) === 1) {
            throw new DernierAdulteException('Il faut garder au moins un profil adulte');
        }
        $this->profils = array_values(array_filter($this->profils, fn(Profil $p) => $p !== $profil));
    }
"""

COMPTE_V3_ADD = r"""
    public function changerForfait(Forfait $f): void
    {
        $trop = count($this->profils) - $f->maxProfils();
        if ($trop > 0) {
            throw new TropDeProfilsException(sprintf("Supprime d'abord %d profil%s pour passer en %s", $trop, $trop > 1 ? 's' : '', $f->libelle()));
        }
        $this->forfait = $f;
    }
"""

PROFIL_DTO = r"""
final class NouveauProfil
{
    public function __construct(
        #[Assert\NotBlank(message: 'Donne un nom au profil')]
        #[Assert\Length(max: 20, message: '20 caractères maximum')]
        public readonly string $nom,
        #[Assert\Range(min: 0, max: 17, notInRangeMessage: "L'âge d'un profil enfant va de 0 à 17 ans")]
        public readonly ?int $age = null,
    ) {}
}

final class ProfilVue
{
    public function __construct(public readonly int $id, public readonly string $nom, public readonly bool $enfant, public readonly ?int $age) {}

    public static function fromEntity(Profil $p): self
    {
        return new self($p->getId(), $p->getNom(), $p->estEnfant(), $p->getAge());
    }
}
"""

CTRL_V1 = r"""
final class ProfilController extends AbstractController
{
    public function __construct(private Stockage $stockage) {}

    #[Route('/api/profils', methods: ['GET'])]
    public function liste(#[CurrentUser] Compte $compte): JsonResponse
    {
        return $this->json(array_map(ProfilVue::fromEntity(...), $compte->getProfils()));
    }

    #[Route('/api/profils', methods: ['POST'])]
    public function creer(#[MapRequestPayload] NouveauProfil $data, #[CurrentUser] Compte $compte): JsonResponse
    {
        $profil = $compte->ajouterProfil($data->nom, $data->age);
        $this->stockage->enregistrer($profil);

        return $this->json(ProfilVue::fromEntity($profil), 201, ['Location' => '/api/profils/' . $profil->getId()]);
    }
"""

CTRL_V2_ADD = r"""
    #[Route('/api/profils/{id}', methods: ['DELETE'])]
    public function supprimer(int $id, #[CurrentUser] Compte $compte): JsonResponse
    {
        // Le profil d'un autre compte répond 404, comme s'il n'existait pas : on ne révèle rien.
        $profil = $compte->trouverProfil($id) ?? throw new NotFoundHttpException('Profil introuvable');
        $compte->retirerProfil($profil);
        $this->stockage->supprimer($profil);

        return $this->json(null, 204);
    }
"""

profils = FM("fil-profils", "Créer et supprimer un profil", 40,
  "Écrire l'API en écriture des profils de Bobine : créer un profil avec un DTO d'entrée validé, transformer les règles métier (forfait plein, nom pris, dernier adulte) en réponses HTTP claires, supprimer un profil et changer de forfait.",
  "Lire des données, c'est la moitié d'une API. L'autre moitié, c'est écrire : et là, tout peut mal se passer (champ vide, âge de 40 ans pour un enfant, 6e profil, suppression du seul adulte). Chaque refus doit arriver au front avec le bon statut et un message qu'on peut afficher tel quel.",
  ["Le front envoie `POST /api/profils` avec `{ \"nom\": \"Léo\", \"age\": 8 }`", "`#[MapRequestPayload]` remplit `NouveauProfil` et le **valide** : 422 avec la liste des erreurs si c'est faux",
   "`#[CurrentUser]` donne le compte connecté (401 sinon)", "Le contrôleur appelle l'entité (`$compte->ajouterProfil()`), qui applique les **règles métier**",
   "Une règle violée lève une exception typée `#[WithHttpStatus(409)]` → 409 avec le message ; sinon **201** + en-tête `Location`"],
  ["Deux sortes de refus : 422 (la demande est mal formée : nom vide, âge 40) et 409 (la demande est bien formée mais contredit l'état : forfait plein, nom pris).",
   "Les règles métier restent dans l'entité ; le contrôleur ne fait que traduire HTTP ↔ métier.",
   "Une exception par règle, avec `#[WithHttpStatus(409)]` : plus besoin de `try/catch` dans chaque contrôleur.",
   "On ne touche qu'aux profils **du compte connecté** : un id d'un autre compte répond 404, pas 403 (on ne confirme pas qu'il existe).",
   "201 Created + `Location` pour une création, 204 No Content pour une suppression."],
  ["Mettre `if (count(...) >= 2)` dans le contrôleur.", "Répondre 500 (exception non gérée) ou 200 avec `{\"ok\": false}` pour un refus métier.", "Chercher le profil par id dans toute la base, sans vérifier qu'il appartient au compte."],
  [Q("Le front envoie `{\"nom\": \"\"}`. La réponse :",
     ["400", "409", "422 avec « Donne un nom au profil »", "201"], 2,
     "La demande est mal formée : c'est la validation du DTO, avant même le code métier."),
   Q("Un compte Essentiel a déjà 2 profils et en crée un 3e. La réponse :",
     ["422", "409 « Ton forfait Essentiel permet 2 profils »", "403", "500"], 1,
     "La demande est bien formée mais contredit l'état du compte : conflit, 409."),
   Q("Ana tente `DELETE /api/profils/57`, un profil qui appartient à un autre compte :",
     ["403 Interdit", "404 Profil introuvable", "204", "409"], 1,
     "Répondre 403 confirmerait que le profil 57 existe. 404 ne révèle rien.")],
  prereq=[
    P("`#[MapRequestPayload]`", "Attribut Symfony qui transforme le JSON reçu en DTO, puis le valide ; 422 si une contrainte échoue."),
    P("`#[CurrentUser]`", "Donne l'utilisateur connecté (ici le compte) au contrôleur ; 401 si personne n'est connecté."),
    P("`#[WithHttpStatus(409)]`", "Attribut posé sur une classe d'exception : Symfony répond avec ce statut quand elle est levée."),
    P("422 / 409", "422 : la demande est mal formée (contraintes du DTO). 409 Conflict : bien formée, mais incompatible avec l'état actuel."),
    P("201 / 204", "201 Created : ressource créée (avec l'en-tête `Location`). 204 No Content : réussi, rien à renvoyer."),
  ],
  diagram=D(
    nodes=[
      N("front", 0, 0, "React", "POST /api/profils\n{ nom, age }", color="accent"),
      N("dto", 1, 0, "NouveauProfil", "MapRequestPayload\n+ validation", kind="file"),
      N("ctrl", 2, 0, "Contrôleur", "#[CurrentUser] Compte"),
      N("ent", 3, 0, "Compte", "ajouterProfil()\nrègles métier", kind="db"),
      N("v422", 1, 1, "422", "nom vide · âge 40", kind="note", color="warn"),
      N("v409", 3, 1, "409", "forfait plein\nnom pris", kind="note", color="bad"),
      N("v201", 2, 1, "201 + Location", "ProfilVue", kind="pill", color="good"),
    ],
    edges=[E("front", "dto"), E("dto", "ctrl"), E("ctrl", "ent"), E("dto", "v422", dashed=True), E("ent", "v409", dashed=True), E("ctrl", "v201", color="good")],
    lanes=[LANE("Front", 0, 0, "accent"), LANE("API", 1, 2, "warn"), LANE("Métier", 3, 3, "tc")],
    caption="Deux filets : le DTO arrête ce qui est mal formé (422), l'entité arrête ce qui contredit l'état (409). Le reste devient un 201."),
  lessons=[
    L("Le DTO d'entrée : ce que le client a le droit d'envoyer", r"""
Le front envoie du JSON. Un DTO décrit exactement ce qui est accepté, avec ses contraintes et des **messages prêts à afficher** :

```php:src/Dto/NouveauProfil.php
final class NouveauProfil
{
    public function __construct(
        #[Assert\NotBlank(message: 'Donne un nom au profil')]
        #[Assert\Length(max: 20, message: '20 caractères maximum')]
        public readonly string $nom,
        #[Assert\Range(min: 0, max: 17, notInRangeMessage: "L'âge d'un profil enfant va de 0 à 17 ans")]
        public readonly ?int $age = null,   // null = profil adulte
    ) {}
}
```

Le client ne choisit **pas** l'id, ni le compte : il n'y a pas de champ pour ça. Le compte vient de la session :

```php
#[Route('/api/profils', methods: ['POST'])]
public function creer(#[MapRequestPayload] NouveauProfil $data, #[CurrentUser] Compte $compte): JsonResponse
{
    $profil = $compte->ajouterProfil($data->nom, $data->age);
    $this->stockage->enregistrer($profil);   // persist + flush dans le vrai projet
    return $this->json(ProfilVue::fromEntity($profil), 201, ['Location' => '/api/profils/' . $profil->getId()]);
}
```
"""),
    L("Des exceptions qui portent leur statut", r"""
Les règles métier sont dans `Compte` (module 2). Quand l'une d'elles dit non, elle lève une exception **typée** :

```php
#[WithHttpStatus(409)]
final class ForfaitPleinException extends \DomainException {}
```

Symfony voit l'attribut et répond `409 {"error": "Ton forfait Essentiel permet 2 profils"}`. Le contrôleur n'a **aucun** `try/catch` : il reste court, et la même règle donne la même réponse partout.

| Situation | Qui dit non | Statut |
|---|---|---|
| pas connecté | `#[CurrentUser]` | 401 |
| `nom` vide, `age: 40` | le DTO | 422 |
| 3e profil en Essentiel, nom déjà pris | l'entité | 409 |
| profil d'un autre compte | le contrôleur (recherche dans le compte) | 404 |
| supprimer le dernier adulte | l'entité | 409 |

Le front peut afficher `error` tel quel : le message est écrit pour une personne, pas pour un développeur.
"""),
    L("Supprimer sans rien révéler", r"""
La route `DELETE /api/profils/{id}`. Ce qu'il faut savoir pour la lire : `#[CurrentUser] Compte $compte` donne le compte connecté ; `trouverProfil($id) ?? throw new NotFoundHttpException(...)` cherche le profil et, s'il n'y en a pas (`null`), lève tout de suite une exception qui devient une réponse 404 ; `$this->json(null, 204)` répond « réussi, sans contenu ».

```php
#[Route('/api/profils/{id}', methods: ['DELETE'])]
public function supprimer(int $id, #[CurrentUser] Compte $compte): JsonResponse
{
    $profil = $compte->trouverProfil($id) ?? throw new NotFoundHttpException('Profil introuvable');
    $compte->retirerProfil($profil);      // refuse de supprimer le dernier adulte
    $this->stockage->supprimer($profil);
    return $this->json(null, 204);
}
```

- On cherche le profil **dans le compte connecté**, pas dans toute la base. Un id d'un autre compte donne 404 : on ne dit pas « il existe mais il n'est pas à toi ».
- La règle « au moins un adulte » est dans `Compte::retirerProfil()` : sans adulte, plus personne ne pourrait gérer le compte ni le contrôle parental.
- 204 : réussi, pas de corps de réponse.
"""),
  ],
  recap=["DTO d'entrée : seulement les champs autorisés, avec des messages prêts à afficher.", "Le compte vient de `#[CurrentUser]`, jamais du JSON.",
         "422 = mal formé (DTO) ; 409 = contredit l'état (entité) ; 404 = pas dans ton compte.", "Une exception typée `#[WithHttpStatus]` par règle : pas de try/catch dans le contrôleur.",
         "201 + Location pour créer, 204 pour supprimer."],
  example=[F("src/Controller/ProfilController.php", "php", USES + PROFIL_DTO + CTRL_V1 + "}\n"), F("echanges.http", "plaintext", r"""
POST /api/profils {"nom": "Léo", "age": 8}
-> 201 [Location: /api/profils/12] {"id": 12, "nom": "Léo", "enfant": true, "age": 8}

POST /api/profils {"nom": "", "age": 40}
-> 422 {"title": "Validation Failed", "violations": [
     {"propertyPath": "nom", "title": "Donne un nom au profil"},
     {"propertyPath": "age", "title": "L'âge d'un profil enfant va de 0 à 17 ans"}]}

POST /api/profils {"nom": "Inès", "age": 12}      (compte Essentiel déjà plein)
-> 409 {"error": "Ton forfait Essentiel permet 2 profils"}

DELETE /api/profils/57                            (profil d'un autre compte)
-> 404 {"error": "Profil introuvable"}
""")],
  notes=["Le contrôleur fait trois lignes : recevoir, appeler l'entité, répondre.", "Toutes les erreurs ont un message lisible par une personne.",
         "`ProfilVue` choisit les champs renvoyés (pas le compte, pas l'email)."],
  tds=[
    TD(1, "Créer un profil",
       "Écris le DTO `NouveauProfil`, la vue `ProfilVue` et le contrôleur : `GET /api/profils` (les profils du compte connecté) et `POST /api/profils`. Le compte, ses règles et les exceptions sont fournis." + SSIM,
       ["`NouveauProfil` : `nom` obligatoire (« Donne un nom au profil »), 20 caractères max (« 20 caractères maximum ») ; `age` facultatif de 0 à 17 (« L'âge d'un profil enfant va de 0 à 17 ans »)",
        "`ProfilVue` : `id`, `nom`, `enfant` (booléen), `age`",
        "`POST /api/profils` : 201 + en-tête `Location: /api/profils/{id}` ; le profil est passé à `Stockage::enregistrer()`",
        "`GET /api/profils` : la liste des profils du compte connecté (`#[CurrentUser] Compte`)"],
       [PROFILS_BASE, F("Compte.php", "php", COMPTE_V1 + "}\n"), F("ProfilController.php", "php", r"""
<?php
final class NouveauProfil
{
    // à toi
}

final class ProfilVue
{
    // à toi
}

final class ProfilController extends AbstractController
{
    // à toi
}

App::$user = new Compte('ana@exemple.fr', Forfait::Essentiel, 'Ana');
App::request('POST', '/api/profils', ['nom' => 'Léo', 'age' => 8]);
App::request('POST', '/api/profils', ['nom' => 'Inès', 'age' => 12]);
""")],
       ["`return $this->json($vue, 201, ['Location' => '/api/profils/' . $profil->getId()]);`",
        "`ProfilVue::fromEntity(...)` en « first-class callable » s'utilise directement dans `array_map`.",
        "Le stockage s'injecte dans le constructeur du contrôleur : `public function __construct(private Stockage $stockage) {}`."],
       [F("ProfilController.php", "php", "<?php" + PROFIL_DTO + CTRL_V1 + r"""}

App::$user = new Compte('ana@exemple.fr', Forfait::Essentiel, 'Ana');
App::request('POST', '/api/profils', ['nom' => 'Léo', 'age' => 8]);
App::request('POST', '/api/profils', ['nom' => 'Inès', 'age' => 12]);
""")],
       ["Un profil valide donne 201 + Location", "Les erreurs donnent 422 (DTO), 409 (règles) ou 401 (pas connecté)"],
       run=SRUN(r"""
App::$user = $c = new Compte('test@exemple.fr', Forfait::Essentiel, 'Ana');
$r = App::request('POST', '/api/profils', ['nom' => 'Léo', 'age' => 8]);
check('POST valide → 201', $r->status === 201, (string) $r);
check('Réponse : id, nom, enfant, age', ($r->json['nom'] ?? '') === 'Léo' && ($r->json['enfant'] ?? null) === true && ($r->json['age'] ?? null) === 8 && isset($r->json['id']), (string) $r);
check('En-tête Location: /api/profils/{id}', $r->header('Location') === '/api/profils/' . ($r->json['id'] ?? '?'), (string) $r->header('Location'));
check('Le profil est enregistré dans le Stockage', count(App::get(Stockage::class)->enregistres) === 1);
check('Pas de compte ni d\'email dans la réponse', !str_contains(json_encode($r->json), 'exemple.fr'));
$l = App::request('GET', '/api/profils');
check('GET /api/profils : Ana et Léo', array_map(fn($x) => $x['nom'], $l->json ?? []) === ['Ana', 'Léo'], (string) $l);
check('Ana est un profil adulte (enfant: false, age: null)', ($l->json[0]['enfant'] ?? null) === false && array_key_exists('age', $l->json[0] ?? []) && $l->json[0]['age'] === null);
$v = App::request('POST', '/api/profils', ['nom' => '', 'age' => 40]);
$msgs = array_map(fn($x) => $x['title'] ?? '', $v->json['violations'] ?? []);
check('Nom vide + âge 40 → 422 avec les deux messages', $v->status === 422 && in_array('Donne un nom au profil', $msgs, true) && in_array("L'âge d'un profil enfant va de 0 à 17 ans", $msgs, true), (string) $v);
check('Nom de 21 caractères → 422 « 20 caractères maximum »', in_array('20 caractères maximum', array_map(fn($x) => $x['title'] ?? '', App::request('POST', '/api/profils', ['nom' => str_repeat('a', 21)])->json['violations'] ?? []), true));
$p = App::request('POST', '/api/profils', ['nom' => 'Inès', 'age' => 12]);
check('3e profil en Essentiel → 409 « Ton forfait Essentiel permet 2 profils »', $p->status === 409 && ($p->json['error'] ?? '') === 'Ton forfait Essentiel permet 2 profils', (string) $p);
App::$user = new Compte('b@exemple.fr', Forfait::Standard, 'Ana');
$d = App::request('POST', '/api/profils', ['nom' => ' ana ']);
check('Nom déjà pris → 409', $d->status === 409, (string) $d);
App::$user = null;
check('Pas connecté → 401', App::request('POST', '/api/profils', ['nom' => 'Zoé'])->status === 401);
""")),
    TD(2, "Supprimer un profil, garder un adulte",
       "Ajoute la suppression : `DELETE /api/profils/{id}`. On ne peut supprimer que les profils de son compte, et jamais le dernier profil adulte." + SSIM,
       ["Crée l'exception `DernierAdulteException` (409)",
        "`Compte::retirerProfil(Profil $p)` : refuse avec « Il faut garder au moins un profil adulte » si `$p` est le seul adulte",
        "`DELETE /api/profils/{id}` : profil absent du compte connecté (autre compte ou inexistant) → 404 « Profil introuvable » ; sinon 204 et `Stockage::supprimer()`",
        "Garde le GET et le POST du TD 1"],
       [PROFILS_BASE, F("Compte.php", "php", COMPTE_V1 + r"""
    // à toi : retirerProfil()
}
"""), F("ProfilController.php", "php", "<?php" + PROFIL_DTO + CTRL_V1 + r"""
    // à toi : DELETE /api/profils/{id}
}

// à toi : DernierAdulteException

App::$user = new Compte('ana@exemple.fr', Forfait::Standard, 'Ana');
$leo = App::$user->ajouterProfil('Léo', 8);
App::request('DELETE', '/api/profils/' . $leo->getId());
""")],
       ["`array_filter($this->profils, fn(Profil $p) => !$p->estEnfant())` donne les adultes.",
        "La route : `#[Route('/api/profils/{id}', methods: ['DELETE'])] public function supprimer(int $id, #[CurrentUser] Compte $compte)`.",
        "`return $this->json(null, 204);`"],
       [F("Compte.php", "php", COMPTE_V1 + COMPTE_V2_ADD + "}\n"), F("ProfilController.php", "php", "<?php" + PROFIL_DTO + CTRL_V1 + CTRL_V2_ADD + r"""}

#[WithHttpStatus(409)]
final class DernierAdulteException extends \DomainException {}

App::$user = new Compte('ana@exemple.fr', Forfait::Standard, 'Ana');
$leo = App::$user->ajouterProfil('Léo', 8);
App::request('DELETE', '/api/profils/' . $leo->getId());
""")],
       ["Supprimer un profil de son compte donne 204", "Le dernier adulte et les profils des autres comptes sont protégés"],
       run=SRUN(r"""
App::$user = $c = new Compte('test@exemple.fr', Forfait::Standard, 'Ana');
$ana = $c->getProfils()[0]; $leo = $c->ajouterProfil('Léo', 8); $papi = $c->ajouterProfil('Papi');
$autre = new Compte('autre@exemple.fr', Forfait::Standard, 'Zoé'); $zoe = $autre->getProfils()[0];
$r = App::request('DELETE', '/api/profils/' . $leo->getId());
check('Supprimer Léo → 204', $r->status === 204, (string) $r);
check('Léo a disparu du compte', count($c->getProfils()) === 2);
check('Stockage::supprimer() appelé', count(App::get(Stockage::class)->supprimes) === 1);
check('Supprimer Ana (Papi reste adulte) → 204', App::request('DELETE', '/api/profils/' . $ana->getId())->status === 204);
$d = App::request('DELETE', '/api/profils/' . $papi->getId());
check('Supprimer Papi, le dernier adulte → 409 avec le message', $d->status === 409 && ($d->json['error'] ?? '') === 'Il faut garder au moins un profil adulte', (string) $d);
check('Papi est toujours là', count($c->getProfils()) === 1);
$z = App::request('DELETE', '/api/profils/' . $zoe->getId());
check('Profil d\'un autre compte → 404 « Profil introuvable » (pas 403)', $z->status === 404 && ($z->json['error'] ?? '') === 'Profil introuvable', (string) $z);
check('Le profil de l\'autre compte n\'a pas été supprimé', count($autre->getProfils()) === 1);
check('Profil inexistant → 404', App::request('DELETE', '/api/profils/99999')->status === 404);
$c2 = new Compte('c@exemple.fr', Forfait::Standard, 'Ana'); $e1 = $c2->ajouterProfil('Léo', 8);
App::$user = $c2;
check('Supprimer un enfant quand il ne reste qu\'un adulte → 204', App::request('DELETE', '/api/profils/' . $e1->getId())->status === 204);
check('Le POST du TD 1 marche toujours (201)', App::request('POST', '/api/profils', ['nom' => 'Inès', 'age' => 12])->status === 201);
""")),
    TD(3, "Changer de forfait",
       "Ajoute `GET /api/compte` et `PATCH /api/compte/forfait`. Passer à un forfait plus petit est refusé s'il y a trop de profils, avec un message qui dit combien en supprimer." + SSIM,
       ["Vue `CompteVue` : `forfait` (`'standard'`), `libelle` (`'Standard'`), `maxProfils`, `profils` (nombre), `placesLibres`",
        "`GET /api/compte` → `CompteVue` du compte connecté",
        "`PATCH /api/compte/forfait` avec `{ \"forfait\": \"essentiel\" }` : DTO `ChangementForfait` (obligatoire, valeur parmi essentiel / standard / premium, sinon 422)",
        "`Compte::changerForfait(Forfait $f)` : `TropDeProfilsException` (409) « Supprime d'abord 2 profils pour passer en Essentiel » (« 1 profil » au singulier) ; sinon 200 + `CompteVue`"],
       [PROFILS_BASE, F("Compte.php", "php", COMPTE_V1 + COMPTE_V2_ADD + r"""
    // à toi : changerForfait()
}

#[WithHttpStatus(409)]
final class DernierAdulteException extends \DomainException {}
"""), F("CompteController.php", "php", r"""
<?php
final class ChangementForfait
{
    // à toi
}

final class CompteVue
{
    // à toi
}

final class CompteController extends AbstractController
{
    // à toi : GET /api/compte, PATCH /api/compte/forfait
}

App::$user = new Compte('ana@exemple.fr', Forfait::Standard, 'Ana');
App::request('PATCH', '/api/compte/forfait', ['forfait' => 'premium']);
""")],
       ["`Forfait::from($data->forfait)` transforme la chaîne validée en enum.", "`#[Assert\\Choice(['essentiel', 'standard', 'premium'])]`",
        "`sprintf(\"Supprime d'abord %d profil%s pour passer en %s\", $trop, $trop > 1 ? 's' : '', $f->libelle())`"],
       [F("Compte.php", "php", COMPTE_V1 + COMPTE_V2_ADD + COMPTE_V3_ADD + r"""}

#[WithHttpStatus(409)]
final class DernierAdulteException extends \DomainException {}

#[WithHttpStatus(409)]
final class TropDeProfilsException extends \DomainException {}
"""), F("CompteController.php", "php", r"""
<?php
final class ChangementForfait
{
    public function __construct(
        #[Assert\NotBlank(message: 'Choisis un forfait')]
        #[Assert\Choice(['essentiel', 'standard', 'premium'], message: 'Forfait inconnu')]
        public readonly string $forfait,
    ) {}
}

final class CompteVue
{
    public function __construct(
        public readonly string $forfait, public readonly string $libelle, public readonly int $maxProfils,
        public readonly int $profils, public readonly int $placesLibres,
    ) {}

    public static function fromEntity(Compte $c): self
    {
        $f = $c->getForfait(); $n = count($c->getProfils());
        return new self($f->value, $f->libelle(), $f->maxProfils(), $n, $f->maxProfils() - $n);
    }
}

final class CompteController extends AbstractController
{
    #[Route('/api/compte', methods: ['GET'])]
    public function voir(#[CurrentUser] Compte $compte): JsonResponse
    {
        return $this->json(CompteVue::fromEntity($compte));
    }

    #[Route('/api/compte/forfait', methods: ['PATCH'])]
    public function changerForfait(#[MapRequestPayload] ChangementForfait $data, #[CurrentUser] Compte $compte, Stockage $stockage): JsonResponse
    {
        $compte->changerForfait(Forfait::from($data->forfait));
        $stockage->enregistrer($compte);
        return $this->json(CompteVue::fromEntity($compte));
    }
}

App::$user = new Compte('ana@exemple.fr', Forfait::Standard, 'Ana');
App::request('PATCH', '/api/compte/forfait', ['forfait' => 'premium']);
""")],
       ["Le compte se lit et le forfait change", "Un forfait trop petit est refusé avec le bon nombre de profils à supprimer"],
       run=SRUN(r"""
App::$user = $c = new Compte('test@exemple.fr', Forfait::Standard, 'Ana');
$c->ajouterProfil('Léo', 8); $c->ajouterProfil('Inès', 12); $c->ajouterProfil('Papi');
$g = App::request('GET', '/api/compte');
check('GET /api/compte : standard, 4 profils, 0 place libre', ($g->json ?? null) == ['forfait' => 'standard', 'libelle' => 'Standard', 'maxProfils' => 4, 'profils' => 4, 'placesLibres' => 0], (string) $g);
$e = App::request('PATCH', '/api/compte/forfait', ['forfait' => 'essentiel']);
check('4 profils → Essentiel : 409 « Supprime d\'abord 2 profils pour passer en Essentiel »', $e->status === 409 && ($e->json['error'] ?? '') === "Supprime d'abord 2 profils pour passer en Essentiel", (string) $e);
check('Le forfait n\'a pas changé', $c->getForfait() === Forfait::Standard);
$p = App::request('PATCH', '/api/compte/forfait', ['forfait' => 'premium']);
check('→ Premium : 200, 5 places, 1 libre', $p->status === 200 && ($p->json['forfait'] ?? '') === 'premium' && ($p->json['placesLibres'] ?? -1) === 1, (string) $p);
App::$user = $c3 = new Compte('x@exemple.fr', Forfait::Standard, 'Ana'); $c3->ajouterProfil('Léo', 8); $c3->ajouterProfil('Inès', 12);
$s = App::request('PATCH', '/api/compte/forfait', ['forfait' => 'essentiel']);
check('3 profils → Essentiel : « Supprime d\'abord 1 profil pour passer en Essentiel » (singulier)', ($s->json['error'] ?? '') === "Supprime d'abord 1 profil pour passer en Essentiel", (string) $s);
check('Forfait inconnu → 422', App::request('PATCH', '/api/compte/forfait', ['forfait' => 'gratuit'])->status === 422);
check('Forfait absent → 422', App::request('PATCH', '/api/compte/forfait', [])->status === 422);
App::$user = null;
check('Pas connecté → 401', App::request('GET', '/api/compte')->status === 401);
""")),
  ])

# =========================================================================== 5. Reprise de lecture
REPRISE_BASE = F("bobine.php", "php", USES + r"""
// ---- Fourni : films, profils, horloge, stockage des visionnages ----

final class Film
{
    public function __construct(private int $id, private string $titre, private int $dureeSecondes, private int $ageMinimum) {}
    public function getId(): int { return $this->id; }
    public function getTitre(): string { return $this->titre; }
    public function getDureeSecondes(): int { return $this->dureeSecondes; }
    public function getAgeMinimum(): int { return $this->ageMinimum; }
}

final class FilmRepository
{
    public array $films = [];
    public function __construct()
    {
        foreach ([[1, 'Big Buck Bunny', 596, 0], [3, 'Sintel', 888, 12], [4, 'Tears of Steel', 734, 12], [5, 'Spring', 464, 0], [8, 'Charge', 240, 16], [10, 'La Nuit des projecteurs', 5520, 16]] as [$id, $t, $d, $a]) {
            $this->films[$id] = new Film($id, $t, $d, $a);
        }
    }
    public function find(int $id): ?Film { return $this->films[$id] ?? null; }
}

final class Profil
{
    public function __construct(private int $id, private string $nom, private ?int $age) {}
    public function getId(): int { return $this->id; }
    public function getNom(): string { return $this->nom; }
    public function peutVoir(Film $f): bool { return $this->age === null || $this->age >= $f->getAgeMinimum(); }
}

/** L'heure courante passe par un service : dans les tests, on la fixe. */
interface Horloge { public function maintenant(): \DateTimeImmutable; }

final class HorlogeFixe implements Horloge
{
    public \DateTimeImmutable $t;
    public function __construct() { $this->t = new \DateTimeImmutable('2026-11-20 20:00:00'); }
    public function maintenant(): \DateTimeImmutable { return $this->t; }
    public function avancer(string $duree): void { $this->t = $this->t->modify($duree); }
}

final class VisionnageRepository
{
    /** @var array<string, Visionnage> */
    public array $tous = [];
    public int $ecritures = 0;
    public function trouver(Profil $p, Film $f): ?Visionnage { return $this->tous[$p->getId() . '-' . $f->getId()] ?? null; }
    public function enregistrer(Visionnage $v): void { $this->tous[$v->getProfil()->getId() . '-' . $v->getFilm()->getId()] = $v; $this->ecritures++; }
    /** @return Visionnage[] */
    public function duProfil(Profil $p): array { return array_values(array_filter($this->tous, fn(Visionnage $v) => $v->getProfil() === $p)); }
}
""")

VIS_V1 = r"""
<?php
final class Visionnage
{
    private int $position = 0;
    private int $dernierEnvoi = 0;
    private \DateTimeImmutable $majLe;

    public function __construct(private Profil $profil, private Film $film, \DateTimeImmutable $maintenant)
    {
        $this->majLe = $maintenant;
    }

    public function getProfil(): Profil { return $this->profil; }
    public function getFilm(): Film { return $this->film; }
    public function getPosition(): int { return $this->position; }
    public function getMajLe(): \DateTimeImmutable { return $this->majLe; }

    public function avancer(int $position, \DateTimeImmutable $maintenant): void
    {
        if ($position < 0) throw new \InvalidArgumentException('Position invalide');
        $this->position = min($position, $this->film->getDureeSecondes());
        $this->majLe = $maintenant;
    }

    public function etat(): string
    {
        $d = $this->film->getDureeSecondes();
        if ($this->position >= $d * 0.95) return 'termine';
        if ($this->position < 60) return 'non-commence';
        return 'en-cours';
    }

    public function reprendreA(): int { return $this->etat() === 'en-cours' ? $this->position : 0; }
"""

VIS_V2_ADD = r"""
    /** Applique la position seulement si l'envoi est plus récent que le dernier reçu. */
    public function recevoir(int $position, int $envoi, \DateTimeImmutable $maintenant): bool
    {
        if ($envoi <= $this->dernierEnvoi) return false;
        $this->dernierEnvoi = $envoi;
        $this->avancer($position, $maintenant);
        return true;
    }
"""

POS_DTO_V1 = r"""
final class NouvellePosition
{
    public function __construct(#[Assert\PositiveOrZero(message: 'Position invalide')] public readonly int $position) {}
}

final class VisionnageVue
{
    public function __construct(public readonly int $filmId, public readonly int $position, public readonly string $etat, public readonly int $reprendreA) {}

    public static function fromEntity(Visionnage $v): self
    {
        return new self($v->getFilm()->getId(), $v->getPosition(), $v->etat(), $v->reprendreA());
    }
}
"""

POS_CTRL_V1 = r"""
final class VisionnageController extends AbstractController
{
    public function __construct(private FilmRepository $films, private VisionnageRepository $visionnages, private Horloge $horloge) {}

    #[Route('/api/visionnages/{filmId}', methods: ['PUT'])]
    public function enregistrer(int $filmId, #[MapRequestPayload] NouvellePosition $data, #[CurrentUser] Profil $profil): JsonResponse
    {
        $film = $this->filmVisible($filmId, $profil);
        $v = $this->visionnages->trouver($profil, $film) ?? new Visionnage($profil, $film, $this->horloge->maintenant());
        $v->avancer($data->position, $this->horloge->maintenant());
        $this->visionnages->enregistrer($v);

        return $this->json(VisionnageVue::fromEntity($v));
    }

    private function filmVisible(int $id, Profil $profil): Film
    {
        $film = $this->films->find($id) ?? throw new NotFoundHttpException("Ce film n'est plus disponible");
        if (!$profil->peutVoir($film)) throw new AccessDeniedHttpException("Ce film n'est pas disponible pour ce profil");
        return $film;
    }
"""

TESTS_SETUP = "App::set(Horloge::class, $h = new HorlogeFixe());\n"

reprise = FM("fil-reprise", "Reprendre la lecture", 40,
  "Enregistrer où chaque profil s'est arrêté dans une vidéo, sans doublon et sans retour en arrière quand deux requêtes arrivent dans le désordre, puis construire la rangée « Continuer à regarder ».",
  "Le lecteur envoie la position toutes les 10 secondes, sur des réseaux instables, parfois depuis deux écrans. Sans précaution, on crée des doublons, une vieille requête efface une position plus récente, ou la rangée « Continuer à regarder » affiche des films finis. C'est le genre de bug que tout le monde remarque.",
  ["Le lecteur envoie `PUT /api/visionnages/{filmId}` avec `{ position, envoi }` toutes les 10 s et à la pause", "Le serveur trouve **le** visionnage du couple profil + film, ou le crée (pas de doublon)",
   "Il ignore un envoi **plus ancien** que le dernier reçu (numéro `envoi` croissant)", "Il ramène la position à la durée et calcule l'état (non commencé, en cours, terminé)",
   "`GET /api/continuer` liste les films **en cours**, du plus récent au plus ancien"],
  ["`PUT` est **idempotent** : envoyer deux fois la même requête laisse le même état (on remplace la position, on n'additionne pas).",
   "Un seul visionnage par profil et par film : on cherche avant de créer (en base : contrainte unique `profil_id, film_id`).",
   "Les requêtes peuvent arriver dans le désordre : un numéro d'envoi croissant (côté client) permet d'ignorer les vieilles.",
   "L'heure passe par un service `Horloge` : en test, on la fixe et on l'avance à la main.",
   "La règle d'état (60 s, 95 %) est celle du module 1, maintenant dans l'entité."],
  ["Utiliser `POST` et créer une ligne à chaque envoi (des milliers de lignes par film).", "Additionner les positions au lieu de les remplacer.", "Appeler `new \\DateTimeImmutable()` partout : impossible à tester."],
  [Q("Le lecteur renvoie deux fois `PUT /api/visionnages/3 {\"position\": 360, \"envoi\": 12}` (réseau capricieux). Résultat :",
     ["deux visionnages", "la position passe à 720", "une seule position, 360 : la 2e requête ne change rien", "une erreur 409"], 2,
     "PUT est idempotent, et l'envoi n°12 déjà reçu est ignoré."),
   Q("L'envoi n°15 (position 500) arrive, puis l'envoi n°14 (position 480), en retard. La position finale :",
     ["480", "500", "980", "0"], 1,
     "Le n°14 est plus ancien que le dernier reçu (15) : on l'ignore."),
   Q("Pourquoi injecter une `Horloge` au lieu d'écrire `new \\DateTimeImmutable()` ?",
     ["C'est plus rapide", "Pour pouvoir fixer et avancer l'heure dans les tests", "Doctrine l'exige", "Pour le fuseau horaire"], 1,
     "« Du plus récent au plus ancien » se teste seulement si on maîtrise l'heure.")],
  prereq=[
    P("Idempotent", "Une requête qu'on peut répéter sans changer le résultat : `PUT position=360` deux fois donne 360, pas 720."),
    P("Upsert", "Mettre à jour si ça existe, créer sinon (« update or insert »)."),
    P("Numéro d'envoi", "Un compteur que le client augmente à chaque envoi ; le serveur garde le plus grand reçu et ignore les plus petits."),
    P("Horloge injectée", "Un service qui donne l'heure courante ; en test, une version fixe qu'on avance à la main."),
    P("Contrainte unique", "En base, `UNIQUE (profil_id, film_id)` interdit deux visionnages pour le même couple."),
  ],
  diagram=D(
    nodes=[
      N("player", 0, 0, "Lecteur", "toutes les 10 s\n+ à la pause", color="accent"),
      N("put", 1, 0, "PUT /visionnages/3", "{ position, envoi }", kind="pill"),
      N("find", 2, 0, "trouver ou créer", "profil + film", kind="db"),
      N("seq", 3, 0, "envoi > dernier ?", "sinon : ignoré", kind="note", color="warn"),
      N("etat", 3, 1, "état", "60 s · 95 %", kind="file", color="good"),
      N("cont", 1, 1, "GET /continuer", "en cours, récents\nd'abord", kind="pill", color="good"),
      N("home", 0, 1, "Accueil", "rangée « Continuer\nà regarder »", color="accent"),
    ],
    edges=[E("player", "put"), E("put", "find"), E("find", "seq"), E("seq", "etat"), E("etat", "cont", dashed=True), E("cont", "home", color="good")],
    lanes=[LANE("Front", 0, 0, "accent"), LANE("API", 1, 1, "warn"), LANE("Métier", 2, 3, "tc")],
    caption="Un visionnage par profil et par film, mis à jour (jamais dupliqué), protégé contre les envois en retard ; la rangée n'affiche que ce qui est en cours."),
  lessons=[
    L("PUT plutôt que POST : remplacer, pas ajouter", r"""
Le lecteur envoie souvent la même information (« j'en suis à 6 min »). `POST /api/visionnages` créerait une ligne à chaque fois ; on veut au contraire **une** ligne par profil et par film, qu'on met à jour.

```http
PUT /api/visionnages/3   {"position": 360, "envoi": 12}
-> 200 {"filmId": 3, "position": 360, "etat": "en-cours", "reprendreA": 360}
```

`PUT` dit « voici la nouvelle valeur ». Répété, il donne le même résultat : c'est ce qu'on appelle **idempotent**. Côté serveur :

```php
$v = $this->visionnages->trouver($profil, $film) ?? new Visionnage($profil, $film, $this->horloge->maintenant());
$v->avancer($data->position, $this->horloge->maintenant());
$this->visionnages->enregistrer($v);
```

En base, une **contrainte unique** `(profil_id, film_id)` garantit qu'il ne peut pas y avoir deux lignes, même si deux requêtes arrivent exactement en même temps.
"""),
    L("Les requêtes en retard", r"""
Les requêtes ne voyagent pas toujours dans l'ordre. Le lecteur envoie :

| Envoi | Position | Arrive au serveur |
|---|---|---|
| n° 14 | 480 s | en 2e (réseau lent) |
| n° 15 | 500 s | en 1er |

Sans précaution, la position finale serait 480 : on recule. Solution : le client numérote ses envois, le serveur garde le plus grand numéro reçu et **ignore** les plus petits :

```php
public function recevoir(int $position, int $envoi, \DateTimeImmutable $maintenant): bool
{
    if ($envoi <= $this->dernierEnvoi) return false;   // plus ancien (ou déjà reçu) : ignoré
    $this->dernierEnvoi = $envoi;
    $this->avancer($position, $maintenant);
    return true;
}
```

La réponse reste **200** avec l'état actuel : pour le client, ce n'est pas une erreur, c'est juste « déjà à jour ».
"""),
    L("L'heure est une dépendance", r"""
« Continuer à regarder » trie par date de mise à jour. Si le code appelle `new \DateTimeImmutable()` directement, deux mises à jour dans le même test ont presque la même heure : le tri devient imprévisible et impossible à tester.

On fait passer l'heure par un **service** :

```php
interface Horloge { public function maintenant(): \DateTimeImmutable; }
```

En production, une implémentation renvoie l'heure réelle (Symfony fournit `ClockInterface` pour ça). En test, `HorlogeFixe` donne une heure fixe qu'on avance à la main :

```php
$h->avancer('+5 minutes');
```

Même idée que l'injection de dépendances du parcours PHP : ce qui varie (l'heure, le hasard, le réseau) entre par le constructeur.
"""),
  ],
  recap=["PUT idempotent : une ligne par profil et par film, mise à jour.", "Un numéro d'envoi croissant protège des requêtes en retard (200, pas d'erreur).",
         "Position ramenée à la durée ; état calculé par l'entité (60 s, 95 %).", "L'heure entre par un service `Horloge`.",
         "« Continuer à regarder » = en cours seulement, récents d'abord."],
  example=[F("src/Entity/Visionnage.php", "php", VIS_V1 + VIS_V2_ADD + "}\n"), F("echanges.http", "plaintext", r"""
PUT /api/visionnages/3 {"position": 360, "envoi": 12}
-> 200 {"filmId": 3, "position": 360, "etat": "en-cours", "reprendreA": 360}

PUT /api/visionnages/3 {"position": 360, "envoi": 12}       (répétée)
-> 200 {"filmId": 3, "position": 360, "etat": "en-cours", "reprendreA": 360}

PUT /api/visionnages/3 {"position": 350, "envoi": 11}       (en retard)
-> 200 {"filmId": 3, "position": 360, ...}                   (ignorée)

GET /api/continuer
-> 200 [{"filmId": 3, "titre": "Sintel", "reprendreA": 360, "pourcentage": 40, "restant": "9 min"}]
""")],
  notes=["`recevoir()` renvoie `false` pour un envoi ignoré : le contrôleur répond quand même 200.",
         "`avancer()` ramène une position trop grande à la durée.", "L'état se calcule, il ne se stocke pas : impossible qu'il soit faux."],
  tds=[
    TD(1, "Enregistrer la position",
       "Écris l'entité `Visionnage` et `PUT /api/visionnages/{filmId}`. Le profil connecté est donné par `#[CurrentUser] Profil`." + SSIM,
       ["`Visionnage(Profil, Film, DateTimeImmutable $maintenant)` : `position` (0 au départ), `majLe` ; getters `getProfil()`, `getFilm()`, `getPosition()`, `getMajLe()`",
        "`avancer(int $position, DateTimeImmutable $maintenant)` : négatif → `InvalidArgumentException` ; au-delà de la durée → ramené à la durée",
        "`etat()` : `'termine'` si ≥ 95 % de la durée, `'non-commence'` sous 60 s, sinon `'en-cours'` ; `reprendreA()` : la position si en cours, sinon 0",
        "`PUT` avec `{ position }` (≥ 0, sinon 422) : film inconnu → 404 « Ce film n'est plus disponible » ; interdit au profil → 403 ; trouve ou crée le visionnage, l'enregistre, répond `{ filmId, position, etat, reprendreA }`",
        "L'heure vient du service `Horloge` (injecté), jamais de `new DateTimeImmutable()`"],
       [REPRISE_BASE, F("Visionnage.php", "php", r"""
<?php
final class Visionnage
{
    // à toi
}
"""), F("VisionnageController.php", "php", r"""
<?php
// à toi : NouvellePosition, VisionnageVue, VisionnageController

App::set(Horloge::class, new HorlogeFixe());
App::$user = new Profil(2, 'Léo', 8);
App::request('PUT', '/api/visionnages/1', ['position' => 360]);
""")],
       ["Le contrôleur reçoit ses services par le constructeur : `public function __construct(private FilmRepository $films, private VisionnageRepository $visionnages, private Horloge $horloge) {}`.",
        "Trouver ou créer : `$repo->trouver($profil, $film) ?? new Visionnage(...)`.",
        "Pour un film très court, la règle des 95 % passe avant celle des 60 s."],
       [F("Visionnage.php", "php", VIS_V1 + "}\n"), F("VisionnageController.php", "php", "<?php" + POS_DTO_V1 + POS_CTRL_V1 + r"""}

App::set(Horloge::class, new HorlogeFixe());
App::$user = new Profil(2, 'Léo', 8);
App::request('PUT', '/api/visionnages/1', ['position' => 360]);
""")],
       ["La position est enregistrée, l'état est juste", "Un seul visionnage par profil et par film ; 404, 403 et 422 selon le cas"],
       run=SRUN(TESTS_SETUP + r"""
App::$user = $leo = new Profil(2, 'Léo', 8);
$r = App::request('PUT', '/api/visionnages/1', ['position' => 360]);
check('PUT 360 s sur Big Buck Bunny → 200 en-cours, reprendre à 360', $r->status === 200 && ($r->json ?? null) == ['filmId' => 1, 'position' => 360, 'etat' => 'en-cours', 'reprendreA' => 360], (string) $r);
$repo = App::get(VisionnageRepository::class);
App::request('PUT', '/api/visionnages/1', ['position' => 420]);
check('Deux PUT sur le même film : un seul visionnage (pas de doublon)', count($repo->tous) === 1);
check('La position est remplacée (420), pas additionnée', $repo->trouver($leo, App::get(FilmRepository::class)->find(1))?->getPosition() === 420);
check('40 s → non-commence, reprendre à 0', (App::request('PUT', '/api/visionnages/5', ['position' => 40])->json['etat'] ?? '') === 'non-commence');
$t = App::request('PUT', '/api/visionnages/5', ['position' => 9999]);
check('Position au-delà de la durée → ramenée à 464, terminé', ($t->json['position'] ?? 0) === 464 && ($t->json['etat'] ?? '') === 'termine' && ($t->json['reprendreA'] ?? -1) === 0, (string) $t);
check('Position -5 → 422', App::request('PUT', '/api/visionnages/1', ['position' => -5])->status === 422);
$nf = App::request('PUT', '/api/visionnages/42', ['position' => 10]);
check('Film inconnu → 404 « Ce film n\'est plus disponible »', $nf->status === 404 && ($nf->json['error'] ?? '') === "Ce film n'est plus disponible", (string) $nf);
check('Charge (16 ans) pour Léo → 403', App::request('PUT', '/api/visionnages/8', ['position' => 10])->status === 403);
$h->avancer('+1 hour');
App::request('PUT', '/api/visionnages/1', ['position' => 430]);
check('majLe vient de l\'Horloge (21:00)', $repo->trouver($leo, App::get(FilmRepository::class)->find(1))?->getMajLe()->format('H:i') === '21:00');
App::$user = $ana = new Profil(1, 'Ana', null);
App::request('PUT', '/api/visionnages/1', ['position' => 100]);
check('Ana a son propre visionnage (la position appartient au profil)', count($repo->tous) === 3 && $repo->trouver($leo, App::get(FilmRepository::class)->find(1))?->getPosition() === 430);
App::$user = null;
check('Pas de profil → 401', App::request('PUT', '/api/visionnages/1', ['position' => 10])->status === 401);
""")),
    TD(2, "Deux écrans et des requêtes en retard",
       "Le lecteur numérote ses envois. Ajoute `envoi` : un envoi plus ancien que le dernier reçu est ignoré (réponse 200 avec l'état actuel). Ajoute aussi `GET /api/visionnages/{filmId}` pour que le lecteur sache où reprendre." + SSIM,
       ["`NouvellePosition` : `position` (≥ 0) et `envoi` (entier ≥ 1, obligatoire)",
        "`Visionnage::recevoir(int $position, int $envoi, DateTimeImmutable $maintenant): bool` : ignore (renvoie `false`) si `envoi` ≤ dernier envoi reçu",
        "Un envoi ignoré n'est **pas** réenregistré (`VisionnageRepository::$ecritures` ne bouge pas) ; la réponse est 200 avec l'état actuel",
        "`GET /api/visionnages/{filmId}` : l'état du visionnage, ou `{ filmId, position: 0, etat: 'non-commence', reprendreA: 0 }` s'il n'existe pas ; mêmes 404 / 403"],
       [REPRISE_BASE, F("Visionnage.php", "php", VIS_V1 + r"""
    // à toi : recevoir()
}
"""), F("VisionnageController.php", "php", "<?php" + POS_DTO_V1 + POS_CTRL_V1 + r"""
    // à toi : utiliser envoi, et GET /api/visionnages/{filmId}
}

App::set(Horloge::class, new HorlogeFixe());
App::$user = new Profil(2, 'Léo', 8);
App::request('PUT', '/api/visionnages/1', ['position' => 500, 'envoi' => 15]);
App::request('PUT', '/api/visionnages/1', ['position' => 480, 'envoi' => 14]);
""")],
       ["Le visionnage garde `private int $dernierEnvoi = 0;`.", "Dans le contrôleur : `if ($v->recevoir($data->position, $data->envoi, $maintenant)) $this->visionnages->enregistrer($v);`",
        "Pour le GET sans visionnage, renvoie directement le tableau `['filmId' => ..., 'position' => 0, ...]`."],
       [F("Visionnage.php", "php", VIS_V1 + VIS_V2_ADD + "}\n"), F("VisionnageController.php", "php", r"""
<?php
final class NouvellePosition
{
    public function __construct(
        #[Assert\PositiveOrZero(message: 'Position invalide')] public readonly int $position,
        #[Assert\Positive(message: 'Numéro d\'envoi invalide')] public readonly int $envoi,
    ) {}
}

final class VisionnageVue
{
    public function __construct(public readonly int $filmId, public readonly int $position, public readonly string $etat, public readonly int $reprendreA) {}

    public static function fromEntity(Visionnage $v): self
    {
        return new self($v->getFilm()->getId(), $v->getPosition(), $v->etat(), $v->reprendreA());
    }
}

final class VisionnageController extends AbstractController
{
    public function __construct(private FilmRepository $films, private VisionnageRepository $visionnages, private Horloge $horloge) {}

    #[Route('/api/visionnages/{filmId}', methods: ['PUT'])]
    public function enregistrer(int $filmId, #[MapRequestPayload] NouvellePosition $data, #[CurrentUser] Profil $profil): JsonResponse
    {
        $film = $this->filmVisible($filmId, $profil);
        $maintenant = $this->horloge->maintenant();
        $v = $this->visionnages->trouver($profil, $film) ?? new Visionnage($profil, $film, $maintenant);
        if ($v->recevoir($data->position, $data->envoi, $maintenant)) {
            $this->visionnages->enregistrer($v);
        }
        return $this->json(VisionnageVue::fromEntity($v));
    }

    #[Route('/api/visionnages/{filmId}', methods: ['GET'])]
    public function voir(int $filmId, #[CurrentUser] Profil $profil): JsonResponse
    {
        $film = $this->filmVisible($filmId, $profil);
        $v = $this->visionnages->trouver($profil, $film);
        return $this->json($v ? VisionnageVue::fromEntity($v) : ['filmId' => $film->getId(), 'position' => 0, 'etat' => 'non-commence', 'reprendreA' => 0]);
    }

    private function filmVisible(int $id, Profil $profil): Film
    {
        $film = $this->films->find($id) ?? throw new NotFoundHttpException("Ce film n'est plus disponible");
        if (!$profil->peutVoir($film)) throw new AccessDeniedHttpException("Ce film n'est pas disponible pour ce profil");
        return $film;
    }
}

App::set(Horloge::class, new HorlogeFixe());
App::$user = new Profil(2, 'Léo', 8);
App::request('PUT', '/api/visionnages/1', ['position' => 500, 'envoi' => 15]);
App::request('PUT', '/api/visionnages/1', ['position' => 480, 'envoi' => 14]);
""")],
       ["Les envois en retard ou répétés sont ignorés", "Le GET dit où reprendre"],
       run=SRUN(TESTS_SETUP + r"""
App::$user = $leo = new Profil(2, 'Léo', 8);
$repo = App::get(VisionnageRepository::class);
$g0 = App::request('GET', '/api/visionnages/5');
check('GET sans visionnage → position 0, non-commence', $g0->status === 200 && ($g0->json ?? null) == ['filmId' => 5, 'position' => 0, 'etat' => 'non-commence', 'reprendreA' => 0], (string) $g0);
$a = App::request('PUT', '/api/visionnages/1', ['position' => 500, 'envoi' => 15]);
check('Envoi 15 (500 s) → 200, position 500', ($a->json['position'] ?? 0) === 500, (string) $a);
$w = $repo->ecritures;
$b = App::request('PUT', '/api/visionnages/1', ['position' => 480, 'envoi' => 14]);
check('Envoi 14 en retard → 200, la position reste 500', $b->status === 200 && ($b->json['position'] ?? 0) === 500, (string) $b);
check('L\'envoi ignoré n\'est pas réenregistré', $repo->ecritures === $w);
$c = App::request('PUT', '/api/visionnages/1', ['position' => 500, 'envoi' => 15]);
check('Envoi 15 répété → ignoré aussi (idempotent)', ($c->json['position'] ?? 0) === 500 && $repo->ecritures === $w);
App::request('PUT', '/api/visionnages/1', ['position' => 520, 'envoi' => 16]);
$g = App::request('GET', '/api/visionnages/1');
check('Envoi 16 accepté ; GET → reprendre à 520', ($g->json['reprendreA'] ?? 0) === 520, (string) $g);
check('Sans envoi → 422', App::request('PUT', '/api/visionnages/1', ['position' => 10])->status === 422);
check('envoi 0 → 422', App::request('PUT', '/api/visionnages/1', ['position' => 10, 'envoi' => 0])->status === 422);
check('GET film interdit → 403 ; film inconnu → 404', App::request('GET', '/api/visionnages/8')->status === 403 && App::request('GET', '/api/visionnages/77')->status === 404);
App::$user = new Profil(1, 'Ana', null);
check('Le compteur d\'envoi est propre à chaque visionnage (Ana, envoi 1 accepté)', (App::request('PUT', '/api/visionnages/1', ['position' => 100, 'envoi' => 1])->json['position'] ?? 0) === 100);
""")),
    TD(3, "La rangée « Continuer à regarder »",
       "Écris `GET /api/continuer` : les films en cours du profil connecté, du plus récemment regardé au plus ancien, avec ce qu'il faut pour afficher une barre de progression." + SSIM,
       ["Seulement les visionnages **en cours** (pas les non commencés, pas les terminés)",
        "Triés par `majLe` décroissant ; 10 au maximum",
        "Chaque élément : `{ filmId, titre, reprendreA, pourcentage, restant }` ; `pourcentage` = position / durée × 100 arrondi à l'entier inférieur ; `restant` = « 9 min » (minutes restantes arrondies au supérieur), « 1 h 05 » au-delà d'une heure",
        "Un film devenu interdit au profil (ou retiré du catalogue) n'apparaît pas"],
       [REPRISE_BASE, F("Visionnage.php", "php", VIS_V1 + VIS_V2_ADD + "}\n"), F("ContinuerController.php", "php", r"""
<?php
final class ContinuerController extends AbstractController
{
    // à toi : GET /api/continuer
}

$h = new HorlogeFixe();
$leo = new Profil(2, 'Léo', 8);
$repo = App::get(VisionnageRepository::class);
$films = App::get(FilmRepository::class);
$v = new Visionnage($leo, $films->find(1), $h->maintenant()); $v->avancer(300, $h->maintenant()); $repo->enregistrer($v);
App::$user = $leo;
App::request('GET', '/api/continuer');
""")],
       ["`usort($liste, fn(Visionnage $a, Visionnage $b) => $b->getMajLe() <=> $a->getMajLe())`",
        "`(int) floor($position * 100 / $duree)` et `(int) ceil(($duree - $position) / 60)`.",
        "Un film retiré : `$films->find($v->getFilm()->getId()) === null`."],
       [F("ContinuerController.php", "php", r"""
<?php
final class ContinuerController extends AbstractController
{
    #[Route('/api/continuer', methods: ['GET'])]
    public function continuer(#[CurrentUser] Profil $profil, VisionnageRepository $visionnages, FilmRepository $films): JsonResponse
    {
        $liste = array_filter($visionnages->duProfil($profil), fn(Visionnage $v) =>
            $v->etat() === 'en-cours'
            && $films->find($v->getFilm()->getId()) !== null
            && $profil->peutVoir($v->getFilm()));
        usort($liste, fn(Visionnage $a, Visionnage $b) => $b->getMajLe() <=> $a->getMajLe());

        return $this->json(array_map(fn(Visionnage $v) => [
            'filmId' => $v->getFilm()->getId(),
            'titre' => $v->getFilm()->getTitre(),
            'reprendreA' => $v->reprendreA(),
            'pourcentage' => (int) floor($v->getPosition() * 100 / $v->getFilm()->getDureeSecondes()),
            'restant' => self::restant($v->getFilm()->getDureeSecondes() - $v->getPosition()),
        ], array_slice($liste, 0, 10)));
    }

    private static function restant(int $secondes): string
    {
        $min = (int) ceil($secondes / 60);
        return $min < 60 ? "$min min" : sprintf('%d h %02d', intdiv($min, 60), $min % 60);
    }
}

$h = new HorlogeFixe();
$leo = new Profil(2, 'Léo', 8);
$repo = App::get(VisionnageRepository::class);
$films = App::get(FilmRepository::class);
$v = new Visionnage($leo, $films->find(1), $h->maintenant()); $v->avancer(300, $h->maintenant()); $repo->enregistrer($v);
App::$user = $leo;
App::request('GET', '/api/continuer');
""")],
       ["Seulement les films en cours, les plus récents d'abord", "Pourcentage et temps restant justes ; films interdits ou retirés exclus"],
       run=SRUN(r"""
$h = new HorlogeFixe();
$repo = App::get(VisionnageRepository::class); $films = App::get(FilmRepository::class);
$ana = new Profil(1, 'Ana', null);
$mk = function (Profil $p, int $id, int $pos) use ($h, $repo, $films) { $v = new Visionnage($p, $films->find($id), $h->maintenant()); $v->avancer($pos, $h->maintenant()); $repo->enregistrer($v); $h->avancer('+10 minutes'); return $v; };
$mk($ana, 1, 300);    // Big Buck Bunny 596 s : 50 %
$mk($ana, 3, 30);     // Sintel : non commencé
$mk($ana, 4, 730);    // Tears of Steel 734 s : terminé
$mk($ana, 10, 1200);  // La Nuit 5520 s : en cours, 72 min restantes
$mk($ana, 5, 100);    // Spring 464 s : en cours (le plus récent)
App::$user = $ana;
$r = App::request('GET', '/api/continuer');
check('200 et une liste', $r->status === 200 && is_array($r->json), (string) $r);
check('En cours seulement, les plus récents d\'abord : Spring, La Nuit, Big Buck Bunny', array_map(fn($x) => $x['filmId'], $r->json ?? []) === [5, 10, 1], json_encode(array_map(fn($x) => $x['filmId'], $r->json ?? [])));
$bbb = array_values(array_filter($r->json ?? [], fn($x) => $x['filmId'] === 1))[0] ?? [];
check('Big Buck Bunny : titre, reprendreA 300, 50 %, « 5 min » restantes', ($bbb['titre'] ?? '') === 'Big Buck Bunny' && ($bbb['reprendreA'] ?? 0) === 300 && ($bbb['pourcentage'] ?? 0) === 50 && ($bbb['restant'] ?? '') === '5 min', json_encode($bbb));
$nuit = array_values(array_filter($r->json ?? [], fn($x) => $x['filmId'] === 10))[0] ?? [];
check('La Nuit : 21 %, « 1 h 12 » restantes', ($nuit['pourcentage'] ?? 0) === 21 && ($nuit['restant'] ?? '') === '1 h 12', json_encode($nuit));
unset($films->films[5]);
check('Spring retiré du catalogue : il disparaît de la rangée', !in_array(5, array_map(fn($x) => $x['filmId'], App::request('GET', '/api/continuer')->json ?? []), true));
$leo = new Profil(2, 'Léo', 8);
$mk($leo, 1, 120);
$vi = new Visionnage($leo, $films->find(10), $h->maintenant()); $vi->avancer(900, $h->maintenant()); $repo->enregistrer($vi);
App::$user = $leo;
check('Léo : seulement ses films autorisés (pas La Nuit, 16 ans), pas ceux d\'Ana', array_map(fn($x) => $x['filmId'], App::request('GET', '/api/continuer')->json ?? []) === [1]);
for ($i = 0; $i < 12; $i++) { $films->films[100 + $i] = new Film(100 + $i, "Court $i", 600, 0); $mk($ana, 100 + $i, 200); }
App::$user = $ana;
check('10 éléments au maximum', count(App::request('GET', '/api/continuer')->json ?? []) === 10);
""")),
  ])

# =========================================================================== 6. Le front React
BOBINE_API = r"""
const db = window.__db = {
  films: [
    { id: 1, titre: 'Big Buck Bunny', annee: 2008, genre: 'animation', duree: '10 min', dureeSecondes: 596, ageMinimum: 0, synopsis: 'Un lapin géant se venge de trois rongeurs farceurs.' },
    { id: 2, titre: 'Elephants Dream', annee: 2006, genre: 'animation', duree: '11 min', dureeSecondes: 654, ageMinimum: 10, synopsis: 'Deux hommes dans une machine étrange.' },
    { id: 3, titre: 'Sintel', annee: 2010, genre: 'animation', duree: '15 min', dureeSecondes: 888, ageMinimum: 12, synopsis: 'Une jeune femme part à la recherche de son dragon.' },
    { id: 4, titre: 'Tears of Steel', annee: 2012, genre: 'sf', duree: '12 min', dureeSecondes: 734, ageMinimum: 12, synopsis: 'Des scientifiques tentent de sauver le monde.' },
    { id: 6, titre: 'Agent 327', annee: 2017, genre: 'action', duree: '4 min', dureeSecondes: 231, ageMinimum: 10, synopsis: 'Un agent secret dans un salon de coiffure.' },
    { id: 8, titre: 'Charge', annee: 2022, genre: 'action', duree: '4 min', dureeSecondes: 240, ageMinimum: 16, synopsis: 'Une chasseuse dans un monde sans énergie.' },
    { id: 10, titre: 'La Nuit des projecteurs', annee: 2024, genre: 'drame', duree: '1 h 32', dureeSecondes: 5520, ageMinimum: 16, synopsis: 'Une projectionniste refuse de fermer son cinéma.' },
  ],
  interdits: [8],
  visionnages: { 3: { position: 360, envoi: 0 } },
  puts: [],
  calls: [],
};
const card = (f) => ({ id: f.id, titre: f.titre, annee: f.annee, genre: f.genre, duree: f.duree, ageMinimum: f.ageMinimum });
__api["GET /api/films"] = (p) => {
  db.calls.push('GET /api/films?' + new URLSearchParams(p).toString());
  let l = db.films;
  if (p.q) l = l.filter((f) => f.titre.toLowerCase().includes(String(p.q).toLowerCase().trim()));
  if (p.genre) l = l.filter((f) => f.genre === p.genre);
  return { items: l.map(card), total: l.length, page: 1, pages: 1 };
};
__api["GET /api/films/:id"] = (p) => {
  db.calls.push('GET /api/films/' + p.id);
  const f = db.films.find((x) => x.id == p.id);
  if (!f) return [404, { error: 'Film introuvable' }];
  if (db.interdits.includes(f.id)) return [403, { error: "Ce film n'est pas disponible pour ce profil" }];
  return { ...card(f), synopsis: f.synopsis };
};
__api["GET /api/visionnages/:id"] = (p) => {
  const f = db.films.find((x) => x.id == p.id); const v = db.visionnages[p.id];
  const pos = v ? v.position : 0;
  const etat = !f ? 'non-commence' : pos >= f.dureeSecondes * 0.95 ? 'termine' : pos < 60 ? 'non-commence' : 'en-cours';
  return { filmId: Number(p.id), position: pos, etat, reprendreA: etat === 'en-cours' ? pos : 0 };
};
__api["PUT /api/visionnages/:id"] = (p, b) => {
  db.puts.push({ id: Number(p.id), ...b });
  const v = db.visionnages[p.id] || { position: 0, envoi: 0 };
  if (b.envoi > v.envoi) db.visionnages[p.id] = { position: b.position, envoi: b.envoi };
  return { filmId: Number(p.id), position: db.visionnages[p.id].position };
};
"""

CLIENT_TS = F("api/client.ts", "ts", r"""
import axios from 'axios';
export const api = axios.create({ baseURL: '/api' });
""")

TYPES_TS = F("api/types.ts", "ts", r"""
export type Genre = 'action' | 'animation' | 'comedie' | 'documentaire' | 'drame' | 'sf';

export type FilmCard = { id: number; titre: string; annee: number; genre: Genre; duree: string; ageMinimum: number };
export type FilmDetail = FilmCard & { synopsis: string };
export type Page<T> = { items: T[]; total: number; page: number; pages: number };
export type Visionnage = { filmId: number; position: number; etat: 'non-commence' | 'en-cours' | 'termine'; reprendreA: number };
""")

APP_CATALOGUE = F("App.tsx", "tsx", r"""
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Catalogue } from './Catalogue';

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Catalogue />
    </QueryClientProvider>
  );
}
""")

CATALOGUE_SOL = r"""
import { useState } from 'react';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { api } from './api/client';
import type { FilmCard, Genre, Page } from './api/types';

const GENRES: { value: Genre | ''; label: string }[] = [
  { value: '', label: 'Tous les genres' },
  { value: 'action', label: 'Action' },
  { value: 'animation', label: 'Animation' },
  { value: 'drame', label: 'Drame' },
  { value: 'sf', label: 'Science-fiction' },
];

async function getFilms(q: string, genre: Genre | ''): Promise<Page<FilmCard>> {
  const r = await api.get<Page<FilmCard>>('/films', { params: { q: q || undefined, genre: genre || undefined } });
  return r.data;
}

export function Catalogue() {
  const [q, setQ] = useState('');
  const [genre, setGenre] = useState<Genre | ''>('');

  const { data, isPending, isError } = useQuery({
    queryKey: ['films', { q, genre }],
    queryFn: () => getFilms(q, genre),
    placeholderData: keepPreviousData,
  });

  return (
    <section>
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Rechercher un film" />
      <select value={genre} onChange={(e) => setGenre(e.target.value as Genre | '')} aria-label="Genre">
        {GENRES.map((g) => <option key={g.value} value={g.value}>{g.label}</option>)}
      </select>
      {isPending && <p>Chargement…</p>}
      {isError && <p role="alert">Impossible de charger le catalogue</p>}
      {data && data.items.length === 0 && <p>Aucun film ne correspond</p>}
      {data && (
        <ul>
          {data.items.map((f) => (
            <li key={f.id}>
              <strong>{f.titre}</strong> <span>{f.duree}</span> {f.ageMinimum > 0 && <span className="age">-{f.ageMinimum}</span>}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
"""

FICHE_SOL = r"""
import axios from 'axios';
import { useQuery } from '@tanstack/react-query';
import { api } from './api/client';
import type { FilmDetail } from './api/types';

async function getFilm(id: number): Promise<FilmDetail> {
  return (await api.get<FilmDetail>(`/films/${id}`)).data;
}

export function Fiche({ id }: { id: number }) {
  const { data, isPending, error } = useQuery({ queryKey: ['film', id], queryFn: () => getFilm(id) });

  if (isPending) return <p>Chargement…</p>;
  if (error) {
    const status = axios.isAxiosError(error) ? error.response?.status : undefined;
    const message = status === 404 ? "Ce film n'existe pas" : status === 403 ? "Ce film n'est pas disponible pour ce profil" : 'Impossible de charger le film';
    return <p role="alert">{message}</p>;
  }

  return (
    <article>
      <h1>{data.titre}</h1>
      <p className="infos">{data.annee} · {data.duree}{data.ageMinimum > 0 ? ` · déconseillé aux moins de ${data.ageMinimum} ans` : ''}</p>
      <p>{data.synopsis}</p>
    </article>
  );
}
"""

SAUVEGARDE_SOL = r"""
export type Envoi = { position: number; envoi: number };

/** Décide quand envoyer la position : toutes les 10 s de lecture, et immédiatement à la pause. */
export class Sauvegarde {
  private dernierePosition = -Infinity;
  private compteur = 0;

  constructor(private envoyer: (e: Envoi) => void) {}

  progression(secondes: number): void {
    const s = Math.floor(secondes);
    if (s - this.dernierePosition >= 10 || s < this.dernierePosition) this.envoie(s);
  }

  pause(secondes: number): void {
    const s = Math.floor(secondes);
    if (s !== this.dernierePosition) this.envoie(s);
  }

  private envoie(s: number): void {
    this.dernierePosition = s;
    this.compteur += 1;
    this.envoyer({ position: s, envoi: this.compteur });
  }
}

export function formatTemps(secondes: number): string {
  const s = Math.floor(secondes);
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60;
  const mm = h ? String(m).padStart(2, '0') : String(m);
  return (h ? h + ':' : '') + mm + ':' + String(r).padStart(2, '0');
}
"""

LECTEUR_SOL = r"""
import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from './api/client';
import type { Visionnage } from './api/types';
import { Sauvegarde, formatTemps } from './sauvegarde';

export function Lecteur({ filmId }: { filmId: number }) {
  const [depart, setDepart] = useState<number | null>(null);
  const { data, isPending } = useQuery({
    queryKey: ['visionnage', filmId],
    queryFn: async () => (await api.get<Visionnage>(`/visionnages/${filmId}`)).data,
  });

  const sauvegarde = useMemo(
    () => new Sauvegarde((e) => { api.put(`/visionnages/${filmId}`, e); }),
    [filmId],
  );

  if (isPending) return <p>Chargement…</p>;

  if (depart === null && data && data.etat === 'en-cours') {
    return (
      <div className="reprise">
        <button onClick={() => setDepart(data.reprendreA)}>Reprendre à {formatTemps(data.reprendreA)}</button>
        <button onClick={() => setDepart(0)}>Revoir depuis le début</button>
      </div>
    );
  }

  return (
    <video
      src={`/videos/${filmId}.mp4`}
      controls
      data-depart={depart ?? 0}
      onLoadedMetadata={(e) => { e.currentTarget.currentTime = depart ?? 0; }}
      onTimeUpdate={(e) => sauvegarde.progression(e.currentTarget.currentTime)}
      onPause={(e) => sauvegarde.pause(e.currentTarget.currentTime)}
    />
  );
}
"""

front = FM("fil-front", "Le front React : catalogue, fiche et lecteur", 45,
  "Construire les écrans de Bobine en React + TypeScript : le catalogue avec recherche et genre (TanStack Query), la fiche d'un film avec ses erreurs 403 et 404, et le lecteur vidéo qui propose de reprendre et sauvegarde la position.",
  "C'est l'écran que tout le monde voit. Les données arrivent de l'API des modules précédents : il faut les typer, gérer le chargement et les erreurs sans écrans blancs, et surtout ne pas inonder le serveur de requêtes (le lecteur produit un événement plusieurs fois par seconde).",
  ["Les **types** (`FilmCard`, `FilmDetail`, `Visionnage`) recopient le contrat de l'API", "`useQuery` charge et met en cache : la clé contient tout ce dont dépend la requête (`['films', { q, genre }]`)",
   "Chaque écran gère trois états : **chargement**, **erreur** (403, 404, autre), **données**", "Le lecteur demande où reprendre (`GET /api/visionnages/3`) et propose « Reprendre à 6:00 »",
   "Pendant la lecture, une petite classe décide **quand** envoyer la position (toutes les 10 s, et à la pause), numérotée"],
  ["Les types du front décrivent exactement les réponses de l'API ; si le contrat change, TypeScript le signale partout.",
   "La clé de requête change quand `q` ou `genre` change : TanStack Query relance la requête toute seule.",
   "Une erreur se lit avec `axios.isAxiosError(error)` et `error.response?.status` : 404 et 403 n'ont pas le même message.",
   "`timeupdate` arrive plusieurs fois par seconde : on n'envoie pas à chaque fois, on regroupe (toutes les 10 s).",
   "La logique d'envoi est une classe TypeScript sans React : elle se teste seule, comme une fonction pure."],
  ["Recopier les données de `useQuery` dans un `useState`.", "Envoyer un `PUT` à chaque `timeupdate`.", "Afficher le même message pour un film interdit et un film inexistant."],
  [Q("Pourquoi `queryKey: ['films', { q, genre }]` et pas seulement `['films']` ?",
     ["C'est plus joli", "Pour que chaque recherche ait son cache et que la requête se relance quand q ou genre change", "TanStack l'exige", "Pour trier"], 1,
     "La clé décrit la requête : tout ce dont elle dépend doit y être."),
   Q("La fiche reçoit une réponse 403. Le message à afficher :",
     ["« Ce film n'existe pas »", "« Ce film n'est pas disponible pour ce profil »", "« Erreur 403 »", "rien"], 1,
     "403 : le film existe, ce profil ne peut pas le voir. Le message doit le dire avec des mots."),
   Q("L'événement `timeupdate` arrive environ 4 fois par seconde. Combien de `PUT` pour 60 s de lecture ?",
     ["240", "60", "6 environ", "1"], 2,
     "On envoie toutes les 10 s (et à la pause) : quelques requêtes au lieu de centaines.")],
  prereq=[
    P("TanStack Query", "Bibliothèque qui charge, met en cache et relance les requêtes (`useQuery`). Parcours Données & API."),
    P("Clé de requête", "Le nom du cache d'une requête : `['films', { q, genre }]`. Une clé différente = une autre entrée en cache."),
    P("Type", "La forme d'une donnée en TypeScript : `type FilmCard = { id: number; titre: string; ... }`. Parcours TypeScript."),
    P("`timeupdate`", "Événement de la balise `<video>` envoyé plusieurs fois par seconde pendant la lecture, avec `currentTime`."),
    P("Throttle", "Limiter la fréquence d'une action : au plus une fois toutes les N secondes, même si l'événement arrive plus souvent."),
  ],
  diagram=D(
    nodes=[
      N("cat", 0, 0, "Catalogue", "useQuery(['films', { q, genre }])", color="accent"),
      N("fiche", 1, 0, "Fiche", "useQuery(['film', id])\n403 / 404", color="accent"),
      N("lect", 2, 0, "Lecteur", "Reprendre à 6:00 ?", color="accent"),
      N("sauv", 2, 1, "Sauvegarde", "toutes les 10 s\n+ pause · envoi n°", kind="file", color="good"),
      N("api", 0, 1, "API Bobine", "GET /films · GET /films/{id}\nGET + PUT /visionnages", kind="db", color="muted"),
    ],
    edges=[E("cat", "fiche", "clic"), E("fiche", "lect", "Lecture"), E("lect", "sauv"), E("sauv", "api", "PUT", dashed=True), E("api", "cat", dashed=True)],
    caption="Trois écrans branchés sur l'API des modules précédents ; la sauvegarde de la position est une petite classe testable à part."),
  lessons=[
    L("Les types : le contrat, côté front", r"""
Les réponses de l'API (module 3) deviennent des types :

```ts:src/api/types.ts
export type Genre = 'action' | 'animation' | 'comedie' | 'documentaire' | 'drame' | 'sf';
export type FilmCard = { id: number; titre: string; annee: number; genre: Genre; duree: string; ageMinimum: number };
export type FilmDetail = FilmCard & { synopsis: string };
export type Page<T> = { items: T[]; total: number; page: number; pages: number };
```

`Page<T>` est un type **générique** : `Page<FilmCard>` pour le catalogue, `Page<Serie>` plus tard. Et `duree` est une chaîne déjà formatée (« 1 h 32 ») : le front affiche, il ne calcule pas.
"""),
    L("Le catalogue et la fiche avec TanStack Query", r"""
Le catalogue utilise **`useQuery`** de TanStack Query. On lui donne une `queryKey` (le nom de la donnée dans le cache, qui inclut les filtres : `['films', { q, genre }]`) et une `queryFn` (la fonction qui charge, ici `getFilms` qui appelle l'API avec axios). Il renvoie `data` (les films), `isPending` (premier chargement en cours) et `isError`. `placeholderData: keepPreviousData` garde l'ancienne liste affichée pendant que la nouvelle charge. Pour la fiche, on lira le statut de l'erreur axios : `axios.isAxiosError(error)` dit si l'erreur vient d'axios, et `error.response?.status` donne le statut (404, 403…).

```tsx
const [q, setQ] = useState('');
const [genre, setGenre] = useState<Genre | ''>('');

const { data, isPending, isError } = useQuery({
  queryKey: ['films', { q, genre }],
  queryFn: () => getFilms(q, genre),
  placeholderData: keepPreviousData,   // garde l'ancienne liste pendant le chargement de la nouvelle
});
```

- Pas de `useEffect`, pas de `useState` pour les films : `data` **est** la liste.
- Taper dans la recherche change la clé → nouvelle requête ; revenir à une recherche déjà faite → réponse immédiate depuis le cache.

Pour la fiche, l'erreur dit **pourquoi** :

```tsx
const status = axios.isAxiosError(error) ? error.response?.status : undefined;
const message = status === 404 ? "Ce film n'existe pas"
  : status === 403 ? "Ce film n'est pas disponible pour ce profil"
  : 'Impossible de charger le film';
```
"""),
    L("Le lecteur : reprendre et sauvegarder sans inonder le serveur", r"""
Au chargement, le lecteur demande où en est le profil (`GET /api/visionnages/3`). Si la vidéo est **en cours**, il propose de reprendre :

```tsx
<button onClick={() => setDepart(data.reprendreA)}>Reprendre à {formatTemps(data.reprendreA)}</button>
<button onClick={() => setDepart(0)}>Revoir depuis le début</button>
```

Pendant la lecture, `<video>` envoie `timeupdate` plusieurs fois par seconde. On ne peut pas envoyer un `PUT` à chaque fois : une petite classe décide **quand** envoyer.

```ts:src/sauvegarde.ts
export class Sauvegarde {
  private dernierePosition = -Infinity;
  private compteur = 0;
  constructor(private envoyer: (e: { position: number; envoi: number }) => void) {}

  progression(secondes: number) { /* envoie si 10 s se sont écoulées depuis le dernier envoi */ }
  pause(secondes: number) { /* envoie tout de suite */ }
}
```

- Le **numéro d'envoi** augmente à chaque envoi : c'est lui qui permet au serveur (module 5) d'ignorer les requêtes en retard.
- La classe ne connaît ni React ni axios : on lui passe une fonction `envoyer`. Elle se teste seule, avec une fausse fonction.
"""),
  ],
  recap=["Les types recopient le contrat de l'API ; `Page<T>` est générique.", "`useQuery` : la clé contient tout ce dont dépend la requête ; pas de copie dans un `useState`.",
         "Trois états par écran ; 403 et 404 ont chacun leur message.", "Le lecteur propose de reprendre si la vidéo est en cours.",
         "La sauvegarde envoie toutes les 10 s et à la pause, avec un numéro croissant."],
  example=[TYPES_TS, F("Catalogue.tsx", "tsx", CATALOGUE_SOL), F("sauvegarde.ts", "ts", SAUVEGARDE_SOL)],
  notes=["`q || undefined` : un paramètre vide n'apparaît pas dans l'URL.", "`placeholderData: keepPreviousData` évite que la liste clignote à chaque lettre tapée.",
         "`Sauvegarde` reçoit `envoyer` en paramètre : c'est de l'injection de dépendance, version TypeScript."],
  tds=[
    TD(1, "Le catalogue",
       "Écris le composant `Catalogue` : un champ de recherche, une liste de genres et la liste des films, chargée avec TanStack Query. L'API de Bobine est simulée (7 films)." ,
       ["`getFilms(q, genre)` appelle `GET /api/films` avec `params` (sans paramètre vide) et renvoie `Page<FilmCard>`",
        "`useQuery` avec la clé `['films', { q, genre }]` ; pas de `useState` pour les films",
        "Un `<input placeholder=\"Rechercher un film\">` et un `<select aria-label=\"Genre\">` (« Tous les genres », Action, Animation, Drame, Science-fiction)",
        "Un `<li>` par film avec le titre et la durée ; « Chargement… » ; « Aucun film ne correspond » si la liste est vide ; erreur → `<p role=\"alert\">Impossible de charger le catalogue</p>`"],
       [CLIENT_TS, TYPES_TS, F("Catalogue.tsx", "tsx", r"""
import { useState } from 'react';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { api } from './api/client';
import type { FilmCard, Genre, Page } from './api/types';

export function Catalogue() {
  // à toi
  return <p>À compléter</p>;
}
"""), APP_CATALOGUE],
       ["`api.get<Page<FilmCard>>('/films', { params: { q: q || undefined, genre: genre || undefined } })`",
        "`onChange={(e) => setGenre(e.target.value as Genre | '')}`",
        "Le message « Aucun film » ne s'affiche que quand `data` existe et que `data.items.length === 0`."],
       [F("Catalogue.tsx", "tsx", CATALOGUE_SOL)],
       ["Le catalogue s'affiche, se filtre et gère ses états", "Pas de copie des données dans un useState"],
       run=RUN("react", entry="App.tsx", api=BOBINE_API, tests=r"""
await waitFor(() => $$('li').length === 7, 4000);
assert.equal($$('li').length, 7, 'Les 7 films sont affichés');
assert.includes($$('li').find((li) => li.textContent.includes('La Nuit')).textContent, '1 h 32', 'La durée formatée est affichée (« 1 h 32 »)');
await type('input', 'sin');
await waitFor(() => $$('li').length === 1, 4000);
assert.includes(text(), 'Sintel', 'Recherche « sin » : Sintel');
assert(window.__db.calls.some((c) => c.includes('q=sin')), 'La recherche part dans les paramètres (?q=sin)');
await type('input', '');
await waitFor(() => $$('li').length === 7, 4000);
await choose('select', 'action');
await waitFor(() => $$('li').length === 2, 4000);
assert(window.__db.calls.some((c) => c.includes('genre=action')), 'Le genre part dans les paramètres (?genre=action)');
assert(!window.__db.calls.some((c) => /q=(&|$)/.test(c)), 'Pas de paramètre q vide dans l\'URL');
await choose('select', '');
await type('input', 'zzz');
await waitFor(() => text().includes('Aucun film ne correspond'), 4000);
assert(true, 'Aucun résultat : message « Aucun film ne correspond »');
assert(!/useState<\s*FilmCard|setFilms/.test(source('Catalogue.tsx')), 'Les films ne sont pas recopiés dans un useState');
assert(/\['films',\s*\{/.test(source('Catalogue.tsx')), 'La clé de requête contient la recherche et le genre');
window.__api['GET /api/films'] = () => [500, { error: 'boom' }];
await type('input', 'erreur');
await waitFor(() => $('[role=alert]'), 4000);
assert.includes($('[role=alert]').textContent, 'Impossible de charger le catalogue', 'Erreur 500 : message d\'erreur');
""")),
    TD(2, "La fiche d'un film et ses erreurs",
       "Écris `Fiche({ id })` : titre, année, durée, mention d'âge et résumé. Une erreur 404 et une erreur 403 n'ont pas le même message.",
       ["`useQuery` avec la clé `['film', id]` et `GET /api/films/{id}` (type `FilmDetail`)",
        "Affiche `<h1>` avec le titre, l'année et la durée, « déconseillé aux moins de 12 ans » si `ageMinimum > 0`, puis le résumé",
        "404 → `<p role=\"alert\">Ce film n'existe pas</p>` ; 403 → « Ce film n'est pas disponible pour ce profil » ; autre → « Impossible de charger le film »",
        "« Chargement… » pendant le chargement"],
       [CLIENT_TS, TYPES_TS, F("Fiche.tsx", "tsx", r"""
import axios from 'axios';
import { useQuery } from '@tanstack/react-query';
import { api } from './api/client';
import type { FilmDetail } from './api/types';

export function Fiche({ id }: { id: number }) {
  // à toi
  return <p>À compléter</p>;
}
"""), F("App.tsx", "tsx", r"""
import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Fiche } from './Fiche';

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

export default function App() {
  const [id, setId] = useState(3);
  return (
    <QueryClientProvider client={queryClient}>
      <nav>
        {[3, 10, 8, 99].map((n) => <button key={n} onClick={() => setId(n)}>Film {n}</button>)}
      </nav>
      <Fiche id={id} />
    </QueryClientProvider>
  );
}
""")],
       ["`axios.isAxiosError(error) ? error.response?.status : undefined`",
        "Avec TypeScript, après `if (isPending) return ...` et `if (error) return ...`, `data` est forcément défini.",
        "La clé `['film', id]` : chaque film a son cache, revenir à un film déjà vu est instantané."],
       [F("Fiche.tsx", "tsx", FICHE_SOL)],
       ["La fiche affiche les informations du film", "404, 403 et autres erreurs ont chacune leur message"],
       run=RUN("react", entry="App.tsx", api=BOBINE_API, tests=r"""
await waitFor(() => $('h1'), 4000);
assert.equal($('h1').textContent, 'Sintel', 'Film 3 : titre Sintel');
assert.includes(text(), '2010', 'L\'année est affichée');
assert.includes(text(), '15 min', 'La durée est affichée');
assert.includes(text(), 'déconseillé aux moins de 12 ans', 'La mention d\'âge est affichée');
assert.includes(text(), 'dragon', 'Le résumé est affiché');
await click(byText('Film 10'));
await waitFor(() => $('h1') && $('h1').textContent.includes('La Nuit'), 4000);
assert.includes(text(), '1 h 32', 'Film 10 : « 1 h 32 »');
await click(byText('Film 8'));
await waitFor(() => $('[role=alert]'), 4000);
assert.equal($('[role=alert]').textContent.trim(), "Ce film n'est pas disponible pour ce profil", '403 : message du contrôle parental');
await click(byText('Film 99'));
await waitFor(() => $('[role=alert]') && $('[role=alert]').textContent.includes('existe'), 4000);
assert.equal($('[role=alert]').textContent.trim(), "Ce film n'existe pas", '404 : « Ce film n\'existe pas »');
const n = window.__db.calls.filter((c) => c === 'GET /api/films/3').length;
await click(byText('Film 3'));
await waitFor(() => $('h1') && $('h1').textContent === 'Sintel', 1500);
assert.equal(window.__db.calls.filter((c) => c === 'GET /api/films/3').length >= n, true, 'Revenir au film 3 : affiché depuis le cache');
""")),
    TD(3, "Le lecteur qui se souvient",
       "Écris la classe `Sauvegarde` (quand envoyer la position) et `formatTemps`, puis le composant `Lecteur` qui propose de reprendre." + JS,
       ["`new Sauvegarde(envoyer)` ; `progression(secondes)` envoie `{ position, envoi }` si au moins **10 s** se sont écoulées depuis le dernier envoi (ou si on est revenu en arrière) ; `pause(secondes)` envoie tout de suite (sauf si la position n'a pas bougé)",
        "Positions arrondies à la seconde inférieure ; `envoi` vaut 1, 2, 3… ; le premier appel à `progression` envoie toujours",
        "`formatTemps(360)` → `'6:00'`, `formatTemps(65)` → `'1:05'`, `formatTemps(3725)` → `'1:02:05'`",
        "`Lecteur({ filmId })` : si `GET /api/visionnages/{filmId}` dit `en-cours`, boutons « Reprendre à 6:00 » et « Revoir depuis le début » ; sinon, ou après le choix, la `<video>` avec `data-depart` (la position de départ) et les événements branchés sur la `Sauvegarde`"],
       [CLIENT_TS, TYPES_TS, F("sauvegarde.ts", "ts", r"""
export type Envoi = { position: number; envoi: number };

export class Sauvegarde {
  constructor(private envoyer: (e: Envoi) => void) {}

  progression(secondes: number): void {
    // à toi
  }

  pause(secondes: number): void {
    // à toi
  }
}

export function formatTemps(secondes: number): string {
  return '';
}
"""), F("Lecteur.tsx", "tsx", r"""
import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from './api/client';
import type { Visionnage } from './api/types';
import { Sauvegarde, formatTemps } from './sauvegarde';

export function Lecteur({ filmId }: { filmId: number }) {
  // à toi
  return <p>À compléter</p>;
}
"""), F("App.tsx", "tsx", r"""
import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Lecteur } from './Lecteur';

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

export default function App() {
  const [id, setId] = useState(3);
  return (
    <QueryClientProvider client={queryClient}>
      <nav>{[3, 1].map((n) => <button key={n} onClick={() => setId(n)}>Film {n}</button>)}</nav>
      <Lecteur key={id} filmId={id} />
    </QueryClientProvider>
  );
}
""")],
       ["Garde la dernière position envoyée : `if (s - this.dernierePosition >= 10 || s < this.dernierePosition) ...` avec `dernierePosition = -Infinity` au départ.",
        "`formatTemps` : heures = `Math.floor(s / 3600)`, minutes = `Math.floor((s % 3600) / 60)`, et `padStart(2, '0')`.",
        "Dans le composant, crée la `Sauvegarde` une seule fois avec `useMemo(() => new Sauvegarde(...), [filmId])`."],
       [F("sauvegarde.ts", "ts", SAUVEGARDE_SOL), F("Lecteur.tsx", "tsx", LECTEUR_SOL)],
       ["La sauvegarde envoie au bon rythme, numérotée", "Le lecteur propose de reprendre au bon endroit"],
       run=RUN("react", entry="App.tsx", api=BOBINE_API, tests=r"""
const { Sauvegarde, formatTemps } = require('./sauvegarde');
const envois = []; const s = new Sauvegarde((e) => envois.push(e));
for (let t = 0; t <= 25; t += 0.25) s.progression(t);
assert.deepEqual(envois.map((e) => e.position), [0, 10, 20], 'Lecture de 0 à 25 s (un événement tous les 0,25 s) : envois à 0, 10 et 20 s seulement');
assert.deepEqual(envois.map((e) => e.envoi), [1, 2, 3], 'Les envois sont numérotés 1, 2, 3');
s.pause(23.7);
assert(envois.length === 4 && envois[3].position === 23 && envois[3].envoi === 4, 'Pause à 23,7 s : envoi immédiat (position 23, envoi 4)', JSON.stringify(envois[3]));
s.pause(23.2);
assert.equal(envois.length, 4, 'Pause à la même seconde : pas de nouvel envoi');
s.progression(5);
assert(envois.length === 5 && envois[4].position === 5, 'Retour en arrière (5 s) : envoi immédiat');
assert.equal(formatTemps(360), '6:00', 'formatTemps(360) → 6:00');
assert.equal(formatTemps(65), '1:05', 'formatTemps(65) → 1:05');
assert.equal(formatTemps(3725), '1:02:05', 'formatTemps(3725) → 1:02:05');
await waitFor(() => byText('Reprendre à 6:00'), 4000);
assert(true, 'Film 3 en cours à 360 s : bouton « Reprendre à 6:00 »');
assert(byText('Revoir depuis le début'), 'Bouton « Revoir depuis le début »');
await click(byText('Reprendre à 6:00'));
await waitFor(() => $('video'), 2000);
assert.equal($('video').getAttribute('data-depart'), '360', 'Reprendre : la vidéo part de 360 s');
assert.includes($('video').getAttribute('src') || '', '/videos/3', 'La vidéo du film 3 est chargée');
$('video').dispatchEvent(new Event('pause'));
await waitFor(() => window.__db.puts.length > 0, 3000).catch(() => {});
assert(window.__db.puts.some((p) => p.id === 3 && typeof p.envoi === 'number'), 'Pause : un PUT /api/visionnages/3 avec un numéro d\'envoi part', JSON.stringify(window.__db.puts));
await click(byText('Film 1'));
await waitFor(() => $('video') && ($('video').getAttribute('src') || '').includes('/videos/1'), 4000);
assert(!byText('Reprendre à 6:00') && $('video').getAttribute('data-depart') === '0', 'Film 1 jamais commencé : la vidéo démarre directement à 0');
""")),
  ])

MODULES = [profils, reprise, front]

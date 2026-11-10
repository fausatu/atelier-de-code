from common import M, Q, TD, code

T = "arch"

MODULES = [
M("arch-roles", T, "Qui fait quoi : les 5 rôles", 15,
  "Savoir exactement le rôle du contrôleur, du DTO, du service, de l'entité et du repository.",
  "Sans séparation, tout finit dans le contrôleur : 200 lignes qui lisent le JSON, valident, calculent, font du SQL et formatent la réponse. Impossible à relire, à tester ou à réutiliser. Pense à un restaurant : le serveur prend la commande, le chef cuisine, le magasinier gère le stock. Personne ne fait le travail des autres.",
  ["**Contrôleur** (le serveur du restaurant) : reçoit la requête HTTP, appelle le bon service, renvoie la réponse",
   "**DTO** (le bon de commande) : la forme des données qui entrent et qui sortent",
   "**Service** (le chef) : exécute le cas d'usage, applique la logique, coordonne",
   "**Entité + Repository** (les ingrédients + le magasinier) : l'entité porte les données et ses règles ; le repository les cherche et les range en base"],
  ["**Contrôleur** : parle HTTP (route, statut, JSON). Il ne contient **aucune** règle métier ni requête. Objectif : moins de 15 lignes par action.",
   "**DTO** : aucune logique ; juste des propriétés et des contraintes de validation.",
   "**Service** : ne connaît **pas** HTTP (pas de `Request`, pas de `JsonResponse`). Il pourrait être appelé par une commande console ou un test.",
   "**Entité** : ses propres règles (`emprunter()` refuse si indisponible). **Repository** : seulement des lectures en base (`find`, QueryBuilder).",
   "Test simple : si tu peux décrire une classe en une phrase sans « et », elle a un seul rôle."],
  ["Un `if` métier dans le contrôleur (« si le stock est à 0… »).",
   "Un service qui renvoie une `JsonResponse` ou lit `$request`."],
  code("plaintext", r"""
            REQUÊTE HTTP  POST /api/emprunts  {"livreId": 3, "rendreLe": "2026-12-01"}
                 |
                 v
  +-----------------------------+
  | CONTRÔLEUR                  |  "Je reçois, je délègue, je réponds."
  | EmpruntController::create   |
  +-----------------------------+
        |  JSON -> EmpruntInput (DTO d'entrée, validé)
        v
  +-----------------------------+
  | SERVICE                     |  "J'exécute le cas d'usage."
  | EmpruntService::emprunter   |
  +-----------------------------+
        |                     |
        | find(3)             | $livre->emprunter()   (règle : disponible ?)
        v                     v
  +---------------+     +---------------+
  | REPOSITORY    |     | ENTITÉ        |  "Je garde mes règles."
  | LivreRepo     |---->| Livre         |
  +---------------+     +---------------+
        |                     |
        v                     | persist / flush (EntityManager)
     BASE DE DONNÉES  <-------+
                 |
                 v
  CONTRÔLEUR : Emprunt -> EmpruntOutput (DTO de sortie) -> JSON, statut 201
"""),
  ["La flèche descend toujours : le contrôleur connaît le service, le service connaît le repository et l'entité. Jamais l'inverse.",
   "Le DTO sert de frontière : en entrée (JSON → objet) et en sortie (entité → JSON).",
   "La règle « livre disponible ? » vit dans l'entité, pas dans le contrôleur ni dans le service."],
  [Q("Où placer « un membre ne peut pas avoir plus de 3 emprunts en cours » ?",
     ["Dans le contrôleur", "Dans le DTO", "Dans le service (ou l'entité si elle a l'info)", "Dans le repository"], 2,
     "C'est une règle métier : service ou entité, jamais le contrôleur ni le DTO."),
   Q("Le service doit-il renvoyer une `JsonResponse` ?",
     ["Oui", "Non : il renvoie des objets métier, le contrôleur fabrique la réponse HTTP", "Seulement en API", "Seulement pour les erreurs"], 1,
     "Le service ne connaît pas HTTP, ce qui permet de l'appeler depuis une commande ou un test."),
   Q("Quel est le rôle du repository ?",
     ["Valider les données", "Chercher et lire les entités en base", "Formater le JSON", "Gérer les routes"], 1,
     "Il cache le SQL/DQL derrière des méthodes nommées.")],
  TD("Trier le code d'un contrôleur",
     "Ce contrôleur fait tout. Pour chaque bloc numéroté, indique dans quelle classe il devrait aller (Contrôleur, DTO, Service, Entité, Repository) et pourquoi, en une phrase.",
     ["Attribue un rôle à chaque bloc de 1 à 7",
      "Justifie en une phrase",
      "Bonus : réécris le contrôleur en 5 lignes maximum"],
     code("php", r"""
#[Route('/api/commandes', methods: ['POST'])]
public function create(Request $request, EntityManagerInterface $em): JsonResponse
{
    // 1
    $data = json_decode($request->getContent(), true);
    if (empty($data['produitId']) || ($data['quantite'] ?? 0) < 1) {
        return new JsonResponse(['error' => 'Données invalides'], 422);
    }
    // 2
    $produit = $em->createQuery('SELECT p FROM App\Entity\Produit p WHERE p.id = :id')
        ->setParameter('id', $data['produitId'])->getOneOrNullResult();
    // 3
    if ($produit->getStock() < $data['quantite']) {
        return new JsonResponse(['error' => 'Stock insuffisant'], 409);
    }
    // 4
    $produit->setStock($produit->getStock() - $data['quantite']);
    // 5
    $commande = new Commande($produit, $data['quantite'], $this->getUser());
    $em->persist($commande);
    $em->flush();
    // 6
    $json = ['id' => $commande->getId(), 'total' => $commande->getTotal() / 100 . ' €'];
    // 7
    return new JsonResponse($json, 201);
}
"""),
     ["Le bloc 1 mélange deux choses : la forme des données (DTO) et la réponse HTTP (contrôleur, ou automatique avec `MapRequestPayload`).",
      "Les blocs 3 et 4 vont ensemble : « retirer du stock, sauf si insuffisant » est une seule règle."],
     code("php", r"""
// 1 -> DTO CommandeInput + #[MapRequestPayload] : forme et validation des données entrantes.
// 2 -> Repository (ProduitRepository::find) : lire en base.
// 3+4 -> Entité Produit::retirerDuStock(int $q) : la règle "pas de stock négatif" appartient au produit.
// 5 -> Service CommandeService::passer() : orchestrer (chercher, appliquer la règle, créer, enregistrer).
// 6 -> DTO de sortie CommandeOutput::fromEntity() : choisir et formater ce qui sort.
// 7 -> Contrôleur : statut HTTP et réponse JSON.

#[Route('/api/commandes', methods: ['POST'])]
public function create(
    #[MapRequestPayload] CommandeInput $input,
    #[CurrentUser] User $user,
    CommandeService $commandes,
): JsonResponse {
    $commande = $commandes->passer($input, $user);
    return $this->json(CommandeOutput::fromEntity($commande), 201);
}
"""),
     ["Chaque bloc a une seule destination",
      "Ton contrôleur réécrit ne contient ni `if` métier ni requête"])),

M("arch-liens", T, "Comment les classes sont reliées", 15,
  "Comprendre comment le contrôleur obtient le service, et le service le repository, sans jamais faire `new`.",
  "On voit `public function __construct(private LivreRepository $livres)` partout, mais on ne sait pas qui crée ces objets ni comment ils arrivent. C'est le conteneur de services de Symfony.",
  ["Chaque classe **déclare** ce dont elle a besoin dans son **constructeur** (ou dans les paramètres d'une action de contrôleur)",
   "Au démarrage, Symfony lit ces **types** (autowiring)",
   "Le **conteneur** crée chaque service **une seule fois** et le passe à ceux qui en ont besoin",
   "Résultat : une **chaîne** Contrôleur → Service → Repository/EntityManager, montée automatiquement"],
  ["Tout ce qui est dans `src/` (sauf entités, DTO…) est un service enregistré automatiquement (`config/services.yaml`).",
   "Les **entités** et les **DTO** ne sont **pas** des services : on les crée avec `new` (ou Symfony les remplit, comme `MapRequestPayload`).",
   "Les dépendances vont **vers le bas** : un repository ne dépend jamais d'un service, un service jamais d'un contrôleur.",
   "Si une interface n'a qu'une implémentation, Symfony les relie tout seul. Sinon, un alias dans `services.yaml`.",
   "Commande utile : `php bin/console debug:autowiring Livre` liste ce que tu peux injecter."],
  ["Faire `new LivreRepository()` ou `new EmpruntService(...)` à la main dans un contrôleur.",
   "Une dépendance circulaire (A a besoin de B qui a besoin de A) : c'est le signe que les rôles sont mal découpés."],
  code("php", r"""
// Le contrôleur demande le service
final class EmpruntController extends AbstractController
{
    public function __construct(private EmpruntService $emprunts) {}   // injecté par Symfony
    // ...
}

// Le service demande le repository et l'EntityManager
final class EmpruntService
{
    public function __construct(
        private LivreRepository $livres,          // pour LIRE
        private EntityManagerInterface $em,       // pour ÉCRIRE (persist/flush)
    ) {}
}

// Le repository demande le registre Doctrine
final class LivreRepository extends ServiceEntityRepository
{
    public function __construct(ManagerRegistry $registry)
    {
        parent::__construct($registry, Livre::class);
    }
}

// Ce que Symfony fait pour toi, en gros :
// $registry   = ...;                                   // fourni par Doctrine
// $em         = ...;
// $livres     = new LivreRepository($registry);
// $service    = new EmpruntService($livres, $em);
// $controller = new EmpruntController($service);
"""),
  ["Personne n'écrit les `new` du bas : c'est le conteneur qui les fait, dans le bon ordre.",
   "Chaque classe ne connaît que l'étage juste en dessous.",
   "En test, tu peux faire ces `new` toi-même avec de fausses implémentations (module Injection de dépendances)."],
  [Q("Qui crée l'instance de `EmpruntService` passée au contrôleur ?",
     ["Le contrôleur avec `new`", "Le conteneur de services de Symfony (autowiring)", "Doctrine", "Le front"], 1,
     "Il lit le type dans le constructeur et fournit l'objet."),
   Q("Un DTO `EmpruntInput` est-il un service injecté ?",
     ["Oui", "Non : c'est une donnée, créée par `new` ou remplie par `MapRequestPayload`", "Seulement s'il est final", "Seulement en prod"], 1,
     "Services = objets qui font quelque chose ; DTO/entités = objets qui portent des données."),
   Q("Quel sens de dépendance est correct ?",
     ["Repository → Service", "Service → Contrôleur", "Contrôleur → Service → Repository", "Entité → Contrôleur"], 2,
     "Toujours de la couche HTTP vers les données.")],
  TD("Dessiner les liens",
     "Pour la fonctionnalité « rendre un livre », écris les classes et leurs constructeurs (sans le corps des méthodes), puis dessine la chaîne.",
     ["`RetourController` (route `POST /api/emprunts/{id}/retour`)",
      "`RetourService::rendre(int $empruntId, User $membre): Emprunt`",
      "`EmpruntRepository` avec une méthode de lecture utile",
      "Ce que chacun reçoit dans son constructeur",
      "Un schéma texte des flèches de dépendance"],
     code("plaintext", r"""
RetourController
  constructeur : ...
  méthode : ...

RetourService
  constructeur : ...

EmpruntRepository
  méthode : ...

Schéma :
  ... -> ... -> ...
"""),
     ["Le service doit vérifier que l'emprunt appartient bien au membre : de quoi a-t-il besoin pour lire, et pour écrire ?",
      "L'entité `Emprunt` peut avoir une méthode `cloturer(\\DateTimeImmutable $le)` qui rend aussi le livre disponible."],
     code("php", r"""
final class RetourController extends AbstractController
{
    public function __construct(private RetourService $retours) {}

    #[Route('/api/emprunts/{id}/retour', methods: ['POST'])]
    public function rendre(int $id, #[CurrentUser] User $membre): JsonResponse
    {
        return $this->json(EmpruntOutput::fromEntity($this->retours->rendre($id, $membre)));
    }
}

final class RetourService
{
    public function __construct(
        private EmpruntRepository $emprunts,     // lire l'emprunt
        private EntityManagerInterface $em,      // enregistrer (flush)
        private ClockInterface $clock,           // la date du jour, remplaçable en test
    ) {}

    public function rendre(int $empruntId, User $membre): Emprunt { /* ... */ }
}

final class EmpruntRepository extends ServiceEntityRepository
{
    public function findEnCoursPourMembre(int $id, User $membre): ?Emprunt { /* ... */ }
}

// Schéma :
// RetourController -> RetourService -> EmpruntRepository -> Doctrine
//                                   -> EntityManager
//                                   -> Emprunt::cloturer() -> Livre::rendre()
"""),
     ["Aucune flèche ne remonte (ex. repository → service)",
      "Aucun `new` de service dans ton code"])),

M("arch-erreurs", T, "Les erreurs à travers les couches", 12,
  "Savoir où chaque erreur est détectée et comment elle devient un code HTTP.",
  "Si chaque couche renvoie ses erreurs à sa façon (`return false`, `null`, `JsonResponse`…), le contrôleur se remplit de `if` et le front reçoit des réponses incohérentes.",
  ["**DTO** : données mal formées → **422** (automatique avec `MapRequestPayload`)",
   "**Repository** : renvoie `null` si rien n'est trouvé ; le **service** transforme ça en exception « introuvable » → **404**",
   "**Entité / service** : règle métier violée → **exception métier** (`LivreIndisponible`) → **409**",
   "Le contrôleur **ne fait rien** : Symfony convertit l'exception en réponse grâce à `#[WithHttpStatus]`"],
  ["Une exception métier par cas, avec un nom clair : `LivreIndisponible`, `QuotaEmpruntsAtteint`.",
   "`#[WithHttpStatus(409)]` sur la classe d'exception (Symfony 6.3+) : Symfony répond 409 tout seul.",
   "Le service et l'entité lèvent des exceptions **métier**, jamais des exceptions HTTP : ils ne connaissent pas HTTP.",
   "Côté React, tu lis le statut : `err.response?.status === 409` (module Mutations).",
   "Codes à retenir : 400 requête mal formée, 401 pas connecté, 403 pas le droit, 404 introuvable, 409 conflit avec l'état actuel, 422 données invalides."],
  ["`return null` ou `return false` pour signaler une erreur métier : l'appelant oublie de vérifier.",
   "Un `try/catch` dans chaque contrôleur pour la même exception."],
  code("php", r"""
// src/Exception/LivreIndisponible.php
use Symfony\Component\HttpKernel\Attribute\WithHttpStatus;

#[WithHttpStatus(409)]
final class LivreIndisponible extends \DomainException
{
    public function __construct(int $livreId)
    {
        parent::__construct("Le livre $livreId est déjà emprunté");
    }
}

#[WithHttpStatus(404)]
final class LivreIntrouvable extends \DomainException {}

// Entité : la règle
public function emprunter(): void
{
    if (!$this->disponible) {
        throw new LivreIndisponible($this->id);
    }
    $this->disponible = false;
}

// Service : null -> exception
$livre = $this->livres->find($in->livreId) ?? throw new LivreIntrouvable();
$livre->emprunter();

// Contrôleur : aucun try/catch
$emprunt = $this->emprunts->emprunter($input, $membre);
return $this->json(EmpruntOutput::fromEntity($emprunt), 201);
"""),
  ["L'entité ne sait pas que 409 existe : elle lève juste `LivreIndisponible`.",
   "C'est l'attribut sur la classe d'exception qui fait le lien avec HTTP.",
   "En environnement de production, le message est masqué ; pour l'exposer au front, utilise un listener d'exception ou renvoie un DTO d'erreur."],
  [Q("Le titre envoyé est vide. Qui détecte l'erreur, et quel code ?",
     ["L'entité, 409", "Le DTO (validation), 422", "Le repository, 404", "Le contrôleur, 500"], 1,
     "C'est un problème de forme des données."),
   Q("Le livre existe mais est déjà emprunté. Quel code ?",
     ["404", "409", "422", "500"], 1,
     "Les données sont valides, mais l'état actuel empêche l'action : conflit."),
   Q("L'entité doit-elle lever une `HttpException` ?",
     ["Oui", "Non : elle lève une exception métier ; le lien avec HTTP se fait ailleurs", "Seulement pour 404", "Seulement en API"], 1,
     "Le domaine ne dépend pas de HTTP.")],
  TD("Quota d'emprunts",
     "Un membre ne peut pas avoir plus de 3 emprunts en cours.",
     ["Exception `QuotaEmpruntsAtteint` → 409 via `#[WithHttpStatus]`",
      "Le repository fournit `compterEnCours(User $membre): int`",
      "Le service vérifie le quota avant d'emprunter",
      "Le contrôleur ne change pas",
      "Côté React : affiche « Tu as déjà 3 livres » si 409 et que le message contient « quota »… ou mieux, propose une solution plus fiable"],
     code("php", r"""
final class QuotaEmpruntsAtteint extends \DomainException
{
    // à toi
}

// EmpruntRepository::compterEnCours : à toi
// EmpruntService::emprunter : ajoute la vérification
"""),
     ["`COUNT(e.id)` avec `e.membre = :m AND e.rendu = false`.",
      "Pour que le front distingue deux 409, renvoie un code d'erreur stable dans le JSON (`\"code\": \"QUOTA\"`) avec un listener d'exception, plutôt que de lire le message."],
     code("php", r"""
#[WithHttpStatus(409)]
final class QuotaEmpruntsAtteint extends \DomainException
{
    public function __construct(int $max)
    {
        parent::__construct("Quota de $max emprunts atteint");
    }
}

// EmpruntRepository
public function compterEnCours(User $membre): int
{
    return (int) $this->createQueryBuilder('e')
        ->select('COUNT(e.id)')
        ->andWhere('e.membre = :m')->setParameter('m', $membre)
        ->andWhere('e.rendu = false')
        ->getQuery()->getSingleScalarResult();
}

// EmpruntService
private const MAX = 3;

public function emprunter(EmpruntInput $in, User $membre): Emprunt
{
    if ($this->emprunts->compterEnCours($membre) >= self::MAX) {
        throw new QuotaEmpruntsAtteint(self::MAX);
    }
    $livre = $this->livres->find($in->livreId) ?? throw new LivreIntrouvable();
    $livre->emprunter();
    // ...
}

// Plus fiable pour le front : un ExceptionListener qui renvoie
// {"code": "QUOTA_ATTEINT", "message": "..."} pour QuotaEmpruntsAtteint,
// et {"code": "LIVRE_INDISPONIBLE", ...} pour LivreIndisponible.
// React teste alors err.response.data.code au lieu du texte.
"""),
     ["Le contrôleur n'a pas été modifié",
      "Le 4e emprunt renvoie 409"])),

M("arch-bout-en-bout", T, "Une fonctionnalité de bout en bout", 18,
  "Suivre une action de l'utilisateur à travers toutes les couches, du clic React à la base de données et retour.",
  "Chaque parcours t'a montré une partie. Ici, on les assemble : c'est en voyant le trajet complet qu'on comprend pourquoi chaque couche existe.",
  ["**React** : le composant appelle le hook ; le hook appelle `api/emprunts.ts` ; axios envoie `POST /api/emprunts`",
   "**Symfony entrée** : la route → le contrôleur → `MapRequestPayload` remplit et valide le **DTO d'entrée**",
   "**Symfony métier** : le **service** lit via le **repository**, applique la règle de l'**entité**, `flush()`",
   "**Retour** : entité → **DTO de sortie** → JSON 201 → axios `res.data` → le hook met à jour le state → React redessine"],
  ["Front et back ont la **même organisation** : une couche qui parle à l'extérieur (composant / contrôleur), une couche de logique (hook / service), une couche d'accès aux données (api / repository).",
   "Le **DTO** est le contrat entre les deux : le type TypeScript `Emprunt` = le DTO `EmpruntOutput`.",
   "Quand un bug apparaît, demande-toi **à quelle étape** du trajet il se produit. L'onglet Réseau (F12) te dit tout de suite si c'est avant ou après le serveur.",
   "Ajouter une fonctionnalité = ajouter une petite pièce à chaque couche, pas un gros bloc à un seul endroit."],
  ["Débugger au hasard au lieu de suivre le trajet étape par étape.",
   "Changer un nom de champ dans le DTO sans mettre à jour le type TypeScript."],
  code("plaintext", r"""
  NAVIGATEUR (React)                         SERVEUR (Symfony)
  ==================                         =================
  Catalogue.tsx  (composant)                 EmpruntController   (contrôleur)
     | clic "Emprunter"                         | route POST /api/emprunts
     v                                          v
  useLivres()    (hook = logique)            EmpruntInput        (DTO d'entrée, validé)
     |                                          |
     v                                          v
  api/livres.ts  (accès aux données)         EmpruntService      (service = logique)
     | axios.post('/emprunts', {...})           |        |
     |                                          v        v
     |  ------------ HTTP JSON -------->     LivreRepo   Livre::emprunter()  (règle)
     |                                          |        |
     |                                          +--> flush() --> BASE DE DONNÉES
     |                                          |
     |  <----------- 201 JSON ---------      EmpruntOutput       (DTO de sortie)
     v
  res.data -> setLivres(...) -> React redessine

  Les deux côtés en miroir :
    composant  <->  contrôleur      (parle à l'extérieur)
    hook       <->  service         (logique)
    api/*.ts   <->  repository      (accès aux données)
    type TS    <->  DTO             (contrat)
"""),
  ["Le trajet complet fait environ 10 étapes, mais chaque étape est courte et ne fait qu'une chose.",
   "Le miroir front/back est le même principe de séparation des rôles, dans deux langages.",
   "Si l'écran ne bouge pas mais que le Réseau montre 201 : le problème est dans le hook (state non mis à jour)."],
  [Q("Le Réseau (F12) montre un 422. Où chercher ?",
     ["Dans le hook React", "Dans les données envoyées et les contraintes du DTO d'entrée", "Dans le repository", "Dans le CSS"], 1,
     "422 = validation du DTO refusée : compare le corps envoyé et les contraintes."),
   Q("Le Réseau montre 201 avec le bon JSON, mais l'écran ne change pas. Où chercher ?",
     ["Dans le service Symfony", "Dans le hook / composant React : le state n'est pas mis à jour", "Dans la base", "Dans le DTO"], 1,
     "Le serveur a fait son travail ; le problème est après la réponse."),
   Q("Quel est l'équivalent front du service Symfony ?",
     ["Le composant", "Le hook (logique)", "Le CSS", "axios"], 1,
     "Composant ↔ contrôleur, hook ↔ service, api ↔ repository.")],
  TD("Fonctionnalité complète : noter un livre",
     "Un membre peut donner une note de 1 à 5 à un livre qu'il a emprunté. Écris chaque pièce, du front au back.",
     ["Back : DTO `NoteInput` (note 1–5, commentaire optionnel ≤ 300 caractères)",
      "Back : entité `Note`, service `NoteService::noter()` (refuse si le membre n'a jamais emprunté le livre → 403 via exception métier), contrôleur `POST /api/livres/{id}/notes`",
      "Back : DTO `NoteOutput`",
      "Front : `api/notes.ts`, un hook ou une mutation TanStack Query, un composant avec 5 boutons",
      "Écris en commentaire le trajet complet, étape par étape"],
     code("plaintext", r"""
BACK
  src/Dto/NoteInput.php
  src/Dto/NoteOutput.php
  src/Entity/Note.php
  src/Exception/PasEmprunte.php
  src/Service/NoteService.php
  src/Controller/NoteController.php

FRONT
  src/api/notes.ts
  src/components/NoterLivre.tsx

Trajet :
  1. ...
"""),
     ["Le service a besoin d'`EmpruntRepository` pour vérifier qu'il existe au moins un emprunt du livre par ce membre.",
      "Côté React, `useMutation({ mutationFn: (note) => noterLivre(livreId, note) })` et un `onSuccess` qui invalide `['livres', livreId]`."],
     code("php", r"""
// ---------- BACK ----------
final class NoteInput
{
    public function __construct(
        #[Assert\Range(min: 1, max: 5)]
        public readonly int $note = 0,
        #[Assert\Length(max: 300)]
        public readonly ?string $commentaire = null,
    ) {}
}

#[WithHttpStatus(403)]
final class PasEmprunte extends \DomainException {}

final class NoteService
{
    public function __construct(
        private EmpruntRepository $emprunts,
        private EntityManagerInterface $em,
    ) {}

    public function noter(Livre $livre, User $membre, NoteInput $in): Note
    {
        if (!$this->emprunts->aDejaEmprunte($membre, $livre)) {
            throw new PasEmprunte('Tu dois avoir emprunté ce livre pour le noter');
        }
        $note = new Note($livre, $membre, $in->note, $in->commentaire);
        $this->em->persist($note);
        $this->em->flush();
        return $note;
    }
}

#[Route('/api/livres/{id}/notes', methods: ['POST'])]
public function noter(
    Livre $livre,
    #[MapRequestPayload] NoteInput $input,
    #[CurrentUser] User $membre,
    NoteService $notes,
): JsonResponse {
    return $this->json(NoteOutput::fromEntity($notes->noter($livre, $membre, $input)), 201);
}

// ---------- FRONT (TypeScript) ----------
// api/notes.ts
// export type NoteOutput = { id: number; note: number; commentaire: string | null };
// export const noterLivre = (livreId: number, body: { note: number; commentaire?: string }) =>
//   api.post<NoteOutput>(`/livres/${livreId}/notes`, body).then((r) => r.data);
//
// components/NoterLivre.tsx
// const qc = useQueryClient();
// const noter = useMutation({
//   mutationFn: (note: number) => noterLivre(livreId, { note }),
//   onSuccess: () => qc.invalidateQueries({ queryKey: ['livres', livreId] }),
// });
// {[1, 2, 3, 4, 5].map((n) => (
//   <button key={n} onClick={() => noter.mutate(n)} disabled={noter.isPending}>{n}</button>
// ))}
// {axios.isAxiosError(noter.error) && noter.error.response?.status === 403 && <p>Emprunte-le d'abord</p>}

// ---------- TRAJET ----------
// clic "4" -> mutation -> noterLivre -> axios POST /api/livres/7/notes {"note":4}
// -> route -> NoteController -> NoteInput validé -> NoteService::noter
// -> EmpruntRepository::aDejaEmprunte -> new Note -> flush
// -> NoteOutput -> JSON 201 -> onSuccess -> invalidation -> React recharge et redessine
"""),
     ["Chaque pièce n'a qu'un rôle",
      "Tu sais dire, pour un 403, un 422 et un 201 sans changement d'écran, où chercher"])),
]

from common_v1 import M, Q, TD, code

T = "dto"

MODULES = [
M("dto-pourquoi", T, "DTO : à quoi ça sert", 12,
  "Comprendre ce qu'est un DTO et où il se place entre l'API et tes entités.",
  "Si ton API renvoie directement l'entité `User`, tu exposes le mot de passe haché, tu crées des boucles infinies avec les relations, et le moindre renommage de colonne casse le front.",
  ["Le front envoie du **JSON** (ex. `axios.post('/api/articles', {...})`)",
   "Symfony le transforme en **DTO d'entrée** et le **valide**",
   "Ton service utilise le DTO pour créer ou modifier l'**entité**",
   "La réponse part sous forme de **DTO de sortie**, converti en JSON"],
  ["DTO = *Data Transfer Object* : une petite classe **sans logique**, juste des propriétés, qui décrit des données qui voyagent.",
   "L'entité représente ta base ; le DTO représente **ce que l'API accepte ou renvoie**. Ce ne sont pas les mêmes besoins.",
   "Un DTO par usage : `CreateArticleInput`, `UpdateArticleInput`, `ArticleOutput`, `ArticleListItem`…",
   "Les propriétés sont souvent `public readonly` : simple à lire, impossible à modifier par erreur.",
   "C'est le **contrat** entre ton back Symfony et ton front React."],
  ["Utiliser l'entité Doctrine comme objet de formulaire ou de réponse JSON.",
   "Mettre de la logique métier dans un DTO : il transporte, il ne décide pas."],
  code("php", r"""
// Ce que le front ENVOIE pour créer un article
final class CreateArticleInput
{
    public function __construct(
        public readonly string $titre,
        public readonly string $contenu,
        public readonly array $tags = [],
    ) {}
}

// Ce que l'API RENVOIE (on choisit les champs exposés)
final class ArticleOutput
{
    public function __construct(
        public readonly int $id,
        public readonly string $titre,
        public readonly string $extrait,
        public readonly string $auteur,      // juste le nom, pas l'objet User
        public readonly string $creeLe,      // date formatée
    ) {}
}

// L'entité Article, elle, reste interne : relations, id, mot de passe de l'auteur...
// Elle ne sort jamais telle quelle de l'API.
"""),
  ["Deux DTO différents pour l'entrée et la sortie : ils n'ont pas les mêmes champs.",
   "`auteur` est une simple chaîne : pas de relation à sérialiser, pas de boucle.",
   "Si tu renommes une colonne en base, seul le code qui remplit `ArticleOutput` change : le front ne voit rien."],
  [Q("Pourquoi ne pas renvoyer l'entité `User` directement en JSON ?",
     ["C'est plus lent", "On exposerait des champs sensibles et on lierait le front à la structure de la base", "Symfony l'interdit", "Le JSON ne gère pas les objets"], 1,
     "Le DTO choisit exactement ce qui sort."),
   Q("Un DTO contient…",
     ["la logique métier", "des données à transporter, sans logique", "les requêtes SQL", "le mapping Doctrine"], 1,
     "Il décrit une forme de données, c'est tout."),
   Q("Pour créer et pour afficher un article, combien de DTO ?",
     ["Un seul pour tout", "Deux : un d'entrée et un de sortie", "Aucun, on utilise l'entité", "Un par colonne"], 1,
     "Le client n'envoie pas l'id ni la date de création, mais il les reçoit.")],
  TD("Concevoir les DTO d'une inscription",
     "Pour l'inscription d'un utilisateur, écris les deux DTO. Pas encore de contrôleur.",
     ["`RegisterInput` : ce que le formulaire React envoie (email, mot de passe, pseudo, acceptation des CGU)",
      "`UserOutput` : ce que l'API renvoie après inscription",
      "Explique en commentaire pourquoi le mot de passe n'apparaît que dans l'un des deux",
      "Propriétés `public readonly`, aucune méthode"],
     code("php", r"""
final class RegisterInput
{
    // à toi
}

final class UserOutput
{
    // à toi
}
"""),
     ["Le client n'envoie pas d'id ni de date : ils sont générés côté serveur.",
      "La sortie peut contenir `id`, `email`, `pseudo`, `inscritLe`… mais jamais le mot de passe."],
     code("php", r"""
final class RegisterInput
{
    public function __construct(
        public readonly string $email,
        public readonly string $motDePasse,   // en clair, uniquement à l'entrée : on le hache tout de suite
        public readonly string $pseudo,
        public readonly bool $accepteCgu,
    ) {}
}

final class UserOutput
{
    public function __construct(
        public readonly int $id,
        public readonly string $email,
        public readonly string $pseudo,
        public readonly string $inscritLe,
    ) {}
    // Pas de mot de passe : une réponse d'API ne renvoie jamais un secret, même haché.
}
"""),
     ["`UserOutput` ne contient aucun champ sensible",
      "`RegisterInput` ne contient pas d'id"])),

M("dto-entree", T, "DTO d'entrée & validation", 15,
  "Recevoir le JSON du front dans un DTO validé automatiquement.",
  "Lire `$request->getContent()`, faire `json_decode` et vérifier chaque champ à la main est long et on oublie toujours un cas.",
  ["Le front envoie un corps JSON (`POST /api/articles`)",
   "`#[MapRequestPayload]` **désérialise** le JSON dans ton DTO",
   "Le **Validator** vérifie les contraintes `#[Assert\\...]`",
   "Valide → ton contrôleur reçoit le DTO. Invalide → Symfony répond **422** avec la liste des erreurs"],
  ["`#[MapRequestPayload]` existe depuis Symfony 6.3.",
   "Les noms des clés JSON doivent correspondre aux propriétés du DTO.",
   "Contraintes courantes : `NotBlank`, `Length`, `Email`, `Positive`, `Choice`, `Count`.",
   "Si la validation échoue, ton code ne s'exécute même pas : le contrôleur reste court.",
   "Côté React, le 422 arrive dans `error.response.data` avec axios : tu peux afficher les erreurs sous chaque champ."],
  ["Valider dans le contrôleur avec des `if` au lieu des contraintes.",
   "Oublier `NotBlank` : une chaîne vide passe le type `string`."],
  code("php", r"""
// src/Dto/CreateArticleInput.php
namespace App\Dto;

use Symfony\Component\Validator\Constraints as Assert;

final class CreateArticleInput
{
    public function __construct(
        #[Assert\NotBlank]
        #[Assert\Length(min: 5, max: 180)]
        public readonly string $titre = '',

        #[Assert\NotBlank]
        public readonly string $contenu = '',

        #[Assert\Count(max: 5)]
        #[Assert\All([new Assert\Length(max: 30)])]
        public readonly array $tags = [],
    ) {}
}

// src/Controller/ArticleController.php
#[Route('/api/articles', methods: ['POST'])]
public function create(
    #[MapRequestPayload] CreateArticleInput $input,
    ArticleService $articles,
): JsonResponse {
    $article = $articles->creer($input);              // on ne passe que des données valides
    return $this->json(ArticleOutput::fromEntity($article), 201);
}
"""),
  ["Les valeurs par défaut (`''`) permettent de signaler « champ manquant » proprement via `NotBlank`.",
   "Le contrôleur fait 2 lignes : la validation est déjà faite.",
   "201 = « créé »."],
  [Q("Que fait `#[MapRequestPayload]` ?",
     ["Il enregistre en base", "Il transforme le JSON reçu en DTO et le valide", "Il génère une migration", "Il crée une route"], 1,
     "Désérialisation + validation, avant d'entrer dans ton contrôleur."),
   Q("Le front envoie un titre vide. Que se passe-t-il ?",
     ["Le contrôleur plante", "Symfony répond 422 avec les erreurs, le contrôleur n'est pas exécuté", "L'article est créé sans titre", "200 OK"], 1,
     "`NotBlank` échoue, Symfony arrête là."),
   Q("Pourquoi `#[Assert\\NotBlank]` sur une propriété `string` ?",
     ["Inutile, le type suffit", "Le type accepte une chaîne vide `''`", "Pour la performance", "Pour Doctrine"], 1,
     "Le type vérifie que c'est une chaîne, pas qu'elle contient quelque chose.")],
  TD("Endpoint d'inscription",
     "Reprends `RegisterInput` et branche-le sur un endpoint qui valide tout.",
     ["Email valide et obligatoire",
      "Mot de passe : 8 caractères minimum",
      "Pseudo : 3 à 20 caractères, lettres, chiffres et `_` seulement (`Regex`)",
      "`accepteCgu` doit valoir `true` (`IsTrue`)",
      "Route `POST /api/register` qui renvoie 201 et un `UserOutput`"],
     code("php", r"""
use Symfony\Component\Validator\Constraints as Assert;

final class RegisterInput
{
    public function __construct(
        public readonly string $email = '',
        public readonly string $motDePasse = '',
        public readonly string $pseudo = '',
        public readonly bool $accepteCgu = false,
    ) {}
}

// Contrôleur : à toi
"""),
     ["`#[Assert\\Regex('/^[a-zA-Z0-9_]+$/')]`",
      "`#[Assert\\IsTrue(message: 'Tu dois accepter les CGU')]`",
      "Le hachage du mot de passe se fait dans le service, avec `UserPasswordHasherInterface`."],
     code("php", r"""
final class RegisterInput
{
    public function __construct(
        #[Assert\NotBlank, Assert\Email]
        public readonly string $email = '',

        #[Assert\NotBlank, Assert\Length(min: 8)]
        public readonly string $motDePasse = '',

        #[Assert\NotBlank, Assert\Length(min: 3, max: 20), Assert\Regex('/^[a-zA-Z0-9_]+$/')]
        public readonly string $pseudo = '',

        #[Assert\IsTrue(message: 'Tu dois accepter les CGU')]
        public readonly bool $accepteCgu = false,
    ) {}
}

#[Route('/api/register', methods: ['POST'])]
public function register(
    #[MapRequestPayload] RegisterInput $input,
    InscriptionService $inscription,
): JsonResponse {
    $user = $inscription->inscrire($input);
    return $this->json(new UserOutput(
        $user->getId(),
        $user->getEmail(),
        $user->getPseudo(),
        $user->getInscritLe()->format(DATE_ATOM),
    ), 201);
}
"""),
     ["Un POST avec `\"pseudo\": \"a b\"` renvoie 422",
      "Le contrôleur ne contient aucun `if` de validation"])),

M("dto-sortie", T, "DTO de sortie & mapping", 12,
  "Transformer une entité en DTO de sortie, proprement et à un seul endroit.",
  "Sérialiser l'entité directement provoque des boucles (Article → Auteur → Articles → …) et expose des champs que le front n'a pas à voir.",
  ["Le contrôleur récupère une ou plusieurs **entités**",
   "Une méthode **`fromEntity()`** construit le DTO de sortie",
   "Le DTO ne contient que des **types simples** (string, int, tableaux)",
   "`$this->json($dto)` le convertit en **JSON**"],
  ["Mets le mapping dans une méthode statique du DTO (`ArticleOutput::fromEntity($a)`) ou dans une classe dédiée (`ArticleMapper`).",
   "Formate les dates en chaînes (`DATE_ATOM`) : le front sait les lire.",
   "Pour une liste : `array_map(ArticleOutput::fromEntity(...), $articles)`.",
   "Un DTO « liste » plus léger qu'un DTO « détail » évite d'envoyer le contenu complet de 50 articles."],
  ["Faire le mapping dans chaque contrôleur : il finit copié-collé et différent partout.",
   "Mettre un objet entité dans le DTO de sortie : la boucle revient."],
  code("php", r"""
final class ArticleOutput
{
    public function __construct(
        public readonly int $id,
        public readonly string $titre,
        public readonly string $extrait,
        public readonly string $auteur,
        public readonly string $creeLe,
    ) {}

    public static function fromEntity(Article $a): self
    {
        return new self(
            id: $a->getId(),
            titre: $a->getTitre(),
            extrait: mb_substr($a->getContenu(), 0, 140),
            auteur: $a->getAuteur()->getNom(),
            creeLe: $a->getCreeLe()->format(DATE_ATOM),
        );
    }
}

#[Route('/api/articles', methods: ['GET'])]
public function list(ArticleRepository $repo): JsonResponse
{
    $articles = $repo->findAvecAuteur();   // fetch join, voir le module N+1
    return $this->json(array_map(ArticleOutput::fromEntity(...), $articles));
}

// JSON renvoyé :
// [{"id":1,"titre":"Hello","extrait":"...","auteur":"Ana","creeLe":"2026-11-10T09:00:00+01:00"}]
"""),
  ["Les arguments nommés (`id:`, `titre:`) rendent le mapping lisible.",
   "`ArticleOutput::fromEntity(...)` (syntaxe PHP 8.1) passe la méthode comme fonction à `array_map`.",
   "Le JSON correspond exactement aux propriétés du DTO : c'est ce que React reçoit dans `response.data`."],
  [Q("Pourquoi `auteur` est une `string` et pas un objet `User` ?",
     ["Pour la performance", "Pour éviter les boucles et ne pas exposer tout l'utilisateur", "Doctrine l'impose", "Par habitude"], 1,
     "Le DTO de sortie ne contient que ce dont l'écran a besoin."),
   Q("Où placer le code entité → DTO ?",
     ["Dans chaque contrôleur", "À un seul endroit : `fromEntity()` ou un mapper", "Dans le template", "Dans l'entité"], 1,
     "Un seul endroit = une seule version du JSON."),
   Q("Côté React avec axios, où se trouve ce JSON ?",
     ["`response.json`", "`response.data`", "`response.body`", "`response.dto`"], 1,
     "axios décode le JSON et le met dans `data`.")],
  TD("API du catalogue de livres",
     "Expose les livres de la bibliothèque (modules Doctrine) avec deux DTO.",
     ["`LivreListItem` : id, titre, auteur (nom), disponible",
      "`LivreDetail` : tout `LivreListItem` + isbn, publieLe (Y-m-d)",
      "`GET /api/livres` renvoie une liste de `LivreListItem`",
      "`GET /api/livres/{id}` renvoie un `LivreDetail` ou 404"],
     code("php", r"""
final class LivreListItem
{
    // à toi
}

final class LivreDetail
{
    // à toi
}

// LivreController : à toi
"""),
     ["404 : `throw $this->createNotFoundException();` si le livre est introuvable.",
      "Avec `#[Route('/api/livres/{id}')]` et un paramètre `Livre $livre`, Symfony charge l'entité et renvoie 404 tout seul (EntityValueResolver)."],
     code("php", r"""
final class LivreListItem
{
    public function __construct(
        public readonly int $id,
        public readonly string $titre,
        public readonly string $auteur,
        public readonly bool $disponible,
    ) {}

    public static function fromEntity(Livre $l): self
    {
        return new self($l->getId(), $l->getTitre(), $l->getAuteur()->getNom(), $l->isDisponible());
    }
}

final class LivreDetail
{
    public function __construct(
        public readonly int $id,
        public readonly string $titre,
        public readonly string $auteur,
        public readonly bool $disponible,
        public readonly string $isbn,
        public readonly string $publieLe,
    ) {}

    public static function fromEntity(Livre $l): self
    {
        return new self(
            $l->getId(), $l->getTitre(), $l->getAuteur()->getNom(), $l->isDisponible(),
            $l->getIsbn(), $l->getPublieLe()->format('Y-m-d'),
        );
    }
}

#[Route('/api/livres', methods: ['GET'])]
public function list(LivreRepository $repo): JsonResponse
{
    return $this->json(array_map(LivreListItem::fromEntity(...), $repo->catalogue()));
}

#[Route('/api/livres/{id}', methods: ['GET'])]
public function show(Livre $livre): JsonResponse   // 404 automatique si absent
{
    return $this->json(LivreDetail::fromEntity($livre));
}
"""),
     ["Le JSON ne contient aucun objet imbriqué `auteur: {...}`",
      "`/api/livres/999999` renvoie 404"])),

M("dto-modifier", T, "Du DTO à l'entité (créer, modifier)", 15,
  "Utiliser un DTO d'entrée pour créer ou modifier une entité, sans setters partout.",
  "Faire `$article->setTitre($data['titre'])` champ par champ dans le contrôleur mélange HTTP, règles et base de données.",
  ["Le contrôleur reçoit un **DTO validé**",
   "Il le passe à un **service** (le cas d'usage)",
   "Le service appelle le **constructeur** ou une **méthode métier** de l'entité avec les valeurs du DTO",
   "Puis `flush()`, et on renvoie un **DTO de sortie**"],
  ["Création : `new Article($input->titre, $input->contenu, $auteur)`.",
   "Modification : une méthode métier, `$article->modifier($input->titre, $input->contenu)`.",
   "PUT = remplacer toute la ressource (tous les champs requis). PATCH = modifier une partie (champs optionnels, souvent `?string`).",
   "L'entité garde ses règles (modules Encapsulation et Entités riches) ; le DTO ne fait que transporter."],
  ["Faire hériter le DTO de l'entité, ou l'inverse.",
   "Utiliser un seul DTO pour créer et modifier alors que les champs obligatoires ne sont pas les mêmes."],
  code("php", r"""
final class UpdateArticleInput
{
    public function __construct(
        #[Assert\NotBlank, Assert\Length(min: 5, max: 180)]
        public readonly string $titre = '',
        #[Assert\NotBlank]
        public readonly string $contenu = '',
    ) {}
}

final class ArticleService
{
    public function __construct(private EntityManagerInterface $em) {}

    public function creer(CreateArticleInput $in, User $auteur): Article
    {
        $article = new Article($in->titre, $in->contenu, $auteur);
        $this->em->persist($article);
        $this->em->flush();
        return $article;
    }

    public function modifier(Article $article, UpdateArticleInput $in): Article
    {
        $article->modifier($in->titre, $in->contenu);   // méthode métier de l'entité
        $this->em->flush();                             // déjà suivie : pas de persist
        return $article;
    }
}

#[Route('/api/articles/{id}', methods: ['PUT'])]
public function update(
    Article $article,
    #[MapRequestPayload] UpdateArticleInput $input,
    ArticleService $service,
): JsonResponse {
    return $this->json(ArticleOutput::fromEntity($service->modifier($article, $input)));
}
"""),
  ["Le contrôleur : HTTP → DTO → service → DTO de sortie.",
   "Le service : il orchestre, sans connaître HTTP.",
   "Pas de `persist` dans `modifier` : l'article vient de la base (module Unit of Work)."],
  [Q("Pour modifier seulement le titre d'un article, quelle méthode HTTP ?",
     ["GET", "PATCH", "DELETE", "POST"], 1,
     "PATCH = modification partielle ; PUT remplace toute la ressource."),
   Q("Qui applique les valeurs du DTO à l'entité ?",
     ["Le DTO lui-même", "Un service, via le constructeur ou une méthode métier de l'entité", "Le front", "Doctrine automatiquement"], 1,
     "Le service orchestre, l'entité garde ses règles."),
   Q("Dans `modifier()`, pourquoi pas de `persist` ?",
     ["Oubli", "L'article vient de la base, il est déjà suivi par Doctrine", "PUT n'en a pas besoin", "Le DTO s'en charge"], 1,
     "Seuls les nouveaux objets ont besoin de `persist`.")],
  TD("Emprunter un livre via l'API",
     "Crée l'endpoint qui enregistre un emprunt.",
     ["DTO `EmpruntInput` : `livreId` (int, positif), `rendreLe` (date `Y-m-d`, dans le futur)",
      "Service `EmpruntService::emprunter(EmpruntInput $in, User $membre): Emprunt`",
      "Le service appelle `$livre->emprunter()` (exception si indisponible)",
      "Route `POST /api/emprunts` → 201 + `EmpruntOutput` ; 409 si le livre est déjà emprunté"],
     code("php", r"""
final class EmpruntInput
{
    // à toi
}

final class EmpruntService
{
    // à toi
}

// Contrôleur : à toi
"""),
     ["Date : `#[Assert\\Date]` sur une `string`, puis `new \\DateTimeImmutable($in->rendreLe)` dans le service. Vérifie qu'elle est future dans le service ou avec `GreaterThan('today')` sur un `DateTimeImmutable`.",
      "409 Conflict : attrape la `DomainException` dans le contrôleur et renvoie `$this->json(['error' => ...], 409)`.",
      "`#[CurrentUser] User $membre` donne l'utilisateur connecté."],
     code("php", r"""
final class EmpruntInput
{
    public function __construct(
        #[Assert\Positive]
        public readonly int $livreId = 0,
        #[Assert\NotBlank, Assert\Date]
        public readonly string $rendreLe = '',
    ) {}
}

final class EmpruntService
{
    public function __construct(private EntityManagerInterface $em, private LivreRepository $livres) {}

    public function emprunter(EmpruntInput $in, User $membre): Emprunt
    {
        $livre = $this->livres->find($in->livreId) ?? throw new NotFoundHttpException('Livre introuvable');
        $retour = new \DateTimeImmutable($in->rendreLe);
        if ($retour <= new \DateTimeImmutable('today')) {
            throw new \InvalidArgumentException('La date de retour doit être dans le futur');
        }
        $livre->emprunter();                         // DomainException si indisponible
        $emprunt = new Emprunt($livre, $membre, $retour);
        $this->em->persist($emprunt);
        $this->em->flush();
        return $emprunt;
    }
}

#[Route('/api/emprunts', methods: ['POST'])]
public function create(
    #[MapRequestPayload] EmpruntInput $input,
    #[CurrentUser] User $membre,
    EmpruntService $service,
): JsonResponse {
    try {
        $emprunt = $service->emprunter($input, $membre);
    } catch (\DomainException $e) {
        return $this->json(['error' => $e->getMessage()], 409);
    } catch (\InvalidArgumentException $e) {
        return $this->json(['error' => $e->getMessage()], 422);
    }
    return $this->json(EmpruntOutput::fromEntity($emprunt), 201);
}
"""),
     ["Emprunter deux fois le même livre renvoie 409",
      "Le contrôleur ne modifie aucune entité lui-même"])),

M("dto-query", T, "Filtres & pagination (query string)", 10,
  "Recevoir les paramètres d'URL (`?page=2&q=php`) dans un DTO validé.",
  "Une liste a presque toujours des filtres et une pagination. Les lire un par un avec `$request->query->get()` est fastidieux et non validé.",
  ["Le front appelle `GET /api/articles?q=php&page=2`",
   "`#[MapQueryString]` remplit un **DTO de filtres**",
   "Les contraintes **valident** (page ≥ 1, taille max…)",
   "Le repository reçoit le DTO et construit la requête"],
  ["`#[MapQueryString]` (Symfony 6.3+) fonctionne comme `#[MapRequestPayload]`, mais avec l'URL.",
   "Donne des valeurs par défaut : `page = 1`, `parPage = 20`.",
   "Limite `parPage` (ex. 100) pour qu'on ne puisse pas demander un million de lignes.",
   "Renvoie aussi le total pour que le front affiche la pagination : `{ items: [...], total: 134, page: 2 }`.",
   "Côté axios : `api.get('/articles', { params: { q: 'php', page: 2 } })` construit l'URL pour toi."],
  ["Accepter `parPage` sans limite.",
   "Construire la requête en concaténant les filtres (injection SQL)."],
  code("php", r"""
final class ArticleFilters
{
    public function __construct(
        #[Assert\Length(max: 50)]
        public readonly ?string $q = null,
        #[Assert\Positive]
        public readonly int $page = 1,
        #[Assert\Range(min: 1, max: 100)]
        public readonly int $parPage = 20,
    ) {}
}

#[Route('/api/articles', methods: ['GET'])]
public function list(
    #[MapQueryString] ?ArticleFilters $filters,
    ArticleRepository $repo,
): JsonResponse {
    $filters ??= new ArticleFilters();             // aucune query string
    [$articles, $total] = $repo->rechercher($filters);

    return $this->json([
        'items' => array_map(ArticleOutput::fromEntity(...), $articles),
        'total' => $total,
        'page' => $filters->page,
    ]);
}

// Repository
public function rechercher(ArticleFilters $f): array
{
    $qb = $this->createQueryBuilder('a')->leftJoin('a.auteur', 'u')->addSelect('u');
    if ($f->q) {
        $qb->andWhere('LOWER(a.titre) LIKE :q')->setParameter('q', '%' . mb_strtolower($f->q) . '%');
    }
    $qb->orderBy('a.creeLe', 'DESC')
       ->setFirstResult(($f->page - 1) * $f->parPage)
       ->setMaxResults($f->parPage);

    $paginator = new Paginator($qb);
    return [iterator_to_array($paginator), count($paginator)];
}
"""),
  ["`?ArticleFilters` + `??=` : sans query string, on prend les valeurs par défaut.",
   "`Paginator` (Doctrine) donne la page ET le total.",
   "La réponse a une forme fixe que le front peut utiliser pour la pagination."],
  [Q("`GET /api/articles?parPage=5000` avec `Range(max: 100)` :",
     ["Renvoie 5000 articles", "Renvoie une erreur de validation (4xx)", "Renvoie 100 articles", "Plante"], 1,
     "La contrainte protège ta base."),
   Q("Avec axios, comment envoyer `?q=php&page=2` proprement ?",
     ["Concaténer la chaîne à la main", "`api.get('/articles', { params: { q: 'php', page: 2 } })`", "Dans le body", "Dans un header"], 1,
     "axios encode les paramètres pour toi."),
   Q("Pourquoi renvoyer `total` avec la liste ?",
     ["Pour le cache", "Pour que le front calcule le nombre de pages", "Doctrine l'exige", "Pour la sécurité"], 1,
     "Sans total, impossible d'afficher « page 2 sur 7 ».")],
  TD("Filtrer le catalogue",
     "Ajoute filtres et pagination à `GET /api/livres`.",
     ["DTO `LivreFilters` : `q` (texte), `disponible` (booléen optionnel), `page`, `parPage` (max 50)",
      "Le repository applique uniquement les filtres fournis",
      "Réponse : `{ items, total, page, pages }`"],
     code("php", r"""
final class LivreFilters
{
    // à toi
}

// LivreRepository::rechercher(LivreFilters $f): array  -> [livres, total]
// LivreController::list : à toi
"""),
     ["`public readonly ?bool $disponible = null` : null = pas de filtre.",
      "`pages` = `(int) ceil($total / $f->parPage)`."],
     code("php", r"""
final class LivreFilters
{
    public function __construct(
        #[Assert\Length(max: 50)]
        public readonly ?string $q = null,
        public readonly ?bool $disponible = null,
        #[Assert\Positive]
        public readonly int $page = 1,
        #[Assert\Range(min: 1, max: 50)]
        public readonly int $parPage = 20,
    ) {}
}

public function rechercher(LivreFilters $f): array
{
    $qb = $this->createQueryBuilder('l')->leftJoin('l.auteur', 'a')->addSelect('a');
    if ($f->q) {
        $qb->andWhere('LOWER(l.titre) LIKE :q')->setParameter('q', '%' . mb_strtolower($f->q) . '%');
    }
    if ($f->disponible !== null) {
        $qb->andWhere('l.disponible = :d')->setParameter('d', $f->disponible);
    }
    $qb->orderBy('l.titre', 'ASC')
       ->setFirstResult(($f->page - 1) * $f->parPage)
       ->setMaxResults($f->parPage);
    $p = new Paginator($qb);
    return [iterator_to_array($p), count($p)];
}

#[Route('/api/livres', methods: ['GET'])]
public function list(#[MapQueryString] ?LivreFilters $f, LivreRepository $repo): JsonResponse
{
    $f ??= new LivreFilters();
    [$livres, $total] = $repo->rechercher($f);
    return $this->json([
        'items' => array_map(LivreListItem::fromEntity(...), $livres),
        'total' => $total,
        'page' => $f->page,
        'pages' => (int) ceil($total / $f->parPage),
    ]);
}
"""),
     ["`?disponible=true` ne renvoie que les livres disponibles",
      "`?parPage=200` est refusé"])),
]

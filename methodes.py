"""Mémo des méthodes : les fonctions et méthodes qu'on croise dans les cours, expliquées simplement.

E(id, cat, nom, cles, sig, desc, params, retour, ex, res=None, piege=None)
- cat : php | doctrine | symfony | js | react | donnees | formulaires | next
- cles : ce qui est reconnu dans le code pour rendre le nom cliquable :
    PHP  : "fn:count" (fonction), "->persist" (méthode), "::from" (méthode statique), "new:DateTimeImmutable", "#Route" (attribut), "Assert:NotBlank"
    JS   : "fn:useState" (fonction), ".map" (méthode sur n'importe quoi), "Math.round" (objet.méthode)
- params : [(nom, explication), ...]
"""

CATS = [
    {"id": "php", "nom": "PHP", "lang": "php"},
    {"id": "doctrine", "nom": "Doctrine", "lang": "php"},
    {"id": "symfony", "nom": "Symfony", "lang": "php"},
    {"id": "js", "nom": "JavaScript", "lang": "js"},
    {"id": "react", "nom": "React", "lang": "js"},
    {"id": "donnees", "nom": "axios & TanStack Query", "lang": "js"},
    {"id": "formulaires", "nom": "Formulaires (React Hook Form, zod)", "lang": "js"},
    {"id": "next", "nom": "Next.js", "lang": "js"},
]

M = []


def E(id, cat, nom, cles, sig, desc, params, retour, ex, res=None, piege=None):
    e = {"id": id, "cat": cat, "nom": nom, "cles": cles, "sig": sig, "desc": desc, "params": [{"n": n, "d": d} for n, d in params], "retour": retour, "ex": ex.strip("\n")}
    if res:
        e["res"] = res
    if piege:
        e["piege"] = piege
    M.append(e)


# =========================================================================== PHP : tableaux
E("count", "php", "count", ["fn:count"], "count(array|Countable $valeur): int",
  "Compte les éléments d'un tableau (ou d'une collection Doctrine).",
  [("$valeur", "le tableau ou la collection à compter")], "le nombre d'éléments (int)",
  "count(['a', 'b', 'c']);\ncount([]);", "3\n0")
E("array_map", "php", "array_map", ["fn:array_map"], "array_map(?callable $fonction, array $tableau): array",
  "Transforme chaque élément d'un tableau avec une fonction et renvoie un **nouveau** tableau de même taille.",
  [("$fonction", "ce qu'on applique à chaque élément, souvent une fonction fléchée `fn($x) => ...`"), ("$tableau", "le tableau de départ (non modifié)")],
  "un nouveau tableau avec les résultats, dans le même ordre",
  "array_map(fn($n) => $n * 2, [1, 2, 3]);\narray_map(FilmCard::fromEntity(...), $films);", "[2, 4, 6]\n[FilmCard, FilmCard, …]",
  "L'ordre des paramètres : la fonction d'abord, le tableau ensuite (l'inverse de `array_filter`).")
E("array_filter", "php", "array_filter", ["fn:array_filter"], "array_filter(array $tableau, ?callable $test = null): array",
  "Garde seulement les éléments pour lesquels la fonction renvoie `true`.",
  [("$tableau", "le tableau de départ"), ("$test", "la fonction qui dit oui ou non pour chaque élément ; sans elle, retire les valeurs « vides » (0, '', null, false)")],
  "un nouveau tableau avec les éléments gardés, **avec leurs clés d'origine**",
  "$pairs = array_filter([1, 2, 3, 4], fn($n) => $n % 2 === 0);", "[1 => 2, 3 => 4]",
  "Les clés gardent des trous : passe le résultat dans `array_values()` avant de l'envoyer en JSON, sinon il devient un objet `{\"1\": 2, \"3\": 4}`.")
E("array_values", "php", "array_values", ["fn:array_values"], "array_values(array $tableau): array",
  "Renumérote un tableau de 0 à n-1 (oublie les clés).",
  [("$tableau", "un tableau, souvent sorti d'`array_filter`")], "le même contenu, avec des clés 0, 1, 2…",
  "array_values([1 => 'b', 3 => 'd']);", "[0 => 'b', 1 => 'd']")
E("array_keys", "php", "array_keys", ["fn:array_keys"], "array_keys(array $tableau): array",
  "Renvoie la liste des clés d'un tableau.", [("$tableau", "le tableau")], "un tableau des clés",
  "array_keys(['id' => 3, 'titre' => 'Sintel']);", "['id', 'titre']")
E("array_slice", "php", "array_slice", ["fn:array_slice"], "array_slice(array $tableau, int $debut, ?int $longueur = null): array",
  "Découpe un morceau d'un tableau. C'est l'outil de la pagination.",
  [("$tableau", "le tableau"), ("$debut", "la position de départ (0 = le premier)"), ("$longueur", "combien d'éléments prendre (jusqu'à la fin si absent)")],
  "le morceau découpé (le tableau d'origine ne change pas)",
  "array_slice(['a', 'b', 'c', 'd', 'e'], 2, 2);\n// page 3 de 10 éléments :\narray_slice($films, (3 - 1) * 10, 10);", "['c', 'd']")
E("array_merge", "php", "array_merge", ["fn:array_merge"], "array_merge(array ...$tableaux): array",
  "Colle plusieurs tableaux bout à bout.", [("...$tableaux", "deux tableaux ou plus")], "un nouveau tableau",
  "array_merge([1, 2], [3], [4, 5]);", "[1, 2, 3, 4, 5]",
  "Avec des clés texte, une clé en double est écrasée par la dernière.")
E("array_sum", "php", "array_sum", ["fn:array_sum"], "array_sum(array $tableau): int|float",
  "Additionne tous les nombres d'un tableau.", [("$tableau", "un tableau de nombres")], "la somme",
  "array_sum([4990, 1990, 1990]);", "8970")
E("array_unique", "php", "array_unique", ["fn:array_unique"], "array_unique(array $tableau): array",
  "Retire les doublons (garde la première occurrence, avec sa clé).", [("$tableau", "le tableau")], "le tableau sans doublons",
  "count(array_unique([1, 1, 2, 2, 2]));", "2")
E("in_array", "php", "in_array", ["fn:in_array"], "in_array(mixed $valeur, array $tableau, bool $strict = false): bool",
  "Dit si une valeur se trouve dans un tableau.",
  [("$valeur", "ce qu'on cherche"), ("$tableau", "où on cherche"), ("$strict", "`true` : compare aussi le type (recommandé)")],
  "`true` ou `false`", "in_array(12, [0, 10, 12, 16, 18], true);", "true",
  "Sans `true` en 3e paramètre, `in_array('abc', [0])` peut donner des surprises : passe toujours `true`.")
E("array_search", "php", "array_search", ["fn:array_search"], "array_search(mixed $valeur, array $tableau, bool $strict = false): int|string|false",
  "Cherche une valeur et renvoie sa clé.", [("$valeur", "ce qu'on cherche"), ("$tableau", "où on cherche"), ("$strict", "comparer aussi le type")],
  "la clé trouvée, ou `false`", "array_search('b', ['a', 'b', 'c']);", "1",
  "La clé 0 et `false` se ressemblent : teste avec `=== false`.")
E("usort", "php", "usort", ["fn:usort"], "usort(array &$tableau, callable $comparer): bool",
  "Trie un tableau **sur place** avec ta propre règle de comparaison.",
  [("&$tableau", "le tableau, modifié directement (le `&`)"), ("$comparer", "fonction `fn($a, $b)` qui renvoie un nombre négatif si `$a` va avant, positif si après, 0 si égal ; l'opérateur `<=>` le fait pour toi")],
  "`true` (le résultat est dans le tableau lui-même)",
  "usort($films, fn($a, $b) => $b->getAnnee() <=> $a->getAnnee());   // plus récent d'abord\nusort($films, fn($a, $b) => strcmp($a->getTitre(), $b->getTitre()));",
  piege="Ne fais pas `$tries = usort(...)` : la fonction renvoie `true`, pas le tableau trié.")
E("implode", "php", "implode", ["fn:implode"], "implode(string $separateur, array $tableau): string",
  "Assemble les éléments d'un tableau en une chaîne, avec un séparateur.", [("$separateur", "ce qu'on met entre les éléments"), ("$tableau", "les morceaux")],
  "une chaîne", "implode(', ', ['Ana', 'Léo', 'Inès']);", "'Ana, Léo, Inès'")
E("explode", "php", "explode", ["fn:explode"], "explode(string $separateur, string $texte): array",
  "Coupe une chaîne en morceaux à chaque séparateur.", [("$separateur", "où couper"), ("$texte", "la chaîne")], "un tableau de chaînes",
  "explode(',', 'php,react,git');", "['php', 'react', 'git']")

# =========================================================================== PHP : chaînes et nombres
E("trim", "php", "trim", ["fn:trim"], "trim(string $texte): string", "Retire les espaces (et retours à la ligne) au début et à la fin.",
  [("$texte", "la chaîne")], "la chaîne nettoyée", "trim('  Léo  ');\ntrim('   ') === '';", "'Léo'\ntrue",
  "Un champ rempli d'espaces n'est pas « vide » pour `$x === ''` : fais `trim($x) === ''`.")
E("mb_strtolower", "php", "mb_strtolower / strtolower", ["fn:mb_strtolower", "fn:strtolower"], "mb_strtolower(string $texte): string",
  "Met une chaîne en minuscules, pour comparer sans tenir compte des majuscules.", [("$texte", "la chaîne")], "la chaîne en minuscules",
  "mb_strtolower('ÉCOLE');\nstrtolower('ÉCOLE');", "'école'\n'École' (les accents ne sont pas convertis)",
  "Avec des accents, utilise la version `mb_` (multi-octets), sinon « É » reste en majuscule.")
E("mb_strtoupper", "php", "mb_strtoupper / strtoupper", ["fn:mb_strtoupper", "fn:strtoupper"], "mb_strtoupper(string $texte): string",
  "Met une chaîne en majuscules.", [("$texte", "la chaîne")], "la chaîne en majuscules", "mb_strtoupper('bienvenue10');", "'BIENVENUE10'")
E("str_contains", "php", "str_contains", ["fn:str_contains"], "str_contains(string $texte, string $morceau): bool",
  "Dit si une chaîne contient un morceau de texte (sensible à la casse).", [("$texte", "où chercher"), ("$morceau", "ce qu'on cherche")], "`true` ou `false`",
  "str_contains('Sintel', 'tel');\nstr_contains(mb_strtolower('Sintel'), 'sin');", "true\ntrue",
  "Pour une recherche qui ignore les majuscules, mets les deux côtés en minuscules.")
E("str_starts_with", "php", "str_starts_with", ["fn:str_starts_with"], "str_starts_with(string $texte, string $debut): bool",
  "Dit si une chaîne commence par un morceau.", [("$texte", "la chaîne"), ("$debut", "le début attendu")], "`true` ou `false`",
  "str_starts_with('/api/films', '/api');", "true")
E("str_replace", "php", "str_replace", ["fn:str_replace"], "str_replace(string|array $cherche, string|array $remplace, string $texte): string",
  "Remplace toutes les occurrences d'un texte par un autre.", [("$cherche", "ce qu'on remplace"), ("$remplace", "par quoi"), ("$texte", "la chaîne")],
  "la nouvelle chaîne", "str_replace(' ', '-', 'la nuit des projecteurs');", "'la-nuit-des-projecteurs'")
E("substr", "php", "substr / mb_substr", ["fn:substr", "fn:mb_substr"], "mb_substr(string $texte, int $debut, ?int $longueur = null): string",
  "Extrait un morceau de chaîne.", [("$texte", "la chaîne"), ("$debut", "position de départ (0 = premier caractère ; négatif = depuis la fin)"), ("$longueur", "nombre de caractères")],
  "le morceau", "mb_substr('Bonjour', 0, 3);\nmb_substr('Bonjour', -4);", "'Bon'\n'jour'")
E("strlen", "php", "strlen / mb_strlen", ["fn:strlen", "fn:mb_strlen"], "mb_strlen(string $texte): int",
  "Longueur d'une chaîne.", [("$texte", "la chaîne")], "le nombre de caractères",
  "mb_strlen('Léo');\nstrlen('Léo');", "3\n4 (« é » prend 2 octets)", "Avec des accents, `strlen` compte des octets : utilise `mb_strlen`.")
E("sprintf", "php", "sprintf", ["fn:sprintf"], "sprintf(string $modele, mixed ...$valeurs): string",
  "Fabrique une chaîne à partir d'un modèle avec des « trous » (`%d` entier, `%s` texte, `%02d` entier sur 2 chiffres, `%.2f` décimal à 2 chiffres).",
  [("$modele", "le texte avec ses trous"), ("...$valeurs", "les valeurs à mettre dans les trous, dans l'ordre")], "la chaîne remplie",
  "sprintf('Épisode S%02dE%02d', 1, 2);\nsprintf('%d h %02d', 1, 5);\nsprintf('%.2f €', 12.5);", "'Épisode S01E02'\n'1 h 05'\n'12.50 €'")
E("number_format", "php", "number_format", ["fn:number_format"], "number_format(float $nombre, int $decimales = 0, string $virgule = '.', string $milliers = ','): string",
  "Formate un nombre pour l'affichage.", [("$nombre", "le nombre"), ("$decimales", "chiffres après la virgule"), ("$virgule", "le séparateur décimal"), ("$milliers", "le séparateur des milliers")],
  "une chaîne", "number_format(1234.5, 2, ',', ' ');", "'1 234,50'")
E("round", "php", "round / ceil / floor", ["fn:round", "fn:ceil", "fn:floor"], "round(float $n, int $decimales = 0): float",
  "Arrondit : `round` au plus proche, `ceil` au-dessus, `floor` en dessous.", [("$n", "le nombre"), ("$decimales", "(round seulement) chiffres gardés après la virgule")],
  "un float (pense à `(int)` pour avoir un entier)", "round(2.5);  ceil(4.1);  floor(4.9);\n(int) ceil(134 / 20);   // nombre de pages", "3.0  5.0  4.0\n7")
E("intdiv", "php", "intdiv", ["fn:intdiv"], "intdiv(int $a, int $b): int",
  "Division entière (sans virgule). Avec `%` (le reste), c'est l'outil des heures et minutes.", [("$a", "ce qu'on divise"), ("$b", "par combien")], "le quotient entier",
  "intdiv(92, 60);   // heures\n92 % 60;          // minutes restantes", "1\n32")
E("max", "php", "max / min", ["fn:max", "fn:min"], "max(mixed ...$valeurs): mixed",
  "Le plus grand (ou le plus petit) de plusieurs valeurs, ou d'un tableau.", [("...$valeurs", "des nombres, ou un seul tableau")], "la valeur",
  "max(1, (int) ceil(0 / 20));   // au moins 1 page\nmin($position, $duree);       // ne pas dépasser la durée", "1")

# =========================================================================== PHP : langage
E("isset", "php", "isset / empty", ["fn:isset", "fn:empty"], "isset(mixed $var): bool",
  "`isset` : la variable (ou la clé) existe et n'est pas `null`. `empty` : elle est absente, `null`, `0`, `''`, `[]` ou `false`.",
  [("$var", "une variable ou une case de tableau comme `$data['nom']`")], "`true` ou `false`",
  "isset($data['age']);\nempty($data['nom'] ?? '');", "false si la clé manque")
E("unset", "php", "unset", ["fn:unset"], "unset(mixed $var): void", "Supprime une variable ou une case d'un tableau.",
  [("$var", "ce qu'on supprime")], "rien", "unset($films[5]);")
E("json_encode", "php", "json_encode / json_decode", ["fn:json_encode", "fn:json_decode"], "json_encode(mixed $valeur, int $options = 0): string",
  "`json_encode` transforme une valeur PHP en texte JSON ; `json_decode($texte, true)` fait l'inverse (en tableau).",
  [("$valeur", "tableau, objet, nombre…"), ("$options", "par exemple `JSON_UNESCAPED_UNICODE` pour garder les accents lisibles")], "une chaîne JSON",
  "json_encode(['titre' => 'Été'], JSON_UNESCAPED_UNICODE);\njson_decode('{\"a\": 1}', true);", "'{\"titre\":\"Été\"}'\n['a' => 1]")
E("preg_match", "php", "preg_match", ["fn:preg_match"], "preg_match(string $motif, string $texte, array &$trouve = null): int",
  "Teste si un texte correspond à une expression régulière.", [("$motif", "l'expression régulière, entre `/…/`"), ("$texte", "le texte testé"), ("&$trouve", "rempli avec les morceaux capturés")],
  "1 si ça correspond, 0 sinon", "preg_match('/^\\d{5}$/', '44000');", "1")
E("filter_var", "php", "filter_var", ["fn:filter_var"], "filter_var(mixed $valeur, int $filtre): mixed",
  "Valide ou convertit une valeur avec un filtre prédéfini.", [("$valeur", "la valeur"), ("$filtre", "`FILTER_VALIDATE_EMAIL`, `FILTER_VALIDATE_INT`…")],
  "la valeur si elle est valide, sinon `false`", "filter_var('ana@exemple.fr', FILTER_VALIDATE_EMAIL) !== false;", "true")
E("var_dump", "php", "var_dump", ["fn:var_dump"], "var_dump(mixed ...$valeurs): void",
  "Affiche le contenu et le type d'une variable : l'outil de débogage de base.", [("...$valeurs", "ce qu'on veut inspecter")], "rien (affiche)",
  "var_dump([1, 'a']);", "array(2) { [0]=> int(1) [1]=> string(1) \"a\" }")
E("date", "php", "date", ["fn:date"], "date(string $format, ?int $timestamp = null): string",
  "La date courante (ou d'un timestamp) au format demandé.", [("$format", "`'Y'` année, `'Y-m-d'`, `'H:i'`…"), ("$timestamp", "un instant précis ; maintenant si absent")],
  "une chaîne", "(int) date('Y');", "2026", "Dans les entités et services testés, préfère une Horloge injectée : `date()` donne toujours « maintenant ».")
E("datetime", "php", "new DateTimeImmutable", ["new:DateTimeImmutable", "new:\\DateTimeImmutable"], "new \\DateTimeImmutable(string $quand = 'now')",
  "Un instant (date + heure) qui ne change jamais : chaque modification renvoie un **nouvel** objet.",
  [("$quand", "`'now'`, `'2026-11-20 20:00'`, `'+14 days'`…")], "un objet date",
  "$d = new \\DateTimeImmutable('2026-11-20');\n$d->modify('+14 days')->format('d/m/Y');", "'04/12/2026'")
E("format", "php", "->format (dates)", ["->format"], "$date->format(string $format): string",
  "Écrit une date sous forme de texte.", [("$format", "`d` jour, `m` mois, `Y` année, `H` heure, `i` minutes ; ex. `'d/m/Y H:i'`")], "une chaîne",
  "$d->format('d/m/Y à H\\hi');", "'20/11/2026 à 20h00'")
E("modify", "php", "->modify (dates)", ["->modify"], "$date->modify(string $changement): static",
  "Décale une date. Avec `DateTimeImmutable`, renvoie une **nouvelle** date (l'ancienne ne bouge pas).", [("$changement", "`'+1 day'`, `'-2 hours'`, `'+10 minutes'`…")],
  "la nouvelle date", "$rendreLe = $aujourdhui->modify('+14 days');",
  piege="`$d->modify('+1 day');` seul ne fait rien sur un Immutable : récupère le résultat.")
E("exceptions", "php", "throw new …Exception", ["new:InvalidArgumentException", "new:\\InvalidArgumentException", "new:DomainException", "new:\\DomainException", "new:LogicException", "new:\\LogicException", "new:RuntimeException"],
  "throw new \\DomainException(string $message)",
  "Arrête le code et signale un problème. `InvalidArgumentException` : un paramètre est impossible (âge -1). `DomainException` : une règle métier dit non (forfait plein). `LogicException` : erreur de programmation.",
  [("$message", "un message lisible, il peut finir affiché à l'utilisateur")], "rien : l'exécution s'arrête et remonte jusqu'à un `catch`",
  "if ($duree <= 0) throw new \\InvalidArgumentException('Durée invalide');",
  piege="Avec Symfony, une exception non gérée donne une erreur 500 : ajoute `#[WithHttpStatus(409)]` sur ta classe d'exception pour un vrai statut.")
E("getMessage", "php", "->getMessage", ["->getMessage"], "$exception->getMessage(): string", "Le message d'une exception attrapée.",
  [], "le texte passé au `new …Exception('…')`", "try { ... } catch (\\DomainException $e) {\n    echo $e->getMessage();\n}")
E("enum_from", "php", "Enum::from / tryFrom / ->value", ["::from", "::tryFrom", "->value"], "Genre::from(string|int $valeur): Genre",
  "Passe d'une valeur stockée (`'animation'`) à un cas d'enum (`Genre::Animation`), et inversement avec `->value`.",
  [("$valeur", "la valeur brute (venue de la base ou du JSON)")], "le cas de l'enum ; `tryFrom` renvoie `null` si la valeur est inconnue au lieu de lever une erreur",
  "Genre::from('animation');\nGenre::tryFrom('horreur');\nGenre::Animation->value;", "Genre::Animation\nnull\n'animation'")
E("enum_cases", "php", "Enum::cases", ["::cases"], "Forfait::cases(): array", "Liste tous les cas d'un enum.", [], "un tableau de cas",
  "array_map(fn($f) => $f->value, Forfait::cases());", "['essentiel', 'standard', 'premium']")
E("first_class", "php", "fonction(...) (callable)", ["re:[\\w>:]\\(\\.\\.\\.\\)"], "MaClasse::methode(...)",
  "Les `(...)` après un nom de fonction ne l'appellent pas : ils en font une valeur qu'on passe à une autre fonction.",
  [], "un objet `Closure`", "array_map(FilmCard::fromEntity(...), $films);\n// équivaut à : array_map(fn($f) => FilmCard::fromEntity($f), $films)")
E("declare", "php", "declare(strict_types=1)", ["fn:declare"], "declare(strict_types=1);",
  "En haut d'un fichier : PHP refuse les conversions automatiques (passer `'12'` à un paramètre `int` devient une erreur).", [], "rien",
  "declare(strict_types=1);\nfunction age(int $a) {}\nage('12');   // TypeError")
E("instanceof", "php", "instanceof", ["re:\\binstanceof\\b"], "$objet instanceof NomDeClasse", "Teste si un objet est d'une classe (ou l'implémente).", [], "`true` ou `false`",
  "$e instanceof \\DomainException;")
E("nullsafe", "php", "?? , ??= et ?->", ["re:\\?\\?|\\?->"], "$a ?? $b   ·   $x ??= $defaut   ·   $objet?->methode()",
  "`??` : la valeur de gauche si elle existe et n'est pas null, sinon celle de droite. `??=` : donne une valeur seulement si c'est null. `?->` : appelle la méthode seulement si l'objet n'est pas null.",
  [], "", "$page = $data['page'] ?? 1;\n$filtres ??= new CatalogueFiltres();\n$v?->getPosition();   // null si $v est null")
E("match", "php", "match", ["fn:match"], "match ($valeur) { cas => résultat, … }",
  "Comme un `switch`, mais qui renvoie une valeur et compare strictement (`===`). Sans `default`, une valeur imprévue lève une erreur.", [], "la valeur du cas trouvé",
  "return match ($this) {\n    Forfait::Essentiel => 2,\n    Forfait::Standard => 4,\n    Forfait::Premium => 5,\n};")

# =========================================================================== Doctrine
E("persist", "doctrine", "->persist", ["->persist"], "$em->persist(object $entite): void",
  "Dit à Doctrine : « cet objet est nouveau, il faudra l'enregistrer ». Rien n'est envoyé à la base tout de suite.",
  [("$entite", "une entité nouvellement créée avec `new`")], "rien",
  "$em->persist($film);\n$em->flush();   // c'est ici que l'INSERT part",
  piege="Inutile pour une entité déjà chargée depuis la base : Doctrine la suit déjà, un `flush()` suffit après la modification.")
E("flush", "doctrine", "->flush", ["->flush"], "$em->flush(): void",
  "Envoie à la base tout ce qui a changé depuis le dernier flush (INSERT, UPDATE, DELETE), dans une transaction.", [], "rien",
  "$profil->renommer('Léo');\n$em->flush();   // UPDATE profil SET nom = 'Léo' ...")
E("remove", "doctrine", "->remove", ["->remove"], "$em->remove(object $entite): void", "Prévoit la suppression d'une entité ; le DELETE part au `flush()`.",
  [("$entite", "l'entité à supprimer")], "rien", "$em->remove($profil);\n$em->flush();")
E("find", "doctrine", "->find", ["->find"], "$repository->find(int $id): ?object",
  "Cherche une entité par son identifiant.", [("$id", "la clé primaire")], "l'entité, ou `null` si elle n'existe pas",
  "$film = $films->find($id) ?? throw new NotFoundHttpException('Film introuvable');",
  "Toujours prévoir le cas `null`.")
E("findAll", "doctrine", "->findAll / findBy / findOneBy", ["->findAll", "->findBy", "->findOneBy"], "$repository->findBy(array $criteres, ?array $tri = null, ?int $limite = null): array",
  "Charge des entités : toutes (`findAll`), celles qui correspondent à des critères (`findBy`), ou une seule (`findOneBy`, `null` si aucune).",
  [("$criteres", "`['genre' => 'animation']`"), ("$tri", "`['annee' => 'DESC']`"), ("$limite", "nombre maximum")], "un tableau d'entités (ou une entité / null)",
  "$films->findBy(['genre' => Genre::Animation], ['titre' => 'ASC'], 10);\n$comptes->findOneBy(['email' => $email]);")
E("createQueryBuilder", "doctrine", "->createQueryBuilder", ["->createQueryBuilder"], "$repository->createQueryBuilder(string $alias): QueryBuilder",
  "Commence une requête sur mesure (filtres optionnels, jointures, tri) écrite en PHP.", [("$alias", "un petit nom pour l'entité dans la requête, ex. `'f'`")], "un QueryBuilder",
  "$qb = $this->createQueryBuilder('f')\n    ->andWhere('f.genre = :g')->setParameter('g', $genre)\n    ->orderBy('f.titre', 'ASC');\nreturn $qb->getQuery()->getResult();")
E("andWhere", "doctrine", "->andWhere / ->where", ["->andWhere", "->where"], "$qb->andWhere(string $condition): QueryBuilder",
  "Ajoute une condition (`AND`). Les valeurs passent par des paramètres nommés `:nom`, jamais collées dans la chaîne.", [("$condition", "ex. `'f.titre LIKE :q'`")],
  "le même QueryBuilder (on enchaîne)", "if ($q) $qb->andWhere('LOWER(f.titre) LIKE :q')->setParameter('q', '%'.mb_strtolower($q).'%');",
  "Utilise toujours `andWhere` : `where` efface les conditions précédentes.")
E("setParameter", "doctrine", "->setParameter", ["->setParameter"], "$qb->setParameter(string $nom, mixed $valeur): QueryBuilder",
  "Donne une valeur à un paramètre `:nom` de la requête. C'est ce qui protège des injections SQL.", [("$nom", "le nom sans les deux-points"), ("$valeur", "la valeur")],
  "le même QueryBuilder", "->setParameter('g', 'animation')")
E("orderBy", "doctrine", "->orderBy", ["->orderBy", "->addOrderBy"], "$qb->orderBy(string $champ, string $sens = 'ASC'): QueryBuilder",
  "Trie les résultats.", [("$champ", "ex. `'f.annee'`"), ("$sens", "`'ASC'` croissant ou `'DESC'` décroissant")], "le même QueryBuilder", "->orderBy('f.ajouteLe', 'DESC')")
E("leftJoin", "doctrine", "->leftJoin / ->addSelect", ["->leftJoin", "->join", "->addSelect"], "$qb->leftJoin(string $relation, string $alias): QueryBuilder",
  "Joint une relation. Avec `addSelect`, les objets liés sont chargés **dans la même requête** : c'est le remède au problème N+1.",
  [("$relation", "ex. `'s.episodes'`"), ("$alias", "un nom pour la relation, ex. `'e'`")], "le même QueryBuilder",
  "$this->createQueryBuilder('s')->leftJoin('s.episodes', 'e')->addSelect('e')")
E("setMaxResults", "doctrine", "->setMaxResults / ->setFirstResult", ["->setMaxResults", "->setFirstResult"], "$qb->setMaxResults(int $n): QueryBuilder",
  "Limite le nombre de résultats (`LIMIT`) et saute les premiers (`OFFSET`) : la pagination côté base.", [("$n", "combien")], "le même QueryBuilder",
  "->setFirstResult(($page - 1) * $parPage)->setMaxResults($parPage)")
E("getResult", "doctrine", "->getQuery()->getResult()", ["->getQuery", "->getResult", "->getOneOrNullResult", "->getSingleScalarResult"], "$qb->getQuery()->getResult(): array",
  "Exécute la requête construite. `getResult` : une liste ; `getOneOrNullResult` : un seul objet ou null ; `getSingleScalarResult` : un seul nombre (COUNT).", [],
  "les entités trouvées", "$total = (int) $qb->select('COUNT(f.id)')->getQuery()->getSingleScalarResult();")
E("collection", "doctrine", "ArrayCollection (add, removeElement, contains…)", ["new:ArrayCollection", "->removeElement", "->contains", "->toArray", "->isEmpty"],
  "new ArrayCollection(array $elements = [])",
  "La « liste » de Doctrine pour les relations OneToMany. `add($x)`, `removeElement($x)`, `contains($x)`, `count()`, `toArray()`, `isEmpty()`, et on peut faire `foreach` dessus.",
  [], "", "$this->episodes = new ArrayCollection();   // dans le constructeur\n$this->episodes->add($ep);\n$this->episodes->removeElement($ep);   // + orphanRemoval → DELETE",
  piege="Crée la collection dans le constructeur, sinon `->add()` plante sur une propriété non initialisée.")
E("attr_entity", "doctrine", "#[ORM\\Entity] / #[ORM\\Column]", ["#Entity", "#Column", "#Id", "#GeneratedValue", "#Table"], "#[ORM\\Column(type: ..., nullable: ..., enumType: ...)]",
  "Disent à Doctrine comment enregistrer la classe : `Entity` (c'est une table), `Id` + `GeneratedValue` (clé auto-incrémentée), `Column` (une colonne).",
  [("type", "`'text'`, `'decimal'`… (souvent deviné depuis le type PHP)"), ("nullable", "`true` si la colonne peut être vide"), ("enumType", "la classe d'enum à stocker")], "",
  "#[ORM\\Entity]\nclass Film\n{\n    #[ORM\\Id, ORM\\GeneratedValue, ORM\\Column]\n    private ?int $id = null;\n\n    #[ORM\\Column(enumType: Genre::class)]\n    private Genre $genre;\n}")
E("attr_relations", "doctrine", "#[ORM\\ManyToOne] / #[ORM\\OneToMany]", ["#ManyToOne", "#OneToMany", "#JoinColumn", "#OneToOne"], "#[ORM\\OneToMany(targetEntity: ..., mappedBy: ..., cascade: [...], orphanRemoval: ...)]",
  "Les deux côtés d'une relation. Le `ManyToOne` (plusieurs épisodes → une série) porte la colonne `serie_id` : c'est le côté propriétaire. Le `OneToMany` est le côté « liste ».",
  [("targetEntity", "la classe liée"), ("mappedBy / inversedBy", "le nom de la propriété de l'autre côté"), ("cascade", "`['persist']` : persister la série persiste ses épisodes"), ("orphanRemoval", "`true` : un élément retiré de la liste est supprimé"), ("JoinColumn(nullable: false)", "la relation est obligatoire")], "",
  "#[ORM\\ManyToOne(inversedBy: 'episodes')]\n#[ORM\\JoinColumn(nullable: false)]\nprivate Serie $serie;")
E("lifecycle", "doctrine", "#[ORM\\PrePersist] / #[ORM\\PreUpdate]", ["#PrePersist", "#PreUpdate", "#HasLifecycleCallbacks"], "#[ORM\\PrePersist] public function avantInsert(): void",
  "Une méthode appelée automatiquement juste avant l'INSERT (ou l'UPDATE). La classe doit avoir `#[ORM\\HasLifecycleCallbacks]`.", [], "",
  "#[ORM\\PrePersist]\npublic function dater(): void { $this->creeLe = new \\DateTimeImmutable(); }")

# =========================================================================== Symfony
E("route", "symfony", "#[Route]", ["#Route"], "#[Route(string $chemin, methods: [...], name: ...)]",
  "Relie une URL et une méthode HTTP à une action de contrôleur. `{id}` dans le chemin devient un paramètre de la méthode.",
  [("$chemin", "ex. `'/api/films/{id}'`"), ("methods", "`['GET']`, `['POST']`, `['PUT']`, `['PATCH']`, `['DELETE']`"), ("name", "un nom pour générer l'URL ailleurs")], "",
  "#[Route('/api/films/{id}', methods: ['GET'])]\npublic function fiche(int $id): JsonResponse { ... }")
E("json", "symfony", "$this->json", ["->json"], "$this->json(mixed $donnees, int $statut = 200, array $entetes = []): JsonResponse",
  "Renvoie une réponse JSON depuis un contrôleur (`AbstractController`).",
  [("$donnees", "un tableau, un DTO… (transformé en JSON)"), ("$statut", "200 par défaut ; 201 création, 204 sans contenu…"), ("$entetes", "ex. `['Location' => '/api/profils/12']`")], "une `JsonResponse`",
  "return $this->json(ProfilVue::fromEntity($p), 201, ['Location' => '/api/profils/' . $p->getId()]);\nreturn $this->json(null, 204);")
E("createNotFound", "symfony", "->createNotFoundException", ["->createNotFoundException"], "$this->createNotFoundException(string $message): NotFoundHttpException",
  "Fabrique une erreur 404 à lancer avec `throw`.", [("$message", "le message renvoyé")], "l'exception (à lancer)",
  "$film ?? throw $this->createNotFoundException('Film introuvable');")
E("http_exceptions", "symfony", "NotFound / AccessDenied … HttpException", ["new:NotFoundHttpException", "new:AccessDeniedHttpException", "new:ConflictHttpException", "new:BadRequestHttpException", "new:UnprocessableEntityHttpException"],
  "throw new NotFoundHttpException(string $message)",
  "Des exceptions qui portent directement un statut HTTP : 404 (`NotFound`), 403 (`AccessDenied`), 409 (`Conflict`), 400 (`BadRequest`), 422 (`UnprocessableEntity`).",
  [("$message", "le message renvoyé dans `{\"error\": ...}`")], "",
  "throw new AccessDeniedHttpException(\"Ce film n'est pas disponible pour ce profil\");")
E("map_payload", "symfony", "#[MapRequestPayload]", ["#MapRequestPayload"], "public function creer(#[MapRequestPayload] NouveauProfil $data)",
  "Transforme le JSON reçu en DTO, puis le valide. Si une contrainte échoue : réponse **422** avec la liste des erreurs, sans entrer dans ta méthode.", [], "",
  "#[Route('/api/profils', methods: ['POST'])]\npublic function creer(#[MapRequestPayload] NouveauProfil $data): JsonResponse")
E("map_query", "symfony", "#[MapQueryString]", ["#MapQueryString"], "public function liste(#[MapQueryString] ?Filtres $f)",
  "Remplit un DTO à partir des paramètres d'URL (`?q=sin&page=2`), convertit les types et valide. Sans aucun paramètre, tu reçois `null` (d'où le `?` et le `??=`).", [], "",
  "public function liste(#[MapQueryString] ?CatalogueFiltres $f): JsonResponse\n{\n    $f ??= new CatalogueFiltres();\n}")
E("current_user", "symfony", "#[CurrentUser]", ["#CurrentUser"], "public function action(#[CurrentUser] Compte $compte)",
  "Donne l'utilisateur connecté au contrôleur. Personne de connecté : 401 (sauf si le paramètre accepte `null`).", [], "",
  "public function liste(#[CurrentUser] Compte $compte): JsonResponse")
E("with_status", "symfony", "#[WithHttpStatus]", ["#WithHttpStatus"], "#[WithHttpStatus(int $statut)] class MonException extends \\DomainException {}",
  "Posé sur une classe d'exception : quand elle est levée, Symfony répond avec ce statut et son message. Plus besoin de try/catch dans les contrôleurs.",
  [("$statut", "souvent 409 (conflit) ou 422")], "", "#[WithHttpStatus(409)]\nfinal class ForfaitPleinException extends \\DomainException {}")
E("event_listener", "symfony", "#[AsEventListener]", ["#AsEventListener"], "#[AsEventListener(event: ..., priority: ...)]",
  "Branche une méthode sur un évènement de Symfony (requête reçue, réponse envoyée, exception…).", [("event", "ex. `KernelEvents::EXCEPTION`"), ("priority", "plus grand = appelé plus tôt")], "",
  "#[AsEventListener(event: KernelEvents::EXCEPTION)]\npublic function surErreur(ExceptionEvent $e): void { ... }")
E("assert_notblank", "symfony", "Assert\\NotBlank", ["Assert:NotBlank", "Assert:NotNull"], "#[Assert\\NotBlank(message: '...')]",
  "Refuse une valeur vide (`''`, `null`, `[]`). `NotNull` refuse seulement `null`.", [("message", "le texte de l'erreur 422")], "", "#[Assert\\NotBlank(message: 'Donne un nom au profil')]\npublic readonly string $nom,")
E("assert_length", "symfony", "Assert\\Length", ["Assert:Length"], "#[Assert\\Length(min: ..., max: ..., message: ...)]",
  "Limite la longueur d'un texte.", [("min / max", "longueur minimum / maximum en caractères"), ("message", "le texte de l'erreur")], "",
  "#[Assert\\Length(max: 20, message: '20 caractères maximum')]")
E("assert_range", "symfony", "Assert\\Range / Positive", ["Assert:Range", "Assert:Positive", "Assert:PositiveOrZero", "Assert:GreaterThan"], "#[Assert\\Range(min: ..., max: ..., notInRangeMessage: ...)]",
  "Limite un nombre : entre deux bornes (`Range`), > 0 (`Positive`), ≥ 0 (`PositiveOrZero`).", [("min / max", "les bornes incluses"), ("notInRangeMessage", "le texte de l'erreur")], "",
  "#[Assert\\Range(min: 1, max: 24)] public readonly int $parPage = 12,\n#[Assert\\Positive] public readonly int $page = 1,")
E("assert_choice", "symfony", "Assert\\Choice", ["Assert:Choice"], "#[Assert\\Choice(array $choix, message: ...)]",
  "N'accepte qu'une valeur de la liste (liste blanche).", [("$choix", "les valeurs autorisées")], "",
  "#[Assert\\Choice(['action', 'animation', 'comedie'])] public readonly ?string $genre = null,")
E("assert_email", "symfony", "Assert\\Email / Regex", ["Assert:Email", "Assert:Regex"], "#[Assert\\Email]  ·  #[Assert\\Regex(pattern: '/.../')]",
  "`Email` : vérifie le format d'une adresse. `Regex` : vérifie avec une expression régulière.", [("pattern", "l'expression régulière")], "",
  "#[Assert\\Regex(pattern: '/^\\d{5}$/', message: 'Code postal à 5 chiffres')]")
E("assert_count", "symfony", "Assert\\Count / Valid / All", ["Assert:Count", "Assert:Valid", "Assert:All"], "#[Assert\\Count(min: ..., max: ...)]",
  "Pour les tableaux : `Count` limite le nombre d'éléments, `All` applique des contraintes à chaque élément, `Valid` valide aussi les DTO imbriqués.", [], "",
  "#[Assert\\Count(min: 1, message: 'Au moins une ligne')]\n#[Assert\\Valid]\npublic readonly array $lignes,")

# =========================================================================== JavaScript : tableaux
E("js_map", "js", ".map", [".map"], "tableau.map((element, index) => nouveau)",
  "Transforme chaque élément et renvoie un **nouveau** tableau de même taille. En React, c'est ce qui affiche une liste.",
  [("element", "l'élément en cours"), ("index", "sa position (facultatif)")], "un nouveau tableau",
  "[1, 2, 3].map((n) => n * 2);\nfilms.map((f) => <li key={f.id}>{f.titre}</li>)", "[2, 4, 6]",
  "Dans une liste React, chaque élément a besoin d'une `key` unique et stable (l'id, pas l'index).")
E("js_filter", "js", ".filter", [".filter"], "tableau.filter((element) => booleen)",
  "Garde les éléments pour lesquels la fonction renvoie `true`.", [("element", "l'élément testé")], "un nouveau tableau (peut être vide)",
  "films.filter((f) => f.genre === 'animation');")
E("js_find", "js", ".find / .findIndex", [".find", ".findIndex"], "tableau.find((element) => booleen)",
  "Le **premier** élément qui correspond (`find`) ou sa position (`findIndex`).", [("element", "l'élément testé")], "l'élément ou `undefined` (`findIndex` : la position ou -1)",
  "films.find((f) => f.id === 3);", "{ id: 3, titre: 'Sintel', ... }", "Prévois le cas `undefined` : `films.find(...)?.titre`.")
E("js_some", "js", ".some / .every", [".some", ".every"], "tableau.some((element) => booleen)",
  "`some` : au moins un élément correspond ? `every` : tous correspondent ?", [("element", "l'élément testé")], "`true` ou `false`",
  "[0, 12, 16].some((a) => a >= 16);\n[0, 12, 16].every((a) => a >= 12);", "true\nfalse")
E("js_reduce", "js", ".reduce", [".reduce"], "tableau.reduce((cumul, element) => nouveauCumul, depart)",
  "Réduit un tableau à une seule valeur (une somme, un objet…).", [("cumul", "le résultat en cours"), ("element", "l'élément en cours"), ("depart", "la valeur de départ du cumul")],
  "la valeur finale", "lignes.reduce((total, l) => total + l.prix * l.quantite, 0);",
  piege="N'oublie pas la valeur de départ (`0`), sinon un tableau vide plante.")
E("js_includes", "js", ".includes", [".includes"], "tableau.includes(valeur)  ·  texte.includes(morceau)",
  "Dit si un tableau contient une valeur, ou si un texte contient un morceau.", [("valeur", "ce qu'on cherche")], "`true` ou `false`",
  "[0, 10, 12].includes(12);\n'Sintel'.toLowerCase().includes('sin');", "true\ntrue")
E("js_push", "js", ".push", [".push"], "tableau.push(element)",
  "Ajoute à la fin d'un tableau, **en le modifiant**.", [("element", "ce qu'on ajoute")], "la nouvelle longueur",
  "liste.push(nouveau);",
  piege="En React, ne fais jamais `push` sur un state : crée un nouveau tableau avec `setListe([...liste, nouveau])`.")
E("js_slice", "js", ".slice", [".slice"], "tableau.slice(debut, fin)",
  "Copie un morceau d'un tableau (ou d'un texte) sans le modifier.", [("debut", "position de départ"), ("fin", "position d'arrêt, non incluse")], "le morceau",
  "['a', 'b', 'c', 'd'].slice(1, 3);\n'2026-11-16T10:00'.slice(0, 10);", "['b', 'c']\n'2026-11-16'")
E("js_sort", "js", ".sort", [".sort"], "tableau.sort((a, b) => nombre)",
  "Trie un tableau **sur place** : négatif si `a` va avant `b`, positif sinon.", [("a, b", "deux éléments à comparer")], "le même tableau, trié",
  "[...films].sort((a, b) => a.titre.localeCompare(b.titre));",
  piege="`sort` modifie le tableau : sur un state React, copie d'abord avec `[...tableau]`.")
E("js_join", "js", ".join / .split", [".join", ".split"], "tableau.join(separateur)  ·  texte.split(separateur)",
  "`join` assemble un tableau en texte ; `split` coupe un texte en tableau.", [("separateur", "ex. `', '`")], "",
  "['Ana', 'Léo'].join(', ');\n'php,react'.split(',');", "'Ana, Léo'\n['php', 'react']")
E("js_foreach", "js", ".forEach", [".forEach"], "tableau.forEach((element) => { ... })",
  "Exécute une action pour chaque élément (sans rien renvoyer).", [("element", "l'élément")], "`undefined`",
  "erreurs.forEach((e) => console.log(e.message));", piege="Pour transformer, utilise `map` ; pour garder, `filter`.")
E("js_spread", "js", "... (décomposition)", ["re:(?<![.\\w])\\.\\.\\.[\\w\\[{(]"], "[...tableau, element]  ·  { ...objet, champ: valeur }",
  "Copie le contenu d'un tableau ou d'un objet dans un nouveau. C'est la façon de « modifier » un state React sans le muter.", [], "",
  "setListe([...liste, nouveau]);\nsetForm({ ...form, nom: 'Léo' });")
E("object_keys", "js", "Object.keys / entries / values", ["Object.keys", "Object.entries", "Object.values", "Object.fromEntries"], "Object.entries(objet)",
  "Transforme un objet en tableau : ses clés (`keys`), ses valeurs (`values`) ou des paires `[clé, valeur]` (`entries`).", [("objet", "l'objet")], "un tableau",
  "Object.entries({ q: 'sin', page: 2 });", "[['q', 'sin'], ['page', 2]]")
E("json_js", "js", "JSON.stringify / JSON.parse", ["JSON.stringify", "JSON.parse"], "JSON.stringify(valeur)  ·  JSON.parse(texte)",
  "Objet → texte JSON (`stringify`) et texte JSON → objet (`parse`).", [("valeur / texte", "ce qu'on convertit")], "",
  "JSON.stringify({ nom: 'Léo' });\nJSON.parse('{\"nom\":\"Léo\"}').nom;", "'{\"nom\":\"Léo\"}'\n'Léo'")

# =========================================================================== JavaScript : texte, nombres, temps
E("js_trim", "js", ".trim", [".trim"], "texte.trim()", "Retire les espaces au début et à la fin.", [], "le texte nettoyé",
  "'  ana@exemple.fr '.trim();", "'ana@exemple.fr'")
E("js_lower", "js", ".toLowerCase / .toUpperCase", [".toLowerCase", ".toUpperCase"], "texte.toLowerCase()", "Met en minuscules (ou en majuscules).", [], "le nouveau texte",
  "'BIENVENUE10'.toLowerCase();", "'bienvenue10'")
E("js_replace", "js", ".replace / .replaceAll", [".replace", ".replaceAll"], "texte.replace(cherche, remplace)",
  "Remplace un morceau de texte. Avec une chaîne, seule la première occurrence change ; `replaceAll` ou une regex `/…/g` remplacent tout.",
  [("cherche", "texte ou expression régulière"), ("remplace", "le nouveau texte")], "le nouveau texte", "'a-b-c'.replaceAll('-', ' ');", "'a b c'")
E("js_padstart", "js", ".padStart", [".padStart"], "texte.padStart(longueur, remplissage)",
  "Complète un texte par la gauche jusqu'à une longueur : idéal pour « 05 ».", [("longueur", "la longueur voulue"), ("remplissage", "le caractère ajouté")], "le texte complété",
  "String(5).padStart(2, '0');", "'05'")
E("js_startswith", "js", ".startsWith / .endsWith", [".startsWith", ".endsWith"], "texte.startsWith(debut)", "Le texte commence (ou finit) par… ?", [("debut", "le morceau attendu")], "`true` ou `false`",
  "'/api/films'.startsWith('/api');", "true")
E("js_tofixed", "js", ".toFixed", [".toFixed"], "nombre.toFixed(decimales)", "Écrit un nombre avec un nombre fixe de décimales.", [("decimales", "chiffres après la virgule")], "un **texte**",
  "(12.5).toFixed(2);", "'12.50'", "Le résultat est un texte : ne refais pas de calcul dessus.")
E("math", "js", "Math.round / floor / ceil / max / min", ["Math.round", "Math.floor", "Math.ceil", "Math.max", "Math.min", "Math.abs"], "Math.floor(nombre)",
  "Arrondir (`round` au plus proche, `floor` en dessous, `ceil` au-dessus) ; `max` / `min` donnent le plus grand / le plus petit.", [("nombre", "le ou les nombres")], "un nombre",
  "Math.round(12.345 * 100) / 100;   // arrondi au centime\nMath.max(1, Math.ceil(0 / 20));", "12.35\n1")
E("number_string", "js", "Number / String", ["fn:Number", "fn:String"], "Number(valeur)  ·  String(valeur)",
  "Convertit en nombre (`Number('12')` → 12, `Number('abc')` → NaN) ou en texte.", [("valeur", "ce qu'on convertit")], "",
  "Number(e.target.value);\nString(5).padStart(2, '0');")
E("settimeout", "js", "setTimeout / clearTimeout", ["fn:setTimeout", "fn:clearTimeout"], "setTimeout(fonction, ms)",
  "Exécute une fonction **une fois**, après un délai. `clearTimeout(id)` l'annule (base du debounce).", [("fonction", "ce qu'on exécute"), ("ms", "le délai en millisecondes")], "un identifiant pour l'annuler",
  "const id = setTimeout(() => chercher(q), 300);\nreturn () => clearTimeout(id);   // dans un useEffect")
E("setinterval", "js", "setInterval / clearInterval", ["fn:setInterval", "fn:clearInterval"], "setInterval(fonction, ms)",
  "Exécute une fonction **à intervalle régulier** jusqu'à `clearInterval(id)`.", [("fonction", "ce qu'on exécute"), ("ms", "l'intervalle")], "un identifiant",
  "const id = setInterval(sauvegarder, 10000);\nreturn () => clearInterval(id);", piege="Sans `clearInterval` dans le nettoyage d'un `useEffect`, les intervalles s'empilent.")
E("date_js", "js", "Date.now / new Date / toISOString", ["Date.now", ".toISOString", "new:Date"], "Date.now()  ·  new Date().toISOString()",
  "`Date.now()` : l'instant présent en millisecondes. `toISOString()` : une date en texte standard (`2026-11-16T15:00:00.000Z`).", [], "",
  "new Date(Date.now() + 14 * 864e5).toISOString().slice(0, 10);   // dans 14 jours", "'2026-11-30'")
E("encodeuri", "js", "encodeURIComponent", ["fn:encodeURIComponent"], "encodeURIComponent(texte)",
  "Rend un texte sûr pour une URL (espaces, accents, `&`…).", [("texte", "la valeur à mettre dans l'URL")], "le texte encodé",
  "`/api/films?q=${encodeURIComponent('la nuit & moi')}`", "'/api/films?q=la%20nuit%20%26%20moi'",
  "Avec axios, passe plutôt `params: { q }` : l'encodage est fait pour toi.")
E("console_log", "js", "console.log", ["console.log", "console.error", "console.warn"], "console.log(...valeurs)",
  "Affiche des valeurs dans la console du navigateur (F12) : l'outil de débogage de base.", [("...valeurs", "ce qu'on veut voir")], "", "console.log('films', films);")
E("localstorage", "js", "localStorage.getItem / setItem", ["localStorage.getItem", "localStorage.setItem", "localStorage.removeItem"], "localStorage.setItem(cle, texte)",
  "Garde du **texte** dans le navigateur, même après rechargement.", [("cle", "le nom"), ("texte", "la valeur (JSON.stringify pour un objet)")], "`getItem` : le texte ou `null`",
  "localStorage.setItem('profil', JSON.stringify(p));\nconst p = JSON.parse(localStorage.getItem('profil') ?? 'null');")
E("set_map", "js", "new Set / new Map", ["new:Set", "new:Map", ".has", ".add"], "new Set(tableau)  ·  new Map()",
  "`Set` : une collection sans doublons (`has`, `add`, `delete`). `Map` : des paires clé → valeur avec n'importe quel type de clé.", [], "",
  "const vus = new Set([1, 2, 2]);\nvus.has(2);   // true\n[...new Set(genres)];   // sans doublons")

# =========================================================================== JavaScript : asynchrone
E("fetch", "js", "fetch", ["fn:fetch"], "fetch(url, { method, headers, body, signal })",
  "Envoie une requête HTTP. Renvoie une promesse de **réponse** ; il faut encore lire le corps avec `res.json()`.",
  [("url", "l'adresse"), ("method", "`'GET'` (défaut), `'POST'`…"), ("headers", "ex. `{ 'Content-Type': 'application/json' }`"), ("body", "le corps en texte : `JSON.stringify(data)`"), ("signal", "pour annuler (AbortController)")],
  "une promesse de `Response`",
  "const res = await fetch('/api/films');\nif (!res.ok) throw new Error('HTTP ' + res.status);\nconst data = await res.json();",
  "fetch ne lève **pas** d'erreur pour un 404 ou un 500 : vérifie `res.ok` toi-même.")
E("res_json", "js", "res.json", [".json"], "reponse.json()",
  "Lit le corps d'une réponse `fetch` et le transforme en objet JS.", [], "une promesse de l'objet", "const films = await res.json();")
E("then", "js", ".then / .catch / .finally", [".then", ".catch", ".finally"], "promesse.then(succes).catch(erreur).finally(toujours)",
  "Ce qu'on fait quand une promesse se termine : avec le résultat (`then`), en cas d'erreur (`catch`), dans tous les cas (`finally`).",
  [("succes", "reçoit le résultat"), ("erreur", "reçoit l'erreur"), ("toujours", "pour arrêter un « Chargement… »")], "une nouvelle promesse",
  "api.get('/films').then((r) => setFilms(r.data)).catch(() => setErreur('…')).finally(() => setLoading(false));")
E("async_await", "js", "async / await", ["re:\\bawait\\b"], "async function f() { const x = await promesse; }",
  "`await` attend la fin d'une promesse et donne son résultat ; seulement dans une fonction `async`. Les erreurs s'attrapent avec `try/catch`.", [], "",
  "async function getFilms() {\n  const r = await api.get('/films');\n  return r.data;\n}")
E("promise", "js", "Promise / Promise.all", ["new:Promise", "Promise.all", "Promise.resolve", "Promise.reject"], "Promise.all([p1, p2])",
  "`Promise.all` lance plusieurs promesses **en même temps** et attend qu'elles soient toutes finies.", [("[p1, p2]", "des promesses")], "une promesse du tableau des résultats",
  "const [films, profils] = await Promise.all([getFilms(), getProfils()]);")
E("abort", "js", "AbortController / .abort", ["new:AbortController", ".abort"], "const c = new AbortController(); c.abort();",
  "Permet d'annuler une requête en cours : on passe `c.signal` à fetch/axios, puis `c.abort()`. Indispensable dans le nettoyage d'un `useEffect`.", [], "",
  "useEffect(() => {\n  const c = new AbortController();\n  api.get('/films', { signal: c.signal }).then(...);\n  return () => c.abort();\n}, [q]);")

# =========================================================================== React
E("usestate", "react", "useState", ["fn:useState"], "const [valeur, setValeur] = useState(valeurInitiale)",
  "Une valeur que le composant garde entre deux affichages. Appeler `setValeur` change la valeur **et réaffiche** le composant.",
  [("valeurInitiale", "la valeur au premier affichage")], "un tableau `[valeur, fonctionPourLaChanger]`",
  "const [q, setQ] = useState('');\nsetCompteur((c) => c + 1);   // à partir de l'ancienne valeur",
  "Ne copie pas dans un state ce qui se calcule (un total, une liste filtrée) : calcule-le pendant le rendu.")
E("useeffect", "react", "useEffect", ["fn:useEffect"], "useEffect(() => { ...; return nettoyage; }, [dependances])",
  "Lance du code **après** l'affichage : charger des données, s'abonner, démarrer un minuteur. Il se relance quand une dépendance change.",
  [("fonction", "le code à lancer ; elle peut renvoyer une fonction de nettoyage"), ("[dependances]", "les valeurs qui déclenchent une relance ; `[]` = une seule fois")], "rien",
  "useEffect(() => {\n  const id = setInterval(tick, 1000);\n  return () => clearInterval(id);\n}, []);",
  "Chaque valeur utilisée dans l'effet doit être dans le tableau de dépendances.")
E("usememo", "react", "useMemo / useCallback", ["fn:useMemo", "fn:useCallback"], "const v = useMemo(() => calcul, [deps])",
  "Garde le résultat d'un calcul (`useMemo`) ou une fonction (`useCallback`) d'un rendu à l'autre, tant que les dépendances ne changent pas.",
  [("calcul", "la fonction qui produit la valeur"), ("[deps]", "quand recalculer")], "la valeur gardée",
  "const sauvegarde = useMemo(() => new Sauvegarde(envoyer), [filmId]);")
E("useref", "react", "useRef", ["fn:useRef"], "const ref = useRef(valeurInitiale)",
  "Une boîte qui garde une valeur entre les rendus **sans** réafficher quand elle change (`ref.current`). Sert aussi à viser un élément du DOM.", [("valeurInitiale", "la valeur de départ")], "un objet `{ current }`",
  "const video = useRef<HTMLVideoElement>(null);\n<video ref={video} />\nvideo.current?.play();")
E("usecontext", "react", "useContext / createContext", ["fn:useContext", "fn:createContext"], "const valeur = useContext(MonContexte)",
  "Lit une valeur partagée par un composant parent (`<MonContexte.Provider value={...}>`), sans la passer de props en props.", [("MonContexte", "créé avec `createContext`")], "la valeur du Provider le plus proche",
  "const profil = useContext(ProfilContext);")
E("preventdefault", "react", "e.preventDefault", [".preventDefault"], "evenement.preventDefault()",
  "Empêche le comportement par défaut du navigateur : pour un `<form>`, recharger la page.", [], "",
  "<form onSubmit={(e) => { e.preventDefault(); envoyer(); }}>")
E("target_value", "react", "e.target.value / onChange", [], "onChange={(e) => setX(e.target.value)}",
  "Dans un champ contrôlé, `e.target.value` est ce que l'utilisateur vient de taper (toujours du **texte**).", [], "",
  "<input value={q} onChange={(e) => setQ(e.target.value)} />\n<input type=\"number\" onChange={(e) => setAge(Number(e.target.value))} />")

# =========================================================================== axios & TanStack Query
E("axios_create", "donnees", "axios.create", ["axios.create"], "axios.create({ baseURL, headers, timeout })",
  "Crée un client axios configuré une fois pour toute l'appli.", [("baseURL", "le début commun des URL, ex. `'/api'`"), ("timeout", "délai maximum en ms")], "un client (`api`)",
  "export const api = axios.create({ baseURL: '/api' });")
E("axios_get", "donnees", "api.get / axios.get", ["api.get", "axios.get", "client.get", "http.get"], "api.get<T>(url, { params, signal })",
  "Requête GET. Contrairement à fetch, la réponse est déjà lue (`r.data`) et un statut 4xx/5xx **lève une erreur**.",
  [("url", "relative au baseURL"), ("params", "les paramètres d'URL, encodés pour toi ; les `undefined` sont ignorés"), ("signal", "pour annuler")], "une promesse de réponse `{ data, status, headers }`",
  "const r = await api.get<Page<FilmCard>>('/films', { params: { q, genre } });\nr.data.items;")
E("axios_post", "donnees", "api.post / put / patch / delete", ["api.post", "api.put", "api.patch", "api.delete", "axios.post", "axios.put", "axios.delete"], "api.post<T>(url, corps)",
  "Envoie des données. Le corps est converti en JSON automatiquement.", [("url", "l'adresse"), ("corps", "l'objet à envoyer (pas pour delete)")], "une promesse de réponse",
  "await api.post('/profils', { nom: 'Léo', age: 8 });\nawait api.put(`/visionnages/${id}`, { position, envoi });")
E("isaxioserror", "donnees", "axios.isAxiosError", ["axios.isAxiosError"], "axios.isAxiosError(erreur)",
  "Dit si une erreur vient d'une requête axios ; on peut alors lire `erreur.response?.status` et `erreur.response?.data`.", [("erreur", "l'erreur attrapée")], "`true` ou `false`",
  "if (axios.isAxiosError(e) && e.response?.status === 409) setMessage(e.response.data.error);")
E("iscancel", "donnees", "axios.isCancel", ["axios.isCancel"], "axios.isCancel(erreur)", "Dit si l'erreur vient d'une requête annulée volontairement (à ignorer).", [("erreur", "l'erreur attrapée")], "`true` ou `false`",
  ".catch((e) => { if (!axios.isCancel(e)) setErreur('…'); })")
E("usequery", "donnees", "useQuery", ["fn:useQuery"], "useQuery({ queryKey, queryFn, placeholderData, enabled, staleTime })",
  "Charge des données, les met en cache et les recharge quand il faut. Remplace le trio `useState` + `useEffect` + `loading`.",
  [("queryKey", "le nom du cache, avec tout ce dont dépend la requête : `['films', { q, genre }]`"), ("queryFn", "la fonction qui va chercher les données"), ("placeholderData", "`keepPreviousData` : garder l'ancien résultat pendant le chargement du nouveau"), ("enabled", "`false` pour attendre (ex. tant qu'il n'y a pas d'id)"), ("staleTime", "combien de temps les données sont « fraîches »")],
  "`{ data, isPending, isError, error, refetch }`",
  "const { data, isPending, isError } = useQuery({\n  queryKey: ['film', id],\n  queryFn: () => getFilm(id),\n});",
  "Ne recopie pas `data` dans un `useState` : `data` est déjà l'état.")
E("usemutation", "donnees", "useMutation", ["fn:useMutation"], "useMutation({ mutationFn, onSuccess, onError })",
  "Pour les requêtes qui **modifient** (POST, PUT, DELETE). On la déclenche avec `mutate(...)`.",
  [("mutationFn", "la fonction qui envoie la requête"), ("onSuccess", "ce qu'on fait après (souvent : invalider le cache)"), ("onError", "en cas d'erreur")],
  "`{ mutate, isPending, isError, error, variables }`",
  "const creer = useMutation({\n  mutationFn: (p: NouveauProfil) => api.post('/profils', p),\n  onSuccess: () => qc.invalidateQueries({ queryKey: ['profils'] }),\n});\ncreer.mutate({ nom: 'Léo', age: 8 });")
E("invalidate", "donnees", "useQueryClient / invalidateQueries", ["fn:useQueryClient", ".invalidateQueries"], "queryClient.invalidateQueries({ queryKey })",
  "Marque un cache comme périmé : les composants qui l'utilisent rechargent les données.", [("queryKey", "le début de la clé : `['films']` invalide aussi `['films', { q }]`")], "une promesse",
  "const qc = useQueryClient();\nqc.invalidateQueries({ queryKey: ['profils'] });")
E("mutate", "donnees", ".mutate", [".mutate"], "mutation.mutate(variables)", "Déclenche une mutation avec ses données.", [("variables", "ce qui sera passé à `mutationFn`")], "rien (le résultat arrive dans l'état de la mutation)",
  "<button onClick={() => emprunt.mutate(livre.id)}>Emprunter</button>")
E("queryclient", "donnees", "QueryClient / QueryClientProvider", ["new:QueryClient"], "<QueryClientProvider client={new QueryClient()}>",
  "Le cache de TanStack Query, placé tout en haut de l'appli pour que tous les composants le partagent.", [], "",
  "const queryClient = new QueryClient();\n<QueryClientProvider client={queryClient}><App /></QueryClientProvider>")

# =========================================================================== Formulaires
E("useform", "formulaires", "useForm", ["fn:useForm"], "useForm<T>({ resolver, defaultValues, mode })",
  "Crée un formulaire géré par React Hook Form : valeurs, erreurs, envoi.",
  [("resolver", "`zodResolver(schema)` pour valider avec zod"), ("defaultValues", "les valeurs de départ"), ("mode", "`'onTouched'`, `'onChange'`… : quand valider")],
  "`{ register, handleSubmit, formState: { errors, isSubmitting }, reset, setError }`",
  "const { register, handleSubmit, formState: { errors } } = useForm<Profil>({ resolver: zodResolver(schema) });")
E("register", "formulaires", "register", ["fn:register", ".register"], "<input {...register('nom')} />",
  "Branche un champ sur le formulaire (valeur, changements, blur) en une ligne.", [("'nom'", "le nom du champ (avec TypeScript : vérifié)")], "des props à étaler sur l'input",
  "<input {...register('nom')} />\n<input type=\"number\" {...register('age', { valueAsNumber: true })} />")
E("handlesubmit", "formulaires", "handleSubmit", ["fn:handleSubmit", ".handleSubmit"], "<form onSubmit={handleSubmit(envoyer)}>",
  "Valide tout le formulaire, puis appelle ta fonction avec les valeurs propres **seulement si c'est valide**.", [("envoyer", "ta fonction, reçoit les valeurs")], "un gestionnaire pour `onSubmit`",
  "<form onSubmit={handleSubmit((v) => creer.mutate(v))}>")
E("seterror", "formulaires", "setError / reset", [".setError", ".reset"], "setError('champ', { message })  ·  reset(valeurs?)",
  "`setError` place une erreur sur un champ (par exemple renvoyée par l'API) ; `reset` remet le formulaire à zéro (ou à des valeurs).", [], "",
  "setError('nom', { message: 'Le profil Léo existe déjà' });\nreset();")
E("zodresolver", "formulaires", "zodResolver", ["fn:zodResolver"], "zodResolver(schema)", "Fait le lien entre un schéma zod et React Hook Form.", [("schema", "le schéma `z.object(...)`")], "un resolver",
  "useForm({ resolver: zodResolver(profilSchema) })")
E("z_object", "formulaires", "z.object / z.infer", ["z.object"], "z.object({ champ: schema, ... })",
  "Décrit la forme d'un objet et ses règles. `z.infer<typeof schema>` en tire le type TypeScript.", [("{ ... }", "un schéma par champ")], "un schéma",
  "const profilSchema = z.object({\n  nom: z.string().trim().min(1, 'Donne un nom').max(20),\n  age: z.number().int().min(0).max(17).optional(),\n});\ntype ProfilForm = z.infer<typeof profilSchema>;")
E("z_string", "formulaires", "z.string / z.number / z.boolean", ["z.string", "z.number", "z.boolean", "z.enum", "z.array", "z.date"], "z.string()  ·  z.number()  ·  z.enum([...])",
  "Les types de base d'un schéma zod, auxquels on enchaîne des règles.", [], "un schéma", "z.enum(['essentiel', 'standard', 'premium'])\nz.array(ligneSchema).min(1)")
E("z_min", "formulaires", ".min / .max / .email / .regex", [".min", ".max", ".email", ".regex", ".int", ".positive", ".optional", ".nullable"], "z.string().min(n, message)",
  "Règles enchaînées sur un schéma zod : longueur ou valeur minimum/maximum, format email, expression régulière, entier, facultatif…", [("n", "la borne"), ("message", "le texte de l'erreur")], "le schéma avec la règle",
  "z.string().email('Email invalide')\nz.number().int().positive()\nz.string().optional()")
E("z_refine", "formulaires", ".refine", [".refine", ".superRefine"], "schema.refine((valeurs) => booleen, { message, path })",
  "Une règle sur mesure, souvent entre plusieurs champs (mot de passe et confirmation).", [("fonction", "renvoie `true` si c'est valide"), ("path", "le champ où afficher l'erreur")], "le schéma",
  "schema.refine((v) => v.mdp === v.confirmation, { message: 'Les mots de passe diffèrent', path: ['confirmation'] })")
E("z_parse", "formulaires", ".parse / .safeParse", [".parse", ".safeParse"], "schema.safeParse(donnees)",
  "Valide des données avec un schéma. `parse` lève une erreur si c'est faux ; `safeParse` renvoie `{ success, data }` ou `{ success: false, error }`.", [("donnees", "ce qu'on vérifie")], "",
  "const r = profilSchema.safeParse(valeurs);\nif (!r.success) console.log(r.error.issues);")
E("z_coerce", "formulaires", "z.coerce", ["z.coerce"], "z.coerce.number()", "Convertit avant de valider : un champ texte « 12 » devient le nombre 12.", [], "", "age: z.coerce.number().int().min(0)")

# =========================================================================== Next.js
E("notfound", "next", "notFound", ["fn:notFound"], "notFound()", "Dans un Server Component, affiche la page 404 et arrête le rendu.", [], "rien (ne revient jamais)",
  "const film = await getFilm(id);\nif (!film) notFound();")
E("revalidatepath", "next", "revalidatePath", ["fn:revalidatePath"], "revalidatePath(chemin)",
  "Après une Server Action, demande à Next.js de refaire le rendu d'une page (son cache est vidé).", [("chemin", "ex. `'/films'`")], "rien",
  "'use server';\nexport async function ajouter(form: FormData) {\n  await db.film.create(...);\n  revalidatePath('/films');\n}")
E("redirect", "next", "redirect", ["fn:redirect"], "redirect(chemin)", "Redirige vers une autre page (Server Component ou Server Action).", [("chemin", "la destination")], "rien (ne revient jamais)",
  "redirect(`/films/${film.id}`);")
E("userouter", "next", "useRouter / usePathname / useSearchParams", ["fn:useRouter", "fn:usePathname", "fn:useSearchParams"], "const router = useRouter()",
  "Dans un Client Component : naviguer (`router.push('/films')`), lire l'URL actuelle (`usePathname`) ou ses paramètres (`useSearchParams`).", [], "",
  "'use client';\nconst router = useRouter();\nrouter.push('/films?genre=animation');")
E("use_client", "next", "'use client' / 'use server'", ["re:^\\s*['\"]use (client|server)['\"]"], "'use client';  ·  'use server';",
  "En haut d'un fichier : `'use client'` = composant exécuté dans le navigateur (state, clics) ; `'use server'` = fonctions exécutées sur le serveur (Server Actions).", [], "",
  "'use client';\nimport { useState } from 'react';")

E("js_optional", "js", "?. et ?? (valeurs absentes)", ["re:\\?\\.[\\w\\[(]|\\?\\?"], "objet?.champ  ·  valeur ?? parDefaut",
  "`?.` lit un champ (ou appelle une fonction) seulement si ce qui est à gauche n'est ni `null` ni `undefined` ; sinon le résultat vaut `undefined` au lieu de planter. `??` donne la valeur de droite quand celle de gauche est `null` ou `undefined`.",
  [], "", "const ville = user?.adresse?.ville;   // undefined si pas d'adresse\nconst page = params.page ?? 1;", res="undefined, puis 1 si page est absent",
  piege="`??` ne remplace pas `0` ni `''` (contrairement à `||`) : `0 ?? 5` vaut `0`, `0 || 5` vaut `5`.")
E("js_destructuring", "js", "Déstructuration { a } = objet", ["re:\\b(const|let)\\s*[{\\[]"], "const { a, b } = objet;  ·  const [x, setX] = tableau;",
  "Sort des valeurs d'un objet (par leur nom) ou d'un tableau (par leur position) dans des variables, en une ligne. Marche aussi dans les paramètres d'une fonction : `function Carte({ titre })`.",
  [], "", "const { titre, duree } = film;\nconst [premier, second] = ['a', 'b'];\nconst [compte, setCompte] = useState(0);", res="titre et duree contiennent film.titre et film.duree ; premier = 'a'",
  piege="Un nom qui n'existe pas dans l'objet donne `undefined`, sans erreur. Tu peux renommer : `const { titre: nom } = film`.")
E("js_arrow", "js", "Fonction fléchée () =>", ["re:=>"], "(a, b) => a + b  ·  (x) => { ...; return y; }",
  "Une façon courte d'écrire une fonction. Sans accolades, la valeur après `=>` est renvoyée directement ; avec accolades, il faut `return`.",
  [], "", "const double = (n) => n * 2;\nconst ids = films.map((f) => f.id);", res="double(4) → 8",
  piege="Pour renvoyer un objet sans accolades de bloc, entoure-le de parenthèses : `() => ({ id: 1 })`.")
E("js_template", "js", "Texte avec ${…} (template literal)", ["re:`[^`]*\\$\\{"], "`Bonjour ${nom}`",
  "Un texte entouré d'accents graves (touche AltGr + 7 sur un clavier AZERTY) au lieu de guillemets, dans lequel `${...}` insère la valeur d'une expression.",
  [], "", "const url = `/api/films/${id}`;", res="'/api/films/3' si id vaut 3")

METHODES = M

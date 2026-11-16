"""Parcours « Projet fil rouge : Bobine » : un site de streaming construit de A à Z.

Modules 1 à 3 : découper le projet, modèle de données Doctrine, API catalogue.
"""
from common import P, L, D, N, E, LANE, F, TD, RUN
from doctrine_sim import DOCTRINE_SETUP
from symfony_sim import SYMFONY_SETUP

T = "fil"


def FM(id, title, minutes, goal, why, flow, points, pitfalls, quiz, prereq, diagram, lessons, recap, example, notes, tds):
    return {"id": id, "track": T, "title": title, "minutes": minutes, "goal": goal, "why": why,
            "flow": flow, "points": points, "pitfalls": pitfalls, "quiz": quiz, "prereq": prereq,
            "diagram": diagram, "lessons": lessons, "recap": recap,
            "example": {"files": example if isinstance(example, list) else [example], "notes": notes}, "tds": tds}


def Q(q, options, answer, why):
    return {"q": q, "options": options, "answer": answer, "why": why}


JS = " Le bouton Exécuter lance les tests sur ton fichier : chaque message te dit ce qui est juste et pourquoi."
DSIM = " Le bouton Exécuter utilise un **Doctrine simulé** : il lit tes attributs `#[ORM\\...]` et affiche le SQL que Doctrine enverrait (`SQL> ...`). Les classes sont sans `namespace` pour tourner dans le navigateur ; dans ton projet, elles seraient dans `namespace App\\Entity;`."
SSIM = " Le bouton Exécuter utilise un **Symfony simulé** : `App::request('GET', '/api/...')` envoie une fausse requête HTTP à ton contrôleur (routes, `#[MapQueryString]`, validation, statuts) et affiche la réponse (`HTTP> ...`)."


def DRUN(tests):
    return RUN("php", tests=tests, setup=DOCTRINE_SETUP)


def SRUN(tests):
    return RUN("php", tests="Atelier\\App::$echo = false;\nAtelier\\App::reset();\n" + tests, setup=SYMFONY_SETUP)


CAHIER = r"""
# Bobine : cahier des charges (version 1)

Bobine est un site de streaming de courts et longs métrages et de séries.

## Ce que veut le client
- Un **catalogue** de films et de séries (saisons, épisodes), avec recherche et filtre par genre.
- Une **fiche** par œuvre : titre, année, durée, genre, âge minimum, résumé, bouton « Lecture ».
- Un **lecteur vidéo** dans la page.
- Un compte par foyer, avec plusieurs **profils** (comme « Ana », « Léo ») ; un profil peut être **enfant**.
- Le **contrôle parental** : un profil enfant ne voit pas les œuvres au-dessus de son âge.
- Trois **forfaits** : Essentiel (2 profils), Standard (4 profils), Premium (5 profils, qualité 4K).
- **Reprendre** une vidéo là où on l'a laissée, et une rangée « Continuer à regarder ».
- **Ma liste** : garder des œuvres pour plus tard.
- Plus tard : recommandations, téléchargement hors ligne, application TV.
"""

# =========================================================================== 1. Découper Bobine
SCEN_REPRISE = r"""// Ticket : « Reprendre la lecture »
// En tant que spectatrice, je veux reprendre une vidéo là où je l'ai arrêtée,
// pour ne pas chercher le bon moment à la main.
// Règles : la position est enregistrée pour le PROFIL (pas pour le compte) ;
// une vidéo arrêtée avant 1 minute n'est pas « commencée » ; au-delà de 95 %, elle est « terminée ».
//
// Les situations proposées par l'équipe :
//   reprise-simple      Léo a arrêté Sintel à 6 min ; il relance : la vidéo repart à 6 min.
//   autre-profil        Ana lance Sintel, que Léo a commencé : elle part du début.
//   moins-une-minute    Léo a regardé 40 secondes puis a fermé : il relance, ça part du début.
//   pile-une-minute     Léo s'est arrêté à 60 secondes exactement.
//   generique-fin       Léo s'est arrêté pendant le générique de fin (97 %) : la vidéo est terminée.
//   film-retire         Le film a été retiré du catalogue depuis.
//   deux-ecrans         Léo regarde sur la télé et sur le téléphone en même temps.
//   coupure-reseau      Le réseau coupe pendant la lecture : la dernière position envoyée doit rester.
//   logo-anime          Le logo Bobine doit être animé au chargement.
//   sous-titres         Les sous-titres doivent être disponibles en anglais.
//   pas-connecte        Une personne non connectée ouvre l'URL du lecteur.
//   position-bizarre    Le navigateur envoie une position plus grande que la durée de la vidéo.
"""

decoupe = FM("fil-decoupe", "Du cahier des charges aux tranches", 30,
  "Lire le cahier des charges de Bobine, le découper en tranches livrables les unes après les autres, et écrire les règles métier (contrôle parental, reprise de lecture) avant de coder.",
  "Un projet entier fait peur : par où commencer quand tout est à faire (base de données, API, front, vidéo…) ? La réponse est toujours la même : une tranche fine qui marche de bout en bout, puis la suivante. Et les règles métier floues (« vu », « enfant ») se clarifient avant, pas pendant.",
  ["Lire le cahier des charges et lister les **fonctionnalités**", "Les ranger en **tranches verticales** : chacune traverse base → API → écran et se montre à quelqu'un",
   "Choisir la **première tranche** : la plus petite qui a de la valeur (voir le catalogue et lancer une vidéo)", "Pour chaque tranche, écrire les **scénarios** et les **règles** à clarifier"],
  ["Une tranche verticale traverse toutes les couches ; une tranche horizontale (« toute la base d'abord ») ne se montre à personne.",
   "La première tranche de Bobine : catalogue + fiche + lecture. Sans profils, sans forfaits : on les ajoute ensuite.",
   "Le hors-périmètre s'écrit noir sur blanc (recommandations, hors ligne, TV) : c'est ce qui évite que le projet n'en finisse jamais.",
   "Une règle métier se transforme en fonction pure testable (`peutVoir`, `etatVisionnage`) avant d'être branchée à la base et à l'écran.",
   "Les seuils (âge, 1 minute, 95 %) sont les endroits où se cachent les bugs : on les teste des deux côtés."],
  ["Commencer par « toute la base de données » ou « toutes les maquettes ».", "Vouloir tout le cahier des charges dans la première version.", "Coder une règle floue (« vu », « enfant ») sans l'avoir écrite."],
  [Q("Quelle est la meilleure première tranche pour Bobine ?",
     ["Toutes les entités Doctrine", "Voir le catalogue, ouvrir une fiche et lancer une vidéo", "Les trois forfaits et le paiement", "Le design de la page d'accueil"], 1,
     "C'est la plus petite chose qui a de la valeur de bout en bout : on peut la montrer et la tester avec quelqu'un."),
   Q("Un profil « 12 ans » peut-il voir un film « déconseillé aux moins de 12 ans » ?",
     ["Oui : 12 ≥ 12", "Non : il faut avoir plus de 12 ans", "Ça dépend du forfait", "Seulement en Premium"], 0,
     "« Moins de 12 ans » exclut 11 ans et moins : à 12 ans, c'est autorisé. C'est le piège du > au lieu de >=."),
   Q("Où enregistre-t-on la position de lecture ?",
     ["Sur le compte", "Sur le profil", "Dans le navigateur seulement", "Sur le film"], 1,
     "Ana et Léo partagent le compte mais pas leur progression : la position appartient au couple profil + vidéo.")],
  prereq=[
    P("Cahier des charges", "Le document qui décrit ce que veut le client : fonctionnalités, règles, contraintes."),
    P("Tranche verticale", "Un petit morceau de fonctionnalité qui traverse toutes les couches (base, API, écran) et peut se montrer. Vu dans le parcours Découper."),
    P("MVP", "Minimum Viable Product : la plus petite version utile, qu'on peut mettre entre les mains de quelqu'un."),
    P("Règle métier", "Une règle qui vient du métier du client, pas de la technique : « un profil enfant ne voit pas les films interdits aux moins de 12 ans »."),
    P("Hors périmètre", "Ce qu'on décide de ne PAS faire dans cette version, écrit noir sur blanc."),
  ],
  diagram=D(
    nodes=[
      N("cdc", 0, 1, "Cahier des charges", "tout ce que veut\nle client", kind="doc", color="muted"),
      N("t1", 1, 0, "Tranche 1", "catalogue · fiche\n· lecture", color="good"),
      N("t2", 2, 0, "Tranche 2", "profils · contrôle\nparental"),
      N("t3", 3, 0, "Tranche 3", "reprise · continuer\nà regarder"),
      N("t4", 4, 0, "Tranche 4", "ma liste · forfaits"),
      N("hors", 1, 2, "Hors périmètre", "recos · hors ligne · TV", kind="note", color="bad"),
      N("reg", 3, 2, "Règles écrites", "peutVoir()\netatVisionnage()", kind="pill", color="warn"),
    ],
    edges=[E("cdc", "t1"), E("t1", "t2"), E("t2", "t3"), E("t3", "t4"), E("cdc", "hors", dashed=True), E("t2", "reg", dashed=True), E("t3", "reg", dashed=True)],
    caption="On livre tranche après tranche ; chaque tranche marche de bout en bout. Les règles floues sont écrites (et testées) avant d'être codées."),
  lessons=[
    L("Le projet : Bobine", r"""
Tout le parcours construit **un seul projet** : **Bobine**, un site de streaming. Chaque module ajoute un morceau au même code, et à la fin tu as un vrai projet à mettre sur ton GitHub.

Les vidéos sont de **courts films libres de droits** (les films d'animation de la Blender Foundation : *Big Buck Bunny*, *Sintel*, *Tears of Steel*…). On ne refait pas l'infrastructure vidéo d'un géant du streaming : on se concentre sur ce qu'un développeur full stack construit vraiment, le catalogue, les comptes, les règles, l'API et l'interface.

Le cahier des charges est dans l'onglet **Exemple**. Lis-le en entier avant la suite : à chaque ligne, demande-toi « est-ce que je sais exactement ce que ça veut dire ? ».
"""),
    L("Découper en tranches verticales", r"""
La tentation, devant un projet : « je fais d'abord toute la base de données, puis toute l'API, puis tout le front ». Pendant des semaines, **rien ne marche** et rien ne se montre.

À la place, découpe en **tranches verticales** : chacune traverse la base, l'API et l'écran, et se montre à quelqu'un.

| Tranche | Ce qu'on peut montrer | Ce qu'elle contient |
|---|---|---|
| **1. Regarder** | « Je vois le catalogue, j'ouvre une fiche, je lance la vidéo. » | entités Film / Série / Épisode, `GET /api/films`, page catalogue, page fiche, lecteur |
| **2. Profils** | « Je choisis mon profil ; Léo ne voit pas les films pour les grands. » | Compte, Profil, contrôle parental dans l'API et à l'écran |
| **3. Reprendre** | « Je reprends où j'en étais ; j'ai une rangée Continuer à regarder. » | Visionnage, `PUT` de la position, rangée sur l'accueil |
| **4. Ma liste et forfaits** | « J'ajoute à ma liste ; mon forfait limite le nombre de profils. » | Ma liste, règles des forfaits |

Et on écrit le **hors périmètre** : recommandations, téléchargement hors ligne, application TV. Ce n'est pas « jamais », c'est « pas dans cette version ».

La première tranche est volontairement **pauvre** : pas de profils, pas de forfait, pas de reprise. Mais elle marche de bout en bout, et chaque tranche suivante s'appuie sur elle.
"""),
    L("Écrire les règles avant de les coder", r"""
Deux règles de Bobine sont pleines de pièges. Écris-les **en phrases**, puis en **cas de test**, avant le code.

**Contrôle parental.** Chaque œuvre a un âge minimum : 0 (tous publics), 10, 12, 16 ou 18. Un profil enfant a un âge ; un profil adulte n'a pas de limite.

| Profil | Œuvre | Résultat | Pourquoi |
|---|---|---|---|
| adulte | 18 | visible | pas de limite |
| enfant 12 ans | 12 | **visible** | « déconseillé aux moins de 12 ans » : 12 ans, c'est bon |
| enfant 11 ans | 12 | caché | |
| enfant 7 ans | 0 | visible | tous publics |

**Reprise de lecture.** La position est enregistrée pour le **profil** (Ana et Léo ne partagent pas leur progression).

| Position | État | Pourquoi |
|---|---|---|
| moins de 60 s | non commencée | on a juste jeté un œil |
| entre 60 s et 95 % | en cours | apparaît dans « Continuer à regarder » |
| 95 % ou plus | terminée | le générique de fin ne compte pas |

Ces règles deviendront des fonctions pures (`peutVoir`, `etatVisionnage`) : faciles à tester, puis utilisées par l'API et par le front. C'est exactement ce que font les TD de ce module.
"""),
  ],
  recap=["Un seul projet, Bobine, construit module après module.",
         "Tranches verticales : chacune marche de bout en bout et se montre.",
         "Tranche 1 = catalogue + fiche + lecture ; le reste vient après.",
         "Le hors périmètre s'écrit.",
         "Les règles métier (âge, reprise) deviennent des fonctions pures testées, seuils compris."],
  example=[F("cahier-des-charges.md", "markdown", CAHIER), F("tranches.md", "markdown", r"""
# Bobine : découpage

## Tranche 1 : Regarder (MVP)
- Catalogue : liste des films et séries, recherche par titre, filtre par genre
- Fiche : titre, année, durée, genre, âge minimum, résumé
- Lecteur : la vidéo se lance dans la page

## Tranche 2 : Profils
- Choisir son profil à l'arrivée ; profil enfant avec un âge
- Contrôle parental : `peutVoir(profil, oeuvre)` appliqué à l'API ET à l'écran

## Tranche 3 : Reprendre
- Enregistrer la position toutes les 10 s (`PUT /api/visionnages`)
- Rangée « Continuer à regarder » (états : non commencé / en cours / terminé)

## Tranche 4 : Ma liste et forfaits
- Ajouter / retirer de Ma liste
- Forfaits : nombre de profils maximum, qualité

## Hors périmètre (version 1)
- Recommandations, téléchargement hors ligne, application TV, paiement réel

## Questions au client
- Une série « vue » : quand tous les épisodes sont terminés, ou le dernier ?
- Un profil enfant peut-il créer d'autres profils ? (proposition : non)
""")],
  notes=["Chaque tranche se termine par quelque chose qu'on peut montrer.",
         "Les questions au client sont notées, pas devinées.",
         "Les règles (âge, reprise) ont leurs tableaux de cas : ils deviennent les tests."],
  tds=[
    TD(1, "Trier les scénarios de la reprise de lecture",
       "Le ticket « Reprendre la lecture » est dans le fichier. Classe chaque situation : `heureux`, `erreur` (refusé avec un message), `limite` (accepté mais à traiter avec soin) ou `hors-sujet`." + JS,
       ["Remplis `classement` : une entrée par identifiant de la liste",
        "Valeurs : `'heureux'`, `'erreur'`, `'limite'`, `'hors-sujet'`",
        "Relis les règles du ticket : profil, 1 minute, 95 %"],
       [F("scenarios.ts", "ts", SCEN_REPRISE + r"""
type Famille = 'heureux' | 'erreur' | 'limite' | 'hors-sujet';

export const classement: Record<string, Famille> = {
  'reprise-simple': 'heureux',
  // à toi : les 11 autres
};
""")],
       ["« Erreur » = l'application doit refuser et le dire. « Limite » = elle accepte, mais c'est là qu'on se trompe (seuil, deux appareils, valeur bizarre, profil différent).",
        "Une personne non connectée qui ouvre le lecteur : on la laisse regarder ?",
        "Le logo et les sous-titres sont peut-être de vrais besoins… mais pas de ce ticket."],
       [F("scenarios.ts", "ts", SCEN_REPRISE + r"""
type Famille = 'heureux' | 'erreur' | 'limite' | 'hors-sujet';

export const classement: Record<string, Famille> = {
  'reprise-simple': 'heureux',
  'autre-profil': 'limite',       // la position appartient au profil : Ana part du début
  'moins-une-minute': 'limite',   // pas « commencée » : on repart du début
  'pile-une-minute': 'limite',    // le seuil : 60 s compte comme commencée
  'generique-fin': 'limite',      // ≥ 95 % : terminée, on ne propose pas de reprendre
  'film-retire': 'erreur',        // « Ce film n'est plus disponible »
  'deux-ecrans': 'limite',        // la dernière position envoyée gagne
  'coupure-reseau': 'limite',     // on garde la dernière position reçue
  'logo-anime': 'hors-sujet',
  'sous-titres': 'hors-sujet',
  'pas-connecte': 'erreur',       // 401 : il faut se connecter
  'position-bizarre': 'limite',   // on la ramène à la durée (et la vidéo est terminée)
};
""")],
       ["Chaque situation a sa famille", "Les seuils et les cas « deux appareils » sont des limites"],
       run=RUN("js", entry="scenarios.ts", tests=r"""
const { classement } = require('./scenarios');
const attendu = {
  'reprise-simple': ['heureux', 'le cas prévu par le ticket'],
  'autre-profil': ['limite', 'accepté, mais la position appartient au PROFIL : Ana part du début'],
  'moins-une-minute': ['limite', 'accepté : sous 1 minute la vidéo n\'est pas « commencée », elle repart du début'],
  'pile-une-minute': ['limite', 'LE seuil : 60 s compte-t-il ? (oui : « avant 1 minute » exclut 60)'],
  'generique-fin': ['limite', 'au-delà de 95 % la vidéo est terminée : on ne propose pas de reprendre au générique'],
  'film-retire': ['erreur', 'l\'application doit refuser et dire que le film n\'est plus disponible'],
  'deux-ecrans': ['limite', 'accepté : deux positions arrivent, la dernière gagne'],
  'coupure-reseau': ['limite', 'accepté : on garde la dernière position reçue'],
  'logo-anime': ['hors-sujet', 'du design, pas ce ticket'],
  'sous-titres': ['hors-sujet', 'un vrai besoin, mais un autre ticket'],
  'pas-connecte': ['erreur', 'refusé (401) : sans profil, pas de position à reprendre'],
  'position-bizarre': ['limite', 'accepté : on ramène la position à la durée de la vidéo'],
};
for (const [id, [fam, pourquoi]] of Object.entries(attendu)) {
  assert.equal(classement[id], fam, id + ' → ' + fam + ' : ' + pourquoi);
}
const inconnus = Object.keys(classement).filter((k) => !attendu[k]);
assert(inconnus.length === 0, 'Pas d\'identifiant inventé', inconnus.join(', '));
""")),
    TD(2, "Contrôle parental : les cas, puis la règle",
       "Écris d'abord les **cas de test** de la règle du contrôle parental, puis la fonction `peutVoir`. Les tests vérifient tes cas avec une règle de référence, puis ta fonction." + JS,
       ["Règle : un profil adulte (`age: null`) voit tout ; un profil enfant voit une œuvre si `age >= ageMinimum` de l'œuvre",
        "Les âges minimums possibles : 0, 10, 12, 16, 18 ; autre valeur → erreur `Âge minimum inconnu`",
        "Un âge de profil négatif ou supérieur à 17 → erreur `Âge de profil invalide` (au-delà, c'est un profil adulte)",
        "`cas` : au moins 6 cas `{ age, ageMinimum, attendu }` (avec `attendu` un booléen), dont **pile au seuil** et **juste en dessous**",
        "Écris `peutVoir(age, ageMinimum)`"],
       [F("parental.ts", "ts", r"""
type Cas = { age: number | null; ageMinimum: number; attendu: boolean };

export const cas: Cas[] = [
  { age: null, ageMinimum: 18, attendu: true },   // adulte : tout
  // à toi
];

export function peutVoir(age: number | null, ageMinimum: number): boolean {
  return true;
}
""")],
       ["Pile au seuil : un enfant de 12 ans et un film « 12 ».", "Commence par les erreurs (`throw`), puis le cas adulte, puis la comparaison.",
        "`[0, 10, 12, 16, 18].includes(ageMinimum)`"],
       [F("parental.ts", "ts", r"""
type Cas = { age: number | null; ageMinimum: number; attendu: boolean };

export const cas: Cas[] = [
  { age: null, ageMinimum: 18, attendu: true },   // adulte : tout
  { age: 12, ageMinimum: 12, attendu: true },     // pile au seuil
  { age: 11, ageMinimum: 12, attendu: false },    // juste en dessous
  { age: 7, ageMinimum: 0, attendu: true },       // tous publics
  { age: 15, ageMinimum: 16, attendu: false },
  { age: 16, ageMinimum: 16, attendu: true },
  { age: 17, ageMinimum: 18, attendu: false },
];

export function peutVoir(age: number | null, ageMinimum: number): boolean {
  if (![0, 10, 12, 16, 18].includes(ageMinimum)) throw new Error('Âge minimum inconnu');
  if (age === null) return true;
  if (age < 0 || age > 17) throw new Error('Âge de profil invalide');
  return age >= ageMinimum;
}
""")],
       ["Les cas sont justes et couvrent le seuil", "La fonction respecte la règle et refuse les valeurs impossibles"],
       run=RUN("js", entry="parental.ts", tests=r"""
const { cas, peutVoir } = require('./parental');
const ref = (a, m) => (a === null ? true : a >= m);
assert(Array.isArray(cas) && cas.length >= 6, 'Au moins 6 cas', 'tu en as ' + (Array.isArray(cas) ? cas.length : 0));
for (const c of cas) assert.equal(c.attendu, ref(c.age, c.ageMinimum), `Cas âge ${c.age} / œuvre ${c.ageMinimum} : attendu ${ref(c.age, c.ageMinimum)}`);
assert(cas.some((c) => c.age !== null && c.age === c.ageMinimum && c.ageMinimum > 0), 'Un cas pile au seuil (ex. 12 ans et film 12)');
assert(cas.some((c) => c.age !== null && c.age === c.ageMinimum - 1), 'Un cas juste en dessous du seuil (ex. 11 ans et film 12)');
const grille = [[null, 18, true], [null, 0, true], [12, 12, true], [11, 12, false], [0, 0, true], [9, 10, false], [10, 10, true], [17, 18, false], [17, 16, true]];
for (const [a, m, r] of grille) assert.equal(peutVoir(a, m), r, `peutVoir(${a}, ${m}) → ${r}`);
const err = (fn) => { try { fn(); return ''; } catch (e) { return e.message; } };
assert.equal(err(() => peutVoir(10, 13)), 'Âge minimum inconnu', 'Âge minimum 13 : erreur « Âge minimum inconnu »');
assert.equal(err(() => peutVoir(-1, 0)), 'Âge de profil invalide', 'Âge -1 : erreur');
assert.equal(err(() => peutVoir(18, 0)), 'Âge de profil invalide', 'Âge 18 pour un profil enfant : erreur (c\'est un adulte)');
""")),
    TD(3, "L'état d'une vidéo : non commencée, en cours, terminée",
       "Code la règle de la reprise de lecture. Elle servira à la fois au lecteur (repartir au bon endroit) et à la rangée « Continuer à regarder ». Écris d'abord les étapes en commentaires." + JS,
       ["`etatVisionnage(position, duree)` (en secondes) renvoie `{ etat, reprendreA }`",
        "`etat` : `'non-commence'` si position < 60 ; `'termine'` si position ≥ 95 % de la durée ; sinon `'en-cours'`",
        "`reprendreA` : la position si `en-cours`, sinon 0 (on repart du début, ou on propose de revoir depuis le début)",
        "Durée ≤ 0 → erreur `Durée invalide` ; position négative → erreur `Position invalide` ; position > durée → ramenée à la durée",
        "Étapes en commentaires numérotés (`// 1.`, `// 2.`…) avant le code"],
       [F("reprise.ts", "ts", r"""
type Etat = 'non-commence' | 'en-cours' | 'termine';

export function etatVisionnage(position: number, duree: number): { etat: Etat; reprendreA: number } {
  // 1. ...
  return { etat: 'non-commence', reprendreA: 0 };
}
""")],
       ["Ordre : refuser l'impossible, ramener la position, puis décider l'état.", "`Math.min(position, duree)`",
        "Pour une vidéo très courte (moins d'une minute), qu'est-ce qui l'emporte, la règle des 60 s ou celle des 95 % ? Teste les deux ordres."],
       [F("reprise.ts", "ts", r"""
type Etat = 'non-commence' | 'en-cours' | 'termine';

export function etatVisionnage(position: number, duree: number): { etat: Etat; reprendreA: number } {
  // 1. refuser les valeurs impossibles
  if (!(duree > 0)) throw new Error('Durée invalide');
  if (position < 0) throw new Error('Position invalide');
  // 2. une position au-delà de la fin est ramenée à la fin
  const p = Math.min(position, duree);
  // 3. 95 % ou plus : terminée (passe avant la règle des 60 s, pour les vidéos très courtes)
  if (p >= duree * 0.95) return { etat: 'termine', reprendreA: 0 };
  // 4. moins d'une minute : pas encore commencée
  if (p < 60) return { etat: 'non-commence', reprendreA: 0 };
  // 5. sinon : en cours, on reprend à la position
  return { etat: 'en-cours', reprendreA: p };
}
""")],
       ["Les seuils (60 s, 95 %) sont justes des deux côtés", "Les valeurs impossibles sont refusées"],
       run=RUN("js", entry="reprise.ts", tests=r"""
const { etatVisionnage: f } = require('./reprise');
const src = source('reprise.ts');
assert(/\/\/\s*1\./.test(src) && /\/\/\s*3\./.test(src), 'Les étapes sont écrites en commentaires numérotés (au moins // 1. à // 3.)');
const d = 888; // Sintel : 14 min 48 s
const cas = [[0, 'non-commence', 0], [59, 'non-commence', 0], [60, 'en-cours', 60], [360, 'en-cours', 360], [Math.floor(d * 0.95) - 1, 'en-cours', Math.floor(d * 0.95) - 1], [Math.ceil(d * 0.95), 'termine', 0], [d, 'termine', 0], [5000, 'termine', 0]];
for (const [p, e, r] of cas) { const x = f(p, d); assert(x && x.etat === e && x.reprendreA === r, `Position ${p} s sur ${d} s → ${e}, reprendre à ${r}`, JSON.stringify(x)); }
const court = f(45, 47);
assert(court.etat === 'termine', 'Vidéo de 47 s regardée jusqu\'à 45 s : terminée (les 95 % passent avant la règle des 60 s)', JSON.stringify(court));
const err = (fn) => { try { fn(); return ''; } catch (e) { return e.message; } };
assert.equal(err(() => f(10, 0)), 'Durée invalide', 'Durée 0 : erreur');
assert.equal(err(() => f(-3, 100)), 'Position invalide', 'Position négative : erreur');
""")),
  ])

# =========================================================================== 2. Modèle de données
FILM_ENUM = r"""
<?php
declare(strict_types=1);

use Doctrine\ORM\Mapping as ORM;

enum Genre: string
{
    case Action = 'action';
    case Animation = 'animation';
    case Comedie = 'comedie';
    case Documentaire = 'documentaire';
    case Drame = 'drame';
    case ScienceFiction = 'sf';

    public function libelle(): string
    {
        return match ($this) {
            Genre::Action => 'Action',
            Genre::Animation => 'Animation',
            Genre::Comedie => 'Comédie',
            Genre::Documentaire => 'Documentaire',
            Genre::Drame => 'Drame',
            Genre::ScienceFiction => 'Science-fiction',
        };
    }
}
"""

modele = FM("fil-modele", "Le modèle de données", 40,
  "Écrire les entités Doctrine de Bobine : un Film avec son genre (enum) et ses règles, une Série et ses épisodes (relation qui lui appartient), un Compte, ses profils et son forfait (règle du nombre de profils).",
  "La base de données est la fondation du projet : une relation mal choisie (cascade, côté propriétaire, orphelins) ou une règle oubliée (deux épisodes S01E02, un 6e profil en Essentiel) se paie partout ensuite, dans l'API comme dans l'écran.",
  ["Lister les **entités** à partir du cahier des charges : Film, Série, Épisode, Compte, Profil", "Choisir les **types** : enum pour le genre et le forfait, entiers pour les durées et les âges",
   "Choisir les **relations** : une série possède ses épisodes (cascade + orphelins) ; un profil appartient à un compte", "Placer les **règles** dans les entités : âge minimum valide, pas de doublon d'épisode, nombre de profils selon le forfait"],
  ["Un enum PHP (`enum Genre: string`) garantit qu'on ne stocke que des genres connus ; Doctrine enregistre sa valeur (`'animation'`).",
   "Une durée se stocke en entier (minutes ou secondes), jamais en texte « 1 h 32 » : le format, c'est l'affichage.",
   "Une série **possède** ses épisodes : `cascade: ['persist']` + `orphanRemoval: true`. Un épisode retiré de la série est supprimé.",
   "Le côté propriétaire d'une relation est le `ManyToOne` (la colonne `serie_id` est dans la table `episode`).",
   "Les règles qui protègent la cohérence (pas deux S01E02, pas trop de profils) vivent dans l'entité qui possède la collection, pas dans le contrôleur."],
  ["Stocker le genre en texte libre (« Animation », « animation », « anim »).", "Oublier `orphanRemoval` : l'épisode retiré reste en base, rattaché à rien.", "Vérifier le nombre de profils dans le contrôleur : un autre chemin de code l'oubliera."],
  [Q("Pourquoi un `enum Genre: string` plutôt qu'une colonne texte libre ?",
     ["C'est plus rapide en SQL", "On ne peut stocker que les genres prévus, et le code ne compare plus des chaînes à la main", "Doctrine ne sait pas stocker du texte", "Pour la traduction"], 1,
     "L'enum limite les valeurs possibles dès PHP : impossible d'écrire « anim » par erreur."),
   Q("On retire l'épisode 3 de la collection d'une série (avec `orphanRemoval: true`). Au `flush()` :",
     ["rien ne se passe", "l'épisode est supprimé (DELETE)", "la série est supprimée", "une erreur"], 1,
     "Un épisode sans série n'a pas de sens : orphanRemoval le supprime."),
   Q("Où vérifier qu'un compte Essentiel n'a pas plus de 2 profils ?",
     ["Dans le contrôleur", "Dans le composant React", "Dans `Compte::ajouterProfil()`", "Dans la migration"], 2,
     "L'entité qui possède la collection protège sa règle : tous les chemins de code passent par elle.")],
  prereq=[
    P("Entité", "Une classe PHP enregistrée en base par Doctrine grâce aux attributs `#[ORM\\Entity]`, `#[ORM\\Column]`… (parcours Doctrine)."),
    P("Enum", "Un type PHP qui n'accepte qu'une liste fermée de valeurs : `enum Genre: string { case Animation = 'animation'; ... }`."),
    P("ManyToOne / OneToMany", "Les deux côtés d'une relation : plusieurs épisodes → une série ; une série → plusieurs épisodes."),
    P("Cascade persist", "Persister la série persiste aussi ses nouveaux épisodes."),
    P("orphanRemoval", "Un élément retiré de la collection est supprimé de la base au `flush()`."),
  ],
  diagram=D(
    nodes=[
      N("film", 0, 0, "Film", "titre · annee · duree\ngenre (enum) · ageMinimum", kind="db"),
      N("serie", 0, 1, "Serie", "titre · genre\nageMinimum", kind="db"),
      N("ep", 1, 1, "Episode", "saison · numero\ntitre · duree", kind="db"),
      N("compte", 0, 2, "Compte", "email · forfait (enum)", kind="db"),
      N("prof", 1, 2, "Profil", "nom · age (null = adulte)", kind="db"),
      N("vis", 2, 1, "Visionnage", "tranche 3", kind="db", color="muted"),
    ],
    edges=[E("serie", "ep", "1 → n · cascade\n+ orphelins"), E("compte", "prof", "1 → n · max selon\nforfait"), E("prof", "vis", dashed=True), E("ep", "vis", dashed=True)],
    caption="Les entités de Bobine. Les flèches pleines sont des relations qui possèdent leurs éléments ; Visionnage arrivera avec la tranche 3."),
  lessons=[
    L("Des entités qui disent non", r"""
Une entité n'est pas un simple sac de données : elle **refuse** ce qui n'a pas de sens. C'est le premier endroit où vivent les règles de Bobine.

```php:src/Entity/Film.php
#[ORM\Entity]
class Film
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    public function __construct(
        #[ORM\Column] private string $titre,
        #[ORM\Column] private int $annee,
        #[ORM\Column] private int $dureeMinutes,
        #[ORM\Column(enumType: Genre::class)] private Genre $genre,
        #[ORM\Column] private int $ageMinimum = 0,
    ) {
        if ($dureeMinutes <= 0) throw new \InvalidArgumentException('Durée invalide');
        if (!in_array($ageMinimum, [0, 10, 12, 16, 18], true)) throw new \InvalidArgumentException('Âge minimum inconnu');
    }
}
```

- Le **genre** est un `enum` : on ne peut pas écrire `'anim'` par erreur, et Doctrine stocke la valeur (`'animation'`).
- La **durée** est un entier : « 1 h 32 », c'est de l'affichage (le DTO de l'API s'en chargera).
- Les **contrôles** sont dans le constructeur : un Film invalide ne peut pas exister.
"""),
    L("Une série possède ses épisodes", r"""
Un épisode n'existe pas sans sa série : la série **possède** la collection.

```php:src/Entity/Serie.php
#[ORM\OneToMany(targetEntity: Episode::class, mappedBy: 'serie', cascade: ['persist'], orphanRemoval: true)]
private Collection $episodes;

public function ajouterEpisode(int $saison, int $numero, string $titre, int $duree): Episode
{
    foreach ($this->episodes as $e) {
        if ($e->getSaison() === $saison && $e->getNumero() === $numero) {
            throw new \DomainException(sprintf('Épisode S%02dE%02d déjà présent', $saison, $numero));
        }
    }
    $ep = new Episode($this, $saison, $numero, $titre, $duree);
    $this->episodes->add($ep);
    return $ep;
}
```

- **cascade persist** : `persist($serie)` suffit, les nouveaux épisodes suivent.
- **orphanRemoval** : `retirerEpisode()` + `flush()` → `DELETE` de l'épisode.
- Le **côté propriétaire** est `Episode::$serie` (`ManyToOne`, non nullable) : c'est lui qui remplit la colonne `serie_id`.
- La règle « pas deux S01E02 » est dans la série, seule à voir toute la collection. `%02d` écrit 1 sous la forme `01`.
"""),
    L("Comptes, profils et forfaits", r"""
Le forfait est un enum **qui porte sa règle** :

```php:src/Entity/Forfait.php
enum Forfait: string
{
    case Essentiel = 'essentiel';
    case Standard = 'standard';
    case Premium = 'premium';

    public function maxProfils(): int
    {
        return match ($this) { Forfait::Essentiel => 2, Forfait::Standard => 4, Forfait::Premium => 5 };
    }
}
```

Et le compte s'en sert pour dire non :

```php
public function ajouterProfil(string $nom, ?int $age = null): Profil
{
    if (count($this->profils) >= $this->forfait->maxProfils()) {
        throw new \DomainException('Ton forfait permet ' . $this->forfait->maxProfils() . ' profils');
    }
    // nom unique dans le compte, sans tenir compte des majuscules…
}
```

Un `match` sans `default` sur un enum est **exhaustif** : si on ajoute un 4e forfait demain, PHP lèvera une erreur tant que `maxProfils()` ne le traite pas. C'est le compilateur qui te rappelle la règle.
"""),
  ],
  recap=["Les entités refusent l'impossible dès le constructeur.", "Genre et forfait sont des enums ; les durées et les âges sont des entiers.",
         "Série → épisodes : cascade persist + orphanRemoval ; le ManyToOne est le côté propriétaire.",
         "La règle d'une collection (pas de doublon, maximum de profils) vit dans l'entité qui la possède.",
         "Un enum peut porter sa règle (`maxProfils()`) ; un `match` exhaustif protège les évolutions."],
  example=[F("src/Entity/Genre.php", "php", FILM_ENUM), F("src/Entity/Film.php", "php", r"""
<?php
declare(strict_types=1);

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Film
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    public function __construct(
        #[ORM\Column] private string $titre,
        #[ORM\Column] private int $annee,
        #[ORM\Column] private int $dureeMinutes,
        #[ORM\Column(enumType: Genre::class)] private Genre $genre,
        #[ORM\Column] private int $ageMinimum = 0,
        #[ORM\Column(type: 'text')] private string $synopsis = '',
    ) {
        if (trim($titre) === '') throw new \InvalidArgumentException('Titre obligatoire');
        if ($dureeMinutes <= 0) throw new \InvalidArgumentException('Durée invalide');
        if (!in_array($ageMinimum, [0, 10, 12, 16, 18], true)) throw new \InvalidArgumentException('Âge minimum inconnu');
    }

    public function getId(): ?int { return $this->id; }
    public function getTitre(): string { return $this->titre; }
    public function getGenre(): Genre { return $this->genre; }
    public function getAgeMinimum(): int { return $this->ageMinimum; }
}

$em = new Doctrine\ORM\FakeEntityManager();
$em->persist(new Film('Sintel', 2010, 15, Genre::Animation, 12, 'Une jeune femme cherche son dragon.'));
$em->flush();
""")],
  notes=["`enumType: Genre::class` : Doctrine stocke `'animation'` et te rend un `Genre::Animation`.",
         "Les contrôles du constructeur rendent un Film invalide impossible à créer.",
         "Exécute l'exemple : le SQL affiché montre la valeur de l'enum."],
  tds=[
    TD(1, "L'entité Film",
       "Écris l'entité `Film` de Bobine (l'enum `Genre` est fourni). Elle doit refuser les valeurs impossibles et s'enregistrer avec Doctrine." + DSIM,
       ["`Film` : `id` généré ; `titre`, `annee`, `dureeMinutes`, `genre` (enum, `enumType`), `ageMinimum` (défaut 0), `synopsis` (défaut `''`)",
        "Refuser : titre vide (même avec des espaces) → `Titre obligatoire` ; durée ≤ 0 → `Durée invalide` ; âge minimum hors de 0, 10, 12, 16, 18 → `Âge minimum inconnu` (toutes en `InvalidArgumentException`)",
        "Une année avant 1888 ou après l'année prochaine → `Année invalide`",
        "Getters : `getId()`, `getTitre()`, `getGenre()`, `getDureeMinutes()`, `getAgeMinimum()`"],
       [F("Genre.php", "php", FILM_ENUM), F("Film.php", "php", r"""
<?php
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Film
{
    // à toi
}

$em = new Doctrine\ORM\FakeEntityManager();
$em->persist(new Film('Big Buck Bunny', 2008, 10, Genre::Animation));
$em->flush();
""")],
       ["`#[ORM\\Column(enumType: Genre::class)] private Genre $genre`",
        "L'année prochaine : `(int) date('Y') + 1`. 1888 : le plus ancien film connu.",
        "`trim($titre) === ''` attrape les titres faits seulement d'espaces."],
       [F("Film.php", "php", r"""
<?php
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Film
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    public function __construct(
        #[ORM\Column] private string $titre,
        #[ORM\Column] private int $annee,
        #[ORM\Column] private int $dureeMinutes,
        #[ORM\Column(enumType: Genre::class)] private Genre $genre,
        #[ORM\Column] private int $ageMinimum = 0,
        #[ORM\Column(type: 'text')] private string $synopsis = '',
    ) {
        if (trim($titre) === '') throw new \InvalidArgumentException('Titre obligatoire');
        if ($annee < 1888 || $annee > (int) date('Y') + 1) throw new \InvalidArgumentException('Année invalide');
        if ($dureeMinutes <= 0) throw new \InvalidArgumentException('Durée invalide');
        if (!in_array($ageMinimum, [0, 10, 12, 16, 18], true)) throw new \InvalidArgumentException('Âge minimum inconnu');
    }

    public function getId(): ?int { return $this->id; }
    public function getTitre(): string { return $this->titre; }
    public function getGenre(): Genre { return $this->genre; }
    public function getDureeMinutes(): int { return $this->dureeMinutes; }
    public function getAgeMinimum(): int { return $this->ageMinimum; }
}

$em = new Doctrine\ORM\FakeEntityManager();
$em->persist(new Film('Big Buck Bunny', 2008, 10, Genre::Animation));
$em->flush();
""")],
       ["Un film valide s'enregistre (INSERT avec le genre en texte)", "Les valeurs impossibles sont refusées"],
       run=DRUN(r"""
$em2 = new Doctrine\ORM\FakeEntityManager(); $em2->echo = false;
$f = new Film('Sintel', 2010, 15, Genre::Animation, 12);
$em2->persist($f); $em2->flush();
check('INSERT INTO film', $em2->count('INSERT INTO film') === 1);
check("Le genre est stocké en texte : 'animation'", (bool) array_filter($em2->log, fn($q) => str_contains($q, "'animation'")), implode(' | ', $em2->log));
check('id généré (1)', $f->getId() === 1);
check('getGenre() renvoie l\'enum', $f->getGenre() === Genre::Animation);
check('ageMinimum par défaut : 0', (new Film('Spring', 2019, 8, Genre::Animation))->getAgeMinimum() === 0);
$msg = function (callable $fn) { try { $fn(); return ''; } catch (InvalidArgumentException $e) { return $e->getMessage(); } catch (Throwable $e) { return get_class($e); } };
check('Titre « ␣␣ » → Titre obligatoire', $msg(fn() => new Film('  ', 2010, 15, Genre::Drame)) === 'Titre obligatoire');
check('Durée 0 → Durée invalide', $msg(fn() => new Film('X', 2010, 0, Genre::Drame)) === 'Durée invalide');
check('Âge 13 → Âge minimum inconnu', $msg(fn() => new Film('X', 2010, 10, Genre::Drame, 13)) === 'Âge minimum inconnu');
check('Âge 18 accepté', $msg(fn() => new Film('X', 2010, 10, Genre::Drame, 18)) === '');
check('Année 1850 → Année invalide', $msg(fn() => new Film('X', 1850, 10, Genre::Drame)) === 'Année invalide');
check('Année 1888 acceptée (le seuil)', $msg(fn() => new Film('X', 1888, 2, Genre::Documentaire)) === '');
check('Année dans 5 ans → Année invalide', $msg(fn() => new Film('X', (int) date('Y') + 5, 10, Genre::Drame)) === 'Année invalide');
""")),
    TD(2, "Une série et ses épisodes",
       "Une série possède ses épisodes : persister la série les enregistre, en retirer un le supprime, et deux épisodes ne peuvent pas avoir le même numéro dans la même saison." + DSIM,
       ["`Episode` : `id` généré ; `ManyToOne` vers `Serie` (`inversedBy: 'episodes'`, non nullable) ; `saison`, `numero`, `titre`, `dureeMinutes` ; getters `getSaison()`, `getNumero()`",
        "`Serie` : `id`, `titre` ; `OneToMany` `episodes` avec `cascade: ['persist']` et `orphanRemoval: true`",
        "`Serie::ajouterEpisode(int $saison, int $numero, string $titre, int $duree): Episode` ; un doublon lève `DomainException` « Épisode S01E02 déjà présent » (deux chiffres)",
        "`retirerEpisode(int $saison, int $numero)`, `nombreEpisodes()`, `nombreSaisons()` (saisons différentes)"],
       [F("Episode.php", "php", r"""
<?php
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Episode
{
    // à toi
}
"""), F("Serie.php", "php", r"""
<?php
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Serie
{
    // à toi
}

$em = new Doctrine\ORM\FakeEntityManager();
$s = new Serie('Les Lamas');
$s->ajouterEpisode(1, 1, 'Le pont', 3);
$s->ajouterEpisode(1, 2, 'La neige', 3);
$em->persist($s);
$em->flush();
""")],
       ["`sprintf('Épisode S%02dE%02d déjà présent', $saison, $numero)`",
        "`nombreSaisons()` : `count(array_unique(array_map(fn($e) => $e->getSaison(), $this->episodes->toArray())))`",
        "Le constructeur de `Serie` crée la collection : `$this->episodes = new ArrayCollection();`"],
       [F("Episode.php", "php", r"""
<?php
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Episode
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    public function __construct(
        #[ORM\ManyToOne(inversedBy: 'episodes')]
        #[ORM\JoinColumn(nullable: false)]
        private Serie $serie,
        #[ORM\Column] private int $saison,
        #[ORM\Column] private int $numero,
        #[ORM\Column] private string $titre,
        #[ORM\Column] private int $dureeMinutes,
    ) {}

    public function getSaison(): int { return $this->saison; }
    public function getNumero(): int { return $this->numero; }
    public function getTitre(): string { return $this->titre; }
}
"""), F("Serie.php", "php", r"""
<?php
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Serie
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    /** @var Collection<int, Episode> */
    #[ORM\OneToMany(targetEntity: Episode::class, mappedBy: 'serie', cascade: ['persist'], orphanRemoval: true)]
    private Collection $episodes;

    public function __construct(#[ORM\Column] private string $titre)
    {
        $this->episodes = new ArrayCollection();
    }

    public function ajouterEpisode(int $saison, int $numero, string $titre, int $duree): Episode
    {
        if ($this->trouver($saison, $numero)) {
            throw new \DomainException(sprintf('Épisode S%02dE%02d déjà présent', $saison, $numero));
        }
        $ep = new Episode($this, $saison, $numero, $titre, $duree);
        $this->episodes->add($ep);
        return $ep;
    }

    public function retirerEpisode(int $saison, int $numero): void
    {
        $ep = $this->trouver($saison, $numero);
        if ($ep) $this->episodes->removeElement($ep);
    }

    public function nombreEpisodes(): int { return count($this->episodes); }

    public function nombreSaisons(): int
    {
        return count(array_unique(array_map(fn(Episode $e) => $e->getSaison(), $this->episodes->toArray())));
    }

    private function trouver(int $saison, int $numero): ?Episode
    {
        foreach ($this->episodes as $e) {
            if ($e->getSaison() === $saison && $e->getNumero() === $numero) return $e;
        }
        return null;
    }
}

$em = new Doctrine\ORM\FakeEntityManager();
$s = new Serie('Les Lamas');
$s->ajouterEpisode(1, 1, 'Le pont', 3);
$s->ajouterEpisode(1, 2, 'La neige', 3);
$em->persist($s);
$em->flush();
""")],
       ["persist(série) enregistre la série et ses épisodes", "Un épisode retiré est supprimé ; un doublon est refusé"],
       run=DRUN(r"""
$em2 = new Doctrine\ORM\FakeEntityManager(); $em2->echo = false;
$s2 = new Serie('Caminandes');
$s2->ajouterEpisode(1, 1, 'Llama Drama', 2); $s2->ajouterEpisode(1, 2, 'Gran Dillama', 3); $s2->ajouterEpisode(2, 1, 'Llamigos', 3);
$em2->persist($s2); $em2->flush();
check('1 INSERT serie + 3 INSERT episode (cascade persist)', $em2->count('INSERT INTO serie') === 1 && $em2->count('INSERT INTO episode') === 3, implode(' | ', $em2->log));
check('Les épisodes ont la colonne serie_id remplie', (bool) array_filter($em2->log, fn($q) => str_contains($q, 'INSERT INTO episode') && str_contains($q, 'serie_id')));
check('nombreEpisodes() = 3, nombreSaisons() = 2', $s2->nombreEpisodes() === 3 && $s2->nombreSaisons() === 2);
$m = ''; try { $s2->ajouterEpisode(1, 2, 'Doublon', 3); } catch (DomainException $e) { $m = $e->getMessage(); }
check('Doublon S01E02 → « Épisode S01E02 déjà présent »', $m === 'Épisode S01E02 déjà présent', $m);
$em2->clearLog();
$s2->retirerEpisode(1, 1); $em2->flush();
check('Retirer S01E01 : DELETE de l\'épisode (orphanRemoval)', $em2->count('DELETE FROM episode') === 1, implode(' | ', $em2->log));
check('Il reste 2 épisodes', $s2->nombreEpisodes() === 2);
$a = (new ReflectionProperty(Serie::class, 'episodes'))->getAttributes('Doctrine\ORM\Mapping\OneToMany')[0]->getArguments();
check('OneToMany avec cascade persist et orphanRemoval', in_array('persist', $a['cascade'] ?? [], true) && ($a['orphanRemoval'] ?? false) === true);
""")),
    TD(3, "Compte, profils et forfait",
       "Un compte Bobine a un forfait et des profils. Le forfait limite le nombre de profils ; les noms sont uniques dans le compte ; et on ne peut pas passer à un forfait plus petit que le nombre de profils actuels." + DSIM,
       ["`enum Forfait: string` (essentiel, standard, premium) avec `maxProfils()` (2, 4, 5) et `libelle()` (« Essentiel »…)",
        "`Profil` : `id`, `ManyToOne` vers `Compte` (non nullable), `nom`, `age` (`?int`, `null` = adulte), `estEnfant()`",
        "`Compte` : `id`, `email`, `forfait` (enum), `OneToMany` `profils` (cascade persist, orphanRemoval) ; le constructeur crée un premier profil adulte avec le nom donné",
        "`ajouterProfil(string $nom, ?int $age = null)` : `DomainException` « Ton forfait Essentiel permet 2 profils » si plein ; « Le profil Léo existe déjà » si le nom existe (sans tenir compte des majuscules ni des espaces autour)",
        "`changerForfait(Forfait $f)` : refusé avec « Supprime d'abord des profils (4 profils, Essentiel en permet 2) » si trop de profils"],
       [F("Forfait.php", "php", r"""
<?php
enum Forfait: string
{
    // à toi
}
"""), F("Profil.php", "php", r"""
<?php
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Profil
{
    // à toi
}
"""), F("Compte.php", "php", r"""
<?php
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Compte
{
    // à toi
}

$em = new Doctrine\ORM\FakeEntityManager();
$c = new Compte('ana@exemple.fr', Forfait::Essentiel, 'Ana');
$c->ajouterProfil('Léo', 8);
$em->persist($c);
$em->flush();
""")],
       ["Comparer les noms : `mb_strtolower(trim($a)) === mb_strtolower(trim($b))`.",
        "Dans le constructeur de `Compte`, crée la collection AVANT d'appeler `ajouterProfil($nomPremierProfil)`.",
        "Le message du forfait utilise `libelle()` et `maxProfils()` : `'Ton forfait ' . $f->libelle() . ' permet ' . $f->maxProfils() . ' profils'`."],
       [F("Forfait.php", "php", r"""
<?php
enum Forfait: string
{
    case Essentiel = 'essentiel';
    case Standard = 'standard';
    case Premium = 'premium';

    public function maxProfils(): int
    {
        return match ($this) { Forfait::Essentiel => 2, Forfait::Standard => 4, Forfait::Premium => 5 };
    }

    public function libelle(): string
    {
        return match ($this) { Forfait::Essentiel => 'Essentiel', Forfait::Standard => 'Standard', Forfait::Premium => 'Premium' };
    }
}
"""), F("Profil.php", "php", r"""
<?php
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Profil
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    public function __construct(
        #[ORM\ManyToOne(inversedBy: 'profils')]
        #[ORM\JoinColumn(nullable: false)]
        private Compte $compte,
        #[ORM\Column] private string $nom,
        #[ORM\Column(nullable: true)] private ?int $age = null,
    ) {}

    public function getNom(): string { return $this->nom; }
    public function getAge(): ?int { return $this->age; }
    public function estEnfant(): bool { return $this->age !== null; }
}
"""), F("Compte.php", "php", r"""
<?php
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class Compte
{
    #[ORM\Id, ORM\GeneratedValue, ORM\Column]
    private ?int $id = null;

    /** @var Collection<int, Profil> */
    #[ORM\OneToMany(targetEntity: Profil::class, mappedBy: 'compte', cascade: ['persist'], orphanRemoval: true)]
    private Collection $profils;

    public function __construct(
        #[ORM\Column] private string $email,
        #[ORM\Column(enumType: Forfait::class)] private Forfait $forfait,
        string $nomPremierProfil,
    ) {
        $this->profils = new ArrayCollection();
        $this->ajouterProfil($nomPremierProfil);
    }

    public function ajouterProfil(string $nom, ?int $age = null): Profil
    {
        if (count($this->profils) >= $this->forfait->maxProfils()) {
            throw new \DomainException('Ton forfait ' . $this->forfait->libelle() . ' permet ' . $this->forfait->maxProfils() . ' profils');
        }
        foreach ($this->profils as $p) {
            if (mb_strtolower(trim($p->getNom())) === mb_strtolower(trim($nom))) {
                throw new \DomainException('Le profil ' . trim($nom) . ' existe déjà');
            }
        }
        $profil = new Profil($this, trim($nom), $age);
        $this->profils->add($profil);
        return $profil;
    }

    public function changerForfait(Forfait $f): void
    {
        $n = count($this->profils);
        if ($n > $f->maxProfils()) {
            throw new \DomainException("Supprime d'abord des profils ($n profils, " . $f->libelle() . ' en permet ' . $f->maxProfils() . ')');
        }
        $this->forfait = $f;
    }

    public function nombreProfils(): int { return count($this->profils); }
    public function getForfait(): Forfait { return $this->forfait; }
}

$em = new Doctrine\ORM\FakeEntityManager();
$c = new Compte('ana@exemple.fr', Forfait::Essentiel, 'Ana');
$c->ajouterProfil('Léo', 8);
$em->persist($c);
$em->flush();
""")],
       ["Le forfait limite les profils", "Les noms sont uniques ; on ne descend pas sous le nombre de profils"],
       run=DRUN(r"""
check('maxProfils : 2 / 4 / 5', Forfait::Essentiel->maxProfils() === 2 && Forfait::Standard->maxProfils() === 4 && Forfait::Premium->maxProfils() === 5);
$em2 = new Doctrine\ORM\FakeEntityManager(); $em2->echo = false;
$c2 = new Compte('ana@exemple.fr', Forfait::Essentiel, 'Ana');
check('Le constructeur crée un premier profil', $c2->nombreProfils() === 1);
$leo = $c2->ajouterProfil('Léo', 8);
check('Léo est un profil enfant', $leo->estEnfant());
$em2->persist($c2); $em2->flush();
check('1 INSERT compte + 2 INSERT profil', $em2->count('INSERT INTO compte') === 1 && $em2->count('INSERT INTO profil') === 2, implode(' | ', $em2->log));
check("Le forfait est stocké : 'essentiel'", (bool) array_filter($em2->log, fn($q) => str_contains($q, "'essentiel'")));
$err = function (callable $fn) { try { $fn(); return ''; } catch (DomainException $e) { return $e->getMessage(); } };
check('3e profil en Essentiel → « Ton forfait Essentiel permet 2 profils »', $err(fn() => $c2->ajouterProfil('Inès', 12)) === 'Ton forfait Essentiel permet 2 profils');
$c3 = new Compte('b@exemple.fr', Forfait::Standard, 'Ana');
check('Nom en double (casse et espaces ignorés) → « Le profil Ana existe déjà »', $err(fn() => $c3->ajouterProfil('  ana ')) === 'Le profil ana existe déjà' || $err(fn() => $c3->ajouterProfil('  ana ')) === 'Le profil Ana existe déjà');
$c3->ajouterProfil('Léo', 8); $c3->ajouterProfil('Inès', 12); $c3->ajouterProfil('Papi');
check('Standard : 4 profils acceptés', $c3->nombreProfils() === 4);
check('Passer en Essentiel avec 4 profils → refusé', $err(fn() => $c3->changerForfait(Forfait::Essentiel)) === "Supprime d'abord des profils (4 profils, Essentiel en permet 2)");
check('Le forfait n\'a pas changé', $c3->getForfait() === Forfait::Standard);
$c3->changerForfait(Forfait::Premium);
check('Passer en Premium : accepté', $c3->getForfait() === Forfait::Premium);
""")),
  ])

# =========================================================================== 3. API catalogue
USES = r"""<?php
declare(strict_types=1);

use Atelier\App;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpKernel\Attribute\MapQueryString;
use Symfony\Component\HttpKernel\Exception\AccessDeniedHttpException;
use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;
use Symfony\Component\Routing\Attribute\Route;
use Symfony\Component\Validator\Constraints as Assert;
"""

CATALOGUE = F("catalogue.php", "php", USES + r"""
// ---- Données fournies (comme si elles venaient de Doctrine) ----

final class Film
{
    public function __construct(
        private int $id, private string $titre, private int $annee, private int $dureeMinutes,
        private string $genre, private int $ageMinimum, private string $synopsis,
        private string $fichierVideo, private \DateTimeImmutable $ajouteLe,
    ) {}
    public function getId(): int { return $this->id; }
    public function getTitre(): string { return $this->titre; }
    public function getAnnee(): int { return $this->annee; }
    public function getDureeMinutes(): int { return $this->dureeMinutes; }
    public function getGenre(): string { return $this->genre; }
    public function getAgeMinimum(): int { return $this->ageMinimum; }
    public function getSynopsis(): string { return $this->synopsis; }
    public function getFichierVideo(): string { return $this->fichierVideo; }   // chemin interne : jamais dans l'API
    public function getAjouteLe(): \DateTimeImmutable { return $this->ajouteLe; }
}

final class FilmRepository
{
    /** @var array<int, Film> */
    private array $films = [];

    public function __construct()
    {
        $d = fn(string $s) => new \DateTimeImmutable($s);
        foreach ([
            [1, 'Big Buck Bunny', 2008, 10, 'animation', 0, 'Un lapin géant se venge de trois rongeurs farceurs.', '2026-09-01'],
            [2, 'Elephants Dream', 2006, 11, 'animation', 10, 'Deux hommes dans une machine étrange et sans fin.', '2026-09-01'],
            [3, 'Sintel', 2010, 15, 'animation', 12, 'Une jeune femme part à la recherche de son dragon.', '2026-09-15'],
            [4, 'Tears of Steel', 2012, 12, 'sf', 12, 'Des scientifiques tentent de sauver le monde à Amsterdam.', '2026-10-01'],
            [5, 'Spring', 2019, 8, 'animation', 0, 'Une bergère et son chien affrontent les esprits de l\'hiver.', '2026-10-05'],
            [6, 'Agent 327', 2017, 4, 'action', 10, 'Un agent secret dans un salon de coiffure piégé.', '2026-10-20'],
            [7, 'Caminandes : Llamigos', 2016, 3, 'comedie', 0, 'Un lama et un pingouin se disputent des baies.', '2026-11-02'],
            [8, 'Charge', 2022, 4, 'action', 16, 'Une chasseuse dans un monde sans énergie.', '2026-11-08'],
            [9, 'Sprite Fright', 2021, 10, 'comedie', 16, 'Des adolescents dérangent les esprits de la forêt.', '2026-11-10'],
            [10, 'La Nuit des projecteurs', 2024, 92, 'drame', 16, 'Une projectionniste refuse de fermer son cinéma.', '2026-11-12'],
        ] as [$id, $t, $a, $m, $g, $age, $syn, $aj]) {
            $this->films[$id] = new Film($id, $t, $a, $m, $g, $age, $syn, "/stockage/videos/$id.mp4", $d($aj));
        }
    }

    /** @return Film[] */
    public function findAll(): array { return array_values($this->films); }
    public function find(int $id): ?Film { return $this->films[$id] ?? null; }
}

final class Profil
{
    public function __construct(private int $id, private string $nom, private ?int $age) {}
    public function getId(): int { return $this->id; }
    public function getNom(): string { return $this->nom; }
    public function getAge(): ?int { return $this->age; }
    public function peutVoir(Film $f): bool { return $this->age === null || $this->age >= $f->getAgeMinimum(); }
}

final class ProfilRepository
{
    public function find(int $id): ?Profil
    {
        return [1 => new Profil(1, 'Ana', null), 2 => new Profil(2, 'Léo', 8), 3 => new Profil(3, 'Inès', 12)][$id] ?? null;
    }
}
""")

DUREE_HINT = "`intdiv($m, 60)` donne les heures, `$m % 60` les minutes ; `sprintf('%d h %02d', $h, $min)` écrit « 1 h 32 »."

api = FM("fil-api", "L'API du catalogue", 40,
  "Écrire l'API que le front de Bobine appellera : la liste du catalogue avec recherche, genre et pagination, la fiche d'un film, le contrôle parental, et la page d'accueil en rangées.",
  "Le front React ne parle qu'à l'API : si elle renvoie des données mal formées (une durée « 92 » au lieu de « 1 h 32 », un chemin de fichier interne, des films interdits aux enfants), chaque écran devra se débrouiller, et un oubli suffit à montrer un film « 16 ans » à Léo.",
  ["Le front appelle `GET /api/films?q=…&genre=…&page=…&profil=…`", "`#[MapQueryString]` transforme l'URL en DTO de filtres **validé** (genre connu, pagination bornée)",
   "Le contrôleur filtre (recherche, genre, **contrôle parental**) puis découpe la page", "Chaque film passe par un **DTO de sortie** : seulement ce que le front doit voir, durée formatée",
   "La réponse : `{ items, total, page, pages }` ; erreurs en 404 / 403 / 422 avec un message"],
  ["Le DTO de filtres a des valeurs par défaut sûres et des bornes (`parPage` ≤ 24) : l'URL vient du client, elle peut contenir n'importe quoi.",
   "Le genre est validé par une liste blanche (`Assert\\Choice`) : jamais de valeur libre dans une requête.",
   "Le DTO de sortie (`FilmCard`) choisit les champs : le chemin interne de la vidéo ne sort jamais.",
   "Le contrôle parental s'applique **côté serveur** : cacher un film dans React ne suffit pas, l'API ne doit pas le renvoyer.",
   "Un film interdit au profil donne **403** sur la fiche ; un film qui n'existe pas donne **404**. Ce ne sont pas les mêmes messages."],
  ["Renvoyer l'entité telle quelle (avec `fichierVideo`, et peut-être des relations circulaires).", "Filtrer les films interdits seulement dans le front.", "Accepter `parPage=100000`."],
  [Q("Pourquoi passer chaque film par `FilmCard::fromEntity()` ?",
     ["Pour aller plus vite", "Pour choisir exactement les champs envoyés (pas le chemin interne) et formater la durée", "Doctrine l'exige", "Pour le cache"], 1,
     "Le DTO de sortie est la frontière : ce qu'il ne contient pas ne peut pas fuiter."),
   Q("Léo (8 ans) demande `GET /api/films?profil=2`. Le film « Charge » (16 ans) doit…",
     ["apparaître, et React le cachera", "ne pas apparaître dans la réponse", "apparaître flouté", "provoquer une erreur 500"], 1,
     "Le serveur applique la règle : le front ne reçoit même pas le film."),
   Q("`GET /api/films/8?profil=2` (Charge, profil de Léo) doit répondre…",
     ["200", "404 Film introuvable", "403 Ce film n'est pas disponible pour ce profil", "422"], 2,
     "Le film existe, mais ce profil n'a pas le droit de le voir : 403.")],
  prereq=[
    P("DTO", "Data Transfer Object : une petite classe qui décrit exactement ce qui entre (filtres, formulaire) ou sort (réponse) de l'API. Parcours DTO."),
    P("`#[MapQueryString]`", "Attribut Symfony qui remplit un DTO à partir des paramètres d'URL (`?q=…&page=2`), les convertit (texte → int) et les valide."),
    P("Pagination", "Découper une longue liste en pages : `page`, `parPage`, `total`, `pages`."),
    P("403 / 404 / 422", "403 : interdit pour toi ; 404 : n'existe pas ; 422 : ta demande est invalide (un filtre mal formé)."),
    P("Liste blanche", "N'accepter que des valeurs connues à l'avance (`Assert\\Choice(['animation', 'action', …])`), plutôt que d'essayer d'interdire les mauvaises."),
  ],
  diagram=D(
    nodes=[
      N("front", 0, 0, "React", "GET /api/films\n?q=&genre=&profil=", color="accent"),
      N("dto", 1, 0, "CatalogueFiltres", "MapQueryString\n+ validation", kind="file"),
      N("ctrl", 2, 0, "Contrôleur", "recherche · genre\n· contrôle parental"),
      N("repo", 3, 0, "Repositories", "films · profils", kind="db", color="muted"),
      N("card", 2, 1, "FilmCard", "fromEntity()\ndurée « 1 h 32 »", kind="file", color="good"),
      N("res", 1, 1, "Réponse", "{ items, total,\npage, pages }", kind="pill", color="good"),
      N("err", 3, 1, "Erreurs", "404 · 403 · 422", kind="note", color="bad"),
    ],
    edges=[E("front", "dto"), E("dto", "ctrl"), E("ctrl", "repo"), E("ctrl", "card", color="good"), E("card", "res", color="good"), E("res", "front", "JSON", color="good"), E("ctrl", "err", dashed=True)],
    lanes=[LANE("Front", 0, 0, "accent"), LANE("API (frontière)", 1, 2, "warn"), LANE("Données", 3, 3, "tc")],
    caption="Ce qui entre est validé (DTO de filtres) ; ce qui sort est choisi (FilmCard). Le contrôle parental est appliqué entre les deux, côté serveur."),
  lessons=[
    L("Le contrat avec le front", r"""
Avant d'écrire le contrôleur, écris ce que le front recevra. C'est le **contrat** :

```http:echanges.http
GET /api/films?genre=animation&page=1&parPage=2
-> 200 {"items": [
     {"id": 1, "titre": "Big Buck Bunny", "annee": 2008, "genre": "animation", "duree": "10 min", "ageMinimum": 0},
     {"id": 2, "titre": "Elephants Dream", "annee": 2006, "genre": "animation", "duree": "11 min", "ageMinimum": 10}
   ], "total": 4, "page": 1, "pages": 2}

GET /api/films?genre=horreur
-> 422 {"violations": [{"propertyPath": "genre", ...}]}

GET /api/films/10
-> 200 {"id": 10, "titre": "La Nuit des projecteurs", "duree": "1 h 32", "synopsis": "...", ...}

GET /api/films/99
-> 404 {"error": "Film introuvable"}
```

Ce contrat se décide **avec** la personne qui fait le front (ici, toi dans le module suivant). La durée arrive déjà formatée : le front n'a rien à calculer.
"""),
    L("Ce qui entre : un DTO de filtres", r"""
Les paramètres d'URL viennent du client : ils peuvent valoir n'importe quoi. Un DTO les reçoit, les convertit et les valide :

```php:src/Dto/CatalogueFiltres.php
final class CatalogueFiltres
{
    public function __construct(
        #[Assert\Length(max: 50)] public readonly ?string $q = null,
        #[Assert\Choice(['action', 'animation', 'comedie', 'documentaire', 'drame', 'sf'])] public readonly ?string $genre = null,
        #[Assert\Positive] public readonly ?int $profil = null,
        #[Assert\Positive] public readonly int $page = 1,
        #[Assert\Range(min: 1, max: 24)] public readonly int $parPage = 12,
    ) {}
}
```

Dans le contrôleur :

```php
#[Route('/api/films', methods: ['GET'])]
public function liste(#[MapQueryString] ?CatalogueFiltres $f, FilmRepository $films): JsonResponse
{
    $f ??= new CatalogueFiltres();   // pas de paramètre du tout : valeurs par défaut
    // …filtrer, puis découper la page
}
```

Un genre inconnu ou `parPage=5000` donne **422** avant même d'entrer dans ton code.
"""),
    L("Ce qui sort : un DTO de sortie, et la règle des enfants", r"""
Chaque film passe par une carte qui choisit les champs et formate la durée :

```php:src/Dto/FilmCard.php
final class FilmCard
{
    public function __construct(
        public readonly int $id, public readonly string $titre, public readonly int $annee,
        public readonly string $genre, public readonly string $duree, public readonly int $ageMinimum,
    ) {}

    public static function fromEntity(Film $f): self
    {
        return new self($f->getId(), $f->getTitre(), $f->getAnnee(), $f->getGenre(), self::duree($f->getDureeMinutes()), $f->getAgeMinimum());
    }

    public static function duree(int $minutes): string
    {
        return $minutes < 60 ? "$minutes min" : sprintf('%d h %02d', intdiv($minutes, 60), $minutes % 60);
    }
}
```

`fichierVideo` n'est pas dans la carte : il ne peut pas sortir par erreur.

Le **contrôle parental** se fait côté serveur, avec la règle écrite au premier module :

```php
if ($f->profil !== null) {
    $profil = $profils->find($f->profil) ?? throw new NotFoundHttpException('Profil introuvable');
    $liste = array_filter($liste, fn(Film $film) => $profil->peutVoir($film));
}
```

Cacher un film seulement dans React ne protège rien : n'importe qui peut appeler l'API directement.
"""),
  ],
  recap=["Le contrat (exemples de requêtes et de réponses) s'écrit avant le code.",
         "Ce qui entre : DTO de filtres validé, valeurs par défaut sûres, bornes, liste blanche.",
         "Ce qui sort : DTO de sortie, durée formatée, pas de champ interne.",
         "Le contrôle parental est appliqué par l'API.",
         "404 : n'existe pas ; 403 : interdit pour ce profil ; 422 : demande invalide."],
  example=[F("src/Controller/CatalogueController.php", "php", USES + r"""
final class CatalogueFiltres
{
    public function __construct(
        #[Assert\Length(max: 50)] public readonly ?string $q = null,
        #[Assert\Choice(['action', 'animation', 'comedie', 'documentaire', 'drame', 'sf'])] public readonly ?string $genre = null,
        #[Assert\Positive] public readonly int $page = 1,
        #[Assert\Range(min: 1, max: 24)] public readonly int $parPage = 12,
    ) {}
}

final class CatalogueController extends AbstractController
{
    #[Route('/api/films', methods: ['GET'])]
    public function liste(#[MapQueryString] ?CatalogueFiltres $f, FilmRepository $films): JsonResponse
    {
        $f ??= new CatalogueFiltres();
        $liste = $films->findAll();
        if ($f->q) $liste = array_filter($liste, fn(Film $x) => str_contains(mb_strtolower($x->getTitre()), mb_strtolower(trim($f->q))));
        if ($f->genre) $liste = array_filter($liste, fn(Film $x) => $x->getGenre() === $f->genre);
        $liste = array_values($liste);
        $page = array_slice($liste, ($f->page - 1) * $f->parPage, $f->parPage);

        return $this->json([
            'items' => array_map(FilmCard::fromEntity(...), $page),
            'total' => count($liste),
            'page' => $f->page,
            'pages' => max(1, (int) ceil(count($liste) / $f->parPage)),
        ]);
    }
}
"""), F("echanges.http", "plaintext", r"""
GET /api/films?q=SINTEL
-> 200 {"items": [{"id": 3, "titre": "Sintel", "annee": 2010, "genre": "animation", "duree": "15 min", "ageMinimum": 12}], "total": 1, "page": 1, "pages": 1}

GET /api/films?genre=animation&parPage=2&page=2
-> 200 {"items": [...2 films...], "total": 4, "page": 2, "pages": 2}

GET /api/films?parPage=500
-> 422 {"title": "Validation Failed", "violations": [{"propertyPath": "parPage", ...}]}
""")],
  notes=["Le contrôleur ne lit jamais `$request->query` : il reçoit un objet validé.",
         "`array_values()` après `array_filter()` : sinon les clés gardent des trous et le JSON devient un objet.",
         "`pages` vaut au moins 1, même quand il n'y a aucun résultat."],
  tds=[
    TD(1, "La liste du catalogue",
       "Écris `GET /api/films` : recherche dans le titre (sans tenir compte des majuscules), filtre par genre, pagination, et une carte `FilmCard` par film avec la durée formatée. Les données (10 films) sont dans `catalogue.php`." + SSIM,
       ["`CatalogueFiltres` : `q` (≤ 50 caractères), `genre` (liste blanche : action, animation, comedie, documentaire, drame, sf), `page` (≥ 1, défaut 1), `parPage` (1 à 24, défaut 12)",
        "`FilmCard` : `id`, `titre`, `annee`, `genre`, `duree`, `ageMinimum` ; `fromEntity(Film $f)` ; durée « 10 min » sous une heure, « 1 h 32 » au-delà",
        "`GET /api/films` → `{ items, total, page, pages }` (`pages` ≥ 1)",
        "Aucun `fichierVideo` ni `synopsis` dans la liste"],
       [CATALOGUE, F("CatalogueController.php", "php", r"""
<?php
final class CatalogueFiltres
{
    // à toi
}

final class FilmCard
{
    // à toi
}

final class CatalogueController extends AbstractController
{
    // à toi : GET /api/films
}

App::request('GET', '/api/films?genre=animation&parPage=2');
App::request('GET', '/api/films?q=nuit');
""")],
       [DUREE_HINT, "Recherche : `str_contains(mb_strtolower($film->getTitre()), mb_strtolower(trim($f->q)))`.",
        "`array_slice($liste, ($f->page - 1) * $f->parPage, $f->parPage)` découpe la page."],
       [F("CatalogueController.php", "php", r"""
<?php
final class CatalogueFiltres
{
    public function __construct(
        #[Assert\Length(max: 50)] public readonly ?string $q = null,
        #[Assert\Choice(['action', 'animation', 'comedie', 'documentaire', 'drame', 'sf'])] public readonly ?string $genre = null,
        #[Assert\Positive] public readonly int $page = 1,
        #[Assert\Range(min: 1, max: 24)] public readonly int $parPage = 12,
    ) {}
}

final class FilmCard
{
    public function __construct(
        public readonly int $id, public readonly string $titre, public readonly int $annee,
        public readonly string $genre, public readonly string $duree, public readonly int $ageMinimum,
    ) {}

    public static function fromEntity(Film $f): self
    {
        return new self($f->getId(), $f->getTitre(), $f->getAnnee(), $f->getGenre(), self::duree($f->getDureeMinutes()), $f->getAgeMinimum());
    }

    public static function duree(int $m): string
    {
        return $m < 60 ? "$m min" : sprintf('%d h %02d', intdiv($m, 60), $m % 60);
    }
}

final class CatalogueController extends AbstractController
{
    #[Route('/api/films', methods: ['GET'])]
    public function liste(#[MapQueryString] ?CatalogueFiltres $f, FilmRepository $films): JsonResponse
    {
        $f ??= new CatalogueFiltres();
        $liste = $films->findAll();
        if ($f->q !== null && trim($f->q) !== '') {
            $liste = array_filter($liste, fn(Film $x) => str_contains(mb_strtolower($x->getTitre()), mb_strtolower(trim($f->q))));
        }
        if ($f->genre !== null) {
            $liste = array_filter($liste, fn(Film $x) => $x->getGenre() === $f->genre);
        }
        $liste = array_values($liste);
        $total = count($liste);

        return $this->json([
            'items' => array_map(FilmCard::fromEntity(...), array_slice($liste, ($f->page - 1) * $f->parPage, $f->parPage)),
            'total' => $total,
            'page' => $f->page,
            'pages' => max(1, (int) ceil($total / $f->parPage)),
        ]);
    }
}

App::request('GET', '/api/films?genre=animation&parPage=2');
App::request('GET', '/api/films?q=nuit');
""")],
       ["La liste filtre, pagine et formate", "Les filtres invalides donnent 422 ; rien d'interne ne sort"],
       run=SRUN(r"""
$all = App::request('GET', '/api/films');
check('Sans filtre : 200, total 10, page 1, pages 1 (12 par page)', $all->status === 200 && ($all->json['total'] ?? 0) === 10 && ($all->json['pages'] ?? 0) === 1, (string) $all);
$it = $all->json['items'][0] ?? [];
check('Une carte a exactement id, titre, annee, genre, duree, ageMinimum', is_array($it) && array_keys($it) == ['id', 'titre', 'annee', 'genre', 'duree', 'ageMinimum'], json_encode(array_keys((array) $it)));
check('Pas de fichierVideo ni de synopsis dans la liste', !str_contains(json_encode($all->json), 'stockage') && !str_contains(json_encode($all->json), 'synopsis'));
$n = App::request('GET', '/api/films?q=NUIT');
check('q=NUIT : La Nuit des projecteurs (casse ignorée)', ($n->json['total'] ?? 0) === 1 && ($n->json['items'][0]['titre'] ?? '') === 'La Nuit des projecteurs');
check('Durée 92 min → « 1 h 32 »', ($n->json['items'][0]['duree'] ?? '') === '1 h 32', $n->json['items'][0]['duree'] ?? '');
check('Durée 10 min → « 10 min »', (array_values(array_filter($all->json['items'], fn($x) => $x['id'] === 1))[0]['duree'] ?? '') === '10 min');
$g = App::request('GET', '/api/films?genre=animation&parPage=2&page=2');
check('genre=animation&parPage=2&page=2 : 2 films, total 4, pages 2', count($g->json['items'] ?? []) === 2 && ($g->json['total'] ?? 0) === 4 && ($g->json['pages'] ?? 0) === 2, (string) $g);
check('genre=horreur → 422', App::request('GET', '/api/films?genre=horreur')->status === 422);
check('parPage=100 → 422', App::request('GET', '/api/films?parPage=100')->status === 422);
check('page=0 → 422', App::request('GET', '/api/films?page=0')->status === 422);
$z = App::request('GET', '/api/films?q=zzz');
check('Aucun résultat : items vide (une liste, pas un objet), total 0, pages 1', ($z->json['items'] ?? null) === [] && ($z->json['total'] ?? -1) === 0 && ($z->json['pages'] ?? 0) === 1, (string) $z);
""")),
    TD(2, "La fiche d'un film et le contrôle parental",
       "Ajoute la fiche `GET /api/films/{id}` et le paramètre `profil` : avec un profil enfant, la liste ne contient que les films autorisés, et la fiche d'un film interdit répond **403**." + SSIM,
       ["Garde ta liste du TD 1 et ajoute `profil` (entier ≥ 1, facultatif) à `CatalogueFiltres`",
        "Liste avec `profil` : seulement les films que `Profil::peutVoir()` autorise ; profil inconnu → 404 « Profil introuvable »",
        "`GET /api/films/{id}` → `FilmDetail` : les champs de la carte + `synopsis` ; film inconnu → 404 « Film introuvable »",
        "`GET /api/films/{id}?profil=2` sur un film interdit → 403 « Ce film n'est pas disponible pour ce profil »"],
       [CATALOGUE, F("CatalogueController.php", "php", r"""
<?php
// Reprends ici ta solution du TD 1 (CatalogueFiltres, FilmCard, CatalogueController),
// puis ajoute le profil, FilmDetail et la route GET /api/films/{id}.

final class ProfilQuery
{
    public function __construct(#[Assert\Positive] public readonly ?int $profil = null) {}
}

App::request('GET', '/api/films?profil=2');
App::request('GET', '/api/films/8?profil=2');
""")],
       ["Pour la fiche, la route a un paramètre : `#[Route('/api/films/{id}', methods: ['GET'])] public function fiche(int $id, #[MapQueryString] ?ProfilQuery $q, ...)`.",
        "`$profils->find($id) ?? throw new NotFoundHttpException('Profil introuvable')`",
        "Mets la recherche du profil dans une petite méthode privée : la liste et la fiche en ont besoin toutes les deux."],
       [F("CatalogueController.php", "php", r"""
<?php
final class CatalogueFiltres
{
    public function __construct(
        #[Assert\Length(max: 50)] public readonly ?string $q = null,
        #[Assert\Choice(['action', 'animation', 'comedie', 'documentaire', 'drame', 'sf'])] public readonly ?string $genre = null,
        #[Assert\Positive] public readonly ?int $profil = null,
        #[Assert\Positive] public readonly int $page = 1,
        #[Assert\Range(min: 1, max: 24)] public readonly int $parPage = 12,
    ) {}
}

final class ProfilQuery
{
    public function __construct(#[Assert\Positive] public readonly ?int $profil = null) {}
}

final class FilmCard
{
    public function __construct(
        public readonly int $id, public readonly string $titre, public readonly int $annee,
        public readonly string $genre, public readonly string $duree, public readonly int $ageMinimum,
    ) {}

    public static function fromEntity(Film $f): self
    {
        return new self($f->getId(), $f->getTitre(), $f->getAnnee(), $f->getGenre(), self::duree($f->getDureeMinutes()), $f->getAgeMinimum());
    }

    public static function duree(int $m): string
    {
        return $m < 60 ? "$m min" : sprintf('%d h %02d', intdiv($m, 60), $m % 60);
    }
}

final class FilmDetail
{
    public function __construct(
        public readonly int $id, public readonly string $titre, public readonly int $annee, public readonly string $genre,
        public readonly string $duree, public readonly int $ageMinimum, public readonly string $synopsis,
    ) {}

    public static function fromEntity(Film $f): self
    {
        return new self($f->getId(), $f->getTitre(), $f->getAnnee(), $f->getGenre(), FilmCard::duree($f->getDureeMinutes()), $f->getAgeMinimum(), $f->getSynopsis());
    }
}

final class CatalogueController extends AbstractController
{
    public function __construct(private FilmRepository $films, private ProfilRepository $profils) {}

    #[Route('/api/films', methods: ['GET'])]
    public function liste(#[MapQueryString] ?CatalogueFiltres $f): JsonResponse
    {
        $f ??= new CatalogueFiltres();
        $liste = $this->films->findAll();
        if ($f->profil !== null) {
            $profil = $this->profil($f->profil);
            $liste = array_filter($liste, fn(Film $x) => $profil->peutVoir($x));
        }
        if ($f->q !== null && trim($f->q) !== '') {
            $liste = array_filter($liste, fn(Film $x) => str_contains(mb_strtolower($x->getTitre()), mb_strtolower(trim($f->q))));
        }
        if ($f->genre !== null) {
            $liste = array_filter($liste, fn(Film $x) => $x->getGenre() === $f->genre);
        }
        $liste = array_values($liste);
        $total = count($liste);

        return $this->json([
            'items' => array_map(FilmCard::fromEntity(...), array_slice($liste, ($f->page - 1) * $f->parPage, $f->parPage)),
            'total' => $total,
            'page' => $f->page,
            'pages' => max(1, (int) ceil($total / $f->parPage)),
        ]);
    }

    #[Route('/api/films/{id}', methods: ['GET'])]
    public function fiche(int $id, #[MapQueryString] ?ProfilQuery $q): JsonResponse
    {
        $film = $this->films->find($id) ?? throw new NotFoundHttpException('Film introuvable');
        if ($q?->profil !== null && !$this->profil($q->profil)->peutVoir($film)) {
            throw new AccessDeniedHttpException("Ce film n'est pas disponible pour ce profil");
        }
        return $this->json(FilmDetail::fromEntity($film));
    }

    private function profil(int $id): Profil
    {
        return $this->profils->find($id) ?? throw new NotFoundHttpException('Profil introuvable');
    }
}

App::request('GET', '/api/films?profil=2');
App::request('GET', '/api/films/8?profil=2');
""")],
       ["Le profil filtre la liste côté serveur", "La fiche répond 200, 403 ou 404 selon le cas"],
       run=SRUN(r"""
check('Sans profil : 10 films', (App::request('GET', '/api/films')->json['total'] ?? 0) === 10);
$leo = App::request('GET', '/api/films?profil=2');
$ages = array_map(fn($x) => $x['ageMinimum'], $leo->json['items'] ?? []);
check('Léo (8 ans) : seulement les films « 0 » (3 films)', ($leo->json['total'] ?? 0) === 3 && $ages && max($ages) === 0, (string) $leo);
$ines = App::request('GET', '/api/films?profil=3');
check('Inès (12 ans) : les films 0, 10 et 12 (7 films, pile au seuil compris)', ($ines->json['total'] ?? 0) === 7, (string) $ines);
check('Ana (adulte) : les 10 films', (App::request('GET', '/api/films?profil=1')->json['total'] ?? 0) === 10);
check('Profil + genre : Léo, animation → 2 films', (App::request('GET', '/api/films?profil=2&genre=animation')->json['total'] ?? 0) === 2);
$pi = App::request('GET', '/api/films?profil=9');
check('Profil inconnu → 404 « Profil introuvable »', $pi->status === 404 && ($pi->json['error'] ?? '') === 'Profil introuvable', (string) $pi);
$fd = App::request('GET', '/api/films/10');
check('Fiche 10 : 200 avec synopsis et durée « 1 h 32 »', $fd->status === 200 && ($fd->json['duree'] ?? '') === '1 h 32' && !empty($fd->json['synopsis']), (string) $fd);
check('Fiche : pas de fichierVideo', !str_contains(json_encode($fd->json), 'stockage'));
$nf = App::request('GET', '/api/films/99');
check('Film 99 → 404 « Film introuvable »', $nf->status === 404 && ($nf->json['error'] ?? '') === 'Film introuvable', (string) $nf);
$no = App::request('GET', '/api/films/8?profil=2');
check('Charge (16) pour Léo → 403 avec le message', $no->status === 403 && ($no->json['error'] ?? '') === "Ce film n'est pas disponible pour ce profil", (string) $no);
check('Sintel (12) pour Inès (12) → 200 (pile au seuil)', App::request('GET', '/api/films/3?profil=3')->status === 200);
""")),
    TD(3, "La page d'accueil en rangées",
       "La page d'accueil de Bobine affiche des **rangées** : « Nouveautés », puis une rangée par genre. Écris `GET /api/accueil?profil=…` qui construit ces rangées, toujours avec le contrôle parental." + SSIM,
       ["`GET /api/accueil` (profil facultatif, inconnu → 404) → `{ rangees: [ { titre, items }, … ] }` ; `items` sont des `FilmCard`",
        "1re rangée « Nouveautés » : les 4 films ajoutés le plus récemment (`getAjouteLe()`), du plus récent au plus ancien",
        "Puis une rangée par genre qui a **au moins 2** films autorisés, titrée avec le libellé (« Animation », « Action », « Comédie », « Documentaire », « Drame », « Science-fiction »), films triés par titre, 6 au maximum",
        "Rangées de genre dans l'ordre alphabétique de leur titre ; un film interdit au profil n'apparaît dans aucune rangée"],
       [CATALOGUE, F("AccueilController.php", "php", r"""
<?php
final class FilmCard
{
    // reprends ta carte du TD 1
}

final class AccueilController extends AbstractController
{
    // à toi : GET /api/accueil
}

App::request('GET', '/api/accueil?profil=2');
""")],
       ["Les nouveautés : `usort($liste, fn($a, $b) => $b->getAjouteLe() <=> $a->getAjouteLe())` puis `array_slice(..., 0, 4)`.",
        "Grouper par genre : `$parGenre[$film->getGenre()][] = $film;` puis garder les groupes avec `count(...) >= 2`.",
        "Un tableau de libellés : `['animation' => 'Animation', 'sf' => 'Science-fiction', ...]` ; trie les rangées avec `usort` sur le titre."],
       [F("AccueilController.php", "php", r"""
<?php
final class FilmCard
{
    public function __construct(
        public readonly int $id, public readonly string $titre, public readonly int $annee,
        public readonly string $genre, public readonly string $duree, public readonly int $ageMinimum,
    ) {}

    public static function fromEntity(Film $f): self
    {
        return new self($f->getId(), $f->getTitre(), $f->getAnnee(), $f->getGenre(), self::duree($f->getDureeMinutes()), $f->getAgeMinimum());
    }

    public static function duree(int $m): string
    {
        return $m < 60 ? "$m min" : sprintf('%d h %02d', intdiv($m, 60), $m % 60);
    }
}

final class ProfilQuery
{
    public function __construct(#[Assert\Positive] public readonly ?int $profil = null) {}
}

final class AccueilController extends AbstractController
{
    private const LIBELLES = ['action' => 'Action', 'animation' => 'Animation', 'comedie' => 'Comédie', 'documentaire' => 'Documentaire', 'drame' => 'Drame', 'sf' => 'Science-fiction'];

    #[Route('/api/accueil', methods: ['GET'])]
    public function accueil(#[MapQueryString] ?ProfilQuery $q, FilmRepository $films, ProfilRepository $profils): JsonResponse
    {
        $liste = $films->findAll();
        if ($q?->profil !== null) {
            $profil = $profils->find($q->profil) ?? throw new NotFoundHttpException('Profil introuvable');
            $liste = array_values(array_filter($liste, fn(Film $f) => $profil->peutVoir($f)));
        }

        $recents = $liste;
        usort($recents, fn(Film $a, Film $b) => $b->getAjouteLe() <=> $a->getAjouteLe());
        $rangees = [['titre' => 'Nouveautés', 'items' => array_map(FilmCard::fromEntity(...), array_slice($recents, 0, 4))]];

        $parGenre = [];
        foreach ($liste as $f) $parGenre[$f->getGenre()][] = $f;
        $genres = [];
        foreach ($parGenre as $genre => $fs) {
            if (count($fs) < 2) continue;
            usort($fs, fn(Film $a, Film $b) => strcmp($a->getTitre(), $b->getTitre()));
            $genres[] = ['titre' => self::LIBELLES[$genre] ?? $genre, 'items' => array_map(FilmCard::fromEntity(...), array_slice($fs, 0, 6))];
        }
        usort($genres, fn($a, $b) => strcmp($a['titre'], $b['titre']));

        return $this->json(['rangees' => array_merge($rangees, $genres)]);
    }
}

App::request('GET', '/api/accueil?profil=2');
""")],
       ["Nouveautés puis rangées de genre, dans le bon ordre", "Le contrôle parental s'applique à toutes les rangées"],
       run=SRUN(r"""
$a = App::request('GET', '/api/accueil');
$r = $a->json['rangees'] ?? [];
check('200 et des rangées', $a->status === 200 && count($r) > 0, (string) $a);
check('1re rangée : « Nouveautés »', ($r[0]['titre'] ?? '') === 'Nouveautés');
check('Nouveautés : 4 films, du plus récent au plus ancien (10, 9, 8, 7)', array_map(fn($x) => $x['id'], $r[0]['items'] ?? []) === [10, 9, 8, 7], json_encode(array_map(fn($x) => $x['id'], $r[0]['items'] ?? [])));
$titres = array_map(fn($x) => $x['titre'], array_slice($r, 1));
check('Sans profil : rangées Action, Animation, Comédie (genres avec au moins 2 films), dans cet ordre', $titres === ['Action', 'Animation', 'Comédie'], json_encode($titres, JSON_UNESCAPED_UNICODE));
$anim = array_values(array_filter($r, fn($x) => $x['titre'] === 'Animation'))[0] ?? [];
check('Animation : films triés par titre', array_map(fn($x) => $x['titre'], $anim['items'] ?? []) === ['Big Buck Bunny', 'Elephants Dream', 'Sintel', 'Spring']);
check('Les items sont des cartes (duree formatée, pas de fichier)', isset($anim['items'][0]['duree']) && !str_contains(json_encode($a->json), 'stockage'));
$l = App::request('GET', '/api/accueil?profil=2');
$rl = $l->json['rangees'] ?? [];
$ages = []; foreach ($rl as $row) foreach ($row['items'] as $it) $ages[] = $it['ageMinimum'];
check('Léo : aucun film au-dessus de 0 dans aucune rangée', $ages && max($ages) === 0, json_encode($ages));
check('Léo : Nouveautés = Caminandes, Spring, Big Buck Bunny (seulement 3 autorisés… plus récents d\'abord)', array_map(fn($x) => $x['id'], $rl[0]['items'] ?? []) === [7, 5, 1], json_encode(array_map(fn($x) => $x['id'], $rl[0]['items'] ?? [])));
check('Léo : une seule rangée de genre (Animation : 2 films)', array_map(fn($x) => $x['titre'], array_slice($rl, 1)) === ['Animation'], json_encode(array_map(fn($x) => $x['titre'], array_slice($rl, 1)), JSON_UNESCAPED_UNICODE));
check('Profil inconnu → 404', App::request('GET', '/api/accueil?profil=42')->status === 404);
""")),
  ])

MODULES = [decoupe, modele, api]

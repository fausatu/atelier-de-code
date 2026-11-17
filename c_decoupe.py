from common import P, L, D, N, E, F, TD, RUN

T = "decoupe"


def DM(id, title, minutes, goal, why, flow, points, pitfalls, quiz, prereq, diagram, lessons, recap, example, notes, tds):
    return {"id": id, "track": T, "title": title, "minutes": minutes, "goal": goal, "why": why,
            "flow": flow, "points": points, "pitfalls": pitfalls, "quiz": quiz, "prereq": prereq,
            "diagram": diagram, "lessons": lessons, "recap": recap,
            "example": {"files": example if isinstance(example, list) else [example], "notes": notes}, "tds": tds}


def Q(q, options, answer, why):
    return {"q": q, "options": options, "answer": answer, "why": why}


JS = " Le bouton Exécuter lance les tests sur ton fichier : chaque message te dit ce qui est juste et pourquoi."
EX = " Le bouton Exécuter affiche le composant dans l'aperçu ; les tests l'utilisent comme un utilisateur."

# =========================================================================== 1. Besoin et scénarios
SCEN_IDS = r"""// Ticket : « Code promo au panier »
// En tant que client, je veux saisir un code promo dans mon panier
// pour obtenir une remise sur ma commande.
// Règles : un seul code par commande ; chaque code a une date de fin
// et un montant minimum de panier (BIENVENUE10 : -10 %, dès 50 €).
//
// Les situations proposées par l'équipe :
//   code-valide          Le client saisit BIENVENUE10 avec un panier de 80 € : -10 %.
//   code-inconnu         Le client saisit un code qui n'existe pas.
//   code-expire          Le client saisit un code dont la date de fin est passée.
//   minimum-pile         Le panier fait exactement 50 € pour un code « dès 50 € ».
//   minimum-loin         Le panier fait 20 € pour un code « dès 50 € ».
//   minuscules           Le client tape « bienvenue10 » en minuscules.
//   espaces              Le client colle «  BIENVENUE10 » avec des espaces autour.
//   deux-codes           Un code est déjà appliqué et le client en saisit un 2e.
//   bouton-vert          Le bouton « Payer » doit être vert.
//   retire-article       Code appliqué, puis le client retire un article : le panier passe sous 50 €.
//   double-clic          Le client clique deux fois très vite sur « Appliquer ».
//   visa                 Le paiement par carte doit accepter Visa.
"""

ex_besoin = F("ticket.md", "markdown", r"""
## Ticket : « Newsletter »

**Phrase** : un visiteur s'inscrit à la newsletter avec son prénom et son email,
et voit un message de confirmation.

**Scénarios**
- heureux : prénom + email valides → « Merci Ana ! », formulaire vidé
- erreurs : prénom vide ; email vide ; email mal formé ; email déjà inscrit (409)
- limites : espaces autour de l'email ; email en majuscules ; double clic sur « S'inscrire »
- hors sujet : le design du footer

**Données**
- entrée : prénom, email
- état : valeurs, champs touchés, tentative d'envoi, envoi en cours, erreur serveur, merci
- sortie : POST /api/newsletter { prenom, email } ; message affiché
""")

besoin = DM("dec-besoin", "Du ticket aux scénarios", 25,
  "Transformer une demande (un ticket) en une phrase claire, une liste de scénarios complète et la liste des données, avant d'écrire la moindre ligne de code.",
  "La plupart des « je ne sais pas par où commencer » viennent d'un besoin flou, pas d'un manque de technique. Les scénarios oubliés sont aussi la première source de bugs et de retours en recette.",
  ["Écrire la **phrase** : qui fait quoi, et pour obtenir quoi", "Lister les **scénarios** : heureux, erreurs, limites (et repérer le hors-sujet)",
   "Lister les **données** : ce qui entre, ce qui est gardé, ce qui sort", "Noter les **questions** à poser quand une règle n'est pas claire"],
  ["Une fonctionnalité se décrit du point de vue de l'utilisateur, pas du code.",
   "Le scénario « heureux » ne représente souvent qu'un quart du travail : les erreurs et les limites font le reste.",
   "Les cas limites se trouvent avec une liste de questions toujours la même (vide, zéro, pile au seuil, majuscules, espaces, double clic, pas connecté, serveur en panne…).",
   "Chaque scénario devient plus tard un `if`, un message ou un test.",
   "Une règle ambiguë se **demande**, elle ne se devine pas."],
  ["Coder dès la lecture du ticket.", "Ne penser qu'au cas où tout se passe bien.", "Inventer une règle au lieu de poser la question."],
  [Q("« Panier de 50 € pile pour un code dès 50 € », c'est…", ["un scénario heureux", "un cas limite", "hors sujet", "une erreur"], 1, "C'est une valeur pile sur le seuil : exactement là où les bugs se cachent (> au lieu de >=)."),
   Q("Quel scénario oublie-t-on le plus souvent ?", ["le cas qui marche", "ce qui se passe quand l'état change après coup (retirer un article après avoir appliqué le code)", "le titre de la page", "aucun"], 1, "Les changements après coup sont rarement dans le ticket."),
   Q("Une règle n'est pas claire (le code reste-t-il si le panier passe sous le minimum ?) :", ["je choisis ce qui est le plus simple à coder", "je pose la question et je note la réponse", "j'ignore le cas", "je fais les deux"], 1, "C'est une décision métier, pas technique.")],
  prereq=[
    P("Ticket", "La demande écrite d'une fonctionnalité (Jira, GitHub issue…), souvent sous forme de « user story »."),
    P("User story", "« En tant que [qui], je veux [quoi] afin de [pourquoi]. »"),
    P("Critère d'acceptation", "Une condition vérifiable qui dit quand c'est fini : « Étant donné un panier de 80 €, quand je saisis BIENVENUE10, alors le total passe à 72 € »."),
    P("Cas limite", "Une situation à la frontière : valeur pile au seuil, champ vide, liste à 0 ou 1 élément, saisie en majuscules, action répétée…"),
  ],
  diagram=D(
    nodes=[
      N("t", 0, 1, "Ticket", "souvent flou", kind="doc", color="muted"),
      N("ph", 1, 1, "Une phrase", "qui · quoi · pourquoi", kind="box", color="accent"),
      N("sc", 2, 0, "Scénarios", "heureux · erreurs · limites", kind="note", color="warn"),
      N("do", 2, 2, "Données", "entrée · état · sortie", kind="db", color="good"),
      N("q", 3, 1, "Questions", "à poser avant de coder", kind="pill", color="bad"),
    ],
    edges=[E("t", "ph"), E("ph", "sc"), E("ph", "do"), E("sc", "q", dashed=True), E("do", "q", dashed=True)],
    caption="Avant le code : une phrase, puis les scénarios et les données ; ce qui reste flou devient une question."),
  lessons=[
    L("Une phrase, du point de vue de l'utilisateur", r"""
Avant tout, écris la fonctionnalité en **une phrase**, avec un sujet qui est une personne :

> Un client saisit un code promo dans son panier et voit la remise appliquée au total.

Le format « user story » donne la même chose avec le pourquoi :

> En tant que **client**, je veux **saisir un code promo** afin de **payer moins cher**.

Si tu n'arrives pas à écrire cette phrase, ne code pas : le besoin n'est pas clair, et aucune technique ne le rendra clair. Relis le ticket, regarde la maquette, demande.

Les **critères d'acceptation** précisent quand c'est fini, sous une forme vérifiable :

| Étant donné… | Quand… | Alors… |
|---|---|---|
| un panier de 80 € | je saisis BIENVENUE10 | le total passe à 72 € et « -10 % » s'affiche |
| un panier de 20 € | je saisis BIENVENUE10 | « Ce code demande 50 € d'achat minimum » |
| un code déjà appliqué | je saisis un autre code | « Un seul code par commande » |

Chaque ligne deviendra un test.
"""),
    L("Lister les scénarios : la liste de questions", r"""
Classe ce qui peut arriver en trois familles (et écarte le hors-sujet) :

| Famille | Définition | Exemple (code promo) |
|---|---|---|
| **heureux** | tout se passe comme prévu | code valide, panier suffisant → remise |
| **erreur** | l'action doit être **refusée**, avec un message | code inconnu, expiré, panier trop petit, 2e code |
| **limite** | situation inhabituelle mais **acceptée**, qu'il faut traiter correctement | panier à 50 € pile, minuscules, espaces, double clic, état qui change après coup |
| hors sujet | ne concerne pas ce ticket | couleur du bouton Payer |

Pour trouver les limites, pose **toujours les mêmes questions** :

- **Vide / zéro / un / beaucoup** : liste vide ? un seul élément ? 1 000 ?
- **Pile sur le seuil** : 50 € quand la règle dit « dès 50 € » ; 30 kg quand la limite est 30 kg.
- **Saisie** : majuscules, espaces autour, accents, texte très long, copier-coller.
- **Répétition** : double clic, deux onglets, deux personnes en même temps.
- **Après coup** : que devient ce qu'on a fait si les données changent ensuite ?
- **Les autres** : pas connecté ? pas le droit ? serveur lent ? serveur en panne ?

Tu n'auras pas la réponse à tout : c'est normal. Ce qui compte, c'est d'avoir **vu** le cas, puis de décider (ou de demander).
"""),
    L("Les données : entrée, état, sortie", r"""
Dernière étape avant le code : liste les données.

| | Question | Code promo |
|---|---|---|
| **Entrée** | qu'est-ce que l'utilisateur (ou l'API) me donne ? | le code tapé, le panier |
| **État** | qu'est-ce que je dois garder entre deux actions ? | le code appliqué, la remise, l'envoi en cours, le message d'erreur |
| **Sortie** | qu'est-ce que je produis ? | `POST /api/panier/code`, le nouveau total, un message |

Cette liste te donne directement tes types, tes `useState` et tes appels d'API (le module suivant t'apprend à choisir le bon type de variable pour chaque donnée).

Enfin, note les **questions** qui restent : « Le code reste-t-il appliqué si le panier repasse sous 50 € ? » Ce n'est pas à toi de l'inventer : c'est une règle métier. Pose-la au chef de projet, et écris la réponse dans le ticket.
"""),
  ],
  recap=["Une phrase avec un utilisateur comme sujet ; sinon, on ne code pas encore.",
         "Scénarios : heureux, erreurs (refusé avec un message), limites (accepté, mais à traiter), hors sujet.",
         "La liste de questions : vide, seuil, saisie, répétition, après coup, les autres.",
         "Données : entrée, état, sortie.",
         "Une règle floue se demande."],
  example=ex_besoin,
  notes=["Une phrase, quatre familles de scénarios, trois sortes de données.", "Chaque scénario sera un `if` ou un message dans le code."],
  tds=[
    TD(1, "Trier les scénarios d'un ticket",
       "L'équipe a listé des situations pour le ticket « Code promo au panier ». Classe chacune : `heureux`, `erreur` (refusé avec un message), `limite` (accepté mais à traiter avec soin) ou `hors-sujet`." + JS,
       ["Remplis l'objet `classement` : une entrée par identifiant de la liste",
        "Valeurs possibles : `'heureux'`, `'erreur'`, `'limite'`, `'hors-sujet'`",
        "Règles du ticket : un seul code par commande, une date de fin, un minimum de panier (BIENVENUE10 : -10 % dès 50 €)",
        "Les tests t'expliquent chaque erreur de classement"],
       [F("scenarios.ts", "ts", SCEN_IDS + r"""
type Famille = 'heureux' | 'erreur' | 'limite' | 'hors-sujet';

export const classement: Record<string, Famille> = {
  'code-valide': 'heureux',
  // à toi : les 11 autres
};
""")],
       ["« Erreur » = l'application doit dire non. « Limite » = elle doit dire oui, mais c'est facile de se tromper (seuil, majuscules, espaces, répétition, changement après coup).",
        "Un panier à 50 € pile pour un code « dès 50 € » : refusé ou accepté ?",
        "Le design du bouton et le moyen de paiement ne font pas partie du ticket « code promo »."],
       [F("scenarios.ts", "ts", SCEN_IDS + r"""
type Famille = 'heureux' | 'erreur' | 'limite' | 'hors-sujet';

export const classement: Record<string, Famille> = {
  'code-valide': 'heureux',
  'code-inconnu': 'erreur',
  'code-expire': 'erreur',
  'minimum-pile': 'limite',      // accepté (« dès 50 € ») : piège du > au lieu de >=
  'minimum-loin': 'erreur',
  'minuscules': 'limite',        // accepté : on met le code en majuscules
  'espaces': 'limite',           // accepté : on retire les espaces
  'deux-codes': 'erreur',        // « Un seul code par commande »
  'bouton-vert': 'hors-sujet',
  'retire-article': 'limite',    // le cas « après coup » : question à poser au chef de projet
  'double-clic': 'limite',       // une seule requête, une seule remise
  'visa': 'hors-sujet',
};
""")],
       ["Chaque situation a sa famille", "Les cas limites sont acceptés, pas refusés"],
       run=RUN("js", entry="scenarios.ts", tests=r"""
const { classement } = require('./scenarios');
const attendu = {
  'code-valide': ['heureux', 'tout se passe comme prévu'],
  'code-inconnu': ['erreur', 'l\'application refuse, avec un message « Code inconnu »'],
  'code-expire': ['erreur', 'refusé : la date de fin est passée'],
  'minimum-pile': ['limite', 'accepté (« dès 50 € » inclut 50 €), mais c\'est LE piège du > au lieu de >='],
  'minimum-loin': ['erreur', 'refusé : le minimum de 50 € n\'est pas atteint'],
  'minuscules': ['limite', 'accepté : le client a tapé le bon code, il faut juste ignorer la casse'],
  'espaces': ['limite', 'accepté : il faut retirer les espaces avant de vérifier'],
  'deux-codes': ['erreur', 'refusé : un seul code par commande'],
  'bouton-vert': ['hors-sujet', 'du design, pas le ticket code promo'],
  'retire-article': ['limite', 'le cas « après coup » : il faut décider (et demander) ce que devient la remise'],
  'double-clic': ['limite', 'accepté, mais une seule requête et une seule remise'],
  'visa': ['hors-sujet', 'le paiement n\'est pas ce ticket'],
};
for (const [id, [fam, pourquoi]] of Object.entries(attendu)) {
  assert.equal(classement[id], fam, id + ' → ' + fam + ' : ' + pourquoi);
}
const inconnus = Object.keys(classement).filter((k) => !attendu[k]);
assert(inconnus.length === 0, 'Pas d\'identifiant inventé', inconnus.join(', '));
""")),
    TD(2, "Écrire les cas de test d'une règle",
       "Avant de coder les frais de livraison, écris la **liste des cas** qui prouvent que la règle est bien comprise. Les tests vérifient que chaque résultat attendu est juste, et que tu n'as oublié aucun seuil." + JS,
       ["Règle : livraison **gratuite dès 50 €** d'achat, sinon **4,90 €** ; colis **de plus de 10 kg** : **+5 €** (même si la livraison est gratuite) ; colis **de plus de 30 kg** : **refusé**",
        "Écris `cas` : une liste de `{ montant, poids, attendu }` où `attendu` est un nombre (en euros) ou `'refusé'`",
        "Couvre au moins : 50 € pile, un montant juste en dessous (49,99 €), 10 kg pile, juste au-dessus (10,5 kg), 30 kg pile, plus de 30 kg, et un colis lourd **avec** livraison gratuite",
        "Au moins 8 cas"],
       [F("cas.ts", "ts", r"""
type Cas = { montant: number; poids: number; attendu: number | 'refusé' };

// Règle : gratuite dès 50 €, sinon 4,90 € ; plus de 10 kg : +5 € ; plus de 30 kg : refusé.
export const cas: Cas[] = [
  { montant: 20, poids: 1, attendu: 4.9 },
  // à toi
];
""")],
       ["« Dès 50 € » : 50 € est inclus. « Plus de 10 kg » : 10 kg n'est pas concerné, 10,5 kg l'est.",
        "Un colis de 15 kg à 80 € : livraison gratuite, mais le supplément de 5 € s'applique quand même.",
        "Pense aux deux côtés de chaque seuil : pile dessus, et juste à côté."],
       [F("cas.ts", "ts", r"""
type Cas = { montant: number; poids: number; attendu: number | 'refusé' };

// Règle : gratuite dès 50 €, sinon 4,90 € ; plus de 10 kg : +5 € ; plus de 30 kg : refusé.
export const cas: Cas[] = [
  { montant: 20, poids: 1, attendu: 4.9 },        // heureux, payant
  { montant: 80, poids: 2, attendu: 0 },          // heureux, gratuit
  { montant: 50, poids: 2, attendu: 0 },          // seuil : 50 € pile → gratuit
  { montant: 49.99, poids: 2, attendu: 4.9 },     // juste en dessous
  { montant: 20, poids: 10, attendu: 4.9 },       // 10 kg pile : pas de supplément
  { montant: 20, poids: 10.5, attendu: 9.9 },     // juste au-dessus : +5 €
  { montant: 80, poids: 15, attendu: 5 },         // gratuit + supplément
  { montant: 20, poids: 30, attendu: 9.9 },       // 30 kg pile : accepté
  { montant: 20, poids: 31, attendu: 'refusé' },  // trop lourd
];
""")],
       ["Chaque résultat attendu est juste", "Chaque seuil est testé des deux côtés"],
       run=RUN("js", entry="cas.ts", tests=r"""
const { cas } = require('./cas');
const ref = (m, p) => (p > 30 ? 'refusé' : Math.round(((m >= 50 ? 0 : 4.9) + (p > 10 ? 5 : 0)) * 100) / 100);
assert(Array.isArray(cas) && cas.length >= 8, 'Au moins 8 cas', 'tu en as ' + (Array.isArray(cas) ? cas.length : 0));
for (const c of cas) {
  const r = ref(c.montant, c.poids);
  const ok = r === 'refusé' ? c.attendu === 'refusé' : typeof c.attendu === 'number' && Math.abs(c.attendu - r) < 0.001;
  assert(ok, `Cas ${c.montant} € / ${c.poids} kg : attendu ${JSON.stringify(c.attendu)}`, 'la règle donne ' + JSON.stringify(r));
}
const a = (f) => cas.some(f);
assert(a((c) => c.montant === 50), 'Couvre 50 € pile (le seuil de gratuité)');
assert(a((c) => c.montant < 50 && c.montant >= 49), 'Couvre un montant juste sous 50 € (49,99 €)');
assert(a((c) => c.poids === 10), 'Couvre 10 kg pile (pas encore de supplément)');
assert(a((c) => c.poids > 10 && c.poids <= 11), 'Couvre un poids juste au-dessus de 10 kg');
assert(a((c) => c.poids === 30), 'Couvre 30 kg pile (encore accepté)');
assert(a((c) => c.poids > 30), 'Couvre un colis de plus de 30 kg (refusé)');
assert(a((c) => c.montant >= 50 && c.poids > 10 && c.poids <= 30), 'Couvre un colis lourd AVEC livraison gratuite (le supplément reste)');
""")),
    TD(3, "Coder la règle à partir des cas",
       "Maintenant que les cas sont clairs, le code devient presque une traduction. Écris d'abord les étapes en commentaires, puis la fonction `fraisLivraison`." + JS,
       ["`fraisLivraison(montant, poids)` renvoie les frais en euros, arrondis au centime",
        "Gratuite dès 50 €, sinon 4,90 € ; plus de 10 kg : +5 € ; plus de 30 kg : lève une erreur `Colis trop lourd (30 kg maximum)`",
        "Montant ou poids négatif → erreur `Montant ou poids invalide`",
        "Écris les étapes en commentaires numérotés (`// 1.`, `// 2.`…) avant le code"],
       [F("livraison.ts", "ts", r"""
export function fraisLivraison(montant: number, poids: number): number {
  // 1. ...
  return 0;
}
""")],
       ["Commence par les refus (`throw`), puis calcule : c'est l'ordre « garde-fous d'abord ».",
        "`let frais = montant >= 50 ? 0 : 4.9; if (poids > 10) frais += 5;`",
        "Arrondi au centime : `Math.round(frais * 100) / 100` (0,1 + 0,2 ne fait pas exactement 0,3 en JavaScript)."],
       [F("livraison.ts", "ts", r"""
export function fraisLivraison(montant: number, poids: number): number {
  // 1. refuser les valeurs impossibles
  if (montant < 0 || poids < 0) throw new Error('Montant ou poids invalide');
  // 2. refuser les colis trop lourds
  if (poids > 30) throw new Error('Colis trop lourd (30 kg maximum)');
  // 3. frais de base : gratuits dès 50 €
  let frais = montant >= 50 ? 0 : 4.9;
  // 4. supplément poids, même si la livraison est gratuite
  if (poids > 10) frais += 5;
  // 5. arrondir au centime
  return Math.round(frais * 100) / 100;
}
""")],
       ["Le code suit les étapes", "Les seuils sont justes des deux côtés"],
       run=RUN("js", entry="livraison.ts", tests=r"""
const { fraisLivraison: f } = require('./livraison');
const src = source('livraison.ts');
assert(/\/\/\s*1\./.test(src) && /\/\/\s*3\./.test(src), 'Les étapes sont écrites en commentaires numérotés (au moins // 1. à // 3.)');
const cas = [[20, 1, 4.9], [80, 2, 0], [50, 2, 0], [49.99, 2, 4.9], [20, 10, 4.9], [20, 10.5, 9.9], [80, 15, 5], [20, 30, 9.9], [0, 0, 4.9]];
for (const [m, p, r] of cas) assert.equal(f(m, p), r, `${m} € / ${p} kg → ${r} €`);
const err = (fn) => { try { fn(); return ''; } catch (e) { return e.message; } };
assert.equal(err(() => f(20, 31)), 'Colis trop lourd (30 kg maximum)', 'Plus de 30 kg : erreur');
assert.equal(err(() => f(-5, 2)), 'Montant ou poids invalide', 'Montant négatif : erreur');
assert.equal(err(() => f(20, -1)), 'Montant ou poids invalide', 'Poids négatif : erreur');
""")),
  ])

# =========================================================================== 2. Variables
VAR_DESC = r"""// Composant <Panier utilisateur={...} /> : ce qu'il doit gérer.
//
//   lignes          les articles du panier ; l'utilisateur en ajoute et en supprime
//   total           la somme des prix × quantités
//   nombreArticles  le nombre total d'articles (somme des quantités)
//   panierVide      vrai s'il n'y a aucune ligne
//   codeSaisi       ce que l'utilisateur tape dans le champ « code promo »
//   remise          le pourcentage renvoyé par le serveur quand le code est accepté
//   enCours         vrai pendant l'appel au serveur pour vérifier le code
//   messageErreur   le message renvoyé par le serveur quand le code est refusé
//   utilisateur     la personne connectée, déjà connue par le composant parent
//   reponse         le JSON reçu du serveur, lu dans la fonction appliquerCode()
//   corpsRequete    l'objet { code, total } construit dans appliquerCode() avant le fetch
//   totalLigne      le prix × quantité d'une ligne, utilisé seulement dans le .map() de l'affichage
"""

PANIER_BUG = r"""
import { useEffect, useState } from 'react';

type Ligne = { id: number; nom: string; prix: number; quantite: number };

const DEPART: Ligne[] = [
  { id: 1, nom: 'Clavier', prix: 50, quantite: 1 },
  { id: 2, nom: 'Souris', prix: 20, quantite: 2 },
];

export default function Panier() {
  const [lignes, setLignes] = useState<Ligne[]>(DEPART);
  const [total, setTotal] = useState(90);
  const [nombre, setNombre] = useState(3);
  const [vide, setVide] = useState(false);

  function ajouter(id: number) {
    setLignes(lignes.map((l) => (l.id === id ? { ...l, quantite: l.quantite + 1 } : l)));
    const l = lignes.find((x) => x.id === id)!;
    setTotal(total + l.prix);
    setNombre(nombre + 1);
  }

  function supprimer(id: number) {
    const reste = lignes.filter((l) => l.id !== id);
    setLignes(reste);
    setNombre(reste.reduce((n, l) => n + l.quantite, 0));
    // oubli : le total n'est pas mis à jour
  }

  useEffect(() => {
    setVide(lignes.length === 0);
  }, [lignes]);

  if (vide) return <p>Ton panier est vide</p>;
  return (
    <div>
      <ul>
        {lignes.map((l) => (
          <li key={l.id}>
            {l.nom} × {l.quantite}
            <button onClick={() => ajouter(l.id)} aria-label={'Ajouter ' + l.nom}>+</button>
            <button onClick={() => supprimer(l.id)} aria-label={'Supprimer ' + l.nom}>Supprimer</button>
          </li>
        ))}
      </ul>
      <p id="nombre">{nombre} article{nombre > 1 ? 's' : ''}</p>
      <p id="total">Total : {total.toFixed(2)} €</p>
    </div>
  );
}
"""

PANIER_OK = r"""
import { useState } from 'react';

type Ligne = { id: number; nom: string; prix: number; quantite: number };

const DEPART: Ligne[] = [
  { id: 1, nom: 'Clavier', prix: 50, quantite: 1 },
  { id: 2, nom: 'Souris', prix: 20, quantite: 2 },
];

export default function Panier() {
  // la seule chose impossible à recalculer : les lignes
  const [lignes, setLignes] = useState<Ligne[]>(DEPART);

  // tout le reste se calcule à chaque rendu : jamais désynchronisé
  const total = lignes.reduce((t, l) => t + l.prix * l.quantite, 0);
  const nombre = lignes.reduce((n, l) => n + l.quantite, 0);
  const vide = lignes.length === 0;

  function ajouter(id: number) {
    setLignes((ls) => ls.map((l) => (l.id === id ? { ...l, quantite: l.quantite + 1 } : l)));
  }

  function supprimer(id: number) {
    setLignes((ls) => ls.filter((l) => l.id !== id));
  }

  if (vide) return <p>Ton panier est vide</p>;
  return (
    <div>
      <ul>
        {lignes.map((l) => (
          <li key={l.id}>
            {l.nom} × {l.quantite}
            <button onClick={() => ajouter(l.id)} aria-label={'Ajouter ' + l.nom}>+</button>
            <button onClick={() => supprimer(l.id)} aria-label={'Supprimer ' + l.nom}>Supprimer</button>
          </li>
        ))}
      </ul>
      <p id="nombre">{nombre} article{nombre > 1 ? 's' : ''}</p>
      <p id="total">Total : {total.toFixed(2)} €</p>
    </div>
  );
}
"""

TACHES_API = r"""
window.__taches = [
  { id: 1, titre: 'Lire le ticket', faite: true },
  { id: 2, titre: 'Lister les scénarios', faite: false },
  { id: 3, titre: 'Écrire les étapes', faite: false },
];
window.__patchs = 0;
__api["GET /api/taches"] = () => window.__taches;
__api["PATCH /api/taches/:id"] = async (p, b) => {
  window.__patchs++;
  await new Promise((r) => setTimeout(r, 250));
  if (p.id === '3') return [500, { title: 'Erreur interne' }];
  const t = window.__taches.find((x) => String(x.id) === p.id);
  t.faite = b.faite;
  return t;
};
"""

variables = DM("dec-variables", "Comment je le sais ? Choisir ses variables", 30,
  "Savoir, pour chaque étape d'une fonctionnalité, quelle variable il faut créer et de quelle sorte : un state, une valeur calculée, une variable locale ou une prop.",
  "« Je sais ce qu'il faut faire, mais je ne sais pas quelle variable créer » : c'est le blocage le plus courant après la lecture du ticket. Il se résout avec une question toujours la même.",
  ["Pour chaque « si… » ou « pendant que… », demander **comment je le sais ?**", "Si je peux le **calculer** à partir de ce que j'ai : une `const`, pas un state",
   "Si ça change dans le temps et que l'écran le montre : un **`useState`**", "Si je n'en ai besoin que dans une fonction : une variable **locale**",
   "Si le parent me le donne : une **prop**"],
  ["Chaque condition du code (`if (enCours)`) suppose une information : il faut savoir d'où elle vient.",
   "Une valeur qui se calcule (total, compteur, « vide », erreurs de validation) ne doit **pas** être un state : sinon elle finit désynchronisée.",
   "Un state ne doit contenir que ce qui est impossible à retrouver autrement (saisie, réponse du serveur, choix de l'utilisateur).",
   "« Pour chaque élément » → un objet (`Record`) ou un `Set` ; « la liste des… » → un tableau ; « pendant que… » → un booléen avec `finally`.",
   "Écris la réponse à « comment je le sais ? » en commentaire au-dessus de chaque `useState`, au début."],
  ["Un `useState` + un `useEffect` pour recopier une valeur calculée.", "Un `useState` pour une variable qui ne sert que dans un handler.", "Recopier une prop dans un state (elle ne se met plus à jour)."],
  [Q("« Afficher le nombre d'articles du panier » :", ["un useState nombre", "const nombre = lignes.reduce(...)", "une prop", "un useEffect"], 1, "Ça se calcule à partir des lignes : jamais de state."),
   Q("« Désactiver le bouton pendant l'envoi » :", ["const enCours = true", "un useState enCours, true au début, false dans finally", "une variable locale", "rien"], 1, "Ça change dans le temps et l'écran le montre."),
   Q("Le JSON reçu dans la fonction d'envoi, utilisé juste pour lire la remise :", ["useState", "variable locale dans la fonction", "prop", "useEffect"], 1, "Une fois la remise rangée dans le state, on n'en a plus besoin.")],
  prereq=[
    P("State", "Une valeur gardée par React entre deux rendus (`useState`) ; la changer redessine le composant."),
    P("Valeur calculée (dérivée)", "Une `const` recalculée à chaque rendu à partir d'autres valeurs (`const total = …`)."),
    P("Variable locale", "Une variable déclarée dans une fonction (un handler) ; elle disparaît quand la fonction est finie."),
    P("Prop", "Une valeur donnée par le composant parent : `<Panier utilisateur={u} />`."),
  ],
  diagram=D(
    nodes=[
      N("q", 0, 1, "Comment je le sais ?", "pour chaque « si… »", kind="note", color="warn"),
      N("p", 1, 0, "Le parent me le donne", "→ prop", kind="pill", color="muted"),
      N("c", 1, 2, "Je peux le calculer", "→ const calculée", kind="pill", color="good"),
      N("s", 2, 0, "Ça change, s'affiche", "→ useState", kind="pill", color="accent"),
      N("l", 2, 2, "Juste dans une fonction", "→ variable locale", kind="pill", color="muted"),
    ],
    edges=[E("q", "p"), E("q", "c"), E("q", "s"), E("q", "l")],
    caption="Une seule question, quatre réponses possibles : prop, valeur calculée, state, variable locale."),
  lessons=[
    L("La question magique", r"""
Chaque fois qu'une étape contient « si… », « pendant que… », « une fois que… », demande-toi : **comment mon code peut-il le savoir à ce moment-là ?**

« Si un envoi est déjà en cours : ne rien faire » :

- Comment je sais qu'un envoi est en cours ? Personne ne me le dit → je dois le **noter moi-même**.
- Ça vaut quoi ? Oui ou non → un **booléen** `enCours`.
- Quand ça change ? `true` au début de l'envoi, `false` à la fin, réussi ou raté (`finally`).
- L'écran réagit ? Oui (bouton « Envoi… ») → **`useState`**.

```ts
const [enCours, setEnCours] = useState(false);   // je le note

if (enCours) return;            // si déjà en cours : rien
setEnCours(true);               // ça commence
try { await fetch(…) }
finally { setEnCours(false) }   // c'est fini, quoi qu'il arrive
```
"""),
    L("Quatre réponses possibles", r"""
Pour chaque information, pose les questions **dans cet ordre** :

1. **Le parent me la donne ?** → c'est une **prop** (`utilisateur`, `produitId`). Ne la recopie pas dans un state.
2. **Je peux la calculer à partir de ce que j'ai déjà ?** → une **`const` calculée** à chaque rendu. Dans l'exemple ci-dessous, `lignes.reduce((t, l) => t + l.prix * l.quantite, 0)` parcourt les lignes en gardant un cumul `t` qui part de `0` : à chaque ligne `l`, la fonction fléchée `(t, l) => …` renvoie le nouveau cumul. Le résultat final est le total.
   ```ts
   const total = lignes.reduce((t, l) => t + l.prix * l.quantite, 0);
   const vide = lignes.length === 0;
   const erreurs = valider(valeurs);
   ```
3. **Ça change dans le temps et l'écran le montre ?** → **`useState`** : ce que tape l'utilisateur, ce qu'a répondu le serveur, un choix (filtre, onglet), « en cours ».
4. **J'en ai besoin seulement dans une fonction ?** → une **variable locale** : le JSON reçu, l'objet envoyé, un résultat intermédiaire.

L'erreur la plus fréquente est de faire un **state pour une valeur calculée**. On doit alors penser à la mettre à jour à chaque modification, et un jour on oublie (le TD 2 te montre ce bug). Une valeur calculée est toujours juste, par construction.
"""),
    L("Les phrases qui reviennent, et leur recette", r"""
| Si l'étape dit… | Variable | Code type |
|---|---|---|
| « pendant que… », « en cours », « en chargement » | booléen en state, `true` au début, `false` dans `finally` | `enCours`, `chargement` |
| « une fois que… », « après la 1re tentative » | booléen en state qui passe à `true` et y reste | `soumis`, `charge` |
| « pour chaque champ / élément » | objet ou `Set` en state | `Record<string, boolean>`, `Set<number>` |
| « la liste des… » | tableau en state (s'il vient de l'utilisateur ou du serveur) | `useState<Tache[]>([])` |
| « le nombre de… », « le total », « est-ce vide ? », « les éléments filtrés » | rien de nouveau : un **calcul** | `const restantes = taches.filter(…).length` |
| « afficher seulement si… » | rien de nouveau : une **condition dans le JSX** | `{erreur && <p>…</p>}` |
| « le message du serveur » | chaîne en state, vide au départ | `useState('')` |
| « ce que l'utilisateur a choisi » (filtre, onglet) | state avec une valeur par défaut | `useState<'toutes' \| 'faites'>('toutes')` |

Astuce de débutant (qui marche aussi après) : au-dessus de chaque `useState`, écris en commentaire la réponse à « comment je le sais ? ». Si tu n'arrives pas à l'écrire, c'est probablement une valeur calculée.
"""),
  ],
  recap=["Pour chaque « si » : comment je le sais ?",
         "Parent → prop ; calculable → const ; change et affiché → useState ; dans une fonction → locale.",
         "Jamais de state pour une valeur calculée (total, compteur, filtrée, erreurs).",
         "« Pendant que » = booléen + finally ; « pour chaque » = objet ou Set."],
  example=F("Compteur.tsx", "tsx", r"""
import { useState } from 'react';

type Tache = { id: number; titre: string; faite: boolean };

export default function Taches({ depart }: { depart: Tache[] }) {   // depart : prop (donnée par le parent)
  // comment je sais quelles tâches existent ? l'utilisateur les coche → state
  const [taches, setTaches] = useState(depart);
  // comment je sais lesquelles afficher ? c'est un choix de l'utilisateur → state
  const [filtre, setFiltre] = useState<'toutes' | 'a-faire'>('toutes');

  // calculs : jamais de state
  const visibles = filtre === 'toutes' ? taches : taches.filter((t) => !t.faite);
  const restantes = taches.filter((t) => !t.faite).length;

  function basculer(id: number) {
    const cible = taches.find((t) => t.id === id);   // variable locale
    if (!cible) return;
    setTaches(taches.map((t) => (t.id === id ? { ...t, faite: !t.faite } : t)));
  }

  return <p>{restantes} restantes, {visibles.length} affichées</p>;
}
"""),
  notes=["Deux states seulement : ce que l'utilisateur change.", "`visibles` et `restantes` se calculent.", "`cible` ne sert que dans la fonction."],
  tds=[
    TD(1, "State, calcul, locale ou prop ?",
       "Pour le composant `<Panier />` décrit dans le fichier, choisis la bonne sorte de variable pour chaque information." + JS,
       ["Remplis l'objet `choix` pour les 12 informations décrites",
        "Valeurs possibles : `'state'`, `'calcul'`, `'locale'`, `'prop'`",
        "Pose-toi la question dans l'ordre : le parent me la donne ? je peux la calculer ? ça change et l'écran le montre ? seulement dans une fonction ?",
        "Les tests t'expliquent chaque erreur"],
       [F("choix.ts", "ts", VAR_DESC + r"""
type Sorte = 'state' | 'calcul' | 'locale' | 'prop';

export const choix: Record<string, Sorte> = {
  lignes: 'state',
  // à toi : les 11 autres
};
""")],
       ["`total`, `nombreArticles` et `panierVide` se déduisent des lignes.",
        "`remise` et `messageErreur` viennent du serveur : impossible de les recalculer.",
        "`reponse` et `corpsRequete` n'existent que pendant `appliquerCode()` ; `totalLigne` n'existe que dans le `.map()`."],
       [F("choix.ts", "ts", VAR_DESC + r"""
type Sorte = 'state' | 'calcul' | 'locale' | 'prop';

export const choix: Record<string, Sorte> = {
  lignes: 'state',          // l'utilisateur les change
  total: 'calcul',          // somme des lignes
  nombreArticles: 'calcul', // somme des quantités
  panierVide: 'calcul',     // lignes.length === 0
  codeSaisi: 'state',       // ce que tape l'utilisateur
  remise: 'state',          // réponse du serveur, impossible à recalculer
  enCours: 'state',         // « pendant que », affiché sur le bouton
  messageErreur: 'state',   // réponse du serveur
  utilisateur: 'prop',      // donné par le parent
  reponse: 'locale',        // seulement dans appliquerCode()
  corpsRequete: 'locale',   // seulement dans appliquerCode()
  totalLigne: 'locale',     // seulement dans le .map()
};
""")],
       ["Trois calculs, cinq states, une prop, trois locales", "Chaque choix a sa justification"],
       run=RUN("js", entry="choix.ts", tests=r"""
const { choix } = require('./choix');
const attendu = {
  lignes: ['state', 'l\'utilisateur ajoute et supprime : ça change et l\'écran le montre'],
  total: ['calcul', 'ça se calcule à partir des lignes : un state serait un jour désynchronisé'],
  nombreArticles: ['calcul', 'somme des quantités des lignes'],
  panierVide: ['calcul', 'lignes.length === 0'],
  codeSaisi: ['state', 'c\'est ce que tape l\'utilisateur dans le champ'],
  remise: ['state', 'vient du serveur : impossible à recalculer, et l\'écran l\'affiche'],
  enCours: ['state', '« pendant que » : true au début, false dans finally ; le bouton l\'affiche'],
  messageErreur: ['state', 'vient du serveur et s\'affiche'],
  utilisateur: ['prop', 'le parent le connaît déjà : on le reçoit, on ne le recopie pas'],
  reponse: ['locale', 'sert seulement dans appliquerCode(), le temps de lire la remise'],
  corpsRequete: ['locale', 'construit et envoyé dans appliquerCode(), inutile après'],
  totalLigne: ['locale', 'calculé dans le .map() pour une ligne, inutile ailleurs'],
};
for (const [k, [sorte, pourquoi]] of Object.entries(attendu)) assert.equal(choix[k], sorte, k + ' → ' + sorte + ' : ' + pourquoi);
""")),
    TD(2, "Trop de useState : le total qui ment",
       "Ce panier a un bug : quand on supprime une ligne, le **total ne change pas**. La cause n'est pas l'oubli d'une ligne de code, c'est le choix des variables : `total`, `nombre` et `vide` sont des states alors qu'ils se calculent. Corrige à la racine." + EX,
       ["Garde **un seul** `useState` : `lignes`",
        "`total`, `nombre` et `vide` deviennent des `const` calculées à partir des lignes ; plus aucun `useEffect`",
        "Même affichage : `#nombre` (« 3 articles ») et `#total` (« Total : 90.00 € »), `Ton panier est vide` quand il n'y a plus rien",
        "Ajouter et supprimer mettent tout à jour correctement"],
       [F("Panier.tsx", "tsx", PANIER_BUG)],
       ["`const total = lignes.reduce((t, l) => t + l.prix * l.quantite, 0);`",
        "Les fonctions `ajouter` et `supprimer` ne font plus que `setLignes(…)`.",
        "Supprime le `useEffect` : `vide` vaut `lignes.length === 0`."],
       [F("Panier.tsx", "tsx", PANIER_OK)],
       ["Un seul state", "Le total ne peut plus mentir"],
       run=RUN("react", entry="Panier.tsx", tests=r"""
const src = source('Panier.tsx');
assert.equal((src.match(/useState\s*[<(]/g) || []).length, 1, 'Un seul useState (pour les lignes)');
assert(!/useEffect\s*\(/.test(src), 'Plus de useEffect : les valeurs se calculent');
assert.equal($('#total').textContent, 'Total : 90.00 €', 'Au départ : 90.00 €');
assert.equal($('#nombre').textContent, '3 articles', 'Au départ : 3 articles');
await click('[aria-label="Ajouter Souris"]');
assert.equal($('#total').textContent, 'Total : 110.00 €', 'Ajouter une souris : 110.00 €');
await click('[aria-label="Supprimer Clavier"]');
assert.equal($('#total').textContent, 'Total : 60.00 €', 'Supprimer le clavier : le total suit (60.00 €)');
assert.equal($('#nombre').textContent, '3 articles', 'Il reste 3 souris');
await click('[aria-label="Supprimer Souris"]');
assert.includes(text(), 'Ton panier est vide', 'Panier vidé : « Ton panier est vide »');
""")),
    TD(3, "Des étapes en français au composant",
       "Voici les étapes d'une liste de tâches, écrites en français. À toi de décider des variables (avec un commentaire « comment je le sais ? » au-dessus de chaque `useState`), puis de coder." + EX,
       ["Au chargement : `GET /api/taches` ; pendant le chargement `Chargement…` ; chaque tâche est un `<li>` avec une case à cocher (`aria-label` = le titre)",
        "Trois boutons de filtre `Toutes`, `À faire`, `Faites` ; le compteur `<p id=\"restantes\">2 tâches restantes</p>` (« 1 tâche restante » au singulier) compte toujours **toutes** les tâches non faites",
        "Cocher : `PATCH /api/taches/<id>` `{ faite }` ; **pendant** la mise à jour, la case de cette tâche est désactivée (les autres non)",
        "Si le serveur répond une erreur : la case revient à son état d'avant et `<p role=\"alert\">Impossible de mettre à jour « titre »</p>`"],
       [F("Taches.tsx", "tsx", r"""
// Étapes :
// 1. au chargement, récupérer les tâches ; pendant ce temps, afficher « Chargement… »
// 2. afficher les tâches selon le filtre choisi (toutes, à faire, faites)
// 3. afficher le nombre de tâches restantes (non faites), quel que soit le filtre
// 4. quand on coche une tâche : l'envoyer au serveur ; pendant ce temps, sa case est désactivée
// 5. si le serveur refuse : remettre la case comme avant et afficher un message

import { useEffect, useState } from 'react';

type Tache = { id: number; titre: string; faite: boolean };

export default function Taches() {
  // à toi : pour chaque useState, un commentaire « comment je le sais ? »
  return <p>Chargement…</p>;
}
""")],
       ["States : `taches` (vient du serveur, change), `chargement`, `filtre` (choix de l'utilisateur), `enCours` (un `Set<number>` des ids en cours : « pour chaque tâche »), `erreur` (message). Calculs : `visibles`, `restantes`.",
        "Pour revenir en arrière en cas d'erreur, garde l'ancienne valeur dans une variable **locale** avant de modifier.",
        "Mettre à jour un Set dans un state : `setEnCours((s) => new Set(s).add(id))` et pour retirer `setEnCours((s) => { const n = new Set(s); n.delete(id); return n; })`."],
       [F("Taches.tsx", "tsx", r"""
// Étapes :
// 1. au chargement, récupérer les tâches ; pendant ce temps, afficher « Chargement… »
// 2. afficher les tâches selon le filtre choisi (toutes, à faire, faites)
// 3. afficher le nombre de tâches restantes (non faites), quel que soit le filtre
// 4. quand on coche une tâche : l'envoyer au serveur ; pendant ce temps, sa case est désactivée
// 5. si le serveur refuse : remettre la case comme avant et afficher un message

import { useEffect, useState } from 'react';

type Tache = { id: number; titre: string; faite: boolean };
type Filtre = 'toutes' | 'a-faire' | 'faites';

const FILTRES: [Filtre, string][] = [['toutes', 'Toutes'], ['a-faire', 'À faire'], ['faites', 'Faites']];

export default function Taches() {
  // comment je connais les tâches ? le serveur me les donne, puis l'utilisateur les coche → state
  const [taches, setTaches] = useState<Tache[]>([]);
  // comment je sais que c'est en cours de chargement ? je le note au début, je l'enlève à la fin → state
  const [chargement, setChargement] = useState(true);
  // comment je sais quel filtre afficher ? c'est le choix de l'utilisateur → state
  const [filtre, setFiltre] = useState<Filtre>('toutes');
  // comment je sais quelles tâches sont en train d'être envoyées ? « pour chaque tâche » → un Set d'ids
  const [enCours, setEnCours] = useState<Set<number>>(new Set());
  // comment je connais le message d'erreur ? il dépend de la réponse du serveur → state
  const [erreur, setErreur] = useState('');

  useEffect(() => {
    fetch('/api/taches')
      .then((r) => r.json())
      .then((t: Tache[]) => setTaches(t))
      .finally(() => setChargement(false));
  }, []);

  // calculs : jamais de state
  const visibles = taches.filter((t) => (filtre === 'toutes' ? true : filtre === 'faites' ? t.faite : !t.faite));
  const restantes = taches.filter((t) => !t.faite).length;

  async function basculer(t: Tache) {
    const avant = t.faite;                       // locale : pour revenir en arrière
    setErreur('');
    setTaches((ts) => ts.map((x) => (x.id === t.id ? { ...x, faite: !avant } : x)));
    setEnCours((s) => new Set(s).add(t.id));
    try {
      const res = await fetch('/api/taches/' + t.id, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ faite: !avant }),
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
    } catch {
      setTaches((ts) => ts.map((x) => (x.id === t.id ? { ...x, faite: avant } : x)));
      setErreur(`Impossible de mettre à jour « ${t.titre} »`);
    } finally {
      setEnCours((s) => { const n = new Set(s); n.delete(t.id); return n; });
    }
  }

  if (chargement) return <p>Chargement…</p>;
  return (
    <div>
      <div>
        {FILTRES.map(([f, label]) => (
          <button key={f} aria-pressed={filtre === f} onClick={() => setFiltre(f)}>{label}</button>
        ))}
      </div>
      <ul>
        {visibles.map((t) => (
          <li key={t.id}>
            <label>
              <input type="checkbox" aria-label={t.titre} checked={t.faite} disabled={enCours.has(t.id)} onChange={() => basculer(t)} /> {t.titre}
            </label>
          </li>
        ))}
      </ul>
      <p id="restantes">{restantes} tâche{restantes > 1 ? 's' : ''} restante{restantes > 1 ? 's' : ''}</p>
      {erreur && <p role="alert">{erreur}</p>}
    </div>
  );
}
""")],
       ["Le compteur se calcule", "Seule la tâche en cours est désactivée"],
       run=RUN("react", entry="Taches.tsx", api=TACHES_API, tests=r"""
const src = source('Taches.tsx');
const nbState = (src.match(/useState\s*[<(]/g) || []).length;
const commentes = (src.match(/\/\/[^\n]*\n\s*const \[[^\]]+\]\s*=\s*useState/g) || []).length;
assert(commentes >= Math.max(1, nbState), 'Chaque useState a un commentaire « comment je le sais ? » juste au-dessus', commentes + ' sur ' + nbState);
assert(!/useState[^;]*restantes|setRestantes/.test(src), 'Le nombre de tâches restantes est calculé, pas un state');
assert(/Chargement/.test(text()), 'Pendant le chargement : « Chargement… »');
await waitFor(() => $$('li').length === 3, 3000);
const box = (t) => $(`input[aria-label="${t}"]`);
assert.equal($('#restantes').textContent, '2 tâches restantes', '2 tâches restantes');
await click(Array.from(document.querySelectorAll('button')).find((b) => b.textContent === 'Faites'));
assert.equal($$('li').length, 1, 'Filtre « Faites » : 1 tâche');
assert.equal($('#restantes').textContent, '2 tâches restantes', 'Le compteur compte toutes les tâches, quel que soit le filtre');
await click(Array.from(document.querySelectorAll('button')).find((b) => b.textContent === 'Toutes'));
await click(box('Lister les scénarios'));
await tick(40);
assert(box('Lister les scénarios').disabled, 'Pendant la mise à jour : la case de cette tâche est désactivée');
assert(!box('Écrire les étapes').disabled, '… mais pas les autres');
assert.equal($('#restantes').textContent, '1 tâche restante', 'Singulier : « 1 tâche restante »');
await waitFor(() => !box('Lister les scénarios').disabled, 3000);
assert.equal(window.__patchs, 1, 'Un PATCH envoyé');
await click(box('Écrire les étapes'));
await waitFor(() => $('[role=alert]'), 3000);
assert.equal($('[role=alert]').textContent, 'Impossible de mettre à jour « Écrire les étapes »', 'Erreur serveur : message');
assert(!box('Écrire les étapes').checked, 'Erreur serveur : la case revient à son état d\'avant');
assert.equal($('#restantes').textContent, '1 tâche restante', '… et le compteur aussi');
""")),
  ])

# =========================================================================== 3. Étapes
FACTURE_MONO = r"""
export type Ligne = { prix: number; quantite: number };
export type Client = { fidele: boolean };
export type Commande = { lignes: Ligne[]; client: Client; pays: 'FR' | 'BE' | 'CH' };

// Une seule fonction qui fait tout. Elle marche, mais personne n'ose la modifier.
export function calculerFacture(c: Commande) {
  let s = 0;
  for (const l of c.lignes) {
    if (l.quantite <= 0) throw new Error('Quantité invalide');
    s = s + l.prix * l.quantite;
  }
  let r = 0;
  if (c.client.fidele) {
    if (s >= 100) r = s * 0.1; else r = s * 0.05;
  }
  const ht = s - r;
  let t = 0;
  if (c.pays === 'FR') t = ht * 0.2;
  else if (c.pays === 'BE') t = ht * 0.21;
  else t = 0;
  let p = 0;
  if (ht < 60) { if (c.pays === 'FR') p = 4.9; else p = 9.9; }
  const ttc = ht + t + p;
  const arr = (x: number) => Math.round(x * 100) / 100;
  return { sousTotal: arr(s), remise: arr(r), ht: arr(ht), tva: arr(t), port: arr(p), total: arr(ttc) };
}
"""

FACTURE_OK = r"""
export type Ligne = { prix: number; quantite: number };
export type Client = { fidele: boolean };
export type Commande = { lignes: Ligne[]; client: Client; pays: 'FR' | 'BE' | 'CH' };

const arrondi = (x: number) => Math.round(x * 100) / 100;

// 1. additionner les lignes
export function sousTotal(lignes: Ligne[]): number {
  for (const l of lignes) if (l.quantite <= 0) throw new Error('Quantité invalide');
  return lignes.reduce((s, l) => s + l.prix * l.quantite, 0);
}

// 2. remise fidélité : 10 % dès 100 €, sinon 5 % ; rien pour les autres
export function remise(montant: number, client: Client): number {
  if (!client.fidele) return 0;
  return montant * (montant >= 100 ? 0.1 : 0.05);
}

// 3. TVA selon le pays
const TAUX_TVA = { FR: 0.2, BE: 0.21, CH: 0 } as const;
export function tva(ht: number, pays: Commande['pays']): number {
  return ht * TAUX_TVA[pays];
}

// 4. frais de port : offerts dès 60 € HT, sinon 4,90 € en France et 9,90 € ailleurs
export function fraisPort(ht: number, pays: Commande['pays']): number {
  if (ht >= 60) return 0;
  return pays === 'FR' ? 4.9 : 9.9;
}

// la fonction principale se lit comme les étapes
export function calculerFacture(c: Commande) {
  const s = sousTotal(c.lignes);
  const r = remise(s, c.client);
  const ht = s - r;
  const t = tva(ht, c.pays);
  const p = fraisPort(ht, c.pays);
  return { sousTotal: arrondi(s), remise: arrondi(r), ht: arrondi(ht), tva: arrondi(t), port: arrondi(p), total: arrondi(ht + t + p) };
}
"""

etapes = DM("dec-etapes", "Écrire les étapes, puis le code", 30,
  "Écrire une fonctionnalité d'abord en étapes numérotées (en français), puis transformer chaque étape en quelques lignes de code ou en une petite fonction bien nommée.",
  "Écrire du code directement mélange deux difficultés : savoir quoi faire et savoir comment l'écrire. Les étapes en commentaires séparent les deux, et la fonction finale se lit comme une recette.",
  ["Écrire les étapes en **commentaires numérotés**, une action par ligne", "Si une étape est trop grosse (plus de ~5 lignes de code), la **redécouper**",
   "**Refus d'abord** : les vérifications qui arrêtent tout, en haut (`return` / `throw`)", "Une étape qui a un nom clair peut devenir une **fonction** (`sousTotal`, `remise`…)"],
  ["Une étape = un verbe : « nettoyer », « vérifier », « calculer », « envoyer », « afficher ».",
   "Les garde-fous (« si… alors on arrête ») se mettent au début : le reste du code n'a plus à s'en soucier.",
   "Une fonction qui fait 60 lignes cache souvent 4 ou 5 étapes : chacune devient une petite fonction testable seule.",
   "La fonction principale doit se lire comme les étapes du commentaire.",
   "On garde les commentaires d'étapes tant qu'ils aident ; on supprime ceux qui répètent le code."],
  ["Commencer par la ligne 1 du code sans savoir où on va.", "Une étape « gérer la commande » (trop vague pour être codée).", "Des `if` imbriqués sur 4 niveaux au lieu de refus en haut."],
  [Q("Une bonne étape :", ["« gérer le formulaire »", "« vérifier que l'email n'est pas déjà utilisé »", "« faire le code »", "« tout valider »"], 1, "Un verbe précis, vérifiable."),
   Q("Où placer « si le panier est vide, arrêter » ?", ["à la fin", "au début (garde-fou)", "dans un else", "nulle part"], 1, "Les refus d'abord : le reste n'y pense plus."),
   Q("Pourquoi découper une grosse fonction en petites fonctions ?", ["c'est plus rapide à exécuter", "chaque étape se lit, se teste et se modifie seule", "c'est obligatoire en TypeScript", "pour avoir plus de fichiers"], 1, "On peut tester la remise sans tester la TVA.")],
  prereq=[
    P("Pseudo-code", "Les étapes d'un programme écrites en langage courant, sans syntaxe."),
    P("Garde-fou (guard clause)", "Une vérification en début de fonction qui arrête tout si les conditions ne sont pas remplies : `if (!email) return …`."),
    P("Fonction pure", "Une fonction qui ne dépend que de ses paramètres et renvoie un résultat sans rien modifier autour : facile à tester."),
  ],
  diagram=D(
    nodes=[
      N("e", 0, 1, "Étapes en commentaires", "// 1. // 2. // 3.", kind="doc", color="accent"),
      N("g", 1, 0, "Garde-fous", "refus d'abord", kind="pill", color="bad"),
      N("c", 1, 2, "Étapes simples", "2 à 5 lignes chacune", kind="pill", color="good"),
      N("f", 2, 1, "Petites fonctions", "une par étape nommée", kind="box", color="warn"),
      N("p", 3, 1, "Fonction principale", "se lit comme la recette", kind="file", color="accent"),
    ],
    edges=[E("e", "g"), E("e", "c"), E("g", "f"), E("c", "f"), E("f", "p")],
    caption="Les étapes d'abord ; les refus en haut ; chaque étape nommée devient une petite fonction ; la fonction principale les enchaîne."),
  lessons=[
    L("Les étapes en commentaires", r"""
Avant de coder, écris la recette :

```ts
function traiterInscription(form, existants) {
  // 1. nettoyer : retirer les espaces, email en minuscules
  // 2. vérifier les champs obligatoires
  // 3. vérifier le format de l'email
  // 4. vérifier que l'email n'est pas déjà utilisé
  // 5. créer l'utilisateur
  // 6. le renvoyer
}
```

Ensuite, remplis **une étape à la fois**, en lançant le code entre deux. Règles :

- **une étape = un verbe** et un objet précis (« vérifier le format de l'email », pas « gérer l'email ») ;
- si une étape demande plus de ~5 lignes, **redécoupe-la** en sous-étapes (`// 4a.`, `// 4b.`) ;
- si tu bloques sur une étape, c'est qu'il te manque une information : reviens à « comment je le sais ? » (module précédent).
"""),
    L("Refus d'abord (garde-fous)", r"""
Compare :

```ts
// imbriqué : on se perd
if (email) {
  if (formatOk(email)) {
    if (!existe(email)) {
      return creer(email);
    } else { return erreur('Email déjà utilisé'); }
  } else { return erreur('Email invalide'); }
} else { return erreur('Email requis'); }
```

```ts
// refus d'abord : chaque règle sur une ligne, le cas heureux à la fin
if (!email) return erreur('Email requis');
if (!formatOk(email)) return erreur('Email invalide');
if (existe(email)) return erreur('Email déjà utilisé');
return creer(email);
```

La 2e version se lit de haut en bas comme la liste des scénarios « erreur » du module 1, puis le scénario heureux. Ajouter une règle = ajouter une ligne.
"""),
    L("Une étape nommée devient une fonction", r"""
Quand une fonction dépasse une quarantaine de lignes, cherche les étapes cachées dedans : chacune devient une **petite fonction** avec un nom qui dit ce qu'elle fait.

```ts
export function calculerFacture(c: Commande) {
  const s = sousTotal(c.lignes);          // 1. additionner les lignes
  const r = remise(s, c.client);          // 2. remise fidélité
  const ht = s - r;
  const t = tva(ht, c.pays);              // 3. TVA selon le pays
  const p = fraisPort(ht, c.pays);        // 4. frais de port
  return { …, total: ht + t + p };
}
```

Bénéfices :
- la fonction principale **se lit comme les étapes** ;
- chaque étape se **teste seule** (« remise d'un client fidèle à 99,99 € ») ;
- une règle qui change (le taux de TVA belge) se modifie à **un seul endroit**.

Bons noms : un verbe pour une action (`envoyerFacture`), un nom pour un calcul (`sousTotal`, `fraisPort`), une question pour un booléen (`estExpire`, `peutCommander`).
"""),
  ],
  recap=["Étapes numérotées en commentaires avant le code ; une étape = un verbe précis.",
         "Étape trop grosse → sous-étapes.",
         "Refus d'abord, cas heureux à la fin.",
         "Étape nommée → petite fonction ; la fonction principale se lit comme la recette."],
  example=F("inscription.ts", "ts", r"""
export function verifierEmail(email: string, existants: string[]): string | null {
  // 1. nettoyer
  const e = email.trim().toLowerCase();
  // 2. refus d'abord
  if (!e) return 'Email requis';
  if (!/^\S+@\S+\.\S+$/.test(e)) return 'Email invalide';
  if (existants.includes(e)) return 'Email déjà utilisé';
  // 3. tout va bien
  return null;
}
"""),
  notes=["Les étapes restent en commentaires.", "Chaque refus tient sur une ligne.", "Le cas heureux est à la fin."],
  tds=[
    TD(1, "Remplir les étapes",
       "Les étapes de `traiterInscription` sont écrites. Remplis chacune avec quelques lignes de code, dans l'ordre, en lançant les tests entre deux." + JS,
       ["Entrée : `form` `{ nom, email }` (tels que saisis), `existants` (liste des emails déjà inscrits, en minuscules), `maintenant` (une date ISO)",
        "Nettoyer : espaces retirés partout, email en minuscules",
        "Refus, **dans cet ordre** et en renvoyant `{ ok: false, erreur }` : `Nom requis`, `Email requis`, `Email invalide`, `Email déjà utilisé`",
        "Succès : `{ ok: true, utilisateur: { id, nom, email, creeLe } }` avec `id` = nombre d'existants + 1 et `creeLe` = `maintenant`"],
       [F("inscription.ts", "ts", r"""
type Form = { nom: string; email: string };
type Utilisateur = { id: number; nom: string; email: string; creeLe: string };
type Resultat = { ok: true; utilisateur: Utilisateur } | { ok: false; erreur: string };

export function traiterInscription(form: Form, existants: string[], maintenant: string): Resultat {
  // 1. nettoyer : retirer les espaces, email en minuscules

  // 2. vérifier les champs obligatoires (nom, puis email)

  // 3. vérifier le format de l'email

  // 4. vérifier que l'email n'est pas déjà utilisé

  // 5. créer l'utilisateur

  // 6. le renvoyer
  return { ok: false, erreur: 'à faire' };
}
""")],
       ["Étape 1 : `const nom = form.nom.trim(); const email = form.email.trim().toLowerCase();`",
        "Étapes 2 à 4 : une ligne chacune, `if (…) return { ok: false, erreur: '…' };`",
        "Format : `/^\\S+@\\S+\\.\\S+$/.test(email)`."],
       [F("inscription.ts", "ts", r"""
type Form = { nom: string; email: string };
type Utilisateur = { id: number; nom: string; email: string; creeLe: string };
type Resultat = { ok: true; utilisateur: Utilisateur } | { ok: false; erreur: string };

export function traiterInscription(form: Form, existants: string[], maintenant: string): Resultat {
  // 1. nettoyer : retirer les espaces, email en minuscules
  const nom = form.nom.trim();
  const email = form.email.trim().toLowerCase();

  // 2. vérifier les champs obligatoires (nom, puis email)
  if (!nom) return { ok: false, erreur: 'Nom requis' };
  if (!email) return { ok: false, erreur: 'Email requis' };

  // 3. vérifier le format de l'email
  if (!/^\S+@\S+\.\S+$/.test(email)) return { ok: false, erreur: 'Email invalide' };

  // 4. vérifier que l'email n'est pas déjà utilisé
  if (existants.includes(email)) return { ok: false, erreur: 'Email déjà utilisé' };

  // 5. créer l'utilisateur
  const utilisateur = { id: existants.length + 1, nom, email, creeLe: maintenant };

  // 6. le renvoyer
  return { ok: true, utilisateur };
}
""")],
       ["Une étape = quelques lignes", "Les refus sont dans l'ordre"],
       run=RUN("js", entry="inscription.ts", tests=r"""
const { traiterInscription: f } = require('./inscription');
const ex = ['ana@exemple.fr', 'leo@exemple.fr'];
const T = '2026-11-16T09:00:00Z';
assert.deepEqual(f({ nom: '  ', email: 'x@y.fr' }, ex, T), { ok: false, erreur: 'Nom requis' }, 'Nom vide (ou que des espaces) → « Nom requis »');
assert.deepEqual(f({ nom: 'Zoé', email: '  ' }, ex, T), { ok: false, erreur: 'Email requis' }, 'Email vide → « Email requis »');
assert.deepEqual(f({ nom: '', email: '' }, ex, T), { ok: false, erreur: 'Nom requis' }, 'Les deux vides : le nom d\'abord (ordre des étapes)');
assert.deepEqual(f({ nom: 'Zoé', email: 'zoe@exemple' }, ex, T), { ok: false, erreur: 'Email invalide' }, 'Format → « Email invalide »');
assert.deepEqual(f({ nom: 'Ana', email: ' ANA@Exemple.fr ' }, ex, T), { ok: false, erreur: 'Email déjà utilisé' }, 'Doublon détecté même en majuscules avec des espaces (nettoyage d\'abord)');
const r = f({ nom: ' Zoé ', email: ' Zoe@Exemple.FR ' }, ex, T);
assert.deepEqual(r, { ok: true, utilisateur: { id: 3, nom: 'Zoé', email: 'zoe@exemple.fr', creeLe: T } }, 'Succès : utilisateur nettoyé, id 3, date reçue');
""")),
    TD(2, "Une fonction de 30 lignes en 4 étapes nommées",
       "`calculerFacture` fait tout dans une seule fonction : sous-total, remise, TVA, port. Elle marche, mais personne n'ose la modifier. Découpe-la en **petites fonctions exportées**, sans changer le résultat." + JS,
       ["Exporte `sousTotal(lignes)` (lève `Quantité invalide` si une quantité est ≤ 0), `remise(montant, client)` (fidèle : 10 % dès 100 €, sinon 5 % ; non fidèle : 0)",
        "Exporte `tva(ht, pays)` (FR 20 %, BE 21 %, CH 0 %) et `fraisPort(ht, pays)` (offerts dès 60 € HT ; sinon 4,90 € en France, 9,90 € ailleurs)",
        "`calculerFacture` utilise ces 4 fonctions et renvoie **exactement** le même objet qu'avant (arrondis au centime)",
        "Les taux de TVA sont dans un objet (une seule ligne à modifier si un taux change)"],
       [F("facture.ts", "ts", FACTURE_MONO)],
       ["Chaque bloc de la fonction actuelle correspond à une étape : repère-les avec un commentaire avant de les extraire.",
        "`const TAUX_TVA = { FR: 0.2, BE: 0.21, CH: 0 } as const;` puis `ht * TAUX_TVA[pays]`.",
        "Extrais une fonction, relance les tests, puis passe à la suivante."],
       [F("facture.ts", "ts", FACTURE_OK)],
       ["Même résultat qu'avant", "Chaque étape se teste seule"],
       run=RUN("js", entry="facture.ts", tests=r"""
const m = require('./facture');
for (const n of ['sousTotal', 'remise', 'tva', 'fraisPort', 'calculerFacture']) assert.equal(typeof m[n], 'function', n + ' est une fonction exportée');
const L = (...xs) => xs.map(([prix, quantite]) => ({ prix, quantite }));
assert.equal(m.sousTotal(L([10, 2], [5, 1])), 25, 'sousTotal : 10×2 + 5×1 = 25');
let e = ''; try { m.sousTotal(L([10, 0])); } catch (x) { e = x.message; }
assert.equal(e, 'Quantité invalide', 'sousTotal : quantité 0 → erreur');
assert.equal(m.remise(100, { fidele: true }), 10, 'remise : fidèle à 100 € → 10 %');
assert.equal(m.remise(99.99, { fidele: true }), 99.99 * 0.05, 'remise : fidèle à 99,99 € → 5 %');
assert.equal(m.remise(500, { fidele: false }), 0, 'remise : non fidèle → 0');
assert.equal(m.tva(100, 'BE'), 21, 'tva : BE 21 %');
assert.equal(m.tva(100, 'CH'), 0, 'tva : CH 0 %');
assert.equal(m.fraisPort(60, 'BE'), 0, 'fraisPort : 60 € HT pile → offerts');
assert.equal(m.fraisPort(59.99, 'FR'), 4.9, 'fraisPort : FR sous 60 € → 4,90 €');
assert.equal(m.fraisPort(10, 'CH'), 9.9, 'fraisPort : ailleurs → 9,90 €');
const cmd = (lignes, fidele, pays) => ({ lignes: L(...lignes), client: { fidele }, pays });
assert.deepEqual(m.calculerFacture(cmd([[40, 3]], true, 'FR')), { sousTotal: 120, remise: 12, ht: 108, tva: 21.6, port: 0, total: 129.6 }, 'Facture FR fidèle 120 €');
assert.deepEqual(m.calculerFacture(cmd([[19.99, 2]], true, 'BE')), { sousTotal: 39.98, remise: 2, ht: 37.98, tva: 7.98, port: 9.9, total: 55.86 }, 'Facture BE fidèle 39,98 €');
assert.deepEqual(m.calculerFacture(cmd([[30, 1]], false, 'CH')), { sousTotal: 30, remise: 0, ht: 30, tva: 0, port: 9.9, total: 39.9 }, 'Facture CH 30 €');
const src = source('facture.ts');
const corps = (src.match(/function calculerFacture[\s\S]*$/) || [''])[0];
assert(/sousTotal\(/.test(corps) && /remise\(/.test(corps) && /tva\(/.test(corps) && /fraisPort\(/.test(corps), 'calculerFacture appelle les 4 fonctions (elle se lit comme les étapes)');
assert(/0\.21/.test(src) && (src.match(/0\.21/g) || []).length === 1, 'Le taux belge n\'apparaît qu\'une fois');
""")),
    TD(3, "Tes étapes, ton code : importer des contacts",
       "Cette fois, rien n'est écrit : écris toi-même les étapes en commentaires numérotés, puis le code. Ta fonction lit un fichier CSV de contacts et dit ce qu'elle a importé et ce qu'elle a ignoré (et pourquoi)." + JS,
       ["`importerContacts(csv)` renvoie `{ importes: { nom, email }[], ignores: { ligne, raison }[] }` ; `ligne` = numéro de ligne dans le fichier (l'en-tête est la ligne 1)",
        "La 1re ligne est l'en-tête `nom;email` ; les lignes vides sont ignorées **sans** être signalées ; espaces retirés ; emails en minuscules",
        "Raisons : `nom manquant`, `email invalide`, `doublon` (même email qu'une ligne déjà importée, quelle que soit la casse)",
        "Au moins 4 étapes en commentaires numérotés (`// 1.` … `// 4.`)"],
       [F("contacts.ts", "ts", r"""
type Contact = { nom: string; email: string };
type Ignore = { ligne: number; raison: 'nom manquant' | 'email invalide' | 'doublon' };

export function importerContacts(csv: string): { importes: Contact[]; ignores: Ignore[] } {
  // à toi : écris d'abord les étapes ici, en commentaires numérotés
  return { importes: [], ignores: [] };
}
""")],
       ["Étapes possibles : 1. découper en lignes ; 2. sauter l'en-tête ; 3. pour chaque ligne : nettoyer, ignorer si vide, découper sur `;` ; 4. refus d'abord (nom, email, doublon) ; 5. importer.",
        "Numéro de ligne : avec `lignes.forEach((texte, i) => …)`, la ligne est `i + 1`.",
        "Doublon : garde les emails déjà importés dans un `Set` (« comment je sais qu'il est déjà importé ? »)."],
       [F("contacts.ts", "ts", r"""
type Contact = { nom: string; email: string };
type Ignore = { ligne: number; raison: 'nom manquant' | 'email invalide' | 'doublon' };

export function importerContacts(csv: string): { importes: Contact[]; ignores: Ignore[] } {
  const importes: Contact[] = [];
  const ignores: Ignore[] = [];
  const dejaVus = new Set<string>();   // comment je sais qu'un email est déjà importé ?

  // 1. découper le fichier en lignes
  const lignes = csv.split(/\r?\n/);

  lignes.forEach((texte, i) => {
    const numero = i + 1;
    // 2. sauter l'en-tête et les lignes vides
    if (i === 0 || texte.trim() === '') return;

    // 3. découper et nettoyer
    const [nomBrut = '', emailBrut = ''] = texte.split(';');
    const nom = nomBrut.trim();
    const email = emailBrut.trim().toLowerCase();

    // 4. refus d'abord
    if (!nom) return ignores.push({ ligne: numero, raison: 'nom manquant' });
    if (!/^\S+@\S+\.\S+$/.test(email)) return ignores.push({ ligne: numero, raison: 'email invalide' });
    if (dejaVus.has(email)) return ignores.push({ ligne: numero, raison: 'doublon' });

    // 5. importer
    dejaVus.add(email);
    importes.push({ nom, email });
  });

  return { importes, ignores };
}
""")],
       ["Tes propres étapes", "Chaque ligne ignorée a sa raison"],
       run=RUN("js", entry="contacts.ts", tests=r"""
const { importerContacts: f } = require('./contacts');
const src = source('contacts.ts');
for (const n of [1, 2, 3, 4]) assert(new RegExp('//\\s*' + n + '\\.').test(src), 'Étape // ' + n + '. écrite en commentaire');
const csv = ['nom;email', 'Ana; ANA@exemple.fr ', '', ' Léo ;leo@exemple', ';zoe@exemple.fr', 'Zoé;zoe@exemple.fr', 'Ana B;ana@Exemple.fr', '   ', 'Max;max@exemple.fr'].join('\n');
const r = f(csv);
assert.deepEqual(r.importes, [{ nom: 'Ana', email: 'ana@exemple.fr' }, { nom: 'Zoé', email: 'zoe@exemple.fr' }, { nom: 'Max', email: 'max@exemple.fr' }], 'Importés : Ana, Zoé, Max (nettoyés, emails en minuscules)', JSON.stringify(r.importes));
assert.deepEqual(r.ignores, [{ ligne: 4, raison: 'email invalide' }, { ligne: 5, raison: 'nom manquant' }, { ligne: 7, raison: 'doublon' }], 'Ignorés : ligne 4 (email invalide), 5 (nom manquant), 7 (doublon)', JSON.stringify(r.ignores));
assert.deepEqual(f('nom;email'), { importes: [], ignores: [] }, 'Fichier avec seulement l\'en-tête : rien');
assert.deepEqual(f('nom;email\r\nEva;eva@exemple.fr\r\n').importes, [{ nom: 'Eva', email: 'eva@exemple.fr' }], 'Fin de ligne Windows (\\r\\n) gérée');
""")),
  ])

# =========================================================================== 4. Tranches
PRODUITS_API = r"""
window.__appels = [];
const P = [
  { id: 1, nom: 'Clavier mécanique', prix: 89 },
  { id: 2, nom: 'Souris sans fil', prix: 29 },
  { id: 3, nom: 'Écran 27 pouces', prix: 249 },
  { id: 4, nom: 'Tapis de souris', prix: 12 },
];
window.__echecs = 0;
__api["GET /api/produits"] = async (p) => {
  const terme = (p.q || '').toLowerCase();
  window.__appels.push(terme);
  if (window.__echecs > 0) { window.__echecs--; return [500, { title: 'Erreur interne' }]; }
  if (terme === 'sou') await new Promise((r) => setTimeout(r, 600));
  return P.filter((x) => x.nom.toLowerCase().includes(terme));
};
"""

RECH_1 = r"""
import { useEffect, useState } from 'react';

type Produit = { id: number; nom: string; prix: number };

export default function Recherche() {
  // comment je connais les produits ? le serveur me les donne → state
  const [produits, setProduits] = useState<Produit[]>([]);
  // comment je connais le texte cherché ? l'utilisateur le tape → state
  const [terme, setTerme] = useState('');

  useEffect(() => {
    fetch('/api/produits').then((r) => r.json()).then(setProduits);
  }, []);

  // calcul : les produits qui correspondent
  const visibles = produits.filter((p) => p.nom.toLowerCase().includes(terme.trim().toLowerCase()));

  return (
    <div>
      <input type="search" aria-label="Rechercher" value={terme} onChange={(e) => setTerme(e.target.value)} />
      {visibles.length === 0 ? (
        <p>Aucun produit</p>
      ) : (
        <ul>{visibles.map((p) => <li key={p.id}>{p.nom} : {p.prix} €</li>)}</ul>
      )}
    </div>
  );
}
"""

RECH_2 = r"""
import { useCallback, useEffect, useState } from 'react';

type Produit = { id: number; nom: string; prix: number };

export default function Recherche() {
  const [produits, setProduits] = useState<Produit[]>([]);
  const [terme, setTerme] = useState('');
  // comment je sais que ça charge ? je le note au début, je l'enlève à la fin
  const [chargement, setChargement] = useState(true);
  // comment je sais que ça a échoué ? la réponse du serveur
  const [erreur, setErreur] = useState(false);

  const charger = useCallback(async () => {
    setChargement(true);
    setErreur(false);
    try {
      const res = await fetch('/api/produits');
      if (!res.ok) throw new Error('HTTP ' + res.status);
      setProduits(await res.json());
    } catch {
      setErreur(true);
    } finally {
      setChargement(false);
    }
  }, []);

  useEffect(() => { charger(); }, [charger]);

  const visibles = produits.filter((p) => p.nom.toLowerCase().includes(terme.trim().toLowerCase()));

  return (
    <div>
      <input type="search" aria-label="Rechercher" value={terme} onChange={(e) => setTerme(e.target.value)} />
      {chargement ? (
        <p>Chargement…</p>
      ) : erreur ? (
        <div role="alert">
          <p>Impossible de charger les produits</p>
          <button onClick={charger}>Réessayer</button>
        </div>
      ) : visibles.length === 0 ? (
        <p>Aucun produit</p>
      ) : (
        <ul>{visibles.map((p) => <li key={p.id}>{p.nom} : {p.prix} €</li>)}</ul>
      )}
    </div>
  );
}
"""

RECH_3 = r"""
import { useEffect, useState } from 'react';

type Produit = { id: number; nom: string; prix: number };

export default function Recherche() {
  const [produits, setProduits] = useState<Produit[]>([]);
  const [terme, setTerme] = useState('');
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState(false);
  // comment je sais qu'il faut recharger (bouton Réessayer) ? un compteur qui change
  const [essai, setEssai] = useState(0);

  useEffect(() => {
    let actif = true;                         // comment je sais que cette réponse est encore la bonne ?
    const t = terme.trim();
    const delai = setTimeout(async () => {    // attendre que l'utilisateur ait fini de taper
      setChargement(true);
      setErreur(false);
      try {
        const res = await fetch('/api/produits' + (t ? '?q=' + encodeURIComponent(t) : ''));
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        if (actif) setProduits(data);         // une réponse en retard est ignorée
      } catch {
        if (actif) setErreur(true);
      } finally {
        if (actif) setChargement(false);
      }
    }, t ? 300 : 0);
    return () => { actif = false; clearTimeout(delai); };
  }, [terme, essai]);

  return (
    <div>
      <input type="search" aria-label="Rechercher" value={terme} onChange={(e) => setTerme(e.target.value)} />
      {chargement && <p>Chargement…</p>}
      {!chargement && erreur && (
        <div role="alert">
          <p>Impossible de charger les produits</p>
          <button onClick={() => setEssai((n) => n + 1)}>Réessayer</button>
        </div>
      )}
      {!chargement && !erreur && (produits.length === 0 ? (
        <p>Aucun produit</p>
      ) : (
        <ul>{produits.map((p) => <li key={p.id}>{p.nom} : {p.prix} €</li>)}</ul>
      ))}
    </div>
  );
}
"""

STARTER_1 = r"""
// Tranche 1 : le cas heureux, de bout en bout.
// - charger les produits (GET /api/produits) et les afficher
// - filtrer par le texte tapé (sans tenir compte des majuscules ni des espaces autour)
// - « Aucun produit » si rien ne correspond
// Pas encore de chargement ni d'erreur : ce sera la tranche 2.

import { useEffect, useState } from 'react';

type Produit = { id: number; nom: string; prix: number };

export default function Recherche() {
  // à toi
  return <input type="search" aria-label="Rechercher" />;
}
"""

tranches = DM("dec-tranches", "Construire par tranches", 30,
  "Découper une fonctionnalité en tranches verticales : chacune marche de bout en bout et ajoute un morceau de valeur, en partant du cas heureux.",
  "Écrire toute l'interface, puis toute l'API, puis brancher à la fin : rien ne marche pendant des jours, et les problèmes arrivent tous en même temps. Par tranches, on a toujours quelque chose qui fonctionne.",
  ["Tranche 1 : le **cas heureux de bout en bout**, même moche", "Tranche 2 : les **états** (chargement, erreur, vide)",
   "Tranche 3 : les **cas limites** et le confort (recherche serveur, attente de frappe, réponses dans le désordre)", "Entre deux tranches : tout marche, on peut s'arrêter ou livrer"],
  ["Une tranche verticale traverse toutes les couches (écran → appel → données) pour un petit morceau de la fonctionnalité.",
   "La première tranche est volontairement simple : elle prouve que le chemin complet fonctionne.",
   "Chaque tranche part du code de la précédente : on ajoute, on ne recommence pas.",
   "L'ordre se choisit par dépendances (ce qui doit exister avant) puis par valeur pour l'utilisateur.",
   "Une tranche = une petite liste de cases à cocher, souvent un commit (ou une PR)."],
  ["Construire tout l'écran avant d'appeler l'API.", "Commencer par les cas limites avant que le cas simple marche.", "Une « tranche » qui ne se teste pas seule."],
  [Q("Une bonne 1re tranche pour « recherche de produits » :", ["le design final", "afficher la liste et filtrer, sans chargement ni erreur", "le debounce", "les tests de charge"], 1, "Le cas heureux, de bout en bout."),
   Q("Après la tranche 2, il manque la recherche côté serveur :", ["rien ne marche", "tout marche, il manque un morceau", "il faut tout refaire", "on ne peut pas livrer"], 1, "Chaque tranche laisse un produit qui fonctionne."),
   Q("Une tranche horizontale, c'est…", ["un morceau de bout en bout", "une couche complète (toute l'API) sans le reste", "une fonction", "un test"], 1, "À éviter : elle ne se voit et ne se teste pas seule.")],
  prereq=[
    P("Tranche verticale", "Un morceau de fonctionnalité qui traverse toutes les couches et marche seul."),
    P("Squelette qui marche (walking skeleton)", "La version la plus simple possible du chemin complet, sur laquelle on construit."),
    P("Debounce", "Attendre que l'utilisateur ait arrêté de taper (ex. 300 ms) avant de lancer la recherche."),
    P("Réponse périmée", "La réponse d'une ancienne requête qui arrive après une plus récente : il faut l'ignorer."),
  ],
  diagram=D(
    nodes=[
      N("t1", 0, 1, "Tranche 1", "liste + filtre", kind="pill", color="good"),
      N("t2", 1, 1, "Tranche 2", "chargement, erreur", kind="pill", color="warn"),
      N("t3", 2, 1, "Tranche 3", "serveur, attente", kind="pill", color="accent"),
      N("ok1", 0, 0, "Ça marche", "livrable", kind="note", color="muted"),
      N("ok2", 1, 0, "Ça marche", "livrable", kind="note", color="muted"),
      N("ok3", 2, 0, "Ça marche", "fini", kind="note", color="muted"),
    ],
    edges=[E("t1", "t2"), E("t2", "t3"), E("t1", "ok1", dashed=True), E("t2", "ok2", dashed=True), E("t3", "ok3", dashed=True)],
    caption="Trois tranches de la même fonctionnalité : après chacune, tout fonctionne."),
  lessons=[
    L("Vertical, pas horizontal", r"""
Deux façons de construire « la recherche de produits » :

| Horizontal (à éviter) | Vertical (par tranches) |
|---|---|
| 1. tout l'écran (champ, liste, états, design) | 1. liste + filtre, de bout en bout |
| 2. toute l'API (filtres, pagination, tri) | 2. chargement, erreur, « Réessayer » |
| 3. tout brancher… et tout casse | 3. recherche serveur, attente de frappe |
| rien ne marche avant la fin | **tout marche après chaque étape** |

Avantages des tranches : on voit le résultat tout de suite, les problèmes arrivent un par un, on peut montrer (ou livrer) à tout moment, et si le temps manque, on a quelque chose d'utile plutôt que trois morceaux qui ne marchent pas ensemble.
"""),
    L("Choisir l'ordre des tranches", r"""
1. **Tranche 1 = le cas heureux, le plus simple possible**, mais complet : les données arrivent, l'écran les montre, l'action principale fonctionne. Moche ? Pas grave.
2. Ensuite, les **états** qu'on verra forcément : chargement, erreur, vide.
3. Puis les **cas limites** et le confort : recherche côté serveur, attente de frappe, réponses dans le désordre, double clic…

Pour ordonner, deux questions :
- **dépendances** : qu'est-ce qui doit exister avant ? (on ne peut pas « retirer un favori » avant de pouvoir en ajouter un) ;
- **valeur** : qu'est-ce qui sert le plus vite à l'utilisateur ?

Chaque tranche = une courte liste de cases à cocher dans le ticket, et souvent un commit (`feat: recherche - liste et filtre`, `feat: recherche - erreurs et réessayer`…).
"""),
    L("Dans ce module : la même fonctionnalité en 3 tranches", r"""
Les trois TD de ce module sont **trois tranches de la même fonctionnalité**. Le code de départ de chaque niveau est la solution du niveau précédent : tu **ajoutes**, tu ne recommences pas.

| Niveau | Tranche | Ce qui s'ajoute |
|---|---|---|
| 1 | cas heureux | charger, afficher, filtrer, « Aucun produit » |
| 2 | états | « Chargement… », erreur + « Réessayer » |
| 3 | serveur et limites | recherche côté serveur (`?q=`), attendre 300 ms sans frappe, ignorer les réponses périmées |

À chaque niveau, les tests des tranches précédentes restent : tu vérifies au passage que tu n'as rien cassé.
"""),
  ],
  recap=["Vertical : chaque tranche traverse tout et marche seule.",
         "Tranche 1 : cas heureux de bout en bout ; puis états ; puis cas limites.",
         "Ordre : dépendances, puis valeur.",
         "Chaque tranche part de la précédente."],
  example=F("tranches.md", "markdown", r"""
## Ticket : recherche de produits

- [ ] **Tranche 1** — afficher la liste, filtrer en tapant, « Aucun produit »
- [ ] **Tranche 2** — « Chargement… », message d'erreur, bouton « Réessayer »
- [ ] **Tranche 3** — chercher côté serveur (`?q=`), attendre 300 ms, ignorer les réponses en retard

Après chaque case cochée : ça marche, je commite.
"""),
  notes=["Trois cases, trois commits.", "Après chacune, la fonctionnalité marche."],
  tds=[
    TD(1, "Tranche 1 : le cas heureux de bout en bout",
       "Première tranche de la recherche de produits : le chemin complet, sans fioritures." + EX,
       ["Au chargement, `GET /api/produits` ; chaque produit dans un `<li>` : `Nom : prix €`",
        "Le champ `<input type=\"search\" aria-label=\"Rechercher\">` filtre la liste pendant la frappe (majuscules et espaces autour ignorés)",
        "Rien ne correspond → `Aucun produit`",
        "Pas de chargement ni d'erreur pour l'instant (tranche 2)"],
       [F("Recherche.tsx", "tsx", STARTER_1)],
       ["Variables : `produits` (serveur) et `terme` (saisie) en state ; `visibles` calculé.",
        "`const visibles = produits.filter((p) => p.nom.toLowerCase().includes(terme.trim().toLowerCase()));`",
        "Un seul `useEffect` avec `[]` pour charger."],
       [F("Recherche.tsx", "tsx", RECH_1)],
       ["Le chemin complet marche", "Le filtre est calculé"],
       run=RUN("react", entry="Recherche.tsx", api=PRODUITS_API, tests=r"""
await waitFor(() => $$('li').length === 4, 3000);
assert.equal($$('li')[0].textContent, 'Clavier mécanique : 89 €', 'Format « Nom : prix € »');
await type('[aria-label=Rechercher]', '  SOURIS ');
assert.equal($$('li').length, 2, 'Filtre « SOURIS » (majuscules, espaces) : 2 produits');
await type('[aria-label=Rechercher]', 'zzz');
assert.includes(text(), 'Aucun produit', 'Rien ne correspond : « Aucun produit »');
await type('[aria-label=Rechercher]', '');
assert.equal($$('li').length, 4, 'Champ vidé : tout revient');
""")),
    TD(2, "Tranche 2 : chargement, erreur, réessayer",
       "La tranche 1 marche (c'est ton code de départ). Ajoute les états qu'on rencontre forcément en vrai : l'attente et la panne." + EX,
       ["Pendant le chargement : `Chargement…` (et pas « Aucun produit »)",
        "Si le serveur répond une erreur : `<div role=\"alert\">` avec `Impossible de charger les produits` et un bouton `Réessayer`",
        "`Réessayer` relance le chargement (avec `Chargement…` pendant ce temps)",
        "Tout ce que faisait la tranche 1 marche toujours"],
       [F("Recherche.tsx", "tsx", RECH_1.replace("export default function Recherche() {", "// Tranche 2 : ajoute « Chargement… », l'erreur et « Réessayer ».\nexport default function Recherche() {"))],
       ["Deux nouveaux states : `chargement` (`true` au départ) et `erreur`.",
        "Mets le chargement dans une fonction `charger` (async, avec `try/catch/finally`) que l'effet ET le bouton appellent.",
        "`if (!res.ok) throw …` : `fetch` ne lève pas d'erreur tout seul sur une 500."],
       [F("Recherche.tsx", "tsx", RECH_2)],
       ["La tranche 1 marche encore", "Le bouton Réessayer relance vraiment"],
       run=RUN("react", entry="Recherche.tsx", api=PRODUITS_API.replace("window.__echecs = 0;", "window.__echecs = 1;"), tests=r"""
assert.includes(text(), 'Chargement', 'Au départ : « Chargement… »');
assert(!/Aucun produit/.test(text()), '… et pas « Aucun produit » pendant le chargement');
await waitFor(() => $('[role=alert]'), 3000);
assert.includes($('[role=alert]').textContent, 'Impossible de charger les produits', 'Erreur serveur : message');
await click(Array.from(document.querySelectorAll('button')).find((b) => b.textContent === 'Réessayer'));
await tick(20);
assert.includes(text(), 'Chargement', 'Réessayer : « Chargement… » pendant le nouvel essai');
await waitFor(() => $$('li').length === 4, 3000);
assert(!$('[role=alert]'), 'Après succès : plus de message d\'erreur');
await type('[aria-label=Rechercher]', 'écran');
assert.equal($$('li').length, 1, 'Tranche 1 toujours là : le filtre marche');
""")),
    TD(3, "Tranche 3 : recherche serveur, attente, réponses en retard",
       "Le catalogue va grossir : la recherche doit se faire **côté serveur**. Sans précaution, une requête part à chaque lettre et une vieille réponse lente peut écraser la bonne. Ajoute la dernière tranche." + EX,
       ["La recherche appelle `GET /api/produits?q=<texte>` (sans `q` quand le champ est vide) ; plus de filtre côté client",
        "Attendre **300 ms** sans frappe avant d'appeler (taper « souris » d'un coup = **un** seul appel)",
        "Une réponse arrivée **après** une requête plus récente est ignorée (la liste affichée correspond toujours au texte du champ)",
        "Chargement, erreur et Réessayer marchent toujours"],
       [F("Recherche.tsx", "tsx", RECH_2.replace("export default function Recherche() {", "// Tranche 3 : recherche côté serveur, attente de 300 ms, réponses périmées ignorées.\nexport default function Recherche() {"))],
       ["Mets la requête dans un `useEffect` qui dépend de `[terme]` : `const delai = setTimeout(…, 300)` et `return () => clearTimeout(delai)`.",
        "Réponse périmée : une variable `let actif = true` dans l'effet, `actif = false` dans le nettoyage, et `if (actif) setProduits(…)`.",
        "Pour Réessayer : un state `essai` (compteur) ajouté aux dépendances de l'effet."],
       [F("Recherche.tsx", "tsx", RECH_3)],
       ["Un seul appel pour un mot tapé d'un coup", "La réponse lente ne gagne jamais"],
       run=RUN("react", entry="Recherche.tsx", api=PRODUITS_API, tests=r"""
await waitFor(() => $$('li').length === 4, 3000);
const avant = window.__appels.length;
for (const t of ['s', 'so', 'sou', 'sour', 'souri', 'souris']) await type('[aria-label=Rechercher]', t);
await waitFor(() => window.__appels.length > avant && $$('li').length === 2, 3000);
await tick(400);
assert.deepEqual(window.__appels.slice(avant), ['souris'], 'Taper « souris » d\'un coup : UN appel, avec ?q=souris', JSON.stringify(window.__appels.slice(avant)));
assert.equal($$('li').length, 2, 'Résultat du serveur : 2 produits');
const n2 = window.__appels.length;
await type('[aria-label=Rechercher]', 'sou');
await tick(360);
await type('[aria-label=Rechercher]', 'écran');
await tick(1200);
assert(window.__appels.slice(n2).includes('sou'), 'La requête « sou » (lente) est bien partie');
assert.equal($$('li').length, 1, 'La réponse lente de « sou » arrive après celle de « écran » : elle est ignorée');
assert.includes($('li').textContent, 'Écran', 'La liste correspond au texte du champ (« écran »)');
assert(!/filter\(\s*\(?p\)?\s*=>\s*p\.nom/.test(source('Recherche.tsx')), 'Plus de filtre côté client : c\'est le serveur qui cherche');
""")),
  ])

# =========================================================================== 5. Ticket complet
FAV_ANALYSE = r"""// Ticket « Favoris »
// En tant que client connecté, je veux mettre des produits en favoris depuis la liste,
// voir combien j'en ai dans l'en-tête et pouvoir en retirer. Maximum 20 favoris.
//
// Tranches proposées (dans le désordre) :
//   limite-20        refuser le 21e favori avec un message
//   retirer          retirer un favori (l'étoile se vide)
//   compteur         afficher le nombre de favoris dans l'en-tête
//   ajouter          cliquer sur l'étoile ajoute le produit aux favoris (appel API)
//   charger          au chargement, récupérer mes favoris (les étoiles déjà pleines)
//   double-clic      un double clic n'envoie qu'une requête
"""

FAV_LOGIQUE = r"""
export type Etat = { favoris: number[]; erreur: string };
export type Action =
  | { type: 'charger'; ids: number[] }
  | { type: 'ajouter'; id: number }
  | { type: 'retirer'; id: number };

export const MAX = 20;
export const ETAT_INITIAL: Etat = { favoris: [], erreur: '' };
"""

FAV_API = r"""
window.__fav = [2];
window.__requetes = [];
__api["GET /api/produits"] = () => [
  { id: 1, nom: 'Clavier' }, { id: 2, nom: 'Souris' }, { id: 3, nom: 'Écran' },
];
__api["GET /api/favoris"] = () => window.__fav;
__api["PUT /api/favoris/:id"] = async (p) => {
  window.__requetes.push('PUT ' + p.id);
  await new Promise((r) => setTimeout(r, 200));
  const id = Number(p.id);
  if (window.__plein) return [409, { title: 'Conflict', detail: 'Limite atteinte' }];
  if (!window.__fav.includes(id)) window.__fav.push(id);
  return [204, null];
};
__api["DELETE /api/favoris/:id"] = async (p) => {
  window.__requetes.push('DELETE ' + p.id);
  await new Promise((r) => setTimeout(r, 200));
  window.__fav = window.__fav.filter((x) => x !== Number(p.id));
  return [204, null];
};
"""

ticket = DM("dec-ticket", "Un ticket complet, de bout en bout", 35,
  "Appliquer toute la méthode sur un vrai ticket : analyser, ordonner les tranches, écrire la logique à part, puis brancher l'interface.",
  "Le but final : recevoir un ticket au travail et savoir quoi faire dans l'ordre, sans rester bloquée devant l'éditeur.",
  ["Lire le ticket : **phrase, scénarios, données, questions**", "Ordonner les **tranches** (dépendances, puis valeur)",
   "Écrire la **logique** à part, dans des fonctions testables sans écran", "Brancher l'**interface** : états, appels, cas limites"],
  ["La méthode complète : besoin → scénarios → variables → étapes → tranches.",
   "Séparer la logique (règles, calculs) de l'affichage : la logique se teste seule et se relit facilement.",
   "Un « reducer » (fonction `(etat, action) => nouvelEtat`) est une bonne forme pour la logique d'un écran.",
   "Le serveur reste juge : l'interface peut prévenir (limite atteinte), mais doit aussi gérer son refus (409).",
   "Garde une checklist du ticket et coche au fur et à mesure."],
  ["Coder l'interface et la logique mélangées dans les `onClick`.", "Faire confiance au compteur du front sans gérer le refus du serveur.", "Oublier le double clic."],
  [Q("La 1re tranche du ticket « Favoris » :", ["la limite de 20", "ajouter un favori (étoile → API)", "le double clic", "le compteur"], 1, "Le cas heureux de bout en bout ; le reste en dépend."),
   Q("Où tester « on ne peut pas dépasser 20 favoris » le plus simplement ?", ["dans un test d'interface", "dans une fonction de logique pure", "en production", "nulle part"], 1, "Pas besoin d'écran pour tester une règle."),
   Q("Le front croit qu'il reste de la place, le serveur répond 409 :", ["on ignore", "on affiche le refus et on remet l'étoile comme avant", "on réessaie en boucle", "on recharge la page"], 1, "Le serveur a le dernier mot.")],
  prereq=[
    P("Reducer", "Une fonction pure `(etat, action) => nouvelEtat` qui décrit toutes les transitions d'un écran (utilisée par `useReducer`)."),
    P("Logique pure", "Du code sans affichage ni appel réseau : il prend des valeurs et en renvoie d'autres."),
    P("Mise à jour optimiste", "Changer l'écran tout de suite, avant la réponse du serveur, et revenir en arrière s'il refuse."),
  ],
  diagram=D(
    nodes=[
      N("a", 0, 1, "Analyse", "scénarios · données", kind="doc", color="accent"),
      N("o", 1, 1, "Ordre des tranches", "dépendances, valeur", kind="note", color="warn"),
      N("l", 2, 0, "Logique pure", "reducer testé seul", kind="box", color="good"),
      N("u", 2, 2, "Interface", "états · API · cas limites", kind="file", color="accent"),
      N("f", 3, 1, "Ticket fini", "checklist cochée", kind="pill", color="good"),
    ],
    edges=[E("a", "o"), E("o", "l"), E("o", "u"), E("l", "f"), E("u", "f")],
    caption="Toute la méthode sur un ticket : analyser, ordonner, écrire la logique à part, brancher l'interface."),
  lessons=[
    L("La méthode complète, en une page", r"""
Quand tu reçois un ticket, fais ces étapes **dans l'ordre**, sur papier ou dans un fichier `notes.md` :

1. **Phrase** : qui fait quoi, pour obtenir quoi.
2. **Scénarios** : heureux, erreurs, limites (vide, seuil, saisie, répétition, après coup, les autres).
3. **Données** : entrée, état, sortie → pour chaque info, « comment je le sais ? » (prop, calcul, state, locale).
4. **Questions** pour le chef de projet (règles floues).
5. **Tranches** : le cas heureux de bout en bout d'abord, puis les états, puis les limites.
6. Pour chaque tranche : **étapes en commentaires**, puis le code, puis on teste, puis on commite.

Ça paraît long ; en pratique, 10 à 20 minutes de papier évitent des heures de code à refaire. Avec l'habitude, les étapes 1 à 4 se font de tête pour les petits tickets.
"""),
    L("Séparer la logique de l'affichage", r"""
Les règles (« pas plus de 20 », « pas de doublon », « retirer ce qui n'existe pas ne fait rien ») n'ont pas besoin d'écran. Écris-les dans une **fonction pure**, souvent un *reducer* :

```ts
export function favorisReducer(etat: Etat, action: Action): Etat {
  switch (action.type) {
    case 'ajouter':
      if (etat.favoris.includes(action.id)) return etat;                       // limite : déjà là
      if (etat.favoris.length >= MAX) return { ...etat, erreur: 'Tu as déjà 20 favoris' };
      return { favoris: [...etat.favoris, action.id], erreur: '' };
    …
  }
}
```

Puis le composant l'utilise avec `useReducer(favorisReducer, ETAT_INITIAL)` et ne s'occupe plus que de l'affichage et des appels.

Bénéfices : la logique se **teste en quelques lignes**, sans cliquer ; le composant devient court ; la même logique peut servir ailleurs (une autre page, une appli mobile).
"""),
    L("Le serveur a le dernier mot", r"""
Même si l'interface empêche le 21e favori, le serveur doit le refuser aussi (quelqu'un peut appeler l'API directement, ou avoir deux onglets ouverts). Et l'interface doit **gérer ce refus** :

1. au clic, mettre l'étoile pleine tout de suite (**optimiste**) et désactiver le bouton ;
2. envoyer la requête ;
3. si le serveur refuse (409) : **revenir en arrière** et afficher son message ;
4. dans tous les cas, réactiver le bouton (`finally`).

C'est la même mécanique que les tâches du module « Choisir ses variables », appliquée à un vrai ticket.
"""),
  ],
  recap=["Phrase → scénarios → données → questions → tranches → étapes → code.",
         "La logique dans une fonction pure (reducer), testée sans écran.",
         "Le composant : affichage, appels, états.",
         "Le serveur a le dernier mot : gérer son refus, revenir en arrière."],
  example=F("notes.md", "markdown", r"""
## Favoris

Phrase : un client connecté met des produits en favoris, voit le compteur, en retire. Max 20.

Scénarios : ajouter ✓ · retirer ✓ · 21e refusé · déjà en favori · double clic · pas connecté (hors ticket : redirection existante) · serveur en panne

Données : entrée = id produit ; état = ids favoris, ids en cours, message ; sortie = PUT/DELETE /api/favoris/:id, compteur

Tranches : ajouter → charger → compteur → retirer → limite-20 → double clic
"""),
  notes=["Une page de notes avant le code.", "Les tranches dans l'ordre des dépendances."],
  tds=[
    TD(1, "Analyser le ticket et ordonner les tranches",
       "Avant de coder les favoris, prépare l'analyse : l'ordre des tranches, et la sorte de chaque variable de l'écran." + JS,
       ["`ordre` : les 6 identifiants de tranches du fichier, dans l'ordre où tu les ferais",
        "Contraintes : on commence par le cas heureux de bout en bout ; on ne peut pas retirer ni limiter avant de pouvoir ajouter ; le compteur a besoin des favoris chargés",
        "`variables` : la sorte (`state`, `calcul`, `locale`, `prop`) de `favoris`, `nombreFavoris`, `enCours`, `message`, `estFavori`, `produits`",
        "Les tests t'expliquent chaque contrainte"],
       [F("analyse.ts", "ts", FAV_ANALYSE + r"""
export const ordre: string[] = [
  // à toi
];

//   favoris        les ids des produits en favoris (chargés puis modifiés par l'utilisateur)
//   nombreFavoris  le nombre affiché dans l'en-tête
//   enCours        les ids des produits dont la requête est en cours
//   message        le message de refus du serveur
//   estFavori      pour un produit dans le .map() de l'affichage, est-il en favori ?
//   produits       la liste des produits, chargée depuis l'API au démarrage
export const variables: Record<string, 'state' | 'calcul' | 'locale' | 'prop'> = {
  // à toi
};
""")],
       ["Le cas heureux de bout en bout : un clic sur l'étoile qui appelle l'API.",
        "`charger` doit venir avant `compteur` ; `retirer` et `limite-20` après `ajouter` ; `double-clic` est un confort de fin.",
        "`nombreFavoris` = `favoris.length` ; `estFavori` n'existe que dans le `.map()`."],
       [F("analyse.ts", "ts", FAV_ANALYSE + r"""
export const ordre: string[] = ['ajouter', 'charger', 'compteur', 'retirer', 'limite-20', 'double-clic'];

//   favoris        les ids des produits en favoris (chargés puis modifiés par l'utilisateur)
//   nombreFavoris  le nombre affiché dans l'en-tête
//   enCours        les ids des produits dont la requête est en cours
//   message        le message de refus du serveur
//   estFavori      pour un produit dans le .map() de l'affichage, est-il en favori ?
//   produits       la liste des produits, chargée depuis l'API au démarrage
export const variables: Record<string, 'state' | 'calcul' | 'locale' | 'prop'> = {
  favoris: 'state',
  nombreFavoris: 'calcul',
  enCours: 'state',
  message: 'state',
  estFavori: 'locale',
  produits: 'state',
};
""")],
       ["Le cas heureux d'abord", "Les dépendances sont respectées"],
       run=RUN("js", entry="analyse.ts", tests=r"""
const { ordre, variables } = require('./analyse');
const ids = ['limite-20', 'retirer', 'compteur', 'ajouter', 'charger', 'double-clic'];
assert(Array.isArray(ordre) && ordre.length === 6 && ids.every((i) => ordre.includes(i)), 'ordre contient les 6 tranches, chacune une fois', JSON.stringify(ordre));
const pos = (i) => ordre.indexOf(i);
assert.equal(ordre[0], 'ajouter', 'On commence par le cas heureux de bout en bout : ajouter (étoile → API)');
assert(pos('retirer') > pos('ajouter'), 'retirer après ajouter (on ne retire que ce qu\'on a pu ajouter)');
assert(pos('limite-20') > pos('ajouter'), 'limite-20 après ajouter (c\'est une règle sur l\'ajout)');
assert(pos('compteur') > pos('charger'), 'compteur après charger (sinon il affiche 0 au démarrage)');
assert(pos('double-clic') > pos('ajouter') && pos('double-clic') >= 4, 'double-clic vers la fin : c\'est un cas limite, pas le cœur');
const v = { favoris: ['state', 'chargés puis modifiés : ça change et ça s\'affiche'], nombreFavoris: ['calcul', 'favoris.length'], enCours: ['state', '« pendant que », pour chaque produit'], message: ['state', 'vient du serveur'], estFavori: ['locale', 'calculé dans le .map() pour un produit'], produits: ['state', 'vient de l\'API au démarrage'] };
for (const [k, [s, why]] of Object.entries(v)) assert.equal(variables[k], s, k + ' → ' + s + ' : ' + why);
""")),
    TD(2, "La logique à part : un reducer testé sans écran",
       "Écris toute la logique des favoris dans une fonction pure. Pas d'écran, pas d'API : juste les règles." + JS,
       ["`favorisReducer(etat, action)` avec les actions `charger` (`ids`), `ajouter` (`id`), `retirer` (`id`) ; il ne modifie jamais l'état reçu (il en renvoie un nouveau)",
        "`ajouter` : déjà en favori → état inchangé (le même objet) ; déjà `MAX` (20) favoris → `erreur: 'Tu as déjà 20 favoris'` sans ajouter ; sinon ajouté à la fin et `erreur` vidée",
        "`retirer` : retire l'id (s'il n'y est pas : état inchangé) et vide `erreur` ; `charger` : remplace la liste (sans doublons) et vide `erreur`",
        "Exporte aussi `peutAjouter(etat)` (`true` s'il reste de la place)"],
       [F("favoris.ts", "ts", FAV_LOGIQUE + r"""
export function favorisReducer(etat: Etat, action: Action): Etat {
  // à toi
  return etat;
}

export function peutAjouter(etat: Etat): boolean {
  return true;
}
""")],
       ["Un `switch (action.type)` avec un `case` par action.",
        "Refus d'abord dans `ajouter` : déjà là, puis limite, puis l'ajout.",
        "Sans doublons : `[...new Set(action.ids)]`."],
       [F("favoris.ts", "ts", FAV_LOGIQUE + r"""
export function favorisReducer(etat: Etat, action: Action): Etat {
  switch (action.type) {
    case 'charger':
      return { favoris: [...new Set(action.ids)], erreur: '' };
    case 'ajouter':
      if (etat.favoris.includes(action.id)) return etat;
      if (etat.favoris.length >= MAX) return { ...etat, erreur: 'Tu as déjà 20 favoris' };
      return { favoris: [...etat.favoris, action.id], erreur: '' };
    case 'retirer':
      if (!etat.favoris.includes(action.id)) return etat;
      return { favoris: etat.favoris.filter((x) => x !== action.id), erreur: '' };
  }
}

export function peutAjouter(etat: Etat): boolean {
  return etat.favoris.length < MAX;
}
""")],
       ["Toutes les règles, testées en quelques lignes", "L'état reçu n'est jamais modifié"],
       run=RUN("js", entry="favoris.ts", tests=r"""
const { favorisReducer: r, peutAjouter, ETAT_INITIAL, MAX } = require('./favoris');
const gele = (o) => Object.freeze({ ...o, favoris: Object.freeze([...o.favoris]) });
let e = r(gele(ETAT_INITIAL), { type: 'charger', ids: [3, 1, 3] });
assert.deepEqual(e, { favoris: [3, 1], erreur: '' }, 'charger : remplace, sans doublon');
const e2 = r(gele(e), { type: 'ajouter', id: 7 });
assert.deepEqual(e2, { favoris: [3, 1, 7], erreur: '' }, 'ajouter : à la fin');
const g = gele(e2);
assert(r(g, { type: 'ajouter', id: 1 }) === g, 'ajouter un favori déjà présent : renvoie le MÊME état (rien ne change)');
const plein = gele({ favoris: Array.from({ length: MAX }, (_, i) => i + 1), erreur: '' });
assert.equal(peutAjouter(plein), false, 'peutAjouter : false à 20');
assert.equal(peutAjouter(gele(e2)), true, 'peutAjouter : true à 3');
const refus = r(plein, { type: 'ajouter', id: 99 });
assert(refus.favoris.length === MAX && refus.erreur === 'Tu as déjà 20 favoris', 'ajouter au-delà de 20 : refusé avec un message');
const apres = r(gele(refus), { type: 'retirer', id: 5 });
assert(apres.favoris.length === MAX - 1 && !apres.favoris.includes(5) && apres.erreur === '', 'retirer : enlève et vide le message');
const g3 = gele(e2);
assert(r(g3, { type: 'retirer', id: 42 }) === g3, 'retirer un id absent : même état');
""")),
    TD(3, "L'écran des favoris",
       "La logique existe (fournie : c'est la solution du niveau 2). Branche l'écran : produits, étoiles, compteur, appels API, refus du serveur et double clic." + EX,
       ["Au chargement : `GET /api/produits` et `GET /api/favoris` (tableau d'ids) → action `charger` ; l'en-tête `<p id=\"compteur\">1 favori</p>` (« 2 favoris » au pluriel, « 0 favori »)",
        "Chaque produit : un `<li>` avec un bouton `aria-label=\"Favori <nom>\"` et `aria-pressed` (true si en favori) ; clic → `PUT /api/favoris/<id>` (ajout) ou `DELETE` (retrait)",
        "Mise à jour **optimiste** : l'étoile change tout de suite ; pendant la requête, **ce** bouton est désactivé (un double clic = une seule requête)",
        "Refus du serveur (409) : revenir en arrière et afficher `<p role=\"alert\">Limite atteinte</p>` (le `detail` renvoyé)"],
       [F("favoris.ts", "ts", FAV_LOGIQUE + r"""
export function favorisReducer(etat: Etat, action: Action): Etat {
  switch (action.type) {
    case 'charger':
      return { favoris: [...new Set(action.ids)], erreur: '' };
    case 'ajouter':
      if (etat.favoris.includes(action.id)) return etat;
      if (etat.favoris.length >= MAX) return { ...etat, erreur: 'Tu as déjà 20 favoris' };
      return { favoris: [...etat.favoris, action.id], erreur: '' };
    case 'retirer':
      if (!etat.favoris.includes(action.id)) return etat;
      return { favoris: etat.favoris.filter((x) => x !== action.id), erreur: '' };
  }
}

export function peutAjouter(etat: Etat): boolean {
  return etat.favoris.length < MAX;
}
"""), F("Favoris.tsx", "tsx", r"""
import { useEffect, useReducer, useState } from 'react';
import { favorisReducer, ETAT_INITIAL } from './favoris';

type Produit = { id: number; nom: string };

export default function Favoris() {
  const [etat, dispatch] = useReducer(favorisReducer, ETAT_INITIAL);
  // à toi : les autres variables (comment je le sais ?), le chargement, le clic
  return <p id="compteur">0 favori</p>;
}
""")],
       ["States en plus du reducer : `produits`, `enCours` (un `Set` d'ids), `messageServeur`. Calculs : le nombre, `estFavori` dans le `.map()`.",
        "Au clic : `const etaitFavori = …` (locale), `dispatch` l'action optimiste, puis la requête ; en cas de `!res.ok`, `dispatch` l'action inverse et lis `(await res.json()).detail`.",
        "Le bouton : `disabled={enCours.has(p.id)}` ; ajoute l'id au début du clic, retire-le dans `finally`."],
       [F("favoris.ts", "ts", FAV_LOGIQUE + r"""
export function favorisReducer(etat: Etat, action: Action): Etat {
  switch (action.type) {
    case 'charger':
      return { favoris: [...new Set(action.ids)], erreur: '' };
    case 'ajouter':
      if (etat.favoris.includes(action.id)) return etat;
      if (etat.favoris.length >= MAX) return { ...etat, erreur: 'Tu as déjà 20 favoris' };
      return { favoris: [...etat.favoris, action.id], erreur: '' };
    case 'retirer':
      if (!etat.favoris.includes(action.id)) return etat;
      return { favoris: etat.favoris.filter((x) => x !== action.id), erreur: '' };
  }
}

export function peutAjouter(etat: Etat): boolean {
  return etat.favoris.length < MAX;
}
"""), F("Favoris.tsx", "tsx", r"""
import { useEffect, useReducer, useState } from 'react';
import { favorisReducer, ETAT_INITIAL } from './favoris';

type Produit = { id: number; nom: string };

export default function Favoris() {
  const [etat, dispatch] = useReducer(favorisReducer, ETAT_INITIAL);
  // comment je connais les produits ? l'API au démarrage
  const [produits, setProduits] = useState<Produit[]>([]);
  // comment je sais quels boutons sont en cours ? « pour chaque produit » → Set d'ids
  const [enCours, setEnCours] = useState<Set<number>>(new Set());
  // comment je connais le refus du serveur ? sa réponse
  const [messageServeur, setMessageServeur] = useState('');

  useEffect(() => {
    fetch('/api/produits').then((r) => r.json()).then(setProduits);
    fetch('/api/favoris').then((r) => r.json()).then((ids: number[]) => dispatch({ type: 'charger', ids }));
  }, []);

  const nombre = etat.favoris.length;   // calcul

  async function basculer(p: Produit) {
    if (enCours.has(p.id)) return;
    const etaitFavori = etat.favoris.includes(p.id);   // locale
    setMessageServeur('');
    dispatch({ type: etaitFavori ? 'retirer' : 'ajouter', id: p.id });   // optimiste
    setEnCours((s) => new Set(s).add(p.id));
    try {
      const res = await fetch('/api/favoris/' + p.id, { method: etaitFavori ? 'DELETE' : 'PUT' });
      if (!res.ok) {
        dispatch({ type: etaitFavori ? 'ajouter' : 'retirer', id: p.id });   // retour en arrière
        const probleme = await res.json().catch(() => null);
        setMessageServeur(probleme?.detail || 'Action impossible');
      }
    } finally {
      setEnCours((s) => { const n = new Set(s); n.delete(p.id); return n; });
    }
  }

  return (
    <div>
      <p id="compteur">{nombre} favori{nombre > 1 ? 's' : ''}</p>
      {(messageServeur || etat.erreur) && <p role="alert">{messageServeur || etat.erreur}</p>}
      <ul>
        {produits.map((p) => {
          const estFavori = etat.favoris.includes(p.id);   // locale au .map()
          return (
            <li key={p.id}>
              {p.nom}
              <button aria-label={'Favori ' + p.nom} aria-pressed={estFavori} disabled={enCours.has(p.id)} onClick={() => basculer(p)}>
                {estFavori ? '★' : '☆'}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
""")],
       ["La logique est réutilisée telle quelle", "Le serveur a le dernier mot"],
       run=RUN("react", entry="Favoris.tsx", api=FAV_API, tests=r"""
const b = (nom) => $(`[aria-label="Favori ${nom}"]`);
await waitFor(() => $$('li').length === 3 && $('#compteur').textContent === '1 favori', 3000);
assert.equal(b('Souris').getAttribute('aria-pressed'), 'true', 'Favoris chargés : Souris déjà en favori');
assert(/favorisReducer/.test(source('Favoris.tsx')), 'Le composant utilise la logique de favoris.ts');
await click(b('Clavier'));
assert.equal(b('Clavier').getAttribute('aria-pressed'), 'true', 'Optimiste : l\'étoile change tout de suite');
assert.equal($('#compteur').textContent, '2 favoris', 'Compteur : 2 favoris (pluriel)');
assert(b('Clavier').disabled, 'Pendant la requête : ce bouton est désactivé');
await click(b('Clavier'));
await waitFor(() => !b('Clavier').disabled, 3000);
assert.deepEqual(window.__requetes, ['PUT 1'], 'Double clic : une seule requête PUT', JSON.stringify(window.__requetes));
await click(b('Souris'));
await waitFor(() => !b('Souris').disabled, 3000);
assert(window.__requetes.includes('DELETE 2') && $('#compteur').textContent === '1 favori', 'Retirer : DELETE et compteur à 1');
window.__plein = true;
await click(b('Écran'));
await waitFor(() => $('[role=alert]'), 3000);
assert.equal($('[role=alert]').textContent, 'Limite atteinte', 'Refus du serveur : son message');
assert.equal(b('Écran').getAttribute('aria-pressed'), 'false', 'Refus : retour en arrière (étoile vide)');
assert.equal($('#compteur').textContent, '1 favori', 'Refus : compteur revenu à 1');
""")),
  ])

MODULES = [besoin, variables, etapes, tranches, ticket]

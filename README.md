# Atelier de code

Un tableau de bord pour apprendre le développement web **en comprenant comment les choses fonctionnent** avant de les écrire.

**En ligne : https://fausatu.github.io/atelier-de-code/**

47 modules, 9 parcours, environ 12 heures de contenu : PHP orienté objet, Doctrine, DTO, architecture Symfony, DDD, React, appels d'API, Next.js et Git.

---

## Sommaire

- [La méthode](#la-méthode)
- [Les parcours](#les-parcours)
- [Fonctionnalités](#fonctionnalités)
- [Utiliser le dashboard](#utiliser-le-dashboard)
- [Activer les boutons Claude](#activer-les-boutons-claude)
- [Modifier ou ajouter du contenu](#modifier-ou-ajouter-du-contenu)
- [Structure du projet](#structure-du-projet)
- [Contribuer](#contribuer)

---

## La méthode

Chaque module suit les mêmes 4 étapes, courtes :

| Étape | Contenu | Pourquoi |
|---|---|---|
| **1. Comprendre** | Le problème que ça résout, puis le mécanisme en 4 étapes sous forme de schéma, l'essentiel et les pièges fréquents | On ne retient bien que ce qu'on comprend |
| **2. Exemple** | Un code réel, commenté, avec ce qu'il faut remarquer | Voir le mécanisme appliqué |
| **3. Quiz** | 3 questions, chaque réponse expliquée | Se tester fixe mieux en mémoire que relire |
| **4. TD** | Un exercice pratique avec éditeur, indices progressifs, solution et vérifications | On apprend en écrivant le code soi-même |

Un module terminé (quiz + TD) revient ensuite en **révision espacée** après 1, 3, 7, 16 puis 35 jours. Une erreur le fait revenir dès le lendemain.

## Les parcours

```
Back   PHP POO ──▶ Doctrine ──▶ DTO ──▶ Architecture ──▶ DDD (bonus)
Front  React ──▶ Données & API ──▶ Next.js
Outils Git & GitHub (en parallèle)
```

Le parcours **Architecture** relie les deux lignes : il suit une action de bout en bout, du clic dans React jusqu'à la base de données via Symfony.

| Parcours | Modules | Durée | Contenu |
|---|---:|---:|---|
| **PHP orienté objet** | 6 | ~1 h 30 | Classes & objets · Encapsulation & visibilité · Héritage & classes abstraites · Interfaces & polymorphisme · Namespaces & autoload · Injection de dépendances |
| **Doctrine ORM** | 5 | ~1 h 10 | ORM, entités & migrations · persist, flush & Unit of Work · Repositories & requêtes · Relations entre entités · Lazy loading & problème N+1 |
| **DTO avec Symfony** | 5 | ~1 h | DTO : à quoi ça sert · DTO d'entrée & validation · DTO de sortie & mapping · Du DTO à l'entité · Filtres & pagination |
| **Architecture : qui fait quoi** | 4 | ~1 h | Les 5 rôles (contrôleur, DTO, service, entité, repository) · Comment les classes sont reliées · Les erreurs à travers les couches · Une fonctionnalité de bout en bout |
| **DDD (bonus)** | 5 | ~1 h 20 | Langage commun & bounded contexts · Value Objects · Entités riches · Agrégats & invariants · Couches & repositories |
| **React** | 5 | ~1 h 20 | Composants, JSX & props · State & re-rendu · Événements & formulaires · useEffect · Hooks personnalisés |
| **React : données & API** | 5 | ~1 h 20 | Une requête HTTP de A à Z · Récupérer des données (fetch & axios) · Envoyer des données (mutations) · Couche API & hook · TanStack Query |
| **Next.js (App Router)** | 5 | ~1 h 10 | Dossiers = routes · Server & Client Components · Données & cache · Server Actions · Route Handlers |
| **Git & GitHub** | 7 | ~1 h 50 | Comment Git fonctionne · Merge & conflits · Rebase · Revenir en arrière · Conventional Commits · Pull Requests · stash, cherry-pick, tags, bisect |

Les TD back et front utilisent le même fil rouge, une **bibliothèque de livres**. Ce que React envoie avec axios arrive dans les DTO Symfony écrits dans un autre parcours.

## Fonctionnalités

- **Tableau de bord graphique** : anneau de progression, un anneau par parcours, calendrier d'activité sur 22 semaines, jours d'affilée.
- **Roadmap par parcours** : chemin étape par étape, avec ta position et l'objectif final.
- **Révisions espacées** : rappel libre (« explique sans regarder »), puis quiz aux réponses mélangées.
- **Éditeur de TD** avec brouillon sauvegardé, indices un par un, solution et liste de vérifications.
- **Boutons Claude** (optionnels) : « Explique-moi autrement », question libre sur un module, correction de TD sans donner la solution, génération d'un nouveau module sur n'importe quel sujet.
- **Ajout de modules** : génération par Claude ou import JSON, dans un parcours existant ou un nouveau.
- **Responsive** : utilisable sur téléphone.

## Utiliser le dashboard

Trois façons de l'ouvrir :

| Où | Progression | Boutons Claude |
|---|---|---|
| **GitHub Pages** : https://fausatu.github.io/atelier-de-code/ | Dans le navigateur (localStorage), par appareil | Avec une clé API (voir plus bas) |
| **claude.ai** (artifact privé) | Sur le compte Claude, synchronisée entre appareils | Oui, sans clé |
| **En local** : ouvrir `index.html` dans un navigateur | Dans le navigateur | Avec une clé API |

`index.html` est une page autonome. Elle ne demande ni serveur, ni build, ni dépendance.

## Activer les boutons Claude

Hors de claude.ai, les boutons Claude utilisent ta propre clé API Anthropic :

1. Crée une clé sur https://console.anthropic.com/settings/keys (le compte doit avoir du crédit).
2. Dans le dashboard, ouvre **« Activer les boutons Claude »** en bas du menu.
3. Colle la clé, enregistre, puis clique sur **Tester la clé**.

- La clé est stockée **uniquement dans ton navigateur**, jamais dans ce dépôt.
- Les appels partent directement du navigateur vers `api.anthropic.com`.
- L'API est facturée à l'usage, séparément de l'abonnement Claude. Fixe une limite de dépense dans la console.
- N'enregistre pas ta clé sur un ordinateur partagé.

## Modifier ou ajouter du contenu

Le contenu est écrit en Python, un fichier par parcours, puis compilé dans `index.html`.

```bash
# 1. modifier un fichier de contenu, par exemple c_react.py
# 2. regénérer la page
python3 build.py
# 3. vérifier dans le navigateur, puis commit + push
git add -A
git commit -m "feat(react): ajoute un module sur useReducer"
git push
```

`build.py` vérifie que chaque module est complet : index de bonne réponse valide, TD avec énoncé, consignes, code de départ, indices, solution et vérifications.

**Format d'un module** (voir `common.py`) :

```python
M("react-reducer", "react", "useReducer", 15,
  "Objectif : ce que tu sauras faire.",
  "Le problème que ça résout.",
  ["Étape 1 du mécanisme", "Étape 2", "Étape 3", "Étape 4"],   # schéma « Comment ça marche »
  ["Point essentiel", "..."],                                   # L'essentiel
  ["Piège fréquent", "..."],                                    # Pièges
  code("tsx", r"""...exemple..."""),
  ["Ce qu'il faut remarquer", "..."],                           # notes de l'exemple
  [Q("Question ?", ["A", "B", "C", "D"], 1, "Explication")],    # quiz (index de la bonne réponse)
  TD("Titre du TD", "Énoncé", ["Consigne"], code("tsx", "// départ"),
     ["Indice 1", "Indice 2"], code("tsx", "// solution"), ["Vérification"]))
```

**Ajouter un parcours** : crée `c_monparcours.py` avec une liste `MODULES`, importe-le dans `build.py` et ajoute une entrée dans `TRACKS` (id, nom, couleur, description).

Depuis le dashboard, tu peux aussi ajouter des modules **sans toucher au code** (page « Ajouter un module »). Ils sont alors stockés avec ta progression, pas dans ce dépôt.

## Structure du projet

```
atelier-de-code/
├── index.html        # la page générée : c'est elle qui est publiée
├── template.html     # interface : HTML, CSS, JavaScript (sans framework)
├── build.py          # assemble template.html et le contenu, valide les modules
├── common.py         # helpers M(), Q(), TD(), code()
├── c_php.py          # PHP orienté objet
├── c_doctrine.py     # Doctrine ORM
├── c_dto.py          # DTO avec Symfony
├── c_arch.py         # Architecture
├── c_ddd.py          # DDD (bonus)
├── c_react.py        # React
├── c_data.py         # React : données & API
├── c_next.py         # Next.js
└── c_git.py          # Git & GitHub
```

Seules dépendances externes, chargées depuis un CDN : [highlight.js](https://highlightjs.org/) pour la coloration du code, et les polices Google Fonts.

## Contribuer

Les messages de commit suivent [Conventional Commits](https://www.conventionalcommits.org/fr/), comme enseigné dans le parcours Git :

```
feat(parcours): ajoute ...      nouveau module ou nouvelle fonctionnalité
fix(module): corrige ...        erreur dans un contenu ou un bug
docs: ...                       README, documentation
refactor: ...                   réorganisation sans changement visible
```

Une erreur dans un module ? Ouvre une issue en indiquant le parcours, le module et l'étape concernés.

# Contexte pour reprendre l'Atelier de code dans une nouvelle conversation

## Le projet
- Tableau de bord d'apprentissage en français pour Ana (étudiante, alternance / école).
- Dépôt : `fausatu/atelier-de-code` (ce dépôt).
- Artefact claude.ai : slug `daa22de5-df22-4847-beff-df94b2df5b0d`
  (https://claude.ai/artifact/TzsbQvAe876tEUsH4rbrqA). On publie `index.html` (+ les fichiers `vendor/` modifiés) avec `publish_files`.
- Elle écrit en français familier, veut que les tâches s'enchaînent sans devoir dire « continue », et qu'on lui dise le plan avant les gros changements.

## Construction et tests
- `python3 build.py` construit `index.html` à partir de `template.html` + les modules `c_*.py` (aides dans `common.py` : P, L, D/N/E, F, TD, RUN).
- Serveur local nécessaire pour valider : `(setsid nohup python3 -m http.server 8765 >/dev/null 2>&1 &)`.
- `python3 validate.py [parcours|module]` exécute chaque solution de TD contre ses tests ; `STARTER=1 python3 validate.py …` vérifie que chaque code de départ échoue. Dernier passage complet : 240/240.
- Types d'exécution : php (php-wasm), react, js, next, git (git-sim), term (term-sim, bash + PowerShell), vérification TypeScript (vendor/ts).
- Catégories de parcours : `GROUPS` dans build.py (methode, back, front, outils, + « perso »).
- Commits : terminer par les lignes d'attribution Co-Authored-By / Claude-Session données par le système.

## État actuel (16/11/2026)
15 parcours, 83 modules. Récemment : parcours Découper, TypeScript, Terminal ; numéros de ligne dans les éditeurs ;
tableau de bord « En cours » + page « Tous les parcours » (#parcours) ; barre latérale allégée (outils en icônes, « Mes parcours »).

## Calendrier (fait le 16/11)
Page `#calendrier` : mois par mois avec les jours école / entreprise / examens / rattrapages / férié (données de
`ecole/calendrier.json`, injectées par build.py dans `DATA.cal`), détail du jour, ajout d'événements perso
(rendu, examen, école, rendez-vous, perso) stockés dans `state.progress.agenda` (synchronisés comme la progression),
rendus cochables, « prochaines semaines d'école », « à venir ». Bandeau sur le tableau de bord, pastille dans la barre latérale.
Les futurs **rendus** de « Mes cours » doivent réutiliser `state.progress.agenda` (type "rendu") pour apparaître ici.

## Prochaines fonctionnalités validées par Ana (dans cet ordre)
1. **Notes par module** : panneau « Mes notes » sur chaque module (markdown, code coloré, tableaux).
2. **Espace « Mes cours » (école)** — PAS seulement du code : management de projet, anglais, UX/UI, etc.
   - Ana est en **MBA Développeur Full Stack (MyDigitalSchool, 2026-2028, en alternance)**. La liste complète des matières
     est dans `ecole/programme.json` (44 modules, M1/M2, UE, heures, ECTS, type, thèmes, évaluations, et lien vers les
     parcours de l'atelier dans `atelier`). S'en servir pour pré-remplir les matières (Ana confirme / supprime ensuite).
   - **Alternance** : `ecole/calendrier.json` = calendrier jour par jour (école / entreprise / examens / rattrapages / férié),
     les périodes regroupées et les dates clés (M1 : examens le 23/04/2027 ; M2 : examens 03-07/07/2028). Idées : afficher
     « cette semaine : école ou entreprise », planifier les révisions et les rendus selon les semaines d'école, et rattacher
     les cours aux jours d'école.
   - Grands rendus connus : My Digital Start-up (Go/No-go au printemps M1, livrables M2), rapport d'entreprise (M1),
     note d'intention du mémoire (début M2), workshops client 2 et 3, certificat MOOC ANSSI, Orthodidacte niveau 3, TOEIC.
   - Matières (couleur, semestre) → cours (date, étiquettes) avec : fichiers du prof (PDF/images affichés, PPTX/DOCX téléchargeables
     ou convertis), notes de cours, **liens vers des outils externes** (Canva, Miro, Figma, Notion, Google Drive/Docs/Slides, YouTube,
     Teams/Moodle… reconnus avec leur nom et un lien d'ouverture).
   - **Rendus** : projets / exercices à rendre avec date limite, statut (à faire, en cours, rendu, noté), consignes, liens, fichiers,
     check-list ; échéances visibles sur le tableau de bord.
   - Stockage en ligne via les capacités d'artefact `assets` (fichiers) et `db` (données) pour retrouver tout sur chaque appareil
     et pour que Claude puisse lire les cours (TD ou cartes à partir d'un chapitre).
3. **Cartes mémo** génériques (pas que code : vocabulaire d'anglais, définitions de management…) : cartes par parcours,
   cartes générées depuis une fiche de cours ou un PDF (capacité `sample`), cartes créées à la main ; intégrées aux révisions
   (même rythme espacé).
4. **Projet fil rouge** : parcours qui relie découpage → PHP/API → React/formulaire → Git → terminal. À discuter avec Ana :
   le caler sur son vrai projet d'école **My Digital Start-up** plutôt qu'une boutique fictive.

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
- `python3 validate.py [parcours|module]` exécute chaque solution de TD contre ses tests ; `STARTER=1 python3 validate.py …` vérifie que chaque code de départ échoue. Dernier passage complet : 240/240 (16/11, après les notes).
- Types d'exécution : php (php-wasm), react, js, next, git (git-sim), term (term-sim, bash + PowerShell), vérification TypeScript (vendor/ts).
- Catégories de parcours : `GROUPS` dans build.py (methode, back, front, outils, + « perso »).
- **Formulaires** : claude.ai affiche l'artefact dans un cadre sandbox SANS `allow-forms` → l'événement `submit` n'est jamais
  envoyé. Tous les `form[data-form]` passent par `handleForm(f, submitter)`, appelé par un écouteur de clic (bouton d'envoi) et de
  touche Entrée (`runForm`, qui vérifie aussi les champs `required`). Ne jamais compter sur `submit` ni `requestSubmit()`.
  Test : servir une page avec `<iframe sandbox="allow-scripts allow-same-origin" src="index.html">`.
- Commits : terminer par les lignes d'attribution Co-Authored-By / Claude-Session données par le système.

## État actuel (16/11/2026)
15 parcours, 83 modules. Récemment : Mes cours (matières/cours/rendus), notes par module, bouton flottant notes + questions ; parcours Découper, TypeScript, Terminal ; numéros de ligne dans les éditeurs ;
tableau de bord « En cours » + page « Tous les parcours » (#parcours) ; barre latérale allégée (outils en icônes, « Mes parcours »).

## Calendrier (fait le 16/11)
Page `#calendrier` : mois par mois avec les jours école / entreprise / examens / rattrapages / férié (données de
`ecole/calendrier.json`, injectées par build.py dans `DATA.cal`), détail du jour, ajout d'événements perso
(rendu, examen, école, rendez-vous, perso) stockés dans `state.progress.agenda` (synchronisés comme la progression),
rendus cochables, « prochaines semaines d'école », « à venir ». Bandeau sur le tableau de bord, pastille dans la barre latérale.
Les futurs **rendus** de « Mes cours » doivent réutiliser `state.progress.agenda` (type "rendu") pour apparaître ici.

## Mes notes (fait le 16/11)
Une note markdown par module, stockée dans `state.progress.notes[moduleId] = { text, ts, created }` (synchronisée comme la
progression ; à la fusion GitHub, la version la plus récente gagne). Panneau latéral `#npanel` (bouton flottant crayon en bas à droite →
menu « Mes notes » / « Une question » (`fabSetOpen`), ou **Alt+N**, Échap pour fermer ; sur écran ≥ 1280 px le contenu se décale), modes Écrire / Aperçu (Ctrl+Entrée),
barre d'outils (titre, gras Ctrl+B, code Ctrl+E, bloc de code avec le langage du parcours, liste, case, tableau, citation, lien Ctrl+K,
« Citer » = passage surligné du cours), suite automatique des listes avec Entrée, bouton « Faire une fiche avec Claude » (capacité
`sample`, proposition à ajouter ou jeter). Page `#notes` (icône dans la barre latérale) : notes par parcours, recherche, copier une /
toutes les notes en markdown, « Modifier » rouvre le module avec le panneau. Repère « notes » sur les modules dans la vue parcours.
`md()` gère maintenant liens `[texte](https://…)`, `~~barré~~`, cases `- [ ]` / `- [x]` et citations sur plusieurs lignes
(profite aussi aux leçons). Fonctions : `notesMap`, `noteOf`, `nSetOpen`, `renderN`, `nInsert`, `nAi`, `viewNotes`.
Idée pour plus tard : les cartes mémo (point 3) pourront être générées depuis une note.

## Mes cours, étape 1 (fait le 16/11) : matières, cours, rendus
- Route `#cours` (lien « Mes cours » dans la barre latérale, pastille = rendus dans les 14 jours), `#mat-<id>`, `#c-<id>` (cours), `#r-<id>` (rendu).
- Premier passage : un bouton « Préparer mes matières » crée tout (+ lien « Choisir une par une » = ancien écran à cases). Cartes de matière = liens
  avec icône par type (`TYPE_ICONS`), en-tête « héros » sur la page matière, cours avec pastille de date.
- (ancien) écran de préparation à partir de `ecole/programme.json` (injecté par build.py dans `DATA.programme`) ; Ana coche
  ses matières, + option « grands rendus connus » (`KNOWN_RENDUS`, date à définir).
- **Stockage** : `state.ecole = { matieres, cours, deleted, setup }` → localStorage + doc db `data/users/<uid>/ecole` (`ecoleWriter`)
  + export/GitHub (`snapshotData`, fusion par id avec `ts`, `deleted` = suppressions). Les **rendus** restent dans
  `state.progress.agenda` (type "rendu") avec `statut` (a_faire/en_cours/rendu/note), `fait` synchronisé, `matiere`, `consignes` (md),
  `checklist`, `liens`, `resultat`, `date` (peut être null = « date à définir ») ; le calendrier les affiche et les relie à `#r-<id>`.
- Matière : couleur (par type par défaut), année, thèmes, évaluation, liens vers les parcours de l'atelier (`ATELIER_ALIAS`).
- Cours : titre, date facultative, étiquettes, liens d'outils reconnus (`TOOLS` : Canva, Miro, Figma, Notion, Google…, pastille
  colorée avec initiales, pas de logos), notes markdown (`mdEditor`, même barre d'outils que Mes notes ; `nInsert` accepte une cible).
- **Emploi du temps (fait le 16/11)** : Ana a donné son lien iCal Pronote/Hyperplanning (lien personnel avec jeton : ne PAS le mettre
  dans le dépôt, il est public). Le réseau du conteneur ne joint pas pronote-campus.net → lecture via le navigateur intégré
  (fetch depuis une page du domaine), puis `ecole/edt.json` = séances regroupées par matière et par jour
  `{m, d, c:[[début,fin]], s:salles, p:profs, t:contenus}` (sans son nom ni sa date de naissance). Pronote ne donne que jusqu'au
  02/01/2027 → à réimporter plus tard. `DATA.edt` → `ensureEdt()` / `syncEdt()` crée un cours par (matière, jour) avec
  `edtKey`, `creneaux`, `salles`, `profs`, `contenu` ; rattachement via `EDT_MAP` (libellé Pronote → nom du programme, champ `prog`
  des matières), sinon création d'une matière. Réimport : met à jour horaires/salles/profs/contenu, garde titre/notes/liens/étiquettes ;
  séance disparue → supprimée si vide, sinon `annule`. Cours supprimé par Ana → `edtIgnore`. Ana peut aussi importer elle-même un
  `.ics` (carte « Emploi du temps » en bas de #cours, `parseIcs`). Cours visibles dans le calendrier (type "cours") et
  « Prochains cours » en haut de #cours.

## Barre latérale repliable + « Ma semaine » (fait le 16/11)
- Bouton dans l'en-tête de la barre latérale (et Alt+S) → `body.side-off` (mémorisé dans localStorage `atelier-side-off`),
  bouton flottant en haut à gauche pour la rouvrir ; sur mobile le même bouton ferme le menu.
- Tableau de bord : refait le 16/11, voir « Style » ci-dessous.

## Fichiers du prof (fait le 16/11)
- Capacité `assets` déclarée (`{db, sample, user, assets}`). `assetsApi` (null hors claude.ai → message). Carte « Fichiers » sur
  chaque cours et rendu (`filesCard`) : glisser-déposer ou sélecteur, `o.fichiers = [{id, nom, type, taille, ajoute, extrait?, orig?, info?}]`.
- Types acceptés par la plateforme : PDF, images, vidéos, texte (20 Mo). **PPTX/DOCX refusés par la plateforme** → texte extrait dans le
  navigateur (`officeToMarkdown` : petit lecteur zip + DecompressionStream ; diapos + notes, titres/listes Word) et stocké en `.md`.
- Visionneuse `#viewer` : PDF rendu page par page avec pdf.js 3.11.174 embarqué (`vendor/pdfjs/`, à publier avec la page), images,
  vidéos, texte/markdown. Suppression = `assets.delete` après confirmation.
- Publier : `index.html` + `vendor/pdfjs/*` si modifiés.
- **Version GitHub Pages** (Ana l'utilise) : pas de capacité `assets` → fichiers rangés dans un **dépôt privé** d'Ana
  (`atelier-fichiers` par défaut) via l'API Contents avec un jeton fine-grained limité à ce dépôt (Contents read/write), configuré
  sur #synchro (carte « Fichiers de cours sur GitHub », localStorage `atelier-fichiers-gh`, `ghfConnect` refuse un dépôt public).
  Chemins `fichiers/AAAA-MM/<id>-<nom>` ; PPTX/DOCX gardés en original + texte extrait en `-texte.md` (`f.texte`).
  Chaque fichier a `src` ("claude" | "github") : chaque version n'affiche que les siens (`fileReachable`), l'autre est indiqué.

## Style (retour d'Ana du 16/11)
- **Pas de bordure de couleur sur le côté (ou en haut) des cartes** : elle trouve que « ça fait très IA ». La couleur passe par de petits
  éléments (point `.dot`, icône teintée, pastille de date, fond légèrement teinté), cartes neutres avec bordure 1 px et ombre au survol.
- Tableau de bord **aéré** : sections titrées (« À venir », « Apprentissage », « Activité ») avec beaucoup d'espace (`.wrap.home`,
  `.home-sec`, `.home-grid2`, `.home-card` 24 px de marge) ; « À venir » = agenda par jour (cours + rendus, `homeAgenda`) et
  « Cette semaine » (`homeWeek` : 5 jours, légende, prochaines semaines d'école, prochaine école / examens).

## Prochaines fonctionnalités validées par Ana (dans cet ordre)
1. ~~Notes par module~~ : fait (voir ci-dessus).
2. **Espace « Mes cours » (école)** — étape 1 faite (voir ci-dessus). Étape 2 faite aussi (fichiers, Ma semaine, emploi du temps ; réimporter l'emploi du temps après le 02/01/2027). Idée suivante possible : TD / cartes générés par Claude depuis les fichiers et notes d'un cours. — PAS seulement du code : management de projet, anglais, UX/UI, etc.
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

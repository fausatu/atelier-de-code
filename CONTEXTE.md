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
- `python3 validate.py [parcours|module]` exécute chaque solution de TD contre ses tests ; `STARTER=1 python3 validate.py …` vérifie que chaque code de départ échoue. Dernier passage complet : 276/276 (17/11, après fil rouge 7-9, axios, Organiser).
- Types d'exécution : php (php-wasm), react, js, next, git (git-sim), term (term-sim, bash + PowerShell), vérification TypeScript (vendor/ts).
- Catégories de parcours : `GROUPS` dans build.py (methode, back, front, outils, + « perso »).
- **Formulaires** : claude.ai affiche l'artefact dans un cadre sandbox SANS `allow-forms` → l'événement `submit` n'est jamais
  envoyé. Tous les `form[data-form]` passent par `handleForm(f, submitter)`, appelé par un écouteur de clic (bouton d'envoi) et de
  touche Entrée (`runForm`, qui vérifie aussi les champs `required`). Ne jamais compter sur `submit` ni `requestSubmit()`.
  Test : servir une page avec `<iframe sandbox="allow-scripts allow-same-origin" src="index.html">`.
- Commits : terminer par les lignes d'attribution Co-Authored-By / Claude-Session données par le système.

## État actuel (17/11/2026)
17 parcours, 95 modules. Récemment : éditeur avec paires auto, complétion et aide aux paramètres, espace En entreprise (journal, missions, documents, captures Ctrl+V), règle « expliquer avant d'utiliser » (encadré auto), module axios, parcours Organiser un projet React, fil rouge complet (9 modules), mémo des méthodes (#methodes, méthodes cliquables dans le code), Mes cours (matières/cours/rendus), notes par module, bouton flottant notes + questions ; parcours Découper, TypeScript, Terminal ; numéros de ligne dans les éditeurs ;
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

## Cartes mémo + révisions variées (fait le 16/11)
Demande d'Ana : **les questions ne doivent pas être les mêmes à chaque révision.**
- **Modules** : `modulePool(m)` = quiz + 2 QCM par mot de `prereq` (définition ↔ terme, mauvaises réponses prises dans les autres mots
  du parcours) + questions générées par Claude (`progress.modules[id].genQ`, 15 max). `pickModuleQuestions` prend les 3 vues il y a le
  plus longtemps (`seenQ`). Après chaque module révisé, `genModuleQuestions` demande 3 nouvelles questions à Claude pour la fois suivante.
- **Cartes** : `state.cartes = { items, deleted }` (localStorage + doc db `.../cartes` + export/GitHub, fusion par id/ts).
  Carte = notion `{id, deck, recto, verso, exemple, variantes[], box, due, seen[], source}` ; paquets `mat:<id>`, `perso`, `track:<id>`.
  Forme choisie à chaque passage (`cardFormats` / `pickFormat`, la moins récemment vue) : def, terme, qcm, qcmt (QCM inversé), trou,
  vf, et `var:<id>` = questions de Claude. Quand une carte a épuisé ses questions de Claude, `refillVariants` en redemande 2 (par lots de 4).
  Même rythme `INTERVALS` ; « S'entraîner » ne touche pas au planning.
- Pages : `#cartes` (paquets), `#paquet-mat-<id>` (cartes, ajout à la main, génération depuis un cours ou un texte collé),
  `#cartes-revision`. Génération depuis un cours (`coursSourceText`) : notes + programme de séance + texte des fichiers (PPTX/DOCX
  extraits, PDF via pdf.js `getTextContent`). Carte « Cartes mémo » sur chaque cours ; compteur Révisions = modules + cartes.
- Attention : un ACTIONS `genSave` existait déjà (génération de modules) → les actions des cartes s'appellent `cg*` / `c*`.

## Projet fil rouge « Bobine » (commencé le 16/11)
- Choix d'Ana : PAS My Digital Start-up (en groupe, pas pour maintenant) → un **site de streaming**, « Bobine » (nom provisoire),
  avec de courts films libres de droits (films d'animation de la Blender Foundation).
- Parcours `fil` (groupe « Projet », couleur `coral`, badge ▶), fichier `c_fil.py`. Fait : modules 1 à 3 (9 TD, 9/9 + départs qui échouent) :
  1. `fil-decoupe` Du cahier des charges aux tranches (TD js : scénarios de reprise, `peutVoir` contrôle parental, `etatVisionnage`)
  2. `fil-modele` Le modèle de données (Doctrine simulé : Film + enum Genre, Série/Épisode cascade+orphelins, Compte/Profil/enum Forfait)
  3. `fil-api` L'API du catalogue (Symfony simulé : `CatalogueFiltres` + `FilmCard`, fiche + contrôle parental 403/404, `/api/accueil` en rangées)
- Modules 7 à 9 faits le 17/11 (`c_fil3.py`, 27 TD au total pour le parcours, tous OK + départs qui échouent) :
  7. `fil-formulaire` RHF + zod (`versApi`, 422 → `setError(champ)`, 409 → `root.serveur`, `invalidateQueries`), renommer avec `isDirty`.
  8. `fil-git` branche par tranche, Conventional Commits, `gh pr create`, rebase + `--force-with-lease`, conflit, `gh pr merge --squash`.
  9. `fil-lancer` back Symfony + front Vite, proxy, `.env`/`.env.local`, port occupé (`lsof`, `kill`), script `dev.sh`.
- Le Doctrine simulé ne gère pas ManyToMany (genre = enum ; Ma liste devra être une entité `ElementListe` ManyToOne×2).
- Modules 4 à 6 faits (`c_fil2.py`, 18 TD au total pour le parcours, 18/18 + départs qui échouent) :
  4. `fil-profils` Créer et supprimer un profil (`#[MapRequestPayload]` NouveauProfil, `#[CurrentUser] Compte`, exceptions
     `#[WithHttpStatus(409)]`, DELETE 404 hors compte / 409 dernier adulte, PATCH forfait)
  5. `fil-reprise` Reprendre la lecture (Visionnage, `PUT` idempotent, numéro d'`envoi` contre les requêtes en retard,
     `Horloge` injectée, `GET /api/continuer`)
  6. `fil-front` Le front React (types du contrat, catalogue `useQuery(['films', { q, genre }])`, fiche 403/404,
     classe `Sauvegarde` toutes les 10 s + pause, `Lecteur` « Reprendre à 6:00 »). API simulée : `BOBINE_API`.
- **Modules 7 à 9 faits le 17/11** (`c_fil3.py`, voir plus bas). Ancienne description : 7. formulaires (créer/modifier un profil avec React Hook Form + zod, afficher les 422/409 de l'API),
  8. Git (une branche par tranche, Conventional Commits, PR), 9. terminal (lancer back + front, .env, ports occupés).

## Mémo des méthodes (fait le 16/11)
- Demande d'Ana : « plein de méthodes, je sais pas à quoi ça sert ni ce que ça prend en paramètre ».
- `methodes.py` : 145 fiches `E(id, cat, nom, cles, sig, desc, params, retour, ex, res, piege)`, familles `CATS`
  (php, doctrine, symfony, js, react, donnees, formulaires, next). Injecté dans `DATA.methodes` par `build.py`.
  Clés de repérage : PHP `fn:count`, `->persist`, `::from`, `new:DateTimeImmutable`, `#Route`, `Assert:NotBlank` ;
  JS `fn:useState`, `.map`, `Math.round`, `api.get`, `z.object`, `new:Set`. Concepts sans clé (`cles=[]`) : seulement dans la page.
- `linkMethods(root)` (appelé à la fin de `highlight`) souligne en pointillés (`.mref`) les noms connus dans les blocs de code
  en lecture seule (pas dans les éditeurs `.ed-wrap`) → clic / Entrée = bulle `#mpop` (signature, paramètres, retour, exemple +
  résultat, piège, « Vu dans N modules » calculé par `memoSeen`), Échap / clic dehors pour fermer.
- Page `#methodes` (icône livre dans la barre d'outils) : recherche `#m-filter`, puces de famille, fiches en `<details>`.
  « Demander à Claude » (bloc ai-only) pour une méthode absente → « Garder dans Mes ajouts » (`state.progress.memoPerso`).
- Pour ajouter une méthode : une entrée `E(...)` dans `methodes.py` (vérifier qu'aucune clé n'est en double).

## RÈGLE PÉDAGOGIQUE : expliquer AVANT d'utiliser (demande d'Ana du 17/11)
- Ana : « tu utilises des notions avant de les avoir expliquées… ne mets pas un exemple puis une petite ligne d'explication en bas ».
- **Pour tout nouveau contenu** : chaque notion, fonction ou syntaxe nouvelle est expliquée dans le texte **avant** le bloc de code
  qui l'utilise (liste « les pièces du code » puis le code). Jamais une leçon qui commence par un bloc de code sans introduction.
- `explique.py` (appelé par `build.py`) calcule pour chaque module `m["croiser"]` : les fiches du mémo utilisées dans son code
  (leçons, exemple, TD + solutions) et pas encore expliquées (ni avant dans le module, ni dans un module précédent du parcours ou
  d'un parcours prérequis : `DEPS`, `MODULE_DEPS`). Affiché en haut de « Comprendre » : encadré « Ce que tu vas croiser dans le code »
  (`croiserBlock`). Une « mention » = le nom entre backticks dans le texte (ou `MOTS` pour les notions de syntaxe).
- `python3 explique.py [parcours|module]` liste aussi les cas « expliqué APRÈS » (7 restants : exemples/TD, couverts par l'encadré).
  À lancer après chaque nouveau module : 0 cas en leçon.
- Onglet Exemple : « Ce que tu vas voir dans ce code » (les notes) est AU-DESSUS du code.
- Fiches de notions ajoutées au mémo avec des clés `re:` (regex) : `?.`/`??`, déstructuration, fonction fléchée, template literal,
  spread, async/await, instanceof, `??`/`?->` PHP. Les génériques `useState<T>(` / `api.get<T>(` sont reconnus.

## Module axios (fait le 17/11)
- Ana utilise **axios + React Query** (pas fetch). `c_axios.py` : module `data-axios` « axios de A à Z », inséré en 2e position du
  parcours Données (build.py : `DATA_[:1] + AXIOS + DATA_[1:]`). Leçons : rôle axios vs React Query, `axios.create`, les 5 verbes et
  `res.data`, erreurs (`isAxiosError`, `err.response`), intercepteurs, `queryFn`. 3 TD (client + fonctions, `messageErreur`, intercepteurs jeton/401).

## Parcours « Organiser un projet React » (fait le 17/11)
- `c_orga.py`, track `orga` (groupe front, couleur `moss` ajoutée dans COLORS / `--t-moss`), entre Données et Formulaires.
  1. `orga-dossiers` : ranger par fonctionnalité (`app/`, `features/<nom>/`, `shared/`), « un fichier commence là où il est utilisé »,
     `index.ts` porte d'entrée, règles d'import. TD : réorganiser (term-sim, mkdir/mv), ajouter « Ma liste », vérificateur d'imports (js).
  2. `orga-props` : quand passer une prop ; remonter le state, React Query (même hook partout), composition (`children`/`barre`),
     Context (`ProfilActif`). TD react : remonter le state, composition, Context.

## Simulateur de terminal : serveurs de dev (ajouté le 17/11, vendor/term-sim/term-sim.js)
- `symfony server:start [-d] [--port=N]` (projet = dossier avec composer.json + bin/console ; port occupé → port suivant + warning),
  `symfony server:stop|server:list`, `php -S hôte:port -t dossier`, `vite` (via `npm run dev` ; lit `vite.config.ts` : `port`,
  `strictPort`, proxy `'/api': 'http://localhost:8000'`), `curl` avec chemin + proxy Vite → back. L'API répond selon `.env`/`.env.local`
  (`DATABASE_URL` avec `!ChangeMe!` → erreur « Access denied »). Tests : `term.procs()` (`kind`: symfony|php|vite, `port`), `term.lastCurl` (`{ok, via}`).

## En entreprise (fait le 17/11)
- Route `#entreprise` (lien « En entreprise » dans la barre latérale, compteur = jours en entreprise sans note sur 10 jours),
  `#j-<id>` (entrée de journal), `#ms-<id>` (mission). Code : bloc « En entreprise » de template.html (`ent()`, `viewEntreprise`,
  `viewJour`, `viewMission`, `entNotions`, `notionModules`, `entNudge`).
- Données dans le document `ecole` (privé, jamais dans le dépôt) : `ecole.entreprise` (infos : nom, poste, service, tuteur,
  tuteurContact, stack, debut, fin, liens, fichiers = Documents, notionsOk), `ecole.journal` [{id, date, mission, fait, appris,
  bloque, notions, fichiers, liens, ts}], `ecole.missions` [{id, titre, statut en_cours|livree|en_pause|abandonnee, debut, fin,
  stack, notions, contexte, realise, difficultes, appris, liens, fichiers, ts}]. Fusion par id/ts comme matières et cours.
- Kinds `jour`, `mission`, `entreprise` (id `infos`) branchés sur `ecObj` : `filesCard`, `uploadFiles`, `linkForm`, `mdEditor`,
  `data-ec` marchent tels quels.
- Tableau de bord : `entNudge()` propose de noter les jours « entreprise » du calendrier sans entrée.
- Notions croisées : agrégées depuis journal + missions ; `notionModules` cherche les modules (titre, objectif, prérequis,
  leçons) et la fiche du mémo ; sinon « Ajouter à Mes questions » (`qSave`). « Je maîtrise » → `entreprise.notionsOk`.
- Jeton GitHub des fichiers (version Pages) : un 401 met `ghf.expired` → bandeau dans `filesCard` + formulaire « Remplacer le jeton »
  dans Synchroniser (garde l'ancien si le nouveau est refusé). Les consignes disent de choisir une expiration Custom (fin d'alternance),
  sinon GitHub met 30 jours (cas d'Ana le 17/11 : « jeton GitHub refusé »).
- **Ctrl+V d'une capture d'écran** : écouteur `paste` global → envoie les fichiers collés dans la 1re zone `[data-drop]` de la page
  (journal, mission, documents, cours, rendus), renommés `capture-AAAA-MM-JJ-HHhMM.png`.
- Idées suivantes (proposées à Ana le 17/11, pas encore faites) : suivi tuteur (points d'étape, objectifs, prépa des questions),
  rapport d'entreprise et mémoire (plan + aide à la rédaction par Claude depuis le journal et les missions, problématiques pour la
  note d'intention), glossaire de l'entreprise (→ cartes mémo), grille de compétences. Ana n'a pas encore dit quel type d'entreprise.

## Éditeur comme VS Code (fait le 17/11)
- Bloc « Éditeur : paires automatiques… » de template.html : `edKeydown` (appelé par le keydown des `textarea.editor`) et
  `edAfterInput` (appelé par leur input). Les insertions passent par `edIns` (`execCommand("insertText")` → Ctrl+Z marche).
- Paires auto (AltGr = Ctrl+Alt sous Windows et Option sur Mac acceptés, pour { [ en AZERTY) `() [] {} '' "" \`\`` (pas devant un mot, pas dans une chaîne), sauter le fermant, Retour arrière entre une paire
  vide, entourer une sélection ; Entrée garde l'indentation (+4 après `{ [ (`, bloc ouvert entre `{}`), `}` désindente ;
  Tab/Maj+Tab sur plusieurs lignes ; Ctrl+/ commente ; `>` ferme la balise JSX/HTML (`.tsx/.jsx/.html`).
- Complétion (popup `#ed-ac`, ↑↓ Entrée/Tab Échap, Ctrl+Espace pour forcer) :
  - TS/JS : vrai service de langage TypeScript (`vendor/ts/typescript.js` + `libs.js` chargés au 1er focus, ~4,6 Mo en cache)
    sur les fichiers du même TD, + **types simplifiés en français** pour axios, TanStack Query, zod, React Hook Form,
    @hookform/resolvers/zod dans `vendor/ts/atelier-types.js` (sources : `declare module` ; régénérer ce fichier si on les modifie).
    Si TS ne trouve rien après un `.`, repli sur le mémo. Fiche du mémo (français) prioritaire sur la doc anglaise de lib.d.ts.
  - PHP : méthodes/propriétés/classes/fonctions déclarées dans les fichiers, `$variables`, fiches du mémo (`fn:`, `->`, `::`, `#`), mots-clés.
- Popup de complétion compacte (7 lignes, doc courte : signature + 1re phrase) à la demande d'Ana.
- Survol (`#ed-hover`, 350 ms) : TS `getQuickInfoAtPosition` (type + doc, fiche du mémo en français si elle existe) ; PHP : déclaration
  trouvée dans les fichiers (fonction, propriété, classe) ou fiche du mémo. `edPosAt` convertit la souris en position dans le texte.
- **Erreurs en direct** (650 ms après la frappe) : calque `.ed-dg` sous le texte (vagues rouges = erreurs, orange = avertissements),
  numéros de ligne colorés, barre `.ed-probs` sous l'éditeur (clic = aller à la ligne), message au survol, paire de parenthèses
  surlignée (`.bm`). PHP/CSS/JSON : `edScan` maison (chaînes, commentaires, heredoc, paires, `;` dans un `[`/`(` ouvert, « ; »
  probablement oublié = `edPhpSemicolons`), une seule cause à la fois. TS/JS : diagnostics du service TypeScript en français ;
  erreurs de types complètes seulement dans le parcours TypeScript / TD `typecheck`, ailleurs seulement les sûres (`SURES`), car
  les types simplifiés des bibliothèques feraient de fausses alertes. Vérifié : 0 fausse alerte sur les 190 solutions TS et 485 fichiers PHP.
- Aide aux paramètres (`#ed-sig`) à `(` et `,` : TS `getSignatureHelpItems`, sinon signature du mémo / de la fonction du fichier,
  paramètre courant en gras + explication du mémo. `memoFor(name, fam, member, recv)` exige le bon objet pour les clés `Math.min`, `api.get`…

## Position dans un module (17/11)
- `state.ui.step` (onglet Comprendre/Exemple/Quiz/TD) et `state.ui.level` (niveau de TD) sont gardés dans `localStorage["atelier-position"]`
  (`uiPos`, `saveUiPos`) : après un rechargement, on retombe sur le même onglet et le même TD.

## Erreurs expliquées en français (17/11)
- `frErreur(text)` + table `ERR_FR` (template.html, avant `runJsFrame`) : coupe le texte anglais de Babel (« Add @babel… »)
  et ajoute une ligne « → … » en français (console et erreurs de tests). Cas vécu : `?? throw` (habitude PHP) en TypeScript.
  Ajouter une ligne à `ERR_FR` pour chaque nouvelle erreur qu'Ana ne comprend pas.

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
3. ~~Cartes mémo~~ : fait (voir ci-dessus). Idée : cartes depuis un module de l'atelier (paquet `track:`), import de vocabulaire.
   Ancienne description : **Cartes mémo** génériques (pas que code : vocabulaire d'anglais, définitions de management…) : cartes par parcours,
   cartes générées depuis une fiche de cours ou un PDF (capacité `sample`), cartes créées à la main ; intégrées aux révisions
   (même rythme espacé).
4. **Projet fil rouge** : commencé (voir « Projet fil rouge Bobine »). Ancienne note : parcours qui relie découpage → PHP/API → React/formulaire → Git → terminal. À discuter avec Ana :
   le caler sur son vrai projet d'école **My Digital Start-up** plutôt qu'une boutique fictive.

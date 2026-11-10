from common import M, Q, TD, code

T = "git"

MODULES = [
M("git-modele", T, "Comment Git fonctionne vraiment", 15,
  "Comprendre ce qu'est un commit, une branche et HEAD : tout le reste en découle.",
  "Rebase, reset, revert paraissent magiques tant qu'on pense « Git enregistre des fichiers ». En réalité Git enregistre des photos du projet reliées entre elles, et les branches ne sont que des étiquettes collées dessus. Une fois ça compris, chaque commande devient « je déplace une étiquette » ou « je crée une nouvelle photo ».",
  ["Tu modifies des fichiers dans ton **dossier de travail**",
   "`git add` les met dans la **zone de préparation** (staging) : « ces changements iront dans la prochaine photo »",
   "`git commit` prend une **photo** (snapshot) du projet, avec un identifiant unique (`a1b2c3d`) et un lien vers la photo **parente**",
   "La **branche** est une étiquette qui pointe vers le dernier commit ; **HEAD** indique où tu te trouves"],
  ["Un commit = une photo complète du projet + son parent + auteur + message. Il est **immuable** : on ne modifie jamais un commit, on en crée un nouveau.",
   "Les commits forment une **chaîne** : chacun pointe vers son parent. L'historique, c'est cette chaîne.",
   "Une branche (`main`, `feature/login`) est juste une **étiquette mobile** : à chaque commit, elle avance sur le nouveau.",
   "**HEAD** = « tu es ici ». D'habitude il pointe vers une branche, qui pointe vers un commit.",
   "`git log --oneline --graph --all` dessine tout ça dans le terminal : utilise-le tout le temps."],
  ["Croire qu'une branche est une copie du code : c'est une étiquette de quelques octets.",
   "Faire `git add .` sans regarder : vérifie toujours avec `git status` et `git diff --staged`."],
  code("plaintext", r"""
  DOSSIER DE TRAVAIL  --git add-->  ZONE DE PRÉPARATION  --git commit-->  HISTORIQUE
  (tes fichiers)                    (staging / index)                     (commits)


  Historique : chaque commit pointe vers son parent

      A <--- B <--- C <--- D          A, B, C, D = commits (photos)
                           ^
                          main        main = étiquette sur D
                           ^
                          HEAD        HEAD = "tu es ici"

  Après un nouveau commit E :

      A <--- B <--- C <--- D <--- E
                                  ^
                                 main  (l'étiquette a avancé toute seule)
                                  ^
                                 HEAD

  Créer une branche = créer une nouvelle étiquette sur le même commit :

      git switch -c feature
      A <--- B <--- C <--- D <--- E
                                  ^
                             main, feature
                                  ^
                                 HEAD -> feature
"""),
  ["Les flèches vont de l'enfant vers le parent : un commit connaît son passé, pas son futur.",
   "`git switch -c feature` ne copie rien : il pose une étiquette.",
   "Toutes les commandes avancées (rebase, reset…) déplacent des étiquettes ou créent de nouveaux commits."],
  [Q("Qu'est-ce qu'une branche dans Git ?",
     ["Une copie complète du projet", "Une étiquette qui pointe vers un commit", "Un dossier", "Un serveur"], 1,
     "C'est pour ça que créer une branche est instantané."),
   Q("Que fait `git add` ?",
     ["Envoie sur GitHub", "Prépare des changements pour le prochain commit", "Crée un commit", "Crée une branche"], 1,
     "Le staging permet de choisir précisément ce qui ira dans le commit."),
   Q("Que désigne HEAD ?",
     ["Le premier commit", "La position actuelle (la branche ou le commit où tu es)", "La branche distante", "Le dernier push"], 1,
     "« Tu es ici » sur la carte de l'historique.")],
  TD("Observer l'historique",
     "Dans un dossier vide, crée un petit dépôt et observe ce que fait chaque commande.",
     ["Crée 3 commits sur `main` (un fichier modifié à chaque fois)",
      "Crée une branche `essai`, fais-y 2 commits",
      "Reviens sur `main`, fais 1 commit",
      "Après chaque étape, lance `git log --oneline --graph --all` et dessine l'arbre sur papier",
      "Note ce que pointe HEAD à chaque fois (`cat .git/HEAD`)"],
     code("bash", r"""
mkdir atelier-git && cd atelier-git
git init -b main
echo "v1" > notes.txt
git add notes.txt
git commit -m "premier commit"
# à toi : continue
git log --oneline --graph --all
"""),
     ["`git switch -c essai` crée la branche et s'y place ; `git switch main` revient.",
      "`cat .git/HEAD` affiche `ref: refs/heads/main` : HEAD pointe vers la branche, pas directement vers un commit."],
     code("bash", r"""
git init -b main
echo "v1" > notes.txt && git add . && git commit -m "c1"
echo "v2" >> notes.txt && git commit -am "c2"
echo "v3" >> notes.txt && git commit -am "c3"

git switch -c essai
echo "e1" > essai.txt && git add . && git commit -m "e1"
echo "e2" >> essai.txt && git commit -am "e2"

git switch main
echo "v4" >> notes.txt && git commit -am "c4"

git log --oneline --graph --all
# * 9f1e2d3 (HEAD -> main) c4
# | * 7a6b5c4 (essai) e2
# | * 3d2c1b0 e1
# |/
# * 1a2b3c4 c3
# * ...  c2
# * ...  c1
# Les deux branches partent de c3 : elles ont "divergé".
"""),
     ["Ton dessin correspond à la sortie de `git log --graph`",
      "Tu sais expliquer pourquoi `essai.txt` disparaît quand tu reviens sur `main`"])),

M("git-merge", T, "Branches, merge & conflits", 15,
  "Fusionner une branche et résoudre un conflit sans paniquer.",
  "Travailler à plusieurs, ou sur plusieurs choses à la fois, demande des branches. Le moment délicat, c'est de les réunir.",
  ["Tu crées une branche pour une tâche (`feature/panier`)",
   "Tu y fais tes commits pendant que `main` avance de son côté",
   "`git merge feature/panier` (depuis `main`) **réunit** les deux histoires",
   "Si les deux ont modifié **les mêmes lignes**, Git s'arrête : **conflit** à résoudre à la main"],
  ["**Fast-forward** : si `main` n'a pas bougé, Git avance simplement l'étiquette. Aucun nouveau commit.",
   "**Merge commit** : si les deux ont avancé, Git crée un commit avec **deux parents**.",
   "Un conflit ressemble à `<<<<<<<`, `=======`, `>>>>>>>` dans le fichier : tu choisis le bon contenu, tu supprimes les marqueurs, `git add`, `git commit`.",
   "`git merge --abort` annule une fusion en cours si tu es perdu.",
   "Ton éditeur (VS Code, PhpStorm) affiche les conflits avec des boutons « Accepter l'actuel / l'entrant / les deux »."],
  ["Laisser des marqueurs `<<<<<<<` dans le code et commiter.",
   "Des branches qui vivent des semaines : plus elles sont longues, plus les conflits sont gros. Fusionne souvent."],
  code("plaintext", r"""
  AVANT                                  APRÈS  git switch main && git merge feature

      A --- B --- C   main                   A --- B --- C ------- M   main
             \                                      \             /
              D --- E   feature                      D --- E -----     feature

  M = merge commit (2 parents : C et E)


  CONFLIT dans prix.php :

  <<<<<<< HEAD
  const TVA = 0.20;          <- version de main (là où tu es)
  =======
  const TVA = 0.055;         <- version de feature (ce que tu fusionnes)
  >>>>>>> feature

  Résolution :
    1. choisir (ou combiner), supprimer les 3 lignes de marqueurs
    2. git add prix.php
    3. git commit            (Git propose un message de merge)
"""),
  ["HEAD dans le conflit = la branche où tu es (ici `main`).",
   "Un conflit n'est pas une erreur : Git te demande juste de décider.",
   "Après résolution, l'historique garde la trace des deux branches."],
  [Q("`main` n'a reçu aucun commit depuis la création de `feature`. Que fait `git merge feature` ?",
     ["Un merge commit", "Un fast-forward : l'étiquette main avance", "Un conflit", "Rien"], 1,
     "Rien à combiner : il suffit d'avancer."),
   Q("Dans un conflit, la partie entre `<<<<<<< HEAD` et `=======` est…",
     ["la version de la branche que tu fusionnes", "la version de la branche où tu es", "l'ancienne version", "un commentaire"], 1,
     "HEAD = là où tu es."),
   Q("Tu es perdu au milieu d'une fusion. Quelle commande annule tout ?",
     ["git reset --hard origin", "git merge --abort", "git delete", "git stop"], 1,
     "Retour à l'état d'avant le merge.")],
  TD("Provoquer et résoudre un conflit",
     "Dans ton dépôt d'essai, fabrique un conflit volontaire et résous-le.",
     ["Sur `main`, crée `config.txt` avec la ligne `couleur=bleu`, commit",
      "Branche `theme` : change en `couleur=vert`, commit",
      "Retour sur `main` : change en `couleur=rouge`, commit",
      "Fusionne `theme` dans `main`, résous en gardant `couleur=vert`",
      "Regarde le graphe final"],
     code("bash", r"""
echo "couleur=bleu" > config.txt && git add . && git commit -m "config"
# à toi
"""),
     ["`git status` pendant le conflit te liste les fichiers en conflit et la marche à suivre.",
      "Après avoir édité le fichier : `git add config.txt` puis `git commit` (sans `-m`, Git propose un message)."],
     code("bash", r"""
echo "couleur=bleu" > config.txt && git add . && git commit -m "config"
git switch -c theme
echo "couleur=vert" > config.txt && git commit -am "theme vert"
git switch main
echo "couleur=rouge" > config.txt && git commit -am "theme rouge"

git merge theme
# CONFLICT (content): Merge conflict in config.txt
git status                     # "both modified: config.txt"
# édite config.txt : garde seulement "couleur=vert"
git add config.txt
git commit                     # message "Merge branch 'theme'"
git log --oneline --graph
"""),
     ["Le fichier final ne contient plus aucun marqueur",
      "Le graphe montre un commit avec deux parents"])),

M("git-rebase", T, "Rebase : réécrire proprement", 18,
  "Comprendre ce que fait rebase, quand l'utiliser et quand l'éviter.",
  "Avec des merges partout, l'historique devient un plat de spaghettis. Rebase permet de « rejouer » tes commits au-dessus de la dernière version de `main`, pour un historique en ligne droite. Mais comme il crée de nouveaux commits, il peut faire des dégâts s'il est mal utilisé.",
  ["Tu es sur `feature`, `main` a avancé depuis que tu as commencé",
   "`git rebase main` **met de côté** tes commits D et E",
   "Il place `feature` au bout de `main`, puis **rejoue** D et E un par un : ce sont de **nouveaux** commits D' et E' (nouveaux identifiants)",
   "Résultat : une ligne droite, comme si tu avais commencé ton travail aujourd'hui"],
  ["Merge **conserve** l'histoire telle qu'elle s'est passée ; rebase la **réécrit** pour qu'elle soit plus lisible.",
   "**Règle d'or** : ne rebase jamais des commits **déjà partagés** sur une branche où d'autres travaillent (ex. `main`). Rebase seulement **ta** branche.",
   "Après un rebase d'une branche déjà poussée : `git push --force-with-lease` (refuse si quelqu'un d'autre a poussé entre-temps, contrairement à `--force`).",
   "**Rebase interactif** `git rebase -i HEAD~3` : réorganiser tes 3 derniers commits : `pick` (garder), `reword` (changer le message), `squash`/`fixup` (fusionner avec le précédent), `drop` (supprimer).",
   "Conflit pendant un rebase : corrige, `git add`, puis `git rebase --continue`. Perdu : `git rebase --abort`."],
  ["Rebaser `main` ou une branche partagée : les autres se retrouvent avec un historique incompatible.",
   "Utiliser `git push --force` au lieu de `--force-with-lease`."],
  code("plaintext", r"""
  AVANT                                  APRÈS  git switch feature && git rebase main

      A --- B --- C --- F   main              A --- B --- C --- F   main
             \                                                   \
              D --- E   feature                                   D' --- E'   feature

  D' et E' = mêmes changements que D et E, mais NOUVEAUX commits (nouveaux ids).
  Ensuite, git switch main && git merge feature  ->  fast-forward, ligne droite.


  REBASE INTERACTIF  git rebase -i HEAD~4   (l'éditeur s'ouvre)

  pick   1a2b3c4 feat: ajoute le panier
  fixup  5d6e7f8 oups typo                  <- fusionné dans le précédent, message jeté
  reword 9a8b7c6 fix bug                    <- tu pourras réécrire le message
  drop   3c2b1a0 console.log de debug       <- supprimé

  Résultat : 2 commits propres au lieu de 4.
"""),
  ["Les anciens D et E existent toujours un moment (voir `reflog`) : un rebase raté se rattrape.",
   "Le rebase interactif sert surtout à nettoyer ta branche avant d'ouvrir une Pull Request.",
   "Beaucoup d'équipes configurent `git pull --rebase` par défaut pour éviter les merges inutiles."],
  [Q("Après `git rebase main`, tes commits ont…",
     ["les mêmes identifiants", "de nouveaux identifiants (ce sont de nouveaux commits)", "disparu", "été fusionnés en un seul"], 1,
     "Rebase rejoue les changements : il crée des copies."),
   Q("Peut-on rebaser `main` sur laquelle toute l'équipe travaille ?",
     ["Oui", "Non : on ne réécrit pas un historique déjà partagé", "Oui avec --force", "Seulement le vendredi"], 1,
     "C'est la règle d'or du rebase."),
   Q("Pour fusionner un commit « oups typo » dans le précédent sans garder son message :",
     ["pick", "fixup", "drop", "reword"], 1,
     "`squash` garde les deux messages pour les combiner, `fixup` jette celui du commit fusionné.")],
  TD("Nettoyer une branche",
     "Crée une branche avec des commits brouillons, puis nettoie-la et mets-la à jour avec `main`.",
     ["Sur `feature/contact`, fais 4 commits : « ajoute formulaire », « wip », « oups », « ajoute validation »",
      "Pendant ce temps, ajoute 1 commit sur `main`",
      "Avec `rebase -i`, obtiens 2 commits : `feat: ajoute le formulaire de contact` et `feat: valide le formulaire de contact`",
      "Rebase la branche sur `main`",
      "Vérifie que l'historique est une ligne droite"],
     code("bash", r"""
git switch main
git switch -c feature/contact
# 4 commits ici...
git switch main
# 1 commit ici...
git switch feature/contact
# à toi
"""),
     ["`git rebase -i HEAD~4` ouvre les 4 derniers commits ; le plus ancien est en haut.",
      "Mets `reword` sur le premier pour changer son message, `fixup` sur « wip » et « oups ».",
      "Pour changer l'éditeur utilisé par Git : `git config --global core.editor \"code --wait\"`."],
     code("bash", r"""
git switch feature/contact
git rebase -i HEAD~4
# Dans l'éditeur :
#   reword a1 ajoute formulaire
#   fixup  b2 wip
#   fixup  c3 oups
#   reword d4 ajoute validation
# puis réécris les messages :
#   feat: ajoute le formulaire de contact
#   feat: valide le formulaire de contact

git rebase main
# en cas de conflit : corrige, git add <fichier>, git rebase --continue

git log --oneline --graph --all
# * (HEAD -> feature/contact) feat: valide le formulaire de contact
# * feat: ajoute le formulaire de contact
# * (main) le commit de main
# * ...
# Ligne droite : un merge dans main sera un fast-forward.
"""),
     ["Ta branche contient exactement 2 commits, au-dessus de `main`",
      "Les messages suivent le format `feat: ...`"])),

M("git-revenir", T, "Revenir en arrière", 18,
  "Choisir la bonne commande pour annuler : restore, reset, revert, et le filet de sécurité reflog.",
  "« Revenir en arrière » peut vouloir dire 5 choses différentes : annuler une modification non sauvegardée, défaire un commit local, annuler un commit déjà poussé, regarder une ancienne version… Chaque cas a sa commande. Se tromper de commande, c'est là qu'on perd du travail.",
  ["Pas encore commité ? **`git restore`** remet un fichier comme au dernier commit",
   "Commité mais **pas poussé** ? **`git reset`** recule l'étiquette de la branche",
   "Déjà **poussé / partagé** ? **`git revert`** crée un **nouveau** commit qui annule l'ancien",
   "Tout cassé ? **`git reflog`** liste toutes les positions passées de HEAD : on peut presque toujours revenir"],
  ["`git restore fichier` : jette tes modifications non commitées (attention, définitif). `git restore --staged fichier` : retire du staging, garde la modification.",
   "`git reset --soft HEAD~1` : annule le dernier commit, **garde** les changements préparés. `--mixed` (par défaut) : les garde mais non préparés. `--hard` : **efface** tout.",
   "`git revert <id>` : sûr sur une branche partagée, l'historique n'est pas réécrit.",
   "Regarder une ancienne version : `git switch --detach <id>` (HEAD « détaché »). Pour y travailler : `git switch -c nouvelle-branche`.",
   "Récupérer un seul fichier d'un ancien commit : `git restore --source=<id> chemin/fichier`.",
   "`git commit --amend` : corrige le **dernier** commit (message ou fichier oublié), seulement s'il n'est pas poussé."],
  ["`git reset --hard` sur des commits déjà poussés : tu réécris l'historique partagé.",
   "Paniquer et recloner le projet : `git reflog` retrouve presque tout."],
  code("bash", r"""
# 1. J'ai cassé un fichier, pas encore commité
git restore src/Panier.php

# 2. J'ai ajouté un fichier au staging par erreur
git restore --staged .env

# 3. J'ai oublié un fichier dans mon dernier commit (pas encore poussé)
git add oubli.php
git commit --amend --no-edit

# 4. Mon dernier commit local est mauvais, je veux le refaire
git reset --soft HEAD~1      # le commit disparaît, les changements restent prêts

# 5. Je veux tout jeter et revenir 2 commits en arrière (local uniquement !)
git reset --hard HEAD~2

# 6. Un commit déjà poussé sur main a introduit un bug
git revert 9f1e2d3           # nouveau commit qui fait l'inverse
git push

# 7. Voir le projet tel qu'il était le 1er octobre
git log --oneline --before="2026-10-01" -1
git switch --detach a1b2c3d
git switch -                 # revenir où j'étais

# 8. J'ai fait un reset --hard de trop, au secours
git reflog                   # liste : HEAD@{0} reset, HEAD@{1} commit "ajoute panier"...
git reset --hard HEAD@{1}    # retour à la position d'avant
"""),
  ["Les cas 1 à 5 ne touchent que ta machine ; le cas 6 est le seul sûr pour un commit déjà partagé.",
   "`HEAD~1` = le parent du commit actuel ; `HEAD~2` = le grand-parent.",
   "Le reflog garde l'historique des déplacements de HEAD pendant environ 90 jours (par défaut)."],
  [Q("Un commit déjà poussé sur `main` contient un bug. Quelle commande ?",
     ["git reset --hard", "git revert <id>", "git commit --amend", "git restore"], 1,
     "revert ajoute un commit d'annulation sans réécrire l'historique partagé."),
   Q("`git reset --soft HEAD~1` fait quoi ?",
     ["Efface le dernier commit et ses changements", "Annule le dernier commit mais garde les changements prêts à être recommités", "Pousse sur GitHub", "Crée une branche"], 1,
     "--soft : seule l'étiquette recule."),
   Q("Après un `reset --hard` malheureux, comment retrouver tes commits ?",
     ["Impossible", "`git reflog` puis `git reset --hard HEAD@{n}`", "Recloner", "git revert"], 1,
     "Le reflog est le filet de sécurité de Git.")],
  TD("Le parcours du combattant",
     "Dans ton dépôt d'essai, provoque chaque situation et répare-la avec la bonne commande.",
     ["Modifie un fichier puis annule la modification sans commit",
      "Fais un commit avec une faute dans le message, corrige le message",
      "Fais 2 commits, puis annule-les en gardant les changements",
      "Fais un `reset --hard HEAD~3`, puis retrouve l'état d'avant grâce au reflog",
      "Fais un commit puis annule-le avec `revert` (comme s'il était déjà poussé) ; regarde le log"],
     code("bash", r"""
# Pour chaque étape, note : la situation, la commande, ce que montre git log --oneline
"""),
     ["Message de commit : `git commit --amend -m \"nouveau message\"`.",
      "Deux commits annulés en gardant les changements : `git reset HEAD~2` (mode mixed par défaut)."],
     code("bash", r"""
# 1
echo "cassé" >> notes.txt
git restore notes.txt

# 2
git commit -am "fix: corrige la typpo"
git commit --amend -m "fix: corrige la typo"

# 3
echo a >> notes.txt && git commit -am "a"
echo b >> notes.txt && git commit -am "b"
git reset HEAD~2           # les modifs a et b sont dans le dossier, non préparées
git status

# 4
git commit -am "ab"
git reset --hard HEAD~3
git reflog                 # repère la ligne "commit: ab", ex. HEAD@{1}
git reset --hard HEAD@{1}

# 5
echo bug >> notes.txt && git commit -am "feat: ajoute un bug"
git revert HEAD            # ouvre l'éditeur avec "Revert ..."
git log --oneline          # 2 commits : le bug ET son annulation
"""),
     ["Tu sais dire quelle commande est sûre après un push (revert)",
      "Tu as récupéré l'état perdu avec le reflog"])),

M("git-commits", T, "Bien écrire ses commits (Conventional Commits)", 12,
  "Écrire des commits utiles : un seul sujet, un message clair au format `type(portée): description`.",
  "« fix », « wip », « modifs » : dans 3 mois, personne (toi compris) ne sait ce qui a changé ni pourquoi. Un format commun rend l'historique lisible, et des outils peuvent s'en servir pour générer un changelog ou numéroter les versions automatiquement.",
  ["Un commit = **un seul changement logique** (atomique)",
   "Message : `type(portée optionnelle): description` à l'impératif, en minuscules, sans point final",
   "Une ligne vide, puis un **corps** qui explique **pourquoi** (si ce n'est pas évident)",
   "Changement qui casse la compatibilité : `!` après le type, ou `BREAKING CHANGE:` en pied de message"],
  ["**feat** : nouvelle fonctionnalité pour l'utilisateur. **fix** : correction de bug.",
   "**refactor** : réorganisation du code sans changer le comportement. **perf** : amélioration de performance.",
   "**docs** : documentation. **test** : ajout ou correction de tests. **style** : formatage (espaces, virgules), pas le CSS.",
   "**chore** : tâches annexes (mise à jour de dépendances, config). **build** : système de build. **ci** : intégration continue (GitHub Actions).",
   "Portée = la zone concernée : `feat(panier): …`, `fix(api): …`.",
   "Le format vient de la spécification *Conventional Commits* (conventionalcommits.org). Chaque équipe peut l'adapter : regarde l'historique du projet."],
  ["Un commit « fix + refactor + nouvelle fonctionnalité » : impossible à annuler proprement avec `revert`.",
   "Un message qui dit **quoi** (`change la ligne 42`) au lieu de **pourquoi**."],
  code("plaintext", r"""
  MAUVAIS                             BON
  -------                             ---
  fix                                 fix(panier): empêche une quantité négative
  wip                                 feat(auth): ajoute la connexion par lien magique
  modifs diverses                     refactor(commande): extrait le calcul du total dans un service
  update                              chore(deps): met à jour symfony/http-kernel en 7.3
  ajout tests + fix bug + css         (3 commits séparés : test, fix, style)


  Message complet :

  fix(emprunt): refuse un 4e emprunt simultané

  La règle "3 emprunts max" n'était vérifiée que côté front :
  un appel direct à l'API permettait de la contourner.
  La vérification est maintenant dans EmpruntService.

  Closes #128


  Changement cassant :

  feat(api)!: renomme le champ "auteur" en "auteurNom" dans LivreOutput

  BREAKING CHANGE: les clients doivent lire "auteurNom".
"""),
  ["Impératif présent : « ajoute », « corrige » (comme une instruction : « ce commit… ajoute »).",
   "`Closes #128` ferme automatiquement l'issue 128 sur GitHub au merge.",
   "`git add -p` te laisse choisir morceau par morceau ce qui va dans le commit : idéal pour faire des commits atomiques."],
  [Q("Tu renommes des variables et déplaces une méthode, sans changer le comportement. Type ?",
     ["feat", "fix", "refactor", "style"], 2,
     "Même comportement, code réorganisé."),
   Q("Tu mets à jour une dépendance dans composer.json. Type ?",
     ["feat", "chore", "fix", "docs"], 1,
     "Tâche de maintenance, pas de changement visible pour l'utilisateur (`build` est aussi accepté selon les équipes)."),
   Q("Comment préparer seulement une partie des modifications d'un fichier ?",
     ["git add .", "git add -p", "git commit -a", "git stash"], 1,
     "`-p` (patch) te demande pour chaque morceau : y / n.")],
  TD("Réécrire des messages",
     "Voici l'historique d'un collègue. Réécris chaque message au format Conventional Commits, et indique ceux qu'il aurait fallu découper.",
     ["Donne le bon type et une portée",
      "Description à l'impératif, courte",
      "Signale les commits qui mélangent plusieurs changements et propose le découpage"],
     code("plaintext", r"""
1. "ajout page profil"
2. "correction bug login qui plantait si email en majuscules"
3. "maj readme"
4. "nettoyage code + correction calcul TVA + ajout bouton export"
5. "passage de react 18 à 19"
6. "tests panier"
7. "le prix s'affiche plus vite"
"""),
     ["Le 4 contient trois changements de types différents.",
      "Le 5 peut être `chore(deps)` ou `build`, selon les conventions de l'équipe."],
     code("plaintext", r"""
1. feat(profil): ajoute la page profil
2. fix(auth): accepte les emails en majuscules à la connexion
3. docs: met à jour le README
4. À DÉCOUPER en 3 commits :
   refactor(facture): simplifie le calcul des lignes
   fix(facture): corrige le taux de TVA appliqué
   feat(facture): ajoute le bouton d'export
5. chore(deps): passe à React 19
6. test(panier): couvre l'ajout et la suppression d'articles
7. perf(catalogue): accélère l'affichage des prix
"""),
     ["Chaque message tient sur une ligne et commence par un type",
      "Tu as découpé le 4"])),

M("git-github", T, "GitHub : remote, Pull Requests & workflow", 15,
  "Comprendre le lien entre ton dépôt local et GitHub, et le circuit d'une Pull Request.",
  "Ton dépôt local et celui de GitHub sont deux copies indépendantes. `push`, `pull` et `fetch` les synchronisent. Sans ce modèle en tête, on ne comprend pas pourquoi « ça marche chez moi mais pas sur GitHub » ou pourquoi un push est refusé.",
  ["**`origin`** = le nom du dépôt GitHub dans ton dépôt local",
   "`git fetch` **télécharge** les nouveautés dans des étiquettes `origin/main` sans toucher à ton travail",
   "`git pull` = fetch + **fusion** dans ta branche ; `git push` **envoie** tes commits",
   "Sur GitHub, une **Pull Request** propose de fusionner ta branche dans `main` après relecture"],
  ["`origin/main` est la dernière version de `main` sur GitHub **que tu as téléchargée**. `git fetch` la met à jour.",
   "Push refusé (« rejected, fetch first ») : quelqu'un a poussé avant toi. `git pull --rebase` puis `git push`.",
   "Premier push d'une branche : `git push -u origin feature/x` (`-u` mémorise le lien pour les fois suivantes).",
   "Workflow classique : branche depuis `main` à jour → commits → push → Pull Request → relecture et CI → merge → supprimer la branche.",
   "Sur la PR, 3 façons de fusionner : **merge commit**, **squash** (tous tes commits en un seul), **rebase**. Beaucoup d'équipes choisissent squash : un commit propre par fonctionnalité sur `main`.",
   "`.gitignore` : liste ce qui ne doit **jamais** partir (`.env`, `vendor/`, `node_modules/`, `var/`)."],
  ["Travailler directement sur `main`.",
   "Commiter un `.env` avec des mots de passe : même supprimé ensuite, il reste dans l'historique. Change le secret."],
  code("plaintext", r"""
  TA MACHINE                                        GITHUB (origin)
  ==========                                        ===============
  main          A---B                               main   A---B---C   (un collègue a poussé C)
  origin/main   A---B   (dernière info connue)

  git fetch     -> origin/main  A---B---C           (ton main n'a pas bougé)
  git pull      -> main         A---B---C           (fetch + fusion)


  WORKFLOW D'UNE FONCTIONNALITÉ

  git switch main && git pull                 1. partir de main à jour
  git switch -c feat/export-pdf               2. une branche par tâche
  ... commits ...                             3. commits atomiques et bien nommés
  git push -u origin feat/export-pdf          4. envoyer la branche
  -> GitHub : "Compare & pull request"        5. ouvrir la PR (description, captures)
  -> relecture, CI verte, corrections         6. nouveaux commits = la PR se met à jour
  -> "Squash and merge"                       7. fusion dans main
  git switch main && git pull                 8. récupérer main à jour
  git branch -d feat/export-pdf               9. supprimer la branche locale
"""),
  ["`fetch` est toujours sans risque : il ne modifie pas tes branches.",
   "Pousser de nouveaux commits sur la branche met la PR à jour automatiquement.",
   "Nomme tes branches comme tes commits : `feat/…`, `fix/…`, `chore/…`."],
  [Q("Différence entre `git fetch` et `git pull` ?",
     ["Aucune", "fetch télécharge sans modifier ta branche ; pull télécharge ET fusionne", "fetch envoie, pull reçoit", "pull est plus sûr"], 1,
     "pull = fetch + merge (ou rebase avec --rebase)."),
   Q("Ton push est refusé car la branche distante a des commits que tu n'as pas. Que faire ?",
     ["git push --force", "git pull --rebase puis git push", "Supprimer le dépôt", "git reset --hard"], 1,
     "Intègre d'abord le travail des autres. --force effacerait leurs commits."),
   Q("« Squash and merge » sur une PR de 6 commits donne…",
     ["6 commits sur main", "1 seul commit sur main", "un merge commit + 6 commits", "rien"], 1,
     "Utile pour garder un main lisible, une ligne par fonctionnalité.")],
  TD("Ta première Pull Request propre",
     "Publie le dashboard (ou un petit projet) sur GitHub en suivant le workflow complet.",
     ["Crée un dépôt sur GitHub et relie-le (`git remote add origin …`)",
      "Pousse `main` avec un premier commit `chore: initialise le projet`",
      "Crée `feat/readme`, ajoute un README en 2 commits, pousse, ouvre une PR",
      "Fusionne avec « Squash and merge » ; récupère `main` en local ; supprime la branche",
      "Bonus : active GitHub Pages pour héberger `index.html`"],
     code("bash", r"""
git init -b main
git add .
git commit -m "chore: initialise le projet"
git remote add origin https://github.com/<ton-pseudo>/atelier-de-code.git
# à toi
"""),
     ["Ajoute un `.gitignore` avant le premier commit si tu as des dossiers générés.",
      "Après le squash, ta branche locale a des commits « différents » de main : `git branch -D` (D majuscule) est nécessaire pour la supprimer."],
     code("bash", r"""
git push -u origin main

git switch -c feat/readme
echo "# Atelier de code" > README.md && git add . && git commit -m "docs: ajoute le titre du README"
echo "Dashboard pour apprendre." >> README.md && git commit -am "docs: décrit le projet"
git push -u origin feat/readme
# GitHub : "Compare & pull request" -> description -> Create
# Puis "Squash and merge" -> message : docs: ajoute le README

git switch main
git pull
git branch -D feat/readme           # -D car le squash a créé un commit différent
git push origin --delete feat/readme  # si GitHub ne l'a pas déjà supprimée

# Bonus : Settings > Pages > Deploy from a branch > main / (root)
"""),
     ["`main` sur GitHub contient un seul commit pour le README",
      "`git log --oneline --graph --all` ne montre plus la branche"])),

M("git-outils", T, "Outils du quotidien : stash, cherry-pick, tags, bisect", 15,
  "Connaître les commandes qui sauvent la mise au quotidien.",
  "Tu es au milieu d'une tâche et on te demande un correctif urgent ; tu as besoin d'un seul commit d'une autre branche ; un bug est apparu « quelque part dans les 50 derniers commits ». Chaque situation a son outil.",
  ["**`stash`** : mettre de côté ton travail en cours, sans commit, pour changer de branche",
   "**`cherry-pick`** : copier **un** commit précis d'une autre branche sur la tienne",
   "**`tag`** : poser une étiquette **fixe** sur une version (`v1.2.0`)",
   "**`bisect`** : trouver le commit qui a introduit un bug, par recherche dichotomique"],
  ["`git stash` met de côté, `git stash pop` récupère. `git stash -u` inclut les nouveaux fichiers. `git stash list` pour voir la pile.",
   "`git cherry-pick <id>` crée un nouveau commit avec les mêmes changements (comme un mini-rebase d'un seul commit).",
   "Un tag ne bouge pas, contrairement à une branche. `git tag -a v1.0.0 -m \"…\"` puis `git push origin v1.0.0`. Versions : MAJEUR.MINEUR.CORRECTIF (semver).",
   "`git bisect` : tu dis un commit « bon » et un « mauvais », Git te place au milieu, tu testes, tu réponds `good`/`bad`… En 6 étapes, il trouve le coupable parmi 50 commits.",
   "`git blame fichier` : qui a modifié chaque ligne, et dans quel commit (pour comprendre **pourquoi**, pas pour accuser)."],
  ["Accumuler des stash oubliés : préfère un commit `wip` sur ta branche, que tu nettoieras au rebase.",
   "Cherry-picker beaucoup de commits entre branches : signe qu'il fallait plutôt fusionner."],
  code("bash", r"""
# Correctif urgent en plein travail
git stash -u                         # mon travail est mis de côté
git switch main && git pull
git switch -c fix/paiement
# ... correction, commit, push, PR ...
git switch feat/panier
git stash pop                        # je retrouve mon travail

# Récupérer un seul correctif d'une autre branche
git log --oneline fix/paiement       # repère l'id : 4e5f6a7
git switch release/1.2
git cherry-pick 4e5f6a7

# Marquer une version
git tag -a v1.2.0 -m "Version 1.2.0 : export PDF"
git push origin v1.2.0

# Trouver le commit fautif
git bisect start
git bisect bad                       # la version actuelle a le bug
git bisect good v1.1.0               # cette version marchait
# Git se place au milieu : teste, puis
git bisect good                      # ou : git bisect bad
# ... jusqu'à : "9f1e2d3 is the first bad commit"
git bisect reset                     # retour à la normale
"""),
  ["`stash` est une pile : le dernier mis de côté ressort en premier.",
   "Après un cherry-pick, le commit existe en deux exemplaires (ids différents) sur deux branches.",
   "`bisect` peut tourner tout seul avec un script de test : `git bisect run ./test.sh`."],
  [Q("Tu dois changer de branche mais ton travail n'est pas prêt à être commité. Que faire ?",
     ["git reset --hard", "git stash", "git revert", "git tag"], 1,
     "Puis `git stash pop` en revenant."),
   Q("Différence entre un tag et une branche ?",
     ["Aucune", "Un tag reste sur son commit, une branche avance à chaque commit", "Un tag est privé", "Une branche est fixe"], 1,
     "Le tag marque une version, une fois pour toutes."),
   Q("Un bug est apparu entre v1.1.0 (ok) et aujourd'hui (128 commits). Quel outil ?",
     ["git blame", "git bisect", "git stash", "git cherry-pick"], 1,
     "Recherche dichotomique : environ 7 tests au lieu de 128.")],
  TD("Trouver le coupable",
     "Fabrique un historique avec un bug caché, puis retrouve-le avec `bisect`.",
     ["Crée 20 commits qui ajoutent chacun une ligne à `nombres.txt`",
      "Au commit 13, ajoute aussi la ligne `BUG`",
      "Tague le commit 5 `v1.0.0`",
      "Avec `git bisect`, retrouve le commit fautif (sans regarder le log)",
      "Bonus : automatise avec `git bisect run`"],
     code("bash", r"""
git init -b main bisect-demo && cd bisect-demo
for i in $(seq 1 20); do
  echo "$i" >> nombres.txt
  # à toi : au tour 13, ajoute aussi BUG
  git add . && git commit -qm "feat: ajoute $i"
  # à toi : au tour 5, crée le tag v1.0.0
done
"""),
     ["Dans la boucle : `if [ \"$i\" -eq 13 ]; then echo BUG >> nombres.txt; fi`.",
      "Test manuel : `grep BUG nombres.txt` → trouvé = bad, sinon good.",
      "Automatique : `git bisect run sh -c '! grep -q BUG nombres.txt'` (code 0 = good)."],
     code("bash", r"""
git init -b main bisect-demo && cd bisect-demo
for i in $(seq 1 20); do
  echo "$i" >> nombres.txt
  if [ "$i" -eq 13 ]; then echo BUG >> nombres.txt; fi
  git add . && git commit -qm "feat: ajoute $i"
  if [ "$i" -eq 5 ]; then git tag -a v1.0.0 -m "v1"; fi
done

git bisect start
git bisect bad              # HEAD (20) contient BUG
git bisect good v1.0.0
# à chaque étape :
grep -q BUG nombres.txt && git bisect bad || git bisect good
# ... "xxxxxxx is the first bad commit  feat: ajoute 13"
git bisect reset

# Version automatique :
git bisect start HEAD v1.0.0
git bisect run sh -c '! grep -q BUG nombres.txt'
git bisect reset
"""),
     ["bisect désigne bien « feat: ajoute 13 »",
      "Il a fallu environ 4 tests pour 15 commits"])),
]

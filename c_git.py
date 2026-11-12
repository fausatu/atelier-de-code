from common import V2, P, L, D, N, E, LANE, F, TD, RUN
from c_git_v1 import MODULES as V1

v1 = {m["id"]: m for m in V1}

SIM = ("Le bouton **Lancer les commandes** exécute ton script dans un **Git simulé** : le dépôt de départ est recréé à chaque lancement, "
       "puis tes commandes s'exécutent ligne par ligne. Tu vois le **graphe des commits**, l'état du dossier et le terminal. "
       "Pour écrire dans un fichier : `echo \"texte\" > fichier` (remplace) ou `>> fichier` (ajoute une ligne) ; "
       "`printf \"ligne 1\\nligne 2\\n\" > fichier` pour plusieurs lignes ; `cat fichier` pour lire. "
       "Lance souvent et regarde le graphe : c'est le meilleur moyen de comprendre.")


def SH(code):
    return [F("commandes.sh", "bash", code)]


def GRUN(tests, setup=""):
    return RUN("git", tests=tests, entry="commandes.sh", start=setup)


# ============================================================ 1. Modèle
modele = V2(v1["git-modele"],
  prereq=[
    P("Dépôt (repository)", "Le dossier de ton projet **plus** un sous-dossier caché `.git/` où Git range tout l'historique. `git init` crée ce sous-dossier."),
    P("Commit", "Une **photo complète** de tous les fichiers suivis à un instant donné, avec un message, un auteur, une date et un lien vers la photo précédente (son **parent**)."),
    P("Hash (identifiant)", "Chaque commit a un identifiant unique calculé à partir de son contenu, comme `a1b2c3d`. On peut l'utiliser partout où Git attend un commit."),
    P("Branche", "Une **étiquette** posée sur un commit. Quand tu commites, l'étiquette de la branche courante avance toute seule."),
    P("HEAD", "Le marqueur « tu es ici ». D'habitude il désigne une branche (`HEAD → main`), qui désigne elle-même un commit."),
    P("Suivi / non suivi", "Un fichier est **suivi** (tracked) si Git le connaît déjà (il est dans le dernier commit ou dans la zone de préparation). Un fichier nouveau est **non suivi** tant que tu ne l'as pas ajouté."),
  ],
  diagram=D(
    nodes=[
      N("w", 0, 1, "Dossier de travail", "tes fichiers", kind="file"),
      N("i", 1, 1, "Zone de préparation", "index / staging", kind="doc", color="warn"),
      N("h", 2, 1, "Historique", "les commits", kind="db", color="accent"),
      N("br", 2, 0, "main", "étiquette de branche", kind="pill", color="good"),
      N("hd", 1, 0, "HEAD", "« tu es ici »", kind="pill"),
    ],
    edges=[E("w", "i", "git add"), E("i", "h", "git commit"), E("hd", "br"), E("br", "h")],
    caption="Tu modifies dans le dossier de travail, tu choisis ce qui part dans la prochaine photo (git add), puis tu prends la photo (git commit). La branche avance sur le nouveau commit ; HEAD indique la branche courante."),
  lessons=[
    L("Trois zones, deux commandes", r"""
Git ne surveille pas tes fichiers en continu. Il connaît **trois endroits** :

1. **Le dossier de travail** : tes fichiers tels que tu les vois dans l'éditeur.
2. **La zone de préparation** (staging, ou index) : la liste de ce qui partira dans le **prochain** commit.
3. **L'historique** : les commits déjà enregistrés, dans `.git/`.

Et deux commandes font passer les changements d'une zone à l'autre :

```bash
git add app.js            # dossier de travail  →  zone de préparation
git commit -m "message"   # zone de préparation →  nouveau commit
```

Pourquoi une zone intermédiaire ? Pour **choisir**. Tu as modifié trois fichiers mais seulement deux concernent le correctif : tu n'ajoutes que ces deux-là, et le troisième attendra un autre commit. Un commit = un changement cohérent.

`git status` te dit à tout moment où en est chaque fichier :

```
Changes to be committed:        ← dans la zone de préparation
	modified:   app.js
Changes not staged for commit:  ← modifié, mais pas encore ajouté
	modified:   style.css
Untracked files:                ← nouveau fichier que Git ne suit pas encore
	notes.txt
```
"""),
    L("Un commit est une photo, reliée à la précédente", r"""
Un commit n'enregistre pas « les lignes qui ont changé » : il enregistre une **photo complète** du projet (Git est malin et ne stocke pas deux fois un fichier identique). Chaque commit contient aussi :

- l'identifiant de son **parent** (le commit d'avant) ;
- l'auteur, la date, le message.

Les commits forment donc une **chaîne** qui remonte dans le temps :

```
A ← B ← C ← D        chaque commit pointe vers son parent
```

Deux propriétés à retenir, elles expliquent tout le reste :

- Un commit est **immuable**. On ne modifie jamais un commit : « modifier » (amend, rebase) crée en réalité un **nouveau** commit avec un nouvel identifiant.
- L'identifiant dépend du contenu **et** du parent. Changer un commit ancien change donc l'identifiant de tous ceux qui le suivent.
"""),
    L("Les branches et HEAD sont des étiquettes", r"""
Une branche n'est **pas** une copie du code. C'est une étiquette de quelques octets posée sur un commit :

```
A ← B ← C ← D
            ↑
          main  ← HEAD
```

Quand tu commites, Git crée E avec D comme parent, puis **déplace l'étiquette** de la branche courante sur E. C'est tout.

Créer une branche = poser une deuxième étiquette au même endroit :

```bash
git switch -c essai     # crée l'étiquette « essai » sur le commit actuel et s'y place
```

Les commits suivants feront avancer `essai`, pas `main`. Revenir sur `main` (`git switch main`) remet les fichiers du dossier de travail dans l'état du commit pointé par `main`.

**HEAD détachée.** Si tu te places directement sur un commit (`git switch --detach HEAD~2`), HEAD ne pointe plus vers une branche. Tu peux regarder, tester, et même commiter ; mais ces commits ne sont tenus par **aucune étiquette** : si tu repars sans créer de branche (`git switch -c nom`), ils deviennent difficiles à retrouver.

Pour désigner un commit sans connaître son identifiant : `HEAD~1` (le parent de HEAD), `HEAD~3` (trois crans en arrière), `main~2`, ou un nom de branche ou de tag.
"""),
    L("Lire l'état du dépôt", r"""
Quatre commandes à utiliser tout le temps, elles ne modifient rien :

| Commande | Ce qu'elle montre |
|---|---|
| `git status` | la branche courante et l'état des fichiers dans les 3 zones |
| `git log --oneline --graph --all` | le graphe des commits et des étiquettes |
| `git diff` | ce que tu as modifié mais pas encore ajouté |
| `git diff --staged` | ce qui partira dans le prochain commit |

Et un fichier spécial : **`.gitignore`**. Chaque ligne est un nom ou un motif (`.env`, `*.log`, `node_modules/`) que Git doit ignorer : ces fichiers n'apparaissent plus comme « non suivis » et `git add .` les saute. C'est là qu'on met les secrets, les dépendances, les fichiers générés.

Attention : `.gitignore` n'agit que sur les fichiers **non suivis**. Un fichier déjà ajouté ou commité reste suivi ; il faut d'abord le retirer de la zone de préparation (`git restore --staged .env`) ou du suivi (`git rm --cached .env`).
"""),
  ],
  recap=[
    "Trois zones : dossier de travail → (`git add`) zone de préparation → (`git commit`) historique.",
    "Un commit = une photo complète + son parent ; il est immuable.",
    "Une branche est une étiquette qui avance à chaque commit ; HEAD indique où tu es.",
    "HEAD détachée : tes commits ne sont tenus par aucune branche ; `git switch -c nom` pour les garder.",
    "`git status`, `git log --oneline --graph --all`, `git diff` : à lancer tout le temps.",
    "`.gitignore` pour les secrets et fichiers générés (seulement les fichiers non suivis).",
  ],
  example=[F("terminal", "bash", r"""
$ git init
$ echo "v1" > notes.txt
$ git status
Untracked files:
	notes.txt                       # nouveau : Git ne le suit pas encore

$ git add notes.txt
$ git commit -m "premier commit"
[main (root-commit) 69aba98] premier commit

$ git switch -c essai               # nouvelle étiquette, même commit
$ echo "v2" >> notes.txt
$ git commit -am "essai v2"         # -a : ajoute les fichiers déjà suivis
[essai 3f2c1d0] essai v2

$ git log --oneline --graph --all
* 3f2c1d0 (HEAD -> essai) essai v2
* 69aba98 (main) premier commit     # main n'a pas bougé
""")],
  notes=["`git status` après `echo` : le fichier est « non suivi ».",
         "Après `git switch -c essai`, les deux étiquettes sont sur le même commit ; seul `essai` avance ensuite.",
         "`commit -a` ajoute automatiquement les fichiers **déjà suivis** (pas les nouveaux)."],
  td1=dict(path="commandes.sh",
    title="Premiers commits et première branche",
    enonce="Le dépôt est vide. Construis un petit historique et regarde le graphe évoluer à chaque étape. " + SIM,
    consignes=["`git init`, puis 3 commits sur `main` (chacun modifie ou crée un fichier)",
               "Crée la branche `essai` et fais-y 2 commits",
               "Reviens sur `main` et fais 1 commit",
               "Termine avec un dossier propre, sur `main`, et un `git log --oneline --graph --all`"],
    hints=["`echo \"v2\" >> notes.txt` puis `git commit -am \"message\"` (fichier déjà suivi).",
           "`git switch -c essai` crée la branche et s'y place ; `git switch main` revient.",
           "Regarde le graphe : `main` et `essai` partent du même commit puis divergent."],
    checks=["`main` a 4 commits", "`essai` a 5 commits, dont les 3 premiers de `main`"],
    files=SH(r"""
# Dépôt vide : à toi de jouer.
git init
echo "v1" > notes.txt
git add notes.txt
git commit -m "premier commit"

# continue ici : 2 autres commits sur main, puis la branche essai…

git log --oneline --graph --all
"""),
    solution=SH(r"""
git init
echo "v1" > notes.txt
git add notes.txt
git commit -m "premier commit"
echo "v2" >> notes.txt
git commit -am "ajoute v2"
echo "# Projet" > README.md
git add README.md
git commit -m "ajoute le README"

git switch -c essai
echo "essai 1" >> notes.txt
git commit -am "essai 1"
echo "essai 2" >> notes.txt
git commit -am "essai 2"

git switch main
echo "v3" >> notes.txt
git commit -am "ajoute v3"
git log --oneline --graph --all
"""),
    run=GRUN(r"""
assert.equal(git.failed().length, 0, 'Aucune commande en erreur' + (git.failed().length ? ' : ' + git.failed().join(' · ') : ''));
assert.equal(git.branch, 'main', 'Tu termines sur main');
assert.equal(git.log('main').length, 4, 'main a 4 commits');
assert(git.branches.essai, 'La branche essai existe');
assert.equal(git.log('essai').length, 5, 'essai a 5 commits');
assert(git.isAncestor('main~1', 'essai') && !git.isAncestor('main', 'essai'), 'essai part du 3e commit de main, et le dernier commit de main n\'est pas dans essai');
assert(git.ids('essai').concat(git.ids('main')).every((id) => git.touched(id).length > 0), 'Chaque commit change au moins un fichier');
assert(git.clean(), 'Le dossier est propre');
""")),
  tds=[
    TD(2, "Choisir ce qui part dans chaque commit",
       "Le projet a trois changements en cours : un correctif dans `app.js`, une retouche de couleur dans `style.css`, et un fichier `.env` (avec une clé secrète) **ajouté par erreur** à la zone de préparation. Tu dois faire des commits propres, sans jamais commiter le secret. " + SIM,
       ["Retire `.env` de la zone de préparation (sans supprimer le fichier)",
        "Commit 1 : seulement `app.js`, message `fix: corrige le calcul du total`",
        "Commit 2 : un `.gitignore` qui ignore `.env`, message `chore: ignore le fichier .env`",
        "Commit 3 : seulement `style.css`, message `style: adoucit la couleur du texte`",
        "À la fin : dossier propre, `.env` toujours présent sur le disque mais ignoré"],
       SH(r"""
# Départ : app.js et style.css modifiés, .env ajouté par erreur (git status pour voir)
git status
# à toi
"""),
       ["`git restore --staged .env` retire le fichier de la zone de préparation, sans toucher au disque.",
        "`git add app.js` n'ajoute que ce fichier : vérifie avec `git status` avant chaque commit.",
        "`echo \".env\" > .gitignore` crée le fichier d'exclusion ; ajoute-le comme n'importe quel fichier."],
       SH(r"""
git status
git restore --staged .env
git add app.js
git commit -m "fix: corrige le calcul du total"
echo ".env" > .gitignore
git add .gitignore
git commit -m "chore: ignore le fichier .env"
git add style.css
git commit -m "style: adoucit la couleur du texte"
git status
"""),
       ["`.env` n'apparaît dans aucun commit", "Chaque commit ne touche qu'un fichier"],
       run=GRUN(r"""
assert.equal(git.failed().length, 0, 'Aucune commande en erreur' + (git.failed().length ? ' : ' + git.failed().join(' · ') : ''));
assert.equal(JSON.stringify(git.log().slice(0, 3)), JSON.stringify(['style: adoucit la couleur du texte', 'chore: ignore le fichier .env', 'fix: corrige le calcul du total']), 'Les 3 commits, dans l\'ordre, avec les bons messages');
assert.equal(JSON.stringify(git.touched('HEAD~2')), JSON.stringify(['app.js']), 'Commit 1 : seulement app.js');
assert.equal(JSON.stringify(git.touched('HEAD~1')), JSON.stringify(['.gitignore']), 'Commit 2 : seulement .gitignore');
assert.equal(JSON.stringify(git.touched('HEAD')), JSON.stringify(['style.css']), 'Commit 3 : seulement style.css');
assert(git.ids().every((id) => git.at(id, '.env') === null), '.env n\'est dans aucun commit');
assert(git.file('.env') && git.file('.env').includes('API_KEY'), '.env existe toujours sur le disque');
assert(git.clean() && git.status().untracked.length === 0, 'Dossier propre, .env ignoré (plus « non suivi »)');
""", r"""
git.sh('git init');
git.write('app.js', 'export function total(prix, qte) {\n  return prix + qte;\n}\n');
git.write('style.css', 'body { color: black; }\n');
git.sh('git add .\ngit commit -m "chore: initialise le projet"');
git.write('app.js', 'export function total(prix, qte) {\n  return prix * qte;\n}\n');
git.write('style.css', 'body { color: #222; }\n');
git.write('.env', 'API_KEY=sk-123456\n');
git.sh('git add .env');
""")),
    TD(3, "Voyager dans le passé (HEAD détachée)",
       "La page a été modifiée en 4 commits. Tu veux tester une idée de menu **à partir de l'état d'il y a deux commits**, sans toucher à `main`, puis garder cet essai dans une branche. " + SIM,
       ["Place-toi sur le commit « ajoute le menu » (deux crans avant `main`) en HEAD détachée",
        "Regarde `page.html` à ce moment-là (`cat`)",
        "Crée `menu.css` et commite-le : `test: essai d'un menu vertical`",
        "Sauve cet essai dans une branche `essai-menu` (sinon il serait perdu), puis reviens sur `main`",
        "`main` ne doit pas avoir bougé"],
       SH(r"""
git log --oneline
# à toi
"""),
       ["`git switch --detach HEAD~2` (ou `git checkout HEAD~2`) : HEAD pointe directement sur le commit.",
        "Le graphe affiche « HEAD » seul, sans branche : c'est l'état détaché.",
        "`git switch -c essai-menu` crée une branche **sur le commit où tu es**, ce qui rattache ton commit."],
       SH(r"""
git log --oneline
git switch --detach HEAD~2
cat page.html
echo "nav { display: flex; flex-direction: column; }" > menu.css
git add menu.css
git commit -m "test: essai d'un menu vertical"
git switch -c essai-menu
git switch main
git log --oneline --graph --all
"""),
       ["`essai-menu` part de « ajoute le menu »", "`main` a toujours 4 commits"],
       run=GRUN(r"""
assert.equal(git.failed().length, 0, 'Aucune commande en erreur' + (git.failed().length ? ' : ' + git.failed().join(' · ') : ''));
assert(git.used(/git (switch --detach|switch -d|checkout) /), 'Tu es passé en HEAD détachée (switch --detach ou checkout <commit>)');
assert(git.branches['essai-menu'], 'La branche essai-menu existe');
assert.equal(git.msg('essai-menu'), "test: essai d'un menu vertical", 'essai-menu pointe sur ton commit');
assert.equal(git.msg('essai-menu~1'), 'ajoute le menu', 'Ton commit a pour parent « ajoute le menu »');
assert(git.at('essai-menu', 'menu.css') !== null, 'menu.css est dans ton commit');
assert.equal(git.log('main').length, 4, 'main a toujours 4 commits');
assert(git.at('main', 'menu.css') === null, 'main ne contient pas menu.css');
assert(git.branch === 'main' && !git.detached, 'Tu es revenu sur main');
""", r"""
git.sh('git init');
git.write('page.html', '<h1>Boutique</h1>\n');
git.sh('git add .\ngit commit -m "v1 de la page"');
git.write('page.html', '<nav>Accueil | Produits</nav>\n<h1>Boutique</h1>\n');
git.sh('git commit -am "ajoute le menu"');
git.write('page.html', '<nav>Accueil | Produits</nav>\n<h1>Boutique</h1>\n<footer>Contact</footer>\n');
git.sh('git commit -am "ajoute le pied de page"');
git.write('page.html', '<nav class="sombre">Accueil | Produits</nav>\n<h1>Boutique</h1>\n<footer>Contact</footer>\n');
git.sh('git commit -am "change les couleurs"');
""")),
  ])

# ============================================================ 2. Merge
merge = V2(v1["git-merge"],
  prereq=[
    P("Fusionner (merge)", "Intégrer dans la branche courante le travail fait sur une autre branche."),
    P("Ancêtre commun", "Le dernier commit que les deux branches partagent : c'est le point de départ qui sert de référence pour fusionner."),
    P("Fast-forward", "Cas simple où la branche courante n'a pas bougé : Git avance juste l'étiquette, sans créer de commit."),
    P("Commit de fusion", "Un commit avec **deux parents**, qui réunit deux historiques divergents."),
    P("Conflit", "Les deux branches ont modifié **les mêmes lignes** différemment : Git ne peut pas choisir, c'est à toi de décider."),
  ],
  diagram=D(
    nodes=[
      N("a", 0, 0, "A", None, kind="pill"),
      N("b", 1, 0, "B", "ancêtre commun", kind="pill", color="warn"),
      N("c", 3, 0, "C", "main", kind="pill", color="accent"),
      N("d", 2, 1, "D", "theme", kind="pill", color="good"),
      N("m", 4, 0, "M", "fusion (C + D)", kind="pill", color="accent"),
    ],
    edges=[E("a", "b"), E("b", "c"), E("b", "d"), E("c", "m"), E("d", "m")],
    caption="main (C) et theme (D) ont divergé depuis B. git merge theme compare B, C et D, et crée M qui a deux parents. Les flèches suivent l'ordre du temps."),
  lessons=[
    L("Deux cas : avance rapide ou vraie fusion", r"""
Tu es sur `main` et tu lances `git merge theme`. Deux situations possibles.

**1. Fast-forward.** `main` n'a pas bougé depuis la création de `theme` :

```
A ← B            main
     ↖
      C ← D      theme
```

Il n'y a rien à « fusionner » : Git **avance l'étiquette** `main` jusqu'à D. Aucun nouveau commit, l'historique reste une ligne droite.

**2. Fusion à trois points.** Les deux branches ont avancé chacune de leur côté :

```
A ← B ← C        main
     ↖
      D          theme
```

Git compare trois versions de chaque fichier : l'**ancêtre commun** (B), la tienne (C) et la leur (D).

- Un fichier changé d'un seul côté : Git prend ce changement.
- Changé des deux côtés mais à des endroits différents : Git combine les deux.
- Les **mêmes lignes** changées différemment : **conflit**.

S'il n'y a pas de conflit, Git crée un **commit de fusion** M avec deux parents (C et D).

`git merge --no-ff theme` force la création d'un commit de fusion même quand un fast-forward serait possible : utile pour garder la trace « cette fonctionnalité a été intégrée ici ».
"""),
    L("Lire un conflit", r"""
En cas de conflit, la fusion s'arrête et Git écrit **les deux versions** dans le fichier, entre des marqueurs :

```
<<<<<<< HEAD
couleur=rouge
=======
couleur=vert
>>>>>>> theme
```

- Entre `<<<<<<< HEAD` et `=======` : ta version (la branche où tu es).
- Entre `=======` et `>>>>>>> theme` : la version de la branche que tu fusionnes.

Git ne sait pas laquelle est la bonne, c'est une décision métier. Tu peux garder l'une, l'autre, ou un mélange des deux. L'important : **supprimer les marqueurs**.

`git status` liste les fichiers en conflit dans « Unmerged paths ».
"""),
    L("Résoudre en 3 étapes", r"""
1. **Modifier le fichier** pour obtenir le contenu final, sans marqueurs.
2. **`git add fichier`** : c'est ainsi qu'on dit à Git « ce conflit est résolu ».
3. **`git commit`** (ou `git merge --continue`) : crée le commit de fusion.

```bash
git merge theme              # CONFLICT (content): Merge conflict in config.txt
cat config.txt               # lire les deux versions
echo "couleur=vert" > config.txt
git add config.txt
git commit -m "Merge branch 'theme'"
```

Pris de panique ? **`git merge --abort`** remet tout comme avant le `git merge`. Rien n'est perdu.

Après la fusion, la branche peut être supprimée : `git branch -d theme`. Ses commits restent dans l'historique (ils sont atteignables depuis le commit de fusion) ; seule l'étiquette disparaît. `-d` refuse de supprimer une branche non fusionnée : c'est une sécurité.
"""),
    L("Limiter les conflits", r"""
Les conflits ne sont pas une erreur : ils arrivent quand deux personnes touchent au même endroit. Pour en avoir moins et des plus petits :

- **Branches courtes** : une branche qui vit 2 jours diverge peu ; une branche de 3 semaines diverge beaucoup.
- **Intégrer `main` souvent** dans ta branche (merge ou rebase, voir le module suivant), pour régler les petits conflits au fil de l'eau.
- **Commits ciblés** : ne reformate pas tout un fichier dans le même commit qu'un correctif.
- Avant de résoudre, **comprends les deux intentions** : souvent la bonne réponse combine les deux changements.
"""),
  ],
  recap=[
    "Fast-forward : la branche courante n'a pas bougé, l'étiquette avance, pas de nouveau commit.",
    "Sinon : fusion à trois points (ancêtre commun, toi, eux) et commit de fusion à 2 parents.",
    "Conflit = mêmes lignes modifiées différemment ; marqueurs `<<<<<<<`, `=======`, `>>>>>>>`.",
    "Résoudre : éditer le fichier → `git add` → `git commit`. Sinon `git merge --abort`.",
    "`--no-ff` pour garder un commit de fusion ; `git branch -d` après fusion.",
  ],
  example=[F("terminal", "bash", r"""
$ git switch main
$ git merge theme
Auto-merging config.txt
CONFLICT (content): Merge conflict in config.txt
Automatic merge failed; fix conflicts and then commit the result.

$ cat config.txt
<<<<<<< HEAD
couleur=rouge
=======
couleur=vert
>>>>>>> theme

$ echo "couleur=vert" > config.txt       # on garde la version de theme
$ git add config.txt                      # « conflit résolu »
$ git commit -m "Merge branch 'theme'"
$ git branch -d theme
Deleted branch theme (was 94caeb6).
""")],
  notes=["Le conflit vient des deux branches qui changent la même ligne de `config.txt`.",
         "`git add` après l'édition marque le conflit comme résolu.",
         "Le commit final a deux parents ; `git branch -d` supprime seulement l'étiquette."],
  td1=dict(path="commandes.sh",
    title="Provoquer et résoudre un conflit",
    enonce="Le dépôt contient `config.txt` avec la ligne `couleur=bleu`. Fabrique un conflit volontaire entre deux branches et résous-le. " + SIM,
    consignes=["Branche `theme` : change en `couleur=vert`, commit",
               "Retour sur `main` : change en `couleur=rouge`, commit",
               "Fusionne `theme` dans `main` ; lis le conflit avec `cat`",
               "Résous en gardant `couleur=vert`, puis termine la fusion",
               "Regarde le graphe final : un commit à deux parents"],
    hints=["`git switch -c theme`, puis `echo \"couleur=vert\" > config.txt` et `git commit -am \"…\"`.",
           "Après `git merge theme`, le fichier contient les marqueurs : remplace tout son contenu.",
           "`git add config.txt` puis `git commit -m \"Merge branch 'theme'\"`."],
    checks=["Le dernier commit de `main` a 2 parents", "`config.txt` vaut `couleur=vert`, sans marqueurs"],
    files=SH(r"""
# Départ : main avec config.txt (couleur=bleu)
cat config.txt
# à toi
"""),
    solution=SH(r"""
git switch -c theme
echo "couleur=vert" > config.txt
git commit -am "theme vert"
git switch main
echo "couleur=rouge" > config.txt
git commit -am "theme rouge"
git merge theme
cat config.txt
echo "couleur=vert" > config.txt
git add config.txt
git commit -m "Merge branch 'theme'"
git log --oneline --graph --all
"""),
    run=GRUN(r"""
assert.equal(git.branch, 'main', 'Tu es sur main');
assert.equal(git.op, null, 'Aucune fusion en cours (elle est terminée)');
assert.equal(git.parents('HEAD').length, 2, 'Le dernier commit est un commit de fusion (2 parents)');
assert.equal(git.parents('HEAD')[1], git.rev('theme'), 'Son 2e parent est la pointe de theme');
assert.equal(git.at('HEAD', 'config.txt'), 'couleur=vert\n', 'config.txt vaut couleur=vert dans le commit');
assert(!/<<<<<<<|>>>>>>>|=======/.test(git.file('config.txt')), 'Plus aucun marqueur de conflit');
assert.equal(git.at('main~1', 'config.txt'), 'couleur=rouge\n', 'Le commit « rouge » est bien sur main');
assert(git.used(/git merge theme/) && git.transcript.some((t) => t.out.includes('CONFLICT')), 'Le conflit a bien eu lieu');
assert(git.clean(), 'Dossier propre');
""", r"""
git.sh('git init');
git.write('config.txt', 'couleur=bleu\n');
git.sh('git add .\ngit commit -m "config initiale"');
""")),
  tds=[
    TD(2, "Conflit réaliste : combiner deux intentions",
       "Tu as arrondi les prix sur `feature/panier`. Pendant ce temps, Léa a modifié **la même ligne** sur `main` pour écrire le calcul autrement, et a ajouté un commentaire sur la TVA. La bonne résolution n'est ni « la mienne » ni « la sienne » : il faut **combiner** les deux. " + SIM,
       ["Sur `main`, fusionne `feature/panier`",
        "Observe : `panier.js` et le commentaire de la TVA sont fusionnés automatiquement ; seule la ligne `return` est en conflit",
        "Résous `prix.js` pour obtenir exactement :\n`export const TVA = 0.2; // taux normal`\n`export function prixTTC(ht) {`\n`  return Math.round((ht + ht * TVA) * 100) / 100;`\n`}`",
        "Termine la fusion puis supprime la branche `feature/panier`"],
       SH(r"""
git log --oneline --graph --all
git merge feature/panier
cat prix.js
# à toi : écris prix.js résolu (printf "ligne 1\nligne 2\n" > prix.js), puis termine
"""),
       ["`printf` interprète `\\n` : `printf \"a\\nb\\n\" > prix.js` écrit deux lignes.",
        "Attention aux espaces : la ligne `return` commence par deux espaces.",
        "`git branch -d feature/panier` fonctionne une fois la fusion faite."],
       SH(r"""
git merge feature/panier
cat prix.js
printf "export const TVA = 0.2; // taux normal\nexport function prixTTC(ht) {\n  return Math.round((ht + ht * TVA) * 100) / 100;\n}\n" > prix.js
git add prix.js
git commit -m "Merge branch 'feature/panier'"
git branch -d feature/panier
git log --oneline --graph --all
"""),
       ["Le commentaire de Léa et l'arrondi sont tous les deux présents", "La branche est supprimée"],
       run=GRUN(r"""
assert.equal(git.op, null, 'Fusion terminée');
assert.equal(git.parents('HEAD').length, 2, 'Commit de fusion créé');
assert.equal(git.at('HEAD', 'prix.js'), 'export const TVA = 0.2; // taux normal\nexport function prixTTC(ht) {\n  return Math.round((ht + ht * TVA) * 100) / 100;\n}\n', 'prix.js combine les deux changements (au caractère près)');
assert.includes(git.at('HEAD', 'panier.js') || '', 'ajouter', 'panier.js de la branche est intégré');
assert.includes(git.at('HEAD', 'README.md') || '', 'TVA', 'Le README de Léa est conservé');
assert(!git.branches['feature/panier'], 'feature/panier est supprimée');
assert(git.clean(), 'Dossier propre');
""", r"""
git.sh('git init');
git.write('prix.js', 'export const TVA = 0.2;\nexport function prixTTC(ht) {\n  return ht * (1 + TVA);\n}\n');
git.write('panier.js', 'export const panier = [];\n');
git.write('README.md', '# Boutique\n');
git.sh('git add .\ngit commit -m "chore: initialise la boutique"\ngit switch -c feature/panier');
git.write('prix.js', 'export const TVA = 0.2;\nexport function prixTTC(ht) {\n  return Math.round(ht * (1 + TVA) * 100) / 100;\n}\n');
git.sh('git commit -am "feat: arrondit les prix au centime"');
git.write('panier.js', 'export const panier = [];\nexport const ajouter = (p) => panier.push(p);\n');
git.sh('git commit -am "feat: ajoute un produit au panier"\ngit switch main');
git.author = 'Léa';
git.write('prix.js', 'export const TVA = 0.2; // taux normal\nexport function prixTTC(ht) {\n  return ht + ht * TVA;\n}\n');
git.write('README.md', '# Boutique\nLes prix sont affichés TTC (TVA 20 %).\n');
git.sh('git commit -am "refactor: explicite le calcul de la TVA"');
git.author = 'toi';
""")),
    TD(3, "Fast-forward, --no-ff et --abort",
       "Trois branches attendent d'être intégrées à `main`. Chacune demande une stratégie différente : à toi de choisir la bonne commande pour chaque cas, en regardant le graphe. " + SIM,
       ["`fix/typo` : intègre-la **sans** commit de fusion (fast-forward)",
        "`feat/export` : intègre-la **avec** un commit de fusion, même si un fast-forward était possible (pour garder la trace de la fonctionnalité)",
        "`feat/experimental` : tente la fusion ; elle provoque un conflit et l'équipe a décidé d'attendre : **annule** proprement la fusion",
        "Termine sur `main`, dossier propre, sans fusion en cours"],
       SH(r"""
git log --oneline --graph --all
# à toi
"""),
       ["Une fusion est en fast-forward quand `main` est un ancêtre de la branche : `git merge fix/typo` le fait tout seul.",
        "`git merge --no-ff feat/export` crée un commit de fusion dans tous les cas.",
        "`git merge --abort` annule une fusion en conflit et remet le dossier comme avant."],
       SH(r"""
git merge fix/typo
git merge --no-ff feat/export -m "Merge branch 'feat/export'"
git merge feat/experimental
git merge --abort
git log --oneline --graph --all
git status
"""),
       ["`fix/typo` n'a pas de commit de fusion", "`feat/experimental` n'est pas dans `main`"],
       run=GRUN(r"""
assert.equal(git.op, null, 'Aucune fusion en cours');
assert(git.clean(), 'Dossier propre');
assert.equal(git.parents('HEAD').length, 2, 'Le dernier commit de main est une fusion');
assert.equal(git.parents('HEAD')[1], git.rev('feat/export'), '… celle de feat/export');
assert.equal(git.parents('HEAD')[0], git.rev('fix/typo'), 'Son 1er parent est fix/typo : elle a été intégrée en fast-forward (aucun commit de fusion pour elle)');
assert.equal(git.merges('main'), 1, 'Une seule fusion dans tout main');
assert(!git.isAncestor('feat/experimental', 'main'), 'feat/experimental n\'est pas intégrée');
assert.equal(git.file('README.md'), '# La Boutique\n', 'README.md a la correction de fix/typo, sans marqueurs');
assert(git.used(/merge --abort/), 'Tu as annulé la fusion avec --abort');
""", r"""
git.sh('git init');
git.write('README.md', '# Boutique\n');
git.write('index.html', '<h1>Boutique</h1>\n');
git.sh('git add .\ngit commit -m "chore: initialise"');
git.sh('git switch -c feat/experimental');
git.write('README.md', '# Boutique (beta)\n');
git.sh('git commit -am "feat: mode beta"\ngit switch main\ngit switch -c fix/typo');
git.write('README.md', '# La Boutique\n');
git.sh('git commit -am "fix: corrige le titre"\ngit switch -c feat/export');
git.write('export.js', 'export const exporter = () => {};\n');
git.sh('git add .\ngit commit -m "feat: ajoute l\'export"');
git.write('export.js', 'export const exporter = (l) => l.join(";");\n');
git.sh('git commit -am "feat: exporte en CSV"\ngit switch main');
""")),
  ])

# ============================================================ 3. Rebase
rebase = V2(v1["git-rebase"],
  prereq=[
    P("Rejouer un commit", "Réappliquer le **changement** apporté par un commit sur une autre base. Le résultat est un nouveau commit (nouvel identifiant), avec le même message."),
    P("Base d'une branche", "Le commit à partir duquel la branche a été créée. Rebaser = changer cette base."),
    P("Historique linéaire", "Un historique sans commit de fusion : une seule ligne droite, facile à lire."),
    P("Réécrire l'historique", "Remplacer des commits existants par d'autres. Sans risque sur des commits **à toi seul** ; dangereux sur des commits déjà partagés."),
  ],
  diagram=D(
    nodes=[
      N("a", 0, 0, "A", None, kind="pill"),
      N("b", 1, 0, "B", None, kind="pill"),
      N("c", 3, 0, "C", "main", kind="pill", color="accent"),
      N("d", 2, 1, "D", "avant", kind="pill", color="muted"),
      N("e", 3, 1, "E", None, kind="pill", color="muted"),
      N("d2", 4, 0, "D'", "rejoué", kind="pill", color="good"),
      N("e2", 5, 0, "E'", "feature", kind="pill", color="good"),
    ],
    edges=[E("a", "b"), E("b", "c"), E("b", "d"), E("d", "e"), E("c", "d2"), E("d2", "e2"), E("e", "e2", "git rebase main", dashed=True)],
    caption="git rebase main rejoue D et E au bout de main : on obtient D' et E', de nouveaux commits. Les anciens D et E ne sont plus tenus par aucune branche."),
  lessons=[
    L("Ce que fait vraiment `git rebase`", r"""
Tu es sur `feature`, partie de `main` il y a quelques jours. Depuis, `main` a avancé :

```
A ← B ← C          main
     ↖
      D ← E        feature
```

`git rebase main` fait ceci :

1. met de côté les changements de D et E ;
2. place `feature` sur C (le bout de `main`) ;
3. **rejoue** les changements de D puis de E, un par un : cela crée D' et E'.

```
A ← B ← C ← D' ← E'    feature
        ↑
       main
```

D' a le même message et le même changement que D, mais **un autre parent**, donc un **autre identifiant**. Les anciens D et E existent encore (le reflog les connaît) mais plus aucune branche ne pointe dessus.

Résultat : une histoire **linéaire**, comme si tu avais commencé ta branche aujourd'hui. Et la fusion dans `main` sera un simple fast-forward.
"""),
    L("Merge ou rebase ?", r"""
Les deux intègrent le travail de `main` dans ta branche ; ils diffèrent par l'historique produit.

| | `git merge main` | `git rebase main` |
|---|---|---|
| Historique | garde la vraie chronologie, ajoute un commit de fusion | réécrit tes commits, ligne droite |
| Commits existants | intacts | remplacés (nouveaux identifiants) |
| Conflits | résolus une fois, dans le commit de fusion | résolus commit par commit |
| Sur une branche partagée | sans danger | **interdit** (voir plus bas) |

La pratique courante : **rebase** pour mettre à jour ta propre branche avant la revue ; **merge** (ou « squash and merge » sur GitHub) pour intégrer dans `main`.

**La règle d'or** : ne rebase jamais des commits que d'autres ont déjà récupérés. Tu les remplaces par des copies : ceux qui travaillent sur les anciens se retrouvent avec deux versions des mêmes commits. Sur **ta** branche de fonctionnalité, rebase librement ; il faudra ensuite pousser avec `git push --force-with-lease`.
"""),
    L("Conflits pendant un rebase", r"""
Comme chaque commit est rejoué un par un, un conflit arrête le rebase **au milieu** :

```
CONFLICT (content): Merge conflict in style.css
error: could not apply 4f1a2b3... style: titres en bordeaux
```

Tu es alors en HEAD détachée, sur les commits déjà rejoués. On résout comme pour un merge, mais on termine différemment :

```bash
# éditer style.css, retirer les marqueurs
git add style.css
git rebase --continue      # termine ce commit et rejoue les suivants
```

- `git rebase --abort` : tout annuler, la branche revient exactement à son état d'avant.
- `git rebase --skip` : abandonner le commit en cours (rarement ce qu'on veut).

Attention au sens de `HEAD` dans les marqueurs : pendant un rebase, `HEAD` désigne la **base** (main + les commits déjà rejoués), et l'autre côté est **ton** commit en train d'être rejoué. C'est l'inverse d'un merge.
"""),
    L("`rebase -i` : nettoyer avant de partager", r"""
`git rebase -i main` (interactif) te laisse **éditer la liste** des commits à rejouer avant de commencer. Chaque ligne commence par une action :

| Action | Effet |
|---|---|
| `pick` | garder le commit tel quel |
| `reword` | garder le changement, changer le message |
| `squash` | fusionner avec le commit précédent, en concaténant les messages |
| `fixup` | fusionner avec le précédent, en gardant seulement le message du précédent |
| `drop` | supprimer le commit |

On peut aussi **réordonner** les lignes. Exemple : 4 commits brouillons deviennent 2 commits propres :

```
reword 1a2b3c4 ajoute formulaire     →  feat: ajoute le formulaire de contact
fixup  5d6e7f8 wip
fixup  9a8b7c6 oups
reword 3c2b1a0 ajoute validation     →  feat: valide le formulaire de contact
```

Dans un vrai terminal, Git ouvre un éditeur avec cette liste. **Dans l'atelier**, tu écris la liste juste après la commande, dans un bloc `<<EOF … EOF`, et pour `reword` ou `squash` tu donnes le nouveau message avec `-m` ; un commit peut être désigné par son identifiant **ou** par son message :

```bash
git rebase -i main <<EOF
reword ajoute formulaire -m "feat: ajoute le formulaire de contact"
fixup wip
fixup oups
reword ajoute validation -m "feat: valide le formulaire de contact"
EOF
```

**Astuce autosquash.** Pour corriger un vieux commit X : fais la correction, puis `git commit --fixup X` (crée un commit `fixup! …`), puis `git rebase -i --autosquash main` : Git place tout seul le correctif sous X avec l'action `fixup`.
"""),
  ],
  recap=[
    "`git rebase main` rejoue tes commits au bout de `main` : nouveaux identifiants, historique linéaire.",
    "Merge garde l'historique réel ; rebase le réécrit. Rebase pour **ta** branche, jamais pour des commits partagés.",
    "Conflit : résoudre → `git add` → `git rebase --continue` ; ou `git rebase --abort`.",
    "`rebase -i` : pick, reword, squash, fixup, drop, réordonner.",
    "`git commit --fixup X` + `git rebase -i --autosquash` pour corriger un vieux commit.",
  ],
  example=[F("terminal", "bash", r"""
$ git switch feature/contact
$ git log --oneline main..feature/contact     # les commits propres à la branche
9a8b7c6 ajoute validation
5d6e7f8 oups
3c2b1a0 wip
1a2b3c4 ajoute formulaire

$ git rebase -i main <<EOF
reword ajoute formulaire -m "feat: ajoute le formulaire de contact"
fixup wip
fixup oups
reword ajoute validation -m "feat: valide le formulaire de contact"
EOF
Successfully rebased and updated refs/heads/feature/contact.

$ git log --oneline main..feature/contact
e2f1c0d feat: valide le formulaire de contact
b7a6d5c feat: ajoute le formulaire de contact
""")],
  notes=["`main..feature/contact` liste les commits de la branche qui ne sont pas dans `main`.",
         "`fixup` fond « wip » et « oups » dans le commit du dessus, sans garder leurs messages.",
         "La branche est aussi rebasée sur le dernier `main` : les identifiants changent."],
  td1=dict(path="commandes.sh",
    title="Nettoyer une branche avant la revue",
    enonce="La branche `feature/contact` contient 4 commits brouillons, et `main` a avancé depuis. Nettoie-la et mets-la à jour en **une seule** commande `rebase -i`. " + SIM,
    consignes=["Va sur `feature/contact` et regarde ses commits (`git log --oneline main..feature/contact`)",
               "Avec `git rebase -i main <<EOF … EOF`, obtiens exactement 2 commits : `feat: ajoute le formulaire de contact` puis `feat: valide le formulaire de contact`",
               "« wip » et « oups » doivent être fondus dans le premier",
               "Résultat : historique linéaire, au-dessus du dernier commit de `main`"],
    hints=["Ordre des lignes = ordre des commits. `fixup` fond un commit dans celui de la ligne au-dessus.",
           "`reword <commit> -m \"nouveau message\"` : dans l'atelier, le nouveau message se donne avec `-m`.",
           "Un commit peut être désigné par son message exact : `fixup wip`."],
    checks=["2 commits sur la branche, avec les bons messages", "La branche contient le dernier commit de `main`"],
    files=SH(r"""
git switch feature/contact
git log --oneline main..feature/contact
# à toi : git rebase -i main <<EOF
# ...
# EOF
"""),
    solution=SH(r"""
git switch feature/contact
git log --oneline main..feature/contact
git rebase -i main <<EOF
reword ajoute formulaire -m "feat: ajoute le formulaire de contact"
fixup wip
fixup oups
reword ajoute validation -m "feat: valide le formulaire de contact"
EOF
git log --oneline --graph --all
"""),
    run=GRUN(r"""
assert.equal(git.op, null, 'Aucun rebase en cours');
assert.equal(git.branch, 'feature/contact', 'Tu es sur feature/contact');
assert.equal(JSON.stringify(git.range('main', 'feature/contact')), JSON.stringify(['feat: ajoute le formulaire de contact', 'feat: valide le formulaire de contact']), 'Exactement 2 commits, dans le bon ordre, avec les bons messages');
assert(git.isAncestor('main', 'feature/contact'), 'La branche est au-dessus du dernier commit de main');
assert(git.isLinear('feature/contact'), 'Historique linéaire (aucune fusion)');
assert.equal(git.at('feature/contact~1', 'contact.html'), '<form>\n  <input name="email">\n  <button>Envoyer</button>\n</form>\n', 'Le premier commit contient le formulaire final (wip et oups inclus)');
assert(git.at('feature/contact~1', 'validation.js') === null && git.at('feature/contact', 'validation.js') !== null, 'validation.js arrive seulement dans le 2e commit');
assert(git.at('feature/contact', 'README.md') !== null, 'Le README ajouté sur main est présent');
""", r"""
git.sh('git init');
git.write('index.html', '<h1>Site</h1>\n');
git.sh('git add .\ngit commit -m "chore: initialise le site"\ngit switch -c feature/contact');
git.write('contact.html', '<form>\n</form>\n');
git.sh('git add .\ngit commit -m "ajoute formulaire"');
git.write('contact.html', '<form>\n  <input name="email">\n  <buton>Envoyer</buton>\n</form>\n');
git.sh('git commit -am "wip"');
git.write('contact.html', '<form>\n  <input name="email">\n  <button>Envoyer</button>\n</form>\n');
git.sh('git commit -am "oups"');
git.write('validation.js', 'export const valide = (email) => email.includes("@");\n');
git.sh('git add .\ngit commit -m "ajoute validation"\ngit switch main');
git.write('README.md', '# Site vitrine\n');
git.sh('git add .\ngit commit -m "docs: ajoute le README"');
""")),
  tds=[
    TD(2, "Rebase avec conflit",
       "Ta branche `feature/titres` met les titres en bordeaux. Pendant ce temps, `main` a changé la même ligne. Mets ta branche à jour par **rebase** et résous le conflit en gardant **ta** couleur. " + SIM,
       ["Sur `feature/titres`, lance `git rebase main`",
        "Le conflit apparaît dans `style.css` : remarque que pendant un rebase, `HEAD` désigne `main`",
        "Résous : `style.css` doit valoir `body { font-size: 16px; }` puis `h1 { color: darkred; }`",
        "Continue le rebase jusqu'au bout",
        "Résultat : 2 commits linéaires au-dessus de `main`"],
       SH(r"""
git switch feature/titres
git rebase main
cat style.css
# à toi
"""),
       ["Après la résolution : `git add style.css` puis `git rebase --continue` (pas `git commit`).",
        "Le 2e commit de la branche (titres.css) se rejoue sans conflit après le `--continue`.",
        "En cas de doute : `git rebase --abort` et on recommence."],
       SH(r"""
git switch feature/titres
git rebase main
cat style.css
printf "body { font-size: 16px; }\nh1 { color: darkred; }\n" > style.css
git add style.css
git rebase --continue
git log --oneline --graph --all
"""),
       ["Plus de rebase en cours", "`main` est un ancêtre de la branche"],
       run=GRUN(r"""
assert.equal(git.op, null, 'Le rebase est terminé');
assert.equal(git.branch, 'feature/titres', 'Tu es sur feature/titres');
assert(git.isAncestor('main', 'feature/titres') && git.isLinear('feature/titres'), 'Branche linéaire au-dessus de main');
assert.equal(git.range('main', 'feature/titres').length, 2, '2 commits sur la branche');
assert.equal(git.at('feature/titres', 'style.css'), 'body { font-size: 16px; }\nh1 { color: darkred; }\n', 'style.css garde ta couleur, sans marqueurs');
assert(git.at('feature/titres', 'titres.css') !== null, 'Le 2e commit (titres.css) a été rejoué');
assert(git.transcript.some((t) => t.out.includes('CONFLICT')), 'Le conflit a bien eu lieu');
assert(git.used(/rebase --continue/), 'Tu as utilisé git rebase --continue');
""", r"""
git.sh('git init');
git.write('style.css', 'body { font-size: 16px; }\nh1 { color: navy; }\n');
git.sh('git add .\ngit commit -m "style: feuille de style de base"\ngit switch -c feature/titres');
git.write('style.css', 'body { font-size: 16px; }\nh1 { color: darkred; }\n');
git.sh('git commit -am "style: titres en bordeaux"');
git.write('titres.css', 'h1 { text-transform: uppercase; }\n');
git.sh('git add .\ngit commit -m "style: titres en majuscules"\ngit switch main');
git.author = 'Léa';
git.write('style.css', 'body { font-size: 16px; }\nh1 { color: #1a1a5e; }\n');
git.sh('git commit -am "style: bleu nuit plus foncé"');
git.author = 'toi';
""")),
    TD(3, "Corriger un vieux commit avec --fixup",
       "Sur `feat/api`, le **premier** des trois commits contient une faute dans l'URL de l'API (`htps://`). Corrige-la de façon à ce que l'historique ait l'air d'avoir toujours été juste : le correctif doit être fondu **dans le premier commit**, pas ajouté à la fin. " + SIM,
       ["Corrige `api.js` (`https://api.exemple.com`)",
        "Crée un commit de correction ciblé avec `git commit --fixup <le premier commit>`",
        "Lance `git rebase -i --autosquash main` : Git range le correctif tout seul",
        "Résultat : toujours 3 commits, mêmes messages, et le premier contient l'URL correcte"],
       SH(r"""
git switch feat/api
git log --oneline main..feat/api
cat api.js
# à toi
"""),
       ["Le premier commit de la branche est `HEAD~2` (ou son identifiant, visible dans le graphe).",
        "`git commit -a --fixup HEAD~2` crée un commit nommé `fixup! feat(api): ajoute le client HTTP`.",
        "Avec `--autosquash`, pas besoin d'écrire la liste : `git rebase -i --autosquash main` suffit."],
       SH(r"""
git switch feat/api
cat api.js
echo "export const BASE = 'https://api.exemple.com';" > api.js
git commit -a --fixup HEAD~2
git rebase -i --autosquash main
git log --oneline main..feat/api
"""),
       ["Aucun commit « fixup! » ne reste", "Le premier commit contient l'URL corrigée"],
       run=GRUN(r"""
assert.equal(git.op, null, 'Aucun rebase en cours');
assert.equal(JSON.stringify(git.range('main', 'feat/api')), JSON.stringify(['feat(api): ajoute le client HTTP', 'feat(api): liste les produits', 'test(api): couvre la liste']), 'Toujours 3 commits, mêmes messages, même ordre');
assert(!git.log('feat/api').some((m) => m.startsWith('fixup!')), 'Plus aucun commit « fixup! »');
assert.includes(git.at('feat/api~2', 'api.js') || '', 'https://', 'Le premier commit contient l\'URL corrigée');
assert(git.used(/--fixup/) && git.used(/--autosquash/), 'Tu as utilisé --fixup puis --autosquash');
assert(git.clean(), 'Dossier propre');
""", r"""
git.sh('git init');
git.write('README.md', '# Boutique\n');
git.sh('git add .\ngit commit -m "chore: initialise"\ngit switch -c feat/api');
git.write('api.js', "export const BASE = 'htps://api.exemple.com';\n");
git.sh('git add .\ngit commit -m "feat(api): ajoute le client HTTP"');
git.write('produits.js', "import { BASE } from './api';\nexport const liste = () => fetch(BASE + '/produits');\n");
git.sh('git add .\ngit commit -m "feat(api): liste les produits"');
git.write('produits.test.js', "test('liste', () => {});\n");
git.sh('git add .\ngit commit -m "test(api): couvre la liste"');
""")),
  ])

# ============================================================ 4. Revenir en arrière
revenir = V2(v1["git-revenir"],
  prereq=[
    P("Annuler / défaire", "Selon l'endroit où se trouve l'erreur (dossier de travail, zone de préparation, commit local, commit partagé), la bonne commande n'est pas la même."),
    P("Commit poussé", "Un commit envoyé sur le dépôt distant (GitHub). D'autres ont pu le récupérer : on ne le réécrit plus, on le **compense**."),
    P("reflog", "Le journal de **tous** les endroits où HEAD est passé (commits, reset, rebase, checkout…). Il garde la trace des commits « perdus » pendant environ 90 jours."),
    P("`HEAD@{n}`", "« Là où était HEAD il y a n mouvements », d'après le reflog. `HEAD@{1}` = la position juste avant le dernier mouvement."),
  ],
  diagram=D(
    nodes=[
      N("a", 0, 0, "Modif non commitée", "dossier ou staging", kind="doc"),
      N("b", 0, 1, "Commit local", "pas encore poussé", kind="doc", color="warn"),
      N("c", 0, 2, "Commit déjà poussé", "partagé", kind="doc", color="bad"),
      N("ra", 1, 0, "git restore", "[--staged] fichier", kind="pill", color="good"),
      N("rb", 1, 1, "git reset / --amend", "réécrit l'historique", kind="pill", color="warn"),
      N("rc", 1, 2, "git revert", "nouveau commit inverse", kind="pill", color="accent"),
      N("rl", 2, 1, "Perdu quelque chose ?", "git reflog", kind="note", color="good"),
    ],
    edges=[E("a", "ra"), E("b", "rb"), E("c", "rc"), E("rb", "rl", dashed=True)],
    caption="La question à se poser : où est l'erreur, et quelqu'un d'autre a-t-il pu la récupérer ? Partagé → revert ; local → reset ou amend ; et le reflog rattrape presque tout."),
  lessons=[
    L("Avant le commit : `restore`", r"""
Tant que rien n'est commité, `git restore` suffit :

```bash
git restore app.js             # jeter mes modifications de app.js (retour à la version préparée/commitée)
git restore --staged app.js    # retirer app.js de la zone de préparation (les modifications restent sur le disque)
git restore .                  # jeter toutes les modifications non préparées
```

Attention : `git restore fichier` **efface** tes modifications non commitées, définitivement (elles n'ont jamais été dans Git, le reflog ne peut rien pour elles).

On voit encore souvent l'ancienne syntaxe `git checkout -- fichier` (même effet que `git restore`) et `git reset fichier` (même effet que `git restore --staged`).
"""),
    L("Le dernier commit : `--amend`", r"""
Faute dans le message, ou fichier oublié dans le dernier commit ?

```bash
git commit --amend -m "fix: corrige le total"    # nouveau message
git add oubli.js
git commit --amend --no-edit                     # ajoute le fichier, garde le message
```

`--amend` ne modifie pas le commit : il le **remplace** par un nouveau (nouvel identifiant). C'est donc une réécriture : à réserver aux commits pas encore poussés.
"""),
    L("Défaire des commits locaux : `reset`", r"""
`git reset <commit>` **déplace l'étiquette de la branche** vers un commit plus ancien. Les commits d'après ne sont plus dans la branche. Trois variantes selon ce qu'on fait de leurs changements :

| Commande | Branche | Zone de préparation | Dossier de travail |
|---|---|---|---|
| `git reset --soft HEAD~2` | recule | **garde** les changements (prêts à commiter) | inchangé |
| `git reset HEAD~2` (mixed) | recule | vidée | **garde** les changements |
| `git reset --hard HEAD~2` | recule | vidée | **remis** à l'état du commit : changements perdus |

Usage typique de `--soft` : « mes 3 derniers commits sont des brouillons, je veux en faire un seul propre » → `git reset --soft HEAD~3` puis `git commit -m "…"`.

`--hard` est la seule commande vraiment dangereuse ici : elle écrase le dossier de travail. Les **commits** restent récupérables (reflog), mais pas les modifications non commitées.
"""),
    L("Commit déjà poussé : `revert`", r"""
Si le commit est sur GitHub, d'autres l'ont peut-être déjà. Le supprimer de l'historique (reset + push forcé) casserait leur travail. On le **compense** :

```bash
git revert a1b2c3d
```

Git crée un **nouveau** commit qui fait exactement l'inverse de `a1b2c3d`. L'historique ne perd rien : on voit l'erreur et sa correction. C'est la seule méthode sûre sur `main`.

Pour annuler un **commit de fusion**, il faut dire quel parent est la « ligne principale » : `git revert -m 1 <merge>` (1 = le premier parent, en général `main`). Le résultat retire tout ce que la branche fusionnée avait apporté.
"""),
    L("Le filet de sécurité : `reflog`", r"""
Un `reset --hard` de trop, une branche supprimée, un rebase raté ? Tant que les changements ont été **commités** un jour, ils sont presque toujours récupérables :

```bash
$ git reflog
69aba98 HEAD@{0}: reset: moving to HEAD~2
8c0b8bb HEAD@{1}: commit: feat: trie les résultats      ← là où j'étais avant le reset
3033dc4 HEAD@{2}: commit: feat: ajoute les filtres
```

Puis on revient où on veut :

```bash
git reset --hard HEAD@{1}          # remettre la branche là où elle était
git branch sauvetage 8c0b8bb       # ou : poser une nouvelle branche sur un commit retrouvé
```

Le reflog est **local** (il n'est pas poussé) et chaque nouveau mouvement décale les numéros `HEAD@{n}` : relis-le juste avant de t'en servir.
"""),
  ],
  recap=[
    "Non commité : `git restore fichier` (jeter) / `git restore --staged fichier` (dé-préparer).",
    "Dernier commit local : `git commit --amend`.",
    "Commits locaux : `git reset --soft | --mixed | --hard <commit>` (seul `--hard` touche au disque).",
    "Commit poussé : `git revert <commit>` (et `-m 1` pour une fusion).",
    "Perdu ? `git reflog`, puis `git reset --hard HEAD@{n}` ou `git branch nom <id>`.",
  ],
  example=[F("terminal", "bash", r"""
$ git log --oneline
d4c3b2a (HEAD -> main) wip 2
c3b2a1f wip 1
b2a1f0e feat: ajoute le panier

$ git reset --soft HEAD~2            # recule de 2 commits, garde les changements préparés
$ git commit -m "feat: ajoute l'export CSV"

$ git revert b2a1f0e --no-edit       # le panier était déjà en production
[main 7e6d5c4] Revert "feat: ajoute le panier"

$ git reset --hard HEAD~1            # oups, trop loin…
$ git reflog
a9b8c7d HEAD@{0}: reset: moving to HEAD~1
7e6d5c4 HEAD@{1}: revert: Revert "feat: ajoute le panier"
$ git reset --hard HEAD@{1}          # et on revient
""")],
  notes=["`--soft` garde les changements des deux « wip » dans la zone de préparation : un seul commit propre.",
         "`revert` ajoute un commit inverse au lieu de réécrire ce qui est déjà partagé.",
         "Le reflog retrouve la position d'avant le `reset --hard`."],
  td1=dict(path="commandes.sh",
    title="Le parcours du combattant",
    enonce="Le dépôt est dans un sale état. Répare chaque situation avec la bonne commande, dans l'ordre. " + SIM,
    consignes=["`app.js` a été cassé dans le dossier de travail (pas commité) : annule cette modification",
               "Les deux derniers commits « wip 1 » et « wip 2 » doivent devenir **un seul** commit `feat: ajoute l'export`",
               "Oups, le message devait être `feat: ajoute l'export CSV` : corrige-le",
               "Le commit `feat: ajoute le panier` était déjà en production et pose problème : annule-le **sans réécrire** l'historique",
               "Résultat attendu (`git log --oneline`) : Revert « panier », export CSV, panier, initialise"],
    hints=["`git restore app.js`.",
           "`git reset --soft HEAD~2` puis `git commit -m \"…\"`.",
           "`git commit --amend -m \"…\"`, puis `git revert HEAD~1 --no-edit` (le panier est juste sous l'export)."],
    checks=["Plus aucun « wip » dans l'historique", "Le panier est annulé par un commit Revert"],
    files=SH(r"""
git status
git log --oneline
# à toi
"""),
    solution=SH(r"""
git status
git restore app.js
git reset --soft HEAD~2
git commit -m "feat: ajoute l'export"
git commit --amend -m "feat: ajoute l'export CSV"
git revert HEAD~1 --no-edit
git log --oneline
"""),
    run=GRUN(r"""
assert.equal(JSON.stringify(git.log()), JSON.stringify(['Revert "feat: ajoute le panier"', "feat: ajoute l'export CSV", 'feat: ajoute le panier', 'chore: initialise']), 'Historique attendu : Revert, export CSV, panier, initialise');
assert.equal(git.file('app.js'), 'export const total = (a, b) => a + b;\n', 'app.js a retrouvé sa version commitée');
assert.includes(git.at('HEAD~1', 'export.js') || '', 'join', 'Le commit export contient le travail des deux « wip »');
assert(git.at('HEAD', 'panier.js') === null, 'panier.js est retiré par le revert');
assert(git.at('HEAD~2', 'panier.js') !== null, '… mais le commit du panier existe toujours dans l\'historique');
assert(git.used(/restore/), 'Tu as utilisé git restore');
assert(git.clean(), 'Dossier propre');
""", r"""
git.sh('git init');
git.write('app.js', 'export const total = (a, b) => a + b;\n');
git.sh('git add .\ngit commit -m "chore: initialise"');
git.write('panier.js', 'export const panier = [];\n');
git.sh('git add .\ngit commit -m "feat: ajoute le panier"');
git.write('export.js', 'export function exporter() {}\n');
git.sh('git add .\ngit commit -m "wip 1"');
git.write('export.js', "export function exporter(lignes) {\n  return lignes.join(';');\n}\n");
git.sh('git commit -am "wip 2"');
git.write('app.js', 'CASSÉ\n');
""")),
  tds=[
    TD(2, "Sauvetage avec le reflog",
       "Quelqu'un (toi, hier soir) a fait deux bêtises : un `git reset --hard HEAD~2` sur `main` qui a fait disparaître deux commits, et la suppression de la branche `experience` qui contenait un essai. Retrouve tout grâce au reflog. " + SIM,
       ["Lis le reflog (`git reflog`) et repère où était `main` avant le reset",
        "Remets `main` à cet endroit : les commits « ajoute les filtres » et « trie les résultats » reviennent",
        "Recrée la branche `experience` sur le commit « test: essai de cache »",
        "Termine sur `main`, dossier propre"],
       SH(r"""
git log --oneline
git reflog
# à toi
"""),
       ["Lance d'abord le script avec seulement `git reflog`, lis la sortie, puis écris la suite : c'est exactement la démarche réelle.",
        "`git reset --hard HEAD@{1}` revient à la position juste avant le dernier mouvement.",
        "Chaque mouvement décale les numéros : après le reset, relis le reflog, ou utilise l'identifiant du commit : `git branch experience <id>`."],
       SH(r"""
git reflog
git reset --hard HEAD@{1}
git reflog
git branch experience HEAD@{3}
git log --oneline --graph --all
"""),
       ["`main` a de nouveau 4 commits", "`experience` pointe sur « test: essai de cache »"],
       run=GRUN(r"""
assert.equal(JSON.stringify(git.log('main')), JSON.stringify(['feat: trie les résultats', 'feat: ajoute les filtres', 'feat: ajoute la recherche', 'chore: initialise']), 'main a retrouvé ses 4 commits');
assert(git.branches.experience, 'La branche experience existe à nouveau');
assert.equal(git.msg('experience'), 'test: essai de cache', 'experience pointe sur « test: essai de cache »');
assert.equal(git.parents('experience')[0], git.rev('main'), 'Son parent est le dernier commit de main');
assert(git.branch === 'main' && git.clean(), 'Sur main, dossier propre');
assert(git.used(/reflog/), 'Tu as consulté le reflog');
""", r"""
git.sh('git init');
git.write('recherche.js', 'export const chercher = (q) => [];\n');
git.sh('git add .\ngit commit -m "chore: initialise"');
git.write('recherche.js', 'export const chercher = (q, data) => data.filter((d) => d.includes(q));\n');
git.sh('git commit -am "feat: ajoute la recherche"');
git.write('filtres.js', 'export const filtres = {};\n');
git.sh('git add .\ngit commit -m "feat: ajoute les filtres"');
git.write('tri.js', 'export const trier = (l) => [...l].sort();\n');
git.sh('git add .\ngit commit -m "feat: trie les résultats"\ngit switch -c experience');
git.write('cache.js', 'export const cache = new Map();\n');
git.sh('git add .\ngit commit -m "test: essai de cache"\ngit switch main\ngit branch -D experience\ngit reset --hard HEAD~2');
""")),
    TD(3, "Annuler une fusion déjà en production",
       "La branche `feat/promo` a été fusionnée dans `main` **et poussée**. La promo pose un problème en production : il faut la retirer tout de suite, sans réécrire l'historique partagé (pas de reset, pas de push forcé). " + SIM,
       ["Repère le commit de fusion de `feat/promo` dans `main`",
        "Annule-le avec `git revert` (une fusion a deux parents : précise lequel est la ligne principale)",
        "Pousse le résultat sur `origin`",
        "`promo.js` et `compte-a-rebours.js` doivent disparaître, le README de `main` doit rester"],
       SH(r"""
git log --oneline --graph --all
# à toi
"""),
       ["Le commit de fusion est le dernier de `main` : `HEAD`.",
        "`git revert -m 1 HEAD --no-edit` : `-m 1` dit que le 1er parent (main) est la ligne à garder.",
        "Un simple `git push` suffit : on a seulement **ajouté** un commit."],
       SH(r"""
git log --oneline --graph --all
git revert -m 1 HEAD --no-edit
git push
git log --oneline --graph --all
"""),
       ["Le commit de fusion est toujours dans l'historique", "Aucun push forcé"],
       run=GRUN(r"""
assert.includes(git.msg('HEAD'), "Revert \"Merge branch 'feat/promo'\"", 'Le dernier commit annule la fusion');
assert(git.at('HEAD', 'promo.js') === null && git.at('HEAD', 'compte-a-rebours.js') === null, 'promo.js et compte-a-rebours.js ont disparu');
assert(git.at('HEAD', 'README.md') !== null, 'Le README de main est toujours là');
assert.equal(git.merges('HEAD'), 1, 'Le commit de fusion est toujours dans l\'historique (rien n\'est réécrit)');
assert.equal(git.remote.branches.main, git.rev('main'), 'origin/main est à jour');
assert(!git.used(/--force|push -f|reset/), 'Ni reset ni push forcé');
""", r"""
git.sh('git init');
git.write('index.html', '<h1>Boutique</h1>\n');
git.sh('git add .\ngit commit -m "chore: initialise"\ngit switch -c feat/promo');
git.write('promo.js', 'export const promo = "-20 %";\n');
git.sh('git add .\ngit commit -m "feat: bannière promo"');
git.write('compte-a-rebours.js', 'export const fin = "2026-12-01";\n');
git.sh('git add .\ngit commit -m "feat: compte à rebours"\ngit switch main');
git.write('README.md', '# Boutique\n');
git.sh('git add .\ngit commit -m "docs: README"\ngit merge --no-ff feat/promo -m "Merge branch \'feat/promo\'"');
git.cloneRemote();
""")),
  ])

# ============================================================ 5. Conventional Commits
CC = r"/^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9-]+\))?!?: \S.{0,71}$/"

commits = V2(v1["git-commits"],
  prereq=[
    P("Message de commit", "La première ligne (le **titre**, court) résume le changement ; une ligne vide ; puis un **corps** optionnel qui explique le pourquoi."),
    P("Commit atomique", "Un commit = **un** changement cohérent (un correctif, une fonctionnalité). Facile à relire, à annuler (revert), à retrouver (bisect)."),
    P("Versionnage sémantique (SemVer)", "Un numéro `MAJEUR.MINEUR.CORRECTIF` : correctif → `1.4.1`, nouvelle fonctionnalité compatible → `1.5.0`, changement incompatible → `2.0.0`."),
    P("Impératif", "Écrire l'action comme un ordre : « ajoute », « corrige », « supprime » (et pas « ajouté », « j'ai corrigé »)."),
  ],
  diagram=D(
    nodes=[
      N("t", 0, 0, "feat(panier)!:", "type(portée)!", kind="pill", color="accent"),
      N("d", 1, 0, "description", "impératif, ≤ 72 car.", kind="doc"),
      N("b", 2, 0, "corps", "le pourquoi (optionnel)", kind="doc", color="muted"),
      N("f", 3, 0, "pied", "BREAKING CHANGE: …\nCloses #12", kind="doc", color="warn"),
      N("v1", 0, 1, "fix", "→ 1.4.1 (correctif)", kind="pill", color="good"),
      N("v2", 1, 1, "feat", "→ 1.5.0 (mineure)", kind="pill", color="good"),
      N("v3", 2, 1, "BREAKING (!)", "→ 2.0.0 (majeure)", kind="pill", color="bad"),
    ],
    edges=[E("t", "d"), E("d", "b"), E("b", "f")],
    caption="Anatomie d'un message Conventional Commits, et l'effet de chaque type sur le numéro de version."),
  lessons=[
    L("Pourquoi une convention", r"""
`git log` est la documentation de **pourquoi** le code a changé. Comparé à :

```
modifs
fix bug
update
ajout truc
```

ceci se lit sans ouvrir un seul fichier :

```
feat(profil): ajoute la page profil
fix(profil): corrige la taille de l'avatar
docs(profil): documente la page profil
test(profil): couvre la page profil
```

La convention **Conventional Commits** est aussi lisible par des outils : génération automatique du CHANGELOG, calcul du prochain numéro de version, filtres (`git log --grep "^fix"`).
"""),
    L("Le format", r"""
```
type(portée optionnelle)!: description

corps optionnel : pourquoi ce changement, ce qui a été envisagé

pied optionnel : BREAKING CHANGE: …   /   Closes #42
```

Les types courants :

| Type | Pour |
|---|---|
| `feat` | une nouvelle fonctionnalité pour l'utilisateur |
| `fix` | une correction de bug |
| `docs` | la documentation seulement |
| `style` | mise en forme (espaces, point-virgule, CSS purement visuel) sans changer le comportement |
| `refactor` | réorganiser le code sans changer le comportement |
| `perf` | améliorer les performances |
| `test` | ajouter ou corriger des tests |
| `build` / `ci` | outils de build, dépendances, pipeline |
| `chore` | maintenance qui ne touche pas au code livré (config, .gitignore) |

Règles pour la description : **impératif**, minuscule au début, **pas de point final**, 72 caractères maximum. La **portée** (`panier`, `api`, `auth`) précise la zone touchée.
"""),
    L("Un commit = un changement", r"""
Un bon message est impossible si le commit mélange tout. « Corrige le total, ajoute l'export et met à jour le README » = **trois** commits.

Pour découper un dossier de travail qui contient plusieurs changements, on prépare **fichier par fichier** :

```bash
git add total.js       && git commit -m "fix(panier): corrige l'arrondi du total"
git add export.js      && git commit -m "feat(export): exporte le panier en CSV"
git add README.md      && git commit -m "docs: explique l'export CSV"
```

(`git add -p` permet même de choisir **morceau par morceau** à l'intérieur d'un fichier, dans un vrai terminal.)

Bénéfices concrets : la revue est plus facile, `git revert` peut annuler le correctif sans retirer la fonctionnalité, et `git bisect` pointe un changement précis.
"""),
    L("Changements incompatibles et versions", r"""
Un changement qui **casse** l'existant (fonction renommée, champ d'API supprimé) se signale de deux façons, souvent ensemble :

```bash
git commit -m "feat(api)!: renomme calculer() en calculerTotal()" \
           -m "BREAKING CHANGE: calculer() n'existe plus, utilise calculerTotal()."
```

- le `!` juste avant les deux-points ;
- un pied de message `BREAKING CHANGE: …` qui explique quoi faire.

(Chaque `-m` ajoute un paragraphe : le premier est le titre, les suivants le corps et le pied.)

Lien avec les versions (SemVer), depuis la dernière version publiée :

- au moins un changement incompatible → version **majeure** (`1.4.0` → `2.0.0`) ;
- sinon au moins un `feat` → version **mineure** (`1.4.0` → `1.5.0`) ;
- sinon que des `fix` → **correctif** (`1.4.0` → `1.4.1`).

On marque la version avec un **tag annoté** : `git tag -a v2.0.0 -m "Version 2.0.0"`.
"""),
  ],
  recap=[
    "Format : `type(portée)!: description` + corps + pied.",
    "Types : feat, fix, docs, style, refactor, perf, test, build, ci, chore.",
    "Description à l'impératif, minuscule, sans point, ≤ 72 caractères.",
    "Un commit = un changement : prépare fichier par fichier.",
    "`!` / `BREAKING CHANGE:` → version majeure ; feat → mineure ; fix → correctif ; tag annoté `git tag -a`.",
  ],
  example=[F("terminal", "bash", r"""
$ git log --oneline v1.4.0..HEAD
9c8b7a6 feat(api)!: renomme calculer() en calculerTotal()
8b7a6f5 feat: ajoute la devise
7a6f5e4 fix: gère les montants négatifs

$ git show --no-patch HEAD
    feat(api)!: renomme calculer() en calculerTotal()

    BREAKING CHANGE: calculer() n'existe plus, utilise calculerTotal().

# un changement incompatible depuis v1.4.0 → version majeure
$ git tag -a v2.0.0 -m "Version 2.0.0"
""")],
  notes=["`v1.4.0..HEAD` : les commits depuis la dernière version.",
         "Le `!` et le pied `BREAKING CHANGE:` signalent la rupture.",
         "Avec un changement incompatible, la version suivante est 2.0.0, même s'il y a aussi des feat et des fix."],
  td1=dict(path="commandes.sh",
    title="Réécrire des messages",
    enonce="La branche `feat/profil` a 4 commits aux messages inutilisables. Voici ce que fait chacun, dans l'ordre : **modifs** crée la page profil (nouvelle fonctionnalité) ; **fix bug** corrige la taille de l'avatar ; **update** documente la page profil dans le README ; **ajout truc** ajoute les tests de la page profil. Réécris-les au format Conventional Commits avec `rebase -i`. " + SIM,
    consignes=["Va sur `feat/profil` ; `git show <commit>` montre ce que change chaque commit",
               "Avec `git rebase -i main <<EOF … EOF` et 4 lignes `reword … -m \"…\"`, donne à chaque commit le bon type et la portée `profil`",
               "Descriptions à l'impératif, minuscule, sans point final",
               "Garde l'ordre et le contenu des commits"],
    hints=["Les types attendus, dans l'ordre : feat, fix, docs, test.",
           "Une ligne : `reword modifs -m \"feat(profil): ajoute la page profil\"`.",
           "Le titre suit le format : `type(portée): description`."],
    checks=["4 messages valides, types feat, fix, docs, test", "Mêmes fichiers dans chaque commit"],
    files=SH(r"""
git switch feat/profil
git log --oneline main..feat/profil
# à toi : git rebase -i main <<EOF
# ...
# EOF
"""),
    solution=SH(r"""
git switch feat/profil
git rebase -i main <<EOF
reword modifs -m "feat(profil): ajoute la page profil"
reword fix bug -m "fix(profil): corrige la taille de l'avatar"
reword update -m "docs(profil): documente la page profil"
reword ajout truc -m "test(profil): couvre la page profil"
EOF
git log --oneline main..feat/profil
"""),
    run=GRUN(r"""
const msgs = git.range('main', 'feat/profil');
assert.equal(msgs.length, 4, '4 commits sur la branche');
const re = """ + CC + r""";
msgs.forEach((m, i) => assert(re.test(m), 'Commit ' + (i + 1) + ' au format Conventional Commits : « ' + m + ' »'));
assert.equal(JSON.stringify(msgs.map((m) => m.split(/[(:!]/)[0])), JSON.stringify(['feat', 'fix', 'docs', 'test']), 'Types dans l\'ordre : feat, fix, docs, test');
assert(msgs.every((m) => /\(profil\)/.test(m)), 'Portée « profil » sur chaque commit');
assert(msgs.every((m) => !/\.$/.test(m) && /: [a-zà-ÿ]/.test(m)), 'Descriptions en minuscule, sans point final');
assert.equal(JSON.stringify(['feat/profil~3', 'feat/profil~2', 'feat/profil~1', 'feat/profil'].map((r) => git.touched(r).join())), JSON.stringify(['profil.js', 'avatar.js', 'README.md', 'profil.test.js']), 'Chaque commit garde son contenu');
""", r"""
git.sh('git init');
git.write('README.md', '# Appli\n');
git.write('avatar.js', 'export const taille = 640;\n');
git.sh('git add .\ngit commit -m "chore: initialise"\ngit switch -c feat/profil');
git.write('profil.js', 'export const Profil = () => "profil";\n');
git.sh('git add .\ngit commit -m "modifs"');
git.write('avatar.js', 'export const taille = 64;\n');
git.sh('git commit -am "fix bug"');
git.write('README.md', '# Appli\n\n## Page profil\nAffiche le nom et l\'avatar.\n');
git.sh('git commit -am "update"');
git.write('profil.test.js', 'test("profil", () => {});\n');
git.sh('git add .\ngit commit -m "ajout truc"');
""")),
  tds=[
    TD(2, "Découper un commit fourre-tout",
       "Tu as travaillé tout l'après-midi sans commiter. Le dossier contient trois changements sans rapport : un **correctif** d'arrondi dans `total.js`, une **nouvelle fonctionnalité** d'export dans `export.js` (nouveau fichier), et de la **documentation** dans `README.md`. Fais-en trois commits atomiques. " + SIM,
       ["Un commit par fichier, chacun avec le bon type (fix, feat, docs)",
        "Messages au format Conventional Commits, avec une portée quand c'est pertinent",
        "À la fin, dossier propre"],
       SH(r"""
git status
git diff
# à toi
"""),
       ["`git add total.js` puis `git commit -m \"fix(panier): …\"` : seul ce fichier part dans le commit.",
        "`export.js` est un nouveau fichier : il faut l'ajouter explicitement.",
        "L'ordre des commits n'a pas d'importance ici, la séparation si."],
       SH(r"""
git status
git add total.js
git commit -m "fix(panier): corrige l'arrondi du total"
git add export.js
git commit -m "feat(export): exporte le panier en CSV"
git add README.md
git commit -m "docs: explique l'export CSV"
git log --oneline
"""),
       ["Chaque commit ne touche qu'un fichier", "Le type correspond au contenu"],
       run=GRUN(r"""
const re = """ + CC + r""";
const ids = git.ids().slice(0, 3);
assert.equal(git.log().length, 4, '3 nouveaux commits');
const type = { 'total.js': 'fix', 'export.js': 'feat', 'README.md': 'docs' };
const vus = new Set();
ids.forEach((id) => {
  const t = git.touched(id); const m = git.msg(id).split('\n')[0];
  assert(t.length === 1, 'Le commit « ' + m + ' » ne touche qu\'un fichier (' + t.join(', ') + ')');
  assert(re.test(m), '« ' + m + ' » est au bon format');
  if (t.length === 1) { vus.add(t[0]); assert(m.startsWith(type[t[0]]), t[0] + ' → type ' + type[t[0]]); }
});
assert.equal(vus.size, 3, 'Les trois fichiers ont chacun leur commit');
assert(git.clean() && git.status().untracked.length === 0, 'Dossier propre');
""", r"""
git.sh('git init');
git.write('total.js', 'export const total = (l) => Math.floor(l.reduce((s, x) => s + x, 0));\n');
git.write('README.md', '# Panier\n');
git.sh('git add .\ngit commit -m "chore: initialise"');
git.write('total.js', 'export const total = (l) => Math.round(l.reduce((s, x) => s + x, 0) * 100) / 100;\n');
git.write('export.js', 'export const versCSV = (l) => l.join(";");\n');
git.write('README.md', '# Panier\n\n## Export\nLe panier peut être exporté en CSV.\n');
""")),
    TD(3, "Changement incompatible et nouvelle version",
       "La bibliothèque est en `v1.4.0`. Depuis, il y a eu un `fix` et un `feat`. Tu viens de **renommer** la fonction publique `calculer()` en `calculerTotal()` (le changement est dans le dossier de travail) : les projets qui utilisent la bibliothèque vont casser. Commite ce changement correctement et publie la bonne version. " + SIM,
       ["Commite `api.js` avec un titre `feat(api)!: …` **et** un pied `BREAKING CHANGE: …` qui dit quoi utiliser à la place",
        "Détermine le prochain numéro de version selon SemVer depuis `v1.4.0`",
        "Crée un **tag annoté** pour cette version sur ton commit (message `Version x.y.z`)",
        "Regarde `git log --oneline v1.4.0..HEAD` pour vérifier ce que contient la version"],
       SH(r"""
git log --oneline
git diff
# à toi
"""),
       ["Deux `-m` : le premier est le titre, le second devient le pied du message.",
        "Un changement incompatible depuis la dernière version → on augmente le numéro **majeur**.",
        "`git tag -a v… -m \"Version …\"` crée un tag annoté sur HEAD."],
       SH(r"""
git add api.js
git commit -m "feat(api)!: renomme calculer() en calculerTotal()" -m "BREAKING CHANGE: calculer() n'existe plus, utilise calculerTotal()."
git log --oneline v1.4.0..HEAD
git tag -a v2.0.0 -m "Version 2.0.0"
git log --oneline
"""),
       ["Le commit annonce la rupture", "Le tag v2.0.0 est annoté et posé sur ton commit"],
       run=GRUN(r"""
const m = git.msg('HEAD') || '';
assert(/^feat\(api\)!: \S/.test(m), 'Titre « feat(api)!: … »');
assert(/\n\nBREAKING CHANGE: \S/.test(m), 'Pied « BREAKING CHANGE: … » séparé par une ligne vide');
assert(/calculerTotal/.test(m.split('BREAKING CHANGE:')[1] || ''), 'Le pied dit quoi utiliser à la place (calculerTotal)');
assert.equal(JSON.stringify(git.touched('HEAD')), JSON.stringify(['api.js']), 'Le commit ne contient que api.js');
assert(git.tags['v2.0.0'], 'Le tag v2.0.0 existe (changement incompatible → version majeure)');
assert(!git.tags['v1.5.0'] && !git.tags['v1.4.1'], 'Pas de v1.5.0 ni v1.4.1 : la rupture impose une majeure');
assert(git.tags['v2.0.0'] && git.tags['v2.0.0'].id === git.rev('HEAD'), 'v2.0.0 est posé sur ton commit');
assert(git.tags['v2.0.0'] && git.tags['v2.0.0'].annotated, 'Tag annoté (-a -m)');
assert(git.clean(), 'Dossier propre');
""", r"""
git.sh('git init');
git.write('api.js', 'export function calculer(lignes) {\n  return lignes.reduce((s, l) => s + l.prix, 0);\n}\n');
git.sh('git add .\ngit commit -m "feat: première version de la bibliothèque"\ngit tag -a v1.4.0 -m "Version 1.4.0"');
git.write('montant.js', 'export const positif = (x) => Math.max(0, x);\n');
git.sh('git add .\ngit commit -m "fix: gère les montants négatifs"');
git.write('devise.js', 'export const devise = "EUR";\n');
git.sh('git add .\ngit commit -m "feat: ajoute la devise"');
git.write('api.js', 'export function calculerTotal(lignes) {\n  return lignes.reduce((s, l) => s + l.prix, 0);\n}\n');
""")),
  ])

# ============================================================ 6. GitHub
github = V2(v1["git-github"],
  prereq=[
    P("Dépôt distant (remote)", "Une copie du dépôt sur un serveur (GitHub). Par convention elle s'appelle `origin`."),
    P("Branche de suivi `origin/main`", "Ta copie **locale** de ce que tu sais de `main` sur GitHub. Elle ne bouge que quand tu fais `git fetch` (ou `pull`)."),
    P("Upstream", "La branche distante associée à ta branche locale. Une fois définie (`push -u`), `git push` et `git pull` savent où aller."),
    P("Pull Request (PR)", "Une demande, sur GitHub, d'intégrer une branche dans une autre. Elle sert à la revue de code et aux vérifications automatiques."),
    P("Push forcé", "Remplacer la branche distante par la tienne, même si elle contient des commits que tu n'as pas. `--force-with-lease` le fait **seulement** si personne n'a poussé depuis ton dernier fetch."),
  ],
  diagram=D(
    nodes=[
      N("loc", 0, 1, "Ton dépôt local", "main, feat/x\norigin/main (copie)", kind="db"),
      N("gh", 2, 1, "origin (GitHub)", "main, feat/x", kind="db", color="accent"),
      N("col", 2, 0, "Collègue", "pousse aussi", kind="actor", color="muted"),
      N("pr", 3, 1, "Pull Request", "revue → merge", kind="doc", color="good"),
    ],
    edges=[E("loc", "gh", "git push"), E("gh", "loc", "git fetch / pull", dashed=True, back=True), E("col", "gh"), E("gh", "pr", "gh pr create"), E("pr", "gh", "merge", dashed=True, back=True)],
    caption="push envoie tes commits, fetch récupère ceux des autres dans origin/…, pull = fetch + intégration. La PR se fusionne sur GitHub ; tu récupères ensuite main en local."),
  lessons=[
    L("Local et distant : deux dépôts", r"""
Ton dépôt local et GitHub sont **deux dépôts complets**. Ils ne se synchronisent jamais tout seuls :

| Commande | Effet |
|---|---|
| `git push` | envoie tes commits de la branche courante vers `origin` |
| `git fetch` | télécharge les nouveaux commits de `origin` et met à jour `origin/main`, `origin/feat/x`… **sans toucher** à tes branches |
| `git pull` | `git fetch` + intégration de `origin/<branche>` dans ta branche |

`origin/main` est une étiquette **locale** : « là où était `main` sur GitHub la dernière fois que j'ai regardé ». Après un `fetch`, comparer `main` et `origin/main` dit si tu es en avance, en retard, ou si vous avez divergé (`git status` l'affiche).

Première publication d'une branche : `git push -u origin feat/x`. Le `-u` (set-upstream) relie `feat/x` à `origin/feat/x` ; ensuite un simple `git push` / `git pull` suffit.
"""),
    L("Quand le push est refusé", r"""
```
 ! [rejected]        main -> main (fetch first)
hint: Updates were rejected because the remote contains work that you do not have locally.
```

Quelqu'un a poussé avant toi : la branche distante contient un commit que tu n'as pas. Git refuse pour ne pas l'écraser. Il faut **d'abord intégrer** son travail :

```bash
git pull --rebase    # récupère son commit, puis rejoue les tiens par-dessus
git push
```

Sans option, si les deux côtés ont des commits, un `git pull` récent s'arrête et demande de choisir : `--rebase` (historique linéaire, le plus courant) ou `--no-rebase` (commit de fusion). Beaucoup d'équipes configurent `git config pull.rebase true` une fois pour toutes.

**Ne réponds jamais à un refus par `git push --force`** : tu supprimerais le commit de ton collègue.
"""),
    L("Le cycle d'une Pull Request", r"""
1. **Branche** à partir d'un `main` à jour : `git switch main && git pull && git switch -c feat/readme`
2. **Commits** propres (Conventional Commits).
3. **Push** : `git push -u origin feat/readme`
4. **Ouvrir la PR** sur GitHub (ou `gh pr create --title "…"` avec l'outil en ligne de commande `gh`).
5. **Revue** : les collègues commentent ; tu ajoutes des commits, tu pousses, la PR se met à jour toute seule.
6. **Fusion** sur GitHub, selon le réglage du dépôt :
   - *Create a merge commit* : garde tous les commits + un commit de fusion ;
   - *Squash and merge* : **un seul** commit sur `main` avec le titre de la PR ;
   - *Rebase and merge* : rejoue les commits sur `main`, sans commit de fusion.
7. **Ménage en local** : `git switch main && git pull`, `git branch -D feat/readme` (`-D` car après un squash, Git ne reconnaît pas les commits de la branche dans `main`), `git fetch --prune` (efface les `origin/…` des branches supprimées sur GitHub).

Dans l'atelier, `gh pr create` et `gh pr merge --squash | --merge | --rebase [--delete-branch]` simulent ce que tu ferais sur le site de GitHub.
"""),
    L("Mettre à jour sa PR : rebase et `--force-with-lease`", r"""
Pendant la revue, `main` avance. Pour que ta PR reste fusionnable sans conflit, tu la mets à jour :

```bash
git fetch
git rebase origin/main
git push --force-with-lease
```

Le rebase a **remplacé** tes commits (nouveaux identifiants) : un push normal est refusé. Il faut forcer, mais **prudemment** :

- `--force` écrase la branche distante quoi qu'elle contienne ;
- `--force-with-lease` n'écrase que si la branche distante est **encore là où tu l'as vue au dernier fetch**. Si un relecteur a poussé une suggestion entre-temps, le push est refusé (« stale info ») au lieu de l'effacer.

Donc, si quelqu'un d'autre peut pousser sur ta branche : `git pull --rebase` d'abord (pour récupérer ses commits), puis le rebase sur `origin/main`, puis `--force-with-lease`.
"""),
  ],
  recap=[
    "`push` envoie, `fetch` récupère dans `origin/…`, `pull` = fetch + intégration.",
    "`git push -u origin branche` la première fois ; ensuite `git push`.",
    "Push refusé → `git pull --rebase` puis `git push` ; jamais `--force` en réponse.",
    "PR : branche → commits → push → PR → revue → merge (squash, merge ou rebase) → ménage.",
    "Après un rebase de ta branche : `git push --force-with-lease`, jamais `--force`.",
  ],
  example=[F("terminal", "bash", r"""
$ git switch -c feat/readme
$ git commit -am "docs: ajoute l'installation"
$ git push -u origin feat/readme
 * [new branch]      feat/readme -> feat/readme
$ gh pr create --title "docs: complète le README"
https://github.com/toi/projet/pull/1
# … revue, puis « Squash and merge » sur GitHub …
$ git switch main
$ git pull
Updating 2d99fc3..93c4ed7
Fast-forward
$ git branch -D feat/readme
$ git fetch --prune
 - [deleted]         (none) -> origin/feat/readme
""")],
  notes=["`-u` relie la branche locale à `origin/feat/readme`.",
         "Après le squash, `main` contient un seul commit qui résume la PR.",
         "`--prune` nettoie les branches de suivi des branches supprimées sur GitHub."],
  td1=dict(path="commandes.sh",
    title="Ta première Pull Request propre",
    enonce="Le projet est déjà sur GitHub (`origin`). Ajoute une documentation en suivant **tout** le cycle d'une PR, jusqu'au ménage final. " + SIM,
    consignes=["Crée `feat/readme`, ajoute au README une section `## Installation` puis une section `## Utilisation`, en 2 commits",
               "Publie la branche et ouvre une PR intitulée `docs: complète le README`",
               "Fusionne-la en « squash » en supprimant la branche distante (`gh pr merge --squash --delete-branch`)",
               "Récupère `main` en local, supprime ta branche locale et nettoie les branches de suivi"],
    hints=["`echo \"## Installation\" >> README.md` puis `git commit -am \"docs: …\"`.",
           "`git push -u origin feat/readme` puis `gh pr create --title \"…\"`.",
           "Après le squash : `git switch main`, `git pull`, `git branch -D feat/readme`, `git fetch --prune`."],
    checks=["`main` local = `main` sur GitHub", "Plus aucune trace de `feat/readme`"],
    files=SH(r"""
git log --oneline --all
# à toi
"""),
    solution=SH(r"""
git switch -c feat/readme
echo "## Installation" >> README.md
git commit -am "docs: ajoute l'installation"
echo "## Utilisation" >> README.md
git commit -am "docs: ajoute l'utilisation"
git push -u origin feat/readme
gh pr create --title "docs: complète le README"
gh pr merge --squash --delete-branch
git switch main
git pull
git branch -D feat/readme
git fetch --prune
git log --oneline --graph --all
"""),
    run=GRUN(r"""
assert(git.prs.length === 1 && git.prs[0].state === 'MERGED', 'Une PR a été ouverte puis fusionnée');
assert.equal(git.prs[0].title, 'docs: complète le README', 'Titre de la PR');
assert.equal(git.remoteLog('main')[0], 'docs: complète le README (#1)', 'main sur GitHub a un seul commit de squash');
assert.equal(git.rev('main'), git.remote.branches.main, 'main local = main sur GitHub');
assert(git.branch === 'main', 'Tu es sur main');
assert(!git.branches['feat/readme'] && !git.remote.branches['feat/readme'] && !git.tracking['feat/readme'], 'Plus de feat/readme : ni locale, ni distante, ni origin/feat/readme');
assert(/## Installation\n## Utilisation/.test(git.file('README.md') || ''), 'Le README contient les deux sections');
""", r"""
git.sh('git init');
git.write('README.md', '# Projet\n');
git.sh('git add .\ngit commit -m "chore: initialise le projet"');
git.cloneRemote();
""")),
  tds=[
    TD(2, "Le collègue a poussé avant toi",
       "Tu ajoutes le panier sur `main`. Pendant ce temps, Léa a poussé la page contact. Publie ton commit sans écraser le sien et sans commit de fusion inutile. " + SIM,
       ["Crée `panier.js` et commite-le : `feat: ajoute le panier`",
        "Tente `git push` : lis le refus",
        "Intègre le travail de Léa en gardant un historique **linéaire**, puis pousse",
        "Ne force rien"],
       SH(r"""
git status
# à toi
"""),
       ["Le refus dit « fetch first » : GitHub a un commit que tu n'as pas.",
        "`git pull --rebase` récupère le commit de Léa et rejoue le tien par-dessus.",
        "Après ça, un `git push` normal passe."],
       SH(r"""
echo "export const panier = [];" > panier.js
git add panier.js
git commit -m "feat: ajoute le panier"
git push
git pull --rebase
git push
git log --oneline --graph --all
"""),
       ["Ton commit est au-dessus de celui de Léa", "Aucun commit de fusion"],
       run=GRUN(r"""
assert(git.transcript.some((t) => /rejected/.test(t.out)), 'Ton premier push a été refusé (normal)');
assert.equal(JSON.stringify(git.remoteLog('main')), JSON.stringify(['feat: ajoute le panier', 'feat: ajoute la page contact', 'chore: initialise']), 'Sur GitHub : ton commit au-dessus de celui de Léa');
assert.equal(git.merges('main'), 0, 'Historique linéaire (aucun commit de fusion)');
assert.equal(git.rev('main'), git.remote.branches.main, 'main local = main distant');
assert(!git.used(/--force|push -f/), 'Aucun push forcé');
""", r"""
git.sh('git init');
git.write('index.html', '<h1>Boutique</h1>\n');
git.sh('git add .\ngit commit -m "chore: initialise"');
git.cloneRemote();
git.remoteCommit('main', 'feat: ajoute la page contact', { 'contact.html': '<form></form>\n' }, 'Léa');
""")),
    TD(3, "Mettre à jour sa PR sans écraser la revue",
       "Ta PR `feat/paiement` est ouverte. Deux choses se sont passées sur GitHub : Sam (le relecteur) a poussé une correction **sur ta branche**, et Léa a fusionné une autre fonctionnalité dans `main`. Mets ta PR à jour sur le dernier `main`, sans perdre le commit de Sam, puis fusionne-la en « rebase ». " + SIM,
       ["Récupère le commit de Sam sur ta branche",
        "Rebase ta branche sur le dernier `origin/main`",
        "Pousse avec la protection `--force-with-lease` (un `--force` simple est interdit)",
        "Fusionne la PR avec `gh pr merge --rebase --delete-branch`, puis mets ton `main` local à jour"],
       SH(r"""
git status
git log --oneline --graph --all
# à toi
"""),
       ["`git pull --rebase` sur `feat/paiement` récupère le commit de Sam (et fait le fetch de `origin/main` au passage).",
        "`git rebase origin/main` : ta branche part maintenant du commit de Léa.",
        "Essaie le push avant le `pull --rebase` pour voir `--force-with-lease` refuser (« stale info »)."],
       SH(r"""
git pull --rebase
git rebase origin/main
git push --force-with-lease
gh pr merge --rebase --delete-branch
git switch main
git pull
git log --oneline --graph --all
"""),
       ["Le commit de Sam et celui de Léa sont dans `main`", "Aucun `--force` simple"],
       run=GRUN(r"""
const L = git.remoteLog('main');
assert(L.includes('fix(paiement): corrige le libellé du bouton'), 'Le commit de Sam est dans main');
assert(L.includes('feat: ajoute la FAQ'), 'Le commit de Léa est dans main');
assert(L.includes('feat(paiement): ajoute le formulaire') && L.includes('feat(paiement): valide la carte'), 'Tes deux commits sont dans main');
assert(L.indexOf('feat: ajoute la FAQ') > L.indexOf('feat(paiement): ajoute le formulaire'), 'Tes commits sont au-dessus de celui de Léa');
assert.equal(git.merges('origin/main'), 0, 'Historique linéaire');
assert(git.prs[0] && git.prs[0].state === 'MERGED', 'La PR est fusionnée');
assert(!git.used(/--force(?!-with-lease)|push -f/), 'Pas de --force simple');
assert(git.used(/--force-with-lease/), 'Tu as poussé avec --force-with-lease');
assert(git.branch === 'main' && git.rev('main') === git.remote.branches.main, 'main local à jour');
""", r"""
git.sh('git init');
git.write('index.html', '<h1>Boutique</h1>\n');
git.sh('git add .\ngit commit -m "chore: initialise"');
git.cloneRemote();
git.sh('git switch -c feat/paiement');
git.write('paiement.js', 'export const payer = () => {};\n');
git.write('bouton.html', '<button>Payr</button>\n');
git.sh('git add .\ngit commit -m "feat(paiement): ajoute le formulaire"');
git.write('carte.js', 'export const valide = (n) => n.length === 16;\n');
git.sh('git add .\ngit commit -m "feat(paiement): valide la carte"\ngit push -u origin feat/paiement\ngh pr create --title "feat: paiement par carte"');
git.remoteCommit('feat/paiement', 'fix(paiement): corrige le libellé du bouton', { 'bouton.html': '<button>Payer</button>\n' }, 'Sam');
git.remoteCommit('main', 'feat: ajoute la FAQ', { 'faq.html': '<h1>FAQ</h1>\n' }, 'Léa');
""")),
  ])

# ============================================================ 7. Outils
nombres_setup = r"""
git.sh('git init');
let contenu = '';
for (let i = 1; i <= 20; i++) {
  contenu += i + '\n';
  if (i === 13) contenu += 'BUG\n';
  git.write('nombres.txt', contenu);
  git.sh('git add .\ngit commit -m "ajoute ' + i + '"');
}
"""

outils = V2(v1["git-outils"],
  prereq=[
    P("Stash", "Une étagère où Git range temporairement tes modifications non commitées, pour retrouver un dossier propre et les reprendre plus tard."),
    P("Cherry-pick", "Copier **un** commit précis d'une branche vers une autre (le changement est rejoué, avec un nouvel identifiant)."),
    P("Tag", "Une étiquette **fixe** sur un commit, en général une version (`v1.2.0`). Contrairement à une branche, elle n'avance jamais."),
    P("Recherche dichotomique", "Couper l'intervalle en deux à chaque étape : parmi 1000 commits, on trouve le coupable en une dizaine d'essais."),
  ],
  diagram=D(
    nodes=[
      N("g", 0, 1, "v1.0.0", "bon", kind="pill", color="good"),
      N("x1", 1, 1, "…", None, kind="pill", color="muted"),
      N("m", 2, 1, "milieu", "on teste ici", kind="pill", color="warn"),
      N("x2", 3, 1, "…", None, kind="pill", color="muted"),
      N("b", 4, 1, "HEAD", "mauvais", kind="pill", color="bad"),
      N("r", 2, 0, "bon → chercher à droite", "mauvais → à gauche", kind="note"),
    ],
    edges=[E("g", "x1"), E("x1", "m"), E("m", "x2"), E("x2", "b"), E("r", "m", dashed=True)],
    caption="git bisect : entre un commit bon et un mauvais, Git place HEAD au milieu ; ta réponse (good/bad) élimine la moitié de l'intervalle, jusqu'au premier commit fautif."),
  lessons=[
    L("`stash` : mettre de côté", r"""
Tu es au milieu d'une fonctionnalité, rien n'est commitable, et un bug urgent arrive sur `main`. Changer de branche avec des modifications en cours est risqué (Git peut refuser, ou les emporter avec toi). Solution :

```bash
git stash push -u -m "recherche en cours"   # range tout (-u : y compris les nouveaux fichiers)
git switch main                              # dossier propre
# … correctif, commit …
git switch feat/recherche
git stash pop                                # ressort les modifications et vide l'étagère
```

- `git stash list` : ce qui est rangé (`stash@{0}` est le plus récent).
- `git stash apply` : ressort sans retirer de l'étagère ; `pop` = apply + drop.
- Sans `-u`, les fichiers **non suivis** restent dans le dossier (et te suivent quand tu changes de branche).

Le stash est un dépannage de courte durée : pour un travail qui dure, un commit « wip » sur ta branche est plus sûr.
"""),
    L("`cherry-pick` : copier un commit", r"""
Un correctif a été fait sur `main`, mais la version `1.x` (déjà en production, branche `release/1.x`) a aussi besoin de lui, **sans** les nouvelles fonctionnalités de `main` :

```bash
git switch release/1.x
git cherry-pick a1b2c3d      # rejoue uniquement le changement de a1b2c3d
```

C'est un nouveau commit (même message, autre identifiant). En cas de conflit : résoudre, `git add`, `git cherry-pick --continue` (ou `--abort`).

À utiliser ponctuellement : si tu cherry-pick des dizaines de commits, c'est qu'il fallait plutôt fusionner ou rebaser.
"""),
    L("Tags : marquer les versions", r"""
```bash
git tag v1.0.0                              # tag léger : juste une étiquette
git tag -a v1.0.1 -m "Version 1.0.1"        # tag annoté : auteur, date, message (à préférer pour les versions)
git tag -a v1.0.0 a1b2c3d -m "…"            # sur un commit précis
git tag                                     # lister
git push origin v1.0.1                      # les tags ne partent PAS avec un push normal
git push --tags                             # tous les tags
```

Un tag ne bouge jamais : `v1.0.1` désignera toujours exactement ce code. On peut l'utiliser partout à la place d'un identifiant (`git switch --detach v1.0.0`, `git log v1.0.0..HEAD`, `git diff v1.0.0 HEAD`).
"""),
    L("`bisect` : trouver le commit fautif", r"""
« Ça marchait en v1.0.0, ça ne marche plus aujourd'hui, et il y a 200 commits entre les deux. » Plutôt que de lire 200 commits :

```bash
git bisect start
git bisect bad                 # le commit actuel est mauvais
git bisect good v1.0.0         # celui-ci était bon
# Git se place au milieu : tu testes, puis tu réponds
git bisect good                # ou : git bisect bad
# … ~8 fois pour 200 commits …
# a1b2c3d is the first bad commit
git bisect reset               # retour sur ta branche
```

Encore mieux : si un **script** peut dire « bon » ou « mauvais » (un test, un `grep`), Git fait tout seul :

```bash
git bisect run npm test                         # code de sortie 0 = bon, autre = mauvais
git bisect run ! grep -q BUG nombres.txt        # bon tant que BUG est absent
```

C'est là que les **commits atomiques** paient : le coupable trouvé est un petit changement, facile à comprendre et à corriger.
"""),
  ],
  recap=[
    "`git stash push -u -m \"…\"` / `git stash pop` : ranger puis reprendre un travail en cours.",
    "`git cherry-pick <commit>` : copier un correctif précis vers une autre branche.",
    "`git tag -a vX.Y.Z -m \"…\"` puis `git push origin vX.Y.Z` (les tags ne partent pas tout seuls).",
    "`git bisect start / bad / good <ref>` puis `good`/`bad` ou `git bisect run <commande>` ; `git bisect reset` à la fin.",
  ],
  example=[F("terminal", "bash", r"""
$ git bisect start
$ git bisect bad
$ git bisect good v1.0.0
Bisecting: 7 revisions left to test after this (roughly 3 steps)
[a7e7951] ajoute 12
$ git bisect run ! grep -q BUG nombres.txt
running '! grep -q BUG nombres.txt'
Bisecting: 3 revisions left to test after this (roughly 2 steps)
…
f2882fd is the first bad commit
    ajoute 13
bisect found first bad commit
$ git bisect reset
""")],
  notes=["`good v1.0.0` : on peut donner un tag au lieu d'un identifiant.",
         "`!` inverse le résultat de `grep` : le commit est « bon » si BUG est absent.",
         "Git a trouvé le coupable en 4 tests au lieu de 15."],
  td1=dict(path="commandes.sh",
    title="Trouver le coupable avec bisect",
    enonce="`nombres.txt` a été construit en 20 commits (« ajoute 1 » … « ajoute 20 »). Une ligne `BUG` s'est glissée en route. Marque la dernière version saine et retrouve le commit fautif **sans lire le log**. " + SIM,
    consignes=["Pose un tag `v1.0.0` sur le commit « ajoute 5 » (la dernière version publiée, sans bug)",
               "Lance `git bisect` entre `HEAD` (mauvais) et `v1.0.0` (bon)",
               "Trouve le premier commit qui contient `BUG` : à la main (`good`/`bad`) ou avec `git bisect run`",
               "Termine par `git bisect reset` pour revenir sur `main`"],
    hints=["« ajoute 5 » est 15 commits avant HEAD : `git tag v1.0.0 HEAD~15`.",
           "`git bisect start`, `git bisect bad`, `git bisect good v1.0.0`.",
           "`git bisect run ! grep -q BUG nombres.txt` : le commit est bon si `BUG` n'y est pas."],
    checks=["Le tag v1.0.0 est sur « ajoute 5 »", "Le premier commit fautif trouvé est « ajoute 13 »"],
    files=SH(r"""
git log --oneline -3
# à toi
"""),
    solution=SH(r"""
git tag v1.0.0 HEAD~15
git bisect start
git bisect bad
git bisect good v1.0.0
git bisect run ! grep -q BUG nombres.txt
git bisect reset
"""),
    run=GRUN(r"""
assert(git.tags['v1.0.0'], 'Le tag v1.0.0 existe');
assert.equal(git.msg('v1.0.0'), 'ajoute 5', 'v1.0.0 est posé sur « ajoute 5 »');
assert(git.bisectFound, 'git bisect a trouvé un commit');
assert.equal(git.msg(git.bisectFound), 'ajoute 13', 'Le premier commit fautif est « ajoute 13 »');
assert(git.bisect === null, 'Le bisect est terminé (git bisect reset)');
assert(git.branch === 'main' && !git.detached, 'Tu es revenu sur main');
""", nombres_setup)),
  tds=[
    TD(2, "Interruption urgente : stash",
       "Tu travailles sur `feat/recherche` : `recherche.js` est modifié et `filtres.js` est un nouveau fichier, rien n'est prêt à commiter. Un bug urgent arrive : `total.js` soustrait au lieu d'additionner, sur `main`. Corrige-le, puis reprends ton travail exactement où tu en étais. " + SIM,
       ["Range ton travail en cours, **y compris** le nouveau fichier, avec un message",
        "Sur `main`, corrige `total.js` (`a + b`) et commite : `fix: corrige le calcul du total`",
        "Reviens sur `feat/recherche` et reprends ton travail ; l'étagère doit être vide à la fin",
        "Le correctif ne doit pas être dans `feat/recherche`"],
       SH(r"""
git status
# à toi
"""),
       ["`git stash push -u -m \"recherche en cours\"` : `-u` inclut les fichiers non suivis.",
        "`echo \"export const total = (a, b) => a + b;\" > total.js`.",
        "`git stash pop` ressort le travail et retire l'entrée de l'étagère."],
       SH(r"""
git stash push -u -m "recherche en cours"
git switch main
echo "export const total = (a, b) => a + b;" > total.js
git commit -am "fix: corrige le calcul du total"
git switch feat/recherche
git stash pop
git status
"""),
       ["`main` contient le correctif", "Ton travail en cours est revenu, étagère vide"],
       run=GRUN(r"""
assert.equal(git.msg('main'), 'fix: corrige le calcul du total', 'Le correctif est le dernier commit de main');
assert.equal(git.at('main', 'total.js'), 'export const total = (a, b) => a + b;\n', 'total.js corrigé sur main');
assert.includes(git.at('feat/recherche', 'total.js') || '', 'a - b', 'feat/recherche n\'a pas reçu le correctif');
assert.equal(git.branch, 'feat/recherche', 'Tu es revenu sur feat/recherche');
assert.includes(git.file('recherche.js') || '', 'toLowerCase', 'Tes modifications de recherche.js sont revenues');
assert(git.status().modified.includes('recherche.js'), 'recherche.js est de nouveau « modifié » (non commité)');
assert(git.status().untracked.includes('filtres.js'), 'filtres.js est revenu (non suivi)');
assert.equal(git.stash.length, 0, 'L\'étagère est vide');
assert(git.used(/stash (push )?.*-u|--include-untracked/), 'Tu as rangé aussi les fichiers non suivis (-u)');
""", r"""
git.sh('git init');
git.write('total.js', 'export const total = (a, b) => a - b;\n');
git.write('recherche.js', 'export const chercher = (q, l) => l.filter((x) => x.includes(q));\n');
git.sh('git add .\ngit commit -m "chore: initialise"\ngit switch -c feat/recherche');
git.write('recherche.js', 'export const chercher = (q, l) => l.filter((x) => x.includes(q));\nexport const normaliser = (s) => s.trim();\n');
git.sh('git commit -am "feat: ébauche de la recherche"');
git.write('recherche.js', 'export const chercher = (q, l) => l.filter((x) => x.toLowerCase().includes(q.toLowerCase()));\nexport const normaliser = (s) => s.trim();\n');
git.write('filtres.js', 'export const filtres = { prixMax: null };\n');
""")),
    TD(3, "Rapatrier un correctif et publier une version",
       "La version `1.x` est en production sur la branche `release/1.x` (tag `v1.0.0`). Sur `main`, entre deux nouvelles fonctionnalités, quelqu'un a corrigé un bug d'arrondi des prix. La production a besoin **de ce correctif seulement**. Publie une version `1.0.1`. " + SIM,
       ["Sur `release/1.x`, récupère uniquement le commit `fix: corrige l'arrondi des prix`",
        "Les fichiers des fonctionnalités (`theme.js`, `favoris.js`) ne doivent pas arriver dans `release/1.x`",
        "Pose un tag annoté `v1.0.1` (message `Version 1.0.1`) sur le résultat",
        "Pousse la branche **et** le tag sur `origin`"],
       SH(r"""
git log --oneline --graph --all
# à toi
"""),
       ["Le correctif est `main~1` (ou son identifiant dans le graphe).",
        "`git cherry-pick main~1` depuis `release/1.x`.",
        "`git push` envoie la branche ; le tag part avec `git push origin v1.0.1` (ou `--tags`)."],
       SH(r"""
git switch release/1.x
git cherry-pick main~1
git tag -a v1.0.1 -m "Version 1.0.1"
git push
git push origin v1.0.1
git log --oneline --graph --all
"""),
       ["`release/1.x` n'a qu'un commit de plus : le correctif", "Le tag est sur GitHub"],
       run=GRUN(r"""
assert.equal(git.msg('release/1.x'), "fix: corrige l'arrondi des prix", 'Le correctif est en haut de release/1.x');
assert.equal(git.parents('release/1.x')[0], git.rev('v1.0.0'), 'Un seul commit ajouté depuis v1.0.0');
assert(git.at('release/1.x', 'theme.js') === null && git.at('release/1.x', 'favoris.js') === null, 'Aucune fonctionnalité de main dans release/1.x');
assert.includes(git.at('release/1.x', 'prix.js') || '', 'Math.round', 'prix.js corrigé dans release/1.x');
assert(git.tags['v1.0.1'] && git.tags['v1.0.1'].id === git.rev('release/1.x') && git.tags['v1.0.1'].annotated, 'Tag annoté v1.0.1 sur release/1.x');
assert.equal(git.remote.branches['release/1.x'], git.rev('release/1.x'), 'release/1.x poussée');
assert(git.remote.tags['v1.0.1'], 'Le tag v1.0.1 est sur origin');
assert.equal(git.msg('main'), 'feat: ajoute les favoris', 'main n\'a pas bougé');
""", r"""
git.sh('git init');
git.write('prix.js', 'export const arrondi = (x) => Math.floor(x * 100) / 100;\n');
git.sh('git add .\ngit commit -m "chore: initialise"\ngit tag -a v1.0.0 -m "Version 1.0.0"\ngit branch release/1.x');
git.write('theme.js', 'export const theme = "sombre";\n');
git.sh('git add .\ngit commit -m "feat: ajoute le mode sombre"');
git.write('prix.js', 'export const arrondi = (x) => Math.round(x * 100) / 100;\n');
git.sh('git commit -am "fix: corrige l\'arrondi des prix"');
git.write('favoris.js', 'export const favoris = [];\n');
git.sh('git add .\ngit commit -m "feat: ajoute les favoris"');
git.cloneRemote();
""")),
  ])

MODULES = [modele, merge, rebase, revenir, commits, github, outils]

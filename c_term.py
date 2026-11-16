from common import P, L, D, N, E, F, TD, RUN

T = "terminal"


def DM(id, title, minutes, goal, why, flow, points, pitfalls, quiz, prereq, diagram, lessons, recap, example, notes, tds):
    return {"id": id, "track": T, "title": title, "minutes": minutes, "goal": goal, "why": why,
            "flow": flow, "points": points, "pitfalls": pitfalls, "quiz": quiz, "prereq": prereq,
            "diagram": diagram, "lessons": lessons, "recap": recap,
            "example": {"files": example if isinstance(example, list) else [example], "notes": notes}, "tds": tds}


def Q(q, options, answer, why):
    return {"q": q, "options": options, "answer": answer, "why": why}


def TERM(tests, start, entry="commandes.sh"):
    return RUN("term", entry=entry, tests=tests, start=start)


SH = (" Écris tes commandes dans le fichier (une par ligne), puis **▶ Lancer les commandes** : elles s'exécutent dans un terminal simulé, "
      "dans un dossier de test recréé à chaque lancement. Ensuite tu peux taper d'autres commandes directement dans le terminal pour explorer (↑ pour l'historique, Tab pour compléter).")
PS1 = SH.replace("terminal simulé", "PowerShell simulé (Windows)")

PROJET = r"""
t.fichier('projets/boutique/package.json', JSON.stringify({ name: 'boutique', version: '1.0.0', scripts: { dev: 'node serveur.js', test: 'echo tests ok' } }, null, 2) + '\n');
t.fichier('projets/boutique/README.md', '# Boutique\n');
t.fichier('projets/boutique/.env', 'API_URL=http://localhost:8000\n');
t.fichier('projets/boutique/src/main.tsx', "import App from './App';\n");
t.fichier('projets/boutique/src/components/ui/Bouton.tsx', 'export function Bouton() { return null; }\n');
t.fichier('projets/boutique/src/components/ui/Carte.tsx', 'export function Carte() { return null; }\n');
t.fichier('projets/boutique/src/pages/Accueil.tsx', 'export default function Accueil() { return null; }\n');
t.fichier('projets/blog/posts/bienvenue.md', '# Bienvenue\n');
t.fichier('projets/blog/README.md', '# Blog\n');
t.fichier('Documents/cv.pdf', '%PDF-1.7\n');
"""

# =========================================================================== 1. Se déplacer
bases = DM("term-bases", "Se repérer et se déplacer", 25,
  "Comprendre ce qu'est un terminal, savoir où l'on est, se déplacer avec des chemins absolus et relatifs, et lister le contenu des dossiers, sous Linux/macOS (bash) comme sous Windows (PowerShell).",
  "Installer un projet, lancer un serveur, utiliser Git, lire un message d'erreur de build : tout passe par le terminal. Et 80 % des erreurs de débutant viennent d'une seule chose : ne pas être dans le bon dossier.",
  ["Savoir **où je suis** (`pwd` / `Get-Location`)", "**Lister** ce qu'il y a ici (`ls` / `Get-ChildItem`)",
   "**Aller** ailleurs (`cd`), avec un chemin absolu ou relatif", "Utiliser **Tab** (compléter) et **↑** (historique) pour ne pas tout taper"],
  ["Le terminal exécute des commandes dans un **dossier courant** ; les chemins relatifs partent de là.",
   "Chemin absolu : depuis la racine (`/home/ana/projets`, `C:\\Users\\ana\\projets`) ; relatif : depuis le dossier courant (`src/pages`, `../blog`).",
   "`.` = ici, `..` = le dossier parent, `~` = ton dossier personnel.",
   "Linux sépare les dossiers par `/`, Windows par `\\` (PowerShell accepte aussi `/`).",
   "Les fichiers qui commencent par un point (`.env`, `.gitignore`) sont **cachés** : `ls -a` / `Get-ChildItem -Force`."],
  ["Lancer `npm install` en dehors du dossier du projet.", "Oublier les guillemets autour d'un nom avec des espaces.", "Taper les chemins à la main au lieu d'utiliser Tab (fautes de frappe)."],
  [Q("Je suis dans /home/ana/projets/boutique/src. `cd ../../blog` m'emmène…", ["/home/ana/blog", "/home/ana/projets/blog", "/blog", "nulle part"], 1, "Deux crans vers le haut (boutique, puis projets), puis blog."),
   Q("Pour voir le fichier .env dans un listing :", ["ls", "ls -a", "ls .env seulement", "impossible"], 1, "Les fichiers qui commencent par un point sont cachés par défaut."),
   Q("L'équivalent PowerShell de `pwd` :", ["Get-ChildItem", "Get-Location", "Set-Location", "Where-Object"], 1, "pwd fonctionne aussi : c'est un alias de Get-Location.")],
  prereq=[
    P("Terminal / shell", "Le terminal est la fenêtre ; le shell est le programme qui lit tes commandes : bash ou zsh (Linux, macOS), PowerShell (Windows)."),
    P("Dossier courant", "Le dossier dans lequel le shell travaille ; affiché dans l'invite (`ana@pc:~/projets$`, `PS C:\\Users\\ana\\projets>`)."),
    P("Chemin absolu / relatif", "Absolu : part de la racine. Relatif : part du dossier courant."),
    P("Invite (prompt)", "Le texte avant le curseur, qui rappelle souvent où tu es."),
  ],
  diagram=D(
    nodes=[
      N("h", 0, 1, "~ (ana)", "dossier personnel", kind="db", color="accent"),
      N("p", 1, 1, "projets", "cd projets", kind="box"),
      N("b", 2, 0, "boutique", "cd boutique", kind="box", color="good"),
      N("g", 2, 2, "blog", "cd ../blog", kind="box", color="warn"),
      N("s", 3, 0, "src", "chemin relatif", kind="pill"),
    ],
    edges=[E("h", "p"), E("p", "b"), E("p", "g"), E("b", "s")],
    caption="Les dossiers forment un arbre ; `..` remonte d'un cran, un nom descend d'un cran."),
  lessons=[
    L("Le terminal, le shell, l'invite", r"""
Le **terminal** est une fenêtre où l'on tape des commandes ; le **shell** est le programme qui les exécute.

| Système | Shell habituel | Invite typique |
|---|---|---|
| Linux, macOS, WSL | bash, zsh | `ana@pc:~/projets$` |
| Windows | PowerShell | `PS C:\Users\ana\projets>` |
| Windows (ancien) | cmd | `C:\Users\ana\projets>` |

Une commande = un **nom**, puis des **options** (`-l`, `--all`, `-Recurse`), puis des **arguments** (un fichier, un dossier) : `ls -la src`.

Deux réflexes qui font gagner un temps fou :
- **Tab** complète un nom de fichier ou de dossier (et évite les fautes de frappe) ;
- **↑** rappelle les commandes précédentes.

Dans les TD, après avoir lancé ton fichier de commandes, tu peux taper directement dans le terminal simulé.
"""),
    L("Où suis-je ? Qu'y a-t-il ici ? Aller ailleurs", r"""
| Action | bash (Linux, macOS) | PowerShell (Windows) |
|---|---|---|
| où suis-je ? | `pwd` | `Get-Location` (ou `pwd`) |
| lister | `ls`, `ls -la` (détails + cachés) | `Get-ChildItem` (ou `ls`, `dir`), `-Force` pour les cachés |
| aller dans un dossier | `cd src/pages` | `Set-Location src\pages` (ou `cd`) |
| remonter d'un cran | `cd ..` | `cd ..` |
| revenir chez soi | `cd` ou `cd ~` | `cd ~` |
| revenir au dossier précédent | `cd -` | `cd -` |
| chercher un fichier par son nom | `find . -name "Bouton*"` | `Get-ChildItem -Recurse -Filter Bouton*` |

PowerShell connaît beaucoup d'alias « à la Linux » (`ls`, `cd`, `pwd`, `cat`, `rm`…), mais ce sont ses propres commandes derrière : les options sont différentes (`ls -la` ne marche pas dans PowerShell).
"""),
    L("Chemins absolus, relatifs, ~, . et ..", r"""
```
/home/ana                       ← ~ (ton dossier personnel)
└── projets
    ├── boutique
    │   ├── .env                ← caché (commence par un point)
    │   └── src
    │       └── components
    └── blog
```

Depuis `/home/ana/projets/boutique/src` :

| Chemin | Où ça mène | Type |
|---|---|---|
| `/home/ana/projets/blog` | blog | absolu (commence par `/`) |
| `~/projets/blog` | blog | absolu via `~` |
| `../../blog` | blog | relatif |
| `components` ou `./components` | src/components | relatif |
| `../.env` | le .env de boutique | relatif |

Sous Windows : `C:\Users\ana\projets\blog` (absolu), `..\..\blog` (relatif). Les noms de fichiers ne sont **pas** sensibles à la casse sous Windows (`README.md` = `readme.md`), mais ils le sont sous Linux.

Un nom avec des espaces s'écrit entre guillemets : `cd "Mes documents"`.
"""),
  ],
  recap=["pwd / Get-Location : où je suis ; ls / Get-ChildItem : ce qu'il y a ; cd / Set-Location : aller ailleurs.",
         "Absolu (depuis la racine) ou relatif (depuis ici) ; `.` ici, `..` parent, `~` chez moi.",
         "Fichiers cachés : `ls -a` / `-Force`.",
         "Tab pour compléter, ↑ pour l'historique, guillemets pour les espaces."],
  example=F("commandes.sh", "bash", r"""
pwd                         # /home/ana
cd projets/boutique         # relatif
ls -la                      # détails + fichiers cachés
cd src/components
cd ../../../blog            # trois crans vers le haut, puis blog
cd ~                        # retour à la maison
"""),
  notes=["Une commande par ligne.", "`#` commence un commentaire.", "`..` remonte, un nom descend."],
  tds=[
    TD(1, "Se repérer dans un projet",
       "Tu ouvres un terminal dans ton dossier personnel. Retrouve le composant `Bouton.tsx`, puis passe au blog **sans repartir de la racine**." + SH,
       ["Affiche d'abord le dossier courant",
        "Va dans le dossier qui contient `Bouton.tsx` et liste son contenu",
        "Depuis là, va dans `~/projets/blog` avec un **chemin relatif** (avec `..`)",
        "Termine par afficher le dossier courant ; aucune commande ne doit échouer"],
       [F("commandes.sh", "bash", r"""
# 1. où suis-je ?

# 2. aller dans le dossier de Bouton.tsx et lister

# 3. aller dans ~/projets/blog avec un chemin relatif

# 4. vérifier
""")],
       ["`pwd` affiche le dossier courant.",
        "Le composant est dans `projets/boutique/src/components/ui`.",
        "De `ui`, il faut remonter 4 fois (`ui` → `components` → `src` → `boutique` → `projets`) : `cd ../../../../blog`."],
       [F("commandes.sh", "bash", r"""
# 1. où suis-je ?
pwd
# 2. aller dans le dossier de Bouton.tsx et lister
cd projets/boutique/src/components/ui
ls
# 3. aller dans ~/projets/blog avec un chemin relatif
cd ../../../../blog
# 4. vérifier
pwd
""")],
       ["`..` remonte d'un cran à chaque fois", "Le terminal affiche toujours où tu es"],
       run=TERM(r"""
const cmds = term.commands();
assert.equal(cmds[0], 'pwd', 'La première commande affiche le dossier courant (pwd)');
assert(/Bouton\.tsx/.test(term.outputOf(/^ls\b/) || ''), 'Un ls liste le dossier qui contient Bouton.tsx', term.outputOf(/^ls\b/) || '(aucun ls)');
const rel = cmds.filter((c) => /^cd\s+\.\./.test(c));
assert(rel.length > 0, 'Un cd avec un chemin relatif (..)', cmds.join(' | '));
assert.equal(term.cwd(), '~/projets/blog', 'On termine dans ~/projets/blog');
assert.equal(cmds[cmds.length - 1], 'pwd', 'La dernière commande vérifie avec pwd');
assert.equal(term.failed().length, 0, 'Aucune commande en erreur', term.failed().join(' | '));
""", PROJET)),
    TD(2, "La même chose sous Windows (PowerShell)",
       "Même projet, mais sur un PC Windows : le dossier personnel est `C:\\Users\\ana`." + PS1,
       ["Affiche le dossier courant avec la commande PowerShell (pas l'alias)",
        "Va dans `C:\\Users\\ana\\projets\\boutique\\src` avec le **chemin absolu Windows** (avec des `\\`)",
        "Trouve tous les fichiers `.tsx` de ce dossier et de ses sous-dossiers",
        "Remonte de deux crans en **une** commande, et vérifie que tu es dans `C:\\Users\\ana\\projets`"],
       [F("commandes.ps1", "powershell", r"""
# 1. où suis-je ?

# 2. aller dans C:\Users\ana\projets\boutique\src (chemin absolu)

# 3. trouver les .tsx (récursivement)

# 4. remonter de deux crans, puis vérifier
""")],
       ["`Get-Location`.", "`Set-Location C:\\Users\\ana\\projets\\boutique\\src`.", "`Get-ChildItem -Recurse -Filter *.tsx` ; puis `Set-Location ..\\..`."],
       [F("commandes.ps1", "powershell", r"""
# 1. où suis-je ?
Get-Location
# 2. aller dans C:\Users\ana\projets\boutique\src (chemin absolu)
Set-Location C:\Users\ana\projets\boutique\src
# 3. trouver les .tsx (récursivement)
Get-ChildItem -Recurse -Filter *.tsx
# 4. remonter de deux crans, puis vérifier
Set-Location ..\..
Get-Location
""")],
       ["Chemins Windows avec \\", "Get-ChildItem -Recurse remplace find"],
       run=TERM(r"""
const cmds = term.commands();
assert(/^Get-Location$/i.test(cmds[0] || ''), 'Première commande : Get-Location');
assert(cmds.some((c) => /^(Set-Location|cd)\s+C:\\Users\\ana\\projets\\boutique\\src\\?$/i.test(c)), 'Set-Location avec le chemin absolu Windows C:\\Users\\ana\\projets\\boutique\\src');
const tsx = term.outputOf(/-Recurse/) || '';
assert(/Bouton\.tsx/.test(tsx) && /Accueil\.tsx/.test(tsx) && /main\.tsx/.test(tsx), 'Get-ChildItem -Recurse trouve les .tsx (Bouton, Accueil, main)', tsx);
assert(cmds.some((c) => /^(Set-Location|cd)\s+\.\.[\\/]\.\.$/i.test(c)), 'Remonter de deux crans en une commande (..\\..)');
assert.equal(term.cwd(), '~/projets', 'On termine dans C:\\Users\\ana\\projets');
assert(/Get-Location/i.test(cmds[cmds.length - 1]), 'On vérifie à la fin avec Get-Location');
assert.equal(term.failed().length, 0, 'Aucune commande en erreur', term.failed().join(' | '));
""", PROJET, entry="commandes.ps1")),
    TD(3, "Fichiers cachés et chemins sans se déplacer",
       "Tu es dans `~/projets/boutique/src`. On n'a pas toujours besoin de `cd` : la plupart des commandes acceptent un chemin. Fais tout **sans changer de dossier**." + SH,
       ["Liste le dossier **parent**, fichiers cachés compris",
        "Affiche le contenu du fichier `.env` du projet (il est dans le dossier parent)",
        "Liste `~/Documents` en utilisant `~`",
        "Aucune commande `cd` ; tu restes dans `~/projets/boutique/src`"],
       [F("commandes.sh", "bash", r"""
# tu es dans ~/projets/boutique/src

""")],
       ["`ls -a ..` (ou `ls -la ..`).", "`cat ../.env`.", "`ls ~/Documents`."],
       [F("commandes.sh", "bash", r"""
# tu es dans ~/projets/boutique/src
ls -la ..
cat ../.env
ls ~/Documents
""")],
       ["Les commandes acceptent des chemins", "Les fichiers cachés commencent par un point"],
       run=TERM(r"""
assert(!term.used(/^cd\b/), 'Aucun cd : on reste sur place');
assert.equal(term.cwd(), '~/projets/boutique/src', 'Toujours dans ~/projets/boutique/src');
const l = term.outputOf(/^ls\s+-[a-zA-Z]*a[a-zA-Z]*\s+\.\.$/);
assert(l && /\.env/.test(l) && /package\.json/.test(l), 'ls -a .. montre le parent, .env compris', l || '(pas de « ls -a .. »)');
assert(/API_URL=/.test(term.outputOf(/^cat\s+\.\.\/\.env$/) || ''), 'cat ../.env affiche le contenu du .env');
assert(/cv\.pdf/.test(term.outputOf(/^ls\s+~\/Documents\/?$/) || ''), 'ls ~/Documents liste cv.pdf');
assert.equal(term.failed().length, 0, 'Aucune commande en erreur', term.failed().join(' | '));
""", PROJET + "t.cd('projets/boutique/src');\n")),
  ])

# =========================================================================== 2. Fichiers
TELECH = r"""
t.fichier('Telechargements/facture-mars.pdf', '%PDF\n');
t.fichier('Telechargements/facture-avril.pdf', '%PDF\n');
t.fichier('Telechargements/cv final (2).pdf', '%PDF\n');
t.fichier('Telechargements/photo-vacances.jpg', 'JPG\n');
t.fichier('Telechargements/photo-chat.jpg', 'JPG\n');
t.fichier('Telechargements/installeur.tmp', 'x\n');
t.fichier('Telechargements/cache.tmp', 'x\n');
t.fichier('Telechargements/notes.txt', 'à garder\n');
t.cd('Telechargements');
"""

fichiers = DM("term-fichiers", "Créer, copier, déplacer, supprimer", 30,
  "Manipuler fichiers et dossiers en ligne de commande : créer, écrire dedans, copier, déplacer, renommer, supprimer, avec les jokers (`*`), sous bash et PowerShell.",
  "Créer la structure d'un projet, préparer un `.env`, ranger des fichiers, nettoyer un dossier de build : on le fait plus vite (et de façon reproductible) au terminal qu'à la souris.",
  ["Créer un dossier (`mkdir -p`) ou un fichier (`touch`, `New-Item`)", "Écrire dans un fichier : `>` (remplace), `>>` (ajoute) ; `Set-Content` / `Add-Content`",
   "Copier (`cp -r`), déplacer ou renommer (`mv`)", "Supprimer (`rm`, `rm -r`) : **sans corbeille**"],
  ["`mkdir -p a/b/c` crée tout le chemin d'un coup.",
   "`echo \"texte\" > f` **remplace** le contenu ; `>>` **ajoute** à la fin.",
   "`mv` sert à déplacer **et** à renommer.",
   "`*` remplace n'importe quels caractères : `*.pdf`, `facture-*`.",
   "`rm -r` supprime définitivement : relis la commande avant d'appuyer sur Entrée."],
  ["`>` au lieu de `>>` (le fichier est écrasé).", "Un nom avec des espaces sans guillemets (`cv final.pdf` = deux fichiers).", "`rm -rf` sur un chemin mal tapé."],
  [Q("`echo \"node_modules\" > .gitignore` sur un .gitignore existant :", ["ajoute une ligne", "remplace tout le contenu", "erreur", "crée .gitignore2"], 1, "> écrase ; >> ajoute."),
   Q("Renommer `a.txt` en `b.txt` :", ["rename a.txt b.txt", "mv a.txt b.txt", "cp a.txt b.txt", "cd a.txt b.txt"], 1, "mv déplace ou renomme."),
   Q("`rm photo vacances.jpg` (sans guillemets) supprime…", ["photo vacances.jpg", "deux fichiers « photo » et « vacances.jpg »", "rien", "le dossier"], 1, "L'espace sépare les arguments.")],
  prereq=[
    P("Redirection", "`>` envoie la sortie d'une commande dans un fichier (en le remplaçant), `>>` l'ajoute à la fin."),
    P("Joker (glob)", "`*` = n'importe quelle suite de caractères, `?` = un caractère : `*.jpg`."),
    P("Récursif", "Qui s'applique aussi à tout le contenu d'un dossier : `cp -r`, `rm -r`, `-Recurse`."),
  ],
  diagram=D(
    nodes=[
      N("m", 0, 1, "mkdir -p", "créer des dossiers", kind="pill", color="good"),
      N("w", 1, 0, "echo > / >>", "écrire, ajouter", kind="pill", color="accent"),
      N("c", 1, 2, "cp -r", "copier", kind="pill", color="accent"),
      N("v", 2, 1, "mv", "déplacer / renommer", kind="pill", color="warn"),
      N("r", 3, 1, "rm -r", "supprimer (définitif)", kind="pill", color="bad"),
    ],
    edges=[E("m", "w"), E("m", "c"), E("w", "v"), E("c", "v"), E("v", "r", dashed=True)],
    caption="Les cinq gestes de base ; le dernier ne pardonne pas."),
  lessons=[
    L("Créer et écrire", r"""
| Action | bash | PowerShell |
|---|---|---|
| créer un dossier (et ses parents) | `mkdir -p src/pages` | `New-Item -ItemType Directory -Path src\pages -Force` (ou `mkdir src\pages`) |
| créer un fichier vide | `touch index.html` | `New-Item index.html` |
| écrire (remplacer) | `echo "# Titre" > README.md` | `Set-Content README.md "# Titre"` |
| ajouter une ligne | `echo ".env" >> .gitignore` | `Add-Content .gitignore ".env"` |
| afficher | `cat README.md` | `Get-Content README.md` (ou `cat`) |

Astuce bash : `mkdir -p src/{components,pages}` crée les deux dossiers d'un coup.

`>` et `>>` marchent aussi en PowerShell pour envoyer la sortie d'une commande dans un fichier.
"""),
    L("Copier, déplacer, renommer, supprimer", r"""
| Action | bash | PowerShell |
|---|---|---|
| copier un fichier | `cp .env.example .env` | `Copy-Item .env.example .env` |
| copier un dossier | `cp -r src sauvegarde` | `Copy-Item src sauvegarde -Recurse` |
| déplacer | `mv *.pdf docs/` | `Move-Item *.pdf docs` |
| renommer | `mv ancien.txt nouveau.txt` | `Rename-Item ancien.txt nouveau.txt` (ou `Move-Item`) |
| supprimer un fichier | `rm f.txt` | `Remove-Item f.txt` |
| supprimer un dossier | `rm -r build` | `Remove-Item build -Recurse` |

⚠️ Le terminal n'a **pas de corbeille**. Avant un `rm -r` (ou `Remove-Item -Recurse`) avec un joker, lance d'abord `ls` avec le même motif pour voir ce qui sera supprimé.

Les noms avec espaces ou parenthèses : entre guillemets, `mv "cv final (2).pdf" cv.pdf`.
"""),
    L("Les jokers", r"""
| Motif | Correspond à |
|---|---|
| `*.pdf` | tous les fichiers qui finissent par `.pdf` |
| `facture-*` | tout ce qui commence par `facture-` |
| `photo?.jpg` | `photo1.jpg`, `photoA.jpg` (un seul caractère) |
| `src/*/index.ts` | `index.ts` dans chaque sous-dossier direct de `src` |

En bash, c'est le **shell** qui remplace le motif par la liste des fichiers avant de lancer la commande : `mv *.jpg images/` devient `mv photo-chat.jpg photo-vacances.jpg images/`. Les fichiers cachés (`.env`) ne sont pas inclus par `*`.
"""),
  ],
  recap=["mkdir -p / New-Item -ItemType Directory ; touch / New-Item.",
         "> remplace, >> ajoute ; Set-Content / Add-Content.",
         "cp -r, mv (déplacer et renommer), rm -r : pas de corbeille.",
         "Jokers `*` `?` ; guillemets pour les espaces."],
  example=F("commandes.sh", "bash", r"""
mkdir -p site/src/{components,pages}
echo "# Mon site" > site/README.md
echo "node_modules" > site/.gitignore
echo ".env" >> site/.gitignore      # ajoute sans écraser
cp -r site site-sauvegarde
mv site-sauvegarde /tmp/
"""),
  notes=["`-p` crée tous les dossiers du chemin.", "`>` puis `>>` : deux lignes dans .gitignore."],
  tds=[
    TD(1, "La structure d'un nouveau projet",
       "Crée la structure d'un petit site dans `~/projets/site`, uniquement avec des commandes." + SH,
       ["Dossiers : `src/components`, `src/pages`, `public`",
        "`README.md` qui contient exactement `# Mon site`",
        "`.gitignore` qui contient deux lignes : `node_modules` puis `.env` (écris la 1re avec `>`, la 2e avec `>>`)",
        "Un fichier vide `src/pages/index.html` ; à la fin, affiche le contenu de `.gitignore`"],
       [F("commandes.sh", "bash", r"""
cd ~/projets
# à toi
""")],
       ["`mkdir -p site/src/components site/src/pages site/public` (ou `cd site` d'abord).",
        "`echo \"# Mon site\" > README.md`.",
        "`touch src/pages/index.html` ; `cat .gitignore`."],
       [F("commandes.sh", "bash", r"""
cd ~/projets
mkdir -p site/src/{components,pages} site/public
cd site
echo "# Mon site" > README.md
echo "node_modules" > .gitignore
echo ".env" >> .gitignore
touch src/pages/index.html
cat .gitignore
""")],
       ["`>` puis `>>` : rien n'est écrasé", "`-p` crée tout le chemin"],
       run=TERM(r"""
for (const d of ['projets/site/src/components', 'projets/site/src/pages', 'projets/site/public']) assert(term.isDir(d), 'Dossier ' + d.replace('projets/site/', ''));
assert.equal(term.read('projets/site/README.md'), '# Mon site\n', 'README.md contient « # Mon site »');
assert.equal(term.read('projets/site/.gitignore'), 'node_modules\n.env\n', '.gitignore : node_modules puis .env', JSON.stringify(term.read('projets/site/.gitignore')));
assert(term.used(/>>\s*\.?\/?(site\/)?\.gitignore/), 'La 2e ligne est ajoutée avec >>');
assert(term.isFile('projets/site/src/pages/index.html') && term.read('projets/site/src/pages/index.html') === '', 'src/pages/index.html existe et est vide');
assert(/node_modules\n\.env/.test(term.outputOf(/^cat\s+.*\.gitignore$/) || ''), 'On affiche .gitignore à la fin');
assert.equal(term.failed().length, 0, 'Aucune commande en erreur', term.failed().join(' | '));
""", "t.dossier('projets');")),
    TD(2, "Ranger le dossier Téléchargements",
       "Le dossier `Telechargements` est en désordre. Range-le avec des jokers, et renomme le CV (attention aux espaces et aux parenthèses)." + SH,
       ["Crée `docs` et `images` ; déplace tous les `.pdf` dans `docs` et tous les `.jpg` dans `images` (avec `*`)",
        "Supprime tous les `.tmp` en une commande",
        "Renomme `docs/cv final (2).pdf` en `docs/cv.pdf`",
        "`notes.txt` reste où il est ; aucune commande ne doit échouer"],
       [F("commandes.sh", "bash", r"""
# tu es dans ~/Telechargements
ls
# à toi
""")],
       ["`mkdir docs images` puis `mv *.pdf docs/` et `mv *.jpg images/`.",
        "`rm *.tmp`.",
        "`mv \"docs/cv final (2).pdf\" docs/cv.pdf` (les guillemets gardent le nom en un seul morceau)."],
       [F("commandes.sh", "bash", r"""
# tu es dans ~/Telechargements
ls
mkdir docs images
mv *.pdf docs/
mv *.jpg images/
rm *.tmp
mv "docs/cv final (2).pdf" docs/cv.pdf
ls docs images
""")],
       ["Les jokers rangent tout d'un coup", "Les guillemets protègent les espaces"],
       run=TERM(r"""
assert.deepEqual(term.ls('Telechargements/docs'), ['cv.pdf', 'facture-avril.pdf', 'facture-mars.pdf'], 'docs : les 3 PDF, CV renommé', JSON.stringify(term.ls('Telechargements/docs')));
assert.deepEqual(term.ls('Telechargements/images'), ['photo-chat.jpg', 'photo-vacances.jpg'], 'images : les 2 JPG');
assert(!term.ls('Telechargements').some((n) => n.endsWith('.tmp')), 'Plus aucun .tmp');
assert(term.isFile('Telechargements/notes.txt'), 'notes.txt est toujours là');
assert(term.used(/\*\.pdf/) && term.used(/\*\.jpg/) && term.used(/rm\s+\*\.tmp/), 'Avec des jokers (*.pdf, *.jpg, *.tmp)');
assert.equal(term.failed().length, 0, 'Aucune commande en erreur', term.failed().join(' | '));
""", TELECH)),
    TD(3, "Préparer un projet sous Windows",
       "Même genre de travail, en PowerShell, sur un projet existant `C:\\Users\\ana\\projets\\api`." + PS1,
       ["Crée `logs` et `config` ; copie `.env.example` en `.env`",
        "Ajoute la ligne `DEBUG=true` à la fin de `.env` (sans écraser le reste)",
        "Fais une sauvegarde : copie tout le dossier `src` (avec son contenu) dans `src_sauvegarde`",
        "Supprime le dossier `ancien` (qui contient des fichiers)"],
       [F("commandes.ps1", "powershell", r"""
# tu es dans C:\Users\ana\projets\api
Get-ChildItem -Force
# à toi
""")],
       ["`New-Item -ItemType Directory logs, config` (ou deux `mkdir`).",
        "`Copy-Item .env.example .env` puis `Add-Content .env \"DEBUG=true\"`.",
        "`Copy-Item src src_sauvegarde -Recurse` ; `Remove-Item ancien -Recurse`."],
       [F("commandes.ps1", "powershell", r"""
# tu es dans C:\Users\ana\projets\api
Get-ChildItem -Force
New-Item -ItemType Directory -Path logs, config
Copy-Item .env.example .env
Add-Content .env "DEBUG=true"
Copy-Item src src_sauvegarde -Recurse
Remove-Item ancien -Recurse
Get-Content .env
""")],
       ["-Recurse pour les dossiers", "Add-Content ajoute sans écraser"],
       run=TERM(r"""
assert(term.isDir('projets/api/logs') && term.isDir('projets/api/config'), 'Dossiers logs et config');
assert.equal(term.read('projets/api/.env'), 'PORT=8000\nDB_URL=postgres://localhost/api\nDEBUG=true\n', '.env = copie de .env.example + DEBUG=true à la fin', JSON.stringify(term.read('projets/api/.env')));
assert.equal(term.read('projets/api/.env.example'), 'PORT=8000\nDB_URL=postgres://localhost/api\n', '.env.example n\'est pas modifié');
assert(term.isFile('projets/api/src_sauvegarde/index.js') && term.isFile('projets/api/src_sauvegarde/routes/produits.js'), 'src_sauvegarde contient tout src (sous-dossiers compris)');
assert(!term.exists('projets/api/ancien'), 'Le dossier ancien est supprimé');
assert.equal(term.failed().length, 0, 'Aucune commande en erreur', term.failed().join(' | '));
""", r"""
t.fichier('projets/api/.env.example', 'PORT=8000\nDB_URL=postgres://localhost/api\n');
t.fichier('projets/api/src/index.js', "console.log('api');\n");
t.fichier('projets/api/src/routes/produits.js', '// routes\n');
t.fichier('projets/api/ancien/v1.js', '// vieux code\n');
t.fichier('projets/api/ancien/notes.txt', 'à jeter\n');
t.cd('projets/api');
""", entry="commandes.ps1")),
  ])

# =========================================================================== 3. Chercher
CODE = r"""
t.fichier('projets/boutique/src/api.ts', "export async function charger() {\n  // TODO gérer les erreurs\n  console.log('chargement');\n}\n");
t.fichier('projets/boutique/src/panier.ts', "export function total() {\n  console.log('total');\n  return 0;\n}\n// TODO arrondir au centime\n");
t.fichier('projets/boutique/src/panier.test.ts', "test('total', () => {});\n");
t.fichier('projets/boutique/src/ui/Bouton.tsx', "// TODO accessibilité\nexport function Bouton() { console.log('rendu'); return null; }\n");
t.fichier('projets/boutique/src/ui/Bouton.test.tsx', "test('Bouton', () => {});\n");
t.fichier('projets/boutique/README.md', "# Boutique\nTODO : écrire la doc\n");
t.cd('projets/boutique');
"""

LOG_LINES = [
    "10.0.0.5 - - [16/Nov/2026:09:00:01] \"GET / HTTP/1.1\" 200 512",
    "10.0.0.7 - - [16/Nov/2026:09:00:02] \"GET /produits HTTP/1.1\" 200 2048",
    "10.0.0.5 - - [16/Nov/2026:09:00:03] \"POST /panier HTTP/1.1\" 500 128",
    "10.0.0.9 - - [16/Nov/2026:09:00:04] \"GET /produits/3 HTTP/1.1\" 404 64",
    "10.0.0.5 - - [16/Nov/2026:09:00:05] \"GET /produits HTTP/1.1\" 200 2048",
    "10.0.0.7 - - [16/Nov/2026:09:00:06] \"POST /panier HTTP/1.1\" 500 128",
    "10.0.0.5 - - [16/Nov/2026:09:00:07] \"GET /compte HTTP/1.1\" 401 32",
    "10.0.0.3 - - [16/Nov/2026:09:00:08] \"GET / HTTP/1.1\" 200 512",
    "10.0.0.5 - - [16/Nov/2026:09:00:09] \"POST /panier HTTP/1.1\" 500 128",
    "10.0.0.7 - - [16/Nov/2026:09:00:10] \"GET /produits HTTP/1.1\" 200 2048",
    "10.0.0.9 - - [16/Nov/2026:09:00:11] \"GET /produits HTTP/1.1\" 200 2048",
    "10.0.0.5 - - [16/Nov/2026:09:00:12] \"GET /produits/8 HTTP/1.1\" 200 900",
    "10.0.0.7 - - [16/Nov/2026:09:00:13] \"GET /paiement HTTP/1.1\" 500 128",
    "10.0.0.5 - - [16/Nov/2026:09:00:14] \"GET / HTTP/1.1\" 200 512",
]
LOG_JS = "t.fichier('logs/access.log', " + repr("\n".join(LOG_LINES) + "\n").replace("'", "\\'").replace('\\\\', '\\\\') + "); t.cd('logs');"
LOG_JS = "t.fichier('logs/access.log', " + __import__("json").dumps("\n".join(LOG_LINES) + "\n") + "); t.cd('logs');"

chercher = DM("term-chercher", "Chercher, filtrer, enchaîner", 30,
  "Trouver des fichiers et du texte (`find`, `grep`), enchaîner des commandes avec le pipe `|` (`sort`, `uniq`, `head`, `wc`) et enregistrer un résultat dans un fichier ; puis la même chose en PowerShell.",
  "« Où est utilisée cette fonction ? », « combien d'erreurs 500 ce matin ? », « quels fichiers de test existent ? » : en une ligne de terminal, sans ouvrir 30 fichiers.",
  ["**Trouver** des fichiers par nom : `find . -name \"*.test.ts\"`", "**Chercher** du texte : `grep -rn TODO src`",
   "**Enchaîner** : la sortie d'une commande devient l'entrée de la suivante (`|`)", "**Enregistrer** le résultat : `> fichier.txt`"],
  ["`grep -r` cherche dans tout un dossier, `-n` ajoute les numéros de ligne, `-i` ignore la casse, `-c` compte.",
   "`find` cherche des **noms** de fichiers ; `grep` cherche du **contenu**.",
   "Le pipe `|` relie des petits outils : `cut` (découper), `sort` (trier), `uniq -c` (compter les doublons voisins), `head` (les premiers), `wc -l` (compter les lignes).",
   "`uniq` ne regroupe que des lignes **voisines** : on trie avant (`sort | uniq -c`).",
   "En PowerShell, le pipe transporte des **objets** : `Select-String`, `Group-Object`, `Sort-Object`, `Select-Object -First`, `Measure-Object`."],
  ["`uniq -c` sans `sort` avant.", "Chercher `console.log` avec un point non échappé (il veut dire « n'importe quel caractère », ici sans gravité).", "Confondre `find` (noms) et `grep` (contenu)."],
  [Q("Compter les lignes qui contiennent « 500 » dans access.log :", ["find 500 access.log", "grep -c \" 500 \" access.log", "cat access.log 500", "wc 500"], 1, "grep -c compte les lignes trouvées."),
   Q("Pourquoi `sort` avant `uniq -c` ?", ["pour aller plus vite", "uniq ne regroupe que les lignes identiques voisines", "c'est obligatoire pour cut", "pour trier par nombre"], 1, "Sans tri, les mêmes IP séparées sont comptées à part."),
   Q("L'équivalent PowerShell de `grep -rn TODO src` :", ["Get-Content TODO", "Get-ChildItem -Recurse src | Select-String TODO", "Find-Text TODO", "Where-Object TODO"], 1, "Select-String cherche du texte dans les fichiers reçus.")],
  prereq=[
    P("Pipe `|`", "Envoie la sortie de la commande de gauche comme entrée de celle de droite."),
    P("Sortie standard / erreurs", "Le résultat normal d'une commande (stdout) et ses messages d'erreur (stderr) ; `>` ne redirige que le résultat normal."),
    P("Expression régulière", "Un motif de recherche : `^` début de ligne, `$` fin, `.` n'importe quel caractère, `\\.` un vrai point."),
  ],
  diagram=D(
    nodes=[
      N("c", 0, 0, "cut -d' ' -f1", "les IP du log", kind="pill", color="accent"),
      N("s", 1, 0, "sort", "regrouper les mêmes", kind="pill"),
      N("u", 2, 0, "uniq -c", "compter", kind="pill"),
      N("r", 2, 1, "sort -rn", "les plus fréquentes", kind="pill"),
      N("h", 1, 1, "head -3 > top.txt", "garder 3, enregistrer", kind="pill", color="good"),
    ],
    edges=[E("c", "s"), E("s", "u"), E("u", "r"), E("r", "h")],
    caption="Une chaîne de petits outils : chacun fait une seule chose, le pipe les relie."),
  lessons=[
    L("Trouver des fichiers, chercher du texte", r"""
| Besoin | bash | PowerShell |
|---|---|---|
| fichiers par nom | `find . -name "*.test.ts"` | `Get-ChildItem -Recurse -Filter *.test.ts` |
| texte dans un fichier | `grep TODO README.md` | `Select-String TODO README.md` |
| texte dans un dossier | `grep -rn TODO src` | `Get-ChildItem -Recurse src \| Select-String TODO` |
| sans tenir compte de la casse | `grep -i` | (par défaut) ; `-CaseSensitive` pour l'inverse |
| compter les lignes trouvées | `grep -c erreur log.txt` | `(Select-String erreur log.txt).Count` |
| inverser (lignes SANS le motif) | `grep -v` | `Select-String -NotMatch` |

La sortie de `grep -rn` : `src/panier.ts:5:// TODO arrondir` = fichier, numéro de ligne, ligne. Dans VS Code, Ctrl+clic sur `fichier:ligne` ouvre directement au bon endroit.
"""),
    L("Le pipe : enchaîner de petits outils", r"""
Chaque outil fait **une** chose ; le pipe `|` les relie :

| Outil | Rôle | Exemple |
|---|---|---|
| `cut -d' ' -f1` | garder un morceau de chaque ligne (ici le 1er champ séparé par des espaces) | les IP d'un log |
| `sort` / `sort -rn` | trier / trier par nombre décroissant | |
| `uniq -c` | compter les lignes identiques **voisines** | après `sort` |
| `head -n 3` / `tail -n 5` | les 3 premières / 5 dernières lignes | |
| `wc -l` | compter les lignes | |
| `grep` | filtrer | |

Les 3 IP les plus actives :

```bash
cut -d' ' -f1 access.log | sort | uniq -c | sort -rn | head -3 > top-ip.txt
```

Et `>` enregistre le résultat final dans un fichier.
"""),
    L("PowerShell : des objets dans le pipe", r"""
En PowerShell, le pipe transporte des **objets** (avec des propriétés), pas du texte :

```powershell
Get-ChildItem -Recurse -Filter *.ts | Select-String TODO           # fichier:ligne:texte

Get-Content access.log |
  ForEach-Object { $_.Split(" ")[0] } |        # l'IP de chaque ligne
  Group-Object |                                # regrouper (Count, Name)
  Sort-Object Count -Descending |
  Select-Object -First 3 Name, Count

Select-String -Path access.log -Pattern '" 500 ' | Measure-Object   # Count
Get-ChildItem | Where-Object { $_.Length -gt 1000 }                # filtrer sur une propriété
```

| bash | PowerShell |
|---|---|
| `grep` | `Select-String` |
| `sort`, `sort -rn` | `Sort-Object`, `Sort-Object -Descending` |
| `uniq -c` | `Group-Object` |
| `head -3`, `tail -5` | `Select-Object -First 3`, `-Last 5` |
| `wc -l` | `Measure-Object` (ou `-Line`) |
| `cut` | `ForEach-Object { $_.Split(" ")[0] }` |
"""),
  ],
  recap=["find : noms ; grep -rn : contenu (fichier:ligne:texte).",
         "Le pipe relie des petits outils : cut, sort, uniq -c, head, tail, wc -l.",
         "sort avant uniq ; > pour enregistrer.",
         "PowerShell : Select-String, Group-Object, Sort-Object, Select-Object, Measure-Object."],
  example=F("commandes.sh", "bash", r"""
grep -rn TODO src                 # où sont les TODO ?
grep -rn TODO src | wc -l         # combien ?
find . -name "*.test.ts"          # quels fichiers de test ?
grep -c '" 500 ' access.log       # combien d'erreurs 500 ?
cut -d' ' -f1 access.log | sort | uniq -c | sort -rn | head -3
"""),
  notes=["Chaque ligne répond à une question.", "Le pipe enchaîne les outils."],
  tds=[
    TD(1, "Faire l'inventaire du code",
       "Avant une réunion de planification, on te demande l'état du code de la boutique : les TODO, le nombre de `console.log` oubliés, les fichiers de test." + SH,
       ["`todos.txt` : toutes les lignes avec `TODO` dans `src` (récursif, avec les numéros de ligne), au format de `grep -rn`",
        "`nb-logs.txt` : le **nombre** de lignes de `src` qui contiennent `console.log` (un seul nombre)",
        "`tests.txt` : la liste des fichiers de test (qui finissent par `.test.ts` ou `.test.tsx`), trouvés avec `find`",
        "Le README (hors de `src`) ne doit pas apparaître dans `todos.txt`"],
       [F("commandes.sh", "bash", r"""
# tu es dans ~/projets/boutique
# à toi
""")],
       ["`grep -rn TODO src > todos.txt`.", "`grep -r \"console.log\" src | wc -l > nb-logs.txt`.", "`find . -name \"*.test.ts*\" > tests.txt` (le `*` final couvre `.ts` et `.tsx`)."],
       [F("commandes.sh", "bash", r"""
# tu es dans ~/projets/boutique
grep -rn TODO src > todos.txt
grep -r "console.log" src | wc -l > nb-logs.txt
find . -name "*.test.ts*" > tests.txt
cat todos.txt nb-logs.txt tests.txt
""")],
       ["grep pour le contenu, find pour les noms", "Le pipe compte"],
       run=TERM(r"""
assert.equal(term.read('projets/boutique/todos.txt'), 'src/api.ts:2:  // TODO gérer les erreurs\nsrc/panier.ts:5:// TODO arrondir au centime\nsrc/ui/Bouton.tsx:1:// TODO accessibilité\n', 'todos.txt : les 3 TODO de src, avec fichier:ligne', JSON.stringify(term.read('projets/boutique/todos.txt')));
assert.equal((term.read('projets/boutique/nb-logs.txt') || '').trim(), '3', 'nb-logs.txt : 3', JSON.stringify(term.read('projets/boutique/nb-logs.txt')));
const t = (term.read('projets/boutique/tests.txt') || '').trim().split('\n').sort();
assert.deepEqual(t, ['./src/panier.test.ts', './src/ui/Bouton.test.tsx'], 'tests.txt : les 2 fichiers de test', JSON.stringify(t));
assert(term.used(/^find\b/), 'tests.txt vient de find');
assert.equal(term.failed().length, 0, 'Aucune commande en erreur', term.failed().join(' | '));
""", CODE)),
    TD(2, "Analyser un fichier de logs",
       "Le serveur a eu des erreurs ce matin. Analyse `access.log` (une ligne par requête : IP, date, requête, code HTTP, taille)." + SH,
       ["`erreurs.txt` : le **nombre** de requêtes en erreur 500",
        "`top-ip.txt` : les 3 adresses IP qui ont fait le plus de requêtes, la plus active en premier, avec leur nombre (format de `uniq -c`)",
        "`fin.txt` : les 5 dernières lignes du log",
        "Une seule ligne de commande (avec des pipes) pour le top 3"],
       [F("commandes.sh", "bash", r"""
# tu es dans ~/logs
head -n 3 access.log
# à toi
""")],
       ["Le code HTTP est entouré d'espaces après le guillemet : `grep -c '\" 500 ' access.log > erreurs.txt`.",
        "`cut -d' ' -f1 access.log | sort | uniq -c | sort -rn | head -3 > top-ip.txt`.",
        "`tail -n 5 access.log > fin.txt`."],
       [F("commandes.sh", "bash", r"""
# tu es dans ~/logs
head -n 3 access.log
grep -c '" 500 ' access.log > erreurs.txt
cut -d' ' -f1 access.log | sort | uniq -c | sort -rn | head -3 > top-ip.txt
tail -n 5 access.log > fin.txt
cat erreurs.txt top-ip.txt
""")],
       ["sort avant uniq -c", "Un seul pipeline pour le top 3"],
       run=TERM(r"""
assert.equal((term.read('logs/erreurs.txt') || '').trim(), '4', 'erreurs.txt : 4 erreurs 500', JSON.stringify(term.read('logs/erreurs.txt')));
const top = (term.read('logs/top-ip.txt') || '').trim().split('\n').map((l) => l.trim().split(/\s+/));
assert.deepEqual(top.map((x) => x[1]), ['10.0.0.5', '10.0.0.7', '10.0.0.9'], 'top-ip.txt : 10.0.0.5, 10.0.0.7, 10.0.0.9', JSON.stringify(term.read('logs/top-ip.txt')));
assert.deepEqual(top.map((x) => x[0]), ['7', '4', '2'], '… avec leurs nombres (7, 4, 2)');
assert(term.used(/\|.*sort.*\|.*uniq\s+-c.*\|.*sort.*\|.*head/), 'Le top 3 tient en un pipeline (… | sort | uniq -c | sort … | head …)');
const fin = (term.read('logs/fin.txt') || '').trim().split('\n');
assert(fin.length === 5 && /09:00:14/.test(fin[4]) && /09:00:10/.test(fin[0]), 'fin.txt : les 5 dernières lignes');
assert.equal(term.failed().length, 0, 'Aucune commande en erreur', term.failed().join(' | '));
""", LOG_JS)),
    TD(3, "Les mêmes recherches en PowerShell",
       "Même log, mais sur le serveur Windows de l'équipe : fais l'analyse avec les commandes PowerShell (pas de `grep` ni de `cut` ici)." + PS1,
       ["Affiche le **nombre** de requêtes en erreur 500 avec `Select-String` et `Measure-Object`",
        "`top-ip.txt` : les 3 IP les plus actives (`Group-Object`, `Sort-Object`, `Select-Object`), avec `Name` et `Count`",
        "`erreurs.txt` : les lignes en erreur 500 elles-mêmes (avec `Select-String`)",
        "Aucune commande en erreur"],
       [F("commandes.ps1", "powershell", r"""
# tu es dans C:\Users\ana\logs
Get-Content access.log -TotalCount 3
# à toi
""")],
       ["`Select-String -Path access.log -Pattern '\" 500 ' | Measure-Object`.",
        "`Get-Content access.log | ForEach-Object { $_.Split(\" \")[0] } | Group-Object | Sort-Object Count -Descending | Select-Object -First 3 Name, Count > top-ip.txt`.",
        "`Select-String -Path access.log -Pattern '\" 500 ' > erreurs.txt`."],
       [F("commandes.ps1", "powershell", r"""
# tu es dans C:\Users\ana\logs
Get-Content access.log -TotalCount 3
Select-String -Path access.log -Pattern '" 500 ' | Measure-Object
Get-Content access.log | ForEach-Object { $_.Split(" ")[0] } | Group-Object | Sort-Object Count -Descending | Select-Object -First 3 Name, Count > top-ip.txt
Select-String -Path access.log -Pattern '" 500 ' > erreurs.txt
Get-Content top-ip.txt
""")],
       ["Des objets dans le pipe", "Group-Object remplace sort | uniq -c"],
       run=TERM(r"""
assert(term.used(/Select-String/i) && term.used(/Measure-Object/i), 'Select-String + Measure-Object');
assert(/Count\s*\n-+\s*\n\s*4\b/.test(term.outputOf(/Measure-Object/i) || ''), 'Le nombre affiché est 4', term.outputOf(/Measure-Object/i) || '');
const top = term.read('logs/top-ip.txt') || '';
const ips = (top.match(/10\.0\.0\.\d+/g) || []);
assert.deepEqual(ips, ['10.0.0.5', '10.0.0.7', '10.0.0.9'], 'top-ip.txt : 10.0.0.5, 10.0.0.7, 10.0.0.9 dans cet ordre', top);
assert(/Group-Object/i.test(term.commands().join('\n')) && /Sort-Object/i.test(term.commands().join('\n')), 'Group-Object et Sort-Object');
const err = (term.read('logs/erreurs.txt') || '').trim().split('\n');
assert(err.length === 4 && err.every((l) => /" 500 /.test(l)), 'erreurs.txt : les 4 lignes en 500', JSON.stringify(err));
assert(!term.used(/^(grep|cut)\b/), 'Sans grep ni cut (n\'existent pas dans PowerShell)');
assert.equal(term.failed().length, 0, 'Aucune commande en erreur', term.failed().join(' | '));
""", LOG_JS, entry="commandes.ps1")),
  ])

# =========================================================================== 4. Env et scripts
env = DM("term-env", "Variables d'environnement, PATH et scripts", 30,
  "Comprendre les variables d'environnement (dont le PATH), corriger un « command not found », écrire et lancer un script, sous bash et PowerShell.",
  "« npm: command not found », « API_URL is undefined », « running scripts is disabled on this system » : trois erreurs du quotidien qui viennent toutes de l'environnement, pas du code.",
  ["Lire / définir une variable : `echo $API_URL`, `export API_URL=…` ; `$env:API_URL`", "Comprendre le **PATH** : la liste des dossiers où le shell cherche les commandes",
   "Écrire un script : shebang, arguments (`$1`), droit d'exécution (`chmod +x`), `./script.sh`", "PowerShell : `.\\script.ps1` et la politique d'exécution"],
  ["Une variable d'environnement est héritée par les programmes lancés depuis le shell (node, npm…).",
   "`export` rend la variable visible aux programmes lancés ensuite ; sans `export`, elle reste dans le shell.",
   "Une commande est trouvée seulement si son dossier est dans le `PATH` (ou si on donne son chemin).",
   "Un script s'exécute dans un **sous-shell** : ses `cd` et variables non exportées ne remontent pas (`source` pour l'exécuter dans le shell courant).",
   "Windows bloque les scripts `.ps1` par défaut : `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` une fois pour toutes."],
  ["Ajouter un dossier au PATH en écrasant l'ancien (`export PATH=~/bin` au lieu de `…:$PATH`).", "Lancer un script sans `./` (le dossier courant n'est pas dans le PATH).", "Mettre des secrets dans un script commité au lieu de variables d'environnement."],
  [Q("`bash: deploiement: command not found` alors que le fichier existe dans ~/outils/bin :", ["le fichier est corrompu", "~/outils/bin n'est pas dans le PATH", "il faut sudo", "il faut redémarrer"], 1, "Le shell ne cherche que dans les dossiers du PATH."),
   Q("`./deploy.sh` → Permission denied :", ["chmod +x deploy.sh", "sudo deploy.sh", "rm deploy.sh", "cd deploy.sh"], 0, "Il manque le droit d'exécution."),
   Q("Dans un script, `$1` vaut…", ["le nom du script", "le 1er argument donné au script", "la 1re ligne", "rien"], 1, "./deploy.sh prod → $1 = prod.")],
  prereq=[
    P("Variable d'environnement", "Une paire NOM=valeur que le shell transmet aux programmes qu'il lance (`HOME`, `PATH`, `API_URL`…)."),
    P("PATH", "La liste des dossiers (séparés par `:` sous Linux, `;` sous Windows) où le shell cherche les commandes."),
    P("Script", "Un fichier texte contenant des commandes, exécutées dans l'ordre."),
    P("Shebang", "La 1re ligne d'un script Unix (`#!/usr/bin/env bash`) qui dit quel programme doit l'exécuter."),
  ],
  diagram=D(
    nodes=[
      N("c", 0, 1, "deploiement", "tu tapes", kind="doc"),
      N("b", 1, 1, "cherche dans le PATH", "/usr/bin, /bin…", kind="box", color="warn"),
      N("n", 2, 0, "pas trouvé", "command not found", kind="pill", color="bad"),
      N("o", 2, 2, "trouvé", "~/outils/bin/deploiement", kind="pill", color="good"),
      N("x", 3, 1, "export PATH=…:$PATH", "ajoute ~/outils/bin", kind="note", color="accent"),
    ],
    edges=[E("c", "b"), E("b", "n"), E("b", "o"), E("n", "x", dashed=True)],
    caption="Une commande n'est trouvée que si son dossier est dans le PATH."),
  lessons=[
    L("Variables d'environnement", r"""
| Action | bash | PowerShell |
|---|---|---|
| lire | `echo $API_URL` | `$env:API_URL` |
| définir (pour la session) | `export API_URL=https://api.exemple.fr` | `$env:API_URL = "https://api.exemple.fr"` |
| définir pour une seule commande | `API_URL=… npm run dev` | (pas de syntaxe courte) |
| lister | `env` | `Get-ChildItem Env:` |
| supprimer | `unset API_URL` | `Remove-Item Env:API_URL` |

Un programme lancé depuis le shell (node, npm, php…) **hérite** des variables exportées : c'est ainsi que `process.env.API_URL` (Node) ou `$_ENV['API_URL']` (PHP) reçoivent leur valeur. Les fichiers `.env` sont lus par les frameworks (dotenv, Symfony, Next.js) pour éviter de tout exporter à la main.

Ces définitions durent jusqu'à la fermeture du terminal. Pour les garder, on les met dans `~/.bashrc` / `~/.zshrc` (bash, zsh) ou dans le profil PowerShell / les « Variables d'environnement » de Windows.
"""),
    L("Le PATH et « command not found »", r"""
Quand tu tapes `npm`, le shell cherche un fichier exécutable nommé `npm` dans chaque dossier du `PATH`, dans l'ordre :

```bash
echo $PATH
/usr/local/bin:/usr/bin:/bin
```

« command not found » veut donc dire l'une de ces trois choses :
1. faute de frappe (`nmp`) ;
2. le programme n'est pas installé ;
3. il est installé, mais **son dossier n'est pas dans le PATH**.

Pour le cas 3 : `export PATH="$HOME/outils/bin:$PATH"` (on **ajoute** devant, on n'écrase pas). `which deploiement` (bash) / `Get-Command deploiement` (PowerShell) dit où une commande est trouvée.

Sous Windows, le PATH se sépare avec `;` et se voit avec `$env:Path`.
"""),
    L("Écrire et lancer un script", r"""
```bash
#!/usr/bin/env bash
# sauvegarde.sh : copie src dans sauvegardes/<nom>
mkdir -p "sauvegardes/$1"
cp -r src "sauvegardes/$1/"
echo "Sauvegarde $1 terminée"
```

```bash
chmod +x sauvegarde.sh       # une fois : donner le droit d'exécution
./sauvegarde.sh v1           # ./ = « le fichier d'ici » ; $1 vaut v1
bash sauvegarde.sh v1        # autre façon, sans chmod
```

Un script s'exécute dans un **sous-shell** : un `cd` dans le script ne change pas ton dossier courant. Pour l'exécuter dans le shell courant (par exemple pour charger des variables) : `source config.sh`.

**PowerShell** : `.\deploy.ps1 prod` (les arguments sont dans `$args[0]`, `$args[1]`…). La première fois, Windows refuse : *running scripts is disabled on this system*. Autorise tes scripts une fois pour toutes : `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
"""),
  ],
  recap=["export NOM=valeur / $env:NOM = \"valeur\" ; les programmes lancés en héritent.",
         "command not found : faute de frappe, pas installé, ou dossier absent du PATH.",
         "PATH : ajouter devant, ne pas écraser.",
         "Script : shebang, chmod +x, ./script.sh arg ($1) ; PowerShell : .\\script.ps1 et Set-ExecutionPolicy."],
  example=F("commandes.sh", "bash", r"""
echo $PATH
export PATH="$HOME/outils/bin:$PATH"
which deploiement
export API_URL=https://api.exemple.fr
echo "API : $API_URL"
"""),
  notes=["On ajoute au PATH sans l'écraser.", "`export` : visible des programmes lancés ensuite."],
  tds=[
    TD(1, "« command not found » : réparer le PATH",
       "Un collègue t'a installé l'outil `deploiement` dans `~/outils/bin`, mais le terminal dit *command not found*. Comprends pourquoi et répare, sans casser les autres commandes." + SH,
       ["Lance `deploiement` une première fois pour voir l'erreur (elle est attendue), puis affiche le `PATH`",
        "Ajoute `~/outils/bin` **au début** du `PATH`, sans perdre les dossiers existants",
        "Vérifie avec `which deploiement`, puis lance `deploiement` (il doit afficher `Déploiement OK`)",
        "Définis et exporte `API_URL=https://api.exemple.fr`, puis affiche-la ; `ls` doit toujours marcher à la fin"],
       [F("commandes.sh", "bash", r"""
deploiement
# à toi
""")],
       ["`echo $PATH`.", "`export PATH=\"$HOME/outils/bin:$PATH\"`.", "`which deploiement` ; `export API_URL=https://api.exemple.fr` ; `echo $API_URL` ; `ls`."],
       [F("commandes.sh", "bash", r"""
deploiement
echo $PATH
export PATH="$HOME/outils/bin:$PATH"
which deploiement
deploiement
export API_URL=https://api.exemple.fr
echo $API_URL
ls
""")],
       ["Le PATH garde ses anciens dossiers", "La commande est trouvée"],
       run=TERM(r"""
const cmds = term.commands();
assert(cmds[0] === 'deploiement' && term.failed()[0] === 'deploiement', 'Le premier appel échoue (command not found)');
assert(term.used(/echo\s+"?\$PATH"?/), 'On affiche le PATH');
const p = term.env('PATH') || '';
assert(p.startsWith('/home/ana/outils/bin:'), 'PATH commence par /home/ana/outils/bin', p);
assert(p.includes('/usr/bin') && p.includes('/bin'), 'Les anciens dossiers du PATH sont gardés', p);
assert.equal((term.outputOf(/^which\s+deploiement$/) || '').trim(), '/home/ana/outils/bin/deploiement', 'which trouve l\'outil');
assert.includes(term.outputOf(/^deploiement$/) || '', 'Déploiement OK', 'Le second appel affiche « Déploiement OK »');
assert.equal(term.env('API_URL'), 'https://api.exemple.fr', 'API_URL exportée');
assert.equal(term.failed().length, 1, 'Une seule erreur : le premier appel', term.failed().join(' | '));
assert(term.used(/^ls\b/) && !term.failed().some((c) => /^ls/.test(c)), 'ls marche toujours');
""", "t.fichier('outils/bin/deploiement', 'echo \"Déploiement OK\"\\n', true); t.dossier('projets');")),
    TD(2, "Écrire un script de sauvegarde",
       "Écris `sauvegarde.sh` (2e fichier) : il copie `src` dans `sauvegardes/<nom>`, où `<nom>` est le premier argument. Puis, dans `commandes.sh`, rends-le exécutable et lance-le." + SH,
       ["`sauvegarde.sh` commence par le shebang `#!/usr/bin/env bash`",
        "Il crée `sauvegardes/$1` (avec les parents), y copie le dossier `src` entier, puis affiche `Sauvegarde <nom> terminée`",
        "`commandes.sh` : donne le droit d'exécution, puis lance `./sauvegarde.sh v1` et `./sauvegarde.sh v2`",
        "Le script ne change pas ton dossier courant"],
       [F("commandes.sh", "bash", r"""
# tu es dans ~/projets/app
./sauvegarde.sh v1
"""), F("sauvegarde.sh", "bash", r"""
# à toi
""")],
       ["`chmod +x sauvegarde.sh` dans commandes.sh, avant de le lancer.",
        "Dans le script : `mkdir -p \"sauvegardes/$1\"` puis `cp -r src \"sauvegardes/$1/\"`.",
        "`echo \"Sauvegarde $1 terminée\"`."],
       [F("commandes.sh", "bash", r"""
# tu es dans ~/projets/app
chmod +x sauvegarde.sh
./sauvegarde.sh v1
./sauvegarde.sh v2
ls sauvegardes
"""), F("sauvegarde.sh", "bash", r"""
#!/usr/bin/env bash
# copie src dans sauvegardes/<nom>
mkdir -p "sauvegardes/$1"
cp -r src "sauvegardes/$1/"
echo "Sauvegarde $1 terminée"
""")],
       ["$1 reçoit l'argument", "chmod +x avant ./"],
       run=TERM(r"""
assert(/^#!\/usr\/bin\/env bash/.test((term.read('projets/app/sauvegarde.sh') || '').trim()), 'Le script commence par le shebang');
assert(term.isExec('projets/app/sauvegarde.sh'), 'Le script est exécutable (chmod +x)');
for (const v of ['v1', 'v2']) {
  assert(term.isFile(`projets/app/sauvegardes/${v}/src/index.js`) && term.isFile(`projets/app/sauvegardes/${v}/src/lib/util.js`), `sauvegardes/${v}/src contient tout src`);
}
assert.includes(term.outputOf(/sauvegarde\.sh v2/) || '', 'Sauvegarde v2 terminée', 'Message « Sauvegarde v2 terminée »');
assert.equal(term.cwd(), '~/projets/app', 'Le dossier courant n\'a pas changé');
assert.equal(term.failed().length, 0, 'Aucune commande en erreur', term.failed().join(' | '));
""", "t.fichier('projets/app/src/index.js', \"console.log('app');\\n\"); t.fichier('projets/app/src/lib/util.js', '// util\\n'); t.cd('projets/app');")),
    TD(3, "Variables et script sous Windows",
       "Sous Windows : définis une variable d'environnement, écris un script `deploy.ps1` qui l'utilise, et lance-le (Windows va d'abord refuser)." + PS1,
       ["Définis `API_URL` à `https://api.exemple.fr` pour la session",
        "`deploy.ps1` (2e fichier) crée le fichier `build\\<arg>.txt` (dossier créé au besoin) et affiche `Déploiement de <arg> vers <API_URL>` (avec `$args[0]` et `$env:API_URL`)",
        "Lance `.\\deploy.ps1 prod` : l'erreur de politique d'exécution est attendue",
        "Autorise les scripts pour ton compte (`RemoteSigned`), puis relance `.\\deploy.ps1 prod`"],
       [F("commandes.ps1", "powershell", r"""
# tu es dans C:\Users\ana\projets\app
# à toi
"""), F("deploy.ps1", "powershell", r"""
# à toi
""")],
       ["`$env:API_URL = \"https://api.exemple.fr\"`.",
        "Dans le script : `New-Item -ItemType File -Path \"build\\$($args[0]).txt\" -Force` puis `Write-Output \"Déploiement de $($args[0]) vers $env:API_URL\"`.",
        "`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`."],
       [F("commandes.ps1", "powershell", r"""
# tu es dans C:\Users\ana\projets\app
$env:API_URL = "https://api.exemple.fr"
.\deploy.ps1 prod
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\deploy.ps1 prod
Get-ChildItem build
"""), F("deploy.ps1", "powershell", r"""
# deploy.ps1 <environnement>
New-Item -ItemType File -Path "build\$($args[0]).txt" -Force
Write-Output "Déploiement de $($args[0]) vers $env:API_URL"
""")],
       ["La politique d'exécution se règle une fois", "$args[0] et $env:API_URL"],
       run=TERM(r"""
assert.equal(term.env('API_URL'), 'https://api.exemple.fr', 'API_URL définie');
const lanc = term.commands().filter((c) => /deploy\.ps1\s+prod/i.test(c));
assert(lanc.length >= 2, 'Le script est lancé deux fois');
assert(term.failed().length === 1 && /deploy\.ps1/i.test(term.failed()[0]), 'Seul le premier lancement échoue (scripts bloqués)', term.failed().join(' | '));
assert.equal(term.policy, 'RemoteSigned', 'Politique d\'exécution : RemoteSigned');
assert.includes(term.outputOf(/deploy\.ps1\s+prod/i) || '', 'Déploiement de prod vers https://api.exemple.fr', 'Le script affiche le bon message');
assert(term.isFile('projets/app/build/prod.txt'), 'build\\prod.txt est créé');
""", "t.fichier('projets/app/src/index.js', '// app\\n'); t.cd('projets/app');", entry="commandes.ps1")),
  ])

# =========================================================================== 5. Processus et ports
SERVEUR = r"""
t.fichier('projets/boutique/package.json', JSON.stringify({ name: 'boutique', version: '2.0.0', scripts: { dev: 'node serveur.js', test: 'echo 12 tests ok' }, dependencies: { express: '^4.21.0' } }, null, 2) + '\n');
t.fichier('projets/boutique/serveur.js', "const app = require('express')();\napp.get('/', (req, res) => res.end('Boutique v2'));\napp.listen(3000);\n");
t.dossier('projets/boutique/node_modules/express');
t.cd('projets/boutique');
"""

processus = DM("term-processus", "Processus et ports : « address already in use »", 25,
  "Comprendre ce qu'est un processus et un port, trouver quel programme occupe un port, arrêter un processus, et vérifier qu'un serveur répond, sous Linux/macOS et Windows.",
  "« EADDRINUSE: address already in use :::3000 » est l'une des erreurs les plus fréquentes en développement web : un ancien serveur tourne encore. La solution prend 30 secondes quand on connaît les 3 commandes.",
  ["Lire l'erreur : **quel port** est pris ?", "Trouver **qui** l'occupe : `lsof -i :3000` / `Get-NetTCPConnection -LocalPort 3000`",
   "**Arrêter** ce processus : `kill PID` / `Stop-Process -Id PID`", "Relancer, puis **vérifier** : `curl localhost:3000` / `Invoke-RestMethod`"],
  ["Un processus = un programme en cours d'exécution, identifié par un numéro (PID).",
   "Un port = un « numéro de porte » sur ta machine ; un seul programme peut écouter sur un port donné.",
   "Ctrl+C arrête le programme lancé au premier plan dans le terminal ; un programme oublié dans un autre terminal (ou planté) peut garder le port.",
   "`kill PID` demande l'arrêt ; `kill -9 PID` force (en dernier recours).",
   "Alternative : lancer sur un autre port (`PORT=3001 npm run dev`)."],
  ["Redémarrer l'ordinateur à chaque EADDRINUSE.", "Tuer un processus au hasard sans vérifier son nom.", "Oublier de vérifier que le nouveau serveur répond."],
  [Q("« EADDRINUSE :::3000 » veut dire…", ["le code a une erreur de syntaxe", "un autre programme écoute déjà sur le port 3000", "Internet est coupé", "npm n'est pas installé"], 1, "Le port est occupé."),
   Q("Trouver le programme qui occupe le port 3000 (Linux/macOS) :", ["ps 3000", "lsof -i :3000", "kill 3000", "port 3000"], 1, "lsof liste les fichiers et connexions ouverts."),
   Q("Sous Windows, l'équivalent :", ["Get-Process 3000", "Get-NetTCPConnection -LocalPort 3000", "netstat-kill 3000", "Stop-Port 3000"], 1, "La colonne OwningProcess donne le PID.")],
  prereq=[
    P("Processus / PID", "Un programme en cours d'exécution ; le PID est son numéro unique."),
    P("Port", "Un numéro (0 à 65535) qui identifie un service sur une machine : 3000 pour un serveur de dev, 5432 pour PostgreSQL, 443 pour HTTPS…"),
    P("localhost", "Ta propre machine (`127.0.0.1`)."),
  ],
  diagram=D(
    nodes=[
      N("e", 0, 0, "EADDRINUSE :3000", "npm run dev échoue", kind="note", color="bad"),
      N("f", 1, 0, "lsof -i :3000", "qui ? → PID 4100", kind="pill", color="warn"),
      N("k", 2, 0, "kill 4100", "arrêter l'ancien", kind="pill", color="accent"),
      N("r", 2, 1, "npm run dev", "relancer", kind="pill", color="good"),
      N("v", 1, 1, "curl :3000", "vérifier", kind="pill", color="good"),
    ],
    edges=[E("e", "f"), E("f", "k"), E("k", "r"), E("r", "v")],
    caption="Lire le port, trouver le PID, arrêter, relancer, vérifier."),
  lessons=[
    L("Processus et ports", r"""
Quand tu lances `npm run dev`, un **processus** démarre (un programme `node`, avec un PID) et **écoute** sur un port (3000, 5173, 8000…). Ton navigateur s'y connecte via `http://localhost:3000`.

Un seul processus peut écouter sur un port donné. Si un ancien serveur tourne encore (terminal oublié, éditeur qui l'a lancé, plantage sans arrêt), le nouveau échoue :

```
Error: listen EADDRINUSE: address already in use :::3000
```

| Besoin | bash (Linux, macOS) | PowerShell (Windows) |
|---|---|---|
| lister les processus | `ps aux` (`ps aux \| grep node`) | `Get-Process` (`Get-Process node`) |
| qui écoute sur le port 3000 ? | `lsof -i :3000` | `Get-NetTCPConnection -LocalPort 3000` (colonne `OwningProcess`) |
| arrêter le processus | `kill 4100` (`kill -9` pour forcer) | `Stop-Process -Id 4100` (`-Force`) |
| arrêter tous les `node` | `pkill node` | `Stop-Process -Name node` |
| tester le serveur | `curl http://localhost:3000` | `Invoke-RestMethod http://localhost:3000` |

En une ligne (bash) : `kill $(lsof -t -i :3000)` (`-t` ne garde que les PID).
"""),
    L("Les bons réflexes", r"""
1. **Lis l'erreur** : elle dit quel port.
2. **Regarde qui l'occupe** avant de tuer : si c'est ton ancien serveur `node`, arrête-le ; si c'est autre chose (une base de données, Docker…), change plutôt de port.
3. **Arrête proprement** : dans le terminal où le serveur tourne, **Ctrl+C**. `kill` sinon ; `kill -9` seulement s'il ne répond pas.
4. **Relance**, puis **vérifie** que le serveur répond (`curl`), avant de chercher un bug dans ton code.

Changer de port (sans rien tuer) : `PORT=3001 npm run dev` (si le serveur lit `process.env.PORT`), ou `npm run dev -- --port 3001` pour Vite/Next.
"""),
  ],
  recap=["EADDRINUSE : le port est pris par un autre processus.",
         "lsof -i :PORT / Get-NetTCPConnection -LocalPort PORT → PID.",
         "kill PID / Stop-Process -Id PID ; Ctrl+C si tu as le terminal.",
         "Relancer, puis vérifier avec curl / Invoke-RestMethod."],
  example=F("commandes.sh", "bash", r"""
npm run dev                  # EADDRINUSE :::3000
lsof -i :3000                # node 4100 …
kill 4100
npm run dev
curl http://localhost:3000
"""),
  notes=["On lit le PID dans la sortie de lsof.", "On vérifie à la fin."],
  tds=[
    TD(1, "EADDRINUSE : libérer le port 3000",
       "Tu veux lancer la boutique, mais un ancien serveur tourne encore sur le port 3000. Libère le port, relance, et vérifie que c'est bien la **nouvelle** version qui répond." + SH,
       ["Lance `npm run dev` et lis l'erreur (elle est attendue)",
        "Trouve le PID du processus qui écoute sur le port 3000, et arrête **ce** processus (lis son numéro dans la sortie, ou utilise `$(lsof -t -i :3000)`)",
        "Relance `npm run dev`",
        "Vérifie avec `curl http://localhost:3000` : la réponse doit être `Boutique v2`"],
       [F("commandes.sh", "bash", r"""
# tu es dans ~/projets/boutique
npm run dev
# à toi
""")],
       ["`lsof -i :3000` affiche une ligne `node  4100  ana … TCP *:3000 (LISTEN)` : 4100 est le PID.",
        "`kill 4100` (ou `kill $(lsof -t -i :3000)` pour ne pas recopier le numéro).",
        "`npm run dev` puis `curl http://localhost:3000`."],
       [F("commandes.sh", "bash", r"""
# tu es dans ~/projets/boutique
npm run dev
lsof -i :3000
kill $(lsof -t -i :3000)
npm run dev
curl http://localhost:3000
""")],
       ["On lit le port dans l'erreur", "On vérifie la réponse à la fin"],
       run=TERM(r"""
assert(term.failed()[0] === 'npm run dev', 'Le premier npm run dev échoue (EADDRINUSE)');
assert(term.used(/lsof\s+.*-i\s*:?3000|lsof\s+-i\s*:3000/), 'On cherche qui occupe le port 3000 (lsof -i :3000)');
assert(!term.procs().some((p) => p.cmd === 'node ancien-serveur.js'), 'L\'ancien serveur est arrêté');
assert(term.procs().some((p) => p.cmd === 'node serveur.js' && p.port === 3000), 'Le nouveau serveur écoute sur 3000');
assert.equal((term.outputOf(/^curl\b/) || '').trim(), 'Boutique v2', 'curl localhost:3000 répond « Boutique v2 »');
assert(term.procs().some((p) => p.nom === 'sshd'), 'Les autres processus n\'ont pas été touchés');
assert.equal(term.failed().length, 1, 'Une seule erreur : le premier lancement', term.failed().join(' | '));
""", SERVEUR + "t.processus('node', 'node ancien-serveur.js', 3000, 'Boutique v1');\n")),
    TD(2, "Faire le ménage dans les processus node",
       "Après une journée de travail, plusieurs serveurs `node` tournent encore en arrière-plan. Fais le ménage **sans** toucher aux autres programmes." + SH,
       ["Liste tous les processus, puis seulement ceux qui contiennent `node` (avec un pipe)",
        "Arrête tous tes processus `node` (en une ou plusieurs commandes)",
        "Vérifie qu'aucun programme n'écoute plus sur 3000 ni 5173 (`curl` doit échouer : c'est attendu)",
        "`postgres` et les processus système doivent toujours tourner"],
       [F("commandes.sh", "bash", r"""
# à toi
""")],
       ["`ps aux` puis `ps aux | grep node`.", "`pkill node` arrête tous tes processus node d'un coup (ou `kill PID1 PID2 PID3`).", "`curl http://localhost:3000` puis `curl http://localhost:5173`."],
       [F("commandes.sh", "bash", r"""
ps aux
ps aux | grep node
pkill node
ps aux
curl http://localhost:3000
curl http://localhost:5173
""")],
       ["grep filtre la liste", "pkill arrête par nom"],
       run=TERM(r"""
assert(term.used(/^ps\s+aux$/), 'ps aux');
assert(term.commands().some((c) => /^ps\s+aux\s*\|\s*grep\s+node$/.test(c)), 'ps aux | grep node pour filtrer les processus node');
assert(!term.procs().some((p) => p.nom === 'node'), 'Plus aucun processus node', JSON.stringify(term.procs().map((p) => p.nom)));
assert(term.procs().some((p) => p.nom === 'postgres') && term.procs().some((p) => p.nom === 'systemd'), 'postgres et les processus système tournent toujours');
const curls = term.commands().filter((c) => /^curl/.test(c));
assert(curls.some((c) => /3000/.test(c)) && curls.some((c) => /5173/.test(c)), 'On vérifie les ports 3000 et 5173 avec curl');
assert(term.failed().every((c) => /^curl|grep/.test(c)), 'Seuls les curl échouent (c\'est attendu)', term.failed().join(' | '));
""", "t.processus('node', 'node serveur.js', 3000); t.processus('node', 'node node_modules/.bin/vite', 5173); t.processus('node', 'node --watch scripts/build.js'); t.processus('postgres', 'postgres -D /var/lib/postgresql', 5432);")),
    TD(3, "Libérer un port sous Windows",
       "Même situation que le niveau 1, sur un PC Windows : un ancien serveur occupe le port 3000." + PS1,
       ["Lance `npm run dev` (l'erreur est attendue)",
        "Trouve le PID avec `Get-NetTCPConnection -LocalPort 3000` (colonne `OwningProcess`)",
        "Arrête ce processus avec `Stop-Process`, puis relance `npm run dev`",
        "Vérifie avec `Invoke-RestMethod http://localhost:3000` : `Boutique v2`"],
       [F("commandes.ps1", "powershell", r"""
# tu es dans C:\Users\ana\projets\boutique
npm run dev
# à toi
""")],
       ["`Get-NetTCPConnection -LocalPort 3000` affiche `OwningProcess : 4100`.",
        "`Stop-Process -Id 4100`.",
        "En une ligne : `Get-NetTCPConnection -LocalPort 3000 | Stop-Process` (le pipe transmet `OwningProcess`)."],
       [F("commandes.ps1", "powershell", r"""
# tu es dans C:\Users\ana\projets\boutique
npm run dev
Get-NetTCPConnection -LocalPort 3000
Stop-Process -Id 4100
npm run dev
Invoke-RestMethod http://localhost:3000
""")],
       ["OwningProcess donne le PID", "Invoke-RestMethod remplace curl"],
       run=TERM(r"""
assert(/^npm run dev$/i.test(term.failed()[0] || ''), 'Le premier npm run dev échoue');
assert(term.used(/Get-NetTCPConnection\s+-LocalPort\s+3000/i), 'Get-NetTCPConnection -LocalPort 3000');
assert(term.used(/Stop-Process/i), 'Stop-Process');
assert(!term.procs().some((p) => p.cmd === 'node ancien-serveur.js'), 'L\'ancien serveur est arrêté');
assert.equal((term.outputOf(/Invoke-RestMethod/i) || '').trim(), 'Boutique v2', 'Invoke-RestMethod répond « Boutique v2 »');
assert.equal(term.failed().length, 1, 'Une seule erreur : le premier lancement', term.failed().join(' | '));
""", SERVEUR + "t.processus('node', 'node ancien-serveur.js', 3000, 'Boutique v1');\n", entry="commandes.ps1")),
  ])

# =========================================================================== 6. Traduire
INSTALL_BASH = r"""
# Installation (README du projet, version Linux / macOS)
mkdir -p storage/logs storage/cache
cp .env.example .env
echo "APP_ENV=dev" >> .env
rm -r tmp
ls storage
"""

INSTALL_PS = r"""
# Installation (README du projet, version Windows)
New-Item -ItemType Directory -Path storage\logs, storage\cache -Force
Copy-Item .env.example .env
Add-Content .env "APP_ENV=dev"
Remove-Item tmp -Recurse
Get-ChildItem storage
"""

ONBOARD = r"""
t.fichier('projets/catalogue/package.json', JSON.stringify({ name: 'catalogue', version: '1.0.0', scripts: { dev: 'node serveur.js', test: 'echo 24 tests passés' }, dependencies: { express: '^4.21.0' } }, null, 2) + '\n');
t.fichier('projets/catalogue/serveur.js', "const app = require('express')();\napp.get('/', (req, res) => res.end('Catalogue prêt'));\napp.listen(4000);\n");
t.fichier('projets/catalogue/.env.example', 'PORT=4000\nDATABASE_URL=\n');
t.fichier('projets/catalogue/README.md', '# Catalogue\\n\\n1. copier .env.example en .env et remplir DATABASE_URL\\n2. npm install\\n3. npm test\\n4. npm run dev (port 4000)\\n');
"""

traduire = DM("term-traduire", "Linux ↔ Windows : traduire, installer un projet", 30,
  "Passer d'un système à l'autre sans se perdre (la table de correspondance bash / PowerShell / cmd, WSL, fins de ligne), et suivre les étapes d'installation d'un projet du README jusqu'au serveur qui tourne.",
  "Les README sont souvent écrits pour Linux/macOS, et ton PC de travail est peut-être sous Windows (ou l'inverse). Savoir traduire une commande, c'est ne plus être bloquée par un tutoriel.",
  ["Reconnaître le shell (invite `$` ou `PS C:\\>`)", "Traduire avec la **table de correspondance**",
   "Sous Windows : **WSL** ou **Git Bash** pour avoir bash", "Installer un projet : `cp .env.example .env`, `npm install`, `npm test`, `npm run dev`"],
  ["Les idées sont les mêmes partout ; seuls les noms et les options changent.",
   "PowerShell a des alias (`ls`, `cd`, `cat`, `rm`, `cp`, `mv`) mais pas les options Linux (`rm -rf` ne marche pas).",
   "WSL donne un vrai Linux dans Windows ; Git Bash donne bash avec Git for Windows.",
   "Fins de ligne : Windows `CRLF`, Linux `LF` ; Git peut les convertir (`core.autocrlf`). Un script bash en CRLF plante (`$'\\r': command not found`).",
   "`npm`, `node`, `git`, `php`, `composer` s'écrivent pareil partout."],
  ["Copier `rm -rf` dans PowerShell.", "Mélanger `\\` et `/` dans un script bash.", "Ignorer une étape du README (le `.env` oublié)."],
  [Q("`cp .env.example .env` en PowerShell :", ["Copy-Item .env.example .env", "cp -i .env", "copy-env", "New-Item .env"], 0, "cp est d'ailleurs un alias de Copy-Item."),
   Q("`export API_URL=x` en PowerShell :", ["set API_URL=x", "$env:API_URL = \"x\"", "export-env API_URL", "Set-Location API_URL"], 1, "Les variables d'environnement sont dans $env:."),
   Q("Le moyen le plus fidèle d'avoir bash sous Windows :", ["cmd", "WSL", "PowerShell ISE", "Notepad"], 1, "WSL fait tourner un vrai Linux.")],
  prereq=[
    P("WSL", "Windows Subsystem for Linux : un vrai Linux (Ubuntu…) qui tourne dans Windows, avec son terminal bash."),
    P("Git Bash", "Un terminal bash livré avec Git for Windows, pratique pour les commandes courantes."),
    P("CRLF / LF", "Les caractères de fin de ligne : `\\r\\n` sous Windows, `\\n` sous Linux et macOS."),
  ],
  diagram=D(
    nodes=[
      N("r", 0, 1, "README (bash)", "cp, rm -r, export", kind="doc", color="muted"),
      N("t", 1, 1, "Correspondances", "même idée, autre nom", kind="box", color="warn"),
      N("p", 2, 0, "PowerShell", "Copy-Item, $env:…", kind="pill", color="accent"),
      N("w", 2, 2, "WSL / Git Bash", "bash sous Windows", kind="pill", color="good"),
    ],
    edges=[E("r", "t"), E("t", "p"), E("t", "w")],
    caption="Un README Linux sous Windows : traduire en PowerShell, ou utiliser bash via WSL ou Git Bash."),
  lessons=[
    L("La table de correspondance", r"""
| Action | bash (Linux, macOS, WSL, Git Bash) | PowerShell | cmd (ancien) |
|---|---|---|---|
| où suis-je | `pwd` | `Get-Location` | `cd` |
| lister | `ls -la` | `Get-ChildItem -Force` | `dir /a` |
| aller | `cd dossier` | `Set-Location dossier` | `cd dossier` |
| créer un dossier | `mkdir -p a/b` | `New-Item -ItemType Directory a\b -Force` | `mkdir a\b` |
| fichier vide | `touch f` | `New-Item f` | `type nul > f` |
| afficher | `cat f` | `Get-Content f` | `type f` |
| écrire / ajouter | `echo x > f` / `>> f` | `Set-Content f x` / `Add-Content f x` | `echo x > f` / `>> f` |
| copier | `cp -r a b` | `Copy-Item a b -Recurse` | `xcopy a b /e /i` |
| déplacer / renommer | `mv a b` | `Move-Item a b` / `Rename-Item a b` | `move a b` / `ren a b` |
| supprimer | `rm -r d` | `Remove-Item d -Recurse` | `rmdir /s d` |
| chercher du texte | `grep -rn x .` | `Get-ChildItem -Recurse \| Select-String x` | `findstr /s /n x *` |
| variable | `export X=1`, `$X` | `$env:X = "1"`, `$env:X` | `set X=1`, `%X%` |
| processus sur un port | `lsof -i :3000` | `Get-NetTCPConnection -LocalPort 3000` | `netstat -ano \| findstr :3000` |
| arrêter un processus | `kill PID` | `Stop-Process -Id PID` | `taskkill /PID PID /F` |
"""),
    L("Avoir bash sous Windows, et les pièges", r"""
- **WSL** (`wsl --install` dans PowerShell administrateur) : un vrai Ubuntu. Idéal si l'équipe travaille sous Linux/macOS : tous les README marchent tels quels. Mets tes projets **dans** le système de fichiers Linux (`~/projets`), pas dans `/mnt/c/…` (beaucoup plus lent).
- **Git Bash** : installé avec Git for Windows, suffisant pour `ls`, `cp`, `grep`, les scripts simples.
- **Terminal Windows** : une seule application avec des onglets PowerShell, WSL, Git Bash.

Pièges :
- **Fins de ligne** : un script `.sh` enregistré en CRLF plante sous Linux avec `$'\r': command not found`. Dans VS Code, en bas à droite, passe de `CRLF` à `LF`.
- **Chemins** : `\` sous Windows, `/` ailleurs ; dans le code (Node, PHP), utilise `/` ou `path.join`.
- **Casse** : `import './Bouton'` marche sous Windows même si le fichier s'appelle `bouton.tsx`… et casse en production sous Linux.
- **Scripts npm** : `"clean": "rm -rf dist"` ne marche pas sous PowerShell : préfère des outils Node (`rimraf dist`) ou des scripts multiplateformes.
"""),
    L("Installer un projet en suivant le README", r"""
Presque tous les projets web s'installent de la même façon :

```bash
git clone https://github.com/equipe/catalogue.git && cd catalogue   # 1. récupérer le code, entrer dans le dossier
cp .env.example .env                                                  # 2. configuration locale (secrets, URL de BDD)
#    → remplir les valeurs vides de .env
npm install                                                           # 3. dépendances (crée node_modules)
npm test                                                              # 4. vérifier que tout est vert
npm run dev                                                           # 5. lancer, puis ouvrir l'URL affichée
```

Si une étape échoue, **lis le message** avant d'aller plus loin : `npm ERR! enoent … package.json` = tu n'es pas dans le bon dossier ; `Cannot find module` = `npm install` oublié ; `EADDRINUSE` = port occupé (module précédent).
"""),
  ],
  recap=["Même idée, autre nom : garde la table de correspondance.",
         "PowerShell a des alias mais pas les options Linux.",
         "WSL ou Git Bash pour suivre un README bash sous Windows ; attention CRLF / LF et à la casse.",
         "Installer : dossier, .env, npm install, npm test, npm run dev ; lire chaque erreur."],
  example=F("commandes.ps1", "powershell", r"""
# README (bash) : cp .env.example .env && echo "DEBUG=1" >> .env && rm -r tmp
Copy-Item .env.example .env
Add-Content .env "DEBUG=1"
Remove-Item tmp -Recurse
"""),
  notes=["Chaque commande bash a son équivalent PowerShell.", "Les noms changent, pas les idées."],
  tds=[
    TD(1, "Traduire un README Linux en PowerShell",
       "Le README de l'API donne des commandes bash (en commentaire dans le fichier). Tu es sous Windows : écris l'équivalent PowerShell, ligne par ligne." + PS1,
       ["Même résultat que le script bash : dossiers `storage\\logs` et `storage\\cache`, `.env` copié de `.env.example` avec `APP_ENV=dev` ajouté à la fin, dossier `tmp` supprimé",
        "Uniquement des commandes PowerShell (pas d'options Linux comme `-p` ou `-r`)",
        "Termine en listant `storage`",
        "Aucune commande en erreur"],
       [F("commandes.ps1", "powershell", "# Version bash du README :\n" + "\n".join("# " + l for l in INSTALL_BASH.strip().splitlines()[1:]) + "\n\n# Ta version PowerShell :\n")],
       ["`New-Item -ItemType Directory -Path storage\\logs, storage\\cache -Force`.",
        "`Copy-Item .env.example .env` puis `Add-Content .env \"APP_ENV=dev\"`.",
        "`Remove-Item tmp -Recurse` ; `Get-ChildItem storage`."],
       [F("commandes.ps1", "powershell", "# Version bash du README :\n" + "\n".join("# " + l for l in INSTALL_BASH.strip().splitlines()[1:]) + "\n\n# Ta version PowerShell :" + INSTALL_PS.replace("# Installation (README du projet, version Windows)\n", ""))],
       ["Une commande PowerShell par commande bash", "Même résultat"],
       run=TERM(r"""
assert(term.isDir('projets/api/storage/logs') && term.isDir('projets/api/storage/cache'), 'storage\\logs et storage\\cache');
assert.equal(term.read('projets/api/.env'), 'APP_KEY=\nDB=sqlite\nAPP_ENV=dev\n', '.env = .env.example + APP_ENV=dev', JSON.stringify(term.read('projets/api/.env')));
assert(!term.exists('projets/api/tmp'), 'tmp supprimé');
assert(!term.used(/\s-(p|r|rf)\b/), 'Pas d\'options Linux (-p, -r, -rf)');
assert(/Get-ChildItem|^ls|^dir/i.test(term.commands()[term.commands().length - 1] || ''), 'On liste storage à la fin');
assert.equal(term.failed().length, 0, 'Aucune commande en erreur', term.failed().join(' | '));
""", "t.fichier('projets/api/.env.example', 'APP_KEY=\\nDB=sqlite\\n'); t.fichier('projets/api/tmp/cache.bin', 'x\\n'); t.cd('projets/api');", entry="commandes.ps1")),
    TD(2, "Et dans l'autre sens : PowerShell → bash",
       "Une collègue sous Windows t'envoie ses commandes PowerShell (en commentaire). Tu es sous Linux (ou WSL) : écris l'équivalent bash." + SH,
       ["Même résultat : dossiers `storage/logs` et `storage/cache`, `.env` = `.env.example` + `APP_ENV=dev`, dossier `tmp` supprimé",
        "Uniquement des commandes bash (pas de `New-Item`, `Copy-Item`…)",
        "Termine en listant `storage`",
        "Aucune commande en erreur"],
       [F("commandes.sh", "bash", "# Version PowerShell de la collègue :\n" + "\n".join("# " + l for l in INSTALL_PS.strip().splitlines()[1:]) + "\n\n# Ta version bash :\n")],
       ["`mkdir -p storage/logs storage/cache`.", "`cp .env.example .env` puis `echo \"APP_ENV=dev\" >> .env`.", "`rm -r tmp` ; `ls storage`."],
       [F("commandes.sh", "bash", "# Version PowerShell de la collègue :\n" + "\n".join("# " + l for l in INSTALL_PS.strip().splitlines()[1:]) + "\n\n# Ta version bash :" + INSTALL_BASH.replace("# Installation (README du projet, version Linux / macOS)\n", ""))],
       ["Même résultat qu'en PowerShell", "Les options bash"],
       run=TERM(r"""
assert(term.isDir('projets/api/storage/logs') && term.isDir('projets/api/storage/cache'), 'storage/logs et storage/cache');
assert.equal(term.read('projets/api/.env'), 'APP_KEY=\nDB=sqlite\nAPP_ENV=dev\n', '.env = .env.example + APP_ENV=dev', JSON.stringify(term.read('projets/api/.env')));
assert(!term.exists('projets/api/tmp'), 'tmp supprimé');
assert(!term.used(/New-Item|Copy-Item|Add-Content|Remove-Item|Get-ChildItem/i), 'Uniquement des commandes bash');
assert(/^ls\s+storage/.test(term.commands()[term.commands().length - 1] || ''), 'On liste storage à la fin');
assert.equal(term.failed().length, 0, 'Aucune commande en erreur', term.failed().join(' | '));
""", "t.fichier('projets/api/.env.example', 'APP_KEY=\\nDB=sqlite\\n'); t.fichier('projets/api/tmp/cache.bin', 'x\\n'); t.cd('projets/api');")),
    TD(3, "Installer un projet de A à Z",
       "Premier jour sur le projet `catalogue` (déjà cloné dans `~/projets`). Suis le README jusqu'au serveur qui répond. Tu ouvres ton terminal dans ton dossier personnel." + SH,
       ["Va dans le projet et lis le README",
        "Crée `.env` à partir de `.env.example`, et remplis `DATABASE_URL` avec `postgres://localhost/catalogue` (la ligne `DATABASE_URL=` vide ne doit plus être vide)",
        "Installe les dépendances, lance les tests, puis le serveur",
        "Vérifie avec `curl` que le serveur répond sur le port **4000** (`Catalogue prêt`)"],
       [F("commandes.sh", "bash", r"""
# premier jour : tu es dans ton dossier personnel
npm install
""")],
       ["`npm install` ici échoue : il n'y a pas de package.json dans ton dossier personnel. Commence par `cd projets/catalogue`.",
        "Pour remplir la valeur : réécris le fichier, par exemple `echo \"PORT=4000\" > .env` puis `echo \"DATABASE_URL=postgres://localhost/catalogue\" >> .env`.",
        "`npm install && npm test && npm run dev`, puis `curl http://localhost:4000`."],
       [F("commandes.sh", "bash", r"""
# premier jour : tu es dans ton dossier personnel
cd projets/catalogue
cat README.md
cp .env.example .env
echo "PORT=4000" > .env
echo "DATABASE_URL=postgres://localhost/catalogue" >> .env
npm install
npm test
npm run dev
curl http://localhost:4000
""")],
       ["Le README donne l'ordre", "Chaque étape est vérifiée"],
       run=TERM(r"""
assert.equal(term.cwd(), '~/projets/catalogue', 'On travaille dans ~/projets/catalogue');
assert(term.used(/^cat\s+README\.md$/), 'On lit le README');
const env = term.read('projets/catalogue/.env') || '';
assert(/^DATABASE_URL=postgres:\/\/localhost\/catalogue$/m.test(env), '.env : DATABASE_URL remplie', JSON.stringify(env));
assert(!/^DATABASE_URL=$/m.test(env), '… et plus de ligne DATABASE_URL vide');
assert(/^PORT=4000$/m.test(env), '.env garde PORT=4000');
assert(term.isDir('projets/catalogue/node_modules'), 'npm install a créé node_modules');
assert.includes(term.outputOf(/^npm (run )?test$/) || '', '24 tests passés', 'npm test passe');
assert.equal((term.outputOf(/^curl\b/) || '').trim(), 'Catalogue prêt', 'curl localhost:4000 répond « Catalogue prêt »');
assert.equal(term.failed().length, 0, 'Aucune commande en erreur', term.failed().join(' | '));
""", ONBOARD)),
  ])

MODULES = [bases, fichiers, chercher, env, processus, traduire]

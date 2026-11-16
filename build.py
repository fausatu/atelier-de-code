import os
import json, sys
sys.path.insert(0, "/home/claude/atelier")
from c_php import MODULES as PHP
from c_doctrine import MODULES as DOC
from c_ddd import MODULES as DDD
from c_react import MODULES as REACT
from c_next import MODULES as NEXT
from c_dto import MODULES as DTO
from c_data import MODULES as DATA_
from c_arch import MODULES as ARCH
from c_git import MODULES as GIT
from c_debug import MODULES as DEBUG
from c_api import MODULES as API
from c_forms import MODULES as FORMS
from c_decoupe import MODULES as DECOUPE
from c_term import MODULES as TERM
from c_ts import MODULES as TSM

TRACKS = [
    {"id": "php", "group": "back", "name": "PHP orienté objet", "short": "PHP POO", "color": "violet",
     "desc": "Classes, encapsulation, héritage, interfaces, autoload, injection de dépendances."},
    {"id": "doctrine", "group": "back", "name": "Doctrine ORM", "short": "Doctrine", "color": "orange",
     "desc": "Entités, migrations, persist/flush, repositories, relations, N+1."},
    {"id": "dto", "group": "back", "name": "DTO avec Symfony", "short": "DTO", "color": "blue",
     "desc": "Recevoir et renvoyer du JSON proprement : DTO d'entrée, validation, sortie, filtres."},
    {"id": "arch", "group": "back", "name": "Architecture : qui fait quoi", "short": "Architecture", "color": "olive",
     "desc": "Contrôleur, DTO, service, entité, repository : leurs rôles, leurs liens, et le trajet complet React → Symfony."},
    {"id": "ddd", "group": "back", "name": "DDD (bonus)", "short": "DDD (bonus)", "color": "green",
     "desc": "Pour aller plus loin : value objects, entités riches, agrégats, architecture en couches."},
    {"id": "ts", "group": "front", "name": "TypeScript", "short": "TypeScript", "color": "navy",
     "desc": "Types de base, unions, génériques, null et données inconnues, React typé, lire les erreurs."},
    {"id": "react", "group": "front", "name": "React", "short": "React", "color": "cyan",
     "desc": "Composants, state, formulaires, effets, hooks personnalisés."},
    {"id": "data", "group": "front", "name": "React : données & API", "short": "Données & API", "color": "rose",
     "desc": "Requêtes HTTP, fetch et axios, mutations, couche API, TanStack Query."},
    {"id": "forms", "group": "front", "name": "Formulaires React", "short": "Formulaires", "color": "indigo",
     "desc": "Du formulaire fait main à React Hook Form et TanStack Form : validation zod, listes, composants de champ, migration."},
    {"id": "next", "group": "front", "name": "Next.js (App Router)", "short": "Next.js", "color": "graphite",
     "desc": "Routes, Server/Client Components, cache, Server Actions, API."},
    {"id": "git", "group": "outils", "name": "Git & GitHub", "short": "Git & GitHub", "color": "brick",
     "desc": "Le modèle de Git, merge, rebase, revenir en arrière, Conventional Commits, Pull Requests, outils."},
    {"id": "terminal", "group": "outils", "name": "Terminal (Linux & Windows)", "short": "Terminal", "color": "slate",
     "desc": "bash et PowerShell : se déplacer, fichiers, chercher, PATH et scripts, ports occupés, installer un projet."},
    {"id": "decoupe", "group": "methode", "name": "Découper une fonctionnalité", "short": "Découper", "color": "plum",
     "desc": "Du ticket au code : scénarios, variables (comment je le sais ?), étapes, tranches."},
    {"id": "debug", "group": "methode", "name": "Déboguer", "short": "Débogage", "color": "amber",
     "desc": "Lire les erreurs et corriger de vrais bugs : PHP, Doctrine, Symfony, React, API, Next.js, Git."},
    {"id": "api", "group": "back", "name": "API REST", "short": "API", "color": "teal",
     "desc": "Créer une API (REST, erreurs, auth, cache, idempotence, limites) et la consommer en PHP et en JS."},
]

modules = PHP + DOC + DTO + ARCH + DDD + TSM + REACT + DATA_ + FORMS + NEXT + GIT + TERM + API + DECOUPE + DEBUG
ids = set()
for m in modules:
    assert m["id"] not in ids, m["id"]
    ids.add(m["id"])
    assert len(m["flow"]) >= 3, m["id"]
    for q in m["quiz"]:
        assert 0 <= q["answer"] < len(q["options"]), (m["id"], q["q"])
    if "tds" in m:
        assert m["tds"], (m["id"], "tds vide")
        levels = [t["level"] for t in m["tds"]]
        assert levels == sorted(set(levels)), (m["id"], "niveaux", levels)
        for td in m["tds"]:
            for k in ["title", "enonce", "consignes", "files", "hints", "solution", "checks"]:
                assert td.get(k), (m["id"], td.get("level"), k)
            for f in td["files"] + td["solution"]:
                assert f.get("path"), (m["id"], td["level"], "fichier sans chemin")
            if td.get("run"):
                assert td["run"]["kind"] in ("php", "react", "js", "next", "git", "term"), (m["id"], td["level"])
        assert m["lessons"], (m["id"], "pas de leçon")
        assert m["example"]["files"], (m["id"], "exemple vide")
        if m.get("diagram"):
            nid = {n["id"] for n in m["diagram"]["nodes"]}
            for e in m["diagram"]["edges"]:
                assert e["from"] in nid and e["to"] in nid, (m["id"], "arête", e)
    else:
        td = m["td"]
        for k in ["title", "enonce", "consignes", "starter", "hints", "solution", "checks"]:
            assert td.get(k), (m["id"], k)

from doctrine_sim import DOCTRINE_SETUP
from symfony_sim import SYMFONY_SETUP
from httpclient_sim import HTTPCLIENT_SETUP
SETUPS = {"doctrine": DOCTRINE_SETUP.strip("\n"), "symfony": SYMFONY_SETUP.strip("\n"), "httpclient": HTTPCLIENT_SETUP.strip("\n")}
for m in modules:
    for td in m.get("tds", []):
        r = td.get("run")
        if r and r.get("setup"):
            for k, v in SETUPS.items():
                r["setup"] = r["setup"].replace(v, "@@SETUP:" + k + "@@")
GROUPS = [
    {"id": "methode", "name": "Méthode", "desc": "Savoir s'y prendre : découper une fonctionnalité, déboguer."},
    {"id": "back", "name": "Web · Back-end", "desc": "PHP → Doctrine → DTO → Architecture → API, DDD en bonus."},
    {"id": "front", "name": "Web · Front-end", "desc": "TypeScript → React → Données & API → Formulaires → Next.js."},
    {"id": "outils", "name": "Outils", "desc": "Les outils du quotidien : Git, le terminal."},
]
_gids = {g["id"] for g in GROUPS}
for t in TRACKS:
    assert t.get("group") in _gids, ("parcours sans catégorie", t["id"])
_cal = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ecole", "calendrier.json"), encoding="utf-8"))
CAL = {"jours": {k: {"formation": "e", "rentree": "r", "entreprise": "n", "examens": "x", "rattrapages": "t", "ferie": "f"}[v]
                 for k, v in _cal["jours"].items() if v in ("formation", "rentree", "entreprise", "examens", "rattrapages", "ferie")},
       "debut": "2026-09-01", "fin": "2028-08-31",
       "evenements": [
           {"date": "2026-09-21", "titre": "Rentrée MBA 1", "type": "ecole"},
           {"date": "2026-09-21", "titre": "Formation tuteurs (session 1)", "type": "info"},
           {"date": "2026-10-01", "titre": "Formation tuteurs (session 1)", "type": "info"},
           {"date": "2026-10-13", "titre": "Formation tuteurs (session 2)", "type": "info"},
           {"date": "2026-11-03", "titre": "Formation tuteurs (session 2) + réunion tuteurs", "type": "info"},
           {"date": "2027-04-23", "titre": "Examens MBA 1", "type": "examen"},
           {"date": "2027-08-23", "titre": "Rattrapages MBA 1 (jusqu'au 27/08)", "type": "examen"},
           {"date": "2027-09-06", "titre": "Rentrée MBA 2", "type": "ecole"},
           {"date": "2028-07-03", "titre": "Examens MBA 2 (jusqu'au 07/07)", "type": "examen"},
           {"date": "2028-08-21", "titre": "Rattrapages MBA 2 (jusqu'au 25/08)", "type": "examen"},
       ]}
data = {"groups": GROUPS, "tracks": TRACKS, "modules": modules, "setups": SETUPS, "cal": CAL}
js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
tpl = open("/home/claude/atelier/template.html", encoding="utf-8").read()
assert "/*__CONTENT__*/" in tpl
out = tpl.replace("/*__CONTENT__*/null", js)
open("/home/claude/atelier/index.html", "w", encoding="utf-8").write(out)
v2 = sum(1 for m in modules if "tds" in m)
print(len(modules), "modules (", v2, "en v2 ),", len(out) // 1024, "KiB")

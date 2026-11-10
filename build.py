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

TRACKS = [
    {"id": "php", "name": "PHP orienté objet", "short": "PHP POO", "color": "violet",
     "desc": "Classes, encapsulation, héritage, interfaces, autoload, injection de dépendances."},
    {"id": "doctrine", "name": "Doctrine ORM", "short": "Doctrine", "color": "orange",
     "desc": "Entités, migrations, persist/flush, repositories, relations, N+1."},
    {"id": "dto", "name": "DTO avec Symfony", "short": "DTO", "color": "blue",
     "desc": "Recevoir et renvoyer du JSON proprement : DTO d'entrée, validation, sortie, filtres."},
    {"id": "arch", "name": "Architecture : qui fait quoi", "short": "Architecture", "color": "olive",
     "desc": "Contrôleur, DTO, service, entité, repository : leurs rôles, leurs liens, et le trajet complet React → Symfony."},
    {"id": "ddd", "name": "DDD (bonus)", "short": "DDD (bonus)", "color": "green",
     "desc": "Pour aller plus loin : value objects, entités riches, agrégats, architecture en couches."},
    {"id": "react", "name": "React", "short": "React", "color": "cyan",
     "desc": "Composants, state, formulaires, effets, hooks personnalisés."},
    {"id": "data", "name": "React : données & API", "short": "Données & API", "color": "rose",
     "desc": "Requêtes HTTP, fetch et axios, mutations, couche API, TanStack Query."},
    {"id": "next", "name": "Next.js (App Router)", "short": "Next.js", "color": "graphite",
     "desc": "Routes, Server/Client Components, cache, Server Actions, API."},
    {"id": "git", "name": "Git & GitHub", "short": "Git & GitHub", "color": "brick",
     "desc": "Le modèle de Git, merge, rebase, revenir en arrière, Conventional Commits, Pull Requests, outils."},
]

modules = PHP + DOC + DTO + ARCH + DDD + REACT + DATA_ + NEXT + GIT
ids = set()
for m in modules:
    assert m["id"] not in ids, m["id"]
    ids.add(m["id"])
    assert len(m["flow"]) >= 3, m["id"]
    for q in m["quiz"]:
        assert 0 <= q["answer"] < len(q["options"]), (m["id"], q["q"])
    td = m["td"]
    for k in ["title", "enonce", "consignes", "starter", "hints", "solution", "checks"]:
        assert td.get(k), (m["id"], k)

data = {"tracks": TRACKS, "modules": modules}
js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
tpl = open("/home/claude/atelier/template.html", encoding="utf-8").read()
assert "/*__CONTENT__*/" in tpl
out = tpl.replace("/*__CONTENT__*/null", js)
open("/home/claude/atelier/index.html", "w", encoding="utf-8").write(out)
print(len(modules), "modules,", len(out) // 1024, "KiB")

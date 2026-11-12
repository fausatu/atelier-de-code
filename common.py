"""Structure d'un module (v2).

M(...)        : un module complet
L(title, md)  : une leçon (section longue, markdown : paragraphes, listes, ```code```)
P(term, def)  : un prérequis / mot de vocabulaire
D(...)        : un diagramme (rendu en SVG par la page)
F(path, lang, code) : un fichier de code
Q(...)        : une question de quiz
TD(...)       : un exercice (niveau 1, 2 ou 3)
RUN(kind, tests, ...) : exécution dans le navigateur (php | react | js) + tests
"""


def F(path, lang, code):
    return {"path": path, "lang": lang, "code": code.strip("\n")}


def code(lang, src):
    """Compat : un seul fichier sans nom."""
    return F("", lang, src)


def P(term, definition):
    return {"term": term, "def": definition}


def L(title, body):
    return {"title": title, "body": body.strip("\n")}


def Q(q, options, answer, why):
    return {"q": q, "options": options, "answer": answer, "why": why}


def N(id, col, row, label, sub=None, kind="box", color=None, span=1):
    """Nœud de diagramme. kind : box | db | actor | doc | note | pill | file"""
    n = {"id": id, "col": col, "row": row, "label": label, "kind": kind}
    if sub:
        n["sub"] = sub
    if color:
        n["color"] = color
    if span != 1:
        n["span"] = span
    return n


def E(frm, to, label=None, dashed=False, color=None, back=False):
    e = {"from": frm, "to": to}
    if label:
        e["label"] = label
    if dashed:
        e["dashed"] = True
    if color:
        e["color"] = color
    if back:
        e["back"] = True
    return e


def D(nodes, edges, lanes=None, caption=None):
    d = {"nodes": nodes, "edges": edges}
    if lanes:
        d["lanes"] = lanes
    if caption:
        d["caption"] = caption
    return d


def LANE(label, col_from, col_to, color=None):
    l = {"label": label, "from": col_from, "to": col_to}
    if color:
        l["color"] = color
    return l


def RUN(kind, tests="", entry=None, api=None, setup=None):
    """kind : 'php' | 'react' | 'js'.
    tests : code de test (PHP : utilise check('desc', bool) ; JS : assert(cond, 'desc'), root, click(), type(), tick()).
    entry : fichier d'entrée (react/js). api : code JS définissant window.__api pour le faux axios.
    setup : code exécuté avant le code de l'élève (PHP : préfixe ; JS : fichier virtuel supplémentaire)."""
    r = {"kind": kind, "tests": tests.strip("\n")}
    if entry:
        r["entry"] = entry
    if api:
        r["api"] = api.strip("\n")
    if setup:
        r["setup"] = setup.strip("\n")
    return r


def TD(level, title, enonce, consignes, files, hints, solution, checks, run=None, expected=None):
    files = [files] if isinstance(files, dict) else list(files)
    solution = [solution] if isinstance(solution, dict) else list(solution)
    td = {
        "level": level,
        "title": title,
        "enonce": enonce,
        "consignes": consignes,
        "files": files,
        "hints": hints,
        "solution": solution,
        "checks": checks,
    }
    if run:
        td["run"] = run
    if expected:
        td["expected"] = expected.strip("\n")
    return td


def M(id, track, title, minutes, goal, why, prereq, flow, diagram, lessons, points, pitfalls, recap, example_files, notes, quiz, tds):
    example_files = [example_files] if isinstance(example_files, dict) else list(example_files)
    return {
        "id": id,
        "track": track,
        "title": title,
        "minutes": minutes,
        "goal": goal,
        "why": why,
        "prereq": prereq,
        "flow": flow,
        "diagram": diagram,
        "lessons": lessons,
        "points": points,
        "pitfalls": pitfalls,
        "recap": recap,
        "example": {"files": example_files, "notes": notes},
        "quiz": quiz,
        "tds": tds,
    }


def V2(v1, prereq, diagram, lessons, recap, example=None, notes=None, td1=None, tds=()):
    """Construit un module v2 à partir d'un module v1 (goal, why, flow, points, pitfalls, quiz réutilisés).

    example : F(...) ou [F(...)] pour remplacer l'exemple ; notes : nouvelles notes (sinon celles du v1).
    td1 : dict optionnel {path, run, expected, files, solution} pour enrichir le TD v1 converti en niveau 1.
    tds : TD(2, ...), TD(3, ...) supplémentaires.
    """
    m = {k: v for k, v in v1.items() if k != "td"}
    m["prereq"] = prereq
    m["diagram"] = diagram
    m["lessons"] = lessons
    m["recap"] = recap
    ex_files = example if example is not None else [F("", v1["example"]["lang"], v1["example"]["code"])]
    ex_files = [ex_files] if isinstance(ex_files, dict) else list(ex_files)
    m["example"] = {"files": ex_files, "notes": notes if notes is not None else v1["example"]["notes"]}
    t = v1["td"]
    td1 = td1 or {}
    path = td1.get("path", "")
    files = td1.get("files") or [F(path, t["starter"]["lang"], t["starter"]["code"])]
    solution = td1.get("solution") or [F(path, t["solution"]["lang"], t["solution"]["code"])]
    first = TD(1, td1.get("title", t["title"]), td1.get("enonce", t["enonce"]), td1.get("consignes", t["consignes"]), files,
               td1.get("hints", t["hints"]), solution, td1.get("checks", t["checks"]),
               run=td1.get("run"), expected=td1.get("expected"))
    m["tds"] = [first] + list(tds)
    return m

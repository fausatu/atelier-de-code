"""Règle « expliquer avant d'utiliser ».

Pour chaque module, on cherche les fonctions / méthodes / notions du mémo (methodes.py) utilisées dans son code
(leçons, exemple, TD et leurs solutions) qui n'ont pas été expliquées AVANT :
- ni dans un module précédent du même parcours ou d'un parcours prérequis (DEPS), texte ou encadré ;
- ni dans le texte de ce module placé avant la première utilisation.
Elles vont dans m["croiser"] (liste d'ids du mémo), affichée en haut du module : « Ce que tu vas croiser dans le code ».
`python3 explique.py [parcours|module]` affiche aussi les cas « expliqué APRÈS » (texte qui arrive après le code) à corriger à la main.
"""
import re
from methodes import METHODES, CATS

FAM = {c["id"]: c["lang"] for c in CATS}
DEPS = {"php": [], "doctrine": ["php"], "dto": ["php", "doctrine"], "arch": ["php", "doctrine", "dto"], "ddd": ["php", "doctrine", "dto", "arch"],
        "api": ["php", "doctrine", "dto", "arch"], "ts": [], "react": ["ts"], "data": ["ts", "react"], "forms": ["ts", "react", "data"],
        "next": ["ts", "react", "data", "forms"], "git": [], "terminal": [], "decoupe": [], "orga": ["ts", "react", "data"],
        "debug": ["php", "doctrine", "dto", "arch", "ts", "react", "data", "forms", "next", "git"],
        "fil": ["php", "doctrine", "dto", "arch", "api", "ts", "react", "data", "forms", "orga", "decoupe", "git", "terminal"]}
# Modules à faire après un autre parcours que les prérequis de leur parcours (ex. TypeScript avec React → après React).
MODULE_DEPS = {"ts-react": ["react", "data"], "ts-erreurs": ["react"]}
LANGF = {"php": "php", "ts": "js", "tsx": "js", "js": "js", "jsx": "js", "javascript": "js", "typescript": "js", "mjs": "js"}
MOTS = {"first_class": ["(...)"], "instanceof": ["instanceof"], "nullsafe": ["??", "?->"], "js_spread": ["..."], "async_await": ["await", "async"],
        "use_client": ["use client"], "js_optional": ["?.", "??"], "js_destructuring": ["déstructur"], "js_arrow": ["=>", "fléchée"], "js_template": ["${", "template literal"]}


def kre(k):
    e = re.escape
    if k.startswith("re:"): return re.compile(k[3:], re.M)
    if k.startswith("fn:"): return re.compile(r"(?<!function )(?<![\w$>:.\\])" + e(k[3:]) + r"\s*(?:<[^()]*?>)?\s*\(")
    if k == "->value": return re.compile(r"->value\b")
    if k.startswith("->") or k.startswith("::"): return re.compile(e(k) + r"\s*\(")
    if k.startswith("new:"): return re.compile(r"\bnew\s+\\?" + e(k[4:].lstrip("\\")) + r"\b")
    if k.startswith("#"): return re.compile(r"#\[[^\]]*\b" + e(k[1:]) + r"\b")
    if k.startswith("Assert:"): return re.compile(r"Assert\\" + e(k[7:]) + r"\b")
    if k.startswith("."): return re.compile(e(k) + r"\s*(?:<[^()]*?>)?\s*\(")
    return re.compile(r"(?<![\w$.])" + e(k) + r"\s*(?:<[^()]*?>)?\s*\(")


def _noms(m):
    if m["id"] in MOTS: return MOTS[m["id"]], False
    n = {m["nom"].split("(")[0].split(" / ")[0].strip()}
    for k in m["cles"]:
        n.add(re.sub(r"^(fn:|new:|#|Assert:|->|::|\.)", "", k).lstrip("\\"))
    return [x for x in n if len(x) > 1], True


ENT = []
for _m in METHODES:
    if not _m["cles"]: continue
    _n, _word = _noms(_m)
    if _word:
        pats = [re.compile(r"`[^`\n]*(?<![\w$])" + re.escape(x) + r"(?![\w$])[^`\n]*`") for x in _n]
    else:
        pats = [re.compile(re.escape(x), re.I) for x in _n]
    ENT.append((_m, FAM[_m["cat"]], [kre(k) for k in _m["cles"]], pats))


def _ext(f): return f.get("lang") or f["path"].split(".")[-1]


def segments(mod):
    out = []
    P = lambda t, w: out.append(("prose", t or "", w, None))
    C = lambda t, lang, w: out.append(("code", t or "", w, LANGF.get(lang)))
    P(mod.get("why"), "le problème")
    for x in mod.get("prereq") or []: P("`" + x["term"] + "` " + x["def"], "avant de commencer")
    for f in mod.get("flow") or []: P(f, "comment ça marche")
    for l in mod.get("lessons") or []:
        body, pos = l["body"], 0
        for mm in re.finditer(r"```(\w*)[^\n]*\n([\s\S]*?)```", body):
            P(body[pos:mm.start()], "leçon « %s »" % l["title"]); C(mm.group(2), mm.group(1), "leçon « %s » (code)" % l["title"]); pos = mm.end()
        P(body[pos:], "leçon « %s »" % l["title"])
    for x in (mod.get("points") or []) + (mod.get("pitfalls") or []) + (mod.get("recap") or []): P(x, "l'essentiel")
    ex = mod.get("example") or {}
    for x in ex.get("notes") or []: P(x, "exemple (à remarquer)")  # affichées au-dessus du code
    for f in ex.get("files") or []: C(f["code"], _ext(f), "exemple " + f["path"])
    for t in mod.get("tds") or []:
        P((t.get("enonce") or "") + " " + " ".join(t.get("consignes") or []), "TD " + t["title"])
        for f in t.get("files") or []: C(f["code"], _ext(f), "TD %s : %s" % (t["title"], f["path"]))
        for h in t.get("hints") or []: P(h, "TD indice")
        for f in t.get("solution") or []: C(f["code"], _ext(f), "TD %s (solution)" % t["title"])
    return out


def _mention(text, pats): return any(p.search(text) for p in pats)


def analyse(modules):
    """Remplit m['croiser'] et renvoie la liste des cas « expliqué après » [(module, id, où)]."""
    bytrack, order = {}, []
    for m in modules: bytrack.setdefault(m["track"], []).append(m)
    seen_prose = {}  # module id -> texte expliqué (prose + encadré) ; 2 passes pour les MODULE_DEPS
    for passe in (1, 2):
        apres = []
        _passe(bytrack, seen_prose, apres)
    return apres


def _passe(bytrack, seen_prose, apres):
    done = set()
    def treat(tr):
        if tr in done: return
        done.add(tr)
        for d in DEPS.get(tr, []):
            if d in bytrack: treat(d)
        ms = bytrack.get(tr, [])
        for idx, mod in enumerate(ms):
            deps = DEPS.get(tr, []) + MODULE_DEPS.get(mod["id"], [])
            before = "\n".join(seen_prose.get(x["id"], "") for d in deps for x in bytrack.get(d, [])) + "\n" + "\n".join(seen_prose.get(x["id"], "") for x in ms[:idx])
            S = segments(mod); cro = []
            for e, fam, res, pats in ENT:
                first = next((j for j, (k, t, w, lf) in enumerate(S) if k == "code" and lf == fam and any(r.search(t) for r in res)), None)
                if first is None or _mention(before, pats): continue
                if _mention("\n".join(t for k, t, *_ in S[:first] if k == "prose"), pats): continue
                cro.append((first, e["id"]))
                if any(k == "prose" and _mention(t, pats) for k, t, *_ in S[first:]):
                    apres.append((mod["id"], e["id"], S[first][2]))
            cro.sort()
            mod["croiser"] = [i for _, i in cro]
            byid = {e["id"]: e for e in METHODES}
            seen_prose[mod["id"]] = "\n".join(t for k, t, *_ in S if k == "prose") + "\n" + "\n".join("`%s`" % " ".join(_noms(byid[i])[0]) for i in mod["croiser"])
    for tr in list(bytrack): treat(tr)


if __name__ == "__main__":
    import json, sys
    s = open("index.html", encoding="utf-8").read(); i = s.index("const DATA = ") + 13
    D, _ = json.JSONDecoder().raw_decode(s[i:].replace("<\\/", "</"))
    apres = analyse(D["modules"])
    only = sys.argv[1:]
    for m in D["modules"]:
        if only and m["track"] not in only and m["id"] not in only: continue
        if m["croiser"]: print(m["id"], ":", " ".join(m["croiser"]))
    print("\n--- expliqué APRÈS le code (à réécrire) ---")
    for a in apres:
        if not only or a[0] in only or a[0].split("-")[0] in only: print(" | ".join(a))
    print(len(apres), "cas ;", sum(len(m["croiser"]) for m in D["modules"]), "entrées d'encadré", file=sys.stderr)

"""Vérifie que la solution de chaque TD exécutable passe ses propres tests, dans le vrai moteur de la page."""
import asyncio, json, sys
from playwright.async_api import async_playwright

ONLY = sys.argv[1] if len(sys.argv) > 1 else None

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome")
        pg = await b.new_page(viewport={"width": 1300, "height": 900})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto("http://localhost:8765/index.html")
        await pg.wait_for_timeout(800)
        items = await pg.evaluate("""() => allModules().flatMap(m => tds(m).filter(t => t.run).map(t => ({id: m.id, track: m.track, level: t.level, kind: t.run.kind})))""")
        if ONLY:
            items = [i for i in items if i["track"] == ONLY or i["id"] == ONLY][:999]
        fails = 0
        for it in items:
            key = f"td-{it['id']}-{it['level']}"
            await pg.evaluate("""([id, level, key]) => {
                const m = mod(id); const td = tds(m).find(t => t.level === level);
                const d = {}; for (const f of td.solution) d[f.path] = f.code;
                // les fichiers de départ absents de la solution gardent leur contenu
                for (const f of td.files) if (d[f.path] === undefined) d[f.path] = f.code;
                state.drafts[draftKey(id, level)] = d;
                state.ui.level[id] = level;
                location.hash = '#m-' + id;
            }""", [it["id"], it["level"], key])
            await pg.wait_for_timeout(150)
            await pg.evaluate("([id]) => { state.ui.step[id] = 3; render(); }", [it["id"]])
            await pg.wait_for_timeout(150)
            head = await pg.evaluate("([id, level]) => { const m = mod(id); const td = tds(m).find(t => t.level === level); const ed = document.querySelector('textarea.editor'); return [currentFiles(m, td)[0].code.slice(0, 60), ed && ed.value.slice(0, 60), location.hash, state.ui.step[id]]; }", [it["id"], it["level"]])
            if ONLY == "debug": print(head)
            await pg.evaluate("([id, level]) => runTD(id, level, true)", [it["id"], it["level"]])
            res = None
            for _ in range(200):
                await pg.wait_for_timeout(100)
                res = await pg.evaluate("(key) => { const r = state.ui.runs[key]; return r && !r.busy && (r.tests || r.console) ? {tests: r.tests, console: r.console} : null; }", key)
                if res and (res.get("tests") or (res.get("console") and "Impossible" in res["console"])):
                    break
            t = (res or {}).get("tests")
            if not t or t.get("error") or any(not c["ok"] for c in t["cases"]):
                fails += 1
                print(f"FAIL {it['id']} L{it['level']} ({it['kind']})")
                if res:
                    print("   console:", (res.get("console") or "")[:600].replace("\n", "\n   "))
                if t:
                    print("   error:", t.get("error"))
                    for c in t["cases"]:
                        if not c["ok"]:
                            print("   ✗", c["name"], "|", c.get("detail", ""))
            else:
                print(f"ok   {it['id']} L{it['level']} ({len(t['cases'])} tests)")
        print("page errors:", errs[:5])
        print("FAILS:", fails, "/", len(items))
        await b.close()

asyncio.run(main())

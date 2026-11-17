/* Terminal simulé pour l'Atelier de code : bash (Linux / macOS) et PowerShell (Windows).
 * Un système de fichiers en mémoire, deux interpréteurs (sous-ensembles fidèles : chemins, fichiers, recherche,
 * pipes, redirections, variables d'environnement, scripts, processus et ports, npm), les vrais messages d'erreur
 * (en anglais, comme dans un vrai terminal) avec une explication en français, et un terminal interactif.
 * Ce n'est pas un vrai shell : c'est une maquette pour s'exercer sans risque.
 */
(function () {
  "use strict";

  const HOME_BASH = "/home/ana";
  const HOME_PS = "/c/Users/ana";
  const DATE0 = new Date(2026, 10, 16, 9, 0, 0);

  window.TermSim = function (ctx) {
    const { root, post } = ctx || {};
    let clock = 0;
    const S = {
      mode: "bash", // "bash" | "pwsh"
      fs: dir(), cwd: HOME_BASH, oldpwd: null,
      env: { HOME: HOME_BASH, USER: "ana", SHELL: "/bin/bash", PATH: "/usr/local/bin:/usr/bin:/bin", LANG: "fr_FR.UTF-8" },
      vars: {}, exported: new Set(["HOME", "USER", "SHELL", "PATH", "LANG"]),
      psvars: {}, policy: "Restricted",
      procs: [{ pid: 1, nom: "systemd", cmd: "/sbin/init", user: "root" }, { pid: 812, nom: "sshd", cmd: "/usr/sbin/sshd -D", user: "root" }, { pid: 1204, nom: "bash", cmd: "-bash", user: "ana" }],
      nextPid: 4100, lastCode: 0, clock: 0, args: [],
    };
    const T = []; // transcript : [{cmd, out:[{text, cls}], code, mode, prompt}]
    let cur = null;
    let quiet = false;

    /* ---------- système de fichiers ---------- */
    function dir() { return { type: "dir", children: new Map(), mtime: tick() }; }
    function tick() { return new Date(DATE0.getTime() + (clock++) * 60000); }
    const ci = () => S.mode === "pwsh";
    function child(d, name) {
      if (!d || d.type !== "dir") return null;
      if (d.children.has(name)) return d.children.get(name);
      if (ci()) { const low = name.toLowerCase(); for (const [k, v] of d.children) if (k.toLowerCase() === low) return v; }
      return null;
    }
    function realName(d, name) {
      if (d.children.has(name)) return name;
      if (ci()) { const low = name.toLowerCase(); for (const k of d.children.keys()) if (k.toLowerCase() === low) return k; }
      return name;
    }
    function norm(p) {
      const parts = []; for (const seg of p.split("/")) { if (!seg || seg === ".") continue; if (seg === "..") parts.pop(); else parts.push(seg); }
      return "/" + parts.join("/");
    }
    function home() { return S.mode === "pwsh" ? HOME_PS : HOME_BASH; }
    /* chemin saisi → chemin interne absolu */
    function abs(p) {
      p = String(p == null ? "" : p);
      if (S.mode === "pwsh") {
        p = p.replace(/\\/g, "/");
        if (/^[a-zA-Z]:/.test(p)) p = "/" + p[0].toLowerCase() + p.slice(2);
        else if (p.startsWith("/")) p = "/c" + p;
      }
      if (p === "~" || p.startsWith("~/")) p = home() + p.slice(1);
      if (!p.startsWith("/")) p = S.cwd + "/" + p;
      return norm(p);
    }
    function lookup(path) {
      let n = S.fs; if (path === "/") return n;
      for (const seg of path.slice(1).split("/")) { n = child(n, seg); if (!n) return null; }
      return n;
    }
    function canon(path) { // chemin avec la casse réelle
      let n = S.fs; const out = [];
      for (const seg of path.slice(1).split("/").filter(Boolean)) { const nm = n ? realName(n, seg) : seg; out.push(nm); n = n ? child(n, seg) : null; }
      return "/" + out.join("/");
    }
    function parentOf(path) { const i = path.lastIndexOf("/"); return [i <= 0 ? "/" : path.slice(0, i), path.slice(i + 1)]; }
    function mkdirp(path) {
      let n = S.fs;
      for (const seg of path.slice(1).split("/").filter(Boolean)) {
        let c = child(n, seg);
        if (!c) { c = dir(); n.children.set(seg, c); n.mtime = tick(); }
        if (c.type !== "dir") throw new Error("not a directory");
        n = c;
      }
      return n;
    }
    function writeFile(path, content, append) {
      const [pd, name] = parentOf(path); const d = lookup(pd);
      if (!d || d.type !== "dir") return false;
      const ex = child(d, name);
      if (ex && ex.type === "dir") return "dir";
      if (ex) { ex.content = append ? ex.content + content : content; ex.mtime = tick(); }
      else d.children.set(name, { type: "file", content, mtime: tick(), exec: false });
      return true;
    }
    function removeNode(path) { const [pd, name] = parentOf(path); const d = lookup(pd); if (d) d.children.delete(realName(d, name)); }
    function cloneNode(n) { if (n.type === "file") return { type: "file", content: n.content, mtime: tick(), exec: n.exec }; const d = dir(); for (const [k, v] of n.children) d.children.set(k, cloneNode(v)); return d; }
    function sizeOf(n) { return n.type === "file" ? new TextEncoder().encode(n.content).length : 4096; }
    function walk(path, n, fn, depth) { fn(path, n, depth || 0); if (n.type === "dir") for (const [k, v] of [...n.children].sort((a, b) => a[0].localeCompare(b[0]))) walk(path === "/" ? "/" + k : path + "/" + k, v, fn, (depth || 0) + 1); }
    /* affichage d'un chemin interne */
    function show(path) {
      if (S.mode === "pwsh") { const m = path.match(/^\/([a-z])(\/.*)?$/); return m ? m[1].toUpperCase() + ":" + (m[2] || "\\").replace(/\//g, "\\") : path.replace(/\//g, "\\"); }
      return path;
    }
    function tildify(path) { const h = home(); return path === h ? "~" : path.startsWith(h + "/") ? "~" + path.slice(h.length) : path; }
    function rel(path) { // relatif au dossier courant (pour les sorties de grep, find, Select-String)
      if (path === S.cwd) return ".";
      if (path.startsWith(S.cwd + "/")) return path.slice(S.cwd.length + 1);
      return path;
    }
    function globToRe(g, flags) { return new RegExp("^" + g.replace(/[.+^${}()|\\]/g, "\\$&").replace(/\*/g, ".*").replace(/\?/g, ".") + "$", flags); }
    function glob(pattern) { // motif avec * ou ? → chemins (affichés comme saisis)
      const isAbs = pattern.startsWith("/") || (S.mode === "pwsh" && /^[a-zA-Z]:/.test(pattern)) || pattern.startsWith("~");
      const sep = S.mode === "pwsh" ? /[\\/]/ : /\//;
      const parts = pattern.split(sep);
      let bases = [{ shown: isAbs ? "" : null, path: isAbs ? abs(parts[0] === "" ? "/" : parts[0]) : S.cwd }];
      const start = isAbs ? 1 : 0;
      if (isAbs && parts[0] !== "" && !parts[0].startsWith("~") && !/^[a-zA-Z]:$/.test(parts[0])) bases = [{ shown: parts[0], path: abs(parts[0]) }];
      if (isAbs) bases[0].shown = parts[0];
      const joinS = S.mode === "pwsh" ? "\\" : "/";
      for (let i = start; i < parts.length; i++) {
        const seg = parts[i]; if (seg === "") continue;
        const next = [];
        for (const b of bases) {
          const n = lookup(b.path); if (!n || n.type !== "dir") continue;
          if (/[*?]/.test(seg)) {
            const re = globToRe(seg, ci() ? "i" : "");
            for (const k of [...n.children.keys()].sort()) if (re.test(k) && (seg.startsWith(".") || !k.startsWith("."))) next.push({ shown: b.shown === null ? k : b.shown + joinS + k, path: b.path + (b.path === "/" ? "" : "/") + k });
          } else next.push({ shown: b.shown === null ? seg : b.shown + joinS + seg, path: b.path + (b.path === "/" ? "" : "/") + seg });
        }
        bases = next;
      }
      return bases.filter((b) => lookup(b.path)).map((b) => b.shown);
    }

    /* ---------- sortie ---------- */
    const out = (text, cls) => { if (cur) cur.out.push({ text: String(text), cls: cls || "" }); return ""; };
    const hint = (fr) => out("↳ " + fr, "hint");

    /* ---------- processus, ports, npm, node ---------- */
    const portOwner = (port) => S.procs.find((p) => p.port === Number(port));
    function startServer(cmd, file, label) {
      const f = lookup(abs(file)); const src = f && f.type === "file" ? f.content : "";
      const m = src.match(/listen\(\s*(?:process\.env\.PORT\s*\|\|\s*)?(\d+)/); const port = m ? Number(m[1]) : null;
      if (!port) { const logs = [...src.matchAll(/console\.log\(\s*(['"`])(.*?)\1\s*\)/g)].map((x) => x[2]); for (const l of logs) out(l); return 0; }
      const busy = portOwner(port);
      if (busy) {
        out("node:events:497", "err"); out("      throw er; // Unhandled 'error' event", "err"); out("      ^", "err"); out("", "err");
        out(`Error: listen EADDRINUSE: address already in use :::${port}`, "err");
        out(`    at Server.setupListenHandle [as _listen2] (node:net:1904:16)`, "err");
        hint(`le port ${port} est déjà pris par un autre processus (PID ${busy.pid}). Trouve-le et arrête-le, ou change de port.`);
        return 1;
      }
      const pid = S.nextPid; S.nextPid += 37;
      S.procs.push({ pid, nom: "node", cmd: label || "node " + file, user: "ana", port, response: (src.match(/end\(\s*(['"`])(.*?)\1/) || [])[2] || "OK" });
      out(`Serveur démarré sur http://localhost:${port}`);
      out(`(simulation : le serveur tourne en arrière-plan, PID ${pid})`, "dim");
      return 0;
    }

    /* ---------- serveurs de dev : symfony, php -S, vite (+ proxy) ---------- */
    function fileText(p) { const f = lookup(p); return f && f.type === "file" ? f.content : null; }
    function readEnvFiles(dir) {
      const env = {};
      for (const name of [".env", ".env.local"]) { const t = fileText(norm(dir + "/" + name)); if (t == null) continue; for (const line of t.split("\n")) { const m = line.match(/^\s*([A-Za-z_]\w*)\s*=\s*(.*?)\s*$/); if (m && !line.trim().startsWith("#")) env[m[1]] = m[2].replace(/^["']|["']$/g, ""); } }
      return env;
    }
    function freePort(port) { while (portOwner(port)) port++; return port; }
    function addProc(o) { const pid = S.nextPid; S.nextPid += 37; S.procs.push(Object.assign({ pid, user: "ana" }, o)); return pid; }
    function apiResponse(dir) {
      const env = readEnvFiles(dir);
      return (path) => {
        if (!/^\/api\//.test(path)) return "<!DOCTYPE html><title>Bobine API</title><h1>Bobine API</h1>";
        if (!env.DATABASE_URL || /!ChangeMe!|app:!ChangeMe/.test(env.DATABASE_URL)) return '{"error":"An exception occurred in the driver: SQLSTATE[HY000] [1045] Access denied for user \'app\'"}';
        if (path.startsWith("/api/films")) return '{"items":[{"id":1,"titre":"Big Buck Bunny"},{"id":3,"titre":"Sintel"}],"total":2,"page":1,"pages":1}';
        return '{"error":"No route found for \\"GET ' + path + '\\""}';
      };
    }
    function symfonyCmd(args) {
      const sub = args[0] || "";
      if (sub === "-v" || sub === "version" || sub === "--version") { out("Symfony CLI version 5.10.4"); return 0; }
      const dir = S.cwd;
      const isProject = !!lookup(norm(dir + "/composer.json")) && !!lookup(norm(dir + "/bin/console"));
      if (sub === "server:stop") {
        const before = S.procs.length; S.procs = S.procs.filter((p) => !(p.kind === "symfony" && p.dir === dir));
        out(before === S.procs.length ? " [ERROR] The web server is not running" : " Stopping the web server... [OK]"); return before === S.procs.length ? 1 : 0;
      }
      if (sub === "server:start" || sub === "serve" || sub === "local:server:start") {
        if (!isProject) { out(" [ERROR] Unable to find a Symfony project here (no composer.json / bin/console in " + show(dir) + ")", "err"); hint("place-toi dans le dossier du back (celui qui contient composer.json), par exemple : cd back"); return 1; }
        const mine = S.procs.find((p) => p.kind === "symfony" && p.dir === dir);
        if (mine) { out(` [WARNING] The local web server is already running for this project at port ${mine.port}`); return 0; }
        const pa = args.find((a) => a.startsWith("--port")); let want = pa ? Number(pa.split("=")[1] || args[args.indexOf(pa) + 1]) : 8000;
        const port = pa ? want : freePort(want);
        if (pa && portOwner(port)) { out(` [ERROR] Port ${port} is already in use by another process (PID ${portOwner(port).pid})`, "err"); hint(`le port ${port} est pris : trouve qui l'utilise avec lsof -i :${port}`); return 1; }
        if (port !== want) out(` [WARNING] Port ${want} is already in use, using port ${port} instead`, "warn");
        addProc({ nom: "php", kind: "symfony", dir, cmd: "symfony server:start" + (args.includes("-d") ? " -d" : ""), port, respond: apiResponse(dir) });
        out(""); out(` [OK] Web server listening`); out(`      The Web server is using PHP CLI 8.3.14`); out(""); out(`      http://127.0.0.1:${port}`); out("");
        out(`(simulation : le serveur tourne en arrière-plan${args.includes("-d") ? "" : " ; dans un vrai terminal, sans -d, il occupe la fenêtre jusqu'à Ctrl+C"})`, "dim");
        return 0;
      }
      if (sub === "server:list") { const l = S.procs.filter((p) => p.kind === "symfony"); if (!l.length) out("No local web servers configured."); for (const p of l) out(`${show(p.dir)}  http://127.0.0.1:${p.port}`); return 0; }
      out(`(simulation : « symfony ${args.join(" ")} » n'est pas disponible ; essaie server:start, server:stop, server:list)`, "dim"); return 0;
    }
    function phpCmd(args) {
      if (args[0] === "-v" || args[0] === "--version") { out("PHP 8.3.14 (cli)"); return 0; }
      if (args[0] === "-S") {
        const hp = args[1] || ""; const port = Number((hp.match(/:(\d+)$/) || [])[1]);
        if (!port) { out("Invalid address: " + hp, "err"); hint("la forme attendue est -S localhost:8000"); return 1; }
        const t = args.indexOf("-t"); const docroot = t >= 0 ? norm(abs(args[t + 1] || ".")) : S.cwd;
        if (!lookup(docroot)) { out(`Directory ${args[t + 1]} does not exist.`, "err"); return 1; }
        if (portOwner(port)) { out(`[Mon Nov 16 09:00:00 2026] Failed to listen on ${hp} (reason: Address already in use)`, "err"); hint(`le port ${port} est déjà pris (PID ${portOwner(port).pid}).`); return 1; }
        const proj = docroot.replace(/\/public$/, "");
        addProc({ nom: "php", kind: "php", dir: proj, cmd: "php " + args.join(" "), port, respond: apiResponse(proj) });
        out(`[Mon Nov 16 09:00:00 2026] PHP 8.3.14 Development Server (http://${hp}) started`); return 0;
      }
      if (args[0] === "bin/console") { out("(simulation : bin/console n'est pas exécuté dans l'atelier)", "dim"); return 0; }
      out("(simulation : seul « php -S hôte:port -t dossier » et « php -v » sont disponibles)", "dim"); return 0;
    }
    function viteCmd(args) {
      const dir = S.cwd;
      if (!lookup(norm(dir + "/node_modules"))) { out("sh: 1: vite: not found", "err"); hint("les dépendances ne sont pas installées dans ce dossier : lance npm install d'abord."); return 127; }
      const cfg = fileText(norm(dir + "/vite.config.ts")) || fileText(norm(dir + "/vite.config.js")) || "";
      const pa = args.find((a) => a.startsWith("--port")); const cp = (cfg.match(/port\s*:\s*(\d+)/) || [])[1];
      let port = pa ? Number(pa.split("=")[1] || args[args.indexOf(pa) + 1]) : cp ? Number(cp) : 5173;
      const strict = /strictPort\s*:\s*true/.test(cfg) || args.includes("--strictPort");
      if (portOwner(port)) {
        if (strict) { out(`error when starting dev server:`, "err"); out(`Error: Port ${port} is already in use`, "err"); hint(`strictPort est activé : Vite refuse de changer de port. Libère le port ${port}.`); return 1; }
        while (portOwner(port)) { out(`Port ${port} is in use, trying another one...`); port++; }
      }
      const pm = cfg.match(/['"]\/api['"]\s*:\s*(?:\{[^}]*?target\s*:\s*)?['"]https?:\/\/(?:localhost|127\.0\.0\.1):(\d+)/);
      const env = readEnvFiles(dir); const vite = {}; for (const [k, v] of Object.entries(env)) if (k.startsWith("VITE_")) vite[k] = v;
      addProc({ nom: "node", kind: "vite", dir, cmd: "vite", port, proxy: pm ? Number(pm[1]) : null, viteEnv: vite, respond: () => '<!doctype html><html lang="fr"><head><title>Bobine</title></head><body><div id="root"></div></body></html>' });
      out(""); out("  VITE v5.4.11  ready in 312 ms"); out(""); out(`  ➜  Local:   http://localhost:${port}/`); out("  ➜  Network: use --host to expose"); out("");
      out("(simulation : Vite tourne en arrière-plan ; dans un vrai terminal, il occupe la fenêtre jusqu'à Ctrl+C)", "dim");
      return 0;
    }
    function readPkg() {
      const f = lookup(abs("package.json"));
      if (!f || f.type !== "file") return null;
      try { return JSON.parse(f.content); } catch (e) { return { invalide: true }; }
    }
    function npm(args) {
      const sub = args[0];
      if (!sub) { out("Usage: npm <command>"); return 1; }
      if (sub === "-v" || sub === "--version") { out("10.8.2"); return 0; }
      const pkg = readPkg();
      const noPkg = () => { out(`npm ERR! code ENOENT`, "err"); out(`npm ERR! syscall open`, "err"); out(`npm ERR! path ${show(abs("package.json"))}`, "err"); out(`npm ERR! enoent Could not read package.json: Error: ENOENT: no such file or directory, open '${show(abs("package.json"))}'`, "err"); hint("il n'y a pas de package.json ici : tu n'es probablement pas dans le dossier du projet (vérifie avec pwd / Get-Location)."); return 254; };
      if (sub === "install" || sub === "i" || sub === "ci") {
        if (!pkg) return noPkg();
        const deps = Object.keys(Object.assign({}, pkg.dependencies, pkg.devDependencies));
        mkdirp(abs("node_modules")); for (const d of deps) mkdirp(abs("node_modules/" + d));
        writeFile(abs("package-lock.json"), JSON.stringify({ name: pkg.name, lockfileVersion: 3 }, null, 2));
        out(""); out(`added ${deps.length * 23 + 4} packages, and audited ${deps.length * 23 + 5} packages in 2s`); out(""); out("found 0 vulnerabilities");
        return 0;
      }
      if (sub === "run" || sub === "test" || sub === "start") {
        if (!pkg) return noPkg();
        const name = sub === "run" ? args[1] : sub;
        if (!name) { out(`Scripts available in ${pkg.name || "projet"} via \`npm run-script\`:`); for (const [k, v] of Object.entries(pkg.scripts || {})) { out("  " + k); out("    " + v); } return 0; }
        const script = (pkg.scripts || {})[name];
        if (!script) { out(`npm ERR! Missing script: "${name}"`, "err"); out("npm ERR!", "err"); out("npm ERR! To see a list of scripts, run:", "err"); out("npm ERR!   npm run", "err"); hint(`le script « ${name} » n'existe pas dans package.json (section "scripts").`); return 1; }
        out(""); out(`> ${pkg.name || "projet"}@${pkg.version || "1.0.0"} ${name}`); out(`> ${script}`); out("");
        if (/^node\s+\S+/.test(script)) { if (!lookup(abs("node_modules")) && Object.keys(pkg.dependencies || {}).length) { out(`Error: Cannot find module '${Object.keys(pkg.dependencies)[0]}'`, "err"); hint("les dépendances ne sont pas installées : lance npm install d'abord."); return 1; } return startServer(script, script.split(/\s+/)[1], script); }
        return runLine(script, "bash-sub");
      }
      out(`Unknown command: "${sub}"`, "err"); return 1;
    }

    /* ======================================================================
     *  BASH
     * ====================================================================== */
    const BASH_HELP = {
      "No such file or directory": "ce fichier ou ce dossier n'existe pas (vérifie le chemin, les majuscules, et où tu es avec pwd).",
      "command not found": "cette commande n'existe pas ici : faute de frappe, programme non installé, ou dossier absent du PATH.",
      "Is a directory": "c'est un dossier, pas un fichier.",
      "Not a directory": "un élément du chemin est un fichier, pas un dossier.",
      "Permission denied": "le fichier n'a pas le droit d'exécution : chmod +x fichier, ou lance-le avec bash fichier.",
      "Directory not empty": "le dossier n'est pas vide : rm -r pour le supprimer avec son contenu.",
      "File exists": "ce nom existe déjà.",
    };
    function berr(msg) { out(msg, "err"); for (const [k, v] of Object.entries(BASH_HELP)) if (msg.includes(k)) { hint(v); break; } }

    /* --- lexer : mots (avec morceaux citations) et opérateurs --- */
    function lexBash(src) {
      const toks = []; let i = 0; let word = null;
      const pushPart = (q, s) => { if (!word) word = { parts: [] }; word.parts.push({ q, s }); };
      const endWord = () => { if (word) { toks.push({ w: word }); word = null; } };
      while (i < src.length) {
        const c = src[i];
        if (c === "\n") { endWord(); toks.push({ op: ";" }); i++; continue; }
        if (c === " " || c === "\t") { endWord(); i++; continue; }
        if (c === "#" && !word) { while (i < src.length && src[i] !== "\n") i++; continue; }
        if (c === "\\" && i + 1 < src.length) { if (src[i + 1] === "\n") { i += 2; continue; } pushPart("'", src[i + 1]); i += 2; continue; }
        if (c === "'") { const j = src.indexOf("'", i + 1); const e = j < 0 ? src.length : j; pushPart("'", src.slice(i + 1, e)); i = e + 1; continue; }
        if (c === '"') {
          let j = i + 1, s = "";
          while (j < src.length && src[j] !== '"') {
            if (src[j] === "\\" && j + 1 < src.length && '"\\$`'.includes(src[j + 1])) { s += "\u0000" + src[j + 1]; j += 2; continue; }
            if (src[j] === "$" && src[j + 1] === "(") { const e = matchParen(src, j + 1); s += src.slice(j, e + 1); j = e + 1; continue; }
            s += src[j++];
          }
          pushPart('"', s); i = j + 1; continue;
        }
        if (c === "$" && src[i + 1] === "(") { const e = matchParen(src, i + 1); pushPart("", src.slice(i, e + 1)); i = e + 1; continue; }
        const two = src.slice(i, i + 2), three = src.slice(i, i + 4);
        if (three === "2>&1") { endWord(); toks.push({ op: "2>&1" }); i += 4; continue; }
        if (["&&", "||", ">>", "2>", "&>"].includes(two)) { endWord(); if (two === "2>" && src[i + 2] === ">") { toks.push({ op: "2>>" }); i += 3; } else { toks.push({ op: two }); i += 2; } continue; }
        if ("|;&><".includes(c)) { endWord(); toks.push({ op: c }); i++; continue; }
        let j = i; while (j < src.length && !" \t\n'\"|;&><\\".includes(src[j]) && !(src[j] === "$" && src[j + 1] === "(")) j++;
        if (j === i) { pushPart("", c); i++; continue; }
        pushPart("", src.slice(i, j)); i = j;
      }
      endWord(); return toks;
    }
    function matchParen(s, i) { let d = 0; for (let j = i; j < s.length; j++) { if (s[j] === "(") d++; else if (s[j] === ")") { d--; if (!d) return j; } else if (s[j] === "'") { const k = s.indexOf("'", j + 1); if (k > 0) j = k; } } return s.length - 1; }
    function varVal(name, scope) {
      if (/^\d$/.test(name)) return name === "0" ? "bash" : (scope.args[Number(name) - 1] ?? "");
      if (name === "#") return String(scope.args.length);
      if (name === "@" || name === "*") return scope.args.join(" ");
      if (name === "?") return String(S.lastCode);
      if (name === "PWD") return S.cwd;
      if (name === "OLDPWD") return S.oldpwd || "";
      if (name in S.vars) return S.vars[name];
      return S.env[name] ?? "";
    }
    function expandStr(s, scope) {
      s = s.replace(/\$\(([\s\S]*)\)/g, (m, inner) => capture(inner, scope).replace(/\n+$/, ""));
      s = s.replace(/\$\{(\w+):-([^}]*)\}/g, (m, n, d) => varVal(n, scope) || d);
      s = s.replace(/\$\{(\w+|[#@?*])\}/g, (m, n) => varVal(n, scope));
      s = s.replace(/\$(\w+|[#@?*])/g, (m, n) => varVal(n, scope));
      return s.replace(/\u0000/g, "");
    }
    function braces(s) {
      const m = s.match(/^(.*?)\{([^{}]*,[^{}]*)\}(.*)$/); if (!m) return [s];
      return m[2].split(",").flatMap((x) => braces(m[1] + x + m[3]));
    }
    function expandWord(w, scope) {
      let text = "", globbable = false, tilde = false;
      w.parts.forEach((p, k) => {
        if (p.q === "'") text += p.s.replace(/[*?]/g, (c) => "\u0001" + c);
        else if (p.q === '"') text += expandStr(p.s, scope).replace(/[*?]/g, (c) => "\u0001" + c);
        else { let s = p.s; if (k === 0 && (s === "~" || s.startsWith("~/"))) tilde = true; if (/[*?]/.test(s)) globbable = true; text += expandStr(s, scope); }
      });
      if (tilde) text = home() + text.slice(1);
      let words = w.parts.length === 1 && w.parts[0].q === "" ? braces(text) : [text];
      if (globbable) words = words.flatMap((t) => { const pat = t.replace(/\u0001[*?]/g, (x) => "\\" + x[1]); if (!/(^|[^\\])[*?]/.test(pat)) return [t]; const g = glob(t.replace(/\u0001/g, "")); return g.length ? g : [t]; });
      return words.map((t) => t.replace(/\u0001/g, ""));
    }
    /* --- découpage en listes / pipelines / commandes --- */
    function parseList(toks) {
      const list = []; let pipeline = [], cmd = { words: [], redir: [] }, conn = null;
      const endCmd = () => { if (cmd.words.length || cmd.redir.length) pipeline.push(cmd); cmd = { words: [], redir: [] }; };
      const endPipe = (op) => { endCmd(); if (pipeline.length) list.push({ pipeline, conn }); pipeline = []; conn = op; };
      for (let i = 0; i < toks.length; i++) {
        const t = toks[i];
        if (t.w) { cmd.words.push(t.w); continue; }
        if (t.op === "|") { endCmd(); continue; }
        if ([">", ">>", "2>", "2>>", "&>", "<"].includes(t.op)) { const nx = toks[i + 1]; if (nx && nx.w) { cmd.redir.push({ op: t.op, w: nx.w }); i++; } continue; }
        if (t.op === "2>&1") { cmd.redir.push({ op: "2>&1" }); continue; }
        if (t.op === "&&" || t.op === "||") { endPipe(t.op); continue; }
        if (t.op === ";" || t.op === "&") { endPipe(null); continue; }
      }
      endPipe(null); return list;
    }
    /* --- blocs for / if (sur une ou plusieurs lignes) --- */
    function splitStatements(src) {
      const lines = src.replace(/\r/g, "").split("\n");
      const st = []; let buf = [], depth = 0;
      for (const raw of lines) {
        const l = raw.trim();
        if (!buf.length && (!l || l.startsWith("#"))) continue;
        buf.push(raw);
        const words = l.replace(/'[^']*'|"[^"]*"/g, "x").split(/[\s;]+/);
        for (const w of words) { if (w === "for" || w === "if" || w === "while") depth++; if (w === "done" || w === "fi") depth--; }
        if (depth <= 0 && !/\\$/.test(l)) { st.push(buf.join("\n")); buf = []; depth = 0; }
      }
      if (buf.length) st.push(buf.join("\n"));
      return st;
    }
    function execBlock(src, scope) {
      const s = src.trim();
      let m = s.match(/^for\s+(\w+)\s+in\s+([\s\S]*?)\s*(?:;|\n)\s*do\s+([\s\S]*?)(?:;|\n)?\s*done\s*$/);
      if (m) {
        const items = parseList(lexBash(m[2]))[0]; const vals = items ? items.pipeline[0].words.flatMap((w) => expandWord(w, scope)) : [];
        let code = 0; for (const v of vals) { S.vars[m[1]] = v; code = execSource(m[3].replace(/;\s*$/, ""), scope); }
        return code;
      }
      m = s.match(/^if\s+([\s\S]*?)\s*(?:;|\n)\s*then\s+([\s\S]*?)(?:(?:;|\n)\s*else\s+([\s\S]*?))?(?:;|\n)?\s*fi\s*$/);
      if (m) { const c = execSource(m[1], scope, true); return c === 0 ? execSource(m[2], scope) : m[3] ? execSource(m[3], scope) : 0; }
      return null;
    }
    function execSource(src, scope, silentCond) {
      let code = 0;
      for (const st of splitStatements(src)) {
        const b = /^\s*(for|if)\s/.test(st) ? execBlock(st, scope) : null;
        code = b !== null ? b : execList(parseList(lexBash(st)), scope);
      }
      return code;
    }
    function execList(list, scope) {
      let code = 0;
      for (const item of list) {
        if (item.conn === "&&" && code !== 0) continue;
        if (item.conn === "||" && code === 0) continue;
        code = execPipeline(item.pipeline, scope);
        S.lastCode = code;
      }
      return code;
    }
    function capture(src, scope) {
      const saved = cur; const tmp = { out: [] }; cur = tmp;
      try { execSource(src, scope); } finally { cur = saved; }
      return tmp.out.filter((o) => o.cls !== "err" && o.cls !== "hint" && o.cls !== "dim").map((o) => o.text).join("\n");
    }
    function execPipeline(pipeline, scope) {
      let input = null, code = 0;
      for (let k = 0; k < pipeline.length; k++) {
        const c = pipeline[k]; const last = k === pipeline.length - 1;
        const saved = cur; const buf = { out: [] }; cur = buf;
        try { code = execCommand(c, input, scope); } catch (e) { out(String(e.message || e), "err"); code = 1; }
        cur = saved;
        // redirections (on garde l'ordre d'origine des lignes)
        let stdout = buf.out.filter((o) => o.cls !== "err" && o.cls !== "hint");
        let stderr = buf.out.filter((o) => o.cls === "err" || o.cls === "hint");
        let ordered = true;
        for (const r of c.redir) {
          if (r.op === "<") continue;
          if (r.op === "2>&1") { stdout = stdout.concat(stderr.filter((o) => o.cls === "err")); stderr = []; continue; }
          const target = expandWord(r.w, scope)[0];
          if (target === "/dev/null") { if (r.op.startsWith("2")) stderr = []; else if (r.op === "&>") { stdout = []; stderr = []; } else stdout = []; continue; }
          const data = (r.op === "&>" ? stdout.concat(stderr.filter((o) => o.cls === "err")) : r.op.startsWith("2") ? stderr.filter((o) => o.cls === "err") : stdout).map((o) => o.text).join("\n");
          const res = writeFile(abs(target), data ? data + "\n" : "", r.op.endsWith(">>"));
          if (res === false) { stderr.push({ text: `bash: ${target}: No such file or directory`, cls: "err" }); code = 1; }
          else if (res === "dir") { stderr.push({ text: `bash: ${target}: Is a directory`, cls: "err" }); code = 1; }
          if (r.op === "&>") stderr = []; else if (r.op.startsWith("2")) stderr = []; else stdout = [];
          ordered = false;
        }
        if (last && ordered && c.redir.every((r) => r.op === "<")) { for (const o of buf.out) if (cur) cur.out.push(o); continue; }
        for (const e of stderr) if (cur) cur.out.push(e);
        if (last) { for (const o of stdout) if (cur) cur.out.push(o); }
        else input = stdout.map((o) => o.text).join("\n");
      }
      return code;
    }
    function execCommand(c, input, scope) {
      // assignations NOM=valeur
      const words = c.words.slice();
      const assigns = [];
      while (words.length && words[0].parts.length && words[0].parts[0].q === "" && /^[A-Za-z_]\w*=/.test(words[0].parts[0].s)) {
        const w = words.shift(); const first = w.parts[0].s; const eq = first.indexOf("=");
        const name = first.slice(0, eq); const val = expandWord({ parts: [{ q: "", s: first.slice(eq + 1) }].concat(w.parts.slice(1)) }, scope).join(" ");
        assigns.push([name, val]);
      }
      if (!words.length) { for (const [n, v] of assigns) { if (S.exported.has(n)) S.env[n] = v; else S.vars[n] = v; } return 0; }
      const argv = words.flatMap((w) => expandWord(w, scope));
      for (const r of c.redir) if (r.op === "<") { const f = lookup(abs(expandWord(r.w, scope)[0])); if (!f || f.type !== "file") { berr(`bash: ${expandWord(r.w, scope)[0]}: No such file or directory`); return 1; } input = f.content; }
      const name = argv[0]; const args = argv.slice(1);
      const savedEnv = {}; for (const [n, v] of assigns) { savedEnv[n] = S.env[n]; S.env[n] = v; }
      try {
        if (BASH[name]) return BASH[name](args, input, scope) || 0;
        if (name.includes("/")) return runFile(name, args, scope);
        const found = which(name);
        if (found) return runFile(found, args, scope);
        berr(`bash: ${name}: command not found`); return 127;
      } finally { for (const [n] of assigns) { if (savedEnv[n] === undefined) delete S.env[n]; else S.env[n] = savedEnv[n]; } }
    }
    function which(name) {
      for (const d of (S.env.PATH || "").split(":")) { if (!d) continue; const p = norm(d + "/" + name); const n = lookup(p); if (n && n.type === "file" && n.exec) return p; }
      return null;
    }
    function runFile(name, args, scope, viaShell) {
      const p = abs(name); const n = lookup(p);
      if (!n) { berr(`bash: ${name}: No such file or directory`); return 127; }
      if (n.type === "dir") { berr(`bash: ${name}: Is a directory`); return 126; }
      if (!n.exec && !viaShell) { berr(`bash: ${name}: Permission denied`); return 126; }
      if (/\.js$/.test(p) || /^#!.*node/.test(n.content)) return startServer("node " + name, name);
      // un script s'exécute dans un sous-shell : variables non exportées et cd ne remontent pas
      const savedCwd = S.cwd, savedVars = S.vars, savedEnv = Object.assign({}, S.env);
      S.vars = {};
      let code;
      try { code = execSource(n.content.replace(/^#!.*\n/, ""), { args }); }
      finally { S.cwd = savedCwd; S.vars = savedVars; S.env = savedEnv; }
      return code;
    }
    const flagsOf = (args) => { const f = new Set(); const rest = []; let stop = false; for (const a of args) { if (!stop && a === "--") { stop = true; continue; } if (!stop && /^-[a-zA-Z]+$/.test(a)) for (const ch of a.slice(1)) f.add(ch); else if (!stop && /^--[\w-]+$/.test(a)) f.add(a); else rest.push(a); } return [f, rest]; };
    const textOf = (input, files, cmdName) => {
      if (!files.length) return [input == null ? "" : input];
      return files.map((f) => { const n = lookup(abs(f)); if (!n) { berr(`${cmdName}: ${f}: No such file or directory`); return null; } if (n.type === "dir") { berr(`${cmdName}: ${f}: Is a directory`); return null; } return n.content; }).filter((x) => x !== null);
    };
    const linesOf = (txt) => { const l = txt.split("\n"); if (l.length && l[l.length - 1] === "") l.pop(); return l; };
    function lsLong(name, n) {
      const mode = (n.type === "dir" ? "d" : "-") + "rw" + (n.type === "dir" || n.exec ? "x" : "-") + "r-" + (n.type === "dir" || n.exec ? "x" : "-") + "r-" + (n.type === "dir" || n.exec ? "x" : "-");
      const d = n.mtime || DATE0; const mois = ["janv.", "févr.", "mars", "avril", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."][d.getMonth()];
      return `${mode} 1 ana ana ${String(sizeOf(n)).padStart(5)} ${String(d.getDate()).padStart(2)} ${mois.padEnd(5)} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")} ${name}`;
    }
    const BASH = {
      pwd() { out(S.cwd); return 0; },
      cd(args) {
        let t = args[0];
        if (!t || t === "~") t = home(); else if (t === "-") { if (!S.oldpwd) { berr("bash: cd: OLDPWD not set"); return 1; } t = S.oldpwd; out(t); }
        const p = abs(t); const n = lookup(p);
        if (!n) { berr(`bash: cd: ${args[0]}: No such file or directory`); return 1; }
        if (n.type !== "dir") { berr(`bash: cd: ${args[0]}: Not a directory`); return 1; }
        S.oldpwd = S.cwd; S.cwd = canon(p); return 0;
      },
      ls(args) {
        const [f, rest] = flagsOf(args); const all = f.has("a") || f.has("A"); const long = f.has("l"); const rec = f.has("R");
        const targets = rest.length ? rest : ["."]; let code = 0;
        const files = targets.filter((t) => { const n = lookup(abs(t)); return n && n.type === "file"; });
        const dirs = targets.filter((t) => { const n = lookup(abs(t)); if (!n) { berr(`ls: cannot access '${t}': No such file or directory`); code = 2; return false; } return n.type === "dir"; });
        for (const t of files) { const n = lookup(abs(t)); if (long) out(lsLong(t, n)); else out(t); }
        const listDir = (t, label) => {
          const n = lookup(abs(t)); if (label) out(t + ":");
          let names = [...n.children.keys()].sort((a, b) => a.replace(/^\./, "").localeCompare(b.replace(/^\./, "")));
          if (!all) names = names.filter((x) => !x.startsWith("."));
          if (f.has("a")) names = [".", ".."].concat(names);
          if (long) { out("total " + names.length * 4); for (const nm of names) { const c = nm === "." ? n : nm === ".." ? (lookup(parentOf(abs(t))[0]) || n) : n.children.get(nm); out(lsLong(nm, c), c.type === "dir" ? "dir" : c.exec ? "exe" : ""); } }
          else if (names.length) { for (const nm of names) { const c = nm === "." || nm === ".." ? n : n.children.get(nm); out(nm, c.type === "dir" ? "dir" : c.exec ? "exe" : ""); } }
          if (rec) for (const nm of names.filter((x) => x !== "." && x !== ".." && n.children.get(x).type === "dir")) { out(""); listDir((t === "." ? "." : t) + "/" + nm, true); }
        };
        dirs.forEach((t, i) => { if (i || files.length) out(""); listDir(t, dirs.length + files.length > 1 || rec); });
        return code;
      },
      mkdir(args) {
        const [f, rest] = flagsOf(args); let code = 0;
        if (!rest.length) { berr("mkdir: missing operand"); return 1; }
        for (const t of rest) {
          const p = abs(t); if (lookup(p)) { if (!f.has("p")) { berr(`mkdir: cannot create directory '${t}': File exists`); code = 1; } continue; }
          if (f.has("p")) { try { mkdirp(p); } catch (e) { berr(`mkdir: cannot create directory '${t}': Not a directory`); code = 1; } continue; }
          const [pd, name] = parentOf(p); const d = lookup(pd);
          if (!d || d.type !== "dir") { berr(`mkdir: cannot create directory '${t}': No such file or directory`); hint("le dossier parent n'existe pas : ajoute -p pour créer tout le chemin."); code = 1; continue; }
          d.children.set(name, dir());
        }
        return code;
      },
      rmdir(args) { let code = 0; for (const t of args) { const n = lookup(abs(t)); if (!n) { berr(`rmdir: failed to remove '${t}': No such file or directory`); code = 1; } else if (n.type !== "dir") { berr(`rmdir: failed to remove '${t}': Not a directory`); code = 1; } else if (n.children.size) { berr(`rmdir: failed to remove '${t}': Directory not empty`); code = 1; } else removeNode(abs(t)); } return code; },
      touch(args) { let code = 0; for (const t of args) { const p = abs(t); const n = lookup(p); if (n) { n.mtime = tick(); continue; } if (!writeFile(p, "")) { berr(`touch: cannot touch '${t}': No such file or directory`); code = 1; } } return code; },
      cat(args, input) { const [f, rest] = flagsOf(args); const txts = textOf(input, rest, "cat"); let n = 1; for (const t of txts) for (const l of linesOf(t)) out(f.has("n") ? String(n++).padStart(6) + "\t" + l : l); return txts.length === Math.max(rest.length, 1) ? 0 : 1; },
      echo(args) {
        let nl = true, e = false; while (args[0] === "-n" || args[0] === "-e") { if (args[0] === "-n") nl = false; else e = true; args = args.slice(1); }
        let s = args.join(" "); if (e) s = s.replace(/\\n/g, "\n").replace(/\\t/g, "\t");
        for (const l of s.split("\n")) out(l); if (!nl && cur && cur.out.length) cur.out[cur.out.length - 1].nonl = true; return 0;
      },
      printf(args) { let s = (args[0] || "").replace(/%s/g, () => args.splice(1, 1)[0] ?? "").replace(/\\n/g, "\n").replace(/\\t/g, "\t"); const ls = s.split("\n"); if (ls[ls.length - 1] === "") ls.pop(); for (const l of ls) out(l); return 0; },
      cp(args) {
        const [f, rest] = flagsOf(args); if (rest.length < 2) { berr("cp: missing destination file operand"); return 1; }
        const dest = rest.pop(); const dp = abs(dest); const dn = lookup(dp); let code = 0;
        if (rest.length > 1 && (!dn || dn.type !== "dir")) { berr(`cp: target '${dest}' is not a directory`); return 1; }
        for (const s of rest) {
          const sn = lookup(abs(s)); if (!sn) { berr(`cp: cannot stat '${s}': No such file or directory`); code = 1; continue; }
          if (sn.type === "dir" && !f.has("r") && !f.has("R")) { berr(`cp: -r not specified; omitting directory '${s}'`); hint("pour copier un dossier et son contenu : cp -r."); code = 1; continue; }
          const target = dn && dn.type === "dir" ? dp + "/" + parentOf(abs(s))[1] : dp;
          const [pd, nm] = parentOf(target); const pdn = lookup(pd); if (!pdn) { berr(`cp: cannot create regular file '${dest}': No such file or directory`); code = 1; continue; }
          pdn.children.set(nm, cloneNode(sn));
        }
        return code;
      },
      mv(args) {
        const [, rest] = flagsOf(args); if (rest.length < 2) { berr("mv: missing destination file operand"); return 1; }
        const dest = rest.pop(); const dp = abs(dest); const dn = lookup(dp); let code = 0;
        if (rest.length > 1 && (!dn || dn.type !== "dir")) { berr(`mv: target '${dest}' is not a directory`); return 1; }
        for (const s of rest) {
          const sp = abs(s); const sn = lookup(sp); if (!sn) { berr(`mv: cannot stat '${s}': No such file or directory`); code = 1; continue; }
          const target = dn && dn.type === "dir" ? dp + "/" + parentOf(sp)[1] : dp;
          const [pd, nm] = parentOf(target); const pdn = lookup(pd); if (!pdn) { berr(`mv: cannot move '${s}' to '${dest}': No such file or directory`); code = 1; continue; }
          removeNode(sp); sn.mtime = tick(); pdn.children.set(nm, sn);
        }
        return code;
      },
      rm(args) {
        const [f, rest] = flagsOf(args); let code = 0; const r = f.has("r") || f.has("R"), force = f.has("f");
        if (!rest.length && !force) { berr("rm: missing operand"); return 1; }
        for (const t of rest) {
          const p = abs(t); const n = lookup(p);
          if (!n) { if (!force) { berr(`rm: cannot remove '${t}': No such file or directory`); code = 1; } continue; }
          if (n.type === "dir" && !r) { berr(`rm: cannot remove '${t}': Is a directory`); hint("pour supprimer un dossier et tout son contenu : rm -r (sans corbeille, attention)."); code = 1; continue; }
          if (p === home() || p === "/") { berr(`rm: refusing to remove '${t}'`); code = 1; continue; }
          removeNode(p);
        }
        return code;
      },
      head(args, input) { let n = 10; const a = args.slice(); const i = a.findIndex((x) => x === "-n"); if (i >= 0) { n = Number(a[i + 1]); a.splice(i, 2); } else { const j = a.findIndex((x) => /^-\d+$/.test(x)); if (j >= 0) { n = Number(a[j].slice(1)); a.splice(j, 1); } } for (const t of textOf(input, a, "head")) for (const l of linesOf(t).slice(0, n)) out(l); return 0; },
      tail(args, input) { let n = 10; const a = args.slice(); const i = a.findIndex((x) => x === "-n"); if (i >= 0) { n = Number(a[i + 1]); a.splice(i, 2); } else { const j = a.findIndex((x) => /^-\d+$/.test(x)); if (j >= 0) { n = Number(a[j].slice(1)); a.splice(j, 1); } } for (const t of textOf(input, a, "tail")) for (const l of linesOf(t).slice(-n)) out(l); return 0; },
      wc(args, input) {
        const [f, rest] = flagsOf(args); const txts = textOf(input, rest, "wc"); const res = [];
        const one = (t, nm) => { const l = (t.match(/\n/g) || []).length + (t && !t.endsWith("\n") ? 1 : 0); const w = (t.match(/\S+/g) || []).length; const c = new TextEncoder().encode(t).length; const parts = f.size ? [f.has("l") && l, f.has("w") && w, f.has("c") && c].filter((x) => x !== false) : [l, w, c]; res.push(parts.map((x) => String(x).padStart(f.size === 1 ? 1 : 7)).join(" ") + (nm ? " " + nm : "")); };
        if (!rest.length) one(input == null ? "" : input + (input && !input.endsWith("\n") ? "\n" : ""), ""); else txts.forEach((t, k) => one(t, rest[k]));
        for (const r of res) out(r.trim() === r ? r : r.replace(/^\s+/, f.size === 1 ? "" : r.match(/^\s*/)[0])); return 0;
      },
      grep(args, input) {
        const a = args.slice(); const f = new Set(); const files = []; let pat = null; let stop = false;
        while (a.length) { const x = a.shift(); if (!stop && x === "--") { stop = true; continue; } if (!stop && x === "-e") { pat = a.shift(); continue; } if (!stop && /^-[a-zA-Z]+$/.test(x)) { for (const ch of x.slice(1)) f.add(ch); continue; } if (!stop && x.startsWith("--include=")) { f.add("inc:" + x.slice(10)); continue; } if (pat === null) pat = x; else files.push(x); }
        if (pat === null) { berr("Usage: grep [OPTION]... PATTERNS [FILE]..."); return 2; }
        let re; try { re = new RegExp(f.has("F") ? pat.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") : pat.replace(/\\\|/g, "|").replace(/\\\(/g, "(").replace(/\\\)/g, ")"), f.has("i") ? "i" : ""); } catch (e) { berr(`grep: Invalid regular expression`); return 2; }
        const inc = [...f].find((x) => x.startsWith("inc:")); const incRe = inc ? globToRe(inc.slice(4)) : null;
        const sources = [];
        if (!files.length) sources.push({ name: null, text: input == null ? "" : input });
        for (const t of files) {
          const p = abs(t); const n = lookup(p);
          if (!n) { berr(`grep: ${t}: No such file or directory`); continue; }
          if (n.type === "dir") { if (!f.has("r") && !f.has("R")) { berr(`grep: ${t}: Is a directory`); continue; } walk(p, n, (wp, wn) => { if (wn.type === "file" && (!incRe || incRe.test(parentOf(wp)[1]))) sources.push({ name: (t === "." ? "" : t.replace(/\/$/, "") + "/") + wp.slice(p.length + 1), text: wn.content }); }); }
          else sources.push({ name: t, text: n.content });
        }
        const showName = sources.length > 1 || f.has("r") || f.has("R"); let total = 0;
        for (const s of sources) {
          let count = 0; const ls = linesOf(s.text);
          ls.forEach((l, i) => { const hit = re.test(l) !== f.has("v"); if (!hit) return; count++; total++; if (f.has("c") || f.has("l")) return; out((showName && s.name ? s.name + ":" : "") + (f.has("n") ? (i + 1) + ":" : "") + l); });
          if (f.has("c")) out((showName && s.name ? s.name + ":" : "") + count);
          if (f.has("l") && count) out(s.name);
        }
        return total ? 0 : 1;
      },
      find(args) {
        const a = args.slice(); const starts = []; while (a.length && !a[0].startsWith("-")) starts.push(a.shift()); if (!starts.length) starts.push(".");
        let name = null, iname = null, type = null, maxd = Infinity;
        while (a.length) { const x = a.shift(); if (x === "-name") name = a.shift(); else if (x === "-iname") iname = a.shift(); else if (x === "-type") type = a.shift(); else if (x === "-maxdepth") maxd = Number(a.shift()); }
        let code = 0;
        for (const s of starts) {
          const p = abs(s); const n = lookup(p); if (!n) { berr(`find: '${s}': No such file or directory`); code = 1; continue; }
          walk(p, n, (wp, wn, depth) => {
            if (depth > maxd) return;
            const nm = depth === 0 ? s : parentOf(wp)[1];
            if (type && ((type === "f") !== (wn.type === "file"))) return;
            if (name && !globToRe(name).test(depth === 0 ? parentOf(p)[1] : nm)) return;
            if (iname && !globToRe(iname, "i").test(depth === 0 ? parentOf(p)[1] : nm)) return;
            out(depth === 0 ? s : (s === "/" ? "" : s.replace(/\/$/, "")) + "/" + wp.slice(p.length + (p === "/" ? 0 : 1)));
          });
        }
        return code;
      },
      sort(args, input) { const [f, rest] = flagsOf(args); let ls = []; for (const t of textOf(input, rest, "sort")) ls = ls.concat(linesOf(t)); ls.sort(f.has("n") ? (x, y) => parseFloat(x) - parseFloat(y) || x.localeCompare(y) : (x, y) => (x < y ? -1 : x > y ? 1 : 0)); if (f.has("r")) ls.reverse(); if (f.has("u")) ls = [...new Set(ls)]; for (const l of ls) out(l); return 0; },
      uniq(args, input) { const [f, rest] = flagsOf(args); const ls = linesOf(textOf(input, rest, "uniq")[0] || ""); const res = []; for (const l of ls) { if (res.length && res[res.length - 1].l === l) res[res.length - 1].n++; else res.push({ l, n: 1 }); } for (const r of res) out(f.has("c") ? String(r.n).padStart(7) + " " + r.l : r.l); return 0; },
      cut(args, input) { let d = "\t", fl = null; const a = args.slice(); const files = []; while (a.length) { const x = a.shift(); if (x === "-d") d = a.shift(); else if (x.startsWith("-d")) d = x.slice(2); else if (x === "-f") fl = a.shift(); else if (x.startsWith("-f")) fl = x.slice(2); else files.push(x); } const idx = (fl || "1").split(",").map(Number); for (const t of textOf(input, files, "cut")) for (const l of linesOf(t)) { const ps = l.split(d); out(idx.map((i) => ps[i - 1] ?? "").filter((x, k) => x !== "" || k === 0).join(d)); } return 0; },
      tr(args, input) { const [a, b] = args; let s = input || ""; if (a && b) { const A = a.replace(/a-z/, "abcdefghijklmnopqrstuvwxyz").replace(/A-Z/, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"), B = b.replace(/a-z/, "abcdefghijklmnopqrstuvwxyz").replace(/A-Z/, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"); s = [...s].map((c) => { const i = A.indexOf(c); return i >= 0 ? B[Math.min(i, B.length - 1)] : c; }).join(""); } for (const l of linesOf(s)) out(l); return 0; },
      chmod(args) { const [mode, ...files] = args; let code = 0; for (const t of files) { const n = lookup(abs(t)); if (!n) { berr(`chmod: cannot access '${t}': No such file or directory`); code = 1; continue; } if (/\+x|7\d\d|5\d\d/.test(mode)) n.exec = true; if (/-x|6\d\d|4\d\d/.test(mode)) n.exec = false; } return code; },
      export(args) { if (!args.length) { for (const k of Object.keys(S.env).sort()) out(`declare -x ${k}="${S.env[k]}"`); return 0; } for (const a of args) { const i = a.indexOf("="); if (i < 0) { S.exported.add(a); if (a in S.vars) { S.env[a] = S.vars[a]; delete S.vars[a]; } } else { const k = a.slice(0, i); S.exported.add(k); S.env[k] = a.slice(i + 1); delete S.vars[k]; } } return 0; },
      unset(args) { for (const a of args) { delete S.vars[a]; delete S.env[a]; S.exported.delete(a); } return 0; },
      env() { for (const k of Object.keys(S.env).sort()) out(k + "=" + S.env[k]); return 0; },
      printenv(args) { if (!args.length) return BASH.env(); const v = S.env[args[0]]; if (v === undefined) return 1; out(v); return 0; },
      which(args) { let code = 0; for (const a of args) { if (BASH[a] && ["cd", "export", "unset", "source", "."].includes(a)) { out(`${a}: shell built-in command`); continue; } const w = which(a) || (["ls", "cat", "grep", "find", "mkdir", "rm", "cp", "mv", "touch", "head", "tail", "wc", "sort", "uniq", "cut", "chmod", "echo", "pwd"].includes(a) ? "/usr/bin/" + a : ["node", "npm", "git", "curl", "php"].includes(a) ? "/usr/bin/" + a : null); if (w) out(w); else code = 1; } return code; },
      type(args) { for (const a of args) { if (BASH[a]) out(`${a} is ${["cd", "export", "echo", "pwd", "source"].includes(a) ? "a shell builtin" : "/usr/bin/" + a}`); else { const w = which(a); if (w) out(`${a} is ${w}`); else berr(`bash: type: ${a}: not found`); } } return 0; },
      source(args, input, scope) { const n = lookup(abs(args[0] || "")); if (!n || n.type !== "file") { berr(`bash: ${args[0]}: No such file or directory`); return 1; } return execSource(n.content.replace(/^#!.*\n/, ""), { args: args.slice(1) }); },
      bash(args, input, scope) { if (!args.length) return 0; if (args[0] === "-c") return execSource(args[1] || "", { args: args.slice(2) }); return runFile(args[0], args.slice(1), scope, true); },
      sh(args, input, scope) { return BASH.bash(args, input, scope); },
      true() { return 0; }, false() { return 1; },
      test(args) { return testExpr(args) ? 0 : 1; },
      "["(args) { if (args[args.length - 1] !== "]") { berr("bash: [: missing `]'"); return 2; } return testExpr(args.slice(0, -1)) ? 0 : 1; },
      clear() { if (cur) cur.clear = true; return 0; },
      history() { T.forEach((e, i) => out(String(i + 1).padStart(5) + "  " + e.cmd)); return 0; },
      whoami() { out("ana"); return 0; }, hostname() { out("atelier"); return 0; },
      date() { out("lun. 16 nov. 2026 09:00:00 CET"); return 0; },
      sleep() { return 0; },
      man(args) { out(`(simulation) Le manuel de « ${args[0] || "?"} » : essaie plutôt « ${args[0] || "commande"} --help », ou cherche « man ${args[0] || ""} » sur le web.`, "dim"); return 0; },
      ps(args) {
        const aux = args.some((a) => /a|x|e/.test(a));
        const list = aux ? S.procs : S.procs.filter((p) => p.user === "ana");
        if (aux) { out("USER         PID %CPU %MEM COMMAND"); for (const p of list) out(`${p.user.padEnd(8)} ${String(p.pid).padStart(7)}  0.${(p.pid % 7)}  1.${p.pid % 5} ${p.cmd}`); }
        else { out("    PID TTY          TIME CMD"); for (const p of list) out(`${String(p.pid).padStart(7)} pts/0    00:00:00 ${p.nom}`); }
        return 0;
      },
      kill(args) {
        const ids = args.filter((a) => !a.startsWith("-")); let code = 0;
        if (!ids.length) { berr("kill: usage: kill [-s sigspec | -n signum | -sigspec] pid | jobspec ... or kill -l [sigspec]"); return 2; }
        for (const id of ids) { const i = S.procs.findIndex((p) => String(p.pid) === id); if (i < 0) { berr(`bash: kill: (${id}) - No such process`); code = 1; continue; } if (S.procs[i].user === "root") { berr(`bash: kill: (${id}) - Operation not permitted`); code = 1; continue; } S.procs.splice(i, 1); }
        return code;
      },
      pkill(args) { const nm = args.filter((a) => !a.startsWith("-"))[0]; const before = S.procs.length; S.procs = S.procs.filter((p) => !(p.user === "ana" && (p.nom === nm || p.cmd.includes(nm)))); return before === S.procs.length ? 1 : 0; },
      killall(args) { return BASH.pkill(args); },
      lsof(args) {
        const i = args.indexOf("-i"); const spec = i >= 0 ? args[i + 1] || "" : ""; const port = (spec.match(/:(\d+)/) || [])[1];
        const list = S.procs.filter((p) => p.port && (!port || String(p.port) === port));
        if (!list.length) return 1;
        if (args.includes("-t")) { for (const p of list) out(String(p.pid)); return 0; }
        out("COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME");
        for (const p of list) out(`${p.nom.padEnd(8)} ${String(p.pid).padStart(5)} ${p.user.padEnd(6)} 23u  IPv6 0x1234      0t0  TCP *:${p.port} (LISTEN)`);
        return 0;
      },
      curl(args) {
        const url = args.find((a) => /^https?:/.test(a) || /^localhost/.test(a) || /^127\.0\.0\.1/.test(a)) || ""; const port = (url.match(/:(\d+)/) || [])[1] || "80";
        const path = (url.replace(/^https?:\/\//, "").match(/^[^/]*(\/.*)?$/) || [])[1] || "/";
        if (/localhost|127\.0\.0\.1/.test(url)) {
          const p = portOwner(port);
          if (!p) { berr(`curl: (7) Failed to connect to localhost port ${port} after 0 ms: Couldn't connect to server`); hint(`aucun programme n'écoute sur le port ${port} : le serveur n'est pas démarré (ou il tourne sur un autre port).`); S.lastCurl = { url, ok: false }; return 7; }
          if (p.kind === "vite" && path.startsWith("/api")) {
            if (!p.proxy) { out('<!doctype html><html lang="fr"><head><title>Bobine</title></head><body><div id="root"></div></body></html>'); hint("Vite a renvoyé la page du front au lieu de l'API : aucun proxy /api n'est configuré dans vite.config.ts."); S.lastCurl = { url, ok: false }; return 0; }
            const b = portOwner(p.proxy);
            if (!b) { out(`(dans le terminal de Vite) [vite] http proxy error: ${path}`, "err"); out(`AggregateError [ECONNREFUSED]: connect ECONNREFUSED 127.0.0.1:${p.proxy}`, "err"); hint(`le proxy envoie /api vers le port ${p.proxy}, mais rien n'y écoute : le back n'est pas démarré, ou il tourne sur un autre port.`); S.lastCurl = { url, ok: false }; return 0; }
            const r = b.respond ? b.respond(path) : b.response || "OK"; out(r); S.lastCurl = { url, ok: !/"error"/.test(r), via: "proxy" }; return 0;
          }
          const r = p.respond ? p.respond(path) : p.response || "OK"; out(r); S.lastCurl = { url, ok: !/"error"/.test(r) }; return 0;
        }
        out("(simulation : pas d'accès à Internet dans l'atelier)", "dim"); return 0;
      },
      symfony(args) { return symfonyCmd(args); },
      php(args) { return phpCmd(args); },
      vite(args) { return viteCmd(args); },
      npm(args) { return npm(args); },
      node(args) { if (args[0] === "-v" || args[0] === "--version") { out("v22.11.0"); return 0; } if (!args.length) { out("(simulation : la console interactive de node n'est pas disponible)", "dim"); return 0; } const n = lookup(abs(args[0])); if (!n) { out("node:internal/modules/cjs/loader:1228", "err"); out(`  throw err;`, "err"); out("", "err"); out(`Error: Cannot find module '${abs(args[0])}'`, "err"); hint("le fichier n'existe pas à cet endroit : vérifie le chemin et le dossier courant."); return 1; } return startServer("node " + args[0], args[0]); },
      pwsh() { S.mode = "pwsh"; S.cwd = canon(HOME_PS); mkdirp(HOME_PS); out("PowerShell 7.4.6", "dim"); return 0; },
      exit() { return 0; },
      help() { out("Commandes disponibles dans ce terminal simulé :", "dim"); out(Object.keys(BASH).filter((k) => /^[a-z]/.test(k)).sort().join("  "), "dim"); return 0; },
    };
    BASH["."] = BASH.source;
    function testExpr(a) {
      if (a[0] === "!") return !testExpr(a.slice(1));
      if (a.length === 2) { const n = lookup(abs(a[1])); if (a[0] === "-f") return !!n && n.type === "file"; if (a[0] === "-d") return !!n && n.type === "dir"; if (a[0] === "-e") return !!n; if (a[0] === "-z") return a[1] === ""; if (a[0] === "-n") return a[1] !== ""; if (a[0] === "-x") return !!n && !!n.exec; }
      if (a.length === 3) { const [x, op, y] = a; if (op === "=" || op === "==") return x === y; if (op === "!=") return x !== y; const nx = Number(x), ny = Number(y); if (op === "-eq") return nx === ny; if (op === "-ne") return nx !== ny; if (op === "-gt") return nx > ny; if (op === "-lt") return nx < ny; if (op === "-ge") return nx >= ny; if (op === "-le") return nx <= ny; }
      if (a.length === 1) return a[0] !== "";
      return false;
    }

    /* ======================================================================
     *  POWERSHELL
     * ====================================================================== */
    class PSItem { constructor(path, n) { this._path = path; this._n = n; } get Name() { return parentOf(this._path)[1]; } get FullName() { return show(this._path); } get Length() { return this._n.type === "file" ? sizeOf(this._n) : undefined; } get Extension() { const m = this.Name.match(/\.[^.]+$/); return m ? m[0] : ""; } get LastWriteTime() { return this._n.mtime; } get Mode() { return this._n.type === "dir" ? "d----" : "-a---"; } get PSIsContainer() { return this._n.type === "dir"; } get BaseName() { return this.Name.replace(/\.[^.]+$/, ""); } get DirectoryName() { return show(parentOf(this._path)[0]); } toString() { return this.FullName; } }
    class MatchInfo { constructor(path, num, line, shown) { this.Path = path ? show(path) : "InputStream"; this.LineNumber = num; this.Line = line; this._shown = shown; this.Filename = path ? parentOf(path)[1] : "InputStream"; } toString() { return this._shown === null ? this.Line : `${this._shown}:${this.LineNumber}:${this.Line}`; } }
    const PSERR = (cmd, msg, fr) => { out(`${cmd}: ${msg}`, "err"); if (fr) hint(fr); return 1; };
    const isPSObj = (x) => x !== null && typeof x === "object";
    function fmtDate(d) { const p = (n) => String(n).padStart(2, "0"); return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()}    ${p(d.getHours())}:${p(d.getMinutes())}`; }
    function formatObjects(objs) {
      const lines = []; let i = 0;
      while (i < objs.length) {
        const o = objs[i];
        if (o instanceof PSItem) {
          const parent = parentOf(o._path)[0]; const group = [];
          while (i < objs.length && objs[i] instanceof PSItem && parentOf(objs[i]._path)[0] === parent) group.push(objs[i++]);
          lines.push("", `    Directory: ${show(parent)}`, "", "Mode                 LastWriteTime         Length Name", "----                 -------------         ------ ----");
          for (const g of group) lines.push({ text: `${g.Mode}          ${fmtDate(g.LastWriteTime)}  ${String(g.Length ?? "").padStart(13)} ${g.Name}`, cls: g.PSIsContainer ? "dir" : "" });
          lines.push(""); continue;
        }
        if (o instanceof MatchInfo || !isPSObj(o) || o instanceof Date) { lines.push(o instanceof Date ? o.toLocaleString("fr-FR") : String(o)); i++; continue; }
        // objets génériques : tableau
        const group = []; const keys0 = Object.keys(o).filter((k) => !k.startsWith("_")).join(",");
        while (i < objs.length && isPSObj(objs[i]) && !(objs[i] instanceof PSItem) && !(objs[i] instanceof MatchInfo) && Object.keys(objs[i]).filter((k) => !k.startsWith("_")).join(",") === keys0) group.push(objs[i++]);
        const cols = keys0.split(",").filter(Boolean);
        if (group.length === 1 && cols.length > 4) { lines.push(""); const w = Math.max(...cols.map((c) => c.length)); for (const c of cols) lines.push(`${c.padEnd(w)} : ${fmtVal(group[0][c])}`); lines.push(""); continue; }
        const widths = cols.map((c) => Math.max(c.length, ...group.map((g) => fmtVal(g[c]).length)));
        lines.push("", cols.map((c, k) => c.padEnd(widths[k])).join(" ").trimEnd(), cols.map((c, k) => "-".repeat(c.length).padEnd(widths[k])).join(" ").trimEnd());
        for (const g of group) lines.push(cols.map((c, k) => (typeof g[c] === "number" ? fmtVal(g[c]).padStart(widths[k]) : fmtVal(g[c]).padEnd(widths[k]))).join(" ").trimEnd());
        lines.push("");
      }
      return lines;
    }
    function fmtVal(v) { if (v === undefined || v === null) return ""; if (v === true) return "True"; if (v === false) return "False"; if (Array.isArray(v)) return "{" + v.map(fmtVal).join(", ") + "}"; if (v instanceof PSItem) return v.Name; if (v instanceof MatchInfo) return v.toString(); return String(v); }
    function toText(objs) { return formatObjects(objs).map((l) => (typeof l === "string" ? l : l.text)); }

    function lexPS(src) {
      const toks = []; let i = 0;
      while (i < src.length) {
        const c = src[i];
        if (c === " " || c === "\t") { i++; continue; }
        if (c === "#") { while (i < src.length && src[i] !== "\n") i++; continue; }
        if (c === "\n" || c === ";") { toks.push({ op: ";" }); i++; continue; }
        if (c === "`" && src[i + 1] === "\n") { i += 2; continue; }
        if (src.startsWith("&&", i) || src.startsWith("||", i)) { toks.push({ op: src.slice(i, i + 2) }); i += 2; continue; }
        if (src.startsWith("2>&1", i)) { toks.push({ op: "2>&1" }); i += 4; continue; }
        if (src.startsWith(">>", i) || src.startsWith("2>", i)) { toks.push({ op: src.slice(i, i + 2) }); i += 2; continue; }
        if (c === "|" || c === ">") { toks.push({ op: c }); i++; continue; }
        if (c === "'") { let j = i + 1, s = ""; while (j < src.length) { if (src[j] === "'" && src[j + 1] === "'") { s += "'"; j += 2; continue; } if (src[j] === "'") break; s += src[j++]; } toks.push({ s, q: "'" }); i = j + 1; continue; }
        if (c === '"') { let j = i + 1, s = ""; while (j < src.length && src[j] !== '"') { if (src[j] === "`" && j + 1 < src.length) { const e = src[j + 1]; s += e === "n" ? "\n" : e === "t" ? "\t" : e; j += 2; continue; } if (src[j] === "$" && src[j + 1] === "(") { const e = matchParen(src, j + 1); s += src.slice(j, e + 1); j = e + 1; continue; } s += src[j++]; } toks.push({ s, q: '"' }); i = j + 1; continue; }
        if (c === "{") { let d = 0, j = i; for (; j < src.length; j++) { if (src[j] === "{") d++; else if (src[j] === "}") { d--; if (!d) break; } } toks.push({ block: src.slice(i + 1, j).trim() }); i = j + 1; continue; }
        if (c === "(") { const e = matchParen(src, i); let s = src.slice(i + 1, e); let j = e + 1; let member = ""; const mm = src.slice(j).match(/^\.(\w+)/); if (mm) { member = mm[1]; j += mm[0].length; } toks.push({ paren: s, member }); i = j; continue; }
        if (c === "@" && src[i + 1] === "(") { const e = matchParen(src, i + 1); toks.push({ arr: src.slice(i + 2, e) }); i = e + 1; continue; }
        if (c === ",") { toks.push({ s: ",", q: "" }); i++; continue; }
        let j = i; while (j < src.length && !" \t\n;|>'\"{}(),".includes(src[j]) && !(src.startsWith("&&", j) || src.startsWith("||", j))) { if (src[j] === "2" && src[j + 1] === ">" && j === i) break; j++; }
        if (j === i) { toks.push({ s: c, q: "" }); i++; continue; }
        toks.push({ s: src.slice(i, j), q: "" }); i = j;
      }
      return toks;
    }
    function psVar(name) {
      const low = name.toLowerCase();
      if (low.startsWith("env:")) { const k = Object.keys(S.env).find((x) => x.toLowerCase() === low.slice(4)); return k ? S.env[k] : ""; }
      if (low === "home") return show(HOME_PS); if (low === "pwd") return show(S.cwd); if (low === "true") return true; if (low === "false") return false; if (low === "null") return null;
      const k = Object.keys(S.psvars).find((x) => x.toLowerCase() === low);
      return k ? S.psvars[k] : "";
    }
    function psExpandStr(s, dollarUnder) {
      s = s.replace(/\$\(([\s\S]*?)\)/g, (m, inner) => toText(psEvalPipeline(inner, dollarUnder)).join(" ").trim());
      return s.replace(/\$(env:\w+|\w+)(\[\d+\])?(\.\w+)?/g, (m, n, idx, prop) => { let v = n === "_" ? dollarUnder : psVar(n); if (idx && Array.isArray(v)) v = v[Number(idx.slice(1, -1))]; if (prop && v !== null && v !== undefined) v = v[prop.slice(1)]; return fmtVal(v); });
    }
    function psValue(tok, dollarUnder) {
      if (tok.q === "'") return tok.s;
      if (tok.q === '"') return psExpandStr(tok.s, dollarUnder);
      if (tok.paren !== undefined) { const r = psEvalPipeline(tok.paren, dollarUnder); const v = r.length === 1 ? r[0] : r; if (!tok.member) return v; const m = tok.member.toLowerCase(); if ((m === "count" || m === "length") && Array.isArray(v)) return v.length; if (m === "count") return v === null || v === "" ? 0 : 1; return v == null ? "" : (Array.isArray(v) ? v.map((x) => x[tok.member]) : v[tok.member]); }
      if (tok.arr !== undefined) return psEvalPipeline(tok.arr, dollarUnder);
      if (tok.block !== undefined) return { _block: tok.block };
      const s = tok.s;
      if (/^\$/.test(s)) { const m = s.match(/^\$(env:\w+|\w+)(?:\[(\d+)\])?((?:\.\w+)*)$/); if (m) { let v = m[1] === "_" ? dollarUnder : psVar(m[1]); if (m[2] !== undefined && Array.isArray(v)) v = v[Number(m[2])]; m[2] = m[3]; for (const p of m[2].split(".").filter(Boolean)) v = v == null ? "" : (p.toLowerCase() === "count" && Array.isArray(v) ? v.length : v[p]); return v; } }
      if (/^-?\d+(\.\d+)?$/.test(s)) return Number(s);
      if (/^\d+(kb|mb)$/i.test(s)) return Number(s.slice(0, -2)) * (s.toLowerCase().endsWith("kb") ? 1024 : 1048576);
      return s;
    }
    function splitPS(toks) { // → [{pipeline:[[tok...]...], conn}]
      const list = []; let pipeline = [], cmd = [], conn = null;
      const endCmd = () => { if (cmd.length) pipeline.push(cmd); cmd = []; };
      const endPipe = (op) => { endCmd(); if (pipeline.length) list.push({ pipeline, conn }); pipeline = []; conn = op; };
      for (const t of toks) { if (t.op === "|") endCmd(); else if (t.op === ";") endPipe(null); else if (t.op === "&&" || t.op === "||") endPipe(t.op); else cmd.push(t); }
      endPipe(null); return list;
    }
    function psEvalPipeline(src, dollarUnder) {
      const saved = cur; const buf = { out: [] }; cur = buf; let res = [];
      try { for (const item of splitPS(lexPS(src))) res = runPSPipeline(item.pipeline, dollarUnder).objs; } finally { cur = saved; }
      for (const o of buf.out) if (o.cls === "err" || o.cls === "hint") out(o.text, o.cls);
      return res;
    }
    const PS_ALIASES = { ls: "get-childitem", dir: "get-childitem", gci: "get-childitem", cd: "set-location", sl: "set-location", chdir: "set-location", pwd: "get-location", gl: "get-location", cat: "get-content", gc: "get-content", type: "get-content", echo: "write-output", write: "write-output", rm: "remove-item", del: "remove-item", erase: "remove-item", ri: "remove-item", rmdir: "remove-item", rd: "remove-item", cp: "copy-item", copy: "copy-item", cpi: "copy-item", mv: "move-item", move: "move-item", mi: "move-item", ren: "rename-item", rni: "rename-item", ni: "new-item", sls: "select-string", select: "select-object", sort: "sort-object", measure: "measure-object", where: "where-object", "?": "where-object", foreach: "foreach-object", "%": "foreach-object", gcm: "get-command", ps: "get-process", gps: "get-process", kill: "stop-process", spps: "stop-process", sc: "set-content", ac: "add-content", clear: "clear-host", cls: "clear-host", group: "group-object", irm: "invoke-restmethod", iwr: "invoke-webrequest", curl: "invoke-webrequest", h: "get-history", history: "get-history", ft: "format-table", fl: "format-list" };
    const SWITCHES = { "get-childitem": ["recurse", "force", "file", "directory", "name"], "remove-item": ["recurse", "force"], "copy-item": ["recurse", "force"], "new-item": ["force"], "select-string": ["simplematch", "casesensitive", "notmatch", "list"], "sort-object": ["descending", "unique"], "measure-object": ["line", "word", "character", "sum", "average", "maximum", "minimum"], "select-object": ["unique"], "get-content": ["raw"], "stop-process": ["force"], "set-executionpolicy": ["force"], "test-path": [], "out-file": ["append"], "get-command": [], "group-object": ["noelement"] };
    function bindArgs(cmd, toks, dollarUnder) {
      const sw = SWITCHES[cmd] || []; const named = {}; const pos = [];
      for (let k = 0; k < toks.length; k++) {
        const t = toks[k];
        if (t.q === "" && /^-[A-Za-z][\w]*(:.*)?$/.test(t.s) && !/^-\d/.test(t.s)) {
          let name = t.s.slice(1).toLowerCase(); let inline = null; const ci2 = name.indexOf(":"); if (ci2 >= 0) { inline = t.s.slice(1 + ci2 + 1); name = name.slice(0, ci2); }
          const full = sw.find((s) => s === name) || sw.find((s) => s.startsWith(name));
          if (full) { named[full] = inline === null ? true : !/^\$?false$/i.test(inline); continue; }
          if (inline !== null) { named[name] = inline; continue; }
          const nx = toks[k + 1]; if (nx && !(nx.q === "" && /^-[A-Za-z]/.test(nx.s))) { let v = psValue(nx, dollarUnder); k++; while (toks[k + 1] && toks[k + 1].q === "" && toks[k + 1].s === ",") { k += 2; v = [].concat(v, psValue(toks[k], dollarUnder)); } named[name] = v; } else named[name] = true;
          continue;
        }
        let v = psValue(t, dollarUnder);
        if (typeof v === "string" && v.includes(",") && t.q === "" && !/^\$/.test(t.s)) v = v.split(",");
        while (toks[k + 1] && toks[k + 1].q === "" && toks[k + 1].s === ",") { k += 2; v = [].concat(v, psValue(toks[k], dollarUnder)); }
        pos.push(v);
      }
      const get = (...names) => { for (const n of names) { const key = Object.keys(named).find((x) => x === n || n.startsWith(x)); if (key !== undefined) return named[key]; } return undefined; };
      return { named, pos, get };
    }
    function runPSPipeline(pipeline, dollarUnder) {
      let objs = null; let code = 0;
      for (let k = 0; k < pipeline.length; k++) {
        let toks = pipeline[k];
        const redir = []; const clean = [];
        for (let j = 0; j < toks.length; j++) { const t = toks[j]; if (t.op === ">" || t.op === ">>" || t.op === "2>") { redir.push({ op: t.op, target: psValue(toks[j + 1] || { s: "" }, dollarUnder) }); j++; } else if (t.op === "2>&1") redir.push({ op: "2>&1" }); else if (!t.op) clean.push(t); }
        toks = clean; if (!toks.length) continue;
        let res;
        const first = toks[0];
        // assignation
        if (first.q === "" && /^\$(env:)?\w+$/.test(first.s) && toks[1] && toks[1].s === "=") {
          const rest = toks.slice(2); let v;
          if (rest.length === 1 && (rest[0].q || rest[0].paren !== undefined || rest[0].arr !== undefined || /^\$|^-?\d/.test(rest[0].s))) v = psValue(rest[0], dollarUnder);
          else { const r = runPSPipeline([rest], dollarUnder).objs; v = r.length === 1 ? r[0] : r; }
          const name = first.s.slice(1);
          if (name.toLowerCase().startsWith("env:")) { const key = Object.keys(S.env).find((x) => x.toLowerCase() === name.slice(4).toLowerCase()) || name.slice(4); S.env[key] = fmtVal(v); }
          else S.psvars[name] = v;
          return { objs: [], code: 0 };
        }
        if (first.q || first.paren !== undefined || first.arr !== undefined || (first.q === "" && /^\$|^-?\d+(\.\d+)?$/.test(first.s) && (toks.length === 1 || (toks[1].q === "" && toks[1].s === ",")))) {
          let v = psValue(first, dollarUnder); let k2 = 1; const vals = [v];
          while (toks[k2] && toks[k2].q === "" && toks[k2].s === "," && toks[k2 + 1]) { vals.push(psValue(toks[k2 + 1], dollarUnder)); k2 += 2; }
          if (vals.length > 1) v = vals;
          res = { objs: Array.isArray(v) ? v : [v], code: 0 };
        } else {
          let name = String(first.s); const low = name.toLowerCase();
          const cmd = PS_ALIASES[low] || low;
          const args = bindArgs(cmd, toks.slice(1), dollarUnder);
          const saved = cur; const buf = { out: [] }; cur = buf;
          try {
            if (PS[cmd]) res = PS[cmd](args, objs, dollarUnder) || { objs: [], code: 0 };
            else if (/[\\/]/.test(name) || /\.ps1$/i.test(name)) res = runPS1(name, args);
            else if (["npm", "node", "git", "php"].includes(low)) { const c = low === "npm" ? npm(args.pos.map(fmtVal).concat(Object.keys(args.named).map((x) => "--" + x))) : BASH.node(args.pos.map(fmtVal)); res = { objs: [], code: c }; }
            else { out(`${name}: The term '${name}' is not recognized as a name of a cmdlet, function, script file, or executable program.`, "err"); out("Check the spelling of the name, or if a path was included, verify that the path is correct and try again.", "err"); hint("commande inconnue : faute de frappe, ou commande Linux qui n'existe pas en PowerShell (voir la table de correspondance)."); res = { objs: [], code: 1 }; }
          } catch (e) { out(String(e.message || e), "err"); res = { objs: [], code: 1 }; }
          cur = saved;
          for (const o of buf.out) if (o.cls === "err" || o.cls === "hint") { if (!redir.some((r) => r.op === "2>")) out(o.text, o.cls); } else if (cur) cur.out.push(o);
        }
        objs = res.objs; code = res.code;
        for (const r of redir) {
          if (r.op === "2>&1" || r.op === "2>") continue;
          const p = abs(fmtVal(r.target)); const data = toText(objs).join("\n");
          const w = writeFile(p, data ? data.replace(/^\n+/, "") + "\n" : "", r.op === ">>");
          if (!w) { out(`out-file: Could not find a part of the path '${show(p)}'.`, "err"); code = 1; }
          objs = [];
        }
      }
      return { objs: objs || [], code };
    }
    function runPS(src) {
      let code = 0;
      for (const item of splitPS(lexPS(src))) {
        if (item.conn === "&&" && code !== 0) continue; if (item.conn === "||" && code === 0) continue;
        const r = runPSPipeline(item.pipeline, undefined); code = r.code;
        for (const l of formatObjects(r.objs)) typeof l === "string" ? out(l) : out(l.text, l.cls);
      }
      S.lastCode = code;
      return code;
    }
    function runPS1(name, args) {
      const p = abs(name); const n = lookup(p);
      if (!n) { out(`${name}: The term '${name}' is not recognized as a name of a cmdlet, function, script file, or executable program.`, "err"); return { objs: [], code: 1 }; }
      if (!/^\.?[\\/]|^[a-zA-Z]:/.test(name) && !name.includes("\\") && !name.includes("/")) { out(`${name}: The term '${name}' is not recognized…`, "err"); hint("pour lancer un script du dossier courant, il faut écrire .\\" + name + " (PowerShell ne cherche pas dans le dossier courant)."); return { objs: [], code: 1 }; }
      if (/\.ps1$/i.test(p) && (S.policy === "Restricted" || S.policy === "AllSigned")) {
        out(`${name}: File ${show(p)} cannot be loaded because running scripts is disabled on this system. For more information, see about_Execution_Policies at https://go.microsoft.com/fwlink/?LinkID=135170.`, "err");
        hint("Windows bloque les scripts par défaut. Autorise-les pour ton compte : Set-ExecutionPolicy -Scope CurrentUser RemoteSigned");
        return { objs: [], code: 1 };
      }
      const saved = S.psvars.args; S.psvars.args = args.pos;
      try { const code = runPS(n.content); return { objs: [], code }; } finally { S.psvars.args = saved; }
    }
    function evalChain(src, x) { // $_.Split(" ")[0].Trim() …
      const m = src.match(/^\$(\w+|env:\w+)/); if (!m) return undefined;
      let v = m[1] === "_" ? x : psVar(m[1]); let rest = src.slice(m[0].length);
      while (rest) {
        let mm = rest.match(/^\[(-?\d+)\]/);
        if (mm) { const i = Number(mm[1]); v = Array.isArray(v) ? v[i < 0 ? v.length + i : i] : typeof v === "string" ? v[i] : undefined; rest = rest.slice(mm[0].length); continue; }
        mm = rest.match(/^\.(\w+)\(((?:'[^']*'|"[^"]*"|[^)'"])*)\)/);
        if (mm) {
          const args = mm[2] ? mm[2].split(/,(?=(?:[^'"]|'[^']*'|"[^"]*")*$)/).map((a) => { const t = a.trim(); return /^['"]/.test(t) ? t.slice(1, -1) : Number(t); }) : [];
          const f = mm[1].toLowerCase(); const sv = String(fmtVal(v));
          v = f === "split" ? sv.split(args[0] ?? " ") : f === "toupper" ? sv.toUpperCase() : f === "tolower" ? sv.toLowerCase() : f === "trim" ? sv.trim() : f === "replace" ? sv.split(String(args[0])).join(String(args[1] ?? "")) : f === "substring" ? sv.substr(args[0], args[1]) : f === "startswith" ? sv.startsWith(args[0]) : f === "endswith" ? sv.endsWith(args[0]) : f === "contains" ? sv.includes(args[0]) : f === "tostring" ? sv : v;
          rest = rest.slice(mm[0].length); continue;
        }
        mm = rest.match(/^\.(\w+)/);
        if (mm) { const p = mm[1]; v = v == null ? undefined : p.toLowerCase() === "count" || p.toLowerCase() === "length" && (Array.isArray(v) || typeof v === "string") ? (Array.isArray(v) || typeof v === "string" ? v.length : v[p]) : v[p]; rest = rest.slice(mm[0].length); continue; }
        return undefined;
      }
      return v;
    }
    function evalBlock(block, x) {
      const src = block.trim();
      if (/^\$\w+(?:\.\w+(?:\((?:'[^']*'|"[^"]*"|[^)'"])*\))?|\[-?\d+\])*$/.test(src)) return evalChain(src, x);
      const cond = src.split(/\s+-(and|or)\s+/i);
      if (cond.length > 1 || /\s-(eq|ne|gt|lt|ge|le|like|notlike|match|notmatch|contains)\s/i.test(src)) {
        let acc = null, op = null;
        for (let k = 0; k < cond.length; k++) {
          if (k % 2 === 1) { op = cond[k].toLowerCase(); continue; }
          const m = cond[k].match(/^(.+?)\s+-(eq|ne|gt|lt|ge|le|like|notlike|match|notmatch|contains)\s+(.+)$/i);
          let v;
          if (!m) v = !!psValue({ s: cond[k], q: "" }, x);
          else {
            const left = psValue(lexPS(m[1])[0], x); const right = psValue(lexPS(m[3])[0], x); const o = m[2].toLowerCase();
            const L = typeof left === "string" ? left.toLowerCase() : left, R = typeof right === "string" ? right.toLowerCase() : right;
            v = o === "eq" ? L == R : o === "ne" ? L != R : o === "gt" ? left > right : o === "lt" ? left < right : o === "ge" ? left >= right : o === "le" ? left <= right
              : o === "like" ? globToRe(String(right), "i").test(String(left)) : o === "notlike" ? !globToRe(String(right), "i").test(String(left))
              : o === "match" ? new RegExp(String(right), "i").test(String(left)) : o === "notmatch" ? !new RegExp(String(right), "i").test(String(left)) : Array.isArray(left) && left.includes(right);
          }
          acc = acc === null ? v : op === "and" ? acc && v : acc || v;
        }
        return acc;
      }
      const r = psEvalPipeline(src, x); return r.length === 1 ? r[0] : r;
    }
    const itemsAt = (pathArg, opts) => {
      const res = []; const paths = [].concat(pathArg === undefined ? "." : pathArg);
      for (const raw of paths) {
        const s = fmtVal(raw); const matches = /[*?]/.test(s) ? glob(s) : [s];
        if (!matches.length) continue;
        for (const m of matches) {
          const p = abs(m); const n = lookup(p);
          if (!n) { out(`Get-ChildItem: Cannot find path '${show(p)}' because it does not exist.`, "err"); hint("ce chemin n'existe pas : vérifie l'orthographe et le dossier courant (Get-Location)."); continue; }
          res.push({ p: canon(p), n });
        }
      }
      return res;
    };
    const PS = {
      "get-location"() { return { objs: [{ Path: show(S.cwd) }], code: 0 }; },
      "set-location"(a) {
        const t = fmtVal(a.get("path", "literalpath") ?? a.pos[0] ?? "~"); const p = t === "-" ? S.oldpwd || S.cwd : abs(t); const n = lookup(p);
        if (!n || n.type !== "dir") { out(`Set-Location: Cannot find path '${show(p)}' because it does not exist.`, "err"); hint("ce dossier n'existe pas : vérifie le chemin (Tab complète les noms) et où tu es (Get-Location)."); return { objs: [], code: 1 }; }
        S.oldpwd = S.cwd; S.cwd = canon(p); return { objs: [], code: 0 };
      },
      "get-childitem"(a) {
        const path = a.get("path", "literalpath") ?? a.pos[0]; const filter = fmtVal(a.get("filter", "include") ?? a.pos[1] ?? "");
        if (typeof path === "string" && /^env:?$/i.test(path.replace(/\\$/, ""))) return { objs: Object.keys(S.env).sort().map((k) => ({ Name: k, Value: S.env[k] })), code: 0 };
        const res = []; const filtRe = filter ? globToRe(filter, "i") : null;
        for (const { p, n } of itemsAt(path)) {
          if (n.type === "file") { res.push(new PSItem(p, n)); continue; }
          const visit = (dp, dn) => {
            const names = [...dn.children.keys()].sort((x, y) => { const dx = dn.children.get(x).type === "dir", dy = dn.children.get(y).type === "dir"; return dx !== dy ? (dx ? -1 : 1) : x.localeCompare(y); });
            const here = []; const sub = [];
            for (const nm of names) { const c = dn.children.get(nm); if (nm.startsWith(".") && !a.get("force") && false) continue; const cp = dp + "/" + nm; if (!filtRe || filtRe.test(nm)) here.push(new PSItem(cp, c)); if (c.type === "dir") sub.push([cp, c]); }
            res.push(...here); if (a.get("recurse")) for (const [cp, c] of sub) visit(cp, c);
          };
          visit(p === "/" ? "" : p, n);
        }
        let r = res; if (a.get("file")) r = r.filter((x) => !x.PSIsContainer); if (a.get("directory")) r = r.filter((x) => x.PSIsContainer);
        if (a.get("name")) return { objs: r.map((x) => (a.get("recurse") ? x._path.slice((abs(fmtVal(path ?? ".")) + "/").length).replace(/\//g, "\\") : x.Name)), code: 0 };
        return { objs: r, code: res.length || !path ? 0 : 1 };
      },
      "get-content"(a) {
        const t = a.get("path", "literalpath") ?? a.pos[0]; if (t === undefined) return PSERR("Get-Content", "Cannot bind argument to parameter 'Path' because it is null.");
        const out2 = [];
        for (const raw of [].concat(t)) {
          const s = fmtVal(raw); for (const m of /[*?]/.test(s) ? glob(s) : [s]) {
            const p = abs(m); const n = lookup(p);
            if (!n) { PSERR("Get-Content", `Cannot find path '${show(p)}' because it does not exist.`, "le fichier n'existe pas ici."); continue; }
            if (n.type === "dir") { PSERR("Get-Content", `Unable to get content because it is a directory: '${show(p)}'. Please use 'Get-ChildItem' instead.`); continue; }
            if (a.get("raw")) { out2.push(n.content); continue; }
            let ls = linesOf(n.content); const first = a.get("totalcount", "head", "first"); const last = a.get("tail", "last");
            if (first !== undefined) ls = ls.slice(0, Number(first)); if (last !== undefined) ls = ls.slice(-Number(last));
            out2.push(...ls);
          }
        }
        return { objs: out2, code: 0 };
      },
      "write-output"(a, input) { return { objs: a.pos.flat(), code: 0 }; },
      "write-host"(a) { out(a.pos.map(fmtVal).join(" ")); return { objs: [], code: 0 }; },
      "new-item"(a) {
        let p = a.get("path") ?? a.pos[0]; const name = a.get("name");
        if (Array.isArray(p)) { let code = 0; const objs = []; for (const x of p) { const sub = { ...a, get: (...k) => (k.includes("path") ? x : a.get(...k)), pos: [x] }; const r = this["new-item"](sub); code = code || r.code; objs.push(...r.objs); } return { objs, code }; } const type = String(a.get("itemtype", "type") || "File").toLowerCase(); const value = a.get("value");
        if (p === undefined && name !== undefined) p = "."; const full = abs(name !== undefined ? fmtVal(p) + "/" + fmtVal(name) : fmtVal(p));
        if (lookup(full) && !a.get("force")) return PSERR("New-Item", `An item with the specified name ${show(full)} already exists.`, "ce fichier ou ce dossier existe déjà (ajoute -Force pour l'écraser / ne pas échouer).");
        if (type.startsWith("dir")) { mkdirp(full); return { objs: [new PSItem(canon(full), lookup(full))], code: 0 }; }
        const [pd] = parentOf(full); if (!lookup(pd)) { if (a.get("force")) mkdirp(pd); else return PSERR("New-Item", `Could not find a part of the path '${show(full)}'.`, "le dossier parent n'existe pas : crée-le d'abord, ou ajoute -Force."); }
        writeFile(full, value === undefined ? "" : fmtVal(value) + "\n"); return { objs: [new PSItem(canon(full), lookup(full))], code: 0 };
      },
      mkdir(a) { const t = a.get("path") ?? a.pos[0]; let code = 0; const objs = []; for (const x of [].concat(t)) { const p = abs(fmtVal(x)); if (lookup(p)) { PSERR("New-Item", `An item with the specified name ${show(p)} already exists.`); code = 1; continue; } mkdirp(p); objs.push(new PSItem(canon(p), lookup(p))); } return { objs, code }; },
      "set-content"(a, input) { const p = abs(fmtVal(a.get("path") ?? a.pos[0])); const v = a.get("value") ?? (a.pos.length > 1 ? a.pos.slice(1) : input || []); const txt = [].concat(v).map(fmtVal).join("\n"); const w = writeFile(p, txt + "\n"); if (!w) return PSERR("Set-Content", `Could not find a part of the path '${show(p)}'.`, "le dossier n'existe pas."); return { objs: [], code: 0 }; },
      "add-content"(a, input) { const p = abs(fmtVal(a.get("path") ?? a.pos[0])); const v = a.get("value") ?? (a.pos.length > 1 ? a.pos.slice(1) : input || []); const n = lookup(p); const prefix = n && n.content && !n.content.endsWith("\n") ? "\n" : ""; const w = writeFile(p, prefix + [].concat(v).map(fmtVal).join("\n") + "\n", true); if (!w) return PSERR("Add-Content", `Could not find a part of the path '${show(p)}'.`); return { objs: [], code: 0 }; },
      "out-file"(a, input) { const p = abs(fmtVal(a.get("filepath", "path") ?? a.pos[0])); const txt = toText(input || []).join("\n").replace(/^\n+/, ""); writeFile(p, txt ? txt + "\n" : "", !!a.get("append")); return { objs: [], code: 0 }; },
      "remove-item"(a) {
        let code = 0; const t = a.get("path", "literalpath") ?? a.pos;
        for (const raw of [].concat(t)) { const s = fmtVal(raw); const matches = /[*?]/.test(s) ? glob(s) : [s];
          for (const m of matches) { const p = abs(m); const n = lookup(p);
            if (!n) { PSERR("Remove-Item", `Cannot find path '${show(p)}' because it does not exist.`); code = 1; continue; }
            if (n.type === "dir" && n.children.size && !a.get("recurse")) { PSERR("Remove-Item", `The item at ${show(p)} has children and the Recurse parameter was not specified. If you continue, all children will be removed with the item.`, "le dossier n'est pas vide : ajoute -Recurse (sans corbeille, attention)."); code = 1; continue; }
            removeNode(p); } }
        return { objs: [], code };
      },
      "copy-item"(a) {
        const src = a.get("path") ?? a.pos[0]; const dest = fmtVal(a.get("destination") ?? a.pos[1]); let code = 0;
        for (const raw of [].concat(src)) { const s = fmtVal(raw); for (const m of /[*?]/.test(s) ? glob(s) : [s]) {
          const sp = abs(m); const sn = lookup(sp); if (!sn) { PSERR("Copy-Item", `Cannot find path '${show(sp)}' because it does not exist.`); code = 1; continue; }
          const dp = abs(dest); const dn = lookup(dp); const target = dn && dn.type === "dir" ? dp + "/" + parentOf(sp)[1] : dp;
          const [pd, nm] = parentOf(target); const pdn = lookup(pd); if (!pdn) { PSERR("Copy-Item", `Could not find a part of the path '${show(target)}'.`); code = 1; continue; }
          if (sn.type === "dir" && !a.get("recurse")) { pdn.children.set(nm, dir()); hint("sans -Recurse, Copy-Item ne copie que le dossier vide."); continue; }
          pdn.children.set(nm, cloneNode(sn)); } }
        return { objs: [], code };
      },
      "move-item"(a) {
        const src = a.get("path") ?? a.pos[0]; const dest = fmtVal(a.get("destination") ?? a.pos[1]); let code = 0;
        for (const raw of [].concat(src)) { const s = fmtVal(raw); for (const m of /[*?]/.test(s) ? glob(s) : [s]) {
          const sp = abs(m); const sn = lookup(sp); if (!sn) { PSERR("Move-Item", `Cannot find path '${show(sp)}' because it does not exist.`); code = 1; continue; }
          const dp = abs(dest); const dn = lookup(dp); const target = dn && dn.type === "dir" ? dp + "/" + parentOf(sp)[1] : dp;
          const [pd, nm] = parentOf(target); const pdn = lookup(pd); if (!pdn) { PSERR("Move-Item", `Could not find a part of the path '${show(target)}'.`); code = 1; continue; }
          removeNode(sp); pdn.children.set(nm, sn); } }
        return { objs: [], code };
      },
      "rename-item"(a) { const sp = abs(fmtVal(a.get("path") ?? a.pos[0])); const nn = fmtVal(a.get("newname") ?? a.pos[1]); const sn = lookup(sp); if (!sn) return PSERR("Rename-Item", `Cannot rename because item at '${show(sp)}' does not exist.`); removeNode(sp); lookup(parentOf(sp)[0]).children.set(nn, sn); return { objs: [], code: 0 }; },
      "test-path"(a) { const p = abs(fmtVal(a.get("path") ?? a.pos[0])); const n = lookup(p); const t = String(a.get("pathtype") || "any").toLowerCase(); return { objs: [!!n && (t === "any" || (t === "leaf") === (n.type === "file"))], code: 0 }; },
      "select-string"(a, input) {
        const pat = fmtVal(a.get("pattern") ?? a.pos[0]); const path = a.get("path") ?? (a.pos.length > 1 ? a.pos[1] : undefined);
        const re = new RegExp(a.get("simplematch") ? pat.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") : pat, a.get("casesensitive") ? "" : "i"); const not = !!a.get("notmatch");
        const res = []; const add = (p, lines, shown) => lines.forEach((l, i) => { if (re.test(l) !== not) res.push(new MatchInfo(p, i + 1, l, shown)); });
        if (path !== undefined) { for (const raw of [].concat(path)) { const s = fmtVal(raw); for (const m of /[*?]/.test(s) ? glob(s) : [s]) { const p = abs(m); const n = lookup(p); if (!n) { PSERR("Select-String", `Cannot find path '${show(p)}' because it does not exist.`); continue; } if (n.type === "file") add(p, linesOf(n.content), rel(canon(p)).replace(/\//g, "\\")); } } }
        else for (const o of input || []) { if (o instanceof PSItem) { if (!o.PSIsContainer) add(o._path, linesOf(o._n.content), rel(o._path).replace(/\//g, "\\")); } else if (o instanceof MatchInfo) { if (re.test(o.Line) !== not) res.push(o); } else { const s = fmtVal(o); if (re.test(s) !== not) res.push(new MatchInfo(null, 0, s, null)); } }
        return { objs: res, code: res.length ? 0 : 1 };
      },
      "select-object"(a, input) {
        let r = (input || []).slice(); const first = a.get("first"); const last = a.get("last"); const exp = a.get("expandproperty"); const props = a.get("property") ?? (a.pos.length ? a.pos.flat() : undefined);
        if (a.get("unique")) r = [...new Map(r.map((x) => [fmtVal(x), x])).values()];
        if (first !== undefined) r = r.slice(0, Number(first)); if (last !== undefined) r = r.slice(-Number(last));
        if (exp !== undefined) r = r.map((x) => x[fmtVal(exp)]).flat();
        else if (props !== undefined) r = r.map((x) => { const o = {}; for (const p of [].concat(props)) o[fmtVal(p)] = x[fmtVal(p)]; return o; });
        return { objs: r, code: 0 };
      },
      "sort-object"(a, input) {
        const prop = a.get("property") ?? a.pos[0]; const key = (x) => (prop !== undefined && isPSObj(x) ? x[fmtVal(prop)] : x);
        let r = (input || []).slice().sort((x, y) => { const X = key(x), Y = key(y); return typeof X === "number" && typeof Y === "number" ? X - Y : String(fmtVal(X)).localeCompare(String(fmtVal(Y))); });
        if (a.get("descending")) r.reverse(); if (a.get("unique")) r = [...new Map(r.map((x) => [fmtVal(key(x)), x])).values()];
        return { objs: r, code: 0 };
      },
      "measure-object"(a, input) {
        const r = input || []; const o = { Count: r.length };
        if (a.get("line") || a.get("word") || a.get("character")) { const txt = r.map(fmtVal); const res = {}; if (a.get("line")) res.Lines = txt.length; if (a.get("word")) res.Words = txt.join(" ").split(/\s+/).filter(Boolean).length; if (a.get("character")) res.Characters = txt.join("").length; return { objs: [res], code: 0 }; }
        const prop = a.get("property") ?? a.pos[0]; if (prop !== undefined) { const vals = r.map((x) => Number(x[fmtVal(prop)]) || 0); if (a.get("sum")) o.Sum = vals.reduce((s, v) => s + v, 0); if (a.get("average")) o.Average = vals.length ? vals.reduce((s, v) => s + v, 0) / vals.length : 0; if (a.get("maximum")) o.Maximum = Math.max(...vals); if (a.get("minimum")) o.Minimum = Math.min(...vals); }
        return { objs: [o], code: 0 };
      },
      "group-object"(a, input) {
        const prop = a.get("property") ?? a.pos[0]; const m = new Map();
        for (const x of input || []) { const k = fmtVal(prop !== undefined && isPSObj(x) ? x[fmtVal(prop)] : x); if (!m.has(k)) m.set(k, []); m.get(k).push(x); }
        return { objs: [...m].map(([k, g]) => (a.get("noelement") ? { Count: g.length, Name: k } : { Count: g.length, Name: k, Group: g })), code: 0 };
      },
      "where-object"(a, input, du) {
        const b = a.pos.find((x) => x && x._block !== undefined);
        if (b) return { objs: (input || []).filter((x) => evalBlock(b._block, x)), code: 0 };
        const [prop, ...rest] = a.pos; const opName = Object.keys(a.named)[0]; const val = a.named[opName];
        return { objs: (input || []).filter((x) => evalBlock(`$_.${fmtVal(prop)} -${opName} ${typeof val === "number" ? val : "'" + fmtVal(val) + "'"}`, x)), code: 0 };
      },
      "foreach-object"(a, input) { const b = a.pos.find((x) => x && x._block !== undefined); if (!b) { const p = fmtVal(a.pos[0]); return { objs: (input || []).map((x) => x[p]), code: 0 }; } const res = []; for (const x of input || []) { const r = evalBlock(b._block, x); if (Array.isArray(r)) res.push(...r); else if (r !== undefined && r !== "") res.push(r); } return { objs: res, code: 0 }; },
      "format-table"(a, input) { return { objs: input || [], code: 0 }; },
      "format-list"(a, input) { const lines = []; for (const o of input || []) { lines.push(""); if (!isPSObj(o)) { lines.push(String(o)); continue; } const ks = o instanceof PSItem ? ["Name", "Length", "LastWriteTime", "FullName"] : Object.keys(o).filter((k) => !k.startsWith("_")); const w = Math.max(...ks.map((k) => k.length)); for (const k of ks) lines.push(`${k.padEnd(w)} : ${fmtVal(o[k])}`); } return { objs: lines, code: 0 }; },
      "get-command"(a) { const n = fmtVal(a.get("name") ?? a.pos[0] ?? ""); const low = n.toLowerCase(); if (PS[low] || PS[PS_ALIASES[low]]) return { objs: [{ CommandType: PS_ALIASES[low] ? "Alias" : "Cmdlet", Name: PS_ALIASES[low] ? `${n} -> ${PS_ALIASES[low].replace(/(^|-)\w/g, (c) => c.toUpperCase())}` : n, Source: "Microsoft.PowerShell.Management" }], code: 0 }; if (["npm", "node", "git"].includes(low)) return { objs: [{ CommandType: "Application", Name: low + ".exe", Source: "C:\\Program Files\\nodejs\\" + low + ".exe" }], code: 0 }; return PSERR("Get-Command", `The term '${n}' is not recognized as a name of a cmdlet, function, script file, or executable program.`, "cette commande n'existe pas (ou n'est pas dans le PATH)."); },
      "get-process"(a) { const n = a.get("name") ?? a.pos[0]; const id = a.get("id"); let l = S.procs.filter((p) => p.user !== "root" || true); if (n !== undefined) l = l.filter((p) => globToRe(fmtVal(n), "i").test(p.nom)); if (id !== undefined) l = l.filter((p) => String(p.pid) === String(id)); if ((n !== undefined || id !== undefined) && !l.length) return PSERR("Get-Process", `Cannot find a process with the ${id !== undefined ? "process identifier " + id : 'name "' + fmtVal(n) + '"'}. Verify the process name and call the cmdlet again.`); return { objs: l.map((p) => ({ Id: p.pid, ProcessName: p.nom, CPU: Number(((p.pid % 9) / 3).toFixed(2)) })), code: 0 }; },
      "stop-process"(a, input) { const ids = [].concat(a.get("id") ?? a.pos[0] ?? (input || []).map((x) => x.Id ?? x.OwningProcess)).filter((x) => x !== undefined); const n = a.get("name"); let code = 0; if (n !== undefined) { const before = S.procs.length; S.procs = S.procs.filter((p) => !(p.user === "ana" && globToRe(fmtVal(n), "i").test(p.nom))); if (before === S.procs.length) { PSERR("Stop-Process", `Cannot find a process with the name "${fmtVal(n)}".`); code = 1; } } for (const id of ids) { const i = S.procs.findIndex((p) => String(p.pid) === String(id)); if (i < 0) { PSERR("Stop-Process", `Cannot find a process with the process identifier ${id}.`); code = 1; continue; } S.procs.splice(i, 1); } return { objs: [], code }; },
      "get-nettcpconnection"(a) { const port = a.get("localport"); const l = S.procs.filter((p) => p.port && (port === undefined || String(p.port) === String(port))); if (!l.length) return PSERR("Get-NetTCPConnection", "No matching MSFT_NetTCPConnection objects found by CIM query for instances of the ROOT/StandardCimv2/MSFT_NetTCPConnection class on the  CIM server: SELECT * FROM MSFT_NetTCPConnection  WHERE ((LocalPort = " + port + ")). Verify query parameters and retry.", "aucun programme n'écoute sur ce port."); return { objs: l.map((p) => ({ LocalAddress: "::", LocalPort: p.port, RemoteAddress: "::", RemotePort: 0, State: "Listen", OwningProcess: p.pid })), code: 0 }; },
      "invoke-restmethod"(a) { const url = fmtVal(a.get("uri") ?? a.pos[0] ?? ""); const port = (url.match(/:(\d+)/) || [])[1] || "80"; if (/localhost|127\.0\.0\.1/.test(url)) { const p = portOwner(port); if (!p) return PSERR("Invoke-RestMethod", `No connection could be made because the target machine actively refused it. (localhost:${port})`, `aucun programme n'écoute sur le port ${port}.`); return { objs: [p.response || "OK"], code: 0 }; } out("(simulation : pas d'accès à Internet dans l'atelier)", "dim"); return { objs: [], code: 0 }; },
      "invoke-webrequest"(a) { const r = PS["invoke-restmethod"](a); return r.code ? r : { objs: [{ StatusCode: 200, StatusDescription: "OK", Content: r.objs[0] }], code: 0 }; },
      "get-executionpolicy"() { return { objs: [S.policy], code: 0 }; },
      "set-executionpolicy"(a) { const p = fmtVal(a.get("executionpolicy") ?? a.pos[0] ?? ""); if (!/^(RemoteSigned|Unrestricted|Bypass|AllSigned|Restricted)$/i.test(p)) return PSERR("Set-ExecutionPolicy", `Cannot bind parameter 'ExecutionPolicy'. Cannot convert value "${p}".`); S.policy = p.replace(/^\w/, (c) => c.toUpperCase()); return { objs: [], code: 0 }; },
      "get-history"() { return { objs: T.map((e, i) => ({ Id: i + 1, CommandLine: e.cmd })), code: 0 }; },
      "clear-host"() { if (cur) cur.clear = true; return { objs: [], code: 0 }; },
      "get-date"() { return { objs: ["lundi 16 novembre 2026 09:00:00"], code: 0 }; },
      "get-help"(a) { out(`(simulation) Aide de ${fmtVal(a.pos[0] || "")} : Get-Help ${fmtVal(a.pos[0] || "")} -Online ouvre la documentation Microsoft.`, "dim"); return { objs: [], code: 0 }; },
      "get-item"(a) { const t = fmtVal(a.get("path") ?? a.pos[0]); if (/^env:/i.test(t)) { const k = Object.keys(S.env).find((x) => x.toLowerCase() === t.slice(4).toLowerCase()); if (!k) return PSERR("Get-Item", `Cannot find path '${t}' because it does not exist.`); return { objs: [{ Name: k, Value: S.env[k] }], code: 0 }; } const r = itemsAt(t); return { objs: r.map(({ p, n }) => new PSItem(p, n)), code: r.length ? 0 : 1 }; },
      bash() { S.mode = "bash"; S.cwd = canon(HOME_BASH); out("(simulation : retour à bash)", "dim"); return { objs: [], code: 0 }; },
      exit() { return { objs: [], code: 0 }; },
      "get-alias"(a) { const n = a.get("name") ?? a.pos[0]; const l = Object.entries(PS_ALIASES).filter(([k]) => n === undefined || k === fmtVal(n).toLowerCase()); return { objs: l.map(([k, v]) => ({ CommandType: "Alias", Name: `${k} -> ${v.replace(/(^|-)\w/g, (c) => c.toUpperCase())}` })), code: 0 }; },
    };
    PS.md = PS.mkdir;

    /* ---------- exécution d'un script (une commande par ligne, affichée avec son invite) ---------- */
    function prompt() { return S.mode === "pwsh" ? `PS ${show(S.cwd)}> ` : `ana@atelier:${tildify(S.cwd)}$ `; }
    function runLine(line, how) {
      if (how === "bash-sub") return execSource(line, { args: [] });
      if (S.mode === "pwsh") {
        if (/^(bash|wsl)$/i.test(line.trim())) { S.mode = "bash"; S.cwd = canon(HOME_BASH); return 0; }
        return runPS(line);
      }
      return execSource(line, { args: [] });
    }
    function interact(line) {
      const entry = { cmd: line, out: [], code: 0, mode: S.mode, prompt: prompt() };
      T.push(entry); const saved = cur; cur = entry;
      try { entry.code = runLine(line); } catch (e) { out(String(e && e.message || e), "err"); entry.code = 1; } finally { cur = saved; }
      S.lastCode = entry.code;
      return entry;
    }
    function scriptStatements(text, mode) {
      if (mode === "pwsh") {
        const res = []; let buf = "", depth = 0;
        for (const l of text.replace(/\r/g, "").split("\n")) { const t = l.trim(); if (!buf && (!t || t.startsWith("#"))) continue; buf += (buf ? "\n" : "") + l; depth += (l.match(/\{/g) || []).length - (l.match(/\}/g) || []).length; if (depth <= 0 && !/`$/.test(t)) { res.push(buf); buf = ""; depth = 0; } }
        if (buf) res.push(buf); return res;
      }
      return splitStatements(text);
    }

    /* ---------- rendu : terminal interactif ---------- */
    const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
    let histIdx = null;
    function render() {
      if (!root) return;
      let startAt = 0; T.forEach((e, i) => { if (e.clear) startAt = i + 1; });
      const lines = T.slice(startAt).map((e) => `<div class="ts-e"><span class="ts-p ${e.mode}">${esc(e.prompt)}</span><span class="ts-c">${esc(e.cmd)}</span>${e.out.length ? "\n" + e.out.map((o) => `<span class="${o.cls ? "ts-" + o.cls : ""}">${esc(o.text)}</span>`).join("\n") : ""}</div>`).join("");
      root.innerHTML = `<style>
        html,body{margin:0;height:100%}
        .ts{background:#0f1420;color:#d7dce6;font:13px/1.5 ui-monospace,SFMono-Regular,"JetBrains Mono",Menlo,monospace;height:100vh;box-sizing:border-box;display:flex;flex-direction:column}
        .ts-bar{display:flex;align-items:center;gap:8px;padding:6px 10px;background:#1a2130;color:#9aa4b5;font:12px system-ui,sans-serif;border-bottom:1px solid #263044}
        .ts-bar b{color:#e5e9f0;font-weight:600}.ts-dot{width:9px;height:9px;border-radius:50%;background:#3a4559}.ts-bar .sp{flex:1}
        .ts-body{flex:1;overflow:auto;padding:10px 12px;white-space:pre-wrap;word-break:break-word}
        .ts-e{margin-bottom:2px}.ts-p.bash{color:#7ee787}.ts-p.pwsh{color:#79c0ff}.ts-c{color:#f0f3f6}
        .ts-err{color:#ff8b8b}.ts-hint{color:#e3b341;font-family:system-ui,sans-serif;font-size:12.5px}.ts-dim{color:#7d8899}.ts-dir{color:#79c0ff;font-weight:600}.ts-exe{color:#7ee787}
        .ts-in{display:flex;align-items:flex-start}.ts-in input{flex:1;background:transparent;border:0;outline:0;color:#f0f3f6;font:inherit;padding:0;caret-color:#7ee787}
        .ts-help{color:#7d8899;font:12px system-ui,sans-serif;padding:5px 12px;border-top:1px solid #263044;background:#121826}
      </style><div class="ts"><div class="ts-bar"><span class="ts-dot"></span><span class="ts-dot"></span><span class="ts-dot"></span><span class="sp"></span><b>${S.mode === "pwsh" ? "PowerShell (Windows)" : "bash (Linux / macOS)"}</b><span class="sp"></span><span>simulé</span></div>
      <div class="ts-body" id="ts-body">${lines}<div class="ts-in"><span class="ts-p ${S.mode}">${esc(prompt())}</span><input id="ts-input" autocomplete="off" autocapitalize="off" spellcheck="false" aria-label="Commande"></div></div>
      <div class="ts-help">Tape une commande puis Entrée · ↑ ↓ historique · Tab complète · ${S.mode === "pwsh" ? "bash : passer en Linux" : "pwsh : passer en PowerShell"}</div></div>`;
      const body = root.querySelector("#ts-body"); body.scrollTop = body.scrollHeight;
      const input = root.querySelector("#ts-input");
      input.addEventListener("keydown", onKey);
      body.addEventListener("click", () => { if (!String(getSelection())) input.focus(); });
    }
    function onKey(e) {
      const input = e.target;
      if (e.key === "Enter") { const v = input.value; histIdx = null; if (v.trim()) { interact(v); post && post({ type: "console", level: "info", text: (S.mode === "pwsh" ? "PS> " : "$ ") + v }); } else T.push({ cmd: "", out: [], code: 0, mode: S.mode, prompt: prompt() }); render(); root.querySelector("#ts-input").focus(); e.preventDefault(); return; }
      if (e.key === "ArrowUp" || e.key === "ArrowDown") { const cmds = T.map((x) => x.cmd).filter(Boolean); if (!cmds.length) return; histIdx = histIdx === null ? cmds.length : histIdx; histIdx = Math.max(0, Math.min(cmds.length, histIdx + (e.key === "ArrowUp" ? -1 : 1))); input.value = cmds[histIdx] || ""; e.preventDefault(); return; }
      if (e.key === "Tab") { e.preventDefault(); input.value = complete(input.value); return; }
      if (e.key === "l" && e.ctrlKey) { e.preventDefault(); T.push({ cmd: "", out: [], code: 0, mode: S.mode, prompt: prompt(), clear: true }); render(); root.querySelector("#ts-input").focus(); }
    }
    function complete(v) {
      const m = v.match(/^(.*?)([^\s'"]*)$/); const before = m[1], word = m[2];
      const isFirst = !before.trim();
      const sepRe = S.mode === "pwsh" ? /[\\/]/ : /\//;
      const k = Math.max(word.lastIndexOf("/"), S.mode === "pwsh" ? word.lastIndexOf("\\") : -1);
      const dirPart = k >= 0 ? word.slice(0, k + 1) : ""; const prefix = k >= 0 ? word.slice(k + 1) : word;
      let cands = [];
      if (isFirst && !dirPart) cands = (S.mode === "pwsh" ? Object.keys(PS).concat(Object.keys(PS_ALIASES)).map((c) => c.replace(/(^|-)\w/g, (x) => x.toUpperCase())) : Object.keys(BASH)).filter((c) => c.toLowerCase().startsWith(prefix.toLowerCase()));
      const d = lookup(abs(dirPart || ".")); if (d && d.type === "dir") cands = cands.concat([...d.children.keys()].filter((n) => (S.mode === "pwsh" ? n.toLowerCase().startsWith(prefix.toLowerCase()) : n.startsWith(prefix)) && (prefix.startsWith(".") || !n.startsWith("."))).map((n) => n + (d.children.get(n).type === "dir" ? (S.mode === "pwsh" ? "\\" : "/") : "")));
      if (!cands.length) return v;
      if (cands.length === 1) { const c = cands[0]; const needQ = /\s/.test(c) && S.mode === "bash"; return before + dirPart + (needQ ? c.replace(/ /g, "\\ ") : c) + (/[\\/]$/.test(c) ? "" : " "); }
      let common = cands[0]; for (const c of cands) while (!c.toLowerCase().startsWith(common.toLowerCase())) common = common.slice(0, -1);
      if (common.length > prefix.length) return before + dirPart + common;
      T.push({ cmd: v, out: [{ text: cands.join("   "), cls: "dim" }], code: 0, mode: S.mode, prompt: prompt() }); render(); const inp = root.querySelector("#ts-input"); inp.value = v; inp.focus();
      return v;
    }

    /* ---------- API ---------- */
    const t = {
      // préparation du scénario (chemins relatifs au dossier personnel, en notation /)
      fichier(p, content, exec) { const full = norm(home() + "/" + p); mkdirp(parentOf(full)[0]); writeFile(full, content == null ? "" : content); if (exec) lookup(full).exec = true; return t; },
      dossier(p) { mkdirp(norm(home() + "/" + p)); return t; },
      cd(p) { S.cwd = canon(norm(p.startsWith("/") ? p : home() + "/" + p)); return t; },
      outil(nom, sortie) { const p = "/usr/local/bin/" + nom; mkdirp("/usr/local/bin"); writeFile(p, `echo "${sortie.replace(/"/g, '\\"')}"`); lookup(p).exec = true; return t; },
      processus(nom, cmd, port, reponse) { const pid = S.nextPid; S.nextPid += 37; S.procs.push({ pid, nom, cmd: cmd || nom, user: "ana", port: port || null, response: reponse || "OK" }); return pid; },
      env(k, v) { S.env[k] = v; S.exported.add(k); return t; },
      mode(m) { S.mode = m; const h = home(); mkdirp(h); S.cwd = h; S.env.HOME = m === "pwsh" ? show(HOME_PS) : HOME_BASH; return t; },
    };
    const api = {
      setMode(m) { t.mode(m); render(); },
      ecrire(p, content) { writeFile(norm(S.cwd + "/" + p.replace(/\\/g, "/")), content); const full = norm(S.cwd + "/" + p.replace(/\\/g, "/")); if (/\.sh$/.test(p) && /^#!/.test(content)) { const n = lookup(full); if (n) n.exec = false; } },
      setup(fn) { const savedQ = quiet; quiet = true; try { fn(t); } finally { quiet = savedQ; } render(); },
      script(text, mode) {
        if (mode && mode !== S.mode) t.mode(mode);
        for (const st of scriptStatements(text || "", S.mode)) interact(st.trim());
        render();
        const f = T.filter((e) => e.code !== 0);
        post && post({ type: "console", level: f.length ? "warn" : "info", text: T.length + " commande(s) exécutée(s)" + (f.length ? `, ${f.length} en erreur : ` + f.map((e) => e.cmd.split("\n")[0]).join(" · ") : "") });
        return T.length;
      },
      run(cmd) { const e = interact(cmd); render(); return e.out.filter((o) => o.cls !== "hint").map((o) => o.text).join("\n"); },
      // lecture pour les tests (chemins relatifs au dossier personnel, ou absolus)
      path(p) { return p.startsWith("/") ? norm(p) : norm(home() + "/" + p); },
      exists(p) { const S2 = S.mode; const n = lookup(api.path(p)); return !!n; },
      isDir(p) { const n = lookup(api.path(p)); return !!n && n.type === "dir"; },
      isFile(p) { const n = lookup(api.path(p)); return !!n && n.type === "file"; },
      read(p) { const n = lookup(api.path(p)); return n && n.type === "file" ? n.content : null; },
      ls(p) { const n = lookup(api.path(p || "")); return n && n.type === "dir" ? [...n.children.keys()].sort() : null; },
      tree(p) { const base = api.path(p || ""); const n = lookup(base); const res = []; if (n) walk(base, n, (wp, wn, d) => { if (d) res.push(wp.slice(base.length + 1) + (wn.type === "dir" ? "/" : "")); }); return res; },
      isExec(p) { const n = lookup(api.path(p)); return !!n && !!n.exec; },
      cwd() { return tildify(S.cwd); },
      get mode() { return S.mode; },
      env(k) { return S.env[k]; },
      get policy() { return S.policy; },
      procs() { return S.procs.map((p) => { const o = Object.assign({}, p); delete o.respond; return o; }); },
      get lastCurl() { return S.lastCurl || null; },
      portPid(port) { const p = portOwner(port); return p ? p.pid : null; },
      commands() { return T.map((e) => e.cmd).filter(Boolean); },
      used(re) { return T.some((e) => (re instanceof RegExp ? re.test(e.cmd) : e.cmd.includes(re))); },
      outputOf(re) { const e = [...T].reverse().find((x) => (re instanceof RegExp ? re.test(x.cmd) : x.cmd.includes(re))); return e ? e.out.filter((o) => o.cls !== "hint" && o.cls !== "dim").map((o) => o.text).join("\n") : null; },
      failed() { return T.filter((e) => e.code !== 0).map((e) => e.cmd); },
      get out() { return T.map((e) => e.prompt + e.cmd + "\n" + e.out.map((o) => o.text).join("\n")).join("\n"); },
    };
    mkdirp("/tmp"); mkdirp(HOME_BASH); mkdirp(HOME_PS); mkdirp("/usr/bin");
    window.__term = api;
    render();
    return api;
  };
})();

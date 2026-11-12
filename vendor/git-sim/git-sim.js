/* Git simulé pour l'Atelier de code.
 * Un vrai modèle Git en mémoire : commits (instantanés + parents), branches, HEAD, index, dossier de travail,
 * merge 3-way avec conflits, rebase (et rebase -i via un bloc <<EOF), reset, revert, cherry-pick, stash,
 * tags, reflog, bisect, remote « origin » (fetch, pull, push, --force-with-lease) et Pull Requests (gh pr).
 * Les commandes sont lues dans un script (une par ligne) et le résultat est dessiné : graphe + terminal.
 * Ce n'est pas Git : c'est une maquette fidèle aux concepts, pour s'exercer dans le navigateur.
 */
(function () {
  "use strict";

  window.GitSim = function (ctx) {
    const { root, post } = ctx;
    const S = {
      commits: {}, seq: 0, branches: {}, tags: {}, head: { branch: "main" }, prev: null,
      index: {}, work: {}, unmerged: new Set(), reflog: [], stash: [], remote: null, tracking: {}, upstream: {},
      op: null, author: "toi", bisect: null, origHead: null, prs: [], quiet: false,
    };
    const T = []; // transcript : [{cmd, out, err}]
    let cur = null;

    /* ---------- utilitaires ---------- */
    const keys = (...objs) => [...new Set(objs.flatMap((o) => Object.keys(o || {})))].sort();
    const copy = (o) => Object.assign({}, o);
    const eqTree = (a, b) => keys(a, b).every((k) => a[k] === b[k]);
    const first = (msg) => String(msg).split("\n")[0];
    function hash(str) {
      let h1 = 0x811c9dc5, h2 = 0x9e3779b1;
      for (let i = 0; i < str.length; i++) { const c = str.charCodeAt(i); h1 = Math.imul(h1 ^ c, 16777619) >>> 0; h2 = Math.imul(h2 ^ c, 2246822519) >>> 0; h2 = (h2 ^ (h2 >>> 13)) >>> 0; }
      return (h1.toString(16).padStart(8, "0") + h2.toString(16).padStart(8, "0")).slice(0, 7);
    }
    class GitError extends Error { constructor(msg, status) { super(msg); this.status = status || 1; } }
    const fail = (msg, status) => { throw new GitError(msg, status); };
    const out = (s) => { if (cur) cur.out.push(s); };

    function mk(parents, tree, msg, author) {
      S.seq++;
      let id = hash(S.seq + "|" + parents.join(",") + "|" + msg + "|" + JSON.stringify(tree));
      while (S.commits[id]) id = hash(id + "x");
      S.commits[id] = { id, parents: parents.slice(), tree: copy(tree), msg, author: author || S.author, seq: S.seq };
      return id;
    }
    const C = (id) => S.commits[id];
    const headId = () => (S.head.branch ? S.branches[S.head.branch] : S.head.detached);
    const treeOf = (id) => (id ? C(id).tree : {});
    const headTree = () => treeOf(headId());
    function ancestors(id) {
      const seen = new Set(); const st = id ? [id] : [];
      while (st.length) { const x = st.pop(); if (seen.has(x)) continue; seen.add(x); st.push(...C(x).parents); }
      return seen;
    }
    const isAncestor = (a, b) => !!a && !!b && ancestors(b).has(a);
    function mergeBase(a, b) {
      const A = ancestors(a); const common = [...ancestors(b)].filter((x) => A.has(x));
      if (!common.length) return null;
      return common.sort((x, y) => C(y).seq - C(x).seq)[0];
    }
    function setHead(id, why) {
      if (S.head.branch) S.branches[S.head.branch] = id; else S.head.detached = id;
      S.reflog.unshift({ id, msg: why });
    }
    function short(id) { return id ? id.slice(0, 7) : "0000000"; }
    function branchLabel() { return S.head.branch ? S.head.branch : "HEAD"; }

    /* ---------- révisions ---------- */
    function resolve(rev, quiet) {
      if (!rev) fail("fatal: révision vide");
      const m = /^(.*?)((?:[~^]\d*)*)$/.exec(rev);
      let base = m[1]; const suffix = m[2];
      let id;
      if (base === "HEAD" || base === "@") id = headId();
      else if (base === "ORIG_HEAD") id = S.origHead;
      else if (/^HEAD@\{(\d+)\}$/.test(base)) { const n = +/\d+/.exec(base)[0]; id = S.reflog[n] && S.reflog[n].id; }
      else if (/^stash@\{(\d+)\}$/.test(base)) { const n = +/\d+/.exec(base)[0]; id = S.stash[n] && S.stash[n].commit; }
      else if (base in S.branches) id = S.branches[base];
      else if (base.startsWith("refs/heads/") && base.slice(11) in S.branches) id = S.branches[base.slice(11)];
      else if (base.startsWith("origin/") && base.slice(7) in S.tracking) id = S.tracking[base.slice(7)];
      else if (base in S.tags) id = S.tags[base].id;
      else if (/^[0-9a-f]{4,40}$/.test(base)) {
        const c = Object.keys(S.commits).filter((k) => k.startsWith(base.slice(0, 7)) && base.startsWith(k.slice(0, Math.min(7, base.length))));
        if (c.length === 1) id = c[0]; else if (c.length > 1) fail("error: short object ID " + base + " is ambiguous");
      }
      if (!id) { if (quiet) return null; fail("fatal: ambiguous argument '" + rev + "': unknown revision or path not in the working tree."); }
      const re = /([~^])(\d*)/g; let t;
      while ((t = re.exec(suffix))) {
        const n = t[2] === "" ? 1 : +t[2];
        if (t[1] === "~") { for (let i = 0; i < n; i++) { id = C(id).parents[0]; if (!id) fail("fatal: ambiguous argument '" + rev + "': unknown revision"); } }
        else { if (n === 0) continue; id = C(id).parents[n - 1]; if (!id) fail("fatal: ambiguous argument '" + rev + "': unknown revision"); }
      }
      return id;
    }

    /* ---------- .gitignore ---------- */
    function ignored(p) {
      const src = S.work[".gitignore"]; if (!src || p in S.index) return false;
      return src.split("\n").map((l) => l.trim()).filter((l) => l && !l.startsWith("#")).some((pat) => {
        if (pat.endsWith("/")) return p.startsWith(pat) || p.includes("/" + pat);
        const rx = new RegExp("^" + pat.replace(/[.+^${}()|[\]\\]/g, "\\$&").replace(/\*/g, "[^/]*").replace(/\?/g, "[^/]") + "$");
        return rx.test(p) || rx.test(p.split("/").pop());
      });
    }

    /* ---------- état du dossier de travail ---------- */
    function status() {
      const H = headTree(), I = S.index, W = S.work;
      const staged = [], modified = [], untracked = [], unmerged = [...S.unmerged].sort();
      for (const p of keys(H, I)) if (!S.unmerged.has(p) && H[p] !== I[p]) staged.push({ path: p, kind: H[p] === undefined ? "new file" : I[p] === undefined ? "deleted" : "modified" });
      for (const p of keys(I)) if (!S.unmerged.has(p) && W[p] !== I[p]) modified.push({ path: p, kind: W[p] === undefined ? "deleted" : "modified" });
      for (const p of keys(W)) if (!(p in I) && !S.unmerged.has(p) && !ignored(p)) untracked.push(p);
      return { staged, modified, untracked, unmerged };
    }
    const dirtyTracked = () => { const s = status(); return s.staged.length + s.modified.length + s.unmerged.length > 0; };
    function requireClean(what) {
      const s = status();
      if (s.unmerged.length) fail("error: you need to resolve your current index first\n" + s.unmerged.map((p) => p + ": needs merge").join("\n"));
      if (s.staged.length || s.modified.length) {
        const files = [...s.staged, ...s.modified].map((x) => "\t" + x.path);
        fail("error: cannot " + what + ": You have unstaged or staged changes.\n" + [...new Set(files)].join("\n") + "\nerror: Please commit or stash them.\n→ indice : fais un commit ou un `git stash` avant.");
      }
    }
    function checkoutTree(target, verb) {
      const H = headTree(), Tt = treeOf(target);
      const dirty = (p) => S.index[p] !== H[p] || (S.work[p] !== S.index[p] && (p in S.index || p in H));
      const bad = [], badU = [];
      for (const p of keys(H, Tt, S.index, S.work)) {
        if (!(p in S.index) && !(p in H)) { if (p in Tt && S.work[p] !== Tt[p] && p in S.work) badU.push(p); continue; }
        if (dirty(p) && Tt[p] !== H[p]) bad.push(p);
      }
      if (bad.length) fail("error: Your local changes to the following files would be overwritten by " + verb + ":\n" + bad.map((p) => "\t" + p).join("\n") + "\nPlease commit your changes or stash them before you switch branches.\nAborting");
      if (badU.length) fail("error: The following untracked working tree files would be overwritten by " + verb + ":\n" + badU.map((p) => "\t" + p).join("\n") + "\nAborting");
      for (const p of keys(H, Tt, S.index)) {
        if (dirty(p)) continue;
        if (Tt[p] === undefined) { delete S.index[p]; delete S.work[p]; } else { S.index[p] = Tt[p]; S.work[p] = Tt[p]; }
      }
    }
    function hardTo(id) {
      const H = headTree(), Tt = treeOf(id);
      for (const p of keys(H, S.index, Tt)) { if (Tt[p] === undefined) { delete S.index[p]; delete S.work[p]; } else { S.index[p] = Tt[p]; S.work[p] = Tt[p]; } }
      S.unmerged.clear();
    }

    /* ---------- fusion 3-way ---------- */
    const lines = (s) => (s === undefined ? [] : s.split("\n"));
    function mergeFile(b, o, t, lo, lt) {
      if (o === t) return { ok: true, v: o };
      if (b === o) return { ok: true, v: t };
      if (b === t) return { ok: true, v: o };
      if (b !== undefined && o !== undefined && t !== undefined) {
        const B = lines(b), O = lines(o), Tl = lines(t);
        if (B.length === O.length && B.length === Tl.length) {
          const res = []; let conflict = false; let i = 0;
          while (i < B.length) {
            if (O[i] === Tl[i] || B[i] === Tl[i]) { res.push(O[i]); i++; continue; }
            if (B[i] === O[i]) { res.push(Tl[i]); i++; continue; }
            conflict = true; const a = [], c = [];
            while (i < B.length && O[i] !== Tl[i] && B[i] !== O[i] && B[i] !== Tl[i]) { a.push(O[i]); c.push(Tl[i]); i++; }
            res.push("<<<<<<< " + lo, ...a, "=======", ...c, ">>>>>>> " + lt);
          }
          return conflict ? { ok: false, v: res.join("\n") } : { ok: true, v: res.join("\n") };
        }
      }
      if (o === undefined || t === undefined) return { ok: false, v: o === undefined ? t : o, deleted: true };
      const strip = (s) => (s.endsWith("\n") ? s.slice(0, -1) : s);
      return { ok: false, v: "<<<<<<< " + lo + "\n" + strip(o) + "\n=======\n" + strip(t) + "\n>>>>>>> " + lt + "\n" };
    }
    function merge3(B, O, Tt, lo, lt) {
      const tree = {}, work = {}, conflicts = [];
      for (const p of keys(B, O, Tt)) {
        const r = mergeFile(B[p], O[p], Tt[p], lo, lt);
        if (r.ok) { if (r.v !== undefined) { tree[p] = r.v; work[p] = r.v; } }
        else { conflicts.push({ path: p, deleted: !!r.deleted }); if (O[p] !== undefined) tree[p] = O[p]; work[p] = r.v; }
      }
      return { tree, work, conflicts };
    }
    function applyMerge(res) {
      const H = headTree();
      for (const p of keys(H, S.index)) { if (!(p in res.tree)) delete S.index[p]; if (!(p in res.work)) delete S.work[p]; }
      for (const p of Object.keys(res.tree)) S.index[p] = res.tree[p];
      for (const p of Object.keys(res.work)) S.work[p] = res.work[p];
      S.unmerged = new Set(res.conflicts.map((c) => c.path));
    }
    function reportConflicts(res) {
      for (const c of res.conflicts) out(c.deleted ? "CONFLICT (modify/delete): " + c.path + " deleted in one branch and modified in the other." : "Auto-merging " + c.path + "\nCONFLICT (content): Merge conflict in " + c.path);
    }

    /* ---------- commits ---------- */
    function changedCount(a, b) { return keys(a, b).filter((k) => a[k] !== b[k]).length; }
    function commitIndex(msg, parents, why, author) {
      const id = mk(parents, S.index, msg, author);
      const before = parents[0] ? treeOf(parents[0]) : {};
      setHead(id, why + ": " + first(msg));
      return { id, n: changedCount(before, S.index) };
    }
    function patchOf(id) {
      const c = C(id); const p = treeOf(c.parents[0]);
      const d = {}; for (const k of keys(p, c.tree)) if (p[k] !== c.tree[k]) d[k] = [p[k], c.tree[k]];
      return JSON.stringify(d);
    }
    function pick(id, msg, author) {
      const c = C(id);
      if (c.parents.length > 1) fail("error: commit " + short(id) + " is a merge but no -m option was given.");
      const res = merge3(treeOf(c.parents[0]), headTree(), c.tree, "HEAD", short(id) + " (" + first(c.msg) + ")");
      applyMerge(res);
      if (res.conflicts.length) { reportConflicts(res); return "conflict"; }
      if (eqTree(S.index, headTree())) return "empty";
      commitIndex(msg || c.msg, [headId()].filter(Boolean), "commit", author || c.author);
      return "ok";
    }

    /* ---------- rebase ---------- */
    function rangeCommits(fromExcl, to) {
      const ex = ancestors(fromExcl);
      return [...ancestors(to)].filter((x) => !ex.has(x)).sort((a, b) => C(a).seq - C(b).seq);
    }
    function startRebase(onto, todo, interactive) {
      requireClean("rebase");
      const orig = headId();
      S.origHead = orig;
      S.op = { type: "rebase", branch: S.head.branch, orig, onto, todo, interactive };
      checkoutTree(onto, "checkout");
      S.head = { detached: onto }; S.reflog.unshift({ id: onto, msg: "rebase (start): checkout " + short(onto) });
      return rebaseLoop();
    }
    function rebaseLoop() {
      const op = S.op;
      while (op.todo.length) {
        const step = op.todo.shift(); op.current = step;
        const c = C(step.id);
        if (step.action === "drop") continue;
        if (step.action === "pick" || step.action === "reword") {
          const r = pick(step.id, step.msg || c.msg, c.author);
          if (r === "conflict") return rebaseStop(step);
          if (r === "empty") { out("dropping " + short(step.id) + " " + first(c.msg) + " -- patch contents already upstream"); continue; }
        } else if (step.action === "squash" || step.action === "fixup") {
          const prev = headId();
          if (!prev || prev === op.onto) fail("error: cannot '" + step.action + "' without a previous commit");
          const r = pick(step.id, c.msg, c.author);
          if (r === "conflict") return rebaseStop(step);
          combine(prev, step);
        }
      }
      return finishRebase();
    }
    function combine(prev, step) {
      const p = C(prev); const now = headId();
      const msg = step.msg || (step.action === "fixup" ? p.msg : p.msg + "\n\n" + C(step.id).msg);
      const id = mk(p.parents, treeOf(now), msg, p.author);
      S.head = { detached: id }; S.reflog.unshift({ id, msg: "rebase (" + step.action + "): " + first(msg) });
    }
    function rebaseStop(step) {
      S.op.stoppedOn = headId();
      out("error: could not apply " + short(step.id) + "... " + first(C(step.id).msg));
      out("hint: Resolve all conflicts manually, mark them as resolved with\nhint: \"git add/rm <conflicted_files>\", then run \"git rebase --continue\".\nhint: To abort and get back to the state before \"git rebase\", run \"git rebase --abort\".");
      return 1;
    }
    function finishRebase() {
      const op = S.op; const id = headId();
      if (op.branch) { S.branches[op.branch] = id; S.head = { branch: op.branch }; S.reflog.unshift({ id, msg: "rebase (finish): returning to refs/heads/" + op.branch }); }
      S.op = null;
      out("Successfully rebased and updated " + (op.branch ? "refs/heads/" + op.branch : "detached HEAD") + ".");
      return 0;
    }
    function rebaseContinue() {
      const op = S.op; const step = op.current;
      if (S.unmerged.size) fail("error: Committing is not possible because you have unmerged files.\nhint: Fix them up in the work tree, and then use 'git add/rm <file>'");
      if (step && headId() === op.stoppedOn) {
        if (eqTree(S.index, headTree())) out("(changement vide : commit ignoré)");
        else if (step.action === "squash" || step.action === "fixup") { const prev = headId(); commitIndex(C(step.id).msg, [prev], "commit", C(step.id).author); combine(prev, step); }
        else commitIndex(step.msg || C(step.id).msg, [headId()], "commit", C(step.id).author);
      }
      return rebaseLoop();
    }
    function parseTodo(body, list) {
      const todo = [];
      for (const raw of body) {
        const line = raw.trim(); if (!line || line.startsWith("#")) continue;
        const tk = tokenize(line)[0] || [];
        const map = { p: "pick", r: "reword", s: "squash", f: "fixup", d: "drop" };
        const action = map[tk[0]] || tk[0];
        if (!["pick", "reword", "squash", "fixup", "drop"].includes(action)) fail("error: invalid command '" + tk[0] + "' (attendu : pick, reword, squash, fixup, drop)");
        let msg = null; const rest = [];
        for (let i = 1; i < tk.length; i++) { if (tk[i] === "-m") { msg = tk[++i]; continue; } rest.push(tk[i]); }
        let id = null;
        if (rest[0] && /^[0-9a-f]{4,}$/.test(rest[0])) id = list.find((x) => x.startsWith(rest[0].slice(0, 7)));
        if (!id) { const txt = rest.join(" "); id = list.find((x) => first(C(x).msg) === txt) || list.find((x) => txt && first(C(x).msg).includes(txt)); }
        if (!id) fail("error: could not parse '" + line + "' : commit introuvable dans la liste à rebaser");
        if (action === "reword" && !msg) fail("error: reword sans message : dans l'atelier, ajoute -m \"nouveau message\" sur la ligne");
        todo.push({ action, id, msg });
      }
      return todo;
    }

    /* ---------- commandes git ---------- */
    function opts(args, spec) {
      // spec : { "-m": "multi", "-b": "value", "--amend": "flag" }
      const o = { _: [] };
      for (let i = 0; i < args.length; i++) {
        const a = args[i];
        const eq = /^(--[a-z-]+)=(.*)$/.exec(a);
        if (eq && spec[eq[1]]) { o[eq[1]] = spec[eq[1]] === "multi" ? (o[eq[1]] || []).concat(eq[2]) : eq[2]; continue; }
        if (spec[a] === "flag") o[a] = true;
        else if (spec[a] === "value") o[a] = args[++i];
        else if (spec[a] === "multi") (o[a] = o[a] || []).push(args[++i]);
        else if (/^-[a-zA-Z]{2,}$/.test(a) && [...a.slice(1)].every((ch) => spec["-" + ch])) {
          const chars = [...a.slice(1)];
          chars.forEach((ch, k) => { const f = "-" + ch; if (spec[f] === "flag") o[f] = true; else if (k === chars.length - 1) { if (spec[f] === "multi") (o[f] = o[f] || []).push(args[++i]); else o[f] = args[++i]; } });
        }
        else if (a.startsWith("-") && a !== "-" && !/^-\d+$/.test(a)) fail("error: unknown option `" + a.replace(/^-+/, "") + "'");
        else o._.push(a);
      }
      return o;
    }
    function pathsMatch(spec, all) {
      if (spec === "." || spec === "-A") return all;
      const p = spec.replace(/\/$/, "");
      return all.filter((k) => k === p || k.startsWith(p + "/"));
    }

    const git = {
      init(a) {
        const o = opts(a, { "-b": "value", "--initial-branch": "value" });
        Object.assign(S, { commits: {}, branches: {}, tags: {}, head: { branch: o["-b"] || o["--initial-branch"] || "main" }, index: {}, work: S.work, unmerged: new Set(), reflog: [], stash: [], op: null });
        out("Initialized empty Git repository in /atelier/.git/");
      },
      config(a) { const k = a.filter((x) => !x.startsWith("--")); if (k[0] === "user.name" && k[1]) S.author = k[1]; },
      status(a) {
        const o = opts(a, { "-s": "flag", "--short": "flag", "-sb": "flag" });
        const s = status();
        if (o["-s"] || o["--short"]) {
          for (const p of s.unmerged) out("UU " + p);
          const map = {}; for (const x of s.staged) map[x.path] = (x.kind === "new file" ? "A" : x.kind === "deleted" ? "D" : "M") + " ";
          for (const x of s.modified) map[x.path] = (map[x.path] || "  ").slice(0, 1) + (x.kind === "deleted" ? "D" : "M");
          for (const p of Object.keys(map).sort()) out(map[p] + " " + p);
          for (const p of s.untracked) out("?? " + p);
          return;
        }
        out(S.head.branch ? "On branch " + S.head.branch : "HEAD detached at " + short(headId()));
        const up = S.head.branch && S.tracking[S.head.branch] && S.upstream[S.head.branch];
        if (up) {
          const l = headId(), r = S.tracking[S.head.branch];
          const ahead = rangeCommits(r, l).length, behind = rangeCommits(l, r).length;
          if (!ahead && !behind) out("Your branch is up to date with 'origin/" + S.head.branch + "'.");
          else if (ahead && !behind) out("Your branch is ahead of 'origin/" + S.head.branch + "' by " + ahead + " commit" + (ahead > 1 ? "s" : "") + ".\n  (use \"git push\" to publish your local commits)");
          else if (!ahead) out("Your branch is behind 'origin/" + S.head.branch + "' by " + behind + " commit" + (behind > 1 ? "s" : "") + ", and can be fast-forwarded.\n  (use \"git pull\" to update your local branch)");
          else out("Your branch and 'origin/" + S.head.branch + "' have diverged,\nand have " + ahead + " and " + behind + " different commits each, respectively.");
        }
        if (S.op && S.op.type === "rebase") out("interactive rebase in progress; onto " + short(S.op.onto) + "\nYou are currently rebasing" + (S.op.branch ? " branch '" + S.op.branch + "'" : "") + " on '" + short(S.op.onto) + "'.\n  (fix conflicts and then run \"git rebase --continue\")");
        if (S.op && S.op.type === "merge") out(s.unmerged.length ? "You have unmerged paths.\n  (fix conflicts and run \"git commit\")\n  (use \"git merge --abort\" to abort the merge)" : "All conflicts fixed but you are still merging.\n  (use \"git commit\" to conclude merge)");
        if (S.op && S.op.type === "cherry-pick") out("You are currently cherry-picking.\n  (fix conflicts and run \"git cherry-pick --continue\")");
        if (S.op && S.op.type === "revert") out("You are currently reverting.\n  (fix conflicts and run \"git revert --continue\")");
        if (S.bisect) out("You are currently bisecting.");
        if (!headId()) out("\nNo commits yet");
        if (s.staged.length) out("\nChanges to be committed:\n" + s.staged.map((x) => "\t" + (x.kind + ":").padEnd(12) + x.path).join("\n"));
        if (s.unmerged.length) out("\nUnmerged paths:\n  (use \"git add <file>...\" to mark resolution)\n" + s.unmerged.map((p) => "\tboth modified:   " + p).join("\n"));
        if (s.modified.length) out("\nChanges not staged for commit:\n" + s.modified.map((x) => "\t" + (x.kind + ":").padEnd(12) + x.path).join("\n"));
        if (s.untracked.length) out("\nUntracked files:\n" + s.untracked.map((p) => "\t" + p).join("\n"));
        if (!s.staged.length && !s.modified.length && !s.unmerged.length) out(s.untracked.length ? "\nnothing added to commit but untracked files present (use \"git add\" to track)" : "nothing to commit, working tree clean");
      },
      add(a) {
        const o = opts(a, { "-A": "flag", "--all": "flag", "-u": "flag", "-f": "flag", "--force": "flag" });
        const force = o["-f"] || o["--force"];
        let specs = o._;
        if (o["-A"] || o["--all"]) specs = ["."];
        if (o["-u"]) specs = specs.length ? specs : ["."];
        if (!specs.length) fail("Nothing specified, nothing added.\nhint: Maybe you wanted to say 'git add .'?");
        for (const sp of specs) {
          let all = keys(S.work, S.index);
          if (o["-u"]) all = all.filter((p) => p in S.index);
          let ps = pathsMatch(sp, all);
          if (!force) {
            const ign = ps.filter((p) => ignored(p));
            if (ign.length && ps.length === 1 && ps[0] === sp) fail("The following paths are ignored by one of your .gitignore files:\n" + ign.join("\n") + "\nhint: Use -f if you really want to add them.");
            ps = ps.filter((p) => !ignored(p));
          }
          if (!ps.length && sp !== "." && !pathsMatch(sp, all).length) fail("fatal: pathspec '" + sp + "' did not match any files");
          for (const p of ps) { if (p in S.work) S.index[p] = S.work[p]; else delete S.index[p]; S.unmerged.delete(p); }
        }
      },
      rm(a) {
        const o = opts(a, { "--cached": "flag", "-r": "flag", "-f": "flag" });
        for (const sp of o._) {
          const ps = pathsMatch(sp, keys(S.index));
          if (!ps.length) fail("fatal: pathspec '" + sp + "' did not match any files");
          for (const p of ps) { delete S.index[p]; S.unmerged.delete(p); if (!o["--cached"]) delete S.work[p]; out("rm '" + p + "'"); }
        }
      },
      mv(a) {
        const [x, y] = a; if (!(x in S.index)) fail("fatal: not under version control, source=" + x);
        S.work[y] = S.work[x]; delete S.work[x]; S.index[y] = S.index[x]; delete S.index[x];
      },
      commit(a) {
        const o = opts(a, { "-m": "multi", "--message": "multi", "-a": "flag", "--all": "flag", "--amend": "flag", "--no-edit": "flag", "--allow-empty": "flag", "--fixup": "value" });
        if (o["-a"] || o["--all"]) for (const p of keys(S.index)) { if (p in S.work) S.index[p] = S.work[p]; else delete S.index[p]; S.unmerged.delete(p); }
        if (S.unmerged.size) fail("error: Committing is not possible because you have unmerged files.\nhint: Fix them up in the work tree, and then use 'git add/rm <file>'\nfatal: Exiting because of an unresolved conflict.");
        const ms = (o["-m"] || []).concat(o["--message"] || []);
        let msg = ms.length ? ms.join("\n\n") : null;
        const h = headId();
        if (o["--fixup"]) msg = "fixup! " + first(C(resolve(o["--fixup"])).msg);
        if (o["--amend"]) {
          if (!h) fail("fatal: You have nothing to amend.");
          if (!msg) { if (o["--no-edit"]) msg = C(h).msg; else fail("Aborting commit due to empty commit message.\n→ indice : dans l'atelier, donne le message avec -m \"…\" ou garde l'ancien avec --no-edit"); }
          const r = commitIndex(msg, C(h).parents, "commit (amend)", C(h).author);
          out("[" + branchLabel() + " " + short(r.id) + "] " + first(msg) + "\n " + changedCount(treeOf(C(h).parents[0]), S.index) + " file(s) changed");
          return;
        }
        if (!msg && S.op && (S.op.type === "merge" || S.op.type === "cherry-pick" || S.op.type === "revert")) msg = S.op.msg;
        if (!msg && S.op && S.op.type === "rebase" && S.op.current) msg = S.op.current.msg || C(S.op.current.id).msg;
        if (!msg) fail("Aborting commit due to empty commit message.\n→ indice : dans l'atelier, le message se donne avec -m \"…\"");
        const parents = [h].filter(Boolean);
        if (S.op && S.op.type === "merge") parents.push(S.op.theirs);
        if (!(S.op && S.op.type === "merge") && !o["--allow-empty"] && eqTree(S.index, headTree())) {
          const s = status();
          fail(s.modified.length || s.untracked.length ? "no changes added to commit (use \"git add\" and/or \"git commit -a\")" : "nothing to commit, working tree clean");
        }
        const author = S.op && S.op.author;
        const r = commitIndex(msg, parents, S.op && S.op.type === "merge" ? "commit (merge)" : h ? "commit" : "commit (initial)", author);
        if (S.op && S.op.type !== "rebase") S.op = null;
        out("[" + branchLabel() + (h ? "" : " (root-commit)") + " " + short(r.id) + "] " + first(msg) + "\n " + r.n + " file" + (r.n > 1 ? "s" : "") + " changed");
      },
      log(a) {
        const o = opts(a, { "--oneline": "flag", "--graph": "flag", "--all": "flag", "-n": "value", "--decorate": "flag", "--first-parent": "flag", "--author": "value", "--grep": "value", "--format": "value", "--pretty": "value" });
        let n = o["-n"] ? +o["-n"] : Infinity;
        const revs = [];
        for (const x of o._) { if (/^-\d+$/.test(x)) n = +x.slice(1); else revs.push(x); }
        let set;
        if (o["--all"]) set = new Set(allTips().flatMap((t) => [...ancestors(t)]));
        else if (revs.length && revs[0].includes("..")) { const [x, y] = revs[0].split(".."); set = new Set(rangeCommits(resolve(x || "HEAD"), resolve(y || "HEAD"))); }
        else if (o["--first-parent"]) { set = new Set(); let x = resolve(revs[0] || "HEAD"); while (x) { set.add(x); x = C(x).parents[0]; } }
        else { const h = revs.length ? resolve(revs[0]) : headId(); if (!h) fail("fatal: your current branch '" + S.head.branch + "' does not have any commits yet"); set = ancestors(h); }
        let list = [...set].sort((x, y) => C(y).seq - C(x).seq);
        if (o["--author"]) list = list.filter((x) => C(x).author.includes(o["--author"]));
        if (o["--grep"]) list = list.filter((x) => C(x).msg.includes(o["--grep"]));
        list = list.slice(0, n);
        const fmt = o["--format"] || o["--pretty"];
        for (const id of list) {
          const c = C(id); const dec = decorations(id);
          if (fmt === "%s") out(first(c.msg));
          else if (o["--oneline"] || fmt === "oneline") out((o["--graph"] ? "* " : "") + short(id) + (dec ? " (" + dec + ")" : "") + " " + first(c.msg));
          else out("commit " + id + (dec ? " (" + dec + ")" : "") + (c.parents.length > 1 ? "\nMerge: " + c.parents.map(short).join(" ") : "") + "\nAuthor: " + c.author + "\n\n" + c.msg.split("\n").map((l) => "    " + l).join("\n") + "\n");
        }
      },
      show(a) {
        const id = resolve(a[0] || "HEAD"); const c = C(id);
        out("commit " + id + "\nAuthor: " + c.author + "\n\n" + c.msg.split("\n").map((l) => "    " + l).join("\n") + "\n");
        diffTrees(treeOf(c.parents[0]), c.tree);
      },
      diff(a) {
        const o = opts(a, { "--staged": "flag", "--cached": "flag", "--stat": "flag", "--name-only": "flag" });
        let A, B;
        if (o._.length >= 1 && !(o._[0] in S.work)) { const r = o._[0].includes("..") ? o._[0].split("..") : o._; A = treeOf(resolve(r[0])); B = r[1] ? treeOf(resolve(r[1])) : S.work; }
        else if (o["--staged"] || o["--cached"]) { A = headTree(); B = S.index; }
        else { A = S.index; B = {}; for (const p of keys(S.index)) if (p in S.work) B[p] = S.work[p]; }
        if (o["--name-only"]) { for (const p of keys(A, B)) if (A[p] !== B[p]) out(p); return; }
        diffTrees(A, B);
      },
      branch(a) {
        const o = opts(a, { "-d": "flag", "-D": "flag", "--delete": "flag", "-m": "flag", "-M": "flag", "-a": "flag", "-f": "flag", "-r": "flag", "-v": "flag", "-vv": "flag", "--merged": "flag" });
        if (o["-d"] || o["-D"] || o["--delete"]) {
          for (const b of o._) {
            if (!(b in S.branches)) fail("error: branch '" + b + "' not found.");
            if (S.head.branch === b) fail("error: Cannot delete branch '" + b + "' checked out at '/atelier'");
            const into = S.upstream[b] && S.tracking[b] ? S.tracking[b] : headId();
            if (!o["-D"] && !isAncestor(S.branches[b], into)) fail("error: The branch '" + b + "' is not fully merged.\nIf you are sure you want to delete it, run 'git branch -D " + b + "'.");
            out("Deleted branch " + b + " (was " + short(S.branches[b]) + ").");
            delete S.branches[b]; delete S.upstream[b];
          }
          return;
        }
        if (o["-m"] || o["-M"]) {
          const [x, y] = o._.length === 2 ? o._ : [S.head.branch, o._[0]];
          if (!(x in S.branches)) fail("error: refname refs/heads/" + x + " not found");
          S.branches[y] = S.branches[x]; delete S.branches[x];
          if (S.head.branch === x) S.head.branch = y;
          return;
        }
        if (!o._.length) {
          const loc = Object.keys(S.branches).sort();
          if (o["--merged"]) { for (const b of loc) if (isAncestor(S.branches[b], headId())) out((b === S.head.branch ? "* " : "  ") + b); return; }
          if (!S.head.branch) out("* (HEAD detached at " + short(headId()) + ")");
          for (const b of loc) out((b === S.head.branch ? "* " : "  ") + b + (o["-v"] || o["-vv"] ? " " + short(S.branches[b]) + (o["-vv"] && S.upstream[b] ? " [origin/" + b + "]" : "") + " " + first(C(S.branches[b]).msg) : ""));
          if (o["-a"] || o["-r"]) for (const b of Object.keys(S.tracking).sort()) out("  remotes/origin/" + b);
          return;
        }
        const [name, start] = o._;
        if (name in S.branches && !o["-f"]) fail("fatal: a branch named '" + name + "' already exists");
        const id = resolve(start || "HEAD");
        S.branches[name] = id;
      },
      switch(a) {
        const o = opts(a, { "-c": "value", "-C": "value", "--create": "value", "--detach": "flag", "-d": "flag", "--track": "flag", "-t": "flag" });
        const create = o["-c"] || o["-C"] || o["--create"];
        if (create) return doSwitchCreate(create, o._[0], !!o["-C"]);
        if (o["--detach"] || o["-d"]) { const id = resolve(o._[0] || "HEAD"); return detachTo(id); }
        let name = o._[0];
        if (!name) fail("fatal: missing branch or commit argument");
        if (name === "-") { if (!S.prev) fail("fatal: no previous branch"); name = S.prev; }
        if (!(name in S.branches)) {
          if (name in S.tracking) { checkoutTree(S.tracking[name], "checkout"); S.branches[name] = S.tracking[name]; S.upstream[name] = true; S.prev = S.head.branch; S.head = { branch: name }; S.reflog.unshift({ id: S.tracking[name], msg: "checkout: moving to " + name }); out("branch '" + name + "' set up to track 'origin/" + name + "'.\nSwitched to a new branch '" + name + "'"); return; }
          if (resolve(name, true)) fail("fatal: a branch is expected, got commit '" + name + "'\nhint: If you want to detach HEAD at the commit, try again with the --detach option.");
          fail("fatal: invalid reference: " + name);
        }
        if (S.head.branch === name) { out("Already on '" + name + "'"); return; }
        checkoutTree(S.branches[name], "checkout");
        S.prev = S.head.branch; S.head = { branch: name };
        S.reflog.unshift({ id: S.branches[name], msg: "checkout: moving from " + (S.prev || short(headId())) + " to " + name });
        out("Switched to branch '" + name + "'");
      },
      checkout(a) {
        const dd = a.indexOf("--");
        if (dd >= 0) return restoreFiles(a.slice(0, dd).length ? resolve(a[0]) : null, a.slice(dd + 1), false, true);
        const o = opts(a, { "-b": "value", "-B": "value", "--detach": "flag" });
        if (o["-b"] || o["-B"]) return doSwitchCreate(o["-b"] || o["-B"], o._[0], !!o["-B"]);
        const name = o._[0];
        if (!name) fail("error: nom de branche manquant");
        if (name in S.branches || name in S.tracking || name === "-") return git.switch([name]);
        const id = resolve(name, true);
        if (id) return detachTo(id);
        if (name in S.index || name in S.work) return restoreFiles(null, o._, false, true);
        fail("error: pathspec '" + name + "' did not match any file(s) known to git");
      },
      restore(a) {
        const o = opts(a, { "--staged": "flag", "-S": "flag", "--worktree": "flag", "-W": "flag", "--source": "value", "-s": "value" });
        const src = o["--source"] || o["-s"];
        const staged = o["--staged"] || o["-S"], wt = o["--worktree"] || o["-W"] || !staged;
        if (!o._.length) fail("fatal: you must specify path(s) to restore");
        restoreFiles(src ? resolve(src) : null, o._, staged, wt);
      },
      reset(a) {
        const o = opts(a, { "--soft": "flag", "--mixed": "flag", "--hard": "flag", "--keep": "flag" });
        const dd = o._.indexOf("--"); if (dd >= 0) o._.splice(dd, 1);
        if (o._.length && !resolve(o._[0], true) && (o._[0] in S.index || o._[0] in headTree() || o._[0] === ".")) {
          const H = headTree();
          for (const sp of o._) for (const p of pathsMatch(sp, keys(S.index, H))) { if (p in H) S.index[p] = H[p]; else delete S.index[p]; }
          return;
        }
        const target = resolve(o._[0] || "HEAD");
        const before = headId();
        S.origHead = before;
        if (o["--hard"]) { hardTo(target); if (S.op && S.op.type !== "rebase") S.op = null; }
        else if (!o["--soft"]) { const Tt = treeOf(target); for (const p of keys(S.index, Tt)) { if (p in Tt) S.index[p] = Tt[p]; else delete S.index[p]; } S.unmerged.clear(); }
        setHead(target, "reset: moving to " + (o._[0] || "HEAD"));
        if (o["--hard"]) out("HEAD is now at " + short(target) + " " + first(C(target).msg));
        else { const s = status(); if (s.modified.length) out("Unstaged changes after reset:\n" + s.modified.map((x) => "M\t" + x.path).join("\n")); }
      },
      merge(a) {
        const o = opts(a, { "--no-ff": "flag", "--ff-only": "flag", "--squash": "flag", "-m": "value", "--abort": "flag", "--continue": "flag", "--no-edit": "flag" });
        if (o["--abort"]) { if (!S.op || S.op.type !== "merge") fail("fatal: There is no merge to abort (MERGE_HEAD missing)."); hardTo(headId()); S.op = null; return; }
        if (o["--continue"]) { if (!S.op || S.op.type !== "merge") fail("fatal: There is no merge in progress (MERGE_HEAD missing)."); return git.commit([]); }
        if (S.op) fail("error: Merging is not possible because you have unmerged files.");
        const name = o._[0]; if (!name) fail("fatal: No remote for the current branch.");
        const target = resolve(name); const h = headId();
        if (isAncestor(target, h)) { out("Already up to date."); return; }
        if (isAncestor(h, target) && !o["--no-ff"] && !o["--squash"]) {
          checkoutTree(target, "merge");
          out("Updating " + short(h) + ".." + short(target) + "\nFast-forward");
          diffStat(treeOf(h), treeOf(target));
          setHead(target, "merge " + name + ": Fast-forward");
          return;
        }
        if (o["--ff-only"]) fail("fatal: Not possible to fast-forward, aborting.");
        requireClean("merge");
        const base = mergeBase(h, target);
        const res = merge3(treeOf(base), headTree(), treeOf(target), "HEAD", name);
        applyMerge(res);
        const msg = o["-m"] || (name.startsWith("origin/") ? "Merge remote-tracking branch '" + name + "'" : "Merge branch '" + name + "'") + (S.head.branch && S.head.branch !== "main" && S.head.branch !== "master" ? " into " + S.head.branch : "");
        if (res.conflicts.length) {
          reportConflicts(res);
          if (o["--squash"]) { out("Squash commit -- not updating HEAD\nAutomatic merge failed; fix conflicts and then commit the result."); S.op = null; return 1; }
          S.op = { type: "merge", theirs: target, msg, name };
          out("Automatic merge failed; fix conflicts and then commit the result.");
          return 1;
        }
        if (o["--squash"]) { out("Squash commit -- not updating HEAD"); return; }
        const id = mk([h, target], S.index, msg); setHead(id, "merge " + name + ": Merge made by the 'ort' strategy.");
        out("Merge made by the 'ort' strategy.");
        diffStat(treeOf(h), S.index);
      },
      rebase(a, heredoc) {
        const o = opts(a, { "-i": "flag", "--interactive": "flag", "--continue": "flag", "--abort": "flag", "--skip": "flag", "--onto": "value", "--autosquash": "flag" });
        if (o["--continue"]) { if (!S.op || S.op.type !== "rebase") fail("fatal: No rebase in progress?"); return rebaseContinue(); }
        if (o["--abort"]) {
          if (!S.op || S.op.type !== "rebase") fail("fatal: No rebase in progress?");
          const op = S.op; hardTo(op.orig);
          if (op.branch) { S.branches[op.branch] = op.orig; S.head = { branch: op.branch }; } else S.head = { detached: op.orig };
          S.reflog.unshift({ id: op.orig, msg: "rebase (abort): returning to " + (op.branch ? "refs/heads/" + op.branch : short(op.orig)) });
          S.op = null; return;
        }
        if (o["--skip"]) { if (!S.op || S.op.type !== "rebase") fail("fatal: No rebase in progress?"); hardTo(headId()); return rebaseLoop(); }
        if (S.op) fail("fatal: It seems that there is already a rebase-merge directory, and\nI wonder if you are in the middle of another rebase.");
        const upName = o._[0] || (S.head.branch && S.upstream[S.head.branch] ? "origin/" + S.head.branch : null);
        if (!upName) fail("There is no tracking information for the current branch.\nPlease specify which branch you want to rebase against.");
        const up = resolve(upName); const h = headId();
        const onto = o["--onto"] ? resolve(o["--onto"]) : up;
        if (o["-i"] || o["--interactive"]) {
          if (!heredoc && o["--autosquash"]) { const list0 = rangeCommits(up, h).filter((x) => C(x).parents.length < 2); return startRebase(onto, autosquash(list0.map((id) => ({ action: "pick", id }))), true); }
          if (!heredoc) fail("error: l'éditeur interactif n'existe pas dans l'atelier.\n→ écris la liste juste après : git rebase -i " + upName + " <<EOF … EOF (une ligne par commit : pick / reword -m \"…\" / squash / fixup / drop)");
          const list = rangeCommits(up, h).filter((x) => C(x).parents.length < 2);
          let todo = parseTodo(heredoc, list);
          if (!todo.length) { out("Nothing to do"); return; }
          return startRebase(onto, todo, true);
        }
        if (isAncestor(up, h) && !o["--onto"]) { out("Current branch " + branchLabel() + " is up to date."); return; }
        if (isAncestor(h, up) && !o["--onto"]) { checkoutTree(up, "rebase"); setHead(up, "rebase (finish): fast-forward"); out("Successfully rebased and updated refs/heads/" + branchLabel() + "."); return; }
        const list = rangeCommits(up, h).filter((x) => C(x).parents.length < 2);
        const upside = new Set(rangeCommits(h, onto).map(patchOf));
        let todo = list.filter((x) => !upside.has(patchOf(x))).map((id) => ({ action: "pick", id }));
        if (o["--autosquash"]) todo = autosquash(todo);
        return startRebase(onto, todo, false);
      },
      "cherry-pick"(a) {
        const o = opts(a, { "--continue": "flag", "--abort": "flag", "--skip": "flag", "-x": "flag" });
        if (o["--continue"]) {
          if (!S.op || S.op.type !== "cherry-pick") fail("error: no cherry-pick or revert in progress");
          if (S.unmerged.size) fail("error: Committing is not possible because you have unmerged files.");
          const op = S.op; commitIndex(op.msg, [headId()], "cherry-pick", op.author); S.op = null;
          return applyPicks(op.rest || []);
        }
        if (o["--abort"]) { if (!S.op || S.op.type !== "cherry-pick") fail("error: no cherry-pick or revert in progress"); hardTo(S.op.orig); setHead(S.op.orig, "cherry-pick: abort"); S.op = null; return; }
        if (o["--skip"]) { if (!S.op) fail("error: no cherry-pick in progress"); hardTo(headId()); const r = S.op.rest || []; S.op = null; return applyPicks(r); }
        requireClean("cherry-pick");
        let ids = [];
        for (const x of o._) { if (x.includes("..")) { const [p, q] = x.split(".."); ids.push(...rangeCommits(resolve(p), resolve(q))); } else ids.push(resolve(x)); }
        if (!ids.length) fail("fatal: empty commit set passed");
        S.origHead = headId();
        return applyPicks(ids, headId());
      },
      revert(a) {
        const o = opts(a, { "--no-edit": "flag", "--continue": "flag", "--abort": "flag", "-m": "value", "--no-commit": "flag", "-n": "flag" });
        if (o["--continue"]) {
          if (!S.op || S.op.type !== "revert") fail("error: no cherry-pick or revert in progress");
          if (S.unmerged.size) fail("error: Committing is not possible because you have unmerged files.");
          commitIndex(S.op.msg, [headId()], "revert", S.author); S.op = null; return;
        }
        if (o["--abort"]) { if (!S.op || S.op.type !== "revert") fail("error: no revert in progress"); hardTo(S.op.orig); S.op = null; return; }
        requireClean("revert");
        let ids = [];
        for (const x of o._) { if (x.includes("..")) { const [p, q] = x.split(".."); ids.push(...rangeCommits(resolve(p), resolve(q)).reverse()); } else ids.push(resolve(x)); }
        for (const id of ids) {
          const c = C(id);
          let parent = c.parents[0];
          if (c.parents.length > 1) { if (!o["-m"]) fail("error: commit " + short(id) + " is a merge but no -m option was given."); parent = c.parents[+o["-m"] - 1]; }
          const msg = "Revert \"" + first(c.msg) + "\"\n\nThis reverts commit " + id + ".";
          const res = merge3(c.tree, headTree(), treeOf(parent), "HEAD", "parent of " + short(id) + " (" + first(c.msg) + ")");
          const orig = headId();
          applyMerge(res);
          if (res.conflicts.length) { reportConflicts(res); S.op = { type: "revert", msg, orig }; out("error: could not revert " + short(id) + "... " + first(c.msg) + "\nhint: After resolving the conflicts, mark them with\nhint: \"git add/rm <pathspec>\", then run\nhint: \"git revert --continue\"."); return 1; }
          if (o["--no-commit"] || o["-n"]) continue;
          const r = commitIndex(msg, [orig], "revert", S.author);
          out("[" + branchLabel() + " " + short(r.id) + "] " + first(msg) + "\n " + r.n + " file" + (r.n > 1 ? "s" : "") + " changed");
        }
      },
      stash(a) {
        const sub = a[0] && !a[0].startsWith("-") ? a[0] : "push";
        const rest = a[0] && !a[0].startsWith("-") ? a.slice(1) : a;
        const pickN = (r) => { const m = /stash@\{(\d+)\}/.exec(r[0] || ""); const n = m ? +m[1] : r[0] && /^\d+$/.test(r[0]) ? +r[0] : 0; if (!S.stash[n]) fail("error: stash@{" + n + "} is not a valid reference"); return n; };
        if (sub === "push" || sub === "save") {
          const o = opts(rest, { "-m": "value", "--message": "value", "-u": "flag", "--include-untracked": "flag" });
          const s = status();
          const withU = o["-u"] || o["--include-untracked"];
          if (!s.staged.length && !s.modified.length && !(withU && s.untracked.length)) { out("No local changes to save"); return; }
          const h = headId();
          const untracked = {}; if (withU) for (const p of s.untracked) untracked[p] = S.work[p];
          const work = {}; for (const p of keys(S.index, headTree())) if (p in S.work) work[p] = S.work[p];
          const msg = (o["-m"] || o["--message"]) ? "On " + branchLabel() + ": " + (o["-m"] || o["--message"]) : "WIP on " + branchLabel() + ": " + short(h) + " " + first(C(h).msg);
          const commit = mk([h], work, msg);
          S.stash.unshift({ base: h, index: copy(S.index), work, untracked, msg, commit });
          hardTo(h); for (const p of Object.keys(untracked)) delete S.work[p];
          out("Saved working directory and index state " + msg);
          return;
        }
        if (sub === "list") { S.stash.forEach((e, i) => out("stash@{" + i + "}: " + e.msg)); return; }
        if (sub === "show") { const e = S.stash[pickN(rest)]; diffTrees(treeOf(e.base), e.work, true); return; }
        if (sub === "drop") { const n = pickN(rest); out("Dropped stash@{" + n + "} (" + short(S.stash[n].commit) + ")"); S.stash.splice(n, 1); return; }
        if (sub === "clear") { S.stash = []; return; }
        if (sub === "pop" || sub === "apply") {
          if (!S.stash.length) fail("No stash entries found.");
          const n = pickN(rest); const e = S.stash[n];
          for (const p of Object.keys(e.untracked)) if (p in S.work) fail("error: " + p + " already exists, no checkout\nerror: could not restore untracked files from stash");
          const curW = {}; for (const p of keys(S.index, headTree())) if (p in S.work) curW[p] = S.work[p];
          const res = merge3(treeOf(e.base), curW, e.work, "Updated upstream", "Stashed changes");
          for (const p of keys(curW, res.work)) { if (p in res.work) S.work[p] = res.work[p]; else delete S.work[p]; }
          for (const c of res.conflicts) S.unmerged.add(c.path);
          for (const p of Object.keys(e.untracked)) S.work[p] = e.untracked[p];
          if (res.conflicts.length) { reportConflicts(res); out("The stash entry is kept in case you need it again."); return 1; }
          git.status([]);
          if (sub === "pop") { out("Dropped refs/stash@{" + n + "} (" + short(e.commit) + ")"); S.stash.splice(n, 1); }
          return;
        }
        if (sub === "branch") { const e = S.stash[0]; doSwitchCreate(rest[0], e.base); git.stash(["pop"]); return; }
        fail("error: sous-commande stash inconnue : " + sub);
      },
      tag(a) {
        const o = opts(a, { "-a": "flag", "-m": "value", "-d": "flag", "-l": "flag", "-f": "flag" });
        if (o["-d"]) { for (const t of o._) { if (!(t in S.tags)) fail("error: tag '" + t + "' not found."); out("Deleted tag '" + t + "' (was " + short(S.tags[t].id) + ")"); delete S.tags[t]; } return; }
        if (!o._.length || o["-l"]) { for (const t of Object.keys(S.tags).sort()) out(t); return; }
        const [name, rev] = o._;
        if (name in S.tags && !o["-f"]) fail("fatal: tag '" + name + "' already exists");
        S.tags[name] = { id: resolve(rev || "HEAD"), annotated: !!(o["-a"] || o["-m"]), msg: o["-m"] || null };
      },
      reflog(a) {
        S.reflog.forEach((e, i) => out(short(e.id) + " HEAD@{" + i + "}: " + e.msg));
      },
      "rev-parse"(a) { for (const x of a.filter((y) => !y.startsWith("-"))) out(resolve(x)); if (a.includes("--abbrev-ref")) out(branchLabel()); },
      remote(a) {
        if (a[0] === "add") { S.remote = S.remote || { url: a[2] || "https://github.com/toi/projet.git", branches: {} }; S.remote.url = a[2] || S.remote.url; return; }
        if (a[0] === "-v") { if (S.remote) out("origin\t" + S.remote.url + " (fetch)\norigin\t" + S.remote.url + " (push)"); return; }
        if (S.remote) out("origin");
      },
      fetch(a) {
        const o = opts(a, { "--prune": "flag", "-p": "flag", "--all": "flag" });
        if (!S.remote) fail("fatal: 'origin' does not appear to be a git repository");
        const lines0 = [];
        for (const [b, id] of Object.entries(S.remote.branches)) {
          const old = S.tracking[b];
          if (old === id) continue;
          if (!old) lines0.push(" * [new branch]      " + b + " -> origin/" + b);
          else if (isAncestor(old, id)) lines0.push("   " + short(old) + ".." + short(id) + "  " + b + " -> origin/" + b);
          else lines0.push(" + " + short(old) + "..." + short(id) + " " + b + " -> origin/" + b + "  (forced update)");
          S.tracking[b] = id;
        }
        if (o["--prune"] || o["-p"]) for (const b of Object.keys(S.tracking)) if (!(b in S.remote.branches)) { lines0.push(" - [deleted]         (none) -> origin/" + b); delete S.tracking[b]; }
        if (lines0.length) out("From " + S.remote.url + "\n" + lines0.join("\n"));
      },
      pull(a) {
        const o = opts(a, { "--rebase": "flag", "-r": "flag", "--no-rebase": "flag", "--ff-only": "flag", "--ff": "flag" });
        git.fetch([]);
        const b = S.head.branch;
        if (!b || !(b in S.tracking)) fail("There is no tracking information for the current branch.\nPlease specify which branch you want to merge with.\n\n    git branch --set-upstream-to=origin/<branch> " + (b || ""));
        const up = S.tracking[b], h = headId();
        if (o["--rebase"] || o["-r"]) return git.rebase(["origin/" + b]);
        if (isAncestor(up, h)) { out("Already up to date."); return; }
        if (isAncestor(h, up)) return git.merge(["origin/" + b]);
        if (o["--ff-only"]) fail("fatal: Not possible to fast-forward, aborting.");
        if (!o["--no-rebase"] && !o["--ff"]) fail("hint: You have divergent branches and need to specify how to reconcile them.\nhint:   git pull --no-rebase   # merge\nhint:   git pull --rebase      # rebase\nhint:   git pull --ff-only     # fast-forward only\nfatal: Need to specify how to reconcile divergent branches.");
        return git.merge(["origin/" + b]);
      },
      push(a) {
        const o = opts(a, { "-u": "flag", "--set-upstream": "flag", "-f": "flag", "--force": "flag", "--force-with-lease": "flag", "--tags": "flag", "-d": "flag", "--delete": "flag" });
        if (!S.remote) fail("fatal: No configured push destination.\nhint: git remote add origin <url>");
        const args = o._.slice(); if (args[0] === "origin") args.shift();
        if (o["--tags"]) { S.remote.tags = Object.assign(S.remote.tags || {}, S.tags); out("To " + S.remote.url + "\n" + Object.keys(S.tags).map((t) => " * [new tag]         " + t + " -> " + t).join("\n")); if (!args.length) return; }
        if (o["-d"] || o["--delete"]) { for (const b of args) { delete S.remote.branches[b]; delete S.tracking[b]; out("To " + S.remote.url + "\n - [deleted]         " + b); } return; }
        let b = args[0];
        if (!b) {
          b = S.head.branch;
          if (!b) fail("fatal: You are not currently on a branch.");
          if (!S.upstream[b] && !(o["-u"] || o["--set-upstream"])) fail("fatal: The current branch " + b + " has no upstream branch.\nTo push the current branch and set the remote as upstream, use\n\n    git push --set-upstream origin " + b + "\n");
        }
        if (b in S.tags && !(b in S.branches)) { S.remote.tags = Object.assign(S.remote.tags || {}, { [b]: S.tags[b] }); out("To " + S.remote.url + "\n * [new tag]         " + b + " -> " + b); return; }
        if (b === "HEAD") b = S.head.branch;
        if (!(b in S.branches)) fail("error: src refspec " + b + " does not match any");
        const l = S.branches[b], r = S.remote.branches[b];
        let line;
        if (r === l) { out("Everything up-to-date"); }
        else {
          if (!r) line = " * [new branch]      " + b + " -> " + b;
          else if (isAncestor(r, l)) line = "   " + short(r) + ".." + short(l) + "  " + b + " -> " + b;
          else if (o["--force-with-lease"]) {
            if (S.tracking[b] !== r) fail("To " + S.remote.url + "\n ! [rejected]        " + b + " -> " + b + " (stale info)\nerror: failed to push some refs to '" + S.remote.url + "'\n→ quelqu'un a poussé depuis ton dernier fetch : --force-with-lease a protégé son travail.");
            line = " + " + short(r) + "..." + short(l) + " " + b + " -> " + b + " (forced update)";
          } else if (o["-f"] || o["--force"]) line = " + " + short(r) + "..." + short(l) + " " + b + " -> " + b + " (forced update)";
          else fail("To " + S.remote.url + "\n ! [rejected]        " + b + " -> " + b + " (" + (S.tracking[b] === r ? "non-fast-forward" : "fetch first") + ")\nerror: failed to push some refs to '" + S.remote.url + "'\nhint: Updates were rejected because the tip of your current branch is behind\nhint: its remote counterpart. Integrate the remote changes (e.g.\nhint: 'git pull ...') before pushing again.");
          S.remote.branches[b] = l; S.tracking[b] = l;
          out("To " + S.remote.url + "\n" + line);
        }
        if (o["-u"] || o["--set-upstream"]) { S.upstream[b] = true; S.tracking[b] = l; out("branch '" + b + "' set up to track 'origin/" + b + "'."); }
      },
      bisect(a) {
        const sub = a[0];
        if (sub === "start") { S.bisect = { bad: null, goods: [], orig: S.head.branch ? { branch: S.head.branch } : { detached: headId() }, steps: 0 }; if (a[1]) git.bisect(["bad", a[1]]); if (a[2]) git.bisect(["good", a[2]]); return; }
        if (!S.bisect) fail("You need to start by \"git bisect start\"");
        if (sub === "bad" || sub === "new") { S.bisect.bad = resolve(a[1] || "HEAD"); return bisectNext(); }
        if (sub === "good" || sub === "old") { for (const r of a.slice(1).length ? a.slice(1) : ["HEAD"]) S.bisect.goods.push(resolve(r)); return bisectNext(); }
        if (sub === "skip") { S.bisect.skips = (S.bisect.skips || []).concat(headId()); return bisectNext(); }
        if (sub === "reset") {
          const o = S.bisect.orig; S.bisect = null; const was = headId();
          const id = o.branch ? S.branches[o.branch] : o.detached;
          checkoutTree(id, "checkout"); S.head = o; S.reflog.unshift({ id, msg: "checkout: moving to " + (o.branch || short(id)) });
          out("Previous HEAD position was " + short(was) + "\nSwitched to branch '" + (o.branch || short(id)) + "'"); return;
        }
        if (sub === "run") {
          if (!S.bisect.bad || !S.bisect.goods.length) fail("error: bisect run failed: il faut d'abord un commit bad et un commit good");
          let guard = 0;
          while (!S.bisect.found && guard++ < 64) {
            const st = runSimple(a.slice(1), true);
            out("running '" + a.slice(1).join(" ") + "'");
            if (st === 0) git.bisect(["good"]); else if (st === 125) git.bisect(["skip"]); else git.bisect(["bad"]);
          }
          if (S.bisect.found) out("bisect found first bad commit");
          return;
        }
        if (sub === "log") { out("# bad: " + short(S.bisect.bad) + "\n" + S.bisect.goods.map((g) => "# good: " + short(g)).join("\n")); return; }
        fail("error: sous-commande bisect inconnue : " + sub);
      },
    };
    git.checkout.toString = () => "checkout";

    function autosquash(todo) {
      const res = todo.filter((t) => !/^(fixup|squash)! /.test(C(t.id).msg));
      for (const t of todo) {
        const m = /^(fixup|squash)! (.*)$/.exec(first(C(t.id).msg)); if (!m) continue;
        const i = res.findIndex((x) => first(C(x.id).msg) === m[2]);
        if (i >= 0) { let j = i + 1; while (j < res.length && res[j].action !== "pick") j++; res.splice(j, 0, { action: m[1], id: t.id }); }
        else res.push(t);
      }
      return res;
    }
    function applyPicks(ids, orig) {
      for (let i = 0; i < ids.length; i++) {
        const id = ids[i]; const c = C(id);
        const r = pick(id, c.msg, c.author);
        if (r === "conflict") {
          S.op = { type: "cherry-pick", msg: c.msg, author: c.author, rest: ids.slice(i + 1), orig: orig || S.origHead };
          out("error: could not apply " + short(id) + "... " + first(c.msg) + "\nhint: After resolving the conflicts, mark them with\nhint: \"git add/rm <pathspec>\", then run\nhint: \"git cherry-pick --continue\".");
          return 1;
        }
        if (r === "empty") fail("The previous cherry-pick is now empty, possibly due to conflict resolution.");
        out("[" + branchLabel() + " " + short(headId()) + "] " + first(c.msg));
      }
    }
    function doSwitchCreate(name, start, force) {
      if (name in S.branches && !force) fail("fatal: a branch named '" + name + "' already exists");
      const id = start ? resolve(start) : headId();
      if (id && id !== headId()) checkoutTree(id, "checkout");
      S.branches[name] = id;
      if (start && start.startsWith("origin/")) S.upstream[name] = true;
      S.prev = S.head.branch; S.head = { branch: name };
      if (id) S.reflog.unshift({ id, msg: "checkout: moving from " + (S.prev || "HEAD") + " to " + name });
      out("Switched to a new branch '" + name + "'");
    }
    function detachTo(id) {
      checkoutTree(id, "checkout");
      S.prev = S.head.branch || S.prev; S.head = { detached: id };
      S.reflog.unshift({ id, msg: "checkout: moving to " + short(id) });
      out("Note: switching to '" + short(id) + "'.\n\nYou are in 'detached HEAD' state. You can look around, make experimental\nchanges and commit them, and you can discard any commits you make in this\nstate without impacting any branches by switching back to a branch.\n\nHEAD is now at " + short(id) + " " + first(C(id).msg));
    }
    function restoreFiles(srcId, specs, staged, worktree) {
      const src = srcId ? treeOf(srcId) : null;
      for (const sp of specs) {
        const all = keys(S.index, S.work, headTree(), src || {});
        const ps = pathsMatch(sp, all);
        if (!ps.length) fail("error: pathspec '" + sp + "' did not match any file(s) known to git");
        for (const p of ps) {
          if (staged) { const from = src || headTree(); if (p in from) S.index[p] = from[p]; else delete S.index[p]; }
          if (worktree) {
            const from = src || S.index;
            if (!(p in from) && !(p in headTree()) && !src) continue; // non suivi : on ne touche pas
            if (p in from) S.work[p] = from[p]; else delete S.work[p];
            if (src) { if (p in from) S.index[p] = from[p]; }
          }
          S.unmerged.delete(p);
        }
      }
    }
    function bisectNext() {
      const B = S.bisect;
      if (!B.bad || !B.goods.length) { out(B.bad ? "status: waiting for good commit(s), bad commit known" : "status: waiting for both good and bad commits"); return; }
      const goodSet = new Set(B.goods.flatMap((g) => [...ancestors(g)]));
      const skips = new Set(B.skips || []);
      const cands = [...ancestors(B.bad)].filter((x) => !goodSet.has(x)).sort((x, y) => C(x).seq - C(y).seq);
      if (cands.length === 1) {
        B.found = cands[0]; S.lastBisect = B.found; const c = C(B.found);
        out(B.found + " is the first bad commit\ncommit " + B.found + "\nAuthor: " + c.author + "\n\n    " + first(c.msg));
        return;
      }
      const testable = cands.filter((x) => x !== B.bad && !skips.has(x));
      if (!testable.length) { out("There are only 'skip'ped commits left to test."); return; }
      const mid = testable[Math.floor((testable.length - 1) / 2)];
      B.steps++;
      checkoutTree(mid, "checkout"); S.head = { detached: mid }; S.reflog.unshift({ id: mid, msg: "checkout: moving to " + short(mid) });
      const left = cands.length - 1;
      out("Bisecting: " + Math.floor(left / 2) + " revision" + (Math.floor(left / 2) > 1 ? "s" : "") + " left to test after this (roughly " + Math.max(0, Math.ceil(Math.log2(left + 1)) - 1) + " steps)\n[" + mid + "] " + first(C(mid).msg));
    }

    /* ---------- diff ---------- */
    function lineDiff(a, b) {
      const A = a === undefined ? [] : a.replace(/\n$/, "").split("\n"), B = b === undefined ? [] : b.replace(/\n$/, "").split("\n");
      const n = A.length, m = B.length, L = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
      for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) L[i][j] = A[i] === B[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
      const res = []; let i = 0, j = 0;
      while (i < n && j < m) { if (A[i] === B[j]) { res.push(" " + A[i]); i++; j++; } else if (L[i + 1][j] >= L[i][j + 1]) res.push("-" + A[i++]); else res.push("+" + B[j++]); }
      while (i < n) res.push("-" + A[i++]); while (j < m) res.push("+" + B[j++]);
      return res;
    }
    function diffTrees(A, B) {
      for (const p of keys(A, B)) {
        if (A[p] === B[p]) continue;
        out("diff --git a/" + p + " b/" + p + (A[p] === undefined ? "\nnew file" : B[p] === undefined ? "\ndeleted file" : "") + "\n--- " + (A[p] === undefined ? "/dev/null" : "a/" + p) + "\n+++ " + (B[p] === undefined ? "/dev/null" : "b/" + p));
        out(lineDiff(A[p], B[p]).join("\n"));
      }
    }
    function diffStat(A, B) { const ch = keys(A, B).filter((k) => A[k] !== B[k]); if (ch.length) out(ch.map((p) => " " + p).join("\n") + "\n " + ch.length + " file" + (ch.length > 1 ? "s" : "") + " changed"); }
    function decorations(id) {
      const d = [];
      if (!S.head.branch && S.head.detached === id) d.push("HEAD");
      for (const b of Object.keys(S.branches).sort()) if (S.branches[b] === id) d.push(S.head.branch === b ? "HEAD -> " + b : b);
      for (const b of Object.keys(S.tracking).sort()) if (S.tracking[b] === id) d.push("origin/" + b);
      for (const t of Object.keys(S.tags).sort()) if (S.tags[t].id === id) d.push("tag: " + t);
      const hi = d.findIndex((x) => x.startsWith("HEAD -> ")); if (hi > 0) d.unshift(d.splice(hi, 1)[0]);
      return d.join(", ");
    }
    function allTips() {
      return [...new Set([headId(), ...Object.values(S.branches), ...Object.values(S.tracking), ...Object.values(S.tags).map((t) => t.id)].filter(Boolean))];
    }

    /* ---------- « gh » : Pull Requests sur origin ---------- */
    function gh(args) {
      if (args[0] !== "pr") fail("gh : seules les commandes « gh pr create | merge | list » existent dans l'atelier");
      if (!S.remote) fail("gh : aucun dépôt distant (git remote add origin …)");
      const sub = args[1];
      const o = opts(args.slice(2), { "--title": "value", "-t": "value", "--base": "value", "-B": "value", "--body": "value", "-b": "value", "--squash": "flag", "-s": "flag", "--merge": "flag", "-m": "flag", "--rebase": "flag", "-r": "flag", "--delete-branch": "flag", "-d": "flag", "--fill": "flag" });
      if (sub === "create") {
        const head = S.head.branch; if (!head || !(head in S.remote.branches)) fail("aborted: you must first push the current branch to a remote, or use the --head flag");
        const base = o["--base"] || o["-B"] || "main";
        const title = o["--title"] || o["-t"] || first(C(S.remote.branches[head]).msg);
        const pr = { number: S.prs.length + 1, head, base, title, state: "OPEN" }; S.prs.push(pr);
        out(S.remote.url.replace(/\.git$/, "") + "/pull/" + pr.number); return;
      }
      if (sub === "list") { for (const p of S.prs.filter((p) => p.state === "OPEN")) out("#" + p.number + "\t" + p.title + "\t" + p.head); return; }
      if (sub === "merge") {
        const ref = o._[0];
        const pr = ref ? S.prs.find((p) => String(p.number) === String(ref).replace("#", "") || p.head === ref) : S.prs.find((p) => p.state === "OPEN" && p.head === S.head.branch);
        if (!pr || pr.state !== "OPEN") fail("no open pull requests found for " + (ref || "the current branch"));
        const R = S.remote.branches; const hb = R[pr.head], bb = R[pr.base];
        const base = mergeBase(bb, hb);
        const res = merge3(treeOf(base), treeOf(bb), treeOf(hb), pr.base, pr.head);
        if (res.conflicts.length) fail("X Pull request #" + pr.number + " is not mergeable: the merge commit cannot be cleanly created.\n→ mets ta branche à jour (git pull --rebase origin " + pr.base + " ou rebase sur origin/" + pr.base + "), résous, puis pousse.");
        if (o["--squash"] || o["-s"]) R[pr.base] = mk([bb], res.tree, pr.title + " (#" + pr.number + ")", S.author);
        else if (o["--rebase"] || o["-r"]) { let tip = bb; for (const c of rangeCommits(bb, hb).filter((x) => C(x).parents.length < 2)) { const r2 = merge3(treeOf(C(c).parents[0]), treeOf(tip), C(c).tree, "a", "b"); tip = mk([tip], r2.tree, C(c).msg, C(c).author); } R[pr.base] = tip; }
        else R[pr.base] = isAncestor(bb, hb) && false ? hb : mk([bb, hb], res.tree, "Merge pull request #" + pr.number + " from " + pr.head + "\n\n" + pr.title, S.author);
        pr.state = "MERGED";
        out("✓ " + ((o["--squash"] || o["-s"]) ? "Squashed and merged" : (o["--rebase"] || o["-r"]) ? "Rebased and merged" : "Merged") + " pull request #" + pr.number + " (" + pr.title + ")");
        if (o["--delete-branch"] || o["-d"]) { delete R[pr.head]; out("✓ Deleted remote branch " + pr.head); }
        return;
      }
      fail("gh pr : sous-commande inconnue " + sub);
    }

    /* ---------- shell ---------- */
    function tokenize(line) {
      // renvoie une liste de commandes (séparées par &&), chacune liste de tokens ; gère "", '', >, >>
      const cmds = [[]]; let cur = null, q = null, i = 0;
      const push = () => { if (cur !== null) { cmds[cmds.length - 1].push(cur); cur = null; } };
      while (i < line.length) {
        const ch = line[i];
        if (q) { if (ch === q) { q = null; i++; continue; } if (ch === "\\" && q === '"' && /["\\$`]/.test(line[i + 1] || "")) { cur += line[i + 1]; i += 2; continue; } cur += ch; i++; continue; }
        if (ch === '"' || ch === "'") { q = ch; cur = cur || ""; i++; continue; }
        if (/\s/.test(ch)) { push(); i++; continue; }
        if (ch === "#" && cur === null) break;
        if (ch === "&" && line[i + 1] === "&") { push(); cmds.push([]); i += 2; continue; }
        if (ch === ">" ) { push(); if (line[i + 1] === ">") { cmds[cmds.length - 1].push({ op: ">>" }); i += 2; } else { cmds[cmds.length - 1].push({ op: ">" }); i++; } continue; }
        if (ch === "<" && line[i + 1] === "<") { push(); cmds[cmds.length - 1].push({ op: "<<" }); i += 2; continue; }
        cur = (cur || "") + ch; i++;
      }
      if (q) throw new GitError("bash: guillemet non fermé (" + q + ")", 2);
      push();
      return cmds.filter((c) => c.length);
    }
    const unescape = (s) => s.replace(/\\n/g, "\n").replace(/\\t/g, "\t").replace(/\\\\/g, "\\");
    function runSimple(tk, silent, heredoc) {
      // tk : tokens (peut contenir {op})
      let redir = null;
      const ri = tk.findIndex((t) => typeof t === "object" && (t.op === ">" || t.op === ">>"));
      if (ri >= 0) { redir = { op: tk[ri].op, file: tk[ri + 1] }; tk = tk.slice(0, ri).concat(tk.slice(ri + 2)); if (!redir.file) throw new GitError("bash: syntax error near unexpected token `newline'", 2); }
      tk = tk.filter((t) => typeof t !== "object");
      let neg = false; if (tk[0] === "!") { neg = true; tk = tk.slice(1); }
      const [cmd, ...args] = tk;
      let st = 0, text = null;
      const prevCur = cur; if (silent) cur = { out: [] };
      try {
        if (cmd === "git") { const sub = args[0]; if (!sub) fail("usage: git <command> [<args>]"); const f = git[sub]; if (!f) fail("git: '" + sub + "' is not a git command (ou n'existe pas dans l'atelier). See 'git --help'."); const r = f(args.slice(1), heredoc); st = typeof r === "number" ? r : 0; }
        else if (cmd === "gh") gh(args);
        else if (cmd === "echo") { let a = args, n = false, e = false; while (a[0] === "-n" || a[0] === "-e") { if (a[0] === "-n") n = true; else e = true; a = a.slice(1); } text = (e ? unescape(a.join(" ")) : a.join(" ")) + (n ? "" : "\n"); }
        else if (cmd === "printf") text = unescape(args.join(""));
        else if (cmd === "cat") { for (const f of args) { if (!(f in S.work)) fail("cat: " + f + ": No such file or directory"); out(S.work[f].replace(/\n$/, "")); } }
        else if (cmd === "touch") { for (const f of args) if (!(f in S.work)) S.work[f] = ""; }
        else if (cmd === "rm") { for (const f of args.filter((x) => !x.startsWith("-"))) { if (!(f in S.work) && !args.includes("-f")) fail("rm: cannot remove '" + f + "': No such file or directory"); delete S.work[f]; } }
        else if (cmd === "mv") { const [x, y] = args; if (!(x in S.work)) fail("mv: cannot stat '" + x + "': No such file or directory"); S.work[y] = S.work[x]; delete S.work[x]; }
        else if (cmd === "ls") { out(Object.keys(S.work).sort().join("  ")); }
        else if (cmd === "grep") {
          const q = args.includes("-q"), rest = args.filter((x) => x !== "-q");
          const [pat, f] = rest; if (!(f in S.work)) fail("grep: " + f + ": No such file or directory", 2);
          const hits = S.work[f].split("\n").filter((l) => l.includes(pat));
          if (!q) for (const h of hits) out(h);
          st = hits.length ? 0 : 1;
        }
        else if (cmd === "true") st = 0;
        else if (cmd === "false") st = 1;
        else if (cmd === "cd" || cmd === "clear" || cmd === "pwd") { if (cmd === "pwd") out("/atelier"); }
        else fail("bash: " + cmd + ": command not found (dans l'atelier : git, gh, echo, printf, cat, touch, rm, mv, ls, grep)", 127);
        if (text !== null) {
          if (redir) { if (redir.op === ">>") S.work[redir.file] = (S.work[redir.file] || "") + text; else S.work[redir.file] = text; }
          else out(text.replace(/\n$/, ""));
        } else if (redir) { S.work[redir.file] = (redir.op === ">>" ? S.work[redir.file] || "" : ""); }
      } catch (e) {
        if (!(e instanceof GitError)) { out("(erreur interne du simulateur : " + e.message + ")"); st = 1; }
        else { out(e.message); st = e.status || 1; if (cur && !silent) cur.err = true; }
      } finally { if (silent) cur = prevCur; }
      return neg ? (st === 0 ? 1 : 0) : st;
    }
    function runScript(src, silent) {
      const L = String(src).replace(/\r/g, "").split("\n");
      let last = 0;
      for (let i = 0; i < L.length; i++) {
        const line = L[i]; if (!line.trim() || line.trim().startsWith("#")) continue;
        let cmds;
        const entry = { cmd: line.trim(), out: [], err: false };
        try { cmds = tokenize(line); }
        catch (e) { entry.out.push(e.message); entry.err = true; if (!silent) T.push(entry); last = 2; continue; }
        // heredoc : <<EOF ... EOF
        let heredoc = null;
        for (const c of cmds) {
          const hi = c.findIndex((t) => typeof t === "object" && t.op === "<<");
          if (hi >= 0) {
            const tag = String(c[hi + 1] || "EOF").replace(/['"]/g, ""); c.splice(hi, 2); heredoc = [];
            while (++i < L.length && L[i].trim() !== tag) heredoc.push(L[i]);
            entry.cmd += "\n" + heredoc.join("\n") + "\n" + tag;
          }
        }
        cur = silent ? { out: [] } : entry;
        for (const c of cmds) { last = runSimple(c, false, heredoc); if (last !== 0) { if (!entry.err) entry.warn = true; break; } }
        if (!silent) T.push(entry);
        cur = null;
      }
      return last;
    }

    /* ---------- rendu ---------- */
    const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
    function graphSVG() {
      const tips = allTips();
      if (!tips.length) return '<div class="gs-empty">Aucun commit pour l\'instant.</div>';
      const all = new Set(tips.flatMap((t) => [...ancestors(t)]));
      const rows = [...all].sort((a, b) => C(b).seq - C(a).seq);
      const lane = {};
      const orderTips = [];
      const pushTip = (id) => { if (id && !orderTips.includes(id)) orderTips.push(id); };
      ["main", "master"].forEach((b) => pushTip(S.branches[b]));
      ["main", "master"].forEach((b) => pushTip(S.tracking[b]));
      Object.keys(S.branches).sort().forEach((b) => pushTip(S.branches[b]));
      pushTip(headId()); Object.values(S.tracking).forEach(pushTip); Object.values(S.tags).forEach((t) => pushTip(t.id));
      // rows contiennent aussi des commits seulement atteignables via 2e parent
      rows.forEach((id) => { if (!orderTips.includes(id)) orderTips.push(id); });
      let nl = 0;
      for (const t of orderTips) {
        if (lane[t] !== undefined) continue;
        const L0 = nl++; let x = t;
        while (x && lane[x] === undefined) { lane[x] = L0; x = C(x).parents[0]; }
      }
      // compacter les couloirs utilisés
      const used = [...new Set(rows.map((r) => lane[r]))].sort((a, b) => a - b); const remap = {}; used.forEach((l, i) => (remap[l] = i));
      rows.forEach((r) => (lane[r] = remap[lane[r]]));
      const lanes = used.length;
      const RH = 26, LW = 18, X0 = 14, Y0 = 14;
      const colors = ["#2f6fdb", "#c2410c", "#15803d", "#7c3aed", "#b45309", "#0e7490", "#be185d"];
      const pos = {}; rows.forEach((id, i) => (pos[id] = { x: X0 + lane[id] * LW, y: Y0 + i * RH }));
      let paths = "";
      for (const id of rows) for (const [k, p] of C(id).parents.entries()) {
        if (!pos[p]) continue;
        const a = pos[id], b = pos[p]; const col = colors[(k === 0 ? lane[id] : lane[p]) % colors.length];
        let d;
        if (a.x === b.x) d = `M${a.x},${a.y} L${b.x},${b.y}`;
        else if (k === 0) d = `M${a.x},${a.y} L${a.x},${b.y - RH / 2} Q${a.x},${b.y} ${b.x},${b.y}`;
        else d = `M${a.x},${a.y} Q${b.x},${a.y} ${b.x},${a.y + RH / 2} L${b.x},${b.y}`;
        paths += `<path d="${d}" stroke="${col}" stroke-width="2" fill="none"/>`;
      }
      const TX = X0 + lanes * LW + 6;
      let nodes = "", labels = "", maxX = 300;
      const hid = headId();
      rows.forEach((id) => {
        const p = pos[id]; const col = colors[lane[id] % colors.length]; const c = C(id);
        nodes += c.parents.length > 1 ? `<circle cx="${p.x}" cy="${p.y}" r="5" fill="#fff" stroke="${col}" stroke-width="2.5"/>` : `<circle cx="${p.x}" cy="${p.y}" r="5" fill="${col}"/>`;
        if (id === hid) nodes += `<circle cx="${p.x}" cy="${p.y}" r="8.5" fill="none" stroke="#111" stroke-width="1.5"/>`;
        let x = TX; let lab = `<text x="${x}" y="${p.y + 4}" class="gs-id">${short(id)}</text>`; x += 58;
        const pills = [];
        if (!S.head.branch && S.head.detached === id) pills.push(["HEAD", "head"]);
        Object.keys(S.branches).sort().forEach((b) => { if (S.branches[b] === id) pills.push([(S.head.branch === b ? "HEAD → " : "") + b, S.head.branch === b ? "head" : "br"]); });
        Object.keys(S.tracking).sort().forEach((b) => { if (S.tracking[b] === id) pills.push(["origin/" + b, "rm"]); });
        Object.keys(S.tags).sort().forEach((t) => { if (S.tags[t].id === id) pills.push(["🏷 " + t, "tag"]); });
        for (const [t, k] of pills) { const w = 10 + t.length * 6.6; lab += `<rect x="${x}" y="${p.y - 9}" width="${w}" height="18" rx="9" class="gs-p-${k}"/><text x="${x + w / 2}" y="${p.y + 4}" text-anchor="middle" class="gs-pt gs-pt-${k}">${esc(t)}</text>`; x += w + 4; }
        lab += `<text x="${x + 2}" y="${p.y + 4}" class="gs-msg">${esc(first(c.msg))}</text>`;
        let endX = x + 8 + first(c.msg).length * 6.9;
        if (c.author !== "toi") { lab += `<text x="${endX}" y="${p.y + 4}" class="gs-au">— ${esc(c.author)}</text>`; endX += 20 + c.author.length * 6.5; }
        maxX = Math.max(maxX, endX);
        labels += lab;
      });
      const H = Y0 * 2 + (rows.length - 1) * RH;
      return `<svg class="gs-svg" width="${Math.ceil(maxX + 20)}" height="${H}">${paths}${nodes}${labels}</svg>`;
    }
    function stateLine() {
      const s = status(); const parts = [];
      parts.push(S.head.branch ? `sur <b>${esc(S.head.branch)}</b>` : `<b class="gs-warn">HEAD détachée</b> sur ${short(headId())}`);
      if (S.op) parts.push(`<b class="gs-warn">${S.op.type} en cours</b>`);
      if (S.bisect) parts.push(`<b class="gs-warn">bisect en cours</b>`);
      if (s.unmerged.length) parts.push(`<span class="gs-bad">conflit : ${s.unmerged.map(esc).join(", ")}</span>`);
      if (s.staged.length) parts.push(`préparés : ${s.staged.map((x) => esc(x.path)).join(", ")}`);
      if (s.modified.length) parts.push(`modifiés : ${s.modified.map((x) => esc(x.path)).join(", ")}`);
      if (s.untracked.length) parts.push(`non suivis : ${s.untracked.map(esc).join(", ")}`);
      if (!s.unmerged.length && !s.staged.length && !s.modified.length) parts.push(`<span class="gs-ok">dossier propre</span>`);
      if (S.stash.length) parts.push(`stash : ${S.stash.length}`);
      if (S.remote) parts.push(`origin : ${Object.keys(S.remote.branches).sort().map((b) => esc(b) + "@" + short(S.remote.branches[b])).join(", ") || "vide"}`);
      return parts.join(" · ");
    }
    function filesPanel() {
      const ps = Object.keys(S.work).sort(); if (!ps.length) return "";
      return `<details class="gs-files"${S.unmerged.size ? " open" : ""}><summary>Fichiers du dossier de travail (${ps.length})</summary>${ps.map((p) => `<div class="gs-f"><b>${esc(p)}</b>${S.unmerged.has(p) ? ' <span class="gs-bad">conflit</span>' : ""}<pre>${esc(S.work[p].replace(/\n$/, ""))}</pre></div>`).join("")}</details>`;
    }
    function render() {
      if (!root) return;
      root.innerHTML = `<style>
        .gs{font:13px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;color:#1f2633}
        .gs h4{font:600 11px system-ui,sans-serif;letter-spacing:.06em;text-transform:uppercase;color:#6b7280;margin:10px 0 4px}
        .gs-graph{border:1px solid #e5e7eb;border-radius:8px;padding:4px 6px;background:#fbfbfa;overflow-x:auto}
        .gs-id{fill:#6b7280;font-size:12px}.gs-msg{fill:#1f2633;font-size:12.5px}.gs-au{fill:#9ca3af;font-size:11.5px}
        .gs-pt{font-size:11px;font-weight:600}.gs-p-head{fill:#dcfce7;stroke:#16a34a}.gs-pt-head{fill:#166534}.gs-p-br{fill:#dbeafe;stroke:#2563eb}.gs-pt-br{fill:#1e40af}
        .gs-p-rm{fill:#f3f4f6;stroke:#9ca3af}.gs-pt-rm{fill:#4b5563}.gs-p-tag{fill:#fef3c7;stroke:#d97706}.gs-pt-tag{fill:#92400e}
        .gs-state{font:12.5px system-ui,sans-serif;margin:6px 0;color:#374151}.gs-warn{color:#b45309}.gs-bad{color:#b91c1c;font-weight:600}.gs-ok{color:#15803d}
        .gs-term{background:#111827;color:#e5e7eb;border-radius:8px;padding:10px 12px;white-space:pre-wrap;margin:0;max-height:none}
        .gs-c{color:#93c5fd}.gs-e{color:#fca5a5}.gs-w{color:#fcd34d}.gs-files summary{cursor:pointer;font:12.5px system-ui,sans-serif;color:#374151;margin-top:8px}
        .gs-f{margin:6px 0}.gs-f pre{margin:2px 0 0;background:#f3f4f6;border-radius:6px;padding:6px 8px;white-space:pre-wrap}.gs-empty{color:#6b7280;font:13px system-ui;padding:8px}
      </style><div class="gs"><h4>Historique (git log --graph --all)</h4><div class="gs-graph">${graphSVG()}</div>
      <div class="gs-state">${stateLine()}</div>${filesPanel()}
      <h4>Terminal</h4><pre class="gs-term">${T.length ? T.map((e) => `<span class="gs-c">$ ${esc(e.cmd)}</span>${e.out.length ? "\n" + `<span class="${e.err ? "gs-e" : e.warn ? "gs-w" : ""}">${esc(e.out.join("\n"))}</span>` : ""}`).join("\n") : '<span class="gs-c">(aucune commande)</span>'}</pre></div>`;
    }

    /* ---------- API (préparation du scénario + tests) ---------- */
    const api = {
      sh(script) { const st = runScript(script, S.quiet); render(); return st; },
      run(script) { return api.sh(script); },
      setup(fn) { S.quiet = true; try { fn(api); } finally { S.quiet = false; } T.length = 0; render(); },
      set author(a) { S.author = a; }, get author() { return S.author; },
      write(p, content) { S.work[p] = content; },
      remove(p) { delete S.work[p]; },
      cloneRemote(url) { S.remote = { url: url || "https://github.com/toi/projet.git", branches: Object.assign({}, S.branches) }; S.tracking = Object.assign({}, S.branches); for (const b of Object.keys(S.branches)) S.upstream[b] = true; },
      remoteCommit(branch, msg, changes, author) {
        const parent = S.remote.branches[branch]; const tree = copy(treeOf(parent));
        for (const [p, v] of Object.entries(changes || {})) { if (v === null) delete tree[p]; else tree[p] = v; }
        S.remote.branches[branch] = mk([parent].filter(Boolean), tree, msg, author || "Léa"); render();
        return S.remote.branches[branch];
      },
      get branch() { return S.head.branch || null; },
      get head() { return headId(); },
      get detached() { return !S.head.branch; },
      rev(r) { return resolve(r, true); },
      commit(r) { const id = resolve(r || "HEAD", true); return id ? Object.assign({}, C(id), { tree: copy(C(id).tree) }) : null; },
      msg(r) { const id = resolve(r || "HEAD", true); return id ? C(id).msg : null; },
      parents(r) { const id = resolve(r || "HEAD", true); return id ? C(id).parents.slice() : []; },
      log(r, all) { let x = resolve(r || "HEAD", true); const res = []; if (all) return [...ancestors(x)].sort((a, b) => C(b).seq - C(a).seq).map((y) => first(C(y).msg)); while (x) { res.push(first(C(x).msg)); x = C(x).parents[0]; } return res; },
      ids(r) { let x = resolve(r || "HEAD", true); const res = []; while (x) { res.push(x); x = C(x).parents[0]; } return res; },
      range(a, b) { return rangeCommits(resolve(a, true), resolve(b, true)).map((x) => first(C(x).msg)); },
      isAncestor(a, b) { return isAncestor(resolve(a, true), resolve(b, true)); },
      isLinear(r) { return [...ancestors(resolve(r || "HEAD", true))].every((x) => C(x).parents.length < 2); },
      merges(r) { return [...ancestors(resolve(r || "HEAD", true))].filter((x) => C(x).parents.length > 1).length; },
      file(p) { return p in S.work ? S.work[p] : null; },
      staged(p) { return p in S.index ? S.index[p] : null; },
      at(r, p) { const id = resolve(r, true); return id && p in C(id).tree ? C(id).tree[p] : null; },
      status() { const s = status(); return { staged: s.staged.map((x) => x.path), modified: s.modified.map((x) => x.path), untracked: s.untracked.slice(), unmerged: s.unmerged.slice() }; },
      clean() { const s = status(); return !s.staged.length && !s.modified.length && !s.unmerged.length; },
      get branches() { return Object.assign({}, S.branches); },
      get tags() { const t = {}; for (const [k, v] of Object.entries(S.tags)) t[k] = Object.assign({}, v); return t; },
      get remote() { return S.remote ? { branches: Object.assign({}, S.remote.branches), tags: Object.assign({}, S.remote.tags || {}) } : null; },
      remoteLog(b) { let x = S.remote && S.remote.branches[b]; const res = []; while (x) { res.push(first(C(x).msg)); x = C(x).parents[0]; } return res; },
      get tracking() { return Object.assign({}, S.tracking); },
      get upstream() { return Object.assign({}, S.upstream); },
      get stash() { return S.stash.map((e) => ({ msg: e.msg, base: e.base, work: copy(e.work) })); },
      get reflog() { return S.reflog.map((e) => Object.assign({}, e)); },
      get op() { return S.op ? S.op.type : null; },
      get bisect() { return S.bisect ? { found: S.bisect.found || null, steps: S.bisect.steps } : null; },
      get bisectFound() { return S.lastBisect || null; },
      ignored(p) { return ignored(p); },
      touched(r) { const id = resolve(r || "HEAD", true); if (!id) return []; const c = C(id), p = treeOf(c.parents[0]); return keys(p, c.tree).filter((k) => p[k] !== c.tree[k]); },
      get prs() { return S.prs.map((p) => Object.assign({}, p)); },
      get transcript() { return T.map((e) => ({ cmd: e.cmd, out: e.out.join("\n"), err: e.err, warn: !!e.warn })); },
      get out() { return T.map((e) => "$ " + e.cmd + "\n" + e.out.join("\n")).join("\n"); },
      commands() { return T.map((e) => e.cmd); },
      used(re) { return T.some((e) => (re instanceof RegExp ? re.test(e.cmd) : e.cmd.includes(re))); },
      failed() { return T.filter((e) => e.err).map((e) => e.cmd); },
      count(r) { return ancestors(resolve(r || "HEAD", true)).size; },
    };
    window.__git = api;
    return api;
  };
})();

/* Next.js (App Router) simulé pour l'Atelier de code.
 * Routage par dossiers (app/.../page.tsx, [param], (groupe)), layouts imbriqués, Server Components async,
 * Client Components ('use client'), notFound(), redirect(), not-found.tsx, error.tsx, next/link,
 * Server Actions ('use server') + useActionState + <form action={fn}>, revalidatePath / revalidateTag,
 * cache de fetch (next.revalidate, tags, horloge simulée), Route Handlers (app/.../route.ts).
 * Ce n'est pas Next.js : c'est une maquette fidèle aux concepts, pour s'exercer dans le navigateur.
 */
(function () {
  "use strict";
  const NOT_FOUND = "NEXT_NOT_FOUND", REDIRECT = "NEXT_REDIRECT";

  window.NextSim = function (ctx) {
    const { req, files, root, post } = ctx;
    const React = window.React, ReactDOM = window.ReactDOM;
    const sim = { url: "/", status: 200, renders: 0, now: 0, log: [] };
    const clientFns = new WeakSet();
    const serverFns = new WeakSet();
    let reactRoot = null, rerenderTimer = null;

    /* ---------- React : useActionState + <form action={fn}> ---------- */
    if (!React.useActionState) {
      React.useActionState = function (action, initial) {
        const [state, setState] = React.useState(initial);
        const [pending, setPending] = React.useState(false);
        const ref = React.useRef(state); ref.current = state;
        const formAction = React.useCallback(async (fd) => {
          setPending(true);
          try { setState(await action(ref.current, fd)); }
          catch (err) { if (err && err.digest === REDIRECT) { sim.navigate(err.url); return; } throw err; }
          finally { setPending(false); }
        }, [action]);
        return [state, formAction, pending];
      };
    }
    const ce = React.createElement;
    React.createElement = function (type, props, ...children) {
      if (type === "form" && props && typeof props.action === "function") {
        const action = props.action;
        props = Object.assign({}, props, {
          onSubmit: (e) => {
            e.preventDefault();
            const fd = new FormData(e.currentTarget);
            Promise.resolve(action(fd)).catch((err) => {
              if (err && err.digest === REDIRECT) return sim.navigate(err.url);
              post({ type: "error", text: String(err && err.message || err) });
            });
          },
        });
        delete props.action;
      }
      return ce.call(React, type, props, ...children);
    };

    /* ---------- modules next/* ---------- */
    function navError(kind, extra) { const e = new Error(kind); e.digest = kind; Object.assign(e, extra); return e; }
    const modules = {
      "next/navigation": {
        notFound: () => { throw navError(NOT_FOUND); },
        redirect: (url) => { throw navError(REDIRECT, { url }); },
        useRouter: () => ({ push: (u) => sim.navigate(u), replace: (u) => sim.navigate(u), refresh: () => sim.refresh(), back: () => {} }),
        usePathname: () => sim.url.split("?")[0],
        useSearchParams: () => new URLSearchParams(sim.url.split("?")[1] || ""),
      },
      "next/link": (() => {
        function Link({ href, children, ...rest }) {
          return ce.call(React, "a", Object.assign({}, rest, { href, onClick: (e) => { e.preventDefault(); sim.navigate(href); } }), children);
        }
        clientFns.add(Link);
        return { __esModule: true, default: Link };
      })(),
      "next/cache": {
        revalidatePath: (p) => { sim.log.push("revalidatePath " + p); for (const k of Object.keys(cache)) if (cache[k].path === p || p === "/") delete cache[k]; scheduleRerender(); },
        revalidateTag: (t) => { sim.log.push("revalidateTag " + t); for (const k of Object.keys(cache)) if ((cache[k].tags || []).includes(t)) delete cache[k]; scheduleRerender(); },
      },
      "next/headers": { cookies: async () => ({ get: () => undefined }), headers: async () => new Headers() },
      "server-only": {},
      "client-only": {},
    };
    sim.modules = modules;
    window.__next = sim;

    /* ---------- fetch avec cache Next ---------- */
    const baseFetch = window.fetch;
    const cache = {};
    sim.fetchCalls = 0; sim.inflight = 0; sim.maxInflight = 0;
    window.fetch = async function (url, init) {
      init = init || {};
      const method = (init.method || "GET").toUpperCase();
      const key = method + " " + String(url);
      const rev = init.next && init.next.revalidate;
      const cacheable = method === "GET" && init.cache !== "no-store" && (init.cache === "force-cache" || rev !== undefined);
      if (cacheable && cache[key] && (rev === undefined || rev === false || sim.now - cache[key].at < rev)) {
        post({ type: "net", text: key + " → (cache)" });
        return cache[key].res.clone();
      }
      sim.fetchCalls++;
      sim.inflight++; sim.maxInflight = Math.max(sim.maxInflight, sim.inflight);
      let r; try { r = await baseFetch(url, init); } finally { sim.inflight--; }
      const body = await r.text();
      const res = new Response(body, { status: r.status, headers: { "content-type": "application/json" } });
      if (cacheable && r.ok) cache[key] = { res: res.clone(), at: sim.now, tags: (init.next && init.next.tags) || [], path: sim.url.split("?")[0] };
      return res;
    };
    sim.advance = (seconds) => { sim.now += seconds; };
    sim.clearCache = () => { for (const k of Object.keys(cache)) delete cache[k]; };

    /* ---------- routes ---------- */
    const paths = Object.keys(files).filter((p) => p.startsWith("app/"));
    for (const p of Object.keys(files)) {
      const isClient = /^\s*['"]use client['"]/.test(files[p]), isServer = /^\s*['"]use server['"]/.test(files[p]);
      if (!isClient && !isServer) continue;
      try {
        const m = req("./" + p);
        for (const v of Object.values(m)) if (typeof v === "function") {
          (isClient ? clientFns : serverFns).add(v);
          if (isServer) v.bind = function (...a) { const b = Function.prototype.bind.apply(this, a); serverFns.add(b); return b; };
        }
      }
      catch (e) { post({ type: "error", text: p + " : " + (e && e.message || e) }); }
    }
    sim.isServerAction = (f) => serverFns.has(f);
    function segments(file) { return file.split("/").slice(1, -1); }
    function urlSegs(file) { return segments(file).filter((s) => !/^\(.*\)$/.test(s)); }
    function match(kind, pathname) {
      const want = pathname.split("/").filter(Boolean);
      for (const f of paths) {
        if (!new RegExp("/" + kind + "\\.(tsx|ts|jsx|js)$").test("/" + f.split("/").pop())) continue;
        const segs = urlSegs(f);
        if (segs.length !== want.length) continue;
        const params = {}; let ok = true;
        segs.forEach((s, i) => { const m = s.match(/^\[(\w+)\]$/); if (m) params[m[1]] = decodeURIComponent(want[i]); else if (s !== want[i]) ok = false; });
        if (ok) return { file: f, params };
      }
      return null;
    }
    function nearest(kind, file) {
      const segs = segments(file);
      for (let i = segs.length; i >= 0; i--) {
        const dir = ["app"].concat(segs.slice(0, i)).join("/");
        const f = paths.find((p) => new RegExp("^" + dir.replace(/[()[\]]/g, "\\$&") + "/" + kind + "\\.(tsx|jsx|ts|js)$").test(p));
        if (f) return f;
      }
      return null;
    }
    function layouts(file) {
      const segs = segments(file); const out = [];
      for (let i = 0; i <= segs.length; i++) {
        const dir = ["app"].concat(segs.slice(0, i)).join("/");
        const f = paths.find((p) => new RegExp("^" + dir.replace(/[()[\]]/g, "\\$&") + "/layout\\.(tsx|jsx)$").test(p));
        if (f) out.push(f);
      }
      return out;
    }
    const comp = (file) => { const m = req("./" + file); return m.default || Object.values(m).find((v) => typeof v === "function"); };

    /* ---------- rendu serveur : on résout les Server Components async ---------- */
    async function resolve(node) {
      if (node === null || node === undefined || typeof node === "boolean" || typeof node === "string" || typeof node === "number") return node;
      if (Array.isArray(node)) return Promise.all(node.map(resolve));
      if (node && typeof node.then === "function") return resolve(await node);
      if (!React.isValidElement(node)) return node;
      const type = node.type;
      if (typeof type === "function" && !clientFns.has(type) && !(type.prototype && type.prototype.isReactComponent)) {
        return resolve(await type(node.props));
      }
      if (type === React.Suspense) return resolve(node.props.children);
      if (typeof type === "function" && clientFns.has(type) && !sim.allowFunctions) {
        for (const [k, v] of Object.entries(node.props || {})) {
          if (k === "children" || typeof v !== "function") continue;
          const target = v.__boundFrom || v;
          if (!serverFns.has(target) && !serverFns.has(v)) throw new Error("Functions cannot be passed directly to Client Components (prop « " + k + " » de <" + (type.name || "Composant") + ">). Seules les Server Actions ('use server') peuvent l'être.");
        }
      }
      const props = Object.assign({ key: node.key }, node.props);
      let kids = props.children;
      delete props.children;
      if (kids === undefined) return ce.call(React, type, props);
      kids = await resolve(kids);
      // tableau « statique » (plusieurs enfants JSX) : passé en arguments pour éviter l'avertissement de clés
      return Array.isArray(kids) ? ce.call(React, type, props, ...kids) : ce.call(React, type, props, kids);
    }

    async function build(url) {
      const [pathname, qs] = url.split("?");
      const query = Object.fromEntries(new URLSearchParams(qs || ""));
      const m = match("page", pathname);
      let tree, status = 200, base = m ? m.file : "app/page.tsx";
      try {
        if (!m) throw navError(NOT_FOUND);
        const Page = comp(m.file);
        tree = await resolve(ce.call(React, Page, { params: Promise.resolve(m.params), searchParams: Promise.resolve(query) }));
      } catch (e) {
        if (e && e.digest === REDIRECT) return { redirect: e.url };
        if (e && e.digest === NOT_FOUND) {
          status = 404;
          const nf = nearest("not-found", base);
          tree = nf ? await resolve(ce.call(React, comp(nf), {})) : ce.call(React, "h1", null, "404 - Page introuvable");
        } else {
          status = 500;
          const ef = nearest("error", base);
          if (!ef) throw e;
          tree = ce.call(React, comp(ef), { error: e, reset: () => sim.refresh() });
          post({ type: "console", level: "error", text: "Erreur serveur : " + (e && e.message || e) });
        }
      }
      for (const lf of layouts(base).reverse()) {
        const L = comp(lf);
        tree = await resolve(ce.call(React, L, { children: tree, params: Promise.resolve((m && m.params) || {}) }));
      }
      return { tree, status };
    }

    sim.render = async function (url) {
      sim.url = url || "/";
      let out = await build(sim.url), hops = 0;
      while (out.redirect && hops++ < 5) { sim.url = out.redirect; out = await build(sim.url); }
      sim.status = out.status;
      sim.renders++;
      if (!reactRoot) reactRoot = ReactDOM.createRoot(root);
      reactRoot.render(out.tree);
      post({ type: "net", text: "GET " + sim.url + " → " + sim.status + " (rendu serveur)" });
      await new Promise((r) => setTimeout(r, 30));
      return sim.status;
    };
    sim.navigate = (url) => sim.render(url);
    sim.refresh = () => sim.render(sim.url);
    function scheduleRerender() { clearTimeout(rerenderTimer); rerenderTimer = setTimeout(() => sim.refresh(), 0); }

    /* ---------- Route Handlers ---------- */
    sim.request = async function (method, url, body, headers) {
      const [pathname] = url.split("?");
      const m = match("route", pathname);
      if (!m) return { status: 404, json: null, text: "" };
      const mod = req("./" + m.file);
      const fn = mod[method.toUpperCase()];
      if (!fn) return { status: 405, json: null, text: "" };
      const init = { method: method.toUpperCase(), headers: Object.assign({ "content-type": "application/json" }, headers || {}) };
      if (body !== undefined) init.body = typeof body === "string" ? body : JSON.stringify(body);
      const res = await fn(new Request("http://localhost" + url, init), { params: Promise.resolve(m.params) });
      const text = res.status === 204 ? "" : await res.text();
      let json = null; try { json = text ? JSON.parse(text) : null; } catch (e) {}
      post({ type: "net", text: method.toUpperCase() + " " + url + " → " + res.status });
      return { status: res.status, json, text };
    };

    window.__next = sim;
    return sim;
  };
})();

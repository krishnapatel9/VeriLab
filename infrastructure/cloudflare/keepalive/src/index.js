// Keeps the free Render backend awake: Render sleeps a free service after
// 15 minutes without traffic, so this pings /health every 10 minutes.
// /health does not touch the database, so the Neon database can still sleep.

async function ping(env) {
  const started = Date.now();
  try {
    const res = await fetch(`${env.BACKEND_URL}/health`, { cf: { cacheTtl: 0 } });
    return { ok: res.ok, status: res.status, ms: Date.now() - started };
  } catch (err) {
    return { ok: false, error: String(err), ms: Date.now() - started };
  }
}

export default {
  async scheduled(_event, env, ctx) {
    ctx.waitUntil(ping(env).then((r) => console.log("keepalive", JSON.stringify(r))));
  },

  // Open the Worker's URL in a browser to test the ping by hand.
  async fetch(_request, env) {
    return Response.json(await ping(env));
  },
};

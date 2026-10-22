// Calls the separate LifeOS Agents Worker.
// Cloudflare refuses Worker -> Worker fetch() over *.workers.dev on the same account:
// it answers HTTP 404 with the plain-text body "error code: 1042" (not the agents Worker's JSON 404).
// A service binding (env.AGENTS) is the supported path; public fetch() stays as a fallback for local/other setups.
export async function lifeosAgentsRequest(env, path, payload, fetchImpl = fetch) {
  const key = env.LIFEOS_AGENTS_API_KEY;
  if (!key) throw new Error("LifeOS Agents is not connected yet. Add LIFEOS_AGENTS_API_KEY as a secret on the life-os Worker.");
  const base = (env.LIFEOS_AGENTS_URL || "https://lifeos-agents.balaadithya74.workers.dev").replace(/\/+$/, "");
  const init = {
    method: payload ? "POST" : "GET",
    headers: { authorization: "Bearer " + key, "content-type": "application/json" },
    signal: AbortSignal.timeout(20000)
  };
  if (payload) init.body = JSON.stringify(payload);
  const viaBinding = Boolean(env.AGENTS && typeof env.AGENTS.fetch === "function");
  const r = viaBinding ? await env.AGENTS.fetch(new Request(base + path, init)) : await fetchImpl(base + path, init);
  const raw = await r.text().catch(() => "");
  let data = {};
  try { data = JSON.parse(raw); } catch { /* non-JSON upstream body */ }
  if (!r.ok) {
    const u = new URL(base + path);
    const blocked = r.status === 404 && /error code:\s*1042/i.test(raw);
    const why = blocked
      ? "Cloudflare blocked a Worker-to-Worker call over workers.dev (error 1042). Add a service binding named AGENTS to the life-os Worker."
      : String(data.message || data.error || "upstream request failed");
    throw new Error(("LifeOS Agents HTTP " + r.status + " at " + u.host + u.pathname + ": " + why).slice(0, 300));
  }
  return data;
}

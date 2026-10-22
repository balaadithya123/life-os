// Calls the separate LifeOS Agents Worker.
// Cloudflare refuses Worker -> Worker fetch() over *.workers.dev on the same account:
// it answers HTTP 404 with the plain-text body "error code: 1042" (not the agents Worker's JSON 404).
// A service binding (env.AGENTS) is the supported path; public fetch() stays as a fallback for local/other setups.

const REASONING_KEYS = /^(reasoning|reasoning_content|reasoning_text|thinking|thought|thoughts|chain_of_thought|cot|scratchpad)$/i;

/** Defense-in-depth: drop internal model fields before Telegram formatting. */
export function sanitizeAgentPayload(data) {
  if (!data || typeof data !== "object") return data;
  const out = Array.isArray(data) ? [] : {};
  for (const [k, v] of Object.entries(data)) {
    if (REASONING_KEYS.test(k)) continue;
    out[k] = (v && typeof v === "object") ? sanitizeAgentPayload(v) : v;
  }
  return out;
}

/** Format agent /api/run result for Telegram — never raw JSON dumps of model internals. */
export function formatAgentTelegramOutput(data, max = 3200) {
  const safe = sanitizeAgentPayload(data) || {};
  if (typeof safe.output === "string" && safe.output.trim()) {
    return safe.output.trim().slice(0, max);
  }
  const parts = [];
  if (safe.summary) parts.push(String(safe.summary));
  if (Array.isArray(safe.steps) && safe.steps.length) {
    parts.push(safe.steps.map((s, i) => `${i + 1}. ${typeof s === "string" ? s : (s?.step || s?.title || JSON.stringify(s))}`).join("\n"));
  }
  if (safe.next_action) parts.push("Next: " + String(safe.next_action));
  const text = parts.filter(Boolean).join("\n\n").trim();
  return (text || "No output returned.").slice(0, max);
}

export async function lifeosAgentsRequest(env, path, payload, fetchImpl = fetch) {
  const key = env.LIFEOS_AGENTS_API_KEY;
  if (!key) throw new Error("LifeOS Agents is not connected yet. Add LIFEOS_AGENTS_API_KEY as a secret on the life-os Worker.");
  const base = (env.LIFEOS_AGENTS_URL || "https://lifeos-agents.balaadithya74.workers.dev").replace(/\/+$/, "");
  const timeoutMs = Number(env.LIFEOS_AGENTS_TIMEOUT_MS) > 0 ? Number(env.LIFEOS_AGENTS_TIMEOUT_MS) : 20000;
  const started = Date.now();
  const init = {
    method: payload ? "POST" : "GET",
    headers: { authorization: "Bearer " + key, "content-type": "application/json" },
    signal: AbortSignal.timeout(timeoutMs)
  };
  if (payload) init.body = JSON.stringify(payload);
  const viaBinding = Boolean(env.AGENTS && typeof env.AGENTS.fetch === "function");
  let r;
  try {
    r = viaBinding ? await env.AGENTS.fetch(new Request(base + path, init)) : await fetchImpl(base + path, init);
  } catch (error) {
    const duration_ms = Date.now() - started;
    const msg = String(error?.message || error);
    if (/abort|timeout|timed out/i.test(msg)) {
      const err = new Error(`LifeOS Agents timed out after ${duration_ms}ms (client limit ${timeoutMs}ms) at ${path}. Layer: main-worker-client.`);
      err.code = "timeout";
      err.duration_ms = duration_ms;
      err.layer = "main-worker-client";
      throw err;
    }
    throw error;
  }
  const duration_ms = Date.now() - started;
  const raw = await r.text().catch(() => "");
  let data = {};
  try { data = JSON.parse(raw); } catch { /* non-JSON upstream body */ }
  data = sanitizeAgentPayload(data);
  if (data && typeof data === "object" && data.duration_ms == null) data.duration_ms = duration_ms;
  if (!r.ok) {
    const u = new URL(base + path);
    const blocked = r.status === 404 && /error code:\s*1042/i.test(raw);
    const timedOut = r.status === 504 || data.error === "timeout";
    const why = blocked
      ? "Cloudflare blocked a Worker-to-Worker call over workers.dev (error 1042). Add a service binding named AGENTS to the life-os Worker."
      : String(data.message || data.error || "upstream request failed");
    const err = new Error(("LifeOS Agents HTTP " + r.status + " at " + u.host + u.pathname + ": " + why + ` (${duration_ms}ms)`).slice(0, 300));
    err.code = timedOut ? "timeout" : "upstream";
    err.duration_ms = duration_ms;
    err.layer = data.layer || (viaBinding ? "agents-worker-via-binding" : "agents-worker-via-fetch");
    err.status = r.status;
    throw err;
  }
  return data;
}

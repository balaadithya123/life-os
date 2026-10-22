import test from "node:test";
import assert from "node:assert/strict";
import { lifeosAgentsRequest } from "../worker/agents-client.js";

const ok = (body, status = 200) => new Response(JSON.stringify(body), { status });
const baseEnv = { LIFEOS_AGENTS_API_KEY: "k" };

test("uses the service binding when present, never public fetch", async () => {
  let seen;
  const env = { ...baseEnv, AGENTS: { fetch: async (req) => { seen = req; return ok({ ok: true, agents: [1] }); } } };
  const out = await lifeosAgentsRequest(env, "/api/agents", undefined, () => { throw new Error("public fetch must not run"); });
  assert.deepEqual(out.agents, [1]);
  assert.equal(new URL(seen.url).pathname, "/api/agents");
  assert.equal(seen.headers.get("authorization"), "Bearer k");
});

test("POST payload is forwarded through the binding", async () => {
  let body;
  const env = { ...baseEnv, AGENTS: { fetch: async (req) => { body = await req.json(); return ok({ ok: true }); } } };
  await lifeosAgentsRequest(env, "/api/run", { agent: "planner", task: "x" });
  assert.deepEqual(body, { agent: "planner", task: "x" });
});

test("error 1042 over workers.dev gives an actionable message (the reported Telegram 404)", async () => {
  const f = async () => new Response("error code: 1042", { status: 404 });
  await assert.rejects(lifeosAgentsRequest(baseEnv, "/api/agents", undefined, f),
    (e) => /HTTP 404 at .*\/api\/agents/.test(e.message) && /1042/.test(e.message) && /service binding/i.test(e.message));
});

test("a real JSON 404 from the agents Worker is reported as-is, not as 1042", async () => {
  const f = async () => ok({ ok: false, error: "not_found" }, 404);
  await assert.rejects(lifeosAgentsRequest(baseEnv, "/api/nope", undefined, f), (e) => /not_found/.test(e.message) && !/1042/.test(e.message));
});

test("401 and missing key are explicit", async () => {
  const f = async () => ok({ ok: false, error: "unauthorized" }, 401);
  await assert.rejects(lifeosAgentsRequest(baseEnv, "/api/agents", undefined, f), /HTTP 401.*unauthorized/);
  await assert.rejects(lifeosAgentsRequest({}, "/api/agents"), /not connected yet/);
});

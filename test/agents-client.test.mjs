import test from "node:test";
import assert from "node:assert/strict";
import { lifeosAgentsRequest, formatAgentTelegramOutput, sanitizeAgentPayload } from "../worker/agents-client.js";

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

test("sanitizeAgentPayload strips reasoning keys", () => {
  const clean = sanitizeAgentPayload({
    output: "hello",
    reasoning: "secret",
    reasoning_content: "secret2",
    nested: { thinking: "x", ok: 1 }
  });
  assert.equal(clean.output, "hello");
  assert.equal(clean.reasoning, undefined);
  assert.equal(clean.reasoning_content, undefined);
  assert.deepEqual(clean.nested, { ok: 1 });
});

test("formatAgentTelegramOutput never includes reasoning and prefers output field", () => {
  const text = formatAgentTelegramOutput({
    output: "Ship the brief\n1. Draft",
    reasoning: "long internal monologue",
    reasoning_content: "more secrets"
  });
  assert.equal(text, "Ship the brief\n1. Draft");
  assert.doesNotMatch(text, /reasoning|monologue|secrets/i);
});

test("formatAgentTelegramOutput builds from summary/steps when output missing", () => {
  const text = formatAgentTelegramOutput({
    summary: "Plan A",
    steps: ["do one", "do two"],
    next_action: "wait for approval",
    reasoning: "nope"
  });
  assert.match(text, /Plan A/);
  assert.match(text, /1\. do one/);
  assert.match(text, /Next: wait for approval/);
  assert.doesNotMatch(text, /nope/);
});

test("client timeout is labeled with layer and duration", async () => {
  const f = async () => {
    const err = new Error("The operation was aborted due to timeout");
    err.name = "TimeoutError";
    throw err;
  };
  await assert.rejects(lifeosAgentsRequest(baseEnv, "/api/run", { agent: "planner", task: "x" }, f), (e) => {
    return e.code === "timeout" && e.layer === "main-worker-client" && typeof e.duration_ms === "number";
  });
});

test("upstream 504 timeout preserves agents-worker layer", async () => {
  const f = async () => ok({ ok: false, error: "timeout", message: "AI request timed out", layer: "agents-worker", duration_ms: 25000 }, 504);
  await assert.rejects(lifeosAgentsRequest(baseEnv, "/api/run", { agent: "planner", task: "x" }, f), (e) => {
    return e.code === "timeout" && e.layer === "agents-worker" && e.status === 504;
  });
});

test("successful run strips reasoning from returned payload", async () => {
  const f = async () => ok({
    ok: true,
    output: "clean plan",
    reasoning: "should be removed",
    duration_ms: 12
  });
  const data = await lifeosAgentsRequest(baseEnv, "/api/run", { agent: "planner", task: "x" }, f);
  assert.equal(data.output, "clean plan");
  assert.equal(data.reasoning, undefined);
  assert.equal(data.duration_ms, 12);
});

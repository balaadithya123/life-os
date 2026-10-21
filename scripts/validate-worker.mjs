import { readFileSync } from "node:fs";
import assert from "node:assert/strict";

const worker = readFileSync("worker/index.js", "utf8");
const wrangler = readFileSync("wrangler.toml", "utf8");

assert.match(worker, /async fetch\(req,env,ctx\)/, "Worker fetch handler is missing");
assert.match(worker, /url\.pathname===["']\/health["']/, "Public health endpoint is missing");
assert.match(worker, /url\.pathname===["']\/telegram["']&&req\.method===["']POST["']/, "Telegram webhook endpoint is missing");
assert.match(worker, /x-telegram-bot-api-secret-token/, "Telegram webhook secret validation is missing");
assert.match(worker, /url\.pathname===["']\/notify["']&&req\.method===["']POST["']/, "Notification endpoint is missing");
assert.match(worker, /if\(!authed\)return new Response\(["']no["'],\{status:401\}\)/, "Notification endpoint must require bearer authentication");
assert.match(worker, /async scheduled\(controller,env,ctx\)/, "Scheduled handler is missing");

const expectedCrons = ["30 1 * * *", "0 7 * * *", "30 14 * * *"];
for (const cron of expectedCrons) {
  assert.ok(wrangler.includes(JSON.stringify(cron)), `Expected scheduled trigger missing: ${cron}`);
}
assert.match(wrangler, /name\s*=\s*"life-os"/, "Unexpected Worker name");
assert.match(wrangler, /binding\s*=\s*"KV"/, "KV binding is missing");

console.log("LifeOS static contract checks passed.");

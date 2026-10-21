const TZ_DEFAULT = "Asia/Kolkata";
const DAILY = {
  "2026-10-13": ["Physics: Kinematics"],
  "2026-10-14": ["Chemistry: Thermochemistry"],
  "2026-10-15": ["Physics: NLM & Friction"],
  "2026-10-16": ["Chemistry: Thermochemistry"],
  "2026-10-17": ["Physics: NLM & Friction"],
  "2026-10-18": ["Chemistry: Thermochemistry", "Physics: NLM"],
  "2026-10-19": ["Physics: Work-Energy-Power"],
  "2026-10-20": ["Chemistry: Chemical Equilibrium"],
  "2026-10-21": ["Physics: COM & Collisions"],
  "2026-10-22": ["Chemistry: Chemical Equilibrium"],
  "2026-10-23": ["Physics: COM & Collisions"],
  "2026-10-24": ["Chemistry: Ionic Equilibrium"],
  "2026-10-25": ["Chemistry: Chemical Equilibrium", "Physics: WPE"],
  "2026-10-26": ["Physics: COM & Collisions"],
  "2026-10-27": ["Chemistry: Ionic Equilibrium"],
  "2026-10-28": ["Physics: Rotation"],
  "2026-10-29": ["Physics: Gravitation"],
  "2026-10-30": ["Chemistry: Mole Concept & Redox", "Physics: Kinematics 1D"],
  "2026-10-31": ["Chemistry: Atomic Structure", "Maths: Complex Numbers I"]
};
const CYCLES = [
  { name: "Cycle 2", start: "2026-11-11", end: "2026-11-20", chapters: ["Physics: KTG & Thermal", "Physics: Thermodynamics", "Chemistry: GOC", "Chemistry: Hydrocarbons"] },
  { name: "Cycle 3", start: "2026-11-21", end: "2026-11-28", chapters: ["Physics: Magnetic Effects & Matter", "Chemistry: Haloalkanes", "Chemistry: Alcohols, Phenols & Ethers", "Chemistry: Aldehydes & Ketones"] },
  { name: "Cycle 4", start: "2026-11-29", end: "2026-12-09", chapters: ["Physics: Optics (Wave & Ray)", "Chemistry: Alcohols, Phenols & Ethers", "Maths: Probability"] },
  { name: "Cycle 5", start: "2026-12-10", end: "2026-12-17", chapters: ["Chemistry: p-Block"] },
  { name: "Cycle 6", start: "2026-12-18", end: "2026-12-24", chapters: ["Chemistry: Practical Chemistry"] },
  { name: "Cycle 7", start: "2026-12-25", end: "2027-01-03", chapters: [] }
];
const FIXED = [
  { start: "2026-10-29", end: "2026-11-10", name: "Coaching Cycle 1" },
  { start: "2026-11-06", end: "2026-11-09", name: "Diwali break" },
  { start: "2026-11-11", end: "2026-11-20", name: "Coaching Cycle 2" },
  { start: "2026-11-21", end: "2026-11-28", name: "Coaching Cycle 3" },
  { start: "2026-11-29", end: "2026-12-09", name: "Coaching Cycle 4" },
  { start: "2026-12-10", end: "2026-12-17", name: "Coaching Cycle 5" },
  { start: "2026-12-18", end: "2026-12-24", name: "Coaching Cycle 6" },
  { start: "2026-12-25", end: "2027-01-03", name: "Cycle 7 (full tests only)" },
  { start: "2027-01-04", end: "2027-01-20", name: "Daily full JEE Main mocks" }
];
// [date, title, category, displayed time, sort key, detail]; reconciled to config/tests.yml.
const EVENTS = [
 ["2026-10-18","Unit tests: Thermochemistry, NLM","Unit test","","99:99","Test 50 min, break 10 min, test 50 min, analysis 70 min"],
 ["2026-10-25","Unit tests: Chemical Equilibrium, WPE","Unit test","","99:99","Test 50 min, break 10 min, test 50 min, analysis 70 min"],
 ["2026-11-05","Cycle-End 1 — JEE Advanced (T06A)","Cycle-End","","14:00","3 hours · afternoon"],
 ["2026-11-07","QPT 4","QPT","17:00","17:00","Diwali target 1 of 2 · 17:00–20:00"],
 ["2026-11-08","QPT 1","QPT","17:00","17:00","Diwali target 2 of 2 · 17:00–20:00"],
 ["2026-11-10","Cycle-End 1 — JEE Mains (T07)","Cycle-End","","08:00","3 hours · morning"],
 ["2026-11-14","AITS Part Test 1 — JEE Main","AITS","09:00","09:00","09:00–12:00"],
 ["2026-11-15","AITS Part Test 1 — JEE Advanced","AITS","","99:99","Paper analysis and error-log review"],
 ["2026-11-19","Cycle-End 2 — JEE Advanced (T14A)","Cycle-End","","14:00","3 hours · afternoon"],
 ["2026-11-20","Cycle-End 2 — JEE Mains (T15)","Cycle-End","","08:00","3 hours · morning"],
 ["2026-11-25","QPT 8","QPT","17:00","17:00","Moved after Gravitation is taught on 24 Nov · 17:00–20:00"],
 ["2026-11-27","Cycle-End 3 — JEE Advanced (T21A)","Cycle-End","","14:00","3 hours · afternoon"],
 ["2026-11-28","Cycle-End 3 — JEE Mains (T22)","Cycle-End","","08:00","3 hours · morning"],
 ["2026-11-29","AITS Full Test 1 — JEE Main","AITS","09:00","09:00","09:00–12:00 · no QPT scheduled"],
 ["2026-11-30","QPT 6","QPT","17:00","17:00","Moved after AITS Full Test 1 · 17:00–20:00"],
 ["2026-12-05","AITS Part Test 2 — JEE Main","AITS","15:00","15:00","15:00–18:00"],
 ["2026-12-06","AITS Part Test 2 — JEE Advanced","AITS","","99:99","Paper analysis and error-log review"],
 ["2026-12-08","Cycle-End 4 — JEE Advanced (T29A)","Cycle-End","","14:00","3 hours · afternoon"],
 ["2026-12-09","Cycle-End 4 — JEE Mains (T30)","Cycle-End","","08:00","3 hours · morning"],
 ["2026-12-10","QPT 10","QPT","17:00","17:00","Moved off 12 Dec to avoid the AITS Main weekend · 17:00–20:00"],
 ["2026-12-13","AITS Full Test 2 — JEE Main","AITS","09:00","09:00","09:00–12:00 · no QPT scheduled"],
 ["2026-12-16","Cycle-End 5 — JEE Advanced (T36A)","Cycle-End","","14:00","3 hours · afternoon"],
 ["2026-12-17","Cycle-End 5 — JEE Mains (T37)","Cycle-End","","08:00","3 hours · morning"],
 ["2026-12-19","AITS Part Test 3 — JEE Main","AITS","15:00","15:00","15:00–18:00"],
 ["2026-12-20","AITS Part Test 3 — JEE Advanced","AITS","","99:99","Paper analysis and error-log review"],
 ["2026-12-21","QPT 3","QPT","17:00","17:00","Moved after the listed Physics teaching window (10–14 Dec) and AITS weekend · 17:00–20:00"],
 ["2026-12-23","Cycle-End 6 — JEE Advanced (T41A)","Cycle-End","","14:00","3 hours · afternoon"],
 ["2026-12-24","Cycle-End 6 — JEE Mains (T42)","Cycle-End","","08:00","3 hours · morning"],
 ["2026-12-27","AITS Full Test 3 — JEE Main","AITS","09:00","09:00","09:00–12:00 · no QPT scheduled"],
 ["2026-12-28","QPT 13 — Cycle 7 QPT","QPT","17:00","17:00","All Class 11 · 17:00–20:00 · only QPT in Cycle 7"],
 ["2027-01-02","Cycle-End 7 — JEE Mains (T48)","Cycle-End","","08:00","3 hours · morning"],
 ["2027-01-02","Cycle-End 7 — JEE Advanced (T48A)","Cycle-End","","14:00","3 hours · afternoon"],
 ["2027-01-04","Full JEE Mains Mock 1 (T49)","Mock","","99:99","3 hours · paper analysis and error-log review"],
 ["2027-01-05","Full JEE Mains Mock 2 (T50)","Mock","","99:99","3 hours · paper analysis and error-log review"],
 ["2027-01-06","Full JEE Mains Mock 3 (T51)","Mock","","99:99","3 hours · paper analysis and error-log review"],
 ["2027-01-07","Full JEE Mains Mock 4 (T52)","Mock","","99:99","3 hours · paper analysis and error-log review"],
 ["2027-01-08","Full JEE Mains Mock 5 (T53)","Mock","","99:99","3 hours · paper analysis and error-log review"],
 ["2027-01-09","Full JEE Mains Mock 6 (T54)","Mock","","99:99","3 hours · paper analysis and error-log review"],
 ["2027-01-11","Full JEE Mains Mock 7 (T55)","Mock","","99:99","3 hours · paper analysis and error-log review"],
 ["2027-01-12","Full JEE Mains Mock 8 (T56)","Mock","","99:99","3 hours · paper analysis and error-log review"],
 ["2027-01-13","Full JEE Mains Mock 9 (T57)","Mock","","99:99","3 hours · paper analysis and error-log review"],
 ["2027-01-14","Full JEE Mains Mock 10 (T58)","Mock","","99:99","3 hours · paper analysis and error-log review"],
 ["2027-01-15","Full JEE Mains Mock 11 (T59)","Mock","","99:99","3 hours · paper analysis and error-log review"],
 ["2027-01-16","Full JEE Mains Mock 12 (T60)","Mock","","99:99","3 hours · paper analysis and error-log review"],
 ["2027-01-18","Full JEE Mains Mock 13 (T61)","Mock","","99:99","3 hours · paper analysis and error-log review"],
 ["2027-01-19","Full JEE Mains Mock 14 (T62)","Mock","","99:99","3 hours · paper analysis and error-log review"],
 ["2027-01-20","Full JEE Mains Mock 15 (T63)","Mock","","99:99","3 hours · paper analysis and error-log review"]
];
const esc = function(s) { return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); };
function today(env) { return new Intl.DateTimeFormat("en-CA", { timeZone: env.TZ || TZ_DEFAULT, year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date()); }
function addDays(ymd, n) { const d = new Date(ymd + "T00:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); }
function pretty(ymd) { return new Intl.DateTimeFormat("en-GB", { timeZone: "UTC", weekday: "short", day: "numeric", month: "short" }).format(new Date(ymd + "T00:00:00Z")); }
function eventsOn(ymd) { return EVENTS.filter(e => e[0] === ymd).sort((a,b) => a[4].localeCompare(b[4])); }
function contextOn(ymd) { return FIXED.filter(f => f.start <= ymd && ymd <= f.end).map(f => f.name); }
function cycleOn(ymd) { return CYCLES.find(c => c.start <= ymd && ymd <= c.end) || null; }
function formatDay(ymd) {
  const lines = ["<b>" + esc(pretty(ymd)) + "</b>"];
  const ctx = contextOn(ymd); if (ctx.length) lines.push(ctx.map(x => "· " + esc(x)).join("\n"));
  const cycle = cycleOn(ymd);
  if (cycle && cycle.chapters.length) lines.push("\n<b>" + esc(cycle.name) + " focus</b>\n" + cycle.chapters.map(x => "· " + esc(x)).join("\n"));
  else if (cycle && cycle.name === "Cycle 7") lines.push("\n<b>Cycle 7</b>: full tests only; no chapter load.");
  const ev = eventsOn(ymd); if (ev.length) { lines.push("\n<b>Tests</b>"); for (const e of ev) { lines.push("· " + (e[3] ? esc(e[3]) + " " : "") + esc(e[1])); if (e[5]) lines.push("   <i>" + esc(e[5]) + "</i>"); } }
  if (DAILY[ymd]) lines.push("\n<b>Your chapters</b>\n" + DAILY[ymd].map(x => "· " + esc(x)).join("\n"));
  if (ymd === "2026-10-18" || ymd === "2026-10-25") lines.push("\nSelf-study target: 3 h");
  return lines.join("\n");
}
function formatWeek(from) { const lines = ["<b>Next 7 days</b>"]; for (let i=0;i<7;i++) { const d=addDays(from,i); const bits=eventsOn(d).map(e => e[1] + (e[3] ? " " + e[3] : "")); if (DAILY[d]) bits.push(...DAILY[d]); const c=cycleOn(d); if (c) bits.push(c.name); const ctx=contextOn(d); bits.push(...ctx); lines.push("<b>"+pretty(d)+"</b>: "+(bits.length?esc(bits.join("; ")):"–")); } return lines.join("\n"); }
async function sendTelegram(env, text, chatId) {
  const target = chatId == null ? env.OWNER_CHAT_ID : chatId;
  let rest = String(text || ""); const chunks=[];
  while (rest.length > 3900) { let cut=rest.lastIndexOf("\n",3900); if (cut<1000) cut=3900; chunks.push(rest.slice(0,cut)); rest=rest.slice(cut); } chunks.push(rest);
  for (const chunk of chunks) { const r=await fetch("https://api.telegram.org/bot"+env.TELEGRAM_BOT_TOKEN+"/sendMessage",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({chat_id:target,text:chunk,parse_mode:"HTML",disable_web_page_preview:true}),signal:AbortSignal.timeout(8000)}); const j=await r.json().catch(()=>({})); if(!r.ok||j.ok!==true) throw new Error("Telegram send failed: "+(j.description||r.status)); }
}
async function hash(s) { const b=await crypto.subtle.digest("SHA-1",new TextEncoder().encode(s)); return Array.from(new Uint8Array(b)).slice(0,8).map(x=>x.toString(16).padStart(2,"0")).join(""); }
function parseFeed(xml,label) { const out=[]; const blocks=xml.match(/<(item|entry)[\s>][\s\S]*?<\/\1>/gi)||[]; for(const b of blocks.slice(0,12)){const tm=b.match(/<title[^>]*>([\s\S]*?)<\/title>/i);let lm=b.match(/<link[^>]*>([\s\S]*?)<\/link>/i);if(!lm)lm=b.match(/<link[^>]*href="([^"]+)"/i);if(tm&&lm){const title=tm[1].replace(/<!\[CDATA\[|\]\]>/g,"").replace(/<[^>]+>/g,"").replace(/&amp;/g,"&").replace(/&lt;/g,"<").replace(/&gt;/g,">").trim();const link=lm[1].replace(/<!\[CDATA\[|\]\]>/g,"").replace(/&amp;/g,"&").trim();if(title&&link)out.push({title,url:link,src:label});}}return out; }
async function collectNews() { const qs=["JEE Main 2027","JEE Advanced 2027","NTA JEE Main notice","India startup funding"]; const jobs=qs.map(async q=>{try{const r=await fetch("https://news.google.com/rss/search?q="+encodeURIComponent(q+" when:2d")+"&hl=en-IN&gl=IN&ceid=IN:en",{signal:AbortSignal.timeout(6000)});if(!r.ok)throw new Error(String(r.status));return parseFeed(await r.text(),"News").slice(0,4);}catch{return [];}}); jobs.push((async()=>{try{const r=await fetch("https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=8",{signal:AbortSignal.timeout(6000)});const j=await r.json();return (j.hits||[]).filter(x=>x.title).map(x=>({title:x.title,url:x.url||("https://news.ycombinator.com/item?id="+x.objectID),src:"HN"}));}catch{return [];}})()); return (await Promise.all(jobs)).flat(); }
async function radar(env,max) { const all=await collectNews(); const candidates=[]; const seen=new Set(); for(const x of all){const k="seen:"+await hash(x.title.toLowerCase().slice(0,80));if(seen.has(k)||await env.KV.get(k))continue;seen.add(k);candidates.push({...x,k});if(candidates.length>=40)break;} if(env.GEMINI_API_KEY&&candidates.length>max){try{const prompt="Choose the most useful official JEE/NTA news first, then strong startup/product signal. Return JSON only as [{\"i\":0,\"why\":\"short reason\"}]. Items:\n"+candidates.map((x,i)=>i+". ["+x.src+"] "+x.title).join("\n");const r=await fetch("https://generativelanguage.googleapis.com/v1beta/models/"+(env.GEMINI_MODEL||"gemini-2.5-flash")+":generateContent",{method:"POST",headers:{"content-type":"application/json","x-goog-api-key":env.GEMINI_API_KEY},body:JSON.stringify({contents:[{parts:[{text:prompt}]}],generationConfig:{responseMimeType:"application/json",temperature:0.2}}),signal:AbortSignal.timeout(10000)});if(r.ok){const j=await r.json();const picks=JSON.parse(j.candidates[0].content.parts[0].text);const ranked=picks.filter(p=>candidates[p.i]).slice(0,max).map(p=>({...candidates[p.i],why:p.why}));if(ranked.length)return ranked;}}catch{}}
  return candidates.slice(0,max); }
function formatRadar(items) { if(!items.length)return ""; return "<b>Radar</b>\n"+items.map(x=>"· <a href=\""+esc(x.url)+"\">"+esc(x.title)+"</a> <i>"+esc(x.src)+"</i>"+(x.why?"\n  "+esc(x.why):"")).join("\n"); }
async function markSeen(env,items){await Promise.all(items.map(x=>env.KV.put(x.k,"1",{expirationTtl:259200}))); }
async function morningBrief(env,force){const d=today(env);if(!force&&await env.KV.get("brief:"+d))return "already sent";const parts=["Good morning, "+esc(env.OWNER_NAME||"LifeOS")+".",formatDay(d)];const upcoming=[];for(let i=1;i<=14&&upcoming.length<4;i++){const day=addDays(d,i);for(const e of eventsOn(day))upcoming.push({date:day,event:e});}if(upcoming.length)parts.push("<b>Coming up</b>\n"+upcoming.slice(0,4).map(x=>"· "+pretty(x.date)+": "+esc(x.event[1])+(x.event[3]?" "+x.event[3]:"")).join("\n"));let items=[];try{items=await radar(env,4);const n=formatRadar(items);if(n)parts.push(n);}catch{}await sendTelegram(env,parts.join("\n\n"));await markSeen(env,items);await env.KV.put("brief:"+d,"1",{expirationTtl:172800});return "sent";}
async function newsRadar(env,force){const items=await radar(env,6);const body=formatRadar(items);if(body){await sendTelegram(env,body);await markSeen(env,items);}else if(force)await sendTelegram(env,"Nothing new right now.");return body?"sent":"nothing new";}
async function evening(env){const d=addDays(today(env),1);await sendTelegram(env,"<b>Tomorrow</b>\n"+formatDay(d)+"\n\nHours done today? Reply /log 3 (just the number).");}

// LIFEOS_AGENT_MERGE_20261020: additive commands; existing schedule, webhook, and bindings preserved.
async function laAI(env,prompt){if(!env.GEMINI_API_KEY)throw new Error('Gemini API key is not configured.');const model=env.GEMINI_MODEL||'gemini-2.5-flash';const r=await fetch('https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent',{method:'POST',headers:{'content-type':'application/json','x-goog-api-key':env.GEMINI_API_KEY},body:JSON.stringify({contents:[{parts:[{text:prompt}]}],generationConfig:{temperature:0.3,maxOutputTokens:1000}}),signal:AbortSignal.timeout(14000)});const j=await r.json().catch(()=>({}));if(!r.ok)throw new Error('Gemini failed ('+r.status+'): '+String(j.error?.message||'request error').slice(0,120));const out=j.candidates?.[0]?.content?.parts?.map(x=>x.text||'').join('\n').trim();if(!out)throw new Error('Gemini returned no text.');return out.slice(0,3500);}
async function laAgent(env,cmd,arg,text){const read=async k=>{const s=await env.KV.get('la:'+k);try{return s?JSON.parse(s):[]}catch{return []}};const save=async(k,v)=>env.KV.put('la:'+k,JSON.stringify(v));if(cmd==='/task'){if(!arg)return sendTelegram(env,'Usage: /task <task>');const a=await read('tasks');const t={id:crypto.randomUUID().slice(0,8),title:arg.slice(0,200),status:'open'};a.unshift(t);await save('tasks',a.slice(0,200));return sendTelegram(env,'Saved task #'+t.id+': '+esc(t.title));}if(cmd==='/tasks'){const a=(await read('tasks')).filter(x=>x.status==='open').slice(0,20);return sendTelegram(env,a.length?'<b>Open tasks</b>\n'+a.map(x=>'· #'+esc(x.id)+' '+esc(x.title)).join('\n'):'No open tasks. Use /task <task>.');}if(cmd==='/done'){const a=await read('tasks');const t=a.find(x=>x.id===arg&&x.status==='open');if(!t)return sendTelegram(env,'Task not found. Use /tasks to see IDs.');t.status='done';await save('tasks',a);return sendTelegram(env,'Completed: '+esc(t.title));}if(cmd==='/score'||cmd==='/mistake'){if(!arg)return sendTelegram(env,'Usage: '+cmd+' <subject/topic> | <details>');const k=cmd==='/score'?'scores':'mistakes';const a=await read(k);a.unshift({text:arg.slice(0,500),at:new Date().toISOString()});await save(k,a.slice(0,100));return sendTelegram(env,(cmd==='/score'?'Score':'Mistake')+' logged: '+esc(arg));}if(cmd==='/status'){const t=await read('tasks'),s=await read('scores'),m=await read('mistakes');return sendTelegram(env,'<b>LifeOS status</b>\nOpen tasks: '+t.filter(x=>x.status==='open').length+'\nCompleted tasks: '+t.filter(x=>x.status==='done').length+'\nScores logged: '+s.length+'\nMistakes logged: '+m.length+'\nJEE schedule: unchanged');}if(cmd==='/radar')return newsRadar(env,true);if(cmd==='/ask'||cmd==='/drill'||cmd==='/spec'||!cmd.startsWith('/')){if(!arg&&!text)return sendTelegram(env,'Send a question or use /ask <question>.');let p=text;if(cmd==='/drill')p='Create 3 progressively harder JEE Main/Advanced practice questions on '+arg+'. Give a concise answer key and essential reasoning.';if(cmd==='/spec')p='Create an actionable software build spec for: '+arg+'. Include MVP, architecture, data model, security, acceptance criteria, and implementation stages.';if(cmd==='/ask')p=arg;const answer=await laAI(env,'You are a concise LifeOS assistant for JEE preparation and software projects. Be accurate and state uncertainty.\n\n'+p);return sendTelegram(env,esc(answer));}return null;}
async function command(env,text){const a=text.trim().split(/\s+/);const cmd=a[0].split("@")[0];const d=today(env);const laResult=await laAgent(env,cmd,a.slice(1).join(" "),text);if(laResult!==null)return laResult;if(cmd==="/today")return sendTelegram(env,formatDay(d));if(cmd==="/tomorrow")return sendTelegram(env,formatDay(addDays(d,1)));if(cmd==="/week")return sendTelegram(env,formatWeek(d));if(cmd==="/news")return newsRadar(env,true);if(cmd==="/log"){const h=Number(a[1]);if(!Number.isFinite(h)||h<0||h>16)return sendTelegram(env,"Send e.g. /log 3.5");await env.KV.put("hours:"+d,String(h));const keys=(await env.KV.list({prefix:"hours:"})).keys.map(x=>x.name).sort().slice(-7);const vals=await Promise.all(keys.map(k=>env.KV.get(k)));const avg=vals.reduce((s,x)=>s+Number(x),0)/vals.length;return sendTelegram(env,"Logged "+h+" h. Last "+vals.length+" days average: "+avg.toFixed(1)+" h.");}if(cmd.startsWith("/"))return sendTelegram(env,"Commands: /today /tomorrow /week /news /radar /log <hours> /task /tasks /done <id> /score /mistake /drill <topic> /spec <idea> /ask <question> /status");return sendTelegram(env,esc(await laAI(env,"Help with JEE study and software projects.\n\n"+text)));}
export default {
 async scheduled(controller,env,ctx){const jobs={"30 1 * * *":()=>morningBrief(env,false),"0 7 * * *":()=>newsRadar(env,false),"30 14 * * *":()=>evening(env)};if(jobs[controller.cron])ctx.waitUntil(jobs[controller.cron]().catch(e=>sendTelegram(env,"LifeOS error: "+esc(e.message)).catch(()=>{})));},
 async fetch(req,env,ctx){const url=new URL(req.url);const bearer=(req.headers.get("authorization")||"").replace(/^Bearer\s+/i,"");const authed=Boolean(env.NOTIFY_SECRET&&bearer===env.NOTIFY_SECRET);
  if(url.pathname.startsWith("/_setup/")){const supplied=url.pathname.slice(8);if(!env.WEBHOOK_SETUP_TOKEN||supplied!==env.WEBHOOK_SETUP_TOKEN)return new Response("not found",{status:404});if(await env.KV.get("webhook:setup:done"))return new Response("setup already used",{status:410});const r=await fetch("https://api.telegram.org/bot"+env.TELEGRAM_BOT_TOKEN+"/setWebhook",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({url:url.origin+"/telegram",secret_token:env.TG_WEBHOOK_SECRET,allowed_updates:["message"]}),signal:AbortSignal.timeout(10000)});const j=await r.json().catch(()=>({}));if(!r.ok||j.ok!==true)return new Response("Telegram webhook setup failed; check the bot token and Worker secrets.",{status:502});await env.KV.put("webhook:setup:done",new Date().toISOString());let test="not sent";try{test=await morningBrief(env,true);}catch(e){test="failed: "+String(e.message||e).slice(0,100);}return Response.json({ok:true,webhook:"configured",testMessage:test,oneTimeSetup:true},{headers:{"cache-control":"no-store"}});}
  if(url.pathname==="/health")return Response.json({ok:true,service:"life-os",schedule:"JEE Plan v5",telegramConfigured:Boolean(env.TELEGRAM_BOT_TOKEN&&env.OWNER_CHAT_ID),webhookConfigured:Boolean(await env.KV.get("webhook:setup:done"))},{headers:{"cache-control":"no-store"}});
  if(url.pathname==="/notify"&&req.method==="POST"){if(!authed)return new Response("no",{status:401});const b=await req.json().catch(()=>({}));if(!b.text)return new Response("text required",{status:400});await sendTelegram(env,(b.title?"<b>"+esc(b.title)+"</b>\n":"")+esc(String(b.text).slice(0,3500)));return new Response("sent");}
  if(url.pathname.startsWith("/run/")&&authed){const name=url.pathname.slice(5);const jobs={brief:()=>morningBrief(env,true),news:()=>newsRadar(env,true),evening:()=>evening(env)};if(!jobs[name])return new Response("unknown",{status:404});return new Response(await jobs[name]());}
  if(url.pathname==="/telegram"&&req.method==="POST"){if(req.headers.get("x-telegram-bot-api-secret-token")!==env.TG_WEBHOOK_SECRET)return new Response("no",{status:401});const update=await req.json().catch(()=>({}));const m=update.message;if(m&&m.text&&m.chat&&String(m.chat.id)===String(env.OWNER_CHAT_ID))ctx.waitUntil(command(env,m.text).catch(()=>{}));return new Response("ok");}
  return new Response("life-os",{status:200});
 }
};
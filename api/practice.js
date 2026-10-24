const MODEL = process.env.EXAMPILOT_AI_MODEL || "openai/gpt-4.1-mini";
const MAX_MATERIAL = 24000;
const MAX_ANSWER = 6000;
const rateWindowMs = 10 * 60 * 1000;
const rateLimit = 24;
const hits = globalThis.__examPilotHits || (globalThis.__examPilotHits = new Map());

function send(res, status, payload) {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  res.end(JSON.stringify(payload));
}
function text(value, max) {
  return typeof value === "string" ? value.trim().slice(0, max) : "";
}
function sentencesOf(source) {
  return source.split(/(?<=[.!?])\s+/).map(s => s.trim()).filter(s => s.length > 20);
}
function chooseContext(material, topic) {
  const sentences = sentencesOf(material);
  const terms = (topic.toLowerCase().match(/[a-z0-9]{3,}/g) || []);
  if (!sentences.length) return "";
  const matchingIndexes = [];
  sentences.forEach((sentence, index) => {
    if (terms.length === 0 || terms.some(term => sentence.toLowerCase().includes(term))) matchingIndexes.push(index);
  });
  const selectedIndexes = new Set();
  for (const index of matchingIndexes) {
    selectedIndexes.add(index);
    if (index > 0) selectedIndexes.add(index - 1);
    if (index + 1 < sentences.length) selectedIndexes.add(index + 1);
  }
  const indexes = (selectedIndexes.size ? [...selectedIndexes] : sentences.map((_, index) => index)).sort((a, b) => a - b).slice(0, 10);
  return indexes.map(index => sentences[index]).join(" ").slice(0, 9000);
}
function parseJson(content) {
  if (typeof content !== "string") throw new Error("The AI response was empty.");
  const clean = content.trim().replace(/^\uFEFF/, "");
  try { return JSON.parse(clean); } catch {}
  const match = clean.match(/\{[\s\S]*\}/);
  if (match) return JSON.parse(match[0]);
  throw new Error("The AI response was not valid JSON.");
}
function safeString(value, max = 700) {
  return typeof value === "string" ? value.trim().slice(0, max) : "";
}
function safeList(value, maxItems = 5) {
  return Array.isArray(value) ? value.slice(0, maxItems).map(v => safeString(v, 240)).filter(Boolean) : [];
}
async function askAI(system, user, maxTokens = 850) {
  const token = process.env.AI_GATEWAY_API_KEY || process.env.VERCEL_OIDC_TOKEN;
  if (!token) {
    const error = new Error("AI service authentication is not configured for this deployment.");
    error.status = 503;
    throw error;
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 25000);
  try {
    const response = await fetch("https://ai-gateway.vercel.sh/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: MODEL,
        temperature: 0.2,
        max_tokens: maxTokens,
        response_format: { type: "json_object" },
        messages: [
          { role: "system", content: system },
          { role: "user", content: user }
        ]
      }),
      signal: controller.signal
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(
        response.status === 401 ? "AI service authentication failed." :
        response.status === 402 ? "AI service credits or budget are unavailable." :
        response.status === 429 ? "AI service is temporarily rate-limited. Try again shortly." :
        response.status === 403 ? "AI service access needs verification or permission." :
        "AI service could not complete this request."
      );
      error.status = response.status === 429 ? 429 : response.status === 401 ? 503 : response.status === 402 ? 503 : response.status === 403 ? 503 : 502;
      throw error;
    }
    const content = data && data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content;
    return parseJson(content);
  } finally {
    clearTimeout(timer);
  }
}
module.exports = async function handler(req, res) {
  if (req.method === "GET") {
    res.setHeader("Allow", "GET, POST");
    return send(res, 200, {
      status: "ok",
      service: "ExamPilot practice API",
      model: MODEL,
      aiAuthConfigured: Boolean(process.env.AI_GATEWAY_API_KEY || process.env.VERCEL_OIDC_TOKEN),
      note: "This health check confirms the route is deployed; a successful POST is required to verify live model access."
    });
  }
  if (req.method !== "POST") {
    res.setHeader("Allow", "GET, POST");
    return send(res, 405, { error: "Use POST for study requests." });
  }
  const origin = req.headers.origin;
  const host = req.headers.host;
  if (origin && host) {
    try {
      const originHost = new URL(origin).host;
      if (originHost !== host) return send(res, 403, { error: "Cross-origin requests are not allowed." });
    } catch {
      return send(res, 403, { error: "Invalid request origin." });
    }
  }
  const forwarded = (req.headers["x-forwarded-for"] || "").split(",")[0].trim();
  const ip = forwarded || "unknown";
  const now = Date.now();
  if (hits.size > 1000) {
    for (const [key, value] of hits) {
      if (now - value.start > rateWindowMs) hits.delete(key);
      if (hits.size <= 800) break;
    }
  }
  const entry = hits.get(ip) || { start: now, count: 0 };
  if (now - entry.start > rateWindowMs) { entry.start = now; entry.count = 0; }
  entry.count += 1;
  hits.set(ip, entry);
  if (entry.count > rateLimit) return send(res, 429, { error: "Too many requests from this connection. Please wait a few minutes and try again." });

  const body = req.body && typeof req.body === "object" ? req.body : {};
  const action = text(body.action, 24);
  const material = text(body.material, MAX_MATERIAL);
  const topic = text(body.topic, 120);
  const question = text(body.question, 1200);
  const answer = text(body.answer, MAX_ANSWER);
  const evidence = text(body.evidence, 1600);
  const style = ["explain", "apply", "recall"].includes(body.style) ? body.style : "explain";
  if (material.length < 80) return send(res, 400, { error: "Add more course material before practising." });
  if (!topic) return send(res, 400, { error: "Enter a topic covered by your notes." });
  const context = chooseContext(material, topic);
  if (!context || context.length < 50) return send(res, 400, { error: "There is not enough readable source material for this topic." });

  try {
    if (action === "question") {
      const recent = safeList(body.recentQuestions, 8);
      const weakConcept = text(body.weakConcept, 240);
      const styleLabel = { explain: "explain a concept", apply: "apply knowledge to an example", recall: "recall key facts" }[style];
      const result = await askAI(
        "You are ExamPilot, a careful university study tutor. Use ONLY the supplied source excerpt. Never invent facts beyond it. Return one valid JSON object with keys: question (string), evidence (string), focusConcept (string), expectedIdeas (array of 2-5 short strings). The evidence value MUST be copied verbatim as one contiguous excerpt from the supplied source excerpt. Ask a useful, answerable question. Do not reveal a model answer in the question. If a weak concept is supplied, target it while remaining grounded in the source. Avoid repeating recent questions. Do not include markdown.",
        JSON.stringify({
          topic,
          requestedStyle: styleLabel,
          sourceExcerpt: context,
          avoidRepeating: recent,
          followUpWeakConcept: weakConcept || null
        }),
        650
      );
      const q = safeString(result.question, 1000);
      const ev = safeString(result.evidence, 1600);
      const focusConcept = safeString(result.focusConcept, 180);
      const expectedIdeas = safeList(result.expectedIdeas, 5);
      if (!q || !ev || !material.includes(ev) || !context.includes(ev) || !expectedIdeas.length) {
        return send(res, 502, { error: "The AI returned a question without verifiable source evidence. Please try again." });
      }
      return send(res, 200, { question: q, evidence: ev, focusConcept, expectedIdeas, mode: "ai", model: MODEL });
    }
    if (action === "evaluate") {
      if (!question || answer.split(/\s+/).filter(Boolean).length < 3) {
        return send(res, 400, { error: "Provide the question and a fuller answer before reviewing." });
      }
      if (!evidence || !material.includes(evidence)) return send(res, 400, { error: "The question's source evidence is no longer available in your notes. Create a new question." });
      const result = await askAI(
        "You are a careful university tutor assessing an answer ONLY against the supplied course material and question. Use expectedIdeas as candidate concepts to check, not as an exact-word checklist. Accept equivalent wording; do not demand exact keywords. Never mark an answer wrong solely because it uses different words. If evidence is insufficient, say so. Return one valid JSON object with keys: grade (one of 'Strong understanding','Developing understanding','Needs review','Insufficient evidence'), summary (string), includedPoints (array of 1-4 short strings), missingPoints (array of 0-4 short strings), nextStep (string), weakConcept (string), evidence (string). Keep feedback supportive, specific, and cautious. Do not claim certainty beyond the notes. The evidence value MUST be a verbatim contiguous excerpt from the supplied source excerpt. For unrelated answers, explain the mismatch without shaming the learner. Do not include markdown.",
        JSON.stringify({
          topic,
          question,
          learnerAnswer: answer,
          sourceExcerpt: context,
          questionEvidence: evidence,
          expectedIdeas: safeList(body.expectedIdeas, 5)
        }),
        850
      );
      const allowed = ["Strong understanding", "Developing understanding", "Needs review", "Insufficient evidence"];
      const grade = allowed.includes(result.grade) ? result.grade : "Developing understanding";
      const ev = safeString(result.evidence, 1600);
      if (!ev || !material.includes(ev) || !context.includes(ev)) {
        return send(res, 502, { error: "The AI feedback did not include verifiable source evidence. Please review the source and try again." });
      }
      return send(res, 200, {
        grade,
        summary: safeString(result.summary, 1000),
        includedPoints: safeList(result.includedPoints, 4),
        missingPoints: safeList(result.missingPoints, 4),
        nextStep: safeString(result.nextStep, 500),
        weakConcept: safeString(result.weakConcept, 240),
        evidence: ev,
        mode: "ai",
        model: MODEL
      });
    }
    return send(res, 400, { error: "Unknown study action." });
  } catch (error) {
    const status = Number.isInteger(error.status) ? error.status : 502;
    const message = status === 503 || status === 429 ? error.message : "The AI service is temporarily unavailable. Try again, or continue in browser preview mode.";
    return send(res, status, { error: message });
  }
};

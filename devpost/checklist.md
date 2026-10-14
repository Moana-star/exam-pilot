---
doc: checklist
status: approved
---

# Build Checklist

Build mode: fast

## Slices

- [ ] **1. Generate a grounded question from pasted material**
  Becomes usable: The learner can run ExamPilot locally, paste relevant notes, choose a topic, and receive either a material-grounded question with verified evidence or a clear unsupported-topic state.
  Why now: This includes project setup and proves the unique grounded-question kernel early, including a real local Ollama request and safe handling of unsupported topics.
  PRD ref: `prd.md > The Core Journey`; `prd.md > Features and Behavior > Material and topic entry`; `prd.md > Features and Behavior > Grounded question generation`; `prd.md > States and Boundaries`.
  Spec ref: `spec.md > Stack`; `spec.md > Where It Runs and How Someone Tries It`; `spec.md > Components > Flask routes and input checks`; `spec.md > Components > Local Ollama request, prompt, and response validation`; `spec.md > Data Model`; `spec.md > Important Failure Modes`.
  Build: Add the Flask app, single-page start/question interface, browser-memory state, word counter, same-origin question route, server-side authoritative word count, local Ollama request to `qwen2.5:3b`, separate prompt instructions, JSON Schema constrained response, exact evidence validation, unsupported-topic actions, loading/duplicate-submit handling, and recoverable question failures. Keep inputs in page memory only. Add the minimal pinned dependencies, ignore rules, and local run instructions needed to launch this usable slice.
  Verify (mechanical): Compile the Python modules; start Flask and confirm `/` loads; check required-field and oversized-material requests are rejected before the model call; with local Ollama running, call `/api/question` with a supported topic and confirm the returned question has a verbatim evidence excerpt, then use unsupported material/topic and confirm no question is returned. Confirm no user text is printed in logs.
  Learner check: Run the app, paste a short relevant course excerpt, choose a topic, and tell me whether the question feels grounded in those notes. Also try a topic the excerpt does not cover and check that the app offers recovery actions.
  Commit: `Build grounded question flow`

- [ ] **2. Complete the answer, evaluation, and evidence loop**
  Becomes usable: The learner can answer the generated question and see an approved evaluation label, explanation, included and missing or incorrect points, and clearly presented source evidence; they can retry a failed request or generate another question.
  Why now: This completes the PRD's study loop after the question path is working, and verifies the most important evaluation and evidence behavior against real material.
  PRD ref: `prd.md > The Core Journey`; `prd.md > Screens and Layout > Feedback screen`; `prd.md > Features and Behavior > Answer and grounded feedback`; `prd.md > Features and Behavior > Recoverable request failures`; `prd.md > States and Boundaries`.
  Spec ref: `spec.md > Components > Study page and browser flow`; `spec.md > Components > Flask routes and input checks`; `spec.md > Components > Local Ollama request, prompt, and response validation`; `spec.md > Components > Feedback and evidence presentation`; `spec.md > Data Model`; `spec.md > Important Failure Modes`.
  Build: Add the evaluation schema and route using material, topic, question, and answer; validate the approved label and all response fields; check every non-empty evidence excerpt against the original material; show empty-evidence points with the approved explicit note and visual distinction; implement evaluation retry with page state preserved; implement **Next Question** and return/change-material actions without losing state before a replacement result is validated. Keep responses non-streaming and do not add automatic retries.
  Verify (mechanical): Compile all Python modules and start the app; with local Ollama running, complete a real supported question and answer, confirm the label is one of the three allowed values and each displayed non-empty excerpt is present verbatim in the original notes; confirm the next-question action reuses the same notes/topic. Exercise missing/oversized input and a simulated Ollama or invalid-evidence failure to confirm inputs stay available and no invalid model output is shown.
  Learner check: Complete the full study loop with your own short material. Check the label, included/missing points, and evidence against the notes, then try **Next Question** and return to change the topic.
  Commit: `Complete grounded evaluation and evidence flow`

- [x] **3. Add in-memory course material uploads**
  Becomes usable: The learner can upload a supported document, review or edit its extracted text in the existing material box, and use the unchanged grounded question and evaluation flow.
  Why now: The initial PRD/spec deferred uploads; this focused learner-approved revision extends material entry while keeping the core study loop, evidence boundary, and browser-memory session intact.
  PRD ref: `prd.md > Screens and Layout > Starting screen`; `prd.md > Features and Behavior > Material and topic entry`; `prd.md > States and Boundaries`.
  Spec ref: `spec.md > Components > Study page and browser flow`; `spec.md > Components > Flask routes and input checks`; `spec.md > File Structure`; `spec.md > External Services and Dependencies`; `spec.md > Important Failure Modes`.
  Build: Add accessible `.txt`, `.md`, text-based `.pdf`, and `.docx` upload; extract in memory into the current textarea; enforce the 10 MB file cap and no extracted-word-count cap, while keeping the approximately 5,000-word paste limit; preserve `/api/question` and `/api/evaluate` response contracts; provide friendly parser and upload errors; add only pypdf and python-docx.
  Verify (mechanical): Exercise each supported format, malformed/empty/unsupported/encrypted/oversized inputs, supported and unsupported topics, evaluation and exact evidence validation, paste workflow, and refresh/close memory clearing. Confirm accepted extracted text uses the existing routes and no upload is persisted.
  Learner check: Upload one of your course files, review the extracted text, then complete the usual question and answer flow.
  Commit: Not requested; implementation remains uncommitted by learner instruction.

## Hands-on Checkpoints

- [ ] Early usable behavior explored — after slice 1, review whether question generation and unsupported-topic recovery feel aligned with the approved PRD.
- [ ] Final kick-the-tires exploration and feedback completed — after slice 2, try the complete study loop and report anything broken or confusing.

## Final Review

- [ ] Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- [ ] Learning activity complete — guided route, focused alternative, prior practice connected, or brief recap
- [ ] Optional edit and transfer reflection addressed — offered/declined/already covered/not applicable as appropriate
- [ ] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence: [what actually happened; real document/test/code references; unfinished work if interrupted]
Route and stops: [actual paths and symbols; guided stops completed, or reference-only route]
Edit outcome: [tried/kept/reverted/declined/not applicable; verification if changed]
Reflection: [offered/answered/declined/already covered — personal answer belongs only in the ignored profile]
Activity mode: [live app and editor, explicit static fallback, focused alternative, prior practice, or recap]

## Revisions

- Switched the AI provider from OpenAI's hosted API to local Ollama `qwen2.5:3b` at the learner's request because OpenAI API credits are unavailable; retained the question JSON contract, grounding prompt, and exact evidence validation.
- Added the learner-approved upload alternative after the original PRD/spec deferred it. This revision adds only in-memory extraction and leaves the material/question/evaluation pipeline and approved grounding rules intact. The learner explicitly requested implementation without a commit.

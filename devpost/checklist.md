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
  Commit: Included in commit `91d6b08` (`Improve source-grounded study question generation`), subsequently published to the public `main` branch. Automated and hands-on verification still need to be completed.

## Automated verification

- [x] GitHub Actions workflow is present at `.github/workflows/tests.yml` and uses the standard-library `unittest` runner on Python 3.11 and 3.12.
- [x] Latest verified code/test run for commit `e039993`: dependency installation, Python compilation, and unit tests passed on Python 3.11 and 3.12, including tests that reject non-matching evaluation evidence and confirm the route returns a recoverable error. Run: [38555409427](https://github.com/Moana-star/exam-pilot/actions/runs/38555409427).
- [x] Public repository contains no tracked `.env`, PDF, DOC/DOCX, or learner-profile file in the inspected tree. Keep checking staged file lists before future commits.
- [x] Correct local test command documented: `python -m unittest discover -s tests -v`. The attempted `python -m pytest -q` returned `No module named pytest`; this project does not declare pytest and its tests use Python's built-in `unittest`, so installing pytest is not required to run the supported suite.
- [ ] Local end-to-end browser + Ollama run still required; CI does not exercise a live Ollama model or the user's installed browser.

## Hands-on Checkpoints

- [ ] Early usable behavior explored — after slice 1, review whether question generation and unsupported-topic recovery feel aligned with the approved PRD.
- [ ] Final kick-the-tires exploration and feedback completed — after slice 2, try the complete study loop and report anything broken or confusing.

## Final Review

- [ ] Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- [x] Learning activity complete — a reference-only code tour and a focused large-note debugging practice are documented in [`devpost/app-map.html`](app-map.html). This does not replace live app testing.
- [x] Optional edit and transfer reflection addressed — transfer prompts are included in the app map; no personal reflection was recorded.
- [x] `devpost/app-map.html` generated from the current source tree, reviewed for route/file links, and linked from the README. It includes the project-grounded debugging practice.

Activity and evidence: Source files reviewed: `app.py`, `ai_service.py`, `context_service.py`, `material_service.py`, `static/app.js`, `templates/index.html`, `tests/`, and `.github/workflows/tests.yml`. CI evidence: run [38555409427](https://github.com/Moana-star/exam-pilot/actions/runs/38555409427) passed for code/test commit `e039993` on Python 3.11 and 3.12. Outstanding: reproduce and resolve the reported question-generation failure with the learner's approximately 20,067-word operating-systems PDF, then complete a full live question → answer → evaluation → next-question session.
Route and stops: Material input and upload → `POST /api/material` / `material_service.extract_material()` → `POST /api/question` / `ai_service.generate_question()` → `context_service.select_relevant_context()` → local Ollama request and exact-evidence validation → `POST /api/evaluate` / `ai_service.evaluate_answer()` → feedback and next question in `static/app.js`.
Edit outcome: Documentation only in this finalization pass; no application source code was changed. The map, demo guide, and submission draft were added. The live large-PDF failure is not marked fixed because it has not been reproduced in a live local runtime here.
Reflection: Transfer prompts included in `app-map.html`; no personal profile content collected or published.
Activity mode: Reference-only source tour and focused debugging alternative; a live local app/model session remains required.

## Revisions

- Switched the AI provider from OpenAI's hosted API to local Ollama `qwen2.5:3b` at the learner's request because OpenAI API credits are unavailable; retained the question JSON contract, grounding prompt, and exact evidence validation.
- Added the learner-approved upload alternative after the original PRD/spec deferred it. This revision adds only in-memory extraction and leaves the material/question/evaluation pipeline and approved grounding rules intact. The learner initially requested implementation without a commit; the implementation was later staged, committed, and published to GitHub.

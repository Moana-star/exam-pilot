---
doc: prd
status: approved
---

# Course-Grounded Study Partner — Product Requirements

A focused study app for university students that turns their own course material into active practice and feedback they can trace back to that material.
Source: `scope.md > Who It's For`, `The Unique Kernel`, and `The Core Loop`. **ExamPilot** is the provisional working product name; the descriptive document title is retained for clarity.

## The Core Journey

1. **Arrive and start.** The student opens the app and sees what it does, where to paste or upload course material, where to enter a topic, and how to begin. No account or setup flow comes first.
2. **Provide study material and topic.** The student pastes their own course material or uploads a supported file, then types a topic they want to practice. Both material and topic are required.
3. **Get one grounded question.** The student selects **Generate Question**. The app presents one focused question about the selected topic, based only on the material they supplied. It indicates that the supplied material was the basis for the question.
4. **Answer in their own words.** The student writes a free-form answer and submits it. Multiple choice, timers, and configuration steps are not part of this flow.
5. **Understand the evaluation.** The app labels the answer **Correct**, **Partially correct**, or **Needs improvement**; explains why; identifies supported points the student included and important supported points they missed or got wrong; and shows the relevant passage from the supplied material. The feedback helps the student improve their understanding rather than simply revealing a correct answer.
6. **Continue or change the session.** **Next Question** generates another focused question using the same material and topic. A secondary action lets the student return to the start to provide different material or choose another topic.

A successful session demonstrates this complete chain on screen: supplied material ? chosen topic ? grounded question ? student's answer ? evaluation ? supporting evidence ? next question.
Source: `scope.md > The Core Loop` and `What "Working" Looks Like`.

## Screens and Layout

### Starting screen

- App name and short tagline at the top. The suggested tagline is “Turn your notes into practice.”
- A brief supporting line explains that questions and feedback use the student's own course material.
- A large text area labeled **Paste your course material here**.
- The text area remains the primary material input. Pasted material supports approximately 5,000 words. Offer an accessible alternative file picker for .txt, .md, .pdf, and .docx files up to 10 MB, without an extracted-word-count limit. PDFs must contain extractable text; scanned PDFs are not OCRd. Extracted text is placed in the same editable text area.
- A topic field labeled **What topic do you want to practice?**
- One prominent **Generate Question** button.
- A nearby note says the question and feedback are based only on the supplied material.
- Missing-field validation appears near the relevant field; the student can correct it on this screen.

### Question screen

- Shows the selected topic and one prominent question.
- Briefly indicates that the question was generated from the student's supplied material.
- Provides a large answer area and a prominent **Submit Answer** button.
- Does not include multiple choice, timers, difficulty or question-type selectors, or other session controls.

### Feedback screen

- Shows the overall evaluation, explanation, included points, missing or incorrect points, and a clearly recognizable evidence section containing the relevant passage from the supplied material.
- Makes **Next Question** the primary action.
- Offers a secondary action to return to the start and change material or topic.

Unsupported-topic and failed-request states appear within the flow and preserve a clear way to continue or recover; they do not require a separate technical error page.
Source: `scope.md > The Core Loop`, `The POC Boundary`, and `Explicitly Cut`.

## Look and Feel

- Clean, calm, academic, and minimal, with generous whitespace and clear visual hierarchy.
- Warm off-white or light background, with deep navy or dark blue for headings and important controls.
- Restrained green or teal for positive/correct states and grounded evidence; neutral grays for secondary text and borders.
- Modern, highly readable typography with clear differences between the app name, headings, question, answer area, and feedback.
- The question and feedback are the visual focus of their screens. Evidence has its own recognizable section rather than appearing as a footnote.
- Rounded cards and subtle borders or shadows are appropriate when useful.
- Avoid excessive gradients, glowing AI effects, animated backgrounds, and futuristic AI styling. Keep the visual treatment simple enough to support a reliable MVP.
Source: learner's PRD interview; supports `scope.md > Inspiration & Identity`.

## Features and Behavior

### Material and topic entry

- The student can paste course material or upload a supported file, review or edit its extracted text, and type a topic on the starting screen.
- Both fields are required before question generation can proceed.
- If the material is empty, show **“Please paste your course material first.”** near the material field.
- If the topic is empty, show **“Please enter a topic to practice.”** near the topic field.
- If both are empty, show both messages. Keep the fields available for correction in place; do not show a modal or technical error page.
- Do not attempt question generation while either required field is empty.
- Support approximately 5,000 words of pasted material. Uploads accept any extracted word count, limited only to .txt, .md, text-based .pdf, and .docx files up to 10 MB; extract in memory only. Give friendly errors for unsupported, invalid, unreadable, encrypted, empty, or oversized files. Do not add OCR. Large prompts that the local model cannot handle follow the friendly request retry/error flow.

Acceptance criteria:

- Submitting with either required field empty shows the applicable inline message and does not start question generation.
- When both fields contain input, the student can proceed directly to question generation.
- Pasted material uses the existing approximately 5,000-word UI limit. Uploaded material is accepted regardless of extracted word count, subject to the 10 MB file-size limit.

### Grounded question generation

- Generate one focused question about the topic the student typed, using only the supplied course material as the source.
- Do not use web searches, external study resources, or unrelated general knowledge to create or justify the question.
- Indicate that the question is based on the student's material.
- If the material does not cover the selected topic sufficiently, do not generate a question from outside knowledge. Explain that the topic is not sufficiently covered and that the app uses only the supplied material as its source of truth.
- In that unsupported-topic state, offer **Choose Another Topic** and **Add More Material**. The first returns to topic entry; the second returns to material entry.

Acceptance criteria:

- With material that supports a selected topic, the question is relevant to that topic and based only on the supplied material.
- With material that does not sufficiently support the selected topic, no unsupported question is presented; the student sees the explanation and both recovery actions.

### Answer and grounded feedback

- Accept a free-form answer written in the student's own words.
- Evaluate the answer only against the supplied material. Do not use web searches or unrelated general knowledge to justify the evaluation.
- Show one of three labels: **Correct**, **Partially correct**, or **Needs improvement**. Do not show a numerical score.
- Use these label rules:
  - **Correct:** The answer covers the important points supported by the supplied material and contains no meaningful incorrect claims.
  - **Partially correct:** The answer demonstrates some correct understanding but misses important supported points or contains a limited misunderstanding.
  - **Needs improvement:** The answer misses most important supported points, substantially misunderstands the material, or does not adequately answer the question.
- Explain the evaluation in natural language, identify important supported points present in the answer and material-supported points that are missing or incorrect, and show the relevant passage from the supplied material.
- Do not present a claim as evidence from the material unless that claim is supported by the material. Do not simply give the student a correct answer in place of explanatory feedback.
- Make **Next Question** the primary action. It generates another focused question from the same supplied material and selected topic. Offer a secondary return to the start to change material or topic.

Acceptance criteria:

- After submission, the feedback screen shows an evaluation label, its explanation, included and missing or incorrect points, and a relevant passage that can be found in the supplied material.
- The label matches the agreed rules for completeness, supported understanding, and meaningful errors; the feedback explains the reasoning instead of relying on the label alone.
- Unsupported claims are not attributed to the supplied material as evidence.
- Selecting **Next Question** starts another question using the same material and topic; the student can also choose the secondary action to start with different material or a different topic.

### Recoverable request failures

- If question generation fails, show a friendly message such as **“Something went wrong while generating your question. Your material and topic are still here, so you can try again.”** Provide **Try Again** as the primary action and a secondary way to return to the previous step.
- If evaluation fails, show a friendly message such as **“We couldn’t evaluate your answer right now. Your answer is still here, so you can try again.”** Provide **Try Again** as the primary action and a secondary way to return to the previous step.
- Preserve the supplied material, selected topic, and answer as applicable so the student does not have to re-enter them.
- Never show raw technical errors or fabricate a question, evaluation, or evidence as though a failed request succeeded. Sophisticated retry logic, offline AI, and automatic recovery are not required.

Acceptance criteria:

- A failed question request leaves the material and topic available and offers **Try Again**; it does not display a fabricated question.
- A failed evaluation leaves the material, topic, and answer available and offers **Try Again**; it does not display fabricated feedback or evidence.

## States and Boundaries

- **First use:** The starting screen immediately explains the product and lets the student begin without login, dashboard, or setup steps.
- **Normal study flow:** Starting screen ? one question ? answer ? feedback/evidence ? next question or return to the start.
- **Missing material or topic:** Show inline messages beside the missing fields and let the student correct them in place.
- **Topic unsupported by material:** Explain that no grounded question can be made; offer **Choose Another Topic** and **Add More Material**. This is a normal product state, not a technical error.
- **Question request failed:** Preserve material and topic, show a friendly failure message, and offer retry or return to the previous step.
- **Evaluation request failed:** Preserve material, topic, and answer; show a friendly failure message and offer retry or return to the previous step.
- **Grounding boundary:** Student-provided material is the only source for question content, evaluation, and supporting evidence. Do not use web searches, external study resources, or unrelated general knowledge; never present unsupported claims as evidence from the material.
- **Session boundary:** No accounts, dashboards, or long-term progress tracking are included. The student can continue with another question in the current study flow or return to the start.

## Product Decisions

- The MVP focuses on university students preparing for tests or exams who have course material but need help turning it into practice. This makes the intended user and problem specific. Source: `scope.md > Who It's For`.
- The student's material is the sole source for both questions and feedback, and feedback must show traceable supporting evidence. This is the product's distinguishing value. Source: `scope.md > The Unique Kernel`.
- The MVP accepts pasted or uploaded material and a student-entered topic, then generates one question at a time. Automatic topic detection remains excluded. Upload is a narrow addition approved after initial scope and does not change the grounded study loop.
- Answers are free-form, not multiple choice, so students practice explaining their understanding.
- Feedback uses qualitative labels and explanations, not numeric scores or gamification.
- A fully offline system is not required; students do not depend on web searches or external study resources for study content. Reliability of the complete loop takes priority.
- The visual direction is calm, academic, readable, and restrained, rather than generic chatbot or futuristic AI styling.
- **ExamPilot** is the provisional working product name; the descriptive PRD title is retained for clarity. The tagline remains provisional.

## What We're Building

- One starting screen for pasted course material with its approximately 5,000-word UI limit or uploaded course material limited only by the 10 MB file-size cap, and a student-entered topic. Upload accepts .txt, .md, text-based .pdf, and .docx and fills the same editable material field.
- Required-field validation for material and topic.
- One-question-at-a-time practice grounded only in supplied material.
- A free-form answer step.
- A material-grounded evaluation with a qualitative label, explanation, included and missing or incorrect points, and traceable supporting evidence.
- A safe unsupported-topic state with actions to choose another topic or add material.
- A next-question action using the same material and topic, plus a secondary way to return to the start.
- Friendly, recoverable question-generation and evaluation failure states that preserve student input and never fabricate output.
- A one-minute demo of the complete study loop and its material-grounded feedback.

## Deferred From the POC

- OCR and upload formats beyond .txt, .md, text-based .pdf, and .docx remain out of scope.
- Automatic topic detection: the student chooses the topic to keep the MVP focused.
- User accounts and authentication: not needed for a single-session proof of concept.
- Dashboards and long-term progress tracking: not needed to demonstrate a grounded practice session.
- Leaderboards and gamification systems: not part of the core learning value.
- Social or community features: not needed for the individual study loop.
- Large question banks: the MVP demonstrates one question at a time from supplied material.
- A fully offline AI system, sophisticated retry logic, or automatic recovery: the agreed MVP prioritizes a reliable end-to-end loop with a clear retry action.

## Possible Later Enhancements

No later enhancements have been committed. Revisit deferred items only after the core study loop is demonstrated reliably.

## Non-Goals

- General-purpose chatbot features: the product is a focused practice partner.
- Web search or external study resources: they would weaken the promise that the student's own material is the source of truth.
- Questions or feedback based on unrelated general knowledge: grounding in supplied material is central to the product.
- Unsupported claims presented as evidence: evidence must be traceable to the supplied material.
- Multiple-choice questions, timers, difficulty selectors, question-type settings, numerical scores, streaks, or other gamification: these add controls or incentives outside the agreed MVP.
- Login screens, dashboards, accounts, and long-term tracking: outside the single-session proof of concept.
- Excessive AI-themed visual effects or complex visual treatment: reliability and clarity take priority.

## Open Questions

The hosted AI extension has been implemented in code but still requires a live request test in the deployed browser, including verification of authentication, credits/provider access, evidence grounding, and fallback behavior. **ExamPilot** remains the working product name; the tagline is provisional.


## Implementation update — hosted AI extension (24 October 2026)

The original PRD describes the local Flask/Ollama MVP. The hosted Vercel page now adds an optional AI path while retaining the browser-only preview as a fallback.

### Added hosted behavior

- The learner explicitly opts in before notes and answers are sent for AI processing.
- `POST /api/practice` accepts `question` and `evaluate` actions, uses Vercel AI Gateway with the configured/default model, limits request sizes, applies a best-effort per-instance rate limit, and returns recoverable errors for missing authentication, unavailable credits, or provider failure.
- Question generation uses topic-relevant context and recent questions, returns a question plus a verbatim source excerpt and expected concepts, and can use the previous evaluation's weak concept to target a follow-up.
- Evaluation returns a qualitative label, included concepts, concepts to review, a suggested next step, and a source excerpt. It accepts equivalent wording and must not treat keyword overlap as correctness.
- The server validates that the selected evidence excerpt occurs exactly in the original material before returning it.
- When AI mode is off or an AI request fails, the page can continue with browser templates and word-overlap feedback, explicitly labelled as preview-only.
- Study history remains in the open page only; no database or account system is added.

### Privacy and release conditions

When AI mode is enabled, notes are sent to the ExamPilot API for context selection; selected context, question, and answer are sent to the AI service. The page discloses this before opt-in. Do not submit confidential content. Do not claim the hosted AI path is verified until a live question request and a live answer-evaluation request both succeed in the deployed browser and their evidence is checked against the supplied notes. A Vercel `READY` status alone is not sufficient evidence of model access or quality.

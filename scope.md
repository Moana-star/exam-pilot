---
doc: scope
status: approved
---

# ExamPilot

One line: ExamPilot turns a student's own course notes into focused practice questions and evidence-grounded answer feedback.

## The Unique Kernel

Practice is grounded in the material the learner supplies, rather than a general chatbot's outside knowledge. ExamPilot checks that displayed evidence excerpts occur in the original notes, making the basis for feedback visible.

## Who It's For

A university or college student revising lecture notes before an exam who needs to test understanding instead of repeatedly rereading material.

## The Core Loop

The student pastes notes or uploads a supported document, chooses a topic, generates a question, answers it, reviews the evaluation and source evidence, and requests another question from the same material and topic. They can change the material or topic when ready.

## Inspiration & Identity

A focused, calm study partner: clear question-first layout, direct feedback, visible source grounding, and recoverable errors. The experience should feel like purposeful exam practice rather than an open-ended chatbot.

## Why This Matters to the Learner

Students need a practical way to check whether they understand their own course material and to see which parts of an answer need more work.

## What "Working" Looks Like

A learner completes the loop using their own notes: ExamPilot asks a relevant question, evaluates the learner's answer, shows feedback with source excerpts, and generates further distinct questions without requiring the learner to re-enter the material.

## The POC Boundary

- Flask application with a browser-based study flow.
- Pasted notes and supported TXT, Markdown, text-based PDF, and DOCX uploads.
- Topic-relevant context selection for longer material.
- Local Ollama inference using qwen2.5:3b.
- Structured question and evaluation responses with server-side validation.
- Evidence excerpt checks against the original supplied material.
- In-browser session state; no accounts, database, or saved study history.
- Recoverable unsupported-topic and request-error states.

## Later

Real-user usability testing, accessibility refinements informed by feedback, broader model-quality evaluation, and deployment suitable for public access.

## Explicitly Cut

- **Hosted AI APIs:** local Ollama keeps inference on the learner's machine by default and avoids requiring a hosted API key.
- **Accounts and saved history:** not required to demonstrate the core study loop and would add personal-data handling.
- **Web search and outside study sources:** would weaken the supplied-material grounding boundary.
- **Scanned-PDF OCR:** outside the current proof-of-concept boundary; image-only PDFs are not supported.
- **Leaderboards, social features, and complex dashboards:** do not prove the core learning loop.


## Differentiator: the Evidence-Based Learning Loop

ExamPilot should make one complete learning loop clear and useful: **student material → topic-focused practice → answer → cautious feedback → visible source passage → next practice or revision**. The distinctive value is traceability to the student's supplied notes, not a claim of unlimited generation or perfect grading.

The application should distinguish three things:
- **Question relevance:** does the question address the chosen topic and stay within the supplied material?
- **Feedback usefulness:** does feedback explain included ideas and important gaps without pretending uncertain results are definitive?
- **Evidence traceability:** can the learner locate the quoted source passage in their own material?

Exact excerpt matching proves that a passage exists in the notes; it does not prove that the model interpreted it correctly. Feedback must remain reviewable by the learner.

## Deployment boundary

ExamPilot now has three explicit execution paths:

- **Hosted AI mode (opt-in):** the Vercel page calls `POST /api/practice`, which uses Vercel AI Gateway for model-generated questions and concept-level evaluation. The server validates request size, rate-limits best-effort per function instance, and verifies returned evidence excerpts against the supplied notes. It uses Vercel OIDC when available or a server-side AI Gateway key; secrets never belong in browser code.
- **Browser-only preview:** when AI mode is unchecked or the AI request fails, the page can use finite question templates and word-overlap feedback. This fallback is not semantic grading and must be labelled honestly.
- **Local AI app:** the Flask application uses a locally running Ollama model for model-generated questions and evaluation. This is separate from the hosted endpoint.

When hosted AI mode is enabled, the full notes are sent to the ExamPilot API for context selection, and selected relevant context plus the learner's answer is sent to the AI service. The page explains this before the learner opts in. The app does not save study history. A Vercel deployment marked READY proves deployment completion, not that live model requests succeed; hosted AI must be tested before the demo claims it works.

## Pre-submission priorities

1. Verify the existing workflow before adding new features.
2. Fix any broken or confusing interactions.
3. Improve evidence-based feedback and the learner's next step.
4. Polish mobile layout, keyboard focus, labels, contrast, and error recovery.
5. Run and record the evaluation plan.
6. Record a truthful short demo and verify the Devpost submission requirements.

Accounts, cloud sync, leaderboards, and decorative analytics remain out of scope until the core learning loop is proven reliable.

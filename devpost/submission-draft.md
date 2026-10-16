# ExamPilot — Devpost Submission Draft

**Status:** Draft for the creator to review and adapt. This document does not submit the project or claim that untested behavior has passed.

## Project title

**ExamPilot — Turn Your Notes Into Practice**

## One-line summary

A source-grounded study app that turns a student's own course material into practice questions and evidence-linked feedback.

## What it does

ExamPilot lets a learner paste course notes or upload a supported TXT, Markdown, text-based PDF, or DOCX file, choose a topic, and generate one focused practice question. The learner answers in their own words and receives a qualitative evaluation—Correct, Partially correct, or Needs improvement—with an explanation of included and missing points.

The app is designed to use only the supplied course material for the question and feedback. It checks that every non-empty evidence excerpt is an exact substring of the original material before displaying it. If the notes do not sufficiently cover a topic, the app should return an unsupported-topic state instead of inventing a question from unrelated knowledge.

## Inspiration

Students can spend a long time rereading lecture notes without checking whether they can explain the important ideas. General-purpose AI chatbots can also bring in outside information, which may not match the material a lecturer expects students to learn. ExamPilot explores a narrower approach: turn the student's own notes into active recall practice and make the basis for feedback visible.

## How it was built

- **Python and Flask** serve the study page and the JSON API routes.
- **HTML, CSS, and JavaScript** implement the single-page study flow and keep the active session in browser memory.
- **Ollama with qwen2.5:3b** provides local model inference through Ollama's local HTTP API.
- **JSON response schemas and server-side validation** constrain the shape of model responses.
- **Context selection** sends a bounded, topic-relevant section from longer notes rather than the entire document.
- **Exact evidence checks** reject non-empty excerpts that do not occur literally in the original material.
- **pypdf and python-docx** extract text from supported uploads in memory.

The project does not require a hosted AI API key or a database. Uploaded files are not saved by the app. Scanned PDFs are not OCR'd.

## A challenge and design decision

A key challenge is using long notes without losing the link between the context sent to the model and the original source. ExamPilot selects relevant source spans and validates evidence against the original material. This preserves the evidence boundary without sending the entire long document in every model request.

A trade-off remains: exact quote matching verifies that a quote exists in the notes, not that the model's interpretation is correct. Learners should compare the explanation with the source material.

## What is distinctive

- Questions and feedback are intended to stay within the student's supplied notes.
- Evidence excerpts are checked on the server before being returned to the browser.
- Large uploads have a file-size cap, while pasted material retains a separate word limit.
- Failed or unsupported requests have recovery paths rather than displaying fabricated results.
- The project is deliberately small: no accounts, database, history, leaderboards, or general-purpose chatbot.

## Technology

Python · Flask · HTML · CSS · JavaScript · Ollama · qwen2.5:3b · pypdf · python-docx · GitHub Actions

## Repository and technical map

- Public repository: https://github.com/Moana-star/exam-pilot
- App map: https://github.com/Moana-star/exam-pilot/blob/main/devpost/app-map.html
- Automated checks: https://github.com/Moana-star/exam-pilot/actions

## Verification note — update before submitting

The current `main` commit `d8b5de2` passed [GitHub Actions run 38905593467](https://github.com/Moana-star/exam-pilot/actions/runs/38905593467), which runs compilation and the unit-test suite on Python 3.11 and 3.12. I also cloned the public `main` branch into a clean test environment, installed the pinned dependencies, and ran the full suite: **30 tests passed**. A route smoke check returned HTTP 200 for the study page and recoverable HTTP 400 responses for empty API requests. These checks verify the automated baseline; they do not replace a real Ollama-backed browser rehearsal.

**Before submission, complete a real local browser session with Ollama:** generate a question from supported notes, answer it, inspect the evaluation and exact excerpts, and try Next Question. Specifically investigate the previously reported failure with a roughly 20,067-word operating-systems PDF. Do not describe this live flow as verified until it has been observed working.

## What is next

The next priority is to rehearse the full end-to-end study loop on the target laptop, resolve any reproducible failure, and record a short demo that shows the real application behavior. Longer-term improvements should follow observed learner feedback rather than expanding the MVP before its core loop is reliable.

## Creator review before copying into Devpost

- Replace or refine any wording so it accurately reflects your own experience.
- Add the actual demo-video URL after recording and uploading it.
- Check the event's exact submission fields, time limit, eligibility, and deadline in Devpost.
- Only claim features and live-test results you personally verified.

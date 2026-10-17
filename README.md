# ExamPilot

[![Test ExamPilot](https://github.com/Moana-star/exam-pilot/actions/workflows/tests.yml/badge.svg)](https://github.com/Moana-star/exam-pilot/actions/workflows/tests.yml)

ExamPilot turns your course notes into one focused practice question, then evaluates your answer with feedback grounded in the same source material.

## What it does

- Accepts pasted notes (up to about 5,000 words) or an uploaded `.txt`, `.md`, text-based `.pdf`, or `.docx` file (up to 10 MB).
- Extracts supported uploads in memory and puts the text in the editable material box before study begins.
- Selects a bounded, topic-relevant context from longer notes rather than sending the entire document to the model.
- Generates one question or clearly reports that the topic is not sufficiently covered.
- Evaluates the learner's answer as **Correct**, **Partially correct**, or **Needs improvement**, with included/missing points and source excerpts.
- Checks evidence excerpts against the supplied source before returning them to the browser.
- Keeps the current study session in browser memory; there is no account, database, or saved study history.

**Grounding boundary:** the supplied course material is the app's only study source. It does not use web search or a hosted AI API. The local Ollama model can still make mistakes, so learners should compare feedback with their notes.

**File limitations:** scanned/image-only PDFs are not OCR'd. Unsupported formats, unreadable files, and password-protected PDFs are rejected with a recoverable message.

## Requirements

- Windows, macOS, or Linux with Python 3.11 or newer.
- [Ollama](https://ollama.com/) installed locally.
- The `qwen2.5:3b` model downloaded in Ollama.

## Run locally on Windows

Open PowerShell in this repository folder.

Create and activate a virtual environment, then install the pinned dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation because script execution is disabled, allow it for this PowerShell process only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Download the model once and check that Ollama can see it:

```powershell
ollama pull qwen2.5:3b
ollama list
```

Start the app:

```powershell
python -m flask --app app run
```

Open <http://127.0.0.1:5000> in your browser. Keep Ollama running while using ExamPilot.

## Run the tests

With the virtual environment active and dependencies installed:

```powershell
python -m compileall -q app.py ai_service.py context_service.py material_service.py tests
python -m unittest discover -s tests -v
```

The automated tests exercise context selection, evidence validation, upload limits, and API behavior. The test suite mocks model requests where appropriate; a real study session still requires Ollama and the downloaded model.

GitHub Actions runs compilation and the unit tests on Python 3.11 and 3.12 for pushes and pull requests to `main`.

## Project structure

| Path | Purpose |
| --- | --- |
| `app.py` | Flask page and API routes |
| `ai_service.py` | Local Ollama requests, response schemas, and validation |
| `context_service.py` | Selects source spans relevant to the requested topic |
| `material_service.py` | In-memory text, Markdown, PDF, and Word extraction |
| `templates/index.html` | Study page markup |
| `static/app.js` | Browser study flow and feedback display |
| `static/styles.css` | Page styling |
| `tests/` | Automated unit and API tests |
| `devpost/` | Product requirements, technical spec, and build checklist |

## Project tour and submission preparation

- [App map and code tour](devpost/app-map.html) — traces the browser flow, Flask routes, context selection, Ollama validation, safety boundaries, and the remaining local verification.
- [Demo recording guide](devpost/demo-script.md) — a short, honest recording plan with a preflight checklist.
- [Devpost submission draft](devpost/submission-draft.md) — editable project summary and verification note. Review it and add your actual demo URL before submitting.
- [Build checklist](devpost/checklist.md) — separates automated checks from hands-on checks that still need a real local run.

## Devpost Learn planning documents

The required planning documents are available at the repository root:

- [Scope](scope.md)
- [Product requirements (PRD)](prd.md)
- [Technical specification](spec.md)
- [MIT license](LICENSE)

The longer project planning and build notes remain in [`devpost/`](devpost/).

## API routes

- `POST /api/material` — extract a supported uploaded file into text.
- `POST /api/question` — generate a topic-grounded question or an unsupported-topic response.
- `POST /api/evaluate` — evaluate an answer and validate returned source excerpts.

## Privacy and safe use

Uploaded file content is extracted in memory and is not saved as an uploaded file by the app. The current study session is held in the open browser page; refreshing or closing the page clears that session. AI requests are sent to the Ollama service at `http://127.0.0.1:11434` on the same machine by default.

The included Flask command starts a **development server** intended for local use. Do not expose it directly to the public internet or treat it as a production deployment without adding and reviewing appropriate production hosting, request protections, and operational controls.

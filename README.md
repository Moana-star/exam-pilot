# ExamPilot

ExamPilot turns pasted or uploaded course material into a focused practice question, then evaluates the student's answer with feedback grounded in that same material.

Pasting material is supported. You can also upload a `.txt`, `.md`, `.pdf`, or `.docx` file (up to 10 MB). Uploads are read in memory, converted to text, and placed in the same editable material box used by the paste workflow. PDF support is for text-based PDFs only; scanned/image-only PDFs are not OCR'd. Uploaded files are not saved.

## Run locally on Windows

Use Python 3.11 or newer. In PowerShell, from this project folder, create and activate the virtual environment, then install the pinned dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation because script execution is disabled, allow scripts for this PowerShell process only, then activate:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Make sure Ollama is running locally and that `qwen2.5:3b` is installed. The app connects to Ollama at `http://127.0.0.1:11434`; no API key or internet access is needed for question generation.

```powershell
ollama list
```

Start Flask:

```powershell
python -m flask --app app run
```

Open <http://127.0.0.1:5000> in your browser. Keep the Ollama service running while using the app.

# ExamPilot — Demo Recording Guide

Target length: **60–90 seconds**. Record the real running app in your browser; keep the browser and terminal ready before starting. This script is a plan, not evidence that the live flow has already passed.

## Before recording

- [ ] Pull the latest `main` branch and confirm `git status -sb` shows a clean, synchronized branch.
- [ ] Install dependencies using the README.
- [ ] Confirm Ollama is running and `ollama list` shows `qwen2.5:3b`.
- [ ] Start Flask with `python -m flask --app app run`; open `http://127.0.0.1:5000`.
- [ ] Prepare a short, relevant excerpt from your own course notes and choose a topic explicitly covered in it.
- [ ] Complete a full rehearsal first. If question generation or evaluation fails, debug it and re-record only after it works. Do not edit the recording to imply a failed action succeeded.
- [ ] Close personal tabs and hide notifications. Do not show passwords, tokens, private notes, or unrelated account details.

## Suggested narration and on-screen actions

### 0–10 seconds — The problem

**Say:** “ExamPilot helps students turn their own course notes into active practice. Instead of asking a general chatbot, the student chooses a topic from their material.”

**Show:** The starting screen and the material/topic fields.

### 10–25 seconds — Grounded question

**Do:** Paste a short excerpt from your own notes, enter a topic that the excerpt covers, and select **Generate Question**.

**Say:** “The app selects a bounded context relevant to the topic and asks a local Ollama model for one question. The server checks the response and requires the evidence quote to appear exactly in the original notes.”

**Show:** The generated question and its source excerpt. Briefly compare the excerpt with the supplied material if it fits on screen.

### 25–45 seconds — Answer and feedback

**Do:** Answer the question in your own words and submit it.

**Say:** “ExamPilot returns a qualitative evaluation, explains the points included and missed, and displays source excerpts for feedback points when exact evidence is available.”

**Show:** The label, explanation, included points, missing or incorrect points, and evidence.

### 45–60 seconds — Trust boundary and continuation

**Do:** Select **Next Question** if the rehearsal confirms it works. Optionally demonstrate a topic not covered by the notes only if time allows.

**Say:** “The supplied material is the intended source of truth. Unsupported topics should not produce an outside-knowledge question, and a failed request should leave the student able to retry.”

**Show:** The next question or the unsupported-topic recovery state.

### 60–75 seconds — Implementation

**Say:** “The MVP uses Flask, plain HTML, CSS and JavaScript, and local Ollama. Uploaded TXT, Markdown, text-based PDF and DOCX files are extracted in memory; the app does not keep a study history.”

**Show:** The GitHub repository and its passing automated test workflow.

## Final recording check

- [ ] The real question, answer, evaluation, and evidence steps all worked during the recording.
- [ ] The quote visibly matches the supplied material.
- [ ] No secret, private document, or unrelated personal information is visible.
- [ ] Audio is understandable and the text is readable.
- [ ] The recording is within the event’s time limit and uploaded to a shareable location allowed by the event.
- [ ] The public repository link is included in the Devpost submission.

**Honesty rule:** Do not say that all large documents work, that feedback is always correct, or that local end-to-end testing passed unless you have personally observed that behavior. Exact quote matching confirms that the quote occurs in the source; it does not guarantee the model interpreted the source correctly.

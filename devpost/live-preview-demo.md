# ExamPilot — Public Preview Demo Guide

Target length: **60–90 seconds**. This guide is for the public Vercel browser preview, not the Ollama-backed local Flask app.

## Before recording
- Open the current public preview and test the exact flow once.
- Use the built-in sample notes or material you have permission to show.
- Check the page on a phone-sized viewport and a desktop viewport.
- Close personal tabs and hide notifications.
- Do not edit the recording to imply an action succeeded when it failed.

## Suggested flow

### 0–10 seconds — The student problem
**Say:** “ExamPilot is a focused way to turn course notes into practice, so students can test what they understand instead of only rereading.”

**Show:** The homepage and its material/topic fields.

### 10–25 seconds — Start from the source
**Do:** Select **Load sample notes**, check the populated material and topic, then create a practice question.

**Say:** “The learner starts with their own material, chooses a topic, and gets a question paired with a passage from those notes.”

### 25–45 seconds — Answer and inspect the source
**Do:** Answer in your own words and select **Review my answer**.

**Say:** “The preview shows the passage alongside a simple word-overlap comparison. That comparison is a prototype aid, not a semantic AI grade, so students should use the source passage to review their answer.”

**Show:** The feedback and source passage.

### 45–60 seconds — Continue learning
**Do:** Select **Try another question** to demonstrate a new prompt, then select **Edit notes** if you want to change the material or topic.

**Say:** “The learner can continue with another template-and-source combination or return to edit the study material. The question pool is finite, so changing the topic or question style helps explore a different set.”

### 60–75 seconds — Explain the technical boundary
**Say:** “The public page is a browser-only prototype. The full repository also contains a Flask application that uses a local Ollama model for question generation and answer evaluation; that model-backed flow is run locally rather than connected to this hosted preview.”

**Show:** The public repository and the README.

## Final check
- [ ] The recorded page is the real public preview.
- [ ] The sample material, question, answer, feedback, and source passage actually appeared.
- [ ] The narration accurately distinguishes the browser prototype from the local AI app.
- [ ] Audio and text are clear.
- [ ] The recording is within the event's allowed duration.
- [ ] The public repository and live demo are linked in the submission.

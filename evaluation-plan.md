# ExamPilot — Pre-submission Evaluation Plan

This is a test plan, not a report of completed tests. Fill in the actual result and notes after running each check. Do not claim user research, accuracy rates, or passing results without evidence.

## A. Automated checks for the full local application

Run the commands in the README in the project environment.

| Check | Expected result | Actual result |
|---|---|---|
| Python compilation | All app modules and tests compile | Not yet recorded |
| Unit/API tests | Test suite completes; investigate and fix failures | Not yet recorded |
| Required-field validation | Empty material or topic is rejected before model request | Not yet recorded |
| Context selection | Selected context is topic-relevant and maps to original source spans | Not yet recorded |
| Question response validation | Malformed or unsupported response is not shown as a valid question | Not yet recorded |
| Evidence validation | Non-empty quote must match the original material exactly | Not yet recorded |
| Evaluation response validation | Invalid labels/fields or invalid evidence are rejected | Not yet recorded |
| Upload validation | Unsupported, unreadable, encrypted, empty, and oversized uploads get recoverable errors | Not yet recorded |
| Privacy/logging review | Notes, answers, and model output are not written to logs or saved by the app | Not yet recorded |

The tests may mock Ollama. Passing automated tests does not prove the model produces consistently good questions or feedback.

## B. Manual checks for the public Vercel application

The public page offers opt-in AI mode through `POST /api/practice`. Do not mark a live AI check passed until the request has actually succeeded in the deployed browser.

| Check | Expected result | Actual result |
|---|---|---|
| Load sample notes | Sample text and Photosynthesis topic populate the fields | Not yet recorded |
| AI opt-in disclosure | Checkbox is unchecked by default and explains what data is sent | Not yet recorded |
| AI question request | With consent enabled, a question is generated from supplied notes and source evidence matches the material exactly | Not yet recorded |
| AI evaluation | Feedback identifies included concepts, possible gaps, and a useful next step without demanding exact keywords | Not yet recorded |
| Targeted follow-up | Next question uses the reported weak concept when one is available | Not yet recorded |
| AI unavailable | Authentication/credits/provider errors are shown clearly and the page labels any fallback as browser preview, not AI | Not yet recorded |
| AI mode off | Questions use browser templates and answer feedback is labelled word-overlap preview | Not yet recorded |
| Paste custom material | Question prompt uses the chosen topic and a passage from the material | Not yet recorded |
| Add supported files | Readable supported file text is appended and shown to the learner | Not yet recorded |
| Unreadable/scanned PDF | Learner gets a clear message if no text can be extracted | Not yet recorded |
| Empty or very short material | Learner is prompted to add sufficient material | Not yet recorded |
| Unsupported topic | Learner is asked to choose a topic covered in the notes or add relevant material | Not yet recorded |
| Try another question | A different question is chosen when available; recent AI questions are sent to the backend to reduce repetition | Not yet recorded |
| Topic change | Question history and follow-up context reset for the new topic | Not yet recorded |
| Narrow mobile viewport | Main controls remain visible and usable without horizontal overflow | Not yet recorded |
| Keyboard/accessibility | Controls can be reached by keyboard and focus remains visible | Not yet recorded |
| Refresh | Page session resets predictably; no promise of saved history | Not yet recorded |

AI mode requires working Vercel AI Gateway authentication and available credits/provider access. A deployment marked READY does not prove that an AI request succeeds. If the request fails, capture the visible error and resolve the cause before recording an AI-powered demo. Never claim AI success based only on a static deployment check.
## C. Learning-quality sample set

Use course notes you are allowed to share. Select at least three topics with clear source passages. For each topic, prepare:
- one answer that includes the main ideas,
- one partial answer that omits a key idea,
- one unrelated or incorrect answer,
- one topic not covered by the supplied notes.

For each case, record whether the question is supported by the source, whether the feedback reflects the answer, whether the evidence is a literal source excerpt, and whether the next step is clear. Save examples of failures and fix them before recording the demo. A small hand-built sample is a smoke test, not a statistically valid accuracy benchmark.

## D. Accessibility and usability pass

- [ ] Test on a narrow mobile screen and a desktop viewport.
- [ ] Check readable contrast and text zoom.
- [ ] Use the page with keyboard only.
- [ ] Confirm fields have labels and status/error messages are announced clearly.
- [ ] Confirm loading states prevent duplicate submissions in the local app.
- [ ] Check that errors preserve the material, topic, and answer when applicable.
- [ ] Ask at least one person unfamiliar with the project to complete the core loop, if time permits; record what actually happened and do not invent participant results.

## E. Release gate

Do not call the project ready until:
1. Automated tests have been run and failures addressed.
2. The complete local AI flow has been rehearsed if it is the version shown in the demo.
3. The public preview's AI limitations are visible and accurately described.
4. The actual demo recording has been watched from beginning to end.
5. The live link, repository link, video, description, and required planning documents are present in the hackathon submission.

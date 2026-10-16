const MAX_PASTED_WORDS = 5000;

const form = document.querySelector("#question-form");
const materialInput = document.querySelector("#material");
const materialFile = document.querySelector("#material-file");
const uploadStatus = document.querySelector("#upload-status");
const topicInput = document.querySelector("#topic");
const wordCount = document.querySelector("#word-count");
const generateButton = document.querySelector("#generate-button");
const requestError = document.querySelector("#request-error");
const retryButton = document.querySelector("#retry-question");
const startView = document.querySelector("#start-view");
const questionView = document.querySelector("#question-view");
const unsupportedView = document.querySelector("#unsupported-view");
const feedbackView = document.querySelector("#feedback-view");
const answerForm = document.querySelector("#answer-form");
const answerInput = document.querySelector("#answer");
const evaluationError = document.querySelector("#evaluation-error");
const retryEvaluationButton = document.querySelector("#retry-evaluation");
const evaluateButton = document.querySelector("#evaluate-button");
const nextQuestionButton = document.querySelector("#next-question");
const retryNextQuestionButton = document.querySelector("#retry-next-question");
const nextQuestionError = document.querySelector("#next-question-error");

const session = {
  material: "",
  topic: "",
  question: "",
  questionEvidence: "",
  answer: "",
  step: "start",
  pending: false,
  materialUploaded: false,
};

function countWords(text) {
  const trimmed = text.trim();
  return trimmed ? trimmed.split(/\s+/u).length : 0;
}

function updateWordCount() {
  const count = countWords(materialInput.value);
  if (session.materialUploaded) {
    wordCount.textContent = `${count.toLocaleString()} words`;
    wordCount.classList.remove("over-limit");
    return;
  }
  wordCount.textContent = `${count.toLocaleString()} / about ${MAX_PASTED_WORDS.toLocaleString()} words`;
  wordCount.classList.toggle("over-limit", count > MAX_PASTED_WORDS);
}

function showView(view) {
  for (const candidate of [startView, questionView, unsupportedView, feedbackView]) {
    candidate.hidden = candidate !== view;
  }
}

function setButtonPending(button, pending) {
  button.disabled = pending;
  button.setAttribute("aria-busy", String(pending));
  const label = button.querySelector(".button-label");
  const loading = button.querySelector(".button-loading");
  if (label) label.hidden = pending;
  if (loading) loading.hidden = !pending;
}

function setPending(pending, button) {
  session.pending = pending;
  setButtonPending(button, pending);
}

function clearFieldErrors() {
  document.querySelector("#material-error").textContent = "";
  document.querySelector("#topic-error").textContent = "";
  requestError.hidden = true;
  requestError.textContent = "";
  retryButton.hidden = true;
}

function validateForm() {
  clearFieldErrors();
  let valid = true;
  if (!materialInput.value.trim()) {
    document.querySelector("#material-error").textContent = "Please paste your course material first.";
    valid = false;
  }
  if (!topicInput.value.trim()) {
    document.querySelector("#topic-error").textContent = "Please enter a topic to practice.";
    valid = false;
  }
  if (!session.materialUploaded && countWords(materialInput.value) > MAX_PASTED_WORDS) {
    document.querySelector("#material-error").textContent =
      "That material is too long. Please paste a shorter selection relevant to your topic.";
    valid = false;
  }
  return valid;
}

async function requestQuestion(button = generateButton, fromFeedback = false) {
  if (session.pending) return;
  if (fromFeedback) {
    nextQuestionError.hidden = true;
    retryNextQuestionButton.hidden = true;
  } else {
    session.material = materialInput.value;
    session.topic = topicInput.value;
    if (!validateForm()) return;
  }

  setPending(true, button);
  try {
    const response = await fetch("/api/question", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ material: session.material, topic: session.topic }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Question request failed.");

    if (result.status === "supported") {
      session.question = result.question;
      session.questionEvidence = result.evidence_excerpt;
      session.answer = "";
      answerInput.value = "";
      session.step = "question";
      document.querySelector("#question-topic").textContent = session.topic;
      document.querySelector("#question-heading").textContent = result.question;
      document.querySelector("#question-evidence").textContent = result.evidence_excerpt;
      showView(questionView);
      document.querySelector("#question-heading").focus({ preventScroll: true });
    } else if (result.status === "unsupported") {
      session.question = "";
      session.questionEvidence = "";
      session.step = "unsupported";
      document.querySelector("#unsupported-explanation").textContent = result.explanation;
      showView(unsupportedView);
      document.querySelector("#unsupported-heading").focus({ preventScroll: true });
    } else {
      throw new Error("Invalid question response.");
    }
  } catch {
    if (fromFeedback) {
      showView(feedbackView);
      nextQuestionError.textContent =
        "Something went wrong while generating your question. Your material and topic are still here, so you can try again.";
      nextQuestionError.hidden = false;
      retryNextQuestionButton.hidden = false;
    } else {
      showView(startView);
      requestError.textContent =
        "Something went wrong while generating your question. Your material and topic are still here, so you can try again.";
      requestError.hidden = false;
      retryButton.hidden = false;
    }
  } finally {
    setPending(false, button);
  }
}

function appendFeedbackPoints(list, points, emptyMessage) {
  list.replaceChildren();
  if (points.length === 0) {
    const empty = document.createElement("li");
    empty.className = "feedback-point";
    empty.textContent = emptyMessage;
    list.append(empty);
    return;
  }

  for (const item of points) {
    const row = document.createElement("li");
    row.className = "feedback-point";
    const description = document.createElement("p");
    description.textContent = item.point;
    row.append(description);
    if (item.evidence_excerpt) {
      const evidence = document.createElement("blockquote");
      evidence.textContent = item.evidence_excerpt;
      row.append(evidence);
    } else {
      const noEvidence = document.createElement("p");
      noEvidence.className = "no-evidence";
      noEvidence.textContent = "No supporting passage was found in your material.";
      row.append(noEvidence);
    }
    list.append(row);
  }
}

function showEvaluation(result) {
  const label = document.querySelector("#evaluation-label");
  label.textContent = result.label;
  label.dataset.label = result.label;
  document.querySelector("#evaluation-explanation").textContent = result.explanation;
  appendFeedbackPoints(
    document.querySelector("#included-points"),
    result.included_points,
    "No supported answer points could be verified from the selected passages.",
  );
  appendFeedbackPoints(
    document.querySelector("#missing-points"),
    result.missing_or_incorrect_points,
    "No specific omission could be verified from the selected passages. Review the full relevant section; this does not mean your answer is complete.",
  );
  evaluationError.hidden = true;
  retryEvaluationButton.hidden = true;
  session.step = "feedback";
  showView(feedbackView);
  document.querySelector("#feedback-heading").focus({ preventScroll: true });
}

async function requestEvaluation() {
  if (session.pending) return;
  session.answer = answerInput.value;
  document.querySelector("#answer-error").textContent = "";
  evaluationError.hidden = true;
  retryEvaluationButton.hidden = true;
  if (!session.answer.trim()) {
    document.querySelector("#answer-error").textContent = "Please write an answer first.";
    return;
  }

  setPending(true, evaluateButton);
  try {
    const response = await fetch("/api/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        material: session.material,
        topic: session.topic,
        question: session.question,
        answer: session.answer,
      }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Evaluation request failed.");
    if (
      !result ||
      typeof result.label !== "string" ||
      typeof result.explanation !== "string" ||
      !Array.isArray(result.included_points) ||
      !Array.isArray(result.missing_or_incorrect_points)
    ) {
      throw new Error("Invalid evaluation response.");
    }
    showEvaluation(result);
  } catch {
    showView(questionView);
    evaluationError.textContent =
      "We couldn’t evaluate your answer right now. Your answer is still here, so you can try again.";
    evaluationError.hidden = false;
    retryEvaluationButton.hidden = false;
  } finally {
    setPending(false, evaluateButton);
  }
}

function returnToStart(focusTarget) {
  showView(startView);
  requestError.hidden = true;
  nextQuestionError.hidden = true;
  session.step = "start";
  focusTarget.focus();
}

materialInput.addEventListener("input", updateWordCount);
materialInput.addEventListener("paste", () => {
  session.materialUploaded = false;
  updateWordCount();
});
materialFile.addEventListener("change", async () => {
  const file = materialFile.files[0];
  uploadStatus.textContent = "";
  uploadStatus.setAttribute("role", "status");
  uploadStatus.setAttribute("aria-live", "polite");
  document.querySelector("#material-error").textContent = "";
  if (!file) return;
  const body = new FormData();
  body.append("file", file);
  materialFile.disabled = true;
  uploadStatus.textContent = "Reading your file…";
  try {
    const response = await fetch("/api/material", { method: "POST", body });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "We couldn’t read that file.");
    if (typeof result.material !== "string" || !result.material.trim()) {
      throw new Error("We couldn’t find readable text in that file. Try another file or paste your material.");
    }
    materialInput.value = result.material;
    session.materialUploaded = true;
    updateWordCount();
    uploadStatus.textContent = `Loaded ${file.name} into the material box. You can review or edit it below.`;
    materialInput.focus();
  } catch (error) {
    uploadStatus.setAttribute("role", "alert");
    uploadStatus.setAttribute("aria-live", "assertive");
    uploadStatus.textContent = error.message;
    materialFile.value = "";
  } finally {
    materialFile.disabled = false;
  }
});
form.addEventListener("submit", (event) => {
  event.preventDefault();
  requestQuestion();
});
answerForm.addEventListener("submit", (event) => {
  event.preventDefault();
  requestEvaluation();
});
document.querySelector("#change-inputs").addEventListener("click", () => returnToStart(materialInput));
document.querySelector("#feedback-change-inputs").addEventListener("click", () => returnToStart(materialInput));
document.querySelector("#choose-topic").addEventListener("click", () => returnToStart(topicInput));
document.querySelector("#add-material").addEventListener("click", () => returnToStart(materialInput));
document.querySelector("#retry-question").addEventListener("click", () => requestQuestion());
retryEvaluationButton.addEventListener("click", requestEvaluation);
nextQuestionButton.addEventListener("click", () => requestQuestion(nextQuestionButton, true));
retryNextQuestionButton.addEventListener("click", () => requestQuestion(retryNextQuestionButton, true));

updateWordCount();

from io import BytesIO
import logging

from flask import Flask, jsonify, render_template, request
from flask.wrappers import Request
from werkzeug.exceptions import RequestEntityTooLarge

from ai_service import (
    AnswerEvaluationError,
    QuestionGenerationError,
    evaluate_answer,
    fallback_evaluate_answer,
    generate_question,
)
from material_service import MaterialExtractionError, extract_material


MAX_PASTED_WORDS = 5_000
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_UPLOAD_REQUEST_BYTES = MAX_UPLOAD_BYTES + 64 * 1024

EVALUATION_LABELS = {"Correct", "Partially correct", "Needs improvement"}
EVALUATION_FIELDS = {
    "label",
    "explanation",
    "included_points",
    "missing_or_incorrect_points",
}


def _valid_evaluation_result(result):
    """Check the API contract before returning evaluation data to the browser."""
    if not isinstance(result, dict) or set(result) != EVALUATION_FIELDS:
        return False
    if result.get("label") not in EVALUATION_LABELS:
        return False
    if not isinstance(result.get("explanation"), str) or not result["explanation"].strip():
        return False
    for field in ("included_points", "missing_or_incorrect_points"):
        points = result.get(field)
        if not isinstance(points, list):
            return False
        for point in points:
            if (
                not isinstance(point, dict)
                or set(point) != {"point", "evidence_excerpt"}
                or not isinstance(point.get("point"), str)
                or not point["point"].strip()
                or not isinstance(point.get("evidence_excerpt"), str)
            ):
                return False
    return True


def _evaluation_unavailable_response():
    """Return a browser-compatible response without pretending an answer was graded."""
    return {
        "label": "Needs improvement",
        "explanation": (
            "ExamPilot could not safely evaluate this answer. No reliable grade was "
            "assigned. Your answer is still here; please try again."
        ),
        "included_points": [],
        "missing_or_incorrect_points": [],
    }


class MemoryOnlyRequest(Request):
    """Keep multipart file streams in memory instead of Werkzeug temp files."""

    def _get_file_stream(
        self, total_content_length, content_type, filename=None, content_length=None
    ):
        return BytesIO()


app = Flask(__name__)
logger = logging.getLogger(__name__)
app.request_class = MemoryOnlyRequest
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_REQUEST_BYTES


@app.get("/")
def index():
    return render_template("index.html")


@app.errorhandler(RequestEntityTooLarge)
def upload_too_large(_error):
    return jsonify(
        error="That request is too large. Choose a file no larger than 10 MB or paste a shorter material selection."
    ), 413


@app.post("/api/material")
def upload_material():
    uploaded = request.files.get("file")
    if uploaded is None or not uploaded.filename:
        return jsonify(error="Choose a course material file to upload."), 400
    if uploaded.stream.getbuffer().nbytes > MAX_UPLOAD_BYTES:
        return jsonify(error="That file is too large. Choose a file no larger than 10 MB."), 413
    try:
        material = extract_material(uploaded.filename, uploaded.stream)
    except MaterialExtractionError as error:
        return jsonify(error=str(error)), 400
    if not material.strip():
        return jsonify(error="We couldn’t find readable text in that file. Try another file or paste your material."), 400
    return jsonify(material=material)


@app.post("/api/question")
def question():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Please enter your material and topic, then try again."), 400

    material = payload.get("material")
    topic = payload.get("topic")
    previous_questions = payload.get("previous_questions", [])
    if (
        not isinstance(previous_questions, list)
        or len(previous_questions) > 20
        or any(not isinstance(item, str) for item in previous_questions)
    ):
        return jsonify(error="The quiz history is invalid. Please start the quiz again."), 400
    if not isinstance(material, str) or not material.strip():
        return jsonify(error="Please paste your course material first."), 400
    if not isinstance(topic, str) or not topic.strip():
        return jsonify(error="Please enter a topic to practice."), 400
    try:
        result = generate_question(
            material=material, topic=topic, previous_questions=previous_questions
        )
    except QuestionGenerationError:
        return (
            jsonify(
                error=(
                    "Something went wrong while generating your question. "
                    "Your material and topic are still here, so you can try again."
                )
            ),
            503,
        )

    return jsonify(result)


@app.post("/api/evaluate")
def evaluation():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Please submit your answer, then try again."), 400

    material = payload.get("material")
    topic = payload.get("topic")
    question_text = payload.get("question")
    answer = payload.get("answer")
    if not isinstance(material, str) or not material.strip():
        return jsonify(error="Please include your course material and try again."), 400
    if not isinstance(topic, str) or not topic.strip():
        return jsonify(error="Please include your topic and try again."), 400
    if not isinstance(question_text, str) or not question_text.strip():
        return jsonify(error="Please generate a question before submitting an answer."), 400
    if not isinstance(answer, str) or not answer.strip():
        return jsonify(error="Please write an answer first."), 400
    result = None
    try:
        result = evaluate_answer(
            material=material,
            topic=topic,
            question=question_text,
            answer=answer,
        )
    except AnswerEvaluationError as error:
        # A service-level failure should not skip the independent source-only
        # fallback. It may still provide useful feedback without the local model.
        logger.exception("Detailed evaluation failed: %s", type(error).__name__)
    except Exception as error:
        # Keep the API recoverable and make one bounded attempt at source-only
        # feedback rather than returning an empty evaluation immediately.
        logger.exception("Unexpected evaluation failure: %s", type(error).__name__)

    # A service can fail by returning malformed data without raising. Validate
    # its result here as well as inside the service so the browser always receives
    # the documented response shape.
    if not _valid_evaluation_result(result):
        logger.warning("Evaluation service returned an invalid response; trying fallback")
        try:
            result = fallback_evaluate_answer(
                material=material,
                topic=topic,
                question=question_text,
                answer=answer,
            )
        except Exception as error:
            logger.exception("Evaluation fallback failed: %s", type(error).__name__)
            result = None

    if not _valid_evaluation_result(result):
        logger.error("Evaluation fallback did not return a valid response")
        result = _evaluation_unavailable_response()

    return jsonify(result)


if __name__ == "__main__":
    app.run()

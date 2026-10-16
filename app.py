from io import BytesIO
import logging

from flask import Flask, jsonify, render_template, request
from flask.wrappers import Request
from werkzeug.exceptions import RequestEntityTooLarge

from ai_service import (
    AnswerEvaluationError,
    QuestionGenerationError,
    evaluate_answer,
    generate_question,
)
from material_service import MaterialExtractionError, extract_material


MAX_PASTED_WORDS = 5_000
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_UPLOAD_REQUEST_BYTES = MAX_UPLOAD_BYTES + 64 * 1024


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
    if not isinstance(material, str) or not material.strip():
        return jsonify(error="Please paste your course material first."), 400
    if not isinstance(topic, str) or not topic.strip():
        return jsonify(error="Please enter a topic to practice."), 400
    try:
        result = generate_question(material=material, topic=topic)
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
    try:
        result = evaluate_answer(
            material=material,
            topic=topic,
            question=question_text,
            answer=answer,
        )
    except AnswerEvaluationError as error:
        # Defensive route-level recovery for stale local files or an unexpected
        # evaluation failure. Never turn grading trouble into an API outage.
        logger.exception("Evaluation returned an unsafe result: %s", type(error).__name__)
        result = {
            "label": "Needs improvement",
            "explanation": (
                "A detailed evaluation could not be completed safely. No grade was assigned. "
                "Your answer is still here; check that your topic is covered by the notes and try again."
            ),
            "included_points": [],
            "missing_or_incorrect_points": [],
        }
    except Exception as error:
        logger.exception("Unexpected evaluation failure: %s", type(error).__name__)
        result = {
            "label": "Needs improvement",
            "explanation": (
                "An unexpected problem prevented safe evaluation. No grade was assigned. "
                "Your answer is still here; you can continue studying or try again."
            ),
            "included_points": [],
            "missing_or_incorrect_points": [],
        }

    return jsonify(result)


if __name__ == "__main__":
    app.run()

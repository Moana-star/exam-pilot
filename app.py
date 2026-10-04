from flask import Flask, jsonify, render_template, request

from ai_service import (
    AnswerEvaluationError,
    QuestionGenerationError,
    evaluate_answer,
    generate_question,
)


MAX_MATERIAL_WORDS = 5_000

app = Flask(__name__)


def count_words(text: str) -> int:
    """Count whitespace-separated words, matching the browser's approximation."""
    return len(text.split())


@app.get("/")
def index():
    return render_template("index.html")


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
    if count_words(material) > MAX_MATERIAL_WORDS:
        return (
            jsonify(
                error=(
                    "That material is too long. Please paste a shorter selection "
                    "relevant to your topic. Your text is still here to edit."
                )
            ),
            413,
        )

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
    if count_words(material) > MAX_MATERIAL_WORDS:
        return (
            jsonify(
                error=(
                    "That material is too long. Please paste a shorter selection "
                    "relevant to your topic. Your text is still here to edit."
                )
            ),
            413,
        )

    try:
        result = evaluate_answer(
            material=material,
            topic=topic,
            question=question_text,
            answer=answer,
        )
    except AnswerEvaluationError:
        return (
            jsonify(
                error=(
                    "We couldn’t evaluate your answer right now. "
                    "Your answer is still here, so you can try again."
                )
            ),
            503,
        )

    return jsonify(result)


if __name__ == "__main__":
    app.run()

import unittest
from unittest.mock import patch

import app as exam_pilot


MATERIAL = (
    "Gathering software requirements is the foundation of the entire software "
    "development project. Functional requirements specify what a system must do."
)
PAYLOAD = {
    "material": MATERIAL,
    "topic": "software requirements",
    "question": "What do functional requirements specify?",
    "answer": "They specify what a system must do.",
}
VALID_RESULT = {
    "label": "Partially correct",
    "explanation": "Your answer captures the main point supported by the notes.",
    "included_points": [
        {
            "point": "You identified what functional requirements specify.",
            "evidence_excerpt": "Functional requirements specify what a system must do.",
        }
    ],
    "missing_or_incorrect_points": [],
}


class EvaluationResponseContractTests(unittest.TestCase):
    def setUp(self):
        self.client = exam_pilot.app.test_client()

    @patch("app.fallback_evaluate_answer", return_value=VALID_RESULT)
    @patch("app.evaluate_answer", return_value={"unexpected": "shape"})
    def test_malformed_primary_result_uses_valid_fallback(self, _evaluate, fallback):
        response = self.client.post("/api/evaluate", json=PAYLOAD)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), VALID_RESULT)
        fallback.assert_called_once_with(
            material=PAYLOAD["material"],
            topic=PAYLOAD["topic"],
            question=PAYLOAD["question"],
            answer=PAYLOAD["answer"],
        )

    @patch("app.fallback_evaluate_answer", return_value={"unexpected": "shape"})
    @patch("app.evaluate_answer", return_value=None)
    def test_malformed_primary_and_fallback_return_safe_contract(self, _evaluate, _fallback):
        response = self.client.post("/api/evaluate", json=PAYLOAD)
        result = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(result),
            {
                "label",
                "explanation",
                "included_points",
                "missing_or_incorrect_points",
            },
        )
        self.assertEqual(result["label"], "Needs improvement")
        self.assertIn("No reliable grade was assigned", result["explanation"])
        self.assertEqual(result["included_points"], [])
        self.assertEqual(result["missing_or_incorrect_points"], [])

    @patch("app.evaluate_answer", return_value=VALID_RESULT)
    @patch("app.fallback_evaluate_answer")
    def test_valid_primary_result_is_returned_without_fallback(self, fallback, _evaluate):
        response = self.client.post("/api/evaluate", json=PAYLOAD)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), VALID_RESULT)
        fallback.assert_not_called()

    @patch("app.fallback_evaluate_answer", side_effect=RuntimeError("fallback failed"))
    @patch("app.evaluate_answer", side_effect=RuntimeError("evaluation failed"))
    def test_exceptions_still_return_browser_compatible_response(self, _evaluate, _fallback):
        response = self.client.post("/api/evaluate", json=PAYLOAD)
        result = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(result["label"], "Needs improvement")
        self.assertEqual(result["included_points"], [])
        self.assertEqual(result["missing_or_incorrect_points"], [])
        self.assertIn("No reliable grade was assigned", result["explanation"])


if __name__ == "__main__":
    unittest.main()

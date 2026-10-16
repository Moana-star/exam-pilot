from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch

import app as exam_app


class MaterialLimitTests(unittest.TestCase):
    def setUp(self):
        self.client = exam_app.app.test_client()

    def upload(self, text, filename="notes.txt"):
        return self.client.post(
            "/api/material",
            data={"file": (BytesIO(text.encode("utf-8")), filename)},
            content_type="multipart/form-data",
        )

    def test_upload_word_counts_are_not_limited(self):
        for count in (5_001, 20_001, 100_000):
            with self.subTest(words=count):
                response = self.upload("note " * count)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.get_json()["material"].split()), count)
                self.assertNotIn("word_count", response.get_json())

    def test_question_and_evaluation_accept_material_over_20000_words(self):
        material = "Evidence supports the key concept. " * 5_001
        with patch.object(
            exam_app, "generate_question", return_value={
                "status": "supported",
                "question": "What does the key concept explain?",
                "evidence_excerpt": "Evidence supports the key concept.",
            }
        ) as generate:
            response = self.client.post(
                "/api/question", json={"material": material, "topic": "key concept"}
            )
        self.assertEqual(response.status_code, 200)
        generate.assert_called_once_with(material=material, topic="key concept", previous_questions=[])

        evaluation = {
            "label": "Correct",
            "explanation": "Your answer matches the notes.",
            "included_points": [
                {"point": "Explains the key concept.", "evidence_excerpt": "Evidence supports the key concept."}
            ],
            "missing_or_incorrect_points": [],
        }
        with patch.object(exam_app, "evaluate_answer", return_value=evaluation) as evaluate:
            response = self.client.post(
                "/api/evaluate",
                json={
                    "material": material,
                    "topic": "key concept",
                    "question": "What does the key concept explain?",
                    "answer": "The notes explain the key concept.",
                },
            )
        self.assertEqual(response.status_code, 200)
        evaluate.assert_called_once()

    def test_pasted_material_counter_remains_separate(self):
        script = Path("static/app.js").read_text(encoding="utf-8")
        self.assertEqual(exam_app.MAX_PASTED_WORDS, 5_000)
        self.assertIn("const MAX_PASTED_WORDS = 5000;", script)
        self.assertIn("if (!session.materialUploaded && countWords(materialInput.value) > MAX_PASTED_WORDS)", script)
        self.assertIn("if (session.materialUploaded)", script)
        self.assertIn("wordCount.classList.remove(\"over-limit\")", script)
        self.assertIn('materialInput.addEventListener("paste"', script)
        self.assertNotIn("MAX_MATERIAL_WORDS", vars(exam_app))

    def test_upload_file_size_limit_remains_10_mb(self):
        self.assertEqual(exam_app.MAX_UPLOAD_BYTES, 10 * 1024 * 1024)
        response = self.upload("x" * (exam_app.MAX_UPLOAD_BYTES + 1))
        self.assertEqual(response.status_code, 413)
        self.assertIn("10 MB", response.get_json()["error"])

    def test_empty_and_unsupported_uploads_are_rejected(self):
        empty = self.upload("")
        self.assertEqual(empty.status_code, 400)
        self.assertIn("readable text", empty.get_json()["error"])

        unsupported = self.upload("some text", filename="notes.rtf")
        self.assertEqual(unsupported.status_code, 400)
        self.assertIn("Unsupported file type", unsupported.get_json()["error"])

    def test_corrupt_and_unreadable_files_are_rejected(self):
        corrupt_pdf = self.upload("not a PDF", filename="notes.pdf")
        self.assertEqual(corrupt_pdf.status_code, 400)
        self.assertIn("couldn’t read", corrupt_pdf.get_json()["error"])

        invalid_utf8 = self.client.post(
            "/api/material",
            data={"file": (BytesIO(b"\xff\xfe"), "notes.txt")},
            content_type="multipart/form-data",
        )
        self.assertEqual(invalid_utf8.status_code, 400)


if __name__ == "__main__":
    unittest.main()

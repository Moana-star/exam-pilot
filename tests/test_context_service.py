import unittest
import json
from unittest.mock import MagicMock, patch

import ai_service
import app as exam_app
from context_service import (
    MAX_CONTEXT_CHARS,
    select_relevant_context,
    select_relevant_material,
)


class ContextSelectionTests(unittest.TestCase):
    def test_ollama_request_uses_local_qwen_json_schema_and_bounded_context(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = json.dumps(
            {"done": True, "response": json.dumps({"ok": True})}
        ).encode()
        context = "# Process Control Block\nPCB stores the process state."

        with patch.object(ai_service, "urlopen", return_value=response) as urlopen:
            result = ai_service._request_ollama(
                instructions=ai_service.QUESTION_INSTRUCTIONS,
                data={"topic": "Process Control Block", "course_material": context},
                schema=ai_service.QUESTION_SCHEMA,
                operation="question",
            )

        self.assertEqual(result, {"ok": True})
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:11434/api/generate")
        payload = json.loads(request.data)
        self.assertEqual(payload["model"], "qwen2.5:3b")
        self.assertEqual(payload["format"], ai_service.QUESTION_SCHEMA)
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["options"]["temperature"], 0)
        prompt_data = json.loads(payload["prompt"])
        self.assertEqual(prompt_data["course_material"], context)
        self.assertIn("Return exactly one JSON object", payload["system"])
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 300)

    def test_prefers_matching_heading_section_and_keeps_source_unchanged(self):
        material = (
            "# Photosynthesis\nPlants use sunlight to make glucose.\n\n"
            "# Respiration\nCells release energy from glucose."
        )
        original = material[:]
        selected = select_relevant_material(material, "photosynthesis")
        self.assertIn("# Photosynthesis", selected)
        self.assertIn("make glucose", selected)
        self.assertNotIn("# Respiration", selected)
        self.assertEqual(material, original)

    def test_falls_back_to_paragraph_match_and_includes_neighbors(self):
        material = "Opening context.\n\nMitosis creates two identical daughter cells.\n\nThis follows DNA replication."
        selected = select_relevant_material(material, "mitosis")
        self.assertIn("Opening context.", selected)
        self.assertIn("Mitosis creates", selected)
        self.assertIn("DNA replication", selected)

    def test_selected_context_is_bounded(self):
        material = "# Biology\n\n" + ("Photosynthesis uses light energy. " * 2_000)
        selected = select_relevant_material(material, "photosynthesis")
        self.assertLessEqual(len(selected), MAX_CONTEXT_CHARS)
        self.assertIn("# Biology", selected)

    def test_unsupported_topic_returns_existing_state_without_model_request(self):
        with patch.object(ai_service, "_request_ollama") as request:
            result = ai_service.generate_question(
                material="Notes about mitosis and cell division.", topic="black holes"
            )
        self.assertEqual(result["status"], "unsupported")
        self.assertEqual(result["question"], "")
        request.assert_not_called()

    def test_model_evidence_is_validated_against_original_material(self):
        material = "# Mitosis\nMitosis creates two identical daughter cells.\n\n" + ("Other notes. " * 2_000)
        response = {
            "status": "supported",
            "question": "What does mitosis create?",
            "explanation": "The section states its outcome.",
            "evidence_excerpt": "Mitosis creates two identical daughter cells.",
        }
        with patch.object(ai_service, "_request_ollama", return_value=response) as request:
            result = ai_service.generate_question(material=material, topic="mitosis")
        self.assertIs(result, response)
        self.assertNotIn(material, request.call_args.kwargs["data"]["course_material"])
        invalid = dict(response, evidence_excerpt="invented evidence")
        with patch.object(ai_service, "_request_ollama", return_value=invalid):
            repaired = ai_service.generate_question(material=material, topic="mitosis")
        self.assertEqual(repaired["question"], response["question"])
        self.assertIn(repaired["evidence_excerpt"], material)
        self.assertIn(repaired["evidence_excerpt"], request.call_args.kwargs["data"]["course_material"])


    def test_repair_selects_verbatim_evidence_from_pdf_wrapped_lines(self):
        material = (
            "# Process Control Block\r\n"
            "A Process Control Block stores information about a process, including its current state,\r\n"
            "program counter, CPU registers, and scheduling information.\r\n"
        )
        response = {
            "status": "supported",
            "question": "Which information about a process is stored in its PCB?",
            "explanation": "The supplied notes describe the information stored in a PCB.",
            "evidence_excerpt": "The PCB keeps all process information, including the state and registers.",
        }

        with patch.object(ai_service, "_request_ollama", return_value=response):
            result = ai_service.generate_question(
                material=material, topic="Process Control Block"
            )

        self.assertEqual(
            result["evidence_excerpt"],
            "A Process Control Block stores information about a process, including its current state,\r\n"
            "program counter, CPU registers, and scheduling information.",
        )
        self.assertIn(result["evidence_excerpt"], material)
        selected = select_relevant_context(material, "Process Control Block")
        self.assertIn(result["evidence_excerpt"], selected.text)

    def test_large_relevant_section_is_bounded_but_evidence_uses_full_source(self):
        evidence = "During a context switch, the operating system saves the process state in its PCB."
        material = (
            "# Process Control Block\n"
            + ("A process control block stores process scheduling information.\n\n" * 500)
            + evidence
        )
        response = {
            "status": "supported",
            "question": "What does the operating system save during a context switch?",
            "explanation": "The notes describe the PCB's role during a context switch.",
            "evidence_excerpt": evidence,
        }

        with patch.object(ai_service, "_request_ollama", return_value=response) as request:
            result = ai_service.generate_question(
                material=material, topic="Process Control Block"
            )

        sent_context = request.call_args.kwargs["data"]["course_material"]
        self.assertLessEqual(len(sent_context), MAX_CONTEXT_CHARS)
        self.assertNotEqual(sent_context, material)
        self.assertLess(len(sent_context), len(material))
        self.assertEqual(result["evidence_excerpt"], evidence)
        self.assertIn(result["evidence_excerpt"], material)

    def test_question_evidence_must_be_exact_in_prompt_context_and_original(self):
        material = (
            "# Process Control Block\n"
            "A PCB stores the process state, including its current program counter.\n\n"
            "# Memory Management\nPages map virtual memory to physical frames."
        )
        topic = "Process Control Block"
        context = select_relevant_material(material, topic)
        evidence = "A PCB stores the process state, including its current program counter."
        response = {
            "status": "supported",
            "question": "What does the PCB store?",
            "explanation": "The notes identify the PCB contents.",
            "evidence_excerpt": evidence,
        }

        # This used to fail because the response was checked against a different
        # representation than the one sent to Ollama.
        self.assertIn(evidence, context)
        self.assertIs(
            ai_service._validate_question_result(response, context, material), response
        )

        for invalid_excerpt in (
            "A PCB keeps process state, including its program counter.",
            "Pages map virtual memory to physical frames.",
        ):
            with self.subTest(evidence=invalid_excerpt):
                invalid = dict(response, evidence_excerpt=invalid_excerpt)
                with self.assertRaises(ai_service.QuestionGenerationError):
                    ai_service._validate_question_result(invalid, context, material)

    def test_required_pcb_quote_is_accepted_but_paraphrase_and_unrelated_are_rejected(self):
        evidence = (
            "A Process Control Block (PCB) is a data structure used by the operating "
            "system to store information about a process."
        )
        material = f"# Process Control Block\n{evidence}\n"
        context = select_relevant_context(material, "Process Control Block")
        valid = {
            "status": "supported",
            "question": "What is a Process Control Block used for?",
            "explanation": "The notes define the PCB and its purpose.",
            "evidence_excerpt": evidence,
        }

        self.assertTrue(context.maps_to(material))
        self.assertIs(ai_service._validate_question_result(valid, context, material), valid)

        for bad_evidence in (
            "A PCB stores information about a process for the operating system.",
            "The operating system uses a PCB to schedule CPU time.",
        ):
            with self.subTest(evidence=bad_evidence):
                invalid = dict(valid, evidence_excerpt=bad_evidence)
                with self.assertRaises(ai_service.QuestionGenerationError):
                    ai_service._validate_question_result(invalid, context, material)

    def test_context_spans_preserve_crlf_spacing_and_map_to_original(self):
        material = (
            "  # Process Control Block  \r\n\r\n"
            "  A Process Control Block (PCB) stores process state.\r\n"
            "\r\n\r\n"
            "# File Systems\r\nFiles organize data.\r\n"
        )
        selected = select_relevant_context(material, "Process Control Block")

        self.assertTrue(selected.text)
        self.assertTrue(selected.maps_to(material))
        self.assertLessEqual(len(selected.text), MAX_CONTEXT_CHARS)
        for start, end in selected.source_spans:
            self.assertTrue(material[start:end])
            self.assertIn(material[start:end], material)

    def test_large_os_material_selects_bounded_pcb_context_and_database_is_unsupported(self):
        evidence = "A Process Control Block stores the state and identifier of a process."
        material = (
            "# General Operating System Notes\n"
            + ("Operating systems manage processes, memory, and devices.\n" * 2_500)
            + "\n# Process Control Block\r\n"
            + evidence
            + "\r\n"
            + ("Additional process scheduling details are included here.\n" * 2_500)
        )
        selected = select_relevant_context(material, "Process Control Block")
        self.assertTrue(selected.text)
        self.assertLessEqual(len(selected.text), MAX_CONTEXT_CHARS)
        self.assertTrue(selected.maps_to(material))
        self.assertIn(evidence, selected.text)

        unsupported = ai_service.generate_question(
            material=material, topic="Database Normalization"
        )
        self.assertEqual(unsupported["status"], "unsupported")
        self.assertEqual(unsupported["question"], "")

    def test_question_api_returns_validated_question_and_unsupported_still_works(self):
        material = (
            "# Process Control Block\n"
            "A PCB stores the process state and current program counter.\n\n"
            "# File Systems\nFiles organize data on storage devices."
        )
        response = {
            "status": "supported",
            "question": "What does a PCB store?",
            "explanation": "The notes list the stored process information.",
            "evidence_excerpt": "A PCB stores the process state and current program counter.",
        }
        with patch.object(ai_service, "_request_ollama", return_value=response):
            result = exam_app.app.test_client().post(
                "/api/question",
                json={"material": material, "topic": "Process Control Block"},
            )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.get_json(), response)

        with patch.object(ai_service, "_request_ollama") as request:
            unsupported = exam_app.app.test_client().post(
                "/api/question",
                json={"material": material, "topic": "black holes"},
            )
        self.assertEqual(unsupported.status_code, 200)
        self.assertEqual(unsupported.get_json()["status"], "unsupported")
        request.assert_not_called()


    def test_evaluation_evidence_must_match_context_and_original_source(self):
        evidence = "A PCB stores the process state and current program counter."
        material = (
            "# Process Control Block\n"
            + evidence
            + "\n\n# File Systems\nFiles organize data on storage devices."
        )
        context = select_relevant_context(material, "Process Control Block")
        valid = {
            "label": "Partially correct",
            "explanation": "The answer identifies one supported point but misses another.",
            "included_points": [
                {"point": "Identifies stored process state.", "evidence_excerpt": evidence}
            ],
            "missing_or_incorrect_points": [
                {"point": "Could mention the program counter.", "evidence_excerpt": ""}
            ],
        }

        self.assertIs(
            ai_service._validate_evaluation_result(valid, context, material), valid
        )

        for invalid_excerpt in (
            "A PCB keeps process state and its program counter.",
            "Files organize data on storage devices.",
        ):
            with self.subTest(evidence=invalid_excerpt):
                invalid = {
                    **valid,
                    "included_points": [
                        {"point": "Identifies stored process state.", "evidence_excerpt": invalid_excerpt}
                    ],
                }
                with self.assertRaises(ai_service.AnswerEvaluationError):
                    ai_service._validate_evaluation_result(invalid, context, material)

    def test_evaluation_api_rejects_nonmatching_evidence_and_returns_recoverable_error(self):
        material = (
            "# Process Control Block\n"
            "A PCB stores process state and the current program counter."
        )
        invalid_result = {
            "label": "Correct",
            "explanation": "The answer matches the topic.",
            "included_points": [
                {
                    "point": "The answer identifies the PCB contents.",
                    "evidence_excerpt": "A PCB stores all information about CPU scheduling.",
                }
            ],
            "missing_or_incorrect_points": [],
        }

        with patch.object(ai_service, "_request_ollama", return_value=invalid_result):
            response = exam_app.app.test_client().post(
                "/api/evaluate",
                json={
                    "material": material,
                    "topic": "Process Control Block",
                    "question": "What does a PCB store?",
                    "answer": "It stores process state.",
                },
            )

        self.assertEqual(response.status_code, 503)
        self.assertIn("try again", response.get_json()["error"].lower())
        self.assertNotIn("all information about CPU scheduling", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()

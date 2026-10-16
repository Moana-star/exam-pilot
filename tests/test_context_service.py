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
        self.assertEqual(payload["options"]["num_predict"], 256)
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 45)
        prompt_data = json.loads(payload["prompt"])
        self.assertEqual(prompt_data["course_material"], context)
        self.assertIn("Return exactly one JSON object", payload["system"])
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 45)

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

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        result = response.get_json()
        self.assertEqual(result["label"], "Correct")
        repaired = result["included_points"][0]["evidence_excerpt"]
        self.assertIn(repaired, material)
        self.assertNotEqual(repaired, "A PCB stores all information about CPU scheduling.")


    def test_evaluation_model_request_has_short_timeout(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = json.dumps(
            {"done": True, "response": json.dumps({
                "label": "Partially correct",
                "explanation": "One supported point was identified.",
                "included_points": [],
                "missing_or_incorrect_points": [],
            })}
        ).encode()

        with patch.object(ai_service, "urlopen", return_value=response) as urlopen:
            ai_service._request_ollama(
                instructions=ai_service.EVALUATION_INSTRUCTIONS,
                data={
                    "topic": "PCB",
                    "course_material": "A PCB stores process state.",
                    "question": "What does a PCB store?",
                    "student_answer": "Process state.",
                },
                schema=ai_service.EVALUATION_SCHEMA,
                operation="evaluation",
            )

        self.assertEqual(urlopen.call_args.kwargs["timeout"], 20)

    def test_evaluation_api_uses_source_fallback_if_service_raises(self):
        material = "# PCB\nThe PCB stores process state."
        with patch.object(
            exam_app,
            "evaluate_answer",
            side_effect=ai_service.AnswerEvaluationError("unsafe evaluation"),
        ):
            response = exam_app.app.test_client().post(
                "/api/evaluate",
                json={
                    "material": material,
                    "topic": "PCB",
                    "question": "What does a PCB store?",
                    "answer": "It stores process state.",
                },
            )

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        result = response.get_json()
        self.assertIn(result["label"], {"Partially correct", "Needs improvement"})
        self.assertIn("word-match check", result["explanation"])
        self.assertGreater(len(result["included_points"]), 0)
        for point in result["included_points"]:
            self.assertIn(point["evidence_excerpt"], material)

    def test_evaluation_returns_recoverable_feedback_when_topic_is_not_in_material(self):
        material = "# File Systems\nFiles organize data on storage devices."

        with patch.object(ai_service, "_request_ollama") as request:
            result = ai_service.evaluate_answer(
                material=material,
                topic="Process Control Block",
                question="What does a PCB store?",
                answer="It stores process information.",
            )

        self.assertEqual(result["label"], "Needs improvement")
        self.assertIn("No grade was assigned", result["explanation"])
        self.assertEqual(result["included_points"], [])
        self.assertEqual(result["missing_or_incorrect_points"], [])
        request.assert_not_called()

    def test_fallback_discloses_when_no_omissions_can_be_verified(self):
        material = (
            "# Process Control Block\n"
            "A Process Control Block is a data structure maintained by the Operating System for every process. "
            "Process Control Blocks store vital information related to processes."
        )
        with patch.object(
            ai_service,
            "_request_ollama",
            side_effect=ai_service.OllamaRequestError("local model unavailable"),
        ):
            result = ai_service.evaluate_answer(
                material=material,
                topic="Process Control Block",
                question="What is a PCB?",
                answer="A Process Control Block is a data structure maintained by the Operating System for every process, and Process Control Blocks store vital information related to processes.",
            )
        self.assertIn("does not mean your answer is complete", result["explanation"])
        self.assertTrue(result["included_points"])
        self.assertEqual(result["missing_or_incorrect_points"], [])

    def test_evaluation_falls_back_to_exact_source_feedback_when_ollama_fails(self):
        material = (
            "# Process Control Block\n"
            "The process state records whether a process is ready or running. "
            "The program counter stores the address of the next instruction. "
            "CPU registers preserve values needed when execution resumes. "
            "Memory management information describes memory allocated to the process."
        )
        with patch.object(
            ai_service,
            "_request_ollama",
            side_effect=ai_service.OllamaRequestError("local model unavailable"),
        ):
            result = ai_service.evaluate_answer(
                material=material,
                topic="Process Control Block",
                question="What information is stored in a PCB?",
                answer="The PCB stores the process state, program counter, CPU registers, and memory management information.",
            )

        self.assertIn(result["label"], {"Partially correct", "Needs improvement"})
        self.assertIn("word-match check", result["explanation"])
        self.assertIsInstance(result["included_points"], list)
        self.assertIsInstance(result["missing_or_incorrect_points"], list)
        for point in result["included_points"] + result["missing_or_incorrect_points"]:
            excerpt = point["evidence_excerpt"]
            self.assertTrue(excerpt)
            self.assertIn(excerpt, material)


    def test_question_generation_retries_when_model_repeats_previous_question(self):
        material = (
            "# Process Control Block\n"
            "A PCB stores the process state. "
            "The program counter stores the address of the next instruction."
        )
        repeated = {
            "status": "supported",
            "question": "What information does a PCB store?",
            "explanation": "The notes describe information stored in a PCB.",
            "evidence_excerpt": "A PCB stores the process state.",
        }
        new_question = {
            "status": "supported",
            "question": "What does the program counter store?",
            "explanation": "The notes describe the program counter.",
            "evidence_excerpt": "The program counter stores the address of the next instruction.",
        }

        with patch.object(
            ai_service, "_request_ollama", side_effect=[repeated, new_question]
        ) as request:
            result = ai_service.generate_question(
                material=material,
                topic="Process Control Block",
                previous_questions=["What information does a PCB store?"],
            )

        self.assertEqual(result["question"], new_question["question"])
        self.assertEqual(request.call_count, 2)
        self.assertIn(
            "What information does a PCB store?",
            request.call_args_list[0].kwargs["data"]["previous_questions"],
        )
        self.assertIn(
            repeated["question"],
            request.call_args_list[1].kwargs["data"]["previous_questions"],
        )


if __name__ == "__main__":
    unittest.main()

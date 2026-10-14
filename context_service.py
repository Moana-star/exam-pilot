"""Select topic-relevant source spans without rewriting uploaded text."""

import re
from dataclasses import dataclass


# This prompt budget does not limit uploads or the original source kept by Flask.
MAX_CONTEXT_CHARS = 6_000
_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+")
_MARKDOWN_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+\S")
_NUMBERED_HEADING_RE = re.compile(r"^\s*\d+(?:\.\d+)*[.)]?\s+\S")
_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "how", "in", "is", "it", "of", "on", "or", "the", "this", "to",
    "was", "what", "when", "where", "which", "why", "with",
}


@dataclass(frozen=True)
class _Block:
    text: str
    start: int
    end: int
    heading: bool


@dataclass(frozen=True)
class SelectedContext:
    """Rendered prompt context plus the exact source ranges it came from."""

    text: str
    source_spans: tuple[tuple[int, int], ...]

    def maps_to(self, material: str) -> bool:
        if any(start < 0 or end < start or end > len(material) for start, end in self.source_spans):
            return False
        reconstructed = "\n\n".join(
            material[start:end] for start, end in self.source_spans
        )
        return reconstructed == self.text


def _tokens(text: str) -> list[str]:
    tokens = [token.casefold() for token in _TOKEN_RE.findall(text)]
    useful = [token for token in tokens if token not in _STOP_WORDS]
    return useful or tokens


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > 140:
        return False
    if _MARKDOWN_HEADING_RE.match(line) or _NUMBERED_HEADING_RE.match(line):
        return True
    if len(stripped.split()) > 14 or re.search(r"[.!?;]$", stripped):
        return False
    if stripped.endswith(":"):
        return True
    letters = [char for char in stripped if char.isalpha()]
    if not letters:
        return False
    if " ".join(stripped.split()).isupper():
        return True
    words = [word for word in stripped.split() if any(char.isalpha() for char in word)]
    title_case_words = sum(1 for word in words if word[:1].isupper() or word.isupper())
    return bool(words) and title_case_words / len(words) >= 0.7


def _blocks(material: str) -> list[_Block]:
    """Find heading and paragraph ranges without normalizing their contents."""
    blocks: list[_Block] = []
    body_start: int | None = None
    body_end = 0
    offset = 0

    def flush_body() -> None:
        nonlocal body_start, body_end
        if body_start is not None:
            blocks.append(
                _Block(material[body_start:body_end], body_start, body_end, False)
            )
            body_start = None

    for line in material.splitlines(keepends=True):
        line_content = line.rstrip("\r\n")
        if not line_content.strip():
            flush_body()
        elif _is_heading(line_content):
            flush_body()
            end = offset + len(line)
            blocks.append(_Block(material[offset:end], offset, end, True))
        else:
            if body_start is None:
                body_start = offset
            body_end = offset + len(line)
        offset += len(line)
    flush_body()
    return blocks


def _match_score(text: str, topic_tokens: set[str], topic_phrase: str) -> float:
    tokens = set(_tokens(text))
    overlap = tokens & topic_tokens
    if not overlap:
        return 0.0
    coverage = len(overlap) / max(1, len(topic_tokens))
    phrase = " ".join(_tokens(text))
    phrase_bonus = 3.0 if topic_phrase and topic_phrase in phrase else 0.0
    return coverage * 5.0 + len(overlap) * 0.25 + phrase_bonus


def _sentence_candidates(
    text: str, topic_tokens: set[str], topic_phrase: str
) -> list[tuple[int, int]]:
    """Return ranges of matching sentences and one sentence of context each side."""
    boundaries = list(_SENTENCE_BOUNDARY_RE.finditer(text))
    ranges: list[tuple[int, int]] = []
    start = 0
    for boundary in boundaries:
        ranges.append((start, boundary.start()))
        start = boundary.end()
    ranges.append((start, len(text)))
    ranges = [
        (start, end)
        for start, end in ranges
        if text[start:end].strip()
    ]
    if len(ranges) <= 1:
        return []
    anchors = [
        index for index, (start, end) in enumerate(ranges)
        if _match_score(text[start:end], topic_tokens, topic_phrase) > 0
    ]
    selected: set[int] = set()
    for index in anchors:
        selected.update(range(max(0, index - 1), min(len(ranges), index + 2)))
    return [ranges[index] for index in sorted(selected)]


def select_relevant_context(material: str, topic: str) -> SelectedContext:
    """Return relevant exact source spans and their rendered prompt form."""
    topic_tokens = set(_tokens(topic))
    topic_phrase = " ".join(_tokens(topic))
    if not topic_tokens:
        return SelectedContext("", ())

    blocks = _blocks(material)
    if not blocks:
        return SelectedContext("", ())

    heading_indexes = [index for index, block in enumerate(blocks) if block.heading]
    sections: list[tuple[int, int]] = []
    if heading_indexes:
        if heading_indexes[0] > 0:
            sections.append((0, heading_indexes[0]))
        for offset, start in enumerate(heading_indexes):
            end = heading_indexes[offset + 1] if offset + 1 < len(heading_indexes) else len(blocks)
            sections.append((start, end))

    matched_sections = []
    for start, end in sections:
        score = _match_score(blocks[start].text, topic_tokens, topic_phrase)
        if blocks[start].heading and score:
            matched_sections.append((score, start, end))

    priorities: dict[int, float] = {}
    if matched_sections:
        best_score = max(section[0] for section in matched_sections)
        best_sections = [
            section for section in matched_sections
            if section[0] >= best_score * 0.7
        ]
        for section_score, start, end in best_sections:
            for index in range(start, end):
                block_score = _match_score(blocks[index].text, topic_tokens, topic_phrase)
                priorities[index] = section_score + block_score * 0.2
    else:
        anchors = [
            index for index, block in enumerate(blocks)
            if not block.heading and _match_score(block.text, topic_tokens, topic_phrase) > 0
        ]
        if not anchors:
            return SelectedContext("", ())
        block_section_start: dict[int, int] = {}
        block_section_end: dict[int, int] = {}
        latest_heading = 0
        next_heading = len(blocks)
        reversed_ends: dict[int, int] = {}
        for index in range(len(blocks) - 1, -1, -1):
            reversed_ends[index] = next_heading
            if blocks[index].heading:
                next_heading = index
        for index, block in enumerate(blocks):
            if block.heading:
                latest_heading = index
            block_section_start[index] = latest_heading
            block_section_end[index] = reversed_ends[index]
        for index in anchors:
            score = _match_score(blocks[index].text, topic_tokens, topic_phrase)
            start = max(block_section_start[index], index - 1)
            end = min(block_section_end[index], index + 2)
            for neighbor in range(start, end):
                neighbor_score = _match_score(blocks[neighbor].text, topic_tokens, topic_phrase)
                priorities[neighbor] = max(
                    priorities.get(neighbor, 0.0),
                    score if neighbor == index else max(0.1, score - 0.7) + neighbor_score * 0.1,
                )
            heading_index = block_section_start[index]
            if blocks[heading_index].heading:
                priorities[heading_index] = max(
                    priorities.get(heading_index, 0.0), score - 0.2
                )

    selected: list[tuple[int, int, int]] = []
    selected_texts: set[str] = set()
    used_chars = 0
    for index, _score in sorted(priorities.items(), key=lambda item: item[1], reverse=True):
        block = blocks[index]
        passage = block.text
        if passage not in selected_texts:
            separator_cost = 2 if selected else 0
            if used_chars + separator_cost + len(passage) <= MAX_CONTEXT_CHARS:
                selected.append((index, 0, len(passage)))
                selected_texts.add(passage)
                used_chars += separator_cost + len(passage)
                continue

        # Oversized blocks contribute complete, source-offset-preserving sentences.
        for start, end in _sentence_candidates(block.text, topic_tokens, topic_phrase):
            sentence = block.text[start:end]
            if sentence in selected_texts:
                continue
            separator_cost = 2 if selected else 0
            if used_chars + separator_cost + len(sentence) > MAX_CONTEXT_CHARS:
                break
            selected.append((index, start, end))
            selected_texts.add(sentence)
            used_chars += separator_cost + len(sentence)
        if used_chars >= MAX_CONTEXT_CHARS:
            break

    selected.sort(key=lambda item: (item[0], item[1]))
    source_spans = tuple(
        (blocks[index].start + start, blocks[index].start + end)
        for index, start, end in selected
    )
    text = "\n\n".join(material[start:end] for start, end in source_spans)
    return SelectedContext(text, source_spans)


def select_relevant_material(material: str, topic: str) -> str:
    """Compatibility helper returning only the rendered context string."""
    return select_relevant_context(material, topic).text

"""Extract plain study text from in-memory uploads."""

from io import BytesIO
from pathlib import PurePosixPath, PureWindowsPath
from typing import BinaryIO

from docx import Document
from pypdf import PdfReader


class MaterialExtractionError(Exception):
    """A safe, user-facing error while extracting an uploaded document."""


def extract_material(filename: str, stream: BinaryIO) -> str:
    """Read supported files from memory and return plain text."""
    name = PureWindowsPath(PurePosixPath(filename).name).name
    extension = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    data = stream.read()

    if extension in {"txt", "md"}:
        try:
            return data.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise MaterialExtractionError(
                "This text file isn’t valid UTF-8. Save it as UTF-8 or paste your material instead."
            ) from error

    if extension == "pdf":
        try:
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted:
                try:
                    if not reader.decrypt(""):
                        raise MaterialExtractionError(
                            "This PDF is password-protected. Remove its password or paste your material instead."
                        )
                except MaterialExtractionError:
                    raise
                except Exception as error:
                    raise MaterialExtractionError(
                        "This PDF is password-protected or unreadable. Paste your material instead."
                    ) from error
            return "\n\n".join(page.extract_text() or "" for page in reader.pages)
        except MaterialExtractionError:
            raise
        except Exception as error:
            raise MaterialExtractionError(
                "We couldn’t read that PDF. Check that it opens correctly, then try another file or paste your material."
            ) from error

    if extension == "docx":
        try:
            document = Document(BytesIO(data))
            parts = []
            for element in document.element.body.iterchildren():
                if element.tag.endswith("}p"):
                    from docx.text.paragraph import Paragraph

                    parts.append(Paragraph(element, document).text)
                elif element.tag.endswith("}tbl"):
                    from docx.table import Table

                    table = Table(element, document)
                    parts.extend("\t".join(cell.text for cell in row.cells) for row in table.rows)
            return "\n".join(parts)
        except Exception as error:
            raise MaterialExtractionError(
                "We couldn’t read that Word document. Check that it opens correctly, then try another file or paste your material."
            ) from error

    raise MaterialExtractionError(
        "Unsupported file type. Choose a .txt, .md, .pdf, or .docx file, or paste your material."
    )

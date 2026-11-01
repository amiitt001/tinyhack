import io

from app.core.exceptions import IntegrationError
from app.schemas.resume import Education, Experience, ParsedResume


class ResumeParser:
    SUPPORTED = {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "text/plain": ".txt",
    }

    def parse(self, content: bytes, mime_type: str) -> ParsedResume:
        if mime_type not in self.SUPPORTED:
            raise ValueError("Unsupported resume format")
        try:
            text = self._extract(content, mime_type)
        except Exception as exc:
            raise IntegrationError("Resume parsing failed") from exc
        if not text.strip():
            raise ValueError("Resume document is empty")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        email = next((line for line in lines if "@" in line and " " not in line), None)
        skills = self._section(lines, ("skills", "technical skills"))
        projects = self._section(lines, ("projects",))
        return ParsedResume(
            name=lines[0] if lines and "@" not in lines[0] else None,
            email=email,
            technical_skills=skills,
            projects=projects,
            education=self._education(lines),
            experience=self._experience(lines),
        )

    def _extract(self, content: bytes, mime_type: str) -> str:
        if mime_type == "application/pdf":
            from pypdf import PdfReader

            return "\n".join(
                page.extract_text() or "" for page in PdfReader(io.BytesIO(content)).pages
            )
        if mime_type.endswith("wordprocessingml.document"):
            from docx import Document

            return "\n".join(
                paragraph.text for paragraph in Document(io.BytesIO(content)).paragraphs
            )
        return content.decode("utf-8")

    @staticmethod
    def _section(lines: list[str], headings: tuple[str, ...]) -> list[str]:
        for index, line in enumerate(lines):
            if line.lower().rstrip(":") in headings:
                values = []
                for value in lines[index + 1 :]:
                    if value.endswith(":") or value.lower() in {
                        "education",
                        "experience",
                        "projects",
                    }:
                        break
                    values.append(value)
                return values
        return []

    @staticmethod
    def _education(lines: list[str]) -> list[Education]:
        return [
            Education(institution=line)
            for line in lines
            if "university" in line.lower() or "college" in line.lower()
        ]

    @staticmethod
    def _experience(lines: list[str]) -> list[Experience]:
        return [
            Experience(role=line)
            for line in lines
            if "intern" in line.lower() or "engineer" in line.lower()
        ]

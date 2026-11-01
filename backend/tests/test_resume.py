import pytest
from docx import Document

from app.core.config import Settings
from app.core.security import AuthenticatedUser
from app.services.resume import ResumeService
from app.services.resume_parser import ResumeParser


class FakeStorage:
    def __init__(self):
        self.uploads = []
        self.deletions = []

    def upload(self, key, content, content_type):
        self.uploads.append((key, content, content_type))

    def delete(self, key):
        self.deletions.append(key)

    def download(self, key):
        return b"resume"


class FakeSession:
    def get(self, model, key):
        return None

    def add(self, user):
        pass

    def flush(self):
        pass


def test_docx_parser_extracts_controlled_fixture():
    document = Document()
    document.add_paragraph("Ada Lovelace")
    document.add_paragraph("ada@example.com")
    document.add_paragraph("Technical Skills:")
    document.add_paragraph("Python")
    document.add_paragraph("Projects:")
    document.add_paragraph("Analytical Engine")
    content = __import__("io").BytesIO()
    document.save(content)

    parsed = ResumeParser().parse(
        content.getvalue(),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    assert parsed.name == "Ada Lovelace"
    assert parsed.email == "ada@example.com"
    assert parsed.technical_skills == ["Python"]
    assert parsed.projects == ["Analytical Engine"]


def test_parser_rejects_empty_and_unsupported_documents():
    with pytest.raises(ValueError, match="empty"):
        ResumeParser().parse(b" \n", "text/plain")
    with pytest.raises(ValueError, match="Unsupported"):
        ResumeParser().parse(b"data", "application/zip")


def test_resume_upload_uses_user_scoped_secure_key():
    storage = FakeStorage()
    service = ResumeService(
        Settings(supabase_url="https://example.supabase.co", supabase_service_key="x"),
        storage=storage,
    )
    user = AuthenticatedUser(id="user-1", email=None, claims={})

    class Repo:
        def create(self, session, resume):
            return resume

    service.repository = Repo()
    resume = service.upload(
        FakeSession(), user, "resume.txt", "text/plain", b"Ada\nada@example.com"
    )
    assert resume.user_id == "user-1"
    assert storage.uploads[0][0].startswith("user-1/")
    assert storage.uploads[0][0].endswith(".txt")


def test_storage_failure_does_not_leave_uploaded_object():
    storage = FakeStorage()

    class Repo:
        def create(self, session, resume):
            raise RuntimeError("database unavailable")

    service = ResumeService(
        Settings(supabase_url="https://example.supabase.co", supabase_service_key="x"),
        storage=storage,
        parser=ResumeParser(),
        repository=Repo(),
    )
    with pytest.raises(RuntimeError, match="database unavailable"):
        service.upload(
            FakeSession(),
            AuthenticatedUser(id="user-1", email=None, claims={}),
            "resume.txt",
            "text/plain",
            b"Ada\nada@example.com",
        )
    assert len(storage.deletions) == 1

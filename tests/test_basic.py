from fastapi.testclient import TestClient

from backend_api import app, chunk_text, build_prompt


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chunk_text_respects_size_and_overlap():
    text = "a" * 2000
    chunks = chunk_text(text, chunk_size=800, overlap=120)

    assert len(chunks) > 1
    assert all(len(chunk) <= 800 for chunk in chunks)
    assert "".join(chunks[0][-120:]) == chunks[1][:120]


def test_build_prompt_contains_question_and_context():
    prompt = build_prompt("Quelle est la question ?", "Voici le contexte.")

    assert "Quelle est la question ?" in prompt
    assert "Voici le contexte." in prompt
    assert "Je ne trouve pas cette information" in prompt

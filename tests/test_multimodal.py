import base64
import pytest
from pydantic import ValidationError
from app.api.schemas.requests import Message
from app.providers.multimodal import anthropic_content, openai_content

def image_part():
    return {"type":"image","mime_type":"image/png","data":base64.b64encode(b"fake-png").decode()}

def test_message_accepts_text_and_base64_image_parts():
    message = Message(role="user", content=[{"type":"text","text":"What is in this picture?"}, image_part()])
    assert len(message.content) == 2
    assert openai_content(message.content)[1]["type"] == "image_url"
    assert anthropic_content(message.content)[1]["source"]["type"] == "base64"

def test_message_rejects_invalid_base64_image():
    with pytest.raises(ValidationError):
        Message(role="user", content=[{"type":"image","mime_type":"image/png","data":"not-base64!"}])

def test_message_rejects_unsupported_mime_type():
    with pytest.raises(ValidationError):
        Message(role="user", content=[{"type":"image","mime_type":"application/pdf","data":base64.b64encode(b"x").decode()}])

def test_gemini_translator_builds_inline_image_part():
    from app.providers.multimodal import gemini_content
    contents = gemini_content([{"role":"user","content":[image_part()]}], None)
    assert contents[0].role == "user"
    assert contents[0].parts[0].inline_data.mime_type == "image/png"

def audio_part():
    return {"type":"audio","mime_type":"audio/mpeg","data":base64.b64encode(b"fake-audio").decode()}

def pdf_part():
    return {"type":"document","mime_type":"application/pdf","data":base64.b64encode(b"%PDF-fake").decode()}

def test_gemini_translator_builds_audio_and_pdf_parts():
    from app.providers.multimodal import gemini_content
    audio = gemini_content([{"role":"user","content":[audio_part()]}], None)
    pdf = gemini_content([{"role":"user","content":[pdf_part()]}], None)
    assert audio[0].parts[0].inline_data.mime_type == "audio/mpeg"
    assert pdf[0].parts[0].inline_data.mime_type == "application/pdf"

def test_anthropic_translator_builds_pdf_document_block():
    result = anthropic_content([pdf_part()])
    assert result[0]["type"] == "document"
    assert result[0]["source"]["media_type"] == "application/pdf"

def test_openai_translator_refuses_unsupported_audio():
    with pytest.raises(ValueError):
        openai_content([audio_part()])

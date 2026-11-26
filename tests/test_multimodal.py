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

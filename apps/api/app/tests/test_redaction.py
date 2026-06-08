from app.observability.redaction import redact_text


def test_redacts_common_pii():
    text, events = redact_text(
        "Email me at rahul@example.com with card 4111 1111 1111 1111 and token sk-testsecretvalue123456",
        "input_preview",
    )
    assert "rahul@example.com" not in text
    assert "4111 1111 1111 1111" not in text
    assert events


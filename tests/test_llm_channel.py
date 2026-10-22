import httpx
import pytest

from agentl.main import LLMChannel


def test_send_request_posts_openai_compatible_payload(monkeypatch):
    captured: dict[str, object] = {}

    def fake_post(*, url, headers, json, timeout):
        captured.update(
            {
                "url": url,
                "headers": headers,
                "json": json,
                "timeout": timeout,
            }
        )
        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            request=request,
            json={"choices": [{"message": {"role": "assistant", "content": "pong"}}]},
        )

    monkeypatch.setattr("agentl.main.httpx.post", fake_post)
    channel = LLMChannel(
        api_key="test-key",
        base_url="https://example.test",
        model="test-model",
    )
    messages = [{"role": "user", "content": "ping"}]

    result = channel.send_request(messages=messages, temperature=0.2, max_tokens=32)

    assert result == {"role": "assistant", "content": "pong"}
    assert captured == {
        "url": "https://example.test/v1/chat/completions",
        "headers": {
            "Authorization": "Bearer test-key",
            "Content-Type": "application/json",
        },
        "json": {
            "model": "test-model",
            "temperature": 0.2,
            "messages": messages,
            "max_tokens": 32,
        },
        "timeout": 30,
    }


def test_send_request_includes_tools_when_provided(monkeypatch):
    captured: dict[str, object] = {}

    def fake_post(*, url, headers, json, timeout):
        captured.update(json)
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={"choices": [{"message": {"role": "assistant", "content": "ok"}}]},
        )

    monkeypatch.setattr("agentl.main.httpx.post", fake_post)
    channel = LLMChannel(api_key="test-key")
    tools = [{"type": "function", "function": {"name": "demo"}}]

    channel.send_request(messages=[], tools=tools)

    assert captured["tools"] == tools


def test_non_200_response_raises_with_status_and_body(monkeypatch):
    def fake_post(*, url, headers, json, timeout):
        return httpx.Response(
            429,
            request=httpx.Request("POST", url),
            text="rate limited",
        )

    monkeypatch.setattr("agentl.main.httpx.post", fake_post)
    channel = LLMChannel(api_key="test-key")

    with pytest.raises(Exception, match="429.*rate limited"):
        channel.send_request(messages=[])

def test_missing_api_key_is_rejected_before_request(monkeypatch):
    def fake_post(*, url, headers, json, timeout):
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={"choices": [{"message": {"role": "assistant", "content": "ok"}}]},
        )

    monkeypatch.setattr("agentl.main.httpx.post", fake_post)
    with pytest.raises(ValueError, match="API key"):
        channel = LLMChannel(api_key=None)

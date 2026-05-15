from appstore_intel_mcp.config import Settings


def test_allowed_tokens_parses_csv() -> None:
    s = Settings(api_keys="a, b ,c")
    assert s.allowed_tokens() == {"a", "b", "c"}


def test_allowed_tokens_empty() -> None:
    s = Settings(api_keys="")
    assert s.allowed_tokens() == set()

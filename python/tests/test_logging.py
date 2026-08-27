import json

from chauff_cmn.logging import configure, logger


def test_configure_emits_json_lines(capsys):
    configure(service="test-service", level="INFO")
    logger.bind(correlation_id="abc-123").info("hello")

    captured = capsys.readouterr()
    line = captured.out.strip().splitlines()[-1]
    payload = json.loads(line)

    assert payload["service"] == "test-service"
    assert payload["message"] == "hello"
    assert payload["level"] == "INFO"
    assert payload["correlation_id"] == "abc-123"

import json

from chauff_cmn.logging import configure, logger


def test_configure_emits_json_lines(capsys):
    configure(service="test-service", level="INFO")
    logger.bind(trace_id="4bf92f3577b34da6a3ce929d0e0e4736").info("hello")

    captured = capsys.readouterr()
    line = captured.out.strip().splitlines()[-1]
    payload = json.loads(line)

    assert payload["service"] == "test-service"
    assert payload["message"] == "hello"
    assert payload["level"] == "INFO"
    assert payload["trace_id"] == "4bf92f3577b34da6a3ce929d0e0e4736"

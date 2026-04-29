import pytest

from app.services.report_extractor import (
    InvalidJsonError,
    MissingJsonBlockError,
    extract_machine_readable_json,
)


def test_successful_extraction_of_json_block():
    text = """
    Hebrew report text.
    --- MACHINE_READABLE_JSON_START ---
    {"schema_version": "1.0", "value": 123}
    --- MACHINE_READABLE_JSON_END ---
    More report text.
    """

    assert extract_machine_readable_json(text) == {
        "schema_version": "1.0",
        "value": 123,
    }


def test_missing_start_marker():
    text = '{"value": 1}\n--- MACHINE_READABLE_JSON_END ---'

    with pytest.raises(MissingJsonBlockError):
        extract_machine_readable_json(text)


def test_missing_end_marker():
    text = '--- MACHINE_READABLE_JSON_START ---\n{"value": 1}'

    with pytest.raises(MissingJsonBlockError):
        extract_machine_readable_json(text)


def test_invalid_json():
    text = """
    --- MACHINE_READABLE_JSON_START ---
    {"value": }
    --- MACHINE_READABLE_JSON_END ---
    """

    with pytest.raises(InvalidJsonError):
        extract_machine_readable_json(text)


def test_multiple_blocks_uses_last(caplog):
    text = """
    --- MACHINE_READABLE_JSON_START ---
    {"value": 1}
    --- MACHINE_READABLE_JSON_END ---
    --- MACHINE_READABLE_JSON_START ---
    {"value": 2}
    --- MACHINE_READABLE_JSON_END ---
    """

    assert extract_machine_readable_json(text) == {"value": 2}
    assert "Multiple machine-readable JSON blocks" in caplog.text


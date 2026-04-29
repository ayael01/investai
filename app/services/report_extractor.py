import json
import logging
import re
from typing import Any


logger = logging.getLogger(__name__)

START_MARKER = "--- MACHINE_READABLE_JSON_START ---"
END_MARKER = "--- MACHINE_READABLE_JSON_END ---"


class MissingJsonBlockError(ValueError):
    pass


class InvalidJsonError(ValueError):
    pass


def extract_machine_readable_json(text: str) -> dict[str, Any]:
    pattern = re.compile(
        rf"{re.escape(START_MARKER)}(.*?){re.escape(END_MARKER)}",
        re.DOTALL,
    )
    matches = pattern.findall(text)

    if not matches:
        raise MissingJsonBlockError("Machine-readable JSON block was not found.")

    if len(matches) > 1:
        logger.warning("Multiple machine-readable JSON blocks found; using the last one.")

    raw_json = matches[-1].strip()

    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise InvalidJsonError("Machine-readable JSON block is invalid JSON.") from exc

    if not isinstance(parsed, dict):
        raise InvalidJsonError("Machine-readable JSON block must contain a JSON object.")

    return parsed


"""Regenerate the checked-in public event-envelope JSON Schema."""

import json
from pathlib import Path

from events.schemas import EventEnvelope


def main() -> None:
    target = Path(__file__).with_name("envelope.v1.json")
    target.write_text(
        json.dumps(EventEnvelope.model_json_schema(), indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()

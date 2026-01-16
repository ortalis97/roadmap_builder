"""SSE (Server-Sent Events) service for streaming pipeline progress."""

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class SSEEvent:
    """A single SSE event to send to the client."""

    event: str
    data: dict[str, Any]
    id: str | None = None

    def encode(self) -> str:
        """Encode the event as an SSE string."""
        lines = []
        if self.id:
            lines.append(f"id: {self.id}")
        lines.append(f"event: {self.event}")
        lines.append(f"data: {json.dumps(self.data)}")
        lines.append("")  # Empty line to end event
        return "\n".join(lines) + "\n"

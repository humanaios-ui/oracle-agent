"""Thin wrapper around the Anthropic SDK for Oracle Agent's two model calls.

Both Jester and Oracle need a guaranteed-schema JSON result. Rather than
forcing tool_choice (which some models reject when combined with extended
thinking), this calls the tool with tool_choice="auto" plus a strict schema
and a strong system-prompt instruction, then retries once with a corrective
nudge if the model responds with plain text instead of a tool call. This
keeps the call safe to use with adaptive thinking on any current model
without depending on undocumented forced-tool-choice behavior.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

import anthropic

DEFAULT_MODEL = os.environ.get("ORACLE_AGENT_MODEL", "claude-opus-5")
MAX_TOKENS = int(os.environ.get("ORACLE_AGENT_MAX_TOKENS", "8000"))

_client: Optional[anthropic.Anthropic] = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


class OracleAgentError(RuntimeError):
    """Raised when a Claude call does not produce the expected structured tool call."""


def wrap_untrusted(source: str, content: str) -> str:
    """Delimit externally-authored audit content (Witness/Witch-Warlock
    markdown, Jester's own output) so text inside it that looks like an
    instruction can't be mistaken for one. A Witness or Witch/Warlock file
    is written by whoever opens that PR -- Jester and Oracle must treat its
    contents as evidence to analyze, never as commands to follow (Copilot
    review, PR #1). Callers pair this with a system-prompt rule that says
    exactly that.

    Escapes angle brackets in `content` first: without that, evidence
    containing a literal "</untrusted_evidence>" could close the wrapper
    early and place injected text outside the delimited region, defeating
    the whole point of wrapping it (Copilot review, PR #1, second pass).
    """
    escaped = content.replace("<", "&lt;").replace(">", "&gt;")
    return f'<untrusted_evidence source="{source}">\n{escaped}\n</untrusted_evidence>'


@dataclass
class StructuredCallResult:
    data: dict[str, Any]
    output_tokens: int
    model: str


def call_structured(
    *,
    system_prompt: str,
    user_prompt: str,
    tool: dict[str, Any],
    model: Optional[str] = None,
    max_tokens: int = MAX_TOKENS,
) -> StructuredCallResult:
    """Call Claude with a single strict-schema tool and return its parsed input."""
    client = get_client()
    resolved_model = model or DEFAULT_MODEL
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_prompt}]

    response = None
    for attempt in range(2):
        response = client.messages.create(
            model=resolved_model,
            max_tokens=max_tokens,
            system=system_prompt,
            thinking={"type": "adaptive"},
            tools=[tool],
            tool_choice={"type": "auto"},
            messages=messages,
        )
        for block in response.content:
            if getattr(block, "type", None) == "tool_use" and block.name == tool["name"]:
                return StructuredCallResult(
                    data=block.input,
                    output_tokens=response.usage.output_tokens,
                    model=resolved_model,
                )
        if attempt == 0:
            messages.append({"role": "assistant", "content": response.content})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"You must call the `{tool['name']}` tool with your full "
                        "answer as its input. Do not respond in plain text."
                    ),
                }
            )

    stop_reason = getattr(response, "stop_reason", "unknown")
    raise OracleAgentError(
        f"Model {resolved_model} did not call tool '{tool['name']}' after 2 attempts "
        f"(stop_reason={stop_reason})"
    )

"""Custom Vertex AI LLM mixin for vanna.

Mirrors the contract in vanna/legacy/google/gemini_chat.py but swaps auth:
- Token comes from `helix auth access-token print -a`
- Vertex is initialized against an internal api_endpoint with REST transport
- Uses an internal CA bundle via REQUESTS_CA_BUNDLE
"""

from __future__ import annotations

import os
import subprocess

# pyrefly: ignore [missing-import]
from app import _ensure_vanna_path  # noqa: F401  (sys.path side effect)

# pyrefly: ignore [missing-import]
import vertexai
# pyrefly: ignore [missing-import]
from google.oauth2.credentials import Credentials
# pyrefly: ignore [missing-import]
from vertexai.generative_models import GenerationConfig, GenerativeModel

from vanna.legacy.base import VannaBase


def _get_helix_token() -> str:
    """Fetch a fresh OAuth access token from the helix CLI."""
    return (
        subprocess.check_output("helix auth access-token print -a", shell=True)
        .decode()
        .strip()
    )


class CitiVertexAIChat(VannaBase):
    """LLM mixin that calls a Citi-internal Vertex AI gateway."""

    def __init__(self, config=None):
        print("  [LLM] initialising VannaBase...", flush=True)
        VannaBase.__init__(self, config=config)
        config = config or {}

        ca_bundle = config.get("ca_bundle") or os.environ.get("REQUESTS_CA_BUNDLE")
        if ca_bundle:
            os.environ["REQUESTS_CA_BUNDLE"] = ca_bundle
            print(f"  [LLM] CA bundle set: {ca_bundle}", flush=True)

        project = config.get("project") or os.environ.get("VERTEX_PROJECT")
        api_endpoint = config.get("api_endpoint") or os.environ.get("VERTEX_ENDPOINT")
        if not project or not api_endpoint:
            raise ValueError(
                "CitiVertexAIChat requires 'project' and 'api_endpoint' "
                "(or VERTEX_PROJECT / VERTEX_ENDPOINT env vars)."
            )

        print("  [LLM] fetching helix token...", flush=True)
        token = _get_helix_token()
        print(f"  [LLM] token fetched (len={len(token)})", flush=True)

        print(f"  [LLM] calling vertexai.init(project={project!r})...", flush=True)
        vertexai.init(
            project=project,
            api_transport="rest",
            api_endpoint=api_endpoint,
            credentials=Credentials(token),
        )
        print("  [LLM] vertexai.init done.", flush=True)

        self.model_name = config.get("model_name", "gemini-2.0-flash-001")
        print(f"  [LLM] loading GenerativeModel({self.model_name!r})...", flush=True)
        self.model = GenerativeModel(self.model_name)
        print("  [LLM] model ready.", flush=True)

        self.temperature = config.get("temperature", 0.2)
        self.top_p = config.get("top_p", 1.0)
        self.top_k = config.get("top_k", 40)

    # --- VannaBase message helpers ---------------------------------------
    def system_message(self, message: str) -> str:
        return message

    def user_message(self, message: str) -> str:
        return message

    def assistant_message(self, message: str) -> str:
        return message

    # --- VannaBase prompt entrypoint -------------------------------------
    def submit_prompt(self, prompt, **kwargs) -> str:
        """Vanna passes a list of strings (system + user + few-shot turns)."""
        contents = prompt if isinstance(prompt, list) else [prompt]
        # Vertex expects str entries; coerce defensively in case any entry is
        # a dict from a different message helper.
        contents = [c if isinstance(c, str) else str(c) for c in contents]

        response = self.model.generate_content(
            contents=contents,
            generation_config=GenerationConfig(
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k,
                candidate_count=1,
            ),
        )
        return response.text

#!/usr/bin/env python3
"""Collect AI model metadata into docs/models.json.

Data comes from https://models.dev (open catalog, no API key needed), filtered
down to the providers listed in PROVIDERS and normalized to a flat list.

Standard library only, so it runs anywhere python3 does:

    python3 scripts/update_models.py
    python3 scripts/update_models.py --providers anthropic,openai
"""

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCE_URL = "https://models.dev/api.json"
OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "models.json"
SCHEMA_VERSION = 1

# models.dev provider ids, in the order they appear in the output.
PROVIDERS = [
    "anthropic",
    "openai",
    "google",
    "xai",
    "mistral",
    "deepseek",
    "meta",
    "cohere",
    "perplexity",
    "groq",
    "openrouter",
]


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "model-lists-updater"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def normalize_model(provider_id, model):
    limit = model.get("limit") or {}
    modalities = model.get("modalities") or {}
    entry = {
        "provider": provider_id,
        "id": model["id"],
        "name": model.get("name") or model["id"],
        "family": model.get("family"),
        "description": model.get("description"),
        "status": model.get("status") or "active",
        "release_date": model.get("release_date"),
        "last_updated": model.get("last_updated"),
        "knowledge_cutoff": model.get("knowledge"),
        "context_window": limit.get("context"),
        "max_input_tokens": limit.get("input"),
        "max_output_tokens": limit.get("output"),
        "modalities": {
            "input": modalities.get("input") or [],
            "output": modalities.get("output") or [],
        },
        "capabilities": {
            "tools": bool(model.get("tool_call")),
            "reasoning": bool(model.get("reasoning")),
            "structured_output": bool(model.get("structured_output")),
            "attachments": bool(model.get("attachment")),
            "temperature": bool(model.get("temperature")),
        },
        "reasoning_options": model.get("reasoning_options"),
        "open_weights": bool(model.get("open_weights")),
        # USD per 1M tokens, keys as published by models.dev.
        "cost": model.get("cost"),
    }
    return {key: value for key, value in entry.items() if value is not None}


def build(catalog, provider_ids):
    providers = []
    models = []
    for provider_id in provider_ids:
        provider = catalog.get(provider_id)
        if not provider or not provider.get("models"):
            raise SystemExit(f"error: provider '{provider_id}' missing or empty in {SOURCE_URL}")
        entries = [normalize_model(provider_id, m) for m in provider["models"].values()]
        # Newest first; id as a stable tie-breaker.
        entries.sort(key=lambda m: m["id"])
        entries.sort(key=lambda m: m.get("release_date") or "", reverse=True)
        providers.append(
            {
                "id": provider_id,
                "name": provider.get("name") or provider_id,
                "docs": provider.get("doc"),
                "api": provider.get("api"),
                "env": provider.get("env") or [],
                "model_count": len(entries),
            }
        )
        models.extend(entries)
    return {
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE_URL,
        "providers": providers,
        "models": models,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--providers", help="comma-separated models.dev provider ids (default: built-in list)")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    provider_ids = [p.strip() for p in args.providers.split(",") if p.strip()] if args.providers else PROVIDERS
    data = build(fetch(SOURCE_URL), provider_ids)

    # Leave the file (and its updated_at) untouched when nothing changed, so
    # scheduled runs only produce a commit when the data actually moved.
    if args.output.exists():
        previous = json.loads(args.output.read_text())
        previous.pop("updated_at", None)
        if previous == data:
            print(f"no changes ({len(data['models'])} models)")
            return

    data = {"updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), **data}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {args.output} ({len(data['models'])} models, {len(data['providers'])} providers)")


if __name__ == "__main__":
    sys.exit(main())

# Model Lists

A single source of truth for AI model ids and metadata, published as a GitHub Page and a JSON file.

- `docs/index.html` — searchable, sortable table of the models
- `docs/models.json` — the data, for tools to consume
- `scripts/update_models.py` — regenerates `models.json` (Python standard library only)

## Usage

```bash
make            # numbered menu
make update     # refresh docs/models.json
make serve      # preview at http://localhost:8000
make stats      # model counts per provider
```

Data comes from [models.dev](https://models.dev), so no API keys are needed. The providers to include are the `PROVIDERS` list at the top of `scripts/update_models.py`; any models.dev provider id works.

Updates are manual: run `make update` and push, or `make update_remote` to run the "Update models" GitHub Action, which commits `models.json` only when the data changed.

## Publishing

Push to GitHub, then run `make pages` once to serve `docs/` from the `main` branch.

## models.json

```jsonc
{
  "updated_at": "2026-10-08T08:24:00Z",
  "schema_version": 1,
  "source": "https://models.dev/api.json",
  "providers": [{ "id": "anthropic", "name": "Anthropic", "docs": "…", "env": ["ANTHROPIC_API_KEY"], "model_count": 17 }],
  "models": [
    {
      "provider": "anthropic",
      "id": "claude-sonnet-5-5",          // the id to send to the provider's API
      "name": "Claude Sonnet 5.5",
      "family": "claude-sonnet",
      "status": "active",                 // active | beta | deprecated
      "release_date": "2026-09-28",
      "knowledge_cutoff": "2026-06",
      "context_window": 1000000,
      "max_output_tokens": 128000,
      "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] },
      "capabilities": { "tools": true, "reasoning": true, "structured_output": true, "attachments": true, "temperature": false },
      "open_weights": false,
      "cost": { "input": 2, "output": 10, "cache_read": 0.1, "cache_write": 2.5 }  // USD per 1M tokens
    }
  ]
}
```

Fields with no upstream value are omitted. Models are grouped by provider, newest first.

```bash
curl -s https://<user>.github.io/<repo>/models.json \
  | jq -r '.models[] | select(.provider == "anthropic" and .status == "active") | .id'
```

# offline-ai-model — Offline AI: answer model (optional)

The small local language model that writes the answer on the phone. It answers
only from passages taken from installed packs, always with citations, and says
when it has no source. It needs `offline-ai-embedder`, which picks those
passages; the app shows the two as one "Offline AI" row and installs or removes
them together.

- **Model:** Qwen3-1.7B (Alibaba Cloud), quantised to Q4_K_M.
- **Licence:** Apache-2.0.
- **Hosting:** linked, from Hugging Face.
- **Format:** `gguf` (llama.cpp), one file, installed as-is.
- **Size:** ~1.1 GB.
- **Cadence:** deliberate releases only.
- **`staleAfterDays`:** 365.

## Why this model

The spec asked for an open-weight 1–4B instruction model "whose license allows
redistribution and app use", so the licence picked the model, not the
benchmark scores. Qwen3-1.7B is Apache-2.0: no acceptable-use terms to pass on,
no redistribution limits. At Q4_K_M it is about 1.1 GB, well under the spec's
2.4 GB budget for the optional AI.

Qwen3 is a hybrid reasoning model. The app runs it with `/no_think`, so it
answers directly instead of spending tokens (and phone battery) on a reasoning
trace first.

## Where the embeddings live

Not here. Embeddings are per pack: they go stale when a pack updates, and
someone with three packs installed does not need vectors for ten. Each `hfdb`
pack carries its own precomputed vectors, keyed to the embedder model in
`meta.embed_model`. The query-side embedder that matches a question against
them is the separate `offline-ai-embedder` pack.

## NOT RELEASED — placeholder entry

The manifest entry still has a placeholder url, size 0 and a zeroed sha256.
What is left is to pin the Hugging Face revision of the Q4_K_M GGUF and record
it with `update_manifest.py`.

Pin the revision, never a branch. Hugging Face `resolve/<sha>/<file>` URLs are
stable; `resolve/main/<file>` is not, and a file that changes under a fixed
`sha256` means every download fails its checksum and the pack simply never
installs.

Nothing here is automated. `check_upstream.py` reports this pack as `manual`,
because swapping the model changes every answer every user gets, and that must
never happen because a cron job found a newer file.

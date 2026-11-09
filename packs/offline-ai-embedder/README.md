# offline-ai-embedder — Offline AI: source matching (optional)

The small embedding model that turns a question into a vector and picks which
passages from your installed packs the answer may use. `offline-ai-model`
then writes the answer from those passages only. The app shows the two as one
"Offline AI" row and installs or removes them together; this one is also what
semantic search in the library needs, even without the answer model.

- **Model:** `sentence-transformers/all-MiniLM-L6-v2`.
- **Licence:** Apache-2.0.
- **Hosting:** ours, on GitHub Releases.
- **Format:** `zip` holding `model.onnx` and `vocab.txt` at the archive root.
  The app unpacks it into the pack folder on install and keeps no copy of the
  ZIP.
- **Size:** ~90 MB.
- **Cadence:** deliberate releases only.
- **`staleAfterDays`:** 365.

## Why it is hosted, and why a ZIP

The app needs two files that belong together: the ONNX export of the model and
its WordPiece vocabulary. A manifest entry has one url, so they ship as one
ZIP. Hugging Face does not publish that ZIP, so we build and host it.

## Embeddings are per pack

The vectors themselves are not in this pack. Each `hfdb` pack carries its own
precomputed embeddings, built with this same model and recorded in its
`meta.embed_model`. That is why this model is pinned hard: changing it means
every `hfdb` pack has to be rebuilt, or its stored vectors no longer match the
questions.

## NOT BUILT — placeholder entry

The manifest entry has a placeholder url, size 0 and a zeroed sha256. To
release it:

1. Take `model.onnx` and `vocab.txt` from a pinned revision of
   `sentence-transformers/all-MiniLM-L6-v2` on Hugging Face.
2. Zip both at the archive root: `offline-ai-embedder.zip`.
3. Upload it to a release here, then record it with
   `update_manifest.py --id offline-ai-embedder --file … --url …`.

There is no build script; the ZIP is assembled by hand. `check_upstream.py`
reports this pack as `manual`.

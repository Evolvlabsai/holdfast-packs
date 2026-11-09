# offline-ai — Offline AI assistant (optional)

A small local model that answers only from installed packs, always with
citations, and says when it has no source.

- **Hosting:** linked, from Hugging Face.
- **Format:** `gguf`.
- **Cadence:** deliberate releases only.
- **`staleAfterDays`:** 365.

## NOT RELEASED — no model chosen

The manifest entry is a placeholder with a TODO url, because the spec's open
question is still open: *"Which on-device AI model, and is 2.4 GB acceptable as
the optional pack size?"*

What has to be settled before a real url can go in:

1. **Which open-weight 1–4B instruction model.** The spec's architecture table
   says llama.cpp mobile bindings and a 1–4B model.
2. **Whether its licence actually allows this.** Several widely used
   "open-weight" licences restrict redistribution, or add acceptable-use terms
   that must be passed on to users. The spec's rule is to pick a model "whose
   license allows redistribution and app use" — so the licence picks the model,
   not the benchmark scores.
3. **The quantisation.** A Q4_K_M GGUF of a 3B model is roughly 2 GB, which
   matches the 2.4 GB budget. A 1B model halves that and answers noticeably
   worse; worth testing against real quick-card questions first.
4. **Where the embeddings live.** The spec puts "precomputed embeddings for
   installed packs" in this pack, but embeddings are *per pack*: they go stale
   when a pack updates, and someone with three packs installed does not need
   embeddings for ten. They probably belong in each `hfdb` instead — which is an
   `hfdb` schema change (a new table) and therefore a `minAppVersion` bump on
   every pack.

## When a url does go in

Pin the revision, never a branch. Hugging Face `resolve/<sha>/<file>` URLs are
stable; `resolve/main/<file>` is not, and a file that changes under a fixed
`sha256` means every download fails its checksum and the pack simply never
installs.

Nothing here is automated. `check_upstream.py` reports this pack as `manual`,
because swapping the model changes every answer every user gets, and that must
never happen because a cron job found a newer file.

<!--
  Content and pipeline changes land here. Merging to main signs the manifest and
  publishes it, so this checklist is the last human gate before every installed
  app sees the change.
-->

## What changed

<!-- One or two sentences. If a pack changed, name it. -->

## Checklist

- [ ] `validate` passed, including the reachability check on every url and mirror
- [ ] every `size` and `sha256` matches the real file (`validate_manifest.py --dist dist` or `--checksums`)
- [ ] no `size` moved more than expected, or the jump is explained and `allowSizeChange` was set with a reason
- [ ] `minAppVersion` raised if any pack's `format` changed
- [ ] the `changes` line reads like something a user would want to see
- [ ] licence and attribution are right for anything new (`LICENSE`)
- [ ] **nothing medical changed without clinician review**, and no quick card lost its source
- [ ] no key, signature or built pack is in the diff

## For content changes

- [ ] the source is named and public, and its licence permits what we are doing with it
- [ ] figures were checked against the current published edition, not an older one
- [ ] no medicine doses

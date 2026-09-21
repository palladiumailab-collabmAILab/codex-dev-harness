---
name: asset-extraction
description: Inventory and shortlist assets in large or mixed directory trees before limited model inspection. Do not use for a small, known set of files.
metadata:
  short-description: Mechanically index and shortlist repository assets
---

# Asset extraction

Use this skill when asset discovery or extraction would otherwise require recursive, model-driven inspection of a large or mixed tree. The goal is a compact, auditable candidate set, not a large command transcript.

## Workflow

1. Define the input root, output artifact location, asset extensions or MIME scope, optional name/path keywords, and directories that are safe to exclude. Keep the raw manifest outside the source tree when practical.
2. Run `scripts/index_assets.py` to traverse mechanically. It records relative paths, sizes, MIME guesses, SHA-256 digests, asset kinds, duplicate relationships, and a deterministic shortlist in JSONL. It does not follow symlinks and excludes the generated manifest itself.
3. Keep the full JSONL manifest on disk. Return only its summary and shortlist to the model; do not paste a recursive listing or the complete manifest into the conversation.
4. Inspect only the shortlisted unique candidates (normally no more than 20, and no more than 50 without a deliberate reason). Use `--keyword` to rank path/name matches before using size as a deterministic tie-breaker.
5. Preserve provenance when copying or transforming an asset: retain its manifest-relative source path and digest, and record the destination or extraction result in the task artifact.
6. On repeated runs, use `--reuse` so an unchanged inventory can be reused. If the inventory fingerprint changes, regenerate and re-evaluate the shortlist.

## Command

From the skill directory, run a command shaped like:

```powershell
python .\scripts\index_assets.py `
  --root C:\path\to\repository `
  --output C:\path\to\artifacts\asset-index.jsonl `
  --keyword logo `
  --keyword hero `
  --max-shortlist 20 `
  --reuse
```

The default scope covers common image, audio, video, and 3D asset extensions. Use repeated `--extension .ext` for a narrower scope or `--include-all` when source/document files are intentionally part of the inventory. Add `--exclude-dir name` for repository-specific vendor or generated directories.

## Boundaries

- Mechanical inventory comes before semantic or visual inspection.
- Hash and deduplicate candidates before opening originals; duplicates remain traceable in the manifest through `duplicate_of`.
- A shortlist is an inspection aid, not proof that unlisted files are irrelevant. Report excluded directories, filters, and unresolved candidates when they affect completeness.
- Treat generated reports, caches, vendored dependencies, secrets, and credentials as out of scope unless the user explicitly includes them. Never copy secrets into an extraction artifact.
- Do not claim the asset task is complete when the requested candidate set, destination, or provenance evidence is still unresolved.

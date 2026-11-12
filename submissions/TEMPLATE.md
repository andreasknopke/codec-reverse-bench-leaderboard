# Community result template

The public [codec-reverse-bench leaderboard](https://andreasknopke.github.io/codec-reverse-bench-leaderboard/)
is built from open GitHub issues in this repository. Each issue must contain
exactly one fenced `json` block with
`"schema": "codec-bench/result@1"`.

## Preferred: let the harness write it

The benchmark harness prints the block from a finished run's `score.json`:

```bash
python3 codec_bench/bench.py submit --run RUN_ID --print
# create/update the issue here directly:
python3 codec_bench/bench.py submit --run RUN_ID \
  --gh --repo andreasknopke/codec-reverse-bench-leaderboard
```

`submit` strips local artifact paths, records the harness version, the
randomised codec instance and token totals, computes a score hash and validates
the block before printing or posting it. Useful overrides when the harness did
not capture them:

```bash
python3 codec_bench/bench.py submit --run RUN_ID \
  --name "Qwen3.8-Flash-Next NVFP4" \
  --quantization NVFP4 \
  --hardware "NVIDIA DGX Spark (GB10) / 128 GB unified memory" \
  --params-b 27.3 --context-tokens 262144 \
  --notes "what the model struggled with" \
  --print
```

## Skeleton

For a manual submission, print the exact current schema from the harness:

```bash
python3 codec_bench/bench.py submit --template
```

Or copy the skeleton from the issue form. The unfilled skeleton intentionally
fails validation because its placeholders are not a real run. Fill every field
from the actual run. Do not invent timings, tokens, hardware or model
metadata; use `null` for values that were not captured.

Important values:

- `harness.suite` is `codec-reverse-bench`; the current suite version is
  `bc3-v2`.
- `harness.codec_spec` is the randomised instance of this run (frame, hop,
  keep, step, version) copied from `score.json`. Bitstreams differ per run;
  only the Compress score is comparable.
- `harness.baseline` is AAC-LC 32 kbit/s: SNR 22.32 dB at 74 613 bytes.
  Compress score 100 equals that baseline; above 100 beats it.
- `run.total` is the cumulative score from `score.json`; scoring stops at the
  first verified roundtrip.
- `run.stopped_at_stage` is the stage where the run ended (passed, ran out of
  budget, or was aborted).
- `run.stage_results` keeps every executed stage: decode result, encoder
  class/Compress score/bytes/SNR/STOI, sub-goal answers, wall time, budget and
  the leak verdict.
- `evidence.level` is `self-reported` unless a maintainer verifies the result.
  `evidence.score_sha256` is the SHA-256 of the submitted `score.json`.

## Validation and trust

```bash
python3 leaderboard.py check FILE   # issue body or raw JSON, '-' for stdin
```

The pages workflow re-parses every open issue, validates the schema, skips
malformed submissions, and rebuilds the page on every issue edit.

- `self-reported` is the default.
- `verified` means a maintainer checked the result; it is not a replay.
- Maintainers can hide an entry without deleting it by adding the `hidden`
  label (`gh issue edit N --add-label hidden`).

See [`schema.json`](schema.json) for the published schema and
[`examples/issue-1.json`](examples/issue-1.json) for a filled local-model
example.

## Ranking

Results are ranked by `run.total` (descending), then by the stage the run
stopped at (earlier is better), then by total wall time (ascending).

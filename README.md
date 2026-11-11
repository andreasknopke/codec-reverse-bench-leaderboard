# Codec Reverse-Benchmark — Community Leaderboard

Public leaderboard for **[codec-reverse-bench](https://github.com/andreasknopke/codec-reverse-bench)**:
a benchmark in which a local LLM must reverse-engineer a custom audio codec
(bitstream, transform, quantization, entropy coding) and then build an encoder
that beats AAC-LC at 32 kbit/s.

**Leaderboard:** https://andreasknopke.github.io/codec-reverse-bench-leaderboard/

The benchmark harness and the reference codec live in a separate, private
repository. This repository only collects results and renders the ranking, so
nothing here can leak the codec to a model under test.

## Submit a result

Open a new issue and pick **Benchmark result** — the form contains the JSON
skeleton. Preferred: let the harness print the block and create the issue:

```bash
python3 codec_bench/bench.py submit --run RUN_ID --print
python3 codec_bench/bench.py submit --run RUN_ID \
  --gh --repo andreasknopke/codec-reverse-bench-leaderboard
```

`--gh` updates the existing open issue for the same `run_id` instead of posting
a duplicate. If the harness did not capture model metadata, pass `--name`,
`--quantization`, `--params-b`, `--context-tokens`, `--hardware` and `--notes`;
use `null` rather than guessing.

The page rebuilds automatically on every issue event. Maintainers can withdraw
an entry without deleting it by adding the `hidden` label.

## Scoring (short version)

| Component | Meaning |
|---|---|
| Decode points | 100 for stage 1, 85+ for stage 2, 65 for stage 3, 50 for stage 4 — the later the stage needed, the fewer points |
| Compress score | Encoder quality anchored at AAC-LC 32 kbit/s: **100 = AAC level**, above 100 beats it; scales with improved SNR/size |
| Sub-goals | Up to 25 points if no roundtrip is verified (15 answers) |

The codec instance (frame size, kept coefficients, quantization step, bitstream
version) is **randomised per run**, so bitstreams are not comparable across
submissions — only the Compress score is. The run stops at the first verified
roundtrip; stages 2–4 carry over the previous work.

## Files

- [`submissions/TEMPLATE.md`](submissions/TEMPLATE.md) — schema, llm/agent
  instructions, validation rules.
- [`submissions/schema.json`](submissions/schema.json) — published JSON schema.
- [`submissions/examples/issue-1.json`](submissions/examples/issue-1.json) — a
  filled local-model example.
- [`leaderboard.py`](leaderboard.py) — the standalone renderer used by CI.

Ranking: total score (descending), then the stage the run stopped at (earlier
is better), then total wall time (ascending). `evidence.level` is
`self-reported` unless a maintainer verifies the result.

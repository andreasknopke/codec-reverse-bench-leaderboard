#!/usr/bin/env python3
"""Codec Reverse-Benchmark — community leaderboard renderer.

Standalone (stdlib only) so the public pages workflow never needs the
benchmark repository. Reads an issue listing (JSON from `gh issue list`),
extracts the fenced `json` result block from every open issue labeled
`benchmark-result`, validates it and renders a static ranking.

Usage:
  python3 leaderboard.py site --issues issues.json --output docs
  python3 leaderboard.py check FILE        # issue body or raw JSON ('-' = stdin)
"""
import argparse
import datetime
import json
import os
import re
import sys

SUBMISSION_SCHEMA = "codec-bench/result@1"
SUITE_NAME = "codec-reverse-bench"
SUITE_VERSION = "bc3-v2"
LABEL = "benchmark-result"
HIDDEN_LABEL = "hidden"


def extract_result_block(body):
    if not isinstance(body, str):
        return None, ["issue body is not text"]
    m = re.search(r"```json\s*\n(.*?)\n```", body, re.S)
    text = m.group(1) if m else body.strip()
    if not m and not text.startswith("{"):
        return None, ["no fenced json block"]
    try:
        return json.loads(text), []
    except json.JSONDecodeError as exc:
        return None, ["invalid json: %s" % exc]


def validate_submission(data):
    errors = []
    if not isinstance(data, dict):
        return ["result must be a json object"]
    if data.get("schema") != SUBMISSION_SCHEMA:
        errors.append("schema must be %r" % SUBMISSION_SCHEMA)
    if not isinstance(data.get("run_id"), str) or not data["run_id"].strip():
        errors.append("run_id must be a non-empty string")
    elif data["run_id"].startswith("YYYY"):
        errors.append("template placeholders are not a real run")
    if not isinstance(data.get("started_at"), str) or not data["started_at"].strip():
        errors.append("started_at must be a non-empty string")
    elif "YYYY" in data["started_at"]:
        errors.append("template placeholders are not a real run")
    harness = data.get("harness") or {}
    if harness.get("suite") != SUITE_NAME:
        errors.append("harness.suite must be %r" % SUITE_NAME)
    if not isinstance(harness.get("suite_version"), str) or not harness["suite_version"]:
        errors.append("harness.suite_version must be a non-empty string")
    spec = harness.get("codec_spec") or {}
    if spec:
        for key in ("frame", "hop", "keep", "step", "version"):
            if key not in spec:
                errors.append("harness.codec_spec.%s missing" % key)
    model = data.get("model") or {}
    if not isinstance(model.get("ref"), str) or not model["ref"].strip():
        errors.append("model.ref must be a non-empty string")
    if model.get("provider_type") != "local":
        errors.append("model.provider_type must be local")
    run = data.get("run") or {}
    if not isinstance(run.get("total"), (int, float)) or isinstance(run.get("total"), bool):
        errors.append("run.total must be a number")
    if not isinstance(run.get("stage_results"), list) or not run["stage_results"]:
        errors.append("run.stage_results must be a non-empty list")
    ev = data.get("evidence") or {}
    if ev.get("level") not in ("self-reported", "verified"):
        errors.append("evidence.level must be self-reported or verified")
    return errors


def _esc(v):
    if isinstance(v, float):
        v = "%g" % v
    return (str(v) if v is not None else "").replace("&", "&amp;").replace(
        "<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _stage_cell(st):
    mark = "PASS" if st.get("roundtrip_pass") else "fail"
    enc = st.get("compress_score")
    enc_s = "%.1f" % enc if isinstance(enc, (int, float)) else "–"
    ans = st.get("answers") or {}
    return ("S%s <b>%s</b><br><span class=muted>Compress %s · %s/%s subgoals</span>"
            % (_esc(st.get("stage")), mark, enc_s,
               _esc(ans.get("correct", "–")), _esc(ans.get("applicable", "–"))))


def render_site(results, generated):
    rows = []
    for i, r in enumerate(results, 1):
        model = r.get("model") or {}
        run = r.get("run") or {}
        spec = ((r.get("harness") or {}).get("codec_spec") or {})
        stages = run.get("stage_results") or []
        best = max((s.get("compress_score") or 0 for s in stages), default=0)
        issue = r.get("_issue") or {}
        rows.append(
            "<tr><td class=rank>%d</td>"
            "<td><div class=model>%s</div><div class=muted>%s</div>"
            "<div class=muted>frame %s · keep %s · step %s</div></td>"
            "<td>%s</td><td class=total>%.1f</td>"
            "<td>S%s</td><td>%s</td><td>%.1f</td><td>%s</td><td>%s</td>"
            "<td><a href=\"%s\">#%s</a></td></tr>"
            % (i, _esc(model.get("name") or model.get("ref")), _esc(model.get("ref")),
               _esc(spec.get("frame", "?")), _esc(spec.get("keep", "?")),
               _esc(spec.get("step", "?")),
               _esc(run.get("hardware") or "–"),
               float(run.get("total") or 0), _esc(run.get("stopped_at_stage")),
               " ".join(_stage_cell(s) for s in stages), float(best),
               _esc(r.get("started_at", "")[:10]),
               _esc((r.get("evidence") or {}).get("level", "self-reported")),
               _esc(issue.get("url") or "#"), _esc(issue.get("number") or "?")))

    html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Codec Reverse-Benchmark — Community Leaderboard</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#0f1115;color:#e6e6e6}
main{max-width:1100px;margin:0 auto;padding:28px 18px 60px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:17px;margin:28px 0 8px}
p.sub{color:#9aa0a6;margin:0 0 22px;line-height:1.5}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:10px 8px;border-bottom:1px solid #23262d;vertical-align:top}
th{color:#9aa0a6;font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.rank{color:#9aa0a6}.total{font-weight:700;font-size:16px}
.model{font-weight:600}.muted{color:#8b9096;font-size:12px}
a{color:#6cb6ff;text-decoration:none}a:hover{text-decoration:underline}
.note{color:#9aa0a6;font-size:13px;margin-top:22px;line-height:1.5}
code{background:#1a1d23;padding:1px 4px;border-radius:4px}
</style></head><body><main>
<h1>Codec Reverse-Benchmark — Community Leaderboard</h1>
<p class="sub">Local LLMs reverse-engineering a custom audio codec. Score = decode points + Compress
score anchored at AAC-LC 32 kbit/s (100 = AAC quality; above 100 beats it).
Generated __GENERATED__ from the open <code>benchmark-result</code> issues.</p>
<table>
<thead><tr><th>#</th><th>Model</th><th>Hardware</th><th>Total</th><th>Stopped</th>
<th>Stages</th><th>Best Compress</th><th>Date</th><th>Evidence</th><th>Issue</th></tr></thead>
<tbody>
__ROWS__
</tbody></table>
<p class="note">Ranked by total, then by the stage the run stopped at, then wall time.
Results are self-reported unless marked <b>verified</b>. The codec instance is
randomised per run, so only the Compress score is comparable across runs.
Submit by opening an issue with the <b>Benchmark result</b> template; see
<code>submissions/TEMPLATE.md</code>.</p>
</main></body></html>
"""
    return html.replace("__GENERATED__", _esc(generated)).replace(
        "__ROWS__", "\n".join(rows) or
        "<tr><td colspan=10 class=muted>No results yet.</td></tr>")


def cmd_site(args):
    with open(args.issues, encoding="utf-8") as f:
        issues = json.load(f)
    if isinstance(issues, dict):
        issues = issues.get("issues") or []
    results, errors = [], []
    for issue in issues:
        labels = {label.get("name") for label in (issue.get("labels") or [])}
        if issue.get("state") not in (None, "OPEN", "open"):
            continue
        if LABEL not in labels or HIDDEN_LABEL in labels:
            continue
        data, errs = extract_result_block(issue.get("body") or "")
        if data is not None:
            errs = validate_submission(data)
        if errs:
            errors.append({"issue": issue.get("number"), "errors": errs})
            continue
        data["_issue"] = {"number": issue.get("number"), "url": issue.get("url")}
        results.append(data)
    results.sort(key=lambda r: (-float((r.get("run") or {}).get("total") or 0),
                                (r.get("run") or {}).get("stopped_at_stage") or 99,
                                float((r.get("run") or {}).get("wall_s") or 0)))
    os.makedirs(args.output, exist_ok=True)
    generated = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    with open(os.path.join(args.output, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_site(results, generated))
    open(os.path.join(args.output, ".nojekyll"), "w").close()
    if args.errors:
        with open(args.errors, "w", encoding="utf-8") as f:
            json.dump(errors, f, indent=2)
    print("rendered %d result(s) -> %s" % (len(results), args.output))
    if errors:
        print("%d invalid submission(s)" % len(errors), file=sys.stderr)
    return 0


def cmd_check(args):
    text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    data, errors = extract_result_block(text)
    if data is not None:
        errors = validate_submission(data)
    if errors:
        for err in errors:
            print("error: " + err, file=sys.stderr)
        return 2
    print("ok")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Codec community leaderboard")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("site", help="render the leaderboard from issue json")
    sp.add_argument("--issues", required=True)
    sp.add_argument("--output", required=True)
    sp.add_argument("--errors", default=None)
    sp.set_defaults(func=cmd_site)
    cp = sub.add_parser("check", help="validate an issue body or raw json")
    cp.add_argument("file")
    cp.set_defaults(func=cmd_check)
    args = ap.parse_args()
    rc = args.func(args)
    if rc:
        raise SystemExit(rc)


if __name__ == "__main__":
    main()

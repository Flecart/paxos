"""Verify the paper examples and render their actual evidence side by side.

Run from the repository root: formal/.venv/bin/python formal/paper_report.py
Uses only the existing verifier and Python's standard library.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from html import escape
import inspect
import json
from pathlib import Path
import textwrap

from examples.paper import EXAMPLES
from rmverify import verify
from test_paper import check_relations

ROOT = Path(__file__).resolve().parent


def code(text):
    return "<pre><code>" + escape(text) + "</code></pre>"


def render(runs, relations):
    sections, summary = [], []
    source_hashes = {}
    for name, spec, report in runs:
        directory = Path(report.evidence)
        artifact = json.loads((directory / "artifact.json").read_text())
        for path, digest in artifact["sources"].items():
            if source_hashes.setdefault(path, digest) != digest:
                raise ValueError(f"Examples were verified against different source versions: {path}")
        translation = (directory / "Translation.lean").read_text()
        functions = [spec.target.__init__, *spec.transitions, *spec.invariants, *spec.strengthening]
        for contract in spec.contracts.values():
            if contract.requires is not None: functions.append(contract.requires)
            functions.append(contract.ensures)
        assert len(functions) == len(artifact["programs"])
        summary.append(f'<tr><td><a href="#{name}">{name}</a></td><td>{report.translation}</td>'
                       f'<td>{escape(str(report.properties))}</td><td>{relations[name]}</td></tr>')
        sections += [f'<section id="{name}"><h2>{name}</h2>',
                     '<p>Field order: ' + escape(", ".join(f"{field}: {kind}" for field, kind in artifact["fields"].items())) + '</p>',
                     '<p>All rows below are generated from the current Python source and the accepted evidence. '
                     'The RM column contains the generated typed Lean definitions. '
                     'The Lean column is an exact excerpt of Translation.lean, including the source tree used for correspondence.</p>']
        for i, (program, function) in enumerate(zip(artifact["programs"], functions, strict=True)):
            assert program["name"] == function.__name__
            start = translation.index(f"def source{i} :")
            end_marker = f"#print axioms translation{i}"
            end = translation.index(end_marker, start) + len(end_marker)
            sections += [f'<h3>{escape(function.__qualname__)}</h3>',
                         '<div class="columns"><table><thead><tr><th scope="col">Python</th>'
                         '<th scope="col">Lean RM definitions</th><th scope="col">Checked theorem</th>'
                         '</tr></thead><tbody><tr><td>', code(textwrap.dedent(inspect.getsource(function))),
                         '</td><td>', code(translation[translation.index("structure ", start):translation.index(f"theorem translation{i}", start)]),
                         '</td><td>', code(translation[translation.index(f"theorem translation{i}", start):end]), '</td></tr></tbody></table></div>']
        sections.append('<h3>Complete evidence</h3><p>Expand to inspect the complete model, properties, '
                        'proofs, kernel axiom audits, and provenance. No proof text is reconstructed by this renderer.</p>')
        files = [*sorted(directory.glob("*.lean")), *sorted(directory.glob("*.log")),
                 *sorted(directory.glob("*.json")), *sorted(directory.glob("*.toml")),
                 directory / "lean-toolchain", directory / "recheck.py",
                 *sorted((directory/"sources").glob("*.py"))]
        for file in files:
            sections += ['<details><summary>' + escape(file.name) + '</summary>', code(file.read_text()), '</details>']
        sections.append('</section>')
    html = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FMSD99 examples: Python → Lean RM definitions → checked theorem</title>
<style>
body{font:16px/1.5 system-ui,sans-serif;margin:2rem;color:#17212b;background:#fff}
h1,h2,h3{line-height:1.2}a{color:#064ea3}section{border-top:2px solid #738294;margin-top:3rem}
table{border-collapse:collapse;width:100%}th,td{border:1px solid #bac3cc;padding:.7rem;vertical-align:top;text-align:left}
th{background:#edf2f6}.columns{overflow-x:auto}.columns table{table-layout:fixed;min-width:1050px}
pre{font:13px/1.45 ui-monospace,monospace;white-space:pre-wrap;overflow-wrap:anywhere;margin:0}
details{margin:.7rem 0;border:1px solid #bac3cc;padding:.7rem}summary{cursor:pointer;font-weight:bold}
details pre{margin-top:1rem;max-height:40rem;overflow:auto}p{max-width:95ch}
@media print{body{margin:0}.columns table{min-width:0}pre{font-size:9px}details pre{max-height:none}}
</style></head><body>
<h1>FMSD99 examples: Python → Lean RM definitions → checked theorem</h1>
<p>This is the generated companion to <a href="fmsd99.md">the full comparison report</a>.
Source: <a href="https://www.cis.upenn.edu/~alur/FMSD99.pdf">Alur and Henzinger, Reactive Modules (1999), Figures 1–2</a>.</p>
<p>These executable specializations use concrete constructor states and environment-supplied choices.
They do not implement the paper's general composition, hiding, or temporal abstraction operators.
The RM column contains typed executable Lean definitions generated from the supported Python source.</p>
<p>Lean checks the extracted source-to-definition equality and the properties of those models. Source extraction,
binding, and the mathematical interpretation of Python/RM operations remain trusted. These are not CPython proofs.
Source syntax and executable Lean definitions are separate inputs to correspondence checking.</p>
<p>All specifications have checks=[]. The finite relation checks below are additional regression evidence;
the property proofs quantify over arbitrary inputs and unbounded executions. For gates and latch the meaningful
theorem is source_contract; their empty conjunction of state invariants is trivially true.</p>
<p>Regenerate from the repository root:</p>
''' + code('formal/.venv/bin/python formal/paper_report.py') + \
        '<p>Generated ' + datetime.now(timezone.utc).isoformat() + '</p>' + \
        '<table><thead><tr><th>Example</th><th>Translation</th><th>Properties</th><th>Exhaustive round checks</th></tr></thead><tbody>' + \
        ''.join(summary) + '</tbody></table><details><summary>Complete Python examples and specifications</summary>' + \
        code(inspect.getsource(inspect.getmodule(runs[0][1].target))) + '</details>' + \
        ''.join(sections) + '</body></html>\n'
    for path, digest in source_hashes.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Source changed before the comparison was rendered: {path}")
    return html


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / ".rmverify" / "paper")
    parser.add_argument("--html", type=Path, default=ROOT / "reports" / "fmsd99-direct.html")
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    relations = check_relations()
    print("Finite relation checks:", relations, flush=True)
    runs = []
    for name, spec in EXAMPLES.items():
        report = verify(spec, directory=args.out / name, timeout=args.timeout, depth=3)
        print(f"{name}: {report.status}; translation={report.translation}; evidence={report.evidence}", flush=True)
        if not report.ok:
            raise SystemExit(f"Report not regenerated: {name} did not prove: {report.diagnostics}")
        runs.append((name, spec, report))
    args.html.parent.mkdir(parents=True, exist_ok=True)
    args.html.write_text(render(runs, relations))
    print("Comparison:", args.html.resolve())


if __name__ == "__main__":
    main()

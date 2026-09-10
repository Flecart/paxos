"""Generate the v2 comparison from freshly accepted Lean evidence."""
import hashlib
from html import escape
import inspect
import json
from pathlib import Path

from examples.peterson_v2 import peterson
from paper_report import code
from rmverify import verify

ROOT = Path(__file__).resolve().parent


def main():
    report = verify(peterson, directory=ROOT/".rmverify"/"peterson-v2", timeout=120)
    print(json.dumps(vars(report), indent=2), flush=True)
    if not report.ok:
        raise SystemExit("Comparison not replaced: Lean did not accept every obligation")
    evidence = Path(report.evidence)
    artifact = json.loads((evidence/"artifact.json").read_text())
    translation = (evidence/"Translation.lean").read_text()
    rows = []
    for i, atom in enumerate(artifact["atoms"]):
        component = peterson.components[atom["component"]]
        snippets = []
        for j in atom["native_initial"] + atom["native_update"]:
            start = translation.index(f"def graphn{j} :")
            end = translation.index("\n", translation.index(f"theorem graph_evaln{j} ", start))
            snippets.append(translation[start:end])
        start = translation.index(f"def atom{i} :")
        marker = f"#print axioms atom_agreement{i}"
        end = translation.index(marker, start)+len(marker)
        snippets.append(translation[start:end])
        rows += [f"<h2>{escape(component.target.__name__)}</h2><div class='columns'><table><thead><tr>"
                 "<th>Python process</th><th>Native RM atom after composition</th><th>Generated Lean</th>"
                 "</tr></thead><tbody><tr><td>", code(inspect.getsource(component.target)), "</td><td>",
                 code(atom["native_text"]), "</td><td>", code("\n\n".join(snippets)), "</td></tr></tbody></table></div>"]
    html = """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Peterson v2: Python → composed RM → Lean</title>
<style>
body{font:16px/1.5 system-ui,sans-serif;margin:2rem;color:#17212b}
table{border-collapse:collapse;width:100%;table-layout:fixed;min-width:1000px}
th,td{border:1px solid #bac3cc;padding:.7rem;vertical-align:top;text-align:left}
th{background:#edf2f6}.columns{overflow-x:auto}
pre{font:13px/1.45 monospace;white-space:pre-wrap;overflow-wrap:anywhere}
details{margin:1rem 0}summary{cursor:pointer;font-weight:bold}
details pre{max-height:40rem;overflow:auto}p{max-width:95ch}
</style><body><h1>Peterson v2: Python → composed RM → Lean</h1>
<p>Read <a href="peterson-v2.md">the comparison and trust boundaries</a>.
These columns contain the actual Python classes, native atom printer output, and accepted Lean definitions.
Internal AnyBool wires select alternatives; there are no external run flags.
Source: <a href="https://www.cis.upenn.edu/~alur/FMSD99.pdf">Alur and Henzinger, Figure 2</a>.</p>
<p>The proof covers all four initial flag valuations and unbounded executions of the composed relation.
Lean also checks source/native correspondence, ownership and await order, initial nonemptiness,
nonblocking updates, and equality with the separately specified initial and round relations.
Native AnyBool is exported by enumerating its complete Boolean domain. The extractor/exporter and
the operational model of the supported Python subset remain trusted; this is not a CPython proof.</p>
<p>Regenerate with <code>formal/.venv/bin/python formal/composition_report.py</code>.</p>
""" + "".join(rows)
    html += "<h2>Complete Python specification</h2>" + code(inspect.getsource(inspect.getmodule(peterson.target)))
    html += "<h2>Complete accepted evidence</h2>"
    for file in [*sorted(evidence.glob("*.lean")), *sorted(evidence.glob("*.log")),
                 evidence/"module.rm", evidence/"artifact.json", evidence/"report.json",
                 evidence/"lean-toolchain", evidence/"lakefile.toml"]:
        html += "<details><summary>"+escape(file.name)+"</summary>"+code(file.read_text())+"</details>"
    for path, digest in artifact["sources"].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
            raise RuntimeError("Source changed before report rendering")
    destination = ROOT/"reports"/"peterson-v2.html"
    destination.write_text(html+"</body></html>\n")
    print(destination, flush=True)


if __name__ == "__main__":
    main()

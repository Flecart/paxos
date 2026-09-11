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


def render(report):
    if not report.ok:
        raise ValueError("Only accepted evidence can be rendered as a proved comparison")
    evidence = Path(report.evidence)
    artifact = json.loads((evidence/"artifact.json").read_text())
    translation = (evidence/"Translation.lean").read_text()
    rows = []
    for i, atom in enumerate(artifact["atoms"]):
        component = peterson.components[atom["component"]]
        snippets = []
        for action in atom["initial"] + atom["actions"]:
            j = action["index"]
            start = translation.index("structure ", translation.index(f"def source{j} :"))
            end = translation.index(f"theorem translation{j}", start)
            snippets.append(translation[start:end])
        start = translation.index(f"def atom{i} :")
        marker = f"#print axioms atom_agreement{i}"
        end = translation.index(marker, start)+len(marker)
        snippets.append(translation[start:end])
        rows += [f"<h2>{escape(component.target.__name__)}</h2><div class='columns'><table><thead><tr>"
                 "<th>Python process</th><th>Lean RM definitions</th><th>Checked correspondence</th>"
                 "</tr></thead><tbody><tr><td>", code(inspect.getsource(component.target)), "</td><td>",
                 code("\n\n".join(snippets[:-1])), "</td><td>", code(snippets[-1]), "</td></tr></tbody></table></div>"]
    html = """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Peterson v2: Python → Lean RM definitions → checked theorem</title>
<style>
body{font:16px/1.5 system-ui,sans-serif;margin:2rem;color:#17212b}
table{border-collapse:collapse;width:100%;table-layout:fixed;min-width:1000px}
th,td{border:1px solid #bac3cc;padding:.7rem;vertical-align:top;text-align:left}
th{background:#edf2f6}.columns{overflow-x:auto}
pre{font:13px/1.45 monospace;white-space:pre-wrap;overflow-wrap:anywhere}
details{margin:1rem 0}summary{cursor:pointer;font-weight:bold}
details pre{max-height:40rem;overflow:auto}p{max-width:95ch}
</style><body><h1>Peterson v2: Python → Lean RM definitions → checked theorem</h1>
<p>Read <a href="peterson-v2.md">the comparison and trust boundaries</a>.
These columns contain the actual Python classes, generated typed functions, and checked correspondence.
Each atom has separate finite alternatives; there are no external run flags.
Source: <a href="https://www.cis.upenn.edu/~alur/FMSD99.pdf">Alur and Henzinger, Figure 2</a>.</p>
<p>The proof covers all four initial flag valuations and unbounded executions of the composed relation.
Lean also checks source/definition correspondence, ownership and await order, initial nonemptiness,
nonblocking updates, and equality with the separately specified initial and round relations.
Constructor alternatives cover their complete finite domains. Source extraction and
the operational model of the supported Python subset remain trusted; this is not a CPython proof.</p>
<p>Regenerate with <code>formal/.venv/bin/python formal/composition_report.py</code>.</p>
""" + "".join(rows)
    html += "<h2>Complete Python specification</h2>" + code(inspect.getsource(inspect.getmodule(peterson.target)))
    html += "<h2>Complete accepted evidence</h2>"
    for file in [*sorted(evidence.glob("*.lean")), *sorted(evidence.glob("*.log")),
                 *sorted(evidence.glob("*.json")), *sorted(evidence.glob("*.toml")),
                 evidence/"lean-toolchain", evidence/"recheck.py",
                 *sorted((evidence/"sources").glob("*.py"))]:
        html += "<details><summary>"+escape(file.name)+"</summary>"+code(file.read_text())+"</details>"
    for path, digest in artifact["sources"].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
            raise RuntimeError("Source changed before report rendering")
    return html+"</body></html>\n"


def main():
    report = verify(peterson, directory=ROOT/".rmverify"/"peterson-v2", timeout=120)
    print(json.dumps(vars(report), indent=2), flush=True)
    destination = ROOT/"reports"/"peterson-direct.html"
    destination.write_text(render(report))
    print(destination, flush=True)


if __name__ == "__main__":
    main()

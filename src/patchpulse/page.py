from html import escape

from patchpulse.models import ComplianceStatus
from patchpulse.report import FleetReport

STATUS_LABELS = {
    ComplianceStatus.STALE: "Stale",
    ComplianceStatus.NON_COMPLIANT: "Non-compliant",
    ComplianceStatus.COMPLIANT: "Compliant",
}

STYLE = """
body { font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 60rem; padding: 0 1rem;
  color: #1f2328; }
h1 { margin-bottom: 0.25rem; }
.meta { color: #59636e; margin-top: 0; }
.counts { display: flex; gap: 1rem; margin: 1.5rem 0; }
.count { border: 1px solid #d1d9e0; border-radius: 6px; padding: 0.75rem 1rem; min-width: 8rem; }
.count strong { display: block; font-size: 1.5rem; }
table { border-collapse: collapse; width: 100%; }
th, td { border-bottom: 1px solid #d1d9e0; padding: 0.5rem; text-align: left; vertical-align: top; }
.stale { color: #9a6700; }
.non_compliant { color: #d1242f; }
.compliant { color: #1a7f37; }
"""


def render_page(report: FleetReport) -> str:
    counts = "".join(
        f'<div class="count {status.value}"><strong>{report.count(status)}</strong>'
        f"{STATUS_LABELS[status]}</div>"
        for status in ComplianceStatus
    )
    rows = "".join(
        "<tr>"
        f"<td>{escape(finding.instance.name)}</td>"
        f"<td><code>{escape(finding.instance.instance_id)}</code></td>"
        f'<td class="{finding.status.value}">{STATUS_LABELS[finding.status]}</td>'
        f"<td>{escape('; '.join(finding.reasons)) or 'Within policy'}</td>"
        "</tr>"
        for finding in report.findings
    )
    generated = escape(report.generated_at.isoformat())
    return (
        "<!DOCTYPE html>"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>PatchPulse report</title>"
        f"<style>{STYLE}</style></head><body>"
        "<h1>PatchPulse report</h1>"
        f'<p class="meta">{len(report.findings)} instances, evaluated as of {generated}.</p>'
        f'<div class="counts">{counts}</div>'
        "<table><thead><tr><th>Name</th><th>Instance</th><th>State</th><th>Reason</th></tr>"
        f"</thead><tbody>{rows}</tbody></table>"
        "</body></html>\n"
    )

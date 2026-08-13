from __future__ import annotations

import html
from typing import Any, Dict, Iterable


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _service_cards(services: Iterable[Dict[str, Any]]) -> str:
    cards = []
    for service in services:
        essential = "Core" if service.get("essential") else "Supporting"
        cards.append(
            f"""
            <article class="service-card">
                <h3>{_escape(service.get('name', 'AWS service'))}</h3>
                <p><strong>Role:</strong> {_escape(service.get('category', 'service'))} · {essential}</p>
                <p>{_escape(service.get('why_needed', 'Selected for this architecture.'))}</p>
                <p><strong>Example:</strong> {_escape(service.get('use_case_example', 'Workload-specific use'))}</p>
                <p><strong>Planning range:</strong> {_escape(service.get('typical_monthly', 'Not calculated'))}/month</p>
            </article>
            """
        )
    return "".join(cards) or "<p>No services were selected.</p>"


def _cost_section(cost_analysis: Dict[str, Any], users: int) -> str:
    summary = cost_analysis.get("summary", {})
    breakdown = cost_analysis.get("breakdown", {})
    assumptions = cost_analysis.get("assumptions", [])
    region = cost_analysis.get("region", "not specified")

    rows = []
    for item in breakdown.values():
        rows.append(
            "<tr>"
            f"<td>{_escape(item.get('name', 'AWS service'))}</td>"
            f"<td>{_escape(item.get('display', 'Not calculated'))}</td>"
            f"<td>{_escape(item.get('free_tier', 'Check current AWS terms'))}</td>"
            "</tr>"
        )
    if not rows:
        rows.append("<tr><td colspan='3'>No recognized services were available for costing.</td></tr>")

    assumptions_html = "".join(f"<li>{_escape(item)}</li>" for item in assumptions)
    free_tier_message = (
        "The workload may fit partly within eligible AWS allowances at this scale."
        if summary.get("free_tier_viable")
        else "The model does not assume that the complete workload remains inside free allowances."
    )

    return f"""
    <section class="narrative-section cost-analysis">
        <h2>Cost planning</h2>
        <p>
            Planning range for approximately <strong>{users:,} monthly active users</strong>
            in <strong>{_escape(region)}</strong>. This is not a live AWS quotation.
        </p>
        <div class="cost-summary">
            <p><strong>Minimum:</strong> {_escape(summary.get('minimum', 'Not calculated'))}</p>
            <p><strong>Planning midpoint:</strong> {_escape(summary.get('typical', 'Not calculated'))}</p>
            <p><strong>Upper range:</strong> {_escape(summary.get('maximum', 'Not calculated'))}</p>
            <p><strong>Budget alignment:</strong> {_escape(summary.get('budget_alignment', 'not assessed'))}</p>
        </div>
        <p>{_escape(free_tier_message)}</p>
        <table>
            <thead><tr><th>Service</th><th>Monthly range</th><th>Allowance note</th></tr></thead>
            <tbody>{''.join(rows)}</tbody>
        </table>
        <h3>Assumptions and limits</h3>
        <ul>{assumptions_html}</ul>
    </section>
    """


def _implementation_section(guide: Dict[str, Any]) -> str:
    introduction = guide.get("introduction", {})
    phases = guide.get("phases", [])
    acceptance_checks = guide.get("acceptance_checks", [])

    phases_html = []
    for index, phase in enumerate(phases, 1):
        steps = "".join(f"<li>{_escape(step)}</li>" for step in phase.get("steps", []))
        phases_html.append(
            f"""
            <article class="implementation-phase">
                <h3>Phase {index}: {_escape(phase.get('name', 'Implementation'))}</h3>
                <p><strong>Estimated effort:</strong> {_escape(phase.get('duration', 'Workload dependent'))}</p>
                <ol>{steps}</ol>
            </article>
            """
        )

    checks_html = "".join(f"<li>{_escape(check)}</li>" for check in acceptance_checks)
    return f"""
    <section class="narrative-section implementation">
        <h2>Implementation roadmap</h2>
        <p>{_escape(introduction.get('overview', 'Phased implementation plan.'))}</p>
        <p><strong>Total planning effort:</strong> {_escape(introduction.get('estimated_effort', 'Not estimated'))}</p>
        {''.join(phases_html)}
        <h3>Acceptance checks</h3>
        <ul>{checks_html}</ul>
    </section>
    """


def _operations_section(guide: Dict[str, Any]) -> str:
    operations = guide.get("operations")
    if not operations:
        return ""

    groups = []
    for title, entries in operations.items():
        items = "".join(f"<li>{_escape(entry)}</li>" for entry in entries)
        groups.append(f"<h3>{_escape(title.replace('_', ' ').title())}</h3><ul>{items}</ul>")
    return f"<section class='narrative-section operations'><h2>Production controls</h2>{''.join(groups)}</section>"


def generate_narrative_analysis(
    services: list[Dict[str, Any]],
    classification: Dict[str, Any],
    cost_analysis: Dict[str, Any],
    implementation_guide: Dict[str, Any],
    estimated_users: int,
) -> str:
    """Generate an escaped HTML report derived only from the current analysis output."""
    project_type = classification.get("primary", "web_application")
    confidence = float(classification.get("confidence", 0.0))
    features = classification.get("features", [])
    context = implementation_guide.get("project_context", {})

    features_html = "".join(f"<li>{_escape(feature.replace('_', ' '))}</li>" for feature in features)
    limitations = [
        "The classifier is a deterministic rules engine, not a trained machine-learning model.",
        "The cost output is a planning range and does not query live AWS prices.",
        "Generated infrastructure requires application code and workload-specific security review.",
        "Service quotas, data residency, compliance, and recovery objectives must be validated separately.",
    ]
    limitations_html = "".join(f"<li>{_escape(item)}</li>" for item in limitations)

    return f"""
    <main class="aws-friendly-counsellor-report">
        <header>
            <h1>AWS architecture planning report</h1>
            <p>
                Recommended baseline for <strong>{_escape(project_type.replace('_', ' ').title())}</strong>,
                approximately <strong>{estimated_users:,} monthly active users</strong>,
                budget profile <strong>{_escape(context.get('budget', 'not specified'))}</strong>,
                region <strong>{_escape(context.get('region', cost_analysis.get('region', 'not specified')))}</strong>.
            </p>
            <p><strong>Classification confidence:</strong> {confidence * 100:.0f}%</p>
        </header>

        <section class="narrative-section classification">
            <h2>Detected requirements</h2>
            <ul>{features_html}</ul>
        </section>

        <section class="narrative-section architecture">
            <h2>Recommended architecture</h2>
            <p>
                The recommendation contains <strong>{len(services)}</strong> services. Core services form the
                minimum workload path; supporting services reflect the selected budget, features, and scale.
            </p>
            <div class="service-grid">{_service_cards(services)}</div>
        </section>

        {_cost_section(cost_analysis, estimated_users)}
        {_implementation_section(implementation_guide)}
        {_operations_section(implementation_guide)}

        <section class="narrative-section limitations">
            <h2>Decision limits</h2>
            <ul>{limitations_html}</ul>
        </section>
    </main>
    """.strip()

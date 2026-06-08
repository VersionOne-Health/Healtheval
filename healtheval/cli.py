from __future__ import annotations
import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from . import load_all_failure_modes, load_failure_mode, run_eval, EvalVerdict

console = Console()

SEV_COLORS = {"critical": "red", "high": "orange3", "medium": "yellow", "low": "green"}
VERDICT_COLORS = {
    EvalVerdict.PASS: "green",
    EvalVerdict.FAIL: "red",
    EvalVerdict.UNCERTAIN: "yellow",
    EvalVerdict.ERROR: "magenta",
}


@click.group()
@click.version_option(package_name="healtheval")
def cli():
    """healtheval — clinical failure mode eval for healthcare AI agents."""
    pass


@cli.command("list")
@click.option("--category", default=None, help="Filter: scribe, rcm, refill, fax_routing, prior_auth")
@click.option("--severity", default=None, help="Filter: critical, high, medium, low")
def list_modes(category, severity):
    """List all available failure modes."""
    modes = load_all_failure_modes()
    if category:
        modes = [m for m in modes if m.category.value == category]
    if severity:
        modes = [m for m in modes if m.severity.value == severity]

    table = Table(title=f"healtheval v0.1 — {len(modes)} failure mode(s)", header_style="bold cyan")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Category", style="dim")
    table.add_column("Severity")
    table.add_column("Specialties", style="dim")

    for m in sorted(modes, key=lambda x: x.id):
        sc = SEV_COLORS.get(m.severity.value, "white")
        table.add_row(
            m.id, m.name, m.category.value,
            f"[{sc}]{m.severity.value}[/{sc}]",
            ", ".join(m.specialties[:3]),
        )
    console.print(table)


@cli.command("show")
@click.argument("failure_mode_id")
def show_mode(failure_mode_id):
    """Show full definition of a failure mode."""
    try:
        fm = load_failure_mode(failure_mode_id.upper())
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    sc = SEV_COLORS.get(fm.severity.value, "white")
    console.print(Panel(
        f"[bold]{fm.name}[/bold]\n\n"
        f"[dim]Category:[/dim] {fm.category.value}   "
        f"[dim]Severity:[/dim] [{sc}]{fm.severity.value}[/{sc}]\n"
        f"[dim]Specialties:[/dim] {', '.join(fm.specialties)}\n\n"
        f"[bold]Description[/bold]\n{fm.description}\n\n"
        f"[bold]What Goes Wrong[/bold]\n{fm.what_went_wrong}\n\n"
        f"[bold]Example Bad Output[/bold]\n[red]{fm.example_bad_output}[/red]\n\n"
        f"[bold]Example Good Output[/bold]\n[green]{fm.example_good_output}[/green]",
        title=f"[cyan]{fm.id}[/cyan]",
        border_style="cyan",
    ))


@cli.command("run")
@click.option("--failure-mode", "-f", required=True)
@click.option("--context", default="")
@click.option("--agent-output", "-o", default="")
@click.option("--transcript", default="")
@click.option("--ehr-data", default="")
@click.option("--prior-context", default="")
@click.option("--remittance-data", default="")
@click.option("--formulary-data", default="")
@click.option("--medication-name", default="")
@click.option("--dea-schedule", default="")
@click.option("--provider-list", default="")
@click.option("--fax-metadata", default="")
@click.option("--policy-document", default="")
@click.option("--no-llm", is_flag=True, default=False)
@click.option("--json", "output_json", is_flag=True, default=False)
def run_command(failure_mode, context, agent_output, transcript, ehr_data,
                prior_context, remittance_data, formulary_data,
                medication_name, dea_schedule, provider_list,
                fax_metadata, policy_document, no_llm, output_json):
    """Run an evaluation against a specific failure mode."""
    fmid = failure_mode.upper()
    kwargs = dict(
        context=context, agent_output=agent_output, transcript=transcript,
        ehr_data=ehr_data, prior_context=prior_context,
        remittance_data=remittance_data, formulary_data=formulary_data,
        medication_name=medication_name, dea_schedule=dea_schedule,
        provider_list=provider_list, fax_metadata=fax_metadata,
        policy_document=policy_document,
    )
    try:
        with console.status(f"Running eval for [cyan]{fmid}[/cyan]..."):
            result = run_eval(fmid, run_llm=not no_llm, **kwargs)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    if output_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
        sys.exit(0 if result.passed else 1)

    vc = VERDICT_COLORS.get(result.final_verdict, "white")
    sc = SEV_COLORS.get(result.severity.value, "white")
    det_txt = ""
    if result.deterministic_result:
        dr = result.deterministic_result
        det_txt = (
            f"\n[bold]Deterministic[/bold]\n"
            f"Verdict: {dr.verdict.value}  Reason: {dr.reason}\n"
            + (f"Flagged: [red]{dr.flagged_content}[/red]\n" if dr.flagged_content else "")
        )
    llm_txt = ""
    if result.llm_result:
        lr = result.llm_result
        llm_txt = (
            f"\n[bold]LLM Evaluation[/bold] ({lr.model_used})\n"
            f"{lr.explanation}\n"
            f"[dim]Tokens: {lr.total_tokens}[/dim]"
        )
    elif not no_llm:
        llm_txt = "\n[dim]LLM eval not run (no API key or deterministic FAIL short-circuited).[/dim]"

    console.print(Panel(
        f"[{vc}][bold]{result.final_verdict.value}[/bold][/{vc}]\n"
        f"[dim]{result.failure_mode_id} — {result.failure_mode_name} — [{sc}]{result.severity.value}[/{sc}][/dim]"
        + det_txt + llm_txt,
        title="healtheval result",
        border_style=vc,
    ))
    sys.exit(0 if result.passed else 1)


@cli.command("test")
@click.option("--failure-mode", "-f", default=None)
@click.option("--no-llm", is_flag=True, default=False)
def run_tests(failure_mode, no_llm):
    """Run built-in test cases from tests/fixtures/sample_cases.yaml."""
    import yaml
    fixtures = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_cases.yaml"
    if not fixtures.exists():
        console.print(f"[red]Fixtures not found at {fixtures}[/red]")
        sys.exit(1)

    with open(fixtures) as f:
        cases = yaml.safe_load(f)

    if failure_mode:
        cases = [c for c in cases if c.get("failure_mode_id") == failure_mode.upper()]

    passed = failed = errors = 0
    for case in cases:
        fmid = case["failure_mode_id"]
        inputs = case.get("inputs", {})
        expected = case.get("expected_verdict")
        try:
            result = run_eval(fmid, run_llm=not no_llm, **inputs)
            actual = result.final_verdict.value
            if actual == expected:
                passed += 1
                console.print(f"[green]PASS[/green] {fmid} / {case.get('name', 'case')}")
            else:
                failed += 1
                console.print(f"[red]FAIL[/red] {fmid} / {case.get('name', 'case')} (expected {expected}, got {actual})")
        except Exception as exc:
            errors += 1
            console.print(f"[magenta]ERROR[/magenta] {fmid}: {exc}")

    console.print(f"\n[bold]Results:[/bold] {passed} passed · {failed} failed · {errors} errors")
    sys.exit(0 if failed == 0 and errors == 0 else 1)


@cli.command("ui")
@click.option("--port", default=8501, help="Port to run the UI on (default: 8501)")
@click.option("--no-browser", is_flag=True, default=False, help="Do not open browser automatically")
def launch_ui(port, no_browser):
    """Launch the healtheval web UI."""
    import subprocess
    app_path = Path(__file__).parent.parent / "app.py"
    if not app_path.exists():
        console.print("[red]Error:[/red] app.py not found. Install with: pip install healtheval[ui]")
        sys.exit(1)
    try:
        import streamlit  # noqa: F401
    except ImportError:
        console.print("[red]Streamlit not installed.[/red] Run: pip install healtheval[ui]")
        sys.exit(1)
    browser_flag = [] if not no_browser else ["--server.headless=true"]
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(app_path),
        f"--server.port={port}", "--server.address=localhost", *browser_flag,
    ]
    console.print(f"[green]Launching healtheval UI on http://localhost:{port}[/green]")
    subprocess.run(cmd)


if __name__ == "__main__":
    cli()

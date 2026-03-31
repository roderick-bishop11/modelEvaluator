#!/usr/bin/env python3

"""
eval.py — LLM Evaluation Tool
Entry point. Wires all subcommands and loads global config.

Usage:
    python eval.py --help
    python eval.py run --model mistralai/mistral-7b-instruct --suite tool-use
    python eval.py compare --models mistralai/mistral-7b,openai/gpt-4o --suite tool-use
    python eval.py review --unreviewed
    python eval.py report --export markdown
    python eval.py suite list
    python eval.py models --free --supports-tools
"""

import sys
import os
from pathlib import Path

import click
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Bootstrap: load .env before anything else so subcommands inherit env vars
# ---------------------------------------------------------------------------

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> dict:
    """
    Load config.toml if it exists. Returns a dict of config values.
    Falls back gracefully to defaults if the file is missing.
    """
    defaults = {
        "default_model": "mistralai/mistral-7b-instruct",
        "judge_model":   "openai/gpt-4o-mini",
        "db_path":       str(Path(__file__).parent / "db" / "eval.duckdb"),
        "suites_dir":    str(Path(__file__).parent / "suites"),
        "timeout":       60,
        "max_retries":   2,
    }

    if not config_path.exists():
        return defaults

    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # pip install tomli for <3.11
        except ImportError:
            click.echo(
                "Warning: could not load config.toml (install tomli for Python <3.11). "
                "Using defaults.",
                err=True,
            )
            return defaults

    with open(config_path, "rb") as f:
        user_config = tomllib.load(f)

    return {**defaults, **user_config}


# ---------------------------------------------------------------------------
# Shared context object passed to all subcommands via Click's obj system
# ---------------------------------------------------------------------------

class EvalContext:
    """Holds global state available to every subcommand."""

    def __init__(self, config: dict, verbose: bool, no_color: bool):
        self.config   = config
        self.verbose  = verbose
        self.no_color = no_color

        # Validate API key early so subcommands don't need to check
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not self.api_key:
            click.echo(
                "Warning: OPENROUTER_API_KEY is not set. "
                "Set it in .env or as an environment variable.",
                err=True,
            )


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(version="0.1.0", prog_name="eval")
@click.option(
    "--config",
    default=str(Path(__file__).parent / "config.toml"),
    show_default=True,
    help="Path to config.toml.",
    type=click.Path(dir_okay=False),
)
@click.option("--verbose", "-v", is_flag=True, default=False, help="Enable verbose output.")
@click.option("--no-color", is_flag=True, default=False, help="Disable colored output.")
@click.pass_context
def cli(ctx: click.Context, config: str, verbose: bool, no_color: bool):
    """
    LLM Evaluation Tool — test, score, and rank language models.

    Run a suite against a model, review results, compare across models,
    and export ranked leaderboards.
    """
    ctx.ensure_object(dict)
    cfg = load_config(Path(config))
    ctx.obj = EvalContext(config=cfg, verbose=verbose, no_color=no_color)


# ---------------------------------------------------------------------------
# Subcommand: run
# ---------------------------------------------------------------------------

@cli.command("run")
@click.option(
    "--model", "-m",
    multiple=True,
    required=True,
    help="Model ID (OpenRouter format). Accepts multiple: -m model-a -m model-b.",
)
@click.option(
    "--suite", "-s",
    required=True,
    help="Suite name (filename without .yaml) or 'all' to run every suite.",
)
@click.option(
    "--judge",
    default=None,
    help="Model ID to use as LLM-as-judge. Overrides config judge_model.",
)
@click.option("--tag", default=None, help="Label for this run (e.g. 'baseline', 'v2-test').")
@click.option("--limit", default=None, type=int, help="Max test cases to run (for smoke tests).")
@click.option("--no-judge", is_flag=True, default=False, help="Skip LLM-as-judge. Rule-based scoring only.")
@click.option("--dry-run", is_flag=True, default=False, help="Validate and print what would run. No API calls.")
@click.pass_obj
def cmd_run(
    obj: EvalContext,
    model: tuple,
    suite: str,
    judge: str | None,
    tag: str | None,
    limit: int | None,
    no_judge: bool,
    dry_run: bool,
):
    """Execute a test suite against one or more models."""
    from src.cli.run import run_command
    run_command(
        ctx=obj,
        models=list(model),
        suite=suite,
        judge=judge or obj.config["judge_model"],
        tag=tag,
        limit=limit,
        no_judge=no_judge,
        dry_run=dry_run,
    )


# ---------------------------------------------------------------------------
# Subcommand: compare
# ---------------------------------------------------------------------------

@cli.command("compare")
@click.option(
    "--models",
    required=True,
    help="Comma-separated model IDs to compare (must have existing run data).",
)
@click.option("--suite", default=None, help="Filter to a specific suite. Omit for all suites.")
@click.option("--tag", default=None, help="Compare only runs with this tag.")
@click.option("--by-category", is_flag=True, default=False, help="Break scores down per test category.")
@click.option(
    "--export",
    default="markdown",
    type=click.Choice(["markdown", "csv", "json", "html"], case_sensitive=False),
    show_default=True,
    help="Output format.",
)
@click.pass_obj
def cmd_compare(
    obj: EvalContext,
    models: str,
    suite: str | None,
    tag: str | None,
    by_category: bool,
    export: str,
):
    """Side-by-side score breakdown across models or runs."""
    from src.cli.compare import compare_command
    compare_command(
        ctx=obj,
        models=[m.strip() for m in models.split(",")],
        suite=suite,
        tag=tag,
        by_category=by_category,
        export=export,
    )


# ---------------------------------------------------------------------------
# Subcommand: review
# ---------------------------------------------------------------------------

@cli.command("review")
@click.option("--model", default=None, help="Filter to a specific model's results.")
@click.option("--suite", default=None, help="Filter to a specific suite.")
@click.option("--run-id", default=None, help="Review results from a specific run by ID.")
@click.option(
    "--unreviewed",
    is_flag=True,
    default=True,
    help="Show only results not yet manually reviewed (default).",
)
@click.option("--flagged", is_flag=True, default=False, help="Show only previously flagged results.")
@click.pass_obj
def cmd_review(
    obj: EvalContext,
    model: str | None,
    suite: str | None,
    run_id: str | None,
    unreviewed: bool,
    flagged: bool,
):
    """
    Manually inspect and override auto-scored results.

    Opens an interactive terminal UI. Key bindings:

    \b
      a       accept auto-score
      0-9     override score (maps to 0-10)
      f       flag for later
      s       skip (leave unchanged)
      q       quit and save changes
    """
    from src.cli.review import review_command
    review_command(
        ctx=obj,
        model=model,
        suite=suite,
        run_id=run_id,
        unreviewed=unreviewed and not flagged,
        flagged=flagged,
    )


# ---------------------------------------------------------------------------
# Subcommand: report
# ---------------------------------------------------------------------------

@cli.command("report")
@click.option("--suite", default=None, help="Scope report to a single suite. Omit for all.")
@click.option("--top", default=None, type=int, help="Show top N models only.")
@click.option(
    "--since",
    default=None,
    help="Only include runs since this date (ISO format: 2025-03-01).",
)
@click.option(
    "--export",
    default="markdown",
    type=click.Choice(["markdown", "csv", "json", "html"], case_sensitive=False),
    show_default=True,
    help="Output format.",
)
@click.option("--include-latency", is_flag=True, default=False, help="Add p50/p95 latency and token/s columns.")
@click.pass_obj
def cmd_report(
    obj: EvalContext,
    suite: str | None,
    top: int | None,
    since: str | None,
    export: str,
    include_latency: bool,
):
    """Generate a full leaderboard and scoring report."""
    from src.cli.report import report_command
    report_command(
        ctx=obj,
        suite=suite,
        top=top,
        since=since,
        export=export,
        include_latency=include_latency,
    )


# ---------------------------------------------------------------------------
# Subcommand group: suite
# ---------------------------------------------------------------------------

@cli.group("suite")
@click.pass_obj
def cmd_suite(obj: EvalContext):
    """Manage and inspect test suites."""
    pass


@cmd_suite.command("list")
@click.pass_obj
def suite_list(obj: EvalContext):
    """List all available suites with case counts and categories."""
    from src.cli.suite import suite_list_command
    suite_list_command(ctx=obj)


@cmd_suite.command("show")
@click.argument("name")
@click.pass_obj
def suite_show(obj: EvalContext, name: str):
    """Print all test cases in SUITE with their IDs, prompts, and rubrics."""
    from src.cli.suite import suite_show_command
    suite_show_command(ctx=obj, name=name)


@cmd_suite.command("validate")
@click.argument("name")
@click.option("--verbose", "-v", is_flag=True, default=False, help="Print each parsed test case.")
@click.pass_obj
def suite_validate(obj: EvalContext, name: str, verbose: bool):
    """Parse and validate SUITE YAML — catch schema errors before a run."""
    from src.cli.suite import suite_validate_command
    suite_validate_command(ctx=obj, name=name, verbose=verbose)


@cmd_suite.command("add")
@click.argument("name")
@click.pass_obj
def suite_add(obj: EvalContext, name: str):
    """Interactive wizard to add a new test case to an existing suite."""
    from src.cli.suite import suite_add_command
    suite_add_command(ctx=obj, name=name)


@cmd_suite.command("new")
@click.argument("name")
@click.pass_obj
def suite_new(obj: EvalContext, name: str):
    """Scaffold a new suite YAML with boilerplate and comments."""
    from src.cli.suite import suite_new_command
    suite_new_command(ctx=obj, name=name)


# ---------------------------------------------------------------------------
# Subcommand: models
# ---------------------------------------------------------------------------

@cli.command("models")
@click.option("--filter", "filter_term", default=None, help="Filter by name substring (e.g. 'mistral').")
@click.option("--free", is_flag=True, default=False, help="Show only models with no per-token cost.")
@click.option("--context", default=None, type=int, help="Minimum context window size (e.g. 32000).")
@click.option("--supports-tools", is_flag=True, default=False, help="Only show models that support function calling.")
@click.pass_obj
def cmd_models(
    obj: EvalContext,
    filter_term: str | None,
    free: bool,
    context: int | None,
    supports_tools: bool,
):
    """List and filter available models from OpenRouter."""
    from src.cli.models import models_command
    models_command(
        ctx=obj,
        filter_term=filter_term,
        free=free,
        min_context=context,
        supports_tools=supports_tools,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cli()
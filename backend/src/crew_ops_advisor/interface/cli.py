"""Command-line interface: `crew-ops <command>`.

    ask "<question>" [--provider agent-sdk|anthropic|offline] [--json] [--no-trace]
                                           one question, answer + reasoning trail
    chat [--provider ...]                  interactive multi-turn session (dev harness)
    eval [--tier 1 2 3] [--ids Q01 ...] [--provider ...] [--out DIR]
                                           grade against questions.json answer keys
    serve [--host H] [--port P] [--provider ...]
                                           local HTTP API (+ the built React UI at /)
    build-db [--force]                     build/refresh var/crew_ops.db from data/*.json
    check <crew_id> <pairing_id> [--from D] [--callout]
                                           legality of a crew member covering a pairing
    rostered <crew_id> <pairing_id> [--on D]
                                           re-evaluate a crew member's own rostered pairing/day

Exit codes: 0 ok/legal · 1 not legal (check/rostered) or evals not all passed · 2 error.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from datetime import date
from pathlib import Path

from crew_ops_advisor.agent import PROVIDERS, make_advisor, render_trace
from crew_ops_advisor.config import Settings
from crew_ops_advisor.data import Datastore, NotFoundError, ensure_database
from crew_ops_advisor.evals import load_questions, run_evals, write_report
from crew_ops_advisor.rules import CrewContext, evaluate_duties, evaluate_rostered

EXIT_OK, EXIT_NOT_LEGAL, EXIT_ERROR = 0, 1, 2
EXIT_LEGAL = EXIT_OK

_BACKEND_ROOT = Path(__file__).resolve().parents[3]


def _parse_date(value: str | None, flag: str) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"error: {flag} expects YYYY-MM-DD, got {value!r}") from exc


def _settings(args: argparse.Namespace) -> Settings:
    settings = Settings.from_env()
    provider = getattr(args, "provider", None)
    if provider:
        settings = dataclasses.replace(settings, llm_provider=provider)
    return settings


# ---------------------------------------------------------------- conversational


def _print_answer(answer, *, as_json: bool, show_trace: bool) -> None:
    if as_json:
        print(json.dumps(answer.to_dict(), indent=2, default=str))
        return
    print(answer.text)
    if show_trace:
        print()
        print(render_trace(answer))


def _cmd_ask(args: argparse.Namespace, settings: Settings) -> int:
    with Datastore.open(settings) as store:
        advisor = make_advisor(settings, store)
        answer = advisor.ask(args.question)
    _print_answer(answer, as_json=args.json, show_trace=not args.no_trace)
    return EXIT_ERROR if answer.error else EXIT_OK


def _cmd_chat(args: argparse.Namespace, settings: Settings) -> int:
    with Datastore.open(settings) as store:
        advisor = make_advisor(settings, store)
        conversation = advisor.new_conversation()
        print(
            f"Crew Ops Advisor — provider: {advisor.provider.name}. Ask a question; 'quit' to exit."
        )
        while True:
            try:
                line = input("\ncontroller> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not line:
                continue
            if line.lower() in ("quit", "exit", "q"):
                break
            answer = advisor.ask(line, conversation)
            print()
            _print_answer(answer, as_json=False, show_trace=not args.no_trace)
    return EXIT_OK


def _cmd_eval(args: argparse.Namespace, settings: Settings) -> int:
    with Datastore.open(settings) as store:
        advisor = make_advisor(settings, store)
        questions = load_questions(store, tiers=args.tier, ids=args.ids)
        if not questions:
            raise ValueError("no questions matched the tier/id filters")
        report = run_evals(advisor, questions)
    out_dir = Path(args.out) if args.out else _BACKEND_ROOT / "evals" / "reports"
    json_path, md_path = write_report(report, out_dir, stem=args.stem)
    print(report.summary())
    for row in report.rows:
        mark = "PASS" if row.grade.passed else ("REFUSED" if row.answer.refused else "MISS")
        extra = f" — missing: {', '.join(row.grade.missing)}" if row.grade.missing else ""
        qid, tier, ms = row.question.question_id, row.question.tier, row.answer.elapsed_ms
        print(f"  {qid} T{tier} {mark:<7} {ms:6.0f} ms{extra}")
    print(f"report: {md_path} (+ {json_path.name})")
    return EXIT_OK if report.passed == report.total else EXIT_NOT_LEGAL


def _cmd_serve(args: argparse.Namespace, settings: Settings) -> int:
    from crew_ops_advisor.interface.api import serve

    serve(args.host, args.port, settings=settings)
    return EXIT_OK


# ---------------------------------------------------------------- deterministic core


def _cmd_build_db(args: argparse.Namespace, settings: Settings) -> int:
    report = ensure_database(settings.data_dir, settings.db_path, force=args.force)
    print(report.summary() if report else f"{settings.db_path}: up to date")
    return EXIT_OK


def _cmd_check(args: argparse.Namespace, settings: Settings) -> int:
    with Datastore.open(settings) as store:
        ctx = CrewContext.load(store, args.crew_id)
        pairing = store.pairings.get(args.pairing_id)
        start = _parse_date(args.from_date, "--from")
        duties = store.pairings.duty_periods(pairing, from_date=start)
        if not duties:
            operates = ", ".join(d.isoformat() for d in pairing.dates)
            raise ValueError(
                f"{pairing.pairing_id} has no duty days on or after {start} (operates {operates})"
            )
        evidence = evaluate_duties(ctx, store.ruleset, duties, callout=args.callout)
    _print_evidence(evidence, args.json)
    return EXIT_LEGAL if evidence.legal else EXIT_NOT_LEGAL


def _cmd_rostered(args: argparse.Namespace, settings: Settings) -> int:
    with Datastore.open(settings) as store:
        ctx = CrewContext.load(store, args.crew_id)
        on = _parse_date(args.on, "--on")
        evidence = evaluate_rostered(ctx, store.ruleset, args.pairing_id, on=on)
    _print_evidence(evidence, args.json)
    return EXIT_LEGAL if evidence.legal else EXIT_NOT_LEGAL


def _print_evidence(evidence, as_json: bool) -> None:
    if as_json:
        print(json.dumps(evidence.to_dict(), indent=2))
        return
    verdict = "LEGAL" if evidence.legal else "NOT LEGAL"
    print(
        f"{evidence.crew_id} on {', '.join(d.isoformat() for d in evidence.duty_dates)}: {verdict}"
    )
    for v in evidence.verdicts:
        mark = {"pass": "✓", "breach": "✗", "conditional": "~"}[v.status.value]
        print(f"  {mark} {v.rule_id:<13} {v.detail}")


# ---------------------------------------------------------------- parser


def _add_provider(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--provider",
        choices=list(PROVIDERS),
        help="language model provider (default: CREW_OPS_LLM_PROVIDER or agent-sdk)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crew-ops", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ask", help="answer one question")
    p.add_argument("question")
    _add_provider(p)
    p.add_argument("--json", action="store_true", help="print the answer + trace as JSON")
    p.add_argument("--no-trace", action="store_true", help="hide the reasoning trail")
    p.set_defaults(func=_cmd_ask)

    p = sub.add_parser("chat", help="interactive multi-turn session")
    _add_provider(p)
    p.add_argument("--no-trace", action="store_true")
    p.set_defaults(func=_cmd_chat)

    p = sub.add_parser("eval", help="grade against questions.json answer keys")
    p.add_argument("--tier", type=int, nargs="+", default=[1], choices=[1, 2, 3])
    p.add_argument("--ids", nargs="+", metavar="QID", help="only these question ids")
    _add_provider(p)
    p.add_argument("--out", metavar="DIR", help="report directory (default evals/reports)")
    p.add_argument("--stem", metavar="NAME", help="report file stem (default provider-timestamp)")
    p.set_defaults(func=_cmd_eval)

    p = sub.add_parser("serve", help="run the local HTTP API (and the React UI if built)")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    _add_provider(p)
    p.set_defaults(func=_cmd_serve)

    p = sub.add_parser("build-db", help="build or refresh the SQLite database")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=_cmd_build_db)

    p = sub.add_parser("check", help="legality of a crew member covering a pairing")
    p.add_argument("crew_id")
    p.add_argument("pairing_id")
    p.add_argument("--from", dest="from_date", metavar="YYYY-MM-DD", help="first day to cover")
    p.add_argument(
        "--callout", action="store_true", help="treat as reserve/day-off callout (RULE-BASE-07)"
    )
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_check)

    p = sub.add_parser("rostered", help="re-evaluate a crew member's own rostered pairing")
    p.add_argument("crew_id")
    p.add_argument("pairing_id")
    p.add_argument("--on", metavar="YYYY-MM-DD", help="one day of the pairing only")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_rostered)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args, _settings(args))
    except (NotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except SystemExit as exc:  # our own usage errors carry a message; argparse's carry a code
        if isinstance(exc.code, str):
            print(exc.code, file=sys.stderr)
            return EXIT_ERROR
        raise

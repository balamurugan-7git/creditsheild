"""
run_psi_monthly.py
==================
CLI script to run Population Stability Index (PSI) monitoring for CrediShield AI.

Intended to be executed monthly (e.g., from a cron job or CI pipeline) to
detect feature distribution drift between the training dataset and new
production data.

Exit Codes
----------
  0 — All features are stable (no PSI > threshold)
  1 — One or more features have drifted (PSI > threshold) → alert / retraining

Usage
-----
    python scripts/run_psi_monthly.py \\
        --training-data data/application_train.csv \\
        --new-data data/production_sept_2024.csv \\
        --output reports/psi_report_2024_09.json \\
        --threshold 0.2

Example CI step (GitHub Actions / Jenkins):
    - run: python scripts/run_psi_monthly.py ... && echo "PSI OK" || echo "DRIFT DETECTED"
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# Allow running from repo root or scripts/ directory
_SCRIPTS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPTS_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.monitoring.psi import generate_psi_report  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_summary_table(report: dict, threshold: float) -> None:
    """Print a human-readable PSI summary table to stdout."""
    feature_psi = report.get("feature_psi", {})
    severity = report.get("severity", {})

    # Sort by PSI descending (worst first)
    sorted_features = sorted(feature_psi.items(), key=lambda x: x[1], reverse=True)

    border = "=" * 65
    print(f"\n{border}")
    print(f"  CrediShield AI — PSI Monthly Report")
    print(f"  Computed at : {report.get('computed_at', 'N/A')}")
    print(f"  Threshold   : {threshold}")
    print(f"  Train rows  : {report.get('training_rows', 'N/A')}")
    print(f"  New rows    : {report.get('new_rows', 'N/A')}")
    print(border)
    print(f"  {'Feature':<40} {'PSI':>8}  {'Status'}")
    print("-" * 65)

    for feat, psi_val in sorted_features:
        sev = severity.get(feat, "")
        flag = " ⚠" if psi_val > threshold else ""
        print(f"  {feat:<40} {psi_val:>8.4f}  {sev}{flag}")

    print(border)
    flagged = report.get("flagged_features", [])
    print(f"\n  SUMMARY: {report.get('total_features', 0)} features evaluated.")
    print(f"  {len(flagged)} feature(s) flagged (PSI > {threshold}):")
    for f in flagged:
        print(f"    • {f} (PSI={feature_psi.get(f, 0):.4f})")
    print()


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    today_str = datetime.now(tz=timezone.utc).strftime("%Y%m%d")

    parser = argparse.ArgumentParser(
        prog="run_psi_monthly",
        description=(
            "Compute Population Stability Index (PSI) between training data "
            "and a new month's production data. Exits with code 1 if any "
            "feature PSI exceeds the specified threshold."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--training-data",
        required=True,
        metavar="PATH",
        help="Path to the reference (training) CSV file.",
    )
    parser.add_argument(
        "--new-data",
        required=True,
        metavar="PATH",
        help="Path to the new month's CSV file to compare against training.",
    )
    parser.add_argument(
        "--output",
        default=f"psi_report_{today_str}.json",
        metavar="PATH",
        help=(
            "Output path for the JSON report. "
            f"Default: psi_report_{today_str}.json"
        ),
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.2,
        metavar="FLOAT",
        help=(
            "PSI threshold above which a feature is flagged as drifted. "
            "Default: 0.2 (industry standard for 'shift')."
        ),
    )
    parser.add_argument(
        "--columns",
        nargs="*",
        default=None,
        metavar="COL",
        help=(
            "Specific columns to evaluate. "
            "If omitted, uses all common columns between both CSVs "
            "(excluding the target column TARGET if present)."
        ),
    )

    return parser


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Execute PSI monitoring pipeline.

    Returns
    -------
    int
        Exit code: 0 = all stable, 1 = drift detected.
    """
    parser = _build_parser()
    args = parser.parse_args()

    # --- Validate input paths ---
    train_path = Path(args.training_data)
    new_path = Path(args.new_data)

    if not train_path.exists():
        print(f"[ERROR] Training data not found: {train_path.resolve()}", file=sys.stderr)
        return 1
    if not new_path.exists():
        print(f"[ERROR] New data not found: {new_path.resolve()}", file=sys.stderr)
        return 1

    # --- Load data ---
    print(f"[run_psi_monthly] Loading training data from: {train_path}")
    training_df = pd.read_csv(train_path)
    print(f"[run_psi_monthly] Training data shape: {training_df.shape}")

    print(f"[run_psi_monthly] Loading new data from: {new_path}")
    new_df = pd.read_csv(new_path)
    print(f"[run_psi_monthly] New data shape: {new_df.shape}")

    # --- Determine feature columns ---
    if args.columns:
        feature_cols = args.columns
    else:
        # Use intersection of columns from both datasets, excluding target/id columns
        exclude = {"TARGET", "SK_ID_CURR"}
        common_cols = set(training_df.columns) & set(new_df.columns)
        feature_cols = sorted(common_cols - exclude)
        print(
            f"[run_psi_monthly] Auto-selected {len(feature_cols)} common feature columns."
        )

    if not feature_cols:
        print("[ERROR] No feature columns found to evaluate.", file=sys.stderr)
        return 1

    # --- Generate PSI report ---
    print(f"[run_psi_monthly] Computing PSI for {len(feature_cols)} features ...")
    report = generate_psi_report(
        training_df=training_df,
        new_df=new_df,
        feature_cols=feature_cols,
        threshold=args.threshold,
        output_path=args.output,
    )

    # --- Print summary table to stdout ---
    _print_summary_table(report, threshold=args.threshold)

    # --- Exit code logic ---
    flagged = report.get("flagged_features", [])
    if flagged:
        print(
            f"[run_psi_monthly] ⚠  DRIFT DETECTED: {len(flagged)} feature(s) "
            f"exceed PSI threshold {args.threshold}. Exiting with code 1.",
            file=sys.stderr,
        )
        return 1
    else:
        print(
            f"[run_psi_monthly] ✓  All features stable (PSI ≤ {args.threshold}). "
            "Exiting with code 0."
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())

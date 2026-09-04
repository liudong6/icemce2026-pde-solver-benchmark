from __future__ import annotations

import argparse
import csv
from pathlib import Path

from pdescale.difficulty_analysis import (
    analyze_difficulty_relationships,
    write_difficulty_relationship_csv,
)


def read_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze rank relationships between coefficient difficulty and solver behaviour."
    )
    parser.add_argument("--solver-decision-csv", default="results/raw/solver_decision_map.csv")
    parser.add_argument("--conditioning-csv", default="results/raw/conditioning.csv")
    parser.add_argument("--output", default="results/raw/difficulty_relationships.csv")
    args = parser.parse_args()

    rows = analyze_difficulty_relationships(
        read_rows(args.solver_decision_csv),
        read_rows(args.conditioning_csv),
    )
    write_difficulty_relationship_csv(rows, args.output)
    print(f"wrote {args.output} ({len(rows)} rows)")


if __name__ == "__main__":
    main()

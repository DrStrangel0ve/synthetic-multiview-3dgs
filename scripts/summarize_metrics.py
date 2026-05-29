#!/usr/bin/env python3
"""Extract Nerfstudio eval metrics into compact CSV/Markdown summaries."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, default=Path("results/metrics/ceramic_idol_turntable.json"))
    parser.add_argument("--output-prefix", type=Path, default=Path("results/synthetic_summary"))
    parser.add_argument("--dataset", default="ceramic_idol_turntable")
    parser.add_argument("--views", type=int, default=None)
    return parser.parse_args()


def find_metric(payload: Any, names: tuple[str, ...]) -> float | None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key.lower() in names and isinstance(value, (int, float)):
                return float(value)
            found = find_metric(value, names)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = find_metric(value, names)
            if found is not None:
                return found
    return None


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def main() -> None:
    args = parse_args()
    payload = json.loads(args.metrics.read_text(encoding="utf-8")) if args.metrics.exists() else {}
    row = {
        "dataset": args.dataset,
        "views": args.views,
        "psnr": find_metric(payload, ("psnr",)),
        "ssim": find_metric(payload, ("ssim",)),
        "lpips": find_metric(payload, ("lpips",)),
        "metrics_path": str(args.metrics) if args.metrics.exists() else "",
    }
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_prefix.with_suffix(".csv")
    md_path = args.output_prefix.with_suffix(".md")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow({key: fmt(value) for key, value in row.items()})
    lines = [
        "# Synthetic Multiview Summary",
        "",
        "| Dataset | Views | PSNR | SSIM | LPIPS | Metrics |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
        f"| `{row['dataset']}` | {fmt(row['views'])} | {fmt(row['psnr'])} | {fmt(row['ssim'])} | {fmt(row['lpips'])} | `{row['metrics_path']}` |",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {csv_path} and {md_path}")


if __name__ == "__main__":
    main()

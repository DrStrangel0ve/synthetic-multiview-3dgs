#!/usr/bin/env python3
"""Summarize several Splatfacto runs over the same synthetic multiview dataset."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


RUNS = [
    {
        "run": "700_iters",
        "iterations": 700,
        "metrics": Path("results/metrics/ceramic_idol_turntable_700.json"),
        "export": Path("exports/ceramic_idol_turntable_700/ceramic_idol_turntable_700.ply"),
    },
    {
        "run": "3000_iters",
        "iterations": 3000,
        "metrics": Path("results/metrics/ceramic_idol_turntable_3000.json"),
        "export": Path("exports/ceramic_idol_turntable_3000/ceramic_idol_turntable_3000.ply"),
    },
]


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def row_for(run: dict[str, Any]) -> dict[str, Any]:
    payload = json.loads(run["metrics"].read_text(encoding="utf-8"))
    results = payload["results"]
    export = run["export"]
    return {
        "run": run["run"],
        "iterations": run["iterations"],
        "psnr": results.get("psnr"),
        "ssim": results.get("ssim"),
        "lpips": results.get("lpips"),
        "fps": results.get("fps"),
        "export_mb": export.stat().st_size / (1024 * 1024) if export.exists() else None,
        "metrics_path": str(run["metrics"]),
        "export_path": str(export) if export.exists() else "",
    }


def main() -> None:
    rows = [row_for(run) for run in RUNS]
    output_prefix = Path("results/run_comparison")
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    csv_path = output_prefix.with_suffix(".csv")
    md_path = output_prefix.with_suffix(".md")

    fieldnames = list(rows[0])
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: fmt(row.get(field)) for field in fieldnames})

    lines = [
        "# Synthetic Splatfacto Run Comparison",
        "",
        "| Run | Iterations | PSNR | SSIM | LPIPS | FPS | Export MB |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['run']}` | {row['iterations']} | {fmt(row['psnr'])} | {fmt(row['ssim'])} | {fmt(row['lpips'])} | {fmt(row['fps'])} | {fmt(row['export_mb'])} |"
        )
    lines.extend(
        [
            "",
            "In this first synthetic run, the shorter 700-iteration checkpoint has better PSNR/SSIM, while the 3,000-iteration checkpoint has better LPIPS but a much larger exported splat.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {csv_path} and {md_path}")


if __name__ == "__main__":
    main()

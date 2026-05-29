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
        "source": "procedural",
        "views": 48,
        "iterations": 700,
        "eval": "fraction",
        "metrics": Path("results/metrics/ceramic_idol_turntable_700.json"),
        "export": Path("exports/ceramic_idol_turntable_700/ceramic_idol_turntable_700.ply"),
    },
    {
        "run": "3000_iters",
        "source": "procedural",
        "views": 48,
        "iterations": 3000,
        "eval": "fraction",
        "metrics": Path("results/metrics/ceramic_idol_turntable_3000.json"),
        "export": Path("exports/ceramic_idol_turntable_3000/ceramic_idol_turntable_3000.ply"),
    },
    {
        "run": "genai_16_views_700",
        "source": "generated contact sheet",
        "views": 16,
        "iterations": 700,
        "eval": "fraction",
        "metrics": Path("results/metrics/genai_ceramic_idol_16_700.json"),
        "export": Path("exports/genai_ceramic_idol_16_700/genai_ceramic_idol_16_700.ply"),
    },
    {
        "run": "zero123plus_seed123_6_evalall",
        "source": "Zero123++ seed 123",
        "views": 6,
        "iterations": 700,
        "eval": "all frames",
        "metrics": Path("results/metrics/zero123plus_seed123_6_700_evalall.json"),
        "export": Path("exports/zero123plus_seed123_6_700_evalall/zero123plus_seed123_6_700_evalall.ply"),
    },
    {
        "run": "zero123plus_seed123_6_holdout",
        "source": "Zero123++ seed 123",
        "views": 6,
        "iterations": 700,
        "eval": "interval 3",
        "metrics": Path("results/metrics/zero123plus_seed123_6_700_interval3.json"),
        "export": Path("exports/zero123plus_seed123_6_700_interval3/zero123plus_seed123_6_700_interval3.ply"),
    },
    {
        "run": "zero123plus_seed123_steps75_holdout",
        "source": "Zero123++ seed 123, 75 steps",
        "views": 6,
        "iterations": 700,
        "eval": "interval 3",
        "metrics": Path("results/metrics/zero123plus_seed123_steps75_6_700_interval3.json"),
        "export": Path(
            "exports/zero123plus_seed123_steps75_6_700_interval3/zero123plus_seed123_steps75_6_700_interval3.ply"
        ),
    },
    {
        "run": "zero123plus_seed456_holdout",
        "source": "Zero123++ seed 456",
        "views": 6,
        "iterations": 700,
        "eval": "interval 3",
        "metrics": Path("results/metrics/zero123plus_seed456_6_700_interval3.json"),
        "export": Path("exports/zero123plus_seed456_6_700_interval3/zero123plus_seed456_6_700_interval3.ply"),
    },
    {
        "run": "zero123plus_seed456_masked_holdout",
        "source": "Zero123++ seed 456, masks",
        "views": 6,
        "iterations": 700,
        "eval": "interval 3",
        "metrics": Path("results/metrics/zero123plus_seed456_6_masked_700_interval3.json"),
        "export": Path(
            "exports/zero123plus_seed456_6_masked_700_interval3/zero123plus_seed456_6_masked_700_interval3.ply"
        ),
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
        "source": run["source"],
        "views": run["views"],
        "iterations": run["iterations"],
        "eval": run["eval"],
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
        "| Run | Source | Views | Iterations | Eval | PSNR | SSIM | LPIPS | FPS | Export MB |",
        "| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['run']}` | {row['source']} | {row['views']} | {row['iterations']} | {row['eval']} | {fmt(row['psnr'])} | {fmt(row['ssim'])} | {fmt(row['lpips'])} | {fmt(row['fps'])} | {fmt(row['export_mb'])} |"
        )
    lines.extend(
        [
            "",
            "Zero123++ is the current best pure-generation path. Eval-all is an upper bound because it evaluates training views; interval-3 is the fairer tiny-dataset holdout.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {csv_path} and {md_path}")


if __name__ == "__main__":
    main()

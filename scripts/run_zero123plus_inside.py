"""Generate a Zero123++ multiview sheet from one conditioning image."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from diffusers import DiffusionPipeline, EulerAncestralDiscreteScheduler
from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--conditioning-output", type=Path, default=None)
    parser.add_argument("--model", default="sudo-ai/zero123plus-v1.2")
    parser.add_argument("--custom-pipeline", default="sudo-ai/zero123plus-pipeline")
    parser.add_argument("--steps", type=int, default=36)
    parser.add_argument("--seed", type=int, default=123)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is required for this Zero123++ run.")

    cond = Image.open(args.input).convert("RGB")
    side = max(cond.size)
    square = Image.new("RGB", (side, side), (232, 232, 232))
    square.paste(cond, ((side - cond.width) // 2, (side - cond.height) // 2))
    cond = square.resize((512, 512), Image.Resampling.LANCZOS)

    if args.conditioning_output:
        args.conditioning_output.parent.mkdir(parents=True, exist_ok=True)
        cond.save(args.conditioning_output)

    generator = torch.Generator(device="cuda").manual_seed(args.seed)
    pipe = DiffusionPipeline.from_pretrained(
        args.model,
        custom_pipeline=args.custom_pipeline,
        torch_dtype=torch.float16,
    )
    pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(
        pipe.scheduler.config,
        timestep_spacing="trailing",
    )
    pipe = pipe.to("cuda:0")

    with torch.inference_mode():
        result = pipe(cond, num_inference_steps=args.steps, generator=generator).images[0]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.save(args.output)
    metadata_path = args.output.with_suffix(".json")
    metadata_path.write_text(
        json.dumps(
            {
                "input": str(args.input),
                "output": str(args.output),
                "model": args.model,
                "custom_pipeline": args.custom_pipeline,
                "steps": args.steps,
                "seed": args.seed,
                "grid": {"columns": 2, "rows": 3},
                "camera": {
                    "azimuth_degrees": [30, 90, 150, 210, 270, 330],
                    "elevation_degrees": [20, -10, 20, -10, 20, -10],
                    "fov_degrees": 30,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"output": str(args.output), "metadata": str(metadata_path)}, indent=2))


if __name__ == "__main__":
    main()

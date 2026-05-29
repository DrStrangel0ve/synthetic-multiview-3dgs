"""Split a generated multiview contact sheet into a Nerfstudio dataset."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


DEFAULT_PROMPT = (
    "A small glossy ceramic sci-fi desk idol, somewhere between a toy robot "
    "and a crystal mushroom, with teal glass highlights, amber side fins, "
    "a smooth white ceramic body, and tiny black eyes."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("datasets/genai_ceramic_idol_source/contact_sheet.png"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("datasets/genai_ceramic_idol_16"),
    )
    parser.add_argument("--grid", type=int, default=4)
    parser.add_argument("--size", type=int, default=384)
    parser.add_argument("--crop-margin", type=int, default=3)
    parser.add_argument("--fov-degrees", type=float, default=45.0)
    parser.add_argument("--radius", type=float, default=3.2)
    parser.add_argument("--height", type=float, default=1.05)
    parser.add_argument("--target-z", type=float, default=0.22)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    return parser.parse_args()


def normalize(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm < 1e-8:
        return vector
    return vector / norm


def look_at(camera: np.ndarray, target: np.ndarray) -> np.ndarray:
    back = normalize(camera - target)
    right = normalize(np.cross(np.array([0.0, 0.0, 1.0], dtype=np.float32), back))
    up = np.cross(back, right)
    matrix = np.eye(4, dtype=np.float32)
    matrix[:3, 0] = right
    matrix[:3, 1] = up
    matrix[:3, 2] = back
    matrix[:3, 3] = camera
    return matrix


def crop_cells(source: Image.Image, grid: int, margin: int) -> list[Image.Image]:
    width, height = source.size
    cells: list[Image.Image] = []
    for row in range(grid):
        for col in range(grid):
            left = round(col * width / grid) + margin
            upper = round(row * height / grid) + margin
            right = round((col + 1) * width / grid) - margin
            lower = round((row + 1) * height / grid) - margin
            cells.append(source.crop((left, upper, right, lower)))
    return cells


def write_contact_sheet(image_paths: list[Path], output: Path, columns: int = 4) -> None:
    images = [Image.open(path).convert("RGB") for path in image_paths]
    thumb_size = 160
    rows = math.ceil(len(images) / columns)
    sheet = Image.new("RGB", (columns * thumb_size, rows * thumb_size), (235, 238, 240))
    for index, image in enumerate(images):
        image.thumbnail((thumb_size, thumb_size))
        x = (index % columns) * thumb_size
        y = (index // columns) * thumb_size
        sheet.paste(image, (x, y))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=92)


def main() -> None:
    args = parse_args()
    source = Image.open(args.source).convert("RGB")
    cells = crop_cells(source, args.grid, args.crop_margin)
    image_dir = args.output / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    views = len(cells)
    target = np.array([0.0, 0.0, args.target_z], dtype=np.float32)
    frames: list[dict[str, Any]] = []
    image_paths: list[Path] = []

    for index, cell in enumerate(cells):
        rel_path = Path("images") / f"view_{index:03d}.png"
        image_path = args.output / rel_path
        cell.resize((args.size, args.size), Image.Resampling.LANCZOS).save(image_path)
        image_paths.append(image_path)

        theta = 2.0 * math.pi * index / views
        camera = np.array(
            [
                args.radius * math.sin(theta),
                -args.radius * math.cos(theta),
                args.height,
            ],
            dtype=np.float32,
        )
        frames.append(
            {
                "file_path": rel_path.as_posix(),
                "transform_matrix": look_at(camera, target).tolist(),
            }
        )

    fl = 0.5 * args.size / math.tan(math.radians(args.fov_degrees) * 0.5)
    transforms = {
        "camera_model": "OPENCV",
        "fl_x": fl,
        "fl_y": fl,
        "cx": args.size / 2.0,
        "cy": args.size / 2.0,
        "w": args.size,
        "h": args.size,
        "camera_angle_x": math.radians(args.fov_degrees),
        "prompt": args.prompt,
        "source": args.source.as_posix(),
        "frames": frames,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "transforms.json").write_text(json.dumps(transforms, indent=2), encoding="utf-8")
    (args.output / "scene_prompt.txt").write_text(args.prompt + "\n", encoding="utf-8")
    write_contact_sheet(image_paths, args.output / "preview_contact_sheet.jpg")

    print(
        json.dumps(
            {
                "source": str(args.source),
                "dataset": str(args.output),
                "views": views,
                "size": args.size,
                "focal": fl,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

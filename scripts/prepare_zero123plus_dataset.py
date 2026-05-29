"""Convert a Zero123++ six-view sheet into a Nerfstudio dataset."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


ZERO123PLUS_AZIMUTHS = [30.0, 90.0, 150.0, 210.0, 270.0, 330.0]
ZERO123PLUS_V12_ELEVATIONS = [20.0, -10.0, 20.0, -10.0, 20.0, -10.0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed-image", type=Path, default=None)
    parser.add_argument("--include-seed", action="store_true")
    parser.add_argument("--grid-cols", type=int, default=2)
    parser.add_argument("--grid-rows", type=int, default=3)
    parser.add_argument("--size", type=int, default=384)
    parser.add_argument("--radius", type=float, default=3.2)
    parser.add_argument("--target-z", type=float, default=0.22)
    parser.add_argument("--fov-degrees", type=float, default=30.0)
    parser.add_argument("--prompt", default="Zero123++ generated multiview ceramic desk idol.")
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


def camera_position(radius: float, target_z: float, azimuth: float, elevation: float) -> np.ndarray:
    az = math.radians(azimuth)
    el = math.radians(elevation)
    return np.array(
        [
            radius * math.cos(el) * math.sin(az),
            -radius * math.cos(el) * math.cos(az),
            target_z + radius * math.sin(el),
        ],
        dtype=np.float32,
    )


def split_sheet(sheet: Image.Image, cols: int, rows: int) -> list[Image.Image]:
    width, height = sheet.size
    cells: list[Image.Image] = []
    for row in range(rows):
        for col in range(cols):
            left = round(col * width / cols)
            upper = round(row * height / rows)
            right = round((col + 1) * width / cols)
            lower = round((row + 1) * height / rows)
            cells.append(sheet.crop((left, upper, right, lower)))
    return cells


def save_square(image: Image.Image, path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").resize((size, size), Image.Resampling.LANCZOS).save(path)


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
    target = np.array([0.0, 0.0, args.target_z], dtype=np.float32)
    image_dir = args.output / "images"
    frames: list[dict[str, Any]] = []
    image_paths: list[Path] = []

    def append_frame(image: Image.Image, azimuth: float, elevation: float, name: str) -> None:
        rel_path = Path("images") / name
        image_path = args.output / rel_path
        save_square(image, image_path, args.size)
        c2w = look_at(camera_position(args.radius, args.target_z, azimuth, elevation), target)
        frames.append(
            {
                "file_path": rel_path.as_posix(),
                "transform_matrix": c2w.tolist(),
                "azimuth_degrees": azimuth,
                "elevation_degrees": elevation,
            }
        )
        image_paths.append(image_path)

    if args.include_seed:
        if args.seed_image is None:
            raise SystemExit("--include-seed requires --seed-image")
        append_frame(Image.open(args.seed_image), 0.0, 0.0, "view_000_seed.png")

    sheet = Image.open(args.sheet).convert("RGB")
    expected_views = args.grid_cols * args.grid_rows
    if expected_views != len(ZERO123PLUS_AZIMUTHS):
        raise SystemExit(f"expected 6 Zero123++ views, got a {args.grid_cols}x{args.grid_rows} grid")
    for index, (cell, azimuth, elevation) in enumerate(
        zip(split_sheet(sheet, args.grid_cols, args.grid_rows), ZERO123PLUS_AZIMUTHS, ZERO123PLUS_V12_ELEVATIONS),
        start=1 if args.include_seed else 0,
    ):
        append_frame(cell, azimuth, elevation, f"view_{index:03d}.png")

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
        "source_sheet": args.sheet.as_posix(),
        "frames": frames,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "transforms.json").write_text(json.dumps(transforms, indent=2), encoding="utf-8")
    (args.output / "scene_prompt.txt").write_text(args.prompt + "\n", encoding="utf-8")
    write_contact_sheet(image_paths, args.output / "preview_contact_sheet.jpg")
    print(json.dumps({"dataset": str(args.output), "views": len(frames), "focal": fl}, indent=2))


if __name__ == "__main__":
    main()

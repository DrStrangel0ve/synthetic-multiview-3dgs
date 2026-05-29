#!/usr/bin/env python3
"""Render a prompt-defined synthetic object from known turntable camera views."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/synthetic_object.json"))
    parser.add_argument("--output", type=Path, default=Path("datasets/ceramic_idol_turntable"))
    parser.add_argument("--views", type=int, default=None)
    parser.add_argument("--size", type=int, default=None)
    parser.add_argument("--steps", type=int, default=96)
    return parser.parse_args()


def length(v: np.ndarray) -> np.ndarray:
    return np.linalg.norm(v, axis=-1)


def normalize(v: np.ndarray) -> np.ndarray:
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-8)


def sd_sphere(p: np.ndarray, center: tuple[float, float, float], radius: float) -> np.ndarray:
    return length(p - np.asarray(center, dtype=np.float32)) - radius


def sd_ellipsoid(p: np.ndarray, center: tuple[float, float, float], radii: tuple[float, float, float]) -> np.ndarray:
    q = (p - np.asarray(center, dtype=np.float32)) / np.asarray(radii, dtype=np.float32)
    return (length(q) - 1.0) * min(radii)


def sd_round_box(p: np.ndarray, center: tuple[float, float, float], half_extents: tuple[float, float, float], radius: float) -> np.ndarray:
    q = np.abs(p - np.asarray(center, dtype=np.float32)) - np.asarray(half_extents, dtype=np.float32)
    outside = length(np.maximum(q, 0.0))
    inside = np.minimum(np.maximum.reduce(q, axis=-1), 0.0)
    return outside + inside - radius


def sd_cylinder_z(p: np.ndarray, center: tuple[float, float, float], radius: float, half_height: float) -> np.ndarray:
    qx = np.sqrt((p[..., 0] - center[0]) ** 2 + (p[..., 1] - center[1]) ** 2) - radius
    qy = np.abs(p[..., 2] - center[2]) - half_height
    outside = np.sqrt(np.maximum(qx, 0.0) ** 2 + np.maximum(qy, 0.0) ** 2)
    inside = np.minimum(np.maximum(qx, qy), 0.0)
    return outside + inside


def component_distances(p: np.ndarray) -> list[np.ndarray]:
    return [
        sd_round_box(p, (0.0, 0.0, -0.16), (0.33, 0.25, 0.48), 0.12),
        sd_ellipsoid(p, (0.0, -0.03, 0.50), (0.48, 0.40, 0.34)),
        sd_ellipsoid(p, (-0.48, -0.01, 0.19), (0.16, 0.10, 0.30)),
        sd_ellipsoid(p, (0.48, -0.01, 0.19), (0.16, 0.10, 0.30)),
        sd_ellipsoid(p, (0.0, 0.0, 0.93), (0.20, 0.17, 0.28)),
        sd_cylinder_z(p, (0.0, 0.0, -0.70), 0.42, 0.08),
        sd_sphere(p, (-0.14, -0.39, 0.55), 0.055),
        sd_sphere(p, (0.14, -0.39, 0.55), 0.055),
        sd_sphere(p, (0.0, -0.405, 0.41), 0.035),
    ]


def scene_sdf(p: np.ndarray) -> np.ndarray:
    return np.minimum.reduce(component_distances(p))


def component_index(p: np.ndarray) -> np.ndarray:
    return np.argmin(np.stack(component_distances(p), axis=-1), axis=-1)


def estimate_normals(p: np.ndarray) -> np.ndarray:
    eps = 0.0025
    dx = scene_sdf(p + np.array([eps, 0.0, 0.0])) - scene_sdf(p - np.array([eps, 0.0, 0.0]))
    dy = scene_sdf(p + np.array([0.0, eps, 0.0])) - scene_sdf(p - np.array([0.0, eps, 0.0]))
    dz = scene_sdf(p + np.array([0.0, 0.0, eps])) - scene_sdf(p - np.array([0.0, 0.0, eps]))
    return normalize(np.stack([dx, dy, dz], axis=-1))


def base_color(p: np.ndarray) -> np.ndarray:
    idx = component_index(p)
    colors = np.zeros((*p.shape[:-1], 3), dtype=np.float32)
    palette = np.asarray(
        [
            [0.90, 0.84, 0.72],
            [0.82, 0.95, 0.92],
            [1.00, 0.55, 0.16],
            [1.00, 0.55, 0.16],
            [0.22, 0.96, 1.00],
            [0.52, 0.43, 0.36],
            [0.02, 0.025, 0.035],
            [0.02, 0.025, 0.035],
            [0.08, 0.03, 0.02],
        ],
        dtype=np.float32,
    )
    for i, color in enumerate(palette):
        colors[idx == i] = color

    stripe = 0.5 + 0.5 * np.sin(18.0 * p[..., 2] + 4.0 * np.sin(5.0 * p[..., 0]))
    body_or_head = (idx == 0) | (idx == 1)
    colors[body_or_head] = colors[body_or_head] * (0.86 + 0.16 * stripe[body_or_head, None])

    crystal = idx == 4
    colors[crystal] = np.clip(colors[crystal] * (0.8 + 0.35 * (p[..., 2][crystal, None] + 0.2)), 0, 1)
    return colors


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


def render_view(size: int, fov_degrees: float, c2w: np.ndarray, steps: int) -> np.ndarray:
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    ndc_x = (x + 0.5 - size * 0.5) / (size * 0.5)
    ndc_y = -(y + 0.5 - size * 0.5) / (size * 0.5)
    focal = 1.0 / math.tan(math.radians(fov_degrees) * 0.5)

    right = c2w[:3, 0]
    up = c2w[:3, 1]
    back = c2w[:3, 2]
    origin = c2w[:3, 3]
    dirs = normalize(ndc_x[..., None] * right + ndc_y[..., None] * up - focal * back)

    t = np.full((size, size), 0.15, dtype=np.float32)
    active = np.ones((size, size), dtype=bool)
    hit = np.zeros((size, size), dtype=bool)
    for _ in range(steps):
        p = origin + dirs * t[..., None]
        d = scene_sdf(p)
        new_hit = active & (d < 0.0025)
        hit |= new_hit
        active &= ~new_hit
        active &= t < 7.5
        t[active] += np.clip(d[active] * 0.82, 0.002, 0.12)
        if not active.any():
            break

    p = origin + dirs * t[..., None]
    normals = estimate_normals(p)
    colors = base_color(p)

    light_dir = normalize(np.array([-0.45, -0.70, 0.90], dtype=np.float32))
    rim_dir = normalize(np.array([0.55, 0.35, 0.75], dtype=np.float32))
    diffuse = np.maximum(np.sum(normals * light_dir, axis=-1), 0.0)
    rim = np.maximum(np.sum(normals * rim_dir, axis=-1), 0.0) ** 3.0
    view = normalize(origin - p)
    half_vec = normalize(light_dir + view)
    spec = np.maximum(np.sum(normals * half_vec, axis=-1), 0.0) ** 42.0

    shaded = colors * (0.22 + 0.78 * diffuse[..., None]) + 0.16 * rim[..., None] + 0.20 * spec[..., None]

    bg_y = np.linspace(0.0, 1.0, size, dtype=np.float32)[:, None]
    bg_x = np.linspace(0.0, 1.0, size, dtype=np.float32)[None, :]
    background = np.dstack(
        [
            np.broadcast_to(0.78 - 0.22 * bg_y + 0.04 * bg_x, (size, size)),
            np.broadcast_to(0.82 - 0.20 * bg_y, (size, size)),
            np.broadcast_to(0.88 - 0.18 * bg_y + 0.02 * np.sin(bg_x * math.pi), (size, size)),
        ]
    ).astype(np.float32)
    vignette = 1.0 - 0.18 * (ndc_x**2 + ndc_y**2)
    background *= vignette[..., None]

    image = background
    image[hit] = shaded[hit]
    image = np.clip(image, 0.0, 1.0) ** (1.0 / 2.2)
    return (image * 255.0 + 0.5).astype(np.uint8)


def write_contact_sheet(image_paths: list[Path], output: Path, columns: int = 8) -> None:
    images = [Image.open(path).convert("RGB") for path in image_paths]
    thumb_size = 128
    rows = math.ceil(len(images) / columns)
    sheet = Image.new("RGB", (columns * thumb_size, rows * thumb_size), (235, 238, 240))
    for i, image in enumerate(images):
        image.thumbnail((thumb_size, thumb_size))
        x = (i % columns) * thumb_size
        y = (i // columns) * thumb_size
        sheet.paste(image, (x, y))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=92)


def main() -> None:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    views = args.views or int(config["views"])
    size = args.size or int(config["image_size"])
    camera_cfg = config["camera"]
    radius = float(camera_cfg["radius"])
    height = float(camera_cfg["height"])
    target = np.asarray(camera_cfg["target"], dtype=np.float32)
    fov = float(camera_cfg["fov_degrees"])

    image_dir = args.output / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    frames: list[dict[str, Any]] = []
    image_paths: list[Path] = []

    for index in range(views):
        theta = 2.0 * math.pi * index / views
        camera = np.array([radius * math.sin(theta), -radius * math.cos(theta), height], dtype=np.float32)
        c2w = look_at(camera, target)
        image = render_view(size, fov, c2w, args.steps)
        rel_path = Path("images") / f"view_{index:03d}.png"
        image_path = args.output / rel_path
        Image.fromarray(image, mode="RGB").save(image_path)
        image_paths.append(image_path)
        frames.append(
            {
                "file_path": rel_path.as_posix(),
                "transform_matrix": c2w.tolist(),
            }
        )
        print(f"wrote {image_path}")

    fl = 0.5 * size / math.tan(math.radians(fov) * 0.5)
    transforms = {
        "camera_model": "OPENCV",
        "fl_x": fl,
        "fl_y": fl,
        "cx": size / 2.0,
        "cy": size / 2.0,
        "w": size,
        "h": size,
        "camera_angle_x": math.radians(fov),
        "prompt": config["prompt"],
        "frames": frames,
    }
    (args.output / "transforms.json").write_text(json.dumps(transforms, indent=2), encoding="utf-8")
    (args.output / "scene_prompt.txt").write_text(config["prompt"] + "\n", encoding="utf-8")
    write_contact_sheet(image_paths, args.output / "preview_contact_sheet.jpg")
    print(json.dumps({"dataset": str(args.output), "views": views, "size": size, "focal": fl}, indent=2))


if __name__ == "__main__":
    main()

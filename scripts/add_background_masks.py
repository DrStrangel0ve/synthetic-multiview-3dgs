"""Add simple border-color masks to a Nerfstudio image dataset."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=18.0)
    parser.add_argument("--soften", type=float, default=1.2)
    return parser.parse_args()


def estimate_background(image: Image.Image) -> np.ndarray:
    arr = np.asarray(image.convert("RGB"), dtype=np.float32)
    border = np.concatenate(
        [
            arr[:8, :, :].reshape(-1, 3),
            arr[-8:, :, :].reshape(-1, 3),
            arr[:, :8, :].reshape(-1, 3),
            arr[:, -8:, :].reshape(-1, 3),
        ],
        axis=0,
    )
    return np.median(border, axis=0)


def make_mask(image: Image.Image, threshold: float, soften: float) -> Image.Image:
    arr = np.asarray(image.convert("RGB"), dtype=np.float32)
    bg = estimate_background(image)
    distance = np.linalg.norm(arr - bg[None, None, :], axis=2)
    mask = (distance > threshold).astype(np.uint8) * 255
    mask_image = Image.fromarray(mask, mode="L")
    if soften > 0:
        mask_image = mask_image.filter(ImageFilter.GaussianBlur(radius=soften))
    return mask_image


def main() -> None:
    args = parse_args()
    meta = json.loads((args.input / "transforms.json").read_text(encoding="utf-8"))
    image_dir = args.output / "images"
    mask_dir = args.output / "masks"
    image_dir.mkdir(parents=True, exist_ok=True)
    mask_dir.mkdir(parents=True, exist_ok=True)

    for frame in meta["frames"]:
        source_path = args.input / frame["file_path"]
        rel_image_path = Path(frame["file_path"])
        dest_image_path = args.output / rel_image_path
        dest_image_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_image_path)

        image = Image.open(source_path).convert("RGB")
        mask_rel = Path("masks") / rel_image_path.name
        mask_path = args.output / mask_rel
        make_mask(image, args.threshold, args.soften).save(mask_path)
        frame["mask_path"] = mask_rel.as_posix()

    for name in ("scene_prompt.txt", "preview_contact_sheet.jpg"):
        source = args.input / name
        if source.exists():
            shutil.copy2(source, args.output / name)

    meta["masking"] = {
        "method": "border_color_distance",
        "threshold": args.threshold,
        "soften": args.soften,
    }
    (args.output / "transforms.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps({"input": str(args.input), "output": str(args.output), "frames": len(meta["frames"])}, indent=2))


if __name__ == "__main__":
    main()

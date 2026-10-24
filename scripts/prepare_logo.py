from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
source = Image.open(ROOT / "assets" / "koreropal-logo.png").convert("RGB")
pixels = np.asarray(source, dtype=float)

# The original artwork is much darker than the paper and grid.
solid = pixels.max(axis=2) < 170
near_artwork = np.asarray(Image.fromarray((solid * 255).astype("uint8")).filter(ImageFilter.MaxFilter(5))) > 0
foreground = np.asarray(source.filter(ImageFilter.MinFilter(5)), dtype=float)
background = np.array([244, 255, 249], dtype=float)
direction = foreground - background
alpha = np.clip(
    np.sum((pixels - background) * direction, axis=2) / np.maximum(np.sum(direction * direction, axis=2), 1),
    0,
    1,
)
alpha[solid] = 1
alpha[~near_artwork] = 0
alpha[alpha < 0.05] = 0

# Remove the pale fringe from the original antialiased edges.
colours = np.clip(
    (pixels - (1 - alpha[..., None]) * background) / np.maximum(alpha[..., None], 0.001),
    0,
    255,
)
colours[solid] = pixels[solid]
rgba = np.dstack([colours, alpha * 255]).astype("uint8")
logo = Image.fromarray(rgba)
bounds = logo.getbbox()
logo = logo.crop((bounds[0] - 16, bounds[1] - 16, bounds[2] + 16, bounds[3] + 16))
logo.thumbnail((700, 700), Image.Resampling.LANCZOS)
logo.save(ROOT / "static" / "logo.png", optimize=True)
print(f"Prepared original artwork: {logo.size}, {logo.mode}")

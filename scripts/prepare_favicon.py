from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
logo = Image.open(ROOT / "static" / "logo.png").convert("RGBA")
logo.thumbnail((464, 464), Image.Resampling.LANCZOS)

# Keep the original logo on a square background for browser and search icons.
favicon = Image.new("RGBA", (512, 512), "#F8F7F2")
position = ((512 - logo.width) // 2, (512 - logo.height) // 2)
favicon.alpha_composite(logo, position)
favicon.convert("RGB").save(ROOT / "static" / "favicon.png", optimize=True)

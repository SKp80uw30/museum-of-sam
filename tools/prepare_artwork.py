"""
Convert Photos/ into web-sized artwork for the hallway frame canvases and
write a manifest the browser can fetch at runtime.

Run from the repo root:

    python3 tools/prepare_artwork.py

Source photos are never modified — this only reads Photos/ (recursively,
including any subfolders dropped in there) and (re)writes
web/artwork/photos/*.jpg + web/artwork/photos-manifest.json. Re-run any
time photos are added or removed there; the manifest is fully regenerated
each run so removed source files stop appearing.

HEIC sources go through macOS's `sips` first (Pillow has no built-in HEIC
decoder) into a temp JPEG, then every image is re-opened with Pillow,
EXIF-orientation-corrected, converted to RGB, downscaled so its longest
edge is MAX_EDGE px, and re-saved as a quality-82 JPEG — small enough to
load quickly onto dozens of frame canvases, large enough not to look soft
on a frame a couple of meters away.
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageOps

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "Photos"
OUT_DIR = REPO_ROOT / "web" / "artwork" / "photos"
MANIFEST_PATH = REPO_ROOT / "web" / "artwork" / "photos-manifest.json"
MAX_EDGE = 1600
JPEG_QUALITY = 82

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic"}


def slugify(stem):
    keep = [c.lower() if c.isalnum() else "-" for c in stem]
    slug = "".join(keep)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "img"


def heic_to_temp_jpeg(src, tmp_dir):
    tmp_path = tmp_dir / (src.stem + "_heic_tmp.jpg")
    subprocess.run(
        ["sips", "-s", "format", "jpeg", str(src), "--out", str(tmp_path)],
        check=True,
        capture_output=True,
    )
    return tmp_path


def convert_one(src, tmp_dir):
    open_path = src
    cleanup = None
    if src.suffix.lower() == ".heic":
        open_path = heic_to_temp_jpeg(src, tmp_dir)
        cleanup = open_path

    try:
        img = Image.open(open_path)
        img = ImageOps.exif_transpose(img)
        if img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
        longest = max(w, h)
        if longest > MAX_EDGE:
            scale = MAX_EDGE / longest
            img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
        return img
    finally:
        if cleanup:
            cleanup.unlink(missing_ok=True)


def main():
    if not SRC_DIR.is_dir():
        print(f"Source directory not found: {SRC_DIR}", file=sys.stderr)
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for existing in OUT_DIR.glob("*.jpg"):
        existing.unlink()

    sources = sorted(
        p for p in SRC_DIR.rglob("*")
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTS
        and not any(part.startswith(".") for part in p.relative_to(SRC_DIR).parts)
    )
    if not sources:
        print(f"No source images found in {SRC_DIR}", file=sys.stderr)
        sys.exit(1)

    used_names = set()
    manifest = []
    failures = []
    for src in sources:
        base_slug = slugify(src.stem)
        slug = base_slug
        n = 2
        while slug in used_names:
            slug = f"{base_slug}-{n}"
            n += 1
        used_names.add(slug)
        out_name = f"{slug}.jpg"
        out_path = OUT_DIR / out_name

        try:
            img = convert_one(src, OUT_DIR)
            img.save(out_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
        except Exception as exc:
            failures.append((src.name, str(exc)))
            continue

        manifest.append(out_name)
        print(f"{src.name} -> {out_name} ({img.width}x{img.height})")

    manifest.sort()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"\nWrote {len(manifest)} images to {OUT_DIR}")
    print(f"Manifest: {MANIFEST_PATH}")
    if failures:
        print(f"\n{len(failures)} failures:", file=sys.stderr)
        for name, err in failures:
            print(f"  {name}: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

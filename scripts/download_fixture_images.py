import json
from pathlib import Path

import requests


BASE_DIR = Path(__file__).resolve().parent.parent

FIXTURE_PATH = BASE_DIR / "products" / "fixtures" / "products.json"

MEDIA_ROOT = BASE_DIR / "media"  # matches your current setup


def download_image(url, filename):
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    dest_path = MEDIA_ROOT / filename

    if dest_path.exists():
        print(f"Already exists, skipping: {filename}")
        return

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except Exception as exc:
        print(f"Failed: {filename} ({url}) -> {exc}")
        return

    with open(dest_path, "wb") as f:
        f.write(resp.content)

    print(f"Downloaded: {filename}")


def main():
    if not FIXTURE_PATH.exists():
        raise SystemExit(f"Fixture not found: {FIXTURE_PATH}")

    with FIXTURE_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        fields = item.get("fields", {})
        url = fields.get("image_url")
        filename = fields.get("image")

        if not url or not filename:
            continue

        download_image(url, filename)

    print("Done downloading images.")


if __name__ == "__main__":
    main()


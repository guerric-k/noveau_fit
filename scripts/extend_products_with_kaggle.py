import json
import random
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
STYLES_CSV = DATA_DIR / "styles.csv"
IMAGES_CSV = DATA_DIR / "images.csv"

FIXTURE_PATH = BASE_DIR / "products" / "fixtures" / "products.json"

# Map Kaggle masterCategory -> your Category PKs
CATEGORY_MAP = {
    "Apparel": 1,          # Activewear
    "Accessories": 11,     # Accessories
    "Footwear": 10,        # Footwear
    "Bags": 12,            # Bags
    "Personal Care": 13,   # Personal Care
    "Sporting Goods": 14,  # Sports Goods
}


def safe_str(val):
    """Return a clean string or '' if value is NaN / None / not string."""
    if isinstance(val, str):
        return val.strip()
    return ""


def build_description(row):
    """
    Build a simple human-looking description from Kaggle columns.
    Handles NaN values safely.
    """
    name = safe_str(row.get("productDisplayName")) or "Fashion item"

    gender = safe_str(row.get("gender"))
    master = safe_str(row.get("masterCategory"))
    sub = safe_str(row.get("subCategory"))
    article = safe_str(row.get("articleType"))
    colour = safe_str(row.get("baseColour"))
    usage = safe_str(row.get("usage"))

    parts = [name.rstrip(".") + "."]

    if gender:
        parts.append(f"Designed for {gender.lower()}.")
    if master:
        parts.append(f"Belongs to our {master.lower()} range.")
    if sub:
        parts.append(f"Subcategory: {sub.lower()}.")
    if article:
        parts.append(f"Style: {article.lower()}.")
    if colour:
        parts.append(f"Base colour: {colour.lower()}.")
    if usage:
        parts.append(f"Ideal for {usage.lower()} use.")

    return " ".join(parts)


def main():
    if not STYLES_CSV.exists() or not IMAGES_CSV.exists():
        raise SystemExit("styles.csv or images.csv not found in data/")

    if not FIXTURE_PATH.exists():
        raise SystemExit("Existing products.json not found.")

    # Load existing fixture
    with FIXTURE_PATH.open("r", encoding="utf-8") as f:
        existing = json.load(f)

    print("Existing fixture entries:", len(existing))

    # Load Kaggle CSVs
    styles = pd.read_csv(STYLES_CSV, on_bad_lines="skip")
    images = pd.read_csv(IMAGES_CSV, on_bad_lines="skip")

    # images.csv: filename like "25947.jpg" -> id 25947
    images["id"] = (
        images["filename"]
        .str.replace(".jpg", "", regex=False)
        .astype("int64")
    )

    # Merge on id
    merged = styles.merge(images, on="id", how="inner")

    # Keep rows that actually have an image link
    merged = merged.dropna(subset=["link"])

    # Replace NaN with '' so string ops are safe
    merged = merged.fillna("")

    # Sample 100 products
    sample = merged.sample(n=100, random_state=42)

    new_items = []
    max_pk = max(item["pk"] for item in existing)
    pk_counter = max_pk + 1

    for _, row in sample.iterrows():
        master_cat = safe_str(row.get("masterCategory"))
        category_pk = CATEGORY_MAP.get(master_cat, 8)  # default: New Arrivals

        sku = f"FP{int(row['id']):06d}"

        # Generate a price if missing or invalid
        price_val = row.get("price", None)
        try:
            price = float(price_val)
        except (TypeError, ValueError):
            price = round(random.uniform(15, 150), 2)

        rating = round(random.uniform(3.5, 5.0), 1)

        item = {
            "pk": pk_counter,
            "model": "products.product",
            "fields": {
                "sku": sku,
                "name": safe_str(
                    row.get("productDisplayName")
                ) or "Fashion product",
                "description": build_description(row),
                "price": price,
                "category": category_pk,
                "rating": rating,
                "image_url": safe_str(row.get("link")),
                "image": safe_str(row.get("filename")),
            },
        }

        new_items.append(item)
        pk_counter += 1

    print("New Kaggle items:", len(new_items))

    combined = existing + new_items

    with FIXTURE_PATH.open("w", encoding="utf-8") as f:
        json.dump(combined, f, indent=4)

    print("Total entries written:", len(combined))
    print(f"Updated fixture: {FIXTURE_PATH}")


if __name__ == "__main__":
    main()

# src/model_training/dietary.py
import pandas as pd

# Map UI checkboxes to expected tag strings in `product_diet_tags`
PREF_TO_TAG = {
    "vegetarian": "vegetarian",
    "gluten_free": "gluten_free",
    "lactose_free": "lactose_free",
    "nut_free": "nut_free",
    "keto": "keto",
    "diabetic_friendly": "diabetic_friendly",
}

def _normalize_tags(cell) -> list:
    """
    Normalize product_diet_tags into a consistent list of lowercase tokens.
    Converts hyphens to underscores for matching.
    Example: "gluten-free" -> "gluten_free"
    """
    if pd.isna(cell):
        return []
    s = str(cell).lower()
    for sep in [";", ",", "|", "/", " "]:
        s = s.replace(sep, " ")
    tokens = [t.strip().replace("-", "_") for t in s.split(" ") if t]
    return tokens

def suggest_items_any(df: pd.DataFrame, prefs: dict, limit: int = 50) -> pd.DataFrame:
    """Return items that match ANY of the selected dietary tags."""
    if df.empty:
        return df

    # Normalize selected tags
    tags = [PREF_TO_TAG[k] for k, v in prefs.items() if k in PREF_TO_TAG and v]
    tags = [t.replace("-", "_") for t in tags]

    if not tags and not prefs.get("allergies"):
        return df.copy().head(limit)

    mask = pd.Series([False] * len(df), index=df.index)

    # Match ANY dietary preference
    if tags and "product_diet_tags" in df.columns:
        tag_lists = df["product_diet_tags"].apply(_normalize_tags)
        for t in tags:
            mask |= tag_lists.apply(lambda lst: t in lst)

    # Allergy exclusion
    allergies = [a.strip().lower() for a in prefs.get("allergies", []) if a]
    if allergies:
        for col in ["Product_Name", "Brand", "Category", "Subcategory"]:
            if col in df.columns:
                mask &= ~df[col].astype(str).str.lower().apply(
                    lambda s: any(a in s for a in allergies)
                )

    out = df.loc[mask] if tags or allergies else df

    # Fallback: if no match found, still return some items
    if out.empty and tags:
        return df.head(limit)

    return out.head(limit)

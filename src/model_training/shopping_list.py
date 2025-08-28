# src/model_training/shopping_list.py
import pandas as pd

def _price(row) -> float:
    try:
        return float(row.get("unit_price_inr", 0) or 0)
    except Exception:
        return 0.0

def add_from_inventory_row(shopping_list: list, row: pd.Series, qty: float, unit: str):
    """Add an inventory item to the shopping list, computing est_price automatically."""
    name = str(row.get("Product_Name", ""))
    brand = str(row.get("Brand", "")) if "Brand" in row else ""
    unit_price = _price(row)
    est = unit_price * float(qty)
    shopping_list.append({
        "name": name,
        "brand": brand,
        "qty": float(qty),
        "unit": unit,
        "unit_price_inr": unit_price,
        "est_price": est,
        "note": ""
    })
    return shopping_list

def as_dataframe(shopping_list: list) -> pd.DataFrame:
    if not shopping_list:
        return pd.DataFrame(columns=["name","brand","qty","unit","unit_price_inr","est_price","note"])
    df = pd.DataFrame(shopping_list)
    # keep columns order
    cols = ["name","brand","qty","unit","unit_price_inr","est_price","note"]
    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA
    return df[cols]

def estimate_total(shopping_list: list) -> float:
    if not shopping_list:
        return 0.0
    try:
        return float(pd.DataFrame(shopping_list)["est_price"].fillna(0).sum())
    except Exception:
        return 0.0

def update_qty(shopping_list: list, index: int, new_qty: float):
    if 0 <= index < len(shopping_list):
        item = shopping_list[index]
        item["qty"] = float(new_qty)
        unit_price = float(item.get("unit_price_inr", 0) or 0)
        item["est_price"] = unit_price * float(new_qty)
        shopping_list[index] = item
    return shopping_list

def remove_item(shopping_list: list, index: int):
    if 0 <= index < len(shopping_list):
        shopping_list.pop(index)
    return shopping_list

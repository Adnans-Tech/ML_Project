# utils.py
import pandas as pd
from datetime import date, timedelta
from typing import Optional

def to_date(s: Optional[str]):
    if pd.isna(s) or s == "":
        return None
    try:
        return pd.to_datetime(s).date()
    except Exception:
        return None

def low_stock(df: pd.DataFrame):
    if df.empty:
        return df.copy()
    df2 = df.copy()
    q = pd.to_numeric(df2.get("quantity_on_hand", 0), errors="coerce").fillna(0)
    r = pd.to_numeric(df2.get("reorder_level", 0), errors="coerce").fillna(0)
    return df2.loc[q < r].copy()

def expiring_soon(df: pd.DataFrame, days: int = 7):
    if df.empty or "expiration_date" not in df.columns:
        return pd.DataFrame(columns=df.columns)
    df2 = df.copy()
    today = date.today()
    df2["_exp"] = df2["expiration_date"].apply(to_date)
    mask = df2["_exp"].notna() & (df2["_exp"] >= today) & (df2["_exp"] <= (today + timedelta(days=days)))
    return df2.loc[mask].drop(columns=["_exp"])

def expired(df: pd.DataFrame):
    if df.empty or "expiration_date" not in df.columns:
        return pd.DataFrame(columns=df.columns)
    df2 = df.copy()
    today = date.today()
    df2["_exp"] = df2["expiration_date"].apply(to_date)
    mask = df2["_exp"].notna() & (df2["_exp"] < today)
    return df2.loc[mask].drop(columns=["_exp"])

def search_inventory(df: pd.DataFrame, text: str):
    if df.empty or not text:
        return df.copy()
    s = text.lower()
    mask = df.get("Product_Name", pd.Series([], dtype=str)).astype(str).str.lower().str.contains(s)
    if "Category" in df.columns:
        mask = mask | df["Category"].astype(str).str.lower().str.contains(s)
    if "Brand" in df.columns:
        mask = mask | df["Brand"].astype(str).str.lower().str.contains(s)
    return df.loc[mask].copy()

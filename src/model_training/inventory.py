import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor


# ---------- Basic inventory ops (no Streamlit here) ----------
def add_product(df: pd.DataFrame, product: Dict[str, Any]) -> pd.DataFrame:
    """Append a product row; create missing columns with NA."""
    df2 = df.copy()
    for c in df2.columns:
        if c not in product:
            product[c] = pd.NA
    return pd.concat([df2, pd.DataFrame([product])], ignore_index=True)


def update_stock(df: pd.DataFrame, product_id: str, delta: float) -> pd.DataFrame:
    df2 = df.copy()
    if "Product_ID" not in df2.columns:
        raise KeyError("Product_ID column missing")
    mask = df2["Product_ID"].astype(str) == str(product_id)
    if not mask.any():
        raise KeyError(f"Product ID {product_id} not found")
    q = pd.to_numeric(df2.loc[mask, "quantity_on_hand"], errors="coerce").fillna(0)
    df2.loc[mask, "quantity_on_hand"] = (q + float(delta)).clip(lower=0)
    return df2


# ---------- Low-stock / expiry helpers (kept here for app imports) ----------
def _to_date(x) -> Optional[date]:
    if pd.isna(x) or x == "":
        return None
    try:
        # accept both date and datetime strings
        d = pd.to_datetime(x)
        return d.date() if isinstance(d, (pd.Timestamp, datetime)) else d
    except Exception:
        return None


def low_stock(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    q = pd.to_numeric(df.get("quantity_on_hand", 0), errors="coerce").fillna(0)
    r = pd.to_numeric(df.get("reorder_level", 0), errors="coerce").fillna(0)
    return df.loc[q < r].copy()


def expiring_soon(df: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    if df.empty or "expiration_date" not in df.columns:
        return pd.DataFrame(columns=df.columns)
    today = date.today()
    df2 = df.copy()
    df2["_exp"] = df2["expiration_date"].apply(_to_date)
    mask = df2["_exp"].notna() & (df2["_exp"] >= today) & (df2["_exp"] <= (today + timedelta(days=days)))
    return df2.loc[mask].drop(columns=["_exp"])


# ---------- Feature engineering ----------
def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a copy with engineered columns:
      - Days_to_Expiry
      - Stock_Value
      - Category_Share
    """
    if df.empty:
        return df.copy()

    out = df.copy()

    # Days_to_Expiry
    today = date.today()
    exp = out.get("expiration_date")
    if exp is not None:
        out["Days_to_Expiry"] = exp.apply(_to_date).apply(
            lambda d: (d - today).days if d is not None else np.nan
        )
    else:
        out["Days_to_Expiry"] = np.nan

    # Stock_Value
    price = pd.to_numeric(out.get("unit_price_inr", 0), errors="coerce").fillna(0)
    qty = pd.to_numeric(out.get("quantity_on_hand", 0), errors="coerce").fillna(0)
    out["Stock_Value"] = price * qty

    # Category_Share (share of stock value within each Category)
    if "Category" in out.columns:
        by_cat = out.groupby("Category")["Stock_Value"].transform("sum").replace(0, np.nan)
        out["Category_Share"] = (out["Stock_Value"] / by_cat).fillna(0.0)
    else:
        out["Category_Share"] = 0.0

    return out


# ---------- Modeling ----------
def train_inventory_model(df_feat: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Simple demo model:
      X -> ['quantity_on_hand', 'Days_to_Expiry', 'Category_Share']
      y -> unit_price_inr (regression)
    Returns metrics for baseline and RandomForest, plus sample predictions.
    """
    if df_feat.empty:
        return None

    # Prepare features/target
    y = pd.to_numeric(df_feat.get("unit_price_inr", np.nan), errors="coerce")
    X = pd.DataFrame({
        "quantity_on_hand": pd.to_numeric(df_feat.get("quantity_on_hand", np.nan), errors="coerce"),
        "Days_to_Expiry": pd.to_numeric(df_feat.get("Days_to_Expiry", np.nan), errors="coerce"),
        "Category_Share": pd.to_numeric(df_feat.get("Category_Share", np.nan), errors="coerce"),
    })

    mask = y.notna() & X.notna().all(axis=1)
    X = X.loc[mask]
    y = y.loc[mask]

    if len(X) < 30:
        # not enough data to split reliably
        return None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=min(0.2, max(0.2, 0.2)), random_state=42
    )

    # --- Baseline: predict mean of y_train ---
    baseline_pred = np.full(shape=y_test.shape, fill_value=float(y_train.mean()))
    baseline_mae = mean_absolute_error(y_test, baseline_pred)
    # robust RMSE (works on any sklearn version)
    try:
        baseline_rmse = mean_squared_error(y_test, baseline_pred, squared=False)
    except TypeError:
        baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_pred))
    baseline_r2 = r2_score(y_test, baseline_pred)

    # --- RandomForest ---
    rf = RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    y_hat = rf.predict(X_test)

    rf_mae = mean_absolute_error(y_test, y_hat)
    try:
        rf_rmse = mean_squared_error(y_test, y_hat, squared=False)
    except TypeError:
        rf_rmse = np.sqrt(mean_squared_error(y_test, y_hat))
    rf_r2 = r2_score(y_test, y_hat)

    pred_samples = pd.DataFrame({
        "quantity_on_hand": X_test["quantity_on_hand"].values,
        "Days_to_Expiry": X_test["Days_to_Expiry"].values,
        "Category_Share": X_test["Category_Share"].values,
        "y_true": y_test.values,
        "y_pred": y_hat,
    }).head(20)

    return {
        "baseline": {"MAE": float(baseline_mae), "RMSE": float(baseline_rmse), "R2": float(baseline_r2)},
        "rf": {"MAE": float(rf_mae), "RMSE": float(rf_rmse), "R2": float(rf_r2)},
        "pred_samples": pred_samples,
    }

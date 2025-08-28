import numpy as np
import pandas as pd

def dtransformation(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    if "unit_price_inr" in df.columns:
        df["log_price"] = np.log1p(pd.to_numeric(df["unit_price_inr"], errors="coerce"))

    if "purchase_date" in df.columns:
        df["purchase_date"] = pd.to_datetime(df["purchase_date"], errors="coerce")
        df["month"] = df["purchase_date"].dt.month
        df["weekday"] = df["purchase_date"].dt.weekday

    if {"quantity_on_hand", "reorder_level"}.issubset(df.columns):
        df["low_stock_flag"] = (
            pd.to_numeric(df["quantity_on_hand"], errors="coerce") <
            pd.to_numeric(df["reorder_level"], errors="coerce")
        ).astype(int)

    return df


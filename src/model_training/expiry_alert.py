import pandas as pd

def items_expiring_within(df, days=7):
    if "expiration_date" not in df.columns:
        return pd.DataFrame()
    df = df.copy()
    df["expiration_date"] = pd.to_datetime(df["expiration_date"], errors="coerce")
    return df[df["expiration_date"] <= pd.Timestamp.today() + pd.Timedelta(days=days)]

def check_item_expiry(df, product_name):
    if "expiration_date" not in df.columns or "Product_Name" not in df.columns:
        return None
    df = df.copy()
    df["expiration_date"] = pd.to_datetime(df["expiration_date"], errors="coerce")
    row = df[df["Product_Name"].astype(str) == str(product_name)]
    if row.empty:
        return None
    return {
        "Product_Name": row.iloc[0].get("Product_Name", ""),
        "Expiration_Date": row.iloc[0].get("expiration_date", None),
        "Quantity_On_Hand": row.iloc[0].get("quantity_on_hand", None)
    }

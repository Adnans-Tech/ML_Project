import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

def train_model(df: pd.DataFrame):
    if df.empty or "unit_price_inr" not in df.columns:
        return None
    df = df.copy()
    X = df.select_dtypes(include=[np.number]).fillna(0)
    y = pd.to_numeric(df["unit_price_inr"], errors="coerce").fillna(0)
    if len(X) < 10:
        return None
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)
    return {"rmse": rmse, "r2": r2, "n_samples": len(df)}

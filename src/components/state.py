# state.py
import pandas as pd
from pathlib import Path

# Your dataset schema (exact column names)
_EXPECTED_COLS = [
    "User_ID","user_diet","preferred_cuisines","monthly_budget","purchase_date",
    "Product_ID","Product_Name","Brand","Category","Subcategory","unit","unit_price_inr",
    "quantity_purchased","discount_applied","total_spent","storage_type","expiration_date",
    "days_to_expiry","quantity_on_hand","reorder_level","reorder_quantity","payment_method",
    "store_type","calories","protein_g","fat_g","carbs_g","fiber_g","sugar_g","sodium_mg",
    "product_diet_tags","recipe_id","recipe_name","recipe_cuisine","recipe_cook_time",
    "ingredient_product_ids","ingredient_qtys","recipe_instructions","user_monthly_spend","category_spend_share"
]

def init_session_state(st, artifacts_dir="artifacts"):
    # make expected cols accessible to app
    st.session_state._expected_inventory_cols = _EXPECTED_COLS

    # Inventory DataFrame
    if "inventory" not in st.session_state:
        artifacts = Path(artifacts_dir)
        data_path = artifacts / "data.csv"
        if data_path.exists():
            try:
                df = pd.read_csv(data_path)
                # Ensure expected columns exist. If not, create as NA.
                for c in _EXPECTED_COLS:
                    if c not in df.columns:
                        df[c] = pd.NA
                st.session_state.inventory = df[_EXPECTED_COLS].copy()
            except Exception:
                st.session_state.inventory = pd.DataFrame(columns=_EXPECTED_COLS)
        else:
            st.session_state.inventory = pd.DataFrame(columns=_EXPECTED_COLS)

    # Dietary preferences
    if "diet_prefs" not in st.session_state:
        st.session_state.diet_prefs = {
            "vegetarian": False,
            "vegan": False,
            "gluten_free": False,
            "lactose_free": False,
            "nut_free": False,
            "keto": False,
            "diabetic_friendly": False,
            "allergies": []
        }

    # Shopping list (in-memory)
    if "shopping_list" not in st.session_state:
        st.session_state.shopping_list = []  # list of dicts

    # Budget
    if "budget" not in st.session_state:
        st.session_state.budget = {
            "monthly_budget": 0.0,
            "planned_spend": 0.0,
            "spent_this_month": 0.0
        }


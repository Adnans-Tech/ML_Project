# app.py
import os
import pandas as pd
import streamlit as st

# state and utils
from src.components.state import init_session_state
from src.utils import search_inventory, low_stock, expiring_soon

# feature modules
from src.model_training import inventory as inv_mod  # keep for low_stock/expiry helpers if you have them there
from src.model_training import shopping_list as sl_mod
from src.model_training import dietary as diet_mod
from src.model_training import budget as budget_mod

st.set_page_config(page_title="Smart Grocery Assistant", page_icon="🛒", layout="wide")
init_session_state(st)

# --- Load dataset (no upload) ---
data_path = os.path.join("artifacts", "data.csv")
if os.path.exists(data_path):
    df = pd.read_csv(data_path)
    expected = st.session_state._expected_inventory_cols
    for c in expected:
        if c not in df.columns:
            df[c] = pd.NA
    st.session_state.inventory = df[expected].copy()
else:
    st.error("❌ Dataset not found. Please place it in artifacts/data.csv")
    st.stop()

# --- Sidebar Navigation ---
with st.sidebar:
    st.markdown("### ⚙️ Navigation")
    menu = st.radio("Go to", [
        "Dashboard", "Inventory", "Dietary Preferences",
        "Shopping List", "Budget", "Expiry Alerts"
    ])

st.title("🛒 Smart Grocery Assistant")

# ---------------- Dashboard ----------------
if menu == "Dashboard":
    st.header("📊 Dashboard")
    df = st.session_state.inventory

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🛍️ Unique products", int(df["Product_Name"].nunique() if "Product_Name" in df.columns else len(df)))
    c2.metric("⚠️ Low stock items", int(len(low_stock(df))))
    c3.metric("⏳ Expiring soon (7d)", int(len(expiring_soon(df, days=7))))
    total_inv_value = (pd.to_numeric(df.get("unit_price_inr", 0), errors="coerce").fillna(0) *
                       pd.to_numeric(df.get("quantity_on_hand", 0), errors="coerce").fillna(0)).sum()
    c4.metric("💰 Est. inventory value (₹)", f"{total_inv_value:,.0f}")

    st.subheader("📦 Inventory preview")
    preview_cols = [c for c in ["Product_Name", "Brand", "unit_price_inr", "expiration_date"] if c in df.columns]
    if preview_cols:
        st.dataframe(df[preview_cols].head(50), use_container_width=True)
    else:
        st.info("Preview columns not found in dataset.")

# ---------------- Inventory ----------------
elif menu == "Inventory":
    st.header("📦 Inventory — Search & Add to List")

    df = st.session_state.inventory
    q = st.text_input("Search by product name, category or brand")
    view = search_inventory(df, q) if q else df

    # lightweight view table
    cols = [c for c in ["Product_Name", "Brand", "Category", "unit", "unit_price_inr", "expiration_date",
                        "quantity_on_hand", "reorder_level"] if c in view.columns]
    st.dataframe(view[cols].reset_index(drop=True), use_container_width=True, height=300)

    # selection + add to list
    st.subheader("➕ Add a product to shopping list")
    if not view.empty:
        # build unique labels
        view = view.reset_index(drop=True)
        labels = view.apply(
            lambda r: f"{r.get('Product_Name','')} — {r.get('Brand','') or 'No brand'}  (₹{r.get('unit_price_inr',0)})",
            axis=1
        ).tolist()
        idx = st.selectbox("Choose a product", options=list(range(len(labels))), format_func=lambda i: labels[i])
        default_unit = str(view.loc[idx, "unit"]) if "unit" in view.columns else "pcs"
        qty = st.number_input("Quantity", min_value=1.0, step=1.0, value=1.0)
        unit = st.text_input("Unit", value=default_unit)

        if st.button("Add to Shopping List"):
            row = view.loc[idx]
            st.session_state.shopping_list = sl_mod.add_from_inventory_row(
                st.session_state.shopping_list, row=row, qty=qty, unit=unit
            )
            st.success(f"Added {row.get('Product_Name','(item)')} (qty {qty:g} {unit}) to shopping list.")
    else:
        st.info("No products to show. Try a different search term.")

# ---------------- Dietary Preferences ----------------
elif menu == "Dietary Preferences":
    st.header("🥗 Dietary Preferences")

    prefs = st.session_state.diet_prefs
    c1, c2, c3 = st.columns(3)
    prefs["vegetarian"] = c1.checkbox("Vegetarian", value=prefs.get("vegetarian", False))
    prefs["vegan"] = c1.checkbox("Vegan", value=prefs.get("vegan", False))
    prefs["gluten_free"] = c2.checkbox("Gluten-free", value=prefs.get("gluten_free", False))
    prefs["lactose_free"] = c2.checkbox("Lactose-free", value=prefs.get("lactose_free", False))
    prefs["nut_free"] = c3.checkbox("Nut-free", value=prefs.get("nut_free", False))
    prefs["keto"] = c3.checkbox("Keto", value=prefs.get("keto", False))
    prefs["diabetic_friendly"] = c3.checkbox("Diabetic-friendly", value=prefs.get("diabetic_friendly", False))

    allergy = st.text_input("Add allergy (press Enter)")
    if allergy:
        if allergy.lower() not in [a.lower() for a in prefs["allergies"]]:
            prefs["allergies"].append(allergy)
            st.success(f"✅ Added allergy: {allergy}")

    st.write("**Allergies:**", ", ".join(prefs["allergies"]) or "None")

    st.subheader("🍴 Suggestions (ANY of selected tags)")
    suggestions = diet_mod.suggest_items_any(st.session_state.inventory, prefs, limit=100)

    disp_cols = [c for c in ["Product_Name", "Brand", "Category", "unit_price_inr", "calories", "product_diet_tags"]
                 if c in suggestions.columns]
    if not suggestions.empty:
        st.dataframe(suggestions[disp_cols].head(50), use_container_width=True)

        # allow adding from suggestions
        suggestions = suggestions.reset_index(drop=True)
        labels = suggestions.apply(
            lambda r: f"{r.get('Product_Name','')} — {r.get('Brand','') or 'No brand'}  (₹{r.get('unit_price_inr',0)})",
            axis=1
        ).tolist()
        idx = st.selectbox("Add a suggested product", options=list(range(len(labels))), format_func=lambda i: labels[i])
        qty = st.number_input("Quantity (suggestions)", min_value=1.0, step=1.0, value=1.0, key="diet_qty")
        unit = suggestions.loc[idx, "unit"] if "unit" in suggestions.columns else "pcs"
        if st.button("Add suggestion to Shopping List"):
            row = suggestions.loc[idx]
            st.session_state.shopping_list = sl_mod.add_from_inventory_row(
                st.session_state.shopping_list, row=row, qty=qty, unit=unit
            )
            st.success(f"Added {row.get('Product_Name','(item)')} from suggestions.")
    else:
        st.info("No suggestions found for the selected preferences.")

# ---------------- Shopping List ----------------
elif menu == "Shopping List":
    st.header("🛒 Shopping List")

    if st.session_state.shopping_list:
        # editable quantities per item
        df_sl = sl_mod.as_dataframe(st.session_state.shopping_list)
        st.dataframe(df_sl, use_container_width=True)

        # simple per-item quantity update
        st.subheader("Update item quantity / remove")
        names = [f"{i}. {item['name']} — {item.get('brand','')}" for i, item in enumerate(st.session_state.shopping_list)]
        if names:
            i_sel = st.selectbox("Select item", options=list(range(len(names))), format_func=lambda i: names[i])
            new_qty = st.number_input("New quantity", min_value=0.0, step=1.0, value=float(st.session_state.shopping_list[i_sel]["qty"]))
            colu = st.columns(2)
            if colu[0].button("Update quantity"):
                st.session_state.shopping_list = sl_mod.update_qty(st.session_state.shopping_list, i_sel, new_qty)
                st.success("Quantity updated.")
            if colu[1].button("Remove item"):
                st.session_state.shopping_list = sl_mod.remove_item(st.session_state.shopping_list, i_sel)
                st.success("Item removed.")

        # totals
        st.metric("Estimated Total (₹)", sl_mod.estimate_total(st.session_state.shopping_list))

        if st.button("Clear shopping list"):
            st.session_state.shopping_list.clear()
            st.success("Shopping list cleared.")
    else:
        st.info("Shopping list is empty. Add items from Inventory or Dietary tabs.")

# ---------------- Budget ----------------
elif menu == "Budget":
    st.header("💰 Budget Manager")

    # auto-compute planned spend from shopping list (read-only)
    planned = sl_mod.estimate_total(st.session_state.shopping_list)

    b = st.session_state.budget
    col = st.columns(3)
    b["monthly_budget"] = col[0].number_input("Monthly budget (₹)", min_value=0.0, step=100.0, value=float(b.get("monthly_budget", 0.0)))
    b["spent_this_month"] = col[1].number_input("Spent this month (₹)", min_value=0.0, step=50.0, value=float(b.get("spent_this_month", 0.0)))

    st.metric("Planned spend (₹)", planned)
    status = budget_mod.check_budget_status({
        "monthly_budget": b["monthly_budget"],
        "spent_this_month": b["spent_this_month"],
        "planned_spend": planned,
    })
    st.metric("Projected remaining (₹)", status["remaining"])
    if status["remaining"] < 0:
        st.error("⚠️ Over budget!")

# ---------------- Expiry Alerts ----------------
elif menu == "Expiry Alerts":
    st.header("⏰ Expiry Alerts")
    df = st.session_state.inventory
    if "Product_Name" not in df.columns:
        st.info("Dataset missing Product_Name.")
    else:
        product_names = df["Product_Name"].astype(str).tolist()
        sel = st.selectbox("Choose product", ["-- choose --"] + product_names)
        if sel and sel != "-- choose --":
            row = df[df["Product_Name"].astype(str) == sel].iloc[0]
            st.write("**Product:**", row.get("Product_Name", ""))
            st.write("**Brand:**", row.get("Brand", ""))
            st.write("**Expiry date:**", row.get("expiration_date", "N/A"))
            st.write("**Quantity on hand:**", row.get("quantity_on_hand", "N/A"))
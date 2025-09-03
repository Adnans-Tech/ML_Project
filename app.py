# app.py
import os
import pandas as pd
import streamlit as st
import plotly.express as px

# state and utils
from src.components.state import init_session_state
from src.utils import search_inventory, low_stock, expiring_soon

# feature modules
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

    def human_format(num):
        for unit in ['', 'K', 'M', 'B']:
            if abs(num) < 1000.0:
                return f"{num:3.1f}{unit}"
            num /= 1000.0
        return f"{num:.1f}T"

    # --- Metrics row ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🛍️ Unique products", int(df["Product_Name"].nunique() if "Product_Name" in df.columns else len(df)))
    c2.metric("⚠️ Low stock items", int(len(low_stock(df))))
    c3.metric("⏳ Expiring soon (7d)", int(len(expiring_soon(df, days=7))))
    total_inv_value = (
        pd.to_numeric(df.get("unit_price_inr", 0), errors="coerce").fillna(0) *
        pd.to_numeric(df.get("quantity_on_hand", 0), errors="coerce").fillna(0)
    ).sum()
    c4.metric("💰 Est. inventory value", f"₹{human_format(total_inv_value)}")

    # --- Visualizations ---
    st.subheader("📦 Inventory Overview")
    col1, col2 = st.columns(2)

    with col1:
        if "Category" in df.columns and not df["Category"].isna().all():
            cat_summary = df.groupby("Category")["quantity_on_hand"].sum().reset_index()
            fig1 = px.pie(cat_summary, names="Category", values="quantity_on_hand",
                          hole=0.4, title="Category-wise Inventory Share")
            fig1.update_traces(textinfo="percent+label", pull=[0.05] * len(cat_summary))
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No category data available for visualization.")

    with col2:
        if "purchase_date" in df.columns and not df["purchase_date"].isna().all():
            df2 = df.copy()
            df2["purchase_date"] = pd.to_datetime(df2["purchase_date"], errors="coerce")
            time_summary = df2.groupby(df2["purchase_date"].dt.to_period("M"))["quantity_purchased"].sum().reset_index()
            time_summary["purchase_date"] = time_summary["purchase_date"].astype(str)
            fig2 = px.line(time_summary, x="purchase_date", y="quantity_purchased",
                           markers=True, title="Purchases Over Time")
            fig2.update_layout(xaxis_title="Month", yaxis_title="Quantity Purchased")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No purchase date data available for visualization.")

# ---------------- Inventory ----------------
elif menu == "Inventory":
    st.header("📦 Inventory — Search & Add to List")
    df = st.session_state.inventory
    q = st.text_input("Search by product name, category or brand")
    view = search_inventory(df, q) if q else df

    st.subheader("🌐 Inventory Overview")
    if not view.empty and "Category" in view.columns:
        fig = px.treemap(view, path=["Category", "Brand", "Product_Name"],
                         values="quantity_on_hand", color="unit_price_inr",
                         color_continuous_scale="RdBu",
                         title="Category → Brand → Product (by Quantity & Price)")
        st.plotly_chart(fig, use_container_width=True, height=600)
    else:
        st.info("No inventory data available for visualization. Try adding some products.")

    # selection + add to list
    st.subheader("➕ Add a product to shopping list")
    if not view.empty:
        view = view.reset_index(drop=True)
        labels = view.apply(lambda r: f"{r.get('Product_Name','')} — {r.get('Brand','') or 'No brand'} (₹{r.get('unit_price_inr',0)})", axis=1).tolist()
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
    prefs["gluten_free"] = c1.checkbox("Gluten-free", value=prefs.get("gluten_free", False))
    prefs["lactose_free"] = c2.checkbox("Lactose-free", value=prefs.get("lactose_free", False))
    prefs["nut_free"] = c2.checkbox("Nut-free", value=prefs.get("nut_free", False))
    prefs["keto"] = c3.checkbox("Keto", value=prefs.get("keto", False))
    prefs["diabetic_friendly"] = c3.checkbox("Diabetic-friendly", value=prefs.get("diabetic_friendly", False))

    allergy = st.text_input("Add allergy (press Enter)")
    if allergy:
        if allergy.lower() not in [a.lower() for a in prefs["allergies"]]:
            prefs["allergies"].append(allergy)
            st.success(f"✅ Added allergy: {allergy}")
            st.rerun()

    st.write("**Allergies:**", ", ".join(prefs["allergies"]) or "None")

    st.subheader("🍴 Suggestions (based on preferences)")
    all_suggestions = diet_mod.suggest_items_any(st.session_state.inventory, prefs)

    if 'display_limit' not in st.session_state:
        st.session_state.display_limit = 10

    if not all_suggestions.empty:
        suggestions_to_show = all_suggestions.head(st.session_state.display_limit)
        st.metric("Matching Products", len(all_suggestions))

        st.subheader("📋 Suggested Products")
        for _, row in suggestions_to_show.iterrows():
            product = row.get("Product_Name", "Unknown")
            brand = row.get("Brand", "No brand")
            price = row.get("unit_price_inr", "N/A")
            st.markdown(f"✅ **{product}** <br> *{brand} — ₹{price}*", unsafe_allow_html=True)

        if len(all_suggestions) > st.session_state.display_limit:
            if st.button("Show more suggestions"):
                st.session_state.display_limit += 10
                st.rerun()
    else:
        st.info("No suggestions found for the selected preferences.")

    st.subheader("➕ Add a product to shopping list")
    suggestion_list = all_suggestions.apply(
        lambda r: f"{r.get('Product_Name','Unknown')} — {r.get('Brand','No brand')} (₹{r.get('unit_price_inr',0)})", axis=1
    ).tolist()

    if suggestion_list:
        idx = st.selectbox("Choose a product", options=list(range(len(suggestion_list))), format_func=lambda i: suggestion_list[i])
        qty = st.number_input("Quantity", min_value=1.0, step=1.0, value=1.0, key="diet_qty")
        unit = all_suggestions.loc[idx, "unit"] if "unit" in all_suggestions.columns else "pcs"

        if st.button("Add suggestion to Shopping List"):
            row = all_suggestions.loc[idx]
            st.session_state.shopping_list = sl_mod.add_from_inventory_row(
                st.session_state.shopping_list, row=row, qty=qty, unit=unit
            )
            st.success(f"Added {row.get('Product_Name','(item)')} to shopping list.")

# ---------------- Shopping List ----------------
elif menu == "Shopping List":
    st.header("📝 My Shopping List")

    # Always convert to DataFrame for display
    sl_df = sl_mod.as_dataframe(st.session_state.shopping_list)

    if not sl_df.empty:
        st.dataframe(sl_df, use_container_width=True)

        total_price = sl_mod.estimate_total(st.session_state.shopping_list)
        st.metric("Total Estimated Cost", f"₹{total_price:,.2f}")
    else:
        st.info("Your shopping list is empty. Add items from the 'Inventory' or 'Dietary Preferences' pages.")

# ---------------- Budget ----------------
elif menu == "Budget":
    st.header("💰 Budget Manager")
    planned = sl_mod.estimate_total(st.session_state.shopping_list)
    b = st.session_state.budget
    col1, col2, col3 = st.columns(3)
    b["monthly_budget"] = col1.number_input("Monthly budget (₹)", min_value=0.0, step=100.0, value=float(b.get("monthly_budget", 0.0)))
    b["spent_this_month"] = col2.number_input("Spent this month (₹)", min_value=0.0, step=50.0, value=float(b.get("spent_this_month", 0.0)))
    col3.metric("Planned spend (₹)", planned)

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
    expiring_items = expiring_soon(df, days=30)

    if not expiring_items.empty:
        st.warning("⚠️ The following items are expiring soon:")
        st.dataframe(expiring_items)
    else:
        st.info("No items are expiring in the next 30 days.")

    st.subheader("Individual Product Expiry Check")
    if "Product_Name" not in df.columns:
        st.info("Dataset missing Product_Name.")
    else:
        product_names = df["Product_Name"].astype(str).tolist()
        sel = st.selectbox("Choose product", ["-- choose --"] + product_names)
        if sel and sel != "-- choose --":
            row = df[df["Product_Name"].astype(str) == sel].iloc[0]
            st.write("**Product:**", row.get("Product_Name", ""))
            st.write("**Brand:**", row.get("Brand", ""))
            if "expiration_date" in row:
                st.write("**Expiry date:**", row["expiration_date"])
            else:
                st.write("**Expiry date:**", "N/A")
            st.write("**Quantity on hand:**", row.get("quantity_on_hand", "N/A"))

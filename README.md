# 🛒 Smart Grocery Assistant

The **Smart Grocery Assistant** is a comprehensive Python application built with **Streamlit** that helps users manage their household grocery inventory, plan shopping, track dietary needs, and stay within a defined budget.  
It integrates smart alerts and machine learning models to provide an **intuitive and efficient grocery management experience**.

---

## 🚀 Features

### 📦 Inventory Management
- Search and manage stocked items.
- View key metrics like **unique products**, **low-stock items**, and **inventory value**.
- Add products directly to your shopping list from the inventory.

### 🛒 Shopping List
- Dynamic shopping list with **real-time estimated pricing** (based on qty, brand, and inventory data).
- Prevents manual entry of product prices — uses the trained ML model for estimation.
- Automatically integrates with **Budget Tracker**.

### 🥗 Dietary Preferences
- Users can define dietary preferences (vegan, gluten-free, lactose-free, nut-free, etc.).
- Suggests multiple matching products based on **dataset dietary tags**.
- Allows adding suggested items directly to the shopping list.

### 💰 Budget Tracker
- Track **monthly budget**, **expenses**, and **planned spend**.
- Automatic calculation of planned spend from shopping list.
- Alerts for **over-budget** scenarios.
- Includes a **RandomForestRegressor** model for budget forecasting.

### ⏰ Expiry Alerts
- Alerts for items expiring within the next 7 days.
- Helps reduce food waste.

---

## 🛠️ Tech Stack

- **Python 3.12+**
- **Streamlit** (frontend framework)
- **Pandas, NumPy** (data handling)
- **scikit-learn** (ML models: RandomForestRegressor, evaluation metrics)
- **Joblib** (model persistence)



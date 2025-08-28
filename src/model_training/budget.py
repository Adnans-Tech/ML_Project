# src/model_training/budget.py
def check_budget_status(b: dict) -> dict:
    """
    remaining = monthly_budget − (spent_this_month + planned_spend)
    """
    monthly = float(b.get("monthly_budget", 0) or 0)
    spent = float(b.get("spent_this_month", 0) or 0)
    planned = float(b.get("planned_spend", 0) or 0)
    remaining = monthly - (spent + planned)
    return {
        "remaining": float(remaining),
        "is_over": remaining < 0
    }

#!/usr/bin/env python

import sys
from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"


EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}


financial_transactions_storage: list[dict[str, Any]] = []


def is_leap_year(year: int) -> bool:
    """
    Для заданного года определяет: високосный (True) или невисокосный (False).

    :param int year: Проверяемый год
    :return: Значение високосности.
    :rtype: bool
    """
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    """
    Парсит дату формата DD-MM-YYYY из строки.

    :param str maybe_dt: Проверяемая строка
    :return: typle формата (день, месяц, год) или None, если дата неправильная.
    :rtype: tuple[int, int, int] | None
    """
    parts = maybe_dt.split("-")
    if len(parts) != 3:
        return None
    if len(parts[0]) != 2 or len(parts[1]) != 2 or len(parts[2]) != 4:
        return None
    if not (parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit()):
        return None
        
    d = int(parts[0])
    m = int(parts[1])
    y = int(parts[2])
    
    if y < 1 or m < 1 or m > 12 or d < 1:
        return None
        
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if is_leap_year(y):
        days_in_month[1] = 29
        
    if d > days_in_month[m - 1]:
        return None
        
    return (d, m, y)


def parse_amount(val: str) -> float | None:
    val = val.replace(",", ".")
    
    if val.startswith("-"):
        body = val[1:]
        sign = -1.0
    else:
        body = val
        sign = 1.0
        
    if not body:
        return None
        
    parts = body.split(".")
    if len(parts) > 2:
        return None
        
    if len(parts) == 1:
        if not parts[0].isdigit():
            return None
    else:
        if parts[0] != "" and not parts[0].isdigit():
            return None
        if parts[1] != "" and not parts[1].isdigit():
            return None
        if parts[0] == "" and parts[1] == "":
            return None

    return sign * float(val)


def income_handler(amount: float, income_date: str) -> str:
    financial_transactions_storage.append({"amount": amount, "date": income_date})
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    financial_transactions_storage.append({"category": category_name, "amount": amount, "date": income_date})
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    lines = []
    for common, targets in EXPENSE_CATEGORIES.items():
        lines.append(f"{common}: {', '.join(targets)}")
    return "\n".join(lines)


def stats_handler(report_date: str) -> str:
    rd = extract_date(report_date)
    if not rd:
        return INCORRECT_DATE_MSG
    ry, rm, rd_day = rd[2], rd[1], rd[0]
    
    total_capital = 0.0
    month_income = 0.0
    month_expenses = 0.0
    
    category_expenses: dict[str, float] = {}
    
    for tx in financial_transactions_storage:
        tx_d = extract_date(tx["date"])
        if not tx_d:
            continue
        t_y, t_m, t_d = tx_d[2], tx_d[1], tx_d[0]
        
        if (t_y, t_m, t_d) <= (ry, rm, rd_day):
            amt = tx["amount"]
            if "category" in tx:
                total_capital -= amt
                if t_y == ry and t_m == rm:
                    month_expenses += amt
                    target_cat = tx["category"].split("::")[1]
                    category_expenses[target_cat] = category_expenses.get(target_cat, 0.0) + amt
            else:
                total_capital += amt
                if t_y == ry and t_m == rm:
                    month_income += amt

    diff = month_income - month_expenses
    if diff < 0:
        profit_loss_str = f"loss amounted to {-diff:.2f}"
    else:
        profit_loss_str = f"profit amounted to {diff:.2f}"

    lines = []
    lines.append(f"Your statistics as of {report_date}:")
    lines.append(f"Total capital: {total_capital:.2f} rubles")
    lines.append(f"This month, the {profit_loss_str} rubles.")
    lines.append(f"Income: {month_income:.2f} rubles")
    lines.append(f"Expenses: {month_expenses:.2f} rubles")
    lines.append("")
    lines.append("Details (category: amount):")
    
    if category_expenses:
        sorted_cats = sorted(category_expenses.keys())
        for i, cat in enumerate(sorted_cats, 1):
            amt = category_expenses[cat]
            if amt.is_integer():
                amt_str = str(int(amt))
            else:
                amt_str = str(amt)
            lines.append(f"{i}. {cat}: {amt_str}")

    return "\n".join(lines)


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if not parts:
            continue
            
        cmd = parts[0]
        if cmd == "income":
            if len(parts) != 3:
                print(UNKNOWN_COMMAND_MSG)
                continue
            amt_str, date_str = parts[1], parts[2]
            
            amt_val = parse_amount(amt_str)
            dt_val = extract_date(date_str)
            
            if amt_val is None or amt_val <= 0:
                print(NONPOSITIVE_VALUE_MSG)
                continue
            if dt_val is None:
                print(INCORRECT_DATE_MSG)
                continue
                
            print(income_handler(amt_val, date_str))
            
        elif cmd == "cost":
            if len(parts) == 2 and parts[1] == "categories":
                print(cost_categories_handler())
                continue
                
            if len(parts) != 4:
                print(UNKNOWN_COMMAND_MSG)
                continue
                
            cat_str, amt_str, date_str = parts[1], parts[2], parts[3]
            
            cat_valid = False
            c_parts = cat_str.split("::")
            if len(c_parts) == 2:
                common, target = c_parts
                if common in EXPENSE_CATEGORIES and target in EXPENSE_CATEGORIES[common]:
                    cat_valid = True
                    
            amt_val = parse_amount(amt_str)
            dt_val = extract_date(date_str)
            
            if not cat_valid:
                print(f"{NOT_EXISTS_CATEGORY}\n{cost_categories_handler()}")
                continue
                
            if amt_val is None or amt_val <= 0:
                print(NONPOSITIVE_VALUE_MSG)
                continue
                
            if dt_val is None:
                print(INCORRECT_DATE_MSG)
                continue
                
            print(cost_handler(cat_str, amt_val, date_str))
            
        elif cmd == "stats":
            if len(parts) != 2:
                print(UNKNOWN_COMMAND_MSG)
                continue
            date_str = parts[1]
            dt_val = extract_date(date_str)
            if dt_val is None:
                print(INCORRECT_DATE_MSG)
                continue
            print(stats_handler(date_str))
            
        else:
            print(UNKNOWN_COMMAND_MSG)


if __name__ == "__main__":
    main()
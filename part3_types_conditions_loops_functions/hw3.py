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

DATE_PARTS_COUNT = 3
DAY_LEN = 2
MONTH_LEN = 2
YEAR_LEN = 4
MONTHS_IN_YEAR = 12
MAX_DECIMAL_PARTS = 2
CMD_INCOME_LEN = 3
CMD_COST_LEN = 4
CMD_STATS_LEN = 2
CMD_CATEGORIES_LEN = 2
CAT_PARTS_LEN = 2
LEAP_YEAR_MULTIPLE = 4
CENTURY_MULTIPLE = 100
QUAD_CENTURY_MULTIPLE = 400


def is_leap_year(year: int) -> bool:
    """
    Для заданного года определяет: високосный (True) или невисокосный (False).

    :param int year: Проверяемый год
    :return: Значение високосности.
    :rtype: bool
    """
    if year % QUAD_CENTURY_MULTIPLE == 0:
        return True
    if year % CENTURY_MULTIPLE == 0:
        return False
    return year % LEAP_YEAR_MULTIPLE == 0


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    """
    Парсит дату формата DD-MM-YYYY из строки.

    :param str maybe_dt: Проверяемая строка
    :return: typle формата (день, месяц, год) или None, если дата неправильная.
    :rtype: tuple[int, int, int] | None
    """
    parts = maybe_dt.split("-")
    if len(parts) != DATE_PARTS_COUNT:
        return None

    if (
        len(parts[0]) != DAY_LEN
        or len(parts[1]) != MONTH_LEN
        or len(parts[2]) != YEAR_LEN
    ):
        return None

    if not (parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit()):
        return None

    d = int(parts[0])
    m = int(parts[1])
    y = int(parts[2])

    if y < 1 or m < 1 or m > MONTHS_IN_YEAR or d < 1:
        return None

    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if is_leap_year(y):
        days_in_month[1] = 29

    if d > days_in_month[m - 1]:
        return None

    return (d, m, y)


def parse_amount(val: str) -> float | None:
    val = val.replace(",", ".")
    body = val[1:] if val.startswith(("-", "+")) else val
    parts = body.split(".")

    is_valid = len(parts) <= MAX_DECIMAL_PARTS and bool(body)
    if is_valid:
        for p in parts:
            if p and not p.isdigit():
                is_valid = False

    if is_valid and not any(p.isdigit() for p in parts):
        is_valid = False

    return float(val) if is_valid else None


def income_handler(amount: float, income_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    dt_val = extract_date(income_date)
    if dt_val is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append({"amount": amount, "date": dt_val})
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    cat_valid = False
    c_parts = category_name.split("::")

    if len(c_parts) == CAT_PARTS_LEN:
        common, target = c_parts[0], c_parts[1]
        if common in EXPENSE_CATEGORIES and target in EXPENSE_CATEGORIES[common]:
            cat_valid = True

    if not cat_valid:
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY

    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    dt_val = extract_date(income_date)
    if dt_val is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append(
        {
            "category": category_name,
            "amount": amount,
            "date": dt_val,
        }
    )
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    lines: list[str] = []
    for common, targets in EXPENSE_CATEGORIES.items():
        lines.extend(f"{common}::{target}" for target in targets)
    return "\n".join(lines)


def process_tx_for_stats(
    tx: dict[str, Any],
    report_date_tuple: tuple[int, int, int],
    stats: dict[str, float],
    category_expenses: dict[str, float],
) -> None:
    if not tx:
        return

    t_d, t_m, t_y = tx["date"]
    rd_day, rm, ry = report_date_tuple

    if (t_y, t_m, t_d) > (ry, rm, rd_day):
        return

    amt = float(tx["amount"])
    is_cost = "category" in tx
    is_current_month = t_y == ry and t_m == rm

    if is_cost:
        stats["total_capital"] -= amt
    else:
        stats["total_capital"] += amt

    if is_current_month:
        if is_cost:
            stats["month_expenses"] += amt
            target_cat = tx["category"].split("::")[1]
            cat_exp = category_expenses.get(target_cat, 0.0)
            category_expenses[target_cat] = cat_exp + amt
        else:
            stats["month_income"] += amt


def stats_handler(report_date: str) -> str:
    rd = extract_date(report_date)
    if not rd:
        return INCORRECT_DATE_MSG
    stats = {"total_capital": 0.0, "month_income": 0.0, "month_expenses": 0.0}
    category_expenses: dict[str, float] = {}
    for tx in financial_transactions_storage:
        process_tx_for_stats(tx, rd, stats, category_expenses)
    diff = stats["month_income"] - stats["month_expenses"]
    profit_loss_str = (
        f"loss amounted to {-diff:.2f}"
        if diff < 0
        else f"profit amounted to {diff:.2f}"
    )
    lines = [
        f"Your statistics as of {report_date}:",
        f"Total capital: {stats['total_capital']:.2f} rubles",
        f"This month, the {profit_loss_str} rubles.",
        f"Income: {stats['month_income']:.2f} rubles",
        f"Expenses: {stats['month_expenses']:.2f} rubles",
        "",
        "Details (category: amount):",
    ]
    if category_expenses:
        for i, cat in enumerate(sorted(category_expenses.keys()), 1):
            amt = category_expenses[cat]
            amt_str = str(int(amt)) if amt.is_integer() else str(amt)
            lines.append(f"{i}. {cat}: {amt_str}")
    return "\n".join(lines)


def handle_income_command(parts: list[str]) -> None:
    if len(parts) != CMD_INCOME_LEN:
        print(UNKNOWN_COMMAND_MSG)
        return
    amt_str, date_str = parts[1], parts[2]
    amt_val = parse_amount(amt_str)
    if amt_val is None:
        amt_val = -1.0
    res = income_handler(amt_val, date_str)
    print(res)


def handle_cost_command(parts: list[str]) -> None:
    if len(parts) == CMD_CATEGORIES_LEN and parts[1] == "categories":
        print(cost_categories_handler())
        return
    if len(parts) != CMD_COST_LEN:
        print(UNKNOWN_COMMAND_MSG)
        return
    cat_str, amt_str, date_str = parts[1], parts[2], parts[3]
    amt_val = parse_amount(amt_str)
    if amt_val is None:
        amt_val = -1.0
    res = cost_handler(cat_str, amt_val, date_str)
    print(res)
    if res == NOT_EXISTS_CATEGORY:
        print(cost_categories_handler())


def handle_stats_command(parts: list[str]) -> None:
    if len(parts) != CMD_STATS_LEN:
        print(UNKNOWN_COMMAND_MSG)
        return
    print(stats_handler(parts[1]))


def main() -> None:
    for line in sys.stdin:
        clean_line = line.strip()
        if not clean_line:
            continue
        parts = clean_line.split()
        if not parts:
            continue
        cmd = parts[0]
        if cmd == "income":
            handle_income_command(parts)
        elif cmd == "cost":
            handle_cost_command(parts)
        elif cmd == "stats":
            handle_stats_command(parts)
        else:
            print(UNKNOWN_COMMAND_MSG)


if __name__ == "__main__":
    main()
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

FLOAT_ZERO = float(0)
INVALID_AMOUNT = -1.0

DAYS_IN_MONTH = (
    31,
    28,
    31,
    30,
    31,
    30,
    31,
    31,
    30,
    31,
    30,
    31,
)


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


def _is_invalid_date(day: int, month: int, year: int) -> bool:
    if year < 1 or month < 1 or month > MONTHS_IN_YEAR or day < 1:
        return True
    max_days = list(DAYS_IN_MONTH)
    if is_leap_year(year):
        max_days[1] = 29
    return day > max_days[month - 1]


def _is_valid_date_format(parts: list[str]) -> bool:
    if len(parts[0]) != DAY_LEN:
        return False
    if len(parts[1]) != MONTH_LEN:
        return False
    return len(parts[2]) == YEAR_LEN


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

    if not _is_valid_date_format(parts):
        return None

    if not "".join(parts).isdigit():
        return None

    d_val = int(parts[0])
    m_val = int(parts[1])
    y_val = int(parts[2])

    if _is_invalid_date(d_val, m_val, y_val):
        return None

    return d_val, m_val, y_val


def parse_amount(val: str) -> float | None:
    val_clean = val.replace(",", ".")
    body = val_clean[1:] if val_clean.startswith(("-", "+")) else val_clean
    parts = body.split(".")

    if not body or len(parts) > MAX_DECIMAL_PARTS:
        return None

    for part in parts:
        if part and not part.isdigit():
            return None

    if not any(part_num.isdigit() for part_num in parts):
        return None

    return float(val_clean)


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
    rep_date: tuple[int, int, int],
    stats: dict[str, float],
    category_expenses: dict[str, float],
) -> None:
    if not tx:
        return

    tx_d, tx_m, tx_y = tx["date"]
    rep_d, rep_m, rep_y = rep_date

    tx_dt = (tx_y, tx_m, tx_d)
    rep_dt = (rep_y, rep_m, rep_d)

    if tx_dt > rep_dt:
        return

    amt = float(tx["amount"])
    is_cost = "category" in tx

    if is_cost:
        stats["total_capital"] -= amt
    else:
        stats["total_capital"] += amt

    if tx_y == rep_y and tx_m == rep_m:
        if is_cost:
            stats["month_expenses"] += amt
            target_cat = tx["category"].split("::")[1]
            cat_exp = category_expenses.get(target_cat, FLOAT_ZERO)
            category_expenses[target_cat] = cat_exp + amt
        else:
            stats["month_income"] += amt


def _build_stats_report(
    rep_date: str,
    stats: dict[str, float],
    cat_exp: dict[str, float],
) -> str:
    diff = stats["month_income"] - stats["month_expenses"]
    diff_abs = abs(diff)
    outcome = "loss" if diff < FLOAT_ZERO else "profit"
    profit_loss_str = f"{outcome} amounted to {diff_abs:.2f}"

    lines = [
        f"Your statistics as of {rep_date}:",
        f"Total capital: {stats['total_capital']:.2f} rubles",
        f"This month, the {profit_loss_str} rubles.",
        f"Income: {stats['month_income']:.2f} rubles",
        f"Expenses: {stats['month_expenses']:.2f} rubles",
        "",
        "Details (category: amount):",
    ]

    if cat_exp:
        for idx, cat_name in enumerate(sorted(cat_exp.keys()), 1):
            amt = cat_exp[cat_name]
            amt_str = str(int(amt)) if amt.is_integer() else str(amt)
            lines.append(f"{idx}. {cat_name}: {amt_str}")

    return "\n".join(lines)


def stats_handler(report_date: str) -> str:
    rd = extract_date(report_date)
    if not rd:
        return INCORRECT_DATE_MSG

    stats = {
        "total_capital": FLOAT_ZERO,
        "month_income": FLOAT_ZERO,
        "month_expenses": FLOAT_ZERO,
    }
    category_expenses: dict[str, float] = {}

    for tx in financial_transactions_storage:
        process_tx_for_stats(tx, rd, stats, category_expenses)

    return _build_stats_report(report_date, stats, category_expenses)


def handle_income_command(parts: list[str]) -> None:
    if len(parts) != CMD_INCOME_LEN:
        print(UNKNOWN_COMMAND_MSG)
        return

    amt_str = parts[1]
    date_str = parts[2]
    amt_val = parse_amount(amt_str)

    if amt_val is None:
        amt_val = INVALID_AMOUNT

    res = income_handler(amt_val, date_str)
    print(res)


def handle_cost_command(parts: list[str]) -> None:
    if len(parts) == CMD_CATEGORIES_LEN and parts[1] == "categories":
        print(cost_categories_handler())
        return

    if len(parts) != CMD_COST_LEN:
        print(UNKNOWN_COMMAND_MSG)
        return

    cat_str = parts[1]
    amt_str = parts[2]
    date_str = parts[3]
    amt_val = parse_amount(amt_str)

    if amt_val is None:
        amt_val = INVALID_AMOUNT

    res = cost_handler(cat_str, amt_val, date_str)
    print(res)
    if res == NOT_EXISTS_CATEGORY:
        print(cost_categories_handler())


def handle_stats_command(parts: list[str]) -> None:
    if len(parts) != CMD_STATS_LEN:
        print(UNKNOWN_COMMAND_MSG)
        return
    print(stats_handler(parts[1]))


def process_command(parts: list[str]) -> None:
    cmd = parts[0]
    if cmd == "income":
        handle_income_command(parts)
    elif cmd == "cost":
        handle_cost_command(parts)
    elif cmd == "stats":
        handle_stats_command(parts)
    else:
        print(UNKNOWN_COMMAND_MSG)


def main() -> None:
    for line in sys.stdin:
        clean_line = line.strip()
        if not clean_line:
            continue

        parts = clean_line.split()
        if parts:
            process_command(parts)


if __name__ == "__main__":
    main()

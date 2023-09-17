import pandas as pd

from io import BytesIO
from fastapi import HTTPException, UploadFile, status
from typing import List
from datetime import date

from sqlalchemy import and_, extract
from sqlalchemy.orm import Session

from src.database.models import Credit, Payment, User, Plan, Diction
from src.schemas import (
    ClosedCreditResponse,
    OpenCreditResponse,
    MonthResponse,
    YearResponse,
)


async def user_cr_info(user_id: int, db: Session) -> List[User] | None:
    no_credits = (
        db.query(Credit)
        .filter(and_(Credit.user_id == user_id, Credit.actual_return_date != None))
        .all()
    )
    is_credits = (
        db.query(Credit)
        .filter(and_(Credit.user_id == user_id, Credit.actual_return_date == None))
        .all()
    )

    all_info = []
    if no_credits:
        for credit in no_credits:
            sum_payments = (
                db.query(Payment).filter(Payment.credit_id == credit.id).all()
            )
            user_info = ClosedCreditResponse(
                issuance_date=credit.issuance_date,  # Дата видачі кредиту
                exist_credit=True,  # Булеве значення чи кредит закритий (true - закритий, false - відкритий)
                return_date=credit.actual_return_date,  # Дата повернення кредиту
                body=credit.body,  # Сума видачі
                percent=credit.percent,  # Нараховані відсотки
                sum=sum(
                    [payment.sum for payment in sum_payments]
                ),  # Сума платежів за кредитом
            )
            all_info.append(user_info)
    elif is_credits:
        for credit in is_credits:
            bod_payments = (
                db.query(Payment)
                .filter(and_(Payment.credit_id == credit.id, Payment.type_id == 1))
                .all()
            )
            perc_payments = (
                db.query(Payment)
                .filter(and_(Payment.credit_id == credit.id, Payment.type_id == 2))
                .all()
            )
            user_info = OpenCreditResponse(
                issuance_date=credit.issuance_date,  # Дата видачі кредиту
                exist_credit=False,  # Булеве значення чи кредит закритий (true - закритий, false - відкритий)
                return_date=credit.return_date,  # Крайня дата повернення кредиту
                overdue_days=(
                    date.today() - credit.return_date
                ).days,  # Кількість днів прострочення кредиту
                body=credit.body,  # Сума видач
                percent=credit.percent,  # Нараховані відсотки
                body_payments=sum(
                    [payment.sum for payment in bod_payments]
                ),  # Сума платежів по тілу
                percent_payments=sum(
                    [payment.sum for payment in perc_payments]
                ),  # Сума платежів по відсоткам
            )
            all_info.append(user_info)
    else:

        return None

    return all_info


def add_to_db(df, db) -> str:
    for ind in df.index:
        diction = (
            db.query(Diction).filter(Diction.name == df["category_name"][ind]).first()
        )
        plan_to_db = Plan(
            period=df["period"][ind], sum=df["sum"][ind], category_id=diction.id
        )
        db.add(plan_to_db)
    db.commit()
    db.refresh(plan_to_db)

    return "Plans successfully added to DB"


async def load_plans(file: UploadFile, db: Session) -> Plan | None:
    df = pd.read_excel(BytesIO(file.file.read()), header=None)
    df.columns = df.iloc[0]
    df = df[1:]

    message = []
    for ind in df.index:
        period = (df["period"][ind]).date()
        diction = (
            db.query(Diction).filter(Diction.name == df["category_name"][ind]).first()
        )
        exist_plan = (
            db.query(Plan)
            .filter(and_(Plan.period == period, Plan.category_id == diction.id))
            .first()
        )

        if exist_plan:
            message.append(
                f"Plan with period: {period} and category_name: '{df['category_name'][ind]}' already exist"
            )
        if period != period.replace(day=1):
            message.append(
                f"Plan period: {period} don't starts with first day of month"
            )
        if df["sum"][ind] == 0:
            message.append(f"Plan with period: {period} missed Sum ")
        continue

    if message:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"{'. '.join(message)}"
        )

    return add_to_db(df, db)


def sum_category(date_on, category_name, db) -> float:
    date_start = date_on.replace(day=1)
    date_list = [day for day in pd.date_range(date_start, date_on)]
    mn_credits = db.query(Credit).filter(Credit.issuance_date.in_(date_list)).all()
    mn_payments = db.query(Payment).filter(Payment.payment_date.in_(date_list)).all()
    if category_name == "видача":

        return sum([credit.body for credit in mn_credits])
    if category_name == "збір":

        return sum([payment.sum for payment in mn_payments])


def percent(numerator, denominator) -> float:

    return numerator * 100 / (denominator + 0.0001)


async def check_mn_plans(date_on: date, db: Session) -> List[Plan] | None:
    mn_plans = (
        db.query(Plan)
        .filter(Plan.period.between(date_on.replace(day=1), date_on))
        .all()
    )
    plans_list = []
    for plan in mn_plans:
        category = db.query(Diction).filter(Diction.id == plan.category_id).first()
        sum_by_category = sum_category(date_on, category.name, db)
        category_plan = MonthResponse(
            period=plan.period,  # Місяць плану
            category=category.name,  # Категорія плану
            sum=plan.sum,  # Сума з плану
            sum_by_category=sum_by_category,  # Сума виданих кредитів або сума платежів
            perc_plan_impl=percent(sum_by_category, plan.sum),  #% виконання плану
        )
        plans_list.append(category_plan)

    return plans_list


async def check_yr_plans(year_on: str, db: Session) -> List[Plan] | None:
    all_yr_credits = db.query(Credit).filter(
        extract("year", Credit.issuance_date) == year_on
    )

    all_yr_payments = db.query(Payment).filter(
        extract("year", Payment.payment_date) == year_on
    )

    all_yr_plans = db.query(Plan).filter(extract("year", Plan.period) == year_on)

    sum_credits_year = sum([credit.body for credit in all_yr_credits])
    sum_payments_year = sum([payment.sum for payment in all_yr_payments])

    plans_list = []
    for mnth in range(1, 12):

        mn_plans_credits = all_yr_plans.filter(
            and_(extract("month", Plan.period) == mnth, Plan.category_id == 3)
        ).all()
        mn_credits = all_yr_credits.filter(
            extract("month", Credit.issuance_date) == mnth
        ).all()
        mn_plans_payments = all_yr_plans.filter(
            and_(extract("month", Plan.period) == mnth, Plan.category_id == 4)
        ).all()
        mn_payments = all_yr_payments.filter(
            extract("month", Payment.payment_date) == mnth
        ).all()

        sum_by_plan_credits = sum([plan.sum for plan in mn_plans_credits])
        sum_credits_month = sum([credit.body for credit in mn_credits])
        sum_by_plan_payments = sum([plan.sum for plan in mn_plans_payments])
        sum_payments_month = sum([payment.sum for payment in mn_payments])

        year_plan = YearResponse(
            month_year=f"{mnth:02}.{year_on}",  # Місяць та рік
            number_credits=len(mn_credits),  # Кількість видач за місяць
            sum_by_plan_credits=sum_by_plan_credits,  # Сума з плану по видачам на місяць
            sum_credits_month=sum_credits_month,  # Сума видач за місяць
            perc_credits=percent(
                sum_credits_month, sum_by_plan_credits
            ),  #% виконання плану по видачам
            number_payments=len(mn_payments),  # Кількість платежів за місяць
            sum_by_plan_payments=sum_by_plan_payments,  # Сума з плану по збору за місяць
            sum_payments_month=sum_payments_month,  # Сума платежів за місяць
            perc_payments=percent(
                sum_payments_month, sum_by_plan_payments
            ),  #% виконання плану по збору
            perc_cred_month_year=percent(
                sum_credits_month, sum_credits_year
            ),  #% суми видач за місяць від суми видач за рік
            perc_pay_month_year=percent(
                sum_payments_month, sum_payments_year
            ),  #% суми платежів за місяць від суми платежів за рік
        )
        plans_list.append(year_plan)

    return plans_list

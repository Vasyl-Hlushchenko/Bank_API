import pandas as pd

from io import BytesIO
from fastapi import HTTPException, UploadFile, status
from typing import List
from datetime import date, datetime

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.database.models import Credit, Payment, User, Plan, Diction
from src.schemas import ClosedCreditResponse, OpenCreditResponse, MonthResponse, YearResponse


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


def add_to_db(df, db):
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
                f"Plan with period: {period} and category_name: '{df['category_name'][ind]}'. Already exist"
            )
        if period != period.replace(day=1):
            message.append(f"Plan period: {period}. Not start with first day of month")
        if df["sum"][ind] == 0:
            message.append(f"Plan with period: {period}. Sum is missed")
        continue

    if message:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{message}")

    return add_to_db(df, db)


def sum_category(date_on, category_name, db):
    date_start = date_on.replace(day=1)
    date_list = [day for day in pd.date_range(date_start, date_on)]
    mn_credits = db.query(Credit).filter(Credit.issuance_date.in_(date_list)).all()
    mn_payments = db.query(Payment).filter(Payment.payment_date.in_(date_list)).all()
    if category_name == "видача":

        return sum([credit.body for credit in mn_credits])
    if category_name == "збір":

        return sum([payment.sum for payment in mn_payments])


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
            perc_plan_impl=sum_by_category
            * 100
            / (plan.sum + 0.001),  #% виконання плану
        )
        plans_list.append(category_plan)

    return plans_list


async def check_yr_plans(year_on: str, db: Session) -> List[Plan] | None:
    date_yr_start = datetime.strptime(f"{year_on}-01-01", "%Y-%m-%d").date()
    date_yr_fin = datetime.strptime(f"{year_on}-12-31", "%Y-%m-%d").date()

    all_yr_credits = (
        db.query(Credit)
        .filter(Credit.issuance_date.between(date_yr_start, date_yr_fin))
        .all()
    )
    all_yr_payments = (
        db.query(Payment)
        .filter(Payment.payment_date.between(date_yr_start, date_yr_fin))
        .all()
    )
    sum_credits_year = sum([credit.body for credit in all_yr_credits])
    sum_payments_year = sum([payment.sum for payment in all_yr_payments])

    fin_dates = [
        day for day in pd.date_range(start=date_yr_start, periods=12, freq="M")
    ]

    plans_list = []
    for mnth in range(1, 13):
        date_m_start = fin_dates[mnth - 1].replace(day=1)
        date_m_fin = fin_dates[mnth - 1]

        yr_plans_credits = (
            db.query(Plan)
            .filter(
                and_(Plan.period.between(date_m_start, date_m_fin)),
                Plan.category_id == 3,
            )
            .all()
        )
        yr_plans_payments = (
            db.query(Plan)
            .filter(
                and_(
                    Plan.period.between(date_m_start, date_m_fin), Plan.category_id == 4
                )
            )
            .all()
        )
        yr_credits = (
            db.query(Credit)
            .filter(Credit.issuance_date.between(date_m_start, date_m_fin))
            .all()
        )
        yr_payments = (
            db.query(Payment)
            .filter(Payment.payment_date.between(date_m_start, date_m_fin))
            .all()
        )

        sum_by_plan_credits = sum([plan.sum for plan in yr_plans_credits])
        sum_credits_month = sum([credit.body for credit in yr_credits])
        sum_by_plan_payments = sum([plan.sum for plan in yr_plans_payments])
        sum_payments_month = sum([payment.sum for payment in yr_payments])

        year_plan = YearResponse(
            month_year=f"{mnth:02}.{year_on}",  # Місяць та рік
            number_credits=len(yr_credits),  # Кількість видач за місяць
            sum_by_plan_credits=sum_by_plan_credits,  # Сума з плану по видачам на місяць
            sum_credits_month=sum_credits_month,  # Сума видач за місяць
            perc_credits=sum_credits_month
            * 100
            / (sum_by_plan_credits + 0.001),  #% виконання плану по видачам
            number_payments=len(yr_payments),  # Кількість платежів за місяць
            sum_by_plan_payments=sum_by_plan_payments,  # Сума з плану по збору за місяць
            sum_payments_month=sum_payments_month,  # Сума платежів за місяць
            perc_payments=sum_payments_month
            * 100
            / (sum_by_plan_payments + 0.001),  #% виконання плану по збору
            perc_cred_month_year=sum_credits_month
            * 100
            / (sum_credits_year + 0.001),  #% суми видач за місяць від суми видач за рік
            perc_pay_month_year=sum_payments_month
            * 100
            / (
                sum_payments_year + 0.001
            ),  #% суми платежів за місяць від суми платежів за рік
        )
        plans_list.append(year_plan)

    return plans_list

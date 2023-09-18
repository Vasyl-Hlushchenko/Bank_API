from datetime import date
from pydantic import BaseModel


class ClosedCreditResponse(BaseModel):
    issuance_date: date
    exist_credit: bool
    return_date: date
    body: float
    percent: float
    sum: float


class OpenCreditResponse(BaseModel):
    issuance_date: date
    exist_credit: bool
    return_date: date
    overdue_days: int
    body: float
    percent: float
    body_payments: float
    percent_payments: float


class MonthResponse(BaseModel):
    month: str
    category: str
    sum: int
    sum_by_category: float
    perc_plan_impl: float


class YearResponse(BaseModel):
    month_year: str
    number_credits: int
    sum_by_plan_credits: float
    sum_credits_month: float
    perc_credits: float
    number_payments: int
    sum_by_plan_payments: float
    sum_payments_month: float
    perc_payments: float
    perc_cred_month_year: float
    perc_pay_month_year: float

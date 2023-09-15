from typing import Optional

from pydantic import BaseModel


class ClosedCreditModel(BaseModel):
    issuance_date: Optional[str]
    exist_credit: Optional[bool]
    return_date: Optional[str]
    body: Optional[float]
    percent: Optional[float]
    sum: Optional[float]

class OpenCreditModel(BaseModel):
    issuance_date: Optional[str]
    exist_credit: Optional[bool]
    return_date: Optional[str]
    overdue_days: Optional[int]
    body: Optional[float]
    percent: Optional[float]
    body_payments: Optional[float]
    percent_payments: Optional[float]

class MonthResponse(BaseModel):
    period: Optional[str]
    category: Optional[str]
    sum: Optional[int]
    sum_by_category: Optional[int | float]
    perc_plan_impl: Optional[int | float]

class YearResponse(BaseModel):
    month_year: Optional[str]
    number_credits: Optional[int]
    sum_by_plan_credits: Optional[int | float]
    sum_credits_month: Optional[int | float]
    perc_credits: Optional[int | float]
    number_payments: Optional[int]
    sum_by_plan_payments: Optional[int | float]
    sum_payments_month: Optional[int | float]
    perc_payments: Optional[int | float]
    perc_cred_month_year: Optional[int | float]
    perc_pay_month_year: Optional[int | float]

from datetime import date
from fastapi import FastAPI, Depends, File, HTTPException, UploadFile, status, Query
from sqlalchemy.orm import Session


from src.repository.users import (
    user_cr_info,
    load_plans,
    check_mn_plans,
    check_yr_plans,
)
from src.database.db import get_db

app = FastAPI()


@app.get("/api/healthchecker")
def root():

    return {"message": "Welcome to Bank_API!"}


@app.get("/user_credits/{user_id}", status_code=status.HTTP_200_OK)
async def user_credits_info(user_id: int, db: Session = Depends(get_db)):

    res = await user_cr_info(user_id, db)
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return res


@app.post("/plans_insert", status_code=status.HTTP_200_OK)
async def download_plans(file: UploadFile = File(None), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Upload xlsx or xls file"
        )

    return await load_plans(file, db)


@app.get("/plans_performance", status_code=status.HTTP_200_OK)
async def check_month_plans(
    date_on: date = Query(None, description="Date in format 2022-02-22"),
    db: Session = Depends(get_db),
):
    plans = await check_mn_plans(date_on, db)
    if not plans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plans not found"
        )

    return plans


@app.get("/year_performance", status_code=status.HTTP_200_OK)
async def check_year_plans(
    year_on: str = Query(None, description="Year in format 2022"),
    db: Session = Depends(get_db),
):
    plans = await check_yr_plans(year_on, db)
    if not plans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plans not found"
        )

    return plans

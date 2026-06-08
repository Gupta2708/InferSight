from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dashboard import SummaryOut
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=SummaryOut)
def summary(db: Session = Depends(get_db)):
    return DashboardService(db).summary()


@router.get("/latency")
def latency(db: Session = Depends(get_db)):
    return DashboardService(db).time_series("latency")


@router.get("/errors")
def errors(db: Session = Depends(get_db)):
    return DashboardService(db).time_series("errors")


@router.get("/tokens")
def tokens(db: Session = Depends(get_db)):
    return DashboardService(db).time_series("tokens")


@router.get("/cost")
def cost(db: Session = Depends(get_db)):
    return DashboardService(db).time_series("cost")


@router.get("/providers")
def providers(db: Session = Depends(get_db)):
    return DashboardService(db).providers()


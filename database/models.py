from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    product_id = Column(Integer)
    manager_id = Column(Integer)
    amount = Column(Float)
    product_name = Column(String)
    manager_name = Column(String)
    profit = Column(Float)
    margin = Column(Float)
    region = Column(String)

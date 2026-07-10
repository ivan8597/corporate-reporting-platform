from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Float


class Base(DeclarativeBase):
    pass



class Sale(Base):

    __tablename__ = "sales"


    id = Column(
        Integer,
        primary_key=True
    )


    product_name = Column(
        String
    )


    manager_name = Column(
        String
    )


    amount = Column(
        Float
    )


    profit = Column(
        Float
    )


    margin = Column(
        Float
    )

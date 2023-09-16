from sqlalchemy import Column, Integer, Float, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    login = Column(Text)
    registration_date = Column(Date)


class Diction(Base):
    __tablename__ = "dictionary"

    id = Column(Integer, primary_key=True)
    name = Column(Text)


class Credit(Base):
    __tablename__ = "credits"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    issuance_date = Column(Date)
    return_date = Column(Date)
    actual_return_date = Column(Date, default=None, nullable=True)
    body = Column(Float)
    percent = Column(Float)

    user = relationship("User", backref="credits")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    sum = Column(Float)
    payment_date = Column(Date)
    credit_id = Column(Integer, ForeignKey("credits.id", ondelete="CASCADE"))
    type_id = Column(Integer, ForeignKey("dictionary.id"))

    credit = relationship("Credit", backref="payments")
    type = relationship("Diction", backref="payments")


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True)
    period = Column(Date, default=None)
    sum = Column(Float)
    category_id = Column(Integer, ForeignKey("dictionary.id", ondelete="CASCADE"))

    category = relationship("Diction", backref="plans")

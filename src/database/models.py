from sqlalchemy import Column, Integer, String, func, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    login = Column(Text)
    registration_date = Column(Text)


class Dictionary(Base):
    __tablename__ = "dictionary"

    id = Column(Integer, primary_key=True)
    name = Column(Text)


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    sum = Column(Float)
    payment_date = Column(Text)
    credit_id = Column(Integer, ForeignKey('credits.id', ondelete='CASCADE'))
    type_id = Column(Integer, ForeignKey('dictionary.id', ondelete='CASCADE'))

    # credit = relationship('Credit', backref="payments")
    # dictionary = relationship('Dictionary', backref="payments")


class Credit(Base):
    __tablename__ = 'credits'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    issuance_date = Column(Text)
    return_date = Column(Text)
    actual_return_date = Column(Text)
    body = Column(Float)
    percent = Column(Float)

    # user = relationship('User', backref="credits")


class Plan(Base):
    __tablename__ = 'plans'
    
    id = Column(Integer, primary_key=True)
    period = Column(Text)
    sum = Column(Float)
    category_id = Column(Integer, ForeignKey('dictionary.id', ondelete='CASCADE'))
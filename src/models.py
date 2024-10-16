from sqlalchemy import Column, Integer, Float, String, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Float, default=0)
    account_type = Column(String, default="user")
    referrer_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    referrer = relationship("User", remote_side=[id], backref="referrals")
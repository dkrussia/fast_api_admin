from datetime import datetime

from sqlalchemy.orm import relationship

from core.database import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Enum
import enum


class BaseModel(Base):
    id = Column(Integer, primary_key=True, index=True)


class Object(BaseModel):
    __tablename__ = "objects"

    name = Column(String)

class TypeEventLevel(enum.Enum):
    ERROR = 1
    INFO = 2

class TypeEventStatus(enum.Enum):
    NEW = 1
    PENDING = 2
    CLOSE = 2

class Events(BaseModel):
    __tablename__ = "events"

    object_id = Column(ForeignKey(Object.id))
    date = Column(DateTime)
    message = Column(DateTime)
    level = Column(Enum(TypeEventLevel))
    status = Column(Enum(TypeEventStatus))




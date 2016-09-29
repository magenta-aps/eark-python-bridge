# -*- coding: utf-8 -*-
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text

from database import Base


class LockedFile(Base):
    __tablename__ = 'lockedfile'
    id = Column(Integer, primary_key=True)
    path = Column(Text, nullable=False)
    is_locked = Column(Boolean, nullable=False, default=False)

    def __init__(self, path, is_locked):
        self.path = path
        self.is_locked = is_locked

    def __repr__(self):
        return '<LockedFile #%r>' % self.id

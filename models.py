# -*- coding: utf-8 -*-
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text

from database import Base


class LockedFile(Base):
    __tablename__ = 'lockedfile'
    id = Column(Integer, primary_key=True)
    path = Column(Text, nullable=False)

    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return '<LockedFile #%r>' % self.id

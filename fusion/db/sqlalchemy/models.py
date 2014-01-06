import sqlalchemy

from sqlalchemy.ext.declarative import declarative_base
from fusion.openstack.common.db.sqlalchemy import session
from fusion.openstack.common.db.sqlalchemy import models
from fusion.openstack.common import uuidutils

from sqlalchemy import Column, Integer, String


BASE = declarative_base()
get_session = session.get_session



class Stack(BASE, models.ModelBase):
    __tablename__ = 'stacks'
    id = sqlalchemy.Column(sqlalchemy.String(36), primary_key=True,
                           default=uuidutils.generate_uuid)
    tenant = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    stack_id = sqlalchemy.Column(sqlalchemy.String(36), nullable=False)
    supported = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)

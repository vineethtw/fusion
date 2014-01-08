from fusion.db.sqlalchemy import models
from fusion.openstack.common.db.sqlalchemy import session as db_session

get_engine = db_session.get_engine
get_session = db_session.get_session


def stack_create(values):
    stack_ref = models.Stack()
    stack_ref.update(values)
    stack_ref.save(get_session())
    return stack_ref


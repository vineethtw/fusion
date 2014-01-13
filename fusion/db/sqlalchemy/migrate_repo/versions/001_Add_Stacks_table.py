from sqlalchemy import *
from migrate import *

meta = MetaData()

stacks = Table(
    'stacks', meta,
    Column('id', String(36), primary_key=True),
    Column('tenant', String(255)),
    Column('stack_id', String(36)),
    Column('supported', Boolean)
)

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    stacks.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    stacks.drop()
"""create initial schema

Revision ID: d04f2ff5939b
Revises:
Create Date: 2018-09-26 16:38:10.912454

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy_utils import UUIDType, JSONType

# revision identifiers, used by Alembic.
revision = 'd04f2ff5939b'
down_revision = None
branch_labels = None
depends_on = None

# always create constraints using standard naming conventions
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = sa.MetaData(naming_convention=naming_convention)


def upgrade():
    op.create_table('record_type', metadata,
                    sa.Column('id', UUIDType, primary_key=True),
                    sa.Column('name', sa.String, nullable=True),
                    sa.Column('schema', JSONType, nullable=False),
                    sa.Column('category_id', sa.Integer, nullable=False))

    op.create_table('user', metadata,
                    sa.Column('id', UUIDType, primary_key=True),
                    sa.Column('username', sa.String, nullable=False, unique=True),
                    sa.Column('password', sa.String, nullable=False),
                    sa.Column('type_id', sa.Integer, nullable=False, default=1),
                    sa.Column('created_at', sa.DateTime, nullable=False,
                              default=func.now()),
                    sa.Column('updated_at', sa.DateTime, nullable=False,
                              default=func.now()),
                    sa.Column('payload', JSONType, nullable=False))

    op.create_table('record', metadata,
                    sa.Column('id', UUIDType, primary_key=True),
                    sa.Column('created_at', sa.DateTime, nullable=False,
                              default=func.now()),
                    sa.Column('updated_at', sa.DateTime, nullable=False,
                              default=func.now()),
                    sa.Column('user_id', UUIDType, sa.ForeignKey('user.id'),
                              nullable=True),
                    sa.Column('created_user_id', sa.String, nullable=True),
                    sa.Column('event_id', UUIDType, sa.ForeignKey('event.id'),
                              nullable=True),
                    sa.Column('parent_record_id', UUIDType, nullable=True),
                    sa.Column('type_id', sa.Integer, nullable=False, default=0),
                    sa.Column('validated_user_id', UUIDType, nullable=True),
                    sa.Column('validated_at', sa.DateTime, nullable=True),
                    sa.Column('payload', JSONType, nullable=False))

    op.create_table('event', metadata,
                    sa.Column('id', UUIDType, primary_key=True),
                    sa.Column('organization_id', sa.Integer, primary_key=True),
                    sa.Column('name', sa.String, nullable=False),
                    sa.Column('description', sa.String, nullable=False),
                    sa.Column('event_at', sa.DateTime, nullable=False),
                    sa.Column('created_at', sa.DateTime, nullable=False,
                              default=func.now()),
                    sa.Column('updated_at', sa.DateTime, nullable=False,
                              default=func.now()),
                    sa.Column('user_id', UUIDType, sa.ForeignKey('user.id'),
                              nullable=True),
                    sa.Column('address', sa.String, nullable=True),
                    sa.Column('postal_code', sa.String, nullable=True),
                    sa.Column('longitude', sa.Numeric, nullable=True),
                    sa.Column('latitude', sa.Numeric, nullable=True),
                    sa.Column('payload', JSONType, nullable=False))

    op.create_table('user_event_link', metadata,
                    sa.Column('user_id', UUIDType, sa.ForeignKey('user.id'),
                              primary_key=True),
                    sa.Column('event_id', UUIDType, sa.ForeignKey('event.id'),
                              primary_key=True),
                    sa.Column('created_at', sa.DateTime, nullable=False,
                              default=func.now()),
                    sa.Column('updated_at', sa.DateTime, nullable=False,
                              default=func.now()),
                    sa.Column('payload', JSONType, nullable=False))


def downgrade():
    op.drop_table('user_event_link')
    op.drop_table('record')
    op.drop_table('user')
    op.drop_table('event')
    op.drop_table('record_type')

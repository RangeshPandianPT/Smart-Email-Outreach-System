from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2a7c2a8a0e4'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    with op.batch_alter_table('leads', schema=None) as batch_op:
        batch_op.add_column(sa.Column('campaign_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_leads_campaign_id', 'campaigns', ['campaign_id'], ['id'])

def downgrade():
    with op.batch_alter_table('leads', schema=None) as batch_op:
        batch_op.drop_constraint('fk_leads_campaign_id', type_='foreignkey')
        batch_op.drop_column('campaign_id')
    op.drop_table('campaigns')

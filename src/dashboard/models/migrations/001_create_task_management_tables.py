"""
數據庫遷移腳本
創建任務管理和Sprint管理相關表

Revision ID: 001
Revises:
Create Date: 2025-10-29 12:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """升級數據庫結構"""

    # 創建任務表
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(20), nullable=False, comment='任務唯一ID'),
        sa.Column('title', sa.String(200), nullable=False, comment='任務標題'),
        sa.Column('description', sa.Text(), comment='任務描述'),
        sa.Column(
            'status',
            postgresql.ENUM(
                '待開始', '進行中', '待驗收', '已完成', '已阻塞',
                name='taskstatus',
                schema='public'
            ),
            nullable=False,
            comment='任務狀態'
        ),
        sa.Column(
            'priority',
            postgresql.ENUM('P0', 'P1', 'P2', name='priority', schema='public'),
            nullable=False,
            comment='優先級'
        ),
        sa.Column('estimated_hours', sa.Integer(), nullable=False, comment='預估工時'),
        sa.Column('actual_hours', sa.Integer(), comment='實際工時'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), comment='完成時間'),
        sa.Column('assignee', sa.String(100), comment='被分配者'),
        sa.Column('reporter', sa.String(100), nullable=False, comment='報告者'),
        sa.Column('watchers', postgresql.ARRAY(sa.String()), default=list(), comment='觀察者列表'),
        sa.Column('dependencies', postgresql.ARRAY(sa.String()), default=list(), comment='前置依賴'),
        sa.Column('dependents', postgresql.ARRAY(sa.String()), default=list(), comment='依賴此任務'),
        sa.Column('acceptance_criteria', postgresql.ARRAY(sa.Text()), default=list(), comment='驗收標準'),
        sa.Column('deliverables', postgresql.ARRAY(sa.String()), default=list(), comment='交付物'),
        sa.Column('sprint', sa.String(50), comment='所屬Sprint'),
        sa.Column('story_points', sa.Integer(), default=1, comment='故事點數'),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), default=dict(), comment='元數據'),
        sa.PrimaryKeyConstraint('id')
    )

    # 創建索引
    op.create_index('idx_tasks_status', 'tasks', ['status'])
    op.create_index('idx_tasks_priority', 'tasks', ['priority'])
    op.create_index('idx_tasks_assignee', 'tasks', ['assignee'])
    op.create_index('idx_tasks_sprint', 'tasks', ['sprint'])
    op.create_index('idx_tasks_created_at', 'tasks', ['created_at'])

    # 創建Sprint表
    op.create_table(
        'sprints',
        sa.Column('id', sa.String(50), nullable=False, comment='Sprint唯一ID'),
        sa.Column('name', sa.String(100), nullable=False, comment='Sprint名稱'),
        sa.Column('goal', sa.Text(), comment='Sprint目標'),
        sa.Column('start_date', sa.Date(), nullable=False, comment='開始日期'),
        sa.Column('end_date', sa.Date(), nullable=False, comment='結束日期'),
        sa.Column(
            'status',
            postgresql.ENUM(
                '計劃中', '進行中', '已完成', '已取消',
                name='sprintstatus',
                schema='public'
            ),
            default='計劃中',
            comment='Sprint狀態'
        ),
        sa.Column('task_ids', postgresql.ARRAY(sa.String()), default=list(), comment='任務ID列表'),
        sa.Column('planned_hours', sa.Integer(), default=0, comment='計劃工時'),
        sa.Column('completed_hours', sa.Integer(), default=0, comment='已完成工時'),
        sa.Column('team_capacity', sa.Integer(), default=0, comment='團隊容量'),
        sa.Column('velocity', sa.Float(), comment='Sprint速度'),
        sa.Column('estimated_velocity', sa.Float(), comment='預估速度'),
        sa.Column('completion_rate', sa.Float(), comment='完成率'),
        sa.Column('burndown_data', postgresql.JSON(astext_type=sa.Text()), comment='燃盡圖數據'),
        sa.Column('retrospective_notes', sa.Text(), comment='回顧記錄'),
        sa.Column('improvements', postgresql.ARRAY(sa.String()), default=list(), comment='改進建議'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # 創建索引
    op.create_index('idx_sprints_status', 'sprints', ['status'])
    op.create_index('idx_sprints_dates', 'sprints', ['start_date', 'end_date'])
    op.create_index('idx_sprints_created', 'sprints', ['created_at'])

    # 創建任務狀態變更日誌表
    op.create_table(
        'task_transitions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.String(20), nullable=False, comment='任務ID'),
        sa.Column('from_status', sa.String(20), comment='原始狀態'),
        sa.Column('to_status', sa.String(20), nullable=False, comment='目標狀態'),
        sa.Column('comment', sa.Text(), comment='變更說明'),
        sa.Column('user_id', sa.String(100), comment='操作用戶'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='變更時間'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 創建索引
    op.create_index('idx_transitions_task_id', 'task_transitions', ['task_id'])
    op.create_index('idx_transitions_created_at', 'task_transitions', ['created_at'])

    # 創建團隊成員表
    op.create_table(
        'team_members',
        sa.Column('id', sa.String(50), primary_key=True, comment='成員ID'),
        sa.Column('name', sa.String(100), nullable=False, comment='成員姓名'),
        sa.Column('email', sa.String(100), comment='郵箱'),
        sa.Column('velocity_avg', sa.Integer(), default=40, comment='平均速度 (工時/Sprint)'),
        sa.Column('capacity_hours', sa.Integer(), default=40, comment='單次Sprint容量'),
        sa.Column('skills', postgresql.ARRAY(sa.String()), default=list(), comment='技能列表'),
        sa.Column('role', sa.String(50), comment='角色'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # 創建項目指標表
    op.create_table(
        'project_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sprint_id', sa.String(50), comment='Sprint ID'),
        sa.Column('metric_name', sa.String(50), nullable=False, comment='指標名稱'),
        sa.Column('metric_value', sa.Float(), comment='指標值'),
        sa.Column('metric_data', postgresql.JSON(astext_type=sa.Text()), comment='指標詳細數據'),
        sa.Column('calculated_at', sa.DateTime(), server_default=sa.func.now(), comment='計算時間'),
        sa.ForeignKeyConstraint(['sprint_id'], ['sprints.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 創建索引
    op.create_index('idx_metrics_sprint', 'project_metrics', ['sprint_id'])
    op.create_index('idx_metrics_name', 'project_metrics', ['metric_name'])
    op.create_index('idx_metrics_calculated', 'project_metrics', ['calculated_at'])

    # 創建Sprint任務關聯表
    op.create_table(
        'sprint_tasks',
        sa.Column('sprint_id', sa.String(50), nullable=False),
        sa.Column('task_id', sa.String(20), nullable=False),
        sa.Column('added_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['sprint_id'], ['sprints.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('sprint_id', 'task_id')
    )


def downgrade():
    """降級數據庫結構"""

    # 刪除表 (按依賴順序)
    op.drop_table('sprint_tasks')
    op.drop_table('project_metrics')
    op.drop_table('team_members')
    op.drop_table('task_transitions')
    op.drop_table('sprints')
    op.drop_table('tasks')

    # 刪除自定義類型
    op.execute('DROP TYPE IF EXISTS taskstatus')
    op.execute('DROP TYPE IF EXISTS sprintstatus')
    op.execute('DROP TYPE IF EXISTS priority')

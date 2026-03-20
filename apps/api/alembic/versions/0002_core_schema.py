"""core_schema

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-20

Creates all core application tables:
  organizations, users, user_org_memberships, classes, students,
  class_enrollments, parent_student_links, consent_records, audit_events
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------------
    # organizations
    # ---------------------------------------------------------------
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("slug"),
    )

    # ---------------------------------------------------------------
    # users (org_id nullable — invited users have no org yet)
    # ---------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("google_id", sa.String(255), nullable=True),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("google_id"),
    )
    op.create_index("idx_users_org_id", "users", ["org_id"])

    # ---------------------------------------------------------------
    # user_org_memberships
    # ---------------------------------------------------------------
    op.create_table(
        "user_org_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.UniqueConstraint("user_id", "org_id", name="uq_user_org_memberships_user_org"),
    )

    # ---------------------------------------------------------------
    # classes
    # ---------------------------------------------------------------
    op.create_table(
        "classes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("state_standard", sa.String(255), nullable=True),
        sa.Column("join_code", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"]),
        sa.UniqueConstraint("join_code"),
    )
    op.create_index("idx_classes_org_id", "classes", ["org_id"])

    # ---------------------------------------------------------------
    # students
    # ---------------------------------------------------------------
    op.create_table(
        "students",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("grade_level", sa.String(50), nullable=True),
        sa.Column("profile", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("consent_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("consent_confirmed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("consent_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["consent_confirmed_by"], ["users.id"]),
    )
    op.create_index("idx_students_org_id", "students", ["org_id"])

    # ---------------------------------------------------------------
    # class_enrollments
    # ---------------------------------------------------------------
    op.create_table(
        "class_enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "enrolled_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.UniqueConstraint("class_id", "student_id", name="uq_class_enrollments_class_student"),
    )
    op.create_index("idx_class_enrollments_class_id", "class_enrollments", ["class_id"])
    op.create_index("idx_class_enrollments_student_id", "class_enrollments", ["student_id"])

    # ---------------------------------------------------------------
    # parent_student_links
    # ---------------------------------------------------------------
    op.create_table(
        "parent_student_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("parent_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("linked_via", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["parent_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.UniqueConstraint("parent_user_id", "student_id", name="uq_parent_student_links_parent_student"),
    )

    # ---------------------------------------------------------------
    # consent_records
    # ---------------------------------------------------------------
    op.create_table(
        "consent_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("confirmed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["confirmed_by"], ["users.id"]),
    )

    # ---------------------------------------------------------------
    # audit_events (append-only — permissions enforced below)
    # ---------------------------------------------------------------
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("target_entity", sa.String(100), nullable=False),
        sa.Column("target_id", sa.String(255), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
    )
    op.create_index("idx_audit_events_org_id", "audit_events", ["org_id"])
    op.create_index("idx_audit_events_actor_id", "audit_events", ["actor_id"])
    op.create_index("idx_audit_events_timestamp", "audit_events", ["timestamp"])

    # audit_events is append-only: revoke UPDATE/DELETE, grant INSERT/SELECT to ilm
    op.execute("REVOKE UPDATE, DELETE ON audit_events FROM ilm")
    op.execute("GRANT INSERT, SELECT ON audit_events TO ilm")


def downgrade() -> None:
    # Drop in reverse dependency order.
    # Note: permissions are implicitly revoked when tables are dropped,
    # so no REVOKE/GRANT is needed here. The upgrade() GRANT/REVOKE
    # requires the migration user to be a table owner or superuser.
    op.drop_table("audit_events")
    op.drop_table("consent_records")
    op.drop_table("parent_student_links")
    op.drop_table("class_enrollments")
    op.drop_table("students")
    op.drop_table("classes")
    op.drop_table("user_org_memberships")
    op.drop_table("users")
    op.drop_table("organizations")

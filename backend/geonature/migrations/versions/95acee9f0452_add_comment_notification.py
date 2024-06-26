"""add comment notification

Revision ID: 95acee9f0452
Revises: 9e9218653d6c
Create Date: 2023-04-06 19:02:39.863972

"""

import sqlalchemy as sa
from alembic import op

from geonature.core.notifications.models import (
    NotificationCategory,
    NotificationRule,
    NotificationTemplate,
)

# revision identifiers, used by Alembic.
revision = "95acee9f0452"
down_revision = "e2a94808cf76"
branch_labels = None
depends_on = ("09a637f06b96",)  # Geonature Notifications

CATEGORY_CODE = "OBSERVATION-COMMENT"
EMAIL_CONTENT = (
    "<p>Bonjour <i>{{ role.nom_complet }}</i> !</p>"
    "<p>{{ user.nom_complet }} a commenté l'observation de {{ synthese.nom_cite }} du {{ synthese.meta_create_date.strftime('%d-%m-%Y') }}"
    "que vous avez créée ou commentée</p>"
    '<p>Vous pouvez y accéder directement <a href="{{ url }}">ici</a></p>'
    "<p><i>Vous recevez cet email automatiquement via le service de notification de GeoNature.</i></p>"
)
DB_CONTENT = (
    "{{ user.nom_complet }} a commenté l'observation de {{ synthese.nom_cite }} du "
    "{{ synthese.meta_create_date.strftime('%d-%m-%Y') }} que vous avez créée ou commentée"
)


def upgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    # Add category
    category = NotificationCategory(
        code=CATEGORY_CODE,
        label="Nouveau commentaire sur une observation",
        description=(
            "Se déclenche lorsqu'un nouveau commentaire est ajouté à une de vos observations, ou une observation que vous avez commenté"
        ),
    )

    session.add(category)

    for method, content in (("EMAIL", EMAIL_CONTENT), ("DB", DB_CONTENT)):
        template = NotificationTemplate(category=category, code_method=method, content=content)
        session.add(template)

    session.commit()

    op.execute(
        f"""
        INSERT INTO 
            gn_notifications.t_notifications_rules (code_category, code_method)
        VALUES
            ('{CATEGORY_CODE}', 'DB'),
            ('{CATEGORY_CODE}', 'EMAIL')
        """
    )


def downgrade():
    conn = op.get_bind()
    metadata = sa.MetaData(bind=conn)
    notification_category = sa.Table(
        "bib_notifications_categories", metadata, schema="gn_notifications", autoload_with=conn
    )
    notification_template = sa.Table(
        "bib_notifications_templates", metadata, schema="gn_notifications", autoload_with=conn
    )
    notification_rule = sa.Table(
        "t_notifications_rules", metadata, schema="gn_notifications", autoload_with=conn
    )
    category = conn.execute(
        sa.select(notification_category).where(notification_category.c.code == CATEGORY_CODE)
    ).one()
    op.execute(
        sa.delete(notification_template).where(
            notification_template.c.code_category == category.code
        )
    )
    op.execute(
        sa.delete(notification_rule).where(notification_rule.c.code_category == category.code)
    )

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ml_experiment_dashboard", "0002_experiment_columns_experiment_commentary_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE ml_experiment_dashboard_experiment DROP COLUMN chart_image;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]

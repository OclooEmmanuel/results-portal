import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Step 1 of 3: introduce a temporary nullable FK from Result to the
    canonical students.Student so existing rows can be re-pointed without
    losing data. The legacy results.Student is dropped in the final step.
    """

    dependencies = [
        ("students", "0001_initial"),
        ("results", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="result",
            name="new_student",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="results_migrated",
                to="students.student",
            ),
        ),
    ]

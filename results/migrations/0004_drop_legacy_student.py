import django.db.models.deletion
from django.db import migrations, models

# Every column of results.Result except the student FKs.
SCORE_COLUMNS = (
    "id",
    "mock_number",
    "maths",
    "english",
    "science",
    "social_studies",
    "rme",
    "computing",
    "carear_tech",
    "cad",
    "asante_twi",
    "french",
    "remark",
)

SCORE_DDL = """
    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    mock_number varchar(2) NOT NULL,
    maths integer NOT NULL,
    english integer NOT NULL,
    science integer NOT NULL,
    social_studies integer NOT NULL,
    rme integer NOT NULL,
    computing integer NOT NULL,
    carear_tech integer NOT NULL,
    cad integer NOT NULL,
    asante_twi integer NOT NULL,
    french integer NOT NULL,
    remark varchar(100)
"""

LEGACY_STUDENT_DDL = """
    CREATE TABLE results_student (
        id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
        full_name varchar(100) NOT NULL,
        index_number varchar(20) NOT NULL,
        access_code varchar(20) NOT NULL,
        photo varchar(100)
    )
"""

UNIQUE_INDEX = (
    'CREATE UNIQUE INDEX "results_result_student_id_mock_number_60e69b26_uniq"'
    " ON results_result (student_id, mock_number)"
)
FK_INDEX = (
    'CREATE INDEX "results_result_student_id_c683d594"'
    " ON results_result (student_id)"
)
TEMP_FK_INDEX = (
    'CREATE INDEX "results_result_new_student_id_9d4e7f21"'
    " ON results_result (new_student_id)"
)


def _create_result_table(cursor, fk_columns):
    columns = ",\n    ".join([SCORE_DDL.strip()] + fk_columns)
    cursor.execute(f"CREATE TABLE results_result (\n    {columns}\n)")


def collapse_onto_canonical_student(apps, schema_editor):
    """
    Forward: drop the legacy results.Student table and promote new_student_id
    to be the real Result.student, referencing students.Student.
    """
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys=off")

        # Refuse to run if any Result never got a canonical student; silently
        # dropping marks here would be far worse than a failed migration.
        cursor.execute(
            "SELECT COUNT(*) FROM results_result WHERE new_student_id IS NULL"
        )
        orphans = cursor.fetchone()[0]
        if orphans:
            raise RuntimeError(
                f"{orphans} Result row(s) still have a NULL new_student_id. "
                f"Run 0003 first; refusing to drop the legacy student table."
            )

        cursor.execute(
            f"CREATE TEMPORARY TABLE _collapse AS "
            f"SELECT {', '.join(SCORE_COLUMNS)}, new_student_id AS student_id "
            f"FROM results_result"
        )
        cursor.execute("DROP TABLE results_result")
        _create_result_table(
            cursor,
            ["student_id bigint NOT NULL REFERENCES students_student(id)"],
        )
        cursor.execute(
            f"INSERT INTO results_result ({', '.join(SCORE_COLUMNS)}, student_id) "
            f"SELECT {', '.join(SCORE_COLUMNS)}, student_id FROM _collapse"
        )
        cursor.execute(UNIQUE_INDEX)
        cursor.execute(FK_INDEX)
        cursor.execute("DROP TABLE _collapse")

        # Only safe once nothing references it.
        cursor.execute("DROP TABLE IF EXISTS results_student")
        cursor.execute("PRAGMA foreign_keys=on")


def restore_legacy_student(apps, schema_editor):
    """
    Reverse: recreate results.Student and restore the exact schema that 0003
    left behind, so the whole 0002-0004 chain can be unapplied.

    One legacy row is recreated per student actually referenced by a result, and
    it is matched to its canonical twin on the unique index_number so that
    0003's reverse reuses these rows rather than duplicating them.
    """
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys=off")
        cursor.execute(LEGACY_STUDENT_DDL)

        cursor.execute(
            """
            INSERT INTO results_student (full_name, index_number, access_code, photo)
            SELECT DISTINCT s.full_name, s.index_number, s.access_code, s.photo
            FROM students_student s
            WHERE s.id IN (SELECT student_id FROM results_result)
            """
        )

        # Snapshot the rows plus both ids before the table is rebuilt.
        cursor.execute(
            f"CREATE TEMPORARY TABLE _restore AS "
            f"SELECT r.id, r.mock_number, r.maths, r.english, r.science, "
            f"r.social_studies, r.rme, r.computing, r.carear_tech, r.cad, "
            f"r.asante_twi, r.french, r.remark, "
            f"ls.id AS legacy_id, r.student_id AS canonical_id "
            f"FROM results_result r "
            f"JOIN students_student s ON s.id = r.student_id "
            f"JOIN results_student ls ON ls.index_number = s.index_number"
        )

        cursor.execute("DROP TABLE results_result")
        _create_result_table(
            cursor,
            [
                "student_id bigint NOT NULL REFERENCES results_student(id)",
                "new_student_id bigint NULL REFERENCES students_student(id)",
            ],
        )
        cursor.execute(
            f"INSERT INTO results_result ({', '.join(SCORE_COLUMNS)}, "
            f"student_id, new_student_id) "
            f"SELECT {', '.join(SCORE_COLUMNS)}, legacy_id, canonical_id "
            f"FROM _restore"
        )
        cursor.execute(UNIQUE_INDEX)
        cursor.execute(FK_INDEX)
        cursor.execute(TEMP_FK_INDEX)
        cursor.execute("DROP TABLE _restore")
        cursor.execute("PRAGMA foreign_keys=on")


class Migration(migrations.Migration):
    """
    Step 3 of 3: drop the legacy results.Student table and make the migrated FK
    the real Result.student.

    The table surgery is explicit SQL rather than RemoveField/RenameField
    because those are not reversibly paired on SQLite: reversing RemoveField
    re-adds a NOT NULL column that no operation can repopulate. State and
    schema are therefore declared separately, with RunPython owning the tables
    in both directions.
    """

    dependencies = [
        ("results", "0003_migrate_students_to_canonical"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterUniqueTogether(
                    name="result",
                    unique_together=set(),
                ),
                migrations.RemoveField(
                    model_name="result",
                    name="student",
                ),
                migrations.RenameField(
                    model_name="result",
                    old_name="new_student",
                    new_name="student",
                ),
                migrations.AlterField(
                    model_name="result",
                    name="student",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="results",
                        to="students.student",
                    ),
                ),
                migrations.AlterUniqueTogether(
                    name="result",
                    unique_together={("student", "mock_number")},
                ),
                migrations.DeleteModel(
                    name="Student",
                ),
            ],
        ),
        migrations.RunPython(
            collapse_onto_canonical_student,
            reverse_code=restore_legacy_student,
        ),
    ]

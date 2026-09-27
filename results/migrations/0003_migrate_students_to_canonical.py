from django.db import migrations

# Fields copied from the legacy results.Student model to students.Student.
STUDENT_FIELDS = ("full_name", "index_number", "access_code", "photo")


def copy_students_to_canonical_table(apps, schema_editor):
    """
    Move every legacy results.Student row into students.Student and re-point
    that row's Result records at the surviving student.

    students.Student is the canonical table going forward, so when a legacy row
    collides with an existing row on the unique `index_number` we re-use the
    canonical row rather than creating a duplicate. index_number is the
    credential students type in, so it is the only safe join key.

    Rows that collide are reported, because the merge is lossy for `full_name`
    and needs a human to reconcile.
    """
    LegacyStudent = apps.get_model("results", "Student")
    Student = apps.get_model("students", "Student")
    Result = apps.get_model("results", "Result")

    collisions = []
    transferred = 0
    reused = 0

    for legacy in LegacyStudent.objects.all().order_by("id"):
        payload = {field: getattr(legacy, field) for field in STUDENT_FIELDS}

        existing = Student.objects.filter(index_number=legacy.index_number).first()

        if existing is None:
            student = Student.objects.create(**payload)
            transferred += 1
        else:
            student = existing
            reused += 1
            if existing.full_name != legacy.full_name:
                collisions.append(
                    f"index_number={legacy.index_number!r}: kept "
                    f"{existing.full_name!r} (students.Student), discarded "
                    f"{legacy.full_name!r} (results.Student)"
                )

        Result.objects.filter(student_id=legacy.id).update(new_student_id=student.id)

    orphan_results = Result.objects.filter(new_student_id__isnull=True).count()
    if orphan_results:
        raise RuntimeError(
            f"{orphan_results} Result row(s) could not be matched to a "
            f"students.Student row. Aborting so no marks are lost."
        )

    print(f"\n[0003] students transferred: {transferred}, re-used: {reused}")
    for conflict in collisions:
        print(f"[0003] !! index_number conflict -> {conflict}")


def restore_students_to_legacy_table(apps, schema_editor):
    """
    Reverse of the above: re-create legacy results.Student rows and re-point
    Result.student at them.

    Re-uses any legacy row already restored by 0004's reverse (matched on the
    unique index_number) instead of creating a second copy, so unapplying the
    chain never duplicates students.
    """
    LegacyStudent = apps.get_model("results", "Student")
    Student = apps.get_model("students", "Student")
    Result = apps.get_model("results", "Result")

    mapping = {}

    for student_id in (
        Result.objects.exclude(new_student_id=None)
        .values_list("new_student_id", flat=True)
        .distinct()
    ):
        student = Student.objects.filter(id=student_id).first()
        if student is None:
            continue

        payload = {field: getattr(student, field) for field in STUDENT_FIELDS}
        legacy = LegacyStudent.objects.filter(
            index_number=student.index_number
        ).first() or LegacyStudent.objects.create(**payload)

        mapping[student.id] = legacy.id

    for student_id, legacy_id in mapping.items():
        Result.objects.filter(new_student_id=student_id).update(student_id=legacy_id)

    Result.objects.update(new_student_id=None)
    print(f"\n[0003 reverse] restored {len(mapping)} legacy student row(s)")


class Migration(migrations.Migration):
    dependencies = [
        ("results", "0002_result_new_student"),
    ]

    operations = [
        migrations.RunPython(
            copy_students_to_canonical_table,
            reverse_code=restore_students_to_legacy_table,
        ),
    ]

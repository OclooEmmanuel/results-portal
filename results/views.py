from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Result
from students.models import Student
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from config.csv_import import (
    cells_to_values,
    normalise_headers,
    read_csv,
    to_int,
)


def home(request):
    return render(request, 'home.html')


#--------------------student result access views---------------------------

def check_results(request):
    error = None

    if request.method == "POST":
        index_number = request.POST.get("index_number")
        access_code = request.POST.get("access_code")
        mock_number = request.POST.get("mock_number")

        try:
            student = Student.objects.get(
                index_number=index_number,
                access_code=access_code
            )
            request.session['student_id'] = student.id
            request.session['mock_number'] = mock_number

            return redirect("student_results")
        except Student.DoesNotExist:
            error = "Invalid index number or access code"

    return render(request, "results/check_results.html", {"error": error})


@login_required
def add_subject_marks(request):
    students = Student.objects.all().order_by("index_number")

    # Single source of truth: the labels and order now match every other page
    # (slip, admin slip, CSV import) instead of drifting from them.
    subjects = Result.SUBJECT_FIELDS

    context = {"students": students, "subjects": subjects}

    if request.method == "POST":
        student_id = request.POST.get("student", "").strip()
        mock_number = request.POST.get("mock_number", "").strip()

        if not student_id:
            messages.error(request, "Select a student before saving.")
            return render(request, "results/add_subject_marks.html", context)

        if not mock_number:
            messages.error(request, "Enter the mock number before saving.")
            return render(request, "results/add_subject_marks.html", context)

        if not Student.objects.filter(id=student_id).exists():
            messages.error(request, "That student no longer exists.")
            return render(request, "results/add_subject_marks.html", context)

        if Result.objects.filter(student_id=student_id, mock_number=mock_number).exists():
            messages.error(request, "Results for this mock already exist.")
            return redirect("add_subject_marks")

        # Marks are NOT NULL in the database, so a blank or non-numeric cell
        # previously reached the ORM and raised IntegrityError (HTTP 500).
        # Validate first and name the offending subjects.
        marks = {}
        errors = []

        for field, label in subjects:
            raw = (request.POST.get(field) or "").strip()

            if not raw:
                errors.append(f"{label} is required")
                continue

            try:
                value = int(raw)
            except ValueError:
                errors.append(f"{label} must be a whole number")
                continue

            if not 0 <= value <= 100:
                errors.append(f"{label} must be between 0 and 100")
                continue

            marks[field] = value

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, "results/add_subject_marks.html", context)

        Result.objects.create(
            student_id=student_id,
            mock_number=mock_number,
            remark=(request.POST.get("remark") or "").strip(),
            **marks,
        )

        messages.success(request, "Results saved successfully.")
        return redirect("add_subject_marks")

    return render(request, "results/add_subject_marks.html", context)


@login_required
def edit_result(request, result_id):
    result = get_object_or_404(Result, id=result_id)

    if request.method != "POST":
        return redirect("manage_results")

    fields = [
        "maths", "english", "science", "social_studies", "rme",
        "computing", "carear_tech", "cad", "asante_twi", "french",
    ]

    for field in fields:
        value = request.POST.get(field)

        if value is None:
            continue

        try:
            value = int(value)
        except ValueError:
            messages.error(request, "All marks must be numbers.")
            return redirect("manage_results")

        if not 0 <= value <= 100:
            messages.error(request, "Marks must be between 0 and 100.")
            return redirect("manage_results")

        setattr(result, field, value)

    result.remark = request.POST.get("remark", "").strip()

    # (Optional) Auto-generate remark if empty
    if not result.remark:
        result.remark = "Results Updated"

    result.save()

    messages.success(
        request,
        f"Results updated successfully for {result.student.full_name}"
    )

    return redirect("manage_results")



@login_required
def manage_results(request):
    query = request.GET.get("q", "")
    mock = request.GET.get("mock", "")

    results = Result.objects.select_related("student")

    if query:
        results = results.filter(
            Q(student__full_name__icontains=query) |
            Q(student__index_number__icontains=query)
        )

    if mock:
        results = results.filter(mock_number=mock)

    # get unique mock numbers for buttons
    mock_numbers = (
        Result.objects
        .values_list("mock_number", flat=True)
        .distinct()
        .order_by("mock_number")
    )

    context = {
        "results": results,
        "count": results.count(),
        "query": query,
        "mock": mock,
        "mock_numbers": mock_numbers,
    }
    return render(request, "results/manage_results.html", context)




# ---------------------------------------------------------

def student_results(request,):
    student_id = request.session.get("student_id")

    if not student_id:
        return redirect("check_results")

    student = get_object_or_404(Student, id=student_id)

    # Get mock from URL
    mock_number = request.GET.get("mock")

    # Get all available mocks for this student
    available_mocks = (
        Result.objects.filter(student=student).values_list("mock_number", flat=True).distinct()
    )

    # If no mock selected → show mock selection
    if not mock_number:
        return render(request, "results/select_mock.html", {
            "student": student,
            "mocks": available_mocks
        })

    # If mock selected but does not exist → redirect safely
    if mock_number not in available_mocks:
        return redirect("student_results")

    # Fetch result
    result = Result.objects.get(
        student=student,
        mock_number=mock_number
    )

    return render(
        request,
        "results/student_results.html",
        result.build_report()
    )


# ---------------------------------------------------------
@login_required
def view_student_mock(request):
    student_id = request.GET.get("student")
    mock_number = request.GET.get("mock")

    if not student_id:
        return redirect("check_results")

    student = get_object_or_404(Student, id=student_id)

    result = get_object_or_404(
        Result,
        student=student,
        mock_number=mock_number
    )

    return render(
        request,
        "results/admin_student_results.html",
        result.build_report()
    )


@login_required
def delete_mock_result(request, result_id):
    result = get_object_or_404(Result, id=result_id)

    if request.method == "POST":
        result.delete()
        messages.success(request, "Mock result deleted successfully.")
        return redirect("manage_results")

    # If someone tries GET directly, just redirect safely
    return redirect("manage_results")


# ---------------------------------------------------------
# BULK RESULTS CSV IMPORT
# ---------------------------------------------------------

# Header spellings we accept. The ten marks are the same subjects as the
# single-student form, so a file exported from the marks sheet or typed by
# hand both work without renaming columns first.
RESULT_CSV_ALIASES = {
    "index_number": "index_number",
    "index_no": "index_number",
    "index": "index_number",
    "index_num": "index_number",
    "student_index": "index_number",
    "mock_number": "mock_number",
    "mock": "mock_number",
    "mock_no": "mock_number",
    "exam": "mock_number",
    "maths": "maths",
    "mathematics": "maths",
    "math": "maths",
    "english": "english",
    "english_language": "english",
    "science": "science",
    "integrated_science": "science",
    "social_studies": "social_studies",
    "social": "social_studies",
    "rme": "rme",
    "religious_and_moral_education": "rme",
    "computing": "computing",
    "ict": "computing",
    "carear_tech": "carear_tech",
    "career_tech": "carear_tech",
    "career_technology": "carear_tech",
    "cad": "cad",
    "creative_arts_design": "cad",
    "creative_arts_and_design": "cad",
    "asante_twi": "asante_twi",
    "twi": "asante_twi",
    "french": "french",
    "remark": "remark",
    "remarks": "remark",
}

RESULT_SESSION_KEY = "result_import_rows"

MARK_FIELDS = tuple(field for field, _ in Result.SUBJECT_FIELDS)

REQUIRED_RESULT_COLUMNS = ("index_number", "mock_number") + MARK_FIELDS

SAMPLE_CSV = (
    "index_number,mock_number,maths,english,science,social_studies,rme,"
    "computing,career_tech,cad,asante_twi,french,remark\r\n"
    "0103060015,1,88,72,65,80,58,45,77,41,91,52,\r\n"
    "0103060016,1,64,81,55,70,62,74,48,66,39,45,Improved\r\n"
)


def _max_length(model, field):
    return model._meta.get_field(field).max_length


def _parse_result_csv(upload):
    """Parse an uploaded marks CSV into a list of per-row dicts.

    Returns (rows, fatal). `fatal` means the file cannot be used at all. A row
    with a problem never sets fatal: it is reported by line number so one bad
    line does not block the rest of the sheet.

    Nothing is written here. This only decides what *would* happen.
    """
    header, raw_rows, fatal = read_csv(upload)
    if fatal:
        return [], fatal

    columns = normalise_headers(header, RESULT_CSV_ALIASES)
    if all(c is None for c in columns):
        return [], (
            "No recognisable columns. The header must include index_number, "
            "mock_number and a column for every subject."
        )

    missing = [label for label in REQUIRED_RESULT_COLUMNS if label not in columns]
    if missing:
        return [], (
            "The file is missing %d required column(s): %s. Download the "
            "template to see the expected layout."
            % (len(missing), ", ".join(missing))
        )

    # One query each, rather than one per row.
    students_by_index = dict(Student.objects.values_list("index_number", "id"))
    names_by_id = dict(Student.objects.values_list("id", "full_name"))

    existing = set(Result.objects.values_list("student_id", "mock_number"))

    seen_keys = set()

    rows = []
    for line_no, raw_row in raw_rows:
        values = cells_to_values(columns, raw_row)

        index = values.get("index_number", "")
        mock_number = values.get("mock_number", "")
        remark = values.get("remark", "")

        row = {
            "line": line_no,
            "index_number": index,
            "student_name": "",
            "mock_number": mock_number,
            "remark": remark,
            "average": "",
            "aggregate": "",
            "status": "new",
            "reason": "",
        }
        rows.append(row)

        # Each check sets `problem` and bails out; the row is reported once at
        # the bottom rather than by a helper mutating it from six branches.
        problem = None

        if not index:
            problem = "index number is required"
        elif len(index) > _max_length(Student, "index_number"):
            problem = "index number is longer than %d characters" % _max_length(
                Student, "index_number"
            )
        elif not mock_number:
            problem = "mock number is required"
        elif len(mock_number) > _max_length(Result, "mock_number"):
            problem = (
                "mock number is longer than %d characters, use 1, 2, 3 ..."
                % _max_length(Result, "mock_number")
            )

        student_id = None
        if problem is None:
            student_id = students_by_index.get(index)
            if student_id is None:
                problem = "no student has this index number, import students first"

        # Every mark must be a whole number in range. A blank cell is an error
        # rather than a silent zero, because 0 is a real mark (grade 9) and a
        # missing cell would quietly drag an aggregate down.
        marks = {}
        if problem is None:
            for field in MARK_FIELDS:
                mark = to_int(values.get(field, ""))
                if mark is None:
                    problem = "%s is missing or not a whole number" % field
                    break
                if not 0 <= mark <= 100:
                    problem = "%s must be between 0 and 100" % field
                    break
                marks[field] = mark

        if problem is None and len(remark) > _max_length(Result, "remark"):
            problem = "remark is longer than %d characters" % _max_length(
                Result, "remark"
            )

        if problem is not None:
            row["status"] = "error"
            row["reason"] = problem
            continue

        row["student_name"] = names_by_id.get(student_id, "")
        row["marks"] = marks

        # Same student and mock twice in one file: the second is the mistake.
        key = (student_id, mock_number)
        if key in seen_keys:
            row["status"] = "error"
            row["reason"] = (
                "index number %s already appears for mock %s in this file"
                % (index, mock_number)
            )
            continue
        seen_keys.add(key)

        # Already saved: skip, never overwrite.
        if key in existing:
            row["status"] = "skip"
            row["reason"] = (
                "results for mock %s already exist for this student" % mock_number
            )
            continue

        # An unsaved instance is enough to grade: get_average and get_aggregate
        # only read the marks.
        preview = Result(mock_number=mock_number, **marks)
        row["average"] = preview.get_average()
        row["aggregate"] = preview.get_aggregate()

    return rows, None


@login_required
def result_import(request):
    """Bulk-create marks from a CSV, with a preview before anything is saved.

    Flow: upload -> parse -> preview (new / skipped / errored) -> confirm.
    Students are matched on index number; a row whose student is unknown is
    rejected rather than creating a student as a side effect. A (student, mock)
    pair that already has results is skipped and reported, never overwritten.
    """
    from django.db import transaction

    if request.method == "GET" and request.GET.get("template") == "csv":
        response = HttpResponse(SAMPLE_CSV, content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="result_import_template.csv"'
        )
        return response

    # ---- step 3: confirm ----
    if request.method == "POST" and request.POST.get("confirm"):
        rows = request.session.pop(RESULT_SESSION_KEY, None) or []
        if not rows:
            messages.error(
                request,
                "That upload has expired. Upload the file again to continue.",
            )
            return redirect("result_import")

        created, skipped, failed = [], [], []
        with transaction.atomic():
            for row in rows:
                if row.get("status") != "new":
                    (skipped if row.get("status") == "skip" else failed).append(row)
                    continue

                index = row["index_number"]
                mock_number = row["mock_number"]

                # Re-check at write time: a result may have been added between
                # the preview and the confirmation.
                if Result.objects.filter(
                    student__index_number=index, mock_number=mock_number
                ).exists():
                    row["status"] = "skip"
                    row["reason"] = "results for mock %s already exist" % mock_number
                    skipped.append(row)
                    continue

                student = Student.objects.get(index_number=index)
                Result.objects.create(
                    student=student,
                    mock_number=mock_number,
                    remark=row.get("remark") or None,
                    **row["marks"],
                )
                created.append(row)

        messages.success(
            request,
            "Imported %d result(s). Skipped %d, rejected %d."
            % (len(created), len(skipped), len(failed)),
        )
        if failed:
            messages.error(
                request,
                "Lines not imported: %s"
                % ", ".join(str(r["line"]) for r in failed[:20]),
            )
        return redirect("manage_results")

    # ---- step 2: parse and preview ----
    if request.method == "POST":
        rows, fatal = _parse_result_csv(request.FILES.get("file"))
        if fatal:
            messages.error(request, fatal)
            return redirect("result_import")

        if not rows:
            messages.error(request, "That file has a header but no data rows.")
            return redirect("result_import")

        request.session[RESULT_SESSION_KEY] = rows
        context = {
            "rows": rows,
            "new_count": sum(1 for r in rows if r["status"] == "new"),
            "skip_count": sum(1 for r in rows if r["status"] == "skip"),
            "error_count": sum(1 for r in rows if r["status"] == "error"),
        }
        return render(request, "results/result_import.html", context)

    # ---- step 1: upload form ----
    return render(request, "results/result_import.html", {"rows": None})

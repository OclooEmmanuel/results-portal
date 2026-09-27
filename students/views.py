from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Student
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required



@login_required
def student_list(request):
    students = Student.objects.all()
    return render(request, "student/student_list.html", {"students": students})


def student_detail(request, indexnumber):
    pass  # Placeholder for student detail view

@login_required
def add_student(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        index_number = request.POST.get("index_number")
        access_code = request.POST.get("access_code")
        photo = request.FILES.get("photo")

        if Student.objects.filter(index_number=index_number).exists():
            messages.error(request, "Index number already exists")
            return redirect("add_student")

        Student.objects.create(
            full_name=full_name,
            index_number=index_number,
            access_code=access_code,
            photo=photo
        )

        messages.success(request, "Student added successfully")
        return redirect("add_student")

    return render(request, "student/add_student.html")



@login_required
def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        try:
            student.full_name = request.POST.get("full_name")
            student.index_number = request.POST.get("index_number")
            student.access_code = request.POST.get("access_code")

            if request.FILES.get("photo"):
                if student.photo:
                    student.photo.delete(save=False)
                student.photo = request.FILES.get("photo")

            student.save()
            messages.success(request, "Student details updated successfully")
        except Exception as e:
            messages.error(request, f"Error updating student: {str(e)}")

        return redirect("student_list")

    # If GET request, return to the list page
    return redirect("student_list")




@login_required
def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        student.delete()
        messages.success(request, f"Student {student.full_name} deleted successfully!")
        return redirect("student_list")

    # If GET request, render a confirmation page
    return render(request, "student/delete_student.html", {"student": student})



# ---------------------------------------------------------
# BULK CSV IMPORT
# ---------------------------------------------------------

# Header spellings we accept, so a file exported from Excel, Google Sheets or
# hand-typed in Notepad all work without the user renaming columns first.
CSV_ALIASES = {
    "full_name": "full_name",
    "name": "full_name",
    "student_name": "full_name",
    "candidate": "full_name",
    "index_number": "index_number",
    "index_no": "index_number",
    "index": "index_number",
    "index_num": "index_number",
    "access_code": "access_code",
    "code": "access_code",
    "pin": "access_code",
    "access_pin": "access_code",
}

# Guards a runaway file; a school cohort is a few hundred, not a few million.
MAX_CSV_ROWS = 5000

SESSION_KEY = "student_import_rows"


def _normalise_header(name):
    key = (name or "").strip().lower().lstrip("\ufeff")
    key = key.replace(" ", "_").replace("-", "_")
    return CSV_ALIASES.get(key)


def _generate_code(taken):
    """A short, readable, unambiguous access code. Never collides."""
    import secrets
    import string

    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no I/O/0/1
    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(8))
        if code not in taken:
            taken.add(code)
            return code


def _parse_student_csv(upload):
    """Parse an uploaded CSV into a list of per-row dicts.

    Returns (rows, fatal). `fatal` is a message when the file cannot be used
    at all (wrong type, no header, missing a required column). Per-row
    problems never set fatal: they are reported row by row so a good file with
    three bad lines still creates the rest.

    Nothing is written here. This only decides what *would* happen.
    """
    import csv
    import io

    if not upload:
        return [], "Choose a CSV file to upload."

    name = (upload.name or "").lower()
    if not name.endswith((".csv", ".txt", ".tsv")):
        return [], "That file is not a CSV. Expected a .csv file."

    raw = upload.read()
    if not raw.strip():
        return [], "That file is empty."

    # utf-8-sig strips the byte-order mark Excel writes, which otherwise ends
    # up glued to the first header name and breaks column detection.
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw.decode("latin-1")
        except UnicodeDecodeError:
            return [], "That file is not readable as text. Save it as UTF-8 CSV."

    # Sheets in some locales export semicolon- or tab-separated.
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    try:
        header = next(reader)
    except StopIteration:
        return [], "That file has no header row."

    columns = [_normalise_header(h) for h in header]
    if all(c is None for c in columns):
        return [], (
            "No recognisable columns. The header must include a name column "
            "and an index number column (e.g. full_name,index_number,access_code)."
        )

    missing = [label for label in ("full_name", "index_number")
               if label not in columns]
    if missing:
        return [], "The file is missing a required column: %s." % ", ".join(missing)

    existing = set(Student.objects.values_list("index_number", flat=True))
    taken_codes = set()
    seen_index = set()

    rows = []
    for line_no, raw_row in enumerate(reader, start=2):
        if not any((cell or "").strip() for cell in raw_row):
            continue  # blank line
        if len(rows) >= MAX_CSV_ROWS:
            return [], (
                "That file has more than %d rows. Split it into smaller files."
                % MAX_CSV_ROWS
            )

        values = {}
        for position, key in enumerate(columns):
            if key and key not in values:
                values[key] = raw_row[position].strip() if position < len(raw_row) else ""

        row = {
            "line": line_no,
            "full_name": values.get("full_name", ""),
            "index_number": values.get("index_number", ""),
            "access_code": values.get("access_code", ""),
            "status": "new",
            "reason": "",
        }
        rows.append(row)

        name = row["full_name"]
        index = row["index_number"]
        code = row["access_code"]

        if not name or not index:
            row["status"] = "error"
            row["reason"] = "name and index number are both required"
            continue
        if len(name) > Student._meta.get_field("full_name").max_length:
            row["status"] = "error"
            row["reason"] = "name is longer than %d characters" % Student._meta.get_field("full_name").max_length
            continue
        if len(index) > Student._meta.get_field("index_number").max_length:
            row["status"] = "error"
            row["reason"] = "index number is longer than %d characters" % Student._meta.get_field("index_number").max_length
            continue
        if len(code) > Student._meta.get_field("access_code").max_length:
            row["status"] = "error"
            row["reason"] = "access code is longer than %d characters" % Student._meta.get_field("access_code").max_length
            continue

        # Duplicate inside the same file: the second one is the mistake.
        if index in seen_index:
            row["status"] = "error"
            row["reason"] = "index number %s appears twice in this file" % index
            continue
        seen_index.add(index)

        # Already in the database: skip, never overwrite.
        if index in existing:
            row["status"] = "skip"
            row["reason"] = "a student with this index number already exists"
            continue

        if not code:
            code = _generate_code(taken_codes)
            row["access_code"] = code
            row["generated"] = True

    return rows, None


@login_required
def student_import(request):
    """Bulk-create students from a CSV, with a preview before anything is saved.

    Flow: upload -> parse -> preview (created / skipped / errored) -> confirm.
    A row whose index number already exists is skipped and reported; it is
    never overwritten. Rows with problems are left out and listed by line
    number, so one bad line does not block the rest of the file.
    """
    from django.db import transaction

    if request.method == "GET" and request.GET.get("template") == "csv":
        sample = (
            "full_name,index_number,access_code\r\n"
            "Ama Mensah,1234567890,\r\n"
            "Kwame Boateng,1234567891,WIS4K7P\r\n"
        )
        response = HttpResponse(sample, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="student_import_template.csv"'
        return response

    # ---- step 3: confirm ----
    if request.method == "POST" and request.POST.get("confirm"):
        rows = request.session.pop(SESSION_KEY, None) or []
        if not rows:
            messages.error(
                request,
                "That upload has expired. Upload the file again to continue.",
            )
            return redirect("student_import")

        created, skipped, failed = [], [], []
        with transaction.atomic():
            for row in rows:
                if row.get("status") != "new":
                    (skipped if row.get("status") == "skip" else failed).append(row)
                    continue

                index = row["index_number"]
                # Re-check at write time: a duplicate may have been created
                # between the preview and the confirmation.
                if Student.objects.filter(index_number=index).exists():
                    row["status"] = "skip"
                    row["reason"] = "index number already exists"
                    skipped.append(row)
                    continue

                Student.objects.create(
                    full_name=row["full_name"],
                    index_number=index,
                    access_code=row["access_code"],
                )
                created.append(row)

        messages.success(
            request,
            "Imported %d student(s). Skipped %d, rejected %d."
            % (len(created), len(skipped), len(failed)),
        )
        if created:
            generated = [r for r in created if r.get("generated")]
            if generated:
                messages.info(
                    request,
                    "%d access code(s) were generated because the file left them "
                    "blank. Open a student to read theirs." % len(generated),
                )
        if failed:
            messages.error(
                request,
                "Lines not imported: %s"
                % ", ".join(str(r["line"]) for r in failed[:20]),
            )
        return redirect("student_list")

    # ---- step 2: parse and preview ----
    if request.method == "POST":
        rows, fatal = _parse_student_csv(request.FILES.get("file"))
        if fatal:
            messages.error(request, fatal)
            return redirect("student_import")

        if not rows:
            messages.error(request, "That file has a header but no data rows.")
            return redirect("student_import")

        request.session[SESSION_KEY] = rows
        context = {
            "rows": rows,
            "new_count": sum(1 for r in rows if r["status"] == "new"),
            "skip_count": sum(1 for r in rows if r["status"] == "skip"),
            "error_count": sum(1 for r in rows if r["status"] == "error"),
        }
        return render(request, "student/student_import.html", context)

    # ---- step 1: upload form ----
    return render(request, "student/student_import.html", {"rows": None})

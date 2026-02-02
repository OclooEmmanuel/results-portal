from django.shortcuts import render, redirect, get_object_or_404
from .models import Student, Result
from django.contrib import messages
from django.db.models import Q

def home(request):
    return render(request, 'home.html')

#--------------------------------------student views-----------------------------

def student_list(request):
    students = Student.objects.all()
    return render(request, "student/student_list.html", {"students": students})


def student_detail(request, indexnumber):

    pass  # Placeholder for student detail view


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




def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        try:
            student.full_name = request.POST.get("full_name")
            student.index_number = request.POST.get("index_number")
            student.access_code = request.POST.get("access_code")

            if request.FILES.get("photo"):
                student.FILES.get["photo"]

            student.save()
            messages.success(request, "Student details updated successfully")
        except Exception as e:
            messages.error(request, f"Error updating student: {str(e)}")

        return redirect("student_list")

    # If GET request, return to the list page
    return redirect("student_list")





def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        student.delete()
        messages.success(request, f"Student {student.full_name} deleted successfully!")
        return redirect("student_list")

    # If GET request, render a confirmation page
    return render(request, "student/delete_student.html", {"student": student})




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



def add_subject_marks(request):
    students = Student.objects.all().order_by("index_number")

    subjects = [
        ("maths", "Mathematics"),
        ("english", "English"),
        ("science", "Science"),
        ("social_studies", "Social Studies"),
        ("rme", "RME"),
        ("computing", "Computing"),
        ("carear_tech", "Career Tech"),
        ("cad", "CAD"),
        ("asante_twi", "Asante Twi"),
        ("french", "French"),
    ]

    if request.method == "POST":
        student_id = request.POST.get("student")
        mock_number = request.POST.get("mock_number")

        if Result.objects.filter(student_id=student_id, mock_number=mock_number).exists():
            messages.error(request, "Results for this mock already exist.")
            return redirect("add_subject_marks")

        Result.objects.create(
            student_id=student_id,
            mock_number=mock_number,
            maths=request.POST.get("maths"),
            english=request.POST.get("english"),
            science=request.POST.get("science"),
            social_studies=request.POST.get("social_studies"),
            rme=request.POST.get("rme"),
            computing=request.POST.get("computing"),
            carear_tech=request.POST.get("carear_tech"),
            cad=request.POST.get("cad"),
            asante_twi=request.POST.get("asante_twi"),
            french=request.POST.get("french"),
        )

        messages.success(request, "Results saved successfully.")
        return redirect("add_subject_marks")

    return render(
        request,
        "results/add_subject_marks.html",
        {
            "students": students,
            "subjects": subjects,
        }
    )



def edit_result(request, result_id):
    result = get_object_or_404(Result, id=result_id)

    if request.method != "POST":
        return redirect("manage_results")

    fields = [
        "maths", "english", "science", "rme",
        "computing", "carear_tech", "cad"
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
def get_grade(score):
    """
    Grade Scale (1–9)
    """
    if score >= 85:
        return 1
    elif score >= 80:
        return 2
    elif score >= 75:
        return 3
    elif score >= 70:
        return 4
    elif score >= 60:
        return 5
    elif score >= 50:
        return 6
    elif score >= 45:
        return 7
    elif score >= 40:
        return 8
    else:
        return 9


def get_grade_remark(grade):
    """
    Official Interpretation
    """
    remarks = {
        1: "Highest",
        2: "Higher",
        3: "High",
        4: "High Average",
        5: "Average",
        6: "Low Average",
        7: "Low",
        8: "Lower",
        9: "Lowest",
    }
    return remarks.get(grade, "")




def student_results(request,):
    student_id = request.session.get("student_id")

    if not student_id:
        return redirect("check_results")

    student = get_object_or_404(Student, id=student_id)

    # Get mock from URL
    mock_number = request.GET.get("mock")

    # Get all available mocks for this student
    available_mocks = (
        Result.objects
        .filter(student=student)
        .values_list("mock_number", flat=True)
        .distinct()
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

    subjects = [
        ("Mathematics", result.maths),
        ("English Language", result.english),
        ("Integrated Science", result.science),
        ("Social Studies", result.social_studies),
        ("R.M.E", result.rme),
        ("Computing", result.computing),
        ("Career Technology", result.carear_tech),
        ("Creative Arts & Design", result.cad),
        ("Asante Twi", result.asante_twi),
        ("French", result.french),
    ]

    subject_results = []
    total_score = 0
    aggregate = 0

    for subject, score in subjects:
        grade = get_grade(score)
        remark = get_grade_remark(grade)

        total_score += score
        aggregate += grade

        subject_results.append({
            "subject": subject,
            "score": score,
            "grade": grade,
            "remark": remark,
        })

    average = round(total_score / len(subjects), 2)
    overall_result = "PASS" if average >= 50 else "FAIL"

    context = {
        "student": student,
        "mock_number": mock_number,
        "subjects": subject_results,
        "total": total_score,
        "average": average,
        "aggregate": aggregate,
        "overall_result": overall_result,
    }

    return render(request, "results/student_results.html", context )


# ---------------------------------------------------------

def view_student_mock(request):
    # Get student + mock from URL
    student_id = request.GET.get("student")
    mock_number = request.GET.get("mock")

    # Safety check
    if not student_id:
        return redirect("check_results")

    student = get_object_or_404(Student, id=student_id)

    # Fetch result
    result = get_object_or_404(
        Result,
        student=student,
        mock_number=mock_number
    )

    subjects = [
        ("Mathematics", result.maths),
        ("English Language", result.english),
        ("Integrated Science", result.science),
        ("Social Studies", result.social_studies),
        ("R.M.E", result.rme),
        ("Computing", result.computing),
        ("Career Technology", result.carear_tech),
        ("Creative Arts & Design", result.cad),
        ("Asante Twi", result.asante_twi),
        ("French", result.french),
    ]

    subject_results = []
    total_score = 0
    aggregate = 0

    for subject, score in subjects:
        grade = get_grade(score)
        remark = get_grade_remark(grade)

        total_score += score
        aggregate += grade

        subject_results.append({
            "subject": subject,
            "score": score,
            "grade": grade,
            "remark": remark,
        })

    average = round(total_score / len(subjects), 2)
    overall_result = "PASS" if average >= 50 else "FAIL"

    context = {
        "student": student,
        "mock_number": mock_number,
        "subjects": subject_results,
        "total": total_score,
        "average": average,
        "aggregate": aggregate,
        "overall_result": overall_result,
    }

    return render(request, "results/admin_student_results.html", context)

def delete_mock_result(request, result_id):
    result = get_object_or_404(Result, id=result_id)

    if request.method == "POST":
        result.delete()
        messages.success(request, "Mock result deleted successfully.")
        return redirect("manage_results")

    # If someone tries GET directly, just redirect safely
    return redirect("manage_results")

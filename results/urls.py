from django.contrib import admin
from django.urls import path
from results import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path("", views.home, name="home"),

#student detail path
   #     path('student/<int:index_number>/', views.student_detail, name='student_detail'),
    path('student/', views.student_list, name='student_list'),
    path("student/add/", views.add_student, name="add_student"),
    path("student/edit/<int:student_id>/", views.edit_student, name="edit_student"),
    path("student/delete/<int:student_id>/", views.delete_student, name="delete_student"),


#reults access paths
    path('result/slip', views.student_results, name='student_results'),
    path('result/check/', views.check_results, name='check_results'),
    path('result/add/', views.add_subject_marks, name='add_subject_marks'),
    #------------------------------------------------------------------------
    path('result/manage/', views.manage_results, name='manage_results'),
    path('result/edit/<int:result_id>/', views.edit_result, name='edit_result'),
    # path("result/<int:student_id>/<str:mock_number>/", views.view_student_mock, name="view_student_mock")
    path("result/view/", views.view_student_mock, name="view_student_mock"),
    path("result/delete/<int:result_id>/", views.delete_mock_result, name="delete_mock_result"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

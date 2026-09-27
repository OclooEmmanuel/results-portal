from django.urls import path
from students import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # path("", views.home, name="home"),

#student detail path
   #     path('student/<int:index_number>/', views.student_detail, name='student_detail'),
    path('student/list', views.student_list, name='student_list'),
    path("student/add/", views.add_student, name="add_student"),
    path("student/import/", views.student_import, name="student_import"),
    path("student/edit/<int:student_id>/", views.edit_student, name="edit_student"),
    path("student/delete/<int:student_id>/", views.delete_student, name="delete_student"),
    ]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

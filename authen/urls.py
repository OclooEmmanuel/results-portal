from django.urls import path
from .views import *


urlpatterns= [
    path('register/',register_view , name='register'),
    path('login/', admin_login, name='login'),
    path('logout/', admin_logout, name='logout'),
]

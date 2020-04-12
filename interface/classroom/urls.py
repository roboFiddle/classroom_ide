from django.urls import path
from django.conf.urls import url
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('process', views.home_process, name='home_process'),
    path('class/<int:class_id>', views.class_info, name='class_info'),
    path('class_process/<int:class_id>', views.class_process, name='class_process'),
    url(r'^signup/', views.signup, name="register")
]
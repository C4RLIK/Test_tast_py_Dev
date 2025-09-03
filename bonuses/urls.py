from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('download-report/', views.download_report, name='download_report'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
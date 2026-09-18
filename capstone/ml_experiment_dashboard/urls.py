from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('', views.index, name='index'),
    path('history/', views.history, name='history'),
    path('experiment/<int:experiment_id>/', views.run_experiment, name='run_experiment'),
]
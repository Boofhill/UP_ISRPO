from django.urls import path
from . import views

urlpatterns = [

    path('', views.dashboard, name='dashboard'),
    path('requests/', views.request_list, name='request_list'),
    path('requests/create/', views.request_create, name='request_create'),
    path('requests/<int:pk>/', views.request_detail, name='request_detail'),
    path('requests/<int:pk>/update/', views.request_update, name='request_update'),
    path('requests/<int:pk>/delete/', views.request_delete, name='request_delete'),
    path('requests/<int:pk>/assign/', views.assign_master, name='assign_master'),
    path('requests/<int:pk>/add-comment/', views.add_comment, name='add_comment'),


    path('admin/users/', views.user_list, name='user_list'),
    path('admin/users/create/', views.user_create, name='user_create'),
    path('admin/users/<int:pk>/update/', views.user_update, name='user_update'),
    path('admin/users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('admin/stats/', views.admin_stats, name='admin_stats'),
]
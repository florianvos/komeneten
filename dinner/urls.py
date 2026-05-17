from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/confirm/', views.confirm_date_view, name='confirm_date'),
    path('dinner/<int:pk>/', views.dinner_detail, name='dinner_detail'),
    path('dinner/<int:pk>/tease/', views.menu_teaser_view, name='menu_teaser'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
]

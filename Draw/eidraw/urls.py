from django.urls import path
from django.views.i18n import set_language
from .import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('draw/<str:user_id>/', views.draw_view, name='draw'),
    path('result/<int:person_id>/', views.result_view, name='result'),
    path('i18n/setlang/', set_language, name='set_language'),
]
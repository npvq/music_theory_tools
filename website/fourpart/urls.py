from django.urls import path

from . import views

app_name = 'fourpart'
urlpatterns = [
	path('', views.landing, name='index')
]
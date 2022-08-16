from django.shortcuts import render
from django.views import generic

def home_view(request):
	return render(request, 'pages/index.html')
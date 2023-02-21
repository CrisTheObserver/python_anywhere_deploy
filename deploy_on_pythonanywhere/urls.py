"""deploy_on_pythonanywhere URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from deploy_on_pythonanywhere import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.update_csv_view),
    path('show_audio/', views.show_audio_view),
    path('historical/', views.historical_csv_view),
    path('download_file/', views.download_file),
    path('hourly_graph/', views.hourly_graph_view),
    path('historical_graph/', views.historical_graph_view),
    path('display_hourly_graph/', views.display_hourly_graph_view),
    path('display_historical_graph/', views.display_historical_graph_view),
    path('user_list/', views.user_list_view),
    path('user_info/', views.user_info_view),
    path('upload/', views.upload_audio_view),
    path('web_historical/', views.web_historical_csv_view),
]

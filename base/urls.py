"""djanglang URL Configuration

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
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('add_source/', views.create_db_form, name='add_source'),  # To display the source addition form
    path('create_db/', views.create_db, name='create_db'),  # To handle the form submission and initiate the database creation process
    path('db_status/', views.db_status, name='db_status'),  # endpoint to check build status
    path('build_db/', views.build_db, name='build_db'),  # New endpoint to trigger DB building
]

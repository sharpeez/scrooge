"""scrooge URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', i'nclude('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from recoup.views import HomePageView, BillView, DUCReport

admin.site.site_header = HomePageView.title
admin.site.site_name = HomePageView.title

urlpatterns = [
    url(r'^$', HomePageView.as_view()),
    url(r'^bill', BillView.as_view()),
    url(r'^reports/DUCReport.xlsx', DUCReport),
    url(r'^admin/', admin.site.urls),
]

from django.urls import path
from django.contrib import admin
from recoup.views import HomePageView, BillView, DUCReport, HealthCheckView

admin.site.site_header = HomePageView.title
admin.site.site_name = HomePageView.title

urlpatterns = [
    path('', HomePageView.as_view()),
    path('bill', BillView.as_view()),
    path('reports/DUCReport.xlsx', DUCReport),
    path('healthcheck', HealthCheckView.as_view()),
    path('admin/', admin.site.urls),
]

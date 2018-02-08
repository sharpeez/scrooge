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

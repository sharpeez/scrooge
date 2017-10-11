from django.db.models import Sum
from django.views.generic.base import TemplateView
from django.utils import timezone

from djqscsv import render_to_csv_response

from recoup import models

class HomePageView(TemplateView):
    template_name = "home.html"
    title = "Scrooge Cost DB"

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)
        context["site_header"], context["site_title"] = self.title, self.title
        context["year"] = models.FinancialYear.objects.first()
        return context

class BillView(TemplateView):
    template_name = "bill.html"

    def get_context_data(self, **kwargs):
        context = super(BillView, self).get_context_data(**kwargs)
        division = models.Division.objects.get(pk=int(self.request.GET["division"]))
        context.update({
            "division": division,
            "created": timezone.now().date,
        })
        return context
    
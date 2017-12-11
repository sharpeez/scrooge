from django.db.models import Sum
from django.views.generic.base import TemplateView
from django.http import HttpResponse
from django.utils import timezone
from decimal import Decimal
import io
import xlsxwriter

from recoup import models

class HomePageView(TemplateView):
    template_name = "home.html"
    title = "Scrooge Cost DB"

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)
        context["site_header"], context["site_title"] = self.title, self.title
        context["year"] = models.FinancialYear.objects.first()
        context["enduser_cost"] = round(sum([e.cost_estimate() for e in models.EndUserService.objects.all()]), 2)
        context["platform_cost"] = round(sum([p.cost_estimate() for p in models.Platform.objects.all()]), 2)
        context["unallocated_cost"] = context["year"].cost_estimate() - context["enduser_cost"] - context["platform_cost"]
        return context

class BillView(TemplateView):
    template_name = "bill.html"

    def get_context_data(self, **kwargs):
        context = super(BillView, self).get_context_data(**kwargs)
        division = models.Division.objects.get(pk=int(self.request.GET["division"]))
        services = division.enduserservice_set.all()

        for service in services:
            service.cost_estimate_display = round(Decimal(division.user_count) / Decimal(service.total_user_count()) * service.cost_estimate(), 2)
        context.update({
            "division": division,
            "services": services,
            "created": timezone.now().date
        })
        return context
    
def DUCReport(request):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=DUCReport.xlsx'
    workbook = xlsxwriter.Workbook(response, {'in_memory': True})
    workbook.close()
    return response


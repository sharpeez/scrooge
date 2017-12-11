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
    with xlsxwriter.Workbook(response, {'in_memory': True}) as workbook:
        bold = workbook.add_format({'bold': True})
        money = workbook.add_format({'num_format': '$#,##0.00'})
        # it user account workbook
        staff = workbook.add_worksheet("IT User Accounts")
        staff.write_row("A1", ("Division / Cost Centre", "IT User Accounts", "% Total"), bold)
        staff.set_column('A:A', 40)
        staff.set_column('B:C', 20)
        row = 1
        for division in models.Division.objects.all():
            staff.write_row(row, 0, ["Tier 2 Structure " + division.name, division.user_count, division.user_count_percentage()])
            row += 1
            for cc in division.costcentre_set.all():
                staff.write_row(row, 0, ["Cost Centre " + cc.name, cc.user_count, cc.user_count_percentage()])
                row += 1
        enduser = workbook.add_worksheet("End-User Services")
        itsystems = workbook.add_worksheet("Business IT Systems")
        invoice = workbook.add_worksheet("Invoice")
        bills = workbook.add_worksheet("Bills")
        contracts = workbook.add_worksheet("Contracts")

    return response


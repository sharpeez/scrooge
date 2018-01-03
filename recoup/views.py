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
        pct = workbook.add_format({'num_format': '0.00%'})
        # it user account workbook
        staff = workbook.add_worksheet("IT User Accounts")
        staff.write_row("A1", ("Division (bold) / Cost Centre", "IT User Accounts", "% Total"))
        staff.set_row(0, None, bold)
        row = 1
        for division in models.Division.objects.all():
            staff.write_row(row, 0, [division.name, division.user_count, division.user_count_percentage()])
            staff.set_row(row, None, bold)
            row += 1
            for cc in division.costcentre_set.all():
                staff.write_row(row, 0, [cc.name, cc.user_count, cc.user_count_percentage()])
                row += 1
        staff.set_column('A:A', 30)
        staff.set_column('B:C', 20)
        # End User services
        enduser = workbook.add_worksheet("End-User Services")
        enduser.write_row("A1", ("End-User Service", "Cost"))
        enduser.set_row(0, None, bold)
        row = 1
        for service in models.EndUserService.objects.all():
            enduser.write_row(row, 0, [service.name, service.cost_estimate()])
            row += 1
        enduser.write_row(row, 0, ["Subtotal", "=SUM(B2:B{})".format(row)])
        enduser.set_column('A:A', 40)
        enduser.set_column('B:B', 20, money)
        # IT Systems
        itsystems = workbook.add_worksheet("Business IT Systems")
        itsystems.write_row("A1", ("Division (bold) / Cost Centre", "IT System", "Cost", "% Total"))
        itsystems.set_row(0, None, bold)
        platform_cost = round(sum([p.cost_estimate() for p in models.Platform.objects.all()]), 2)
        itsystems.write_row("A2", ("Total", "All IT Systems", platform_cost, 1), bold)
        itsystems.set_row(1, None, bold)
        row = 2
        for division in models.Division.objects.all():
            itsystems.write_row(row, 0, [division.name, "Subtotal", division.system_cost_estimate() , "=C{}/C2".format(row+1)])
            itsystems.set_row(row, None, bold)
            row += 1
            for system in division.itsystem_set.filter(depends_on__isnull=False).distinct():
                itsystems.write_row(row, 0, [system.cost_centre, system.__str__(), system.cost_estimate(), "=C{}/C2".format(row+1)])
                row += 1
        itsystems.set_column('A:B', 40)
        itsystems.set_column('C:C', 20, money)
        itsystems.set_column('D:D', 20, pct)
        # invoice
        invoice = workbook.add_worksheet("Invoice")
        invoice.write_row("A1", ("Division (bold) / Cost Centre", "IT User Accounts", "End User Services", "Business IT Systems", "Total DUC Cost"))
        invoice.set_row(0, None, bold)
        row = 1
        divrow = 1
        for division in models.Division.objects.all():
            invoice.write_row(row, 0, [division.name, division.user_count, division.enduser_estimate(), division.system_cost_estimate(), "=SUM(C{},D{})".format(row+1, row+1)])
            invoice.set_row(row, None, bold)
            divrow = row
            row += 1
            for cc in division.costcentre_set.all():
                invoice.write_row(row, 0, [cc.name, cc.user_count, "=B{}*C{}/B{}".format(row+1, divrow+1, divrow+1), "=B{}*D{}/B{}".format(row+1, divrow+1, divrow+1), "=SUM(C{},D{})".format(row+1, row+1)])
                row += 1
        invoice.set_column('A:A', 30)
        invoice.set_column('B:B', 20)
        invoice.set_column('C:E', 20, money)
        bills = workbook.add_worksheet("Bills")
        contracts = workbook.add_worksheet("Contracts")

    return response


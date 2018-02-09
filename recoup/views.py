from django.views.generic.base import TemplateView
from django.http import HttpResponse
from django.utils import timezone
from decimal import Decimal
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
        bold_big_font = workbook.add_format({'bold': True, 'align': 'center'})
        bold_big_font.set_font_size(14)
        bold_italic = workbook.add_format({'bold': True, 'italic': True})
        pct = workbook.add_format({'num_format': '0.00%'})
        pct_bold = workbook.add_format({'num_format': '0.00%', 'bold': True})
        pct_bold_italic = workbook.add_format({'num_format': '0.00%', 'bold': True, 'italic': True})
        money = workbook.add_format({'num_format': '#,##0.00'})
        money_bold = workbook.add_format({'num_format': '#,##0.00', 'bold': True})
        money_bold_italic = workbook.add_format({'num_format': '#,##0.00', 'bold': True, 'italic': True})

        # Computer user account worksheet
        staff = workbook.add_worksheet("IT User Accounts")
        staff.write_row("A1", ("Division / Cost Centre", "Computer User Accounts", "% Total"))
        staff.set_row(0, None, bold_big_font)
        user_count = 0
        row = 2
        for division in models.Division.objects.all():
            staff.write(row, 0, division.name, bold)
            staff.write(row, 1, division.user_count, bold)
            staff.write(row, 2, division.user_count_percentage() / 100, pct_bold)
            user_count += division.user_count
            row += 1
            for cc in division.costcentre_set.all():
                staff.write_row(row, 0, [cc.name, cc.user_count, cc.user_count_percentage() / 100])
                row += 1
        staff.set_column('A:A', 34)
        staff.set_column('B:B', 27)
        staff.set_column('C:C', 20, pct)
        # Insert total row at the top
        staff.write('A2', 'Total', bold_italic)
        staff.write('B2', user_count, bold_italic)
        staff.write('C2', 1, pct_bold_italic)

        # End User services worksheet
        enduser = workbook.add_worksheet("End-User Services")
        enduser.write_row("A1", ("End-User Services", "Estimated Cost ($)"))
        enduser.set_row(0, None, bold_big_font)
        enduser_total = 0
        row = 2
        for service in models.EndUserService.objects.all():
            enduser_total += service.cost_estimate()
            enduser.write_row(row, 0, [service.name, service.cost_estimate()])
            row += 1
        enduser.set_column('A:A', 40)
        enduser.set_column('B:B', 20, money)
        # Insert total row at the top
        enduser.write('A2', 'Total', bold_italic)
        enduser.write('B2', enduser_total, money_bold_italic)

        # Business IT systems worksheet
        itsystems = workbook.add_worksheet("Business IT Systems")
        itsystems.write_row("A1", ("Division / Cost Centre", "Business IT Systems", "Estimated Cost ($)", "% Total"))
        itsystems.set_row(0, None, bold_big_font)
        # Insert total row at the top
        platform_cost = round(sum([p.cost_estimate() for p in models.Platform.objects.all()]), 2)
        itsystems.write('A2', 'Total', bold_italic)
        itsystems.write('B2', 'All IT Systems', bold_italic)
        itsystems.write('C2', platform_cost, money_bold_italic)
        itsystems.write('D2', 1, pct_bold_italic)
        row = 2
        for division in models.Division.objects.all():
            itsystems.write(row, 0, division.name, bold)
            itsystems.write(row, 1, 'Subtotal', bold)
            itsystems.write(row, 2, division.system_cost_estimate(), money_bold)
            itsystems.write(row, 3, '=C{}/C2'.format(row + 1), pct_bold)
            row += 1
            for system in division.itsystem_set.filter(depends_on__isnull=False).distinct():
                itsystems.write_row(row, 0, [system.cost_centre.name, system.__str__(), system.cost_estimate(), "=C{}/C2".format(row + 1)])
                row += 1
        itsystems.set_column('A:A', 34)
        itsystems.set_column('B:B', 67)
        itsystems.set_column('C:C', 20, money)
        itsystems.set_column('D:D', 15, pct)

        # Statement worksheet
        invoice = workbook.add_worksheet('Statement')
        invoice.write_row("A1", ("Division / Cost Centre", "Computer User Accounts", "End User Services ($)", "Business IT Systems ($)", "Total DUC Estimated Cost ($)"))
        invoice.set_row(0, None, bold_big_font)
        # Insert total row at the top
        invoice.write('A2', 'Total', bold_italic)
        invoice.write('B2', user_count, bold_italic)
        invoice.write('C2', enduser_total, money_bold_italic)
        invoice.write('D2', platform_cost, money_bold_italic)
        invoice.write('E2', enduser_total + platform_cost, money_bold_italic)
        row = 2
        divrow = 2
        for division in models.Division.objects.all():
            invoice.write(row, 0, division.name, bold)
            invoice.write(row, 1, division.user_count, bold)
            invoice.write(row, 2, division.enduser_estimate(), money_bold)
            invoice.write(row, 3, division.system_cost_estimate(), money_bold)
            invoice.write(row, 4, division.enduser_estimate() + division.system_cost_estimate(), money_bold)
            divrow = row
            row += 1
            for cc in division.costcentre_set.all():
                invoice.write_row(row, 0, [cc.name, cc.user_count, "=B{}*C{}/B{}".format(row + 1, divrow + 1, divrow + 1), cc.system_cost_estimate(), "=SUM(C{},D{})".format(row + 1, row + 1)])
                row += 1
        invoice.set_column('A:A', 34)
        invoice.set_column('B:B', 27)
        invoice.set_column('C:D', 25, money)
        invoice.set_column('E:E', 32, money)
        workbook.add_worksheet("Bills")
        workbook.add_worksheet("Contracts")

    return response

from django.db.models import Sum
from django.views.generic.base import TemplateView

from djqscsv import render_to_csv_response

from scrooge.models import CostBreakdown, UserGroup

# current fin year only
cbqs = CostBreakdown.objects.filter(cost__finyear=2017)

class HomePageView(TemplateView):
    template_name = "home.html"
    title = "Scrooge Cost DB"

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)
        context["site_header"], context["site_title"] = self.title, self.title
        context["servicepools"] = cbqs.values("service_pool").annotate(Sum("finyear_percentage")).annotate(Sum("predicted_cost")).order_by("-finyear_percentage__sum").distinct()
        return context

def cost_breakdown_report(request):
    CostBreakdown.update_calculations()
    return render_to_csv_response(cbqs.values())

def user_group_report(request):
    return render_to_csv_response(UserGroup.objects.values())
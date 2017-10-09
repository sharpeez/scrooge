from django.db.models import Sum
from django.views.generic.base import TemplateView
from django.utils import timezone

from djqscsv import render_to_csv_response

from scrooge.models import CostBreakdown, UserGroup, Cost

# current fin year only
cbqs = CostBreakdown.objects.filter(cost__finyear=2017)
costqs = Cost.objects.filter(finyear=2017)

class HomePageView(TemplateView):
    template_name = "home.html"
    title = "Scrooge Cost DB"

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)
        context["site_header"], context["site_title"] = self.title, self.title
        context["total_cost"] = costqs.aggregate(Sum("predicted_cost"))["predicted_cost__sum"]
        context["servicepools"] = cbqs.values("service_pool").annotate(Sum("finyear_percentage")).annotate(Sum("predicted_cost")).order_by("-finyear_percentage__sum").distinct()
        context["usergroups"] = UserGroup.objects.all()
        return context

class BillView(TemplateView):
    template_name = "bill.html"

    def get_context_data(self, **kwargs):
        context = super(BillView, self).get_context_data(**kwargs)
        usergroup = UserGroup.objects.get(pk=int(self.request.GET["usergroup"]))
        context.update({
            "usergroup": usergroup,
            "created": timezone.now().date,
        })
        return context
    

def cost_breakdown_report(request):
    CostBreakdown.update_calculations()
    return render_to_csv_response(cbqs.values())

def user_group_report(request):
    return render_to_csv_response(UserGroup.objects.values())

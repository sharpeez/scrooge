from datetime import date
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.html import format_html


def field_sum(queryset, fieldname):
    return queryset.aggregate(models.Sum(fieldname))["{}__sum".format(fieldname)]


class CostSummary(models.Model):
    """
    Maintains some fields for summarising costs for an object
    """
    def __str__(self):
        return self.name

    def get_cost_queryset(self):
        """
        Override with appropriate filtering across bills or costs
        """
        return self.__class__.objects.none()

    def cost(self):
        return field_sum(self.get_cost_queryset(), "cost") or Decimal(0)

    def cost_estimate(self):
        return field_sum(self.get_cost_queryset(), "cost_estimate") or Decimal(0)

    @property
    def year(self):
        return FinancialYear.objects.first()

    def cost_percentage(self):
        year_cost = self.year.cost()
        if year_cost == Decimal(0):
            return 0
        return round(self.cost() / year_cost * 100, 2)

    cost_percentage.short_description = "Cost/FY %"

    def cost_estimate_percentage(self):
        year_cost_est = self.year.cost_estimate()
        if year_cost_est == Decimal(0):
            return 0
        return round(self.cost_estimate() / year_cost_est * 100, 2)

    cost_estimate_percentage.short_description = "Estimate/FY %"

    class Meta:
        abstract = True
        ordering = ('name',)


class Contract(CostSummary):
    vendor = models.CharField(max_length=320)
    brand = models.CharField(max_length=320, default="N/A")
    reference = models.CharField(max_length=320, default="N/A")
    invoice_period = models.CharField(max_length=320, default="Annual")
    start = models.DateField(default=date.today)
    end = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def get_cost_queryset(self):
        return self.bill_set.filter(active=True)

    def __str__(self):
        return "{} ({})".format(self.vendor, self.reference)

    class Meta:
        ordering = ('vendor',)


class FinancialYear(CostSummary):
    """
    Maintains a running total for the full cost of a year
    Totals are used to calculate percentage values of costs for invoicing
    """
    start = models.DateField()
    end = models.DateField()

    def get_cost_queryset(self):
        return self.bill_set.filter(active=True)

    def __str__(self):
        return "{}/{}".format(self.start.year, self.end.year)

    class Meta:
        ordering = ("end",)


class Bill(models.Model):
    """
    As Bills are updated they should propagate totals for the financial year
    """
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT)
    name = models.CharField(max_length=320, help_text="Product or Service")
    description = models.TextField(default="N/A")
    comment = models.TextField(blank=True, default="")
    quantity = models.CharField(max_length=320, default="1")
    year = models.ForeignKey(FinancialYear, on_delete=models.PROTECT)
    renewal_date = models.DateField(null=True, blank=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cost_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    active = models.BooleanField(default=True)

    def allocated(self):
        return field_sum(self.cost_items.all(), "percentage") or 0

    def post_save(self):
        # recalculate child cost values
        for cost in EndUserCost.objects.filter(bill=self):
            cost.save()
        for cost in ITPlatformCost.objects.filter(bill=self):
            cost.save()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("-cost_estimate",)


class ServicePool(CostSummary):
    """
    ServicePool used for reporting
    """
    name = models.CharField(max_length=320, editable=False, unique=True)


class Cost(CostSummary):
    name = models.CharField(max_length=320)
    bill = models.ForeignKey(Bill, related_name="cost_items", on_delete=models.PROTECT)
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)])
    service_pool = models.ForeignKey(ServicePool, related_name="cost_items", on_delete=models.PROTECT)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    cost_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)

    def pre_save(self):
        if not self.bill.active:
            self.cost, self.cost_estimate = 0, 0
        self.cost = self.bill.cost * self.percentage / Decimal(100)
        self.cost_estimate = self.bill.cost_estimate * self.percentage / Decimal(100)

    class Meta:
        ordering = ("-percentage",)


class Division(CostSummary):
    """
    A Tier 2 Division in the department
    """
    name = models.CharField(max_length=320)
    user_count = models.PositiveIntegerField(default=0)
    position = models.PositiveIntegerField(unique=True)

    def cc_count(self):
        return self.costcentre_set.count()

    def system_count(self):
        return self.systems_by_cc().count()

    def enduser_cost(self):
        total = Decimal(0)
        for service in self.enduserservice_set.all():
            total += round(Decimal(self.user_count) / Decimal(service.total_user_count()) * service.cost(), 2)
        return total

    def enduser_estimate(self):
        total = Decimal(0)
        for service in self.enduserservice_set.all():
            total += round(Decimal(self.user_count) / Decimal(service.total_user_count()) * service.cost_estimate(), 2)
        return total

    def system_cost(self):
        return sum(system.cost() for system in self.systems_by_cc().all())

    def system_cost_estimate(self):
        return sum(system.cost_estimate() for system in self.systems_by_cc().all())

    def cost(self):
        return self.enduser_cost() + self.system_cost()

    def cost_estimate(self):
        return self.enduser_estimate() + self.system_cost_estimate()

    def systems_by_cc(self):
        return self.itsystem_set.filter(systemdependency__isnull=False).order_by("cost_centre", "name").distinct()

    def bill(self):
        return format_html('<a href="/bill?division={}" target="_blank">Bill</a>', self.pk)

    def user_count_percentage(self):
        return round(self.user_count / field_sum(Division.objects.all(), 'user_count') * 100, 2)

    class Meta:
        ordering = ('position',)


class CostCentre(models.Model):
    name = models.CharField(max_length=128, unique=True)
    code = models.CharField(max_length=16, unique=True)
    division = models.ForeignKey(Division, on_delete=models.PROTECT)
    user_count = models.PositiveIntegerField(default=0)

    def systems(self):
        return self.itsystem_set.filter(systemdependency__isnull=False).distinct()

    def system_count(self):
        return self.systems().count()

    def system_cost(self):
        return sum(system.cost() for system in self.systems())

    def system_cost_estimate(self):
        return sum(system.cost_estimate() for system in self.systems())

    def user_count_percentage(self):
        return round(self.user_count / field_sum(Division.objects.all(), 'user_count') * 100, 2)

    def post_save(self):
        self.division.user_count = field_sum(self.division.costcentre_set.all(), "user_count")
        if self.division.user_count > 0:
            self.division.save()

    def __str__(self):
        return self.code

    class Meta:
        ordering = ('name',)


class EndUserService(CostSummary):
    """
    Grouping used to simplify linkages of costs to divisions, and for reporting
    """
    name = models.CharField(max_length=320)
    divisions = models.ManyToManyField(Division)

    def total_user_count(self):
        return field_sum(self.divisions, "user_count")

    def get_cost_queryset(self):
        return self.endusercost_set.filter()


class EndUserCost(Cost):
    """
    Broken down cost for end users
    """
    service = models.ForeignKey(EndUserService, on_delete=models.PROTECT)


class Platform(CostSummary):
    """
    Platform or Infrastructure IT systems depend on
    Grouping used to simplify linkages of costs to systems, and for reporting
    Note a system may have to have its own unique systemdependency
    """
    name = models.CharField(max_length=320)

    def system_count(self):
        return self.systemdependency_set.count()

    def system_weight_total(self):
        return field_sum(self.systemdependency_set, "weighting")

    def get_cost_queryset(self):
        return self.itplatformcost_set.all()

    class Meta(CostSummary.Meta):
        abstract = False
        verbose_name = "IT Platform"


class ITSystem(CostSummary):
    """
    A system owned by a division, that shares the cost of a set of service groups
    """
    system_id = models.CharField(max_length=4, unique=True)
    cost_centre = models.ForeignKey(CostCentre, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=320)
    division = models.ForeignKey(Division, on_delete=models.PROTECT)
    depends_on = models.ManyToManyField(Platform, through="SystemDependency")

    def cost(self):
        total = Decimal(0)
        for dep in self.systemdependency_set.all():
            total += dep.platform.cost() * Decimal(dep.weighting / dep.platform.system_weight_total())
        return round(total, 2)

    def cost_estimate(self):
        total = Decimal(0)
        for dep in self.systemdependency_set.all():
            total += dep.platform.cost_estimate() * Decimal(dep.weighting / dep.platform.system_weight_total())
        return round(total, 2)

    def depends_on_display(self):
        return ", ".join(str(p) for p in self.depends_on.all())

    def pre_save(self):
        self.division = self.cost_centre.division

    def __str__(self):
        return "{} (#{})".format(self.name, self.system_id)

    class Meta(CostSummary.Meta):
        ordering = ('cost_centre__name', 'name')


class SystemDependency(CostSummary):
    """
    Links a system to the platforms it uses
    """
    system = models.ForeignKey(ITSystem, on_delete=models.PROTECT)
    platform = models.ForeignKey(Platform, on_delete=models.PROTECT)
    weighting = models.FloatField(default=1)

    def post_save(self):
        self.platform.system_count = self.platform.systemdependency_set.count()
        self.platform.save()

    def __str__(self):
        return "{} depends on {}".format(self.system, self.platform)

    class Meta:
        unique_together = (("system", "platform"),)


class ITPlatformCost(Cost):
    """
    Broken down cost for IT component
    """
    platform = models.ForeignKey(Platform, on_delete=models.PROTECT)


@receiver(post_save)
def post_save_hook(sender, instance, **kwargs):
    if 'raw' in kwargs and kwargs['raw']:
        return
    if (hasattr(instance, "post_save")):
        instance.post_save()


@receiver(pre_save)
def pre_save_hook(sender, instance, **kwargs):
    if 'raw' in kwargs and kwargs['raw']:
        return
    if (hasattr(instance, "pre_save")):
        instance.pre_save()

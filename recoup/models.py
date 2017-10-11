from datetime import date
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

def field_sum(queryset, fieldname):
    return queryset.aggregate(models.Sum(fieldname))["{}__sum".format(fieldname)]

def update_costs(queryset, instance):
    """
    Convenience method to update a parent objects costs from a queryset of children
    """
    instance.cost = field_sum(queryset, "cost")
    instance.cost_estimate = field_sum(queryset, "cost_estimate")
    instance.save()

class CostSummary(models.Model):
    """
    Maintains some fields for summarising costs for an object
    """
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    cost_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)

    def __str__(self):
        return self.name

    @property
    def year(self):
        return FinancialYear.objects.first()

    def cost_percentage(self):
        if self.year.cost == Decimal(0):
            return 0
        return round(self.cost / self.year.cost * 100, 2)

    def cost_estimate_percentage(self):
        if self.year.cost_estimate == Decimal(0):
            return 0
        return round(self.cost_estimate / self.year.cost_estimate * 100, 2)

    class Meta:
        abstract = True
        ordering = ("-cost_estimate",)

class Contract(CostSummary):
    vendor = models.CharField(max_length=320)
    brand = models.CharField(max_length=320, default="N/A")
    reference = models.CharField(max_length=320, default="N/A")
    invoice_period = models.CharField(max_length=320, default="Annual")
    start = models.DateField(default=date.today)
    end = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return "{} ({})".format(self.vendor, self.reference)

class FinancialYear(CostSummary):
    """
    Maintains a running total for the full cost of a year
    Totals are used to calculate percentage values of costs for invoicing
    """
    start = models.DateField()
    end = models.DateField()

    def __str__(self):
        return "{}/{}".format(self.start.year, self.end.year)

    class Meta:
        ordering = ("end",)

class Bill(models.Model):
    """
    As Bills are updated they should propagate totals for the financial year
    """
    contract = models.ForeignKey(Contract)
    name = models.CharField(max_length=320, help_text="Product or Service")
    description = models.TextField(default="N/A")
    comment = models.TextField(blank=True, default="")
    quantity = models.CharField(max_length=320, default="1")
    year = models.ForeignKey(FinancialYear, default=FinancialYear.objects.first)
    renewal_date = models.DateField(null=True, blank=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cost_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    allocated = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], editable=False)
    active = models.BooleanField(default=True)

    def pre_save(self):
        self.allocated = field_sum(self.cost_items.all(), "percentage") or 0

    def post_save(self):
        update_costs(self.contract.bill_set.filter(active=True), self.contract)
        update_costs(self.year.bill_set.filter(active=True), self.year)
        costs = self.cost_items.all()
        if field_sum(costs, "cost") != self.cost or field_sum(costs, "cost_estimate") != self.cost_estimate:
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
    bill = models.ForeignKey(Bill, related_name="cost_items")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    service_pool = models.ForeignKey(ServicePool, related_name="cost_items")

    def pre_save(self):
        if not self.bill.active:
            self.cost, self.cost_estimate = 0, 0
        self.cost = self.bill.cost * self.percentage / Decimal(100)
        self.cost_estimate = self.bill.cost_estimate * self.percentage / Decimal(100)

    def post_save(self):
        update_costs(self.service_pool.cost_items.all(), self.service_pool)

    class Meta:
        ordering = ("-percentage",)

class Division(CostSummary):
    """
    A Tier 2 Division in the department
    """
    name = models.CharField(max_length=320)
    user_count = models.PositiveIntegerField(default=0)
    cc_count = models.PositiveIntegerField(default=0)
    system_count = models.PositiveIntegerField(default=0, editable=False)

class EndUserService(CostSummary):
    """
    Grouping used to simplify linkages of costs to divisions, and for reporting
    """
    name = models.CharField(max_length=320)
    divisions = models.ManyToManyField(Division)
    total_user_count = models.PositiveIntegerField(default=0, editable=False)

class EndUserCost(Cost):
    """
    Broken down cost for end users
    """
    service = models.ForeignKey(EndUserService)

    def post_save(self):
        update_costs(self.service.endusercost_set.all(), self.service)

class ITSystem(CostSummary):
    """
    A system owned by a division, that shares the cost of a set of service groups
    """
    system_id = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=320)
    division = models.ForeignKey(Division)

class Platform(CostSummary):
    """
    Platform or Infrastructure IT systems depend on
    Grouping used to simplify linkages of costs to systems, and for reporting
    Note a system may have to have its own unique systemdependency
    """
    name = models.CharField(max_length=320)
    system_count = models.PositiveIntegerField(default=0, editable=False)

    class Meta(CostSummary.Meta):
        abstract = False
        verbose_name = "IT Platform"

class SystemDependency(CostSummary):
    """
    Links a system to the platforms it uses
    """
    system = models.ForeignKey(ITSystem)
    platform = models.ForeignKey(Platform)
    weighting = models.FloatField(default=1)

    def post_save(self):
        self.platform.system_count = self.platform.systemdependency_set.count()

    class Meta:
        unique_together = (("system", "platform"),)

class ITPlatformCost(Cost):
    """
    Broken down cost for IT component
    """
    platform = models.ForeignKey(Platform)

    def post_save(self):
        update_costs(self.platform.itplatformcost_set.all(), self.platform)

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
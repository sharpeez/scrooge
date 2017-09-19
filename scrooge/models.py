from datetime import date
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ValidationError

FINYEAR_CHOICES = (
    (2015, '2015/16'),
    (2016, '2016/17'),
    (2017, '2017/18'),
    (2018, '2018/19'),
    (2019, '2019/20')
)

class Contract(models.Model):
    vendor = models.CharField(max_length=320)
    brand = models.CharField(max_length=320, default="N/A")
    contract = models.CharField(max_length=320, default="N/A")
    invoice_period = models.CharField(max_length=320, default="Annual")
    start = models.DateField(default=date.today)
    end = models.DateField(null=True, blank=True)

    def __str__(self):
        return "{} ({})".format(self.vendor, self.contract)

    class Meta:
        unique_together = ("vendor", "contract")

class Cost(models.Model):
    contract = models.ForeignKey(Contract)
    name = models.CharField(max_length=320, help_text="Product or Service")
    description = models.TextField(default="N/A")
    comment = models.TextField(blank=True, default="")
    quantity = models.CharField(max_length=320, default="1")
    finyear = models.IntegerField(choices=FINYEAR_CHOICES)
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    predicted_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def finyear_sum(self, fieldname):
        return Cost.objects.filter(finyear=self.finyear).aggregate(sum=models.Sum(fieldname))["sum"]

    def actual_percentage(self):
        return (100 * self.actual_cost / self.finyear_sum('actual_cost')).quantize(Decimal(10)**-2)

    def predicted_percentage(self):
        return (100 * self.predicted_cost / self.finyear_sum('predicted_cost')).quantize(Decimal(10)**-2)

    def breakdown(self):
        display = ", ".join([str(c) for c in self.costbreakdown_set.all()])
        total = self.costbreakdown_set.aggregate(total=models.Sum("percentage"))["total"]
        if total != 100:
            display = "INVALID {}%: ".format(100 - total) + display
        return display

    class Meta:
        unique_together = ("name", "finyear", "contract")
        ordering = ('-predicted_cost',)

    def __str__(self):
        return self.name

class ITSystem(models.Model):
    system_id = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=320)
    cost_data = JSONField(default=dict, encoder=DjangoJSONEncoder, editable=False)

    def __str__(self):
        return "{} - {}".format(self.system_id, self.name)

class UserGroup(models.Model):
    name = models.CharField(max_length=320)
    user_count = models.PositiveIntegerField()
    cost_data = JSONField(default=dict, encoder=DjangoJSONEncoder, editable=False)

    @classmethod
    def update_calculations(cls):
        for ug in cls.objects.all():
            ug.cost_data = [item for item in ug.costbreakdown_set.values()]
            ug.save()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('-user_count',)

def largest_user_group():
    return UserGroup.objects.first().pk

class CostBreakdown(models.Model):
    SERVICE_POOL_CHOICES = (
        ("Internal Labor", "Internal Labor"),
        ("External Labor", "External Labor"),
        ("Outside Services", "Outside Services"),
        ("Hardware", "Hardware"),
        ("Software", "Software"),
        ("Facilities and Power", "Facilities and Power"),
        ("Telecom", "Telecom"),
        ("Other", "Other"),
        ("Internal Services", "Internal Services")
    )
    cost = models.ForeignKey(Cost)
    name = models.CharField(max_length=320)
    description = models.TextField(blank=True)
    service_pool = models.CharField(max_length=64, choices=SERVICE_POOL_CHOICES)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    it_systems = models.ManyToManyField(ITSystem, blank=True, editable=False)
    user_groups = models.ManyToManyField(UserGroup, blank=True, default=largest_user_group)
    total_user_count = models.PositiveIntegerField(default=0)
    finyear_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], editable=False)
    predicted_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)

    @classmethod
    def update_calculations(cls):
        for cb in cls.objects.all():
            total = cb.cost.finyear_sum('predicted_cost')
            cb.finyear_percentage = cb.percentage / 100 * cb.cost.predicted_percentage()
            cb.predicted_cost = cb.finyear_percentage / 100 * total
            cb.total_user_count = cb.user_groups.aggregate(total=models.Sum("user_count"))["total"]
            cb.save()

    def user_groups_display(self):
        output = ",".join(self.user_groups.all())

    def __str__(self):
        return "{} ({}%)".format(self.name, self.percentage)

    class Meta:
        unique_together = ("cost", "name")
        ordering = ('-percentage',)

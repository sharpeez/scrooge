from datetime import date
from django.db import models
from django.core.validators import MaxValueValidator
from django.contrib.postgres.fields import JSONField

FINYEAR_CHOICES = (
    (2015, '2015/16'),
    (2016, '2016/17'),
    (2017, '2017/18'),
    (2018, '2018/19'),
    (2019, '2019/20')
)

class ContractReference(models.Model):
    vendor = models.CharField(max_length=320)
    brand = models.CharField(max_length=320, blank=True)
    contract = models.CharField(max_length=320)
    invoice_period = models.CharField(max_length=320, default="Annual")
    start = models.DateField(default=date.today)
    end = models.DateField(null=True, blank=True)

    def __str__(self):
        return "{} ({})".format(self.vendor, self.contract)

    class Meta:
        unique_together = ("vendor", "contract")

class Cost(models.Model):
    contract = models.ForeignKey(ContractReference)
    name = models.CharField(max_length=320, help_text="Product or Service")
    description = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    quantity = models.CharField(max_length=320, default="1")
    finyear = models.IntegerField(choices=FINYEAR_CHOICES)
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    predicted_cost = models.DecimalField(max_digits=12, decimal_places=2)
    allocated_percentage = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100)])

    def __str__(self):
        return self.name

class ITSystem(models.Model):
    system_id = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=320)
    cost_data = JSONField(default=dict)

    def __str__(self):
        return "{} - {}".format(self.system_id, self.name)

class UserGroup(models.Model):
    name = models.CharField(max_length=320)
    user_count = models.PositiveIntegerField()
    cost_data = JSONField(default=dict)

    def __str__(self):
        return self.name

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
    percentage = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100)])
    it_systems = models.ManyToManyField(ITSystem)
    user_groups = models.ManyToManyField(UserGroup)

    def __str__(self):
        return self.name

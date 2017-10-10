from datetime import date
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ValidationError

class Contract(models.Model):
    vendor = models.CharField(max_length=320)
    brand = models.CharField(max_length=320, default="N/A")
    reference = models.CharField(max_length=320, default="N/A")
    invoice_period = models.CharField(max_length=320, default="Annual")
    start = models.DateField(default=date.today)
    end = models.DateField(null=True, blank=True)

class FinancialYear(models.Model):
    """
    Maintains a running total for the full cost of a year
    Totals are used to calculate percentage values of costs for invoicing
    """
    start = models.DateField()
    end = models.DateField()
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    cost_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)

class Bill(models.Model):
    """
    As Bills are updated they should propagate totals for the financial year
    """
    contract = models.ForeignKey(Contract)
    name = models.CharField(max_length=320, help_text="Product or Service")
    description = models.TextField(default="N/A")
    comment = models.TextField(blank=True, default="")
    quantity = models.CharField(max_length=320, default="1")
    year = models.ForeignKey(FinancialYear)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cost_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0)

class ServicePool(models.Model):
    """
    ServicePool used for reporting
    """
    name = models.CharField(max_length=320)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    cost_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)

class Division(models.Model):
    """
    A Tier 2 Division in the department
    """
    name = models.CharField(max_length=320)
    user_count = models.PositiveIntegerField()
    cc_count = models.PositiveIntegerField()
    system_count = models.PositiveIntegerField(editable=False)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    cost_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)

class ServiceGroup(models.Model):
    """
    Grouping used to simplify linkages of costs to user groups, and for reporting
    """
    name = models.CharField(max_length=320)
    division = models.ForeignKey(Division)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    cost_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)

class ITSystem(models.Model):
    """
    A system owned by a division, that shares the cost of a set of service groups    
    """
    system_id = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=320)
    division = models.ForeignKey(Division)
    service_groups = models.ManyToManyField

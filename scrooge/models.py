from django.db import models
from datetime import date

FINYEAR_CHOICES = (
    ('2015', '2015/16'),
    ('2016', '2016/17'),
    ('2017', '2017/18'),
    ('2018', '2018/19'),
    ('2019', '2019/20')
)

class ContractReference(models.Model):
    vendor = models.CharField(max_length=320)
    brand = models.CharField(max_length=320, blank=True)
    contract = models.CharField(max_length=320)
    invoice_period = models.CharField(max_length=320, default="Annual")
    start = models.DateField(default=date.today)
    end = models.DateField(null=True, blank=True)

class Cost(models.Model):
    contract = models.ForeignKey(ContractReference)
    name = models.CharField(max_length=320, help_text="Product or Service")
    description = models.TextField(default="N/A")
    comment = models.TextField(blank=True)
    quantity = models.CharField(max_length=320, default="1")
    finyear = models.IntegerField(choices=FINYEAR_CHOICES)
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    predicted_cost = models.DecimalField(max_digits=12, decimal_places=2)


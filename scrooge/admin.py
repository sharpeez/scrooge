from django.contrib import admin
from reversion.admin import VersionAdmin
from scrooge.models import ContractReference, Cost

@admin.register(ContractReference)
class ContractReferenceAdmin(VersionAdmin):
    list_editable = ['invoice_period', 'start', 'end']
    list_display = ['__str__', 'brand'] + list_editable
    search_fields = ['vendor', 'contract', 'brand']
    date_hierarchy = "start"
    list_filter = ["vendor", "invoice_period"]

@admin.register(Cost)
class CostAdmin(VersionAdmin):
    pass

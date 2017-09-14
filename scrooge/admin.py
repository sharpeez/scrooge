from django.contrib import admin
from reversion.admin import VersionAdmin
from scrooge.models import ContractReference, Cost, CostBreakdown, ITSystem, UserGroup

@admin.register(ContractReference)
class ContractReferenceAdmin(VersionAdmin):
    list_editable = ['invoice_period', 'start', 'end']
    list_display = ['__str__', 'brand'] + list_editable
    search_fields = ['vendor', 'contract', 'brand']
    date_hierarchy = "start"
    list_filter = ["vendor", "invoice_period"]

@admin.register(Cost)
class CostAdmin(VersionAdmin):
    list_filter = ["finyear", "allocated_percentage"]

@admin.register(ITSystem)
class ITSystemAdmin(VersionAdmin):
    pass

@admin.register(UserGroup)
class UserGroupAdmin(VersionAdmin):
    pass

@admin.register(CostBreakdown)
class CostBreakdownAdmin(VersionAdmin):
    list_filter = ["service_pool"]
    filter_horizontal = ["it_systems", "user_groups"]
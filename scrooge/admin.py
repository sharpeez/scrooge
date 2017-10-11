from django.contrib import admin
from reversion.admin import VersionAdmin
from import_export import resources
from import_export.admin import ImportExportMixin
from scrooge.models import Contract, Cost, CostBreakdown, ITSystem, UserGroup

class ScroogeAdmin(ImportExportMixin, VersionAdmin):
    pass

@admin.register(Contract)
class ContractAdmin(ScroogeAdmin):
    list_editable = ['invoice_period', 'start', 'end']
    list_display = ['__str__', 'brand'] + list_editable
    search_fields = ['vendor', 'contract', 'brand']
    date_hierarchy = "start"
    list_filter = ["vendor", "invoice_period"]

class CostBreakdownAdmin(ImportExportMixin, admin.StackedInline):
    model = CostBreakdown
    extra = 0
    fields = (("name", "service_pool", "percentage"), "user_groups")
    filter_horizontal = ['user_groups']

@admin.register(Cost)
class CostAdmin(ScroogeAdmin):
    list_display = ["__str__", "contract", "quantity", "predicted_cost", "predicted_percentage", "breakdown"]
    list_filter = ["finyear"]
    search_fields = ["name", "description", "comment", "contract__vendor", "contract__contract", "contract__brand"]
    inlines = [CostBreakdownAdmin]

#@admin.register(ITSystem)
class ITSystemAdmin(ScroogeAdmin):
    pass

@admin.register(UserGroup)
class UserGroupAdmin(ScroogeAdmin):
    list_display = ["__str__", "user_count", "cost_centres", "it_systems"]

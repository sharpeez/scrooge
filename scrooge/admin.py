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

@admin.register(Cost)
class CostAdmin(ScroogeAdmin):
    list_editable = ["actual_cost", "predicted_cost"]
    list_display = ["__str__", "contract", "quantity"] + list_editable + ["description", "comment"]
    list_filter = ["finyear", "allocated_percentage"]
    search_fields = ["name", "description", "comment", "contract__vendor", "contract__contract", "contract__brand"]

#@admin.register(ITSystem)
class ITSystemAdmin(ScroogeAdmin):
    pass

@admin.register(UserGroup)
class UserGroupAdmin(ScroogeAdmin):
    pass

@admin.register(CostBreakdown)
class CostBreakdownAdmin(ScroogeAdmin):
    list_display = ["__str__", "cost", "service_pool", "percentage", "calc_predicted_cost"]
    list_editable = ["service_pool", "percentage"]
    list_filter = ["service_pool"]
    filter_horizontal = ["it_systems", "user_groups"]
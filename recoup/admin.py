from django.contrib import admin
from reversion.admin import VersionAdmin
from recoup import models

class InlineBillAdmin(admin.TabularInline):
    model = models.Bill
    fields = ["name", "year", "renewal_date", "cost", "cost_estimate"]
    extra = 0

@admin.register(models.Contract)
class ContractAdmin(VersionAdmin):
    list_display = ["__str__", "cost", "cost_estimate", "start", "active"]
    search_fields = ["bill__name", "bill__description", "bill__comment", "vendor", "reference", "brand"]
    inlines = [InlineBillAdmin]

class EndUserCostAdmin(admin.TabularInline):
    model = models.EndUserCost
    extra = 0
    ordering = ("-percentage",)

class ITPlatformCostAdmin(admin.TabularInline):
    model = models.ITPlatformCost
    extra = 0
    ordering = ("-percentage",)

@admin.register(models.Bill)
class BillAdmin(VersionAdmin):
    list_display = ["__str__", "contract", "quantity", "cost", "cost_estimate", "allocated", "active"]
    list_filter = ["year", "allocated", "active"]
    search_fields = ["name", "description", "comment", "contract__vendor", "contract__reference", "contract__brand"]
    inlines = [EndUserCostAdmin, ITPlatformCostAdmin]

@admin.register(models.EndUserService)
class EndUserServiceAdmin(VersionAdmin):
    list_display = ["__str__", "cost", "cost_estimate", "cost_percentage", "cost_estimate_percentage"]
    inlines = [EndUserCostAdmin]

@admin.register(models.Platform)
class PlatformAdmin(VersionAdmin):
    list_display = ["__str__", "cost", "cost_estimate", "cost_percentage", "cost_estimate_percentage"]
    inlines = [ITPlatformCostAdmin]

@admin.register(models.Division)
class DivisionAdmin(VersionAdmin):
    list_display = ["__str__", "cost", "cost_estimate", "cost_percentage", "cost_estimate_percentage"]

@admin.register(models.ServicePool)
class ServicePoolAdmin(VersionAdmin):
    list_display = ["__str__", "cost", "cost_estimate", "cost_percentage", "cost_estimate_percentage"]
    inlines = [EndUserCostAdmin, ITPlatformCostAdmin]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

admin.site.register([
    models.SystemDependency,
    models.ITSystem,
])
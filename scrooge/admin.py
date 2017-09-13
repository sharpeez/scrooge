from django.contrib import admin
from reversion.admin import VersionAdmin
from scrooge.models import ContractReference, Cost

@admin.register(ContractReference)
class ContractReferenceAdmin(VersionAdmin):
    pass

@admin.register(Cost)
class CostAdmin(VersionAdmin):
    pass

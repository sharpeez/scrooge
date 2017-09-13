from django.contrib import admin
from scrooge.models import ContractReference, Cost

admin.site.register([ContractReference, Cost])
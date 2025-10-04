from django.contrib import admin
from .models import Lead, Offer

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'company', 'industry', 'intent', 'score']
    list_filter = ['intent', 'industry']
    search_fields = ['name', 'company', 'role']

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']

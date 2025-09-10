from django.contrib import admin
from .models import Partner
from import_export.admin import ImportExportModelAdmin

@admin.register(Partner)
class PartnerAdmin(ImportExportModelAdmin):
    list_display = ('firm_name', 'hq', 'focus_area', 'contact', 'current_partnership_status', 'created', 'updated')
    # list_filter = ('hq', 'current_partnership_status', 'created')
    # search_fields = ('firm_name', 'hq', 'focus_area', 'contact', 'donor_experience', 'current_partnership_status')
    # ordering = ('firm_name',)
    # list_per_page = 20
    # fieldsets = (
    #     (None, {
    #         'fields': ('firm_name',)
    #     }),
    #     ('Details', {
    #         'fields': ('hq', 'focus_area', 'contact', 'donor_experience', 'current_partnership_status')
    #     }),
    #     ('Timestamps', {
    #         'fields': ('created', 'updated'),
    #         'classes': ('collapse',)  # Collapsible section for timestamps
    #     }),
    # )
    # readonly_fields = ('created', 'updated')

    # def get_readonly_fields(self, request, obj=None):
    #     # Make timestamps readonly in edit mode
    #     return self.readonly_fields
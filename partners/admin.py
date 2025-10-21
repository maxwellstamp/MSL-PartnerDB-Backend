# admin.py
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Partner
from .resources import PartnerResource
import os

@admin.register(Partner)
class PartnerAdmin(ImportExportModelAdmin):
    resource_class = PartnerResource
    list_display = ('firm_name', 'hq', 'contact', 'current_partnership_status', 'created', 'updated')
    list_filter = ('hq', 'current_partnership_status', 'created')
    search_fields = ('firm_name', 'hq', 'focus_area', 'contact', 'donor_experience', 'current_partnership_status')
    ordering = ('firm_name',)
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('firm_name',)
        }),
        ('Details', {
            'fields': ('hq', 'focus_area', 'contact', 'donor_experience', 'current_partnership_status')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created', 'updated')

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields

    def process_import(self, request, *args, **kwargs):
        """
        Override process_import to handle temporary file cleanup more robustly.
        """
        import_file = request.FILES.get('import_file')
        if not import_file:
            return self._handle_import_file_not_found(request)

        # Use a context manager to ensure the file is properly handled
        import_path = self.get_import_path(request, *args, **kwargs)
        try:
            with open(import_path, 'wb+') as destination:
                for chunk in import_file.chunks():
                    destination.write(chunk)
            result = super().process_import(request, *args, **kwargs)
        finally:
            # Clean up only if the file exists
            if os.path.exists(import_path):
                try:
                    os.remove(import_path)
                except OSError as e:
                    logger.error(f"Failed to remove temp file {import_path}: {str(e)}")

        return result

    def get_import_path(self, request, *args, **kwargs):
        """
        Get the import path, ensuring it matches the temp storage location.
        """
        from import_export.tmp_storages import TempFolderStorage
        tmp_storage = TempFolderStorage()
        return tmp_storage.get_full_path()

    def _handle_import_file_not_found(self, request):
        self.message_user(request, "No file was uploaded.", level='error')
        return None

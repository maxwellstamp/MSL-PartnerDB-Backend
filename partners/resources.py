# resources.py
from import_export import resources
from import_export.fields import Field
from .models import Partner

class PartnerResource(resources.ModelResource):
    firm_name = Field(attribute='firm_name', column_name='firm_name')
    hq = Field(attribute='hq', column_name='hq')
    focus_area = Field(attribute='focus_area', column_name='focus_area')
    contact = Field(attribute='contact', column_name='contact')
    donor_experience = Field(attribute='donor_experience', column_name='donor_experience')
    current_partnership_status = Field(attribute='current_partnership_status', column_name='current_partnership_status')

    class Meta:
        model = Partner
        fields = (
            'firm_name',
            'hq',
            'focus_area',
            'contact',
            'donor_experience',
            'current_partnership_status',
        )
        export_order = fields
        import_id_fields = ('firm_name',)  # Use firm_name as identifier for updates
        skip_unchanged = True
        report_skipped = True
        use_bulk = True  # Enable bulk operations for better performance

    def before_import_row(self, row, **kwargs):
        """Clean and validate data before import"""
        # Clean firm_name
        if 'firm_name' in row and row['firm_name']:
            row['firm_name'] = str(row['firm_name']).strip()
        
        # Clean other fields
        for field in ['hq', 'focus_area', 'contact', 'donor_experience', 'current_partnership_status']:
            if field in row and row[field]:
                row[field] = str(row[field]).strip()
            elif field in row:
                row[field] = ''

    def get_or_init_instance(self, instance_loader, row):
        """Get existing instance or create new one based on firm_name"""
        try:
            instance = Partner.objects.get(firm_name=row['firm_name'])
            return instance, False  # False means it's an update
        except Partner.DoesNotExist:
            return Partner(), True  # True means it's a new instance

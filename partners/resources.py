from import_export import resources
from .models import Partner

class PartnerResource(resources.ModelResource):
    class Meta:
        model = Partner
        fields = ('firm_name', 'hq', 'focus_area', 'contact', 'donor_experience', 'current_partnership_status', 'created', 'updated')
        import_id_fields = ["firm_name"]
        skip_unchanged = True
        use_bulk = True
        

        # fields = ('id', 'firm_name', 'hq', 'focus-area')
        # export_order = ('id', 'firm_name', 'hq', 'focus_area', 'contact', 'donor_experience', 'current_partnership_status', 'created', 'updated')
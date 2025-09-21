from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from .models import Partner
from .serializers import PartnerSerializer
import pandas as pd
from rest_framework import status
from import_export.tmp_storages import TempFolderStorage
from .resources import PartnerResource
import re
from io import BytesIO

# Custom Pagination Class
class PartnerPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100

class PartnerViewSet(viewsets.ModelViewSet):
    queryset = Partner.objects.all().order_by("id")
    serializer_class = PartnerSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["hq"]
    search_fields = [
        "firm_name", "hq", "focus_area",
        "contact", "donor_experience", "current_partnership_status"
    ]
    pagination_class = PartnerPagination

@api_view(["GET"])
@permission_classes([AllowAny])
def hq_list(request):
    hqs = Partner.objects.exclude(hq__isnull=True).exclude(hq__exact="").values_list("hq", flat=True).distinct()
    return Response(sorted(hqs))

@api_view(['POST'])
@permission_classes([AllowAny])  # Change to IsAuthenticated in production
def upload_excel(request):
    if 'file' not in request.FILES:
        return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    file = request.FILES['file']
    if not file.name.endswith(('.xlsx', '.xls')):
        return Response({"error": "Invalid file type. Only Excel files allowed."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Read uploaded file into a resettable in-memory buffer
        file_bytes = file.read()
        if not file_bytes:
            return Response({"error": "Empty file"}, status=status.HTTP_400_BAD_REQUEST)
        buffer = BytesIO(file_bytes)

        # Choose engine by extension
        name_lower = file.name.lower()
        read_engine = 'openpyxl' if name_lower.endswith('.xlsx') else 'xlrd'

        # Detect header row containing firm name
        try:
            df_probe = pd.read_excel(
                buffer,
                engine=read_engine,
                header=None,
                dtype=object,
                keep_default_na=False
            )
        except ValueError as ve:
            return Response({"error": f"Invalid Excel file or engine error: {str(ve)}"}, status=status.HTTP_400_BAD_REQUEST)
        if df_probe.empty:
            return Response({"error": "Empty file"}, status=status.HTTP_400_BAD_REQUEST)

        header_row_idx = None
        header_aliases_firm = {
            'firm name', 'company name', 'company_name', 'firm', 'name of organization(firms)'
        }
        max_scan_rows = min(len(df_probe), 50)
        for idx in range(max_scan_rows):
            row_values = [str(v).strip().lower() for v in df_probe.iloc[idx].tolist() if v]
            if any((cell in header_aliases_firm) or ('firm' in cell and 'name' in cell) for cell in row_values):
                header_row_idx = idx
                break

        if header_row_idx is None:
            return Response({"error": "Could not detect header row with 'Firm Name' or equivalent."}, status=status.HTTP_400_BAD_REQUEST)

        # Re-read with detected header from the same buffer
        buffer.seek(0)
        try:
            df = pd.read_excel(
                buffer,
                engine=read_engine,
                header=header_row_idx,
                dtype=object,
                keep_default_na=False
            )
        except ValueError as ve:
            return Response({"error": f"Invalid Excel file or engine error: {str(ve)}"}, status=status.HTTP_400_BAD_REQUEST)
        if df.empty:
            return Response({"error": "No data rows found below header"}, status=status.HTTP_400_BAD_REQUEST)

        # Normalize headers: lowercase, replace multiple spaces/hyphens with single space
        df.columns = [re.sub(r"[\s_\-]+", " ", str(c).strip().lower()) for c in df.columns]

        # Map common aliases
        column_mapping = {
            'company name': 'firm_name',
            'company_name': 'firm_name',
            'firm': 'firm_name',
            'name of organization(firms)': 'firm_name',
            'firm name': 'firm_name',
            'origin': 'hq',
            'headquarters': 'hq',
            'headquarter': 'hq',
            'head quarter': 'hq',
            'hq': 'hq',
            'focus area': 'focus_area',
            'focus_area': 'focus_area',
            'donor experience': 'donor_experience',
            'donor exprience': 'donor_experience',
            'contact': 'contact',
            'email': 'contact',
            'number': 'contact',
            'phone': 'contact',
            'phone number': 'contact',
            'current partnership status': 'current_partnership_status',
            'partnership status': 'current_partnership_status',
        }
        df = df.rename(columns=column_mapping)

        # Validate required column
        if 'firm_name' not in df.columns:
            return Response({"error": "Missing required column: 'Firm Name' or equivalent"}, status=status.HTTP_400_BAD_REQUEST)

        # Filter out rows where firm_name is null or empty
        df = df[df['firm_name'].notna() & (df['firm_name'].str.strip() != '')]

        # Prepare data for import
        import_data = []
        
        for index, row in df.iterrows():
            # Create a dictionary for each row
            row_data = {
                'firm_name': str(row.get('firm_name', '')).strip(),
            }
            
            # Add other fields if they exist in the dataframe
            for field in ['hq', 'focus_area', 'contact', 'donor_experience', 'current_partnership_status']:
                if field in df.columns:
                    value = row.get(field, '')
                    # Convert to string and clean up
                    if pd.isna(value) or value == '':
                        row_data[field] = ''
                    else:
                        row_data[field] = str(value).strip()
                else:
                    row_data[field] = ''
            
            # Only add rows with valid firm names
            if row_data['firm_name']:
                import_data.append(row_data)

        if not import_data:
            return Response({"error": "No valid data rows found with firm names"}, status=status.HTTP_400_BAD_REQUEST)

        # Use django-import-export to import the data
        resource = PartnerResource()
        
        # Create dataset from the prepared data
        dataset = resource.export().dataset
        dataset.clear()
        
        # Add headers
        headers = ['firm_name', 'hq', 'focus_area', 'contact', 'donor_experience', 'current_partnership_status']
        dataset.headers = headers
        
        # Add data rows
        for row_data in import_data:
            row = [row_data.get(field, '') for field in headers]
            dataset.append(row)

        # Import data
        result = resource.import_data(dataset, dry_run=False, raise_errors=False, collect_failed_rows=True)
        
        # Process results
        total_rows = result.total_rows
        created_count = result.totals.get('new', 0)
        updated_count = result.totals.get('update', 0)
        skipped_count = result.totals.get('skip', 0)
        error_count = result.totals.get('error', 0)
        
        # Collect detailed error information
        errors = []
        if result.has_errors():
            for error in result.row_errors():
                row_num, row_errors = error
                error_messages = [str(e.error) for e in row_errors]
                errors.append(f"Row {row_num}: {', '.join(error_messages)}")
        
        # Collect skipped row information
        skipped = []
        if result.has_skipped():
            for skip in result.skipped_rows():
                row_num, skip_reason = skip
                skipped.append(f"Row {row_num}: {skip_reason}")
        
        response_data = {
            "message": f"Excel upload completed successfully!",
            "summary": {
                "total_rows": total_rows,
                "created": created_count,
                "updated": updated_count,
                "skipped": skipped_count,
                "errors": error_count
            },
            "details": {
                "errors": errors if errors else None,
                "skipped": skipped if skipped else None
            }
        }
        
        # Return success even if some rows had errors, as long as some were processed
        if created_count > 0 or updated_count > 0:
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": f"Excel upload failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def upload_status(request):
    """Get information about the upload endpoint"""
    return Response({
        "message": "Excel upload endpoint is ready",
        "supported_formats": [".xlsx", ".xls"],
        "required_fields": ["firm_name"],
        "optional_fields": ["hq", "focus_area", "contact", "donor_experience", "current_partnership_status"],
        "usage": "POST /api/upload-excel/ with multipart/form-data containing 'file' field"
    })
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
    pagination_class = PartnerPagination   # pagination add

@api_view(["GET"])
@permission_classes([AllowAny])
def hq_list(request):
    hqs = Partner.objects.exclude(hq__isnull=True).exclude(hq__exact="").values_list("hq", flat=True).distinct()
    return Response(sorted(hqs))


#Fuctionalities of excel read, scrape and added in database

@api_view(['POST'])
@permission_classes([AllowAny])  # Change to IsAuthenticated in production
def upload_excel(request):
    if 'file' not in request.FILES:
        return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    file = request.FILES['file']
    if not file.name.endswith(('.xlsx', '.xls')):
        return Response({"error": "Invalid file type. Only Excel files allowed."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Read Excel into DataFrame
        df = pd.read_excel(file, engine='openpyxl')  # Use openpyxl for .xlsx
        if df.empty:
            return Response({"error": "Empty file"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Normalize column names: lowercase, strip spaces
        df.columns = df.columns.str.strip().str.lower()
        #df.columns = df.columns.str.strip().str.lower().str.replace(r'\u200b', '', regex=True).str.replace(r'\xa0', '', regex=True)

        
        # Map common aliases (e.g., 'company name' to 'firm_name', 'headquarters' to 'hq')
        column_mapping = {
            'company name': 'firm_name',
            'company_name': 'firm_name',
            'firm': 'firm_name',
            'name of organization(firms)': 'firm_name',
            'firm name': 'firm_name',
            
            
            'origin': 'hq',
            'headquarters': 'hq',
            'origin': 'hq',
            'focus area': 'focus_area',
            'donor experience': 'donor_experience',
            'contact': 'contact',
            'email': 'contact',
            'number': 'contact',
        }
        df = df.rename(columns=column_mapping)
        
        # Check for required column
        if 'firm_name' not in df.columns:
            return Response({"error": "Missing required column: 'firm_name' or 'company name' or 'name of Organization(firms)'"}, status=status.HTTP_400_BAD_REQUEST)
        
        processed = 0
        skipped = []
        for index, row in df.iterrows():
            firm_name = str(row.get('firm_name', 'firms', 'firm name')).strip().lower()
            if pd.isna(firm_name) or not firm_name:
                skipped.append(f"Row {index+2}: Missing firm_name")  # +2 for header and 1-indexing
                continue
            
            # Prepare defaults for other fields with specific parsing logic
            defaults = {}

            # Parsing logic for 'hq'
            hq = row.get('hq')
            if not pd.isna(hq):
                defaults['hq'] = str(hq).strip().capitalize()

            # Parsing logic for 'focus_area'
            focus_area = row.get('focus_area')
            if not pd.isna(focus_area):
                defaults['focus_area'] = str(focus_area).strip()

            # Parsing logic for 'contact'
            contact = row.get('contact')
            if not pd.isna(contact):
                defaults['contact'] = str(contact).strip()

            # Parsing logic for 'donor_experience'
            donor_experience = row.get('donor_experience')
            if not pd.isna(donor_experience):
                defaults['donor_experience'] = str(donor_experience).strip()

            # Parsing logic for 'current_partnership_status'
            current_partnership_status = row.get('current_partnership_status')
            if not pd.isna(current_partnership_status):
                defaults['current_partnership_status'] = str(current_partnership_status).strip()

            # Check for existing record and update or create
            existing_partner = Partner.objects.filter(firm_name__iexact=firm_name).first()
            if existing_partner:
                for key, value in defaults.items():
                    setattr(existing_partner, key, value)
                existing_partner.save()
            else:
                Partner.objects.create(firm_name=firm_name, **defaults)
            
            processed += 1
        
        response_data = {
            "message": f"Processed {processed} rows successfully.",
            "skipped": skipped if skipped else None
        }
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
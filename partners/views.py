from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from .models import Partner
from .resources import PartnerResource
from django.contrib import messages
from .serializers import PartnerSerializer
import pandas as pd
from rest_framework import status
from tablib import Dataset
from django.http import HttpResponse

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
@permission_classes([AllowAny])
def upload_excel(request):
    if 'file' not in request.FILES:
        return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES['file']
    if not file.name.endswith(('.xlsx', '.xls')):
        return Response({"error": "Invalid file type. Only Excel files allowed."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        df = pd.read_excel(file, engine='openpyxl')
        df.columns = df.columns.str.strip().str.lower()

        column_mapping = {
            'firm name': 'firm_name',
            'headquarters': 'hq',
            'origin': 'hq',
            'focus area': 'focus_area',
            'donor experience': 'donor_experience',
            'contact': 'contact',
            'current partnership status': 'current_partnership_status'
        }

        df = df.rename(columns=column_mapping, errors='ignore')

        if 'firm_name' not in df.columns:
            return Response({"error": "Missing required column: firm_name"}, status=status.HTTP_400_BAD_REQUEST)

        processed_count = 0
        skipped_rows = []

        for index, row in df.iterrows():
            try:
                firm_name = row.get('firm_name', None)
                if pd.isna(firm_name) or str(firm_name).strip() == '':
                    skipped_rows.append(f"Row {index + 2}: firm_name is missing")
                    continue

                firm_name = str(firm_name).strip()

                hq = row.get('hq', None)
                focus_area = row.get('focus_area', None)
                contact = row.get('contact', None)
                donor_experience = row.get('donor_experience', None)
                current_partnership_status = row.get('current_partnership_status', None)

                defaults = {}
                if hq is not None and not pd.isna(hq):
                    defaults['hq'] = str(hq).strip().capitalize()
                if focus_area is not None and not pd.isna(focus_area):
                    defaults['focus_area'] = str(focus_area).strip()
                if contact is not None and not pd.isna(contact):
                    defaults['contact'] = str(contact).strip()
                if donor_experience is not None and not pd.isna(donor_experience):
                    defaults['donor_experience'] = str(donor_experience).strip()
                if current_partnership_status is not None and not pd.isna(current_partnership_status):
                    defaults['current_partnership_status'] = str(current_partnership_status).strip()

                Partner.objects.update_or_create(
                    firm_name__iexact=firm_name.lower(),
                    defaults={'firm_name': firm_name, **defaults}
                )
                processed_count += 1

            except Exception as e:
                skipped_rows.append(f"Row {index + 2}: Error - {str(e)}")

        if skipped_rows:
            return Response({
                "message": f"Processed {processed_count} rows. Some rows were skipped.",
                "skipped": skipped_rows
            }, status=status.HTTP_200_OK)

        return Response({"message": f"Processed {processed_count} rows successfully."}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# models.py
from django.db import models

class Partner(models.Model):
    firm_name = models.CharField(max_length=255, unique=True)  # Required field, unique constraint
    hq = models.CharField(max_length=255, blank=True, null=True)  # Headquarters (country/city)
    focus_area = models.TextField(blank=True, null=True)
    contact = models.CharField(max_length=255, blank=True, null=True)
    donor_experience = models.TextField(blank=True, null=True)
    current_partnership_status = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["firm_name"]

    def __str__(self):
        return self.firm_name
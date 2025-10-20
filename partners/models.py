from django.db import models

# Create your models here.
class Partner(models.Model):
    firm_name = models.CharField(max_length=255, unique=True)  # required
    hq = models.CharField(max_length=255, blank=True, null=True)  # country / city
    focus_area = models.TextField(blank=True, null=True)
    contact = models.CharField(max_length=255, blank=True, null=True)
    donor_experience = models.TextField(blank=True, null=True)
    current_partnership_status = models.CharField(max_length=255, blank=True, null=True)
    sector = models.CharField(max_length=255, blank=True, null=True)  # NEW: sector of the firm

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["firm_name"]

    def __str__(self):
        return self.firm_name
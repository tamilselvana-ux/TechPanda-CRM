from django.db import models
from django.conf import settings


class SavedReport(models.Model):
    name = models.CharField(max_length=150)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_reports'
    )
    report_type = models.CharField(max_length=50, default='calls')
    period_type = models.CharField(max_length=20, default='day')
    period_date = models.DateField(null=True, blank=True)
    filters = models.JSONField(default=dict, blank=True)
    is_shared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class ReportExportJob(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='export_jobs'
    )
    report_type = models.CharField(max_length=50)
    file_format = models.CharField(max_length=10, default='xlsx')
    period_summary = models.CharField(max_length=150, blank=True, default='')
    filters = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLETED')
    file_path = models.CharField(max_length=300, blank=True, default='')
    download_url = models.CharField(max_length=300, blank=True, default='')
    row_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Export #{self.id} {self.report_type} ({self.file_format}) by {self.user.username}"

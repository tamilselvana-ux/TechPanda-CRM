from django.db import models

class Product(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'

    class GSTTreatment(models.TextChoices):
        WITH_GST = 'WITH_GST', 'With GST'
        WITHOUT_GST = 'WITHOUT_GST', 'Without GST'

    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    gst_treatment = models.CharField(
        max_length=20,
        choices=GSTTreatment.choices,
        default=GSTTreatment.WITH_GST,
        help_text="Whether course fee includes GST or is without GST"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

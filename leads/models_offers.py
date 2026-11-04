from django.db import models
from django.utils import timezone
from products.models import Product
from branches.models import Branch


class ApprovedOfferCategory(models.TextChoices):
    FEE_FLEXIBILITY = 'FEE', 'Fee & Installment Flexibility'
    PLACEMENT_SUPPORT = 'PLACEMENT', 'Placement Assistance & Career Services'
    TIMING_BATCH = 'TIMING', 'Batch Timing & Attendance Flexibility'
    CURRICULUM = 'CURRICULUM', 'Course Curriculum & Hands-on Projects'
    GENERAL = 'GENERAL', 'General Approved Talking Point'


class ApprovedOffer(models.Model):
    """
    Admin-managed and approved talking points, offers, and objection rebuttals.
    Ensures telecallers and counselors strictly communicate real, management-approved
    offers and policies without inventing fees, discounts, or placement claims.
    """
    title = models.CharField(max_length=200, help_text="Short descriptive title of the approved offer or rebuttal.")
    category = models.CharField(
        max_length=30,
        choices=ApprovedOfferCategory.choices,
        default=ApprovedOfferCategory.GENERAL,
        db_index=True
    )
    approved_text = models.TextField(
        help_text="Exact approved script / talking points for staff to communicate to students."
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_offers',
        help_text="Optional: Restrict this offer/script to a specific course."
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_offers',
        help_text="Optional: Restrict this offer/script to a specific branch."
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Only active offers appear in the Smart Pitch Decision-Support block."
    )
    display_order = models.IntegerField(
        default=0,
        help_text="Lower numbers appear first."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = 'Approved Offer & Script'
        verbose_name_plural = 'Approved Offers & Scripts'

    def __str__(self):
        prod_str = f" [{self.product.name}]" if self.product else ""
        return f"{self.title}{prod_str} ({self.get_category_display()})"

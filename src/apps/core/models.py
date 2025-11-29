from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid


class BaseModel(models.Model):
    """
    Abstract base model for all models in the application.
    Provides UUID primary key and timestamp fields.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    created_at = models.DateTimeField(db_index=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:  # type: ignore
        abstract = True


class AgeGroup(models.IntegerChoices):
    """
    Age group classifications for characters and book templates.
    Each group defines an age range for automatic classification.

    NOTE: Animals (DOG, CAT, RABBIT, TURTLE) are excluded from age groups.
    """

    BABY = 1, _("Baby")  # 0-3 years
    TODDLER = 2, _("Toddler")  # 4-6 years
    CHILD = 3, _("Child")  # 7-8 years
    PRE_TEEN = 4, _("Pre-Teen")  # 9-12 years
    YOUNG_TEEN = 5, _("Young Teen")  # 13-15 years
    MID_TEEN = 6, _("Mid Teen")  # 16-17 years
    LATE_TEEN = 7, _("Late Teen")  # 18-19 years
    ADULT = 8, _("Adult")  # 20-64 years
    SENIOR = 9, _("Senior")  # 65+ years

    @classmethod
    def get_age_range(cls, age_group_value: int) -> tuple[int, int]:
        """
        Get the min/max age range for an age group.

        Args:
            age_group_value: AgeGroup enum value (1-9)

        Returns:
            Tuple of (min_age, max_age)
        """
        ranges = {
            cls.BABY: (0, 3),
            cls.TODDLER: (4, 6),
            cls.CHILD: (7, 8),
            cls.PRE_TEEN: (9, 12),
            cls.YOUNG_TEEN: (13, 15),
            cls.MID_TEEN: (16, 17),
            cls.LATE_TEEN: (18, 19),
            cls.ADULT: (20, 64),
            cls.SENIOR: (65, 150),
        }
        return ranges.get(age_group_value, (0, 150))

    @classmethod
    def from_age(cls, age: int) -> int:
        """
        Determine age group from a given age.

        Args:
            age: Age in years

        Returns:
            AgeGroup enum value (1-9)
        """
        if age <= 3:
            return cls.BABY
        elif 4 <= age <= 6:
            return cls.TODDLER
        elif 7 <= age <= 8:
            return cls.CHILD
        elif 9 <= age <= 12:
            return cls.PRE_TEEN
        elif 13 <= age <= 15:
            return cls.YOUNG_TEEN
        elif 16 <= age <= 17:
            return cls.MID_TEEN
        elif 18 <= age <= 19:
            return cls.LATE_TEEN
        elif 20 <= age <= 64:
            return cls.ADULT
        else:  # 65+
            return cls.SENIOR


class Language(BaseModel):
    """
    Model representing supported languages for book content.
    Linked to settings.LANGUAGES for consistency.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Language Name"),
        help_text=_("Full language name, e.g., 'English', 'Spanish'"),
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        choices=settings.LANGUAGES,
        verbose_name=_("Language Code"),
        help_text=_("ISO language code, e.g., 'en', 'es'"),
    )
    country = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Country"),
        help_text=_("Country or region, e.g., 'Spain' for Spanish (Spain)"),
    )

    class Meta:
        verbose_name = _("Language")
        verbose_name_plural = _("Languages")
        ordering = ["name"]

    def __str__(self):
        return self.name

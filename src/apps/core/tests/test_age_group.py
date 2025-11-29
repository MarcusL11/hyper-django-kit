# apps/core/tests/test_age_group.py

import pytest
from apps.core.models import AgeGroup


class TestAgeGroupFromAge:
    """
    Test suite for AgeGroup.from_age() classmethod.

    Source: pytest best practices - Test boundary conditions for classification logic
    """

    def test_baby_age_range(self):
        """Test ages 0-3 return BABY."""
        assert AgeGroup.from_age(0) == AgeGroup.BABY
        assert AgeGroup.from_age(1) == AgeGroup.BABY
        assert AgeGroup.from_age(2) == AgeGroup.BABY
        assert AgeGroup.from_age(3) == AgeGroup.BABY

    def test_toddler_age_range(self):
        """Test ages 4-6 return TODDLER."""
        assert AgeGroup.from_age(4) == AgeGroup.TODDLER
        assert AgeGroup.from_age(5) == AgeGroup.TODDLER
        assert AgeGroup.from_age(6) == AgeGroup.TODDLER

    def test_child_age_range(self):
        """Test ages 7-8 return CHILD."""
        assert AgeGroup.from_age(7) == AgeGroup.CHILD
        assert AgeGroup.from_age(8) == AgeGroup.CHILD

    def test_pre_teen_age_range(self):
        """Test ages 9-12 return PRE_TEEN."""
        assert AgeGroup.from_age(9) == AgeGroup.PRE_TEEN
        assert AgeGroup.from_age(10) == AgeGroup.PRE_TEEN
        assert AgeGroup.from_age(11) == AgeGroup.PRE_TEEN
        assert AgeGroup.from_age(12) == AgeGroup.PRE_TEEN

    def test_young_teen_age_range(self):
        """Test ages 13-15 return YOUNG_TEEN."""
        assert AgeGroup.from_age(13) == AgeGroup.YOUNG_TEEN
        assert AgeGroup.from_age(14) == AgeGroup.YOUNG_TEEN
        assert AgeGroup.from_age(15) == AgeGroup.YOUNG_TEEN

    def test_mid_teen_age_range(self):
        """Test ages 16-17 return MID_TEEN."""
        assert AgeGroup.from_age(16) == AgeGroup.MID_TEEN
        assert AgeGroup.from_age(17) == AgeGroup.MID_TEEN

    def test_late_teen_age_range(self):
        """Test ages 18-19 return LATE_TEEN."""
        assert AgeGroup.from_age(18) == AgeGroup.LATE_TEEN
        assert AgeGroup.from_age(19) == AgeGroup.LATE_TEEN

    def test_adult_age_range(self):
        """Test ages 20-64 return ADULT."""
        assert AgeGroup.from_age(20) == AgeGroup.ADULT
        assert AgeGroup.from_age(30) == AgeGroup.ADULT
        assert AgeGroup.from_age(50) == AgeGroup.ADULT
        assert AgeGroup.from_age(64) == AgeGroup.ADULT

    def test_senior_age_range(self):
        """Test ages 65+ return SENIOR."""
        assert AgeGroup.from_age(65) == AgeGroup.SENIOR
        assert AgeGroup.from_age(75) == AgeGroup.SENIOR
        assert AgeGroup.from_age(100) == AgeGroup.SENIOR

    def test_boundary_ages(self):
        """
        Test critical boundary ages between groups.

        Source: pytest best practices - Test boundary conditions
        """
        # Baby -> Toddler boundary
        assert AgeGroup.from_age(3) == AgeGroup.BABY
        assert AgeGroup.from_age(4) == AgeGroup.TODDLER

        # Toddler -> Child boundary
        assert AgeGroup.from_age(6) == AgeGroup.TODDLER
        assert AgeGroup.from_age(7) == AgeGroup.CHILD

        # Child -> Pre-Teen boundary
        assert AgeGroup.from_age(8) == AgeGroup.CHILD
        assert AgeGroup.from_age(9) == AgeGroup.PRE_TEEN

        # Pre-Teen -> Young Teen boundary
        assert AgeGroup.from_age(12) == AgeGroup.PRE_TEEN
        assert AgeGroup.from_age(13) == AgeGroup.YOUNG_TEEN

        # Young Teen -> Mid Teen boundary
        assert AgeGroup.from_age(15) == AgeGroup.YOUNG_TEEN
        assert AgeGroup.from_age(16) == AgeGroup.MID_TEEN

        # Mid Teen -> Late Teen boundary
        assert AgeGroup.from_age(17) == AgeGroup.MID_TEEN
        assert AgeGroup.from_age(18) == AgeGroup.LATE_TEEN

        # Late Teen -> Adult boundary
        assert AgeGroup.from_age(19) == AgeGroup.LATE_TEEN
        assert AgeGroup.from_age(20) == AgeGroup.ADULT

        # Adult -> Senior boundary
        assert AgeGroup.from_age(64) == AgeGroup.ADULT
        assert AgeGroup.from_age(65) == AgeGroup.SENIOR


class TestAgeGroupGetAgeRange:
    """Test suite for AgeGroup.get_age_range() classmethod."""

    def test_baby_age_range(self):
        """Test BABY returns (0, 3) range."""
        assert AgeGroup.get_age_range(AgeGroup.BABY) == (0, 3)

    def test_toddler_age_range(self):
        """Test TODDLER returns (4, 6) range."""
        assert AgeGroup.get_age_range(AgeGroup.TODDLER) == (4, 6)

    def test_child_age_range(self):
        """Test CHILD returns (7, 8) range."""
        assert AgeGroup.get_age_range(AgeGroup.CHILD) == (7, 8)

    def test_pre_teen_age_range(self):
        """Test PRE_TEEN returns (9, 12) range."""
        assert AgeGroup.get_age_range(AgeGroup.PRE_TEEN) == (9, 12)

    def test_young_teen_age_range(self):
        """Test YOUNG_TEEN returns (13, 15) range."""
        assert AgeGroup.get_age_range(AgeGroup.YOUNG_TEEN) == (13, 15)

    def test_mid_teen_age_range(self):
        """Test MID_TEEN returns (16, 17) range."""
        assert AgeGroup.get_age_range(AgeGroup.MID_TEEN) == (16, 17)

    def test_late_teen_age_range(self):
        """Test LATE_TEEN returns (18, 19) range."""
        assert AgeGroup.get_age_range(AgeGroup.LATE_TEEN) == (18, 19)

    def test_adult_age_range(self):
        """Test ADULT returns (20, 64) range."""
        assert AgeGroup.get_age_range(AgeGroup.ADULT) == (20, 64)

    def test_senior_age_range(self):
        """Test SENIOR returns (65, 150) range."""
        assert AgeGroup.get_age_range(AgeGroup.SENIOR) == (65, 150)


class TestAgeGroupChoices:
    """Test AgeGroup IntegerChoices values."""

    def test_age_group_values(self):
        """Test all age groups have correct integer values."""
        assert AgeGroup.BABY.value == 1
        assert AgeGroup.TODDLER.value == 2
        assert AgeGroup.CHILD.value == 3
        assert AgeGroup.PRE_TEEN.value == 4
        assert AgeGroup.YOUNG_TEEN.value == 5
        assert AgeGroup.MID_TEEN.value == 6
        assert AgeGroup.LATE_TEEN.value == 7
        assert AgeGroup.ADULT.value == 8
        assert AgeGroup.SENIOR.value == 9

    def test_age_group_labels(self):
        """Test all age groups have correct display labels."""
        assert AgeGroup.BABY.label == "Baby"
        assert AgeGroup.TODDLER.label == "Toddler"
        assert AgeGroup.CHILD.label == "Child"
        assert AgeGroup.PRE_TEEN.label == "Pre-Teen"
        assert AgeGroup.YOUNG_TEEN.label == "Young Teen"
        assert AgeGroup.MID_TEEN.label == "Mid Teen"
        assert AgeGroup.LATE_TEEN.label == "Late Teen"
        assert AgeGroup.ADULT.label == "Adult"
        assert AgeGroup.SENIOR.label == "Senior"

    def test_all_choices_count(self):
        """Test there are exactly 9 age group choices."""
        assert len(AgeGroup.choices) == 9

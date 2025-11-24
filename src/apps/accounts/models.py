from django.contrib.auth.models import AbstractUser
from apps.core.models import BaseModel
from django.db import models
from djstripe.models import Subscription, Customer


class CustomUser(AbstractUser, BaseModel):  # type: ignore
    subscription = models.ForeignKey(
        Subscription,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="The user's Stripe Subscription object (cached for performance)",
    )
    customer = models.ForeignKey(
        Customer,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="The user's Stripe Customer object, if it exists",
    )
    profile_image = models.ImageField(
        upload_to="profiles/%Y/%m/",
        null=True,
        blank=True,
        help_text="User profile picture (max 8MB)",
    )

    def __str__(self):
        return self.username

    @property
    def active_subscription(self):
        """
        Returns the user's currently active subscription.

        Queries dj-stripe for subscriptions linked to this user's Stripe Customer,
        then filters in Python for 'active' or 'trialing' status.

        Note: This property always queries the database for guaranteed accuracy.
        For cached access (faster but may be stale), use the 'subscription' FK field.

        Returns:
            Subscription object if active subscription exists, None otherwise.

        Example:
            if user.active_subscription:
                plan_name = user.active_subscription.product.name
        """
        if not self.customer:
            return None

        for subscription in self.customer.subscriptions.all().order_by("-created"):
            if subscription.status in ["active", "trialing"]:
                return subscription

        return None

    @property
    def subscription_status(self):
        """
        Returns the status of the user's currently active subscription.

        Queries dj-stripe for subscriptions linked to this user's Stripe Customer,
        then filters in Python for 'active' or 'trialing' status.

        Note: This property always queries the database for guaranteed accuracy.
        For cached access (faster but may be stale), use the 'subscription' FK field.

        Returns:
            String status if active subscription exists, None otherwise.

        Example:
            status = user.subscription_status
            if status == "active":
                # User has an active subscription
        """
        active_sub = self.active_subscription
        if active_sub:
            return active_sub.status
        return None

    def has_feature(self, feature_name: str) -> bool:
        """
        Check if user has access to a specific feature.

        Args:
            feature_name: Feature constant from apps.subscriptions.features

        Returns:
            True if user's subscription includes this feature, False otherwise.

        Example:
            from apps.subscriptions import features

            if user.has_feature(features.LUDICROUS_MODE):
                enable_ludicrous_mode()
            else:
                return HttpResponseForbidden("Premium feature")
        """
        sub = self.active_subscription
        if sub and sub.product and sub.product.subscription_metadata:
            return feature_name in sub.product.subscription_metadata.features
        return False

    def get_subscription_features(self) -> list[str]:
        """
        Get list of all features for user's subscription.

        Returns:
            List of feature strings, empty list if no active subscription.

        Example:
            features = user.get_subscription_features()
            # ['Unlimited Widgets', 'Priority Support']
        """
        sub = self.active_subscription
        if sub and sub.product and sub.product.subscription_metadata:
            return sub.product.subscription_metadata.features
        return []

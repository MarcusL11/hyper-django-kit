from django.apps import AppConfig


class SubscriptionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.subscriptions"

    def ready(self):
        """Import signal handlers to register them with dj-stripe."""
        import apps.subscriptions.signals  # noqa

        """
        Extend dj-stripe models with custom properties.
        Called once during Django initialization.

        Note: This is SAFE because we only DEFINE properties here,
        we don't EXECUTE any database queries. Queries only run when
        the properties are accessed (e.g., user.active_subscription.product).
        """
        from djstripe.models import Subscription, Product
        from apps.subscriptions.metadata import METADATA_MAP

        # Add .product property to Subscription model
        # TODO: If you add multi-product subscriptions in the future
        @property
        def product(self):
            """
            Returns the Product for this subscription.

            Navigates: Subscription → items.first() → Price → Product

            Note: Uses .first() because this app uses single-product
            subscriptions (user subscribes to one plan: Starter, Standard,
            or Premium).

            (e.g., Base Plan + Add-ons), update this logic to either:
            - Filter by product type/metadata to get the base plan
            - Return a list of all products
            - Add a separate property like .base_product and .addon_products

            Returns:
                Product object if subscription has items, None otherwise.
            """
            first_item = self.items.first()
            if first_item and first_item.price:
                return first_item.price.product
            return None

        # Add .subscription_metadata property to Product model
        @property
        def subscription_metadata(self):
            """
            Returns custom SubscriptionProductMetadata for this Stripe Product.

            Looks up product ID in METADATA_MAP which contains
            subscription-specific metadata like features, descriptions,
            and ordering.

            Note: Named 'subscription_metadata' to avoid conflict with
            shop app's 'shop_metadata' property.

            Returns:
                SubscriptionProductMetadata object if found in METADATA_MAP,
                None otherwise.
            """
            return METADATA_MAP.get(self.id)

        # Attach properties to dj-stripe models
        # This is idempotent - safe to run multiple times
        Subscription.product = product  # type:ignore
        Product.subscription_metadata = subscription_metadata  # type:ignore

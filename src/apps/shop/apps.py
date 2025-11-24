from django.apps import AppConfig


class ShopConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.shop"

    def ready(self):
        # Register webhook signal handlers
        import apps.shop.signals  # noqa

        # Extend djstripe.Product with .shop_metadata property
        # Similar to subscriptions app pattern
        from djstripe.models import Product as StripeProduct
        from apps.shop.models import ShopProduct

        @property
        def shop_metadata(self):
            """
            Returns ShopProduct for this Stripe Product.

            Similar to subscriptions.apps.py pattern,
            but queries database instead of static METADATA_MAP.

            Note: Named 'shop_metadata' to avoid conflict with
            subscriptions app's 'subscription_metadata' property.

            Usage in views:
                stripe_product = StripeProduct.objects.get(id="prod_xxx")
                shop_product = stripe_product.shop_metadata
                images = shop_product.images.all() if shop_product else []

            Returns:
                ShopProduct instance if exists, None otherwise
            """
            try:
                return ShopProduct.objects.get(product_id=self.id)
            except ShopProduct.DoesNotExist:
                return None

        # Monkey-patch djstripe Product model
        StripeProduct.shop_metadata = shop_metadata  # type:ignore

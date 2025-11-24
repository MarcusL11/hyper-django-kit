from django.db import models
from apps.core.models import BaseModel
import logging

logger = logging.getLogger(__name__)


class ShopCategory(BaseModel):
    """
    Product categories for shop organization.
    Allows admins to create and manage product categories.
    """

    name = models.CharField(
        max_length=100, unique=True, help_text="Category name (e.g., 'Books', 'Toys')"
    )

    slug = models.SlugField(
        unique=True, max_length=100, help_text="URL slug for category filtering"
    )

    description = models.TextField(
        blank=True, help_text="Category description for category pages"
    )

    sort_order = models.IntegerField(
        default=0, help_text="Display order (lower = first)"
    )

    is_active = models.BooleanField(
        default=True, help_text="Show category in navigation/filters"
    )

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Shop Category"
        verbose_name_plural = "Shop Categories"

    def __str__(self):
        return self.name


class ShopProduct(BaseModel):
    """
    Shop-specific product enrichment for djstripe.Product.

    This model acts as a standalone product catalog that matches
    Stripe products by ID (similar to subscriptions/metadata.py pattern).

    - djstripe.Product: Source of truth for pricing, currency, Stripe data
    - ShopProduct: UI-specific enrichment (images, categories, flags)

    Manually created in admin, ensuring product_id matches
    actual Stripe products synced to djstripe.
    """

    product_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Stripe Product ID (matches djstripe.Product.id)",
    )

    # UI Fields
    name = models.CharField(
        max_length=255, help_text="Display name (can differ from Stripe product name)"
    )

    slug = models.SlugField(
        unique=True, max_length=100, help_text="URL slug for product detail page"
    )

    description = models.TextField(
        blank=True, help_text="Rich product description for detail page"
    )

    category = models.ForeignKey(
        "ShopCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        help_text="Product category",
    )

    is_new = models.BooleanField(default=False, help_text="Show 'NEW' badge in UI")

    is_popular = models.BooleanField(
        default=False, help_text="Show 'POPULAR' badge in UI"
    )

    sort_order = models.IntegerField(
        default=0, help_text="Display order within category (lower = first)"
    )

    is_active = models.BooleanField(
        default=True, help_text="Show product in shop (can hide without deleting)"
    )

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Shop Product"
        verbose_name_plural = "Shop Products"

    def __str__(self):
        return f"{self.name} ({self.product_id})"

    @property
    def stripe_product(self):
        """
        Get associated djstripe.Product.
        Returns None if product not yet synced from Stripe.
        """
        from djstripe.models import Product as StripeProduct

        try:
            return StripeProduct.objects.get(id=self.product_id)
        except StripeProduct.DoesNotExist:
            return None

    @property
    def primary_image(self):
        """Get first image for thumbnails/cards"""
        return self.images.first()

    @property
    def all_images(self):
        """Get all images ordered by sort_order"""
        return self.images.all()


class ShopProductImage(BaseModel):
    """
    Product images with file upload support.
    Multiple images per product via FK relationship.
    """

    product = models.ForeignKey(
        "ShopProduct",
        on_delete=models.CASCADE,
        related_name="images",
        help_text="Associated product",
    )

    image = models.ImageField(
        upload_to="shop/products/%Y/%m/", help_text="Product image (uploaded via admin)"
    )

    alt_text = models.CharField(
        max_length=255, blank=True, help_text="Alternative text for accessibility"
    )

    sort_order = models.IntegerField(default=0, help_text="Display order (lower = first)")

    class Meta:
        ordering = ["sort_order", "created_at"]
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"

    def __str__(self):
        return f"{self.product.name} - Image {self.sort_order + 1}"


class Basket(BaseModel):
    """
    Shopping basket for pre-checkout items.
    One active basket per user, persists across sessions.
    """

    user = models.ForeignKey(
        "accounts.CustomUser", on_delete=models.CASCADE, related_name="baskets"
    )

    checked_out = models.BooleanField(
        default=False, help_text="True when basket has been converted to an order"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Basket {self.id} - {self.user.email}"

    @property
    def total_items(self):
        """Total number of items (sum of quantities)"""
        return sum(item.quantity for item in self.items.all())

    @property
    def total_amount(self):
        """Total amount in cents"""
        total = 0
        for item in self.items.all():
            if item.product and item.product.default_price:
                total += item.product.default_price.unit_amount * item.quantity
        return total

    @property
    def total_amount_dollars(self):
        """Total amount in dollars"""
        return self.total_amount / 100

    @property
    def is_empty(self):
        """Check if basket has no items"""
        return not self.items.exists()


class BasketItem(BaseModel):
    """
    Individual item in a basket.
    Links to djstripe.Product (source of truth for pricing).
    Access ShopProduct UI data via item.product.shop_metadata
    """

    basket = models.ForeignKey("Basket", on_delete=models.CASCADE, related_name="items")

    product = models.ForeignKey(
        "djstripe.Product",  # FK to djstripe.Product (source of truth)
        on_delete=models.CASCADE,
        related_name="basket_items",
        help_text="Stripe Product (for pricing and checkout)",
    )

    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = [["basket", "product"]]
        ordering = ["-created_at"]

    def __str__(self):
        name = self.product.name if self.product else "Unknown"
        return f"{name} x{self.quantity}"

    @property
    def shop_product(self):
        """
        Get ShopProduct metadata for UI display.
        Accesses via product.shop_metadata (monkey-patched in apps.py)
        """
        return self.product.shop_metadata if self.product else None

    @property
    def line_total(self):
        """Total for this line item in cents"""
        if self.product and self.product.default_price:
            return self.product.default_price.unit_amount * self.quantity
        return 0

    @property
    def line_total_dollars(self):
        """Total for this line item in dollars"""
        return self.line_total / 100


class Order(BaseModel):
    """
    Order for one-time product purchase.
    Created after successful Stripe checkout.

    Note: No primary_product field - access products via:
    - order.basket.items.all() (if basket exists)
    - order.session.line_items (from Stripe Session data)
    """

    user = models.ForeignKey(
        "accounts.CustomUser", on_delete=models.CASCADE, related_name="shop_orders"
    )

    session = models.OneToOneField(
        "djstripe.Session",
        on_delete=models.PROTECT,
        related_name="shop_order",
        help_text="Checkout Session - contains line_items, amounts, payment_intent",
    )

    basket = models.ForeignKey(
        "Basket",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        help_text="Original basket that created this order",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.id} - {self.user.email}"

    @property
    def amount(self):
        """Total amount in cents"""
        return self.session.amount_total if self.session else None

    @property
    def amount_dollars(self):
        """Total amount in dollars"""
        return self.amount / 100 if self.amount else 0

    @property
    def currency(self):
        """Currency from Session"""
        return self.session.currency.upper() if self.session else None

    @property
    def status(self):
        """
        Order status derived from PaymentIntent.
        Source of truth: Stripe PaymentIntent status from stripe_data.
        """
        if not self.session or not self.session.payment_intent:
            return "unknown"

        # PaymentIntent status is stored in stripe_data JSONField
        pi_status = self.session.payment_intent.stripe_data.get("status")

        if not pi_status:
            return "unknown"

        status_map = {
            "succeeded": "paid",
            "processing": "processing",
            "canceled": "canceled",
            "requires_action": "requires_action",
            "requires_payment_method": "payment_failed",
        }
        return status_map.get(pi_status, "pending")

    @property
    def line_items(self):
        """
        All purchased items from Session.
        Supports multi-product orders.
        """
        if not self.session:
            return []

        line_items_data = self.session.stripe_data.get("line_items", {})
        return line_items_data.get("data", [])

    @property
    def products_count(self):
        """Number of line items"""
        return len(self.line_items)

    @property
    def products(self):
        """
        Get all products from basket if available.
        Returns list of djstripe.Product objects.
        """
        if self.basket:
            return [item.product for item in self.basket.items.all()]
        return []

    @property
    def first_product(self):
        """
        Get first product for display purposes (e.g., order list).
        Returns djstripe.Product or None.
        """
        products = self.products
        return products[0] if products else None

    @property
    def customer(self):
        """Stripe Customer via user"""
        return self.user.customer

    @property
    def payment_intent(self):
        """PaymentIntent via Session"""
        return self.session.payment_intent if self.session else None

    @property
    def receipt(self):
        """
        Get the Stripe Charge with receipt URL for this order.

        For one-time payments, Stripe automatically creates a receipt
        via the Charge object when payment succeeds.

        Returns:
            Charge instance with receipt_url if exists, None otherwise
        """
        if self.session and self.session.payment_intent:
            try:
                # Access charges via reverse relationship from PaymentIntent
                # PaymentIntent can have multiple charges (e.g., if first attempt fails)
                # Get the most recent charge by created timestamp
                charge = (
                    self.session.payment_intent.charges.order_by("-created")
                    .first()
                )
                return charge if charge else None
            except Exception:
                # Charge doesn't exist or relationship error
                return None
        return None

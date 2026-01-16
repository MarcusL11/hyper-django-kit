import re
import unicodedata

from django.template.loader import render_to_string
from common.constants import MAX_FILENAME_BASE_LENGTH


def is_datastar(request):
    """
    Check if the incoming request is from Datastar.
    Usage:
    if is_datastar(request):
        # Handle Datastar-specific logic
    """
    return bool(request.headers.get("Datastar-Request"))


def is_staff_user(user):
    """
    Check if user is authenticated staff member.

    Usage:

    @user_passes_test(is_staff_user)
    def your_view(request):
        # view logic here

    """
    return user.is_authenticated and user.is_staff


def is_admin(user):
    """
    Check if the user is an admin.

    Usage:

    @user_passes_test(is_admin)
    def your_view(request):
        # view logic here

    """
    return user.is_authenticated and user.is_admin


def render_toast_notification(
    message_text, message_tags, dismissible=True, auto_dismiss_ms=5000
):
    """
    Render a toast notification component for use with Datastar patching.

    This function renders the cotton toast component with appropriate styling based on
    the message tags. Uses ElementPatchMode.INNER to replace existing toasts.

    Args:
        message_text (str): The message content to display in the toast
        message_tags (str): Django message tags (success, error, warning, info, debug)
        dismissible (bool): Whether the toast can be manually dismissed
        auto_dismiss_ms (int): Auto-dismiss duration in milliseconds (0 to disable)

    Returns:
        str: Rendered HTML for the toast notification

    Usage in views:
        from apps.core.utils import render_toast_notification
        from datastar_py.consts import ElementPatchMode
        from datastar_py import ServerSentEventGenerator as SSE

        # Add a message to Django messages framework
        messages.success(request, "Email set as primary!")

        # Render the toast for Datastar patching
        toast_html = render_toast_notification(
            message_text="Email set as primary!",
            message_tags="success"
        )

        # Include in Datastar response alongside other patches
        return DatastarResponse([
            SSE.patch_elements(...),  # Your main content patch
            SSE.patch_elements(
                mode=ElementPatchMode.INNER,
                selector="#toast-container",
                elements=toast_html
            )
        ])
    """
    # Map Django message tags to toast types
    tag_mapping = {
        "success": "success",
        "error": "info",
        "warning": "info",
        "info": "info",
        "debug": "info",
    }

    # Get the toast type, default to 'info'
    toast_type = tag_mapping.get(message_tags)

    # Prepare context for the toast component
    context = {
        "type": toast_type,
        "dismissible": dismissible,
        "auto_dismiss_ms": auto_dismiss_ms if auto_dismiss_ms > 0 else None,
        "slot": message_text,
    }

    # Render the cotton toast component
    return render_to_string("cotton/toast.html", context)


def sanitize_filename(name: str, default_prefix: str = "file") -> str:
    """
    Sanitize filename for S3 and third-party API compatibility (e.g., Peecho).

    GUARANTEED: Always returns a non-empty, safe filename.

    This function:
    1. Validates input (handles None, empty strings, non-strings)
    2. Normalizes Unicode characters (ñ→n, á→a) using NFD decomposition
    3. Removes non-ASCII characters
    4. Replaces any character that is NOT alphanumeric, dot, underscore, or hyphen with underscore
    5. Cleans up consecutive underscores
    6. Strips leading/trailing underscores
    7. Limits filename length to ~50 characters (preserving extension)
    8. If result would be empty, generates UUID-based fallback name

    This is important for:
    - S3 key compatibility across different systems
    - Peecho API which may have issues with special characters
    - Cross-platform filesystem compatibility

    Args:
        name: Original filename (e.g., "María's Book (2024).pdf")
        default_prefix: Prefix for fallback name when sanitization fails (default: "file")
                       Used to generate contextual names like "avatar_abc123.png"

    Returns:
        Sanitized filename (e.g., "Maria_s_Book_2024.pdf")
        NEVER returns empty string - generates UUID-based fallback if needed.

    Usage:
        from apps.core.utils import sanitize_filename

        # Normal usage
        safe_name = sanitize_filename("Niño's Cuento Especial.pdf")
        # Returns: "Nino_s_Cuento_Especial.pdf"

        # With custom prefix for context-specific fallback
        safe_name = sanitize_filename(filename, default_prefix="avatar")
        # If filename is invalid, returns: "avatar_a1b2c3d4.png"

        # Edge cases - always returns valid filename
        sanitize_filename(None)           # Returns: "file_a1b2c3d4"
        sanitize_filename("")             # Returns: "file_a1b2c3d4"
        sanitize_filename("@#$%")         # Returns: "file_a1b2c3d4"
        sanitize_filename("日本語.jpg")   # Returns: "file_a1b2c3d4.jpg"
    """
    import uuid

    def _generate_fallback(extension: str = "") -> str:
        """Generate UUID-based fallback filename."""
        fallback = f"{default_prefix}_{uuid.uuid4().hex[:8]}"
        return f"{fallback}.{extension}" if extension else fallback

    # Extract extension from original name for fallback (before validation)
    original_ext = ""
    if name and isinstance(name, str) and "." in name:
        original_ext = name.rsplit(".", 1)[-1]
        # Validate extension contains only safe characters
        if not re.match(r"^[a-zA-Z0-9]+$", original_ext):
            original_ext = ""

    # Input validation
    if not name or not isinstance(name, str):
        return _generate_fallback(original_ext)

    # NFD normalization - decompose accented characters
    name = unicodedata.normalize("NFD", name)
    # Remove non-ASCII characters (diacritics, special chars)
    name = name.encode("ascii", "ignore").decode("ascii")
    # Replace any non-alphanumeric/dot/underscore/hyphen with underscore
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    # Remove consecutive underscores
    name = re.sub(r"_+", "_", name)
    # Remove leading/trailing underscores
    name = name.strip("_")

    # Handle case where sanitization removed all characters
    if not name:
        return _generate_fallback(original_ext)

    # Limit length while preserving extension
    name_parts = name.rsplit(".", 1)
    if len(name_parts) == 2:
        base, ext = name_parts
        base = base[:MAX_FILENAME_BASE_LENGTH]
        # If base is empty after truncation, use fallback with preserved extension
        if not base:
            return _generate_fallback(ext)
        return f"{base}.{ext}"

    return name[:MAX_FILENAME_BASE_LENGTH]

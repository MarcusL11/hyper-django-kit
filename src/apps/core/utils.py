from django.template.loader import render_to_string


def is_datastar(request):
    """
    Check if the incoming request is from Datastar.
    Usage:
    if is_datastar(request):
        # Handle Datastar-specific logic
    """
    return bool(request.headers.get("Datastar-Request"))


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

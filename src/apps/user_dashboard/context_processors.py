def user_sidebar_state(request):
    """
    Inject sidebar details state from session into all user_dashboard templates.

    This context processor ensures consistent sidebar state persistence
    across all dashboard pages by automatically reading from the session.

    The sidebar uses Datastar signals to manage collapsible <details> elements.
    When users toggle sections (Account, Subscription, etc.), the state is
    saved to the Django session via the user_sidebar_state view. This context processor
    reads that session data and injects it into all templates so the sidebar
    state persists across page navigation.

    Returns:
        dict: Contains details_account and details_subscription as lowercase strings
              ("true" or "false") for use in Datastar data-signals initialization.

    Example:
        Session contains: {'details': {'account': True, 'subscription': False}}
        Context returned: {'details_account': 'true', 'details_subscription': 'false'}
    """

    # Only inject for authenticated users
    if not request.user.is_authenticated:
        return {}

    user_sidebar_state = request.session.get("user_sidebar_state", {})

    details_account = bool(user_sidebar_state.get("details", {}).get("account"))

    details_subscription = bool(
        user_sidebar_state.get("details", {}).get("subscription")
    )

    return {
        "details_account": details_account,
        "details_subscription": details_subscription,
    }

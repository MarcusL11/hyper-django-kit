# Project Structure

## Folders

```
django_saas_ecom_starterkit/
├── src/
│   ├── apps/
│   │   ├── accounts/              # Custom user model and authentication
│   │   ├── allauth_ui/            # Authentication templates and flows
│   │   ├── core/                  # Shared utilities and validators
│   │   ├── shop/                  # E-commerce functionality
│   │   │   ├── models.py          # Product, Cart, Order models
│   │   │   ├── views.py           # Shop views and checkout
│   │   │   └── templates/         # Shop templates
│   │   ├── subscriptions/         # SaaS subscription management
│   │   │   ├── models.py          # Subscription-related models
│   │   │   ├── views.py           # Pricing, checkout, webhooks
│   │   │   └── templates/         # Landing page, pricing
│   │   ├── user_dashboard/        # User self-service portal
│   │   │   ├── views.py           # Profile, orders, subscriptions
│   │   │   └── templates/         # Dashboard templates
│   │   └── theme/                 # UI styling and Tailwind config
│   │       ├── static_src/        # Tailwind source files
│   │       └── templates/         # Base templates
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py            # Shared settings
│   │   │   ├── development.py    # Development settings
│   │   │   └── production.py     # Production settings
│   │   ├── urls.py                # Root URL configuration
│   │   ├── wsgi.py                # WSGI application
│   │   └── .env.sample            # Environment variables template
│   ├── templates/                 # Global templates
│   │   ├── cookie_consent/        # Cookie banner and preferences
│   │   └── components/            # Shared components
│   └── static/                    # Static assets (images, fonts, etc.)
├── requirements/                  # Dependency files
│   ├── base.in                    # Base dependencies
│   ├── development.in             # Development dependencies
│   └── production.in              # Production dependencies
├── manage.py                      # Django management script
├── .gitignore                     # Git ignore rules
└── README.md                      # This file
```

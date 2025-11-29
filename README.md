<!--markdownlint-disable-->
# HyperDjangoKit

![HyperDjangoKit Logo](src/static/images/hyper-django-kit-logo.png)

**Django SaaS E-Commerce Starter Kit**

---

## Overview

> **Video Walkthrough**: [Watch the 3-Minute Demo](https://www.youtube.com/watch?v=S-SM2AVInTA)

HyperDjangoKit is a production-ready Django starter kit that combines SaaS subscriptions with e-commerce functionality. Built for developers who want to skip the 100+ hours of boilerplate setup and focus on building their unique features.

HyperDjangoKit supports **dual revenue models**:

- **Subscription-based SaaS** - Tiered pricing with recurring revenue (Free, Pro, Enterprise)
- **E-Commerce Shop** - One-time product purchases with full shopping cart functionality

Both systems work seamlessly together, giving you maximum flexibility for your business model.

### Why HyperDjangoKit?

- ⏱️ **Save 100+ Hours** - Skip repetitive authentication, payment, and user management setup
- 💰 **Dual Revenue Streams** - Support both subscriptions and one-time purchases
- 🎨 **Modern Stack** - Django 5.2, Tailwind CSS 4, DaisyUI 5, HATEOAS architecture
- 🔒 **Production-Ready** - Security best practices, environment configs, webhook handling
- 📱 **Responsive Design** - Mobile-first UI with dark mode support
- 🚀 **Quick Start** - Get running locally in under 10 minutes

---

## Features

### 🔐 Authentication

- **Django Allauth** fully configured out of the box
- Email and username-based login
- Social authentication (Google OAuth configured, easily extend to GitHub, Facebook, etc.)
- Password reset and email verification flows
- Session management with activity tracking
- Customized email templates with brand styling

### 💳 Payments & Subscriptions

- **Stripe integration** via dj-stripe for robust payment processing
- Three pre-configured subscription tiers (Free, Pro, Enterprise)
- Monthly and yearly billing options with toggle
- Complete e-commerce checkout flow for one-time purchases
- **Customer billing portal** (Stripe-hosted) for subscription management
- Automatic webhook handling for payment events
- Invoice generation and management
- Subscription lifecycle management (trials, cancellations, upgrades)

### 🎨 Modern Frontend

- **Tailwind CSS 4.x** with **DaisyUI 5.x** components for rapid UI development
- **Django Cotton** for reusable template components
- **Datastar** for HATEOAS-powered reactive UIs without heavy JavaScript frameworks
- Built-in **dark mode** support with persistent user preference
- **Flexoki color scheme** for modern, accessible design
- Fully responsive design (mobile-first approach)
- Alpine.js for interactive components (modals, toggles, etc.)

### 🏗️ Clean Architecture

- **Modular Django app structure** with 7 focused apps:
  - `accounts/` - Custom user model
  - `allauth_ui/` - Authentication templates and flows
  - `core/` - Shared utilities and validators
  - `shop/` - E-commerce functionality
  - `subscriptions/` - SaaS subscription management
  - `user_dashboard/` - User self-service portal
  - `theme/` - UI styling and components
- **PostgreSQL** database support (SQLite for development)
- **Environment-based configuration** (development/production)
- Security best practices built-in (CSRF, CSP, XSS prevention)
- Comprehensive cookie consent management (GDPR-compliant)

---

## Tech Stack

| Category | Technology | Version |
|----------|-----------|---------|
| **Backend** | Django | 5.2.7 |
| **Language** | Python | 3.13 |
| **Database** | PostgreSQL | Latest |
| **Payments** | Stripe (dj-stripe) | 2.10.3 |
| **Authentication** | Django Allauth | 65.12.1 |
| **Frontend** | Tailwind CSS | 4.x |
| **UI Components** | DaisyUI | 5.x |
| **Templates** | Django Cotton | 2.1.3 |
| **Reactivity** | Datastar | 0.6.5 |
| **JavaScript** | Alpine.js | 3.x |

---

## Local Development Setup

### 1. Clone and Navigate

```bash
git clone <your-repo-url>
cd django_saas_ecom_starterkit
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install pip-tools
pip install "pip<24"
pip install pip-tools

# Compile and install dependencies
pip-compile requirements/development.in
pip install -r requirements/development.txt
```

### 4. Configure Environment Variables

Copy the sample environment file and configure:

```bash
cp src/config/.env.sample src/config/.env
```

Generate Django secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Edit `src/config/.env` and configure the following:

```bash
# Environment
DJANGO_ENVIRONMENT=development

# Django Core
DJANGO_SECRET_KEY=your-generated-secret-key-here
ALLOWED_HOSTS=127.0.0.1,localhost

# Database (PostgreSQL - optional, SQLite used by default in development)
POSTGRES_DB=hyperdjangokit_db
POSTGRES_USER=hyperdjangokit_admin
POSTGRES_PASSWORD=your-password

# Stripe (get from https://dashboard.stripe.com/test/apikeys)
STRIPE_TEST_SECRET_KEY=sk_test_your_test_key
STRIPE_LIVE_SECRET_KEY=sk_live_your_live_key
DJSTRIPE_TEST_WEBHOOK_SECRET=whsec_your_test_webhook_secret
DJSTRIPE_LIVE_WEBHOOK_SECRET=whsec_your_live_webhook_secret

# Email (Production only)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
```

### 5. Run Database Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 7. Install Tailwind Dependencies

```bash
python manage.py tailwind install
```

### 8. Run Development Server

**Option 1: Run both Django and Tailwind together** (Recommended)

```bash
python manage.py runserver_plus 0:8000
```

Then in a separate terminal:

```bash
python manage.py tailwind start
```

**Option 2: Use the combined development command**

```bash
# Install django-extensions if not already installed
pip install django-extensions

# Run both servers in parallel (requires tmux or screen)
python manage.py tailwind dev
```

Visit <http://127.0.0.1:8000> in your browser.

---

## Environment Configuration

### DJANGO_ENVIRONMENT Variable

The project uses environment-based settings controlled by the `DJANGO_ENVIRONMENT` variable:

- **`development`** (default) - Local development
  - `DEBUG = True`
  - Console email backend
  - Stripe test mode
  - SQLite database (or PostgreSQL if configured)
  - Debug toolbar enabled

- **`production`** - Production deployment
  - `DEBUG = False`
  - SMTP email backend
  - Stripe live mode
  - PostgreSQL database required
  - Enhanced security settings (SECURE_SSL_REDIRECT, HSTS, etc.)

### Required Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_ENVIRONMENT` | Environment mode (`development`/`production`) | `development` |
| `DJANGO_SECRET_KEY` | Django secret key (generate new for production) | Required |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1` |
| `STRIPE_TEST_SECRET_KEY` | Stripe test mode secret key | Required |
| `STRIPE_LIVE_SECRET_KEY` | Stripe live mode secret key | Required for production |
| `DJSTRIPE_TEST_WEBHOOK_SECRET` | Stripe test webhook signing secret | Required |
| `DJSTRIPE_LIVE_WEBHOOK_SECRET` | Stripe live webhook signing secret | Required for production |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_DB` | PostgreSQL database name | `hyperdjangokit_db` |
| `POSTGRES_USER` | PostgreSQL username | `hyperdjangokit_admin` |
| `POSTGRES_PASSWORD` | PostgreSQL password | Required if using PostgreSQL |
| `EMAIL_HOST` | SMTP email host | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP email port | `587` |
| `EMAIL_HOST_USER` | SMTP username | Required for production |
| `EMAIL_HOST_PASSWORD` | SMTP password | Required for production |

---

## Project Structure

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

---

## Key Features Walkthrough

### 1. Landing Page

- Hero section with value proposition
- Feature showcase with 6 key areas
- Customer testimonials carousel
- Interactive pricing section with monthly/yearly toggle
- FAQ section with collapsible answers
- Responsive navigation with mobile menu

### 2. Authentication System

- Login with email or username
- Google OAuth (easily extend to other providers)
- Email verification for new signups
- Password reset flow
- Session management
- Customized, branded email templates

### 3. Subscription Management

- Three-tier pricing (Free, Pro, Enterprise)
- Monthly and yearly billing options
- Stripe Checkout integration
- Customer portal for subscription changes
- Automatic webhook handling for:
  - Successful payments
  - Failed payments
  - Subscription cancellations
  - Plan upgrades/downgrades

### 4. E-Commerce Shop

- Product catalog with images and descriptions
- Shopping cart functionality
- One-time payment checkout via Stripe
- Order history in user dashboard
- Inventory management (admin)

### 5. User Dashboard

- Profile management
- Order history
- Subscription status and management
- Billing information
- Account settings

### 6. Cookie Consent

- GDPR-compliant cookie banner
- Cookie preference management page
- Granular cookie group controls (Required, Analytics, Marketing)
- Persistent user preferences

---

## Stripe Setup

### 1. Create Stripe Account

Sign up at [https://stripe.com](https://stripe.com)

### 2. Get API Keys

- Navigate to **Developers → API Keys**
- Copy **Secret key** (starts with `sk_test_` for test mode)
- Add to `.env` as `STRIPE_TEST_SECRET_KEY`

### 3. Configure Webhook

- Navigate to **Developers → Webhooks**
- Click **Add endpoint**
- URL: `http://localhost:8000/stripe/webhook/` (for development)
- Select events:
  - `customer.subscription.created`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.payment_succeeded`
  - `invoice.payment_failed`
  - `checkout.session.completed`
- Copy **Signing secret** (starts with `whsec_`)
- Add to `.env` as `DJSTRIPE_TEST_WEBHOOK_SECRET`

### 4. Test Mode

- Use test cards from [Stripe Testing](https://stripe.com/docs/testing)
- Successful payment: `4242 4242 4242 4242`
- Requires authentication: `4000 0025 0000 3155`
- Declined: `4000 0000 0000 9995`

---

## Deployment

### Environment Variables for Production

Ensure the following are set in your production environment:

```bash
DJANGO_ENVIRONMENT=production
DJANGO_SECRET_KEY=<generate-new-secret-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
STRIPE_LIVE_SECRET_KEY=sk_live_your_live_key
DJSTRIPE_LIVE_WEBHOOK_SECRET=whsec_your_live_webhook_secret
POSTGRES_DB=your_production_db
POSTGRES_USER=your_production_user
POSTGRES_PASSWORD=your_production_password
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
```

### Deployment Checklist

- [ ] Set `DJANGO_ENVIRONMENT=production`
- [ ] Generate new `DJANGO_SECRET_KEY`
- [ ] Configure production database (PostgreSQL)
- [ ] Set up Stripe live mode webhook
- [ ] Configure email backend (SMTP)
- [ ] Set up static file serving (WhiteNoise or CDN)
- [ ] Configure ALLOWED_HOSTS
- [ ] Run `python manage.py collectstatic`
- [ ] Run `python manage.py migrate`
- [ ] Create superuser for admin access
- [ ] Test payment flows in live mode
- [ ] Set up SSL/TLS certificate

### Recommended Platforms

- **Railway** - Simple Django deployment with PostgreSQL
- **Render** - Automatic deployments from Git
- **Heroku** - Classic PaaS with extensive documentation
- **DigitalOcean App Platform** - Managed platform with databases
- **AWS Elastic Beanstalk** - Scalable AWS infrastructure

---

## Customization Guide

### Branding

1. **Logo**: Replace `src/static/images/hyper-django-kit-logo.png`
2. **Favicons**: Replace files in `src/static/images/`
3. **Colors**: Update Flexoki theme in `src/apps/theme/static_src/tailwind.config.js`
4. **Fonts**: Change Google Fonts import in base templates

### Subscription Tiers

Edit pricing in `src/apps/subscriptions/views.py`:

```python
plans_monthly = [
    {
        "name": "Your Plan Name",
        "price": "$XX",
        "stripe_price_id": "price_your_stripe_id",
        "features": ["Feature 1", "Feature 2"],
    }
]
```

### Email Templates

Customize email templates in:

- `src/apps/allauth_ui/templates/account/email/`

### Landing Page Content

Edit content in:

- `src/apps/subscriptions/templates/subscriptions/landing/index.html`

---

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run specific app tests
pytest src/apps/shop/tests/

# Run with coverage
pytest --cov=src/apps --cov-report=html
```

### Test Stripe Integration

Use Stripe test mode cards:

- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 9995`
- 3D Secure: `4000 0025 0000 3155`

---

## Troubleshooting

### Tailwind Styles Not Updating

```bash
# Restart Tailwind watcher
python manage.py tailwind start
```

### Database Migration Issues

```bash
# Reset migrations (development only!)
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
python manage.py makemigrations
python manage.py migrate
```

### Stripe Webhooks Not Working

1. Check webhook URL is accessible
2. Verify webhook secret is correct in `.env`
3. Check webhook event types are selected
4. Review webhook logs in Stripe dashboard

---

## Acknowledgments & Inspiration

This project was built with inspiration from:

- **[Flexoki](https://stephango.com/flexoki)** - Beautiful, accessible color scheme by Steph Ango
- **[LearnDjango](https://learndjango.com/)** - Django best practices by William S. Vincent
- **[django-structurator](https://github.com/maulik-0207/django-structurator)** - Project organization patterns
- **[SaaS Pegasus](https://www.saaspegasus.com/)** - SaaS architecture insights by Cory Zue

---

## License

[Add your license information]

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## Support

For questions or issues:

- Open an issue on GitHub
- Check the documentation
- Review Stripe integration guide

---

**Built with ❤️ using Django**

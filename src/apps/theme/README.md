# Theme CSS Architecture

This document explains the CSS structure and management strategy for this Django project using both the Nexus DaisyUI template and django-tailwind.

## Overview

This project uses a **dual CSS system** with clear separation of concerns:

1. **Nexus Template CSS** - Static foundation (purchased template)
2. **Django-Tailwind CSS** - Dynamic utilities (project-specific)

---

## CSS Files

### 1. Nexus Template CSS (Static Foundation)

**Location**: `theme/static/assets/app.css`

**Details**:
- **Source**: Nexus DaisyUI template (purchased from [nexus.daisyui.com](https://nexus.daisyui.com/))
- **Size**: ~600KB (15,345 lines, minified)
- **Version**: Tailwind CSS v4.1.12 + DaisyUI v5.0.43
- **Status**: ⚠️ **DO NOT MODIFY** - This is a static asset from the template

**Contains**:
- Complete DaisyUI component library (buttons, cards, modals, toasts, etc.)
- Theme system with multiple color schemes (light, dark, contrast, material, etc.)
- Base Tailwind utilities
- Custom Nexus-specific components and styles

**Purpose**: Provides the complete design system foundation for the application.

---

### 2. Django-Tailwind CSS (Dynamic Utilities)

**Location**: `theme/static/css/dist/styles.css`

**Details**:
- **Source**: Generated from `theme/static_src/src/styles.css`
- **Size**: ~180KB (dynamically generated)
- **Version**: Tailwind CSS v4.1.14 + DaisyUI v5.0.43
- **Status**: ✅ **Automatically generated** - Rebuilds when templates change

**Contains**:
- Tailwind utilities specific to YOUR templates
- Custom dark mode configuration for `data-theme` attributes
- Project-specific utility classes
- Only classes actually used in your `.html`, `.py`, and `.js` files

**Purpose**: Extends Nexus with custom utilities and ensures compatibility with Nexus's theme system.

---

## File Structure

```
theme/
├── README.md                     # This file
│
├── static/                       # Compiled/static assets
│   ├── assets/
│   │   └── app.css              # Nexus template CSS (static, DO NOT EDIT)
│   │
│   ├── css/
│   │   └── dist/
│   │       └── styles.css       # Django-tailwind generated CSS
│   │
│   ├── images/                  # Static images
│   ├── js/                      # JavaScript files
│   └── ...
│
├── static_src/                  # Django-tailwind source files
│   ├── src/
│   │   └── styles.css           # Tailwind configuration (EDIT THIS)
│   │
│   ├── package.json             # npm dependencies
│   ├── postcss.config.js        # PostCSS configuration
│   ├── node_modules/            # npm packages (git ignored)
│   └── package-lock.json
│
└── templates/                   # Django templates
    ├── base.html
    └── cotton/
        └── toast.html
```

---

## CSS Loading Order

In your base templates, CSS is loaded in this specific order:

```html
<head>
  <!-- 1. Nexus Foundation (loads first) -->
  <link rel="stylesheet" href="{% static 'assets/app.css' %}" />

  <!-- 2. Django-Tailwind Utilities (loads second, can override) -->
  {% load tailwind_tags %}
  {% tailwind_css %}

  <!-- 3. Custom overrides (optional) -->
  {% block extra_css %}{% endblock %}
</head>
```

**Why this order?**
- Nexus provides base styles and components
- Django-tailwind adds project-specific utilities and can override if needed
- Extra CSS block for one-off page-specific styles

---

## Dark Mode Configuration

### How It Works

The Nexus template uses DaisyUI's `data-theme` attribute for theme switching:

```html
<html data-theme="light">  <!-- or "dark", "contrast", etc. -->
```

JavaScript toggles this attribute when users click the theme switcher button.

### Custom Dark Mode Variant

We've configured django-tailwind to make `dark:` utilities work with `data-theme="dark"`:

**Configuration** (`theme/static_src/src/styles.css`):
```css
@custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *));
```

**Result**: Now `dark:hidden`, `dark:inline`, `dark:bg-blue-500`, etc. all work with the theme toggle!

**Example**:
```html
<!-- Logo that switches based on theme toggle -->
<img class="hidden dark:inline" src="logo-dark.png" />
<img class="inline dark:hidden" src="logo-light.png" />
```

---

## Development Workflow

### When to Rebuild Django-Tailwind

#### ✅ Rebuild Required:

Run this command:
```bash
python manage.py tailwind build
```

**Scenarios:**
1. You add NEW Tailwind utility classes to templates (e.g., `bg-purple-800`, `grid-cols-7`)
2. You use NEW `dark:` variants (e.g., `dark:text-green-500`)
3. You modify `theme/static_src/src/styles.css`
4. You create custom components with new class combinations

#### ❌ No Rebuild Needed:

**Scenarios:**
1. Using existing DaisyUI components from Nexus (buttons, cards, modals, etc.)
2. Changing HTML structure without adding new Tailwind classes
3. Modifying JavaScript or Python logic
4. Using classes that were already generated in previous builds

---

## Commands

### Development Mode (Watch for Changes)

Automatically rebuilds when you save template files:

```bash
python manage.py tailwind start
```

**Use this during active development** - keeps a process running that watches for changes.

### Production Build

One-time build with optimizations:

```bash
python manage.py tailwind build
```

**Use this:**
- Before committing code
- Before deploying to production
- After adding new utility classes

### Check Installation

Verify django-tailwind is configured correctly:

```bash
python manage.py tailwind check
```

---

## Configuration Files

### Django Settings (`project/settings.py`)

```python
TAILWIND_APP_NAME = "theme"
TAILWIND_APPS = ["tailwind", "theme"]
```

### Tailwind Source (`theme/static_src/src/styles.css`)

```css
@import "tailwindcss";

/**
 * Dark mode configuration for DaisyUI's data-theme attribute
 */
@custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *));

/**
 * DaisyUI Plugin Configuration
 */
@plugin "daisyui" {
  themes: light --default, dark --prefersdark;
}

/**
 * Source paths - Tailwind scans these for utility classes
 */
@source "../../../**/*.{html,py,js}";
```

### PostCSS Configuration (`theme/static_src/postcss.config.js`)

```javascript
module.exports = {
  plugins: {
    "@tailwindcss/postcss": {},
    "postcss-simple-vars": {},
    "postcss-nested": {}
  },
}
```

---

## Troubleshooting

### Issue: Dark mode utilities not working

**Symptom**: `dark:hidden`, `dark:inline` don't respond to theme toggle

**Solution**:
1. Verify `@custom-variant dark` is in `theme/static_src/src/styles.css`
2. Rebuild: `python manage.py tailwind build`
3. Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+F5)

### Issue: New utility classes not appearing

**Symptom**: Added `bg-purple-800` to template but it's not styled

**Solution**:
1. Rebuild: `python manage.py tailwind build`
2. Verify the class is in the `@source` paths
3. Check browser console for 404 errors on CSS files

### Issue: Toast notifications not working

**Symptom**: Toast component has no styling

**Solution**:
- Toast styles come from Nexus CSS (`app.css`)
- Verify `<link rel="stylesheet" href="{% static 'assets/app.css' %}" />` is in your template
- Check that `theme/static/assets/app.css` exists

### Issue: CSS conflicts or unexpected styling

**Symptom**: Styles behaving oddly, conflicts between files

**Solution**:
1. Check CSS loading order (Nexus first, then django-tailwind)
2. Use browser DevTools to inspect which CSS file is winning
3. Consider using more specific selectors or `!important` sparingly
4. Clear Django static files cache: `python manage.py collectstatic --clear`

### Issue: Rebuild is slow or fails

**Symptom**: `tailwind build` takes forever or errors

**Solution**:
1. Check `node_modules` exists: `cd theme/static_src && npm install`
2. Reduce `@source` scope if scanning too many files
3. Check for syntax errors in templates that might confuse the scanner

---

## Best Practices

### ✅ DO:

- Use DaisyUI components from Nexus for consistency (buttons, cards, modals)
- Add custom Tailwind utilities when you need project-specific styling
- Rebuild django-tailwind after adding new utility classes
- Document any custom components or patterns you create
- Keep the `@custom-variant dark` configuration for theme toggle compatibility

### ❌ DON'T:

- Modify `theme/static/assets/app.css` directly (it's from the template)
- Remove the `{% tailwind_css %}` tag from base templates
- Commit `theme/static_src/node_modules/` to version control
- Use inline styles when Tailwind utilities would work
- Create duplicate components that already exist in Nexus

---

## Performance Notes

### File Sizes

- **Nexus CSS**: ~600KB (but includes everything from the template)
- **Django-Tailwind CSS**: ~180KB (only utilities you use)
- **Total**: ~780KB of CSS

### Optimization Opportunities

1. **PurgeCSS is automatic**: django-tailwind only generates classes found in your templates
2. **Minimize custom utilities**: Use Nexus components when possible
3. **Lazy load CSS**: Consider splitting CSS by route if needed
4. **CDN/Caching**: Both CSS files should be cached aggressively in production

### Production Checklist

Before deploying:
- [ ] Run `python manage.py tailwind build` for optimized CSS
- [ ] Test theme toggle functionality
- [ ] Verify all pages load CSS correctly
- [ ] Check browser console for CSS 404 errors
- [ ] Test dark mode utilities work as expected

---

## Version History

### Current Versions

- **Nexus Template**: v3.0 (Tailwind CSS v4.1.12)
- **Django-Tailwind**: Tailwind CSS v4.1.14 + DaisyUI v5.0.43
- **Python Package**: django-tailwind (latest)

### Changelog

#### 2025-10-28
- ✅ Added `@custom-variant dark` configuration for `data-theme` support
- ✅ Fixed logo toggle to work with Nexus theme switcher
- ✅ Verified toast notifications work with dual CSS system
- ✅ Created this documentation

---

## Resources

### Documentation

- [Nexus Template Docs](https://nexus.daisyui.com/)
- [Django-Tailwind Docs](https://django-tailwind.readthedocs.io/)
- [Tailwind CSS v4 Docs](https://tailwindcss.com/docs)
- [DaisyUI Component Library](https://daisyui.com/components/)

### Useful Commands

```bash
# Install/update dependencies
cd theme/static_src && npm install

# Development watch mode
python manage.py tailwind start

# Production build
python manage.py tailwind build

# Check configuration
python manage.py tailwind check

# Collect static files
python manage.py collectstatic
```

---

## Questions or Issues?

If you encounter problems or have questions about the CSS architecture:

1. Check the troubleshooting section above
2. Review the django-tailwind logs: `python manage.py tailwind start` (shows build output)
3. Inspect browser DevTools to see which CSS file is applying styles
4. Check this documentation for configuration examples

---

**Last Updated**: October 28, 2025
**Maintained By**: Project Team
**Template Source**: [Nexus DaisyUI Template](https://nexus.daisyui.com/)

# Blog Components Documentation

This directory contains reusable django-cotton components for the blog feature, built with DaisyUI 5.0 and TailwindCSS 4.1.

## Components Overview

### 1. `_blog_card.html`
Displays a single blog post in a card format.

**Props:**
- `post` (required): Blog post object
- `featured` (optional, default: False): Whether to display as a featured post (larger, more prominent)
- `show_author` (optional, default: True): Whether to display author information

**Features:**
- Responsive image with hover effect (scale on hover)
- Category badges (shows up to 3)
- Publication date with calendar icon
- Title with line clamping
- Excerpt/summary with line clamping
- Author avatar (uses first letter of name as placeholder)
- "Read More" button
- Different sizes for featured vs. regular cards

**Usage:**
```django
<!-- Regular blog card -->
<c-blogs._blog_card :post="post" />

<!-- Featured blog card -->
<c-blogs._blog_card :post="post" featured="True" />

<!-- Without author info -->
<c-blogs._blog_card :post="post" show_author="False" />
```

### 2. `_blog_pagination.html`
Displays pagination controls for blog post lists.

**Props:**
- `page_obj` (required): Django Paginator page object

**Features:**
- Previous/Next buttons with icons
- Smart page number display (shows first, last, current, and 2 pages on each side)
- Ellipsis (...) for gaps in page numbers
- Active page highlighting
- Preserves category filter in URLs
- Disabled state for unavailable navigation
- Fully accessible with ARIA labels

**Usage:**
```django
<c-blogs._blog_pagination :page_obj="page_obj" />
```

### 3. `_category_filter.html`
Category filtering component with responsive design.

**Props:**
- `categories` (required): QuerySet or list of category objects
- `active_category` (optional, default: ""): Currently selected category object

**Features:**
- Mobile: Dropdown menu with filter icon
- Desktop: Tab navigation
- "All Categories" option
- Active category indication
- Checkmark icon for selected category (mobile)
- Resets to page 1 when changing categories

**Usage:**
```django
<c-blogs._category_filter
  :categories="categories"
  :active_category="active_category"
/>
```

### 4. `_blog_skeleton.html`
Loading skeleton for blog cards.

**Props:**
- `featured` (optional, default: False): Whether to display as featured size

**Features:**
- Matches blog card dimensions and layout
- Animated pulse effect
- Responsive sizing
- Useful for initial page load or dynamic content loading

**Usage:**
```django
<!-- Regular skeleton -->
<c-blogs._blog_skeleton />

<!-- Featured skeleton -->
<c-blogs._blog_skeleton featured="True" />
```

## Design System

### Colors
The components use DaisyUI semantic colors:
- `primary`: Main brand color (used for badges, links, CTAs)
- `secondary`: Secondary brand color
- `accent`: Accent color
- `base-100`: Main background
- `base-200`: Secondary background
- `base-300`: Border color
- `base-content`: Text color with opacity variants

### Typography
- Headings: `font-heading` class
- Body text: `font-body` class
- Line clamping: `line-clamp-2`, `line-clamp-3` for text truncation

### Spacing
- Cards: 4-6 padding on mobile, larger on desktop
- Gaps: 6-8 between cards
- Consistent mb (margin-bottom) for vertical rhythm

### Icons
Uses Iconify with Lucide icon set:
- Calendar: `lucide--calendar`
- Arrow Right: `lucide--arrow-right`
- Chevrons: `lucide--chevron-left`, `lucide--chevron-right`
- Filter: `lucide--filter`
- Check: `lucide--check`
- Grid: `lucide--grid-3x3`
- Book: `lucide--book-open`
- Sparkles: `lucide--sparkles`
- Star: `lucide--star`

## Accessibility Features

All components include:
- Semantic HTML5 elements (`<article>`, `<nav>`, `<time>`)
- ARIA labels and roles
- `aria-current="page"` for active navigation items
- Proper button types and disabled states
- Keyboard navigation support (via DaisyUI)
- Focus indicators
- Alt text for images

## Internationalization

All user-facing text uses Django's `{% trans %}` template tag for i18n support:
- English and Spanish translations supported
- Dates formatted using Django's date filters
- RTL support through DaisyUI

## Responsive Breakpoints

- Mobile: Default (< 768px)
- Tablet: `md:` (>= 768px)
- Desktop: `lg:` (>= 1024px)

### Component Behavior:
- **Category Filter**: Dropdown on mobile, tabs on desktop (lg+)
- **Blog Grid**: 1 column → 2 columns (md) → 3 columns (lg)
- **Featured Post**: Full width on all screens, larger text on desktop
- **Card Padding**: Increases from 4 to 6 on medium+ screens

## Integration with Blog App

### Required Model Fields

The blog post model should include:
- `title`: CharField
- `slug`: SlugField (for URLs)
- `summary`: TextField (excerpt/description)
- `content`: MarkdownxField or TextField
- `date`: DateField (publication date)
- `featured_image`: ImageField (optional)
- `author`: ForeignKey to User
- `categories`: ManyToManyField to Category
- `published`: BooleanField

### View Context Requirements

The blog_list view should provide:
```python
context = {
    'blogs': paginated_posts,  # QuerySet of published posts
    'page_obj': paginator.get_page(page_number),  # Paginator object
    'categories': Category.objects.all(),  # All categories
    'active_category': category_obj or None,  # Selected category
    'featured_post': featured_post or None,  # Optional featured post
}
```

## Customization Tips

### Adjusting Card Layout
Modify aspect ratios in `_blog_card.html`:
```django
<!-- Change from 4:3 to 16:9 for regular cards -->
<figure class="aspect-[16/9]">  <!-- was aspect-[4/3] -->
```

### Adding More Categories to Badge Display
In `_blog_card.html`, change the slice:
```django
{% for category in post.categories.all|slice:":5" %}  <!-- was :3 -->
```

### Changing Grid Layout
In `blog_list.html`, modify the grid classes:
```django
<!-- 4 columns on extra large screens -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
```

### Custom Empty State
Replace the empty state section in `blog_list.html` with your own design.

## Children's Book Platform Aesthetic

The design maintains a friendly, colorful yet professional look:
- Gradient backgrounds with soft pastel colors
- Rounded corners on cards (`rounded-xl`, `rounded-3xl`)
- Smooth hover transitions (scale, shadow, color)
- Playful iconography from Lucide
- Generous whitespace
- Large, readable typography
- Decorative elements (gradient orbs)

## Performance Considerations

- Images use `loading="lazy"` for lazy loading
- Skeleton screens for perceived performance
- CSS-only animations (no JavaScript required)
- Efficient Tailwind classes (purged in production)
- Minimal HTTP requests (icons via Iconify)

## Browser Support

Compatible with:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Android)

## Future Enhancements

Potential additions:
- Search functionality
- Tag filtering (in addition to categories)
- Reading time estimates
- Social sharing buttons
- Related posts section
- Comment system integration
- Newsletter signup in empty state

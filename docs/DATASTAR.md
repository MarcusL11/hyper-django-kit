<!--markdownlint--disable-->
# The Datastar Way

A practical guide to building real-time, collaborative web apps and simple websites using Datastar, focusing on performance and a streamlined mental model.

---

## Core Concepts

### State in the Right Place

Most state should live in the backend. Since the frontend is exposed to the user, the backend should be the source of truth for your application state.

### Patch Elements & Signals

Since the backend is the source of truth, it should drive the frontend by patching (adding, updating and removing) HTML elements and signals.

### In Morph We Trust

Morphing ensures that only modified parts of the DOM are updated, preserving state and improving performance. This allows you to send down large chunks of the DOM tree (all the way up to the html tag), sometimes known as “fat morph”, rather than trying to manage fine-grained updates yourself. If you want to explicitly ignore morphing an element, place the data-ignore-morph attribute on it.

### SSE Responses

SSE responses allow you to send 0 to n events, in which you can patch elements, patch signals, and execute scripts. Since event streams are just HTTP responses with some special formatting that SDKs can handle for you, there’s no real benefit to using a content type other than text/event-stream.

### Compression

Since SSE responses stream events from the backend and morphing allows sending large chunks of DOM, compressing the response is a natural choice. Compression ratios of 200:1 are not uncommon when compressing streams using Brotli. Read more about compressing streams in this article.

### Use Backend Templating

Since your backend generates your HTML, you can and should use your templating language to keep things DRY (Don’t Repeat Yourself).

### Use Signals Sparingly

Overusing signals typically indicates trying to manage state on the frontend. Favor fetching current state from the backend rather than pre-loading and assuming frontend state is current. A good rule of thumb is to only use signals for user interactions (e.g. toggling element visibility) and for sending new state to the backend (e.g. form input fields).

### Page Navigation

Page navigation hasn't changed in 30 years. Use the anchor element (<a>) to navigate to a new page, or a redirect if redirecting from the backend. For smooth page transitions, use the View Transition API.

### Browser History

Browsers automatically keep a history of pages visited. As soon as you start trying to manage browser history yourself, you are adding complexity. Each page is a resource. Use anchor tags and let the browser do what it is good at.

### CQRS

CQRS, in which commands (writes) and requests (reads) are segregated, makes it possible to have a single long-lived request to receive updates from the backend (reads), while making multiple short-lived requests to the backend (writes). It is a powerful pattern that makes real-time collaboration simple using Datastar. Here’s a basic example.

```html
<div id="main" data-init="@get('/cqrs_endpoint')">
  <button data-on:click="@post('/do_something')">
    Do something
  </button>
</div>

```

### Loading Indicators

Loading indicators inform the user that an action is in progress. Use the data-indicator attribute to show loading indicators on elements that trigger backend requests. Here’s an example of a button that shows a loading element while waiting for a response from the backend.

```html
<div>
  <button data-indicator:_loading
    data-attr:disabled="$_loading"
    data-on:click="@post('/perform_action')"
  >
    Perform Action
  </button>
  <span data-show="$_loading"
    style="display: none;"
  >
    Loading...
  </span>
</div>

```

### Optimistic Updates

Optimistic updates (also known as optimistic UI) are when the UI updates immediately as if an operation succeeded, before the backend actually confirms it. It is a strategy used to makes web apps feel snappier, when it in fact deceives the user. Imagine seeing a confirmation message that an action succeeded, only to be shown a second later that it actually failed. Rather than deceive the user, use loading indicators (or progress indicators) to show the user that the action is in progress, and only confirm success from the backend.

### Accessibility

The web should be accessible to everyone. Datastar stays out of your way and leaves accessibility to you. Use semantic HTML, apply ARIA where it makes sense, and ensure your app works well with keyboards and screen readers. Here’s an example of using adata-attr to apply ARIA attributes to a button than toggles the visibility of a menu. Here’s an example.

```html
<button data-on:click="$_menuOpen = !$_menuOpen"
  data-attr:aria-expanded="$_menuOpen"
  aria-controls="menu"
>
  Open/Close Menu
</button>
<div id="menu" data-attr:aria-hidden="$_menuOpen">
  ...
</div>
```

### Hypermedia System

- Respond with HTML, not JSON.
- Use `data-on` attributes for hypermedia controls:
  - Example: `data-on:click="@get('/endpoint')"`
  - Any element/event can trigger HTTP requests.
  - Backend Actions: `@get('/endpoint')`

### Fat Morphing

- Respond with the entire modified page.
- Morphing algorithm updates only changed elements.
- Suitable for collaborative apps: all users see the same updated page.
- Similar to htmx's `hx-boost`, but retains elements.

### SSE (Server-Sent Events)

- Open long-lived connections to stream responses.
- Use HTTP/2 or HTTP/3 for more connections.
- Initial load: `text/html`, updates: `text/event-stream`.

### Brotli Compression

- Compress the whole stream for efficiency.
- Increase context window for better compression.
- Outperforms gzip, especially for streaming.

---

## `data-on` Attribute

- Central to Datastar; generalizes event handling.
- Supports non-standard events:
  - `data-init`, `data-on-intersect`, `data-on-interval`, `data-on-signal-patch`
- Expressions allow for advanced logic:
  - Example: `data-on:click="confirm('Are you sure?') && @delete('/examples/delete_row/0')"`
- Use request indicators for UX:
  - `data-indicator:_fetching`, `data-attr:disabled="$_fetching"`

---

## Fat Morphing Details

- Send entire page, not fragments.
- Reduces endpoint complexity.
- Use event bubbling for efficiency.
- Prefer `pointerdown/mousedown` over `click` for responsiveness.

#### Morphing Algorithms

- Patch elements: Create, Update, Delete.
- Retains unchanged elements.
- See [Idiomorph](https://github.com/bigskysoftware/idiomorph), [Morphlex](https://github.com/yippee-fun/morphlex).

---

## Optimal Fat Morphing: CQRS Pattern

- Limit endpoints that change the view.
- Separate Commands (Create, Update, Delete) from Queries (Read).
- Commands change data, Queries update views.
- Use Publish-Subscribe for event-driven architecture.
- App becomes `view = function(state)`:
  - All data processed on backend.
  - Page re-computed on every data change.

---

## SSE for Real-Time Apps

- Stream updates efficiently.
- Use modern HTTP protocols for scalability.

---

## Brotli Compression

- Designed for HTTP streaming.
- High compression ratios over streams.
- Adjustable context window for performance.
- Outperforms gzip (2-3x better).

#### Stats

- Example: 26 MB stream compressed to 190 kB (137x reduction).
- Example: 6 MB stream compressed to 14 kB (429x reduction).

#### Comparison with gzip

- Gzip: fixed 32 kB window, not optimized for streaming.
- Brotli: tunable window, better streaming support.

---

## URL Design

- Use query parameters or request body to store states in the URL.
- Avoid path parameters as they enforce a hierarchical structure.

### Multiplayer

- Multiplayer: real-time + collaborative.
- Multiplayer is the default behavior, since the views are shared to all users.
- The function rendering the view doesn't distinguish users, so that it renders the same view for everyone.
- To show user-specific views, create them in that same function, and send them to that user's stream only.

- Add client-side reactivity to a page.
- Start with 0 signals.
- Datastar stores all signals in one object in every request, so the server still has full access to the client's state
- Declare all signals with `__ifmissing` to prevent existing signals getting patched: `data-signals:foo__ifmissing="1"`
- Add an underscore to not include that signal in requests to the backend: `data-signals:_foo="1"`
- Signals are not stored persistently, and are not shared between tabs.

# Limitations

- No [progressive enhancement](https://en.wikipedia.org/wiki/Progressive_enhancement).
  - JavaScript is needed.
  - Consider alternatives: htmx's [`hx-boost`](https://htmx.org/attributes/hx-boost/), [Alpine](https://alpinejs.dev/)'s [Alpine-Ajax](https://alpine-ajax.js.org/)
- Modern browsers only (no IE11 support)
- No History API support
  - Add new history entry: [redirect](https://data-star.dev/how_tos/redirect_the_page_from_the_backend) to a new page
  - How to deal with state
    - Make state a part of the URL
    - Put state in cookie
- Offline functionality: uncharted territory, consider using [Service Workers](https://github.com/mvolkmann/htmx-offline).

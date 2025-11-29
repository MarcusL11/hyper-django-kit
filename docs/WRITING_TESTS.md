<!--markdownlint-disable-->
## Writing Tests

### When to write a test

- For every new feature or bug fix.
- When you add or change business logic (models, views, forms, serializers, etc.).
- When fixing a bug, write a test that would fail before the fix and pass after.
- Before refactoring critical code, to ensure you don’t break existing behavior.

### What to write tests for

- **Models:** Custom methods, signals, constraints, and properties.
- **Views:** Correct responses, permissions, redirects, and error handling.
- **Forms/Serializers:** Validation logic and cleaned data.
- **APIs:** Endpoints, authentication, and expected data.
- **Utilities/Helpers:** Any custom logic or calculations.
- **Permissions:** Access control and user roles.
- **Templates:** (Optional) Key template logic, context variables.

### What not to test

- Django’s built-in functionality (unless you override it).
- Third-party packages (unless you extend/customize them).
- Trivial code (like simple assignments or getters/setters).

### Why write tests?

- To catch bugs early.
- To make refactoring safe.
- To document expected behavior.
- To ensure code quality and reliability.

# DJANGO STYLE GUIDE

## Business Logic

>[!NOTE] Inspiration from [Django-Styleguide](https://github.com/HackSoftware/Django-Styleguide/tree/master)

**Business logic should live in:**

- Services - functions, that mostly take care of writing things to the database.
- Selectors - functions, that mostly take care of fetching things from the database.
- Model properties (with some exceptions).
- Model `clean` method for additional validations (with some exceptions).

**Business logic should not live in:**

- APIs and Views.
- Serializers and Forms.
- Form tags.
- Model save method.
- Custom managers or querysets.
- Signals.

**Model properties vs selectors:**

- If the property spans multiple relations, it should better be a selector.
- If the property is non-trivial & can easily cause `N + 1` queries problem, when serialized, it should better be a selector.

The general idea is to "separate concerns" so those concerns can be maintainable / testable.

## Model Validation

Validation - clean and full_clean

Lets take a look at an example model:

```python
class Course(BaseModel):
    name = models.CharField(unique=True, max_length=255)

    start_date = models.DateField()
    end_date = models.DateField()

    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("End date cannot be before start date")
```

We are defining the model's clean method, because we want to make sure we get good data in our database.

Now, in order for the clean method to be called, someone must call full_clean on an instance of our model, before saving.

Our recommendation is to do that in the service, right before calling save:

```python
def course_create(*, name: str, start_date: date, end_date: date) -> Course:
    obj = Course(name=name, start_date=start_date, end_date=end_date)

    obj.full_clean()
    obj.save()

    return obj

```

This also plays well with Django admin, because the forms used there will trigger full_clean on the instance.

We have few general rules of thumb for when to add validation in the model's clean method:

If we are validating based on multiple, non-relational fields, of the model.
If the validation itself is simple enough.
Validation should be moved to the service layer if:

The validation logic is more complex.
Spanning relations & fetching additional data is required.
It's OK to have validation both in clean and in the service, but we tend to move things in the service, if that's the case.
Validation - constraints

As proposed in this issue, if you can do validation using Django's constraints, then you should aim for that.

Less code to write, less code to maintain, the database will take care of the data even if it's being inserted from a different place.

Lets look at an example!

```python
class Course(BaseModel):
    name = models.CharField(unique=True, max_length=255)

    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="start_date_before_end_date",
                check=Q(start_date__lt=F("end_date"))
            )
        ]

```

Now, if we try to create new object via course.save() or via Course.objects.create(...), we are going to get an IntegrityError, rather than a ValidationError.

This can actually be a downside (this is not the case, starting from Django 4.1. Check the extra section below.) to the approach, because now, we have to deal with the IntegrityError, which does not always have the best error message.

👀 ⚠️ 👀 Since Django 4.1, calling .full_clean will also check model constraints!

This actually removes the downside, mentioned above, since you'll get a nice ValidationError, if your model constraints fail the check (if you go thru Model.objects.create(...) the downside still holds)

More on this, here - <https://docs.djangoproject.com/en/4.1/ref/models/instances/#validating-objects>

For an example test case, check the Styleguide-Example repo - <https://github.com/HackSoftware/Django-Styleguide-Example/blob/master/styleguide_example/common/tests/models/test_random_model.py#L12>
The Django's documentation on constraints is quite lean, so you can check the following articles by Adam Johnson, for examples of how to use them:

Using Django Check Constraints to Ensure Only One Field Is Set
Django’s Field Choices Don’t Constrain Your Data
Using Django Check Constraints to Prevent Self-Following

## Logging Errors

```python
logger.error(
    "[%(app)s:%(view)s] %(message)s",
    extra={
        "app": "ShopApp",
        "view": "OrderTemplateView",
        "message": f"Template ID {template_id} not found for series {slug}"
    }
)
```

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

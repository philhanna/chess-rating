The best way to handle this in `pytest` is to use **custom markers** to distinguish between unit tests and system tests. Here’s how you can do it:

### 1. **Mark the System Test with a Custom Marker**
Modify your system test file and add a custom marker, e.g., `system_test`:

```python
import pytest

@pytest.mark.system_test
def test_high_level_system():
    # This test makes network calls
    assert some_network_function() == "expected_result"
```

### 2. **Configure `pytest` to Skip System Tests by Default**
In your `pytest.ini` (or create one in the project root if you don’t have it), add the following:

```ini
[pytest]
markers =
    system_test: marks tests as system tests (deselect with '-m "not system_test"')
```

### 3. **Run Only Unit Tests (Default Behavior)**
By default, when you run:

```sh
pytest
```
`pytest` will run all tests **except** those marked with `@pytest.mark.system_test` if you apply the `-m` option.

### 4. **Explicitly Run System Tests When Needed**
If you want to run **only** the system tests:

```sh
pytest -m system_test
```

If you want to run **all** tests including system tests:

```sh
pytest -m "not system_test"
pytest -m "system_test"
```

Or just:

```sh
pytest  # Runs everything if no filtering is applied
```

### 5. **Alternative: Use `-k` to Filter Tests**
If you name your system test file with a convention like `test_system_*.py`, you can exclude it:

```sh
pytest -k "not test_system"
```

But the marker approach is more flexible since it doesn’t depend on file naming.

### Summary:
- Mark system tests with `@pytest.mark.system_test`.
- Add the marker to `pytest.ini`.
- Run unit tests by default.
- Run system tests explicitly with `pytest -m system_test`.

This keeps your test suite fast by default while allowing you to run the expensive system tests when needed. 🚀
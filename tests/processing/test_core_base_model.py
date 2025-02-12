from pydantic import Field
from typing import Optional

from somesy.core.models import SomesyBaseModel


class TestModel(SomesyBaseModel):
    """Test model with some basic fields."""

    name: str = Field(alias="full_name")
    age: int
    email: Optional[str] = None


def test_key_order():
    """Test custom key order functionality."""
    # Create a fresh model instance for each test
    model = TestModel(full_name="John Doe", age=30)

    # Test default order - should contain both keys, order doesn't matter
    default_keys = list(model.model_dump().keys())
    assert set(default_keys) == {
        "name",
        "age",
    }, f"Expected keys {{'name', 'age'}}, got {set(default_keys)}"

    # Test custom order
    model.set_key_order(["age", "name", "email"])
    custom_keys = list(model.model_dump().keys())
    assert custom_keys == [
        "age",
        "name",
    ], f"Expected ['age', 'name'], got {custom_keys}"

    # Test with aliases
    alias_keys = list(model.model_dump(by_alias=True).keys())
    assert alias_keys == [
        "age",
        "full_name",
    ], f"Expected ['age', 'full_name'], got {alias_keys}"


def test_model_copy_preserves_order():
    """Test that model_copy preserves custom key order."""
    model = TestModel(full_name="John Doe", age=30, email="j.doe@example.com")
    model.set_key_order(["age", "name", "email"])  # Use field names, not aliases

    copied = model.model_copy()
    assert copied._key_order == model._key_order
    assert list(copied.model_dump().keys()) == ["age", "name", "email"]


def test_make_partial():
    """Test make_partial class method with aliases."""
    data = {"full_name": "John Doe", "age": 30}
    model = TestModel.make_partial(data)
    assert model.name == "John Doe"
    assert model.age == 30


def test_model_dump_json():
    """Test JSON serialization with custom order."""
    model = TestModel(full_name="John Doe", age=30)
    model.set_key_order(["age", "name"])  # Use field names, not aliases

    # Test without aliases
    json_str = model.model_dump_json()
    assert '"age":30' in json_str or '"age": 30' in json_str
    assert '"name":"John Doe"' in json_str or '"name": "John Doe"' in json_str

    # Test with aliases
    json_str = model.model_dump_json(by_alias=True)
    assert '"age":30' in json_str or '"age": 30' in json_str
    assert '"full_name":"John Doe"' in json_str or '"full_name": "John Doe"' in json_str


def test_patch_kwargs_defaults():
    """Test default kwargs patching."""
    model = TestModel(full_name="John Doe", age=30)

    # Test that defaults are set
    kwargs = {}
    model._patch_kwargs_defaults(kwargs)
    assert kwargs == {"exclude_defaults": True, "exclude_none": True}

    # Test that existing values are not overwritten
    kwargs = {"exclude_defaults": False}
    model._patch_kwargs_defaults(kwargs)
    assert kwargs == {"exclude_defaults": False, "exclude_none": True}


def test_reorder_dict():
    """Test dictionary reordering."""
    model = TestModel(full_name="John Doe", age=30)

    # Test with partial key order using field names
    model.set_key_order(["age", "name"])
    dct = {"name": "John Doe", "age": 30, "email": None}
    reordered = model._reorder_dict(dct)
    assert list(reordered.keys()) == ["age", "name", "email"]


def test_aliases():
    """Test alias mapping functionality."""
    aliases = TestModel._aliases()
    assert aliases == {"full_name": "name", "age": "age", "email": "email"}


def test_model_config():
    """Test model configuration."""
    assert TestModel.model_config["extra"] == "forbid"
    assert TestModel.model_config["validate_assignment"] is True
    assert TestModel.model_config["populate_by_name"] is True
    assert TestModel.model_config["str_strip_whitespace"] is True
    assert TestModel.model_config["str_min_length"] == 1


def test_key_order_empty():
    """Test behavior when key_order is empty."""
    # Create a fresh model instance
    model = TestModel(full_name="John Doe", age=30)

    # Explicitly ensure no key order is set
    model._key_order = None

    dct = {"name": "John Doe", "age": 30}
    reordered = model._reorder_dict(dct)
    # When no order is set, we only care that both keys are present
    assert set(reordered.keys()) == {
        "name",
        "age",
    }, f"Expected keys {{'name', 'age'}}, got {set(reordered.keys())}"


def test_model_dump_with_none():
    """Test model dump with None values and exclude_none=False."""
    model = TestModel(full_name="John Doe", age=30, email=None)
    dumped = model.model_dump(exclude_none=False)
    # exclude default takes precedence so email should not be there
    assert not "email" in dumped


def test_model_dump_json_with_none():
    """Test model dump_json with None values and exclude_none=False."""
    model = TestModel(full_name="John Doe", age=30, email=None)
    json_str = model.model_dump_json(exclude_none=False)
    # exclude default takes precedence so email should not be there
    assert '"email"' not in json_str


def test_set_key_order_with_aliases():
    """Test setting key order with alias names."""
    model = TestModel(full_name="John Doe", age=30)
    # Set order using aliases
    model.set_key_order(["full_name", "age"])
    # Should convert aliases to field names internally
    assert model._key_order == ["name", "age"]


def test_model_dump_json_ensure_ascii():
    """Test JSON serialization with non-ASCII characters."""
    model = TestModel(full_name="José Doé", age=30)
    json_str = model.model_dump_json()
    assert "José" in json_str  # Should not be escaped because ensure_ascii=False


def test_reorder_dict_missing_keys():
    """Test reordering with keys missing from the input dict."""
    model = TestModel(full_name="John Doe", age=30)
    model.set_key_order(["missing_key", "age", "name"])
    dct = {"name": "John Doe", "age": 30}
    reordered = model._reorder_dict(dct)
    assert list(reordered.keys()) == ["age", "name"]


def test_model_dump_with_by_alias_and_exclude():
    """Test model dump with both by_alias and exclude options."""
    model = TestModel(full_name="John Doe", age=30, email=None)
    dumped = model.model_dump(by_alias=True, exclude={"email"})
    assert "full_name" in dumped
    assert "email" not in dumped


def test_model_dump_json_with_by_alias_and_exclude():
    """Test model dump_json with both by_alias and exclude options."""
    model = TestModel(full_name="John Doe", age=30, email=None)
    json_str = model.model_dump_json(by_alias=True, exclude={"email"})
    assert "full_name" in json_str
    assert "email" not in json_str


def test_patch_kwargs_defaults_no_change():
    """Test _patch_kwargs_defaults when values are already set."""
    kwargs = {
        "exclude_defaults": True,
        "exclude_none": True,
    }
    model = TestModel(full_name="John Doe", age=30)
    original_kwargs = kwargs.copy()
    model._patch_kwargs_defaults(kwargs)
    assert kwargs == original_kwargs


def test_make_partial_with_unknown_field():
    """Test make_partial with an unknown field."""
    data = {"full_name": "John Doe", "age": 30, "unknown": "value"}
    model = TestModel.make_partial(data)
    assert model.name == "John Doe"
    assert model.age == 30

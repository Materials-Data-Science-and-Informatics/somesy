from somesy.codemeta.utils import validate_codemeta


def test_validate_codemeta_valid():
    """Test validation with valid codemeta data."""
    valid_data = {
        "@context": [
            "https://doi.org/10.5063/schema/codemeta-2.0",
            "https://schema.org",
        ],
        "@type": "SoftwareSourceCode",
        "name": "original_name",
        "version": "0.0.1",
        "author": [{"@type": "Person", "name": "Original Author"}],
        "downloadUrl": "https://example.com/download",
        "funder": {"@type": "Organization", "name": "Original Funder"},
    }

    invalid_fields = validate_codemeta(valid_data)
    assert len(invalid_fields) == 0


def test_validate_codemeta_invalid():
    """Test validation with invalid codemeta data."""
    # Test missing required field
    missing_required = {
        "@context": [
            "https://doi.org/10.5063/schema/codemeta-2.0",
            "https://schema.org",
        ],
        "@type": "SoftwareSourceCode",
        # missing 'name' field
    }
    invalid_fields = validate_codemeta(missing_required)
    assert "name" in invalid_fields

    # Test invalid @context
    invalid_context = {
        "@context": ["https://schema.org"],  # missing codemeta v2 doi
        "@type": "SoftwareSourceCode",
        "name": "test_name",
    }
    invalid_fields = validate_codemeta(invalid_context)
    assert "@context" in invalid_fields

    # Test invalid field
    invalid_data = {
        "@context": [
            "https://doi.org/10.5063/schema/codemeta-2.0",
            "https://schema.org",
        ],
        "@type": "SoftwareSourceCode",
        "name": "original_name",
        "nonExistentField": "This field should not be in codemeta",
    }
    invalid_fields = validate_codemeta(invalid_data)
    assert "nonExistentField" in invalid_fields

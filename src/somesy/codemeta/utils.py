"""Utility functions for codemeta.json."""

import copy
import json
import logging
from pathlib import Path

from pyld import jsonld

logger = logging.getLogger(__name__)

V2_DOI = "https://doi.org/10.5063/schema/codemeta-2.0"


def validate_codemeta(codemeta: dict) -> list:
    """Validate the codemeta.json file against the codemeta.jsonld schema.

    Args:
        codemeta (dict): codemeta.json file as a dictionary.

    Returns:
        invalid_fields (list): List of invalid fields.

    """
    schema_path = Path(__file__).parent / "schema-2.jsonld"
    invalid_fields = []

    # Check for required fields
    required_fields = {"@context", "@type", "name"}
    missing_fields = [field for field in required_fields if field not in codemeta]
    if missing_fields:
        invalid_fields.extend(missing_fields)

    # Validate @context
    codemeta_context = codemeta.get("@context", [])
    if isinstance(codemeta_context, str):
        codemeta_context = [codemeta_context]
    if V2_DOI not in codemeta_context:
        invalid_fields.append("@context")
        logger.warning(
            "The @context field in codemeta.json does not contain the Codemeta v2 DOI."
        )

    try:
        # Load Codemeta JSON-LD Schema
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        # Use schema's context to avoid network fetch issues
        schema_context = schema["@context"]
        codemeta_copy = copy.deepcopy(codemeta)
        codemeta_copy["@context"] = schema_context

        # Expand and compact to validate terms
        expanded = jsonld.expand(codemeta_copy)
        compacted = jsonld.compact(expanded, schema_context)

        # Check for unmapped fields (fields with ':' indicating schema prefix)
        compacted_keys = compacted.keys()
        for key in compacted_keys:
            if ":" in key:
                logger.error(f"Invalid schema reference found: {key}")
                invalid_fields.append(key)

        # Check for unsupported terms by comparing original and compacted keys
        original_keys = set(codemeta.keys())
        compacted_keys = set(compacted.keys())

        # Remove @type from comparison as it might be handled differently in compaction
        if "@type" in original_keys:
            original_keys.remove("@type")
        if "@type" in compacted_keys:
            compacted_keys.remove("@type")

        unsupported_terms = original_keys - compacted_keys
        if unsupported_terms:
            logger.warning(f"Unsupported terms found: {sorted(unsupported_terms)}")
            invalid_fields.extend(unsupported_terms)

    except Exception as e:
        logger.error(f"Codemeta validation failed: {e}")
        return ["Validation error"]

    return list(set(invalid_fields))  # Remove duplicates

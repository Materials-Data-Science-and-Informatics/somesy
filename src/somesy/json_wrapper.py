"""Utility functions for somesy."""

import json

import wrapt


@wrapt.decorator
def json_dump_wrapper(wrapped, instance, args, kwargs):
    """Wrap json.dump to write non-ascii characters with default indentation."""
    # Ensure ensure_ascii is set to False
    kwargs["ensure_ascii"] = False
    # set indent to 2 if not set
    kwargs["indent"] = kwargs.get("indent", 2)
    result = wrapped(*args, **kwargs)
    (args[1] if len(args) > 1 else kwargs["fp"]).write("\n")
    return result


# Apply the wrapper
json.dump = json_dump_wrapper(json.dump)

"""Common function that might be used in different modules."""

from typing import Dict

# TODO: tests


def convert_dependencies(dependencies: Dict[str, str], runtime_platform: str) -> dict:
    """Convert package:version dependency pair to a semantic dependency.

    Args:
        dependencies (Dict[str,str]): package:version pairs
        runtime_platform (str): which language/system dependency is running

    Returns:
        dict: semantic dependency

    """
    response = []
    for key in dependencies.keys():
        dep = {
            "@type": "SoftwareApplication",
            "identifier": key,
            "name": key,
            "runtimePlatform": runtime_platform,
            "version": dependencies[key],
        }
        response.append(dep)
    return response

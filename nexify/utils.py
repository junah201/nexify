from typing import Annotated, get_origin


def is_annotated(t) -> bool:
    """Check if the type hint is annotated"""
    return get_origin(t) is Annotated

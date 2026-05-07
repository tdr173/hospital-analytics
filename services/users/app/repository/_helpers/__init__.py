from repository._helpers.names import patient_name_col, provider_name_col

__all__ = ["patient_name_col", "provider_name_col", "MAX_PAGE_SIZE", "clamp_page_size"]

MAX_PAGE_SIZE = 200


def clamp_page_size(rows: int) -> int:
    """Defence against clients requesting absurdly large pages (OOM risk)."""
    if rows is None or rows < 1:
        return 1
    return min(rows, MAX_PAGE_SIZE)

def include_object(obj, name, type_, reflected, compare_to):
    """Manage only application tables; preserve probes and unrelated tables."""
    if type_ == "table":
        if name == "stage1_probe":
            return False
        if reflected and compare_to is None:
            return False
    return True

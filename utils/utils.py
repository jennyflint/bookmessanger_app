def parse_size(size: int | str) -> int:
    if isinstance(size, int):
        return size  # already in bytes

    size = size.strip().upper()

    units = {
        "KB": 1024,
        "MB": 1024 * 1024,
        "GB": 1024 * 1024 * 1024,
    }

    for unit, multiplier in units.items():
        if size.endswith(unit):
            number = float(size.replace(unit, "").strip())
            return int(number * multiplier)

    return int(size)

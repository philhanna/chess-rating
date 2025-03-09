# Lichess

# Extract matching perfs
"""
I want to extract all direct child elements of "perfs" that have a
"games" child with a value greater than zero and a "rating" child

filtered_perfs = {
    key: value
    for key, value in data["perfs"].items()
    if isinstance(value, dict) and "games" in value and value["games"] > 0 and "rating" in value
}
"""

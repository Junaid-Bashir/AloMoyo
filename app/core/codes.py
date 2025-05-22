# File: app/core/codes.py

import string


def make_human_code(country: str, slug: str, id: int) -> str:
    """
    Generate a human-friendly numeric code with a trailing letter, e.g.: 
      001a, 002a, … 026a, 027b, … 120a, 120e, etc.
    Only the `id` determines the code; `country` and `slug` are unused but
    kept for signature compatibility.
    """
    # Zero-pad the numeric part to 3 digits
    num = f"{id:03d}"
    # Cycle letters a–z for each block of 26
    letter_index = (id - 1) // 26
    letter = string.ascii_lowercase[letter_index % 26]
    return f"{num}{letter}"

# End of file

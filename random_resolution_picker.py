import random

MAX_SEED = 2**31 - 1

DEFAULT_RESOLUTIONS = """\
# Duplicate lines are weighted — list a size twice to double its probability.
1328,1328
1664,928
928,1664
1472,1104
1104,1472
1584,1056
1056,1584"""


def _parse_resolutions(text: str) -> list[tuple[int, int]]:
    """Parse multiline 'width,height' text into (width, height) tuples.

    Rules:
    - Blank lines and lines starting with '#' are skipped.
    - Duplicate lines are kept; they act as weighted entries.
    - Raises ValueError with a line number on any malformed or invalid line.
    """
    pairs = []
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(",")
        if len(parts) != 2:
            raise ValueError(
                f"Line {line_no}: expected 'width,height' but got {raw!r}. "
                "Each non-comment line must contain exactly one comma."
            )
        try:
            w = int(parts[0].strip())
            h = int(parts[1].strip())
        except ValueError:
            raise ValueError(
                f"Line {line_no}: width and height must be integers, got {raw!r}."
            )
        if w <= 0 or h <= 0:
            raise ValueError(
                f"Line {line_no}: width and height must be positive integers, "
                f"got width={w}, height={h}."
            )
        pairs.append((w, h))
    if not pairs:
        raise ValueError(
            "Resolution list is empty — add at least one 'width,height' line."
        )
    return pairs


class RandomResolutionPicker:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "resolutions": ("STRING", {
                    "default": DEFAULT_RESOLUTIONS,
                    "multiline": True,
                }),
                "auto_randomize": ("BOOLEAN", {"default": True}),
                "seed": ("INT", {"default": 0, "min": 0, "max": MAX_SEED}),
            },
            "hidden": {
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("INT", "INT", "STRING")
    RETURN_NAMES = ("width", "height", "label")
    FUNCTION = "pick"
    CATEGORY = "image/resolution"

    @classmethod
    def IS_CHANGED(cls, resolutions, auto_randomize, seed, **kwargs):
        if auto_randomize:
            return float("nan")
        return (resolutions, seed)

    def pick(self, resolutions, auto_randomize, seed, extra_pnginfo=None):
        seed_used = seed
        if auto_randomize:
            seed_used = random.randint(0, MAX_SEED)

        pairs = _parse_resolutions(resolutions)
        w, h = random.Random(seed_used).choice(pairs)

        if isinstance(extra_pnginfo, dict):
            extra_pnginfo["RandomResolutionPicker"] = {
                "resolution": f"{w}x{h}",
                "resolution_width": w,
                "resolution_height": h,
                "resolution_seed": seed_used,
            }

        return (w, h, f"{w}x{h}")


NODE_CLASS_MAPPINGS = {
    "RandomResolutionPicker": RandomResolutionPicker,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "RandomResolutionPicker": "Random Resolution Picker",
}

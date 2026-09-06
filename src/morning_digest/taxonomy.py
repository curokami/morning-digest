from pathlib import Path

import yaml


class Taxonomy:
    def __init__(self, tags: set[str], fallback: str) -> None:
        if fallback not in tags:
            raise ValueError("Taxonomy fallback must be a controlled tag")
        self.tags = frozenset(tags)
        self.fallback = fallback

    def validate(self, tags: list[str] | tuple[str, ...]) -> tuple[str, ...]:
        if not tags:
            return (self.fallback,)
        unknown = set(tags) - self.tags
        if unknown:
            raise ValueError(f"Unknown Digest Tags: {', '.join(sorted(unknown))}")
        return tuple(dict.fromkeys(tags))

    @classmethod
    def load(cls, path: str | Path) -> "Taxonomy":
        with Path(path).open(encoding="utf-8") as stream:
            data = yaml.safe_load(stream) or {}
        tags = {tag for category in data.get("categories", {}).values()
                for tag in category.get("tags", [])}
        return cls(tags, data.get("fallback", "Uncategorized"))

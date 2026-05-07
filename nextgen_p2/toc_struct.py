from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class TocNode:
    title: str
    page: str
    # The quotes around 'TocNode' allow for recursive type hinting
    subsections: List['TocNode'] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> 'TocNode':
        """Recursively converts a dictionary into TocNode objects."""
        subsections = [cls.from_dict(sub) for sub in data.get("subsections", [])]
        return cls(
            title=data.get("title", ""),
            page=str(data.get("page", "")),
            subsections=subsections
        )

# Example of how to print the tree nicely
def print_toc_tree(nodes: List[TocNode], level: int = 0):
    indent = "    " * level
    for node in nodes:
        print(f"{indent}├── {node.title} (Page {node.page})")
        print_toc_tree(node.subsections, level + 1)
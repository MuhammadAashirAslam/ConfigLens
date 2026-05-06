"""Line-number preserving YAML loader using PyYAML."""

from typing import Any, Dict, List, Optional
import yaml
from yaml.composer import Composer
from yaml.constructor import SafeConstructor
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode
from yaml.parser import Parser
from yaml.reader import Reader
from yaml.resolver import Resolver
from yaml.scanner import Scanner


class AnnotatedDict(dict):
    """Dictionary subclass retaining source YAML line numbers and key-line mappings."""

    def __init__(
        self,
        *args: Any,
        line_number: int = 1,
        column: int = 0,
        key_lines: Optional[Dict[str, int]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.line_number = line_number
        self.column = column
        self.key_lines: Dict[str, int] = key_lines or {}

    def get_line(self, key: str, default: Optional[int] = None) -> int:
        """Get the line number where a specific key is defined."""
        if key in self.key_lines:
            return self.key_lines[key]
        return default if default is not None else self.line_number


class AnnotatedList(list):
    """List subclass retaining source YAML line numbers."""

    def __init__(
        self,
        *args: Any,
        line_number: int = 1,
        column: int = 0,
        item_lines: Optional[List[int]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.line_number = line_number
        self.column = column
        self.item_lines: List[int] = item_lines or []


class LinePreservingSafeLoader(Reader, Scanner, Parser, Composer, SafeConstructor, Resolver):
    """Custom PyYAML loader preserving line numbers on mappings and sequences."""

    def __init__(self, stream: Any) -> None:
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        SafeConstructor.__init__(self)
        Resolver.__init__(self)


def _construct_mapping(loader: Any, node: MappingNode) -> AnnotatedDict:
    loader.flatten_mapping(node)
    mapping: Dict[Any, Any] = {}
    key_lines: Dict[str, int] = {}

    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=False)
        val = loader.construct_object(value_node, deep=True)
        mapping[key] = val
        if isinstance(key, str):
            key_lines[key] = key_node.start_mark.line + 1

    return AnnotatedDict(
        mapping,
        line_number=node.start_mark.line + 1,
        column=node.start_mark.column,
        key_lines=key_lines,
    )


def _construct_sequence(loader: Any, node: SequenceNode) -> AnnotatedList:
    items = []
    item_lines = []
    for item_node in node.value:
        items.append(loader.construct_object(item_node, deep=True))
        item_lines.append(item_node.start_mark.line + 1)

    return AnnotatedList(
        items,
        line_number=node.start_mark.line + 1,
        column=node.start_mark.column,
        item_lines=item_lines,
    )


LinePreservingSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)
LinePreservingSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG,
    _construct_sequence,
)


def load_yaml_with_line_numbers(content: str) -> Any:
    """Parse YAML string preserving line numbers on dictionaries and lists.

    Returns:
        AnnotatedDict, AnnotatedList, or scalar value. Returns None for empty input.
    """
    if not content or not content.strip():
        return None
    return yaml.load(content, Loader=LinePreservingSafeLoader)

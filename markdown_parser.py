import re
from dataclasses import dataclass
from typing import Optional, List
from llama_index.core.node_parser import MarkdownNodeParser
from .token_encoder.encode import get_token_length
from llama_index.core.schema import TextNode, MetadataMode
from .text_splitter import split_text_into_sentences

from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass
class TreeElement:
    """
    Represents a node in the tree structure.

    Attributes:
        header (Optional[str]): The header text (e.g., "Introduction") or None if no header.
        content (str): All non-header text in the section.
        token_length (int): The length of the content in tokens.
        children (List["TreeElement"]): Nested subsections under this node.
    """

    header: Optional[str]
    content: str
    token_length: int
    children: List["TreeElement"]
    pages: Set[int] = field(default_factory=set)


@dataclass
class SemanticChunk:
    """
    Represents a semantically meaningful chunk of text.

    Attributes:
        content (str): The text content of the chunk.
        token_length (int): The token length of the content.
        headers (List[str]): List of headers associated with this chunk, ordered from
                             most general to most specific.
    """

    content: str
    token_length: int
    headers: List[str]
    pages: Set[int] = field(default_factory=set)


class SemanticMarkdownParser:
    """
    A parser that converts markdown text into semantic chunks based on its structure.
    """

    def parse_markdown_to_tree(
        self, markdown_text: str, page_break: str = "\n---\n"
    ) -> TreeElement:
        """
        Parses markdown text into a tree structure.

        Args:
            markdown_text (str): The markdown text to parse.

        Returns:
            TreeElement: The root of the tree structure.

        Raises:
            ValueError: If the markdown text is empty or contains no content.
        """
        if not markdown_text.strip():
            raise ValueError("Empty markdown text provided")

        parser = MarkdownNodeParser.from_defaults()
        base_node = TextNode(text=markdown_text, id_="doc1", metadata={})
        parsed_nodes = parser.get_nodes_from_node(base_node)
        pages = markdown_text.split(page_break)

        if not parsed_nodes:
            raise ValueError("No content found in markdown text")

        root = TreeElement(header=None, content="", children=[], token_length=0)

        for node in parsed_nodes:
            node_text = node.get_content(metadata_mode=MetadataMode.NONE)
            lines = node_text.split("\n")
            if "---" in lines:
                lines.remove("---")
            heading_line = lines[0].strip() if lines else ""
            header_match = re.match(r"^(#+)\s+(.*)$", heading_line)

            page_index = next(
                (
                    i
                    for i, chunk in enumerate(pages)
                    if node_text.splitlines()[0] in chunk
                ),
                -1,
            )
            page_count = set(
                range(page_index, page_index + node_text.count(page_break) + 1)
            )

            if header_match:
                header_text = header_match.group(2).strip()
                content = "\n".join(lines[1:]).strip()
            else:
                header_text = None
                content = node_text

            token_length = get_token_length(content)
            path_str = node.metadata.get("header_path", "/")
            path_parts = path_str.strip("/").split("/") if path_str.strip("/") else []

            current_element = root
            for part in path_parts:
                found_child = next(
                    (
                        child
                        for child in current_element.children
                        if child.header == part
                    ),
                    None,
                )

                if not found_child:
                    found_child = TreeElement(
                        header=part, content="", children=[], token_length=0
                    )
                    current_element.children.append(found_child)

                current_element = found_child

            new_child = TreeElement(
                header=header_text,
                content=content,
                children=[],
                token_length=token_length,
                pages=page_count,
            )
            current_element.children.append(new_child)

        return root

    def get_full_header_path(self, headers: List[str]) -> str:
        """
        Creates a formatted header path string from a list of headers.

        Args:
            headers (List[str]): The list of headers.

        Returns:
            str: The formatted header path.
        """
        return " > ".join(filter(None, headers))

    def format_chunk_with_headers(
        self, headers: List[str], content: str, include_hashes: bool = False
    ) -> str:
        """
        Formats content with its header path.

        Args:
            headers (List[str]): The list of headers associated with the content.
            content (str): The content to format.
            include_hashes (bool, optional): If True, formats individual headers with markdown heading syntax.
                                             Defaults to False.

        Returns:
            str: The formatted content.
        """
        if not headers:
            return content

        if include_hashes:
            return (
                content  # For combined chunks, content already includes hashed headers
            )

        # For the main header path at the top, use the > separator format
        header_path = self.get_full_header_path(headers)
        return f"{header_path}\n\n{content}"

    def combine_chunks(
        self, chunk1: SemanticChunk, chunk2: SemanticChunk
    ) -> SemanticChunk:
        """
        Combines two semantic chunks while properly handling headers with markdown syntax.

        Args:
            chunk1 (SemanticChunk): The first chunk.
            chunk2 (SemanticChunk): The second chunk.

        Returns:
            SemanticChunk: The combined chunk.
        """
        # Find common prefix length
        common_prefix_length = 0
        for h1, h2 in zip(chunk1.headers, chunk2.headers):
            if h1 != h2:
                break
            common_prefix_length += 1

        if chunk1.headers == chunk2.headers:
            # If headers are exactly the same, just combine content
            combined_content = f"{chunk1.content}\n\n{chunk2.content}"
        else:
            # Format unique headers for each chunk with proper markdown heading level
            content_parts = []

            # Add first chunk with its unique headers
            if len(chunk1.headers) > common_prefix_length:
                unique_headers = chunk1.headers[common_prefix_length:]
                for level, header in enumerate(
                    unique_headers, start=common_prefix_length + 1
                ):
                    content_parts.append(f"{'#' * level} {header}")
            content_parts.append(chunk1.content)

            # Add second chunk with its unique headers
            if len(chunk2.headers) > common_prefix_length:
                unique_headers = chunk2.headers[common_prefix_length:]
                for level, header in enumerate(
                    unique_headers, start=common_prefix_length + 1
                ):
                    content_parts.append(f"\n{'#' * level} {header}")
            content_parts.append(chunk2.content)

            combined_content = "\n\n".join(content_parts)

        combined_length = get_token_length(combined_content)
        return SemanticChunk(
            content=combined_content,
            token_length=combined_length,
            headers=chunk1.headers[:common_prefix_length],  # Keep only common headers
            pages=chunk1.pages.union(chunk2.pages),
        )

    def process_tree_to_chunks(
        self,
        root: TreeElement,
        max_tokens: int = 500,
        current_headers: Optional[List[str]] = None,
    ) -> List[SemanticChunk]:
        """
        Processes the tree using post-order traversal to create semantic chunks.

        Args:
            root (TreeElement): The root of the tree.
            max_tokens (int, optional): The maximum number of tokens per chunk. Defaults to 500.
            current_headers (Optional[List[str]], optional): The current list of headers. Defaults to None.

        Returns:
            List[SemanticChunk]: A list of semantic chunks.
        """
        if current_headers is None:
            current_headers = []

        chunks: List[SemanticChunk] = []

        # Process children first (post-order traversal)
        for child in root.children:
            child_headers = current_headers.copy()
            if child.header:
                child_headers.append(child.header)

            child_chunks = self.process_tree_to_chunks(child, max_tokens, child_headers)
            chunks.extend(child_chunks)

        # Process current node's content
        if root.content.strip():
            if root.token_length > max_tokens:
                content_chunks = split_text_into_sentences(root.content)
                for content in content_chunks:
                    chunks.append(
                        SemanticChunk(
                            content=content,
                            token_length=get_token_length(content),
                            headers=current_headers.copy(),
                            pages=root.pages,
                        )
                    )
            else:
                chunks.append(
                    SemanticChunk(
                        content=root.content,
                        token_length=root.token_length,
                        headers=current_headers.copy(),
                        pages=root.pages,
                    )
                )

        # Try to combine chunks while respecting token limit
        combined_chunks: List[SemanticChunk] = []
        current_chunk = None

        for chunk in chunks:
            if current_chunk is None:
                current_chunk = chunk
                continue

            # Try to combine chunks
            potential_combined = self.combine_chunks(current_chunk, chunk)

            # Check if combination is possible within token limit
            if potential_combined.token_length <= max_tokens:
                current_chunk = potential_combined
            else:
                combined_chunks.append(current_chunk)
                current_chunk = chunk

        # Add the last chunk if it exists
        if current_chunk is not None:
            combined_chunks.append(current_chunk)

        return combined_chunks

    def get_semantic_chunks(
        self, root: TreeElement, max_tokens: int = 500
    ) -> List[str]:
        """
        Processes the tree and returns formatted semantic chunks.

        Args:
            root (TreeElement): The root of the tree.
            max_tokens (int, optional): The maximum number of tokens per chunk. Defaults to 500.

        Returns:
            List[str]: A list of formatted semantic chunks with headers.
        """
        chunks = self.process_tree_to_chunks(root, max_tokens)
        return [
            self.format_chunk_with_headers(chunk.headers, chunk.content)
            for chunk in chunks
        ]

# Semantic Markdown Parser

A Python project that parses Markdown files into a tree structure, then processes them into semantically meaningful text chunks. This can be used to restructure or summarize large bodies of text while respecting a maximum token limit.

## Description

This repository provides a robust parser that:
1. Converts a Markdown file into a hierarchical tree using custom classes (`TreeElement` and `SemanticChunk`).
2. Splits oversized text sections into smaller parts based on sentence boundaries.
3. Combines smaller chunks where possible, ensuring you stay under a predefined token limit.
4. Produces a Text output (or any format you choose) showcasing these semantic chunks.

The project uses **Poetry** for dependency management and includes sample input and output files (`input.md` and `output.txt`) to demonstrate how the code works.

---

## Features

- **Markdown to Tree**: Uses `MarkdownNodeParser` from `llama_index.core.node_parser` (and custom logic) to convert Markdown into a hierarchical structure.
- **Token-Aware Splitting**: Splits or combines chunks based on token length, using a customizable token limit.
- **Post-Order Traversal**: Ensures children are processed before the parent, giving a logical structure to the output.
- **Configurable Headers**: Preserves header hierarchy in `SemanticChunk` objects.

---

## Getting Started

### Prerequisites

- **Python 3.12.6+** (Recommended)
- **Poetry** (to manage dependencies)

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/tsensei/Semantic-Markdown-Parser/
   cd Semantic-Markdown-Parser
   ```

2. **Install dependencies with Poetry:**

   ```bash
   poetry install
   ```

This will create a virtual environment (if needed) and install all the required libraries.

---

## Usage

1. **Prepare your input Markdown file** (e.g., `input.md`) with the content you want to parse.
2. **Run your parser code**. You can modify or create a script that uses `SemanticMarkdownParser` to parse `input.md` and produce an `output.txt` (or just print results).

   Example Python snippet (assuming you have a `main.py` or similar entry point):

   ```python
    from markdown_parser import SemanticMarkdownParser
    from pathlib import Path
    import json
    from token_encoder.encode import get_token_length


    if __name__ == "__main__":
        parser = SemanticMarkdownParser()
        input_text = Path("input.md").read_text(encoding="utf-8")

        # Parse to tree
        root = parser.parse_markdown_to_tree(input_text)
        
        # Process tree into chunks
        chunks = parser.get_semantic_chunks(root, max_tokens=500)
        
        # Print resulting chunks
        with open("output.txt", "w") as file:
            for i, chunk in enumerate(chunks, 1):
                file.write(f"\nChunk {i}:\n")
                file.write("-" * 80 + "\n")
                file.write(chunk + "\n")
                file.write("-" * 80 + "\n")
                file.write(f"Token length: {get_token_length(chunk)}\n")

        print("Output saved to output.txt")
   ```

3. **Run it with Poetry**:

   ```bash
   poetry run python main.py
   ```

   Your parsed output should appear in `output.txt`.

---

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests if you have suggestions or bug reports.

1. **Fork** the repo on GitHub
2. **Clone** your fork locally
3. Create a **feature branch** (`git checkout -b feature/my-new-feature`)
4. Commit and push your changes
5. Open a **Pull Request** describing your changes

---

## License

This project is open source and distributed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact

For any questions, feel free to open an issue or reach out to me directly via [GitHub Issues](../../issues).
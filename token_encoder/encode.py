import os

from tokenizers import Tokenizer

# Get the absolute path to tokenizer.json
current_dir = os.path.dirname(os.path.abspath(__file__))
tokenizer_path = os.path.join(current_dir, "tokenizer.json")

# Load the tokenizer
tokenizer = Tokenizer.from_file(tokenizer_path)


def get_token_length(content: str) -> int:
    output = tokenizer.encode(content)
    return len(output.tokens)


def get_tokens(content: str) -> list:
    output = tokenizer.encode(content)
    return output.tokens

from llama_index.core.node_parser import SentenceSplitter
from .token_encoder.encode import get_token_length, get_tokens


def split_text_into_sentences(text, parent_text="", chunk_size=500):
    token_length = get_token_length(text)

    if token_length < 10:
        return []

    splitter = SentenceSplitter(
        chunk_size=chunk_size, chunk_overlap=100, tokenizer=get_tokens
    )

    sentences = splitter.split_text(text=text)

    if parent_text:
        sentences_with_parent = [
            f"{parent_text}\n\n{sentence}" for sentence in sentences
        ]
    else:
        sentences_with_parent = sentences

    return sentences_with_parent

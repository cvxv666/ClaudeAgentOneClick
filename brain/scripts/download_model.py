#!/usr/bin/env python3
"""Pre-download the ONNX embedding model to HuggingFace cache."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from huggingface_hub import hf_hub_download
from brain.config import EMBEDDING_MODEL

if __name__ == "__main__":
    print(f"Downloading {EMBEDDING_MODEL} ONNX model...")
    model_path = hf_hub_download(EMBEDDING_MODEL, "onnx/model.onnx")
    tokenizer_path = hf_hub_download(EMBEDDING_MODEL, "tokenizer.json")
    print(f"Model: {model_path}")
    print(f"Tokenizer: {tokenizer_path}")
    print("Done.")

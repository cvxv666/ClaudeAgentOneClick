#!/usr/bin/env python3
"""Build or rebuild the semantic search index for the vault."""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from brain.vault.embeddings import build_index

if __name__ == "__main__":
    force = "--force" in sys.argv
    print("Building semantic index...")
    t0 = time.time()
    count = build_index(force=force)
    elapsed = time.time() - t0
    print(f"Indexed {count} chunks in {elapsed:.1f}s")

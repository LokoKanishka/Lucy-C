import sys
from pathlib import Path

# Add the project root to sys.path
root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

from lucy_c.prompts import get_canonical_prompt, PROMPT_VERSION

def verify_prompts():
    print(f"--- LUCY PROMPT VERIFICATION ---")
    print(f"Version: {PROMPT_VERSION}")
    print(f"--- CANONICAL PROMPT ---")
    print(get_canonical_prompt())
    print(f"--------------------------------")

if __name__ == "__main__":
    verify_prompts()

import os
from app.ai import extract_triage_info
from app.triage_rules import apply_overrides

messages = [
    "Good morning, the elevator in block B has stopped again and there is an elderly lady on the 5th floor who cannot get down. This already happened yesterday.",
    "Can someone fix the front door of the Ministry Annex on Rua da Prata? It does not close properly and anyone can enter the lobby without badging in.",
    "Hi, there is water coming through the ceiling in apartment 3C. I think it started after the upstairs neighbour used the washing machine. It's not urgent, I put a bucket under it.",
    "The light in garage level -2 has been flickering for weeks."
]

def run_tests():
    for i, msg in enumerate(messages, 1):
        print(f"\n--- Processing Message {i} ---\n{msg}")
        try:
            extracted = extract_triage_info(msg)
            print("AI Extracted:")
            print(extracted.model_dump_json(indent=2))
            
            overridden = apply_overrides(extracted, msg)
            print("\nAfter Rules Applied:")
            print(overridden.model_dump_json(indent=2))
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
        print("-" * 40)
        
if __name__ == "__main__":
    if os.environ.get("OPENAI_API_KEY", "dummy_key_to_prevent_init_crash") == "dummy_key_to_prevent_init_crash":
        print("Please export an OPENAI_API_KEY with your OpenRouter key to run these tests.")
        print("Example: export OPENAI_API_KEY='sk-or-v1-...'")
    else:
        run_tests()

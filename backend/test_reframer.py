from reframer import Reframer

def test_reframer():
    reframer = Reframer()
    
    test_cases = [
        "I always fail at everything, I'm such a loser.",
        "They probably hate me because I missed their call.",
        "I should have worked harder today, it's a disaster.",
        "I feel fine today."
    ]

    for text in test_cases:
        print(f"\n--- Testing: {text} ---")
        distortions = reframer.detect_distortions(text)
        print(f"Detected: {[d['name'] for d in distortions]}")
        instructions = reframer.get_reframing_instructions(distortions)
        print(f"Instructions:\n{instructions}")

if __name__ == "__main__":
    test_reframer()

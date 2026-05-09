def clean_sample(example):
    text = example["patient_question"]
    label = example["dominant_distortion"]

    if text is None or label is None:
        return None

    return {
        "text": text.strip(),
        "label": label.strip()
    }


def build_prompt(example):
    return {
        "prompt": f"""
Identify the cognitive distortion in the following text.

Text: {example['text']}

Answer (one label only):
"""
    }
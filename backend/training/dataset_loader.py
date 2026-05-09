from datasets import load_dataset

def load_cognitive_dataset():
    dataset = load_dataset("masked-kunsiquat/shreevastava-cognitive-distortions")

    data = dataset["train"]

    return data


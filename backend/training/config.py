LABELS = [
    "CATASTROPHIZING",
    "OVERGENERALIZATION",
    "PERSONALIZATION",
    "MIND_READING",
    "LABELING",
    "EMOTIONAL_REASONING",
    "SHOULD_STATEMENTS",
    "MENTAL_FILTER",
    "DISQUALIFYING_POSITIVE",
    "MAGNIFICATION",
    "MINIMIZATION",
    "NONE"
]

label2id = {l: i for i, l in enumerate(LABELS)}
id2label = {i: l for l, i in label2id.items()}
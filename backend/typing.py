def analyze_typing(keystrokes):
    if len(keystrokes) < 2:
        return {}

    intervals = [
        keystrokes[i] - keystrokes[i - 1]
        for i in range(1, len(keystrokes))
    ]

    avg_speed = sum(intervals) / len(intervals)

    return {
        "avg_interval": avg_speed
    }
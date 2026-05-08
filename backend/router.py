"""
Sanctuary 3.0 — Cactus Edge Router
Intelligently routes requests between lightweight local processing and
the heavy Gemma core based on multimodal stress signals.

Routing signals:
- Typing cadence (slow typing → high cognitive load → heavy core)
- Text complexity (long text → needs deeper analysis → heavy core)
- Acoustic biomarkers (high pitch variance → emotional arousal → heavy core)
"""

import logging
from config import Config

logger = logging.getLogger(__name__)


class CactusEdgeRouter:
    """
    Heuristic router that determines whether a request needs the full
    Gemma reasoning engine or can be handled with a lightweight response.
    """

    @staticmethod
    def route_task(
        text: str,
        audio_features: dict | None,
        typing_features: dict,
    ) -> str:
        """
        Determine the routing path based on multimodal heuristics.

        Args:
            text: The user's journal text.
            audio_features: Extracted acoustic biomarkers (pitch, energy, speech_rate) or None.
            typing_features: Dict with 'avg_interval' in milliseconds.

        Returns:
            'heavy_core' for full Gemma analysis, 'lightweight_local' for brief response.
        """
        reasons: list[str] = []

        # Signal 1: Text complexity
        word_count = len(text.split())
        if word_count > Config.TEXT_COMPLEXITY_WORD_COUNT:
            reasons.append(f"text_complexity ({word_count} words)")

        # Signal 2: Typing cadence (hesitation = stress)
        avg_interval = typing_features.get("avg_interval", 0)
        if avg_interval > Config.TYPING_INTERVAL_STRESS_THRESHOLD:
            reasons.append(f"typing_stress ({avg_interval:.0f}ms avg interval)")

        # Signal 3: Acoustic arousal (high pitch variance or low energy)
        if audio_features:
            pitch = audio_features.get("pitch", 0)
            energy = audio_features.get("energy", 0)
            # High pitch often correlates with anxiety/distress
            if pitch > 200:
                reasons.append(f"high_pitch ({pitch:.1f}Hz)")
            # Very low energy may indicate monotone/depressive speech
            if 0 < energy < 0.01:
                reasons.append(f"low_energy ({energy:.4f})")

        route = "heavy_core" if reasons else "lightweight_local"
        logger.info(
            "Routing decision: %s | Signals: %s",
            route,
            reasons if reasons else ["none — defaulting to lightweight"],
        )
        return route

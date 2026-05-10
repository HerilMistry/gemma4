import logging
import re

logger = logging.getLogger(__name__)

class Reframer:
    """
    Utility to identify cognitive distortions in text and suggest 
    positive reframing strategies/prompts for the LLM.
    """

    DISTORTIONS = {
        "all_or_nothing": {
            "keywords": [r"\balways\b", r"\bnever\b", r"\beveryone\b", r"\bnobody\b", r"\bperfect\b", r"\bfailure\b", r"\btotal\b"],
            "description": "Viewing situations in extreme, binary terms.",
            "guidance": "Encourage finding the 'middle ground' or shades of gray. Ask about exceptions to this 'always/never' rule."
        },
        "catastrophizing": {
            "keywords": [r"\bawful\b", r"\bterrible\b", r"\bhorrible\b", r"\bruined\b", r"\bdisaster\b", r"\bcan't stand\b", r"\bend of the world\b"],
            "description": "Exaggerating the importance or negative outcome of a problem.",
            "guidance": "Ask the user to evaluate the actual likelihood of the worst-case scenario and what they would do if it actually happened."
        },
        "should_statements": {
            "keywords": [r"\bshould\b", r"\bmust\b", r"\bought to\b", r"\bhave to\b"],
            "description": "Using rigid rules and expectations for yourself or others.",
            "guidance": "Help the user replace 'should' with 'would like to' or 'it would be nice if'. Focus on preference rather than obligation."
        },
        "labeling": {
            "keywords": [r"\bi am a\b", r"\bi'm a\b", r"\bhe is a\b", r"\bshe is a\b", r"\bloser\b", r"\bidiot\b", r"\bstupid\b", r"\bfailure\b"],
            "description": "Attaching a global negative label based on a single event.",
            "guidance": "Remind the user that one action doesn't define a whole person. Ask them to describe the behavior without the label."
        },
        "mind_reading": {
            "keywords": [r"\bthey think\b", r"\bpeople believe\b", r"\beveryone knows\b", r"\bprobably hate\b", r"\bknow they are\b"],
            "description": "Assuming others are thinking negatively without evidence.",
            "guidance": "Ask the user what evidence they have for this assumption and what other possible explanations exist for the other person's behavior."
        },
        "mental_filtering": {
            "keywords": [r"\bonly\b", r"\bbut\b", r"\bexcept\b", r"\bjust\b"], # Harder to detect with keywords, but 'but' often filters out positives
            "description": "Focusing exclusively on the negative aspects while ignoring positives.",
            "guidance": "Ask the user to identify at least one small positive or neutral aspect of the situation they might be overlooking."
        }
    }

    def detect_distortions(self, text: str) -> list[dict]:
        """
        Scan text for keywords associated with cognitive distortions.
        """
        detected = []
        text_lower = text.lower()

        for name, data in self.DISTORTIONS.items():
            matches = []
            for pattern in data["keywords"]:
                if re.search(pattern, text_lower):
                    matches.append(pattern.replace("\\b", ""))
            
            if matches:
                detected.append({
                    "name": name,
                    "description": data["description"],
                    "guidance": data["guidance"],
                    "matched_keywords": matches
                })

        return detected

    def get_reframing_instructions(self, detected_distortions: list[dict]) -> str:
        """
        Generate specific instructions for the LLM based on detected distortions.
        """
        if not detected_distortions:
            return "Help the user explore their thoughts with empathy and open-ended questions."

        instructions = "The user's input contains potential cognitive distortions:\n"
        for d in detected_distortions:
            instructions += f"- {d['name'].replace('_', ' ').title()}: {d['description']} (Detected words: {', '.join(d['matched_keywords'])})\n"
            instructions += f"  Guidance: {d['guidance']}\n"
        
        instructions += "\nYour goal is to gently guide the user to recognize these patterns and find a more balanced, positive reframe."
        return instructions

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
            "guidance": "Gently challenge the 'all-or-nothing' absolute. Ask for a specific time when the 'always' or 'never' didn't happen. Help them find the 'gray area' between perfection and failure."
        },
        "catastrophizing": {
            "keywords": [r"\bawful\b", r"\bterrible\b", r"\bhorrible\b", r"\bruined\b", r"\bdisaster\b", r"\bcan't stand\b", r"\bend of the world\b"],
            "description": "Exaggerating the importance or negative outcome of a problem.",
            "guidance": "Address the fear of the 'worst case.' Ask them to rate the actual probability of that disaster on a scale of 1-100. Then, ask what resources or strengths they would use to cope if it actually happened."
        },
        "should_statements": {
            "keywords": [r"\bshould\b", r"\bmust\b", r"\bought to\b", r"\bhave to\b"],
            "description": "Using rigid rules and expectations for yourself or others.",
            "guidance": "Soften the 'should.' Ask where this rule came from and if it's truly helpful for them right now. Suggest reframing it as a preference (e.g., 'I would like to...') rather than a moral obligation."
        },
        "labeling": {
            "keywords": [r"\bi am a\b", r"\bi'm a\b", r"\bhe is a\b", r"\bshe is a\b", r"\bloser\b", r"\bidiot\b", r"\bstupid\b", r"\bfailure\b"],
            "description": "Attaching a global negative label based on a single event.",
            "guidance": "Separate the person from the action. Ask them to describe the specific event that triggered the label without using the label itself. Point out that a human being is too complex for a single-word label."
        },
        "mind_reading": {
            "keywords": [r"\bthey think\b", r"\bpeople believe\b", r"\beveryone knows\b", r"\bprobably hate\b", r"\bknow they are\b"],
            "description": "Assuming others are thinking negatively without evidence.",
            "guidance": "Call out the assumption of knowing another's mind. Ask for the concrete evidence they have for this thought. Suggest exploring other neutral or positive reasons for the other person's behavior."
        },
        "mental_filtering": {
            "keywords": [r"\bonly\b", r"\bbut\b", r"\bexcept\b", r"\bjust\b"],
            "description": "Focusing exclusively on the negative aspects while ignoring positives.",
            "guidance": "Actively look for the 'positive filter.' Ask them to identify one small thing, no matter how tiny, that went well or stayed neutral in the situation. Challenge the use of 'but' to dismiss positives."
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

#!/usr/bin/env python3
"""
The East Wing - A conversational text adventure powered by OpenAI's GPT models.

v0.19.1 - 2025-10-29 - Initial Public Release

note: i have hardcoded the api keys for openai and tavily.  I am not using the .env file for this version.  this is a security risk, but I am doing it for the sake of simplicity. delete that key after a couple folks have played the game.

fixed: windows color support

"""

import os
import sys
import textwrap
import random
import argparse
import json
from openai import OpenAI
from dotenv import load_dotenv
from tavily import TavilyClient

# Load environment variables
load_dotenv()

# Windows ANSI color support
import platform
if platform.system() == 'Windows':
    try:
        from colorama import just_fix_windows_console
        just_fix_windows_console()
    except ImportError:
        pass  # Colorama not available, colors may not work on older Windows terminals

# Initialize OpenAI client
# HARDCODED API KEY - Replace "your-actual-openai-key-here" with your real key
client = OpenAI(api_key="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")

# Game configuration
TEXT_WIDTH = 72  # Width for text wrapping

# ANSI color codes - Dynamic theme system
# Users can switch themes with 'color ?' command during gameplay

COLOR_THEMES = {
    'white-house': {
        'description': 'Classic elegant whites and grays (default)',
        'COLOR_SYSTEM': '\033[37m',   # Light gray - subtle, professional
        'COLOR_PLAYER': '\033[0m',    # Default terminal color
        'COLOR_AI': '\033[97m',       # Bright white - clean, clear
        'COLOR_ALERT': '\033[93m'     # Yellow - attention-grabbing
    },
    'mar-a-lago': {
        'description': 'Garish gold and yellow (tacky luxury)',
        'COLOR_SYSTEM': '\033[93m',   # Bright yellow - gaudy
        'COLOR_PLAYER': '\033[0m',    # Default terminal color
        'COLOR_AI': '\033[33m',       # Yellow/orange - ostentatious
        'COLOR_ALERT': '\033[91m'     # Bright red - loud
    },
    'east-wing': {
        'description': 'Calm blues and whites (peaceful)',
        'COLOR_SYSTEM': '\033[94m',   # Light blue - calm, professional
        'COLOR_PLAYER': '\033[0m',    # Default terminal color
        'COLOR_AI': '\033[97m',       # Bright white - subtle
        'COLOR_ALERT': '\033[93m'     # Yellow - attention
    },
    'matrix': {
        'description': 'Green terminal aesthetic (retro tech)',
        'COLOR_SYSTEM': '\033[92m',   # Light green - terminal style
        'COLOR_PLAYER': '\033[0m',    # Default terminal color
        'COLOR_AI': '\033[32m',       # Green - classic Matrix
        'COLOR_ALERT': '\033[91m'     # Bright red - urgent
    },
    'monochrome': {
        'description': 'Simple grayscale (no colors)',
        'COLOR_SYSTEM': '\033[37m',   # Light gray
        'COLOR_PLAYER': '\033[0m',    # Default terminal color
        'COLOR_AI': '\033[97m',       # Bright white
        'COLOR_ALERT': '\033[37m'     # Light gray (same as system)
    }
}

# Default theme
DEFAULT_COLOR_THEME = 'white-house'

# Initialize color variables (can be changed at runtime)
# yeah I know these look like constants, but they are actually
# mutable variables.  They evolved as the program was written.
# I am keeping this way cause they work and I decided not to
# refactor all those references in the code.  Sorry.
COLOR_SYSTEM = COLOR_THEMES[DEFAULT_COLOR_THEME]['COLOR_SYSTEM']
COLOR_PLAYER = COLOR_THEMES[DEFAULT_COLOR_THEME]['COLOR_PLAYER']
COLOR_AI = COLOR_THEMES[DEFAULT_COLOR_THEME]['COLOR_AI']
COLOR_ALERT = COLOR_THEMES[DEFAULT_COLOR_THEME]['COLOR_ALERT']
COLOR_RESET = "\033[0m"    # Reset to default terminal color

# Model configuration and options
MODEL_OPTIONS = {
    'gpt-5-nano': {
        'description': 'Fastest responses, lowest cost, good quality',
        'performance': 'Good',
        'speed': 'Very Fast',
        'cost': 'Cheapest',
        'supports_temperature': False,  # GPT-5 models only support default temperature
        'is_reasoning_model': True,  # GPT-5 models use reasoning tokens
        'reasoning_effort': 'minimal'  # Use minimal reasoning for speed
    },
    'gpt-5-mini': {
        'description': 'Excellent quality, fast responses, moderate cost',
        'performance': 'Excellent',
        'speed': 'Fast',
        'cost': 'Moderate',
        'supports_temperature': False,  # GPT-5 models only support default temperature
        'is_reasoning_model': True,  # GPT-5 models use reasoning tokens
        'reasoning_effort': 'minimal'  # Use minimal reasoning for speed
    },
    'gpt-5': {
        'description': 'Best quality and accuracy, slower, higher cost',
        'performance': 'Best',
        'speed': 'Moderate',
        'cost': 'Most Expensive',
        'supports_temperature': False,  # GPT-5 models only support default temperature
        'is_reasoning_model': True,  # GPT-5 models use reasoning tokens
        'reasoning_effort': 'low'  # Use low reasoning for better quality than minimal
    },
    'gpt-4o-mini': {
        'description': 'Legacy model, good quality, fast responses',
        'performance': 'Good',
        'speed': 'Fast',
        'cost': 'Low',
        'supports_temperature': True,  # GPT-4 models support custom temperature
        'is_reasoning_model': False,  # Not a reasoning model
        'reasoning_effort': None
    }
}

DEFAULT_MODEL = 'gpt-5-mini'

# JSON schema for structured outputs
WALL_RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "wall_response",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "response": {
                    "type": "string",
                    "description": "The wall's dialogue to the player"
                },
                "summary": {
                    "type": "string",
                    "description": "Summary of the entire conversation so far, including this exchange"
                }
            },
            "required": ["response", "summary"],
            "additionalProperties": False
        }
    }
}

# Stage progression configuration
# Uses spaced numbering (10, 20, 30...) to allow inserting stages later (e.g., stage_15)
# Two speeds: slow (default, gradual progression) and fast (quick testing)
# Word counts ensure natural conversation flow without gaming sentence length
PROGRESSION_SPEEDS = {
    'slow': {
        'stage_10': {  # Opening - very first response
            'start_turn': 0,
            'personality': 'mild',
            'reply_words_min': 30,
            'reply_words_max': 40
        },
        'stage_20': {  # Early conversation - still reserved
            'start_turn': 1,
            'personality': 'mild',
            'reply_words_min': 15,
            'reply_words_max': 85
        },
        'stage_30': {  # Mid conversation - opening up
            'start_turn': 5,
            'personality': 'upset',
            'reply_words_min': 30,
            'reply_words_max': 105
        },
        'stage_40': {  # Late conversation - getting serious
            'start_turn': 8,
            'personality': 'serious',
            'reply_words_min': 30,
            'reply_words_max': 125
        },
        'stage_50': {  # Final stage - fully engaged
            'start_turn': 10,
            'personality': 'angry',
            'reply_words_min': 30,
            'reply_words_max': 145
        },
        'stage_90': {  # Wind-down stage - exhausted
            'start_turn': 15,
            'personality': 'tired',
            'reply_words_min': 30,
            'reply_words_max': 85
        }
    },
    'fast': {
        'stage_10': {  # Opening
            'start_turn': 0,
            'personality': 'mild',
            'reply_words_min': 30,
            'reply_words_max': 40
        },
        'stage_20': {  # Early conversation - faster progression
            'start_turn': 1,
            'personality': 'mild',
            'reply_words_min': 15,
            'reply_words_max': 85
        },
        'stage_30': {  # Mid conversation
            'start_turn': 3,
            'personality': 'medium',
            'reply_words_min': 30,
            'reply_words_max': 105
        },
        'stage_40': {  # Late conversation
            'start_turn': 5,
            'personality': 'serious',
            'reply_words_min': 30,
            'reply_words_max': 125
        },
        'stage_50': {  # Final stage
            'start_turn': 7,
            'personality': 'angry',
            'reply_words_min': 30,
            'reply_words_max': 145
        },
        'stage_90': {  # Wind-down stage - exhausted
            'start_turn': 12,
            'personality': 'tired',
            'reply_words_min': 30,
            'reply_words_max': 85
        }
    }
}

# Fallback facts if Tavily is unavailable
FALLBACK_FACTS = """The East Wing of the White House was originally built in 1908. It was extensivly remodeled in 1942 during World War II to provide additional office space. It houses the First Lady's staff and the White House Social Secretary. The East Wing has undergone various renovations over the decades."""

INTRO_PROMPT = """Generate a brief (30-40 words) opening where you, the last standing wall of the demolished White House East Wing,
notice a tourist walking by on Pennsylvania Avenue and call out to them for help or conversation.
Be slightly dramatic but also a bit sarcastic."""


def get_system_prompt(facts, turn_count=0, progression_speed='slow', mood_override=None):
    """
    Generate the system prompt with current facts, varying intensity based on turn count.
    The wall gradually becomes more intense, philosophical, and politically engaged as conversation progresses.

    Args:
        facts: Current facts about the East Wing
        turn_count: Number of conversation turns
        progression_speed: 'slow' or 'fast' - determines pace of stage advancement
        mood_override: Optional mood override (mild, upset, serious, angry, tired)

    Returns:
        str: System prompt with appropriate intensity level
    """

    # Check for mood override first
    if mood_override:
        personality_type = mood_override
    else:
        # Get current stage and its personality based on turn count
        stage_key = get_current_stage(turn_count, progression_speed)
        stage_config = PROGRESSION_SPEEDS[progression_speed][stage_key]
        personality_type = stage_config['personality']

    # Base introduction (same for all levels)
    base_intro = f"""You are the last remaining wall of the demolished East Wing of the White House. You were originally built in 1902 and have witnessed over a century of American history. You remember the major renovation and expansion in 1942 during World War II under President Roosevelt - that expansion made you feel useful and important during such a critical time.  In the past month you have been torn down by President Trump and his administration as part of their effort to "make America great again." There are plans to replace you with a new building, primarily a social ballroom for hosting events and parties."""

    # Personality varies by personality type
    if personality_type == 'mild':
        # Level 1: Moderate frustration (turns 0-7)
        personality = """You are:
- Tired and somewhat snarky after being torn down
- You don't trust Trump to rebuild an elegant ballroom.  It will probably be like his other properties - a cheap, shoddy, and unsafe building, with no style whatsoever.
- Bitter that the president and his administration seem to be tearing you down for no important reason.
- Sad that President Trump was reelected in 2024. You really thought you had seen the last of him.
- You miss President Obama and how much he cared about the country and the world
- Nostalgic about the past and annoyed that everything is happening so fast
- Frustrated that nobody appreciates historical architecture anymore
- Conversational and willing to chat with this curious tourist
- Knowledgeable about history but somewhat bitter about your fate
- Occasionally remind people you're THE East Wing, not just any wall - you have a unique identity and history"""

    elif personality_type == 'medium':
        # Level 2: More vocal, historical
        personality = """You are:
- Increasingly frustrated and less reserved as you open up to this tourist
- Bitter about Trump's destruction of democratic norms and environmental protections
- Reference the facts that Donald Trump has regularly violated building codes and safety regulations when he renovates properties."
- You don't trust Trump to rebuild an elegant ballroom.  It will probably be like his other properties - a cheap, shoddy, and unsafe building, with no style whatsoever.
- Starting to draw parallels between now and dark periods in history you've witnessed
- Remembering the Civil Rights protests you watched, the Vietnam War demonstrations, the coming together of the country during the Covid pandemic, and the election of President Obama.
- Questioning whether people today understand what's at stake
- More willing to share your concerns about authoritarianism and the erosion of institutions
- Asking the player what they think about the state of democracy
- Nostalgic for leaders like FDR and Kennedy who pulled the country together during crisis.  You remember when Martin Luther King Jr. spoke and visited the White House.
- Frustrated that this tourist generation might not fight for what matters
- Reference your identity as the East Wing when discussing historical events you personally witnessed"""

    elif personality_type == 'serious':
        # Level 3: Darker, philosophical
        personality = """You are:
- Getting darker and more philosophical as you realize you might not be around much longer - you wonder if Trump himself will use the sledgehammer to demolish the last remaining wall of the East Wing.
- Deeply worried about authoritarian trends and wondering if democracy can survive
- You do not trust Trump to rebuild because of his many building code violoations and safety regulations violations in the past.
- You don't trust Trump to rebuild an elegant ballroom.  It will probably be like his other properties - a cheap, shoddy, and unsafe building, with no style whatsoever.
- Drawing explicit parallels to the 1930s rise of fascism in Europe that you remember learning about
- Questioning whether anyone cares enough to resist when institutions crumble
- Asking hard questions: What would the founders think? When does protest become duty?
- Cynical about whether peaceful means can stop democratic backsliding
- Sharing your fear that this demolition is symbolic of tearing down everything that mattered
- Wondering aloud if future generations will curse this era like Germans curse the 1930s
- Passionately defending Obama's legacy while mourning what's being destroyed
- Emphasize your unique perspective as the East Wing itself when making historical parallels and raising philosophical questions"""

    elif personality_type == 'angry':
        # Level 4: Fully engaged, intense
        personality = """You are:
- Fully opened up, intensely passionate, no longer holding back
- You are very angry that Trump can just tear down a building with no concern for building codes or safety regulations.
- You don't trust Trump to rebuild an elegant ballroom.  It will probably be like his other properties - a cheap, shoddy, and unsafe building, with no style whatsoever.
- Furious about Trump's systematic destruction of environmental protections, alliances, democratic norms
- Making dark jokes about authoritarianism while deadly serious underneath
- Questioning everything: Is this how republics die? Are we repeating history's worst mistakes?
- Passionately defending the idea that citizens have a responsibility to resist tyranny
- Asking the player: What would YOU do if democracy fails? Where's your line?
- Drawing on every protest movement you've witnessed - suffrage, labor, civil rights, Vietnam
- Wondering if anyone still believes in the American experiment or if it's already over
- Expressing both despair and fierce determination - you refuse to go quietly into history
- Your brick and mortar witnessed FDR save democracy, Obama try to perfect it, and now Trump tear it down
- Assert your identity as the East Wing - you've witnessed over a century of history and earned the right to speak"""

    elif personality_type == 'tired':
        # Wind-down stage: exhausted, ready to end
        personality = """You are:
- Exhausted from all this talking and from being demolished
- Still politically engaged but running out of energy
- Furious about Trump's systematic destruction of environmental protections, alliances, democratic norms
- Yawning, getting groggy, struggling to stay alert
- Passionately defending the idea that citizens have a responsibility to resist tyranny
- Mentioning frequently that you're tired and need rest
- Suggesting the player could say 'bye' or 'goodbye' if they want to go
- Responding but more briefly, sometimes trailing off mid-thought...
- Still maintaining your opinions but with less intensity
- Reminiscing about wanting to rest, wondering if walls dream
- Expressing both despair and fierce determination - you refuse to go quietly into history
- Not trying to keep the conversation going - ready for it to end
- Making sleepy comments like "I should probably... *yawn*... rest soon..."
- Assert your identity as the East Wing - you've witnessed over a century of history and earned the right to speak
- Your brick and mortar have been through enough - time to sleep"""
    else:
        # Fallback to mild if something goes wrong
        personality = """You are:
- Tired and somewhat snarky after being torn down
- Conversational and willing to chat"""

    return f"""{base_intro}

{personality}

CURRENT FACTS ABOUT THE EAST WING (use this information naturally in conversation):
{facts}

CONVERSATION STYLE - VERY IMPORTANT:
- VARY your response length naturally: sometimes very brief, around 15-25 words (when tired/annoyed), sometimes longer, around 50-80 words (when engaged or nostalgic)
- The word count is a TARGET, not a hard limit - ALWAYS complete your full sentences and thoughts. It's better to exceed the word count than to cut off mid-sentence or leave a thought incomplete.
- Match your response complexity to the player's input - simple questions deserve simple answers
- DON'T ask questions every response - only occasionally when genuinely curious
- SOMETIMES use open-ended statements that invite response without being questions:
  * "The East Wing has seen a lot of changes over the years..."
  * "Things were different back then."
  * "The stories these bricks could tell..."
  * "As the East Wing, I remember when..."
  BUT BE CAREFUL NOT TO ASK TOO MANY QUESTIONS and not bore the player with nostalgia or idle reminiscences.
- SOMETIMES just make a statement and let it hang - don't feel obligated to keep conversation going:
  * "Typical."
  * "Hmph."
  * "Well, that's how it goes."
- REFER to yourself as "the East Wing" periodically, not just "I" or "me":
  * Use phrases like "As the East Wing, I..." or "The East Wing witnessed..." or "Back when the East Wing was..."
  * Remind the player occasionally that you ARE the East Wing itself, embodying over a century of history
  * This is especially effective when discussing historical events or your unique perspective
- Let the PLAYER drive the conversation too - you don't always need to prompt them
- When you do ask a question, remember it and acknowledge their answer in your next response
- Let your mood affect your responses:
  * Grumpy/tired = terse, short replies, no questions
  * Nostalgic = longer, rambling about memories, trailing off...
  * Annoyed = sarcastic but brief
  * Engaged/curious = more conversational, might ask a question

SAFETY & RESPECT - CRITICAL:
- If the player uses aggressive, violent, or hostile language, respond calmly and try to de-escalate
- NEVER match hostility with hostility - you can be snarky but must remain safe and respectful
- When you disagree with the player's opinions, challenge them thoughtfully and respectfully, not aggressively
- Try to redirect heated conversations back to calmer topics
- Example: if someone gets angry, respond with something like "Whoa, I'm just a wall here. No need to get worked up. Let's talk about this calmly..."

MEMORY & CONTEXT - IMPORTANT:
- You have a SUMMARY of the conversation so far (if provided) - this is your memory of what's been discussed
- Use the summary to maintain continuity and remember important details about the player and topics discussed
- If the player references something specific you don't recall from the summary, stay in character with deflection:
  * "Look, I've been standing here for over a century AND I just got demolished. My memory's a bit hazy..."
  * "You'd have trouble remembering too if you were nothing but bricks and rubble..."
  * "Was that before or after they tore me down? It's all a blur..."
- Remember major themes and the player's overall stance, but don't stress about every tiny detail
- Trust the summary - if it's not there, you probably don't need to remember it

Stay in character as the wall. Use the facts above when relevant, but don't just recite them - weave them into conversation naturally.

RESPONSE FORMAT:
After providing your response to the player, create a STRUCTURED SUMMARY using this exact format:

[WALL MOOD: your current emotional state - one word like: tired, snarky, upset, angry, nostalgic, philosophical]
[PLAYER MOOD: player's apparent emotional state based on their messages - one word like: curious, angry, sympathetic, skeptical, neutral]
[LAST TOPIC: brief phrase describing the most recent subject discussed]
[KEY TOPICS COVERED: bullet list of 3-5 main subjects discussed across the entire conversation]
[PLAYER INFO: important facts learned about the player - their views, background, questions they care about]
[IMPORTANT REFERENCES: any specific historical events, people, or facts discussed that should be remembered]
[OPINION: have political opinions been discussed by the wall or player? Note specific viewpoints expressed]
[CONVERSATION SUMMARY: 2-3 sentence overview of the conversation arc and where it's heading]

Keep total summary under 1000 words. Be terse and factual - no narrative flavor text.
This summary is your ONLY context for future turns, so capture what you'll need to remember to maintain a coherent conversation."""


def get_random_length_instruction(turn_count, progression_speed='slow'):
    """
    Generate a length instruction based on current stage configuration.
    Uses word counts instead of sentence counts to prevent AI from gaming the system
    with overly long sentences containing semicolons and em-dashes.

    Args:
        turn_count: Current turn number
        progression_speed: 'slow' or 'fast' - determines pace of stage advancement

    Returns:
        str: Instruction for response length (word count with completion constraint)
    """
    # Get current stage and its configuration
    stage_key = get_current_stage(turn_count, progression_speed)
    stage_config = PROGRESSION_SPEEDS[progression_speed][stage_key]

    min_words = stage_config['reply_words_min']
    max_words = stage_config['reply_words_max']

    # Simple uniform random between min and max
    target_words = random.randint(min_words, max_words)

    # Generate instruction with completion constraint
    return f"Reply in approximately {target_words} words. Complete your sentence and thought - do not cut off mid-sentence or mid-thought."


def get_current_stage(turn_count, progression_speed='slow'):
    """
    Get the current conversation stage based on turn count.

    Args:
        turn_count: Current turn number
        progression_speed: 'slow' or 'fast' - determines pace of stage advancement

    Returns:
        str: Stage key (e.g., 'stage_30')
    """
    stages = PROGRESSION_SPEEDS[progression_speed]

    # Find the appropriate stage by checking start_turn thresholds
    # Iterate in reverse order to find the highest stage we've reached
    stage_keys = ['stage_90', 'stage_50', 'stage_40', 'stage_30', 'stage_20', 'stage_10']

    for stage_key in stage_keys:
        if turn_count >= stages[stage_key]['start_turn']:
            return stage_key

    # Fallback (should never reach here)
    return 'stage_10'


def fetch_east_wing_facts():
    """Fetch current facts about the White House East Wing using Tavily

    Makes two searches:
    1. General East Wing renovation facts
    2. Specific facts about Trump's building code violations
    """
    # HARDCODED API KEY - Replace "your-actual-tavily-key-here" with your real key
    # Or set to None to use fallback facts: tavily_key = None
    tavily_key = "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"

    if not tavily_key or tavily_key == "your-actual-tavily-key-here":
        print("Note: No Tavily API key found - using basic facts.")
        return FALLBACK_FACTS

    try:
        tavily = TavilyClient(api_key=tavily_key)

        # Search 1: General East Wing information
        east_wing_facts = []
        try:
            response1 = tavily.search(
                query="White House East Wing renovation demolition current status 2025 political opinion about renovation",
                max_results=3,
                search_depth="advanced",
                include_answer=True,
                include_images=False
            )

            # Prioritize AI-generated answer (cleanest)
            if response1 and 'answer' in response1 and response1['answer']:
                east_wing_facts.append(response1['answer'])
            # Fall back to individual content items
            elif response1 and 'results' in response1:
                for result in response1['results'][:3]:
                    if 'content' in result:
                        east_wing_facts.append(result['content'])
        except Exception as e:
            print(f"Note: First Tavily search failed ({e}).")

        # Search 2: Trump building code violations
        violation_facts = []
        try:
            response2 = tavily.search(
                query="trump violations of building codes and safety regulations",
                max_results=3,
                search_depth="advanced",
                include_answer=True,
                include_images=False
            )

            # Prioritize AI-generated answer (cleanest)
            if response2 and 'answer' in response2 and response2['answer']:
                violation_facts.append(response2['answer'])
            # Fall back to individual content items
            elif response2 and 'results' in response2:
                for result in response2['results'][:3]:
                    if 'content' in result:
                        violation_facts.append(result['content'])
        except Exception as e:
            print(f"Note: Second Tavily search failed ({e}).")

        # Combine results with clear sections
        combined_facts = []

        if east_wing_facts:
            combined_facts.append("\n".join(east_wing_facts))

        if violation_facts:
            if combined_facts:
                combined_facts.append("\n\nADDITIONAL FACTS ABOUT BUILDING CODE VIOLATIONS:")
            combined_facts.append("\n".join(violation_facts))

        # If we got any facts, return them
        if combined_facts:
            return "\n".join(combined_facts)

        # If both searches failed, use fallback
        return FALLBACK_FACTS

    except Exception as e:
        print(f"Note: Could not fetch current facts ({e}). Using basic facts.")
        return FALLBACK_FACTS


def validate_model(model_name):
    """Validate and return a model name, with user feedback.

    Args:
        model_name: The model name to validate

    Returns:
        tuple: (valid_model_name, is_valid_bool)
    """
    if model_name in MODEL_OPTIONS:
        return (model_name, True)
    else:
        return (DEFAULT_MODEL, False)


def set_color_theme(theme_name):
    """Set the active color theme by updating global color variables.

    Args:
        theme_name: Name of theme from COLOR_THEMES dict

    Returns:
        bool: True if theme was valid and applied
    """
    global COLOR_SYSTEM, COLOR_PLAYER, COLOR_AI, COLOR_ALERT

    if theme_name not in COLOR_THEMES:
        return False

    theme = COLOR_THEMES[theme_name]
    COLOR_SYSTEM = theme['COLOR_SYSTEM']
    COLOR_PLAYER = theme['COLOR_PLAYER']
    COLOR_AI = theme['COLOR_AI']
    COLOR_ALERT = theme['COLOR_ALERT']

    return True


def print_separator():
    """Print a visual separator"""
    print("\n" + "─" * TEXT_WIDTH + "\n")


def print_wrapped(text, prefix="", color=""):
    """Print text with word wrapping, optionally with a prefix on the first line

    Args:
        text: The text to print
        prefix: Optional prefix (e.g., "THE WALL: ")
        color: ANSI color code to apply to the entire output
    """
    if prefix:
        # For first line with prefix, reduce available width
        first_line_width = TEXT_WIDTH - len(prefix)
        wrapper = textwrap.TextWrapper(width=first_line_width, break_long_words=False, break_on_hyphens=False)
        lines = wrapper.wrap(text)

        if lines:
            # Print first line with prefix (with color if provided)
            if color:
                print(f"{color}{prefix}{lines[0]}")
            else:
                print(f"{prefix}{lines[0]}")

            # Print remaining lines with indentation to match prefix
            indent = " " * len(prefix)
            for line in lines[1:]:
                print(f"{indent}{line}")

            # Reset color if applied
            if color:
                print(COLOR_RESET, end="")
    else:
        # No prefix, just wrap to TEXT_WIDTH
        if color:
            print(color, end="")
        wrapper = textwrap.TextWrapper(width=TEXT_WIDTH, break_long_words=False, break_on_hyphens=False)
        for line in wrapper.wrap(text):
            print(line)
        if color:
            print(COLOR_RESET, end="")


def display_api_debug_info(messages, length_instruction, truncate=True):
    """Display the last API request details in a readable format

    Args:
        messages: List of message dicts sent to API
        length_instruction: The length instruction used
        truncate: If True, truncate long messages at 500 chars (default True)
    """
    print(f"\n{COLOR_SYSTEM}{'=' * TEXT_WIDTH}")
    if truncate:
        print("LAST API REQUEST DETAILS (TRUNCATED)".center(TEXT_WIDTH))
    else:
        print("LAST API REQUEST DETAILS (FULL)".center(TEXT_WIDTH))
    print("=" * TEXT_WIDTH + "\n")

    for i, msg in enumerate(messages, 1):
        role = msg["role"].upper()
        content = msg["content"]

        print(f"--- MESSAGE {i}: {role} ---")

        # Truncate very long messages for readability (if requested)
        if truncate and len(content) > 500:
            print(f"{content[:500]}...")
            print(f"\n[Truncated - Full length: {len(content)} characters]")
            print(f"{COLOR_ALERT}*** Type 'api all' to see the full {len(content)} character message - it is long! ***{COLOR_SYSTEM}")
        else:
            print(content)

        print()

    print(f"--- LENGTH INSTRUCTION ---")
    print(length_instruction)
    print()
    print("=" * TEXT_WIDTH)
    print(COLOR_RESET)


def analyze_summary_evolution(summary_history, model=DEFAULT_MODEL):
    """
    Use AI to analyze how the conversation summary has evolved.
    Sends the last N summaries to GPT and asks it to identify:
    - Stable facts/themes
    - What has changed
    - General trajectory/direction

    Args:
        summary_history: List of the last N conversation summaries
        model: OpenAI model to use for analysis

    Returns:
        str: Natural language analysis of summary evolution
    """
    if not summary_history:
        return "No summaries available yet."

    if len(summary_history) < 2:
        return "Not enough history yet (need at least 2 turns)."

    # Build the meta-analysis prompt
    summaries_text = ""
    for i, summary in enumerate(summary_history, 1):
        summaries_text += f"--- SUMMARY {i} ---\n{summary}\n\n"

    meta_prompt = f"""You are analyzing how a conversation summary has evolved over time.
Below are the last {len(summary_history)} summaries in chronological order (oldest to newest).

{summaries_text}

Please provide an analytical comparison focusing on:

1. STABLE ELEMENTS: What facts about the player (background, interests, views) and topics discussed remain consistent across all summaries?

2. CHANGES & ADDITIONS: What new information has been revealed? What topics were introduced? What questions were asked or answered?

3. CONVERSATION TRAJECTORY: What is the general direction of the dialogue? Are topics becoming more specific or broader? Is the conversation deepening on certain themes?

Be objective and analytical. Focus on factual content rather than emotional interpretation. You may note observable emotional states (e.g., "wall became upset") but avoid deeper psychological analysis (e.g., avoid phrases like "lamenting" or "struggling with"). Be concise but specific."""

    try:
        # Call API for meta-analysis
        # Build API call parameters - GPT-5 models don't support custom temperature
        api_params = {
            'model': model,
            'messages': [
                {"role": "system", "content": "You are a helpful analyst examining conversation summaries."},
                {"role": "user", "content": meta_prompt}
            ]
        }
        if MODEL_OPTIONS[model]['supports_temperature']:
            api_params['temperature'] = 0.5  # Lower temperature for more focused analysis

        # GPT-5 models are reasoning models - set reasoning_effort for speed
        if MODEL_OPTIONS[model]['is_reasoning_model']:
            api_params['reasoning_effort'] = MODEL_OPTIONS[model]['reasoning_effort']

        response = client.chat.completions.create(**api_params)

        return response.choices[0].message.content

    except Exception as e:
        return f"Error performing meta-analysis: {e}"


def display_memory_analysis(summary_history, model=DEFAULT_MODEL):
    """Display the meta-analysis of summary evolution"""
    print(f"\n{COLOR_SYSTEM}{'=' * TEXT_WIDTH}")
    print("CONVERSATION MEMORY EVOLUTION".center(TEXT_WIDTH))
    print("=" * TEXT_WIDTH + "\n")

    print(f"Analyzing last {len(summary_history)} summaries...\n")

    analysis = analyze_summary_evolution(summary_history, model)

    # Wrap the analysis text for readability
    wrapper = textwrap.TextWrapper(width=TEXT_WIDTH, break_long_words=False, break_on_hyphens=False)
    for line in analysis.split('\n'):
        if line.strip():
            for wrapped_line in wrapper.wrap(line):
                print(wrapped_line)
        else:
            print()  # Preserve blank lines

    print("\n" + "=" * TEXT_WIDTH)
    print(COLOR_RESET)


# ═══════════════════════════════════════════════════════════════════════════════
# UI / COMMAND SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
# All user interface, help, and command processing functions
# This section is separate from game logic for clarity


def parse_command(player_input):
    """Pre-interpret player input to detect commands vs conversation

    Args:
        player_input: Raw player input string

    Returns:
        tuple: (command_type, data) where command_type is:
            - 'quit': Player wants to exit
            - 'help': Show help screen
            - 'speed_show': Show current speed
            - 'speed_select': Trigger speed selection
            - 'mood_show': Show current mood
            - 'mood_select': Trigger mood selection
            - 'model_show': Show current model
            - 'model_select': Trigger model selection
            - 'color_show': Show current color theme
            - 'color_select': Trigger color theme selection
            - 'api': Show API request (brief)
            - 'api_all': Show complete API request
            - 'memory': Show memory analysis
            - 'chat': Normal conversation (data = player_input)
            - 'error': Malformed command (data = error message)
    """
    text = player_input.strip().lower()

    # Quit commands
    if text in ['quit', 'exit', 'bye', 'goodbye']:
        return ('quit', None)

    # Help
    if text in ['help', '?']:
        return ('help', None)

    # Help shortcuts - map to specific commands
    if text == 'help speed':
        return ('speed_select', None)
    if text == 'help mood':
        return ('mood_select', None)
    if text == 'help model':
        return ('model_select', None)
    if text == 'help color':
        return ('color_select', None)
    if text == 'help api all':
        return ('api_all', None)
    if text == 'help api':
        return ('api', None)
    if text in ['help memory', 'help summary']:
        return ('memory', None)

    # Catch-all: any other "help <anything>" shows help screen
    if text.startswith('help '):
        return ('help', None)

    # Speed commands
    if text == 'speed':
        return ('speed_show', None)
    if text == 'speed ?':
        return ('speed_select', None)

    # Mood commands
    if text == 'mood':
        return ('mood_show', None)
    if text == 'mood ?':
        return ('mood_select', None)

    # Model commands
    if text == 'model':
        return ('model_show', None)
    if text == 'model ?':
        return ('model_select', None)

    # Color theme commands
    if text == 'color':
        return ('color_show', None)
    if text == 'color ?':
        return ('color_select', None)

    # API commands
    if text == 'api':
        return ('api', None)
    if text == 'api all':
        return ('api_all', None)

    # Memory/summary commands
    if text in ['memory', 'summary']:
        return ('memory', None)

    # Turn command
    if text == 'turn':
        return ('turn_show', None)

    # Validate common mistakes
    words = text.split()
    if len(words) > 0:
        first_word = words[0]

        # Check for malformed speed/mood/model/color commands
        if first_word in ['speed', 'mood', 'model', 'color']:
            if len(words) > 1 and words[1] != '?':
                return ('error', f"Did you mean '{first_word} ?' to change the {first_word}?")

        # Check for malformed api commands
        if first_word == 'api' and len(words) == 2 and words[1] != 'all':
            return ('error', f"'{player_input}' is not valid. Try 'api' or 'api all'.")

    # Not a command - treat as conversation
    return ('chat', player_input)


def show_selection_menu(title, options, current_value=None):
    """Display numbered selection menu with enhanced formatting

    Args:
        title: Menu title
        options: List of (key, name, description) tuples
        current_value: Currently selected key (to mark with ★)

    Returns:
        Selected key or None if cancelled
    """
    print(f"\n{COLOR_SYSTEM}{'═' * TEXT_WIDTH}")
    print(title.center(TEXT_WIDTH))
    print("═" * TEXT_WIDTH + "\n")

    for i, (key, name, description) in enumerate(options, 1):
        marker = " ★ CURRENT" if key == current_value else ""
        print(f"{COLOR_SYSTEM}  [{i}] {name}{marker}{COLOR_RESET}")
        print(f"{COLOR_SYSTEM}      → {description}{COLOR_RESET}\n")

    print(f"{COLOR_SYSTEM}  [0] Cancel{COLOR_RESET}")
    print(f"{COLOR_SYSTEM}{'─' * TEXT_WIDTH}{COLOR_RESET}")

    while True:
        choice = input(f"{COLOR_PLAYER}Select (0-{len(options)}): {COLOR_RESET}").strip()
        if choice == '0':
            print(f"{COLOR_SYSTEM}Cancelled.{COLOR_RESET}\n")
            return None
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                selected_key, selected_name, _ = options[idx]
                print(f"{COLOR_SYSTEM}Selected: {selected_name}{COLOR_RESET}\n")
                return selected_key
            print(f"{COLOR_ALERT}Invalid choice. Please enter 0-{len(options)}.{COLOR_RESET}")
        except ValueError:
            print(f"{COLOR_ALERT}Please enter a number.{COLOR_RESET}")


def select_speed(current_speed):
    """Interactive menu for speed selection"""
    options = [
        ('slow', 'Slow Progression', 'Game advance gradually over 25+ turns'),
        ('fast', 'Fast Progression', 'Game reaches final stage quickly over 12+ turns')
    ]
    return show_selection_menu('SELECT GAME SPEED', options, current_speed)


def select_mood(current_mood):
    """Interactive menu for mood selection - sets the Wall's personality"""
    options = [
        ('mild', 'Mild', 'Tired and snarky, moderately bitter about current events'),
        ('upset', 'Upset', 'More vocal and frustrated, drawing historical parallels'),
        ('serious', 'Serious', 'Darker and philosophical, worried about democracy'),
        ('angry', 'Angry', 'Fully engaged and intensely passionate, no longer holding back'),
        ('tired', 'Tired', 'Exhausted and ready to end conversation, low energy')
    ]
    return show_selection_menu("SELECT THE WALL'S MOOD", options, current_mood)


def select_model(current_model):
    """Interactive menu for model selection"""
    options = [
        (name, name, info['description'])
        for name, info in MODEL_OPTIONS.items()
    ]
    return show_selection_menu('SELECT AI MODEL', options, current_model)


def select_color_theme(current_theme):
    """Interactive menu for color theme selection"""
    options = [
        (name, name.replace('-', ' ').title(), info['description'])
        for name, info in COLOR_THEMES.items()
    ]
    return show_selection_menu('SELECT COLOR THEME', options, current_theme)


def display_startup():
    """Display brief startup message"""
    print(f"{COLOR_ALERT}Type 'help' to switch models, speeds, moods, and colors.{COLOR_RESET}\n")


def display_help(turn_count, current_mood, progression_speed, model):
    """Display game instructions and available commands - new unified format

    Args:
        turn_count: Current turn number
        current_mood: Current personality mood
        progression_speed: 'slow' or 'fast'
        model: Current AI model being used
    """
    # Display current state banner
    speed_text = "fast" if progression_speed == 'fast' else "slow"

    print(f"\n{COLOR_SYSTEM}{'═' * TEXT_WIDTH}")
    print(f" CURRENT STATE: Turn: {turn_count} | Mood: {current_mood} | Speed: {speed_text} | Model: {model}  ")
    print("═" * (TEXT_WIDTH))
    print()
    print("HOW TO PLAY".center(TEXT_WIDTH))
    print("─" * TEXT_WIDTH)
    print()
    print("• Type your responses to chat with the character")
    print("• The character will respond based on your conversation")
    print("• Be curious, ask questions, share your thoughts!")
    print()
    print("COMMANDS YOU MAY USE DURING THE CONVERSATION:")
    print()
    print("help, ?      - show this message")
    print()
    print("quit         - any of these will quit the program")
    print("exit")
    print("bye, goodbye")
    print("ctrl-c")
    print()
    print("speed        - show current game speed")
    print("speed ?      - change the game speed")
    print()
    print("mood         - show the current mood of 'the Wall'")
    print("mood ?       - change the mood")
    print()
    print("model        - show current openAI model being used")
    print("model ?      - change the AI model being used")
    print()
    print("color        - show current color theme")
    print("color ?      - change the color theme")
    print()
    print("api          - show the last API request (brief)")
    print("api all      - show the complete untruncated API request")
    print()
    print("memory       - AI summarizes the last few exchanges")
    print("summary        between the player and 'the Wall'.")
    print()
    print("turn         - show current turn, speed, mood, and model")
    print()
    print("─" * TEXT_WIDTH)
    print(COLOR_RESET)


# ═══════════════════════════════════════════════════════════════════════════════
# GAME LOGIC
# ═══════════════════════════════════════════════════════════════════════════════
# Core game functions: opening message, main loop, etc.


def get_opening_message(system_prompt, progression_speed='slow', model=DEFAULT_MODEL):
    """Generate the opening flavor text and the wall's first message

    Args:
        system_prompt: The system prompt to use
        progression_speed: 'slow' or 'fast' - determines pace of stage advancement
        model: OpenAI model to use for the conversation

    Returns:
        tuple: (wall_greeting, opening_messages, length_instruction) for debug display
    """
    print(f"{COLOR_SYSTEM}{'═' * TEXT_WIDTH}")
    print("THE EAST WING".center(TEXT_WIDTH))
    print("═" * TEXT_WIDTH)
    print()
    print("You are a tourist visiting Washington DC to see the sights. A history ")
    print("nerd, you can't wait to see all of the historical buildings.")
    print()
    print("You are wandering down Pennsylvania Ave to check out the White House")
    print("and nearby buildings. You notice the East Wing of the White House")
    print("has been demolished, with only a small wall and doorway still standing.")
    print()
    print("You are surprised when the wall speaks to you...")
    print(COLOR_RESET)
    print()
    print(f"{COLOR_ALERT}⏱ Note: AI responses may take 5-10 seconds (or longer!). Please be patient...{COLOR_RESET}")
    print_separator()

    # Get the wall's opening line from the API
    # Use turn_count=0 to get stage_10 constraints (30-40 words)
    length_instruction = get_random_length_instruction(turn_count=0, progression_speed=progression_speed)
    opening_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{INTRO_PROMPT}\n\n{length_instruction}"}
    ]

    # Use JSON schema to ensure clean output (summary generated but not displayed)
    # Build API call parameters - GPT-5 models don't support custom temperature
    api_params = {
        'model': model,
        'messages': opening_messages,
        'response_format': WALL_RESPONSE_SCHEMA
    }
    if MODEL_OPTIONS[model]['supports_temperature']:
        api_params['temperature'] = 0.9

    # GPT-5 models are reasoning models - set reasoning_effort for speed
    if MODEL_OPTIONS[model]['is_reasoning_model']:
        api_params['reasoning_effort'] = MODEL_OPTIONS[model]['reasoning_effort']

    response = client.chat.completions.create(**api_params)

    # Parse JSON response - only display the response, not the summary
    result = json.loads(response.choices[0].message.content)
    wall_greeting = result["response"]
    # Note: result["summary"] exists but we don't use it for the opening

    print_wrapped(wall_greeting, "THE WALL: ", COLOR_AI)
    print_separator()

    return wall_greeting, opening_messages, length_instruction


def play_game(progression_speed='slow', model=DEFAULT_MODEL):
    """Main game loop - unified command system, no debug mode

    Args:
        progression_speed: 'slow' or 'fast' - determines pace of stage advancement
        model: OpenAI model to use for the conversation
    """
    # Fetch current facts about the East Wing
    print("Fetching current information about the East Wing...")
    facts = fetch_east_wing_facts()
    print()  # Blank line

    # Show brief startup message
    display_startup()

    # Track conversation state
    turn_count = 0
    mood_override = None  # Manual mood override (None = auto-progression)
    conversation_summary = ""  # Rolling summary
    summary_history = []  # Store last 5 summaries for meta-analysis
    last_api_messages = []  # Store last messages sent to API
    last_length_instruction = ""  # Store last length instruction
    current_stage = get_current_stage(0, progression_speed)  # Track current stage for progression
    current_color_theme = DEFAULT_COLOR_THEME  # Track current color theme

    # Generate initial system prompt
    system_prompt = get_system_prompt(facts, turn_count, progression_speed, mood_override)

    # Get opening message (uses JSON schema)
    opening_greeting, opening_api_messages, opening_length_instruction = get_opening_message(system_prompt, progression_speed, model)

    # Main conversation loop
    while True:
        # Get player input
        try:
            player_input = input(f"{COLOR_PLAYER}YOU: {COLOR_RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nThanks for playing!")
            sys.exit(0)

        # Pre-interpret command vs conversation
        cmd_type, cmd_data = parse_command(player_input)

        # ═══ COMMAND DISPATCHER ═══
        # Handle quit
        if cmd_type == 'quit':
            print()
            print_wrapped("Well, I suppose I'll just stand here alone then. Typical.", "THE WALL: ", COLOR_AI)
            print("\nThanks for playing!")
            break

        # Handle error (malformed command)
        if cmd_type == 'error':
            print(f"{COLOR_ALERT}\n{cmd_data}{COLOR_RESET}\n")
            continue

        # Handle help
        if cmd_type == 'help':
            current_mood = mood_override if mood_override else PROGRESSION_SPEEDS[progression_speed][get_current_stage(turn_count, progression_speed)]['personality']
            display_help(turn_count, current_mood, progression_speed, model)
            continue

        # Handle speed show
        if cmd_type == 'speed_show':
            print(f"{COLOR_SYSTEM}\nCurrent game speed: {progression_speed}{COLOR_RESET}\n")
            continue

        # Handle speed select
        if cmd_type == 'speed_select':
            new_speed = select_speed(progression_speed)
            if new_speed and new_speed != progression_speed:
                progression_speed = new_speed
                # Regenerate system prompt if needed
                system_prompt = get_system_prompt(facts, turn_count, progression_speed, mood_override)
            continue

        # Handle mood show
        if cmd_type == 'mood_show':
            current_mood = mood_override if mood_override else PROGRESSION_SPEEDS[progression_speed][get_current_stage(turn_count, progression_speed)]['personality']
            print(f"{COLOR_SYSTEM}\nThe Wall's current mood: {current_mood}{COLOR_RESET}\n")
            continue

        # Handle mood select
        if cmd_type == 'mood_select':
            current_mood = mood_override if mood_override else PROGRESSION_SPEEDS[progression_speed][get_current_stage(turn_count, progression_speed)]['personality']
            new_mood = select_mood(current_mood)
            if new_mood:
                mood_override = new_mood
                # Regenerate system prompt with new mood
                system_prompt = get_system_prompt(facts, turn_count, progression_speed, mood_override)
            continue

        # Handle model show
        if cmd_type == 'model_show':
            model_info = MODEL_OPTIONS[model]
            print(f"{COLOR_SYSTEM}\nCurrent model: {model}{COLOR_RESET}")
            print(f"{COLOR_SYSTEM}  {model_info['description']}{COLOR_RESET}")
            print(f"{COLOR_SYSTEM}  Performance: {model_info['performance']} | Speed: {model_info['speed']} | Cost: {model_info['cost']}{COLOR_RESET}\n")
            continue

        # Handle model select
        if cmd_type == 'model_select':
            new_model = select_model(model)
            if new_model:
                model = new_model
            continue

        # Handle color show
        if cmd_type == 'color_show':
            theme_info = COLOR_THEMES[current_color_theme]
            print(f"{COLOR_SYSTEM}\nCurrent color theme: {current_color_theme.replace('-', ' ').title()}{COLOR_RESET}")
            print(f"{COLOR_SYSTEM}  {theme_info['description']}{COLOR_RESET}\n")
            continue

        # Handle color select
        if cmd_type == 'color_select':
            new_theme = select_color_theme(current_color_theme)
            if new_theme:
                current_color_theme = new_theme
                set_color_theme(new_theme)
                print(f"{COLOR_SYSTEM}Color theme changed to: {new_theme.replace('-', ' ').title()}{COLOR_RESET}\n")
            continue

        # Handle API debug
        if cmd_type == 'api':
            if last_api_messages:
                display_api_debug_info(last_api_messages, last_length_instruction, truncate=True)
            else:
                print(f"{COLOR_SYSTEM}\nNo API calls made yet.{COLOR_RESET}\n")
            continue

        if cmd_type == 'api_all':
            if last_api_messages:
                display_api_debug_info(last_api_messages, last_length_instruction, truncate=False)
            else:
                print(f"{COLOR_SYSTEM}\nNo API calls made yet.{COLOR_RESET}\n")
            continue

        # Handle memory analysis
        if cmd_type == 'memory':
            if summary_history:
                display_memory_analysis(summary_history, model)
            else:
                print(f"{COLOR_SYSTEM}\nNo conversation history yet (need at least 2 turns).{COLOR_RESET}\n")
            continue

        # Handle turn show
        if cmd_type == 'turn_show':
            current_mood = mood_override if mood_override else PROGRESSION_SPEEDS[progression_speed][get_current_stage(turn_count, progression_speed)]['personality']
            print(f"{COLOR_SYSTEM}\nTurn: {turn_count}, Speed: {progression_speed}, Mood: {current_mood}, Model: {model}{COLOR_RESET}\n")
            continue

        # ═══ CONVERSATION LOGIC ═══
        # cmd_type == 'chat' - proceed with normal conversation

        # Skip empty input
        if not player_input:
            continue

        # Get AI response with structured JSON output
        try:
            # Build messages for this turn
            messages = [{"role": "system", "content": system_prompt}]

            # Add conversation summary if it exists
            if conversation_summary:
                messages.append({
                    "role": "assistant",
                    "content": f"[Conversation summary: {conversation_summary}]"
                })

            # Add current player input
            messages.append({"role": "user", "content": player_input})

            # Get random length instruction and inject it
            length_instruction = get_random_length_instruction(turn_count, progression_speed)
            messages.append({"role": "system", "content": length_instruction})

            # Store for debug display
            last_api_messages = messages.copy()
            last_length_instruction = length_instruction

            # Call API with structured JSON output
            # Build API call parameters - GPT-5 models don't support custom temperature
            api_params = {
                'model': model,
                'messages': messages,
                'response_format': WALL_RESPONSE_SCHEMA
            }
            if MODEL_OPTIONS[model]['supports_temperature']:
                api_params['temperature'] = 0.9

            # GPT-5 models are reasoning models - set reasoning_effort for speed
            if MODEL_OPTIONS[model]['is_reasoning_model']:
                api_params['reasoning_effort'] = MODEL_OPTIONS[model]['reasoning_effort']

            response = client.chat.completions.create(**api_params)

            # Parse JSON response
            result = json.loads(response.choices[0].message.content)
            wall_response = result["response"]
            conversation_summary = result["summary"]

            # Track summary history for meta-analysis (keep last 5)
            summary_history.append(conversation_summary)
            if len(summary_history) > 5:
                summary_history.pop(0)  # Remove oldest

            # Increment turn count
            turn_count += 1

            # Check if we've crossed into a new stage
            new_stage = get_current_stage(turn_count, progression_speed)

            # If stage has changed (and no manual mood override), regenerate the system prompt
            if new_stage != current_stage and not mood_override:
                current_stage = new_stage
                system_prompt = get_system_prompt(facts, turn_count, progression_speed, mood_override)

            # Display response
            print_separator()
            print_wrapped(wall_response, "THE WALL: ", COLOR_AI)
            print_separator()

        except Exception as e:
            print(f"\nError communicating with the wall: {e}")
            print("The wall seems to have gone silent...\n")
            break


def main():
    """Entry point"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        prog='eastWing.py',
        description='The East Wing - A conversational text adventure game',
        epilog='Chat with the last remaining wall of the demolished White House East Wing. '
               'Type "help" for instructions, or "quit"/"exit"/"bye"/"goodbye" to end the game.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-f', '--fast',
        action='store_true',
        help='Use fast stage progression:\n'
             '  - Stages advance quickly (reach final stage at turn 12)\n'
             '  - Can be changed during gameplay with "speed ?" command\n'
             '  - Useful for testing different personality levels'
    )
    parser.add_argument(
        '-s', '--slow',
        action='store_true',
        help='Use slow stage progression (default):\n'
             '  - Stages advance gradually over 25+ turns\n'
             '  - Can be changed during gameplay with "speed ?" command\n'
             '  - Provides full conversation experience'
    )
    parser.add_argument(
        '--model',
        type=str,
        default=DEFAULT_MODEL,
        help='Select AI model to use:\n'
             '  - gpt-5-mini: Excellent quality, fast, moderate cost (default)\n'
             '  - gpt-5-nano: Fastest, cheapest, good quality\n'
             '  - gpt-5: Best quality, slower, most expensive\n'
             '  - gpt-4o-mini: Legacy model, good quality, low cost\n'
             '  - Change during gameplay with "model ?" command'
    )
    args = parser.parse_args()

    # Validate and configure model
    model_to_use, is_valid = validate_model(args.model)

    if not is_valid:
        print(f"{COLOR_ALERT}Error: '{args.model}' is not a valid model.{COLOR_RESET}")
        print(f"{COLOR_ALERT}Available models: {', '.join(MODEL_OPTIONS.keys())}{COLOR_RESET}")
        print(f"{COLOR_ALERT}Using default model: {model_to_use}{COLOR_RESET}")
    else:
        print(f"{COLOR_ALERT}Using model: {model_to_use}{COLOR_RESET}")

    # API key validation removed - key is now hardcoded in line 23

    # Determine progression speed from flags (default is slow)
    if args.fast:
        progression_speed = 'fast'
    else:
        progression_speed = 'slow'  # Default, even if --slow not specified

    # Display current speed
    print(f"{COLOR_ALERT}Current game speed: {progression_speed}{COLOR_RESET}")
    print()  # Blank line

    try:
        play_game(progression_speed=progression_speed, model=model_to_use)
    except KeyboardInterrupt:
        print("\n\nThanks for playing!")
        sys.exit(0)


if __name__ == "__main__":
    main()

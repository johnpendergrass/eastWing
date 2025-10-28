#!/usr/bin/env python3
"""
The East Wing - A conversational text adventure, with openAI's GPT-4o-mini model.
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

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Game configuration
MODEL = "gpt-4o-mini"  # Using the affordable mini model
TEXT_WIDTH = 60  # Width for text wrapping

# ANSI color codes for terminal output
# Customize these to change the visual style of the game

# System text (help, instructions, messages) - uncomment your preferred option
# COLOR_SYSTEM = "\033[96m"  # Bright cyan - clear, informational
COLOR_SYSTEM = "\033[94m"  # Light blue - calm, professional
# COLOR_SYSTEM = "\033[37m"  # Light gray - subtle, understated

# Player input prompt
COLOR_PLAYER = "\033[0m"   # Default terminal color

# AI response color - uncomment your preferred option
# COLOR_AI = "\033[92m"      # Light green - friendly, easy on eyes
# COLOR_AI = "\033[94m"    # Light blue - calm, professional
# COLOR_AI = "\033[93m"    # Light yellow - warm, inviting
# COLOR_AI = "\033[95m"    # Bright magenta - bold, distinctive
COLOR_AI = "\033[97m"      # Bright white (current) - subtle enhancement

# Debug command output (api, memory, summary)
COLOR_DEBUG = "\033[36m"   # Cyan - technical, distinct from system

# Alert/warning color - uncomment your preferred option
COLOR_ALERT = "\033[93m"   # Bright yellow - attention-grabbing
# COLOR_ALERT = "\033[91m"   # Bright red - urgent
# COLOR_ALERT = "\033[95m"   # Bright magenta - distinctive

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

DEFAULT_MODEL = 'gpt-5-nano'

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
# Separate from debug features - controlled by --faster flag
PROGRESSION_SPEEDS = {
    'normal': {
        'stage_10': {  # Opening - very first response
            'start_turn': 0,
            'personality': 'mild',
            'reply_length_min': 2,
            'reply_length_max': 2
        },
        'stage_20': {  # Early conversation - still reserved
            'start_turn': 1,
            'personality': 'mild',
            'reply_length_min': 1,
            'reply_length_max': 4
        },
        'stage_30': {  # Mid conversation - opening up
            'start_turn': 5,
            'personality': 'upset',
            'reply_length_min': 2,
            'reply_length_max': 5
        },
        'stage_40': {  # Late conversation - getting serious
            'start_turn': 8,
            'personality': 'serious',
            'reply_length_min': 2,
            'reply_length_max': 6
        },
        'stage_50': {  # Final stage - fully engaged
            'start_turn': 10,
            'personality': 'angry',
            'reply_length_min': 2,
            'reply_length_max': 7
        },
        'stage_90': {  # Wind-down stage - exhausted
            'start_turn': 15,
            'personality': 'tired',
            'reply_length_min': 2,
            'reply_length_max': 4
        }
    },
    'fast': {
        'stage_10': {  # Opening
            'start_turn': 0,
            'personality': 'mild',
            'reply_length_min': 2,
            'reply_length_max': 2
        },
        'stage_20': {  # Early conversation - faster progression
            'start_turn': 1,
            'personality': 'mild',
            'reply_length_min': 1,
            'reply_length_max': 4
        },
        'stage_30': {  # Mid conversation
            'start_turn': 3,
            'personality': 'medium',
            'reply_length_min': 2,
            'reply_length_max': 5
        },
        'stage_40': {  # Late conversation
            'start_turn': 5,
            'personality': 'serious',
            'reply_length_min': 2,
            'reply_length_max': 6
        },
        'stage_50': {  # Final stage
            'start_turn': 7,
            'personality': 'angry',
            'reply_length_min': 2,
            'reply_length_max': 7
        },
        'stage_90': {  # Wind-down stage - exhausted
            'start_turn': 12,
            'personality': 'tired',
            'reply_length_min': 2,
            'reply_length_max': 4
        }
    }
}

# Fallback facts if Tavily is unavailable
FALLBACK_FACTS = """The East Wing of the White House was originally built in 1908. It was extensivly remodeled in 1942 during World War II to provide additional office space. It houses the First Lady's staff and the White House Social Secretary. The East Wing has undergone various renovations over the decades."""

INTRO_PROMPT = """Generate a brief (2 sentences) opening where you, the last standing wall of the demolished White House East Wing,
notice a tourist walking by on Pennsylvania Avenue and call out to them for help or conversation.
Be slightly dramatic but also a bit sarcastic."""


def get_system_prompt(facts, turn_count=0, progression_speed='normal'):
    """
    Generate the system prompt with current facts, varying intensity based on turn count.
    The wall gradually becomes more intense, philosophical, and politically engaged as conversation progresses.

    Args:
        facts: Current facts about the East Wing
        turn_count: Number of conversation turns
        progression_speed: 'normal' or 'fast' - determines pace of stage advancement

    Returns:
        str: System prompt with appropriate intensity level
    """

    # Get current stage and its personality
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
- VARY your response length naturally: sometimes just one sentence (when tired/annoyed), sometimes 2-3 sentences (when engaged or nostalgic)
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


def get_random_length_instruction(turn_count, progression_speed='normal'):
    """
    Generate a length instruction based on current stage configuration.
    Uses simple uniform random selection between min and max for the stage.

    Args:
        turn_count: Current turn number
        progression_speed: 'normal' or 'fast' - determines pace of stage advancement

    Returns:
        str: Instruction for response length
    """
    # Get current stage and its configuration
    stage_key = get_current_stage(turn_count, progression_speed)
    stage_config = PROGRESSION_SPEEDS[progression_speed][stage_key]

    min_length = stage_config['reply_length_min']
    max_length = stage_config['reply_length_max']

    # Simple uniform random between min and max
    target_length = random.randint(min_length, max_length)

    # Generate instruction based on target
    if target_length == 1:
        return "Reply in exactly 1 sentence."
    elif target_length == 2:
        return "Reply in exactly 2 sentences."
    else:
        return f"Reply in {target_length} sentences."


def get_current_stage(turn_count, progression_speed='normal'):
    """
    Get the current conversation stage based on turn count.

    Args:
        turn_count: Current turn number
        progression_speed: 'normal' or 'fast' - determines pace of stage advancement

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
    tavily_key = os.getenv("TAVILY_API_KEY")

    if not tavily_key:
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
    print(f"\n{COLOR_DEBUG}{'=' * TEXT_WIDTH}")
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
            print(f"{COLOR_ALERT}*** Type 'api all' to see the full {len(content)} character message - it is long! ***{COLOR_DEBUG}")
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
    print(f"\n{COLOR_DEBUG}{'=' * TEXT_WIDTH}")
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


def select_model_interactive(current_model):
    """Interactive numbered menu for model selection

    Args:
        current_model: The currently active model

    Returns:
        str: The selected model name (or current_model if cancelled)
    """
    models = list(MODEL_OPTIONS.keys())

    print(f"\n{COLOR_SYSTEM}{'═' * TEXT_WIDTH}")
    print("SELECT AI MODEL".center(TEXT_WIDTH))
    print("═" * TEXT_WIDTH + "\n")

    for i, model_name in enumerate(models, 1):
        info = MODEL_OPTIONS[model_name]
        marker = " (current)" if model_name == current_model else ""
        print(f"{COLOR_SYSTEM}[{i}] {model_name}{marker}{COLOR_RESET}")
        print(f"{COLOR_SYSTEM}    {info['description']}{COLOR_RESET}")
        print(f"{COLOR_SYSTEM}    Performance: {info['performance']} | Speed: {info['speed']} | Cost: {info['cost']}{COLOR_RESET}\n")

    print(f"{COLOR_SYSTEM}[0] Cancel (keep current model){COLOR_RESET}\n")

    while True:
        choice = input(f"{COLOR_PLAYER}Select model (0-{len(models)}): {COLOR_RESET}").strip()
        if choice == '0':
            print(f"{COLOR_SYSTEM}Keeping current model: {current_model}{COLOR_RESET}\n")
            return current_model
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                new_model = models[idx]
                model_info = MODEL_OPTIONS[new_model]
                print(f"{COLOR_SYSTEM}Switched to: {new_model}{COLOR_RESET}")
                print(f"{COLOR_SYSTEM}  {model_info['description']}{COLOR_RESET}\n")
                return new_model
            print(f"{COLOR_ALERT}Invalid choice. Please enter 0-{len(models)}.{COLOR_RESET}")
        except ValueError:
            print(f"{COLOR_ALERT}Please enter a number.{COLOR_RESET}")


def display_startup():
    """Display brief startup message"""
    print(f"\n{COLOR_SYSTEM}A conversation with The East Wing")
    print(f"{COLOR_ALERT}Type 'help' for details.{COLOR_RESET}\n")


def display_help(debug_enabled=False, progression_speed='normal', model=DEFAULT_MODEL):
    """Display game instructions and available commands

    Args:
        debug_enabled: Whether debug mode is currently active
        progression_speed: 'normal' or 'fast'
        model: Current AI model being used
    """
    # Display current state banner
    speed_text = "Fast" if progression_speed == 'fast' else "Normal"
    debug_text = "ON" if debug_enabled else "OFF"

    print(f"\n{COLOR_SYSTEM}{'═' * TEXT_WIDTH}")
    print(f"CURRENT STATE: {speed_text} speed | Debug {debug_text} | Model: {model}".center(TEXT_WIDTH))
    print("═" * TEXT_WIDTH)
    print()
    print("HOW TO PLAY".center(TEXT_WIDTH))
    print("─" * TEXT_WIDTH)
    print()
    print("• Type your responses to chat with the character")
    print("• The character will respond based on your conversation")
    print("• Be curious, ask questions, share your thoughts!")
    print()
    print("TO EXIT:")
    print("  quit, exit, bye, goodbye, or Ctrl+C")
    print()
    print("COMMANDS:")
    print("  'help'         - Show this help message")
    print("  'speed'        - Show current progression speed")
    print("  'mood'         - Show current mood/personality")
    print("  'model'        - Show current model and available options")
    print("  'change model' - Switch AI model during gameplay")
    print()
    print("MODEL SELECTION:")
    model_info = MODEL_OPTIONS[model]
    print(f"  Current: {model}")
    print(f"    {model_info['description']}")
    print(f"    Performance: {model_info['performance']} | Speed: {model_info['speed']} | Cost: {model_info['cost']}")
    print()
    print("  Switch models anytime with 'change model' (or 'switch model'/'select model')")
    print("  Available models:")
    for model_name, info in MODEL_OPTIONS.items():
        marker = " *" if model_name == model else ""
        print(f"    {model_name}{marker} - {info['description']}")

    if debug_enabled:
        print("  'debug off' - Disable debug features")
        print()
        print("DEBUG COMMANDS (currently active):")
        print("  'api'       - Show last API request (truncated)")
        print("  'api all'   - Show complete untruncated API request")
        print("  'memory'    - Analyze conversation summary evolution")
        print("  'summary'   - (alias for memory)")
        print("  'fast'      - Switch to fast progression speed")
        print("  'normal'    - Switch to normal progression speed")
    else:
        print("  'debug on'  - Enable debug features")
        print()
        print("DEBUG FEATURES (when enabled):")
        print("  'api'       - Show last API request (truncated)")
        print("  'api all'   - Show complete untruncated API request")
        print("  'memory'    - Analyze conversation summary evolution")
        print("  'summary'   - (alias for memory)")
        print("  'fast'      - Switch to fast progression speed")
        print("  'normal'    - Switch to normal progression speed")
        print("  'debug off' - Disable debug mode")

    print()
    print("─" * TEXT_WIDTH)
    print(COLOR_RESET)


def get_opening_message(system_prompt, progression_speed='normal', model=DEFAULT_MODEL):
    """Generate the opening flavor text and the wall's first message

    Args:
        system_prompt: The system prompt to use
        progression_speed: 'normal' or 'fast' - determines pace of stage advancement
        model: OpenAI model to use for the conversation

    Returns:
        tuple: (wall_greeting, opening_messages, length_instruction) for debug display
    """
    print(f"{COLOR_SYSTEM}{'═' * TEXT_WIDTH}")
    print("THE EAST WING".center(TEXT_WIDTH))
    print("═" * TEXT_WIDTH)
    print()
    print("You are visiting Washington DC to see the sights. You're a history")
    print("buff who knows a lot about American history, presidencies, and")
    print("particularly historical architecture.")
    print()
    print("You are wandering down Pennsylvania Ave to check out the White House")
    print("and nearby buildings. You notice the East Wing of the White House")
    print("has been demolished, with only a small wall and doorway still standing.")
    print()
    print("You are surprised when the wall speaks to you...")
    print(COLOR_RESET)
    print_separator()

    # Get the wall's opening line from the API
    # Use turn_count=0 to get stage_10 constraints (2 sentences)
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


def play_game(debug_enabled=False, use_fast_progression=False, model=DEFAULT_MODEL):
    """Main game loop

    Args:
        debug_enabled: Enable debug commands and detailed prompts
        use_fast_progression: Use fast stage progression (9 turns vs 20 to reach final stage)
        model: OpenAI model to use for the conversation
    """
    # Fetch current facts about the East Wing
    print("Fetching current information about the East Wing...")
    facts = fetch_east_wing_facts()

    # Determine progression speed
    progression_speed = 'fast' if use_fast_progression else 'normal'

    # Show brief startup message
    display_startup()

    # Track conversation turns and summary
    turn_count = 0
    current_stage = 'stage_10'  # Track which stage we're at
    conversation_summary = ""  # Rolling summary replaces full conversation history
    summary_history = []  # Store last 5 summaries for meta-analysis
    last_api_messages = []  # Store last messages sent to API for debugging
    last_length_instruction = ""  # Store last length instruction
    opening_greeting = ""  # Store opening greeting for early debug display
    opening_api_messages = []  # Store opening API messages for early debug display
    opening_length_instruction = ""  # Store opening length instruction

    # Generate initial system prompt
    system_prompt = get_system_prompt(facts, turn_count, progression_speed)

    # Get opening message (uses JSON schema)
    opening_greeting, opening_api_messages, opening_length_instruction = get_opening_message(system_prompt, progression_speed, model)

    # Main conversation loop
    while True:
        # Get player input
        try:
            if debug_enabled:
                stage_key = get_current_stage(turn_count, progression_speed)
                personality = PROGRESSION_SPEEDS[progression_speed][stage_key]['personality']
                player_input = input(f"YOU (debug {COLOR_DEBUG}on{COLOR_RESET}, turn {turn_count}, {personality}): ").strip()
            else:
                player_input = input(f"{COLOR_PLAYER}YOU: {COLOR_RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nThanks for playing!")
            sys.exit(0)

        # Check for quit commands
        if player_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
            print()
            print_wrapped("Well, I suppose I'll just stand here alone then. Typical.", "THE WALL: ", COLOR_AI)
            print("\nThanks for playing!")
            break

        # Check for help command
        if player_input.lower() == 'help':
            display_help(debug_enabled, progression_speed, model)
            continue

        # Command validation: catch malformed commands before they reach the AI
        # Only check if input is 1-2 words (potential command)
        words = player_input.lower().split()
        if len(words) <= 2 and len(words) > 0:
            first_word = words[0]

            # Check for malformed 'debug' commands
            if first_word == 'debug':
                if len(words) == 1:
                    print(f"{COLOR_ALERT}\nPlease specify 'debug on' or 'debug off'.{COLOR_RESET}\n")
                    continue
                elif len(words) == 2 and words[1] not in ['on', 'off']:
                    print(f"{COLOR_ALERT}\n'debug {words[1]}' is not valid. Please use 'debug on' or 'debug off'.{COLOR_RESET}\n")
                    continue

            # Check for malformed 'api' commands
            elif first_word == 'api':
                if len(words) == 2 and words[1] != 'all':
                    print(f"{COLOR_ALERT}\n'api {words[1]}' is not a valid command. Try 'api' or 'api all'.{COLOR_RESET}\n")
                    continue

            # Check for malformed single-word commands
            elif first_word in ['fast', 'normal', 'memory', 'summary', 'speed', 'mood', 'model']:
                if len(words) > 1:
                    print(f"{COLOR_ALERT}\n'{first_word}' should be used alone. Try just '{first_word}'.{COLOR_RESET}\n")
                    continue

            # Check for malformed 'change/switch/select model' commands
            elif first_word in ['change', 'switch', 'select']:
                if len(words) == 1:
                    print(f"{COLOR_ALERT}\n'{first_word}' is incomplete. Did you mean '{first_word} model'?{COLOR_RESET}\n")
                    continue
                elif len(words) == 2 and words[1] != 'model':
                    print(f"{COLOR_ALERT}\n'{player_input}' is not a valid command. Try '{first_word} model'.{COLOR_RESET}\n")
                    continue
                elif len(words) > 2:
                    print(f"{COLOR_ALERT}\n'{first_word} model' should not have extra arguments. Try just '{first_word} model'.{COLOR_RESET}\n")
                    continue

        # Check for 'speed' command - shows current progression speed
        if player_input.lower() == 'speed':
            current_speed = "Fast" if progression_speed == 'fast' else "Normal"
            print(f"{COLOR_SYSTEM}\nThe game's current progression speed: {current_speed}{COLOR_RESET}")
            if debug_enabled:
                print(f"{COLOR_SYSTEM}[Use 'fast' or 'normal' to change speed]{COLOR_RESET}\n")
            else:
                print(f"{COLOR_SYSTEM}[Enable debug mode with 'debug on' to change speed]{COLOR_RESET}\n")
            continue

        # Check for 'mood' command - shows current mood/personality
        if player_input.lower() == 'mood':
            current_stage = get_current_stage(turn_count, progression_speed)
            current_personality = PROGRESSION_SPEEDS[progression_speed][current_stage]['personality']
            print(f"{COLOR_SYSTEM}\nThe wall's current mood is: {current_personality}{COLOR_RESET}\n")
            continue

        # Check for 'model' command - shows current model and available options
        if player_input.lower() == 'model':
            print(f"{COLOR_SYSTEM}\nCURRENT MODEL: {model}{COLOR_RESET}")
            model_info = MODEL_OPTIONS[model]
            print(f"{COLOR_SYSTEM}  {model_info['description']}{COLOR_RESET}")
            print(f"{COLOR_SYSTEM}  Performance: {model_info['performance']} | Speed: {model_info['speed']} | Cost: {model_info['cost']}{COLOR_RESET}\n")

            print(f"{COLOR_SYSTEM}AVAILABLE MODELS:{COLOR_RESET}")
            for model_name, info in MODEL_OPTIONS.items():
                marker = " (current)" if model_name == model else ""
                print(f"{COLOR_SYSTEM}  {model_name}{marker}{COLOR_RESET}")
                print(f"{COLOR_SYSTEM}    {info['description']}{COLOR_RESET}")
                print(f"{COLOR_SYSTEM}    [Performance: {info['performance']} | Speed: {info['speed']} | Cost: {info['cost']}]{COLOR_RESET}")
                print()

            print(f"{COLOR_SYSTEM}To change models during gameplay, type 'change model'{COLOR_RESET}\n")
            continue

        # Check for 'change model' / 'switch model' / 'select model' commands
        if player_input.lower() in ['change model', 'switch model', 'select model']:
            new_model = select_model_interactive(model)
            if new_model != model:
                model = new_model
            continue

        # Check for debug toggle commands
        if player_input.lower() == 'debug on':
            if not debug_enabled:
                debug_enabled = True
                print(f"{COLOR_SYSTEM}\nDebug mode enabled. Type 'help' to see debug commands.{COLOR_RESET}\n")
            else:
                print(f"{COLOR_SYSTEM}\nDebug mode is already enabled.{COLOR_RESET}\n")
            continue

        if player_input.lower() == 'debug off':
            if debug_enabled:
                debug_enabled = False
                print(f"{COLOR_SYSTEM}\nDebug mode disabled.{COLOR_RESET}\n")
            else:
                print(f"{COLOR_SYSTEM}\nDebug mode is already disabled.{COLOR_RESET}\n")
            continue

        # Check for speed switch commands (requires debug mode)
        if player_input.lower() == 'fast':
            if not debug_enabled:
                print(f"{COLOR_ALERT}\n'fast' does not work unless you are in debug mode. [hint: to switch to debug mode, type 'debug on']{COLOR_RESET}\n")
                continue
            if progression_speed == 'fast':
                print(f"{COLOR_SYSTEM}\nProgression speed is already set to 'fast'.{COLOR_RESET}\n")
            else:
                # Calculate old and new stages
                old_stage = get_current_stage(turn_count, progression_speed)
                progression_speed = 'fast'
                new_stage = get_current_stage(turn_count, progression_speed)

                # Get personality for display
                new_personality = PROGRESSION_SPEEDS[progression_speed][new_stage]['personality']

                # If stage changed, regenerate system prompt
                if new_stage != old_stage:
                    current_stage = new_stage
                    system_prompt = get_system_prompt(facts, turn_count, progression_speed)

                print(f"{COLOR_SYSTEM}\nTurn {turn_count}. Progression speed changed to 'fast'. Mood is: {new_personality}.{COLOR_RESET}\n")
            continue

        if player_input.lower() == 'normal':
            if not debug_enabled:
                print(f"{COLOR_ALERT}\n'normal' does not work unless you are in debug mode. [hint: to switch to debug mode, type 'debug on']{COLOR_RESET}\n")
                continue
            if progression_speed == 'normal':
                print(f"{COLOR_SYSTEM}\nProgression speed is already set to 'normal'.{COLOR_RESET}\n")
            else:
                # Calculate old and new stages
                old_stage = get_current_stage(turn_count, progression_speed)
                progression_speed = 'normal'
                new_stage = get_current_stage(turn_count, progression_speed)

                # Get personality for display
                new_personality = PROGRESSION_SPEEDS[progression_speed][new_stage]['personality']

                # If stage changed, regenerate system prompt
                if new_stage != old_stage:
                    current_stage = new_stage
                    system_prompt = get_system_prompt(facts, turn_count, progression_speed)

                print(f"{COLOR_SYSTEM}\nTurn {turn_count}. Progression speed changed to 'normal'. Mood is: {new_personality}.{COLOR_RESET}\n")
            continue

        # Check for debug command to show API details (full, untruncated)
        if player_input.lower() == 'api all':
            if not debug_enabled:
                print(f"{COLOR_ALERT}\n'api all' does not work unless you are in debug mode. [hint: to switch to debug mode, type 'debug on']{COLOR_RESET}\n")
                continue
            if last_api_messages:
                display_api_debug_info(last_api_messages, last_length_instruction, truncate=False)
            elif opening_api_messages:
                print(f"{COLOR_DEBUG}\n[Showing opening message API call - no conversation turns yet]\n{COLOR_RESET}")
                display_api_debug_info(opening_api_messages, opening_length_instruction, truncate=False)
            else:
                print(f"{COLOR_DEBUG}\nNo API requests have been made yet.\n{COLOR_RESET}")
            continue

        # Check for debug command to show API details (truncated)
        if player_input.lower() == 'api':
            if not debug_enabled:
                print(f"{COLOR_ALERT}\n'api' does not work unless you are in debug mode. [hint: to switch to debug mode, type 'debug on']{COLOR_RESET}\n")
                continue
            if last_api_messages:
                display_api_debug_info(last_api_messages, last_length_instruction, truncate=True)
            elif opening_api_messages:
                print(f"{COLOR_DEBUG}\n[Showing opening message API call - no conversation turns yet]\n{COLOR_RESET}")
                display_api_debug_info(opening_api_messages, opening_length_instruction, truncate=True)
            else:
                print(f"{COLOR_DEBUG}\nNo API requests have been made yet.\n{COLOR_RESET}")
            continue

        # Check for debug command to show memory evolution analysis
        if player_input.lower() in ['memory', 'summary']:
            if not debug_enabled:
                print(f"{COLOR_ALERT}\n'{player_input.lower()}' does not work unless you are in debug mode. [hint: to switch to debug mode, type 'debug on']{COLOR_RESET}\n")
                continue
            if summary_history:
                display_memory_analysis(summary_history, model)
            elif conversation_summary:
                # Show current summary if no history yet
                print(f"\n{COLOR_DEBUG}{'=' * TEXT_WIDTH}")
                print("CURRENT CONVERSATION SUMMARY".center(TEXT_WIDTH))
                print("=" * TEXT_WIDTH + "\n")
                wrapper = textwrap.TextWrapper(width=TEXT_WIDTH, break_long_words=False, break_on_hyphens=False)
                for line in wrapper.wrap(conversation_summary):
                    print(line)
                print("\n" + "=" * TEXT_WIDTH)
                print(f"[Only 1 turn - need at least 2 for evolution analysis]{COLOR_RESET}\n")
            else:
                print(f"{COLOR_DEBUG}\nNo conversation history yet. Play a few turns first! (use 'api' to see opening message)\n{COLOR_RESET}")
            continue

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

            # If stage has changed, regenerate the system prompt
            if new_stage != current_stage:
                current_stage = new_stage
                system_prompt = get_system_prompt(facts, turn_count, progression_speed)

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
        prog='game.py',
        description='The East Wing - A conversational text adventure game',
        epilog='Chat with the last remaining wall of the demolished White House East Wing. '
               'Type "help" for instructions, or "quit"/"exit"/"bye"/"goodbye" to end the game.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Enable debug features:\n'
             '  - Show turn count and personality level in prompt\n'
             '  - Access to debug commands: "api", "memory"/"summary"\n'
             '  - Can also be toggled during gameplay with "debug on/off"\n'
             '  - Type "help" during gameplay for full command list'
    )
    parser.add_argument(
        '-f', '--fast',
        action='store_true',
        help='Use fast stage progression:\n'
             '  - Stages advance quicker (stage_50 reached at turn 9 vs turn 20)\n'
             '  - Can also be toggled during gameplay with "fast"/"normal" commands\n'
             '  - Useful for testing different personality levels'
    )
    parser.add_argument(
        '--model',
        type=str,
        default=DEFAULT_MODEL,
        help='Select AI model to use:\n'
             '  - gpt-5-nano: Fastest, cheapest, good quality (default)\n'
             '  - gpt-5-mini: Excellent quality, fast, moderate cost\n'
             '  - gpt-5: Best quality, slower, most expensive\n'
             '  - gpt-4o-mini: Legacy model, good quality, low cost\n'
             '  - Type "model" during gameplay to see current model'
    )
    args = parser.parse_args()

    # Validate and configure model
    model_to_use, is_valid = validate_model(args.model)

    if not is_valid:
        print(f"{COLOR_ALERT}Error: '{args.model}' is not a valid model.{COLOR_RESET}")
        print(f"{COLOR_ALERT}Available models: {', '.join(MODEL_OPTIONS.keys())}{COLOR_RESET}")
        print(f"{COLOR_SYSTEM}Using default model: {model_to_use}{COLOR_RESET}\n")
    else:
        model_info = MODEL_OPTIONS[model_to_use]
        print(f"{COLOR_SYSTEM}Using model: {model_to_use}{COLOR_RESET}")
        print(f"{COLOR_SYSTEM}  {model_info['description']}{COLOR_RESET}\n")

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your API key.")
        print("See .env.example for the format.")
        sys.exit(1)

    try:
        play_game(debug_enabled=args.debug, use_fast_progression=args.fast, model=model_to_use)
    except KeyboardInterrupt:
        print("\n\nThanks for playing!")
        sys.exit(0)


if __name__ == "__main__":
    main()

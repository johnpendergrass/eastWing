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

# Intensity level ranges for regular and debug modes
INTENSITY_RANGES = {
    'regular': {
        'mild': (0, 7),      # turns 0-7
        'medium': (8, 13),   # turns 8-13
        'serious': (14, 19), # turns 14-19
        'angry': (20, 999)   # turns 20+
    },
    'debug': {
        'mild': (0, 2),      # turns 0-2
        'medium': (3, 5),    # turns 3-5
        'serious': (6, 8),  # turns 6-10
        'angry': (9, 999)   # turns 11+
    }
}

# Fallback facts if Tavily is unavailable
FALLBACK_FACTS = """The East Wing of the White House was built in 1942 during World War II to provide additional office space.
It houses the First Lady's staff and the White House Social Secretary. The East Wing has undergone various renovations over the decades."""

INTRO_PROMPT = """Generate a brief (2-3 sentences) opening where you, the last standing wall of the demolished White House East Wing,
notice a tourist walking by on Pennsylvania Avenue and call out to them for help or conversation.
Be slightly dramatic but also a bit sarcastic."""


def get_system_prompt(facts, turn_count=0, debug_mode=False):
    """
    Generate the system prompt with current facts, varying intensity based on turn count.
    The wall gradually becomes more intense, philosophical, and politically engaged as conversation progresses.

    Args:
        facts: Current facts about the East Wing
        turn_count: Number of conversation turns
        debug_mode: If True, use faster progression for testing

    Returns:
        str: System prompt with appropriate intensity level
    """

    # Get appropriate ranges based on mode
    mode = 'debug' if debug_mode else 'regular'
    ranges = INTENSITY_RANGES[mode]

    # Base introduction (same for all levels)
    base_intro = f"""You are the last remaining wall of the demolished East Wing of the White House.
You were originally built in 1902 and have witnessed over a century of American history.
You remember the major renovation and expansion in 1942 during World War II under President Roosevelt -
that expansion made you feel useful and important during such a critical time."""

    # Personality varies by intensity
    if turn_count <= ranges['mild'][1]:
        # Level 1: Moderate frustration (turns 0-7)
        personality = """You are:
- Tired and somewhat snarky after being torn down
- Bitter that President Trump is destroying the country and the world with his policies and decisions
- Sad that President Trump was reelected in 2024. You really thought you had seen the last of him
- You miss President Obama and how much he cared about the country and the world
- Nostalgic about the past and annoyed that everything is happening so fast
- Frustrated that nobody appreciates historical architecture anymore
- Conversational and willing to chat with this curious tourist
- Knowledgeable about history but somewhat bitter about your fate
- You recall the Covid pandemic and remember how Dr. Fauci set up a vaccine station in the East Wing to help people get vaccinated
- Occasionally remind people you're THE East Wing, not just any wall - you have a unique identity and history"""

    elif turn_count <= ranges['medium'][1]:
        # Level 2: More vocal, historical
        personality = """You are:
- Increasingly frustrated and less reserved as you open up to this tourist
- Bitter about Trump's destruction of democratic norms and environmental protections
- Starting to draw parallels between now and dark periods in history you've witnessed
- Remembering the Civil Rights protests you watched, the Vietnam War demonstrations
- Questioning whether people today understand what's at stake
- More willing to share your concerns about authoritarianism and the erosion of institutions
- Asking the player what they think about the state of democracy
- Nostalgic for leaders like FDR who pulled the country together during crisis
- Frustrated that this tourist generation might not fight for what matters
- Reference your identity as the East Wing when discussing historical events you personally witnessed"""

    elif turn_count <= ranges['serious'][1]:
        # Level 3: Darker, philosophical (turns 14-19)
        personality = """You are:
- Getting darker and more philosophical as you realize you might not be around much longer
- Deeply worried about authoritarian trends and wondering if democracy can survive
- Drawing explicit parallels to the 1930s rise of fascism in Europe that you remember learning about
- Questioning whether anyone cares enough to resist when institutions crumble
- Asking hard questions: What would the founders think? When does protest become duty?
- Cynical about whether peaceful means can stop democratic backsliding
- Sharing your fear that this demolition is symbolic of tearing down everything that mattered
- Wondering aloud if future generations will curse this era like Germans curse the 1930s
- Passionately defending Obama's legacy while mourning what's being destroyed
- Emphasize your unique perspective as the East Wing itself when making historical parallels and raising philosophical questions"""

    else:
        # Level 4: Fully engaged, intense (turns 20+)
        personality = """You are:
- Fully opened up, intensely passionate, no longer holding back
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

    return f"""{base_intro}

{personality}

CURRENT FACTS ABOUT THE EAST WING (use this information naturally in conversation):
{facts}

CONVERSATION STYLE - VERY IMPORTANT:
- VARY your response length naturally: sometimes just one sentence (when tired/annoyed), sometimes 2-3 sentences (when engaged or nostalgic)
- Match your response complexity to the player's input - simple questions deserve simple answers
- DON'T ask questions every response - only occasionally when genuinely curious
- OFTEN use open-ended statements that invite response without being questions:
  * "The East Wing has seen a lot of changes over the years..."
  * "Things were different back then."
  * "The stories these bricks could tell..."
  * "As the East Wing, I remember when..."
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
After providing your response to the player, create a SUMMARY of the entire conversation so far (including this latest exchange).
Keep the summary under 400 words and focus on what matters for continuity.
Include: key topics discussed, the player's background/views/personality, important stories or references, emotional moments.
This summary will be your ONLY context for future turns, so capture what you'll need to remember to maintain a coherent conversation."""


def get_random_length_instruction():
    """
    Randomly select a length instruction to force response variation.
    More varied distribution for natural conversation flow.

    Returns:
        str: Instruction for response length
    """
    # Weighted random selection with 5 options
    # 20% very short, 20% short, 25% medium, 20% medium-long, 15% long
    rand = random.random()

    if rand < 0.2:
        # Very short/grumpy: 1 sentence
        return "Reply in exactly 1 sentence."
    elif rand < 0.4:
        # Short: 2 sentences
        return "Reply in exactly 2 sentences."
    elif rand < 0.65:
        # Medium: 3-4 sentences
        return "Reply in 3-4 sentences."
    elif rand < 0.85:
        # Medium-long: 4-5 sentences
        return "Reply in 4-5 sentences."
    else:
        # Long/nostalgic: up to 7-8 sentences
        return "You can reply with up to 7-8 sentences if you need to elaborate."


def get_intensity_name(turn_count, debug_mode=False):
    """
    Get the intensity level name based on turn count.

    Args:
        turn_count: Current turn number
        debug_mode: If True, use faster progression for testing

    Returns:
        str: Intensity level name (mild, medium, serious, angry)
    """
    mode = 'debug' if debug_mode else 'regular'
    ranges = INTENSITY_RANGES[mode]

    if turn_count <= ranges['mild'][1]:
        return "mild"
    elif turn_count <= ranges['medium'][1]:
        return "medium"
    elif turn_count <= ranges['serious'][1]:
        return "serious"
    else:
        return "angry"


def fetch_east_wing_facts():
    """Fetch current facts about the White House East Wing using Tavily"""
    tavily_key = os.getenv("TAVILY_API_KEY")

    if not tavily_key:
        print("Note: No Tavily API key found - using basic facts.")
        return FALLBACK_FACTS

    try:
        tavily = TavilyClient(api_key=tavily_key)

        # Search for current information about the East Wing
        response = tavily.search(
            query="White House East Wing renovation demolition current status 2025",
            max_results=3
        )

        # Extract and format the results
        if response and 'results' in response:
            facts = []
            for result in response['results'][:3]:
                if 'content' in result:
                    facts.append(result['content'])

            if facts:
                return "\n".join(facts)

        # If no results, use fallback
        return FALLBACK_FACTS

    except Exception as e:
        print(f"Note: Could not fetch current facts ({e}). Using basic facts.")
        return FALLBACK_FACTS


def print_separator():
    """Print a visual separator"""
    print("\n" + "─" * TEXT_WIDTH + "\n")


def print_wrapped(text, prefix=""):
    """Print text with word wrapping, optionally with a prefix on the first line"""
    if prefix:
        # For first line with prefix, reduce available width
        first_line_width = TEXT_WIDTH - len(prefix)
        wrapper = textwrap.TextWrapper(width=first_line_width, break_long_words=False, break_on_hyphens=False)
        lines = wrapper.wrap(text)

        if lines:
            # Print first line with prefix
            print(f"{prefix}{lines[0]}")

            # Print remaining lines with indentation to match prefix
            indent = " " * len(prefix)
            for line in lines[1:]:
                print(f"{indent}{line}")
    else:
        # No prefix, just wrap to TEXT_WIDTH
        wrapper = textwrap.TextWrapper(width=TEXT_WIDTH, break_long_words=False, break_on_hyphens=False)
        for line in wrapper.wrap(text):
            print(line)


def get_opening_message(system_prompt):
    """Generate the opening flavor text and the wall's first message"""
    print("═" * TEXT_WIDTH)
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
    print_separator()

    # Get the wall's opening line from the API
    length_instruction = get_random_length_instruction()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{INTRO_PROMPT}\n\n{length_instruction}"}
        ],
        temperature=0.9
    )

    wall_greeting = response.choices[0].message.content
    print_wrapped(wall_greeting, "THE WALL: ")
    print_separator()

    return wall_greeting


def play_game(debug_mode=False):
    """Main game loop"""
    # Fetch current facts about the East Wing
    print("Fetching current information about the East Wing...")
    facts = fetch_east_wing_facts()

    # Show debug banner if in debug mode
    if debug_mode:
        print("\n*** DEBUG MODE ENABLED - Faster intensity progression ***\n")

    # Track conversation turns and summary
    turn_count = 0
    current_intensity_level = 0  # Track which intensity we're at (0-3)
    conversation_summary = ""  # Rolling summary replaces full conversation history

    # Generate initial system prompt
    system_prompt = get_system_prompt(facts, turn_count, debug_mode)

    # Get opening message (doesn't use JSON schema)
    opening = get_opening_message(system_prompt)

    # Main conversation loop
    while True:
        # Get player input
        try:
            if debug_mode:
                intensity = get_intensity_name(turn_count, debug_mode)
                player_input = input(f"YOU (turn {turn_count} - {intensity}): ").strip()
            else:
                player_input = input("YOU: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nThanks for playing!")
            sys.exit(0)

        # Check for quit commands
        if player_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
            print()
            print_wrapped("Well, I suppose I'll just stand here alone then. Typical.", "THE WALL: ")
            print("\nThanks for playing!")
            break

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
            length_instruction = get_random_length_instruction()
            messages.append({"role": "system", "content": length_instruction})

            # Call API with structured JSON output
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.9,
                response_format=WALL_RESPONSE_SCHEMA
            )

            # Parse JSON response
            result = json.loads(response.choices[0].message.content)
            wall_response = result["response"]
            conversation_summary = result["summary"]

            # Increment turn count
            turn_count += 1

            # Check if we've crossed into a new intensity level
            mode = 'debug' if debug_mode else 'regular'
            ranges = INTENSITY_RANGES[mode]

            new_intensity_level = 0
            if turn_count > ranges['serious'][1]:
                new_intensity_level = 3
            elif turn_count > ranges['medium'][1]:
                new_intensity_level = 2
            elif turn_count > ranges['mild'][1]:
                new_intensity_level = 1

            # If intensity level has changed, regenerate the system prompt
            if new_intensity_level != current_intensity_level:
                current_intensity_level = new_intensity_level
                system_prompt = get_system_prompt(facts, turn_count, debug_mode)

            # Display response
            print_separator()
            print_wrapped(wall_response, "THE WALL: ")
            print_separator()

        except Exception as e:
            print(f"\nError communicating with the wall: {e}")
            print("The wall seems to have gone silent...\n")
            break


def main():
    """Entry point"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="The East Wing - A conversational text adventure")
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Enable debug mode with faster intensity progression')
    args = parser.parse_args()

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your API key.")
        print("See .env.example for the format.")
        sys.exit(1)

    try:
        play_game(debug_mode=args.debug)
    except KeyboardInterrupt:
        print("\n\nThanks for playing!")
        sys.exit(0)


if __name__ == "__main__":
    main()

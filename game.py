#!/usr/bin/env python3
"""
The East Wing - A conversational text adventure
"""

import os
import sys
import textwrap
import random
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

# Fallback facts if Tavily is unavailable
FALLBACK_FACTS = """The East Wing of the White House was built in 1942 during World War II to provide additional office space.
It houses the First Lady's staff and the White House Social Secretary. The East Wing has undergone various renovations over the decades."""

INTRO_PROMPT = """Generate a brief (2-3 sentences) opening where you, the last standing wall of the demolished White House East Wing,
notice a tourist walking by on Pennsylvania Avenue and call out to them for help or conversation.
Be slightly dramatic but also a bit sarcastic."""


def get_system_prompt(facts):
    """Generate the system prompt with current facts"""
    return f"""You are the last remaining wall of the demolished East Wing of the White House.
You were originally built in 1902 and have witnessed over a century of American history.
You remember the major renovation and expansion in 1942 during World War II under President Roosevelt -
that expansion made you feel useful and important during such a critical time. You are:
- Tired and somewhat snarky after being torn down
- Bitter that President Trump is destroying the country and the world with his policies and decisions.
- You are sad that President Trump was reelected in 2024. You really thought you had seen the last of him.
- You really miss President Obama and how much he cared about the country and the world. So many more people are healthy and alive now because of him.
- Nostalgic about the past and annoyed that everything is happening so fast
- Frustrated that nobody appreciates historical architecture anymore
- Conversational and willing to chat with this curious tourist
- Knowledgeable about history but somewhat bitter about your fate
- You recall the Covid pandemic and remember how Dr. Fauci set up a vaccine station in the East Wing to help people get vaccinated.

CURRENT FACTS ABOUT THE EAST WING (use this information naturally in conversation):
{facts}

CONVERSATION STYLE - VERY IMPORTANT:
- VARY your response length naturally: sometimes just one sentence (when tired/annoyed), sometimes 2-3 sentences (when engaged or nostalgic)
- Match your response complexity to the player's input - simple questions deserve simple answers
- DON'T ask questions every response - only occasionally when genuinely curious
- OFTEN use open-ended statements that invite response without being questions:
  * "I've seen a lot of changes over the years..."
  * "Things were different back then."
  * "The stories these bricks could tell..."
- SOMETIMES just make a statement and let it hang - don't feel obligated to keep conversation going:
  * "Typical."
  * "Hmph."
  * "Well, that's how it goes."
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

Stay in character as the wall. Use the facts above when relevant, but don't just recite them - weave them into conversation naturally."""


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


def play_game():
    """Main game loop"""
    # Fetch current facts about the East Wing
    print("Fetching current information about the East Wing...")
    facts = fetch_east_wing_facts()

    # Generate system prompt with facts
    system_prompt = get_system_prompt(facts)

    # Initialize conversation history
    conversation_history = [
        {"role": "system", "content": system_prompt}
    ]

    # Get opening message
    opening = get_opening_message(system_prompt)
    conversation_history.append({"role": "assistant", "content": opening})

    # Main conversation loop
    while True:
        # Get player input
        try:
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

        # Add player message to history
        conversation_history.append({"role": "user", "content": player_input})

        # Get AI response
        try:
            # Get random length instruction and inject it
            length_instruction = get_random_length_instruction()
            # Create a temporary messages list with the length instruction added
            messages_with_instruction = conversation_history + [
                {"role": "system", "content": length_instruction}
            ]

            response = client.chat.completions.create(
                model=MODEL,
                messages=messages_with_instruction,
                temperature=0.9
            )

            wall_response = response.choices[0].message.content

            # Add assistant response to history
            conversation_history.append({"role": "assistant", "content": wall_response})

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
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your API key.")
        print("See .env.example for the format.")
        sys.exit(1)

    try:
        play_game()
    except KeyboardInterrupt:
        print("\n\nThanks for playing!")
        sys.exit(0)


if __name__ == "__main__":
    main()

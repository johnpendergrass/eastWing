# The East Wing - Technical Specifications

## Overview

A conversational text adventure game where the player talks with an AI character (the last remaining wall of the demolished White House East Wing). The wall has personality, remembers the conversation via rolling summaries, and evolves its intensity over time.

## Architecture

### Core Technology Stack
- **Language**: Python 3.8+
- **AI Model**: OpenAI GPT-4o-mini
- **APIs**:
  - OpenAI Chat Completions API with structured outputs
  - Tavily API for real-time web search (optional)
- **Dependencies**: openai, python-dotenv, tavily-python

### Memory System: Rolling Summary Approach

**Implementation**: Each turn, the AI receives:
1. System prompt (personality + instructions)
2. Conversation summary (if exists) from previous turn
3. Current player input

**Output**: Structured JSON with two fields:
- `response`: The wall's dialogue to display to player
- `summary`: Updated summary of entire conversation (≤400 words)

**Benefits**:
- Constant token usage per turn (~1500 tokens)
- Supports unlimited conversation length
- No context window limits
- Summary grows naturally to capture important details

**JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "response": {"type": "string"},
    "summary": {"type": "string"}
  },
  "required": ["response", "summary"]
}
```

### Personality System: Progressive Intensity Levels

**4 Discrete Intensity Levels**:

1. **Mild** (Regular: turns 0-7, Debug: turns 0-2)
   - Tired, snarky, nostalgic
   - Moderately bitter about current events
   - Conversational and willing to chat

2. **Medium** (Regular: turns 8-13, Debug: turns 3-5)
   - More vocal and frustrated
   - Drawing historical parallels
   - Questioning player about their views

3. **Serious** (Regular: turns 14-19, Debug: turns 6-8)
   - Darker, philosophical
   - Deep concerns about democracy
   - Explicit historical parallels to 1930s

4. **Angry** (Regular: turns 20+, Debug: turns 9+)
   - Fully engaged, passionate
   - No longer holding back
   - Fierce determination despite despair

**System Prompt**: Regenerated at intensity threshold crossings

### Response Variation System

**Weighted random sentence count distribution**:
- 20% - 1 sentence (very short/grumpy)
- 20% - 2 sentences (short)
- 25% - 3-4 sentences (medium)
- 20% - 4-5 sentences (medium-long)
- 15% - Up to 7-8 sentences (long/nostalgic)

**Implementation**: Prompt injection via system message

### Configuration

**Constants**:
- `MODEL = "gpt-4o-mini"` - OpenAI model
- `TEXT_WIDTH = 60` - Character width for text wrapping
- `INTENSITY_RANGES` - Turn thresholds for regular/debug modes

**Environment Variables** (.env file):
- `OPENAI_API_KEY` - Required
- `TAVILY_API_KEY` - Optional (uses fallback facts if missing)

### Debug Mode

**Activation**: `python game.py --debug` or `python game.py -d`

**Features**:
- Faster intensity progression (9 turns vs 20 turns to reach max intensity)
- Shows turn count and intensity level in prompt: `YOU (turn X - level):`
- Debug banner displayed at game start

### Character Design: The Wall

**Identity**: Last remaining wall of demolished White House East Wing
- Originally built: 1902
- Major renovation: 1942 under FDR
- Over 120 years of American history witnessed

**Personality Traits**:
- Bitter about Trump, nostalgic for Obama
- Knowledgeable about history
- Tired and snarky after demolition
- Progressive political views
- Self-aware about being "the East Wing" itself

**Memory Handling**:
- Uses summary to remember important details
- Can deflect forgotten details in-character:
  - "Look, I've been standing here for over a century AND I just got demolished. My memory's a bit hazy..."
  - "You'd have trouble remembering too if you were nothing but bricks and rubble..."

### Conversation Flow

1. **Opening**: Flavor text + AI-generated greeting (no JSON schema)
2. **Turn Loop**:
   - Player input
   - Build messages: system prompt + summary + player input + length instruction
   - API call with structured JSON response format
   - Parse response and summary
   - Update conversation summary
   - Check for intensity level change → regenerate system prompt if needed
   - Display response to player
3. **Exit**: `quit`, `exit`, `bye`, `goodbye`, or Ctrl+C

### Future Extensibility

**Dynamic System Prompts** (deferred):
- Add parameters to `get_system_prompt()`: intensity_modifier, player_sentiment
- Enable gradual intensity ramping (0-100 scale)
- React to player behavior in real-time
- Conditional personality adjustments

**Potential Additions**:
- Save/load conversations
- Multiple characters
- Different story scenarios
- ASCII art of the wall
- Sentiment analysis of player input

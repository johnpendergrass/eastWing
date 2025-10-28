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

### Personality System: Stage-Based Progression

**5 Discrete Stages** (using spaced numbering for future extensibility):

1. **stage_10** (Opening - Turn 0)
   - Very first response only
   - Always exactly 2 sentences
   - Uses 'mild' personality

2. **stage_20** (Early - Normal: turn 1-7, Fast: turn 1-2)
   - Tired, snarky, nostalgic
   - Moderately bitter about current events
   - Conversational and willing to chat
   - Response length: 1-4 sentences
   - Uses 'mild' personality

3. **stage_30** (Mid - Normal: turn 8-13, Fast: turn 3-5)
   - More vocal and frustrated
   - Drawing historical parallels
   - Questioning player about their views
   - Response length: 2-5 sentences
   - Uses 'upset' personality

4. **stage_40** (Late - Normal: turn 14-19, Fast: turn 6-8)
   - Darker, philosophical
   - Deep concerns about democracy
   - Explicit historical parallels to 1930s
   - Response length: 2-6 sentences
   - Uses 'serious' personality

5. **stage_50** (Final - Normal: turn 20+, Fast: turn 9+)
   - Fully engaged, passionate
   - No longer holding back
   - Fierce determination despite despair
   - Response length: 2-7 sentences
   - Uses 'angry' personality

**System Prompt**: Regenerated when crossing stage thresholds

**Reply Length Progression**: Response length scales naturally with emotional intensity. Uses simple uniform random selection between min/max for current stage.

### Configuration

**Constants**:
- `MODEL = "gpt-4o-mini"` - OpenAI model
- `TEXT_WIDTH = 60` - Character width for text wrapping
- `PROGRESSION_SPEEDS` - Stage thresholds and reply lengths for 'normal' and 'fast' modes

**Color Constants** (all customizable):
- `COLOR_SYSTEM` - Bright cyan (help, instructions, system messages)
- `COLOR_PLAYER` - Default (player input prompt)
- `COLOR_AI` - Bright white (wall responses)
- `COLOR_DEBUG` - Cyan (debug command output)
- `COLOR_ALERT` - Yellow (warnings, alerts)

**Environment Variables** (.env file):
- `OPENAI_API_KEY` - Required
- `TAVILY_API_KEY` - Optional (uses fallback facts if missing)

### Command-Line Flags

**`--debug` or `-d`**: Enable debug features
- Shows turn count and personality level in prompt
- Enables debug commands: `api`, `api all`, `memory`/`summary`, `fast`, `normal`
- Can also be toggled during gameplay with `debug on`/`debug off`

**`--fast` or `-f`**: Use fast stage progression
- Stages advance quicker (stage_50 at turn 9 vs turn 20)
- Useful for testing different personality levels
- Can also be toggled during gameplay with `fast`/`normal` (requires debug mode)

**Examples**:
- `python game.py` - Normal gameplay
- `python game.py --debug` - With debug commands
- `python game.py --fast` - Fast progression for testing
- `python game.py --debug --fast` - Both features

### Runtime Commands

**Always Available**:
- `help` - Display instructions and current state
- `speed` - Show current progression speed (normal or fast)
- `mood` - Show current mood/personality of the wall
- `quit`, `exit`, `bye`, `goodbye` - End game
- `debug on` / `debug off` - Toggle debug mode during gameplay

**Debug Commands** (when debug mode is active):
- `api` - Show last API request (truncated at 500 chars)
- `api all` - Show complete untruncated API request
- `memory` or `summary` - Analyze how conversation summary has evolved
- `fast` - Switch to fast progression speed (includes turn number and current mood)
- `normal` - Switch to normal progression speed (includes turn number and current mood)

**Command Validation**:
- Malformed commands (e.g., `debug xyz`, `api xyz`, `fast something`) are caught before reaching the AI
- Helpful error messages in yellow (COLOR_ALERT) explain correct usage
- Example: `'api xyz' is not a valid command. Try 'api' or 'api all'.`

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

1. **Opening**: Flavor text + AI-generated greeting
   - Display scenario text (system color)
   - Call API with stage_10 constraints (2 sentences exactly)
   - Uses JSON schema format (summary generated but not displayed)
   - Display wall's greeting (AI color)

2. **Turn Loop**:
   - Player input (player color)
   - Validate input for malformed commands
   - Check for commands (help, speed, mood, debug on/off, fast/normal, api, memory, quit)
   - Build messages: system prompt + summary + player input + length instruction
   - API call with structured JSON response format
   - Parse response and summary
   - Update conversation summary and history (keep last 5)
   - Check for stage transition → regenerate system prompt if needed
   - Display response to player (AI color)

3. **Exit**: `quit`, `exit`, `bye`, `goodbye`, or Ctrl+C

### Color System

**Purpose-Based Color Coding**:
- **SYSTEM** (bright cyan) - Help text, instructions, confirmations, errors
- **PLAYER** (default) - Player input prompt only
- **AI** (bright white) - Wall's dialogue responses only
- **DEBUG** (cyan) - Output from debug commands (api, memory, summary)
- **ALERT** (yellow) - Warnings and important notices

**Customization**: All colors have commented alternatives at top of game.py for easy switching

### Future Extensibility

**Stage System Expansion**:
- Spaced numbering (10, 20, 30...) allows easy insertion of intermediate stages
- Could add stage_15, stage_25, etc. without refactoring
- Example: stage_15 could be a transitional "slightly frustrated" level

**Dynamic System Prompts** (deferred):
- Add parameters to `get_system_prompt()`: intensity_modifier, player_sentiment
- Enable gradual intensity ramping (0-100 scale)
- React to player behavior in real-time
- Conditional personality adjustments

**Debug Features**:
- Additional debug commands for testing (e.g., jump to specific stage)
- Conversation state inspection
- Export debug logs

**Potential Additions**:
- Save/load conversations
- Multiple characters
- Different story scenarios
- ASCII art of the wall
- Sentiment analysis of player input
- Color theme presets (dark mode, light mode, high contrast)
- Configuration file for persistent settings

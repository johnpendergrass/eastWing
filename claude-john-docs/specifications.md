# The East Wing - Technical Specifications
**Version:** 0.03
**Last Updated:** 2025-10-28

---

## Project Overview

The East Wing is a conversational text adventure game where the player chats with the last remaining wall of the demolished White House East Wing. The wall is a character with evolving personality, political opinions, and emotional depth based on turn progression.

---

## Design Decisions

### 1. Architecture Pattern: Stateless API with Rolling Summary

**Decision:** Use rolling summary instead of full conversation history

**Why:**
- **Token efficiency:** Conversation history grows linearly; summary stays constant (~500 words)
- **Cost control:** Each API call uses ~700-1000 tokens vs thousands for full history
- **Context preservation:** AI-generated summary captures what matters for continuity
- **Scalability:** Unlimited conversation length without context window limits

**Implementation:**
- Each response includes JSON with `{response, summary}` fields
- Summary replaces entire conversation history on next turn
- Last 5 summaries stored for meta-analysis

---

### 2. Stage-Based Personality Progression

**Decision:** 6 distinct stages (10, 20, 30, 40, 50, 90) with automatic progression based on turn count

**Why:**
- **Natural character development:** Wall gradually opens up as trust builds
- **Dynamic storytelling:** Conversation evolves from mild → upset → serious → angry → tired
- **Replayability:** Fast mode for testing, slow mode for full experience
- **Predictable pacing:** Clear progression markers

**Stages:**
- **Stage 10** (Turn 0): Mild - tired and snarky, initial greeting
- **Stage 20** (Turn 1): Mild - conversational but reserved
- **Stage 30** (Turn 5/3): Upset - more vocal, drawing historical parallels
- **Stage 40** (Turn 8/5): Serious - darker, philosophical, worried
- **Stage 50** (Turn 10/7): Angry - fully engaged, intensely passionate
- **Stage 90** (Turn 15/12): Tired - exhausted, ready to end conversation

**Two Speed Modes:**
- **Slow** (default): 25+ turns to completion, gradual progression
- **Fast** (testing): 12 turns to completion, quick personality shifts

---

### 3. Unified Command System (No Debug Mode)

**Decision:** Make all commands available to all users, remove debug mode entirely

**Why:**
- **Simplicity:** No mode switching, no confusion about what's available
- **Discoverability:** All features in one help screen
- **User empowerment:** Players can explore API details, memory, etc. if curious
- **Reduced complexity:** Fewer conditional code paths

**Command Pre-Interpreter:**
- Single `parse_command()` function categorizes input
- Returns command type + data or ('chat', player_input)
- Centralized validation with helpful error messages
- Clean dispatcher pattern in main loop

---

### 4. Selection Menu Interface

**Decision:** Use numbered selection (1, 2, 3) vs arrow keys or text input

**Why:**
- **Zero dependencies:** Works on all terminals without libraries
- **Universal compatibility:** No ANSI issues on old terminals
- **Speed:** Type a number faster than arrow navigation for 2-4 options
- **Clarity:** Everyone understands "type 1 or 2"
- **Simplicity:** Matches John's philosophy of easy-to-understand code

**Format:**
```
════════════════════════════════════════════════════════════
                  SELECT AI MODEL
════════════════════════════════════════════════════════════

  [1] gpt-5-mini ★ CURRENT
      → Excellent quality, fast responses, moderate cost
      → Performance: Excellent | Speed: Fast | Cost: Moderate

  [2] gpt-5-nano
      → Fastest responses, lowest cost, good quality
      → Performance: Good | Speed: Very Fast | Cost: Cheapest

  [0] Cancel
────────────────────────────────────────────────────────────
Select (0-2):
```

**Commands with Selection:**
- `speed ?` → Choose slow or fast
- `mood ?` → Choose mild, upset, serious, angry, tired
- `model ?` → Choose between 4 AI models

---

### 5. Model Configuration & Runtime Switching

**Decision:** Allow model switching mid-game without losing context

**Why:**
- **Experimentation:** Players can compare model quality in same conversation
- **Cost control:** Start with expensive model, switch to cheap if acceptable
- **Performance tuning:** Switch to faster model if impatient
- **Stateless API:** Every call is independent, only summary matters

**Supported Models:**
1. **gpt-5-mini** (default) - Best balance of quality/cost/speed
2. **gpt-5-nano** - Fastest and cheapest, 50% cost savings
3. **gpt-5** - Best quality, expensive, slower
4. **gpt-4o-mini** - Legacy fallback

**Model-Specific Configurations:**
- Temperature support (GPT-4 only, GPT-5 doesn't support custom temps)
- Reasoning effort (GPT-5 models only, set to 'minimal' for speed)

---

### 6. Mood Override System

**Decision:** Allow manual mood selection that overrides stage progression

**Why:**
- **Player agency:** Want to explore a specific personality without waiting
- **Testing:** Quickly test dialogue at different mood levels
- **Creative play:** Players can keep wall calm or make it angry on demand
- **Persistent:** Override stays active until changed or player exits

**Implementation:**
- `mood_override = None` (auto-progression) or `'angry'` (manual)
- Check override first in `get_system_prompt()`, fall back to stage
- Regenerate system prompt immediately when mood changed
- Display current mood (manual or automatic) in help screen

---

### 7. Structured Summary Format

**Decision:** Use structured format with 8 labeled sections vs narrative paragraph

**Why:**
- **Information density:** More facts in fewer words
- **Parseable:** AI can easily find specific info (moods, topics, opinions)
- **Consistency:** Every summary has same structure
- **Debugging:** Easier to verify summary quality

**Format:**
```
[WALL MOOD: snarky]
[PLAYER MOOD: curious]
[LAST TOPIC: demolition timeline]
[KEY TOPICS COVERED: bullet list]
[PLAYER INFO: facts about player]
[IMPORTANT REFERENCES: historical events mentioned]
[OPINION: political views discussed]
[CONVERSATION SUMMARY: 2-3 sentence overview]
```

**Character limit:** 1000 words (structured format actually uses less than narrative)

---

### 8. Real-Time Facts Integration (Tavily API)

**Decision:** Fetch current web facts about East Wing and Trump at game start

**Why:**
- **Relevance:** Game references actual current events
- **Freshness:** Not limited to training data cutoff
- **Authenticity:** Wall can discuss real recent developments
- **Filtered:** Clean text-only, no image refs or navigation menus

**Tavily Configuration:**
- `search_depth="advanced"` - Better content extraction
- `include_images=False` - No image references
- `include_answer=True` - AI-generated clean summary
- `max_results=3` per query

**Fallback:** Static facts if API unavailable

---

### 9. Color-Coded Output

**Decision:** Use ANSI color codes for different message types

**Colors:**
- `COLOR_AI` (cyan/36m): The Wall's responses
- `COLOR_PLAYER` (green/32m): Player prompts
- `COLOR_SYSTEM` (yellow/33m): Status messages, help text
- `COLOR_ALERT` (red/31m): Errors, warnings
- `COLOR_DEBUG` (magenta/35m): Technical info (API, memory)

**Why:**
- **Readability:** Instantly distinguish player vs AI text
- **Visual hierarchy:** System messages vs gameplay
- **Accessibility:** Works on all modern terminals
- **Simple:** Basic ANSI codes, no external libraries

---

### 10. Text Wrapping

**Decision:** Wrap text at 60 characters with proper formatting

**Why:**
- **Readability:** Long lines strain eyes
- **Terminal compatibility:** Fits most terminal widths
- **Professionalism:** Clean, newspaper-like presentation
- **Prefix alignment:** "THE WALL: " prefix + wrapped indent

**Implementation:** Python `textwrap.TextWrapper` with `width=60`

---

## File Organization

```
game.py structure (~1275 lines):
├── Constants (lines 1-210)
│   ├── ANSI colors
│   ├── MODEL_OPTIONS (4 models with capabilities)
│   ├── DEFAULT_MODEL = 'gpt-5-mini'
│   ├── WALL_RESPONSE_SCHEMA (JSON schema)
│   ├── PROGRESSION_SPEEDS (slow + fast)
│   └── INTRO_PROMPT / FALLBACK_FACTS
│
├── Core Functions (lines 210-720)
│   ├── get_system_prompt(facts, turn, speed, mood_override)
│   ├── get_random_length_instruction()
│   ├── get_current_stage()
│   ├── fetch_east_wing_facts() - Tavily API
│   ├── validate_model()
│   ├── print helpers (separator, wrapped)
│   ├── display_api_debug_info()
│   ├── analyze_summary_evolution()
│   └── display_memory_analysis()
│
├── ═══ UI / COMMAND SYSTEM ═══ (lines 720-930)
│   ├── parse_command() - Command pre-interpreter
│   ├── show_selection_menu() - Generic numbered menu
│   ├── select_speed()
│   ├── select_mood()
│   ├── select_model()
│   ├── display_startup()
│   └── display_help() - Unified help screen
│
├── ═══ GAME LOGIC ═══ (lines 930-1200)
│   ├── get_opening_message()
│   └── play_game(progression_speed, model)
│       ├── Setup & initialization
│       ├── Input loop
│       ├── Command dispatcher (no debug mode!)
│       └── Conversation/API logic
│
└── main() - Entry point with argparse (lines 1200+)
```

**Organization Philosophy:**
- Clear visual separators between sections
- UI separate from game logic (per John's request)
- All related functions grouped together
- Easy to find and modify specific functionality

---

## Command-Line Interface

```bash
python game.py [--fast | --slow] [--model MODEL_NAME]

Flags:
  --fast, -f       Fast progression (12 turns to final stage)
  --slow, -s       Slow progression (25+ turns) [DEFAULT]
  --model NAME     Select AI model (default: gpt-5-mini)

Examples:
  python game.py                          # Slow mode, gpt-5-mini
  python game.py --fast                   # Fast mode for testing
  python game.py --model gpt-5-nano       # Cheapest model
  python game.py --fast --model gpt-5     # Fast + best quality
```

**Note:** Debug mode has been removed in v0.03. All commands are now available to everyone.

---

## Runtime Commands

**All commands available to everyone:**

```
help         - Show help screen with current state

quit/exit/bye/goodbye/ctrl-c - Exit game

speed        - Show current game speed
speed ?      - Select new speed (slow or fast)

mood         - Show the Wall's current mood
mood ?       - Manually set the Wall's mood

model        - Show current AI model
model ?      - Switch AI models mid-game

api          - Show last API request (brief)
api all      - Show complete untruncated API request

memory       - AI analyzes summary evolution
summary      - (alias for memory)
```

**Command Format:**
- Commands with `?` show a numbered selection menu
- Menu format: Type number (0-4) to select, 0 to cancel
- All menus have consistent formatting with ★ CURRENT marker

---

## Help Screen Format

```
════════════════════════════════════════════════════════════
 CURRENT STATE: Turn: 7 | Mood: calm | Speed: slow | Model: gpt-5-mini
════════════════════════════════════════════════════════════

                        HOW TO PLAY
────────────────────────────────────────────────────────────

• Type your responses to chat with the character
• The character will respond based on your conversation
• Be curious, ask questions, share your thoughts!

COMMANDS YOU MAY USE DURING THE CONVERSATION:

help         - show this message

quit         - any of these will quit the program
exit
bye, goodbye
ctrl-c

speed        - show current game speed
speed ?      - change the game speed

mood         - show the current mood of 'the Wall'
mood ?       - change the mood

model        - show current openAI model being used
model ?      - change the AI model being used

api          - show the last API request (brief)
api all      - show the complete untruncated API request

memory       - AI summarizes the last few exchanges
summary        between the player and 'the Wall'.

────────────────────────────────────────────────────────────
```

---

## Algorithm Details

### Stage Determination

```python
def get_current_stage(turn_count, progression_speed):
    """Reverse lookup: check stages 90→50→40→30→20→10"""
    stage_keys = ['stage_90', 'stage_50', 'stage_40',
                  'stage_30', 'stage_20', 'stage_10']

    for stage_key in stage_keys:
        if turn_count >= PROGRESSION_SPEEDS[speed][stage_key]['start_turn']:
            return stage_key

    return 'stage_10'
```

**Why reverse order:** Find highest stage player has reached

### Command Parsing

```python
def parse_command(player_input):
    """
    Returns: (command_type, data)

    Priority:
    1. Exact quit commands
    2. Exact other commands
    3. Validation for common mistakes
    4. Return 'chat' for conversation
    """
```

**Command types:** quit, help, speed_show, speed_select, mood_show, mood_select, model_show, model_select, api, api_all, memory, chat, error

---

## Future Enhancement Considerations

### Potential Additions:
1. **Save/Load:** Serialize game state (turn, summary, mood) to resume later
2. **Multiple Characters:** Other White House fixtures with different personalities
3. **Branching Paths:** Different story branches based on player's political stance
4. **Achievement System:** Track milestones
5. **Conversation Export:** Save transcripts as text/JSON
6. **Theme System:** User-configurable color schemes

### Known Limitations:
- No save game system
- Summary quality depends on AI's summarization skill
- Tavily API requires internet connection
- Color codes might not work on very old terminals
- Quit intent detection is simple (exact match only)

---

## Testing Checklist

**Functionality:**
- ✅ All commands work (help, speed, mood, model, api, memory, quit)
- ✅ Selection menus work (speed ?, mood ?, model ?)
- ✅ Model switching preserves conversation context
- ✅ Mood override persists correctly
- ✅ Stage progression occurs at correct turns
- ✅ API errors handled gracefully
- ✅ Color coding displays correctly
- ✅ Text wrapping works properly
- ✅ Invalid commands show helpful errors

**Performance Targets:**
- Response time: < 3 seconds (gpt-5-nano minimal reasoning)
- Cost per 20-turn conversation:
  - gpt-5-nano: ~$0.012
  - gpt-5-mini: ~$0.060
  - gpt-5: ~$0.30
  - gpt-4o-mini: ~$0.048
- Memory usage: < 50MB
- Python 3.8+ compatibility

---

*This specification reflects v0.03 after the major help/debug system overhaul completed on 2025-10-28.*

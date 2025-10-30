# The East Wing - Technical Specifications
**Version:** 0.19.2 (Error Handling & API Key Security)
**Last Updated:** 2025-10-30

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
- **Replayability:** Fast mode for quick experience, slow mode for full experience
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
- **Fast**: 12 turns to completion, quick personality shifts

---

### 3. Word-Based Response Length Control

**Decision:** Use word counts instead of sentence counts to control AI response length

**Why:**
- **Prevents gaming:** AI can't create overly long "sentences" with semicolons and em-dashes
- **More predictable:** Word counts give consistent response sizes
- **Natural completion:** Explicitly allow exceeding count to complete thoughts
- **Better UX:** Responses are appropriately sized for readability

**Implementation:**
- Each stage has `reply_words_min` and `reply_words_max` parameters
- Random word count selected within range each turn
- Instruction: "Reply in approximately X words. Complete your sentence and thought - do not cut off mid-sentence or mid-thought."

**Word Count Ranges by Stage:**
| Stage | Min | Max | Typical Range |
|-------|-----|-----|---------------|
| 10 (opening) | 30 | 40 | ~35 words |
| 20 (early) | 15 | 85 | 15-85 words |
| 30 (mid) | 30 | 105 | 30-105 words |
| 40 (late) | 30 | 125 | 30-125 words |
| 50 (angry) | 30 | 145 | 30-145 words |
| 90 (tired) | 30 | 85 | 30-85 words |

**Key Phrase in System Prompt:**
"The word count is a TARGET, not a hard limit - ALWAYS complete your full sentences and thoughts. It's better to exceed the word count than to cut off mid-sentence or leave a thought incomplete."

---

### 4. Dynamic Color Theme System

**Decision:** Allow runtime color theme switching with 5 predefined themes

**Why:**
- **User preference:** Different users prefer different color schemes
- **Accessibility:** Some users may need specific color combinations
- **Thematic fit:** Mar-a-Lago theme adds humor, Matrix theme for retro feel
- **Experimentation:** Easy to try different aesthetics mid-game

**Implementation:**
- `COLOR_THEMES` dictionary defines all themes
- `set_color_theme()` function updates global color variables at runtime
- `select_color_theme()` provides selection menu
- Theme persists for entire session

**Available Themes:**
1. **white-house** (default)
   - System: Light gray (subtle, professional)
   - AI: Bright white (clean, clear)
   - Player: Default terminal
   - Alert: Yellow (attention-grabbing)

2. **mar-a-lago** (garish/tacky)
   - System: Bright yellow (gaudy)
   - AI: Yellow/orange (ostentatious)
   - Player: Default terminal
   - Alert: Bright red (loud)

3. **east-wing** (calm/peaceful)
   - System: Light blue (calm, professional)
   - AI: Bright white (subtle)
   - Player: Default terminal
   - Alert: Yellow

4. **matrix** (retro tech)
   - System: Light green (terminal style)
   - AI: Green (classic Matrix)
   - Player: Default terminal
   - Alert: Bright red

5. **monochrome** (no colors)
   - System: Light gray
   - AI: Bright white
   - Player: Default terminal
   - Alert: Light gray (same as system)

**Color Simplification:**
- Removed COLOR_DEBUG (was in v0.03)
- Now use only 4 colors: SYSTEM, PLAYER, AI, ALERT
- Technical output (api, memory) uses COLOR_SYSTEM

---

### 5. Unified Command System (No Debug Mode)

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

### 6. Intuitive Help Shortcuts

**Decision:** Support "help <command>" syntax in addition to "?" syntax

**Why:**
- **Intuitive:** New users naturally type "help model" to see model options
- **Discoverability:** Makes features more discoverable
- **Non-breaking:** Doesn't remove existing "?" syntax
- **Graceful fallback:** Unknown "help X" commands show general help

**Supported Shortcuts:**
- `help speed` → Speed selection menu (same as `speed ?`)
- `help mood` → Mood selection menu (same as `mood ?`)
- `help model` → Model selection menu (same as `model ?`)
- `help color` → Color theme selection menu (same as `color ?`)
- `help api` → Show API request (same as `api`)
- `help api all` → Show full API request (same as `api all`)
- `help memory` / `help summary` → Memory analysis (same as `memory`)
- `help <anything else>` → General help screen (catch-all)

---

### 7. Selection Menu Interface

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
- `color ?` → Choose between 5 color themes

---

### 8. Model Configuration & Runtime Switching

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
- Reasoning effort (GPT-5 models only, set to 'minimal' or 'low' for speed)

---

### 9. Mood Override System

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

### 10. Structured Summary Format

**Decision:** Use structured format with 8 labeled sections vs narrative paragraph

**Why:**
- **Information density:** More facts in fewer words
- **Parseable:** AI can easily find specific info (moods, topics, opinions)
- **Consistency:** Every summary has same structure
- **Debugging:** Easier to verify summary quality

**Format:**
```
[WALL MOOD: your current emotional state]
[PLAYER MOOD: player's apparent emotional state]
[LAST TOPIC: brief phrase describing recent subject]
[KEY TOPICS COVERED: bullet list of 3-5 main subjects]
[PLAYER INFO: facts about the player - views, background, questions]
[IMPORTANT REFERENCES: historical events, people, or facts discussed]
[OPINION: political views discussed by wall or player]
[CONVERSATION SUMMARY: 2-3 sentence overview]
```

**Character limit:** 1000 words (structured format actually uses less than narrative)

---

### 11. Real-Time Facts Integration (Tavily API)

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

### 12. Enhanced Startup Sequence

**Decision:** Streamlined startup with clear information hierarchy

**Why:**
- **Information first:** Show model and speed before long fetch process
- **Better expectations:** Timing reminder before first API call
- **Visual clarity:** Proper blank lines and color coding
- **Less clutter:** Removed redundant text

**Startup Flow:**
```
Using model: gpt-5-mini                    [ALERT COLOR]
Current game speed: slow                   [ALERT COLOR]

Fetching current information about the East Wing...

Type 'help' to switch models, speeds, moods, and colors.  [ALERT COLOR]

══════════════════════════════════════════════════════════
                  THE EAST WING
══════════════════════════════════════════════════════════
[opening scene...]

⏱ Note: AI responses may take 5-10 seconds (or longer!). Please be patient...
──────────────────────────────────────────────────────────

THE WALL: [first AI response here]
```

---

### 13. Color-Coded Output

**Decision:** Use ANSI color codes for different message types

**Colors:**
- `COLOR_SYSTEM` (varies by theme): Help, menus, status, technical info
- `COLOR_PLAYER` (default): Player input prompts
- `COLOR_AI` (varies by theme): The Wall's responses
- `COLOR_ALERT` (varies by theme): Errors, warnings, important notices

**Why:**
- **Readability:** Instantly distinguish player vs AI text
- **Visual hierarchy:** System messages vs gameplay
- **Accessibility:** Works on all modern terminals
- **Simple:** Basic ANSI codes, no external libraries
- **Customizable:** 5 themes for different preferences

---

### 14. Text Wrapping

**Decision:** Wrap text at 72 characters with proper formatting

**Why:**
- **Readability:** Long lines strain eyes
- **Terminal compatibility:** Fits most terminal widths
- **Professionalism:** Clean, newspaper-like presentation
- **Prefix alignment:** "THE WALL: " prefix + wrapped indent

**Implementation:** Python `textwrap.TextWrapper` with `width=72`

---

### 15. Graceful API Key Error Handling

**Decision:** Defer OpenAI client initialization and catch errors with user-friendly messages

**Why:**
- **Security incident:** OpenAI detected keys in GitHub repo and disabled them (v0.19.1)
- **User experience:** Crashes with technical errors are confusing for non-developers
- **Windows .exe behavior:** Window instantly closes on error, users can't see what went wrong
- **Distribution safety:** Need to keep placeholder keys in GitHub, real keys only in .exe

**Problem with v0.19.1:**
```python
# Old way - failed at script load time (line 37)
client = OpenAI(api_key="sk-proj-...")
# If key invalid, Python crashes immediately with no way to catch it
```

**Solution in v0.19.2:**
```python
# Line 37 - Store key as variable
OPENAI_API_KEY = "your-actual-openai-key-here"

# Line 40 - Defer client creation
client = None

# Line 1127 - Initialize with error handling
try:
    global client
    if client is None:
        client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(**api_params)
except Exception as e:
    display_api_key_error_and_exit(str(e))
```

**Error Display Function (line 254):**
- Shows formatted error message in a bordered box
- Explains that valid OpenAI API key is required
- Displays specific error details for debugging
- **Waits for Enter key** - Critical for .exe so window doesn't disappear
- Exits gracefully with `sys.exit(1)`

**Error Message Format:**
```
════════════════════════════════════════════════════════════
                         ERROR
════════════════════════════════════════════════════════════

OpenAI API key is missing or invalid.

This program requires a valid OpenAI API key to function.

Error details: [specific OpenAI error message]

Press <Enter> to exit...
════════════════════════════════════════════════════════════
```

**Tavily Error Handling:**
- Non-fatal: Shows warning but continues with fallback facts
- Message: "Tavily API key missing or invalid. Using fallback facts."
- Game playable without Tavily (basic facts provided)

**Benefits:**
- Users see clear explanation instead of Python traceback
- Window stays open so users can read error (critical for .exe)
- Catches all error types: missing key, invalid key, expired key, network errors
- Allows safe build workflow (placeholder keys in GitHub, real keys in .exe)

---

## File Organization

```
eastWing.py structure (~1415 lines in v0.19.2):
├── Shebang & Docstring (lines 1-11)
├── Imports (lines 13-21)
├── Windows Color Support (lines 26-33)
├── API Key & Client Setup (lines 35-40) - NEW in v0.19.2
│   ├── OPENAI_API_KEY variable (placeholder in GitHub, real in .exe)
│   └── client = None (deferred initialization)
├── Game Configuration (lines 42-43)
│   └── TEXT_WIDTH = 72
├── Color Theme System (lines 45-95)
│   ├── COLOR_THEMES dict (5 themes)
│   ├── DEFAULT_COLOR_THEME
│   └── Initialize color variables
├── Model Configuration (lines 97-138)
│   ├── MODEL_OPTIONS (4 models with capabilities)
│   └── DEFAULT_MODEL = 'gpt-5-mini'
├── Response Schema (lines 140-161)
│   └── WALL_RESPONSE_SCHEMA (JSON schema)
├── Stage Progression Config (lines 163-265)
│   ├── PROGRESSION_SPEEDS (slow + fast)
│   └── Word count ranges per stage
├── Fallback Facts & Prompts (lines 267-275)
│
├── Core Functions (lines 254-808) - UPDATED in v0.19.2
│   ├── display_api_key_error_and_exit(error_message) - NEW
│   ├── get_system_prompt(facts, turn, speed, mood_override)
│   ├── get_random_length_instruction(turn, speed)
│   ├── get_current_stage(turn, speed)
│   ├── fetch_east_wing_facts() - Tavily API with improved errors
│   ├── validate_model(model_name)
│   ├── set_color_theme(theme_name)
│   ├── print_separator()
│   ├── print_wrapped(text, prefix, color)
│   ├── display_api_debug_info(messages, length, truncate)
│   ├── analyze_summary_evolution(history, model)
│   └── display_memory_analysis(history, model)
│
├── ═══ UI / COMMAND SYSTEM ═══ (lines 765-957)
│   ├── parse_command() - Command pre-interpreter with help shortcuts
│   ├── show_selection_menu() - Generic numbered menu
│   ├── select_speed(current)
│   ├── select_mood(current)
│   ├── select_model(current)
│   ├── select_color_theme(current)
│   ├── display_startup()
│   └── display_help(turn, mood, speed, model)
│
├── ═══ GAME LOGIC ═══ (lines 958-1307)
│   ├── get_opening_message(prompt, speed, model)
│   └── play_game(speed, model)
│       ├── Fetch facts & setup
│       ├── Initialize conversation state
│       ├── Get opening message
│       └── Main input loop with command dispatcher
│
└── main() - Entry point with argparse (lines 1308-1376)
```

**Organization Philosophy:**
- Clear visual separators between sections
- UI separate from game logic (per John's request)
- All related functions grouped together
- Easy to find and modify specific functionality

---

## Command-Line Interface

```bash
python eastWing.py [--fast | --slow] [--model MODEL_NAME]

Flags:
  --fast, -f       Fast progression (12 turns to final stage)
  --slow, -s       Slow progression (25+ turns) [DEFAULT]
  --model NAME     Select AI model (default: gpt-5-mini)

Examples:
  python eastWing.py                          # Slow mode, gpt-5-mini
  python eastWing.py --fast                   # Fast mode
  python eastWing.py --model gpt-5-nano       # Cheapest model
  python eastWing.py --fast --model gpt-5     # Fast + best quality
```

**Note:** Debug mode was removed in v0.03. All commands now available to everyone.

---

## Runtime Commands

**All commands available to everyone:**

```
help, ?      - Show help screen with current state
help <cmd>   - Shortcuts: help speed, help mood, help model, help color, help api, help memory

quit/exit/bye/goodbye/ctrl-c - Exit game

speed        - Show current game speed
speed ?      - Select new speed (slow or fast)

mood         - Show the Wall's current mood
mood ?       - Manually set the Wall's mood

model        - Show current AI model
model ?      - Switch AI models mid-game

color        - Show current color theme
color ?      - Change color theme

api          - Show last API request (brief)
api all      - Show complete untruncated API request

memory       - AI analyzes summary evolution
summary      - (alias for memory)

turn         - Show current turn, speed, and mood
```

**Command Format:**
- Commands with `?` show a numbered selection menu
- Menu format: Type number (0-N) to select, 0 to cancel
- All menus have consistent formatting with ★ CURRENT marker

---

## Help Screen Format

```
════════════════════════════════════════════════════════════════════════
 CURRENT STATE: Turn: 7 | Mood: calm | Speed: slow | Model: gpt-5-mini
════════════════════════════════════════════════════════════════════════

                        HOW TO PLAY
────────────────────────────────────────────────────────────────────────

• Type your responses to chat with the character
• The character will respond based on your conversation
• Be curious, ask questions, share your thoughts!

COMMANDS YOU MAY USE DURING THE CONVERSATION:

help, ?      - show this message

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

color        - show current color theme
color ?      - change the color theme

api          - show the last API request (brief)
api all      - show the complete untruncated API request

memory       - AI summarizes the last few exchanges
summary        between the player and 'the Wall'.

turn         - show current turn, speed, and mood

────────────────────────────────────────────────────────────────────────
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
    2. Exact help command
    3. Help shortcuts (help <option>)
    4. Other exact commands
    5. Validation for common mistakes
    6. Return 'chat' for conversation
    """
```

**Command types:** quit, help, speed_show, speed_select, mood_show, mood_select, model_show, model_select, color_show, color_select, api, api_all, memory, chat, error

### Word Count Selection

```python
def get_random_length_instruction(turn_count, progression_speed):
    stage_config = PROGRESSION_SPEEDS[progression_speed][stage_key]
    min_words = stage_config['reply_words_min']
    max_words = stage_config['reply_words_max']
    target_words = random.randint(min_words, max_words)
    return f"Reply in approximately {target_words} words. Complete your sentence and thought..."
```

**Variation:** Each turn gets random word count within stage range

---

## Windows Executable Distribution

### PyInstaller Build (v0.19.2)

**Status:** ✅ COMPLETED - Tested and verified on multiple machines

**Distribution Method:** John's Dropbox links (private sharing with trusted friends)

**Build Configuration:**
- **Tool:** PyInstaller
- **Mode:** --onefile (single executable)
- **Compression:** UPX enabled
- **Platform:** Windows 10+ (64-bit)
- **File Size:** ~17 MB
- **Spec File:** eastWing.spec

**What's Bundled:**
- Complete Python 3.x runtime
- All dependencies (openai, python-dotenv, tavily-python)
- Standard library modules
- **API keys embedded from variables** (eastWing.py lines 37 and 523)

**API Key Implementation (v0.19.2):**
- **OpenAI API Key** - Stored in variable at line 37: `OPENAI_API_KEY = "sk-proj-..."`
- **Tavily API Key** - Stored in variable at line 523: `tavily_key = "tvly-dev-..."`
- **Client Initialization** - Deferred until first use (line 40: `client = None`)
- **Error Handling** - Graceful error display if keys are missing/invalid
- No `.env` file required or bundled
- Keys are embedded directly in the executable
- ⚠️ **Security Note:** Suitable for private distribution to trusted friends only. NOT suitable for public distribution without modification.

**Build Command (Safe Workflow):**
```bash
# IMPORTANT: Add real keys to eastWing.py first (lines 37 and 523)

# Clean previous builds
rm -rf build/ dist/

# Build executable (with real keys in variables)
pyinstaller eastWing.spec

# Output location
dist/eastWing.exe

# CRITICAL: Immediately restore placeholder keys in eastWing.py before git operations
# Line 37: OPENAI_API_KEY = "your-actual-openai-key-here"
# Line 523: tavily_key = "your-actual-tavily-key-here"
```

**Alternative: Git Checkout Method**
```bash
# Add real keys to eastWing.py
# Build executable
pyinstaller eastWing.spec

# Restore file to GitHub version (removes real keys)
git checkout eastWing.py

# Now safe to commit other changes
```

**Distribution Requirements:**
- Windows 10 or later (64-bit)
- Internet connection (for OpenAI and Tavily APIs)
- ~50-100 MB temp disk space (for extraction)
- No Python installation required
- No additional dependencies
- No .env file or configuration needed

**Testing Results:**
- ✅ Runs on Windows 10 without Python
- ✅ Runs on Windows 11 without Python
- ✅ Works without .env file (keys embedded)
- ✅ All game features functional
- ✅ All commands work correctly
- ✅ AI integration operational (both OpenAI and Tavily)
- ✅ Color themes display properly
- ✅ Performance acceptable (~2-3 second startup)

**Known Behaviors:**
- First startup takes 2-3 seconds (PyInstaller extraction)
- Antivirus may flag as suspicious (false positive - common with PyInstaller)
- Temp files created in %TEMP% directory
- API keys embedded in executable (extractable with reverse-engineering effort)

**Security Considerations:**
- ✅ **Safe for:** Private distribution via Dropbox to trusted friends
- ⚠️ **NOT safe for:** Public distribution (GitHub releases, itch.io, website downloads)
- API keys can be extracted from the executable by someone with technical skills
- For public distribution, would need to rebuild without hardcoded keys and require users to provide their own

**For Public Distribution (Future):**
- Remove hardcoded keys from eastWing.py (lines 23, 485)
- Restore .env file requirement or add command-line key arguments
- Update DISTRIBUTION_README.md with API key setup instructions
- Consider alternative approaches (backend proxy, subscription model, etc.)
- Create Linux/Mac builds
- Code signing to reduce antivirus warnings

---

## Future Enhancement Considerations

### Potential Additions:
1. **Save/Load:** Serialize game state (turn, summary, mood, theme) to resume later
2. **Multiple Characters:** Other White House fixtures with different personalities
3. **Branching Paths:** Different story branches based on player's political stance
4. **Achievement System:** Track milestones
5. **Conversation Export:** Save transcripts as text/JSON
6. **Custom Themes:** User-configurable color schemes

### Long-Term Ideas:
1. **Web Interface:** Browser-based version using Flask/FastAPI
2. **Voice Integration:** Text-to-speech for Wall's responses
3. **Multi-language:** Support for other languages
4. **Analytics Dashboard:** Track conversation patterns, topics, sentiment

### Known Limitations:
- No save game system
- Summary quality depends on AI's summarization skill
- Tavily API requires internet connection
- Color codes might not work on very old terminals
- Quit intent detection is simple (exact match only)

---

## Testing Checklist

**Functionality:**
- ✅ All commands work (help, ?, speed, mood, model, color, api, memory, turn, quit)
- ✅ Selection menus work (speed ?, mood ?, model ?, color ?)
- ✅ Turn command shows current state (turn, speed, mood, model)
- ✅ '?' help synonym works correctly
- ✅ Model switching preserves conversation context
- ✅ Color theme switching changes colors immediately
- ✅ Mood override persists correctly
- ✅ Stage progression occurs at correct turns
- ✅ Help shortcuts work (help speed, help model, etc.)
- ✅ API errors handled gracefully
- ✅ Color coding displays correctly
- ✅ Text wrapping works properly at 72 chars
- ✅ Invalid commands show helpful errors
- ✅ Word count system prevents overly long responses

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

## Dependencies

**Python Version:** 3.8+

**Required Packages (requirements.txt):**
```
openai>=1.12.0
python-dotenv>=1.0.0
tavily-python>=0.3.0
```

**Standard Library (no install needed):**
- os, sys, textwrap, random, argparse, json

**API Keys Required (for development):**
- `OPENAI_API_KEY` (required)
- `TAVILY_API_KEY` (optional - fallback facts used if missing)

**API Keys for Distribution (v0.19.1):**
- Keys are hardcoded in eastWing.py (lines 23 and 485)
- No .env file needed for distributed executable
- See "Windows Executable Distribution" section above for details

---

## Version History

- **v0.01-v0.05** - Development versions (internal)
- **v0.19.1** - Initial public release (2025-10-29)
  - Turn command added
  - '?' help synonym added
  - Windows executable built and tested
  - **2025-10-30 Morning:** API keys embedded in source code (lines 23, 485)
  - **2025-10-30 Morning:** Distribution via Dropbox links to trusted friends
  - **Issue:** OpenAI detected keys in GitHub and disabled them
- **v0.19.2** - Security fix and error handling (2025-10-30 afternoon)
  - Graceful error handling for invalid/missing API keys
  - Deferred OpenAI client initialization (line 40)
  - User-friendly error message with "Press Enter to exit"
  - API keys stored as variables (lines 37, 523) instead of direct in OpenAI() call
  - Improved Tavily error messages (non-fatal)
  - Safe build workflow documented (placeholder keys in GitHub, real keys in .exe)
  - Ready for private distribution via Dropbox

---

*This specification reflects v0.19.2 of The East Wing, with API key security and error handling improvements completed on 2025-10-30.*

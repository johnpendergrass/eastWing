# To Be Continued

This file tracks ongoing work and tasks that need to be completed or revisited.

## Current Status - v0.03 (Latest)

### Recently Completed Features (This Session)

1. **Runtime Speed Switching** - COMPLETED
   - Renamed `--faster` flag to `--fast` for consistency
   - Added `fast` command to switch to fast progression during gameplay (requires debug mode)
   - Added `normal` command to switch to normal progression during gameplay (requires debug mode)
   - Speed changes automatically regenerate system prompt if stage changes
   - Messages show turn number and current mood: "Turn 5. Progression speed changed to 'fast'. Mood is: angry."

2. **Command Validation System** - COMPLETED
   - Catches malformed commands before they reach the AI
   - Validates command format for: debug, api, fast, normal, memory, summary, speed, mood
   - Examples:
     - `debug` alone → suggests "debug on" or "debug off"
     - `api xyz` → suggests "api" or "api all"
     - `fast something` → suggests just "fast"
   - All error messages in yellow (COLOR_ALERT) with helpful hints

3. **New Information Commands** - COMPLETED
   - `speed` - Shows current progression speed (normal or fast)
     - Displays: "The game's current progression speed: Normal"
     - Hints how to change it (debug mode or not)
   - `mood` - Shows current mood/personality of the wall
     - Displays: "The wall's current mood is: upset"
     - Available to all players, not just debug mode

4. **Enhanced Debug Error Messages** - COMPLETED
   - All debug commands show consistent error format when used without debug mode
   - Format: `'[command]' does not work unless you are in debug mode. [hint: to switch to debug mode, type 'debug on']`
   - Applies to: fast, normal, api, api all, memory, summary

5. **Personality Update** - COMPLETED
   - Changed stage_30 personality from 'medium' to 'upset' for better emotional clarity

### Previous Features (v0.02)

1. **Separated Debug and Speed Features**
   - `--debug` flag for debug commands (api, memory, summary)
   - `--fast` flag for fast stage progression (previously --faster)
   - Can be used independently or together

2. **Runtime Debug Toggle**
   - `debug on` / `debug off` commands during gameplay
   - Confirmation messages for state changes

3. **Enhanced Color System**
   - COLOR_SYSTEM (bright cyan) - for help/instructions
   - COLOR_PLAYER (default) - for player input
   - COLOR_AI (bright white) - for wall responses
   - COLOR_DEBUG (cyan) - for debug command output
   - COLOR_ALERT (yellow) - for warnings/alerts
   - All colors easily customizable at top of file

4. **Stage-Based Progression**
   - Renamed INTENSITY_RANGES → PROGRESSION_SPEEDS
   - 5 stages (stage_10 through stage_50) with spaced numbering
   - Reply length scales with emotional intensity
   - First reply always 2 sentences

5. **Enhanced API Debugging**
   - `api` command shows truncated request (500 chars)
   - `api all` command shows full untruncated request
   - Yellow alert hints when truncation occurs

6. **Help System Improvements**
   - Shows current state banner (speed + debug status)
   - Contextual command display based on debug state
   - Always available `help` command

## Future Enhancements

### Dynamic System Prompt Adjustments
- Could add intensity modifier based on player sentiment
- Could inject conditional personality tweaks based on player background
- Implementation deferred for now - easy to add later via `get_system_prompt()` parameters

### Potential Improvements
- Track player sentiment/emotional tone
- Adjust wall personality in response to player behavior
- Add more granular stage progression (e.g., stage_15, stage_25)
- Save/load conversation states
- Export conversation transcripts

### Color System Expansion
- Consider theme presets (dark mode, light mode, high contrast)
- User-configurable color schemes via config file

## Testing Needed

- Test runtime speed switching (fast/normal commands) during active gameplay
- Verify that speed switches correctly regenerate system prompts when stage changes
- Test command validation with various malformed inputs
- Test rolling summary system with long conversations (20+ turns)
- Verify summary quality and continuity across stage transitions
- Test fast progression mode (--fast) for rapid testing
- Test debug toggle during gameplay
- Verify 'api all' command with very long system prompts
- Test color display on different terminal types
- Test 'speed' and 'mood' commands at various stages
- Verify all error messages display correctly in COLOR_ALERT (yellow)

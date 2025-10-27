# To Be Continued

This file tracks ongoing work and tasks that need to be completed or revisited.

## Current Status

Implementation of rolling summary system with structured JSON outputs - COMPLETED

## Future Enhancements

### Dynamic System Prompt Adjustments
- Could add intensity modifier based on player sentiment
- Could inject conditional personality tweaks based on player background
- Implementation deferred for now - easy to add later via `get_system_prompt()` parameters

### Potential Improvements
- Track player sentiment/emotional tone
- Adjust wall personality in response to player behavior
- Add more nuanced intensity progression (0-100 scale vs 4 discrete levels)

## Testing Needed

- Test rolling summary system with long conversations (20+ turns)
- Verify summary quality and continuity
- Test "forgetful wall" deflection phrases in practice
- Debug mode testing of summary generation

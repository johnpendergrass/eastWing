# The East Wing

A conversational text adventure where you chat with the last remaining wall of the demolished White House East Wing.

## Setup

1. **Install Python 3.8+** (if not already installed)

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key:**
   - Copy `.env.example` to `.env`
   - Replace `your_api_key_here` with your actual OpenAI API key
   - **IMPORTANT:** Never commit your `.env` file to version control!

4. **Run the game:**
   ```bash
   python game.py
   ```

## How to Play

- Type your responses to converse with the wall
- The wall has personality - it's tired, snarky, and nostalgic
- Type `quit`, `exit`, `bye`, or `goodbye` to end the game
- Press Ctrl+C to exit at any time

## Game Mechanics

The game uses OpenAI's API to generate dynamic responses. Each conversation is unique based on:
- The wall's personality (defined in the system prompt)
- Full conversation history (the wall "remembers" everything you've discussed)
- Your creative responses

## Cost Considerations

This game uses the `gpt-4o-mini` model which is very affordable (~$0.15 per million input tokens). A typical conversation costs less than a penny.

## Future Ideas

- Save/load conversations
- Multiple characters to talk to
- Context summarization for very long conversations
- Different story scenarios
- Add ASCII art of the wall

## Troubleshooting

**"OPENAI_API_KEY not found"**: Make sure you created a `.env` file with your API key

**API errors**: Check that your API key is valid and you have credits in your OpenAI account

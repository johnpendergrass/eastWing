# The East Wing

A conversational text adventure game where you chat with the last remaining wall of the demolished White House East Wing.

## How to Run

1. **Download** `eastWing.exe` from the latest release
2. **Double-click** `eastWing.exe` to start playing!

That's it! No installation, no setup required.

---

## How to Play

- Type your responses naturally to chat with the Wall
- The Wall's personality evolves as you talk
- Type `help` anytime to see available commands
- Type `quit` or `exit` to end the conversation

---

## Antivirus Warning ⚠️

Your antivirus software might flag this `.exe` as suspicious. This is a **false positive** - common with Python executables.

**Why this happens:**
- The .exe unpacks Python code at runtime (looks like unusual behavior to antivirus)
- It's an unsigned executable

**This software is safe:**
- Source code available at: https://github.com/johnpendergrass/eastWing
- You can review the Python code yourself
- Built with PyInstaller (standard Python packaging tool)

**To use it:**
- Add an exception in your antivirus if it blocks the file
- Or run from a trusted folder location

---

## Commands

Type these anytime during conversation:

- `help` - Show all commands and current game state
- `model ?` - Switch AI models (quality vs speed)
- `speed ?` - Change game speed (slow/fast progression)
- `mood ?` - Manually set the Wall's mood
- `color ?` - Change color theme
- `quit` - Exit game

---

## System Requirements

- **Windows 10 or later**
- **Internet connection** (for AI responses)
- No Python installation required!

---

## Troubleshooting

### Game window closes immediately
Run from PowerShell to see any error messages:
```powershell
cd path\to\folder
.\eastWing.exe
```

### Slow responses
AI responses take 5-15 seconds (this is normal!). The Wall is thinking...

---

## Support & Source Code

- **Issues/Questions**: https://github.com/johnpendergrass/eastWing/issues
- **Source Code**: https://github.com/johnpendergrass/eastWing

---

**Have fun chatting with the Wall!**

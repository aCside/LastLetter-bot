# TitanBot v6.6

TitanBot is an advanced, fully configurable automation tool made for Roblox game "Last Letter"

Unlike basic solvers, TitanBot focuses on humanization and strategy, allowing it to mimic natural typing patterns, make intentional mistakes, and prioritize words that are difficult for opponents to counter.

# Key Features:

## Intelligent Word Generation:

Hybrid Database: Uses a local database combined with the Datamuse API to find words instantly.

Smart Filtering: Automatically rejects proper nouns (names, cities), nonsense words, and words without vowels.

Session Memory: Remembers used words to prevent repetitions within a single session.

## Strategy Modes:

Killer: Prioritizes words ending in difficult letters (X, Z, J, Q) to trap opponents.

Longest: Prioritizes long words for maximum points.

Smart: Balanced approach based on length and complexity.

Custom: Define your own 3-stage priority waterfall (e.g., Try Killer -> Then Longest -> Then Random).

## Human-Like Behavior:

TitanBot doesn't just paste text; it simulates a real keyboard.

Variable Latency: Randomizes the delay between every single keystroke (e.g., 50ms-150ms).

Thinking Time: Adds realistic pauses before typing long words or after rerolling letters.

Simulated Typos: Configurable chance to make "human errors" and automatically backspace to correct them.

Key Hold Simulation: Randomizes how long a key is physically "held" down (15ms-40ms) to bypass basic anti-cheat detection.

## In-Game Overlay & Controls:

Smart Input (F2): The bot "listens" to you typing the syllable, catches it, finds a word, and types it for you automatically.

Reroll (F4): Don't like the word? Press F4 to scrub the input and find the next best option with a "thinking" delay.

Ban/Unban: Encountered a bad word? Ban it instantly via hotkey or the UI.

Profiles: Save and load different config presets for different game modes.

Themes: Switch between Dark and Light modes.

## Configuration:

You have full control over the bot's speed and logic:

Latency: Min/Max speed between keystrokes.

Start Delay: How long to wait before starting to type.

Length Delay: Adds extra wait time per character (simulates reading/thinking).

Reroll Strategy: Define a separate strategy specifically for when you panic-reroll.

## Installation:

TitanBot is a self-contained script.

Ensure you have Python installed.

Run the script.

The bot includes a Self-Installer: it will automatically detect missing libraries (pydirectinput, keyboard, requests, pygetwindow) and install them on the first launch.

# Disclaimer & Bugs:

Beta Status: This software is currently in version v6.6. While robust, it may contain bugs or edge cases where word filtering isn't 100% perfect (e.g., some obscure proper nouns might slip through).

Use at your own risk: Automation tools may violate the Terms of Service of certain games. The creator is not responsible for bans or restrictions placed on your accounts.

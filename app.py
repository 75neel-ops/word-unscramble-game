"""
Word Scramble Game
------------------
- Difficulty: easy / hard / tough
- Word length: 3, 4, 5 or 6 letters
- Words come from the online Datamuse word list and are verified
  against the Free Dictionary API (dictionaryapi.dev).
- Hints: dictionary definition (easy/hard); a Gemini-written clue (tough).

Setup:
    pip install requests
    set GEMINI_API_KEY=your_key        (Windows)
    export GEMINI_API_KEY=your_key     (Mac/Linux)

Run:
    python word_scramble.py
"""

import os
import random
import re

import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"  # change if your key supports a different model

# Difficulty rules
DIFFICULTY = {
    "easy": {
        "tries": 3,
        "keep_first_letter": True,
        "desc": "First letter stays in place, 3 tries, hint = dictionary meaning",
    },
    "hard": {
        "tries": 2,
        "keep_first_letter": False,
        "desc": "Fully scrambled, 2 tries, hint = dictionary meaning",
    },
    "tough": {
        "tries": 1,
        "keep_first_letter": False,
        "desc": "Fully scrambled, only 1 try, hint = a tricky clue from Gemini",
    },
}

HEADERS = {"User-Agent": "word-scramble-game/1.0"}


# ---------------------------------------------------------------- online data
def fetch_candidate_words(length):
    """Get common words of the given length from the Datamuse API."""
    url = "https://api.datamuse.com/words"
    params = {"sp": "?" * length, "max": 1000, "md": "f"}
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
    except requests.RequestException:
        return []

    words = []
    for item in r.json():
        word = item.get("word", "")
        if not (word.isalpha() and word.islower() and len(word) == length):
            continue
        # keep reasonably common words only
        freq = 0.0
        for tag in item.get("tags", []):
            if tag.startswith("f:"):
                freq = float(tag[2:])
        if freq >= 2.0:
            words.append(word)
    return words


def fetch_definition(word):
    """Return (part_of_speech, definition) from the dictionary API, or None."""
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None
        meanings = r.json()[0]["meanings"]
        pos = meanings[0]["partOfSpeech"]
        definition = meanings[0]["definitions"][0]["definition"]
        return pos, definition
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return None


def pick_word(length, used):
    """Pick a random verified dictionary word we haven't used yet."""
    candidates = [w for w in fetch_candidate_words(length) if w not in used]
    random.shuffle(candidates)
    for word in candidates[:25]:  # try a limited number of lookups
        info = fetch_definition(word)
        if info:
            return word, info
    return None, None


def gemini_clue(word, pos, definition):
    """Ask Gemini for a tricky (but fair) clue that does not reveal the word."""
    if not GEMINI_API_KEY:
        return None
    prompt = (
        f"Write ONE short, clever clue (max 20 words) for the word '{word}' "
        f"({pos}; meaning: {definition}). Never include the word itself or "
        f"any part of it. Return only the clue."
    )
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )
    try:
        r = requests.post(
            url,
            headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=15,
        )
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        return mask_word(text, word)
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return None


# ---------------------------------------------------------------- game logic
def mask_word(text, word):
    """Hide the answer if it appears inside a hint."""
    return re.sub(re.escape(word), "_" * len(word), text, flags=re.IGNORECASE)


def scramble(word, keep_first):
    letters = list(word)
    for _ in range(50):
        if keep_first:
            rest = letters[1:]
            random.shuffle(rest)
            result = [letters[0]] + rest
        else:
            result = letters[:]
            random.shuffle(result)
        if "".join(result) != word:
            return "".join(result)
    return "".join(result)  # very rare (e.g. words like "ooo")


def ask_choice(prompt, options):
    while True:
        choice = input(prompt).strip().lower()
        if choice in options:
            return choice
        print(f"  Please choose one of: {', '.join(options)}")


def get_hint(word, level, pos, definition):
    if level == "tough":
        clue = gemini_clue(word, pos, definition)
        if clue:
            return clue
    return f"({pos}) {mask_word(definition, word)}"


def play_round(length, level, used):
    print("\nFetching a word from the online dictionary...")
    word, info = pick_word(length, used)
    if not word:
        print("Could not get a word (check your internet connection).")
        return False
    used.add(word)
    pos, definition = info

    rules = DIFFICULTY[level]
    jumbled = scramble(word, rules["keep_first_letter"])
    tries_left = rules["tries"]
    hint_used = False

    print(f"\nUnscramble this word:  {jumbled.upper()}   ({length} letters)")
    print(f"Tries: {tries_left}   |   Type 'hint' for a hint\n")

    while tries_left > 0:
        guess = input("Your answer: ").strip().lower()

        if guess == "hint":
            if hint_used and level == "tough":
                print("  Hint already used. Hint: " + get_hint(word, level, pos, definition))
            else:
                print("  Hint: " + get_hint(word, level, pos, definition))
                hint_used = True
            continue

        if not guess:
            continue

        if guess == word:
            print(f"\n🎉 Congratulations! '{word.upper()}' is correct!")
            return True

        tries_left -= 1
        if tries_left > 0:
            print(f"  ❌ Wrong answer. {tries_left} {'try' if tries_left == 1 else 'tries'} left.")

    print(f"\n❌ Your answer is wrong. The right answer is: {word.upper()}")
    print(f"   Meaning: ({pos}) {definition}")
    return False


def main():
    print("=" * 44)
    print("          WORD SCRAMBLE GAME")
    print("=" * 44)
    if not GEMINI_API_KEY:
        print("(Tip: set GEMINI_API_KEY to get Gemini clues in 'tough' mode)")

    print("\nDifficulty levels:")
    for name, rules in DIFFICULTY.items():
        print(f"  {name:<6} - {rules['desc']}")
    level = ask_choice("\nChoose difficulty (easy/hard/tough): ", list(DIFFICULTY))
    length = int(ask_choice("Choose word length (3/4/5/6): ", ["3", "4", "5", "6"]))

    used, score, rounds = set(), 0, 0
    while True:
        result = play_round(length, level, used)
        if result is not False or used:
            rounds += 1
            score += 1 if result else 0
        print(f"\nScore: {score}/{rounds}")

        again = ask_choice("\nDo you want to play the next word? (y/n): ", ["y", "n", "yes", "no"])
        if again.startswith("n"):
            print(f"\nThanks for playing! Final score: {score}/{rounds}")
            break

        change = ask_choice("Change difficulty or length? (y/n): ", ["y", "n", "yes", "no"])
        if change.startswith("y"):
            level = ask_choice("Choose difficulty (easy/hard/tough): ", list(DIFFICULTY))
            length = int(ask_choice("Choose word length (3/4/5/6): ", ["3", "4", "5", "6"]))
            used.clear()


if __name__ == "__main__":
    main()

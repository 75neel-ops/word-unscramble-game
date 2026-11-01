"""
Word Scramble Game - Streamlit version
--------------------------------------
- Difficulty: easy / hard / tough
- Word length: 3, 4, 5 or 6 letters
- Words come from the online Datamuse word list and are verified against the
  Free Dictionary API (dictionaryapi.dev); Datamuse definitions are the backup.
- Hints: dictionary meaning (easy/hard); Gemini-written clue (tough).

Gemini key: in Streamlit Cloud open  App -> Settings -> Secrets  and add
    GEMINI_API_KEY = "your_key_here"
"""

import os
import random
import re

import requests
import streamlit as st

st.set_page_config(page_title="Word Scramble", page_icon="🔤")

GEMINI_MODEL = "gemini-2.0-flash"  # change if your key supports a different model
HEADERS = {"User-Agent": "word-scramble-game/1.0"}
POS_NAMES = {"n": "noun", "v": "verb", "adj": "adjective", "adv": "adverb", "u": "word"}

DIFFICULTY = {
    "easy": {"tries": 3, "keep_first": True,
             "desc": "First letter stays in place, 3 tries, hint = dictionary meaning"},
    "hard": {"tries": 2, "keep_first": False,
             "desc": "Fully scrambled, 2 tries, hint = dictionary meaning"},
    "tough": {"tries": 1, "keep_first": False,
              "desc": "Fully scrambled, only 1 try, hint = tricky clue from Gemini"},
}


# ---------------------------------------------------------------- online data
def get_gemini_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.getenv("GEMINI_API_KEY", "")


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_candidate_words(length):
    """Common words of a given length from Datamuse (errors are raised, so they are not cached)."""
    r = requests.get(
        "https://api.datamuse.com/words",
        params={"sp": "?" * length, "max": 1000, "md": "fd"},
        headers=HEADERS,
        timeout=10,
    )
    r.raise_for_status()
    words = []
    for item in r.json():
        word = item.get("word", "")
        if not (word.isalpha() and word.islower() and len(word) == length):
            continue
        freq = 0.0
        for tag in item.get("tags", []):
            if tag.startswith("f:"):
                try:
                    freq = float(tag[2:])
                except ValueError:
                    pass
        if freq < 2.0:
            continue
        fallback = None
        defs = item.get("defs") or []
        if defs:
            code, _, text = defs[0].partition("\t")
            if text:
                fallback = (POS_NAMES.get(code, "word"), text)
        words.append((word, fallback))
    return words


def fetch_definition(word):
    try:
        r = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}",
            headers=HEADERS, timeout=8,
        )
        if r.status_code != 200:
            return None
        meaning = r.json()[0]["meanings"][0]
        return meaning["partOfSpeech"], meaning["definitions"][0]["definition"]
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return None


def pick_word(length, used):
    candidates = [c for c in fetch_candidate_words(length) if c[0] not in used]
    random.shuffle(candidates)
    dict_failures = 0
    for word, fallback in candidates[:25]:
        info = None
        if dict_failures < 3:
            info = fetch_definition(word)
            if info is None:
                dict_failures += 1
        info = info or fallback
        if info:
            return word, info
    return None, None


def gemini_clue(word, pos, definition):
    key = get_gemini_key()
    if not key:
        return None
    prompt = (
        f"Write ONE short, clever clue (max 20 words) for the word '{word}' "
        f"({pos}; meaning: {definition}). Never include the word itself or any "
        f"part of it. Return only the clue."
    )
    try:
        r = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{GEMINI_MODEL}:generateContent",
            headers={"x-goog-api-key": key, "Content-Type": "application/json"},
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
            break
    return "".join(result)


def init_state():
    ss = st.session_state
    ss.setdefault("game", None)
    ss.setdefault("used", set())
    ss.setdefault("score", 0)
    ss.setdefault("rounds", 0)
    ss.setdefault("error", "")


def start_round():
    ss = st.session_state
    level, length = ss.level, int(ss.length)
    ss.error = ""
    try:
        word, info = pick_word(length, ss.used)
    except (requests.RequestException, ValueError) as e:
        ss.game = None
        ss.error = f"Could not reach the word list ({type(e).__name__}). Please try again."
        return
    if not word:
        ss.game = None
        ss.error = "Could not find a word. Please try again."
        return
    ss.used.add(word)
    pos, definition = info
    rules = DIFFICULTY[level]
    ss.game = {
        "word": word, "pos": pos, "definition": definition, "level": level,
        "jumbled": scramble(word, rules["keep_first"]),
        "tries_left": rules["tries"], "hint": None, "feedback": "", "status": "playing",
    }


def show_hint():
    g = st.session_state.game
    if g and g["hint"] is None:
        clue = gemini_clue(g["word"], g["pos"], g["definition"]) if g["level"] == "tough" else None
        g["hint"] = clue or f"({g['pos']}) {mask_word(g['definition'], g['word'])}"


def submit_guess():
    ss = st.session_state
    g = ss.game
    guess = (ss.get("guess_box") or "").strip().lower()
    if not g or g["status"] != "playing" or not guess:
        return
    if guess == g["word"]:
        g["status"] = "won"
        ss.score += 1
        ss.rounds += 1
        return
    g["tries_left"] -= 1
    if g["tries_left"] <= 0:
        g["status"] = "lost"
        ss.rounds += 1
    else:
        n = g["tries_left"]
        g["feedback"] = f"Wrong answer. {n} {'try' if n == 1 else 'tries'} left."


# ---------------------------------------------------------------- the page
init_state()

st.title("🔤 Word Scramble")
st.caption("Unscramble the letters to find the word.")

c1, c2 = st.columns(2)
c1.selectbox("Difficulty", list(DIFFICULTY), key="level")
c2.selectbox("Word length", ["3", "4", "5", "6"], index=1, key="length")
st.caption(DIFFICULTY[st.session_state.level]["desc"])
if not get_gemini_key():
    st.caption("Tip: add GEMINI_API_KEY in the app's Secrets to get Gemini clues in tough mode.")

g = st.session_state.game

if st.session_state.error:
    st.error(st.session_state.error)

if g is None:
    st.button("Start game", on_click=start_round, type="primary")
else:
    st.markdown(f"### `{g['jumbled'].upper()}`")
    st.write(f"{len(g['word'])} letters · {g['level']} mode")

    if g["status"] == "playing":
        st.write(f"Tries left: **{g['tries_left']}**")
        with st.form("guess_form", clear_on_submit=True):
            st.text_input("Your answer", key="guess_box")
            st.form_submit_button("Submit", on_click=submit_guess, type="primary")
        st.button("💡 Hint", on_click=show_hint)
        if g["hint"]:
            st.info(f"Hint: {g['hint']}")
        if g["feedback"]:
            st.warning(g["feedback"])
    else:
        if g["status"] == "won":
            st.balloons()
            st.success(f"🎉 Congratulations! **{g['word'].upper()}** is correct!")
        else:
            st.error(f"❌ Your answer is wrong. The right answer is **{g['word'].upper()}**.")
        st.write(f"Meaning: ({g['pos']}) {g['definition']}")
        st.button("Next word ➜", on_click=start_round, type="primary")

st.divider()
st.write(f"Score: **{st.session_state.score} / {st.session_state.rounds}**")

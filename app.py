import random
import streamlit as st

st.title("🎯 5-Letter Word Unscramble Game")

# A sample list of 5-letter words
FIVE_LETTER_WORDS = [
    "Apple",
    "Beach",
    "Chair",
    "Dance",
    "Eagle",
    "Flame",
    "Grape",
    "Heart",
    "Juice",
    "Knock",
    "Lemon",
    "Mouse",
    "Night",
    "Ocean",
    "Piano",
    "Queen",
    "River",
    "Smile",
    "Train",
    "Voice",
    "Water",
    "Yacht",
    "Zebra",
]

# Initialize session state for the secret word
if "secret_word" not in st.session_state:
  st.session_state.secret_word = random.choice(FIVE_LETTER_WORDS)
  scrambled = list(st.session_state.secret_word)
  random.shuffle(scrambled)
  while "".join(scrambled).lower() == st.session_state.secret_word.lower():
    random.shuffle(scrambled)
  st.session_state.scrambled_word = "".join(scrambled)

st.write(
    f"### Unscramble this 5-letter word:"
    f" **{st.session_state.scrambled_word.upper()}**"
)

# Streamlit text input instead of python input()
guess = st.text_input("Your 5-letter guess:", key="user_guess").strip()

if st.button("Check Answer"):
  if len(guess) != 5:
    st.warning("⚠️ Please enter a valid 5-letter word!")
  elif guess.lower() == st.session_state.secret_word.lower():
    st.success("🎉 Perfect! You got it right away!")
  else:
    st.error("Not quite! Here is your breakdown:")
    for i in range(5):
      if i < len(guess):
        if guess[i].lower() == st.session_state.secret_word[i].lower():
          st.write(f"Position {i+1}: '{guess[i]}' is **CORRECT** ✔️")
        else:
          st.write(f"Position {i+1}: **Wrong** (You typed '{guess[i]}') ❌")
      else:
        st.write(f"Position {i+1}: **Missing** ❓")

    st.info(f"The hidden word was: {st.session_state.secret_word}")

if st.button("Play Again / New Word"):
  for key in list(st.session_state.keys()):
    del st.session_state[key]
  st.rerun()

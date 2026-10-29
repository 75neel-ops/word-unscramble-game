import streamlit as st
import random

st.title("🎯 Word Unscramble Game")

# We use session state to keep the secret word from changing on every click
if 'secret_word' not in st.session_state:
    st.session_state.secret_word = random.choice(["Football", "Cricket", "Chess", "Hockey", "Tennis"])
    scrambled = list(st.session_state.secret_word)
    random.shuffle(scrambled)
    st.session_state.scrambled_word = "".join(scrambled)

st.write(f"### Unscramble this word: **{st.session_state.scrambled_word}**")

guess = st.text_input("Your guess:").strip()

if st.button("Check Answer"):
    if guess.lower() == st.session_state.secret_word.lower():
        st.success("Perfect! You got it right away! 🌟")
    else:
        st.error("Not quite! Here is your breakdown:")
        for i in range(len(st.session_state.secret_word)):
            if i < len(guess):
                if guess[i].lower() == st.session_state.secret_word[i].lower():
                    st.write(f"Position {i+1}: '{guess[i]}' is **CORRECT** ✔️")
                else:
                    st.write(f"Position {i+1}: **Wrong** (You typed '{guess[i]}') ❌")
            else:
                st.write(f"Position {i+1}: **Missing** ❓")
                
        st.info(f"The hidden word was: {st.session_state.secret_word}")
        
if st.button("Play Again / New Word"):
    del st.session_state.secret_word
    st.rerun()

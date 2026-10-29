import random

print("🎯 5-Letter Word Unscramble Game")
print("-" * 35)

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

# Select a random secret word
secret_word = random.choice(FIVE_LETTER_WORDS)
scrambled = list(secret_word)
random.shuffle(scrambled)

# Ensure the scrambled word isn't identical to the original
while "".join(scrambled).lower() == secret_word.lower():
  random.shuffle(scrambled)

scrambled_word = "".join(scrambled)

print(f"\nUnscramble this 5-letter word: {scrambled_word.upper()}")

# Loop for guessing
while True:
  guess = input("\nYour 5-letter guess (or type 'quit' to exit): ").strip()

  if guess.lower() == "quit":
    print(f"The hidden word was: {secret_word}")
    break

  if len(guess) != 5:
    print("⚠️ Please enter a valid 5-letter word!")
    continue

  if guess.lower() == secret_word.lower():
    print("🎉 Perfect! You got it right away!")
    break
  else:
    print("Not quite! Here is your breakdown:")
    for i in range(5):
      if i < len(guess):
        if guess[i].lower() == secret_word[i].lower():
          print(f"Position {i+1}: '{guess[i]}' is CORRECT ✔️")
        else:
          print(f"Position {i+1}: Wrong (You typed '{guess[i]}') ❌")
      else:
        print(f"Position {i+1}: Missing ❓")

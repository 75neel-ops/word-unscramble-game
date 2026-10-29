import random

# Ensure all words in the pool are compared safely
secret_word = random.choice(["Football", "Cricket", "Chess", "Hockey", "Tennis"])
scrambled = list(secret_word)
random.shuffle(scrambled)
scrambled_word = "".join(scrambled)

print(f"Unscramble this word: {scrambled_word}")
guess = input("Your guess: ").strip() # Removed .lower() from here so we can see what you typed

# FIX: Convert both strings to lowercase (.lower()) only when doing comparisons!
if guess.lower() == secret_word.lower():
    print("Perfect! You got it right away! 🌟")
else:
    print("\nNot quite! Let's see which letters you got in the right spot:")
    
    for i in range(len(secret_word)):
        if i < len(guess):
            # FIX: Compare lowercase versions here too
            if guess[i].lower() == secret_word[i].lower():
                print(f"Position {i+1} ('{secret_word[i]}'): CORRECT ✔️")
            else:
                print(f"Position {i+1} ('{secret_word[i]}'): Wrong (You typed '{guess[i]}') ❌")
        else:
            print(f"Position {i+1} ('{secret_word[i]}'): Missing ❓")
            
    print(f"\nThe hidden word was: {secret_word}")

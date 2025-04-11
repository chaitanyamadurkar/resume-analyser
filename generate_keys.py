import pickle
from pathlib import Path

import streamlit_authenticator as stauth

names = ["Group CA8 ", "Chaitanya madurkar"]
usernames = ["ca8", "chaitanya"]
passwords = ["c1234", "c3434"]

hashed_passwords = stauth.Hasher(passwords).generate()

file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("wb") as file:
    pickle.dump(hashed_passwords, file)
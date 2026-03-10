"""
Run this to add a new user:
  python3 add_user.py
"""
import bcrypt
import yaml
import os

AUTH_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auth_config.yaml")

with open(AUTH_FILE) as f:
    config = yaml.safe_load(f)

username = input("Username (no spaces): ").strip().lower()
name     = input("Display name: ").strip()
email    = input("Email: ").strip()
password = input("Password: ").strip()

hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

config["credentials"]["usernames"][username] = {
    "name": name,
    "email": email,
    "password": hashed,
    "failed_login_attempts": 0,
    "logged_in": False,
}

with open(AUTH_FILE, "w") as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

print(f"\nUser '{username}' added successfully.")

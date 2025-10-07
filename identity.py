import os
import json
import random
import string

TOKEN_FILE = 'token.json'

# -----------------------------
# File Handling
# -----------------------------
def init_token_file():
    """Ensure token.json exists."""
    if not os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'w') as f:
            json.dump({}, f, indent=4)

def load_tokens():
    """Load token data from disk."""
    init_token_file()
    with open(TOKEN_FILE, 'r') as f:
        return json.load(f)

def save_tokens(tokens):
    """Save token data to disk."""
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f, indent=4)

# -----------------------------
# Token / Tag Generators
# -----------------------------
def generate_token(length=12):
    """Generate a unique permanent token (identity key)."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def generate_tag():
    """Generate a 4-digit discriminator tag."""
    return f"{random.randint(0, 9999):04d}"

# -----------------------------
# Handshake System
# -----------------------------
def handshake(username=None, tag=None, provided_token=None, client_ip=None):
    """
    Handle user authentication/creation.
    - No token → create new identity.
    - With token → authenticate and update username/tag if changed.
    """
    tokens = load_tokens()

    # New user: no token provided
    if provided_token is None:
        new_token = generate_token()
        new_tag = tag if tag else generate_tag()

        tokens[new_token] = {
            "username": username if username else "Unnamed",
            "tag": new_tag,
            "last_seen_ip": client_ip
        }
        save_tokens(tokens)

        print(f"New identity created: {username}#{new_tag} with token {new_token}")
        return new_token, "new_identity"

    # Existing user: token provided
    if provided_token in tokens:
        user = tokens[provided_token]
        changed = False

        if username and username != user["username"]:
            user["username"] = username
            changed = True
        if tag and tag != user["tag"]:
            user["tag"] = tag
            changed = True
        if client_ip and client_ip != user.get("last_seen_ip"):
            user["last_seen_ip"] = client_ip
            changed = True

        if changed:
            save_tokens(tokens)
            print(f"Updated identity for {provided_token}: {user['username']}#{user['tag']}")

        print(f"✅ Authenticated as {user['username']}#{user['tag']}")
        return provided_token, "authenticated"

    # Invalid token
    print(f"Invalid token: {provided_token}")
    return None, "invalid_token"

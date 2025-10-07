import os
import json
import identity

print("=== TEST 1: Create New Identity ===")
token, status = identity.handshake("Alice", "0420")
assert status == "new_identity"
assert token is not None
print(f"Token assigned: {token}\n")

print("=== TEST 2: Authenticate Existing Identity ===")
token2, status2 = identity.handshake("Alice", "0420", provided_token=token)
assert status2 == "authenticated"
assert token2 == token
print(f"Authenticated as: {token2}\n")

print("=== TEST 3: Change Username/Tag ===")
token3, status3 = identity.handshake("CoolAlice", "7777", provided_token=token)
assert status3 == "authenticated"
with open('token.json', 'r') as f:
    data = json.load(f)
    assert data[token3]['username'] == "CoolAlice"
    assert data[token3]['tag'] == "7777"
print(f"Username/Tag updated for {token3}\n")

print("=== TEST 4: Invalid Token ===")
invalid_token = "FAKETOKEN123"
token4, status4 = identity.handshake("Bob", "0001", provided_token=invalid_token)
assert status4 == "invalid_token"
assert token4 is None
print("Invalid token correctly rejected\n")

print("=== TEST 5: New User Different Token ===")
token5, status5 = identity.handshake("Bob", "0001")
assert status5 == "new_identity"
assert token5 != token
print(f"New token assigned to Bob: {token5}\n")


from auth.jwt_handler import (
    create_access_token,
    verify_access_token
)

token = create_access_token(
    {
        "sub": "prajwal@gmail.com",
        "role": "ADMIN"
    }
)

print("JWT Token:")
print(token)

print()

decoded = verify_access_token(token)

print("Decoded Payload:")
print(decoded)
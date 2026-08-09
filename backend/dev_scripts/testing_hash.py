from auth.hashing import hash_password, verify_password

password = "Prajwal@123"

hashed = hash_password(password)

print("Hashed Password:")
print(hashed)

print("\nVerification Result:")
print(verify_password(password, hashed))
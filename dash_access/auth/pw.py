# Passwords need to be hashed with a salt and a "slow" hashing algorithm. 
# SHA1, SHA256 etc. are not secure to GPU smashing and modern power;
# rather, they are meant to be fast and secure to the computers of 
# 20 years ago. `bcrypt` uses an intentionally slow hash
# so it is more secure.


import bcrypt

def generate_password_hash(pw: str):
    """shortcut to using bcrypt to hash a password"""
    salt = bcrypt.gensalt()
    pw = bytes(pw,'utf8')
    out = bcrypt.hashpw(pw, salt)
    return out.decode('utf8')

def check_password_hash(hashed, pw):
    """shortcut to using bcrypt to check password"""
    pwbytes = bytes(pw,'utf8')
    hashedbytes = bytes(hashed, 'utf8')
    return bcrypt.checkpw(pwbytes, hashedbytes)
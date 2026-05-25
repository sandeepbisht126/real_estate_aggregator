import hashlib

def generate_hash(title, price, living_space):

    text = f"{title}-{price}-{living_space}"

    return hashlib.md5(text.encode()).hexdigest()
# private key
# public key
# address = pub key


# thw marikas

from Crypto.PublicKey import RSA


class Wallet:

    def __init__(self):
        bits = 2048
        new_key = RSA.generate(bits, e=65537)
        self.private_key = new_key
        self.public_key = new_key.publickey()
        self.address = self.public_key

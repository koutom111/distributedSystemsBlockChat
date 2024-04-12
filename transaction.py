# Κάθε transaction περιέχει πληροφορίες για την αποστολή νομισμάτων/μηνύματος από ένα wallet
# σε ένα άλλο. Οι πληροφορίες που περιλαμβάνει είναι
# sender_address: To public key του wallet από το οποίο προέρχεται το μήνυμα
# receiver_address: To public key του wallet παραλήπτη του μηνύματος
# type_of_transaction: Καθορίζει τον τύπο του transaction (coins or message)
# amount: το ποσο νομισμάτων προς αποστολή
# message: το String του μηνύματος που στέλνεται
# nonce: counter που διατηρείται ανά αποστολέα και αυξάνεται κατά 1 μετά από κάθε αποστολή
# transaction_id: το hash του transaction
# Signature: Υπογραφή που αποδεικνύει ότι ο κάτοχος του wallet δημιούργησε αυτό το transaction.


import time
import Crypto
import Crypto.Random
from Crypto.Hash import SHA, SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


def makeRSAjsonSendable(rsa):  # ????
    return rsa.exportKey("PEM").decode('ascii')


def makejsonSendableRSA(jsonSendable):  # ????
    return RSA.importKey(jsonSendable.encode('ascii'))


class Transaction:

    def __init__(self, sender_address, sender_private_key, recipient_address, transaction_type, nonce, amount=None,
                 message=None,
                 reals=None, realr=None):
        # prepei sender_address kai sender_private_key na einai RSA
        if not type(sender_address) == type(0) and not isinstance(sender_private_key, RSA.RsaKey):
            sender_private_key = makejsonSendableRSA(sender_private_key)
        if not type(sender_address) == type(0) and not isinstance(sender_address, RSA.RsaKey):
            sender_address = makejsonSendableRSA(sender_address)
        self.sender_address = sender_address
        self.receiver_address = recipient_address
        self.transaction_type = transaction_type
        self.amount = amount
        self.message = message
        self.nonce = nonce

        self.signature = None  # na paroume periptwsh gia bootstrap node poy tote 8a exoyme validator=0
        if (not type(self.sender_address) == type(0)):
            self.signature = self.sign_transaction(sender_private_key)
        self.transaction_id_hex = self.calculate_transaction_id().hexdigest()

        # helpers?????
        # self.rand = Crypto.Random.get_random_bytes(10)
        # self.transaction_myid = str(sender_address) + str(recipient_address) + str(amount) + str(self.rand)
        self.reals = reals
        self.realr = realr
        # self.transaction_id_hex = self.transaction_id.hexdigest()
        self.timeCreated = time.time()
        self.timeAdded = None

    def calculate_transaction_id(self):
        transaction_content = (f"{self.sender_address}{self.receiver_address}{self.amount}{self.message}"
                               f"{self.transaction_type}{self.nonce}")
        return SHA256.new(transaction_content.encode('utf-8'))

        # self.transaction_id = SHA.new(
        #     (str(sender_address) + str(recipient_address) + str(value) + str(self.rand)).encode())
        # self.signature = None
        # if not type(self.sender_address) == type(0):
        #     self.signature = self.sign_transaction(sender_private_key)  # ?????

    def sign_transaction(self, private_key):
        """
        Sign transaction with private key
        """
        signature = PKCS1_v1_5.new(private_key).sign(self.calculate_transaction_id())
        return signature

    # helpers???????
    def verify_signature(self):
        """
        Verify signature of sender (private, public keys)
        """
        try:
            PKCS1_v1_5.new(self.sender_address).verify(self.calculate_transaction_id(), self.signature)
            return True
        except (ValueError, TypeError):
            return False

    def calculate_charge(self):
        if type(self.receiver_address) == type(0):  # stake
            return float(self.amount)
        if self.transaction_type == 'message':
            return float(len(self.message))
        elif self.transaction_type == 'coins':
            amount = float(self.amount)
            charge = float(0.03 * amount)
            total = amount + charge
            return total

        else:
            print('Invalid type of transaction.')
            return 0

    def printMe(self):
        sender = self.sender_address
        receiver = self.receiver_address
        if (not self.reals == None):
            sender = self.reals
        if (not self.realr == None):
            receiver = self.realr

        message = self.message

        if self.message is None:
            message = self.amount

        print("\t \t I AM transaction ({}) of TYPE {}and I SEND {} $ from node {} to node {}".format(
            self.transaction_id_hex,
            self.transaction_type,
            message, sender, receiver))

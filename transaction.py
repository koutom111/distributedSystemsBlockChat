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

    def __init__(self, sender_address, sender_private_key, recipient_address, transaction_type, amount, nonce, message,
                 reals=None, realr=None):

        self.sender_address = sender_address
        self.receiver_address = recipient_address
        self.transaction_type = transaction_type
        self.amount = amount
        self.message = message
        self.nonce = nonce

        self.signature = None  # na paroume periptwsh gia bootstrap node poy tote 8a exoyme validator=0
        self.transaction_id_hex = self.calculate_transaction_id()

        # helpers?????
        self.rand = Crypto.Random.get_random_bytes(10)
        self.transaction_myid = str(sender_address) + str(recipient_address) + str(amount) + str(self.rand)
        self.reals = reals
        self.realr = realr
        self.transaction_inputs = []
        self.transaction_outputs = []
        # self.transaction_id_hex = self.transaction_id.hexdigest()
        self.timeCreated = time.time()
        self.timeAdded = None

    # def to_dict(self):
    #     return {
    #         'sender_address': makeRSAjsonSendable(self.sender_address) if self.sender_address else None,
    #         'receiver_address': makeRSAjsonSendable(self.receiver_address) if self.receiver_address else None,
    #         'transaction_type': self.transaction_type,
    #         'amount': self.amount,
    #         'message': self.message,
    #         'nonce': self.nonce,
    #         'transaction_id_hex': self.transaction_id_hex,
    #         'signature':  None,  # Assuming signature is bytes
    #         'timeCreated': self.timeCreated,
    #         'timeAdded': self.timeAdded,
    #         # Include other fields as needed
    #     }

    # @classmethod
    # def from_dict(cls, data):    #kai ayto mallon lathos
    #     # Create an instance without calling the original constructor
    #     transaction = cls.__new__(cls)
    #
    #     # Directly set attributes from the dictionary
    #     transaction.sender_address = makejsonSendableRSA(data['sender_address']) if data['sender_address'] else None
    #     transaction.receiver_address = makejsonSendableRSA(data['receiver_address']) if data[
    #         'receiver_address'] else None
    #     transaction.transaction_type = data['transaction_type']
    #     transaction.amount = data['amount']
    #     transaction.message = data['message']
    #     transaction.nonce = data['nonce']
    #     transaction.transaction_id_hex = data['transaction_id_hex']
    #     transaction.signature = bytes.fromhex(data['signature']) if data['signature'] else None
    #     transaction.timeCreated = data.get('timeCreated')
    #     transaction.timeAdded = data.get('timeAdded')
    #
    #     # Reinitialize any missing complex attributes or perform any necessary post-processing
    #     # For example, if you have lists of inputs or outputs, initialize them here
    #
    #     return transaction

    def calculate_transaction_id(self):
        transaction_content = (f"{self.sender_address}{self.receiver_address}{self.amount}{self.message}"
                               f"{self.transaction_type}{self.nonce}")
        return SHA256.new(transaction_content.encode('utf-8')).hexdigest()  # hexdigest?????

        # self.transaction_id = SHA.new(
        #     (str(sender_address) + str(recipient_address) + str(value) + str(self.rand)).encode())
        # self.signature = None
        # if not type(self.sender_address) == type(0):
        #     self.signature = self.sign_transaction(sender_private_key)  # ?????

    def sign_transaction(self, private_key):
        """
        Sign transaction with private key
        """
        signature = PKCS1_v1_5.new(private_key).sign(self.transaction_id)
        return signature

    # helpers???????
    def verify_transaction(self):
        return True

    def printMe(self):
        sender = self.sender_address
        receiver = self.receiver_address
        if (not self.reals == None):
            sender = self.reals
        if (not self.realr == None):
            receiver = self.realr
        print("\t \t I am transaction ({}) giving {} $ from node {} to node {}".format(self.transaction_id_hex,
                                                                                       self.amount, sender, receiver))

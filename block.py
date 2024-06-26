#   index: o αύξων αριθμός του block,   -
# ● timestamp: το timestamp της δημιουργίας του block -
# ● transactions: Η λίστα με τα transactions που περιέχονται στο block  -
# ● validator: το public key του κόμβου που επικύρωσε το block
# ● current_hash: το hash του block
# ● previous_hash: το hash του προηγούμενου block στο blockchain.
# Θεωρούμε ότι το κάθε block έχει συγκεριμένη χωρητικότητα σε αριθμό από transaction. Η
# χωρητικότητα καθορίζεται από τη σταθερά capacity.

import threading
import time
import jsonpickle
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA

def makeRSAjsonSendable(rsa):  # ????
    return rsa.exportKey("PEM").decode('ascii')


def makejsonSendableRSA(jsonSendable):  # ????
    return RSA.importKey(jsonSendable.encode('ascii'))

class Block:
    def __init__(self, index, previousHash_hex, timestamp, capacity, validator):
        self.index = index
        self.timestamp = timestamp
        self.listOfTransactions = []
        self.previousHash_hex = previousHash_hex
        self.capacity = capacity
        self.timeCreated = time.time()
        self.timeAdded = None
        self.validator = validator
        self.lock = threading.Lock()

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['lock']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.lock = threading.Lock()

    def compute_current_hash(self):
        return SHA.new(
            (str(self.index) + str(self.previousHash_hex)).encode()
        ).hexdigest()

    # def to_dict(self):
    #     return {
    #         'index': self.index,
    #         'timestamp': self.timestamp,
    #         'previousHash_hex': self.previousHash_hex,
    #         'currentHash_hex': self.compute_current_hash(),
    #         'capacity': self.capacity,
    #     }

    @classmethod
    # def from_dict(cls, block_dict):
    #     block = cls(
    #         block_dict['index'],
    #         block_dict['previousHash_hex'],
    #         block_dict['nonce'],
    #         block_dict['timestamp'],
    #         block_dict['capacity']
    #     )
    #     return block
    def __eq__(self, other):
        """Overrides the default implementation"""
        ret = (
                self.index == other.index and self.previousHash_hex == other.previousHash_hex and self.timestamp == other.timestamp)
        return ret

    # ti kanoume me to nonce
    def myHash(self):
        return SHA.new((str(self.index) + str(self.previousHash_hex)).encode())

    #  helpers?
    def add_transaction(self, transaction):
        self.listOfTransactions.append(transaction)

    def convert_transactions(self):
        for transaction in self.listOfTransactions:
            if isinstance(transaction.sender_address, RSA.RsaKey):
                transaction.sender_address = makeRSAjsonSendable(transaction.sender_address)

            if isinstance(transaction.receiver_address, RSA.RsaKey):
                transaction.receiver_address = makeRSAjsonSendable(transaction.receiver_address)

    def revert_transactions(self):
        for transaction in self.listOfTransactions:
            if isinstance(transaction.sender_address, str):
                transaction.sender_address = makejsonSendableRSA(transaction.sender_address)

            #den me noiazei na allaksw pisw to receiver_address PROS TO PARON


    def printMe(self):
        print("\t I am block with index", self.index)
        print("\t My current hash is")
        print(self.compute_current_hash())
        print("\t My Transaction list contains:")
        for t in self.listOfTransactions:
            t.printMe()
        print("All of me:", self)

    def isInBlock(self, hex):
        for t in self.listOfTransactions:
            if (t.transaction_id_hex == hex):
                return True
        return False
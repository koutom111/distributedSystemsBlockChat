#   index: o αύξων αριθμός του block,   -
# ● timestamp: το timestamp της δημιουργίας του block -
# ● transactions: Η λίστα με τα transactions που περιέχονται στο block  -
# ● validator: το public key του κόμβου που επικύρωσε το block
# ● current_hash: το hash του block
# ● previous_hash: το hash του προηγούμενου block στο blockchain.
# Θεωρούμε ότι το κάθε block έχει συγκεριμένη χωρητικότητα σε αριθμό από transaction. Η
# χωρητικότητα καθορίζεται από τη σταθερά capacity.


from Crypto.Hash import SHA
import threading
import time


class Block:
    def __init__(self, index, previousHash_hex, nonce, timestamp, difficulty, capacity):
        self.index = index
        self.timestamp = timestamp
        self.listOfTransactions = []
        # validator
        self.currentHash = SHA.new(
            (str(self.index) + str(self.previousHash_hex) + str(self.nonce)).encode())  # ti kanoume me to nonce
        self.currentHash_hex = self.currentHash.hexdigest()
        self.previousHash_hex = previousHash_hex

        self.capacity = capacity

        # self.nonce = nonce #not needed in our work

        self.timeCreated = time.time()  # axrista????
        self.timeAdded = None  # axrista????
        self.difficulty = difficulty  # axrista????
        self.lock = threading.Lock()

    # The __eq__ function in Python is a method for defining how instances of a class should be compared for equality.
    def __eq__(self, other):
        """Overrides the default implementation"""
        ret = (
                self.index == other.index and self.previousHash_hex == other.previousHash_hex and self.timestamp == other.timestamp)
        return ret

    # ti kanoume me to nonce
    def myHash(self, nonce):
        return SHA.new((str(self.index) + str(self.previousHash_hex) + str(self.nonce)).encode())

    #  helpers?
    def add_transaction(self, transaction):
        self.listOfTransactions.append(transaction)

    def printMe(self):
        print("\t I am block with index", self.index)
        print("\t My Transaction list contains:")
        for t in self.listOfTransactions:
            t.printMe()

    def isInBlock(self, hex):
        for t in self.listOfTransactions:
            if (t.transaction_id_hex == hex):
                return True
        return False

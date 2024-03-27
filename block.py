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
    def __init__(self, index, previousHash_hex, nonce, timestamp, capacity):
        self.index = index
        self.timestamp = timestamp
        self.listOfTransactions = []
        # validator
        self.previousHash_hex = previousHash_hex
        self.currentHash = SHA.new(
            (str(self.index) + str(self.previousHash_hex) + str(nonce)).encode())  # ti kanoume me to nonce????????????
        self.currentHash_hex = self.currentHash.hexdigest()


        self.capacity = capacity

        # self.nonce = nonce #not needed in our work

        self.timeCreated = time.time()  # axrista????
        self.timeAdded = None  # axrista????
        #self.difficulty = difficulty  # axrista????
        self.lock = threading.Lock()

    # The __eq__ function in Python is a method for defining how instances of a class should be compared for equality.
    def to_dict(self):
        """Converts the block into a dictionary for easier serialization."""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'listOfTransactions': [t.to_dict() for t in self.listOfTransactions],
            # Assuming Transaction has a to_dict method
            'previousHash_hex': self.previousHash_hex,
            'currentHash_hex': self.currentHash_hex,
            'capacity': self.capacity,
            # Exclude non-serializable fields like 'lock'
        }

    def block_from_dict(block_dict):     ## mallon einai lathos
        """Recreates a Block instance from a dictionary."""
        block = Block(
            block_dict['index'],
            block_dict['previousHash_hex'],
            block_dict.  # Provide default value if nonce isn't stored
            block_dict['timestamp'],
            block_dict['capacity']
        )
        # Assuming Transaction has a from_dict method or similar
        block.listOfTransactions = [Transaction.from_dict(t) for t in block_dict['listOfTransactions']]
        # Reinitialize any non-serialized fields like 'lock'
        block.lock = threading.Lock()
        return block
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

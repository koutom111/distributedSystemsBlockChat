#   chain: το blockchain ως τωρα,   -
# BCCs - currentBCCs ???? διαφορά ??? -
# wallet: public - private key  -
# ring: λίστα με τα IPs ολων των nodes και pub keys
# current_block: το hash του current block ???
# previous_block: το hash του προηγούμενου block στο blockchain ???
# myip: το IP του node
# myport: το port του node
# completed_transactions : vlepoume an to theloume
# validated_transactions : vlepoume an to theloume
# nonce : μετρητής transactions
# state : λίστα με τους υπάρχοντες λογαριασμούς και τα υπόλοιπά τους
# staking : για το proof-of-state
import base64
import pickle
import random

from block import Block
from wallet import Wallet
from transaction import Transaction
import time
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
import jsonpickle
import requests
from _thread import *
import threading

DEBUG = False
PRINTCHAIN = False


def makeRSAjsonSendable(rsa):
    return rsa.exportKey("PEM").decode('ascii')


def makejsonSendableRSA(jsonSendable):
    return RSA.importKey(jsonSendable.encode('ascii'))


class Node:
    def __init__(self):

        self.chain = None
        self.current_id_count = None  # +1 every time a node is added
        self.id = None  # 0...n-1   #auto 8a to balei o bootstrap
        self.BCCs = []
        self.current_BCCs = []
        self.wallet = None  # created with generate_wallet()   / prepei na to steilei sto bootstrap
        self.ring = []
        self.generate_wallet()
        self.previous_block = None
        self.current_block = None
        self.block_capacity = None
        self.myip = None
        self.myport = None
        self.completed_transactions = []
        self.validated_transactions = []
        self.all_lock = threading.Lock()
        self.nonce = 0 #DIKO MAS
        self.state = [] #DIKO MAS
        self.staking =0 #DIKO MAS
        self.winner = None #HELPER FOR VALIDATION

    def create_new_block(self, index, previousHash_hex, timestamp, capacity, validator):
        return Block(index, previousHash_hex, timestamp, capacity, validator)

    def generate_wallet(self):
        self.wallet = Wallet()

    def create_transaction(self, sender, sender_private_key, receiver, transaction_type, amount, nonce, message):
        realsender = None
        realreceiver = None
        if (DEBUG):
            if (type(sender) == type(0)):
                realsender = "genesis"
                realreceiver = "0"
            for r in self.ring:
                try:
                    if (r['public_key'] == sender):
                        realsender = r['id']
                except:
                    pass
                try:
                    if (r['public_key'] == makeRSAjsonSendable(sender)):
                        realsender = r['id']
                except:
                    pass
                try:
                    if (sender == self.wallet.public_key):
                        realsender = self.id
                except:
                    pass
                try:
                    if (makeRSAjsonSendable(sender) == makeRSAjsonSendable(self.wallet.public_key)):
                        realsender = self.id
                except:
                    pass
                try:
                    if (r['public_key'] == receiver):
                        realreceiver = r['id']
                except:
                    pass
                try:
                    if (r['public_key'] == makeRSAjsonSendable(receiver)):
                        realreceiver = r['id']
                except:
                    pass
                try:
                    if (receiver == self.wallet.public_key):
                        realreceiver = self.id
                except:
                    pass
                try:
                    if (makeRSAjsonSendable(receiver) == makeRSAjsonSendable(self.wallet.public_key)):
                        realreceiver = self.id
                except:
                    pass
        transaction = Transaction(sender, sender_private_key, receiver, transaction_type, amount, nonce, message, reals=realsender, realr=realreceiver)

        # if (not realsender == "genesis"):
        #     transaction.transaction_inputs = self.current_BCCs[realsender][1]
        #
        #     output_id1 = transaction.transaction_id_hex + 'a'
        #     output1 = [output_id1, transaction.transaction_id_hex, int(realreceiver), amount]
        #     transaction.transaction_outputs.append(output1)
        #
        #     output_id2 = transaction.transaction_id_hex + 'b'
        #     output2 = [output_id2, transaction.transaction_id_hex, int(realsender),
        #                self.current_BCCs[int(realsender)][0] - amount]
        #     transaction.transaction_outputs.append(output2)
        #
        # if (transaction.signature):
        #     transactionjson = jsonpickle.encode(transaction)
        #     baseurl = 'http://{}:{}/'.format(self.myip, self.myport)
        #     res = requests.post(baseurl + "ValidateTransaction", json={'transaction': transactionjson})

        if self.state:  #GIA NA TESTARW AN DOYLEVEI TO BROADCAST_TRANSACTION META TO SVHNW
            for r in self.ring:
                start_new_thread(self.broadcast_transaction, (transaction, r,))
        return transaction

    def broadcast_transaction(self, transaction, r):
        baseurl = 'http://{}:{}/'.format(r['ip'], r['port'])
        # den mporw na ta steilw an einai RSA
        if isinstance(transaction.sender_address, RSA.RsaKey):
            transaction.sender_address = makeRSAjsonSendable(transaction.sender_address)

        if isinstance(transaction.receiver_address, RSA.RsaKey):
            transaction.receiver_address = makeRSAjsonSendable(transaction.receiver_address)

        json_trans = pickle.dumps(transaction)
        serialized_trans_b64 = base64.b64encode(json_trans).decode('utf-8')
        res = requests.post(baseurl + "ValidateTransaction", json={'transaction': serialized_trans_b64})

    def validate_transaction(self, transaction):
        # sender_address = transaction.sender_address
        # h = SHA.new(transaction.transaction_myid.encode())
        # signature = transaction.signature
        # pubkey = sender_address
        # verified = PKCS1_v1_5.new(pubkey).verify(h, signature)
        verified = transaction.verify_signature()
        if (not (verified)):
            return False

        realsender = int(transaction.reals)
        realreceiver = int(transaction.realr)

        if (verified and transaction.amount <= self.current_BCCs[int(realsender)][0]):
            self.current_BCCs[realsender][0] = self.current_BCCs[realsender][0] - transaction.amount
            self.current_BCCs[realsender][1].append(transaction.transaction_id_hex)
            self.current_BCCs[realreceiver][0] = self.current_BCCs[realreceiver][0] + transaction.amount
            self.current_BCCs[realreceiver][1].append(transaction.transaction_id_hex)
            return True

        else:
            return False

    def add_transaction_to_block(self, transaction):
        self.all_lock.acquire()
        for b in self.chain.chain:
            for trans_iter in b.listOfTransactions:
                if (transaction.transaction_id_hex == trans_iter.transaction_id_hex):
                    try:
                        self.all_lock.release()
                    except:
                        pass
                    return False

        for trans_iter in self.completed_transactions:
            if (transaction.transaction_id_hex == trans_iter.transaction_id_hex):
                try:
                    self.all_lock.release()
                except:
                    pass
                return False

        for trans_iter in self.validated_transactions:
            if (transaction.transaction_id_hex == trans_iter.transaction_id_hex):
                try:
                    self.all_lock.release()
                except:
                    pass
                return False

        for trans_iter in self.current_block.listOfTransactions:
            if (transaction.transaction_id_hex == trans_iter.transaction_id_hex):
                try:
                    self.all_lock.release()
                except:
                    pass
                return False
        self.current_block.add_transaction(transaction)
        self.validated_transactions.append(transaction)

        if (len(self.current_block.listOfTransactions) == self.current_block.capacity):
            try:
                self.all_lock.release()
            except:
                pass
            finally:
                self.all_lock.acquire()
            mined_block = self.mine_block()
            self.current_block = self.create_new_block(self.current_block.index + 1, self.current_block.currentHash_hex,
                                                       0, time.time(), self.current_block.difficulty,
                                                       self.current_block.capacity)
            try:
                self.all_lock.release()
            except:
                pass
        else:
            try:
                self.all_lock.release()
            except:
                pass
        return 1

    def mint_block(self):
        state = self.state
        seed = self.chain.chain[-1].compute_current_hash()
        total_stake = sum(node['staking'] for node in state)

        random.seed(seed)

        # Check if all stakes are 0
        if total_stake == 0:
            # If all stakes are 0, choose a random node as the validator
            winner = random.choice([node['public_key'] for node in state])
        else:
            rand_num = random.uniform(0, 1)
            cumulative_percentage = 0
            for node in state:
                node_percentage = node['staking'] / total_stake
                cumulative_percentage += node_percentage
                if rand_num <= cumulative_percentage:
                    winner = node['public_key']
                    break
            else:
                # If for some reason we don't select any node, return None
                return None

        self.winner = winner
        if winner == self.wallet.public_key:
            self.current_block.validator = self.wallet.public_key
            return self.current_block
        # if you didn't win don't return any block
        return None

    def broadcast_block(self, block, r):
        baseurl = 'http://{}:{}/'.format(r['ip'], r['port'])
        #kanw ta transactions xwris RSA attributes
        block.convert_transactions()
        json_block = pickle.dumps(block)
        serialized_block_b64 = base64.b64encode(json_block).decode('utf-8')
        res = requests.post(baseurl + "AddBlock", json={'block': serialized_block_b64})

    def validate_block(self, block):
        #gia na prospernaei to genesis
        if (block.previousHash_hex == 1 and block.validator == 0):
            return True
        if (block.validator == self.winner and block.previousHash_hex == self.chain.chain[-1].compute_current_hash()):
            return True
        else:
            return False

    def validate_chain(self, blockchain):
        for block in blockchain.chain:
            # if (block.index > 0):
            if not self.validate_block(block):
                return False
            return True

    def stake(self, amount):
        self.nonce += 1
        self.staking = amount
        transaction = self.create_transaction(self.wallet.public_key, self.wallet.private_key, 0,
                                          'payment', amount, self.nonce,
                                          'stake')
        return transaction

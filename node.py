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
        self.balance = 0
        self.wallet = None  # created with generate_wallet()   / prepei na to steilei sto bootstrap
        self.ring = []
        self.generate_wallet()
        self.previous_block = None
        self.current_block = None
        self.block_capacity = None
        self.myip = None
        self.myport = None
        self.temp_transactions = []
        self.validated_block_transactions = []
        self.all_lock = threading.Lock()
        self.nonce = 0  # DIKO MAS
        self.state = []  # DIKO MAS
        self.staking = 0  # DIKO MAS
        self.winner = None  # HELPER FOR VALIDATION

    def create_new_block(self, index, previousHash_hex, timestamp, capacity, validator):
        return Block(index, previousHash_hex, timestamp, capacity, validator)

    def generate_wallet(self):
        self.wallet = Wallet()

    def create_transaction(self, sender, sender_private_key, receiver, transaction_type, nonce, amount=None,
                           message=None):
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
        transaction = Transaction(sender, sender_private_key, receiver, transaction_type, nonce, amount, message,
                                  reals=realsender, realr=realreceiver)

        if message == 'First Salary':
            self.all_lock.acquire()
            self.balance -= transaction.amount
            self.all_lock.release()


        elif message == 'First Transaction':
            self.all_lock.acquire()
            self.balance = amount
            self.all_lock.release()
        else:
            if transaction.signature:
                baseurl = 'http://{}:{}/'.format(self.myip, self.myport)
                if isinstance(transaction.sender_address, RSA.RsaKey):
                    transaction.sender_address = makeRSAjsonSendable(transaction.sender_address)

                if isinstance(transaction.receiver_address, RSA.RsaKey):
                    transaction.receiver_address = makeRSAjsonSendable(transaction.receiver_address)

                json_trans = pickle.dumps(transaction)
                serialized_trans_b64 = base64.b64encode(json_trans).decode('utf-8')
                res = requests.post(baseurl + "ValidateTransaction", json={'transaction': serialized_trans_b64})

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
            self.current_block.lock.acquire()
            self.current_block.validator = self.wallet.public_key
            for trans in self.temp_transactions:
                self.current_block.listOfTransactions.append(trans)
            self.current_block.lock.release()

            return self.current_block
        # if you didn't win don't return any block
        return None

    def validate_transaction(self, transaction):
        if not transaction.verify_signature():
            return False, 'Invalid signature'

        if transaction.transaction_id_hex in self.validated_block_transactions:  # ?????????????????
            return True, 'Valid from previous block'

        trans = transaction

        coins_needed = trans.calculate_charge()
        if self.wallet.public_key == trans.sender_address:
            balance = self.balance
            stake = self.staking
            nonce = self.nonce
            if nonce > trans.nonce:
                return False ,f'nonce>{nonce}'
        else:
            for r in self.state:
                # if isinstance(trans.sender_address, str):
                #     trans.sender_address = makejsonSendableRSA(trans.sender_address)
                # if isinstance(r['public_key'], str):
                #     trans.sender_address = makejsonSendableRSA(r['public_key'])
                # # if isinstance(trans.receiver_address, str):
                # #     trans.receiver_address = makejsonSendableRSA(trans.receiver_address)
                if r['public_key'] == trans.sender_address:
                    sender_dict = r
                    balance = sender_dict['balance']
                    stake = sender_dict['staking']
                    nonce = sender_dict['nonce']

        if (type(trans.receiver_address) == type(0)) & (coins_needed > balance):
            return False, 'not enough for stake'
        elif coins_needed > balance - stake:
            # logging.info('Sender does not have enough coins.')
            return False, f'not enough! coins needed:{coins_needed} and balance {balance} and  stake {stake}'
        else:
            return True, f'All validated from me: coins needed:{coins_needed} and balance {balance} and  stake {stake}'

    def broadcast_block(self, block, r):
        baseurl = 'http://{}:{}/'.format(r['ip'], r['port'])
        # kanw ta transactions xwris RSA attributes
        block.convert_transactions()
        json_block = pickle.dumps(block)
        serialized_block_b64 = base64.b64encode(json_block).decode('utf-8')
        res = requests.post(baseurl + "AddBlock", json={'block': serialized_block_b64})


    def validate_block(self, block):
        # gia na prospernaei to genesis
        if (block.previousHash_hex == 1 and block.validator == 0):
            return True
        if (block.validator == self.winner and block.previousHash_hex == self.chain.chain[-1].compute_current_hash()):
            return True
        else:
            return False

    def update_recipient_balances(self, block):
        # logging.info('Validating block from minter', block.validator)
        for trans in block.listOfTransactions:

            for i in range(len(self.temp_transactions)):
                if self.temp_transactions[i].transaction_id_hex == trans.transaction_id_hex:

                    validator = block.validator

                    self.all_lock.acquire()

                    if trans.transaction_type == 'coins':
                        recipient = makejsonSendableRSA(trans.receiver_address)
                        amount = trans.amount
                        # Update recipient balance
                        for r in self.state:
                            # Give 3% to the block validator
                            if r['public_key'] == validator:
                                r['balance'] += amount * 0.03
                        if self.wallet.public_key == recipient:
                            self.balance += amount
                    elif trans.type_of_transaction == 'message':
                        amount = len(trans.message)
                        for r in self.state:
                            if r['public_key'] == validator:
                                r['balance'] += amount

                    self.all_lock.release()
                    del self.temp_transactions[i]
                    break

                elif trans.transaction_id_hex not in self.validated_block_transactions:
                    validator = block.validator

                    self.all_lock.acquire()

                    if trans.transaction_type == 'coins':
                        recipient = makejsonSendableRSA(trans.receiver_address)
                        amount = trans.amount
                        # Update recipient balance
                        for r in self.state:
                            # Give 3% to the block validator
                            if r['public_key'] == validator:
                                r['balance'] += amount * 0.03
                        if self.wallet.public_key == recipient:
                            self.balance += amount
                            # and sender balance?
                    elif trans.type_of_transaction == 'message':
                        amount = len(trans.message)
                        for r in self.state:
                            if r['public_key'] == validator:
                                r['balance'] += amount

                    if self.wallet.public_key == trans.sender_address:  # an eimai o sender
                        if (type(trans.receiver_address) == type(0)):
                            self.staking = trans.amount  # an exw kanei egw stake
                        else:
                            self.balance -= trans.calculate_charge()  # an egw exw xrewsei kapoion
                    elif not (type(trans.receiver_address) == type(
                            0)):  # an den einai stake kai kapoios allos einai o sender
                        for r in self.state:
                            if r['public_key'] == trans.sender_address:  # vres poios einai o sender kai afairesai poso
                                r['balance'] -= trans.calculate_charge()
                                r['nonce'] = trans.nonce
                    else:
                        for r in self.state:  # vres poios exei balei na kanei stake
                            if r['public_key'] == trans.sender_address:
                                r['staking'] = trans.amount
                                r['nonce'] = trans.nonce

                    if trans.transaction_type == 'coins':
                        recipient = makejsonSendableRSA(trans.receiver_address)
                        amount = trans.amount
                        # Update recipient balance
                        if self.wallet.public_key == recipient:
                            self.balance += amount
                        else:
                            for r in self.state:
                                if r['public_key'] == recipient:
                                    r['balance'] += amount

                    # if trans.transaction_type == 'message':
                    #     recipient = makejsonSendableRSA(trans['receiver_address'])
                    #     message = trans.message
                    #     # Update recipient balance
                    #     if self.wallet.public_key == recipient:
                    #         print(f'I received message: {message} from {trans.sender_address}')

                    self.all_lock.release()

                self.validated_block_transactions.append(trans.transaction_id_hex)

    def traceback_transaction(self):
        for trans in self.temp_transactions:
            self.all_lock.acquire()
            if self.wallet.public_key == trans.sender_address:  # an eimai o sender
                if (type(trans.receiver_address) == type(0)):
                    pass  # an exw kanei egw stake
                else:
                    self.balance += trans.calculate_charge()  # an egw exw xrewsei kapoion
            elif not (type(trans.receiver_address) == type(0)):  # an den einai stake kai kapoios allos einai o sender
                for r in self.state:
                    if r['public_key'] == trans.sender_address:  # vres poios einai o sender kai afairesai poso
                        r['balance'] += trans.calculate_charge()

            if trans.transaction_type == 'coins':
                recipient = makejsonSendableRSA(trans.receiver_address)
                amount = trans.amount
                # Update recipient balance
                if self.wallet.public_key == recipient:
                    self.balance -= amount
                else:
                    for r in self.state:
                        if r['public_key'] == recipient:
                            r['balance'] -= amount

            self.all_lock.release()

    def validate_chain(self, blockchain):
        for block in blockchain.chain:
            # if (block.index > 0):
            if not self.validate_block(block):
                return False
            return True

    def stake(self, amount):
        self.all_lock.acquire()
        self.nonce += 1
        self.all_lock.release()

        self.staking = amount

        transaction = self.create_transaction(self.wallet.public_key, self.wallet.private_key, 0,
                                              'payment', self.nonce, amount,
                                              'stake')
        return transaction

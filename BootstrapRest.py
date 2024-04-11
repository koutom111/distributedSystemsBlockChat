import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from multiprocessing import Value, Array, Process, Manager, Lock
from block import Block
from node import Node
from blockchain import Blockchain
from wallet import Wallet
from _thread import *
import threading
import transaction
import json
import sys, os
import time
import jsonpickle
import pickle
import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from copy import deepcopy
from Crypto.Signature import PKCS1_v1_5
import base64

PRINTCHAIN = False
CLIENT = 1  # read transactions from noobcash client
# CLIENT = 0  # read transactions from txt

app = Flask(__name__)
CORS(app)


def makeRSAjsonSendable(rsa):
    return rsa.exportKey("PEM").decode('ascii')


def makejsonSendableRSA(jsonSendable):
    return RSA.importKey(jsonSendable.encode('ascii'))


#######################  marika      ################################

def read_transaction(node):  # na balw to cli script
    help_message = '''
    Available commands:
    * `t [recepient_address] [message] `                Send `message` of `type` transaction to `recepient` node
    * `stake [amount]`                                        Set the node stake
    * `view`                                                  View transactions of the latest block
    * `balance`                                               View balance of each wallet (as of last validated block)
    * `help`                                                  Print this help message
    '''
    if CLIENT:
        print("============================")
        print("!!! WELCOME TO BLOCKCHAT !!!")
        print("============================")
        while (True):
            print("Enter a desired action! Type help if want to know the available actions!")
            choice = input()

            # Transaction
            if choice.startswith('t'):
                params = choice.split()

                payload = {'receiver_id': int(params[1]), 'message': params[2]}

                print('Transaction!')
                print(payload)
                transaction_type = 'message'
                if payload['message'].isdigit():
                    transaction_type = 'coins'
                flag = 0
                for r in node.ring:
                    if r['id'] == payload['receiver_id']:
                        flag = 1
                        pub_key = r['public_key']

                        node.all_lock.acquire()
                        node.nonce += 1
                        node.all_lock.release()

                        if transaction_type == 'coins':
                            trans = node.create_transaction(node.wallet.address, node.wallet.private_key, pub_key,
                                                    transaction_type, node.nonce, payload['message'], None)
                            print(f"{trans}")
                            trans.printMe()

                        if transaction_type == 'message':
                            trans = node.create_transaction(node.wallet.address, node.wallet.private_key, pub_key,
                                                    transaction_type, node.nonce, None, payload['message'])
                            print(f"Created Transaction!! : \n {trans}")
                            trans.printMe()
                        break

                print(node.ring)
                if flag == 0:
                    print("<recipient_address> invalid")

            # Stake
            elif choice.startswith('s'):
                params = choice.split()

                payload = {'ammount': params[1]}
                print('Stake!')
                print(payload)

                stake = node.stake(payload['ammount'])
                print(stake)

            # view last transaction
            elif choice == 'view':
                node.chain.view()
                # response = requests.get(URL + "view_transactions")
                # print(response.json())
            # balance
            elif choice == 'balance':
                print(node.balance)
            # help
            elif choice == 'help':
                print(help_message)
            else:
                print("Invalid action. Try again!")
    # ??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????//
    # else:
    #     f = open("5nodes/transactions" + str(node.id) + ".txt", "r")
    #     for line in f:
    #         id, amount = (line).split()
    #         for n in node.ring:
    #             if int(n['id']) == int(id[-1]):
    #                 node.create_transaction(node.wallet.address, node.wallet.private_key, n['public_key'], int(amount))
    #                 break


def FirstBroadcast(ring):
    for r in ring:
        baseurl = 'http://{}:{}/'.format(r['ip'], r['port'])
        ringWithoutSelf = {}
        u = 0
        for k in ring:
            if (not k['port'] == r['port']):
                ringWithoutSelf[str(u)] = k
                u += 1

        load = ringWithoutSelf

        while (True):
            try:
                r = requests.get(baseurl + "Live")
                r.raise_for_status()
            except:
                time.sleep(0.1)
            else:
                break
        json_load = pickle.dumps(load)
        serialized_load_b64 = base64.b64encode(json_load).decode('utf-8')
        resRing = requests.post(baseurl + "UpdateRing", json=serialized_load_b64)
        print(resRing)
    start_new_thread(read_transaction, (node,))


def MakeFirstTransaction(pub_key, ip, port):
    print(MakeFirstTransaction)
    amount = 1000
    baseurl = 'http://{}:{}/'.format(ip, port)
    while (True):
        try:
            r = requests.get(baseurl + "Live")
            r.raise_for_status()
        except:
            time.sleep(0.1)
        else:
            break

    # node.all_lock.acquire()
    # node.nonce += 1  # ayksanw to nonce PREPEI NA VALW LOCK??????
    # node.all_lock.release()

    # pub_key einai JSON kai bootstrap_public_key RSA
    transaction = node.create_transaction(bootstrap_public_key, node.wallet.private_key, pub_key,
                                          'coins', node.nonce, amount,
                                          'First Salary')  # ayto to node einai to bootstap se ayto to script

    genesis_block.add_transaction(transaction)

    if BootstrapDict['nodeCount'] == BootstrapDict['N']:
        blockchain.add_block_to_chain(genesis_block)
        print('\nGenesis\n')
        print(node.chain.printMe())

    # ti kanoyme me to nonce?? pros to paron to bazw 2
    transaction.printMe()
    return transaction


######################################################

# @app.route('/ValidateTransaction', methods=['POST'])
# def ValidateTransaction():
#     if request is None:
#         return "Error: Please supply a valid Transaction", 400
#     data = request.json
#     if data is None:
#         return "Error: Please supply a valid Transaction", 400
#     print(f'Received  ValidateTransaction data: {data}')
#     return data
#     # trans = jsonpickle.decode(data["transaction"])
#     # valid = node.validate_transaction(trans)                        #to be fixed!!!
#     # if(valid):
#     #     node.add_transaction_to_block(transaction)                  #to be fixed!!!!!!!
#     #
#     #     return "Transaction Validated by Node {} !".format(node.id), 200
#     # else:
#     #     return "Error: Not valid!", 400

@app.route('/Live', methods=['GET'])
def Live():
    return "I am alive!", 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    if request is None:
        return "Error: Please supply a valid Node", 400
    data = request.json
    # print('\n load pub key\n')
    # print(data['public_key'])
    if data is None:
        return "Error: Please supply a valid Node", 400
    if (BootstrapDict['nodeCount'] >= BootstrapDict['N']):
        print(BootstrapDict['nodeCount'])
        return "Error: System is full", 405

    lock = Lock()
    lock.acquire()
    BootstrapDict['nodeCount'] += 1
    BootstrapDictInstance = BootstrapDict.copy()
    lock.release()

    # print(BootstrapDictInstance)
    # print(makejsonSendableRSA(BootstrapDictInstance['bootstrap_public_key']))
    #
    # print()
    # print()
    # print(node.current_block.listOfTransactions)
    # print(json.dumps(node.current_block.to_dict()))
    # print()

    node.ring.append({'id': BootstrapDictInstance['nodeCount'] - 1, 'ip': data['ip'], 'port': data['port'],
                      'public_key': data['public_key'], 'balance': 1000})  # na ftiajv to load poy erxete apo to Rest.py
    node.state.append({
            'id': BootstrapDictInstance['nodeCount'] - 1,
            'public_key': data['public_key'],
            'balance': int(1000),
            'staking': 0,
            'nonce': 0
        })
    # print("Node Count:", BootstrapDict['nodeCount'])
    # print("N:", BootstrapDict['N'])
    if (BootstrapDict['nodeCount'] == BootstrapDict['N']):
        start_new_thread(FirstBroadcast, (node.ring,))  # 8elei ftiajimo

    print('\nBlockchain\n')
    print(blockchain.printMe())
    print('\nNode.chain\n')
    print(node.chain)

    serialized_blockchain = pickle.dumps(blockchain)  # logika ayto 88a exei 8ema
    serialized_blockchain_b64 = base64.b64encode(serialized_blockchain).decode('utf-8')
    # GIA NA TSEKARW AN DOYLEVEI TO SERIALIZATION/DESERIALIZATION
    # # Deserialize the serialized data
    # deserialized_blockchain = pickle.loads(serialized_blockchain)
    #
    # # Ensure that the deserialized object matches the original blockchain object
    # if deserialized_blockchain.chain == blockchain.chain:
    #     print("Serialization and deserialization successful!")
    # else:
    #     print("Serialization or deserialization failed.")
    print(f'Going for first transaction {data}')
    start_new_thread(MakeFirstTransaction, (data['public_key'], data['ip'], data['port'],))
    print(f"Port number {data['port']} is here")

    current_block_pickled = pickle.dumps(node.current_block)
    serialized_current_block_b64 = base64.b64encode(current_block_pickled).decode('utf-8')

    response = jsonify({'id': BootstrapDictInstance['nodeCount'],
                        'bootstrap_public_key': BootstrapDictInstance['bootstrap_public_key'],
                        'blockchain': serialized_blockchain_b64,
                        'block_capacity': BLOCK_CAPACITY,
                        'start_ring': {'id': 0, 'ip': '127.0.0.1', 'port': '5000',  # to be fixed for OUR bootstrap!!!
                                       'public_key': BootstrapDictInstance['bootstrap_public_key'],
                                       'balance': 1000},
                        'current_block': serialized_current_block_b64,
                        'balance': 1000})

    print(f"Response : {response.json}")
    return response


@app.route('/ValidateTransaction', methods=['POST'])
def ValidateTransaction():
    if request is None:
        return "Error: Please supply a valid Transaction", 400
    rejson = request.json
    # Deserialize transaction received from the server
    data = rejson["transaction"]
    serialized_data = base64.b64decode(data)
    trans = pickle.loads(serialized_data)
    if trans is None:
        return "Error: Please supply a valid Transaction", 400
    # den me enoxlei to receiver_address na einai json PROS TO PARON
    if isinstance(trans.sender_address, str):
        trans.sender_address = makejsonSendableRSA(trans.sender_address)
    if isinstance(trans.receiver_address, str):
        trans.receiver_address = makejsonSendableRSA(trans.receiver_address)
    print(trans.message)
    print("BROADCASTED TRANSACTION!!!!!!!!!!!!!!")

    valid, message = node.validate_transaction(trans)
    print(message)
    if valid:
        node.temp_transactions.append(trans)

        node.all_lock.acquire()    #!!!!!!!

        if node.wallet.public_key == trans.sender_address: #an eimai o sender
            if (type(trans.receiver_address) == type(0)):
                node.staking = trans.amount                 #an exw kanei egw stake
            else:
                node.balance -= trans.calculate_charge()        #an egw exw xrewsei kapoion
        elif not (type(trans.receiver_address) == type(0)):   #an den einai stake kai kapoios allos einai o sender
            for r in node.state:
                if r['public_key'] == trans.sender_address:         #vres poios einai o sender kai afairesai poso
                    r['balance'] -= trans.calculate_charge()
                    r['nonce'] = trans.nonce
        else:
            for r in node.state:                            #vres poios exei balei na kanei stake
                if r['public_key'] == trans.sender_address:
                  r['staking'] = trans.amount
                  r['nonce'] = trans.nonce

        if trans.transaction_type == 'coins':
            recipient = trans.receiver_address
            amount = trans.amount
            # Update recipient balance
            if node.wallet.public_key == recipient:
                node.balance += amount
            else:
                for r in node.state:
                    if r['public_key'] == recipient:
                        r['balance'] += amount

        node.all_lock.release()

        if trans.transaction_type == 'message':
            recipient = trans.receiver_address
            message = trans.message
            # Update recipient balance
            if node.wallet.public_key == recipient:
                print()
                print('-------------------------------------------------')
                print(f'I received message: {message} from {trans.sender_address}')
                print('-------------------------------------------------')



        if len(node.temp_transactions) == node.block_capacity:
            minted = node.mint_block()
            if minted is not None:
                for r in node.ring:
                    start_new_thread(node.broadcast_block, (minted, r,))
                    node.temp_transactions = []

            node.current_block = node.create_new_block(node.current_block.index + 1,
                                                       node.current_block.compute_current_hash, time.time(),
                                                       node.current_block.capacity, None)
            print("Transaction Validated and New Block Created by Node {} !".format(node.id))
            return "Transaction Validated and New Block Created by Node {} !".format(node.id), 200
        print("Transaction Validated")
        return "Transaction Validated by Node {} !".format(node.id), 200
    else:
        print("Invalid Transaction")
        return "Error: Not valid!", 400



@app.route('/AddBlock', methods=['POST'])
def AddBlock():
    if request is None:
        return "Error: Please supply a valid Block", 400
    rejson = request.json
    # Deserialize transaction received from the server
    data = rejson["block"]
    serialized_data = base64.b64decode(data)
    block = pickle.loads(serialized_data)
    if block is None:
        return "Error: Please supply a valid Block", 400

    block.revert_transactions()
    if(block.index > 0):
        valid = node.validate_block(block)

        if (valid):
            node.update_recipient_balances(block)
            node.traceback_transaction()
        else:
            return "Error: Invalid Block", 400
        return "OK", 200


@app.route('/')
def home():
    return 'Hello, Bootstrap is here!'


if __name__ == '__main__':
    host = '127.0.0.1'
    port = 5000
    BLOCK_CAPACITY = 10
    N = 5  # Number of nodes i  the system
    blockchain = Blockchain()

    manager = Manager()  # ????? to 8eloyme???????

    BootstrapDict = manager.dict()
    nodeCount = 1
    bootstrap_public_key = ""

    node = Node()
    node.id = 0
    node.myip = host  # '192.168.1.5'
    node.myport = port

    bootstrap_public_key = node.wallet.public_key

    BootstrapDict['nodeCount'] = nodeCount
    BootstrapDict['bootstrap_public_key'] = makeRSAjsonSendable(bootstrap_public_key)
    BootstrapDict['N'] = N

    # print(BootstrapDict)

    # create genesis block
    genesis_block = node.create_new_block(0, 1, time.time(),
                                          BLOCK_CAPACITY, 0)  # index = 0, previousHash = 1, capacity = BLOCK_CAPACITY, validator=0

    # TSEKARW AN TO SERIALIZATION TOY BLOCK DOYLEVEI, ALLAZEI TO LOCK EPEIDH TO KANW EXCLUDE!!! EINAI THEMA??
    # serialized_genesis_block = pickle.dumps(genesis_block)
    #
    # # Deserialize the serialized data
    # deserialized_genesis_block = pickle.loads(serialized_genesis_block)
    #
    # # Ensure that the deserialized object matches the original genesis_block object
    # if deserialized_genesis_block.__dict__ == genesis_block.__dict__:
    #     print("Serialization and deserialization successful for genesis_block object!")
    # else:
    #     print("Serialization or deserialization failed for genesis_block object.")
    # print("Deserialized Genesis Block:")
    # print(deserialized_genesis_block.__dict__)

    # # Print genesis_block dictionary
    # print("\nGenesis Block:")
    # print(genesis_block.__dict__)
    # print(genesis_block)

    node.current_block = genesis_block

    # print(genesis_block.printMe())
    # first transaction
    amount = 1000 * N
    BootstrapDictInstance = BootstrapDict.copy()

    # node.all_lock.acquire()
    # node.nonce += 1
    # node.all_lock.release()

    first_transaction = node.create_transaction(0, None, BootstrapDictInstance['bootstrap_public_key'],
                                                'coins', node.nonce, amount, 'First Transaction')
    # # TSEKARW AN TO SERIALIZATION TOY TRANSACTION DOYLEVEI, EINAI OK
    # serialized_transaction = pickle.dumps(first_transaction)
    #
    # # Deserialize the pickled data
    # deserialized_transaction = pickle.loads(serialized_transaction)
    #
    # # Compare attributes to ensure successful serialization and deserializationamount
    # if first_transaction.__dict__ == deserialized_transaction.__dict__:
    #     print("Serialization and deserialization successful for Transaction object!")
    # else:
    #     print("Serialization or deserialization failed for Transaction object.")
    # vale mono ayto to 1o transaction sto genesis block

    # print('\nFirst Transaction:\n')
    # print(f'{first_transaction.printMe()}')

    genesis_block.add_transaction(first_transaction)

    # print('\nGenesis block after first transaction: \n')
    # print(f'{genesis_block.printMe()}')
    # vale to genesis block sto blockchain kai ftiaxe neo block gia na einai to current block
    node.chain = blockchain
    print(node.chain.printMe())
    node.previous_block = None
    node.current_block = node.create_new_block(1, genesis_block.compute_current_hash(), time.time(),
                                               BLOCK_CAPACITY, None)
    # jekina
    print('\nNew Block:\n')
    print(f'{node.current_block.printMe()}')
    app.run(host=host, port=port, debug=False)

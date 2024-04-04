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
# CLIENT = 1                                    # read transactions from noobcash client
CLIENT = 0  # read transactions from txt

app = Flask(__name__)
CORS(app)


def makeRSAjsonSendable(rsa):
    return rsa.exportKey("PEM").decode('ascii')


def makejsonSendableRSA(jsonSendable):
    return RSA.importKey(jsonSendable.encode('ascii'))


#######################  marika      ################################

def read_transaction():  # na balw to cli script
    if (CLIENT):
        print("****** Welcome to Noobcash Client . . . ******")
        while (True):
            input1 = input()
            if input1 == "view":
                node.chain.view()
            elif input1 == "balance":
                print("Wallet UTXO's: ", node.NBCs[node.id][0])
            elif input1 == "help":
                print(
                    "t <recipient_address> <amount>   New transaction: Sends to recipient_address wallet, amount NBC coins from wallet sender_address.")
                print(
                    "view                             View last transactions: Displays the transactions contained in the last validated block.")
                print("balance                          Show balance: Displays wallet UTXOs.")
            else:
                message = "'" + input1 + "'"
                a = input1.split()
                try:
                    int(a[2])
                    if (a[0] == 't'):
                        flag = 0
                        for r in node.ring:
                            if (r['ip'] == a[1]):
                                flag = 1
                                pk = r['public_key']
                                node.create_transaction(node.wallet.address, node.wallet.private_key, pk, int(a[2]))
                                break
                        if (flag == 0):
                            print("<recipient_address> invalid")
                    else:
                        print(message,
                              "is not recognized as a command. Please type 'help' to see all the valid commands")
                except:
                    print(message,
                          "except is not recognized as a command. Please type 'help' to see all the valid commands")
    else:
        f = open("5nodes/transactions" + str(node.id) + ".txt", "r")
        for line in f:
            id, amount = (line).split()
            for n in node.ring:
                if int(n['id']) == int(id[-1]):
                    node.create_transaction(node.wallet.address, node.wallet.private_key, n['public_key'], int(amount))
                    break


def FirstBroadcast(ring):
    for r in ring:
        baseurl = 'http://{}:{}/'.format(r['ip'], r['port'])
        ringWithoutSelf = {}
        print("------------------------------")
        print(r)
        print("------------------------------")
        u = 0
        for k in ring:
            if (not k['ip'] == r['ip']):
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
        resRing = requests.post(baseurl + "UpdateRing", json=load)
        print(resRing)
    # start_new_thread(read_transaction, ())


def MakeFirstTransaction(pub_key, ip, port):
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
    transaction = node.create_transaction(bootstrap_public_key, node.wallet.private_key, pub_key,
                                          'payment', amount, 2,
                                          'your first money')  # ayto to node einai to bootstap se ayto to script
    # ti kanoyme me to nonce?? pros to paron to bazw 2
    transaction.printMe()
    return transaction


######################################################


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    if request is None:
        return "Error: Please supply a valid Node", 400
    data = request.json
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

    print(BootstrapDictInstance)
    print(makejsonSendableRSA(BootstrapDictInstance['bootstrap_public_key']))

    print()
    print()
    print(node.current_block.listOfTransactions)
    print(json.dumps(node.current_block.to_dict()))
    print()

    node.ring.append({'id': BootstrapDictInstance['nodeCount'] - 1, 'ip': data['ip'], 'port': data['port'],
                      'public_key': data['public_key'], 'balance': 0})  # na ftiajv to load poy erxete apo to Rest.py

    print("Node Count:", BootstrapDict['nodeCount'])
    print("N:", BootstrapDict['N'])
    if (BootstrapDict['nodeCount'] == BootstrapDict['N']):
        start_new_thread(FirstBroadcast, (node.ring,))      #8elei ftiajimo

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

    start_new_thread(MakeFirstTransaction, (data['public_key'], data['ip'], data['port'],))
    print(f"Node:{node.id} BCCs: {node.BCCs}")
    print(f"Node: {node.id} Current BCCs: {node.current_BCCs}")
    print(f"Port number {data['port']} is here")
    response = jsonify({'id': BootstrapDictInstance['nodeCount'],
                        'bootstrap_public_key': BootstrapDictInstance['bootstrap_public_key'],
                        'blockchain': serialized_blockchain_b64,
                        'block_capacity': BLOCK_CAPACITY,
                        'start_ring': {'id': 0, 'ip': '192.168.1.5', 'port': '5000',
                                       'public_key': BootstrapDictInstance['bootstrap_public_key'],
                                       'balance': 0},
                        'current_block': json.dumps(node.current_block.to_dict()),
                        'BCCs': node.BCCs,
                        'current_BCCs': node.current_BCCs})

    print(f"Response : {response.json}")
    return response


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

    print(BootstrapDict)

    # create genesis block
    genesis_block = node.create_new_block(0, 1, 0, time.time(),
                                          BLOCK_CAPACITY)  # index = 0, previousHash = 1, nonce = 0, capacity = BLOCK_CAPACITY

    #TSEKARW AN TO SERIALIZATION TOY BLOCK DOYLEVEI, ALLAZEI TO LOCK EPEIDH TO KANW EXCLUDE!!! EINAI THEMA??
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

    # Print genesis_block dictionary
    print("\nGenesis Block:")
    print(genesis_block.__dict__)
    node.current_block = genesis_block
    print(genesis_block.printMe())
    # first transaction
    amount = 1000 * N
    BootstrapDictInstance = BootstrapDict.copy()
    first_transaction = node.create_transaction(0, None, BootstrapDictInstance['bootstrap_public_key'],
                                                'payment', amount, 1, 'First Transaction')
    # TSEKARW AN TO SERIALIZATION TOY TRANSACTION DOYLEVEI, EINAI OK
    # serialized_transaction = pickle.dumps(first_transaction)
    #
    # # Deserialize the pickled data
    # deserialized_transaction = pickle.loads(serialized_transaction)
    #
    # # Compare attributes to ensure successful serialization and deserialization
    # if first_transaction.__dict__ == deserialized_transaction.__dict__:
    #     print("Serialization and deserialization successful for Transaction object!")
    # else:
    #     print("Serialization or deserialization failed for Transaction object.")
    # vale mono ayto to 1o transaction sto genesis block
    print(f'First Transaction:{first_transaction.printMe()}')
    genesis_block.add_transaction(first_transaction)
    print(f'Genesis block after first transaction: {genesis_block.printMe()}')
    # vale to genesis block sto blockchain kai ftiaxe neo block gia na einai to current block
    blockchain.add_block_to_chain(genesis_block)
    node.chain = blockchain
    print(node.chain.printMe())
    node.previous_block = None
    node.current_block = node.create_new_block(1, genesis_block.to_dict()['currentHash_hex'], 0, time.time(),
                                               BLOCK_CAPACITY)
    # jekina
    app.run(host=host, port=port, debug=True)

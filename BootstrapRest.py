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
CLIENT = 1                                    # read transactions from noobcash client
#CLIENT = 0  # read transactions from txt

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
    * `exit`                                                  Exit client (will not stop server)
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

                payload = {'receiver_id': params[1], 'message': params[2]}

                print('Transaction!')
                print(payload)

                flag = 0
                for r in node.ring:
                    if r['id'] == payload['receiver_id']:
                        flag = 1
                        #TO BE FIXED
                        #pub_key = r['public_key']
                        #node.create_transaction(node.wallet.address, node.wallet.private_key, pk, int(a[2]))
                        break
                if flag == 0:
                    print("<recipient_address> invalid")
                # payload = json.dumps(payload)
                #
                # response = requests.post(URL + "create_transaction", data=payload,
                #                          headers={'Content-type': 'application/json', 'Accept': 'text/plain'})
                # if response.status_code == 200:
                #     print('Transaction Done!')
                # else:
                #     print(f'Error: {response.text}')
            #Stake
            elif choice.startswith('s'):
                params = choice.split()

                payload = {'ammount': params[1]}
                print('Stake!')
                print(payload)
                # payload = json.dumps(payload)
                #
                # response = requests.post(URL + "stake_ammount", data=payload,  # mporei na prepei na to allajoyme
                #                          )
                # if response.status_code == 200:
                #     print('Successful Stake')
                # else:
                #     print(f'Error: {response.text}')
            # view last transaction
            elif choice == 'view':
                node.chain.view()
                # response = requests.get(URL + "view_transactions")
                # print(response.json())
            # balance
            elif choice == 'balance':
                print(node.BCCs)
                print(node.current_BCCs)
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
    node.nonce += 1 #ayksanw to nonce PREPEI NA VALW LOCK??????
    # pub_key einai JSON kai bootstrap_public_key RSA
    transaction = node.create_transaction(bootstrap_public_key, node.wallet.private_key, pub_key,
                                          'payment', amount, node.nonce,
                                          'your first money')  # ayto to node einai to bootstap se ayto to script
    if transaction.verify_signature():
        print("VERIFIED !!!!!!!!!!!!!!!!!!")
    # ti kanoyme me to nonce?? pros to paron to bazw 2
    transaction.printMe()
    return transaction


######################################################


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
                      'public_key': data['public_key'], 'balance': 0})  # na ftiajv to load poy erxete apo to Rest.py

    # print("Node Count:", BootstrapDict['nodeCount'])
    # print("N:", BootstrapDict['N'])
    if (BootstrapDict['nodeCount'] == BootstrapDict['N']):
        start_new_thread(FirstBroadcast, (node.ring,))      #8elei ftiajimo

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

    start_new_thread(MakeFirstTransaction, (data['public_key'], data['ip'], data['port'],))
    print(f"Node:{node.id} BCCs: {node.BCCs}")
    print(f"Node: {node.id} Current BCCs: {node.current_BCCs}")
    print(f"Port number {data['port']} is here")

    current_block_pickled = pickle.dumps(node.current_block)
    serialized_current_block_b64 = base64.b64encode(current_block_pickled).decode('utf-8')

    response = jsonify({'id': BootstrapDictInstance['nodeCount'],
                        'bootstrap_public_key': BootstrapDictInstance['bootstrap_public_key'],
                        'blockchain': serialized_blockchain_b64,
                        'block_capacity': BLOCK_CAPACITY,
                        'start_ring': {'id': 0, 'ip': '192.168.1.5', 'port': '5000',             # to be fixed for OUR bootstrap!!!
                                       'public_key': BootstrapDictInstance['bootstrap_public_key'],
                                       'balance': 0},
                        'current_block': serialized_current_block_b64,
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

    #print(BootstrapDict)

    # create genesis block
    genesis_block = node.create_new_block(0, 1, time.time(),
                                          BLOCK_CAPACITY, 0)  # index = 0, previousHash = 1, capacity = BLOCK_CAPACITY, validator=0

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

    # # Print genesis_block dictionary
    # print("\nGenesis Block:")
    # print(genesis_block.__dict__)
    # print(genesis_block)

    node.current_block = genesis_block

    # print(genesis_block.printMe())
    # first transaction
    amount = 1000 * N
    BootstrapDictInstance = BootstrapDict.copy()
    node.nonce += 1
    first_transaction = node.create_transaction(0, None, BootstrapDictInstance['bootstrap_public_key'],
                                                'payment', amount, node.nonce, 'First Transaction')
    # # TSEKARW AN TO SERIALIZATION TOY TRANSACTION DOYLEVEI, EINAI OK
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

    # print('\nFirst Transaction:\n')
    # print(f'{first_transaction.printMe()}')

    genesis_block.add_transaction(first_transaction)

    # print('\nGenesis block after first transaction: \n')
    # print(f'{genesis_block.printMe()}')
    # vale to genesis block sto blockchain kai ftiaxe neo block gia na einai to current block
    blockchain.add_block_to_chain(genesis_block)
    node.chain = blockchain
    print(node.chain.printMe())
    node.previous_block = None
    node.current_block = node.create_new_block(1, genesis_block.compute_current_hash(), time.time(),
                                               BLOCK_CAPACITY, None)
    # jekina
    print('\nNew Block:\n')
    print(f'{node.current_block.printMe()}')
    app.run(host=host, port=port, debug=False)

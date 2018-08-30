#!/usr/bin/python3

import os
import sys
import collections
import json
from blockchain_parser.blockchain import Blockchain
from blockchain_parser.script import *

blockchain = Blockchain(os.path.expanduser('~/bitcoin-data/blocks'))

stop = 1
data = {}
txindex = {}

print ('start')
for block in blockchain.get_unordered_blocks():
    stop = stop + 1
    if stop > 80000:
        print ('stop break')
        break
    #print block
    print (stop)
    for transaction in block.transactions:
        txindex[transaction.hash] = {}
        output_i = 0
        for output in transaction.outputs:
            txindex[transaction.hash][output_i] = [output.value, []]
            for address in output.addresses:
                txindex[transaction.hash][output_i][1].append(address.address)
                #datalist = {}
                #datalist['hash'] = transaction.hash
                #datalist['value'] = output.value
                #data[address.address].append(output.value)
                #data[address.address].append(transaction.hash)
                if not address.address in data:
                    data[address.address] = output.value
                else:
                    data[address.address] += output.value
                ##print ('--------------')
                ##print (block.hash, output.addresses, output.value)
            output_i += 1
        for inp in transaction.inputs:
            try:
                tx = txindex[inp.transaction_hash][inp.transaction_index]
                for address in tx[1]:
                    data[address] -= tx[0]
            except:
                pass
            


print len(list(data.keys()))
for k in data:
    if data[k] < 0:
        print k, data[k] / 100000000.0
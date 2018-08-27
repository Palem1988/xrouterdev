#!/usr/bin/python3

import os
import sys
import collections
import json
from blockchain_parser.blockchain import Blockchain

blockchain = Blockchain(os.path.expanduser('~/.bitcoin/blocks'))


stop = 1
data = {}
data = collections.defaultdict(list)

print ('start')
for block in blockchain.get_unordered_blocks():
    stop = stop + 1
    if stop > 100000:
        print ('stop break')
        break
    for transaction in block.transactions:
        for output in transaction.outputs:
            for address in output.addresses:
                datalist = {}
                datalist['hash'] = transaction.hash
                datalist['value'] = output.value
                #data[address.address].append(output.value)
                #data[address.address].append(transaction.hash)
                data[address.address].append(datalist)
                ##print ('--------------')
                ##print (block.hash, output.addresses, output.value)
    if len (block.transactions) > 15:
        print (' 15 transactions, done')
        print ( json.dumps(data, indent=4))
        break



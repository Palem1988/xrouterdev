import os
import sys
import collections
import json
import pickle
import json

from blockchain_parser.blockchain import Blockchain
from blockchain_parser.script import *

chain_const = {"BTC":{"pch": b"\xf9\xbe\xb4\xd9", "vb":[b'\x00', b'\x05']},
         "BLOCK":{"pch": b"\xa1\xa0\xa2\xa3", "vb":[b'\x1a', b'\x1c']},
         "BLOCKTEST":{"pch": b"\x45\x76\x65\xba", "vb":[b'\x8b', b'\x13']}
         }

PREFIX_SIZE = 1

def gen_prefix(size):
    letters = "0123456789abcdef"
    if size == 1:
        return [c for c in letters]
    else:
        res = []
        suffixes = gen_prefix(size - 1)
        for c in letters:
            for s in suffixes:
                res.append(c + s)
        return res

class BalancePlugin:
    def __init__(self, chain, chainpath):
        self.chain = chain
        self.chainpath = chainpath
        self.last_block = 0
        if not os.path.isdir("txdata"):
            os.mkdir("txdata") 
        try:
            f = open("txdata/" + self.chain + "-balances.pickle", "rb")
            self.balances = pickle.load(f)
        except:
            self.balances = {}
        self.blockchain = Blockchain(os.path.expanduser(self.chainpath), chain_const[self.chain]["pch"])
       
    def load_settings(self):
        try:
            f = open("settings.json", "r")
        except:
            self.last_block = 0
            return
        settings = json.loads(f.read())
        if "last_block" in settings:
            if self.chain in settings["last_block"]:
                self.last_block = settings["last_block"][self.chain]
                return
        self.last_block = 0
        
    def dump_settings(self):
        try:
            f = open("settings.json", "r")
            settings = json.loads(f.read())
            if not "last_block" in settings:
                settings["last_block"] = {self.chain:self.last_block}
            else:
                settings["last_block"][self.chain] = self.last_block
            f.close()
        except:
            settings = {"last_block":{self.chain:self.last_block}}
        f = open("settings.json", "w")
        f.write(json.dumps(settings, indent=4))
        f.close()
            
    def dump(self):
        f = open("txdata/" + self.chain + "-balances.pickle", "wb")
        pickle.dump(self.balances, f)
        
    def dump_txindex(self):
        prefixes = gen_prefix(PREFIX_SIZE)
        for p in prefixes:
            p_keys = [txid for txid in self.txindex.keys() if txid.startswith(p)]
            try:
                f = open("txdata/" + self.chain + "-" + p + "-txindex.pickle", "rb")
                txindex_p = pickle.load(f)
                f.close()
            except:
                txindex_p = {}
            for k in p_keys:
                txindex_p[k] = self.txindex[k]
            f = open("txdata/" + self.chain + "-" + p + "-txindex.pickle", "wb")
            pickle.dump(txindex_p, f)
            f.close()
        
    def scan_all(self, start=None, end=None):
        self.load_settings()
        self.txindex = {}
        if start is None:
            start = self.last_block + 1
        block_generator = self.blockchain.get_ordered_blocks(os.path.expanduser(self.chainpath + "/index"), start=start, end=end)
            
        stop = start
        print (stop)
        unresolved = []
        txcount = 0
        print (start, stop, end)
        for block in block_generator:
            self.last_block = block.height
            stop = stop + 1
            if not (end is None) and (stop > end):
                break
            #print block
            if stop % 1000 == 0:
                print (stop)
            for transaction in block.transactions:
                self.txindex[transaction.hash] = {}
                output_i = 0
                for output in transaction.outputs:
                    self.txindex[transaction.hash][output_i] = [output.value, [], "u", block.height]
                    txcount += 1
                    for address in output.addresses:
                        addr = address.get_address(version_bytes=chain_const[self.chain]["vb"])
                        self.txindex[transaction.hash][output_i][1].append(addr)
                        if not addr in self.balances:
                            self.balances[addr] = output.value
                        else:
                            self.balances[addr] += output.value
                    output_i += 1
                for inp in transaction.inputs:
                    if inp.transaction_hash.replace("0", "") == "":
                        continue
                    try:
                        tx = self.txindex[inp.transaction_hash][inp.transaction_index]
                        for address in tx[1]:
                            if not address in self.balances:
                                self.balances[address] = -tx[0]
                            else:
                                self.balances[address] -= tx[0]
                        self.txindex[inp.transaction_hash][inp.transaction_index][2] = "s"
                    except:
                        unresolved.append([inp.transaction_hash, inp.transaction_index])
            if txcount > 100000:
                self.dump_txindex()
                self.txindex = {}
                txcount = 0
        self.dump_txindex()
        prefixes = gen_prefix(PREFIX_SIZE)
        for p in prefixes:
            p_unresolved = [txd for txd in unresolved if txd[0].startswith(p)]
            f = open("txdata/" + self.chain + "-" + p + "-txindex.pickle", "rb")
            self.txindex = pickle.load(f)
            f.close()
            for txd in p_unresolved:
                try:
                    tx = self.txindex[txd[0]][txd[1]]
                    for address in tx[1]:
                        if not address in self.balances:
                            self.balances[address] = -tx[0]
                        else:
                            self.balances[address] -= tx[0]
                    self.txindex[txd[0]][txd[1]][2] = "s"
                except:
                    pass
            f = open("txdata/" + self.chain + "-" + p + "-txindex.pickle", "wb")
            pickle.dump(self.txindex, f)
            f.close()
        self.dump()
        self.dump_settings()
        self.blockchain.dump_indexes("txdata/" + self.chain + "-index-cache.txt")
        del self.txindex
        self.txindex = {}
        
    def get_balance(self, address):
        if address in self.balances:
            return self.balances[address] / 100000000.0
        else:
            return "Unknown address"
            
    def get_utxos(self, address):
        prefixes = gen_prefix(PREFIX_SIZE)
        result = []
        self.blockchain.load_indexes(os.path.expanduser(self.chainpath + "/index"), cache="txdata/" + self.chain + "-index-cache.txt")
        for p in prefixes:
            f = open("txdata/" + self.chain + "-" + p + "-txindex.pickle", "rb")
            txindex = pickle.load(f)
            f.close()
            for txhash in txindex.keys():
                for vout in txindex[txhash].keys():
                    tx = txindex[txhash][vout]
                    if address in tx[1]:
                        if tx[2] == "u":
                            block = self.blockchain.load_block(tx[3])
                            result.append({"txhash": txhash, "vout": vout, "value": tx[0], "block_number": tx[3], "block_hash": block.hash})
        return sorted(result, key=lambda x:x["block_number"]) 
            
if __name__ == "__main__":
    f = open("xrmbalance.ini", "r")
    config = json.loads(f.read())
    plugins = {}
    for coin in config.keys():
        plugins[coin] = BalancePlugin(coin, config[coin])
        
    if len(sys.argv) < 3:
        print("Not enough parameters")
        sys.exit(0)
    chain = sys.argv[1]
    if not chain in plugins:
        print("This chain is not available yet")
        sys.exit(0)
    command = sys.argv[2]
    p = plugins[chain]
    if command == "scan":
        p.scan_all()
    elif command == "getbalance":
        if len(sys.argv) < 4:
            print("Address not specified")
            sys.exit(0)
        else:
            addr = sys.argv[3]
            print(p.get_balance(addr))
    elif command == "getutxos":
        if len(sys.argv) < 4:
            print("Address not specified")
            sys.exit(0)
        else:
            addr = sys.argv[3]
            res = p.get_utxos(addr)
            for v in res:
                print(v)
            bal = sum(x["value"] for x in res) / 100000000.0
            print (bal)
    #print(len(list(p.balances.keys())))
    #print(p.balances['xyLmRZxgDhnHq9xbCtV6HQQLNCDMxzJKbz'] / 100000000.0)
    '''for k in p.balances:
        if p.balances[k] > 1000000000000:
            print (k, p.balances[k] / 100000000.0)'''

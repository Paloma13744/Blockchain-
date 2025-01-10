import hashlib
import json
from time import time

class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

        # Criação do bloco Genesis
        self.new_block(previous_hash='1', proof=100)

    def new_block(self, proof, previous_hash=None):
        """Cria um novo bloco e o adiciona à cadeia."""
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.current_transactions = []  # Redefine as transações atuais
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """Cria uma nova transação que será incluída no próximo bloco minerado."""
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """Gera o hash de um bloco."""
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        """Retorna o último bloco da cadeia."""
        return self.chain[-1]

    def proof_of_work(self, last_block):
        """Realiza a prova de trabalho para encontrar um proof válido."""
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)
        proof = 0
        while not self.valid_proof(last_proof, proof, last_hash):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """Valida o proof resolvendo o problema do hash."""
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def valid_chain(self, chain):
        """Verifica se a cadeia recebida é válida."""
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # Verifique se o hash do bloco está correto
            if block['previous_hash'] != self.hash(last_block):
                return False
            # Verifique se a Prova de Trabalho é válida
            if not self.valid_proof(last_block['proof'], block['proof'], self.hash(last_block)):
                return False
            last_block = block
            current_index += 1
        return True

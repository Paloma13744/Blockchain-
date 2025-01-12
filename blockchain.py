from flask import Flask, jsonify, request
from uuid import uuid4
import hashlib
import json
from time import time


class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

        # Criação do bloco Gênesis
        self.new_block(previous_hash='1', proof=100)
        
        

    def new_block(self, proof, previous_hash=None): # Cria um novo bloco e adiciona à cadeia
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
    

    def new_transaction(self, sender, recipient, amount): # cria uma nova transação e a adiciona à lista de transações atuais
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1
    

    @staticmethod  # Gera o hash de um bloco usando o algoritmo SHA-256.
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):  # Retorna o último bloco da cadeia.
        return self.chain[-1]
    
 
    def proof_of_work(self, last_block):  # O método que realiza o processo de prova de trabalho
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)
        proof = 0
        while not self.valid_proof(last_proof, proof, last_hash):
            proof += 1
        return proof


    @staticmethod
    def valid_proof(last_proof, proof, last_hash):    # Verifica se o hash gerado pela combinação do last_proof, proof e last_hash começa com "0000", o que indica que o proof é válido.
        """Valida o proof resolvendo o problema do hash."""
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
    
    

    def valid_chain(self, chain):  # Verifica se a cadeia recebida é válida.
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



   # Definição das rotas
    app = Flask(__name__)
    node_identifier = str(uuid4()).replace(
        '-', '')  # Identificador único para o nó
    blockchain = Blockchain()


    @app.route('/mine', methods=['GET'])
    def mine():
        # Obter o último bloco da cadeia
        last_block = blockchain.last_block
        # Encontrar a prova de trabalho para o último bloco
        proof = blockchain.proof_of_work(last_block)

        # Adiciona uma transação especial para premiar o minerador
        blockchain.new_transaction(
            sender="0",  
            recipient=node_identifier,  # Recompensa vai para o nó que minerou
            amount=1,
        )

        # Cria um novo bloco e adiciona à cadeia
        block = blockchain.new_block(proof)

        # Retorna a resposta com detalhes do novo bloco minerado
        response = {
            'message': "Novo bloco minerado com sucesso!",
            'index': block['index'],
            'transactions': block['transactions'],
            'proof': block['proof'],
            'previous_hash': block['previous_hash'],
        }
        return jsonify(response), 200


    def new_transaction(self, sender, recipient, amount):
            """Cria uma nova transação que será incluída no próximo bloco minerado."""
            self.current_transactions.append({
                'sender': sender,
                'recipient': recipient,
                'amount': amount,
            })
            return self.last_block['index'] + 1

    @app.route('/chain', methods=['GET'])
    def full_chain():
        # Retorna toda a cadeia de blocos e o comprimento da cadeia
        response = {
            'chain': blockchain.chain,
            'length': len(blockchain.chain),
        }
        return jsonify(response), 200


    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000)

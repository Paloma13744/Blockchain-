from flask import Flask, jsonify, request
from uuid import uuid4
import hashlib
import json
from time import time
from urllib.parse import urlparse
import requests

class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

        # Criação do bloco Gênesis
        self.new_block(previous_hash='1', proof=100)

    def new_block(self, proof, previous_hash=None):  # Cria um novo bloco e adiciona à cadeia
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

    # Cria uma nova transação e a adiciona à lista de transações atuais
    def new_transaction(self, sender, recipient, amount):
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

    # O método que realiza o processo de prova de trabalho
    def proof_of_work(self, last_block):
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)
        proof = 0
        while not self.valid_proof(last_proof, proof, last_hash):
            proof += 1
        return proof

    @staticmethod
    # Verifica se o hash gerado pela combinação do last_proof, proof e last_hash começa com "0000", o que indica que o proof é válido.
    def valid_proof(last_proof, proof, last_hash):
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

    def resolve_conflicts(self):
        """
        Este é o nosso algoritmo de consenso, ele resolve conflitos
        substituindo nossa cadeia pela mais longa na rede.

        :return: <bool> True se nossa cadeia foi substituída, False se não.
        """
        neighbours = self.nodes
        new_chain = None

        # Estamos apenas procurando por cadeias mais longas que a nossa
        max_length = len(self.chain)

        # Pegamos e verificamos as cadeias de todos os nós na nossa rede
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Verifique se o comprimento é maior e se a cadeia é válida
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Substituímos nossa cadeia se descobrirmos uma nova cadeia válida e mais longa que a nossa
        if new_chain:
            self.chain = new_chain
            return True

        return False


    def register_node(self, address):
        """
        Adiciona um novo nó à lista de nós.

        :param address: Endereço do nó. Exemplo: 'http://192.168.0.5:5000'
        """
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('URL inválido')


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


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Valores ausentes', 400

    # Cria uma nova transação
    index = blockchain.new_transaction(
        values['sender'], values['recipient'], values['amount'])

    response = {'message': f'A transação será adicionada ao bloco {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    # Retorna toda a cadeia de blocos e o comprimento da cadeia
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Erro: Por favor, forneça uma lista válida de nós", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'Novos nós foram adicionados',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201



@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Nossa cadeia foi substituída',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Nossa cadeia é autoritária',
            'chain': blockchain.chain
        }

    return jsonify(response), 200



if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000,
                        type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)

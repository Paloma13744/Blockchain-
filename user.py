import requests
import json
from blockchain import Blockchain  


# Exemplo de criação(transação)
new_transaction = {
    'sender': 'Alice',
    'recipient': 'Bob',
    'amount': 5,
}

response = requests.post('http://localhost:5000/transactions/new', json=new_transaction)
print(response.json())
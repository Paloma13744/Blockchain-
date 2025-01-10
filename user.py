import requests

# Cria uma nova transação
new_transaction = { 
    'sender': 'Alice',
    'recipient': 'Bob',
    'amount': 5,
}

# Envia a transação para o servidor
response = requests.post('http://127.0.0.1:5000/transactions/new', json=new_transaction)

# Imprime a resposta do servidor
if response.status_code == 200:
    print(response.json())
else:
    print(f"Erro: {response.status_code}, {response.text}")
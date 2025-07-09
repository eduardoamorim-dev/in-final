# Classificador de Churn Bancário

Este projeto implementa um classificador de churn bancário que utiliza um modelo de árvore de decisão treinado previamente e salvo em formato PMML.

## Estrutura do Projeto

```
churn-classifier/
├── app.py                 # Backend Flask
├── templates/
│   └── index.html        # Frontend HTML
├── paste.txt             # Arquivo PMML com o modelo treinado
├── requirements.txt      # Dependências do projeto
└── README.md            # Este arquivo
```

## Configuração do Ambiente

### 1. Instalar Python
Certifique-se de ter Python 3.7+ instalado em seu sistema.

### 2. Criar ambiente virtual (recomendado)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Colocar o arquivo PMML
Certifique-se de que o arquivo `paste.txt` (contendo o modelo PMML) está na raiz do projeto.

## Executar o Projeto

### 1. Iniciar o servidor Flask
```bash
python app.py
```

### 2. Acessar a aplicação
Abra seu navegador e acesse: `http://localhost:5000`

## Como Usar

### Dados de Entrada
O formulário solicita os seguintes dados do cliente:

- **Credit Score**: Pontuação de crédito (350-850)
- **Geography**: Localização geográfica (France, Spain, Germany)
- **Gender**: Gênero (Female, Male)
- **Age**: Idade (18-92 anos)
- **Balance**: Saldo da conta (0-251.000)
- **Number of Products**: Número de produtos (1-4)
- **Is Active Member**: Cliente ativo (0=Não, 1=Sim)

### Resultado
O sistema retorna uma das seguintes classificações:
- **YES**: Cliente fará churn (sairá do banco)
- **NO**: Cliente NÃO fará churn (permanecerá no banco)

## API Endpoints

### POST /predict
Endpoint para fazer predições via API.

**Payload:**
```json
{
    "CreditScore": 600,
    "Geography": "France",
    "Gender": "Male",
    "Age": 35,
    "Balance": 50000.0,
    "NumOfProducts": 2,
    "IsActiveMember": 1
}
```

**Resposta:**
```json
{
    "prediction": "no",
    "message": "Cliente NÃO fez churn (permaneceu no banco)",
    "input_data": {
        "CreditScore": 600,
        "Geography": "France",
        "Gender": "Male",
        "Age": 35,
        "Balance": 50000.0,
        "NumOfProducts": 2,
        "IsActiveMember": 1
    }
}
```

## Normalização dos Dados

O modelo foi treinado com dados normalizados. O sistema automaticamente converte os valores de entrada para o formato esperado:

- **CreditScore**: (valor - 350) / (850 - 350)
- **Geography**: France=0, Spain=1, Germany=2 → dividido por 2
- **Gender**: Female=0, Male=1 → dividido por 1
- **Age**: (valor - 18) / (92 - 18)
- **Balance**: valor / 251000
- **NumOfProducts**: (valor - 1) / (4 - 1)
- **IsActiveMember**: valor / 1 (já normalizado)

## Validação de Dados

O sistema valida automaticamente:
- Tipos de dados corretos
- Valores dentro dos intervalos permitidos
- Presença de todos os campos obrigatórios

## Tecnologias Utilizadas

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **Modelo**: Árvore de Decisão (formato PMML)
- **Parsing XML**: xml.etree.ElementTree

## Troubleshooting

### Erro: "TreeModel não encontrado no PMML"
- Verifique se o arquivo `paste.txt` está na raiz do projeto
- Certifique-se de que o arquivo contém um modelo PMML válido

### Erro: "Campos obrigatórios ausentes"
- Verifique se todos os campos do formulário estão preenchidos
- Certifique-se de que os nomes dos campos correspondem aos esperados

### Erro: "Valores fora do intervalo"
- Verifique se os valores estão dentro dos intervalos permitidos
- Consulte a documentação dos campos para os limites corretos

## Exemplo de Uso via cURL

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "CreditScore": 600,
    "Geography": "France",
    "Gender": "Male",
    "Age": 35,
    "Balance": 50000.0,
    "NumOfProducts": 2,
    "IsActiveMember": 1
  }'
```

## Melhorias Futuras

- Adicionar logging para rastreamento de predições
- Implementar cache para melhorar performance
- Adicionar métricas de confiança na predição
- Implementar autenticação e autorização
- Adicionar dashboard para análise de dados# in-final

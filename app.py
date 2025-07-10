from flask import Flask, request, jsonify, render_template
import xml.etree.ElementTree as ET
import os
import logging

app = Flask(__name__)

# Configurar logging para debug
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PMMLDecisionTreeClassifier:
    def __init__(self, pmml_file):
        try:
            self.tree = ET.parse(pmml_file)
            self.root = self.tree.getroot()
            self.namespace = {'pmml': 'http://www.dmg.org/PMML-4_2'}
            
            # Verificar se o arquivo é válido
            if not self.validate_pmml():
                raise ValueError("Arquivo PMML inválido ou incompleto")
                
            logger.info(f"PMML carregado com sucesso: {pmml_file}")
            
        except ET.ParseError as e:
            logger.error(f"Erro ao parsear XML: {e}")
            raise ValueError(f"Arquivo PMML inválido: {e}")
        except FileNotFoundError:
            logger.error(f"Arquivo não encontrado: {pmml_file}")
            raise ValueError(f"Arquivo PMML não encontrado: {pmml_file}")
    
    def validate_pmml(self):
        """Valida se o arquivo PMML contém um TreeModel válido"""
        tree_model = self.root.find('.//pmml:TreeModel', self.namespace)
        if tree_model is None:
            logger.error("TreeModel não encontrado no PMML")
            return False
        
        root_node = tree_model.find('./pmml:Node', self.namespace)
        if root_node is None:
            logger.error("Nó raiz não encontrado no TreeModel")
            return False
        
        logger.info("PMML validado com sucesso")
        return True
    
    def get_data_dictionary(self):
        """Extrai informações do DataDictionary para normalização automática"""
        data_dict = {}
        data_dictionary = self.root.find('.//pmml:DataDictionary', self.namespace)
        
        if data_dictionary is not None:
            for data_field in data_dictionary.findall('./pmml:DataField', self.namespace):
                field_name = data_field.get('name')
                data_type = data_field.get('dataType')
                op_type = data_field.get('optype')
                
                # Buscar intervalos para campos contínuos
                intervals = data_field.findall('./pmml:Interval', self.namespace)
                if intervals:
                    for interval in intervals:
                        left_margin = interval.get('leftMargin')
                        right_margin = interval.get('rightMargin')
                        if left_margin and right_margin:
                            data_dict[field_name] = {
                                'type': data_type,
                                'optype': op_type,
                                'min': float(left_margin),
                                'max': float(right_margin)
                            }
                
                # Buscar valores para campos categóricos
                values = data_field.findall('./pmml:Value', self.namespace)
                if values:
                    value_list = [v.get('value') for v in values]
                    data_dict[field_name] = {
                        'type': data_type,
                        'optype': op_type,
                        'values': value_list
                    }
        
        return data_dict
    
    def normalize_input(self, input_data):
        """Normaliza os dados de entrada usando informações do PMML quando disponível"""
        normalized = {}
        data_dict = self.get_data_dictionary()
        
        logger.debug(f"Data dictionary: {data_dict}")
        logger.debug(f"Input data: {input_data}")
        
        # Normalização com fallback para valores padrão
        for field, value in input_data.items():
            if field in data_dict and 'min' in data_dict[field]:
                # Normalização baseada no PMML
                min_val = data_dict[field]['min']
                max_val = data_dict[field]['max']
                normalized[field] = (value - min_val) / (max_val - min_val)
            else:
                # Fallback para normalização manual
                normalized[field] = self.manual_normalize(field, value)
        
        logger.debug(f"Normalized data: {normalized}")
        return normalized
    
    def manual_normalize(self, field, value):
        """Normalização manual como fallback"""
        if field == 'CreditScore':
            return (value - 350) / (850 - 350)
        elif field == 'Geography':
            geography_map = {'France': 0, 'Spain': 1, 'Germany': 2}
            return geography_map.get(value, 0) / 2.0
        elif field == 'Gender':
            gender_map = {'Female': 0, 'Male': 1}
            return gender_map.get(value, 0)
        elif field == 'Age':
            return (value - 18) / (92 - 18)
        elif field == 'Balance':
            return value / 251000.0
        elif field == 'NumOfProducts':
            return (value - 1) / (4 - 1)
        elif field == 'IsActiveMember':
            return value
        else:
            return value
    
    def find_tree_model(self):
        """Encontra o modelo TreeModel no PMML"""
        return self.root.find('.//pmml:TreeModel', self.namespace)
    
    def traverse_tree(self, node, input_data):
        """Percorre a árvore de decisão recursivamente com debug"""
        logger.debug(f"Visiting node with score: {node.get('score')}")
        
        # Procura por nós filhos
        child_nodes = node.findall('./pmml:Node', self.namespace)
        
        # Se não há nós filhos, retorna o score deste nó
        if not child_nodes:
            logger.debug(f"Leaf node reached with score: {node.get('score')}")
            return node.get('score')
        
        # Percorre os nós filhos
        for child in child_nodes:
            # Procura por SimplePredicate
            predicate = child.find('./pmml:SimplePredicate', self.namespace)
            if predicate is not None:
                field = predicate.get('field')
                operator = predicate.get('operator')
                value = float(predicate.get('value'))
                
                logger.debug(f"Evaluating: {field} {operator} {value} (actual: {input_data.get(field)})")
                
                # Avalia a condição
                if self.evaluate_condition(input_data.get(field, 0), operator, value):
                    logger.debug(f"Condition TRUE, following child node")
                    return self.traverse_tree(child, input_data)
                else:
                    logger.debug(f"Condition FALSE, skipping child node")
            
            # Procura por True (condição sempre verdadeira)
            true_elem = child.find('./pmml:True', self.namespace)
            if true_elem is not None:
                logger.debug(f"True condition found, following child node")
                return self.traverse_tree(child, input_data)
        
        # Se nenhuma condição foi satisfeita, retorna o score do nó atual
        logger.debug(f"No condition satisfied, returning current node score: {node.get('score')}")
        return node.get('score')
    
    def evaluate_condition(self, field_value, operator, threshold):
        """Avalia uma condição da árvore de decisão"""
        if field_value is None:
            return False
            
        if operator == 'lessOrEqual':
            return field_value <= threshold
        elif operator == 'greaterThan':
            return field_value > threshold
        elif operator == 'equal':
            return field_value == threshold
        elif operator == 'lessThan':
            return field_value < threshold
        elif operator == 'greaterOrEqual':
            return field_value >= threshold
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False
    
    def predict(self, input_data):
        """Faz a predição para um conjunto de dados"""
        logger.info(f"Making prediction for: {input_data}")
        
        # Normaliza os dados de entrada
        normalized_data = self.normalize_input(input_data)
        
        # Encontra o modelo da árvore
        tree_model = self.find_tree_model()
        if tree_model is None:
            raise ValueError("TreeModel não encontrado no PMML")
        
        # Encontra o nó raiz da árvore
        root_node = tree_model.find('./pmml:Node', self.namespace)
        if root_node is None:
            raise ValueError("Nó raiz não encontrado")
        
        # Percorre a árvore e retorna a predição
        prediction = self.traverse_tree(root_node, normalized_data)
        
        logger.info(f"Prediction result: {prediction}")
        return prediction

# Função para testar se o arquivo PMML existe e é válido
def check_pmml_file():
    pmml_files = ['model.pmml', 'churn_model.pmml', 'tree_model.pmml']
    
    for file in pmml_files:
        if os.path.exists(file):
            try:
                classifier = PMMLDecisionTreeClassifier(file)
                logger.info(f"PMML file {file} loaded successfully")
                return classifier
            except Exception as e:
                logger.error(f"Failed to load {file}: {e}")
    
    # Se não encontrar nenhum arquivo válido, criar um mock para teste
    logger.warning("No valid PMML file found. Creating mock classifier for testing.")
    return create_mock_classifier()

def create_mock_classifier():
    """Cria um classificador mock para teste quando não há arquivo PMML válido"""
    class MockClassifier:
        def predict(self, input_data):
            # Lógica simples de exemplo para teste
            score = 0
            
            # Adicionar peso baseado nos campos
            if input_data.get('CreditScore', 0) < 500:
                score += 2
            if input_data.get('Age', 0) > 50:
                score += 1
            if input_data.get('Balance', 0) == 0:
                score += 2
            if input_data.get('NumOfProducts', 0) == 1:
                score += 1
            if input_data.get('IsActiveMember', 0) == 0:
                score += 2
            
            # Retornar 'yes' para churn se score > 3, senão 'no'
            return 'yes' if score > 3 else 'no'
    
    return MockClassifier()

# Inicializa o classificador
classifier = check_pmml_file()

@app.route('/')
def index():
    """Página inicial com formulário"""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Endpoint para fazer predições"""
    try:
        # Recebe os dados do formulário
        data = request.json
        logger.info(f"Received prediction request: {data}")
        
        # Valida os dados de entrada
        required_fields = ['CreditScore', 'Geography', 'Gender', 'Age', 'Balance', 'NumOfProducts', 'IsActiveMember']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório ausente: {field}'}), 400
        
        # Converte os tipos de dados
        input_data = {
            'CreditScore': int(data['CreditScore']),
            'Geography': data['Geography'],
            'Gender': data['Gender'],
            'Age': int(data['Age']),
            'Balance': float(data['Balance']),
            'NumOfProducts': int(data['NumOfProducts']),
            'IsActiveMember': int(data['IsActiveMember'])
        }
        
        # Validações dos rangos
        if not (350 <= input_data['CreditScore'] <= 850):
            return jsonify({'error': 'CreditScore deve estar entre 350 e 850'}), 400
        
        if input_data['Geography'] not in ['France', 'Spain', 'Germany']:
            return jsonify({'error': 'Geography deve ser France, Spain ou Germany'}), 400
        
        if input_data['Gender'] not in ['Female', 'Male']:
            return jsonify({'error': 'Gender deve ser Female ou Male'}), 400
        
        if not (18 <= input_data['Age'] <= 92):
            return jsonify({'error': 'Age deve estar entre 18 e 92'}), 400
        
        if not (0 <= input_data['Balance'] <= 251000):
            return jsonify({'error': 'Balance deve estar entre 0 e 251000'}), 400
        
        if not (1 <= input_data['NumOfProducts'] <= 4):
            return jsonify({'error': 'NumOfProducts deve estar entre 1 e 4'}), 400
        
        if input_data['IsActiveMember'] not in [0, 1]:
            return jsonify({'error': 'IsActiveMember deve ser 0 ou 1'}), 400
        
        # Faz a predição
        prediction = classifier.predict(input_data)
        
        # Prepara a resposta
        result = {
            'prediction': prediction,
            'message': 'Cliente fez churn (saiu do banco)' if prediction == 'yes' else 'Cliente NÃO fez churn (permaneceu no banco)',
            'input_data': input_data
        }
        
        logger.info(f"Prediction result: {result}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/debug')
def debug():
    """Endpoint para debug do modelo"""
    try:
        if hasattr(classifier, 'root'):
            tree_model = classifier.find_tree_model()
            if tree_model:
                return jsonify({
                    'status': 'PMML loaded successfully',
                    'tree_model_found': True,
                    'data_dictionary': classifier.get_data_dictionary()
                })
        return jsonify({
            'status': 'Mock classifier active',
            'tree_model_found': False
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
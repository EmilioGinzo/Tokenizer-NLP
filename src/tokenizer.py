import re
import json
import os

class TokenData:
    def __init__(self, lexemas, posiciones, patron):
        self.lexemas = lexemas
        self.posiciones = posiciones
        self.patron = patron

tokens = [
    'ARTICULO',
    'SUSTANTIVO',
    'VERBO',
    'ADJETIVO',
    'ADVERBIO',
    'OTROS',
    'ERROR_LX',
]

patterns = {
    'ARTICULO': re.compile(r'\b(el|la|los|las|un|una|unos|unas)\b', re.IGNORECASE),
    'SUSTANTIVO': re.compile(r'\b(perro)\b'),  # Define el patrón correspondiente
    'VERBO': re.compile(r'\b(corre|come)\b'),       # Define el patrón correspondiente
    'ADJETIVO': re.compile(r'\b(chico)\b'),    # Define el patrón correspondiente
    'ADVERBIO': re.compile(r'\b(\w+mente)\b'),
    'OTROS': re.compile(r'\b\d+([.,]\d+)?\b'),       # Define el patrón correspondiente
    'ERROR_LX': re.compile(r'[^a-zA-Z0-9\s]+'),  # Captura cualquier secuencia de caracteres que no sean alfanuméricos o espacios
}

tokens_dict = {token: TokenData([], [], patterns[token]) for token in tokens}

def load_classified_lexemes(filename='data/dictionary_entry.json'):  # Asegúrate de que la ruta predeterminada sea correcta
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
            if content:  # Verifica si el contenido no está vacío
                try:
                    data = json.loads(content)
                    # Repoblar tokens_dict con los datos del JSON
                    for token, details in data.items():
                        lexemas = details['lexemas']
                        posiciones = details['posiciones']
                        patron = re.compile(details['patron'], re.IGNORECASE)
                        tokens_dict[token] = TokenData(lexemas, posiciones, patron)
                    return tokens_dict
                except json.JSONDecodeError as e:
                    print(f"Error al decodificar JSON en el archivo {filename}: {e}")
                    return {}  # Retorna un diccionario vacío si hay un error de decodificación
            else:
                print(f"El archivo {filename} está vacío.")
                return {}  # Retorna un diccionario vacío si el archivo está vacío
    else:
        print(f"No se encontró el archivo {filename}.")
        return {}  # Retorna un diccionario vacío si el archivo no existe

def get_lexemes(text):
    lexemes = re.findall(r'\b\w+\b', text.lower())
    return lexemes

def tokenize(lexeme):
    for token, pattern in patterns.items():
        if re.match(pattern, lexeme):
            return token
    return 'ERROR_LX'

def classify_lexeme(lexeme):
    for token, data in tokens_dict.items():
        if data.patron.match(lexeme):
            return data
    return None


def process_file(classify_dict, file_path, entry_number):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    lexemes = get_lexemes(text)

    for i, lexeme in enumerate(lexemes, start=1):
        entry = classify_lexeme(lexeme)
        position_label = f'TXT{entry_number}-{i}'  # Formato de etiqueta de posición
        if not entry:
            # Obtener contexto: palabras antes y después del lexema no clasificado
            context_range = 2  # Define cuántas palabras antes y después incluir en el contexto
            context_start = max(0, i - context_range - 1)
            context_end = min(len(lexemes), i + context_range)
            context = lexemes[context_start:context_end]
            # Crear una versión del contexto con el lexema resaltado
            highlighted_context = ' '.join(
                [f"\033[1;31m{word}\033[0m" if word == lexeme else word for word in context]
            )
            print(f'No se pudo clasificar el lexema "{lexeme}" en el contexto "{highlighted_context}". Por favor, ingrese el número correspondiente al token:')
            for idx, token_name in enumerate(tokens, start=1):
                print(f'{idx}. {token_name}')
            while True:
                try:
                    token_choice = int(input('Ingrese el número del token: '))
                    if 1 <= token_choice <= len(tokens):
                        selected_token = tokens[token_choice - 1]
                        print(f'Token: {selected_token} seleccionado')
                        # Agregar el lexema al patrón existente
                        existing_pattern = classify_dict[selected_token].patron.pattern
                        # Asegurarse de que el patrón se maneje correctamente
                        if existing_pattern.endswith('\\b'):
                            existing_pattern = existing_pattern[:-2]  # Remove the boundary marker
                        new_pattern = f'\\b({existing_pattern}|{lexeme})\\b'  # Recompilar el patrón con el nuevo lexema
                        
                        classify_dict[selected_token].patron = re.compile(new_pattern, re.IGNORECASE)  # Corrected line
                        classify_dict[selected_token].lexemas.append(lexeme)
                        classify_dict[selected_token].posiciones.append(position_label)  # Agregar la etiqueta de posición
                        break
                    else:
                        print('Número fuera de rango. Intente de nuevo.')
                except ValueError:
                    print('Entrada inválida. Por favor, ingrese un número.')
        else:
            # Correctly append the lexeme to the lexemas list and position label if it's not already present
            if lexeme not in entry.lexemas:
                entry.lexemas.append(lexeme)
                entry.posiciones.append(position_label)  # Agregar la etiqueta de posición
    
    return classify_dict

def save_to_file(classify_dict, entry_number):
    # Preparar los datos para la serialización
    serializable_dict = {}
    json_file_path = 'data/dictionary_entry.json'  # Modificar la ruta para usar la carpeta 'data'

    # Leer el contenido existente si el archivo ya existe
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r', encoding='utf-8') as file:
            existing_data = json.load(file)
        # Actualizar el diccionario existente con los nuevos datos
        for token, entries in classify_dict.items():
            if token in existing_data:
                existing_data[token]['lexemas'].extend(entries.lexemas)
                existing_data[token]['posiciones'].extend(entries.posiciones)
                # Asegurarse de que no hay duplicados
                existing_data[token]['lexemas'] = list(set(existing_data[token]['lexemas']))
                existing_data[token]['posiciones'] = list(set(existing_data[token]['posiciones']))
            else:
                existing_data[token] = {
                    'lexemas': entries.lexemas,
                    'posiciones': entries.posiciones,
                    'patron': entries.patron.pattern
                }
        serializable_dict = existing_data
    else:
        # Convertir cada patrón a su representación en cadena antes de guardar
        for token, entries in classify_dict.items():
            serializable_dict[token] = {
                'lexemas': entries.lexemas,
                'posiciones': entries.posiciones,
                'patron': entries.patron.pattern
            }

    # Guardar el diccionario serializable en el archivo JSON
    with open(json_file_path, 'w', encoding='utf-8') as file:
        json.dump(serializable_dict, file, ensure_ascii=False, indent=4)
    
    # Guardar los lexemas en un archivo de texto
    with open(f'data/tokens_output_{entry_number}.txt', 'w', encoding='utf-8') as file:
        for token, data in serializable_dict.items():
            file.write(f'{token}: {" ".join(data["lexemas"])}\n')

def get_next_entry_number():
    entry_number_file = 'data/entry_number.txt'  # Modificar la ruta para usar la carpeta 'data'
    if os.path.exists(entry_number_file):
        with open(entry_number_file, 'r', encoding='utf-8') as file:
            entry_number = int(file.read().strip()) + 1
    else:
        entry_number = 1  # Comienza desde 1 si el archivo no existe
    with open(entry_number_file, 'w', encoding='utf-8') as file:
        file.write(str(entry_number))
    return entry_number

def process_and_save(file_path):
    entry_number = get_next_entry_number()
    classify_dict = process_file(tokens_dict, file_path, entry_number)
    save_to_file(classify_dict, entry_number)

load_classified_lexemes()
# Ahora simplemente llama a process_and_save con la ruta del archivo
process_and_save('.\data\input.txt')
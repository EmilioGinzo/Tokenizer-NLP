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
tokens_txt = {token: TokenData([], [], patterns[token]) for token in tokens}

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

def highlight_context(lexemes, index, context_range, target_lexeme):
    """Generates a string with the target lexeme highlighted within its context."""
    context_start = max(0, index - context_range - 1)
    context_end = min(len(lexemes), index + context_range)
    context = lexemes[context_start:context_end]
    return ' '.join([f"\033[1;31m{word}\033[0m" if word == target_lexeme else word for word in context])

def get_token_choice(num_tokens):
    """Prompts the user for a token choice and validates the input."""
    while True:
        try:
            token_choice = int(input('Ingrese el número del token: '))
            if 1 <= token_choice <= num_tokens:
                return token_choice
            else:
                print('Número fuera de rango. Intente de nuevo.')
        except ValueError:
            print('Entrada inválida. Por favor, ingrese un número.')

def update_classify_dict(classify_dict, token_choice, lexeme, position_label):
    """Updates the classification dictionary with the user's choice."""
    selected_token = tokens[token_choice - 1]
    print(f'Token: {selected_token} seleccionado')
    if selected_token != 'OTROS':
        existing_pattern = classify_dict[selected_token].patron.pattern.rstrip(')\\b')
        new_pattern = f'{existing_pattern}|{lexeme})\\b'
    else:
        existing_pattern = classify_dict[selected_token].patron.pattern.rstrip('\\b')
        new_pattern = f'{existing_pattern}|{lexeme}\\b'        
    
    classify_dict[selected_token].patron = re.compile(new_pattern, re.IGNORECASE)
    classify_dict[selected_token].lexemas.append(lexeme)
    classify_dict[selected_token].posiciones.append(position_label)

def update_entry(entry, lexeme, position_label):
    """Updates the entry with new lexeme and position if not already present."""
    if lexeme not in entry.lexemas:
        entry.lexemas.append(lexeme)
        entry.posiciones.append(position_label)

def update_output(token_name, lexeme):
    tokens_txt[token_name].lexemas.append(lexeme)

def process_file(classify_txt, classify_dict, file_path, entry_number):
    """Processes the file to classify lexemes and handle unclassified lexemes interactively."""
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    lexemes = get_lexemes(text)
    total_lexemes = len(lexemes)
    unclassified_lexemes = 0

    initial_counts = {token: len(data.lexemas) for token, data in classify_dict.items()}
    new_counts = {token: 0 for token in classify_dict}

    for i, lexeme in enumerate(lexemes, start=1):
        entry = classify_lexeme(lexeme)
        position_label = f'TXT{entry_number}-{i}'
        if not entry:
            unclassified_lexemes += 1
            highlighted_context = highlight_context(lexemes, i, 2, lexeme)
            print(f'No se pudo clasificar el lexema "{lexeme}" en el contexto "{highlighted_context}".')
            print('Por favor, ingrese el número correspondiente al token:')
            for idx, token_name in enumerate(tokens[:-1], start=1):
                print(f'{idx}. {token_name}')
            token_choice = get_token_choice(len(tokens) - 1) # no quiero que se pueda seleccionar error
            update_classify_dict(classify_dict, token_choice, lexeme, position_label)
            token_name = tokens[token_choice - 1]
        else:
            update_entry(entry, lexeme, position_label)
            token_name = [token for token, data in tokens_dict.items() if data == entry][0]
        update_output(token_name, lexeme)

    processed_lexemes = total_lexemes - unclassified_lexemes
    processed_percentage = (processed_lexemes / total_lexemes) * 100
    unclassified_percentage = (unclassified_lexemes / total_lexemes) * 100

    print(f"\nProcesamiento completado:")
    print(f"Total de lexemas: {total_lexemes}")
    print(f"Lexemas procesados: {processed_lexemes} ({processed_percentage:.2f}%)")
    print(f"Lexemas no procesados: {unclassified_lexemes} ({unclassified_percentage:.2f}%)\n")

    for token, initial_count in initial_counts.items():
        total_count = len(classify_dict[token].lexemas)
        print(f"Token: {token}")
        print(f"  Cantidad previa: {initial_count}")
        print(f"  Cantidad nueva: {total_count - initial_count}")
        print(f"  Cantidad total: {total_count}\n")

    return classify_txt, classify_dict

def save_to_file(classify_txt, classify_dict, entry_number):
    # Preparar los datos para la serialización
    serializable_dict = {}
    serializable_txt = {}
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

    # Convertir cada patrón a su representación en cadena antes de guardar
    for token, entries in classify_txt.items():
        serializable_txt[token] = {
            'lexemas': entries.lexemas,
        }
    # Guardar el diccionario serializable en el archivo JSON
    with open(json_file_path, 'w', encoding='utf-8') as file:
        json.dump(serializable_dict, file, ensure_ascii=False, indent=4)
    
    # Guardar los lexemas en un archivo de texto
    with open(f'data/tokens_output_{entry_number}.txt', 'w', encoding='utf-8') as file:
        for token, data in serializable_txt.items():
            file.write(f'{token} -> {" | ".join(data["lexemas"])}\n')

def get_next_entry_number():
    entry_number_file = 'data/entry_number.txt'  # Modificar la ruta para usar la carpeta 'data'
    os.makedirs(os.path.dirname(entry_number_file), exist_ok=True)  # Ensure the directory exists
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
    classify_txt, classify_dict = process_file(tokens_txt, tokens_dict, file_path, entry_number)
    save_to_file(classify_txt, classify_dict, entry_number)

load_classified_lexemes()
# Ahora simplemente llama a process_and_save con la ruta del archivo
process_and_save('data/input.txt')
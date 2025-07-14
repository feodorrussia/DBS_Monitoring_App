from flask import Flask, render_template, request, jsonify
import os
import re
import json

app = Flask(__name__)

# Загрузка настроек
settings_file = 'settings.json'
if os.path.exists(settings_file):
    with open(settings_file, 'r') as f:
        settings = json.load(f)
else:
    settings = {
        'folder_path': '',
        'file_pattern': 'Dref(\\d{5})',
        'file_type': '.SHT',
        'output_folder': '',
        'output_file': 'experiments.txt',
        'metadata_header': 'Default metadata header'
    }


# Сохранение настроек
def save_settings():
    with open(settings_file, 'w') as f:
        json.dump(settings, f)


# Маршрут для главной страницы
@app.route('/')
def index():
    return render_template('index.html', settings=settings)


# Маршрут для сканирования папки
@app.route('/scan', methods=['POST'])
def scan_files():
    try:
        data = request.json
        folder_path = data.get('folder_path', settings['folder_path'])
        regex = data.get('regex', settings['file_pattern'])
        file_type = data.get('file_type', settings['file_type'])

        if not os.path.exists(folder_path):
            return jsonify({'error': 'Directory not found'}), 400

        # Обновление настроек
        settings['folder_path'] = folder_path
        settings['file_pattern'] = regex
        settings['file_type'] = file_type
        save_settings()

        experiments = []
        for filename in os.listdir(folder_path):
            if file_type and not filename.lower().endswith(file_type.lower()):
                continue
            match = re.search(regex, filename)
            if match and match.group(1):  # Извлекаем только группу с номером
                experiment_number = match.group(1)
                experiments.append(experiment_number)

        # Чтение уже сохранённых экспериментов
        output_file_path = os.path.join(settings.get('output_folder', ''),
                                        settings.get('output_file', 'experiments.txt'))
        existing_experiments = set()
        if os.path.exists(output_file_path):
            with open(output_file_path, 'r') as f:
                for line in f:
                    existing_experiments.add(line.strip())

        # Фильтруем только новые эксперименты
        new_experiments = [exp for exp in experiments if exp not in existing_experiments]
        return jsonify({'experiments': new_experiments})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Маршрут для сохранения результатов
@app.route('/save', methods=['POST'])
def save_files():
    try:
        data = request.json
        experiments = data.get('experiments', [])
        output_folder = data.get('output_folder', settings.get('output_folder', ''))
        output_file = data.get('output_file', settings.get('output_file', 'experiments.txt'))
        metadata_header = data.get('metadata_header', settings.get('metadata_header', ''))

        # Обновление настроек
        settings['output_folder'] = output_folder
        settings['output_file'] = output_file
        settings['metadata_header'] = metadata_header
        save_settings()

        # Полный путь к выходному файлу
        output_file_path = os.path.join(output_folder, output_file)

        # Чтение уже сохранённых экспериментов
        existing_experiments = set()
        if os.path.exists(output_file_path):
            with open(output_file_path, 'r') as f:
                for line in f:
                    existing_experiments.add(line.strip())

        # Новые эксперименты для добавления
        new_experiments = [exp for exp in experiments if exp not in existing_experiments]

        # Добавление новых экспериментов в файл
        with open(output_file_path, 'a') as f:
            for exp in new_experiments:
                f.write(f"{exp}\n")

        return jsonify({'message': f'Saved successfully. Added {len(new_experiments)} new experiments.',
                        'new_experiments': new_experiments})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Маршрут для редактирования настроек
@app.route('/settings')
def settings_page():
    return render_template('settings.html', settings=settings)


@app.route('/save_settings', methods=['POST'])
def save_settings_route():
    try:
        new_settings = request.json
        settings.update(new_settings)
        save_settings()
        return jsonify({'message': 'Settings saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, request, jsonify
import os
import re
import json
import sys

from sources.Data_processing import normalise, calc_magnitude, calc_dPhase
from sources.Files_operating import load_sht, save_df_to_txt

if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
else:
    template_folder = 'templates'

app = Flask(__name__, template_folder=template_folder)

ROOT_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))
# print(ROOT_DIR)

os.makedirs(ROOT_DIR + "/info", exist_ok=True)


# Сохранение настроек
def save_settings():
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=4)


# Парсинг метаданных
def meta_parsing(header: str, ch_metadata: dict, is_converted: bool = False) -> str:
    """

    :param header:
    :param ch_metadata:
    :param is_converted:
    :return:
    """
    text = header + "\n"

    if is_converted:
        text += "Header for converted files.\n"
    else:
        text += "Header for proceeded files.\n"
    text += "-" * 20 + "\n"

    if ch_metadata["n_ch"] != 0:
        # TODO parsing channels data
        return text + f"N channels: {ch_metadata['n_ch']}"
    return text + "No channels set"


# TODO make feature to set & select names of setting (templates)
# Загрузка настроек
settings_file = os.path.join(ROOT_DIR, 'info/settings.json')
if os.path.exists(settings_file):
    with open(settings_file, 'r') as f:
        settings = json.load(f)
else:
    settings = {
        "folder_path": "",
        "file_pattern": "Dref(\\d{5})",
        "file_types": [".SHT", ".dat", ".txt", "All files (*.*)"],
        "selected_file_type": ".SHT",
        "output_folder": "",
        "output_folder_txt": "",
        "output_folder_A": "",
        "output_folder_dPh": "",
        "output_file": "experiments.txt",
        "metadata_header": "Default metadata header",
        "channels_metadata": {
            "n_ch": 0,
            "ch_meta": [],
            "default_ch_meta": {
                "ch_name": "ch0",
                "freq": 0,
                "ver_angle": 0,
                "hor_angle": 0,
                "height": 0,
                "i_index": 0,
                "q_index": 0,
            }
        }
    }
    save_settings()


# Главная страница
@app.route('/')
def index():
    return render_template('index.html', settings=settings)


# Сканирование файлов
@app.route('/scan', methods=['POST'])
def scan_files():
    try:
        data = request.json
        folder_path = data.get('folder_path', settings['folder_path'])
        regex = data.get('regex', settings['file_pattern'])
        file_type = data.get('file_type', settings['selected_file_type'])
        output_folder = data.get('output_folder', settings['output_folder'])
        output_file = data.get('output_file', settings['output_file'])

        if not os.path.exists(folder_path):
            return jsonify({'error': 'Input directory not found'}), 400
        if not output_folder:
            output_folder = ROOT_DIR
        elif not os.path.exists(output_folder):
            return jsonify({'error': 'Output directory not found'}), 400

        # Обновление настроек
        settings['folder_path'] = folder_path
        settings['file_pattern'] = regex
        settings['selected_file_type'] = file_type
        settings['output_folder'] = output_folder
        settings['output_file'] = output_file
        save_settings()

        experiments = []
        for filename in os.listdir(folder_path):
            if file_type and 'all' not in file_type.lower() and not filename.lower().endswith(file_type.lower()):
                continue
            match = re.search(regex, filename)
            if match and match.group(1):
                experiment_number = match.group(1)
                experiments.append(experiment_number)

        # Чтение уже сохранённых экспериментов
        output_file_path = os.path.join(settings.get('output_folder', ROOT_DIR),
                                        settings.get('output_file', 'experiments.txt'))
        existing_experiments = set()
        if os.path.exists(output_file_path):
            with open(output_file_path, 'r') as f:
                for line in f:
                    existing_experiments.add(line.strip())

        # Фильтрация новых экспериментов
        new_experiments = [exp for exp in experiments if exp not in existing_experiments]
        return jsonify({'experiments': new_experiments})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Сохранение результатов
@app.route('/save', methods=['POST'])
def save_files():
    try:
        data = request.json
        experiments = data.get('experiments', [])
        output_folder = data.get('output_folder', settings.get('output_folder', ''))
        output_file = data.get('output_file', settings.get('output_file', 'experiments.txt'))

        # Обновление настроек
        settings['output_folder'] = output_folder
        settings['output_file'] = output_file
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

        return jsonify({'message': f'Added {len(new_experiments)} new experiments.'
                                   f'Saved successfully to \n{output_file_path}\n',
                        'new_experiments': new_experiments})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Обработка файлов
@app.route('/proceed', methods=['POST'])
def proceed_files():
    try:
        data = request.json
        experiments = data.get('experiments', [])
        output_folder = data.get('output_folder', settings.get('output_folder', ''))
        output_file = data.get('output_file', settings.get('output_file', 'experiments.txt'))
        output_folder_txt = data.get('output_folder_txt', settings.get('output_folder_txt', ''))
        output_folder_A = data.get('output_folder_A', settings.get('output_folder_A', ''))
        output_folder_dPh = data.get('output_folder_dPh', settings.get('output_folder_dPh', ''))
        metadata_header = data.get('metadata_header', settings.get('metadata_header', ''))

        # Обновление настроек
        settings['output_folder'] = output_folder
        settings['output_file'] = output_file
        settings['output_folder_txt'] = output_folder_txt
        settings['output_folder_A'] = output_folder_A
        settings['output_folder_dPh'] = output_folder_dPh
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
        if not new_experiments:
            new_experiments = experiments

        for file_num in new_experiments:
            filename = settings['file_pattern'].replace("(\\d{" + f"{len(file_num)}" + "})", file_num)
            file_path = os.path.join(settings['folder_path'], filename + settings['selected_file_type'])

            df = load_sht(file_path)
            norm_df = normalise(df)

            save_df_to_txt(df, file_num, settings["output_folder_txt"],
                           meta=meta_parsing(settings['metadata_header'], settings['channels_metadata']))

            magnitude = calc_magnitude(norm_df)
            save_df_to_txt(magnitude, f"{file_num}_A", settings["output_folder_A"],
                           meta=meta_parsing(settings['metadata_header'], settings['channels_metadata']))

            d_phase = calc_dPhase(norm_df)
            save_df_to_txt(d_phase, f"{file_num}_dPh", settings["output_folder_dPh"],
                           meta=meta_parsing(settings['metadata_header'], settings['channels_metadata']))

        # TODO loading bar on page while processing
        # TODO separated processing files (by one)

        return jsonify({'message': f'Proceeded {len(new_experiments)} experiments.\n\n'
                                   f'All files converted successfully to \n{output_folder_txt}\n'
                                   f'Magnitude saved to \n{output_folder_A}\n'
                                   f'Diff of the Phase saved to \n{output_folder_dPh}\n',
                        'new_experiments': new_experiments})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Страница настроек
@app.route('/settings')
def settings_page():
    return render_template('settings.html', settings=settings)


# Сохранение настроек
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

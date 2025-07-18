import copy
import json
import os
import re
import sys

from flask import Flask, render_template, request, jsonify

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

    if ch_metadata["n_ch"] > 0:
        text += f"Channels: {ch_metadata['n_ch']}\n"
        for i, ch in enumerate(ch_metadata["ch_meta"]):
            text += f"\nChannel {ch['ch_name']} (I: {ch['i_index']['value']}, Q: {ch['q_index']['value']}):\n"
            text += f"  {ch['freq']['name']}: {ch['freq']['value']}\n"
            text += f"  {ch['ver_angle']['name']}: {ch['ver_angle']['value']}\n"
            text += f"  {ch['hor_angle']['name']}: {ch['hor_angle']['value']}\n"
            text += f"  {ch['height']['name']}: {ch['height']['value']}\n"
            text += "-" * 20 + "\n" if i < ch_metadata['n_ch'] - 1 else ""
    else:
        text += "No channels configured\n"
    return text


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
                "freq": {"name": "Frequency (GHz)", "value": 0},
                "ver_angle": {"name": "Vertical Angle", "value": 0},
                "hor_angle": {"name": "Horizontal Angle", "value": 0},
                "height": {"name": "Height (cm)", "value": 0},
                "i_index": {"name": "I-index", "value": 0},
                "q_index": {"name": "Q-index", "value": 0},
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
        settings['folder_path'] = folder_path.replace('\\', '/')
        settings['file_pattern'] = regex
        settings['selected_file_type'] = file_type
        settings['output_folder'] = output_folder.replace('\\', '/')
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
        settings['output_folder'] = output_folder.replace('\\', '/')
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


@app.route('/update_n_ch', methods=['POST'])
def update_n_ch():
    try:
        data = request.json
        new_n_ch = data.get('n_ch', 0)
        if new_n_ch < 0:
            return jsonify({'error': 'n_ch cannot be negative'}), 400
        current_n_ch = settings['channels_metadata']['n_ch']
        if new_n_ch > current_n_ch:
            for _ in range(new_n_ch - current_n_ch):
                settings['channels_metadata']['ch_meta'].append(
                    copy.deepcopy(settings['channels_metadata']['default_ch_meta']))
        elif new_n_ch < current_n_ch:
            settings['channels_metadata']['ch_meta'] = settings['channels_metadata']['ch_meta'][:new_n_ch]
        settings['channels_metadata']['n_ch'] = new_n_ch
        save_settings()
        return jsonify({'channels_metadata': settings['channels_metadata']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/update_ch_meta', methods=['POST'])
def update_ch_meta():
    try:
        data = request.json
        index = int(data.get('index', None))
        field = data.get('field', None)
        subfield = data.get('subfield', None)
        value = data.get('value', None)
        if index is None or field is None or value is None:
            return jsonify({'error': 'Missing parameters'}), 400
        if index < 0 or index >= settings['channels_metadata']['n_ch']:
            return jsonify({'error': 'Invalid channel index'}), 400
        ch = settings['channels_metadata']['ch_meta'][index]
        if subfield is None:
            if field in ch:
                ch[field] = value
            else:
                return jsonify({'error': 'Field not found'}), 400
        else:
            if field in ch and subfield in ch[field]:
                ch[field][subfield] = value
            else:
                return jsonify({'error': 'Field or subfield not found'}), 400
        save_settings()
        return jsonify({'message': 'Updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/update_proceed_setting', methods=['POST'])
def update_proceed_setting():
    try:
        data = request.json
        field = data.get('field')
        value = data.get('value')

        field_to_key_dict = {
            "outputFolder_txt": "output_folder_txt",
            "outputFolder_A": "output_folder_A",
            "outputFolder_dPh": "output_folder_dPh",
            "metadataHeader": "metadata_header",
        }

        if field in ['outputFolder_txt', 'outputFolder_A',
                     'outputFolder_dPh']:
            settings[field_to_key_dict[field]] = value.replace('\\', '/')
            save_settings()
            return jsonify({'message': 'Setting updated'})
        elif field == 'metadataHeader':
            settings[field_to_key_dict[field]] = value.replace('\n', '\\n')
            save_settings()
            return jsonify({'message': 'Setting updated'})
        return jsonify({'error': 'Invalid field'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/proceed_experiment', methods=['POST'])
def proceed_experiment():
    try:
        data = request.json
        experiment_num = data.get('experiment_num')
        if not experiment_num:
            return jsonify({'error': 'Missing experiment_num'}), 400

        # Получаем актуальные настройки
        output_folder_txt = settings.get('output_folder_txt', '').replace('\\', '/')
        output_folder_A = settings.get('output_folder_A', '').replace('\\', '/')
        output_folder_dPh = settings.get('output_folder_dPh', '').replace('\\', '/')
        metadata_header = settings.get('metadata_header', '').replace('\\n', '\n')

        settings['output_folder_txt'] = output_folder_txt
        settings['output_folder_A'] = output_folder_A
        settings['output_folder_dPh'] = output_folder_dPh
        save_settings()

        # Формируем путь к файлу
        filename = f"{settings['file_pattern'].replace('(\\d{5})', experiment_num)}{settings['selected_file_type']}"
        file_path = os.path.join(settings['folder_path'], filename)

        # Обработка файла
        df = load_sht(file_path)
        norm_df = normalise(df)

        # Сохранение с метаданными
        save_df_to_txt(df, experiment_num, output_folder_txt,
                       meta=meta_parsing(metadata_header, settings['channels_metadata'], True))

        magnitude = calc_magnitude(norm_df)
        save_df_to_txt(magnitude, f"{experiment_num}_A", output_folder_A,
                       meta=meta_parsing(metadata_header, settings['channels_metadata']))

        d_phase = calc_dPhase(norm_df)
        save_df_to_txt(d_phase, f"{experiment_num}_dPh", output_folder_dPh,
                       meta=meta_parsing(metadata_header, settings['channels_metadata']))

        return jsonify({'message': f'Processed {experiment_num}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Страница настроек
@app.route('/settings')
def settings_page():
    with open(settings_file, 'r') as f:
        settings = json.load(f)
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

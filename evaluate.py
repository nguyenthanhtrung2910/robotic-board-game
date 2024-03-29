import re, os, math
from statistics import mean, stdev

re_ex = 'At t=[0-9]{4} Player . win'
folder_path = 'log_files_for_2x2'


def search_in_files(reg_ex, file):
    with open(file) as f:
        logs = f.read()
        return re.findall(reg_ex, logs)


game_times = []
files = os.listdir(folder_path)
# Iterate through the files
for file_name in files:
    file_path = os.path.join(folder_path, file_name)
    game_times.append(int(search_in_files(re_ex, file_path)[0][5:9]))

print('t={:.2f}\u00B1{:05.2f} \n'.format(
    mean(game_times),
    math.sqrt(1 / len(game_times)) * stdev(game_times)))
for color in ['r', 'b', 'o', 'g', 'y']:
    victory_count = 0
    for file_name in files:
        file_path = os.path.join(folder_path, file_name)
        with open(file_path) as f:
            logs = f.read()
            if re.search('Player ' + color + ' win', logs):
                victory_count += 1
    print('player {} win {} time'.format(color, victory_count))

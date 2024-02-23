import matplotlib.pyplot as plt

game_times = []
with open('game_time_by_number_player.txt', 'r') as f:
    data = f.read().split("\n")
    for data_line in data:
        game_times.append(float(data_line.split(': ')[1]))

fig, ax = plt.subplots()

fruits = [2,3,4,5,6]
bar_colors = ['tab:blue']*5

ax.bar(fruits, game_times, color=bar_colors)
ax.set_xlabel('Number players')
ax.set_ylabel('Mean of game time (100 samples)')
ax.set_title('Game time for 50 required mails when each player have 2 robots')

plt.show()
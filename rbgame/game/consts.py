MAP_COLORS = {
    'w': (255, 255, 255),
    'r': (255, 0, 0),
    'b': (0, 0, 255),
    'gr': (0, 255, 0),
    'y': (255, 255, 0),
    'g': (128, 128, 128),
}
ROBOT_COLORS = {
    'r': '#f44336',
    'o': '#ce7e00',
    'gr': '#8fce00',
    'b': '#2986cc',
    'p': '#6a329f',
    'pi': '#c90076',
}
COLOR2STR = {
    'r': 'Red',
    'b': 'Blue',
    'gr': 'Green',
    'p': 'Purple',
    'pi': 'Pink',
    'o': 'Orange'
}
CELL_SIZE = (48, 48)
CELL_BATTERY_SIZE = (16, 16)
FRAME_PER_STEP = 10
MAXIMUM_ROBOT_BATTERY = 10
BATTERY_UP_PER_CHARGE = 1
BATTERY_PER_STEP = 0.2
PERCENT_BATTERY_TO_CHARGE = 0.4
PERCENT_BATTERY_TO_LEAVE = 0.8
MAXIMUM_STEP_PER_TURN = 6
REWARD_FOR_DROP_OFF_MAIL = 5
REWARD_FOR_PICK_UP_MAIL = 1
# reward agent if it reach blue cell
# it shoulen't be so small in comparsion with reward for dropping off a mail
# otherwise agent don't recognize blue cell and go to there when battery go down
REWARD_FOR_REACHING_BLUE = 1
# small punishment for agent every move so it can complete episode as soon as possible
# but it can't be too small in comparsion with reward for reaching blue cell
# because agent can walk more steps in order to charge more times, but reward is still positive.
DEFAULT_REWARD = -0.1
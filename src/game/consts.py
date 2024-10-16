COLOR2RBG = {
    'w': (255, 255, 255),
    'b': (0, 0, 255),
    'r': (255, 0, 0),
    'y': (255, 255, 0),
    'gr': (0, 255, 0),
    'g': (128, 128, 128),
    'o': (255, 165, 0)
}
COLOR_MAP = {
    'r': 'Red',
    'b': 'Blue',
    'gr': 'Green',
    'y': 'Yellow',
    'o': 'Orange'
}
CELL_SIZE = (48, 48)
CELL_BATTERY_SIZE = (12, 12)
FRAME_PER_STEP = 10
MAXIMUM_ROBOT_BATTERY = 50
BATERRY_UP_PER_STEP = 6
BATTERY_TO_CHARGE = 20
MAXIMUM_STEP_PER_TURN = 6
REWARD_FOR_DROP_OFF_MAIL = 10
REWARD_FOR_PICK_UP_MAIL = 2
#reward agent if it reach blue cell
#it shoulen't be so small in comparsion with reward for dropping off a mail
#otherwise agent don't recognize blue cell and go to there when battery go down
REWARD_FOR_MOVING_TO_BLUE = 3
#small punishment for agent every move so it can complete episode as soon as possible
#but it can't be too small in comparsion with reward for reaching blue cell
#because agent can walk more steps in order to charge more times, but reward is still positive.
DEFAULT_REWARD = -0.3
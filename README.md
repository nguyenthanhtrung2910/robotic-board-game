  
# Robotic Board Game with rendering by Pygame 

## How to run:
### Arguments:
``--color_map``: path for csv color map file. <br/>
``--targte_map``: path for csv target map file. <br/>
``--required_mail``: number requried mails in order to win, it shouldn't more than 5.<br/> 
``--number_robot_per_player``: number robots for each player. <br/>
``--player{number player}_color``: player's color. <br/>
``--player{number player}_type``: player's type. It can be ``'computer'`` or ``'player'``.<br/>
Allowed player's colors: ``r`` : red, ``b`` :blue, ``gr`` :green, ``y`` :yellow, ``w`` : white.<br/>

Game can have less than 5 players.
### Example:
```
python main.py --color_map csv_files/colors_map.csv --target_map csv_files/targets_map.csv --required_mail 100 --number_robot_per_player 3 --player1_color b --player1_type computer --player2_color gr --player2_type computer

```
## Buttons detail:
### Play with below buttons:<br/>
$\uparrow$: Move up. <br/>
$\downarrow$: Move up. <br/>
$\rightarrow$: Move right. <br/>
$\leftarrow$: Move left. <br/>
``F`` : Finish your turn. We also can finish our turn when we haven't moved all robot but we must move all fully charged robots, located in blue cell before finishing our turn.<br/>
When all your robots have done their moves, keyboard is blocked. You must press ``F`` key to finish your turn. <br/>
``1``,``2``,``3``,... : Chose your robot to move.<br/>

Game's process is writen in file ``events.log``. 

## About Computer Algorithm:
Our board changes every step so we need search shortest path to destination for each robot every movement.<br/>
I use A* algorithm for shortest path searching.<br/>
When robot reach its destination,it changes its destination to new destination. <br/>
Robot need to charge if its baterry less than 25 and get ready to go if its battery more than 50. <br/>
But sometimes when too many robots are going to baterry station, they may get stuck. So I consider put baterry stations in center of board. <br/>
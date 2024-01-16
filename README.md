  
# Robotic Board Game with rendering by Pygame 

## How to run:
### Arguments:
``--color_map``: path for csv color map file. <br/>
``--targte_map``: path for csv target map file. <br/>
``--required_mail``: number requried mails in order to win, it shouldn't more than 5.<br/> 
``--number_robot_per_player``: number robots for each player. <br/>
``--player1_color``: first player's color. <br/>
``--player2_color``: second player's color. <br/>
``--player3_color``: third player's color. <br/>
``--player4_color``: fourth player's color. <br/>
``--player5_color``: fiveth player's color. <br/>
Allowed player's colors: ``r`` : red, ``b`` :blue, ``gr`` :green, ``y`` :yellow, ``w`` : white.<br/>
Game can have less than 5 players.
### Example:
```
python main.py --color_map csv_files/colors_map.csv --target_map csv_files/targets_map.csv --required_mail 1 --number_robot_per_player 3 --player1_color r --player2_color gr

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


Pure agent using A* path finding algorithm
==========================================

Our main task is automatic controlling robot to win.
In first look, in order to control robot, we can solve 
subtask that is shortest path finding between two vertices
in graph. This subtask can be solved with 
`Dijkstra's algorithm <https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm>`_, 
`A* <https://en.wikipedia.org/wiki/A*_search_algorithm>`_, or
`D* <https://en.wikipedia.org/wiki/D*>`_. We chose A* because it searches faster 
than Dijkstra's algorithm (A* prioritizes evaluating vertex with smaller heuristic
distance so find out the path faster). D* need some optimization before running and 
continute optimize during running, it's effective for large field when we are 
afraid to re-optimize from scratch at every step. For our case, field is small and we
don't need to worry about that. 

Algorithm for controlling single robot is described below:

.. figure:: ../_static/algorithm_for_auto_play.svg
    :align: center
    :alt: Algorithm for controlling single robot.
    :width: 500

    Algorithm for controlling single robot.

|

.. note::

    \*: A cell is considered blocked if a robot is standing on it and only 
    1 of its neighbors is free. Agent decides that the robot will stand 
    waiting if the destination is occupied. Therefore, if all the 
    neighboring cells of the destination are occupied by waiting robots, 
    the robot at the destination will not be able to exit that cell. 
    All the robots will stop waiting for each other and the game cannot 
    continue. We want to avoid this case.

Higher schema using algorithm for chosing destination, which is described below:

.. figure:: ../_static/algorithm_for_chosing_destination.svg
    :align: center
    :alt: Algorithm for chosing destination.
    :width: 300

    Algorithm for chosing destination.

For more details, please access the :mod:`API reference <rbgame.agent.astar_agent>`.
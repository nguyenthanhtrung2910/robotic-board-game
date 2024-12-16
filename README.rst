.. figure:: docs/source/_static/logo.gif
   :align: center
   :width: 400

|

.. image:: https://img.shields.io/badge/author-Nguyen_Thanh_Trung-blue
   :alt: Static Badge

.. image:: https://img.shields.io/github/license/nguyenthanhtrung2910/robotic-board-game
   :alt: GitHub License

.. image:: https://img.shields.io/pypi/pyversions/rbgame
   :alt: PyPI - Python Version

.. image:: https://badge.fury.io/py/rbgame.svg
   :alt: PyPi package

.. image:: https://img.shields.io/badge/pygame-2.6.1%2B-orange
   :alt: Static Badge

.. image:: https://img.shields.io/badge/tianshou-0.5.1%2B-purple
   :alt: Static Badge

.. image:: https://img.shields.io/pypi/dm/rbgame
   :alt: PyPI - Downloads

.. image:: https://img.shields.io/github/issues/nguyenthanhtrung2910/robotic-board-game
   :alt: GitHub Issues or Pull Requests

|

Overview
========

This library simulates the process of a board game. The goal of the simulation is to predict the game 
process statistics depending on various parameters. From this, we can conclude which parameters are 
desirable to set in order to play effectively in a real game. 

We design a simple board game as an reinforcement learning environment and try to solve this.

For more details, read the documention in `here <https://robotic-board-game.readthedocs.io/en/latest/>`_.

Installation
============

Installation in virtual environment is always recommended:

.. code-block:: console

   python -m venv .venv
   source .venv/bin/activate

Simply install with :code:`pip`:

.. code-block:: console

   pip install rbgame


.. warning::

   If you want to animate the game process with pre-trained models, please follow steps in
   our `documention <https://robotic-board-game.readthedocs.io/en/latest/animation.html>`_.





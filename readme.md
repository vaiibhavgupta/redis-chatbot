<!-- To preview this file, open it in VS Code, and press Ctrl+Shift+V (on Windows/Linux) or Cmd+Shift+V (on Mac).  -->

# Redis PubSub ChatBot

The project is redis-based chatbot that demonstrate pub-sub functionality of redis db.

## Project Motivation

The project is a constituent of DS 5760: No SQL for Modern Data Science Applications that gives hands-on experience with usage of docker and redis with python.

## How to Set Up

1. Download all the files in the folder and navigate to the download location in your local and open a terminal window and follow the following commands. `cd` into the directory

   `cd redis-chatbot`

2. Start the docker container

   `docker-compose up`

3. Login into python bash

   `docker exec -it python-container-miniproject1 bash`

4. Install dependencies

   `pip install -r requirements.txt`

5. Start the Chatbot and follow the commands on screen

   `python chatbot.py`

6. Optional: If you want to interact directly with Redis, execute this in a new terminal

   `docker exec -it redis-container-miniproject1 redis-cli`

## Use of Generative AI

1. `./utils/weather_information.py` - The code to build a functionality to fetch latest weather update for any valid location is being derived from ChatGPT.

2. `./utils/random_facts.py` - The code to build a functionality to fetch a random fact is being dervied from ChatGPT.

# Telegram Bot Projects

A personal portfolio of **Telegram bots written in Python**, created to practice and demonstrate skills in API integration, database management, networking, and error handling.  
This repository serves as a showcase of my progress in backend development and Python programming.

---

## 📋 Table of Contents

- [Goal](#goal)  
- [Projects](#projects)  
- [Technologies & Skills](#technologies--skills)  
- [How to Run](#how-to-run)  
- [Project Structure](#project-structure)  
- [What I Learned](#what-i-learned)  
- [Contacts](#contacts)  

---

## 🎯 Goal

- To build practical Telegram bots and strengthen my understanding of Python.  
- To demonstrate the ability to work with APIs, handle errors, manage user data, and implement secure solutions.  
- To create a portfolio project that reflects not only working results but also clean code and good development practices.  

---

## 🤖 Projects

| Project         | Description                                                                 | Key Features |
|-----------------|-----------------------------------------------------------------------------|--------------|
| **Database Bot** | User registration bot with database support and secure password hashing.    | Data input & validation, SQLite database, hashed password storage |
| **Network Bot**  | Network diagnostic bot that checks website availability and open ports.     | `/check` (website status), `/portscan` commands, error handling |
| **Weather Bot**  | Weather information bot using OpenWeatherMap API.                          | Fetches weather by city name, formatted results, API integration |

---

## 🧰 Technologies & Skills

- **Python** (3.x)  
- **Telegram Bot Frameworks**: `pyTelegramBotAPI`  
- **APIs**: OpenWeatherMap and others  
- **Database**: SQLite (with secure password hashing)  
- **Networking**: `socket`, `ipaddress` modules for diagnostics  
- **Environment variables** with `.env` for secrets  
- **Error handling** and input validation  
- **Version control**: Git, GitHub  

---


## 🚀 How to Run

To run any of the bots, follow these straightforward steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/gloudstoun/telegram-bot-project.git
    cd telegram-bot-project\main
    ```

2.  **Setup the environment:**
    * Create and activate a virtual environment:
        ```bash
        python3 -m venv venv
        source venv/bin/activate    # Linux / MacOS
        venv\Scripts\activate       # Windows
        ```
    * Install required dependencies:
        ```bash
        pip install -r requirements.txt
        ```

3.  **Configuration (Tokens):**
    * Create a file named **`.env`** in the project root.
    * Add your bot tokens and API keys (obtained from BotFather and OpenWeatherMap, respectively):
        ```
        WEATHER_BOT_TOKEN="..."
        DATABASE_BOT_TOKEN="..."
        NETWORK_BOT_TOKEN="..."
        OPENWEATHER_API_KEY="..." # Required for Weather Bot functionality
        ```

4.  **Run the bot:**
    Execute the desired bot's script, for example:
    ```bash
    python weather_bot.py
    ```
    *(Other bots are available via: `database_bot.py` and `network_bot.py`.)*

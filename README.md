Hello and welcome to my Telegram bots portfolio!

This repository is a collection of three projects built with Python to hone my programming skills and explore various technologies. Each bot solves a unique problem and demonstrates my abilities in software development, API integration, and building reliable applications.

⚙️ Technologies and Skills
Python: The primary programming language used throughout the projects.

pyTelegramBotAPI: The framework I confidently use for creating bots.

Data Management:

SQLite: Working with a local database to store user data.

hashlib: Implementing secure password storage through hashing.

API Integration:

requests: Integrating with external APIs, such as OpenWeatherMap.

JSON Parsing: Processing data received from API responses.

Network Programming:

socket: Basic socket programming for port checking.

ipaddress: Validating IP addresses.

Security and Configuration:

python-dotenv: Managing secret keys (tokens and API keys) via environment variables, a key best practice.

Error Handling:

Using try-except blocks to ensure application resilience against network errors, bad requests, and other exceptions.

🚀 Projects
1. Database Bot
A user registration bot that securely stores data in an SQLite database. This project showcases my skills in data security, input validation, and database interaction.

Key Functions: user registration, name uniqueness validation, and password hashing.

2. Network Bot
A network diagnostics bot that can check website availability and scan for open ports. This is an excellent demonstration of my network programming skills and ability to work with low-level protocols (HTTP, TCP).

Key Functions: website status checks (/check), and port scanning (/portscan).

3. Weather Bot
A simple and elegant bot that provides real-time weather information. This project highlights my ability to integrate with external APIs, process data, and present it in a user-friendly format.

Key Functions: fetching weather by city name.

🛠️ How to Run the Projects
Clone the repository: git clone [repository address].

Navigate to the project folder: cd telegram-bots.

Create and activate a virtual environment.

Install the dependencies: pip install -r requirements.txt.

Create a .env file in the root directory and add your tokens:

WEATHER_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN_1"
DATABASE_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN_2"
OPENWEATHER_API_KEY="YOUR_OPENWEATHER_API_KEY"
Run any bot with the command: python bot_name.py.

💬 Contact Information
I am open to new opportunities and projects. Feel free to connect with me via Telegram or email.

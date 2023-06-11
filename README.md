# AChurch - MValls Bot

AChurch - MValls Bot is a Telegram bot that acts as a lambda calculator. It allows you to input λ-calculus expressions and performs reduction steps to simplify them. 
The bot is built using the Python programming language and relies on the python-telegram-bot library.

## Author

Marc Valls Camps (LP12)

## Usage

1. Follow the Installation and Setup instructions below.
2. Start a chat with the AChurch - MValls Bot on Telegram.
3. Send λ-calculus expressions as messages to the bot.
4. The bot will respond with reduction steps and the simplified result.

## Commands

- `/start`: Start the bot and receive a welcome message.
- `/help`: Get information on how to use the bot.
- `/macros`: View the defined macros and their corresponding λ-calculus expressions.
- `/author`: Learn about the author of the bot.

## Example

Input:
(\x.\y.x) (\z.z)

Output:

<div style="background-color: #f2f2f2; border: 1px solid #ccc; padding: 10px;">
    This is a box.
</div>


## Installation and Setup

To run the AChurch - MValls Bot locally, follow these steps:

1. Clone the repository: `git clone git@github.com:mvalls21/AChurch.git`
2. Install the required dependencies: `pip install python-telegram-bot`
3. Create a new Telegram bot and obtain the API token. You can follow the official Telegram Bot documentation for more information.
4. Create a file named `token.txt` in the project root directory and paste your API token into it.
5. Run the bot: `python3 achurch.py`

## Dependencies

- Python 3.7 or higher
- python-telegram-bot

## Implementation details

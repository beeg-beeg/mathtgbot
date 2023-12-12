from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup
from random import randint
import math_bot

kb = [
    ["1 / 7", "2 / 3", "3 / 5"],
    ["4 * 8", "5 / 2"]
]


def started(update, context):
    print("/start called")


def solve(a, op, b):
    solutions = {
        "+": a + b,
        "-": a - b,
        "*": a * b,
        "/": a / b
    }
    return solutions.get(op, f"No such operation `{op}`!")


def give(update, context):
    if len(update.message.text.split()) > 1:
        if not context.user_data.get("guesses"):
            context.user_data["answer"] = randint(1, 10)
            context.user_data["guesses"] = 3
            print(context.user_data["answer"])
        if context.user_data["guesses"] > 0:
            text = int(update.message.text.split()[1])
            context.user_data["guesses"] -= 1
            if text == context.user_data["answer"]:
                update.message.reply_text("Молодец!")
                return
            elif text > context.user_data["answer"]:
                update.message.reply_text(f"Меньше! Осталось {context.user_data['guesses']} попыток!")
            else:
                update.message.reply_text(f"Больше! Осталось {context.user_data['guesses']} попыток!")
            if context.user_data["guesses"] == 0:
                update.message.reply_text(
                    f"Повезет в следующий раз! Загаданное число было {context.user_data['answer']}")
                return
    else:
        update.message.reply_text(f"Формат вызова - /give %число%, не `{update.message.text}`")


def greet(update, context):
    text = update.message.text
    print(text)
    mkb = ReplyKeyboardMarkup(kb)
    a, op, b = text.split()
    update.message.reply_text(solve(int(a), op, int(b)), reply_markup=mkb)


def main():
    bot = Updater(sett.api_key, use_context=True)
    disp = bot.dispatcher
    disp.add_handler(CommandHandler("start", started))
    disp.add_handler(CommandHandler("give", give))
    disp.add_handler(MessageHandler(Filters.text, greet))
    bot.start_polling()
    bot.idle()


if __name__ == "__main__":
    main()

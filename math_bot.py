
import datetime
import random
from random import choice, randint
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import json

TOKEN = "6026789241:AAHI9iG0_Q0qJiFs4Xf9XoWX7hoZcrLEC0c"


# Дополнительные функции для работы с датой и серией
def add_streak(context: CallbackContext):
    current_streak = context.user_data.get('streak', 0)
    last_solved_date = context.user_data.get('last_solved_date', datetime.date.today() - datetime.timedelta(days=1))

    if last_solved_date == datetime.date.today() - datetime.timedelta(days=1):
        # Если последняя решенная задача была вчера, увеличиваем серию
        current_streak += 1
    elif last_solved_date < datetime.date.today() - datetime.timedelta(days=1):
        # Если последний раз решали задачу более чем вчера, начинаем серию заново
        current_streak = 1

    context.user_data['streak'] = current_streak
    context.user_data['last_solved_date'] = datetime.date.today()

def reset_streak_if_needed(context: CallbackContext):
    last_solved_date = context.user_data.get('last_solved_date', datetime.date.today())
    if last_solved_date < datetime.date.today() - datetime.timedelta(days=1):
        # Сброс серии, если с момента решения последней задачи прошло больше одного дня
        context.user_data['streak'] = 0

#Проверка отрицательного числа и его записи
def addpar(n):
    return f"{n}" if n >= 0 else f"({n})"


#Генерация задач
def generate_problem(difficulty):
    if difficulty == 1:
        ops = [["+", "-"]]
        num_range = (-10, 10)
    elif difficulty == 2:
        ops = [["+", "-"], ["*", "/"]]
        num_range = (-50, 50)
    else:
        ops = [["+", "-"], ["*", "/"]]
        num_range = (-100, 100)

    v3 = randint(*num_range)
    v4 = randint(*num_range)
    op3 = choice(ops[0])
    right = eval(f"{v3}{op3}{v4}")
    v1 = right * (randint(-50, 50+right + 100)//right + 1)
    v2 = right * (randint(-50-right-100, 50)//right + 1)
    op1 = choice(ops[0])
    op2 = choice(ops[min(difficulty - 1, 1)])

    problem = f"({addpar(v1)} {op1} {addpar(v2)}) {op2} ({addpar(v3)} {op3} {addpar(v4)})"
    return problem

def generate_text_problem(difficulty):
    difficultyToKey = {
        1 : "easy",
        2 : "mid",
        3 : "hard"
    }
    with open("problems.json", "r") as f:
        problems = json.load(f)[difficultyToKey[difficulty]]
    return choice(problems)

#Сложность
def math_problem(update: Update, context: CallbackContext):
    if context.args:
        try:
            difficulty = int(context.args[0])
            difficulty = min(max(difficulty, 1), 3)
        except ValueError:
            update.message.reply_text("Неверный формат сложности. Используйте число от 1 до 3.")
            return

    problem = generate_problem(difficulty)
    update.message.reply_text(problem)
    context.user_data['type'] = "math"
    context.user_data['problem'] = problem
    context.user_data['answer'] = round(eval(problem))
    context.user_data['total_problems'] = context.user_data.get('total_problems', 0) + 1
    context.user_data['remaining_problems'] = 4
    context.user_data['correct_problems'] = []
    context.user_data['incorrect_problems'] = []

def text_problem(update, context):
    if context.args:
        try:
            difficulty = int(context.args[0])
            difficulty = min(max(difficulty, 1), 3)
        except ValueError:
            update.message.reply_text("Неверный формат сложности. Используйте число от 1 до 3.")
            return
    problem = generate_text_problem(difficulty)
    update.message.reply_text(problem["text"])
    context.user_data['type'] = "text"
    context.user_data['problem'] = problem["text"]
    context.user_data['answer'] = problem["answer"]
    context.user_data['total_problems'] = context.user_data.get('total_problems', 0) + 1
    context.user_data['remaining_problems'] = 4
    context.user_data['correct_problems'] = []
    context.user_data['incorrect_problems'] = []

#Проверка задач
def check_answer(update: Update, context: CallbackContext):
    user_answer = update.message.text.strip()
    correct_answer = context.user_data.get('answer')
    problem = context.user_data.get('problem')

    if correct_answer is not None:
        if str(correct_answer) == user_answer:
            update.message.reply_text("Правильно! Ответ верный.")
            context.user_data['correct_answers'] = context.user_data.get('correct_answers', 0) + 1
            context.user_data['correct_problems'].append(problem)
            add_streak(context)
        else:
            update.message.reply_text(f"Неправильно! Правильный ответ: {correct_answer}")
            context.user_data['incorrect_problems'].append(problem)

        remaining_problems = context.user_data.get('remaining_problems', 0)
        if remaining_problems > 0:
            difficulty = context.user_data.get('difficulty', 1)
            if context.user_data['type'] == "math":
                problem = generate_problem(difficulty)
                update.message.reply_text(problem)
                context.user_data['problem'] = problem
                context.user_data['answer'] = round(eval(problem))
            elif context.user_data['type'] == "text":
                problem = generate_text_problem(difficulty)
                update.message.reply_text(problem["text"])
                context.user_data['problem'] = problem["text"]
                context.user_data['answer'] = problem["answer"]
            context.user_data['remaining_problems'] = remaining_problems - 1
        else:
            correct_problems = "\n".join(context.user_data['correct_problems'])
            incorrect_problems = "\n".join(context.user_data['incorrect_problems'])
            result_message = f"Результаты:\n\nПравильные ответы:\n{correct_problems}\n\nНеправильные ответы:\n{incorrect_problems}\nОцените бота с помощью этой формы: https://forms.gle/osmSwwv6RshLCcsL7\n Спасибо!"
            update.message.reply_text(result_message)
    else:
        update.message.reply_text("Пожалуйста, сначала запросите задачу с помощью команды /problem.")

#Статистика
def stats(update: Update, context: CallbackContext) -> None:
    reset_streak_if_needed(context)
    current_streak = context.user_data.get('streak', 0)
    total_problems = context.user_data.get('total_problems', 0)
    correct_answers = context.user_data.get('correct_answers', 0)
    update.message.reply_text(f"Всего задач: {total_problems}\nПравильных ответов: {correct_answers}\nТекущая серия: {current_streak}")

#СТАРТ
def start(update: Update, context: CallbackContext) -> None:
    reset_streak_if_needed(context)
    user_first_name = update.effective_user.first_name
    welcome_message = f"""Привет, {user_first_name}! Этот бот предоставляет математические задачи для решения. 
Используйте команду /problem, чтобы получить задачу. Удачи!

Уровни сложности:
1 - сложение и вычитание, числа от -10 до 10
2 - сложение, вычитание, умножение и деление, числа от -50 до 50
3 - сложение, вычитание, умножение и деление, числа от -100 до 100

Для выбора уровня сложности, используйте команду /problem с аргументом, например: /problem 2"""
    update.message.reply_text(welcome_message)

#Помощь
def help(update: Update, context: CallbackContext) -> None:
    help_message = (
        "Как использовать этого бота:\n"
        "/start - начать использование бота и получить приветственное сообщение.\n"
        "/problem [сложность] - получить математическую задачу. Вы можете указать уровень сложности (1, 2, или 3).\n"
        "/stats - узнать свою статистику, включая количество решенных задач и длину текущего серии правильных ответов.\n"
        "Просто отправьте ответ на задачу, и бот проверит его.\n"
        "Если у вас есть вопросы или предложения, пожалуйста, обращайтесь к администратору бота."
    )
    update.message.reply_text(help_message)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("problem", math_problem, pass_args=True))
    dp.add_handler(CommandHandler("text_problem", text_problem, pass_args=True))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, check_answer))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()

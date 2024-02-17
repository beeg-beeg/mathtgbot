
import datetime
import random
from random import choice, randint
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import json

TOKEN = ""






# Дополнительные функции для работы с датой и серией
def add_streak(context: CallbackContext):
    current_streak = context.user_data.get('streak', 0)
    context.user_data['streak'] = current_streak + 1
    context.user_data['last_solved_date'] = datetime.date.today().isoformat()  # Сохраняем дату в формате ISO для удобства


def reset_streak_if_needed(context: CallbackContext):
    last_solved_date_str = context.user_data.get('last_solved_date')
    if last_solved_date_str is not None:
        last_solved_date = datetime.datetime.strptime(last_solved_date_str, '%Y-%m-%d').date()
        if (datetime.date.today() - last_solved_date).days > 1:
            context.user_data['streak'] = 0


#Проверка отрицательного числа и его записи
def addpar(n):
    return f"{n}" if n >= 0 else f"({n})"


#Генерация задач
def generate_problem(difficulty):
    if difficulty == 1:
        ops = ["+", "-"]
        num_range = (-10, 10)
    elif difficulty == 2:
        ops = ["+", "-", "*", "/"]
        num_range = (-50, 50)
    else:  # difficulty == 3
        ops = ["+", "-", "*", "/"]
        num_range = (-100, 100)

    # Генерация четырех случайных чисел в заданном диапазоне
    v1, v2, v3, v4 = [randint(*num_range) for _ in range(4)]

    # Выбор двух случайных операций из списка доступных
    op1, op2 = choice(ops), choice(ops)

    # Составление математической задачи
    problem = f"({addpar(v1)} {op1} {addpar(v2)}) {op2} ({addpar(v3)} {op2} {addpar(v4)})"
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
    difficulty = 1  # Устанавливаем сложность по умолчанию
    if context.args:
        try:
            difficulty = int(context.args[0])
            difficulty = min(max(difficulty, 1), 3)
        except ValueError:
            update.message.reply_text("Неверный формат сложности. Используйте число от 1 до 3.")
            return

    problem = generate_problem(difficulty)  # Генерируем одну задачу
    update.message.reply_text(problem)

    # Сохраняем информацию о задаче и сложности
    context.user_data['type'] = "math"
    context.user_data['problem'] = problem
    context.user_data['answer'] = round(eval(problem))
    context.user_data['difficulty'] = difficulty
    context.user_data['total_problems'] = 1
    context.user_data['remaining_problems'] = 4  # Осталось 4 задачи после первой


def text_problem(update, context):
    difficulty = 1
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
    context.user_data['difficulty'] = difficulty
    context.user_data['remaining_problems'] = 4


#Проверка задач
def check_answer(update: Update, context: CallbackContext):
    # Проверяем, были ли инициализированы списки для хранения правильных и неправильных ответов
    if 'correct_problems' not in context.user_data:
        context.user_data['correct_problems'] = []
    if 'incorrect_problems' not in context.user_data:
        context.user_data['incorrect_problems'] = []

    user_answer = update.message.text.strip()
    correct_answer = context.user_data.get('answer')
    problem_type = context.user_data.get('type', 'math')

    # Сброс серии, если необходимо
    reset_streak_if_needed(context)

    if correct_answer is not None:
        if str(correct_answer).lower() == user_answer.lower():
            update.message.reply_text("Правильно! Ответ верный.")
            context.user_data['correct_answers'] = context.user_data.get('correct_answers', 0) + 1
            context.user_data['correct_problems'].append(context.user_data['problem'])
            add_streak(context)  # Увеличиваем серию правильных ответов
        else:
            update.message.reply_text(f"Неправильно! Правильный ответ: {correct_answer}.")
            context.user_data['incorrect_problems'].append(context.user_data['problem'])

        remaining_problems = context.user_data.get('remaining_problems', 0)
        difficulty = context.user_data.get('difficulty', 1)
        if remaining_problems > 0:
            if problem_type == "math":
                new_problem = generate_problem(difficulty)
                update.message.reply_text(new_problem)
                context.user_data['problem'] = new_problem
                context.user_data['answer'] = round(eval(new_problem))
            elif problem_type == "text":
                new_problem = generate_text_problem(difficulty)
                update.message.reply_text(new_problem["text"])
                context.user_data['problem'] = new_problem["text"]
                context.user_data['answer'] = new_problem["answer"]

            context.user_data['remaining_problems'] = remaining_problems - 1
        else:
            # Вывод результатов после решения всех задач
            correct_problems = "\n".join(context.user_data['correct_problems'])
            incorrect_problems = "\n".join(context.user_data['incorrect_problems'])
            result_message = f"Результаты:\n\nПравильные ответы:\n{correct_problems}\n\nНеправильные ответы:\n{incorrect_problems}\nТекущая серия правильных ответов: {context.user_data.get('streak', 0)}"
            update.message.reply_text(result_message)

            # Очищаем данные пользователя для нового набора задач, кроме информации о серии
            context.user_data['total_problems'] = 0
            context.user_data['remaining_problems'] = 0
            context.user_data['correct_problems'] = []
            context.user_data['incorrect_problems'] = []
            context.user_data['correct_answers'] = 0
    else:
        update.message.reply_text("Пожалуйста, сначала запросите задачу с помощью команды /problem или /text_problem.")



def stats(update: Update, context: CallbackContext) -> None:
    reset_streak_if_needed(context)
    current_streak = context.user_data.get('streak', 0)
    total_problems = context.user_data.get('total_problems', 0)
    correct_answers = context.user_data.get('correct_answers', 0)
    update.message.reply_text(f"Всего задач: {total_problems}\nПравильных ответов: {correct_answers}\nТекущая серия: {current_streak}")

#СТАРТ
def start(update: Update, context: CallbackContext) -> None:
    welcome_message = (
        "Привет! Я бот, созданный для помощи в изучении математики.\n"
        "Вот что я могу делать:\n"
        "- Генерировать математические и текстовые задачи различной сложности.\n"
        "- Проверять ваши ответы и вести статистику ваших успехов.\n"
        "- Поддерживать серию правильных ответов, мотивируя вас учиться ежедневно.\n"
        "\nИспользуйте команду /help, чтобы узнать больше о том, как со мной работать.\n"
        "Удачи и приятного обучения!"
    )
    update.message.reply_text(welcome_message)


#Помощь
def help(update: Update, context: CallbackContext) -> None:
    help_message = (
        "Вот как вы можете использовать этого бота:\n"
        "/start - получить приветственное сообщение и краткое руководство по использованию бота.\n"
        "/problem [сложность] - запросить математическую задачу заданной сложности. Доступные уровни сложности: 1 (легко), 2 (средне), 3 (сложно).\n"
        "/text_problem [сложность] - запросить текстовую задачу заданной сложности. Аналогично, доступны уровни сложности 1, 2 и 3.\n"
        "/stats - показать вашу статистику, включая общее количество решенных задач, количество правильных ответов и вашу текущую серию (streak) правильных ответов подряд.\n"
        "\nПросто отправьте ваш ответ на задачу, и бот проверит его. После каждого правильного ответа вы получите следующую задачу той же сложности, пока не решите 5 задач подряд.\n"
        "\nЕсли у вас возникнут вопросы или предложения, пожалуйста, обращайтесь к администратору бота."
    )
    update.message.reply_text(help_message)



def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("stats", stats))
    dp.add_handler(CommandHandler("problem", math_problem, pass_args=True))
    dp.add_handler(CommandHandler("text_problem", text_problem, pass_args=True))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, check_answer))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()

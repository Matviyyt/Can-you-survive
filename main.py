import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Time limit for questions (in seconds)
QUESTION_TIME_LIMIT = 30

# Dictionary to store user scores
user_scores = {}

# Define scenarios
SCENARIOS = {
    "start": {
        "title": "Інтерактивний тест: Ти зможеш вижити?",
        "description": "Вітаємо в симуляторі виживання!\nОбери один зі сценаріїв і спробуй пройти шлях до виживання. Наприкінці отримаєш результат.",
        "options": [
            ("🏜️ Пустеля", "desert_1"),
            ("⛰️ Гори", "mountain_1"),
            ("🌆 Апокаліпсис", "apocalypse_1"),
            ("🌲 Ліс", "forest_1"),
        ],
    },
    "desert_1": {
        "title": "Сценарій: Ти загубився в пустелі",
        "description": "Ти опинився зовсім один посеред безкрайньої розпеченої пустелі. Навколо — тільки пісок, спека і повна невідомість, а вижити можна лише приймаючи правильні рішення.",
        "question": "Крок 1: Що ти робиш першим?",
        "options": [
            ("A) Йдеш в одному напрямку", "desert_1_wrong"),
            ("Б) Ховаєшся в тінь", "desert_2"),
            ("В) Кличеш на допомогу", "desert_1_wrong"),
        ],
        "explanation": "У пустелі головна небезпека – спека й зневоднення. Треба зберігати енергію і чекати вечора."
    },
    "desert_1_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найкраще рішення у пустелі. Спека та зневоднення можуть швидко виснажити твої сили.",
        "options": [
            ("↩️ Спробувати ще раз", "desert_1"),
            ("🏠 До головного меню", "start"),
        ],
    },
    "desert_2": {
        "title": "Добре рішення!",
        "description": "Ти правильно вирішив зберегти енергію.",
        "question": "Крок 2: У тебе є півпляшки води. Як ти її використовуєш?",
        "options": [
            ("A) Випиваєш одразу", "desert_2_wrong"),
            ("Б) П'єш потроху", "desert_3"),
            ("В) Заливаєш на голову", "desert_2_wrong"),
        ],
        "explanation": "Важливо уникати зневоднення, тому потрібно пити розумно."
    },
    "desert_2_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найкраще використання обмеженого запасу води у пустелі.",
        "options": [
            ("↩️ Спробувати ще раз", "desert_2"),
            ("🏠 До головного меню", "start"),
        ],
    },
    "desert_3": {
        "title": "Добре рішення!",
        "description": "Економне використання води допоможе тобі вижити довше.",
        "question": "Крок 3: Уночі дуже холодно. Що робиш?",
        "options": [
            ("A) Палиш все для тепла", "desert_3_wrong"),
            ("Б) Зариваєшся в пісок", "desert_result"),
            ("В) Йдеш далі вночі", "desert_3_wrong"),
        ],
        "explanation": "Зниження температури вночі - типове для пустелі. Тепло тіла треба зберігати."
    },
    "desert_3_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найкраще рішення для виживання холодної ночі у пустелі.",
        "options": [
            ("↩️ Спробувати ще раз", "desert_3"),
            ("🏠 До головного меню", "start"),
        ],
    },
    "desert_result": {
        "title": "Результат: Виживання в пустелі",
        "description": "Вітаємо! Ти набрав 3 бали: вижив, дочекався рятувальників.\n\nТи зробив правильні кроки:\n1. Зберіг енергію, перечекавши спеку в тіні\n2. Раціонально використав обмежені запаси води\n3. Захистився від нічного холоду",
        "options": [
            ("🏠 До головного меню", "start"),
            ("🔄 Пройти ще раз", "desert_1"),
        ],
        "score": 3
    },
    
    # Mountain scenario
    "mountain_1": {
        "title": "Сценарій: Тебе занесло у горах",
        "description": "Ти загубився в горах після снігової бурі. Телефон не ловить, температура — -5°C. Ти одягнений, але без спеціального спорядження.",
        "question": "Крок 1: Що робиш першим?",
        "options": [
            ("A) Спускаєшся в долину", "mountain_1_wrong"),
            ("Б) Робиш укриття", "mountain_2"),
            ("В) Шукаєш сигнал", "mountain_1_wrong"),
        ],
        "explanation": "Спершу потрібно зберегти тепло і захиститися від переохолодження."
    },
    "mountain_1_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найкраще рішення у горах при низькій температурі.",
        "options": [
            ("↩️ Спробувати ще раз", "mountain_1"),
            ("🏠 До головного меню", "start"),
        ],
    },
    "mountain_2": {
        "title": "Добре рішення!",
        "description": "Збереження тепла - пріоритет у холодних горах.",
        "question": "Крок 2: У тебе є батончик і трохи води. Як розподілиш?",
        "options": [
            ("A) Їси й п'єш одразу", "mountain_2_wrong"),
            ("Б) Залишаєш на потім", "mountain_2_wrong"),
            ("В) Їси і п'єш потроху", "mountain_3"),
        ],
        "explanation": "Організм потребує енергії, але різкий сплеск калорій у стресі – погана ідея."
    },
    "mountain_2_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найкраще використання обмежених запасів у горах.",
        "options": [
            ("↩️ Спробувати ще раз", "mountain_2"),
            ("🏠 До головного меню", "start"),
        ],
    },
    "mountain_3": {
        "title": "Добре рішення!",
        "description": "Рівномірне споживання їжі та води допоможе підтримувати енергію.",
        "question": "Крок 3: Ти бачиш ущелину. Що робиш?",
        "options": [
            ("A) Спускаєшся до річки", "mountain_3_wrong"),
            ("Б) Шукаєш інший шлях", "mountain_result"),
            ("В) Залишаєшся на місці", "mountain_3_wrong"),
        ],
        "explanation": "Рельєф у горах небезпечний. Спуск у незнайому ущелину без екіпірування – ризикований."
    },
    "mountain_3_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це небезпечне рішення у гірських умовах.",
        "options": [
            ("↩️ Спробувати ще раз", "mountain_3"),
            ("🏠 До головного меню", "start"),
        ],
    },
    "mountain_result": {
        "title": "Результат: Виживання в горах",
        "description": "Вітаємо! Ти набрав 3 бали: вижив у гірських умовах.\n\nТи зробив правильні кроки:\n1. Зберіг тепло, створивши укриття\n2. Раціонально розподілив запаси їжі та води\n3. Обрав безпечний шлях руху",
        "options": [
            ("🏠 До головного меню", "start"),
            ("🔄 Пройти ще раз", "mountain_1"),
        ],
        "score": 3
    },
    
    # Apocalypse scenario
    "apocalypse_1": {
        "title": "Сценарій: Апокаліпсис без світла",
        "description": "У місті сталася аварія. Немає електрики, зв'язку, паніка. Ти вдома, в тебе стандартні запаси.",
        "question": "Крок 1: Що робиш першим?",
        "options": [
            ("A) Йдеш до магазину", "apocalypse_1_wrong"),
            ("Б) Перевіряєш запаси", "apocalypse_2"),
            ("В) Пишеш друзям", "apocalypse_1_wrong"),
        ],
        "explanation": "У разі надзвичайної ситуації краще уникати натовпу. Оцінка запасів – перший крок."
    },
    "apocalypse_1_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найкраще рішення у ситуації відключення електрики.",
        "options": [
            ("↩️ Спробувати ще раз", "apocalypse_1"),
            ("🏠 До головного меню", "start"),
        ],
    },
    "apocalypse_2": {
        "title": "Добре рішення!",
        "description": "Знати, що в тебе є, допоможе спланувати подальші дії.",
        "question": "Крок 2: У тебе є трохи води. Як дієш?",
        "options": [
            ("A) Вариш воду з крана", "apocalypse_3"),
            ("Б) П'єш запаси", "apocalypse_2_wrong"),
            ("В) П'єш напої", "apocalypse_2_wrong"),
        ],
        "explanation": "Кип'ятіння – базовий спосіб знезараження води. Варто це зробити, поки є газ/тепло."
    },
    "apocalypse_2_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найкраще використання води у надзвичайній ситуації.",
        "options": [
            ("↩️ Спробувати ще раз", "apocalypse_2"),
            ("🏠 До головного меню", "start"),
        ],
    },
    "apocalypse_3": {
        "title": "Добре рішення!",
        "description": "Кип'ятіння знезаражує воду і робить її безпечною для пиття.",
        "question": "Крок 3: Наступна ніч. У квартирі холодно. Твої дії:",
        "options": [
            ("A) Утеплюєш вікна", "apocalypse_result"),
            ("Б) Спиш у ванній", "apocalypse_3_wrong"),
            ("В) Йдеш до друзів", "apocalypse_3_wrong"),
        ],
        "explanation": "Тепло – головне. Можна зробити «печеру з ковдр» і зберегти тепло тіла."
    },
    "apocalypse_3_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найкраще рішення для збереження тепла при відключенні опалення.",
        "options": [
            ("↩️ Спробувати ще раз", "apocalypse_3"),
            ("🏠 До головного меню", "start"),
        ],
    },
    "apocalypse_result": {
        "title": "Результат: Виживання в блекаут",
        "description": "Вітаємо! Ти набрав 3 бали: успішно пережив відключення електрики.\n\nТи зробив правильні кроки:\n1. Оцінив свої запаси перед тим, як діяти\n2. Подбав про запас безпечної питної води\n3. Зберіг тепло в помешканні",
        "options": [
            ("🏠 До головного меню", "start"),
            ("🔄 Пройти ще раз", "apocalypse_1"),
        ],
        "score": 3
    },
    
    # Forest scenario
    "forest_1": {
        "title": "Сценарій: Ти загубився в лісі",
        "description": "Під час прогулянки ти відійшов від групи і загубився. Скоро вечір, у тебе лише легка куртка і півпляшки води.",
        "question": "Крок 1: Що робиш першим?",
        "options": [
            ("A) Продовжуєш рухатись", "forest_1_wrong"),
            ("Б) Визначаєш місце", "forest_2"),
            ("В) Кличеш на допомогу", "forest_1_wrong"),
        ],
        "explanation": "Коли заблукав, важливо зупинитися та зорієнтуватися, щоб не віддалятися ще більше."
    },
    "forest_1_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це може лише погіршити ситуацію в лісі.",
        "options": [
            ("↩️ Спробувати ще раз", "forest_1"),
            ("🏠 До головного меню", "start"),
        ],
    },
    "forest_2": {
        "title": "Добре рішення!",
        "description": "Ти зупинився, щоб не заблукати ще більше.",
        "question": "Крок 2: Наближається ніч. Твої дії:",
        "options": [
            ("A) Шукаєш дорогу", "forest_2_wrong"),
            ("Б) Робиш укриття", "forest_3"),
            ("В) Лізеш на дерево", "forest_2_wrong"),
        ],
        "explanation": "Ночівля в лісі без укриття небезпечна. Важливо зберігати тепло та енергію."
    },
    "forest_2_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найкраще рішення при настанні темряви в лісі.",
        "options": [
            ("↩️ Спробувати ще раз", "forest_2"),
            ("🏠 До головного меню", "start"),
        ],
    },
    "forest_3": {
        "title": "Добре рішення!",
        "description": "Підготовка до ночівлі збереже твої сили та здоров'я.",
        "question": "Крок 3: Вранці ти знайшов струмок. Що робиш?",
        "options": [
            ("A) П'єш воду одразу", "forest_3_wrong"),
            ("Б) Кип'ятиш воду", "forest_result"),
            ("В) Йдеш вздовж струмка", "forest_3_wrong"),
        ],
        "explanation": "Вода з природних джерел може містити небезпечні мікроорганізми. Кип'ятіння - найнадійніший спосіб знезараження."
    },
    "forest_3_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найбезпечніше рішення щодо води в лісі.",
        "options": [
            ("↩️ Спробувати ще раз", "forest_3"),
            ("🏠 До головного меню", "start"),
        ],
    },
    "forest_result": {
        "title": "Результат: Виживання в лісі",
        "description": "Вітаємо! Ти набрав 3 бали: успішно вижив у лісі, дочекався порятунку.\n\nТи зробив правильні кроки:\n1. Зупинився і оцінив ситуацію, не панікуючи\n2. Підготувався до ночівлі, зберігаючи тепло\n3. Безпечно використав знайдену воду",
        "options": [
            ("🏠 До головного меню", "start"),
            ("🔄 Пройти ще раз", "forest_1"),
        ],
        "score": 3
    },
}

# Define scenario names for results display
SCENARIO_NAMES = {
    "desert": "Пустеля",
    "mountain": "Гори",
    "apocalypse": "Апокаліпсис",
    "forest": "Ліс"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send message on `/start`."""
    scenario = SCENARIOS["start"]
    # Use a 2-column layout for better button spacing
    keyboard = []
    row = []
    
    for i, (text, data) in enumerate(scenario["options"]):
        row.append(InlineKeyboardButton(text, callback_data=data))
        if i % 2 == 1 or i == len(scenario["options"]) - 1:
            keyboard.append(row)
            row = []
    
    # Add additional buttons in their own rows
    keyboard.append([InlineKeyboardButton("📊 Результати", callback_data="results")])
    keyboard.append([InlineKeyboardButton("🔄 Скинути прогрес", callback_data="reset")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"*{scenario['title']}*\n\n{scenario['description']}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset progress and start over."""
    user_id = update.effective_user.id
    if user_id in user_scores:
        del user_scores[user_id]
    
    await update.message.reply_text("Твій прогрес скинуто! Почнемо спочатку.")
    await start(update, context)

async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's results for all completed scenarios."""
    user_id = update.effective_user.id
    
    if user_id not in user_scores or not user_scores[user_id]:
        # No results yet
        await update.callback_query.message.reply_text(
            "*Твої результати*\n\nТи ще не пройшов жодного сценарію. Спробуй пройти хоча б один сценарій!",
            parse_mode="Markdown"
        )
        return
    
    results_text = "*Твої результати*\n\n"
    
    for scenario, score in user_scores[user_id].items():
        scenario_name = SCENARIO_NAMES.get(scenario, scenario)
        results_text += f"🎯 *{scenario_name}*: {score}/3 бали\n"
    
    # Add a return to main menu button
    keyboard = [[InlineKeyboardButton("🏠 До головного меню", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.reply_text(
        results_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any message that isn't a command."""
    # Redirect to start command for any text input
    await start(update, context)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    # Initialize user scores if not exists
    if user_id not in user_scores:
        user_scores[user_id] = {}
    
    # Check special callbacks
    if query.data == "reset":
        if user_id in user_scores:
            del user_scores[user_id]
        
        await query.message.reply_text("Твій прогрес скинуто! Почнемо спочатку.")
        scenario = SCENARIOS["start"]
        keyboard = []
        row = []
        
        for i, (text, data) in enumerate(scenario["options"]):
            row.append(InlineKeyboardButton(text, callback_data=data))
            if i % 2 == 1 or i == len(scenario["options"]) - 1:
                keyboard.append(row)
                row = []
        
        keyboard.append([InlineKeyboardButton("📊 Результати", callback_data="results")])
        keyboard.append([InlineKeyboardButton("🔄 Скинути прогрес", callback_data="reset")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            f"*{scenario['title']}*\n\n{scenario['description']}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Check if this is a results request
    if query.data == "results":
        await show_results(update, context)
        return
    
    # Special case for returning to start
    if query.data == "start":
        scenario = SCENARIOS["start"]
        keyboard = []
        row = []
        
        for i, (text, data) in enumerate(scenario["options"]):
            row.append(InlineKeyboardButton(text, callback_data=data))
            if i % 2 == 1 or i == len(scenario["options"]) - 1:
                keyboard.append(row)
                row = []
        
        keyboard.append([InlineKeyboardButton("📊 Результати", callback_data="results")])
        keyboard.append([InlineKeyboardButton("🔄 Скинути прогрес", callback_data="reset")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            f"*{scenario['title']}*\n\n{scenario['description']}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Get scenario from callback data
    scenario_key = query.data
    
    # Verify the scenario exists
    if scenario_key not in SCENARIOS:
        logger.error(f"Невідомий сценарій: {scenario_key}")
        await query.message.reply_text(
            "Вибачте, сталася помилка. Спробуйте знову або почніть з початку за допомогою /start"
        )
        return
    
    scenario = SCENARIOS[scenario_key]
    
    # Check if this is a result scenario to update user scores
    if scenario_key.endswith("_result"):
        # Extract scenario base name (e.g., "desert" from "desert_result")
        scenario_base = scenario_key.split("_")[0]
        # Save the score
        user_scores[user_id][scenario_base] = scenario.get("score", 3)  # Default to 3 if score is not specified
    
    # Create keyboard from options
    keyboard = []
    for text, data in scenario["options"]:
        keyboard.append([InlineKeyboardButton(text, callback_data=data)])
    
    # Add additional buttons
    if not scenario_key.endswith("_wrong"):  # Don't show results button on wrong screens
        keyboard.append([InlineKeyboardButton("📊 Результати", callback_data="results")])
    
    keyboard.append([InlineKeyboardButton("🔄 Скинути прогрес", callback_data="reset")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Format the message based on scenario content
    message_text = f"*{scenario['title']}*\n\n"
    if "description" in scenario:
        message_text += f"{scenario['description']}\n\n"
    if "question" in scenario:
        message_text += f"{scenario['question']}\n\n"
        
        # Add timer information if this is a question (not a wrong or result page)
        if not query.data.endswith("_wrong") and not query.data.endswith("_result"):
            message_text += f"⏱️ *Маєш {QUESTION_TIME_LIMIT} секунд на відповідь*\n\n"
    
    if "explanation" in scenario:
        message_text += f"_Пояснення: {scenario['explanation']}_"
    
    try:
        await query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Помилка при оновленні повідомлення: {e}")
        # Try sending a new message instead
        await query.message.reply_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

# Simplified time-up callback without job handling complexity
async def time_up_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Called when the timer for a question expires."""
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    message_id = job_data["message_id"]
    question = job_data["question"]
    
    # Get the corresponding _wrong destination
    wrong_destination = f"{question}_wrong"
    
    # Check if the wrong destination exists, otherwise go to start
    if wrong_destination not in SCENARIOS:
        wrong_destination = "start"
    
    # Get the wrong scenario
    scenario = SCENARIOS[wrong_destination]
    
    # Create keyboard from options
    keyboard = []
    for text, data in scenario["options"]:
        keyboard.append([InlineKeyboardButton(text, callback_data=data)])
    
    # Add reset button
    keyboard.append([InlineKeyboardButton("🔄 Скинути прогрес", callback_data="reset")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Format the message
    message_text = f"*{scenario['title']}*\n\n"
    message_text += "⏱️ *Час вийшов!* Ти не встиг відповісти вчасно.\n\n"
    if "description" in scenario:
        message_text += f"{scenario['description']}\n\n"
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error sending time up message: {e}")
        # Try to send a new message if edit fails
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except:
            pass

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token("7598948681:AAHcFldyo1IhYlZPfGQ4JROZIRL94EwoUY0").build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()

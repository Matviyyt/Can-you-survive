import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define conversation states
CHOOSING_SCENARIO, ANSWERING_QUESTIONS = range(2)

# Define scenarios data structure
scenarios = {
    "1": {
        "title": "Ти загубився в пустелі",
        "intro": "Ти опинився зовсім один посеред безкрайньої розпеченої пустелі. Навколо тільки пісок, спека і повна невідомість, а вижити можна лише приймаючи правильні рішення.",
        "questions": [
            {
                "question": "Що ти робиш першим?",
                "options": {
                    "a": "Йдеш одразу в одному напрямку, сподіваючись знайти людей.",
                    "б": "Ховаєшся в тінь, щоб перечекати найспекотніший час.",
                    "в": "Кричиш і кличеш на допомогу."
                },
                "correct": "б",
                "explanation": "У пустелі головна небезпека - спека й зневоднення. Треба зберігати енергію і чекати вечора."
            },
            {
                "question": "У тебе є півпляшки води. Як ти її використовуєш?",
                "options": {
                    "a": "Випиваєш одразу - хочеться пити.",
                    "б": "П'єш потроху, ковтками протягом дня.",
                    "в": "Заливаєш на голову, щоб охолонути."
                },
                "correct": "б",
                "explanation": "Важливо уникати зневоднення, тому потрібно пити розумно."
            },
            {
                "question": "Уночі дуже холодно. Що робиш?",
                "options": {
                    "a": "Палиш усе, що маєш, для тепла.",
                    "б": "Зариваєшся в пісок або вкриваєшся одягом.",
                    "в": "Йдеш далі, бо краще йти вночі, ніж удень."
                },
                "correct": "б",
                "explanation": "Зниження температури вночі - типове для пустелі. Тепло тіла треба зберігати."
            }
        ],
        "results": {
            "3": "Вітаємо! Ти вижив, дочекався рятувальників.",
            "2": "Ти отримав переохолодження, але вибрався.",
            "1": "Ти отримав переохолодження, але вибрався.",
            "0": "На жаль, ти помер від холоду чи травм."
        }
    },
    "2": {
        "title": "Тебе занесло у горах",
        "intro": "Ти загубився в горах після снігової бурі. Телефон не ловить, температура -5°С. Ти одягнений, але без спеціального спорядження.",
        "questions": [
            {
                "question": "Що робиш першим?",
                "options": {
                    "a": "Починаєш спускатися в долину, щоб знайти людей.",
                    "б": "Розпалюєш вогонь і робиш укриття.",
                    "в": "Кричиш і намагаєшся знайти мобільний сигнал."
                },
                "correct": "б",
                "explanation": "Спершу потрібно зберегти тепло і захиститися від переохолодження."
            },
            {
                "question": "У тебе є батончик і трохи води. Як розподілиш?",
                "options": {
                    "a": "Їси й п'єш одразу, щоб набратися сил.",
                    "б": "Залишаєш \"на потім\" – можливо, хтось прийде.",
                    "в": "Їси і п'єш малими порціями, рівномірно."
                },
                "correct": "в",
                "explanation": "Організм потребує енергії, але різкий сплеск калорій у стресі – погана ідея."
            },
            {
                "question": "Ти бачиш ущелину. Що робиш?",
                "options": {
                    "a": "Спускаєшся вниз, бо там може бути річка.",
                    "б": "Обходиш, шукаючи безпечніший шлях.",
                    "в": "Залишаєшся на місці."
                },
                "correct": "б",
                "explanation": "Рельєф у горах небезпечний. Спуск у незнайому ущелину без екіпірування ризикований."
            }
        ],
        "results": {
            "3": "Вітаємо! Ти вижив і знайшов допомогу.",
            "2": "Ти вибрався, але отримав обмороження.",
            "1": "Ти вибрався, але отримав обмороження.",
            "0": "На жаль, ти загинув у горах."
        }
    },
    "3": {
        "title": "Апокаліпсис - зникло світло",
        "intro": "У місті сталася аварія. Немає електрики, зв'язку, паніка. Ти вдома, в тебе стандартні запаси.",
        "questions": [
            {
                "question": "Що робиш першим?",
                "options": {
                    "a": "Йдеш до магазину закупитися.",
                    "б": "Перевіряєш, що маєш удома.",
                    "в": "Пишеш у чаті друзям - можливо, хтось щось знає."
                },
                "correct": "б",
                "explanation": "У разі надзвичайної ситуації краще уникати натовпу. Оцінка запасів – перший крок."
            },
            {
                "question": "У тебе є трохи води. Як дієш?",
                "options": {
                    "a": "Вариш воду з крана",
                    "б": "Починаєш пити запаси.",
                    "в": "П'єш напої - колу, сік, щоб зекономити воду."
                },
                "correct": "a",
                "explanation": "Кип'ятіня - базовий спосіб знезараження води. Варто це зробити, поки є газ/тепло."
            },
            {
                "question": "Наступна ніч. У квартирі холодно. Твої дії:",
                "options": {
                    "a": "Обклеюєш вікна, утеплюєш ліжко.",
                    "б": "Спиш у ванній - там менше вікон.",
                    "в": "Ідеш до друзів - у них більше ресурсів."
                },
                "correct": "a",
                "explanation": "Тепло - головне. Можна зробити «печеру з ковдр» і зберегти тепло тіла."
            }
        ],
        "results": {
            "3": "Вітаємо! Ти вижив і зберіг всі ресурси до відновлення комунікацій.",
            "2": "Ти вижив, але втратив частину ресурсів.",
            "1": "Ти вижив, але втратив частину ресурсів.",
            "0": "На жаль, ти не зміг впоратися з ситуацією."
        }
    },
    "4": {
        "title": "Ти загубився в лісі",
        "intro": "Ти відстав від групи під час походу і загубився в глухому лісі. Скоро стемніє, а в тебе лише невеликий рюкзак з базовими речами.",
        "questions": [
            {
                "question": "Що ти робиш перш за все?",
                "options": {
                    "a": "Продовжуєш йти, щоб знайти дорогу.",
                    "б": "Шукаєш високе місце, щоб оглянути місцевість.",
                    "в": "Починаєш будувати укриття, поки є світло."
                },
                "correct": "в",
                "explanation": "Першочергове завдання – забезпечити захист перед ніччю. Без укриття ти вразливий до холоду та вологи."
            },
            {
                "question": "Ти чуєш звук води. Як діятимеш?",
                "options": {
                    "a": "Йдеш до джерела води негайно.",
                    "б": "Закінчуєш укриття, а потім йдеш до води.",
                    "в": "Ігноруєш звук – це може бути небезпечно."
                },
                "correct": "б",
                "explanation": "Вода важлива, але безпека важливіша. Спочатку забезпечуєш базове укриття."
            },
            {
                "question": "Як орієнтуватимешся наступного дня?",
                "options": {
                    "a": "Рухаєшся вниз по схилу – це має привести до цивілізації.",
                    "б": "Вибираєш один напрямок і йдеш прямо.",
                    "в": "Залишаєшся на місці і подаєш сигнали про допомогу."
                },
                "correct": "в",
                "explanation": "Якщо тебе шукають, краще залишатися на місці. Блукання може віддалити від рятувальників і виснажити тебе."
            }
        ],
        "results": {
            "3": "Вітаємо! Ти зробив все правильно і тебе швидко знайшли рятувальники.",
            "2": "Ти вижив, але пережив важкий час у лісі.",
            "1": "Ти вижив, але отримав зневоднення та переохолодження.",
            "0": "На жаль, ти не зміг вижити в лісі."
        }
    }
}

# User data storage (in-memory for simplicity)
user_data_storage = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user to choose a scenario."""
    keyboard = [
        [
            InlineKeyboardButton("1. Ти загубився в пустелі", callback_data="1"),
            InlineKeyboardButton("2. Тебе занесло у горах", callback_data="2"),
        ],
        [
            InlineKeyboardButton("3. Апокаліпсис - зникло світло", callback_data="3"),
            InlineKeyboardButton("4. Ти загубився в лісі", callback_data="4"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Вітаємо в симуляторі виживання! \n\n"
        "Обери один зі сценаріїв і спробуй пройти шлях до виживання. Наприкінці "
        "отримаєш результат.\n\n"
        "Сценарії на вибір:",
        reply_markup=reply_markup
    )
    
    return CHOOSING_SCENARIO

async def choose_scenario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle scenario selection."""
    query = update.callback_query
    await query.answer()
    
    selected_scenario = query.data
    user_id = update.effective_user.id
    
    # Initialize user data
    user_data_storage[user_id] = {
        "scenario": selected_scenario,
        "current_question": 0,
        "score": 0
    }
    
    scenario_data = scenarios[selected_scenario]
    
    # Send scenario introduction
    await query.message.reply_text(f"*{scenario_data['title']}*\n\n{scenario_data['intro']}", parse_mode="Markdown")
    
    # Send the first question
    return await send_question(update, context)

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send the current question to the user."""
    user_id = update.effective_user.id
    user_data = user_data_storage.get(user_id)
    
    if not user_data:
        # If user data is missing, restart the conversation
        await update.callback_query.message.reply_text(
            "Щось пішло не так. Давай почнемо спочатку. Використай /start."
        )
        return ConversationHandler.END
    
    scenario_id = user_data["scenario"]
    question_index = user_data["current_question"]
    
    # Check if all questions have been answered
    if question_index >= len(scenarios[scenario_id]["questions"]):
        return await end_quiz(update, context)
    
    # Get current question data
    question_data = scenarios[scenario_id]["questions"][question_index]
    
    # Create keyboard with options
    keyboard = []
    for key, text in question_data["options"].items():
        keyboard.append([InlineKeyboardButton(f"{key}) {text}", callback_data=key)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Determine if we're replying to a message or a callback query
    if update.callback_query:
        await update.callback_query.message.reply_text(
            f"Крок {question_index + 1}: {question_data['question']}",
            reply_markup=reply_markup
        )
    else:
        # This case should not normally happen here
        await update.message.reply_text(
            f"Крок {question_index + 1}: {question_data['question']}",
            reply_markup=reply_markup
        )
    
    return ANSWERING_QUESTIONS

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's answer to a question."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_data = user_data_storage.get(user_id)
    
    if not user_data:
        await query.message.reply_text(
            "Щось пішло не так. Давай почнемо спочатку. Використай /start."
        )
        return ConversationHandler.END
    
    scenario_id = user_data["scenario"]
    question_index = user_data["current_question"]
    question_data = scenarios[scenario_id]["questions"][question_index]
    
    # Check if the answer is correct
    selected_option = query.data
    correct_option = question_data["correct"]
    
    result_text = f"Твоя відповідь: {selected_option}\n"
    
    if selected_option == correct_option:
        result_text += "✅ Правильно!\n"
        user_data["score"] += 1
    else:
        result_text += f"❌ Неправильно. Правильна відповідь: {correct_option}\n"
    
    result_text += f"\n📝 {question_data['explanation']}"
    
    await query.message.reply_text(result_text)
    
    # Move to the next question
    user_data["current_question"] += 1
    
    # Send the next question or end the quiz
    return await send_question(update, context)

async def end_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End the quiz and show the results."""
    user_id = update.effective_user.id
    user_data = user_data_storage.get(user_id)
    
    if not user_data:
        # Handle the case where user_data is missing
        if update.callback_query:
            await update.callback_query.message.reply_text(
                "Щось пішло не так. Давай почнемо спочатку. Використай /start."
            )
        else:
            await update.message.reply_text(
                "Щось пішло не так. Давай почнемо спочатку. Використай /start."
            )
        return ConversationHandler.END
    
    scenario_id = user_data["scenario"]
    score = user_data["score"]
    
    result = scenarios[scenario_id]["results"][str(score)]
    
    result_message = (
        f"*Результат тесту на виживання:*\n\n"
        f"Сценарій: {scenarios[scenario_id]['title']}\n"
        f"Твій бал: {score}/3\n\n"
        f"{result}\n\n"
        "Щоб спробувати інший сценарій, напиши /start"
    )
    
    # Clean up user data
    if user_id in user_data_storage:
        del user_data_storage[user_id]
    
    if update.callback_query:
        await update.callback_query.message.reply_text(result_message, parse_mode="Markdown")
    else:
        await update.message.reply_text(result_message, parse_mode="Markdown")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    user_id = update.effective_user.id
    
    # Clean up user data
    if user_id in user_data_storage:
        del user_data_storage[user_id]
    
    await update.message.reply_text(
        "Тест скасовано. Щоб почати знову, напиши /start."
    )
    
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("7598948681:AAHcFldyo1IhYlZPfGQ4JROZIRL94EwoUY0").build()
    
    # Set up conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_SCENARIO: [CallbackQueryHandler(choose_scenario)],
            ANSWERING_QUESTIONS: [CallbackQueryHandler(handle_answer)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

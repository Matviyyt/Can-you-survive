import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define scenarios
SCENARIOS = {
    "start": {
        "title": "Інтерактивний тест: Ти зможеш вижити?",
        "description": "Вітаємо в симуляторі виживання!\nОбери один зі сценаріїв і спробуй пройти шлях до виживання. Наприкінці отримаєш результат.",
        "options": [
            ("Ти загубився в пустелі", "desert_1"),
            ("Тебе занесло у горах", "mountain_1"),
            ("Апокаліпсис — зникло світло", "apocalypse_1"),
            ("Ти загубився в лісі", "forest_1"),
        ],
    },
    "desert_1": {
        "title": "Сценарій 1 — Ти загубився в пустелі",
        "description": "Ти опинився зовсім один посеред безкрайньої розпеченої пустелі. Навколо — тільки пісок, спека і повна невідомість, а вижити можна лише приймаючи правильні рішення.",
        "question": "Крок 1: Що ти робиш першим?",
        "options": [
            ("Йдеш одразу в одному напрямку, сподіваючись знайти людей", "desert_1_wrong"),
            ("Ховаєшся в тінь, щоб перечекати найспекотніший час", "desert_2"),
            ("Кричиш і кличеш на допомогу", "desert_1_wrong"),
        ],
        "explanation": "У пустелі головна небезпека – спека й зневоднення. Треба зберігати енергію і чекати вечора."
    },
    "desert_1_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найкраще рішення у пустелі. Спека та зневоднення можуть швидко виснажити твої сили.",
        "options": [
            ("Спробувати ще раз", "desert_1"),
            ("Повернутися до вибору сценарію", "start"),
        ],
    },
    "desert_2": {
        "title": "Добре рішення!",
        "description": "Ти правильно вирішив зберегти енергію.",
        "question": "Крок 2: У тебе є півпляшки води. Як ти її використовуєш?",
        "options": [
            ("Випиваєш одразу – хочеться пити", "desert_2_wrong"),
            ("П'єш потроху, ковтками протягом дня", "desert_3"),
            ("Заливаєш на голову, щоб охолонути", "desert_2_wrong"),
        ],
        "explanation": "Важливо уникати зневоднення, тому потрібно пити розумно."
    },
    "desert_2_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найкраще використання обмеженого запасу води у пустелі.",
        "options": [
            ("Спробувати ще раз", "desert_2"),
            ("Повернутися до вибору сценарію", "start"),
        ],
    },
    "desert_3": {
        "title": "Добре рішення!",
        "description": "Економне використання води допоможе тобі вижити довше.",
        "question": "Крок 3: Уночі дуже холодно. Що робиш?",
        "options": [
            ("Палиш все, що маєш, для тепла", "desert_3_wrong"),
            ("Зариваєшся в пісок або вкриваєшся одягом", "desert_result"),
            ("Йдеш далі, бо краще йти вночі, ніж удень", "desert_3_wrong"),
        ],
        "explanation": "Зниження температури вночі - типове для пустелі. Тепло тіла треба зберігати."
    },
    "desert_3_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найкраще рішення для виживання холодної ночі у пустелі.",
        "options": [
            ("Спробувати ще раз", "desert_3"),
            ("Повернутися до вибору сценарію", "start"),
        ],
    },
    "desert_result": {
        "title": "Результат: Виживання в пустелі",
        "description": "Вітаємо! Ти набрав 3 бали: вижив, дочекався рятувальників.\n\nТи зробив правильні кроки:\n1. Зберіг енергію у спеку\n2. Розумно використав обмежений запас води\n3. Зберіг тепло тіла вночі",
        "options": [
            ("Обрати інший сценарій", "start"),
        ],
    },
    
    # Mountain scenario
    "mountain_1": {
        "title": "Сценарій 2 — Тебе занесло у горах",
        "description": "Ти загубився в горах після снігової бурі. Телефон не ловить, температура — -5°C. Ти одягнений, але без спеціального спорядження.",
        "question": "Крок 1: Що робиш першим?",
        "options": [
            ("Починаєш спускатися в долину, щоб знайти людей", "mountain_1_wrong"),
            ("Розпалюєш вогонь і робиш укриття", "mountain_2"),
            ("Кричиш і намагаєшся знайти мобільний сигнал", "mountain_1_wrong"),
        ],
        "explanation": "Спершу потрібно зберегти тепло і захиститися від переохолодження."
    },
    "mountain_1_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найкраще рішення у горах при низькій температурі.",
        "options": [
            ("Спробувати ще раз", "mountain_1"),
            ("Повернутися до вибору сценарію", "start"),
        ],
    },
    "mountain_2": {
        "title": "Добре рішення!",
        "description": "Збереження тепла - пріоритет у холодних горах.",
        "question": "Крок 2: У тебе є батончик і трохи води. Як розподілиш?",
        "options": [
            ("Їси й п'єш одразу, щоб набратися сил", "mountain_2_wrong"),
            ("Залишаєш \"на потім\" — можливо, хтось прийде", "mountain_2_wrong"),
            ("Їси і п'єш малими порціями, рівномірно", "mountain_3"),
        ],
        "explanation": "Організм потребує енергії, але різкий сплеск калорій у стресі – погана ідея."
    },
    "mountain_2_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найкраще використання обмежених запасів у горах.",
        "options": [
            ("Спробувати ще раз", "mountain_2"),
            ("Повернутися до вибору сценарію", "start"),
        ],
    },
    "mountain_3": {
        "title": "Добре рішення!",
        "description": "Рівномірне споживання їжі та води допоможе підтримувати енергію.",
        "question": "Крок 3: Ти бачиш ущелину. Що робиш?",
        "options": [
            ("Спускаєшся вниз, бо там може бути річка", "mountain_3_wrong"),
            ("Обходиш, шукаючи безпечніший шлях", "mountain_result"),
            ("Залишаєшся на місці", "mountain_3_wrong"),
        ],
        "explanation": "Рельєф у горах небезпечний. Спуск у незнайому ущелину без екіпірування – ризикований."
    },
    "mountain_3_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це небезпечне рішення у гірських умовах.",
        "options": [
            ("Спробувати ще раз", "mountain_3"),
            ("Повернутися до вибору сценарію", "start"),
        ],
    },
    "mountain_result": {
        "title": "Результат: Виживання в горах",
        "description": "Вітаємо! Ти набрав 3 бали: вижив у гірських умовах.\n\nТи зробив правильні кроки:\n1. Зберіг тепло, створивши укриття\n2. Розумно розподілив їжу та воду\n3. Уникнув додаткових ризиків при русі",
        "options": [
            ("Обрати інший сценарій", "start"),
        ],
    },
    
    # Apocalypse scenario
    "apocalypse_1": {
        "title": "Сценарій 3 — Апокаліпсис: зникло світло",
        "description": "У місті сталася аварія. Немає електрики, зв'язку, паніка. Ти вдома, в тебе стандартні запаси.",
        "question": "Крок 1: Що робиш першим?",
        "options": [
            ("Йдеш до магазину закупитися", "apocalypse_1_wrong"),
            ("Перевіряєш, що маєш удома", "apocalypse_2"),
            ("Пишеш у чаті друзям – можливо, хтось щось знає", "apocalypse_1_wrong"),
        ],
        "explanation": "У разі надзвичайної ситуації краще уникати натовпу. Оцінка запасів – перший крок."
    },
    "apocalypse_1_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найкраще рішення у ситуації відключення електрики.",
        "options": [
            ("Спробувати ще раз", "apocalypse_1"),
            ("Повернутися до вибору сценарію", "start"),
        ],
    },
    "apocalypse_2": {
        "title": "Добре рішення!",
        "description": "Знати, що в тебе є, допоможе спланувати подальші дії.",
        "question": "Крок 2: У тебе є трохи води. Як дієш?",
        "options": [
            ("Вариш воду з крана", "apocalypse_3"),
            ("Починаєш пити запаси", "apocalypse_2_wrong"),
            ("П'єш напої - колу, сік, щоб зекономити воду", "apocalypse_2_wrong"),
        ],
        "explanation": "Кип'ятіння – базовий спосіб знезараження води. Варто це зробити, поки є газ/тепло."
    },
    "apocalypse_2_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найкраще використання води у надзвичайній ситуації.",
        "options": [
            ("Спробувати ще раз", "apocalypse_2"),
            ("Повернутися до вибору сценарію", "start"),
        ],
    },
    "apocalypse_3": {
        "title": "Добре рішення!",
        "description": "Кип'ятіння знезаражує воду і робить її безпечною для пиття.",
        "question": "Крок 3: Наступна ніч. У квартирі холодно. Твої дії:",
        "options": [
            ("Обклеюєш вікна, утеплюєш ліжко", "apocalypse_result"),
            ("Спиш у ванній - там менше вікон", "apocalypse_3_wrong"),
            ("Ідеш до друзів- у них більше ресурсів", "apocalypse_3_wrong"),
        ],
        "explanation": "Тепло – головне. Можна зробити «печеру з ковдр» і зберегти тепло тіла."
    },
    "apocalypse_3_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найкраще рішення для збереження тепла при відключенні опалення.",
        "options": [
            ("Спробувати ще раз", "apocalypse_3"),
            ("Повернутися до вибору сценарію", "start"),
        ],
    },
    "apocalypse_result": {
        "title": "Результат: Виживання в блекаут",
        "description": "Вітаємо! Ти набрав 3 бали: успішно пережив відключення електрики.\n\nТи зробив правильні кроки:\n1. Оцінив наявні запаси\n2. Подбав про безпечну воду\n3. Ефективно зберіг тепло",
        "options": [
            ("Обрати інший сценарій", "start"),
        ],
    },
    
    # Forest scenario
    "forest_1": {
        "title": "Сценарій 4 — Ти загубився в лісі",
        "description": "Під час прогулянки ти відійшов від групи і загубився. Скоро вечір, у тебе лише легка куртка і півпляшки води.",
        "question": "Крок 1: Що робиш першим?",
        "options": [
            ("Продовжуєш рухатись, шукаючи дорогу", "forest_1_wrong"),
            ("Зупиняєшся і намагаєшся визначити своє місцезнаходження", "forest_2"),
            ("Кричиш і кличеш на допомогу", "forest_1_wrong"),
        ],
        "explanation": "Коли заблукав, важливо зупинитися та зорієнтуватися, щоб не віддалятися ще більше."
    },
    "forest_1_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це може лише погіршити ситуацію в лісі.",
        "options": [
            ("Спробувати ще раз", "forest_1"),
            ("Повернутися до вибору сценарію", "start"),
        ],
    },
    "forest_2": {
        "title": "Добре рішення!",
        "description": "Ти зупинився, щоб не заблукати ще більше.",
        "question": "Крок 2: Наближається ніч. Твої дії:",
        "options": [
            ("Продовжуєш шукати дорогу, поки не зовсім темно", "forest_2_wrong"),
            ("Збираєш матеріали і робиш укриття на ніч", "forest_3"),
            ("Шукаєш високе дерево, щоб залізти і роздивитися околиці", "forest_2_wrong"),
        ],
        "explanation": "Ночівля в лісі без укриття небезпечна. Важливо зберігати тепло та енергію."
    },
    "forest_2_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найкраще рішення при настанні темряви в лісі.",
        "options": [
            ("Спробувати ще раз", "forest_2"),
            ("Повернутися до вибору сценарію", "start"),
        ],
    },
    "forest_3": {
        "title": "Добре рішення!",
        "description": "Підготовка до ночівлі збереже твої сили та здоров'я.",
        "question": "Крок 3: Вранці ти знайшов струмок. Що робиш?",
        "options": [
            ("П'єш воду одразу, бо дуже хочеш пити", "forest_3_wrong"),
            ("Кип'ятиш воду перед вживанням", "forest_result"),
            ("Ідеш вздовж струмка, він має вивести до людей", "forest_3_wrong"),
        ],
        "explanation": "Вода з природних джерел може містити небезпечні мікроорганізми. Кип'ятіння - найнадійніший спосіб знезараження."
    },
    "forest_3_wrong": {
        "title": "Неправильний вибір",
        "description": "На жаль, це не найбезпечніше рішення щодо води в лісі.",
        "options": [
            ("Спробувати ще раз", "forest_3"),
            ("Повернутися до вибору сценарію", "start"),
        ],
    },
    "forest_result": {
        "title": "Результат: Виживання в лісі",
        "description": "Вітаємо! Ти набрав 3 бали: успішно вижив у лісі, дочекався порятунку.\n\nТи зробив правильні кроки:\n1. Зупинився і зорієнтувався, не панікуючи\n2. Зробив укриття на ніч, зберігаючи сили\n3. Подбав про безпечну воду",
        "options": [
            ("Обрати інший сценарій", "start"),
        ],
    },
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send message on `/start`."""
    scenario = SCENARIOS["start"]
    keyboard = [[InlineKeyboardButton(text, callback_data=data)] for text, data in scenario["options"]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"*{scenario['title']}*\n\n{scenario['description']}",
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
    
    # Get scenario from callback data
    scenario_key = query.data
    scenario = SCENARIOS[scenario_key]
    keyboard = [[InlineKeyboardButton(text, callback_data=data)] for text, data in scenario["options"]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Format the message based on scenario content
    message_text = f"*{scenario['title']}*\n\n"
    if "description" in scenario:
        message_text += f"{scenario['description']}\n\n"
    if "question" in scenario:
        message_text += f"{scenario['question']}\n\n"
    if "explanation" in scenario:
        message_text += f"_Пояснення: {scenario['explanation']}_"
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token("YOUR_TELEGRAM_BOT_TOKEN").build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()

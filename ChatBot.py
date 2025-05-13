import logging
import sqlite3
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from config import TOKEN

DB_NAME = 'solar_system.sqlite'

# === Логирование ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HELLO_TEXT = """
Привет! Я — бот о Солнечной системе 🌞🪐
Вот, что ты можешь узнать:
- Напиши "Солнце", чтобы получить параметры
- Напиши "Меркурий", "Земля", ..., "Нептун" для информации о планете
- Напиши "Астероиды", "Кометы"
"""


# === Функции работы с БД ===
def clean_value(value):
    if not value:
        return "Не найдено"
    value = str(value).strip()
    value = value.replace(',', '.').replace(' ', '').replace('⋅', '×')
    return value


def get_sun_info(field):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"SELECT `{field}` FROM Sun WHERE `id Sun` = 1")
    result = cursor.fetchone()
    conn.close()
    return clean_value(result[0]) if result else "Не найдено"


def get_planet_by_name(planet_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Planets WHERE title=?", (planet_name,))
    result = cursor.fetchone()
    conn.close()
    return result


def get_small_body_by_name(body_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Small_Celestial_Bodies WHERE title=?", (body_name,))
    result = cursor.fetchone()
    conn.close()
    return result


# === Обработчики команд ===
async def start(update: ContextTypes.DEFAULT_TYPE, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELLO_TEXT)


async def handle_message(update: ContextTypes.DEFAULT_TYPE, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    logger.info(f"Пользователь написал: '{text}'")

    # ==== СОЛНЦЕ ====
    if text == "солнце":
        reply = """
        Про Солнце можно узнать:
    - площадь поверхности
    - объем
    - температура ядра
    - масса
    - диаметр
    """
        context.user_data['mode'] = 'sun'
        await update.message.reply_text(reply)

    elif context.user_data.get('mode') == 'sun':
        if any(k in text for k in ["площадь поверхности", "поверхность"]):
            value = get_sun_info("surface area(m^2)")
            await update.message.reply_text(f"Площадь поверхности Солнца: {value} м²")

        elif "объем" in text:
            value = get_sun_info("volume(m^3)")
            await update.message.reply_text(f"Объем Солнца: {value} м³")

        elif "температура" in text or "ядро" in text:
            value = get_sun_info("core temperature(K)")
            await update.message.reply_text(f"Температура ядра Солнца: {value} K")

        elif "масса" in text:
            value = get_sun_info("weight(kg)")
            await update.message.reply_text(f"Масса Солнца: {value} кг")

        elif "диаметр" in text:
            value = get_sun_info("diameter(m)")
            await update.message.reply_text(f"Диаметр Солнца: {value} м")

        else:
            await update.message.reply_text("Неизвестный параметр. Попробуй ещё раз.")

    # ==== ПЛАНЕТЫ ====
    elif any(p.lower() in text for p in ["меркурий", "венера", "земля", "марс", "юпитер", "сатурн", "уран", "нептун"]):
        planet = next(p for p in ["Меркурий", "Венера", "Земля", "Марс", "Юпитер", "Сатурн", "Уран", "Нептун"] if
                      p.lower() in text)
        info = get_planet_by_name(planet)
        if info:
            columns = [
                "ID",
                "Один из спутников",
                "Название",
                "Орбитальная скорость (км/с)",
                "Период вращения (дней)",
                "Число спутников",
                "Тип",
                "Масса (кг)"
            ]
            reply = f"""
            Про {planet} можно узнать:
            - Орбитальная скорость
            - Период вращения
            - Число спутников
            - Тип
            - Масса
            """
            context.user_data['mode'] = 'planet'
            context.user_data['selected_planet'] = planet
            await update.message.reply_text(reply)
        else:
            await update.message.reply_text("Информация не найдена.")

    elif context.user_data.get('mode') == 'planet':
        planet = context.user_data.get('selected_planet')
        info = get_planet_by_name(planet)
        if not info:
            await update.message.reply_text("Ошибка: данные о планете потеряны.")
            return

        if "орбитальная скорость" in text:
            await update.message.reply_text(f"Орбитальная скорость, {planet}: {clean_value(info[3])} км/с")

        elif "период вращения" in text:
            await update.message.reply_text(f"Период вращения, {planet}: {clean_value(info[4])} дней")

        elif "число спутников" in text:
            await update.message.reply_text(f"Число спутников, {planet}: {clean_value(info[5])}")

        elif "тип" in text:
            await update.message.reply_text(f"Тип планеты, {planet}: {clean_value(info[6])}")

        elif "масса" in text:
            await update.message.reply_text(f"Масса, {planet}: {clean_value(info[7])} кг")

        else:
            await update.message.reply_text("Неизвестный параметр. Попробуй ещё раз.")

    # ==== АСТЕРОИДЫ / КОМЕТЫ ====
    elif any(b in text for b in ["C/2024 G3", "2022 YO1", "2011 CQ1"]):
        body = next(b for b in ["C/2024 G3", "2022 YO1", "2011 CQ1"] if b.lower() in text)
        info = get_small_body_by_name(body)
        if info:
            reply = f"""
            Про {body} можно узнать:
            - Орбитальный период (лет)
            - Длительность наблюдений (дней)
            """
            context.user_data['mode'] = 'small_body'
            context.user_data['selected_body'] = body
            await update.message.reply_text(reply)
        else:
            await update.message.reply_text("Информация не найдена.")

    elif context.user_data.get('mode') == 'small_body':
        body = context.user_data.get('selected_body')
        info = get_small_body_by_name(body)
        if not info:
            await update.message.reply_text("Ошибка: данные о теле потеряны.")
            return

        if "орбитальный период" in text:
            await update.message.reply_text(f"Орбитальный период {body}: {clean_value(info[3])} лет")

        elif "длительность наблюдений" in text:
            await update.message.reply_text(f"Длительность наблюдений за {body}: {clean_value(info[4])} дней")

        else:
            await update.message.reply_text("Неизвестный параметр. Попробуй ещё раз.")

    # ==== ДРУГИЕ КОМАНДЫ ====
    elif "планеты" in text:
        planets = ["Меркурий", "Венера", "Земля", "Марс", "Юпитер", "Сатурн", "Уран", "Нептун"]
        await update.message.reply_text("Планеты Солнечной системы:\n" + "\n".join(planets))

    elif any(k in text for k in ["астероид", "комета", "малые тела"]):
        info = """
        Малые небесные тела:
        - C/2024 G3 (комета)
        - 2022 YO1 (астероид)
        - 2011 CQ1 (астероид)

        Напиши название объекта, чтобы выбрать параметр.
        """
        await update.message.reply_text(info)

    else:
        await update.message.reply_text("Не понял запрос. Напиши /start, чтобы посмотреть доступные команды.")


# === Основная функция запуска ===
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    application.run_polling()


if __name__ == '__main__':
    main()
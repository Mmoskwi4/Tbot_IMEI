import logging
import asyncio
import aiohttp
import tzlocal
import json
from settings import TOKEN_BOT, IMEI_API
from datetime import datetime
from aiohttp.client_exceptions import ClientConnectorError
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, CommandStart


logging.basicConfig(level=logging.INFO)
bot = Bot(str(TOKEN_BOT))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
local_timezone = tzlocal.get_localzone()


# Определение состояний
class Form(StatesGroup):
    waiting_for_imei = State()


# IMEI информация
async def imei_info(device_info: dict) -> str:

    if device_info is not None:
        response = (
            f"🔍 **Информация об устройстве с IMEI {device_info['imei'] if device_info.get('imei') != None else 'Не указано'}**:\n"
            f"📱 **Название устройства**: {device_info['deviceName'] if device_info.get('deviceName') != None else 'Не указано'}\n"
            f"🌍 **Страна покупки**: {device_info['purchaseCountry'] if device_info.get('purchaseCountry') != None else 'Не указано'}\n"
            f"🗓️ **Дата покупки**: {datetime.fromtimestamp(device_info['estPurchaseDate'], local_timezone).strftime('%Y-%m-%d %H:%M:%S') if device_info.get('estPurchaseDate') != None else 'Не указано'}\n"
            f"🔒 **SIM Lock**: {device_info['simLock'] if device_info.get('simLock') != None else 'Не указано'}\n"
            f"🛡️ **Статус гарантии**: {device_info['warrantyStatus'] if device_info.get('warrantyStatus') != None else 'Не указано'}\n"
            f"🛠️ **Покрытие ремонта**: {device_info['repairCoverage'] if device_info.get('repairCoverage') != None else 'Не указано'}\n"
            f"🆘 **Техническая поддержка**: {device_info['technicalSupport'] if device_info.get('technicalSupport') != None else 'Не указано'}\n"
            f"🎨 **Описание модели**: {device_info['modelDesc'] if device_info.get('modelDesc') != None else 'Не указано'}\n"
            f"📦 **Демо-устройство**: {device_info['demoUnit'] if device_info.get('demoUnit') != None else 'Не указано'}\n"
            f"🔄 **Был в ремонте**: {device_info['refurbished'] if device_info.get('refurbished') != None else 'Не указано'}\n"
            f"📶 **Сеть**: {device_info['network'] if device_info.get('network') != None else 'Не указано'}\n"
            f"🇺🇸 **Статус в США**: {device_info['usaBlockStatus'] if device_info.get('usaBlockStatus') != None else 'Не указано'}\n"
            f"🔒 **Find My iPhone (FMI)**: {device_info['fmiOn'] if device_info.get('fmiOn') != None else 'Не указано'}\n"
            f"🚫 **Режим потерянного устройства**: {device_info['lostMode'] if device_info.get('lostMode') != None else 'Не указано'}\n"
            f"🖼️ [Изображение устройства]({device_info['image'] if device_info.get('image') != None else 'Не указано'})"
        )
    else:
        response = "Ошибка при получении информации об IMEI. Введите команду /imei, чтобы снова проверить imei или обратитесь в поддержку"
    return response


# Регистрация нового пользователя
async def create_tg_user_api(username: str, chat_id: str):
    url = f"https://my.telegram.org/auth/telegram"
    json_data = {"chat_id": int(chat_id), "username": username}
    error_text = "Ошибка при регистрации обратитесь в поддержку"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=json_data) as response:
                if response.status != 200:
                    return error_text
                else:
                    success_text = f"Привет, {username}! Это бот для проверки IMEI, введи команду /imei для того чтобы отправить IMEI"
                    return success_text
    except ClientConnectorError as e:
        print(e)
        return error_text


# Проверки IMEI
async def validate_imei(imei: str) -> bool:
    # Проверка длины
    if len(imei) != 15:
        return False

    # Проверка на все цифры
    if not imei.isdigit():
        return False

    # Алгоритм Luhn
    total = 0

    for i, digit in enumerate(imei):
        n = int(digit)
        # Удваиваем каждую вторую цифру
        if i % 2 == 1:
            n *= 2
            # Если результат больше 9, вычтем 9
            if n > 9:
                n -= 9
        total += n

    # Если сумма делится на 10, IMEI действителен
    return total % 10 == 0

async def check_balance():
    # Проверка баланса
    url = 'https://api.imeicheck.net/v1/account'
    imei_api = str(IMEI_API)
    headers = {
        "Authorization": "Bearer " + imei_api,
        "Content-Type": "application/json"
    }
    error_text = "Ошибка при проверке баланса. Проверьте авторизацию по API"


    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    balance = await response.text()
                    count = json.loads(balance)
                    return count['balance']
                else:
                    return f'Не удалось проверить баланс. Ошибка {response.status}'
    except ClientConnectorError:
        return error_text


# Сбор данных IMEI
async def check_imei_api(imei: str):
    url = "https://api.imeicheck.net/v1/checks"
    imei_api = str(IMEI_API)
    headers = {
        "Authorization": "Bearer " + imei_api,
        "Content-Type": "application/json"
    }
    body = json.dumps({"deviceId": imei, "serviceId": 1})
    error_text = "Ошибка при проверке IMEI. Введите команду /imei, чтобы снова проверить imei или обратитесь в поддержку"
    if await check_balance() != 0:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=body) as response:
                    if response.status == 200:
                        res = await response.text()
                        json_res = json.loads(res)
                        for device in json_res:
                            if device.get("deviceId") == imei:
                                return await imei_info(device.get("properties", None))
                    elif response.status == 400 or response.status == 404:
                        json_res = await response.json()
                        return json_res["detail"]
                    else:
                        return response.text
        except ClientConnectorError:
                return error_text
    else:
        return f'Ваш баланс: {check_balance}, этого недостаточно! Пополните счёт.'


# Команда /start
@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    message_text = await create_tg_user_api(
        username=message.chat.username, chat_id=message.chat.id
    )
    await message.reply(message_text)


# Команда /imei
@dp.message(Command("imei"))
async def send_welcome(message: types.Message):
    await message.reply("Хорошо! Отправь мне 15-значный IMEI для проверки.")


# Проверкуа на ввод IMEI, чтобы в нём были только цифры (в количестве 15)
@dp.message(lambda message: not message.text.isdigit() or len(message.text) != 15)
async def invalid_imei_handler(message: types.Message):
    await message.reply(
        "Пожалуйста, вводите только 15-значный числовой IMEI. Введите команду /imei, чтобы снова проверить imei"
    )


# Предоставлет ответ по IMEI
@dp.message(lambda message: message.text.isdigit() and len(message.text) == 15)
async def imei_handler(message: types.Message):
    imei = message.text.strip()
    check_imei = await validate_imei(imei)
    if check_imei:
        check_imei_api_text = await check_imei_api(imei)
        await message.reply(check_imei_api_text, parse_mode="Markdown")
    else:
        await message.reply(
            f"IMEI {imei} является недействительным. Введите команду /imei, чтобы снова проверить imei"
        )


# Аснихронный запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

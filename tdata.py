import os
import json
import asyncio
import shutil
from opentele.td import TDesktop
from opentele.api import UseCurrentSession
from telethon import TelegramClient

API_ID = 123456  # Твой api_id
API_HASH = 'asdgas12asdfas1q2dasf'  # Твой api_hash

async def convert_tdata_to_session(tdata_path, output_dir):
    account_name = os.path.basename(output_dir)
    session_path = os.path.join(output_dir, f"{account_name}.session")
    json_path = os.path.join(output_dir, f"{account_name}.json")
    temp_tdata = os.path.join(output_dir, f"temp_tdata")

    for file_path in [session_path, json_path]:
        if os.path.exists(file_path):
            os.remove(file_path)

    if os.path.exists(temp_tdata):
        shutil.rmtree(temp_tdata)
    shutil.copytree(tdata_path, temp_tdata)

    try:
        tdesk = TDesktop(temp_tdata)
        if not tdesk.isLoaded():
            print(f"Ошибка: папка {tdata_path} не валидна.")
            return

        client = await tdesk.ToTelethon(session=session_path, flag=UseCurrentSession)
        
        await client.connect()

        if await client.is_user_authorized():
            print(f"[+] Успешно создана сессия: {session_path}")
            info = await client.get_me()

            account_info = {
                "session_file": session_path,
                "phone": info.phone,
                "user_id": info.id,
                "username": info.username,
                "first_name": info.first_name,
                "last_name": info.last_name,
                "api_id": API_ID,
                "api_hash": API_HASH,
                "source_tdata": tdata_path
            }

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(account_info, f, indent=4, ensure_ascii=False)
            print(f"[+] Информация о сессии сохранена: {json_path}")
        else:
            print("[-] Ошибка: аккаунт не авторизован.")

        await client.disconnect()

    except Exception as e:
        print(f"Ошибка при обработке: {str(e)}")
    finally:
        shutil.rmtree(temp_tdata)

async def process_accounts(root_dir="acc"):
    for folder in os.listdir(root_dir):
        account_dir = os.path.join(root_dir, folder)
        tdata_path = os.path.join(account_dir, "tdata")

        if os.path.isdir(tdata_path):
            print(f"Обработка: {tdata_path}")
            await convert_tdata_to_session(tdata_path, account_dir)
        else:
            print(f"Пропущено: {account_dir} (нет tdata)")

async def main():
    await process_accounts()

if __name__ == '__main__':
    print("Закройте Telegram Desktop перед запуском.")
    asyncio.run(main())

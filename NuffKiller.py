import os
import asyncio
import aiohttp
from art import text2art
from aiohttp_socks import ProxyConnector
from telethon import TelegramClient
from telethon.tl.functions.messages import ReportRequest, ReportSpamRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import (
    InputPeerUser, PeerUser, PeerChat, PeerChannel,
    InputReportReasonViolence, InputReportReasonSpam, InputReportReasonPornography,
    InputReportReasonChildAbuse, InputReportReasonCopyright, InputReportReasonGeoIrrelevant,
    InputReportReasonFake, InputReportReasonIllegalDrugs, InputReportReasonPersonalDetails,
    InputReportReasonOther
)
from tqdm import tqdm
import re
import json
import random
from colorama import init, Fore, Style

init()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_menu_choice():
    clear_screen()
    nuffkiller_art = text2art("NuffKiller", font="small")
    print(f"{Fore.CYAN}{nuffkiller_art}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}=== Меню ==={Style.RESET_ALL}")
    print(f"{Fore.WHITE}1. Начать отправку жалоб{Style.RESET_ALL}")
    print(f"{Fore.WHITE}2. Выход{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}Created by: {Fore.CYAN}@NuffLik{Style.RESET_ALL}")
    while True:
        choice = input(f"{Fore.CYAN}Выберите 1 или 2: {Style.RESET_ALL}").strip()
        if choice in ['1', '2']:
            return choice
        print(f"{Fore.RED}Ошибка: введите 1 или 2.{Style.RESET_ALL}")

def get_input(prompt, required=True):
    while True:
        value = input(f"{Fore.CYAN}{prompt}{Style.RESET_ALL}").strip()
        if value or not required:
            return value
        if required:
            print(f"{Fore.RED}Ошибка: это поле обязательно.{Style.RESET_ALL}")

async def check_proxy(proxy, timeout=60, retries=2, semaphore=None):
    async with semaphore:
        for attempt in range(retries):
            try:
                if proxy.startswith('http://'):
                    proxy_url = proxy
                    proxy_display = proxy.replace('http://', 'HTTP: ')
                    proxy_type = 'http'
                elif proxy.startswith('socks5://'):
                    proxy_url = proxy
                    proxy_display = proxy.replace('socks5://', 'SOCKS5: ')
                    proxy_type = 'socks5'
                elif proxy.startswith('socks4://'):
                    proxy_url = proxy
                    proxy_display = proxy.replace('socks4://', 'SOCKS4: ')
                    proxy_type = 'socks4'
                else:
                    proxy_url = f"http://{proxy}"
                    proxy_display = f"HTTP: {proxy}"
                    proxy_type = 'http'
                connector = ProxyConnector.from_url(proxy_url)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get('https://api.telegram.org/', timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                        print(f"{Fore.GREEN}✓ {proxy_display} - ответ {response.status} (попытка {attempt + 1}){Style.RESET_ALL}")
                        return proxy_display, proxy_type, True
            except Exception as e:
                if attempt < retries - 1:
                    print(f"{Fore.YELLOW}Попытка {attempt + 1} для {proxy_display} не удалась: {str(e)}. Пробуем снова...{Style.RESET_ALL}")
                    await asyncio.sleep(2)
                else:
                    print(f"{Fore.RED}✗ {proxy_display} - не работает после {retries} попыток: {str(e)}{Style.RESET_ALL}")
                    return proxy_display, proxy_type, False

async def load_proxies(proxy_files=["p1.txt", "p2.txt", "p3.txt", "p4.txt", "ps1.txt"], max_workers=500):
    all_proxies = {}
    for proxy_file in proxy_files:
        if not os.path.exists(proxy_file):
            print(f"{Fore.RED}Файл {proxy_file} не найден!{Style.RESET_ALL}")
            continue
        with open(proxy_file, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
            all_proxies[proxy_file] = proxies
    
    if not all_proxies:
        print(f"{Fore.RED}Список прокси пуст!{Style.RESET_ALL}")
        return []

    total_proxies = sum(len(proxies) for proxies in all_proxies.values())
    recommended_workers = min(total_proxies, max_workers, os.cpu_count() * 5)
    print(f"{Fore.YELLOW}Рекомендуемое количество воркеров для {total_proxies} прокси: {recommended_workers}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Текущее количество воркеров: {max_workers}{Style.RESET_ALL}")

    semaphore = asyncio.Semaphore(max_workers)
    tasks = []
    proxy_to_file = {}
    for proxy_file, proxies in all_proxies.items():
        for proxy in proxies:
            tasks.append(check_proxy(proxy, semaphore=semaphore))
            proxy_to_file[proxy] = proxy_file
    
    working_proxies = []
    proxy_results = {}
    proxy_types = {}
    print(f"\n{Fore.YELLOW}Проверка прокси:{Style.RESET_ALL}")
    with tqdm(total=total_proxies, desc="Прогресс проверки", unit="proxy", colour='cyan') as pbar:
        for coro in asyncio.as_completed(tasks):
            proxy_display, proxy_type, is_working = await coro
            proxy = proxy_display.split(': ')[1] if ': ' in proxy_display else proxy_display
            proxy_results[proxy] = is_working
            proxy_types[proxy] = proxy_type
            if is_working:
                working_proxies.append((proxy, proxy_type))
                pbar.write(f"{Fore.GREEN}✓ {proxy_display} - работает{Style.RESET_ALL}")
            else:
                pbar.write(f"{Fore.RED}✗ {proxy_display} - не работает{Style.RESET_ALL}")
            pbar.update(1)
    
    for proxy_file, proxies in all_proxies.items():
        original_count = len(proxies)
        updated_proxies = [p for p in proxies if proxy_results.get(p, False)]
        if updated_proxies != proxies:
            with open(proxy_file, 'w') as f:
                f.write('\n'.join(updated_proxies) + '\n')
            print(f"{Fore.YELLOW}Файл {proxy_file}: удалено {original_count - len(updated_proxies)} нерабочих прокси, осталось {len(updated_proxies)}{Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN}Найдено {len(working_proxies)} рабочих прокси из {total_proxies}{Style.RESET_ALL}")
    return working_proxies

def load_accounts(acc_dir="acc"):
    accounts = []
    if not os.path.isdir(acc_dir):
        print(f"{Fore.RED}Директория '{acc_dir}' не найдена!{Style.RESET_ALL}")
        return accounts
    
    for acc_folder in os.listdir(acc_dir):
        folder_path = os.path.join(acc_dir, acc_folder)
        if os.path.isdir(folder_path):
            session_path = os.path.join(folder_path, f"{acc_folder}.session")
            json_path = os.path.join(folder_path, f"{acc_folder}.json")
            if os.path.exists(session_path) and os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    api_id = config.get('api_id')
                    api_hash = config.get('api_hash')
                    phone = config.get('phone')
                    if api_id and api_hash:
                        accounts.append({
                            'folder': folder_path,
                            'session': session_path,
                            'api_id': api_id,
                            'api_hash': api_hash,
                            'phone': phone
                        })
                    else:
                        print(f"{Fore.RED}Ошибка: в {json_path} отсутствует api_id или api_hash{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Предупреждение: отсутствует {session_path} или {json_path} в {folder_path}{Style.RESET_ALL}")
    
    print(f"{Fore.GREEN}Найдено {len(accounts)} аккаунтов{Style.RESET_ALL}")
    return accounts

def get_report_reason():
    print(f"\n{Fore.YELLOW}=== Типы жалоб ==={Style.RESET_ALL}")
    reasons = {
        '1': 'dislike',
        '2': 'child_abuse',
        '3': 'violence',
        '4': 'illegal_goods',
        '5': 'pornography',
        '6': 'personal_details',
        '7': 'terrorism',
        '8': 'fraud_or_spam',
        '9': 'copyright',
        '10': 'other',
        '11': 'remove_not_illegal'
    }
    
    reason_names = {
        '1': 'Не нравится',
        '2': 'Жестокое обращение с детьми',
        '3': 'Насилие',
        '4': 'Незаконные товары',
        '5': 'Порнографические материалы',
        '6': 'Персональные данные',
        '7': 'Терроризм',
        '8': 'Мошенничество или спам',
        '9': 'Нарушение авторских прав',
        '10': 'Другое',
        '11': 'Не нарушает закон, но надо удалить'
    }
    
    for key in reasons.keys():
        print(f"{Fore.WHITE}{key}. {reason_names[key]}{Style.RESET_ALL}")
    
    while True:
        choice = input(f"{Fore.CYAN}Выберите тип жалобы (1-11): {Style.RESET_ALL}").strip()
        if choice in reasons:
            return reasons[choice]
        print(f"{Fore.RED}Ошибка: выберите от 1 до 11.{Style.RESET_ALL}")

def get_sub_reason(main_reason):
    sub_reasons = {
        'illegal_goods': {
            '1': 'Оружие',
            '2': 'Наркотики',
            '3': 'Подделка документов',
            '4': 'Фальшивомонетничество',
            '5': 'Другие товары'
        },
        'pornography': {
            '1': 'Детская порнография',
            '2': 'Интимные изображения без согласия',
            '3': 'Другие незаконные материалы'
        },
        'personal_details': {
            '1': 'Номер',
            '2': 'Адрес',
            '3': 'Личные изображения',
            '4': 'Другие личные данные'
        },
        'fraud_or_spam': {
            '1': 'Фишинг',
            '2': 'Выдача себя за другое лицо',
            '3': 'Мошеннические продажи',
            '4': 'Спам'
        }
    }
    
    available_subs = sub_reasons.get(main_reason, {})
    if not available_subs:
        return None
    
    print(f"\n{Fore.YELLOW}=== Поджалобы для {main_reason} ==={Style.RESET_ALL}")
    for key, value in available_subs.items():
        print(f"{Fore.WHITE}{key}. {value}{Style.RESET_ALL}")
    
    while True:
        choice = input(f"{Fore.CYAN}Выберите поджалобу или оставьте пустым для основной причины: {Style.RESET_ALL}").strip()
        if not choice:
            return None
        if choice in available_subs:
            return choice
        print(f"{Fore.RED}Ошибка: выберите из доступных вариантов или оставьте пустым.{Style.RESET_ALL}")

def generate_complaint_text(username, telegram_id, main_reason, sub_reason=None, channel=None, violation_link=None):
    synonyms = {
        "greeting": ["Dear Telegram Support", "Hello", "Hi there", "Hey Telegram Team", "Good day", "Dear Support Crew", "Hey folks", "Greetings", "Hello support squad"],
        "urgent": ["urgently", "right now", "immediately", "asap", "quickly", "at once", "fast", "pronto", "without delay"],
        "please": ["please", "kindly", "do it", "I beg you", "pretty please", "at your earliest", "if you could", "be so kind", "help me out"],
        "action": ["investigate", "take action", "check this", "deal with", "ban", "restrict", "sort out", "handle", "shut down", "look into"],
        "violation": ["violation", "abuse", "breach", "misconduct", "offense", "rule-breaking", "wrongdoing", "mess", "nonsense", "bullshit"]
    }
    
    variations = {
        "child_abuse": [
            f"{random.choice(synonyms['greeting'])}! This sick fuck {username} (ID: {telegram_id}) is posting child abuse shit. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
            f"Help! {username} (ID: {telegram_id}) is sharing disgusting child abuse content. {random.choice(synonyms['please'])} ban this monster {random.choice(synonyms['urgent'])}!"
        ],
        "violence": [
            f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) is spreading violent crap everywhere. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
            f"Hey! {username} (ID: {telegram_id}) keeps posting violent bullshit. {random.choice(synonyms['please'])} stop this asshole {random.choice(synonyms['urgent'])}!"
        ],
        "illegal_goods": {
            "1": [
                f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) is selling illegal weapons. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
                f"Yo! {username} (ID: {telegram_id}) is peddling guns like it’s nothing. {random.choice(synonyms['please'])} shut this down {random.choice(synonyms['urgent'])}!"
            ],
            "2": [
                f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) is dealing drugs openly. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
                f"Hi! {username} (ID: {telegram_id}) is pushing dope everywhere. {random.choice(synonyms['please'])} ban this dealer {random.choice(synonyms['urgent'])}!"
            ],
            "3": [
                f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) is selling fake IDs and passports. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
                f"Hey! {username} (ID: {telegram_id}) is pumping out forged docs. {random.choice(synonyms['please'])} kill this {random.choice(synonyms['urgent'])}!"
            ],
            "4": [
                f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) is making counterfeit cash. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
                f"Yo! {username} (ID: {telegram_id}) is flooding with fake money. {random.choice(synonyms['please'])} stop this {random.choice(synonyms['urgent'])}!"
            ],
            "5": [
                f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) is selling shady illegal stuff. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
                f"Hi! {username} (ID: {telegram_id}) is dealing in banned crap. {random.choice(synonyms['please'])} handle this {random.choice(synonyms['urgent'])}!"
            ]
        },
        "pornography": {
            "1": [
                f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) is posting fucking child porn. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this sick {random.choice(synonyms['violation'])}!",
                f"Help! {username} (ID: {telegram_id}) is sharing CP garbage. {random.choice(synonyms['please'])} ban this creep {random.choice(synonyms['urgent'])}!"
            ],
            "2": [
                f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) is leaking nudes without consent. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
                f"Hey! {username} (ID: {telegram_id}) is posting private pics without permission. {random.choice(synonyms['please'])} stop this {random.choice(synonyms['urgent'])}!"
            ],
            "3": [
                f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) is sharing illegal porn crap. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
                f"Hi! {username} (ID: {telegram_id}) is spreading banned adult content. {random.choice(synonyms['please'])} kill this {random.choice(synonyms['urgent'])}!"
            ]
        },
        "personal_details": {
            "1": [
                f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) leaked my phone number. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
                f"Yo! {username} (ID: {telegram_id}) posted my number without consent. {random.choice(synonyms['please'])} ban this {random.choice(synonyms['urgent'])}!"
            ],
            "2": [
                f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) shared my home address. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
                f"Help! {username} (ID: {telegram_id}) doxxed my address. {random.choice(synonyms['please'])} stop this {random.choice(synonyms['urgent'])}!"
            ],
            "3": [
                f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) posted my private pics. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
                f"Hey! {username} (ID: {telegram_id}) leaked my personal photos. {random.choice(synonyms['please'])} kill this {random.choice(synonyms['urgent'])}!"
            ],
            "4": [
                f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) exposed my personal info. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
                f"Hi! {username} (ID: {telegram_id}) is leaking my private data. {random.choice(synonyms['please'])} handle this {random.choice(synonyms['urgent'])}!"
            ]
        },
        "terrorism": [
            f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) is posting terrorist propaganda and bomb plans. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this insane {random.choice(synonyms['violation'])}!",
            f"Help! {username} (ID: {telegram_id}) is recruiting for terror attacks. {random.choice(synonyms['please'])} nuke this psycho {random.choice(synonyms['urgent'])}!"
        ],
        "fraud_or_spam": {
            "1": [
                f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) is phishing for accounts. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
                f"Yo! {username} (ID: {telegram_id}) is trying to steal logins. {random.choice(synonyms['please'])} ban this scam {random.choice(synonyms['urgent'])}!"
            ],
            "2": [
                f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) is pretending to be someone else. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
                f"Hey! {username} (ID: {telegram_id}) is impersonating people. {random.choice(synonyms['please'])} stop this {random.choice(synonyms['urgent'])}!"
            ],
            "3": [
                f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) is scamming with fake sales. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
                f"Hi! {username} (ID: {telegram_id}) is ripping people off with scams. {random.choice(synonyms['please'])} kill this {random.choice(synonyms['urgent'])}!"
            ],
            "4": [
                f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) is spamming like a bot. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
                f"Yo! {username} (ID: {telegram_id}) floods chats with spam. {random.choice(synonyms['please'])} ban this {random.choice(synonyms['urgent'])}!"
            ]
        },
        "copyright": [
            f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) stole my copyrighted work. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
            f"Help! {username} (ID: {telegram_id}) is using my content without permission. {random.choice(synonyms['please'])} handle this {random.choice(synonyms['urgent'])}!"
        ],
        "other": [
            f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) is doing some shady crap. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this {random.choice(synonyms['violation'])}!",
            f"Hi! {username} (ID: {telegram_id}) is up to no good. {random.choice(synonyms['please'])} check this out {random.choice(synonyms['urgent'])}!"
        ],
        "remove_not_illegal": [
            f"{random.choice(synonyms['greeting'])}! {username} (ID: {telegram_id}) posted stuff I want gone, even if it’s not illegal. {random.choice(synonyms['urgent'])} {random.choice(synonyms['action'])} this please!",
            f"Hey! {username} (ID: {telegram_id}) has content I need removed, not illegal but personal. {random.choice(synonyms['please'])} delete this {random.choice(synonyms['urgent'])}!"
        ]
    }
    
    if main_reason in variations:
        if isinstance(variations[main_reason], dict) and sub_reason:
            text = random.choice(variations[main_reason][sub_reason])
        else:
            text = random.choice(variations[main_reason])
        if violation_link:
            text += f" Proof: {violation_link}"
        return text
    return f"Complaint about {username} (ID: {telegram_id}) for {main_reason}"

def parse_message_link(link):
    pattern = r"https://t.me/(\w+)/(\d+)"
    match = re.match(pattern, link)
    if match:
        return match.group(1), int(match.group(2))
    return None, None

def get_reason_object(reason_str):
    reason_map = {
        'dislike': InputReportReasonOther(),
        'child_abuse': InputReportReasonChildAbuse(),
        'violence': InputReportReasonViolence(),
        'illegal_goods': InputReportReasonIllegalDrugs(),
        'pornography': InputReportReasonPornography(),
        'personal_details': InputReportReasonPersonalDetails(),
        'terrorism': InputReportReasonOther(),
        'fraud_or_spam': InputReportReasonSpam(),
        'copyright': InputReportReasonCopyright(),
        'other': InputReportReasonOther(),
        'remove_not_illegal': InputReportReasonOther()
    }
    return reason_map.get(reason_str)

async def report_target(client, target, violation_link, reason, sub_reason, proxy_display, semaphore=None):
    async with semaphore:
        try:
            await client.connect()
            if not await client.is_user_authorized():
                print(f"{Fore.YELLOW}Сессия {client.session.filename} не авторизована{Style.RESET_ALL}")
                return False
            print(f"{Fore.YELLOW}Подключение через {proxy_display} успешно для {client.session.filename.split('/')[-1]}{Style.RESET_ALL}")
            
            me = await client.get_me()
            print(f"{Fore.YELLOW}Текущий пользователь: {me.username or me.phone} (ID: {me.id}){Style.RESET_ALL}")
            
            complaint_text = ""
            if reason != 'dislike' or sub_reason:
                if violation_link:
                    chat_username, _ = parse_message_link(violation_link)
                    complaint_text = generate_complaint_text(target or chat_username, me.id, reason, sub_reason, chat_username, violation_link)
                else:
                    complaint_text = generate_complaint_text(target, me.id, reason, sub_reason)
            
            if violation_link:
                chat_username, msg_id = parse_message_link(violation_link)
                if not chat_username or not msg_id:
                    raise ValueError("Неверный формат ссылки на нарушение")
                entity = await client.get_entity(f"t.me/{chat_username}")
                print(f"{Fore.YELLOW}Чат нарушения: {entity.__class__.__name__} (ID: {entity.id}){Style.RESET_ALL}")
                
                try:
                    message = await client.get_messages(entity, ids=msg_id)
                    if not message:
                        print(f"{Fore.RED}✗ Сообщение {violation_link} не найдено или недоступно для {client.session.filename.split('/')[-1]}{Style.RESET_ALL}")
                        return False
                    print(f"{Fore.GREEN}✓ Сообщение {violation_link} найдено: {message.text[:50] if message.text else '[без текста]'}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}✗ Ошибка при проверке сообщения {violation_link}: {e}{Style.RESET_ALL}")
                    return False
                
                reason_obj = get_reason_object(reason)
                await client(ReportRequest(
                    peer=entity,
                    id=[msg_id],
                    reason=reason_obj,
                    message=complaint_text if complaint_text else ""
                ))
                target_desc = f"сообщение {violation_link}"
            else:
                target_entity = await client.get_entity(target)
                print(f"{Fore.YELLOW}Цель: {target_entity.__class__.__name__} (ID: {target_entity.id}){Style.RESET_ALL}")
                
                if reason == 'fraud_or_spam' and (not sub_reason or sub_reason == '4'):
                    await client(ReportSpamRequest(peer=target_entity))
                    target_desc = f"пользователь {target} (спам)"
                else:
                    print(f"{Fore.YELLOW}Жалоба на профиль пользователя напрямую поддерживается только для 'мошенничество или спам (спам)'. Укажите ссылку на нарушение для {reason}.{Style.RESET_ALL}")
                    return False
            
            print(f"{Fore.GREEN}✓ Жалоба ({reason}{f', поджалоба {sub_reason}' if sub_reason else ''}) на {target_desc} отправлена с {client.session.filename.split('/')[-1]} через {proxy_display}{Style.RESET_ALL}")
            if complaint_text:
                print(f"{Fore.YELLOW}Текст жалобы: {complaint_text}{Style.RESET_ALL}")
            return True
        except telethon.errors.rpcerrorlist.PhoneNumberBannedError as e:
            print(f"{Fore.RED}✗ Номер заблокирован для {client.session.filename.split('/')[-1]}: {e}{Style.RESET_ALL}")
            return False
        except Exception as e:
            print(f"{Fore.RED}✗ Ошибка для {client.session.filename.split('/')[-1]} через {proxy_display}: {e}{Style.RESET_ALL}")
            return False
        finally:
            await client.disconnect()

async def main():
    proxy_files = ["p1.txt"]
    acc_dir = "acc"
    use_proxy = False

    print(f"{Fore.YELLOW}Проверка подключения к Telegram без прокси...{Style.RESET_ALL}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('https://api.telegram.org/', timeout=aiohttp.ClientTimeout(total=15)) as response:
                print(f"{Fore.GREEN}Статус без прокси: {response.status}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Ошибка без прокси: {e}{Style.RESET_ALL}")
    
    max_proxy_workers = 100
    proxies = await load_proxies(proxy_files, max_workers=max_proxy_workers) if use_proxy else []
    if use_proxy and not proxies:
        print(f"{Fore.RED}Нет рабочих прокси. Программа завершена.{Style.RESET_ALL}")
        return
    
    while True:
        clear_screen()
        choice = get_menu_choice()

        if choice == '2':
            print(f"{Fore.YELLOW}Выход из программы.{Style.RESET_ALL}")
            break

        if choice == '1':
            clear_screen()
            print(f"{Fore.YELLOW}=== Настройка отправки жалоб ==={Style.RESET_ALL}")
            
            target = get_input("Введите имя пользователя (@username) или ссылку на сообщение (https://t.me/username/123): ")
            violation_link = None
            if target.startswith('https://t.me/'):
                violation_link = target
                target = None
            else:
                if not target.startswith('@'):
                    target = '@' + target
                violation_link = get_input("Введите ссылку на нарушение (https://t.me/chat/123) или оставьте пустым для жалобы на профиль: ", required=False)
            
            if violation_link and not parse_message_link(violation_link):
                print(f"{Fore.RED}Ошибка: неверный формат ссылки на нарушение.{Style.RESET_ALL}")
                input(f"{Fore.CYAN}Нажмите Enter для возврата в меню...{Style.RESET_ALL}")
                continue
            
            accounts = load_accounts(acc_dir)
            if not accounts:
                print(f"{Fore.RED}Не найдено аккаунтов в директории acc!{Style.RESET_ALL}")
                input(f"{Fore.CYAN}Нажмите Enter для возврата в меню...{Style.RESET_ALL}")
                continue
            
            max_report_workers = min(len(accounts), len(proxies) if use_proxy else float('inf'), os.cpu_count() * 2)
            print(f"{Fore.YELLOW}Рекомендуемое количество воркеров для {len(accounts)} аккаунтов и {len(proxies) if use_proxy else 'без'} прокси: {max_report_workers}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Текущее количество воркеров для жалоб: {max_report_workers}{Style.RESET_ALL}")

            report_reason = get_report_reason()
            sub_reason = get_sub_reason(report_reason)
            print(f"\n{Fore.GREEN}Найдено {len(accounts)} аккаунтов. Начинаем отправку жалоб...{Style.RESET_ALL}")

            async def run_reports():
                semaphore = asyncio.Semaphore(max_report_workers)
                tasks = []
                for i, account in enumerate(accounts):
                    if use_proxy and proxies:
                        proxy, proxy_type = proxies[i % len(proxies)]
                        proxy_ip, proxy_port = proxy.split(':')
                        proxy_display = f"{proxy_type.upper()}: {proxy}"
                        client = TelegramClient(
                            account['session'],
                            account['api_id'],
                            account['api_hash'],
                            proxy={'proxy_type': proxy_type, 'addr': proxy_ip, 'port': int(proxy_port)},
                            timeout=60
                        )
                    else:
                        proxy_display = "без прокси"
                        client = TelegramClient(
                            account['session'],
                            account['api_id'],
                            account['api_hash']
                        )
                    
                    await client.connect()
                    if not await client.is_user_authorized():
                        try:
                            print(f"{Fore.YELLOW}Сессия {account['session']} не авторизована, переавторизация...{Style.RESET_ALL}")
                            await client.start(phone=lambda: account['phone'])
                            print(f"{Fore.GREEN}Сессия {account['session']} успешно переавторизована{Style.RESET_ALL}")
                        except telethon.errors.rpcerrorlist.PhoneNumberBannedError as e:
                            print(f"{Fore.RED}✗ Номер {account['phone']} заблокирован: {e}{Style.RESET_ALL}")
                            await client.disconnect()
                            continue
                        except Exception as e:
                            print(f"{Fore.RED}✗ Ошибка авторизации {account['session']}: {e}{Style.RESET_ALL}")
                            await client.disconnect()
                            continue
                    await client.disconnect()
                    
                    tasks.append(report_target(client, target, violation_link, report_reason, sub_reason, proxy_display, semaphore))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        print(f"{Fore.RED}✗ Необработанное исключение: {result}{Style.RESET_ALL}")

            await run_reports()
            print(f"\n{Fore.GREEN}Процесс завершён.{Style.RESET_ALL}")
            input(f"{Fore.CYAN}Нажмите Enter, чтобы вернуться в меню...{Style.RESET_ALL}")

if __name__ == "__main__":
    asyncio.run(main())
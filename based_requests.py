from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from random import choice
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

token = "" # можно взять на https://mirror2.dropmail.info/api/
admin_id = 404 # вставьте сюда ваш id (пользователя)
session_wo_addr = """mutation {
    introduceSession(input: {withAddress: false}) {
        id
    }
}"""
get_domains = """query { 
    domains {
        id, name, introducedAt, availableVia
    }
}"""
introduce_address_parts = ('''
mutation {
    introduceAddress(input: {sessionId: "''', '''",
                             domainId: "''', '''"}) {
        address,
        restoreKey
    }
}''')

restore_parts = ('''mutation {
        restoreAddress(input: {sessionId: "''', '''",
                                 mailAddress: "''', '''",
                                 restoreKey: "''', '''"}) { 
        address, 
        restoreKey 
    }
}''')

check_parts = ('''query {
            session(id: "''', '''") {
                mails{
                    fromAddr,
                    toAddr,
                    toAddrOrig,
                    downloadUrl,
                    text,
                    headerSubject,
                    id
                }
            }
        }''')

ga_addrs = ('''query {
    session(id: "''', '''") {
        addresses {address, restoreKey}
    }
}''')  # get active addresses (by session id)

loaded_domains = {}
users_and_sessions = {}
user_and_last_mails = {}

spravka = """
Любой адрес можно расширить. 
Например, почта, отправленная 
на ffnyrmipb-qweqwe@wasd.supere.ml или ffnyrmipb.ololo@a.b.c.supere.ml 
автоматически будет доставлена на ffnyrmipb@supere.ml
Примеры: ffnyrmipb+byz@dviv.supere.ml, ffnyrmipb@ginl.supere.ml, ffnyrmipb.ule@supere.ml."""

restore_addr_help = "Отправьте боту сообщение вида: 'Восстановить адрес токен'"


def load_domains_if_not_loaded():
    if not loaded_domains:
        dmfilelines = open("domains.txt", "r").readlines()
        for line in dmfilelines:
            temp_list = line.rstrip().split(" ")
            loaded_domains[temp_list[0]] = temp_list[1]


def introduce_session_if_not(uid, recreate=False):
    if uid not in users_and_sessions.keys() and not recreate:
        session_id = make_request(session_wo_addr)["introduceSession"]["id"]
        users_and_sessions[uid] = session_id
    elif recreate:
        session_id = make_request(session_wo_addr)["introduceSession"]["id"]
        users_and_sessions[uid] = session_id
        return additional("Сессия пересоздана.")


def format_email(mail_dct):
    origaddress = mail_dct['toAddrOrig']
    address = mail_dct['toAddr']
    text = mail_dct['text']
    header = mail_dct['headerSubject']
    from_address = mail_dct['fromAddr']
    dl_url = mail_dct['downloadUrl']
    to_address = address if address == origaddress else f"{origaddress} ({address})"
    message = "На адрес {} пришло новое письмо.\n\nОно пришло от: \n{}\n\nТема:\n{}\n\nТекст письма:\n{}\n\nСсылка " \
              "для скачивания (.eml):{}".format(to_address, from_address, header, text, dl_url)
    return message


def check_new_session_mails(uid):
    introduce_session_if_not(uid)
    built_request = check_parts[0] + users_and_sessions[uid] + check_parts[1]
    returned = make_request(built_request)
    print(returned)
    if returned['session']['mails']:
        if uid not in user_and_last_mails.keys():
            user_and_last_mails[uid] = None
        if returned['session']['mails'][0]['id'] != user_and_last_mails[uid]:
            user_and_last_mails[uid] = returned['session']['mails'][0]['id']
            return format_email(returned['session']['mails'][0])
        else:
            return "Вы прочитали все письма..."
    else:
        return "Писем нет..."


def new_address(uid, *args):
    load_domains_if_not_loaded()
    if not args:
        keys_list = list(loaded_domains.keys())
        keyboard = [[] for _ in range(6)]
        cut = len(keys_list) // 6
        for i in range(6):
            for elem in keys_list[cut * i:cut * (i + 1):]:
                keyboard[i].append(InlineKeyboardButton(elem, callback_data=elem))
        markup2 = InlineKeyboardMarkup(keyboard)
        return ["Выберите домен из списка ниже: ", markup2]
    else:
        introduce_session_if_not(uid)
        domain_id = loaded_domains[args[0]]
        sid = users_and_sessions[uid]
        final_req = introduce_address_parts[0] + sid + introduce_address_parts[1] + domain_id + introduce_address_parts[
            2]
        addr_with_key = make_request(final_req)['introduceAddress']
        return f"{addr_with_key['address']} {addr_with_key['restoreKey']}"


def menu():
    return "Вы вернулись в основное меню"


def additional(message=None):
    keyboard = [['Обновить список доменов бота'], ['Пересоздать сессию'], ['Получить мои данные из бота'],
                ['Назад']]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
    if not message:
        return ["Вот дополнительные возможности: ", markup]
    else:
        return [message, markup]


def restore_address(uid, address, restoken):
    introduce_session_if_not(uid)
    built_req = restore_parts[0] + users_and_sessions[uid] + restore_parts[1] + address + restore_parts[2] + restoken + \
                restore_parts[3]
    try:
        result = make_request(built_req)
        if result['restoreAddress']:
            return f"Адрес {address} восстановлен."
    except Exception as ee:
        return str(ee)


def return_user_info(uid):
    session = None
    latest_mail_id = None
    if uid in users_and_sessions.keys():
        session = users_and_sessions[uid]
    if uid in user_and_last_mails.keys():
        latest_mail_id = user_and_last_mails[uid]
    message = f"Ваша сессия: {session}, id вашего последнего письма: {latest_mail_id}"
    return additional(message)


def update_domains(uid):
    if uid == admin_id:
        result = make_request(get_domains)
        for elem in result["domains"]:
            loaded_domains[elem["name"]] = elem["id"]
        x = []
        for key in loaded_domains:
            x.append(f"{key} {loaded_domains[key]}")
        tempf = open("domains.txt", 'w')
        tempf.write("\n".join(x))
        tempf.close()
        return additional("Домены обновлены.")
    else:
        return additional("У вас нет прав для этой операции. Обратитесь к @estubens")


def active_addresses(uid):
    introduce_session_if_not(uid)
    sid = users_and_sessions[uid]
    built_req = ga_addrs[0] + sid + ga_addrs[1]
    return make_request(built_req)


def make_request(req_name):
    transport = AIOHTTPTransport(url="https://mirror2.dropmail.info/api/graphql/" + token) # dropmail.me
    client = Client(transport=transport, fetch_schema_from_transport=True)
    query = gql(req_name)
    result = client.execute(query)
    return result


def fetch_users_messages(uid, message):
    match message:
        case '/start':
            return "Добро пожаловать! Смотрите на клавиатуру Telegram."
        case 'Помощь':
            return spravka
        case 'Проверить входящие':
            return check_new_session_mails(uid)
        case 'Новый адрес':
            return new_address(uid)
        case 'Восстановить адрес':
            return restore_addr_help
        case 'Пересоздать сессию':
            return introduce_session_if_not(uid, True)
        case "Доп. функции":
            return additional()
        case 'Назад':
            return menu()
        case 'Получить мои данные из бота':
            return return_user_info(uid)
        case 'Активные адреса':
            active_addrs = active_addresses(uid)
            tempaddresses = []
            for elem in active_addrs['session']['addresses']:
                tempaddresses.append(f"{elem['address']} {elem['restoreKey']}")
            if tempaddresses:
                return "\n".join(tempaddresses)
            else:
                return "Вы не создали ни одного адреса"
        case "Обновить список доменов бота":
            return update_domains(uid)
        case _:
            if "Восстановить" in message and len(message.split()) == 3:
                lst = message.split()
                return restore_address(uid, lst[1], lst[2])
            else:
                return "Я не знаю такой команды."

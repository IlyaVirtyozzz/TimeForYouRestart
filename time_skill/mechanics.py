from flask_app import db, logging
from time import time
from datetime import datetime
from .constants import *
from .time_change import time_change, tts_change
from .database import TimeFlow, ThingTime, User


def return_previous_info(func):
    def wrapper(req, res, session):
        func(req, res, session)
        res.text = res.text + " " + session["text"]
        res.tts = res.tts + " sil <[300]> " + session["tts"]
        res.buttons = session["buttons"]
        if session["card"]:
            res.card = session["card"]

    return wrapper


def save_previous_session_info(func):
    def wrapper(req, res, session):
        func(req, res, session)
        session["text"] = res.text
        session["tts"] = res.tts
        session["buttons"] = res.buttons
        session["card"] = res.card if res.card else None

    return wrapper


def get_card_menu(req, res, session):
    res.card = menu_card
    res.card["header"]['text'] = res.text
    res.buttons = [BUTTONS['help'], BUTTONS['can']]
    return res.card, res.buttons


def if_time_flow(func):
    def wrapper(req, res, session):
        user = User.get_user(req.user_id)
        timeflow = TimeFlow.get_timeflow(user.id) if user else None
        if timeflow:
            res.text, res.text = choice(time_flow_timeflowing_dialog)
            session["state"] = 8
            res.buttons = [BUTTONS["update"], BUTTONS["stop"]]

        else:
            func(req, res, session)

    return wrapper


def stop_time_flow_mech(thing, timeflow, db):
    this_time = time()
    thing.time = thing.time + (this_time - timeflow.time_start)
    thing.last_time = this_time - timeflow.time_start
    thing.res_last_time = 1
    times = time_change(thing.last_time)
    db.session.delete(timeflow)


def get_items_thing(things_list, session, res):
    res.card = deepcopy(things_list_card)
    res.text = res.card['header']['text'] = ""
    for item in things_list[(session['room'] - 1) * 5: (session['room']) * 5]:
        times_all = time_change(item.time)
        res.card["items"].append({
            "title": "• " + item.name.capitalize(),
            "description": "{}:{}:{}".format(*times_all),
            "button": {
                "text": item.name.capitalize(),
                "payload": {
                    "text": item.name.capitalize()
                }
            }
        })
        res.tts += item.name + "sil <[300]> "
    return res


def get_str_things_list(things_list):
    str_things_list = ""
    for thing in things_list:
        str_things_list += timer_list_thing_dialog[0].format(thing.name.capitalize())
    return str_things_list


def go_start_time_flow(res, user, thing, session):
    session["state"] = 8
    timeflow = TimeFlow.add_thing_flow(user.id, user.thing_id)
    TimeFlow.refresh_last_time(thing, datetime.today())
    text_, tts_ = choice(time_flow_start_start_dialog)
    start_word_text_, start_word_tts_ = choice(time_flow_start_start_words_dialog)
    action_text, action_tts = choice(time_flow_start_actions_dialog)
    text_ = text_.format(thing.name.capitalize())
    tts_ = tts_.format(thing.name)
    res.text, res.tts = "\n".join([text_, start_word_text_, action_text]), " ".join([tts_, start_word_tts_, action_tts])
    res.text = res.text.strip("\n").strip(" ").strip("\n")
    res.buttons = [BUTTONS['update'], BUTTONS['stop']]

    return res, session


def get_all_check(req, things_name):
    maybe_thing = ThingTime.query.filter_by(name=things_name).first()
    any_serv = any(word in things_name.lower().split() for word in SERVICE_WORDS)
    max_check = len(things_name.strip().lower()) > 40
    min_check = len(things_name.strip().lower()) < 5

    all_check = [(any_serv, create_serv_dialog), (maybe_thing, create_repeat_dialog),
                 (req.dangerous_word, create_bitch_dialog),
                 (min_check, create_min_dialog), (max_check, create_max_dialog)]
    items_check = [any_serv, maybe_thing, req.dangerous_word, min_check, max_check]
    return all_check, items_check


def get_menu(req, res, session):
    action_text, action_tts = choice(menu_old_true_actions_dialog)
    if ThingTime.get_things_list(req.user_id):
        text_, tts_ = choice(menu_old_true_list_dialog)
        if User.get_action(req.user_id):
            action_text, action_tts = choice(menu_old_true_actions_dialog)
    else:
        text_, tts_ = choice(menu_old_empty_list_dialog)
        if User.get_action(req.user_id):
            action_text, action_tts = choice(menu_old_empty_actions_dialog)

    res.card = menu_card
    res.card["header"]['text'] = res.text = " ".join([text_, action_text])
    res.tts = " ".join([tts_, action_tts])
    res.buttons = [BUTTONS['help'], BUTTONS['can']]
    session["state"] = 0
    return res, session


def get_menu_things_list_settings(req, res, session, things_list):
    session['state'] = 5
    res.buttons = [BUTTONS['help'], BUTTONS['menu']]
    if req.has_screen:
        res = get_items_thing(things_list, session, res)

        if session['room'] != 1:
            res.buttons.insert(0, BUTTONS["back"])

        if things_list[(session['room'] + 1) * 5:]:
            res.buttons.insert(0, BUTTONS["next"])
    else:
        text_ = tts_ = get_str_things_list(things_list)
        tts_.replace("\n", " sil <[300]> ")
        res.text, res.tts = text_, tts_
    return res, session


def get_menu_things_list(req, res, session):
    things_list = ThingTime.get_things_list(req.user_id)
    if things_list:
        if not session.get('room'):
            session['room'] = 1
        if req.type_click == "ButtonPressed":
            res, session = get_menu_things_list_settings(req, res, session, things_list)
        elif session['state'] == 1:
            text_ = tts_ = get_str_things_list(things_list)
            tts_.replace("\n", " sil <[400]> ")
            res.text, res.tts = text_, tts_
            res.buttons = [BUTTONS['help'], BUTTONS['catalog'], BUTTONS['menu']]
            res.text = res.text.strip("\n").strip(" ").strip("\n")
        else:
            res, session = get_menu_things_list_settings(req, res, session, things_list)
    else:
        session['state'] = 0
        res.text, res.tts = choice(timer_list_zero_dialaog)
        res.buttons = [BUTTONS['add'], BUTTONS['help']]

    return res, session


def get_menu_start_time_list(req, res, session):
    session['room'] = 0

    user = User.get_user(req.user_id)
    things_list = ThingTime.get_things_list(req.user_id)

    if session['state'] == 6:
        thing = ThingTime.get_thing(user.thing_id)
        res, session = go_start_time_flow(res, user, thing, session)
    else:
        if things_list:
            thing = ThingTime.search_thing(req.text, things_list)
            if thing:
                res, session = go_start_time_flow(res, user, thing, session)
            else:
                session['state'] = 1
                if user.help_actions:
                    actions_text_, actions_tts_ = choice(timer_list_start_dialog)
                else:
                    actions_text_, actions_tts_ = '', ''

                text_ = tts_ = get_str_things_list(things_list)
                res.text, res.tts = "\n".join([actions_text_, text_]), "".join([actions_tts_, tts_])
                res.buttons = [BUTTONS['help'], BUTTONS['catalog'], BUTTONS['menu']]
                res.text = res.text.strip("\n").strip(" ").strip("\n")
        else:
            session['state'] = 0
            res.text, res.tts = choice(timer_list_zero_dialaog)
            res.buttons = [BUTTONS['add'], BUTTONS['help']]
    return res, session


def get_menu_add_thing(req, res, session):
    session['room'] = 0
    user = User.get_user(req.user_id)

    things_list = ThingTime.get_things_list(req.user_id)
    if len(things_list) >= 15:
        session['state'] = 3
        text_, tts_ = choice(create_delete_start_dialog)
        res.text, res.tts = text_, tts_
        res.buttons = [BUTTONS['yes'], BUTTONS['no'], BUTTONS['help']]

    else:

        things_name = get_things_name(req.text)
        all_check, items_check = get_all_check(req, things_name)
        if things_name:
            if any(items_check):
                for item in all_check:
                    if item[0]:
                        res.text, res.tts = choice(item[1])
                        res.buttons = [BUTTONS['cancl'], BUTTONS['help']]

                if user.help_actions:
                    actions_text, actions_tts = choice(create_actions_dialog)
                    res.text, res.tts = "\n".join([res.text, actions_text]), " ".join([res.tts, actions_tts])
                else:
                    pass
                session['state'] = 2
            else:
                res, session = to_create_thing(res, session, things_name)

        else:
            session['state'] = 2
            text_, tts_ = choice(create_start_dialog)
            actions_text, actions_tts = "", ""
            if User.get_action(req.user_id):
                actions_text, actions_tts = choice(create_actions_dialog)
            res.text = " ".join([text_, actions_text])
            res.tts = " ".join([tts_, actions_tts])
            res.buttons = [BUTTONS['cancl'], BUTTONS['help']]
    return res, session


def get_buttons_things_list(things_list, session):
    buttons = [BUTTONS["catalog"], BUTTONS["help"], BUTTONS["menu"]]
    if things_list[(session['room']) * 5: (session['room'] + 1) * 5]:
        buttons.insert(0, BUTTONS["next"])
    if session['room'] != 1:
        buttons.insert(0, BUTTONS["back"])

    return buttons


def get_thing_info(res, user, thing):
    times_last = time_change(thing.last_time)
    times_all = time_change(thing.time)
    user.thing_id = thing.id
    thing_menu = choice(things_setting_thing_menu_dialog)
    empty_menu = choice(things_setting_empty_thing_menu_dialog)
    if thing.time:
        res.text = thing_menu[0].format(thing.name.capitalize(), *times_all, *times_last)
        res.tts = thing_menu[1].format(thing.name, tts_change(*times_all), tts_change(*times_last))
    else:
        res.text = empty_menu[0].format(thing.name.capitalize())
        res.tts = empty_menu[1].format(thing.name.capitalize())
    if user.help_actions:
        action = choice(things_setting_actions_dialog)
        res.text += "\n" + action[0]
        res.tts += "sil <[400]>" + action[1]

    res.buttons = [BUTTONS["start"], BUTTONS["time"], BUTTONS["delete"], BUTTONS["catalog"], BUTTONS["menu"],
                   BUTTONS["help"]]
    if thing.res_last_time == 1:
        res.buttons.insert(2, BUTTONS["cancel"])
    elif thing.res_last_time == 2:
        res.buttons.insert(2, BUTTONS["return"])
    else:
        pass
    return res


def before_delete(res, thing, session):
    session["state"] = 7
    text_, tts_ = choice(things_setting_want_del_dialog)
    res.text, res.tts = text_.format(thing.name.capitalize()), tts_.format(thing.name.capitalize())
    res.buttons = [BUTTONS["yes"], BUTTONS["no"]]
    return res, session


def deletes_things(req, res, session, things_list):
    if any(word in req.text.lower().strip() for word in [x.name.lower() for x in things_list]):
        session['state'] = 2

        thing = ThingTime.search_thing(req.text, things_list)
        db.session.delete(thing)
        text_, tts_ = choice(create_delete_thing_after_dialog)
        res.text, res.tts = text_.format(thing.name.capitalize()), tts_.format(thing.name.capitalize())
    else:
        res.text, res.tts = choice(create_delete_thing_else_dialog)

    res.buttons = [BUTTONS["cancl"], BUTTONS["help"]]
    return res, session


def to_create_thing(res, session, things_name):
    session['state'] = 10
    session['create_thing'] = things_name
    text_, tts_ = choice(create_to_create_start_dialog)
    res.text = text_.format(things_name)
    res.tts = tts_.format(things_name)
    res.buttons = [BUTTONS['yes'], BUTTONS['no']]
    return res, session


def get_things_name(command):
    command = command.lower().strip().split()
    for i in ['алиса', "алис", "алиска"]:
        try:
            command.remove(i)
        except ValueError:
            pass

    for i in ['дела', "дело"]:
        try:
            command.remove(i)
            break
        except ValueError:
            pass

    for i in CREATE:
        try:
            command.remove(i)
            break
        except ValueError:
            pass

    return " ".join(command).capitalize()


def main_menu_click(func):
    def wrapper(req, res, session):
        if req.type_click == "ButtonPressed":
            not_menu_click = True
            for i in [('Мои дела', get_menu_things_list), ('Добавить дело', get_menu_add_thing),
                      ('Засечь время', get_menu_start_time_list)]:
                if i[0] == req.text:
                    not_menu_click = False
                    i[1](req, res, session)
            if not_menu_click:
                func(req, res, session)
        else:
            func(req, res, session)

    return wrapper

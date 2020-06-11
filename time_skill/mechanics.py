from flask_app import db
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


def get_thing_menu(thing, user, res, session):
    times_last = time_change(thing.last_time)
    times_all = time_change(thing.time)
    session["state"] = 6
    user.thing_id = thing.id
    thing_menu = choice(things_setting_thing_menu_dialog)
    if thing.time:
        res.text = thing_menu[0].format(
            thing.name.capitalize(), *times_all, *times_last)
        res.tts = thing_menu[1].format(
            thing.name, tts_change(*times_all), tts_change(*times_last))
    else:
        res.text = things_setting_empty_thing_menu_dialog.format(thing.name.capitalize())
        res.tts = things_setting_empty_thing_menu_dialog.format(thing.name.capitalize())
    if user.help_actions:
        action = choice(DIALOGS_CONTENT["dialogs"]["usersthing"]["-1"]["actions"])
        res.text += action[0]
        res.tts += "sil <[400]>" + action[1]

    res.buttons = [BUTTONS["start"], BUTTONS["time"], BUTTONS["delete"], BUTTONS["catalog"], BUTTONS["menu"],
                   BUTTONS["help"]]
    if thing.res_last_time == 1:
        res.buttons.insert(2, BUTTONS["cancel"])
    elif thing.res_last_time == 2:
        res.buttons.insert(2, BUTTONS["return"])
    else:
        pass

    return res, session


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
    res.buttons = [BUTTONS['update'], BUTTONS['stop']]

    return res, session


def get_all_check(req):
    not_alice_text = req.text.lower().replace('алиса', "")
    maybe_thing = ThingTime.query.filter_by(name=not_alice_text).first()
    any_serv = any(word in req.tokens for word in SERVICE_WORDS)
    max_check = len(not_alice_text.strip().lower()) > 40
    min_check = len(not_alice_text.strip().lower()) < 5

    all_check = [(any_serv, create_serv_dialog), (maybe_thing, create_repeat_dialog),
                 (req.dangerous_word, create_bitch_dialog),
                 (min_check, create_min_dialog), (max_check, create_max_dialog)]
    items_check = [any_serv, maybe_thing, req.dangerous_word, min_check, max_check]
    return all_check, items_check, not_alice_text


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
            tts_.replace("\n", " sil <[300]> ")
            res.text, res.tts = text_, tts_
            res.buttons = [BUTTONS['help'], BUTTONS['catalog'], BUTTONS['menu']]
        else:
            res, session = get_menu_things_list_settings(req, res, session, things_list)
    else:
        session['state'] = 0
        res.text, res.tts = choice(timer_list_zero_dialaog)
        res.buttons = [BUTTONS['add'], BUTTONS['help']]
    return res, session


def get_buttons_things_list(things_list, session):
    buttona = [BUTTONS["catalog"], BUTTONS["help"], BUTTONS["menu"]]
    if things_list[(session['room']) * 5: (session['room'] + 1) * 5]:
        buttona.insert(0, BUTTONS["next"])
    if session['room'] != 1:
        buttona.insert(0, BUTTONS["back"])

    return buttona


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




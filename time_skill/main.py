from base_skill.skill import *
from .mechanics import *
from flask_app import db

handler = CommandHandler()


class TimeSkill(BaseSkill):
    name = 'time_skill'
    command_handler = handler


all_states = (0, 1, 3, 4, 5, 6, 7, 8, 9)


@handler.hello_command
@save_previous_session_info
@if_time_flow
def hello(req, res, session):
    hello_text, hello_tts = choice(menu_hello_dialog)
    user = User.get_user(req.user_id)
    things_list = ThingTime.get_things_list(req.user_id)
    time_flow = TimeFlow.get_timeflow(req.user_id)
    actions_text, actions_tts = "", ""
    session['state'] = 0
    if not user:
        user = User.add_new_user(req.user_id)
        text_, tts_ = choice(menu_new_user_dialog)
        res.text = " ".join([hello_text, text_])
        res.tts = " ".join([hello_tts, tts_])
        res.card, res.buttons = get_card_menu(req, res, session)
    else:
        if not things_list:
            text_, tts_ = choice(menu_new_empty_list_dialog)
            if user.help_actions:
                actions_text, actions_tts = choice(menu_new_empty_actions_dialog)
            else:
                actions_text, actions_tts = "", ""
            res.text = " ".join([hello_text, text_, actions_text])
            res.tts = " ".join([hello_tts, tts_, actions_tts])
            res.card, res.buttons = get_card_menu(req, res, session)
        else:
            if time_flow:
                text_, tts_ = choice(time_flow_start_new_session_dialog)
                if user.help_actions:
                    actions_text, actions_tts = choice(menu_new_true_actions_dialog)
                else:
                    actions_text, actions_tts = "", ""
                res.text = "\n".join([hello_text, text_, actions_text])
                res.tts = " ".join([hello_tts, tts_, actions_tts])
                res.buttons = [BUTTONS["update"], BUTTONS["stop"]]
            else:
                if req.text:
                    command = req.text
                    thing = ThingTime.search_thing(command, things_list)
                    if thing:
                        res, session = go_start_time_flow(res, user, thing, session)
                    else:
                        session['state'] = 1
                        res.text, res.tts = choice(menu_not_found_dialog)
                        res.buttons = [BUTTONS['help'], BUTTONS['catalog'], BUTTONS['menu']]
                else:
                    text_, tts_ = choice(menu_new_true_list_dialog)
                    if user.help_actions:
                        actions_text, actions_tts = choice(menu_new_true_actions_dialog)
                    else:
                        actions_text, actions_tts = "", ""
                    res.text = " ".join([hello_text, text_, actions_text])
                    res.tts = " ".join([hello_tts, tts_, actions_tts])
                    res.card, res.buttons = get_card_menu(req, res, session)


"""-----------------All_room_commands--(0)-----------------"""


@handler.command(words=SETTINGS, states=all_states)
@save_previous_session_info
@if_time_flow
def settings_thing(req, res, session):
    user = User.get_user(req.user_id)
    things_list = ThingTime.get_things_list(req.user_id)

    if things_list:
        thing = ThingTime.search_thing(req.text, things_list)
        if thing:
            user.thing_id = thing.id
            session["state"] = 6
            res = get_thing_info(res, user, thing)
        else:
            res, session = get_menu(req, res, session)
            res.text, res.tts = choice(menu_not_found_dialog)
            res.card["header"]['text'] = res.text
    else:
        session['state'] = 0
        res.text, res.tts = choice(timer_list_zero_dialaog)
        res.buttons = [BUTTONS['add'], BUTTONS['help']]


@handler.command(words=EXIT, states=all_states)
@save_previous_session_info
def to_exit(req, res, session):
    res.text, res.tts = choice(exit_dialog)
    res.end_session = True


@handler.command(words=CAN, states=all_states)
@save_previous_session_info
def what_can_you_do(req, res, session):
    res.text, res.tts = choice(menu_can_dialog)
    res.buttons = session["buttons"]


@handler.command(words=MANUAL, states=all_states)
@save_previous_session_info
def get_manual(req, res, session):
    res.text, res.tts = choice(manual_dialog)
    res.buttons = session["buttons"]


@handler.command(words=HINT, states=all_states)
@return_previous_info
def hint(req, res, session):
    user = User.get_user(req.user_id)
    if any(word in req.tokens for word in OFF):
        res.text, res.tts = choice(hint_off_dialogs)

        user.help_actions = False
    else:
        res.text, res.tts = choice(hint_on_dialogs)
        user.help_actions = True


@handler.command(words=HELP, states=all_states)
@save_previous_session_info
def get_help(req, res, session):
    item_help = helps_all[str(session["state"])]
    res.text, res.tts = choice(item_help['help'])
    if item_help['buttons']:
        res.buttons = item_help['buttons']
    else:
        res.buttons = session["buttons"]


@handler.command(words=MENU, states=all_states)
@save_previous_session_info
@if_time_flow
def go_main_menu(req, res, session):
    session['room'] = 0
    res, session = get_menu(req, res, session)


@handler.command(words=REPEAT, states=all_states)
def repeat_all(req, res, session):
    if any(word in req.tokens for word in THING_LIST):
        res, session = get_menu_things_list(req, res, session)
    else:
        res.text, res.tts = session["text"], session["tts"]
        res.buttons = session["buttons"]
        if session.get("card", ""):
            res.card = session["card"]


@handler.command(words=CREATE, states=all_states)
@save_previous_session_info
@if_time_flow
def menu_add_thing(req, res, session):
    res, session = get_menu_add_thing(req, res, session)


@handler.command(words=THING_LIST, states=all_states)
@save_previous_session_info
@if_time_flow
def menu_things_list(req, res, session):
    res, session = get_menu_things_list(req, res, session)


@handler.command(words=START_TIME, states=all_states)
@save_previous_session_info
@if_time_flow
def menu_start_time_list(req, res, session):
    res, session = get_menu_start_time_list(req, res, session)


@handler.command(words=DELETE, states=all_states)
@save_previous_session_info
@if_time_flow
def delete_thing(req, res, session):
    user = User.get_user(req.user_id)
    things_list = ThingTime.get_things_list(req.user_id)

    if session['state'] == 6:
        thing = ThingTime.get_thing(user.thing_id)
        res, session = before_delete(res, thing, session)

    else:
        if things_list:
            thing = ThingTime.search_thing(req.text, things_list)
            if thing:
                res, session = before_delete(res, thing, session)
            else:
                res, session = get_menu(req, res, session)
                res.text, res.tts = choice(menu_not_found_dialog)
                res.card["header"]['text'] = res.text
        else:
            session['state'] = 0
            res.text, res.tts = choice(timer_list_zero_dialaog)
            res.buttons = [BUTTONS['add'], BUTTONS['help']]


@handler.undefined_command(states=0)
@save_previous_session_info
@if_time_flow
@main_menu_click
def undefined_menu_thing(req, res, session):
    session['room'] = 0
    res, session = get_menu(req, res, session)


"""-----------------Start_time_commands--(1)-----------------"""


@handler.undefined_command(states=1)
@save_previous_session_info
@if_time_flow
@main_menu_click
def undefined_start_time(req, res, session):
    user = User.get_user(req.user_id)
    things_list = ThingTime.get_things_list(req.user_id)
    thing = ThingTime.search_thing(req.text, things_list)
    if thing:
        user.thing_id = thing.id
        res, session = go_start_time_flow(res, user, thing, session)
    else:
        res.text, res.tts = choice(timer_list_else_dialog)
        res.buttons = [BUTTONS["catalog"], BUTTONS["help"], BUTTONS["menu"]]


"""-----------------Create_thing_commands--(2)-----------------"""


@handler.command(words=CANCEL, states=(2, 3, 4))
@save_previous_session_info
@if_time_flow
def cancel_add_thing(req, res, session):
    res, session = get_menu(req, res, session)


@handler.undefined_command(states=2)
@save_previous_session_info
@if_time_flow
@main_menu_click
def undefined_create_thing(req, res, session):
    user = User.get_user(req.user_id)

    if any(word in req.tokens for word in HELP):
        item_help = helps_all[str(session["state"])]
        res.text, res.tts = choice(item_help['help'])
        if item_help['buttons']:
            res.buttons = item_help['buttons']
        else:
            res.buttons = session["buttons"]
    else:
        things_name = get_things_name(req.text)
        all_check, items_check = get_all_check(req, things_name)
        if any(items_check):
            for item in all_check:
                if item[0]:
                    res.text, res.tts = choice(item[1])
                    res.buttons = session["buttons"]

            if user.help_actions:
                actions_text, actions_tts = choice(create_actions_dialog)
                res.text, res.tts = "\n".join([res.text, actions_text]), " ".join([res.tts, actions_tts])
            else:
                pass
        else:
            res, session = to_create_thing(res, session, things_name)


"""-----------------Start_created_thing_commands--(9)-----------------"""


@handler.command(words=NO, states=9)
@save_previous_session_info
@if_time_flow
def no_start_created(req, res, session):
    res, session = get_menu(req, res, session)


@handler.command(words=YES, states=9)
@save_previous_session_info
@if_time_flow
def yes_start_created(req, res, session):
    user = User.get_user(req.user_id)
    thing = ThingTime.get_thing(user.thing_id)
    res, session = go_start_time_flow(res, user, thing, session)


@handler.undefined_command(states=9)
@save_previous_session_info
@if_time_flow
@main_menu_click
def undefined_delete_thing(req, res, session):
    res.text, res.tts = choice(create_start_help_dialog)
    res.buttons = [BUTTONS["yes"], BUTTONS["no"], BUTTONS["help"]]


"""-----------------Delete_created_thing_commands--(3)-----------------"""


@handler.command(words=NO, states=3)
@save_previous_session_info
@if_time_flow
def no_delete_created(req, res, session):
    res, session = get_menu(req, res, session)


@handler.command(words=YES, states=3)
@save_previous_session_info
@if_time_flow
def yes_delete_created(req, res, session):
    session['state'] = 4
    things_list = ThingTime.get_things_list(req.user_id)
    text_, tts_ = choice(create_delete_thing_start_dialog)
    things_text = things__tts = get_str_things_list(things_list)
    res.text, res.tts = "\n".join([text_, things_text]), "".join([tts_, things__tts])
    res.buttons = [BUTTONS["cancl"], BUTTONS["help"]]


@handler.undefined_command(states=3)
@save_previous_session_info
@if_time_flow
@main_menu_click
def undefined_delete_created(req, res, session):
    res.text, res.tts = choice(create_delete_help_dialog)
    res.buttons = [BUTTONS["yes"], BUTTONS["no"], BUTTONS["help"]]


"""-----------------Delete_created_things_list_commands--(4)-----------------"""


@handler.undefined_command(states=4)
@save_previous_session_info
@if_time_flow
@main_menu_click
def undefined_delete_created_list(req, res, session):
    user = User.get_user(req.user_id)
    things_list = ThingTime.get_things_list(req.user_id)

    res, session = deletes_things(req, res, session, things_list)


"""-----------------Things_list_commands--(5)-----------------"""


@handler.command(words=NEXT, states=5)
@save_previous_session_info
@if_time_flow
def next_things_list(req, res, session):
    things_list = ThingTime.get_things_list(req.user_id)
    session['state'] = 5
    if req.has_screen:
        if things_list[(session['room']) * 5: (session['room'] + 1) * 5]:
            session['room'] += 1
        res = get_items_thing(things_list, session, res)
        res.buttons = get_buttons_things_list(things_list, session)
    else:
        text_ = tts_ = get_str_things_list(things_list)
        res.text, res.tts = text_
        res.buttons = [BUTTONS['help'], BUTTONS['menu']]


@handler.command(words=BACK, states=5)
@save_previous_session_info
@if_time_flow
def back_things_list(req, res, session):
    things_list = ThingTime.get_things_list(req.user_id)
    session['state'] = 5
    if req.has_screen:
        if things_list[(session['room'] - 2) * 5: (session['room'] - 1) * 5]:
            session['room'] -= 1
        res = get_items_thing(things_list, session, res)
        res.buttons = get_buttons_things_list(things_list, session)
    else:
        text_ = tts_ = get_str_things_list(things_list)
        res.text, res.tts = text_
        res.buttons = [BUTTONS['help'], BUTTONS['menu']]


@handler.undefined_command(states=5)
@save_previous_session_info
@if_time_flow
@main_menu_click
def undefined_things_list(req, res, session):
    user = User.get_user(req.user_id)
    things_list = ThingTime.get_things_list(req.user_id)
    thing = ThingTime.search_thing(req.text, things_list)
    if thing:
        user.thing_id = thing.id
        session["state"] = 6
        res = get_thing_info(res, user, thing)
    else:
        res.text, res.tts = choice(things_list_else_dialog)
        res.buttons = [BUTTONS["catalog"], BUTTONS["help"], BUTTONS["menu"]]


"""-----------------Settings_thing_commands--(6)-----------------"""


@handler.command(words=TIME, states=6)
@save_previous_session_info
@if_time_flow
def thing_info(req, res, session):
    user = User.get_user(req.user_id)
    thing = ThingTime.get_thing(user.thing_id)
    session["state"] = 6
    res = get_thing_info(res, user, thing)


@handler.command(words=CANCEL, states=6)
@save_previous_session_info
@if_time_flow
def cancel_last_time(req, res, session):
    user = User.get_user(req.user_id)
    thing = ThingTime.get_thing(user.thing_id)

    if thing.res_last_time == 0:
        text_, tts_ = choice(things_setting_none_cancel_dialog)
    elif thing.res_last_time == 2:
        text_, tts_ = choice(things_setting_unsuc_cancel_dialog)
    else:
        thing.time = thing.time - thing.last_time
        thing.res_last_time = 2
        text_, tts_ = choice(things_setting_suc_cancel_dialog)

    if user.help_actions:
        action_text, action_tts = choice(things_setting_actions_dialog)
    else:
        action_text, action_tts = "", ""
    res.text = " ".join([text_, action_text])
    res.tts = "sil <[400]>".join([tts_, action_tts])
    res.buttons = [BUTTONS["start"], BUTTONS["time"], BUTTONS["delete"], BUTTONS["catalog"], BUTTONS["menu"],
                   BUTTONS["help"]]
    if thing.res_last_time == 1:
        res.buttons.insert(2, BUTTONS["cancel"])
    elif thing.res_last_time == 2:
        res.buttons.insert(2, BUTTONS["return"])
    else:
        pass


@handler.command(words=RETURN, states=6)
@save_previous_session_info
@if_time_flow
def return_last_time(req, res, session):
    user = User.get_user(req.user_id)
    thing = ThingTime.get_thing(user.thing_id)

    if thing.res_last_time == 2:
        thing.time = thing.time + thing.last_time
        thing.res_last_time = 1
        text_, tts_ = choice(things_setting_suc_return_dialog)
    else:
        text_, tts_ = choice(things_setting_unsuc_return_dialog)

    if user.help_actions:
        action_text, action_tts = choice(things_setting_actions_dialog)
    else:
        action_text, action_tts = "", ""
    res.text = " ".join([text_, action_text])
    res.tts = " ".join([tts_, action_tts])
    res.buttons = [BUTTONS["start"], BUTTONS["time"], BUTTONS["delete"], BUTTONS["catalog"], BUTTONS["menu"],
                   BUTTONS["help"]]
    if thing.res_last_time == 1:
        res.buttons.insert(2, BUTTONS["cancel"])
    elif thing.res_last_time == 2:
        res.buttons.insert(2, BUTTONS["return"])
    else:
        pass


@handler.undefined_command(states=6)
@save_previous_session_info
@if_time_flow
@main_menu_click
def undefined_settings_thing(req, res, session):
    user = User.get_user(req.user_id)
    thing = ThingTime.get_thing(user.thing_id)

    res.text, res.tts = choice(things_setting_help_dialog)
    res.buttons = [BUTTONS["start"], BUTTONS["time"], BUTTONS["delete"], BUTTONS["catalog"], BUTTONS["menu"],
                   BUTTONS["help"]]

    if thing.res_last_time == 1:
        res.buttons.insert(2, BUTTONS["cancel"])
    elif thing.res_last_time == 2:
        res.buttons.insert(2, BUTTONS["return"])
    else:
        pass


"""-----------------Delete_thing_commands--(7)-----------------"""


@handler.command(words=NO, states=7)
@save_previous_session_info
@if_time_flow
def no_delete(req, res, session):
    res, session = get_menu(req, res, session)


@handler.command(words=YES, states=7)
@save_previous_session_info
@if_time_flow
def yes_delete(req, res, session):
    user = User.get_user(req.user_id)
    thing = ThingTime.query.filter_by(id=user.thing_id).first()
    db.session.delete(thing)
    res, session = get_menu(req, res, session)

    res.text = "Занятие удалено!\n" + res.text
    res.card["header"]['text'] = "Занятие удалено!"
    res.tts = "Занятие удалено! sil <[200]> " + res.tts


@handler.undefined_command(states=7)
@save_previous_session_info
@if_time_flow
@main_menu_click
def undefined_delete_thing(req, res, session):
    res.text, res.tts = choice(things_del_help_dialog)
    res.buttons = [BUTTONS["yes"], BUTTONS["no"]]


"""-----------------Time_flow_commands--(8)-----------------"""


@handler.command(words=STOP, states=8)
@save_previous_session_info
def stop_time_flow(req, res, session):
    user = User.get_user(req.user_id)
    timeflow = TimeFlow.get_timeflow(user.id)
    thing = ThingTime.get_thing(timeflow.thing_id)
    times = time_change(time() - timeflow.time_start)

    text_, tts_ = choice(time_flow_stop_dialog)
    text_, tts_ = text_.format(thing.name.capitalize(), *times), tts_.format(thing.name, tts_change(*times))
    victory_text, victory_tts = choice(time_flow_stop_victory_dialog)
    actions_text, actions_tts = "", ""
    if user.help_actions:
        actions_text, actions_tts = choice(time_flow_stop_actions_dialog)

    session["state"] = 0
    stop_time_flow_mech(thing, timeflow, db)
    res.text = "\n".join([text_, victory_text, actions_text])
    res.tts = " ".join([tts_, victory_tts, actions_tts])
    res.buttons = [BUTTONS["list"], BUTTONS["add"], BUTTONS["start"], BUTTONS["help"], BUTTONS["can"]]


@handler.command(words=UPDATE, states=8)
@save_previous_session_info
def update_time_flow(req, res, session):
    user = User.get_user(req.user_id)
    timeflow = TimeFlow.get_timeflow(user.id)
    thing = ThingTime.get_thing(timeflow.thing_id)

    times = time_change(time() - timeflow.time_start)
    text_, tts_ = choice(time_flow_update_dialog)
    res.text, res.tts = text_.format(thing.name.capitalize(), *times), tts_.format(thing.name, tts_change(*times))

    res.buttons = [BUTTONS["update"], BUTTONS["stop"]]


@handler.undefined_command(states=8)
@save_previous_session_info
def undefined_time_flow(req, res, session):
    res.text, res.tts = choice(time_flow_help_dialog)
    res.buttons = [BUTTONS["update"], BUTTONS["stop"]]


"""-----------------To_create_commands--(10)-----------------"""


@handler.command(words=NO, states=10)
@save_previous_session_info
@if_time_flow
def no_create(req, res, session):
    session["state"] = 2
    text_, tts_ = choice(create_start_dialog)
    actions_text, actions_tts = "", ""
    if User.get_action(req.user_id):
        actions_text, actions_tts = choice(create_actions_dialog)
    res.text = " ".join([text_, actions_text])
    res.tts = " ".join([tts_, actions_tts])
    res.buttons = [BUTTONS['cancl'], BUTTONS['help']]


@handler.command(words=YES, states=10)
@save_previous_session_info
@if_time_flow
def yes_create(req, res, session):
    user = User.get_user(req.user_id)
    session["state"] = 9
    thing = ThingTime.add_new_thing(req.user_id, session['create_thing'])
    user.thing_id = thing.id
    res.text, res.tts = choice(create_created_dialog)
    res.buttons = [BUTTONS["yes"], BUTTONS["no"], BUTTONS["help"]]


@handler.undefined_command(states=10)
@save_previous_session_info
@main_menu_click
def undefined_created(req, res, session):
    res.text, res.tts = choice(create_to_create_help_dialog)
    res.text = res.text.format(session['create_thing'])
    res.tts = res.tts.format(session['create_thing'])
    res.buttons = [BUTTONS["yes"], BUTTONS["no"]]

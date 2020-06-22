import json, logging,pymorphy2
from base_skill.skill import Response, Request
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqldatabase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'key?'
db = SQLAlchemy(app)

from time_skill.main import TimeSkill

SKILLS = [TimeSkill()]
skill_dict = {skill.name: skill for skill in SKILLS}
sessionStorage = {
    skill.name: {} for skill in SKILLS
}


@app.route('/<skill>', methods=['POST'])
def main(skill):
    if skill in skill_dict:
        req = request.json
        return handle_dialog(req, skill_dict[skill])
    return '404'


def prepare_res(req):
    return {
        'session': req['session'],
        'version': req['version'],
        'response': {
            'end_session': False
        }
    }


def block_ping(req, res):
    if req.text == 'ping':
        res.text = 'Всё работает'
        return True
    return False


def handle_dialog(req, skill):
    res = Response(prepare_res(req))
    req = Request(req)
    session = sessionStorage[skill.name]
    user_id = req.user_id

    if not block_ping(req, res):
        if req.new_session:
            session[user_id] = {'state': 0}
            skill.command_handler.hello.execute(req=req, res=res, session=session[user_id])
        else:
            if user_id not in session:
                session[user_id] = {'state': 0}

            skill.command_handler.execute(req=req, res=res, session=session[user_id])

        skill.log(req=req, res=res, session=session[user_id])

    db.session.commit()
    return json.dumps(res.res)

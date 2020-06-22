from time import time
from datetime import datetime
from flask_app import db, pymorphy2

morph = pymorphy2.MorphAnalyzer()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=False, nullable=False)
    step_passage = db.Column(db.Integer, unique=False, nullable=False)
    step_room = db.Column(db.Integer, unique=False, nullable=False)
    thing_id = db.Column(db.Integer, unique=False, nullable=True)
    help_actions = db.Column(db.Boolean, unique=False, nullable=True)

    def __repr__(self):
        return "<User {} {} {} {}>".format(self.id, self.user_id, self.thing_id, self.help_actions)

    @staticmethod
    def get_action(user_id):
        user = db.session.query(User).filter_by(user_id=user_id).first()
        return user.help_actions

    @staticmethod
    def add_new_user(user_id):
        user = User(user_id=user_id, step_passage=0, step_room=0, help_actions=True)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def get_thing_id(user):
        return ThingTime.query.filter_by(id=user.thing_id).first()

    @staticmethod
    def get_user(user_id):
        user = db.session.query(User).filter_by(user_id=user_id).first()
        return user

    @staticmethod
    def create_user(user_id):
        ThingTime.add_new_user(user_id)
        user = db.session.query(User).filter_by(user_id=user_id).first()
        return user


class TimeFlow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=False, nullable=False)
    thing_id = db.Column(db.Integer, unique=False, nullable=False)
    time_start = db.Column(db.Integer, unique=False, nullable=False)

    def __repr__(self):
        return "<TimeFlow {} {} {}>".format(self.id, self.user_id, self.time_start)

    @staticmethod
    def add_thing_flow(user_id, thing_id):
        timeflow = TimeFlow(user_id=user_id, thing_id=thing_id, time_start=time())
        db.session.add(timeflow)
        db.session.commit()
        return timeflow

    @staticmethod
    def get_timeflow(user_id):
        timeflow = TimeFlow.query.filter_by(user_id=user_id).first()
        return timeflow

    @staticmethod
    def refresh_last_time(thing, date_time):
        thing.last_data = date_time
        db.session.commit()


class ThingTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=False, nullable=False)
    name = db.Column(db.String, unique=False, nullable=False)
    time = db.Column(db.Integer, unique=False, nullable=False)
    last_time = db.Column(db.Integer, unique=False, nullable=False)
    res_last_time = db.Column(db.Integer, unique=False, nullable=False)
    last_data = db.Column(db.DateTime, unique=False, nullable=False)

    def __repr__(self):
        return "<ThingTime {} {} {} {} {} {} {}>".format(self.id, self.user_id, self.name, self.time,
                                                         self.res_last_time, self.last_time, self.last_data)

    @staticmethod
    def get_things_list(user_id):
        things_list = ThingTime.query.filter_by(user_id=user_id).order_by(ThingTime.last_data).all()[::-1]
        return things_list

    @staticmethod
    def get_thing(thing_id):
        thing = ThingTime.query.filter_by(id=thing_id).first()
        return thing

    @staticmethod
    def add_new_thing(user_id, command):
        thing = ThingTime(user_id=user_id, name=command.lower().strip(), time=0, last_time=0, res_last_time=0,
                          last_data=datetime.today())
        db.session.add(thing)
        db.session.commit()
        return thing

    @staticmethod
    def search_thing(command, things_list):
        command = command.lower().strip()

        for thing in things_list:
            if thing.name.lower().strip().replace(" ", "") in command.replace(" ", ""):
                return thing
        for thing in things_list:
            if all(word in [morph.parse(x)[0].normal_form for x in command.split()]
                   for word in [morph.parse(x)[0].normal_form for x in thing.name.lower().strip().split()]):
                return thing

        return False


if __name__ == '__main__':
    db.create_all()

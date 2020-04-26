from gino import Gino

db = Gino()

class LoginTable(db.Model):
	__tablename__ = "logins"

	id = db.Column(db.Integer(), primary_key=True)
	player_id = db.Column(db.Integer())
	username = db.Column(db.Unicode())
	timestamp = db.Column(db.Unicode())
	ip = db.Column(db.Unicode())

class UserTable(db.Model):
	__tablename__ = "users"

	id = db.Column(db.Integer(), primary_key=True)

	username = db.Column(db.Unicode())
	password = db.Column(db.Unicode())
	login_key = db.Column(db.Unicode())

	color = db.Column(db.Integer())
	head = db.Column(db.Integer())
	face = db.Column(db.Integer())
	neck = db.Column(db.Integer())
	body = db.Column(db.Integer())
	hand = db.Column(db.Integer())
	feet = db.Column(db.Integer())
	pin = db.Column(db.Integer())
	background = db.Column(db.Integer())
	coins = db.Column(db.Integer())

class ItemTable(db.Model):
	__tablename__ = "items"

	player_id = db.Column(db.Integer())
	item_id = db.Column(db.Integer())

class BuddyTable(db.Model):
	__tablename__ = "buddies"

	player_id = db.Column(db.Integer())
	buddy_id = db.Column(db.Integer())
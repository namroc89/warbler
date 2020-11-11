"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


from app import app, CURR_USER_KEY
import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new",
                          data={"text": "Hello"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")
            self.assertEqual(len(Message.query.all()), 1)
            self.assertIn("<p>Hello</p>", html)

    def test_delete_message(self):
        """Can a logged in user delete own messages"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            msg = Message(text="Hola!", user_id=self.testuser.id)
            msgid = 123
            msg.id = msgid
            msg2 = Message(text="Hello!", user_id=self.testuser.id)
            msgid2 = 1123
            msg2.id = msgid2
            db.session.add_all([msg, msg2])
            db.session.commit()

            resp = c.post("/messages/123/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(Message.query.all()), 1)
            self.assertIn("<p>Hello!</p>", html)

    def test_logged_out_add(self):
        """Can a logged out user add a message"""
        with self.client as c:
            resp = c.post("/messages/new",
                          data={"text": "Hello"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_logged_out_add(self):
        """Can a logged out user delete a message"""
        with self.client as c:

            msg2 = Message(text="Hello!", user_id=self.testuser.id)
            msgid2 = 1123
            msg2.id = msgid2
            db.session.add(msg2)
            db.session.commit()

            resp = c.post("/messages/1123/delete",
                          follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)
            self.assertIsNotNone(Message.query.get(1123))

    def test_wrong_user_add(self):
        """Can invalid user add message"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 111111111

            resp = c.post("/messages/new",
                          data={"text": "hello"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_wrong_user_delete(self):
        """Can other user delete message"""
        u = User.signup(username="tester",
                        email="test@tt.com",
                        password="testuser",
                        image_url=None)

        u.id = 12345
        msg2 = Message(text="Hello!", user_id=self.testuser.id)
        msgid2 = 1123
        msg2.id = msgid2
        db.session.add_all([msg2, u])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 12345

            resp = c.post("/messages/1123/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

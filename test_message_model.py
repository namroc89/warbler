"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app  # noqa
# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class MessageModelTestCase(TestCase):
    """Test Message model"""

    def setUp(self):
        """Create test client and sample data"""

        db.drop_all()
        db.create_all()

        u = User.signup("test1", "email@email.com", "password", None)
        uid = 1234
        u.id = uid

        db.session.commit()

        self.u = User.query.get(uid)

        self.uid = uid

        # self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        """Does the basic model work"""
        m = Message(
            text="testtesttest", user_id=self.uid
        )
        db.session.add(m)
        db.session.commit()

        self.assertEqual(m.text, "testtesttest")
        self.assertEqual(self.u.messages[0].text, "testtesttest")
        self.assertEqual(len(self.u.messages), 1)
        self.assertTrue(m.timestamp)

    def test_invalid_text_input(self):
        """test error given if user input is invalid"""
        m = Message(
            text=None, user_id=self.uid
        )
        db.session.add(m)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_user_input(self):
        """test error given if user input is invalid"""
        m = Message(
            text=None, user_id=None
        )
        db.session.add(m)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

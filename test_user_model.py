"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


from app import app
import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

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


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        u1 = User.signup("test1", "email@email.com", "password", None)
        uid1 = 1234
        u1.id = uid1

        u2 = User.signup("test2", "email2@email.com", "password", None)
        uid2 = 2234
        u2.id = uid2

        db.session.commit()

        u1 = User.query.get(uid1)
        u2 = User.query.get(uid2)

        self.u1 = u1
        self.uid1 = uid1

        self.u2 = u2
        self.uid2 = uid2

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers. The user model should create specified user
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    # Follow Tests ##################

    def test_user_follows(self):
        """User added succesfully to follow/follower"""

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u1.following), 1)
        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u2.followers), 1)

        self.assertEqual(self.u1.following[0].id, self.u2.id)
        self.assertEqual(self.u2.followers[0].id, self.u1.id)

    def test_is_followed_by(self):
        """Test is_followed_by detects user is being followed"""
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))

    def test_is_following(self):
        """Test is_following detects user following another"""
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

    # User sign up tests ######################

    def test_valid_signup(self):
        """tests if user can sign up with valid inputs"""

        valid_user = User.signup(
            "validuser", "goodemail@email.com", "Password", None)
        uid = 56789
        valid_user.id = uid
        db.session.commit()

        v_user = User.query.get(uid)

        self.assertEqual(v_user.username, "validuser")
        self.assertEqual(v_user.email, "goodemail@email.com")
        self.assertNotEqual(v_user.password, "Password")
        self.assertEqual(v_user.image_url, "/static/images/default-pic.png")
        self.assertTrue(v_user.password.startswith("$2b$"))

    def test_invalid_username(self):
        """tests to see if error is thrown when invalid username is used"""
        invalid_user = User.signup(None, "emailss@smail.com", "password", None)
        uid = 1244546457
        invalid_user.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email(self):
        """tests to see if error is thrown when invalid email is used"""
        invalid_user = User.signup("testtest", None, "password", None)
        uid = 1244546457
        invalid_user.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_pass(self):
        """tests to see if error is thrown when entering an invalid password"""

        with self.assertRaises(ValueError) as context:
            invalid_user = User.signup(
                "testtest", "eamil@dsklsa.com", None, None)

        with self.assertRaises(ValueError) as context:
            invalid_user = User.signup(
                "testtest", "eamil@dsklsa.com", "", None)

    ### Testing Authentication #####################

    def test_valid_authentication(self):
        """When given correct info, user is logged in"""
        user = User.authenticate(self.u1.username, "password")
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.uid1)

    def test_bad_username(self):
        """tests that user won't be logged in with incorrect username"""
        self.assertFalse(User.authenticate("wrong", "password"))

    def test_bad_password(self):
        """tests that user won't be logged in with incorrect password"""
        self.assertFalse(User.authenticate(self.u1.username, "wrongpassword"))

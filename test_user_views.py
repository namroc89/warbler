"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py
import os
from unittest import TestCase
from models import db, connect_db, Message, User, Likes, Follows
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
from app import app, CURR_USER_KEY  # noqa


db.create_all()


app.config['WTF_CSRF_ENABLED'] = False


class UserViewsTest(TestCase):
    """Test views for Users"""

    def setUp(self):
        """Create test client, add sample data"""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuserpass",
                                    image_url=None)
        self.tester_id = 1234
        self.testuser.id = self.tester_id

        self.u1 = User.signup("Lewis", "lewis@mail.com", "passowrd", None)
        self.u1_id = 5678
        self.u1.id = self.u1_id
        self.u2 = User.signup("Elena", "elena@mail.com", "passowrd", None)
        self.u2_id = 9012
        self.u2.id = self.u2_id
        self.u3 = User.signup("Ruth", "ruth@mail.com", "passowrd", None)
        self.u3_id = 3456
        self.u3.id = self.u3_id

        db.session.commit()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_list(self):
        """do all users show up when /users is navigated to"""
        with self.client as c:
            resp = c.get("/users")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(User.query.all()), 4)
            self.assertIn("Lewis", html)
            self.assertIn("Elena", html)
            self.assertIn("Ruth", html)

    def test_user_following_logged_in(self):
        """Can a logged in user visit another users following page"""
        f1 = Follows(user_being_followed_id=self.u1_id,
                     user_following_id=self.u3_id)
        f2 = Follows(user_being_followed_id=self.u2_id,
                     user_following_id=self.u3_id)

        db.session.add_all([f1, f2])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.u3_id}/following")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Lewis", html)
            self.assertIn("Elena", html)

    def test_logged_out_following(self):
        """Can someone who has not logged inview a users following"""
        with self.client as c:
            resp = c.get(
                f"/users/{self.tester_id}/following", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_user_followers_logged_in(self):
        """Can a logged in user visit another users followers page"""
        f1 = Follows(user_being_followed_id=self.u1_id,
                     user_following_id=self.u3_id)
        f2 = Follows(user_being_followed_id=self.u1_id,
                     user_following_id=self.u2_id)

        db.session.add_all([f1, f2])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.u1_id}/followers")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Ruth", html)
            self.assertIn("Elena", html)

    def test_logged_out_followers(self):
        """Can someone who has not logged inview a users followers"""
        with self.client as c:
            resp = c.get(
                f"/users/{self.tester_id}/followers", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)

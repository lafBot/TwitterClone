"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

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

        self.testuser_id = 1111
        self.testuser.id = self.testuser_id

        u2 = User.signup("user2", "user2@gmail.com", "password", None)
        uid2 = 2222
        u2.id = uid2

        self.u2 = u2
        self.uid2 = uid2

        db.session.add(u2)

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

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_view_messages(self):
        """Test that user can see messages when logged in"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            msg = Message(
                    id=9999,
                    text="Message content",
                    user_id=self.testuser.id
                )
                
            db.session.add(msg)
            db.session.commit()

            resp = c.get(f'/messages/{msg.id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(msg.text, str(resp.data))

    def test_not_logged_in(self):
        """Test that user is not able to post message if not logged in"""
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Message contents"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
    
    def test_invalid_user_attempt(self):
        """Test attempt to add message for wrong user"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 2813308004

            resp = c.post("/messages/new", data={"text": "Message contents"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_invalid_message_show(self):
        """Ensure that error is shown when message id is not valid"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                # import pdb; pdb.set_trace()
            
            resp = c.get('/messages/99999999')

            self.assertEqual(resp.status_code, 404)

    def test_delete_message(self):
        """Assert that valid message deletion can occur"""
        msg = Message(
            id=9999,
            text="Message contents",
            user_id=self.testuser_id
        )
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/9999/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            msg = Message.query.get(9999)
            self.assertIsNone(msg)

    def test_invalid_delete_message(self):
        """Test wrong user tries to delete message"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2.id
            
            msg = Message(
                id=9999,
                text="Message content",
                user_id=self.testuser_id
            )
            db.session.add(msg)
            db.session.commit()

            resp = c.post("/messages/9999/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))

            msg = Message.query.get(9999)
            self.assertIsNotNone(msg)

    def test_message_delete_no_authentication(self):
        """Test non-logged in tries to delete message"""
        msg = Message(
            id=9999,
            text="a test message",
            user_id=self.testuser_id
        )
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            resp = c.post("/messages/9999/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            msg = Message.query.get(9999)
            self.assertIsNotNone(msg)

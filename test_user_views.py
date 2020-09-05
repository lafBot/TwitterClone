"""User views tests"""

import os
from unittest import TestCase

from models import db, connect_db, User, Message, Likes
from bs4 import BeautifulSoup


os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        u1 = User.signup("user1", "user1@gmail.com", "password", None)
        uid1 = 1111
        u1.id = uid1

        u2 = User.signup("user2", "user2@gmail.com", "password", None)
        uid2 = 2222
        u2.id = uid2

        db.session.commit()

        u1 = User.query.get(uid1)

        self.u1 = u1
        self.uid1 = uid1

        u2 = User.query.get(uid2)
        
        self.u2 = u2
        self.uid2 = uid2

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
    
    def test_users_index(self):
        with self.client as client:
            res = client.get('/users')

            self.assertIn('user1', str(res.data))
            self.assertIn('user2', str(res.data))
    
    def test_users_search(self):
        with self.client as client:
            res = client.get('/users?q=user')

            self.assertIn('@user1', str(res.data))
            self.assertIn('@user2', str(res.data))
    
    def test_user_show(self):
        with self.client as client:
            res = client.get(f'/users/{self.uid1}')

            self.assertEqual(res.status_code, 200)
            self.assertIn('@user1', str(res.data))
    
    def setup_likes(self):
        m1 = Message(text="message 1 text", user_id=self.uid1)
        m2 = Message(text="message 2 text", user_id=self.uid1)
        m3 = Message(id=7887, text="message likable text", user_id=self.uid2)
        db.session.add_all([m1,m2,m3])
        db.session.commit()

        like1 = Likes(user_id=self.uid1, message_id=7887)
        db.session.add(like1)
        db.session.commit()
        # import pdb; pdb.set_trace()
    
    def test_user_show_likes(self):
        self.setup_likes()

        with self.client as client:
            res = client.get(f"/users/{self.uid1}")

            self.assertEqual(res.status_code, 200)
            self.assertIn('@user1', str(res.data))

            soup = BeautifulSoup(str(res.data), 'html.parser')
            found = soup.find_all('li', {'class': 'stat'})

            self.assertEqual(len(found), 4)

            # check for message count = 1
            self.assertIn('2', found[0].text)
            # check for followers count = 0
            self.assertIn('0', found[1].text)
            # check for following count = 0
            self.assertIn('0', found[2].text)
            # check for like count = 1
            self.assertIn('1', found[3].text)
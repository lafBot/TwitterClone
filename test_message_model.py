"""User model tests."""

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Likes


os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        u1 = User.signup("user1", "user1@gmail.com", "password", None)
        uid1 = 1111
        u1.id = uid1

        db.session.commit()

        u1 = User.query.get(uid1)

        self.u1 = u1
        self.uid1 = uid1

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        """Test if creatime a message applys message, user connection, and creates a timestamp"""
        msg = Message(id=999, text="This is the message", user_id=self.uid1)
        db.session.add(msg)
        db.session.commit()
        message = Message.query.get(999)
        
        self.assertEquals(message.text, "This is the message")
        self.assertEquals(message.user_id, self.uid1)
        self.assertTrue(message.timestamp)
    
    def test_message_likes(self):
        """Test liking a message is applied to user in database"""
        msg = Message(id=999, text="This is the message", user_id=self.uid1)

        self.u1.likes.append(msg)
        db.session.commit()

        like = Likes.query.filter(Likes.user_id == self.uid1).all()
        self.assertEqual(len(like), 1)
        self.assertEqual(like[0].message_id, 999)
"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

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

        u1 = User.signup("user1", "user1@gmail.com", "password", None)
        uid1 = 1111
        u1.id = uid1

        u2 = User.signup("user2", "user2@gmail.com", "password", None)
        uid2 = 2222
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

    def test_user_repr(self):
        """Does the repr return <User #{self.id}: {self.username}, {self.email}> format"""
        self.assertEqual(str(self.u1), f"<User #{self.u1.id}: {self.u1.username}, {self.u1.email}>")

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_follows(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u2.followers), 1)
        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u1.following), 1)

        self.assertEqual(self.u2.followers[0].id, self.u1.id)
        self.assertEqual(self.u1.following[0].id, self.u2.id)

    def test_is_following(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

    def test_is_followed_by(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))

#######################################
###########Signup Tests################
#######################################

    def test_user_unique(self):
        """Test if invalid validations -uniqueness, non-nullable- reject user creation"""
        u1 = User.signup("user1", "user1@gmail.com", "password", None)
        db.session.add(u1)
        
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_valid_signup(self):
        """Test if valid information allows a user to sign up"""
        user = User.signup(
            username="validUser",
            email="valid@gmail.com",
            password="password1",
            image_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&w=1000&q=80",
        )
        user.id = 5555
        db.session.commit()
        valid = User.query.get(user.id)

        self.assertEqual(str(valid), f"<User #{valid.id}: {valid.username}, {valid.email}>")

    def test_invalid_username(self):
        """Test if invalid username is rejected"""
        user = User.signup(
            username=None,
            email="validemail@gmail.com",
            password="password1",
            image_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&w=1000&q=80",
        )
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email(self):
        """Test if invalid email is rejected"""
        user = User.signup(
            username="validUserName",
            email=None,
            password="password1",
            image_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&w=1000&q=80",
        )
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password(self):
        """Test if invalid password is rejected"""
        with self.assertRaises(ValueError) as context:
            User.signup(
            username="validUserName",
            email="validemail@gmail.com",
            password=None,
            image_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&w=1000&q=80",
        )

        with self.assertRaises(ValueError) as context:
            User.signup(
            username="validUserName",
            email="validemail@gmail.com",
            password="",
            image_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&w=1000&q=80",
        )

#######################################
######## Authentication Tests##########
#######################################

    def test_valid_authentication(self):
        u = User.authenticate(self.u1.username, "password")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.uid1)
    
    def test_invalid_username(self):
        self.assertFalse(User.authenticate("badusername", "password"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.u1.username, "badpassword"))


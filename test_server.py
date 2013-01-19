"""
Unit tests for server-side logic for the EHP Portfolios Private Comments app.

@author: Sam Pottinger
@license: GNU GPL v3
"""

import datetime
import unittest2
import urllib

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import testbed

import account_facade
import models
import util


class FakeUser:
    """
    Dependency injection construct to replace GAE stock User class.

    Dependency injection construct to simulate the Google App Engine User
    class (google.appengine.api.users.User).
    """

    def __init__(self, email):
        """
        Create a new FakeUser with the given email.

        @param email: The email address to assign to this FakeUser.
        @type email: str
        """
        self.__email = email

    def email(self):
        """
        Get the email address of this FakeUser.

        @return: The email in this FakeUser.
        @rtype: str
        """
        return self.__email


def assert_user_info_equal(test, info_1, info_2):
    """
    Convienence routine to assert that two UserInfo objects are equivalent.

    Convienence routine to check that two UserInfo instances have the same
    email addresses and access permissions.

    @param test: The test to run this assertion as part of.
    @type test: unittest2.TestCase
    @param info_1: The first UserInfo object to test.
    @type info_1: models.UserInfo
    @param info_2: The second UserInfo object to test.
    @type info_2: models.UserInfo
    """
    test.assertEqual(info_1.email, info_2.email)
    test.assertEqual(info_1.safe_email, info_2.safe_email)
    test.assertEqual(info_1.is_reviewer, info_2.is_reviewer)


class ServerTestCase(unittest2.TestCase):
    """Test case for server-side logic."""

    def setUp(self):
        """Start the Google App Engine testbed and dependency injection."""
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        """De-activate Google App Engine testbed and dependency injection."""
        self.testbed.deactivate()

    def test_user_info(self):
        """Test the models.UserInfo data model."""
        user_1 = FakeUser("test1@test.com")
        user_2 = FakeUser("test2@test.com")

        user_info_1 = models.UserInfo()
        user_info_1.email = user_1.email()
        user_info_1.safe_email = util.get_safe_email(user_1)
        user_info_1.is_reviewer = False
        user_info_1.put()

        user_info_2 = models.UserInfo()
        user_info_2.email = user_2.email()
        user_info_2.safe_email = util.get_safe_email(user_2)
        user_info_2.is_reviewer = True
        user_info_2.put()

        ret_info_1 = models.UserInfo.get_for_user(user_1)
        ret_info_2 = models.UserInfo.get_for_email(user_2.email())

        assert_user_info_equal(self, ret_info_1, user_info_1)
        assert_user_info_equal(self, ret_info_2, user_info_2)

    def test_viewing_profile(self):
        """Test the models.ViewingProfile data model."""
        user_1 = FakeUser("test1@test.com")
        user_2 = FakeUser("test2@test.com")
        profile_email = "safe_email"
        section_1_name = "section1"
        section_2_name = "section2"
        test_timestamp_1 = datetime.datetime(2000, 1, 2)
        test_timestamp_2 = datetime.datetime(2003, 4, 5)

        viewing_profile_1 = models.ViewingProfile()
        viewing_profile_1.viewer_email = user_1.email()
        viewing_profile_1.profile_email = profile_email
        viewing_profile_1.section_name = section_1_name
        viewing_profile_1.last_visited = test_timestamp_1
        viewing_profile_1.put()

        viewing_profile_2 = models.ViewingProfile()
        viewing_profile_2.viewer_email = user_2.email()
        viewing_profile_2.profile_email = profile_email
        viewing_profile_2.setion_name = section_2_name
        viewing_profile_2.last_visited = test_timestamp_2
        viewing_profile_2.put()

        ret_profile_1 = models.ViewingProfile.get_for(user_1,
            profile_email, section_1_name)
        ret_profile_2 = models.ViewingProfile.get_for(user_2,
            profile_email, section_1_name)

        self.assertEqual(ret_profile_1.last_visited,
            viewing_profile_1.last_visited)
        self.assertEqual(ret_profile_2.last_visited,
            None)

    def test_comment(self):
        """Test the models.Comment data model."""
        user_1 = FakeUser("test1@test.com")
        user_2 = FakeUser("test2@test.com")
        profile_email = "safe_email"
        section_1_name = "section1"
        section_2_name = "section2"
        contents_1 = "test contents 1"
        contents_2 = "test contents 2"
        test_timestamp_1 = datetime.datetime(2000, 1, 2)
        test_timestamp_2 = datetime.datetime(2003, 4, 5)
        test_divisor_timestamp = datetime.datetime(2001, 4, 5)

        test_comment_1 = models.Comment()
        test_comment_1.author_email = user_1.email()
        test_comment_1.profile_email = profile_email
        test_comment_1.section_name = section_1_name
        test_comment_1.contents = contents_1
        test_comment_1.timestamp = test_timestamp_1
        test_comment_1.put()

        test_comment_2 = models.Comment()
        test_comment_2.author_email = user_2.email()
        test_comment_2.profile_email = profile_email
        test_comment_2.section_name = section_2_name
        test_comment_2.contents = contents_2
        test_comment_2.timestamp = test_timestamp_2
        test_comment_2.put()

        query_1 = models.Comment.get_before_or_on_date(profile_email,
            test_divisor_timestamp, section_1_name)
        query_2 = models.Comment.get_past_date(profile_email,
            test_divisor_timestamp, section_2_name)

        self.assertEqual(query_1.count(), 1)
        self.assertEqual(query_2.count(), 1)

        result_1 = query_1.get()
        result_2 = query_2.get()

        self.assertEqual(result_1.contents, contents_1)
        self.assertEqual(result_2.contents, contents_2)

        self.assertEqual(result_1.timestamp, test_timestamp_1)
        self.assertEqual(result_2.timestamp, test_timestamp_2)

    def test_is_reviewer(self):
        """Test recording / reporting user access control permissions."""
        user_1 = FakeUser("test1@test.com")
        user_2 = FakeUser("test2@test.com")

        user_info_1 = models.UserInfo()
        user_info_1.email = user_1.email()
        user_info_1.safe_email = util.get_safe_email(user_1)
        user_info_1.is_reviewer = False
        user_info_1.put()

        user_info_2 = models.UserInfo()
        user_info_2.email = user_2.email()
        user_info_2.safe_email = util.get_safe_email(user_2)
        user_info_2.is_reviewer = True
        user_info_2.put()

        self.assertFalse(account_facade.is_reviewer(user_1))
        self.assertTrue(account_facade.is_reviewer(user_2))

    def test_ensure_user_info(self):
        """Test creation logic for the a models.UserInfo data model."""
        user_1 = FakeUser("test1@test.com")
        user_2 = FakeUser("test2@test.com")

        user_info_1 = models.UserInfo()
        user_info_1.email = user_1.email()
        user_info_1.safe_email = util.get_safe_email(user_1)
        user_info_1.is_reviewer = True
        user_info_1.put()

        ret_info_1 = account_facade.ensure_user_info(user_1)
        ret_info_2 = account_facade.ensure_user_info(user_2)

        self.assertEqual(ret_info_1.email, user_1.email())
        self.assertTrue(ret_info_1.is_reviewer)
        self.assertEqual(ret_info_2.email, user_2.email())
        self.assertFalse(ret_info_2.is_reviewer)

    def test_viewer_has_access(self):
        """Test checking user access control permissions.""" 
        user_1 = FakeUser("test1@test.com")
        user_2 = FakeUser("test2@test.com")
        profile_email_1 = util.get_safe_email(user_1)
        profile_email_2 = util.get_safe_email(user_2)

        user_info_1 = models.UserInfo()
        user_info_1.email = user_1.email()
        user_info_1.safe_email = util.get_safe_email(user_1)
        user_info_1.is_reviewer = False
        user_info_1.put()

        user_info_2 = models.UserInfo()
        user_info_2.email = user_2.email()
        user_info_2.safe_email = util.get_safe_email(user_2)
        user_info_2.is_reviewer = True
        user_info_2.put()

        self.assertTrue(
            account_facade.viewer_has_access(user_1, user_1.email())
        )
        self.assertTrue(
            account_facade.viewer_has_access(user_2, user_1.email())
        )
        self.assertFalse(
            account_facade.viewer_has_access(user_1, user_2.email())
        )

    def test_get_comments(self):
        """Test comment retrieval for a portfolio / section.""" 
        user_1 = FakeUser("test1@test.com")
        user_2 = FakeUser("test2@test.com")
        profile_email = "safe_email"
        section_1_name = "section1"
        section_2_name = "section2"
        contents_1 = "test contents 1"
        contents_2 = "test contents 2"
        test_timestamp_1 = datetime.datetime(2000, 1, 2)
        test_timestamp_2 = datetime.datetime(2003, 4, 5)
        viewing_timestamp = datetime.datetime(2001, 4, 5)

        test_comment_1 = models.Comment()
        test_comment_1.author_email = user_1.email()
        test_comment_1.profile_email = profile_email
        test_comment_1.section_name = section_1_name
        test_comment_1.contents = contents_1
        test_comment_1.timestamp = test_timestamp_1
        test_comment_1.put()

        test_comment_2 = models.Comment()
        test_comment_2.author_email = user_2.email()
        test_comment_2.profile_email = profile_email
        test_comment_2.section_name = section_2_name
        test_comment_2.contents = contents_2
        test_comment_2.timestamp = test_timestamp_2
        test_comment_2.put()

        viewing_profile = models.ViewingProfile()
        viewing_profile.viewer_email = user_1.email()
        viewing_profile.profile_email = profile_email
        viewing_profile.section_name = section_1_name
        viewing_profile.last_visited = viewing_timestamp
        viewing_profile.put()

        new_msgs = account_facade.get_new_comments(user_1, profile_email)
        self.assertEqual(new_msgs.count(), 1)
        self.assertEqual(new_msgs.get().contents, contents_2)

        old_msgs = account_facade.get_old_comments(user_1, profile_email)
        self.assertEqual(old_msgs.count(), 1)
        self.assertEqual(old_msgs.get().contents, contents_1)

    def test_get_updated_sections(self):
        """Test listing of unread comments / updated portfolio sections."""
        user_1 = FakeUser("test1@test.com")
        user_2 = FakeUser("test2@test.com")
        profile_email = "safe_email"
        section_1_name = "section1"
        section_2_name = "section2"
        contents_1 = "test contents 1"
        contents_2 = "test contents 2"
        test_timestamp_1 = datetime.datetime(2000, 1, 2)
        test_timestamp_2 = datetime.datetime(2003, 4, 5)
        viewing_timestamp = datetime.datetime(2001, 4, 5)

        test_comment_1 = models.Comment()
        test_comment_1.author_email = user_1.email()
        test_comment_1.profile_email = profile_email
        test_comment_1.section_name = section_1_name
        test_comment_1.contents = contents_1
        test_comment_1.timestamp = test_timestamp_1
        test_comment_1.put()

        test_comment_2 = models.Comment()
        test_comment_2.author_email = user_2.email()
        test_comment_2.profile_email = profile_email
        test_comment_2.section_name = section_2_name
        test_comment_2.contents = contents_2
        test_comment_2.timestamp = test_timestamp_2
        test_comment_2.put()

        viewing_profile = models.ViewingProfile()
        viewing_profile.viewer_email = user_1.email()
        viewing_profile.profile_email = profile_email
        viewing_profile.section_name = section_1_name
        viewing_profile.last_visited = viewing_timestamp
        viewing_profile.put()

        updated_listing = account_facade.get_updated_sections(user_1,
            profile_email)
        self.assertIn(section_2_name, updated_listing)
        self.assertEqual(updated_listing[section_2_name], 1)

    def test_set_viewed(self):
        """Test indicating that a user viewed a portfolio section."""
        user_1 = FakeUser("test1@test.com")
        section_1_name = "section1"
        contents_1 = "test contents 1"
        viewing_timestamp = datetime.datetime(2001, 4, 5)
        profile_email = "safe_email"

        viewing_profile = models.ViewingProfile()
        viewing_profile.viewer_email = user_1.email()
        viewing_profile.profile_email = profile_email
        viewing_profile.section_name = section_1_name
        viewing_profile.last_visited = viewing_timestamp
        viewing_profile.put()

        account_facade.set_viewed(user_1, profile_email, section_1_name)

        updated_viewing_profile = models.ViewingProfile.get_for(
            user_1, profile_email, section_1_name)
        self.assertTrue(
            viewing_timestamp != updated_viewing_profile.last_visited)

    def test_get_full_name(self):
        """Test getting full name of a user based on his / her email address."""
        name = util.get_full_name_from_email("first.last@colorado.edu")
        self.assertEqual(name[0], "First")
        self.assertEqual(name[1], "Last")


if __name__ == "__main__":
    unittest2.main()

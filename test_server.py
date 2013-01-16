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

    def __init__(self, email):
        self.__email = email

    def email(self):
        return self.__email


def assert_user_info_equal(test, info_1, info_2):
    test.assertEqual(info_1.email, info_2.email)
    test.assertEqual(info_1.safe_email, info_2.safe_email)
    test.assertEqual(info_1.is_reviewer, info_2.is_reviewer)


class ServerTestCase(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_user_info(self):
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
        ret_info_2 = models.UserInfo.get_for_safe_email(
            util.get_safe_email(user_2))

        assert_user_info_equal(self, ret_info_1, user_info_1)
        assert_user_info_equal(self, ret_info_2, user_info_2)

    def test_viewing_profile(self):
        user_1 = FakeUser("test1@test.com")
        user_2 = FakeUser("test2@test.com")
        profile_safe_email = "safe_email"
        section_1_name = "section1"
        section_2_name = "section2"
        test_timestamp_1 = datetime.datetime(2000, 1, 2)
        test_timestamp_2 = datetime.datetime(2003, 4, 5)

        viewing_profile_1 = models.ViewingProfile()
        viewing_profile_1.viewer_email = user_1.email()
        viewing_profile_1.profile_safe_email = profile_safe_email
        viewing_profile_1.section_name = section_1_name
        viewing_profile_1.last_visited = test_timestamp_1
        viewing_profile_1.put()

        viewing_profile_2 = models.ViewingProfile()
        viewing_profile_2.viewer_email = user_2.email()
        viewing_profile_2.profile_safe_email = profile_safe_email
        viewing_profile_2.setion_name = section_2_name
        viewing_profile_2.last_visited = test_timestamp_2
        viewing_profile_2.put()

        ret_profile_1 = models.ViewingProfile.get_for(user_1,
            profile_safe_email, section_1_name)
        ret_profile_2 = models.ViewingProfile.get_for(user_2,
            profile_safe_email, section_1_name)

        self.assertEqual(ret_profile_1.last_visited,
            viewing_profile_1.last_visited)
        self.assertEqual(ret_profile_2.last_visited,
            None)

    def test_message(self):
        user_1 = FakeUser("test1@test.com")
        user_2 = FakeUser("test2@test.com")
        profile_safe_email = "safe_email"
        section_1_name = "section1"
        section_2_name = "section2"
        contents_1 = "test contents 1"
        contents_2 = "test contents 2"
        test_timestamp_1 = datetime.datetime(2000, 1, 2)
        test_timestamp_2 = datetime.datetime(2003, 4, 5)
        test_divisor_timestamp = datetime.datetime(2001, 4, 5)

        test_message_1 = models.Message()
        test_message_1.author_email = user_1.email()
        test_message_1.profile_safe_email = profile_safe_email
        test_message_1.section_name = section_1_name
        test_message_1.contents = contents_1
        test_message_1.timestamp = test_timestamp_1
        test_message_1.put()

        test_message_2 = models.Message()
        test_message_2.author_email = user_2.email()
        test_message_2.profile_safe_email = profile_safe_email
        test_message_2.section_name = section_2_name
        test_message_2.contents = contents_2
        test_message_2.timestamp = test_timestamp_2
        test_message_2.put()

        query_1 = models.Message.get_before_or_on_date(profile_safe_email,
            test_divisor_timestamp, section_1_name)
        query_2 = models.Message.get_past_date(profile_safe_email,
            test_divisor_timestamp, section_2_name)

        self.assertEqual(query_1.count(), 1)
        self.assertEqual(query_2.count(), 1)

        self.assertEqual(query_1.get().contents, contents_1)
        self.assertEqual(query_2.get().contents, contents_2)

    def test_is_reviewer(self):
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
        user_1 = FakeUser("test1@test.com")
        user_2 = FakeUser("test2@test.com")
        profile_safe_email_1 = util.get_safe_email(user_1)
        profile_safe_email_2 = util.get_safe_email(user_2)

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
            account_facade.viewer_has_access(user_1, profile_safe_email_1)
        )
        self.assertTrue(
            account_facade.viewer_has_access(user_2, profile_safe_email_1)
        )
        self.assertFalse(
            account_facade.viewer_has_access(user_1, profile_safe_email_2)
        )


if __name__ == '__main__':
    unittest2.main()

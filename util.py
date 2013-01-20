"""
Convienence routines for the EHP Portfolio Private Comments application.

@author: Sam Pottinger
@license: GNU GPL v3
"""

import collections
import re
import urllib

EMAIL_REGEX = re.compile("([\w\d\-]+)\.([\w\d\-]+)\@colorado\.edu")


# Simple struct to hold information about a portfolio section
SectionStatus = collections.namedtuple(
    "SectionStatus",
    ["name", "num_comments", "safe_name"]
)


def check_email(target_email):
    """
    Check that an email address is an individual email from colorado.edu.

    @param target_email: The email address to check.
    @type target_email: str
    @return: True if the email is for an invidual at CU and False otherwise.
    @rtype: bool
    """
    return EMAIL_REGEX.match(target_email) != None


def get_user_home(target_user):
    """
    Get the URL that a user should be redirected to after authenticating.

    @param target_user: The user to get a home URL for.
    @type target_user: str
    @return: The URL that the given user should be redirected to after
             authenticating.
    @rtype: str
    """
    return "/portfolio/%s/overview" % get_safe_email(target_user)


def get_safe_email(target_user):
    """
    Get a URL-safe version of a user email address.

    @param target_user: The user to get a safe email (escaped) string for.
    @type target_user: google.appengine.api.users.User
    @return: URL-safe / URL escaped version of the given user's email address.
    @rtype: str
    """
    return sanitize_email(target_user.email())


def sanitize_email(target_email):
    """
    Get a URL-safe version of an email address.

    @param target_email: The email address to URL escape.
    @type target_email: str
    @return: The URL-safe version of the provided email.
    @rtype: str
    """
    return urllib.quote(target_email, "")


def get_full_name_from_email(target_email):
    """
    Get the full name for a user given his / her email address.

    @param target_email: The email to extract a full name from. Must match
                         EMAIL_REGEX.
    @type target_email: str
    @return: List with the given users's full name. The first element is the
             user's first name and the second is the user's last name.
    @rtype: List with two string elements.
    """
    match = EMAIL_REGEX.match(target_email)
    if not match:
        return target_email
    return [match.group(1).capitalize(), match.group(2).capitalize()]

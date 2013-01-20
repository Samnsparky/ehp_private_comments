"""
Logic to perform high level user account access and management operations.

@author Sam Pottinger
@license GNU GPL v3
"""

import datetime
import models
import util


def is_reviewer(viewing_user):
    """
    Determines if the specified user has "profile reviewer" access privileges.

    @param viewing_user: The user to determine reviewer privileges for.
    @type viewing_user: google.appengine.api.users.User
    @return: True if user can review other users' profiles and False otherwise.
    @rtype: bool
    """
    target_user_info = models.UserInfo.get_for_user(viewing_user)
    return target_user_info.is_reviewer


def ensure_user_info(target_user):
    """
    Ensure that a models.UserInfo record exists for the target user.

    Ensure that a models.UserInfo record exists for the target user, creating it
    if it does not exist and returning it regardless.

    @param target_user: The user to ensure a UserInfo record exists for.
    @type target_user: google.appengine.api.users.User
    @return: The UserInfo record for the given user.
    @rtype: models.UserInfo
    """
    user_info = models.UserInfo.get_for_user(target_user)
    if not user_info:
        user_info = models.UserInfo()
        user_info.email = target_user.email()
        user_info.safe_email = util.get_safe_email(target_user)
        user_info.is_reviewer = False
        name_parts = util.get_full_name_from_email(target_user.email())
        user_info.first_name = name_parts[0]
        user_info.last_name = name_parts[1]
        user_info.put()
    return user_info


def viewer_has_access(viewing_user, profile_user_email):
    """
    Check to see if a user has access to the given profile's private comments.

    @param viewing_user: The user to check access permissions for.
    @type viewing_user: google.appengine.api.users.User
    @param profile_user_email: The email of the user whose profile access rights
                               are in question for.
    @type profile_user_email: 
    @return: True if the given user has access to private comments on the
             provided profile and False otherwise.
    @rtype: bool
    """
    # Check actually logged in
    if viewing_user == None:
        return False

    # Check that a portfolio even exists
    if not models.UserInfo.get_for_email(profile_user_email):
        return False

    # Provide access to own portfolio and others if reviewer
    if viewing_user.email() == profile_user_email:
        return True
    elif is_reviewer(viewing_user):
        return True

    return False


def get_new_comments(viewing_user, profile_user_email, section_name=None):
    """
    Get the new comments for a given user on a given profile.

    Get the comments that the given viewing user has not yet seen for the
    profile of the user with the given email.

    @param viewing_user: The user for whom new comments should be returned.
    @type viewing_user: google.appengine.api.users.User
    @param profile_user_email: The email of the user whose profile is being
                               queried for new comments.
    @type profile_user_email: str
    @keyword section_name: The name of the section on which new comments should
                           be looked for. If None, all profile sections will be
                           examined.
    @type section_name: str
    @return: New comments for the given profile and section that the given user
             has not yet seen.
    @rtype: Iterable over models.Comment
    """
    viewing_profile = models.ViewingProfile.get_for(
        viewing_user, profile_user_email, section_name)
    last_visited = viewing_profile.last_visited
    if last_visited:
        return models.Comment.get_past_date(
            profile_user_email, last_visited, section_name)
    else:
        return models.Comment.get_for(profile_user_email, section_name)


def get_old_comments(viewing_user, profile_user_email, section_name=None):
    """
    Get the old comments for a given user on a given profile.

    Get the comments that the given viewing user has already seen for the
    profile of the user with the given email.

    @param viewing_user: The user for whom old comments should be returned.
    @type viewing_user: google.appengine.api.users.User
    @param profile_user_email: The email of the user whose profile is being
                               queried for old comments.
    @type profile_user_email: str
    @keyword section_name: The name of the section on which old comments should
                           be looked for. If None, all profile exceptions will
                           be examined.
    @type section_name: str
    @return: Old commens for the given profile and section that the given user
             has already seen.
    @rtype: Iterable over models.Comment
    """
    viewing_profile = models.ViewingProfile.get_for(
        viewing_user, profile_user_email, section_name)
    last_visited = viewing_profile.last_visited
    return models.Comment.get_before_or_on_date(
        profile_user_email, last_visited, section_name)


def get_updated_sections(viewing_user, profile_user_email):
    """
    Get the profile sections containing comments unread by the given user.

    Look over the profile for the user with the given email, searching for
    profile sections that the given user has not yet read.

    @param viewing_user: The user for whom sections with unread comments should
                         be returned.
    @type viewing_user: google.appengine.api.users.User
    @param profile_user_email: The email of the user whose profile's comments
                               should be searched.
    @type profile_user_email: str
    @return: The number of unread comments in each section containing > 0
             unread comments for the given user.
    @rtype: Dict mapping str to int
    """
    section_encounters = map(
        lambda x: x.section_name,
        get_new_comments(viewing_user, profile_user_email)
    )
    listing = {}
    for section in section_encounters:
        if not section in listing:
            listing[section] = 0
        listing[section] += 1
    return listing


def set_viewed(viewing_user, profile_user_email, section_name):
    """
    Indicate that a user just viewed a given section on a given profile.

    @param viewing_user: The user that viewed the given section on the given
                         profile.
    @type viewing_user: google.appengine.api.users.User
    @param profile_user_email: The email address of the user whose profile was
                               just viewed.
    @param section_name: The name of the section this user just viewed.
    @type section_name: str
    """
    viewing_profile = models.ViewingProfile.get_for(
        viewing_user, profile_user_email, section_name)
    viewing_profile.last_visited = datetime.datetime.now()
    viewing_profile.put()

def get_account_listing():
    query = models.UserInfo.all()
    query.order("last_name")
    query.order("first_name")
    return query

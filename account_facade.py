import models
import util

def is_reviewer(viewing_user):
    target_user_info = models.UserInfo.get_for_user(viewing_user)
    return target_user_info.is_reviewer

def ensure_user_info(target_user):
    user_info = models.UserInfo.get_for_user(target_user)
    if not user_info:
        user_info = models.UserInfo()
        user_info.email = target_user.email()
        user_info.safe_email = util.get_safe_email(target_user)
        user_info.is_reviewer = False
        user_info.put()
    return user_info

def viewer_has_access(viewing_user, profile_user_email):
    # Check actually logged in
    if viewing_user == None:
        return False

    # Check that a portfolio even exists
    if not models.UserInfo.get_for_safe_email(profile_user_email):
        return False

    # Provide access to own portfolio and others if reviewer
    if util.get_safe_email(viewing_user) == profile_user_email:
        return True
    elif is_reviewer(viewing_user):
        return True

    return False

def get_new_messages(viewing_user, profile_user_name, section_name=None):
    viewing_profile = models.ViewingProfile.get_for(
        viewing_user, profile_user_email, section_name)
    last_visited = viewing_profile.last_visited
    if last_visited:
        return models.Message.get_past_date(
            profile_user_email, last_visited, section_name)
    else:
        return models.Message.get_for(profile_user_email, section_name)

def get_old_messages(viewing_user, profile_user_name, section_name=None):
    viewing_profile = models.ViewingProfile.get_for(
        viewing_user, profile_user_email, section_name)
    last_visited = viewing_profile.last_visited
    return models.Message.get_before_or_on_date(
        profile_user_email, last_visited, section_name)

def get_updated_sections(viewing_user, profile_user_email):
    return map(
        lambda x: x.section_name,
        get_new_messages(viewing_user, profile_user_email)
    )
    # TODO this isn't meeting req. yet

def set_viewed(viewing_user, profile_user_name, section_name):
    viewing_profile = models.ViewingProfile.get_for(
        viewing_user, profile_user_email, section_name)
    viewing_profile.last_visited = datetime.datetime.now()
    viewing_profile.put()

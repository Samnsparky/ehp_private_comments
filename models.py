"""
Data models for the EHP Portfolios Private Comments application.

@author: Sam Pottinger
@license: GNU GPL v3
"""

from google.appengine.ext import db


class UserInfo(db.Model):
    """Data model for application specific user information."""
    
    email = db.StringProperty()
    safe_email = db.StringProperty()
    is_reviewer = db.BooleanProperty()

    @classmethod
    def get_for_user(cls, target_user):
        """
        Get the UserInfo record for a given user.

        @param target_user: The user for whom a UserInfo record should be
                            returned.
        @type target_user: google.appengine.api.users.User
        @return: The UserInfo object for the given user or None if none exists.
        @rtype: UserInfo or None
        """
        query = db.Query(cls)
        query.filter("email ==", target_user.email())
        return query.get()

    @classmethod
    def get_for_email(cls, email):
        """
        Get the UserInfo record for the user with the given email address.

        @param email: The email address of the user to get a UserInfo record
                      for.
        @type email: str
        @return: The UserInfo record for the given user.
        @rtype: UserInfo
        """
        query = db.Query(cls)
        query.filter("email ==", email)
        return query.get()


class ViewingProfile(db.Model):
    """
    Data model describing which profiles and sections a user has viewed.

    Data model with information about which profiles / sections a user has
    viewed along with timestamps for when they were last viewed.
    """

    viewer_email = db.StringProperty()
    profile_email = db.StringProperty()
    section_name = db.StringProperty()
    last_visited = db.DateTimeProperty()

    @classmethod
    def get_for(cls, viewing_user, profile_email, section_name):
        """
        Get the viewing profile record for the given user and portfolio.

        Get the viewing profile record for the given user in relationship to
        the given portfolio and section, a data model with information about
        when the given user last viewed the portfolio / section in question.

        @param viewing_user: The user for whom a viewing profile should be
                             returned.
        @type viewing_user: google.appengine.api.users.User
        @param profile_email: The email of the user whose profile the viewing
                              profile should have information for.
        @type profile_email: str
        @param section_name: The name of the profile section to get viewing
                             information for.
        @type section_name: str
        @return: A ViewingProfile with information about when the given user
                 last visited the given profile section.
        @rtype: ViewingProfile
        """
        query = db.Query(cls)
        
        query.filter("viewer_email ==", viewing_user.email())
        query.filter("profile_email ==", profile_email)
        
        if section_name != None:
            query.filter("section_name ==", section_name)
        
        if query.count() == 0:
            new_profile = ViewingProfile()
            new_profile.viewer_email = viewing_user.email()
            new_profile.profile_email = profile_email
            new_profile.section_name = section_name
            new_profile.last_visited = None
            new_profile.put()
            return new_profile
        else:
            return query.get()


class Comment(db.Model):
    """Data model describing a private comment left by one user for another."""

    author_email = db.StringProperty()
    profile_email = db.StringProperty()
    section_name = db.StringProperty()
    contents = db.TextProperty()
    timestamp = db.DateTimeProperty()

    @classmethod
    def get_for(cls, profile_user_email, section_name=None):
        """
        Get private comments for the given portfolio and section.

        @param profile_user_email: The email address of the user whose
                                   portfolio's private comments should be
                                   returned.
        @type profile_user_email: str
        @keyword section_name: The portfolio section for which private comments
                               should be returned.
        @type section_name: str
        @return: Comments for the given portfolio and section sorted in reverse
                 chronological order (by timestamp field).
        @rtype: Iterable over Comment
        """
        query = db.Query(cls)
        query.filter("profile_email ==", profile_user_email)

        if section_name != None:
            query.filter("section_name ==", section_name)
        
        query.order("-timestamp")
        return query

    @classmethod
    def get_past_date(cls, profile_user_email, timestamp, section_name=None):
        """
        Get private comments for a portfolio / section posted after a date.

        Get all of the private comments left on a portfolio / section that
        were posted after a given date and time.

        @param profile_user_email: The email address of the user whose portfolio
                                   should be searched for comments.
        @type profile_user_email: str
        @param timestamp: The date / time to start looking for comments after.
        @type timestamp: datetime.datetime
        @keyword section_name: The name of the section to find comments on. If
                               None, comments for all sections will be returned.
                               Defaults to None.
        @type section_name: str
        @return: Comments posted after the given timestamp on the given
                 portfolio / section sorted in reverse chronological order (on
                 the timestamp property).
        @rtype: Iterable over Comment
        """
        query = db.Query(cls)
        query.filter("profile_email ==", profile_user_email)
        query.filter("timestamp >", timestamp)

        if section_name != None:
            query.filter("section_name ==", section_name)
        
        query.order("-timestamp")
        return query

    @classmethod
    def get_before_or_on_date(cls, profile_email, timestamp, section_name=None):
        """
        Get private comments for a portfolio / section posted before a date.

        Get all of the private comments left on a portfolio / section that were
        posted before a given date and time.

        @param profile_email: The email address of the user whose portfolio
                              should be searched for comments.
        @type profile_email: str
        @param timestamp: The date / time to stop looking for comments at.
        @type timestamp: datetime.datetime
        @keyword section_name: The name of the section to get comments for. If
                             None, comments for all sections will be returned.
                             Defaults to None.
        @type section_name: str
        @return: Comments posted before or on the given timestamp on the given
                 portfolio / section sorted in reverse chronological order (on
                 the timestamp property).
        @rtype: Iterable over Comment
        """
        query = db.Query(cls)
        query.filter("profile_email ==", profile_email)
        query.filter("timestamp <=", timestamp)

        if section_name != None:
            query.filter("section_name ==", section_name)
        
        query.order("-timestamp")
        return query

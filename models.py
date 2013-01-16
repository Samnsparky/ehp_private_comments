from google.appengine.ext import db

class UserInfo(db.Model):
    email = db.StringProperty()
    safe_email = db.StringProperty()
    is_reviewer = db.BooleanProperty()

    @classmethod
    def get_for_user(cls, viewing_user):
        query = db.Query(cls)
        query.filter('email ==', viewing_user.email())
        return query.get()

    @classmethod
    def get_for_safe_email(cls, safe_email):
        query = db.Query(cls)
        query.filter('safe_email ==', safe_email)
        return query.get()


class ViewingProfile(db.Model):
    viewer_email = db.StringProperty()
    profile_safe_email = db.StringProperty()
    section_name = db.StringProperty()
    last_visited = db.DateTimeProperty()

    @classmethod
    def get_for(cls, viewing_user, profile_safe_email, section_name):
        query = db.Query(cls)
        
        query.filter('viewer_email ==', viewing_user.email())
        query.filter('profile_safe_email ==', profile_safe_email)
        
        if section_name != None:
            query.filter('section_name ==', section_name)
        
        if query.count() == 0:
            new_profile = ViewingProfile()
            new_profile.viewer_email = viewing_user.email()
            new_profile.profile_safe_email = profile_safe_email
            new_profile.section_name = section_name
            new_profile.last_visited = None
            new_profile.put()
            return new_profile
        else:
            return query.get()

class Message(db.Model):
    author_email = db.StringProperty()
    profile_safe_email = db.StringProperty()
    section_name = db.StringProperty()
    contents = db.TextProperty()
    timestamp = db.DateTimeProperty()

    @classmethod
    def get_past_date(cls, profile_user_email, last_visited, section_name=None):
        query = db.Query(cls)
        query.filter('profile_safe_email ==', profile_user_email)
        query.filter('timestamp >', last_visited)

        if section_name != None:
            query.filter('section_name ==', section_name)
        
        query.order('-timestamp')
        return query

    @classmethod
    def get_before_or_on_date(cls, profile_user_email, last_visited,
        section_name=None):
        query = db.Query(cls)
        query.filter('profile_safe_email ==', profile_user_email)
        query.filter('timestamp <=', last_visited)

        if section_name != None:
            query.filter('section_name ==', section_name)
        
        query.order('-timestamp')
        return query

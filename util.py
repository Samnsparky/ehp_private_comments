import collections
import urllib


SectionStatus = collections.namedtuple(
    'SectionStatus',
    ['name', 'num_comments', 'safe_name']
)


def get_user_home(target_user):
    return '/portfolio'

def has_own_portfolio(target_user):
    return True

def get_safe_email(target_user):
    return urllib.quote(target_user.email(), '')

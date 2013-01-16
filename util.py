import collections
import urllib


SectionStatus = collections.namedtuple(
    'SectionStatus',
    ['name', 'num_comments', 'safe_name']
)


def get_user_home(target_user):
    return '/portfolio'


def get_safe_email(target_user):
    return urllib.quote(target_user.email(), '')

import collections
import re
import urllib


EMAIL_REGEX = re.compile('(\w+)\.(\w+)\@colorado\.edu')


SectionStatus = collections.namedtuple(
    'SectionStatus',
    ['name', 'num_comments', 'safe_name']
)


def get_user_home(target_user):
    return '/portfolio/%s/overview' % get_safe_email(target_user)


def get_safe_email(target_user):
    return urllib.quote(target_user.email(), '')


def get_full_name_from_email(target_email):
    match = EMAIL_REGEX.match(target_email)
    if not match:
        return target_email
    return [match.group(1).capitalize(), match.group(2).capitalize()]

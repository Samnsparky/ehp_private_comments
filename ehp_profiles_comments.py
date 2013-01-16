import cgi
import datetime
import os

import jinja2
import webapp2

from google.appengine.api import users

import account_facade
import constants
import models
import util


jinja_file_system_loader = jinja2.FileSystemLoader(
    os.path.join(os.path.dirname(__file__), constants.TEMPLATES_DIR))
jinja_environment = jinja2.Environment(loader=jinja_file_system_loader)


def get_standard_template_dict():
    cur_user = users.get_current_user()
    return {
        'user': cur_user,
        'logout_url': users.create_logout_url(constants.HOME_URL),
        'profile_safe_email': util.get_safe_email(cur_user),
        'is_reviewer': account_facade.is_reviewer(cur_user)
    }


class HomePage(webapp2.RequestHandler):
    def get(self):
        cur_user = users.get_current_user()
        if cur_user:
            self.redirect('/sync_user')
        else:
            template = jinja_environment.get_template('home.html')
            content = template.render(
                {'login_url': users.create_login_url(self.request.uri)}
            )
            self.response.out.write(content)


class SyncUserHandler(webapp2.RequestHandler):
    def get(self):
        cur_user = users.get_current_user()
        account_facade.ensure_user_info(cur_user)
        self.redirect(util.get_user_home(cur_user))


class PortfolioOverviewPage(webapp2.RequestHandler):
    def get(self, profile_email):
        cur_user = users.get_current_user()
        if not account_facade.viewer_has_access(cur_user, profile_email):
            self.redirect(constants.HOME_URL)

        section_statuses = account_facade.get_updated_sections(
            cur_user, profile_email)
        sections = constants.PORTFOLIO_SECTIONS

        template = jinja_environment.get_template('portfolio_overview.html')
        template_vals = get_standard_template_dict()
        owner_name = util.get_full_name_from_email(profile_email)
        template_vals["cur_section"] = 'overview'
        template_vals["owner_name"] = ' '.join(owner_name)
        template_vals["sections"] = sections
        template_vals["section_statuses"] = section_statuses
        content = template.render(template_vals)
        self.response.out.write(content)


class PortfolioContentPage(webapp2.RequestHandler):
    def get(self, profile_email, section_name):
        cur_user = users.get_current_user()
        if not account_facade.viewer_has_access(cur_user, profile_email):
            self.redirect(constants.HOME_URL)

        new_messages = account_facade.get_new_messages(
            cur_user, profile_email, section_name)
        old_messages = account_facade.get_old_messages(
            cur_user, profile_email, section_name)

        account_facade.set_viewed(cur_user, profile_email, section_name)
        section_statuses = account_facade.get_updated_sections(
            cur_user, profile_email)
        sections = constants.PORTFOLIO_SECTIONS

        template = jinja_environment.get_template('portfolio_section.html')
        template_vals = get_standard_template_dict()
        owner_name = util.get_full_name_from_email(profile_email)
        template_vals["cur_section"] = section_name
        template_vals["owner_name"] = ' '.join(owner_name)
        template_vals["sections"] = sections
        template_vals["section_statuses"] = section_statuses
        template_vals["new_messages"] = new_messages
        template_vals["old_messages"] = old_messages
        content = template.render(template_vals)
        self.response.out.write(content)

    def post(self, profile_email, section_name):
        cur_user = users.get_current_user()
        if not account_facade.viewer_has_access(cur_user, profile_email):
            self.redirect(constants.HOME_URL)

        raw_comment_contents = self.request.get('message-contents', '')
        comment_contents = cgi.escape(raw_comment_contents)
        comment_contents = '<br>'.join(comment_contents.splitlines())

        new_message = models.Message()
        new_message.author_email = cur_user.email()
        new_message.profile_email = profile_email
        new_message.section_name = section_name
        new_message.contents = comment_contents
        new_message.timestamp = datetime.datetime.now()
        new_message.put()

        account_facade.set_viewed(cur_user, profile_email, section_name)

        self.redirect(self.request.path)


app = webapp2.WSGIApplication(
        [
            ('/', HomePage),
            ('/sync_user', SyncUserHandler),
            ('/portfolio/([^/]+)/overview', PortfolioOverviewPage),
            ('/portfolio/([^/]+)/section/([^/]+)', PortfolioContentPage)
        ],
        debug=True
    )

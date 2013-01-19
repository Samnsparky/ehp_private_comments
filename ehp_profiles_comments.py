"""
Handlers for the EHP Portfolios Private Comments application.

@author: Sam Pottinger
@license: GNU GPL v3
"""

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


# Prepare template files and loader for the jinja2 template rendering package.
jinja_file_system_loader = jinja2.FileSystemLoader(
    os.path.join(os.path.dirname(__file__), constants.TEMPLATES_DIR))
jinja_environment = jinja2.Environment(loader=jinja_file_system_loader)


def get_standard_template_dict():
    """
    Generate a dictionary of template values common to all inner app pages.

    Generate a dictionary of template values common to all pages outside of
    account mechanics (registration, login, etc).

    @return: Dictionary of common template values.
    @rtype: dict
    """
    cur_user = users.get_current_user()
    return {
        "user": cur_user,
        "logout_url": users.create_logout_url(constants.HOME_URL),
        "profile_safe_email": util.get_safe_email(cur_user),
        "is_reviewer": account_facade.is_reviewer(cur_user)
    }


class HomePage(webapp2.RequestHandler):
    """Handler for the application homepage."""

    def get(self):
        """
        GET request handler that displays the homepage.

        GET request handler that renders the application home page for
        non-authenticated visitors and redirects authenticated users to the
        profile sync user page. 
        """
        cur_user = users.get_current_user()
        if cur_user:
            self.redirect("/sync_user")
        else:
            template = jinja_environment.get_template("home.html")
            content = template.render(
                {"login_url": users.create_login_url(self.request.uri)}
            )
            self.response.out.write(content)


class SyncUserHandler(webapp2.RequestHandler):
    """
    Handler for a redirect page that ensures a user has an account.

    Handler for a redirect page that ensures a user has a corresponding
    models.UserInfo record before continuing.
    """

    def get(self):
        """
        GET request handler that ensures a user has a models.UserInfo record.

        GET request handler that checks that a user has a models.UserInfo
        record, creating it if it does not already exit. All users are then
        redirected to the page specified by util.get_user_home.
        """
        cur_user = users.get_current_user()
        account_facade.ensure_user_info(cur_user)
        self.redirect(util.get_user_home(cur_user))


class PortfolioOverviewPage(webapp2.RequestHandler):
    """
    Handler that renders a portfolio's overview page, showing unread comments.

    Handler that determines which profile sections contain unread comments for
    the given user and displays a listing.
    """

    def get(self, profile_email):
        """
        GET request handler that renders a profile overview page.

        @param profile_email: The email address of the user whose profile's
                              overview page should be rendered.
        @type profile_email: str
        """
        cur_user = users.get_current_user()
        if not account_facade.viewer_has_access(cur_user, profile_email):
            self.redirect(constants.HOME_URL)

        section_statuses = account_facade.get_updated_sections(
            cur_user, profile_email)
        sections = constants.PORTFOLIO_SECTIONS

        template = jinja_environment.get_template("portfolio_overview.html")
        template_vals = get_standard_template_dict()
        owner_name = util.get_full_name_from_email(profile_email)
        template_vals["cur_section"] = "overview"
        template_vals["owner_name"] = " ".join(owner_name)
        template_vals["sections"] = sections
        template_vals["section_statuses"] = section_statuses
        content = template.render(template_vals)
        self.response.out.write(content)


class PortfolioContentPage(webapp2.RequestHandler):
    """Handler to render the private comments for a section of a portfolio."""

    def get(self, profile_email, section_name):
        """
        GET request handler that renders the private comments for a section.

        @param profile_email: The email address of the user whose portfolio's
                              comments should be displayed.
        @type profile_email: str
        @param section_name: The name of the portfolio section to render
                             comments for.
        @type section_name: str
        """
        cur_user = users.get_current_user()
        if not account_facade.viewer_has_access(cur_user, profile_email):
            self.redirect(constants.HOME_URL)

        new_comments = account_facade.get_new_comments(
            cur_user, profile_email, section_name)
        old_comments = account_facade.get_old_comments(
            cur_user, profile_email, section_name)

        account_facade.set_viewed(cur_user, profile_email, section_name)
        section_statuses = account_facade.get_updated_sections(
            cur_user, profile_email)
        sections = constants.PORTFOLIO_SECTIONS

        template = jinja_environment.get_template("portfolio_section.html")
        template_vals = get_standard_template_dict()
        owner_name = util.get_full_name_from_email(profile_email)
        template_vals["cur_section"] = section_name
        template_vals["owner_name"] = " ".join(owner_name)
        template_vals["sections"] = sections
        template_vals["section_statuses"] = section_statuses
        template_vals["new_comments"] = new_comments
        template_vals["old_comments"] = old_comments
        content = template.render(template_vals)
        self.response.out.write(content)

    def post(self, profile_email, section_name):
        """
        POST handler for adding a priate comment to a portfolio section.

        @param profile_email: The email address of the user whose portfolio
                              should recieve the new comment.
        @type profile_email: str
        @param section_name: The name of the portfolio section to add the new
                             comment to.
        @type section_name: str
        """
        cur_user = users.get_current_user()
        if not account_facade.viewer_has_access(cur_user, profile_email):
            self.redirect(constants.HOME_URL)

        raw_comment_contents = self.request.get("comment-contents", "")
        comment_contents = cgi.escape(raw_comment_contents)
        comment_contents = "<br>".join(comment_contents.splitlines())

        new_comment = models.Comment()
        new_comment.author_email = cur_user.email()
        new_comment.profile_email = profile_email
        new_comment.section_name = section_name
        new_comment.contents = comment_contents
        new_comment.timestamp = datetime.datetime.now()
        new_comment.put()

        account_facade.set_viewed(cur_user, profile_email, section_name)

        self.redirect(self.request.path)


# Register handlers along with URL patterns
app = webapp2.WSGIApplication(
        [
            ("/", HomePage),
            ("/sync_user", SyncUserHandler),
            ("/portfolio/([^/]+)/overview", PortfolioOverviewPage),
            ("/portfolio/([^/]+)/section/([^/]+)", PortfolioContentPage)
        ],
        debug=True
    )

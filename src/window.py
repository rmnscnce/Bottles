# window.py
#
# Copyright 2020 brombinmirko <send@mirko.pm>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, Gio, Notify

import logging, webbrowser, time

from .params import *
from .download import BottlesDownloadEntry
from .runner import BottlesRunner, RunAsync

from .pages.add import BottlesAdd, BottlesAddDetails
from .pages.create import BottlesCreate
from .pages.details import BottlesDetails
from .pages.list import BottlesList
from .pages.preferences import BottlesPreferences
from .pages.dialog import BottlesDialog, BottlesAboutDialog

from .utils import UtilsConnection

'''
Set the default logging level
'''
logging.basicConfig(level=logging.DEBUG)

@Gtk.Template(resource_path='/pm/mirko/bottles/window.ui')
class BottlesWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'BottlesWindow'

    '''
    Get and assign widgets to variables from
    template childs
    '''
    grid_main = Gtk.Template.Child()
    stack_main = Gtk.Template.Child()
    btn_back = Gtk.Template.Child()
    btn_add = Gtk.Template.Child()
    btn_list = Gtk.Template.Child()
    btn_preferences = Gtk.Template.Child()
    btn_download_preferences = Gtk.Template.Child()
    btn_about = Gtk.Template.Child()
    btn_downloads = Gtk.Template.Child()
    btn_menu = Gtk.Template.Child()
    btn_translate = Gtk.Template.Child()
    btn_support = Gtk.Template.Child()
    switch_dark = Gtk.Template.Child()
    box_downloads = Gtk.Template.Child()
    pop_downloads = Gtk.Template.Child()

    '''
    Define environments and select the first
    by default
    '''
    envs = [
        'Gaming',
        'Software',
        'Custom'
    ]
    env_active = envs[0]

    '''
    Common variables
    '''
    previous_page = ""
    default_settings = Gtk.Settings.get_default()
    settings = Gio.Settings.new(APP_ID)

    '''
    Initializing Notify
    '''
    Notify.init(APP_ID)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        '''
        Initialize template
        '''
        self.init_template()
        self.default_settings.set_property("gtk-application-prefer-dark-theme",
                                           THEME_DARK)


        self.utils_conn = UtilsConnection(self)

        '''
        Create a runner instance
        '''
        self.runner = BottlesRunner(self)

        '''
        Get and assign pages to variables
        '''
        page_add = BottlesAdd(self)
        page_add_details = BottlesAddDetails(self)
        page_details = BottlesDetails(self)
        page_list = BottlesList(self)
        page_create = BottlesCreate(self)
        page_preferences = BottlesPreferences(self)

        '''
        Set reusable variables
        '''
        self.page_add_details = page_add_details
        self.page_create = page_create
        self.page_preferences = page_preferences
        self.page_list = page_list
        self.page_details = page_details

        '''
        Add pages to stack and set options
        '''
        self.stack_main.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack_main.set_transition_duration(ANIM_DURATION)
        self.stack_main.add_titled(page_add, "page_add", "New Bottle")
        self.stack_main.add_titled(page_create, "page_create", "Create Bottle")
        self.stack_main.add_titled(page_add_details, "page_add_details", "New Bottle details")
        self.stack_main.add_titled(page_details, "page_details", "Bottle details")
        self.stack_main.add_titled(page_list, "page_list", "Bottles")
        self.stack_main.add_titled(page_preferences, "page_preferences", "Preferences")

        '''
        Add widgets to main grid
        '''
        self.grid_main.attach(self.stack_main, 0, 1, 1, 1)

        '''
        Connect signals to widgets
        '''
        self.btn_back.connect('pressed', self.go_back)
        self.btn_add.connect('pressed', self.show_add_view)
        self.btn_list.connect('pressed', self.show_list_view)
        self.btn_about.connect('pressed', self.show_about_dialog)
        self.btn_support.connect('pressed', self.open_support_url)
        self.btn_translate.connect('pressed', self.open_translate_url)
        self.btn_preferences.connect('pressed', self.show_preferences_view)
        self.btn_download_preferences.connect('pressed', self.show_download_preferences_view)
        self.switch_dark.connect('state-set', self.toggle_dark)

        '''
        Set widgets status from user settings
        '''
        self.switch_dark.set_active(self.settings.get_boolean("dark-theme"))

        '''
        Load startup view from user settings
        '''
        self.stack_main.set_visible_child_name(
            self.settings.get_string("startup-view"))

        '''
        This method sould be executed as last
        '''
        self.on_start()

    '''
    This method should be called after window shown
    '''
    def on_start(self):
        '''
        Check if there is at least 1 runner in the system
        '''
        if len(self.runner.runners_available) == 0:
            message = "There are no Runners in the system. "

            if self.utils_conn.check_connection():
                message += "Proceed with the installation of the latest version?"
            else:
                message += "But you don't seem to be connected to the internet and you won't be able to download a runner. Connect to the internet and confirm this message to begin the download."

            dialog_checks = BottlesDialog(parent=self,
                                          title="No runners found",
                                          message=message)
            response = dialog_checks.run()

            if response == Gtk.ResponseType.OK:
                logging.info("OK status received")

                '''
                Performs runner checks
                '''
                self.runner.checks()
            else:
                logging.info("Cancel status received")

            dialog_checks.destroy()
        '''
        TODO: Else check for updates
        '''

    '''
    Toggle UI usability, this method should be used when performing delicate
    operations, like new bottle creation
    '''
    def set_usable_ui(self, status):
        for widget in [self.btn_back,
                       self.btn_add,
                       self.btn_list,
                       self.btn_downloads,
                       self.btn_menu]:
            widget.set_sensitive(status)

    '''
    Request a new notification to the Notify instance
    '''
    def send_notification(self, title, text, image=""):
        notification = Notify.Notification.new(title, text, image)
        notification.show()

    '''
    Save the previous page to allow the user to go back
    '''
    def set_previous_page_status(self):
        current_page = self.stack_main.get_visible_child_name()

        if self.previous_page != current_page:
            self.previous_page = current_page
            self.btn_back.set_visible(True)

    '''
    Open URLs
    '''
    def open_translate_url(self, widget):
        webbrowser.open_new_tab("https://github.com/bottlesdevs/Bottles/tree/develop")

    def open_support_url(self, widget):
        webbrowser.open_new_tab("https://github.com/bottlesdevs/Bottles/issues")

    '''
    Return to previous page
    '''
    def go_back(self, widget):
        self.btn_back.set_visible(False)
        self.stack_main.set_visible_child_name(self.previous_page)

    def show_add_view(self, widget):
        self.stack_main.set_visible_child_name("page_add")

    def show_list_view(self, widget):
        self.stack_main.set_visible_child_name("page_list")

    def show_preferences_view(self, widget, view=0):
        self.set_previous_page_status()
        self.page_preferences.notebook_preferences.set_current_page(view)
        self.stack_main.set_visible_child_name("page_preferences")

    def show_download_preferences_view(self, widget):
        self.show_preferences_view(widget, view=1)

    def show_about_dialog(self, widget):
        BottlesAboutDialog().show_all()

    '''
    Toggle dark mode and store status in settings
    '''
    def toggle_dark(self, widget, state):
        self.settings.set_boolean("dark-theme", state)
        self.default_settings.set_property("gtk-application-prefer-dark-theme",
                                            state)

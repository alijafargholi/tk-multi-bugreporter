# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import re
import tempfile
from functools import partial

import sgtk
# by importing QT from sgtk rather than directly, we ensure that
# the code will be compatible with both PySide and PyQt.
from sgtk.platform.qt import QtCore, QtGui

from .ui.dialog import Ui_Dialog
from .ui.link_dialog import Ui_link_form

screen_grab = sgtk.platform.import_framework("tk-framework-qtwidgets",
                                             "screen_grab")
shotgun_fields = sgtk.platform.import_framework("tk-framework-qtwidgets",
                                                "shotgun_fields")
logger = sgtk.platform.get_logger(__name__)


def show_dialog(app_instance):
    """
    Shows the main dialog window.
    """
    # in order to handle UIs seamlessly, each toolkit engine has methods for
    # launching different types of windows. By using these methods, your
    # windows will be correctly decorated and handled in a consistent fashion
    # by the system.

    # we pass the dialog class to this method and leave the actual construction
    # to be carried out by toolkit.
    app_instance.engine.show_dialog("Report Bugs!", app_instance, AppDialog)


class AppDialog(QtGui.QWidget):
    """
    Main application dialog window
    """

    def __init__(self):
        """
        Constructor
        """
        # first, call the base class and let it do its thing.
        super(AppDialog, self).__init__()

        # now load in the UI that was created in the UI designer
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # most of the useful accessors are available through the Application
        # class instance it is often handy to keep a reference to this. You can
        # get it via the following method:
        self._app = sgtk.platform.current_bundle()

        # via the self._app handle we can for example access:
        # - The engine, via self._app.engine
        # - A Shotgun API instance, via self._app.shotgun
        # - A tk API instance, via self._app.tk
        self.ui.buttons.accepted.connect(self.create_ticket)
        self.ui.buttons.rejected.connect(self.close)
        self.ui.screen_grab.clicked.connect(self.screen_grab)
        self.ui.bold.clicked.connect(partial(self.style, 'bold'))
        self.ui.italic.clicked.connect(partial(self.style, 'italic'))
        self.ui.link.clicked.connect(partial(self.style, 'link'))

        self._screenshot = None
        self._cc_widget = None
        self._ticket_type_widget = None
        self._ticket_priority_widget = None

        # The ShotgunFieldManager is a factory used to build widgets for fields
        # associated with an entity type in Shotgun. It pulls down the schema
        #  from Shotgun asynchronously when the initialize method is called, so
        # before we do that we need to hook up the signal it emits when it's
        # done to our method that gets the widget we want and adds it to the UI.
        self._field_manager = shotgun_fields.ShotgunFieldManager(parent=self)
        self._field_manager.initialized.connect(self._get_shotgun_fields)
        self._field_manager.initialize()

    def style(self, style_type):
        """Style the selected text from the Body widget to either Bold, Italic
           or a link

        :type style_type: str
        :param style_type: style type
        """
        selected_test = self.ui.ticket_body.textCursor().selectedText()
        if not selected_test:
            return

        cursor = self.ui.ticket_body.textCursor()
        start_pos = cursor.selectionStart()
        end_pos = cursor.selectionEnd()
        if style_type == 'bold':
            styled_text = "__{}__".format(selected_test)
        elif style_type == 'italic':
            styled_text = "_{}_".format(selected_test)
        else:
            link_form_ui = Ui_link_form()
            if link_form_ui.exec_():
                link = link_form_ui.link.text()
                styled_text = "[{}]({})".format(selected_test, link)
            else:
                return
        text = self.ui.ticket_body.toPlainText()
        new_text = text[:start_pos] + styled_text + text[end_pos:]
        self.ui.ticket_body.setPlainText(new_text)

    def _get_shotgun_fields(self):
        """
        Populates the CC list Shotgun field widget.
        """
        # Get a list of user entities from Shotgun representing the default
        # list that we'll pull from the "cc" config setting for the app.
        raw_cc = self._app.get_setting("cc", "")
        users = self._app.shotgun.find(
            "HumanUser",
            [["login", "in", re.split(r"[,\s]+", raw_cc)]],
            fields=("id", "type", "name")
        )

        # Create the widget that the user will use to view the default CC
        # list, plus enter in any additional users if the choose to do so.
        self._cc_widget = self._field_manager.create_widget(
            "Ticket",
            "addressings_cc",
            parent=self,
        )

        self._ticket_type_widget = self._field_manager.create_widget(
            "Ticket",
            "sg_ticket_type",
            parent=self,
        )

        self._ticket_priority_widget = self._field_manager.create_widget(
            "Ticket",
            "sg_priority",
            parent=self,
        )

        # Add our list of default users to the CC widget and then add the
        # widget to the appropriate layout.
        self._cc_widget.set_value(users)
        self.ui.cc_layout.addWidget(self._cc_widget)
        self.ui.type_layout.addWidget(self._ticket_type_widget)
        self.ui.priority_layout.addWidget(self._ticket_priority_widget)

        # Setting defaults
        type_default = self._app.get_setting("default_type", "")
        priority_default = self._app.get_setting("default_priority", "")
        self._ticket_type_widget.set_value(type_default)
        self._ticket_priority_widget.set_value(priority_default)

    def screen_grab(self):
        """
        Triggers a screen grab to be initiated.
        """
        pixmap = screen_grab.ScreenGrabber.screen_capture()
        self._screenshot = pixmap
        self.ui.screenshot.setPixmap(pixmap.scaled(100, 100))

    def create_ticket(self):
        """
        Creates a new Ticket entity in Shotgun from the contents of the dialog.
        """
        # Create the new Ticket entity, pulling the project from the current
        # context, and the title, ticket body, and cc list from the UI.
        description = self.ui.ticket_body.toPlainText()
        ticket_title = self.ui.ticket_title.text()
        if not description or not ticket_title:
            QtGui.QMessageBox.critical(
                self,
                'Missing Description Ticket Tile',
                'Please make sure you have included the description and the '
                'subject!',
                QtGui.QMessageBox.StandardButton.Abort
            )
            return
        ticket_body = description

        ticket_body += "\n\n__Engine Name__: {}\n__Engine Version__: " \
                       "{}\n__Context__: {}".format(self._app.engine.name,
                                                    self._app.engine.version,
                                                    self._app.context)

        error_log = self.ui.error_log.toPlainText()
        if error_log:
            ticket_body += '\n```\n{}\n```'.format(error_log)

        if self._app.get_setting("include_env", ""):
            prone_envs = self._app.get_setting("prone_envs", "")
            if prone_envs:
                prone_envs = re.split(r"[,\s]+", prone_envs)
                envs = {}
                for env in prone_envs:
                    envs[env] = os.environ.get(env)
            else:
                envs = os.environ
            env_info = "\n".join(["**{}** = {}".format(env, value)
                                  for env, value in envs.items()])

            ticket_body += "\n### Environment Variable\n{}".format(env_info)

        try:
            facility_project = {'type': 'Project', 'id': 143}
            result = self._app.shotgun.create(
                "Ticket",
                dict(
                    project=facility_project,
                    title=ticket_title,
                    description=ticket_body,
                    addressings_cc=self._cc_widget.get_value(),
                    sg_priority=str(self._ticket_priority_widget.get_value()),
                    sg_ticket_type=str(self._ticket_type_widget.get_value()),
                )
            )
        except Exception as e:
            logger.error(e)

        # If we have a screenshot that was recorded, we write that to disk as a
        # png file and then upload it to Shotgun, associating it with the Ticket
        # entity we just created.
        if self._screenshot:
            path = tempfile.mkstemp(suffix=".png")[1]
            file_obj = QtCore.QFile(path)
            file_obj.open(QtCore.QIODevice.WriteOnly)
            self._screenshot.save(file_obj, "PNG")
            self._app.shotgun.upload(
                "Ticket",
                result["id"],
                path,
                "attachments",
            )

        QtGui.QMessageBox.information(
            self,
            "Ticket successfully created!",
            "Ticket #%s successfully submitted!" % result["id"],
        )
        self.close()

# Copyright 2016 Mycroft AI, Inc.
#
# This file is part of Mycroft Core.
#
# Mycroft Core is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mycroft Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mycroft Core.  If not, see <http://www.gnu.org/licenses/>.


# Visit https://docs.mycroft.ai/skill.creation for more detailed information
# on the structure of this skill and its containing folder, as well as
# instructions for designing your own skill based on this template.


# Import statements: the list of outside modules you'll be using in your
# skills, whether from other files in mycroft-core or from external libraries
from os.path import dirname

from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.skills.context import adds_context, removes_context
from adapt.intent import IntentBuilder
from mycroft.skills.intent_service import IntentDeterminationEngine
from mycroft.util.log import getLogger
from smtplib import SMTP_SSL as SMTP
import re

__author__ = 'thecalcaholic'

# Logger: used for debug lines, like "LOGGER.debug(xyz)". These
# statements will show up in the command line when running Mycroft.
LOGGER = getLogger(__name__)
engine = IntentDeterminationEngine()
# The logic of each skill is contained within its own class, which inherits
# base methods from the MycroftSkill class with the syntax you can see below:
# "class ____Skill(MycroftSkill)"
class MessagingSkill(MycroftSkill):

    # The constructor of the skill, which calls MycroftSkill's constructor
    def __init__(self):
        super(MessagingSkill, self).__init__(name="MessagingSkill")
        self.message_builder = None

    def initialize(self):
        #self.register_intent_file('send.mail.to.recipient.intent', self.handle_new_mail)
        self.register_intent_file('send.mail.intent', self.handle_new_mail)
        self.register_vocabulary('peter', 'RecipientEntity')

    def handle_new_mail(self, message):
        LOGGER.debug("handle_new_mail(message)")
        self.message_builder = EmailBuilder('email')
        recipient = message.data.get("recipient")
        LOGGER.debug("found recipient: " + str(recipient))
        if recipient:
            self.message_builder.set_recipient(recipient)
        self.enable_intent("SetMessageRecipient")
        self.enable_intent("SetMessageRecipientExplicitly")
        self.enable_intent("MessageSetSubjectExpl")
        self.enable_intent("MessageSetContentExpl")
        self.set_context('MessageInProgress', 'true')
        self.next_step()

    @intent_handler(IntentBuilder("SetMessageRecipient").require("MessageInProgress").require("RecipientEntity").build())
    @adds_context("MessageInProgress")
    def handle_set_recipient(self, message):
        LOGGER.debug("handle_set_recipient(message)")
        self.message_builder.set_recipient(message.data.get('RecipientEntity'))
        self.remove_context("AskedForRecipientContext")
        self.next_step()

    @intent_handler(IntentBuilder('MessageSetSubjectExpl')
                    .require("MessageInProgress").require('Subject').build())
    @adds_context("MessageInProgress")
    def handle_set_subject_explicitly(self, message):
        LOGGER.debug("handle_set_subject_excplicitly(message)")
        subject_regex = re.compile(r"(?:set (?:the )?(?:subject|title) (?:of the message )?to (?P<subject1>.*))$"
                                   + r"|(?:(?:the )?(?:subject|title) (?:of the message )?is (?P<subject2>.*))$")

        match = subject_regex.search(message.data.get("utterance"))
        if match:
            subject = match.group("subject1") or match.group("subject2")
        elif message.get("AskedForSubject"):
            subject = message.data.get("utterance")
        else:
            self.speak_dialog("not.understood")
            return
        self.message_builder.set_subject(subject)
        self.next_step()

    @intent_handler(IntentBuilder("MessageSetContentExpl").require("MessageInProgress").require("Content").build())
    @adds_context("MessageInProgress")
    def handle_set_content_explicitly(self, message):
        LOGGER.debug("handle_set_content_explicitly(message)")
        content_regex = re.compile(r"(?:set (?:the )?content (?:of the message )?to (?P<content1>.*))$"
                                   + r"|(?:(?:the )?content (?:of the message )?is (?P<content2>.*))$"
                                   + r"|(?:(?:the )?message (says|reads) (?P<content3>.*))$")

        match = content_regex.search(message.data.get("utterance"))
        if match:
            content = match.group("content1") or match.group("content2") or match.group("content3")
        else:
            content = None
        self.set_content(content)

    #@intent_handler(IntentBuilder("MessageSetContentImpl").require("MessageInProgress").build())
    #@adds_context("MessageInProgress")
    def handle_set_content(self, message):
        LOGGER.debug("handle_set_content(message)")
        LOGGER.debug(message.data)
        self.set_content(message.data.get("utterance"))

    def set_content(self, content):
        LOGGER.debug("set_content(content)")
        if len(content) < 3:
            return
        self.message_builder.set_content(content)
        self.next_step()

    def handle_send_message_confirm(self, message):
        LOGGER.debug("handle_send_message_confirm(message)")
        self.speak_dialog("sending.message")

    def next_step(self):
        LOGGER.debug("next_step()")
        if self.message_builder.ready:
            self.speak_dialog("readout.message")
            self.speak("The message will be sent to {0}.".format(self.message_builder.message.recipient))
            self.speak("Its title is {0}.".format(self.message_builder.message.subject))
            self.speak("The message says: {0}".format(self.message_builder.message.content))
            self.speak_dialog("should.i.send")
        else:
            self.ask_for_next_input()

    def ask_for_next_input(self):
        LOGGER.debug("ask_for_next_input()")
        if not self.message_builder or self.message_builder.ready:
            return
        next_requirement = self.message_builder.required_fields[0]

        LOGGER.debug("speaking dialog: 'ask.for." + next_requirement + "'")
        self.speak_dialog("ask.for." + next_requirement, expect_response=True)

        self.remove_context("AskedForContent")
        self.remove_context("AskedForSubject")
        if next_requirement == "subject":
            self.set_context("AskedForSubject", "true")
        elif next_requirement == "content":
            self.set_context("AskedForContent", "true")

    # The "stop" method defines what Mycroft does when told to stop during
    # the skill's execution. In this case, since the skill's functionality
    # is extremely simple, the method just contains the keyword "pass", which
    # does nothing.
    def stop(self):
        pass


class EmailBuilder:
    def __init__(self, typeId):
        self.message = None
        self.required_fields = []

        if typeId == 'email':
            self.message = Email()
            self.required_fields = [
                "recipient",
                "subject",
                "content"
            ]

    @property
    def ready(self):
        if len(self.required_fields) == 0:
            LOGGER.debug("Message is ready")
            return True
        else:
            return False
    
    def set_recipient(self, recp):
        if "recipient" in self.required_fields:
            self.required_fields.remove("recipient")
        self.message.recipient = recp
    
    def set_subject(self, subject):
        if "subject" in self.required_fields:
            self.required_fields.remove("subject")
        self.message.subject = subject

    def set_content(self, content):
        if "content" in self.required_fields:
            self.required_fields.remove("content")
        self.message.content = content

    def build(self):
        return self.message


class Email:
    def __init__(self):
        self.msgType = 'email'
        self.recipient = None
        self.subject = ''
        self.content = ''

# The "create_skill()" method is used to create an instance of the skill.
# Note that it's outside the class itself.
def create_skill():
    return MessagingSkill()

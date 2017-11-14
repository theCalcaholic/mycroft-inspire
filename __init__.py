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
        self.set_context('MessageStartedContext', 'true')
        self.message_builder = MessageBuilder('email')
        recipient = message.data.get("recipient")
        LOGGER.debug("found recipient: " + str(recipient))
        if recipient:
            self.message_builder.set_recipient(recipient)
        self.next_step()

    @intent_handler(IntentBuilder("SetMessageRecipient").require("MessageStartedContext")
                    .require("AskedForRecipientContext").require("RecipientEntity").build())
    def handle_set_recipient(self, message):
        LOGGER.debug("handle_set_recipient(message)")
        self.handle_set_recipient_explicitly(message)

    @intent_handler(IntentBuilder("SetMessageRecipientExplicitly").require("MessageStartedContext")
                    .require("RecipientEntity").require("SetCommand").require("RecipientEntity").build())
    def handle_set_recipient_explicitly(self, message):
        LOGGER.debug("handle_set_recipient_explicitly(message)")
        self.message_builder.set_recipient(message.data.get('RecipientEntity'))
        self.remove_context("AskedForRecipientContext")
        self.next_step()

    @intent_handler(IntentBuilder('MessageSetSubject').require('MessageStartedContext').require('Subject')
                    .build())
    def handle_set_subject_explicitly(self, message):
        LOGGER.debug("handle_set_subject_excplicitly(message)")
        self.set_subject(message.data.get("Subject"))

    @intent_handler(IntentBuilder("MessageSetSubjectOrContent").require("MessageStartedContext")
                    .require("AskedForSubjectContext").build())
    def handle_set_subject(self, message):
        LOGGER.debug("handle_set_subject(message)")
        self.set_subject(message.data.get("utterance"))

    def set_subject(self, subject):
        LOGGER.debug("set_subject(subject)")
        self.message_builder.set_subject(subject)
        self.next_step()

    @intent_handler(IntentBuilder("MessageSetContent").require("MessageStartedContext").require("Content")
                    .build())
    def handle_set_content_explicitly(self, message):
        LOGGER.debug("handle_set_content_explicitly(message)")
        self.set_content(message.data.get("Content"))

    @intent_handler(IntentBuilder("MessageSetSubjectOrContent").require("MessageStartedContext")
                    .require("AskedForContentContext").build())
    def handle_set_content(self, message):
        LOGGER.debug("handle_set_content(message)")
        self.set_content(message.data.get("utterance"))

    def set_content(self, content):
        LOGGER.debug("set_content(content)")
        self.message_builder.set_content(content)
        self.next_step()

    @removes_context('MessageStartedContext')
    def handle_send_message_confirm(self, message):
        LOGGER.debug("handle_send_message_confirm(message)")
        self.speak_dialog("sending.message.dialog")

    def next_step(self):
        LOGGER.debug("next_step()")
        if self.message_builder.ready:
            self.speak_dialog("should.i.send")
        else:
            self.set_context("MessageStartedContext", "true")
            self.ask_for_next_input()

    def ask_for_next_input(self):
        LOGGER.debug("ask_for_next_input()")
        if not self.message_builder or self.message_builder.ready:
            return
        next_requirement = self.message_builder.required_fields[0]

        LOGGER.debug("speaking dialog: 'ask.for." + next_requirement + "'")
        self.speak_dialog("ask.for." + next_requirement, expect_response=True)

        if next_requirement == "subject":
            self.set_context("AskedForSubjectContext", "true")
        elif next_requirement == "content":
            self.set_context("AskedForContentContext", "true")
        elif next_requirement == "recipient":
            self.set_context("AskedForRecipientContext", "true")

    # The "stop" method defines what Mycroft does when told to stop during
    # the skill's execution. In this case, since the skill's functionality
    # is extremely simple, the method just contains the keyword "pass", which
    # does nothing.
    def stop(self):
        pass


class MessageBuilder:
    def __init__(self, typeId):
        self.message = None
        self.required_fields = []

        if typeId == 'email':
            self.message = EMail()
            self.required_fields = [
                "recipient",
                "subject",
                "content"
            ]

    @property
    def ready(self):
        return len(self.required_fields) == 0
    
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


class EMail:
    def __init__(self):
        self.msgType = 'email'
        self.recipient = None
        self.subject = ''
        self.content = ''

# The "create_skill()" method is used to create an instance of the skill.
# Note that it's outside the class itself.
def create_skill():
    return MessagingSkill()

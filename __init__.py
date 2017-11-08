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
from mycroft.util.log import getLogger
from smtplib import SMTP
import re

__author__ = 'thecalcaholic'

# Logger: used for debug lines, like "LOGGER.debug(xyz)". These
# statements will show up in the command line when running Mycroft.
LOGGER = getLogger(__name__)

# The logic of each skill is contained within its own class, which inherits
# base methods from the MycroftSkill class with the syntax you can see below:
# "class ____Skill(MycroftSkill)"
class MessagingSkill(MycroftSkill):

    # The constructor of the skill, which calls MycroftSkill's constructor
    def __init__(self):
        super(MessagingSkill, self).__init__(name="MessagingSkill")
        self.message_builder = None

    
    def initialize(self):
        self.register_intent_file('send.mail.intent', self.handle_send_mail)a

    def handle_send_mail(self, message):
        self.message_builder = MessageBuilder('email')
        utterance = message.data.get('utterance').lower();
        
        self.speak_dialog("enter.subject")

    # The "stop" method defines what Mycroft does when told to stop during
    # the skill's execution. In this case, since the skill's functionality
    # is extremely simple, the method just contains the keyword "pass", which
    # does nothing.
    def stop(self):
        pass

class MessageBuilder:
    def __init__(self, typeId):
        if(typeId == 'email'):
            self.message = EMail()
    
    def set_recipient(self, recp):
        self.message.recipient = recp
    
    def set_subject(self, subject):
        self.message.subject = subject

    def set_content(self, content):
        self.message.content = content

    def build(self):
        return message

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

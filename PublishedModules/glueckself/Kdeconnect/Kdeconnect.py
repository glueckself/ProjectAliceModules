import json

import core.base.Managers as managers
from core.base.model.Intent import Intent
from core.base.model.Module import Module
from core.dialog.model.DialogSession import DialogSession

#workflow
# start kdeconnectd (runs as alice-user, provides dbus service to interact with phone)
# use python dbus to interact with kdeconnectd
# probably: find-my-phone intent -> dbus method call -> kdeconnect magic -> phone

# todo: how to configure kdeconnectd? needs to be paired, maybe widget?
## pairing can be done via kdeconnect-cli, but not sure if it needs user input

# /usr/lib/libexec/kdeconnectd -platform offscreen
# https://github.com/KDE/kdeconnect-kde/blob/master/cli/kdeconnect-cli.cpp lists the dbus interface and how to use it

class Kdeconnect(Module):
	"""
	Author: glueckself
	Description: Connect an android device via kde connect to receive notifications and find the phone.
	"""

	def __init__(self):
		self._SUPPORTED_INTENTS	= [
		]

		super().__init__(self._SUPPORTED_INTENTS)


	def onMessage(self, intent: str, session: DialogSession) -> bool:
		if not self.filterIntent(intent, session):
			return False

		sessionId = session.sessionId
		siteId = session.siteId
		slots = session.slots

		return True

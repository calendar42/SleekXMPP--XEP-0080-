"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import logging
import traceback
import sys

from sleekxmpp.exceptions import XMPPError, IqError, IqTimeout
from sleekxmpp.stanza import Error
from sleekxmpp.xmlstream import ET, StanzaBase, register_stanza_plugin
try:
    from settings import XMPP_ERROR_BOT
except:
    XMPP_ERROR_BOT = None

log = logging.getLogger(__name__)


class RootStanza(StanzaBase):

    """
    A top-level XMPP stanza in an XMLStream.

    The RootStanza class provides a more XMPP specific exception
    handler than provided by the generic StanzaBase class.

    Methods:
        exception -- Overrides StanzaBase.exception
    """

    def exception(self, e):
        """
        Create and send an error reply.

        Typically called when an event handler raises an exception.
        The error's type and text content are based on the exception
        object's type and content.

        Overrides StanzaBase.exception.

        Arguments:
            e -- Exception object
        """
        if isinstance(e, IqError):
            # We received an Iq error reply, but it wasn't caught
            # locally. Using the condition/text from that error
            # response could leak too much information, so we'll
            # only use a generic error here.
            self.reply(clear=False)
            self['error']['condition'] = 'undefined-condition'
            self['error']['text'] = 'External error'
            self['error']['type'] = 'cancel'
            log.warning('You should catch IqError exceptions')
            self.send()
            if XMPP_ERROR_BOT is not None:
                self['to'] = XMPP_ERROR_BOT
                self.send()
        elif isinstance(e, IqTimeout):
            self.reply(clear=False)
            self['error']['condition'] = 'remote-server-timeout'
            self['error']['type'] = 'wait'
            log.warning('You should catch IqTimeout exceptions')
            self.send()
            if XMPP_ERROR_BOT is not None:
                self['to'] = XMPP_ERROR_BOT
                self.send()
        elif isinstance(e, XMPPError):
            # We raised this deliberately
            self.reply(clear=False)
            self['error']['condition'] = e.condition
            self['error']['text'] = e.text
            self['error']['type'] = e.etype
            if e.extension is not None:
                # Extended error tag
                extxml = ET.Element("{%s}%s" % (e.extension_ns, e.extension),
                                    e.extension_args)
                self['error'].append(extxml)
            self.send()
            if XMPP_ERROR_BOT is not None:
                self['to'] = XMPP_ERROR_BOT
                self.send()
        else:
            # We probably didn't raise this on purpose, so send an error stanza
            self.reply(clear=False)
            self['error']['condition'] = 'undefined-condition'
            self['error']['text'] = "SleekXMPP got into trouble."
            self['error']['type'] = 'cancel'
            self.send()
            if XMPP_ERROR_BOT is not None:
                self['to'] = XMPP_ERROR_BOT
                self.send()
            # log the error
            log.exception('Error handling {%s}%s stanza' ,  self.namespace, self.name)
            # Finally raise the exception to a global exception handler
            self.stream.exception(e)

register_stanza_plugin(RootStanza, Error)

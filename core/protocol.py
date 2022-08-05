import core.network
import core.utils


def protocol_msg_from_line(bl, conn, line):
    """

    This function is fhe factory for producing instances of ProtocolMsg classes
    for incoming messages. The receiver will call this for every line it
    receives and then call the message's execute() method.
    """

    # Each protocol message as it is transmitted and received from the socket
    # is in the following form (which I call the "line")
    #
    # <command>0x20<encoded>
    #
    # future extensions to the protocol might define new commands
    # but <command> may only consist of characters [a-z] or _
    # we split it at the first space character (0x20)
    command, encoded = core.utils.split_line(line)

    # 'encoded' is a string of encoded binary data.
    # The constructor will decode and parse it, so we can return
    # a readily initialized message object.
    try:
        msg = globals()[f'Protocol{command}']
    except KeyError:
        msg = ProtocolMsg

    return msg(bl, conn, command, encoded)


class ProtocolMsg:
    """The base class for all Protocol* classes. All message classes
    must inherit from this class.

    Besides being the base class for all Protocol* classes
    this class is also instantiated for every unknown incoming message.
    In this case execute() will simply reply with not_implemented"""

    def __init__(self, *args):
        """ this is actually a few overloaded constructors,
        depending on the types of arguments

        when receiving a message we instantiate it like this:
        __init__(self, bl, connection, command, encoded)

        when preparing a message for sending we do it like this:
        __init__(self, connection, blob)
        __init__(self, buddy, blob)

        blob is a string of raw binary 8-bit data, the contents
        of chat messages, names, texts must be UTF-8 encoded"""

        self.bl = None
        self.buddy = None
        self.connection = None

        #
        # incoming
        #
        # __init__(self, bl, connection, command, encoded)
        if type(args[0]) == BuddyList:
            self.bl = args[0]
            self.connection = args[1]
            if self.connection:
                self.buddy = self.connection.buddy
            self.command = args[2]

            # decode from line format to raw binary
            # and then let the message parse it
            self.blob = decode_lf(args[3])
            self.parse()

            # the incoming message is now properly initialized and somebody
            # could now call its execute() method to trigger its action
            return

        #
        # outgoing
        #
        # __init__(self, connection, blob)
        # __init__(self, buddy, blob)
        if type(args[0]) in [core.network.InConnection, core.network.OutConnection, Buddy]:
            if type(args[0]) in [core.network.InConnection, core.network.OutConnection]:
                self.connection = args[0]
                if self.connection.buddy:
                    self.buddy = self.connection.buddy

            elif type(args[0]) == Buddy:
                self.buddy = args[0]
                self.connection = self.buddy.conn_out

            if len(args) > 1:
                blob = args[1]
                if type(blob) in [list, tuple]:
                    self.blob = ' '.join(str(part) for part in blob)
                else:
                    self.blob = str(blob)
            else:
                self.blob = ''

            self.command = type(self).__name__[12:]

    def parse(self):
        pass

    def execute(self):
        # a generic message of this class will be automatically instantiated
        # if an incoming message with an unknown command is received
        # do nothing and just reply with "not_implemented"
        if self.buddy:
            print(f'(2) received unimplemented msg ({self.command}) from {self.buddy.address}')
            message = ProtocolNotImplemented(self.buddy)
            message.send()
        else:
            print('(2) received unknown command on unknown connection. Closing.')
            print(f"(2) unknown connection had '{self.connection.last_ping_address}' in last ping. Closing.")
            self.connection.close()

    def get_line(self) -> str:
        """return the entire message readily encoded as a string of characters
        that we can transmit over the socket, terminated by a 0x0a character

        :return: Encoded message.
        :rtype: str
        """
        # This is important:
        # The data that is transmitted over the socket (the entire contents
        # of one protocol message will be put into one string of bytes that
        # is terminated by exactly one newline character 0x0a at the end).
        #
        # This string of bytes is what I refer to as the "line"
        #
        # Therefore the entire message data (the contents of ProtocolMsg.blob)
        # which can contain any arbitrary byte sequence (even chat messages are
        # considered a blob since they are UTF-8 text with arbitrary formatting
        # chars) will be properly encoded for transmission in such a way that
        # it will not contain any 0x0a bytes anymore.
        #
        # This is implemented in the functions encode_lf() and decode_lf()
        #
        # get_line() is called right before transmitting it over the socket
        # to produce the "line" and the exact inverse operation on the
        # receiving side will happen in __init__() when a new message object
        # is constructed from the incoming encoded line string.
        return f'{self.command} {encode_lf(self.blob)}\n'

    def send(self):
        """Sends the outgoing message."""
        if self.connection:
            self.connection.send(self.get_line())
        else:
            print('(0) message without connection could not be sent')


class ProtocolNotImplemented(ProtocolMsg):
    """This message is sent whenever we cannot understand the command.

    When receiving this we currently do nothing, except logging it to the debug log.
    """
    offending_command = None

    def parse(self):
        self.offending_command = self.blob

    def execute(self):
        if self.buddy:
            print(f"(2) {self.buddy.address} says it can't handle '{self.offending_command}'")

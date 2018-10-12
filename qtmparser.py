import struct

from qtm.packet import QRTPacketType, QRTPacket, QRTEvent
from qtm.packet import RTheader, RTEvent, RTCommand

class QtmParser(object):
    @staticmethod
    def parse_header(data):
        size, type_ = RTheader.unpack_from(data, 0)
        type_ = QRTPacketType(type_)
        return size, type_

    @staticmethod
    def parse_response(type_, data):
        if (
            type_ == QRTPacketType.PacketError
            or type_ == QRTPacketType.PacketCommand
            or type_ == QRTPacketType.PacketXML
        ):
            return data[:-1].decode("utf-8")

        elif type_ == QRTPacketType.PacketData:
            return QRTPacket(data)

        elif type_ == QRTPacketType.PacketEvent:
            event, = RTEvent.unpack(data)
            return QRTEvent(ord(event))

    @staticmethod
    def create_command(command, command_type):
        cmd_length = len(command)

        return struct.pack(
            RTCommand % cmd_length,
            RTheader.size + cmd_length + 1,
            command_type.value,
            command.encode(),
            b"\0",
        )
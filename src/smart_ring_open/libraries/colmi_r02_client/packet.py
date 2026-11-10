def make_packet(command: int, sub_data: bytearray | None = None) -> bytearray:
    """
    Make a well formed packet from a command key and optional sub data.

    That means ensuring it's 16 bytes long and the last byte is a valid CRC.

    command must be between 0 and 255 (inclusive)
    sub_data must have a length between 0 and 14
    """
    assert 0 <= command <= 255, "Invalid command, must be between 0 and 255"
    packet = bytearray(16)
    packet[0] = command

    if sub_data:
        assert len(sub_data) <= 14, "Sub data must be less than 14 bytes"
        for i in range(len(sub_data)):
            packet[i + 1] = sub_data[i]

    packet[-1] = checksum(packet)

    return packet


def checksum(packet: bytearray) -> int:
    """
    Packet checksum

    Add all the bytes together modulo 256 (keep the lowest byte)
    """

    return sum(packet) & 255


PACKET_LENGTH = 16
ERROR_FLAG = 0x80


def is_valid(packet: bytes | bytearray) -> bool:
    """
    True if a received packet is 16 bytes long and its last byte is the checksum of the
    first 15. A packet that fails this was corrupted and must not be parsed.
    """
    return len(packet) == PACKET_LENGTH and checksum(bytearray(packet[:-1])) == packet[-1]


def has_error_flag(packet: bytes | bytearray) -> bool:
    """
    True if the ring answered with the error flag: the top bit of the command byte is set
    (e.g. 0xE9 instead of 0x69), meaning it rejected or could not run the command.
    """
    return bool(packet[0] & ERROR_FLAG)

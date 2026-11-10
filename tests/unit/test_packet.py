from src.smart_ring_open.libraries.colmi_r02_client.packet import checksum, has_error_flag, is_valid, make_packet


def test_checksum_is_the_lowest_byte_of_the_sum():
    assert checksum(bytearray([0xFF, 0x02])) == 0x01


def test_made_packets_are_valid():
    assert is_valid(make_packet(0x69, bytearray([1, 1])))


def test_corrupted_or_short_packets_are_invalid():
    p = make_packet(0x69, bytearray([1, 0, 72]))
    corrupted = bytearray(p)
    corrupted[3] = 73  # one changed HR value byte, checksum left as it was
    assert not is_valid(corrupted)
    assert not is_valid(p[:15])


def test_error_flag_is_the_top_bit_of_the_command():
    assert has_error_flag(make_packet(0x69 | 0x80))
    assert not has_error_flag(make_packet(0x69))


def test_commands_at_or_above_0x80_are_not_errors_when_known():
    raw = make_packet(0xA1, bytearray([0x02]))
    assert has_error_flag(raw)  # the bit alone cannot tell
    assert not has_error_flag(raw, known_commands={0xA1})
    assert has_error_flag(make_packet(0xE9), known_commands={0xA1})

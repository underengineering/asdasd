
import os
import re
from typing import List
from dataclasses import dataclass

from asyncraft.utils import Version
from asyncraft.proto.utils import ProtocolState, PacketDirection

# pylint: disable=pointless-string-statement
"""
	Set packet state: $ (state)
	Set packet direction: > (direction SERVERBOUND/CLIENTBOUND)
	Set packet id: = (packet name) (id)
	Comment: # (comment)
"""

class PacketParserError(ValueError):
	def __init__(self, pattern: str, data: str, offset: int) -> None:
		region = data[max(offset - 8, 0):offset + 8]
		region_repr = repr(region)
		message = f"Expected {pattern!r} near {region!r}"

		offset_to_error = len(self.__class__.__module__ + "." + self.__class__.__name__)
		offset_to_error += 2

		half_region_repr = repr(data[max(offset - 8, 0):offset])
		offset_to_error += len(message) - len(region_repr) + len(half_region_repr) - 1

		message += "\n"
		message += "-" * offset_to_error
		message += "^"

		super().__init__(message)

@dataclass
class PacketInfo:
	direction: PacketDirection
	state: ProtocolState
	name: str
	id: int

class PacketParser:
	DIR = "packets/versions"

	def __init__(self, version: Version):
		abs_path = os.path.dirname(__file__)
		with open(os.path.join(abs_path, self.DIR, str(version) + ".txt"),
					"r", encoding = "utf-8") as file:
			self._data = file.read()

		self._offset = 0

		self._current_state: ProtocolState = None
		self._current_direction: PacketDirection = None
		self._packets: List[PacketInfo] = []

	def _add_packet(self, packet_name: str, packet_id: int) -> None:
		self._packets.append(
			PacketInfo(self._current_direction, self._current_state, packet_name, packet_id))

	def _peek(self, pattern: str, flags: re.RegexFlag = 0) -> re.Match:
		match = re.match(pattern, self._data[self._offset:], flags)
		return match

	def _match(self, pattern: str, flags: re.RegexFlag = 0) -> re.Match:
		match = self._peek(pattern, flags)
		if match is None:
			return None

		self._offset += match.end()
		return match

	def _expect_match(self, pattern: str, flags: re.RegexFlag = 0) -> re.Match:
		match = self._match(pattern, flags)
		if match is None:
			raise PacketParserError(pattern, self._data, self._offset)

		return match

	def _is_eof(self) -> bool:
		return self._offset >= len(self._data)

	def _skip_newlines(self) -> None:
		self._match(r"(\s*\r?\n\s*)+")

	def _skip_whitespaces(self) -> None:
		self._match(r"\s+")

	def _parse_command(self) -> str:
		return self._expect_match(r"[$>=#]").group(0)

	def _parse_packet_name(self) -> str:
		return self._expect_match(r"[_a-zA-Z][_a-zA-Z0-9]*").group(0)

	def _parse_comment(self) -> None:
		self._match(r".*?$", re.MULTILINE)

	def _parse_line(self) -> None:
		self._skip_whitespaces()
		cmd = self._parse_command()
		self._skip_whitespaces()

		match cmd:
			case "$":
				state = self._expect_match(r"[A-Z]+").group(0)
				self._current_state = ProtocolState[state]
			case ">":
				direction = self._expect_match(r"[A-Z]+").group(0)
				self._current_direction = PacketDirection[direction]
			case "=":
				packet_name = self._parse_packet_name()
				self._skip_whitespaces()
				packet_id = int(self._expect_match(r"\d+").group(0))
				self._add_packet(packet_name, packet_id)
			case "#":
				self._parse_comment()

		self._skip_newlines()

	def parse(self) -> List[PacketInfo]:
		self._skip_newlines()

		while not self._is_eof():
			self._parse_line()

		return self._packets

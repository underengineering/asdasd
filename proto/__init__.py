
import asyncio
import os

from typing import Coroutine, Dict, List, Tuple, Type
from enum import IntEnum

from cryptography.hazmat.primitives.ciphers.modes import CFB8
from cryptography.hazmat.primitives.serialization import load_der_public_key

from asyncraft.proto.utils import ProtocolState, PacketDirection
from asyncraft.proto.packets import get_packet_class
from asyncraft.proto.packet import Packet, PacketDirection
from asyncraft.streams import AsyncIOStreamReader, AsyncIOStreamWriter, ByteArrayStreamReader, ByteArrayStreamWriter
from asyncraft.varint import VarInt

class Protocol:
	def __init__(self, host: str, port: int) -> None:
		self._host = host
		self._port = port

		self._reader: AsyncIOStreamReader = None
		self._writer: AsyncIOStreamWriter = None

		self._state = ProtocolState.HANDSHAKING

		self._packet_listeners: Dict[ProtocolState, Dict[int, List[Coroutine]]] = {
			ProtocolState.HANDSHAKING: {},
			ProtocolState.LOGIN: {},
			ProtocolState.PLAY: {}
		}

	@property
	def state(self) -> ProtocolState:
		return self._state

	def add_packet_listener(self, packet_class: Type[Packet], coro: Coroutine) -> None:
		self._packet_listeners[packet_class.state][packet_class.ID] = coro

	async def connect(self) -> None:
		reader, writer = await asyncio.open_connection(self._host, self._port)
		self._reader = AsyncIOStreamReader(reader)
		self._writer = AsyncIOStreamWriter(writer)

		asyncio.create_task(self._read_packets_task())

	async def read(self, num_bytes: int) -> bytes:
		return await self._reader.read_exactly(num_bytes)

	async def read_packet(self, packet_cls: Type[Packet]) -> Packet:
		return await packet_cls.read_from(self._reader)

	def write(self, data: bytes) -> None:
		self._writer.write(data)

	async def write_packet(self, packet: Packet, flush: bool = True) -> None:
		packet_buffer = bytearray()

		stream = ByteArrayStreamWriter(packet_buffer)
		packet.write_to(stream)

		packet_length = len(packet_buffer)

		VarInt.write_to(packet_length, self._writer)
		self.write(bytes(packet_buffer))
		if flush:
			await self.flush()

	async def flush(self) -> None:
		await self._writer.flush()

	async def wait_closed(self) -> None:
		await self._writer.wait_closed()

	def is_closing(self) -> bool:
		return self._writer.is_closing()

	def close(self) -> None:
		self._writer.close()

	async def _read_packet(self) -> Packet:
		print("_read_packet")
		packet_length = await VarInt.read_from(self._reader)
		packet_data = await self.read(packet_length)

		packet_stream = ByteArrayStreamReader(bytearray(packet_data))
		packet_id = await VarInt.read_from(packet_stream)

		print(f"wtf {packet_length=} {packet_id=} {packet_data=}")

		try:
			packet_class = get_packet_class(PacketDirection.CLIENTBOUND,
											self.state,
											packet_id)
		except KeyError:
			return None

		packet = await packet_class.read_from(packet_stream)

		return packet

	async def _read_packets_task(self) -> None:
		while not self.is_closing():
			packet = await self._read_packet()
			if packet is None:
				# Unknown packet received
				continue

			listeners = self._packet_listeners[self.state].get(packet.ID, [])
			for listener in listeners:
				await listener(packet)

	def __del__(self) -> None:
		self.close()

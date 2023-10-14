
import socket
import asyncio
import zlib

from typing import Coroutine, Dict, List, Tuple, Type
from enum import IntEnum

from asyncraft.proto.utils import ProtocolState, PacketDirection
from asyncraft.proto.packets import get_packet_class
from asyncraft.proto.packets import *
from asyncraft.proto.crypto import ProtocolCipher, CryptoStreamReader, CryptoStreamWriter
from asyncraft.streams import AsyncIOStreamReader, AsyncIOStreamWriter, ByteArrayStreamReader, ByteArrayStreamWriter
from asyncraft.varint import VarInt

class Protocol:
	def __init__(self, host: str, port: int, proto_version: int) -> None:
		self._host = host
		self._port = port
		self._proto_version = proto_version

		self._user_name: str = None

		self._reader: CryptoStreamReader = None
		self._writer: CryptoStreamWriter = None
		self._cipher = ProtocolCipher()

		self._state = ProtocolState.HANDSHAKING

		self._compression_threshold = -1

		self._packet_listeners: Dict[ProtocolState, Dict[int, List[Coroutine]]] = {
			ProtocolState.HANDSHAKING: {},
			ProtocolState.LOGIN: {},
			ProtocolState.PLAY: {}
		}

		self._logger = logging.getLogger("proto")

		self._add_listeners()

	@property
	def state(self) -> ProtocolState:
		return self._state

	@property
	def user_name(self) -> str:
		return self._user_name

	def add_packet_listener(self, packet_class: Type[Packet], coro: Coroutine) -> None:
		packets = self._packet_listeners[packet_class.state]
		if packet_class.ID not in packets:
			packets[packet_class.ID] = []

		packets[packet_class.ID].append(coro)

	async def connect(self, user_name: str) -> None:
		self._user_name = user_name

		reader, writer = await asyncio.open_connection(self._host, self._port)

		self._reader = CryptoStreamReader(AsyncIOStreamReader(reader), self._cipher)
		self._writer = CryptoStreamWriter(AsyncIOStreamWriter(writer), self._cipher)

		asyncio.create_task(self._read_packets_task())

		await self._handshake()

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
		if self._writer is not None:
			self._writer.close()

	async def _handshake(self):
		await self.write_packet(Handshake(self._proto_version,
											self._host,
											self._port,
											NextHandshakeState.LOGIN))

		self._state = ProtocolState.LOGIN

		await self.write_packet(LoginStart(self._user_name))

	async def _read_packet(self) -> Packet:
		packet_length = await VarInt.read_from(self._reader)

		print("packet_length", packet_length)
		print("compres", self._compression_threshold)

		if self._compression_threshold >= 0:
			data_length_size = await VarInt.count_from(self._reader)
			print("oke", data_length_size)
			data_length = await VarInt.read_from(self._reader)
			packet_data = await self._reader.read_exactly(packet_length - data_length_size)
			if data_length >= self._compression_threshold:
				packet_data = zlib.decompress(packet_data)
		else:
			packet_data = await self.read(packet_length)

		packet_stream = ByteArrayStreamReader(bytearray(packet_data))

		packet_id = await VarInt.read_from(packet_stream)

		print("packet_id", packet_id)

		try:
			packet_class = get_packet_class(PacketDirection.CLIENTBOUND,
											self.state,
											packet_id)
		except KeyError:
			return None, packet_id, packet_length

		packet = await packet_class.read_from(packet_stream)

		return packet, packet_id, packet_length

	async def _read_packets_task(self) -> None:
		while not self.is_closing():
			packet, packet_id, packet_length = await self._read_packet()
			if packet is None:
				self._logger.warning("Unknown packet id=%d, length=%d", packet_id, packet_length)
				continue

			listeners = self._packet_listeners[self.state].get(packet.ID, [])
			for listener in listeners:
				await listener(packet)

	async def _on_encryption_request(self, packet: EncryptionRequest) -> None:
		verify_token, shared_secret = self._cipher.encrypt_token_and_secret(bytes(packet.verify_token),
																			bytes(packet.public_key))

		await self.write_packet(EncryptionResponse(len(shared_secret),
												shared_secret,
												len(verify_token),
												verify_token))

		self._reader.enable_encryption()
		self._writer.enable_encryption()

		print("enabled encryption")

	async def _on_set_compression(self, packet: SetCompression) -> None:
		print("COMPRESSION", packet)
		self._compression_threshold = packet.threshold

	def _add_listeners(self) -> None:
		self.add_packet_listener(EncryptionRequest, self._on_encryption_request)
		self.add_packet_listener(SetCompression, self._on_set_compression)

	def __del__(self) -> None:
		self.close()

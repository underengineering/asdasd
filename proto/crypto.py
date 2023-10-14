
import os
import socket
from typing import List, Tuple

from cryptography.hazmat.primitives.serialization import load_der_public_key
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from asyncraft.streams import IStreamReader,  IStreamWriter

__all__ = (
	"ProtocolCipher", "CryptoStreamReader"
)

class ProtocolCipher:
	def __init__(self) -> None:
		self._shared_secret = os.urandom(16)

		self._cipher = Cipher(algorithms.AES(self._shared_secret),
								modes.CFB8(self._shared_secret))

	def encrypt_token_and_secret(self,
									verify_token: bytes,
									public_key_bytes: bytes) -> Tuple[bytes, bytes]:
		public_key = load_der_public_key(public_key_bytes)

		verify_token = public_key.encrypt(verify_token, PKCS1v15())
		shared_secret = public_key.encrypt(self._shared_secret, PKCS1v15())

		return verify_token, shared_secret

	def encrypt(self, data: bytes) -> bytes:
		encryptor = self._cipher.encryptor()
		return encryptor.update(data)

	def decrypt(self, data: bytes) -> bytes:
		decryptor = self._cipher.decryptor()
		return decryptor.update(data)

class CryptoStreamReader(IStreamReader):
	def __init__(self, stream: IStreamReader, cipher: ProtocolCipher) -> None:
		self._stream = stream
		self._cipher = cipher

		self._encryption_enabled = False

	def enable_encryption(self) -> None:
		self._encryption_enabled = True

	def at_eof(self) -> bool:
		return self._stream.at_eof()

	async def read_line(self) -> bytes:
		raise NotImplementedError()

	async def read_until(self, separator: str = b"\n") -> bytes:
		raise NotImplementedError()

	async def read(self, num_bytes: int = -1) -> bytes:
		return await self.read_exactly(num_bytes)

	async def read_exactly(self, num_bytes: int) -> bytes:
		data = await self._stream.read_exactly(num_bytes)
		if self._encryption_enabled:
			data = self._cipher.decrypt(data)

		return data

class CryptoStreamWriter(IStreamWriter):
	def __init__(self, stream: IStreamWriter, cipher: ProtocolCipher) -> None:
		self._stream = stream
		self._cipher = cipher

		self._encryption_enabled = False

	def enable_encryption(self) -> None:
		self._encryption_enabled = True

	def write(self, data: bytes) -> None:
		if self._encryption_enabled:
			data = self._cipher.encrypt(data)

		self._stream.write(data)

	def write_lines(self, lines: List[bytes]) -> None:
		raise NotImplementedError()

	def write_eof(self) -> None:
		self._stream.write_eof()

	def can_write_eof(self) -> bool:
		return self._stream.can_write_eof()

	async def flush(self) -> None:
		await self._stream.flush()

	async def wait_closed(self) -> None:
		await self._stream.wait_closed()

	def close(self) -> None:
		self._stream.close()

	def is_closing(self) -> bool:
		return self._stream.is_closing()

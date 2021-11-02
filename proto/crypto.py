
import os

from cryptography.hazmat.primitives.serialization import load_der_public_key
from cryptography.hazmat.primitives.ciphers.algorithms import AES

__all__ = (
	"generate_shared_secret",
)

def generate_shared_secret():
	return os.urandom(16)

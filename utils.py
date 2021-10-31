
from dataclasses import dataclass

@dataclass(slots = True)
class Version:
	major: int
	minor: int
	patch: int

	@staticmethod
	def from_string(version: str):
		major, minor, patch = version.split(".")
		return Version(major, minor, patch)

	def __str__(self):
		return f"{self.major}.{self.minor}.{self.patch}"

	def __eq__(self, other) -> bool:
		return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

	def __lt__(self, other) -> bool:
		return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

	def __gt__(self, other) -> bool:
		return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)

def unsigned_to_signed(value: int, num_bits: int) -> int:
	max_value = 2 ** (num_bits - 1)
	if value >= max_value:
		value -= max_value * 2

	return value

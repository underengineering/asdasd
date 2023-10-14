
import re
from dataclasses import dataclass

@dataclass(slots = True)
class Version:
	major: int
	minor: int
	patch: int
	is_snapshot: bool = False

	@staticmethod
	def from_string(version: str):
		if version.find("w") != -1:
			match = re.match(r"(\d+)w(\d+)([a-z])", version)
			major = match.group(1)
			minor = match.group(2)
			patch = match.group(3)
			return Version(major, minor, patch)

		major, minor, patch = version.split(".")
		return Version(major, minor, patch)

	def __str__(self) -> str:
		if self.is_snapshot:
			return f"{self.major}w{self.minor}{self.patch}"

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

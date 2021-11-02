
import re
import os
import bs4
import requests
from collections import namedtuple
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

def main():
	url = "https://wiki.vg/index.php?title=Protocol&oldid=14204" # input("URL: ")
	version = "1.12.2" #input("Version: ")
	version = Version.from_string(version)

	page = requests.get(url).text
	soup = bs4.BeautifulSoup(page, "html.parser")

	packets = {
		"Handshaking": {"Server": [], "Client": []},
		"Login": {"Server": [], "Client": []},
		"Play": {"Server": [], "Client": []},
		"Status": {"Server": [], "Client": []}
	}

	for table in soup.find_all("table", class_ = "wikitable"):
		table_body = table.find("tbody")

		packet_name = None
		packet_id = None
		packet_state = None
		packet_direction = None

		rows = table_body.find_all("tr")
		for row_num, row in enumerate(rows):
			columns = row.find_all("td")
			if row_num == 0:
				headers = row.find_all("th")
				headers = [header.text.strip() for header in headers]
				if headers != ["Packet ID", "State", "Bound To", "Field Name", "Field Type", "Notes"]:
					break

				continue
			elif row_num == 1:
				packet_id = int(columns[0].text[2:].strip(), 16)
				packet_state = columns[1].text.strip()
				packet_direction = columns[2].text.strip()

				packet_name_header = table.previous_sibling
				while packet_name_header.name != "h4":
					packet_name_header = packet_name_header.previous_sibling

				packet_name = packet_name_header.find("span", class_ = "mw-headline").text.strip()
				packet_name = re.sub(r"\(.*?\)", "", packet_name)
				packet_name = re.sub(r"[^a-zA-Z0-9_]", "", packet_name)
				packet_name = packet_name.replace(" ", "")

				packets[packet_state][packet_direction].append({
					"name": packet_name,
					"id": packet_id,
					"state": packet_state,
					"direction": packet_direction
				})

	file_lines = []
	for packet_state, packets in packets.items():
		file_lines.append("$ " + packet_state.upper())
		for packet_direction, packets in packets.items():
			file_lines.append("\t> " + packet_direction.upper() + "BOUND")

			for packet in packets:
				packet_name = packet["name"]
				packet_id = packet["id"]
				file_lines.append(f"\t\t= {packet_name} {packet_id}")

			file_lines.append("")

		file_lines.append("")

	abs_path = os.path.dirname(__file__)
	with open(os.path.join(abs_path, "versions", str(version) + ".txt"),
				"w", encoding = "utf-8") as file:
		file.write("\n".join(file_lines))

if __name__ == "__main__":
	main()

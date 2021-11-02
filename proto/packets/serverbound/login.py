
from asyncraft.proto.packet import Packet, packet
from asyncraft.proto.fields import String

@packet
class LoginStart(Packet):
	user_name: String

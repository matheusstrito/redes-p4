class CamadaEnlace:
    ignore_checksum = False

    def __init__(self, serial_interfaces):
        self.upper_layer_handler = None
        self.active_links = {
            dest_ip: Enlace(serial_if)
            for dest_ip, serial_if in serial_interfaces.items()
        }
        for link in self.active_links.values():
            link.set_receiver(self._handle_reception)

    def registrar_recebedor(self, handler):
        self.upper_layer_handler = handler

    def enviar(self, packet, destination_address):
        if destination_address in self.active_links:
            self.active_links[destination_address].send(packet)

    def _handle_reception(self, packet):
        if self.upper_layer_handler:
            self.upper_layer_handler(packet)


class Enlace:
    def __init__(self, serial_port):
        self.serial_port = serial_port
        self.serial_port.registrar_recebedor(self._raw_data_handler)
        self.reception_buffer = b''
        self.packet_receiver = None

    def set_receiver(self, callback):
        self.packet_receiver = callback

    def _escape_payload(self, payload):
        payload = payload.replace(b'\xdb', b'\xdb\xdd')
        payload = payload.replace(b'\xc0', b'\xdb\xdc')
        return payload

    def send(self, data_packet):
        escaped_packet = self._escape_payload(data_packet)
        frame = b'\xc0' + escaped_packet + b'\xc0'
        self.serial_port.enviar(frame)

    def _unescape_payload(self, escaped_payload):
        payload = escaped_payload.replace(b'\xdb\xdc', b'\xc0')
        payload = payload.replace(b'\xdb\xdd', b'\xdb')
        return payload

    def _raw_data_handler(self, incoming_data):
        self.reception_buffer += incoming_data
        
        frames = self.reception_buffer.split(b'\xc0')
        self.reception_buffer = frames[-1]

        for frame_content in frames[:-1]:
            if not frame_content:
                continue
            
            try:
                if self.packet_receiver:
                    datagram = self._unescape_payload(frame_content)
                    self.packet_receiver(datagram)
            except:
                import traceback
                traceback.print_exc()
import json
from Qt import QtNetwork
from Qt import QtCore
from Qt.QtCore import Signal, Property

import xml2json
from qtmparser import QtmParser

from qtm.packet import QRTPacketType, QRTPacket, QRTEvent
from qtm.packet import RTheader, RTEvent
import qtm
from time import sleep

class QQtmRt(QtCore.QObject):
    connectedChanged = Signal(bool)
    streamingChanged = Signal(bool)
    packetReceived = Signal(QRTPacket)
    noDataReceived = Signal(QRTPacket)
    eventReceived = Signal(int)

    def __init__(self, parent=None):
        super(QQtmRt, self).__init__(parent=parent)

        self._connected = False
        self._streaming = False
        self._socket = QtNetwork.QTcpSocket(parent=self)

        self._socket.disconnected.connect(self._disconnected)

        self._handlers = {
            QRTPacketType.PacketData: self._on_data,
            QRTPacketType.PacketEvent: self._on_event,
            QRTPacketType.PacketError: self._on_error,
            QRTPacketType.PacketNoMoreData: self._on_no_data,
        }

        self._receiver = qtm.Receiver(self._handlers)

        self.streamingChanged.connect(self._streaming_changed)

    def _on_no_data(self, packet):
        self.noDataReceived.emit(packet)

    def _on_data(self, packet):
        self.packetReceived.emit(packet)

    def _on_xml(self, packet):
        self.packetReceived.emit(packet)

    def _on_error(self, packet):
        self.packetReceived.emit(packet)

    def _on_event(self, event):
        self.eventReceived.emit(event)

    def _disconnected(self):
        self.streaming = False
        self.connected = False

    def _get_connected(self):
        return self._connected

    def _set_connected(self, connected):
        if self._connected == connected:
            return

        self._connected = connected
        self.connectedChanged.emit(connected)

    connected = QtCore.Property(
        bool, _get_connected, _set_connected, notify=connectedChanged
    )

    def _get_streaming(self):
        return self._streaming

    def _set_streaming(self, streaming):
        if self._streaming == streaming:
            return

        self._streaming = streaming
        self.streamingChanged.emit(streaming)

    streaming = QtCore.Property(
        bool, _get_streaming, _set_streaming, notify=streamingChanged
    )

    def _handshake(self):
        response = self._wait_for_reply()

        if response is not None and response != 'QTM RT Interface connected':
            return False

        self.requested_version = '1.21'
        version = self.set_version(version=self.requested_version)

        return version == 'Version set to {}'.format(self.requested_version)

    def _wait_for_reply(self, event=False):
        response = None
        data = bytes()

        if self._socket.waitForReadyRead():
            while True:
                data += self._socket.readAll().data()
                size, type_ = QtmParser.parse_header(data)

                while len(data) < size:
                    self._socket.waitForReadyRead()
                    data += self._socket.readAll().data()

                response = QtmParser.parse_response(type_, data[RTheader.size : size])
                data = data[size:]

                if type_ == QRTPacketType.PacketEvent:
                    if event:
                        return response
                    else:
                        self.eventReceived.emit(response)
                else:
                    return response

        return response

    def _send_command(self, command, command_type=QRTPacketType.PacketCommand):
        command = QtmParser.create_command(command, command_type)
        self._socket.write(command)

    def _streaming_changed(self, streaming):
        if streaming:
            self._socket.readyRead.connect(self._data_received)
        else:
            self._socket.readyRead.disconnect(self._data_received)

    def _delayed_stream_stop(self):
        self.streaming = False

    def get_settings(self, *args):
        if args is ():
            args = ['all']

        self._send_command('getparameters {}'.format(' '.join(args)))

        xml_text = self._wait_for_reply()
        options = lambda: None
        options.pretty = False
        json_text = xml2json.xml2json(xml_text, options)
        settings = json.loads(json_text)
        settings = settings.pop('QTM_Parameters_Ver_' + self.requested_version)

        return settings

    # Added by JTD
            
    def get_parameters(self, *args):
        if args is ():
            args = ['all']

        self._send_command('getparameters {}'.format(' '.join(args)))

        xml_text = self._wait_for_reply()
        return xml_text

    def send_XMLCommand(self, command):

        cmd = "takecontrol password"
        self._send_command(cmd)
        resp = self._wait_for_reply()
        print "Control response is ", resp

        if resp == "You are now master" or  resp == "You are already master" :
            newxml = u"<QTM_Settings>\n"
            newxml += command
            newxml += u"</QTM_Settings>"

            #print "XML Start"
            #print newxml
            #print "XML End"
            
            #reprocess_cmd = "stop"
            #self._send_command(reprocess_cmd)
            #resp = self._wait_for_reply()
            #print "Reprocess STOP.  Response is", resp 

            cmd = QtmParser.create_command(newxml,QRTPacketType.PacketXML)
            self._socket.write(cmd)
            resp = self._wait_for_reply()
            print "Pushed XML.  Response is", resp 

            #reprocess_cmd = "reprocess"
            #self._send_command(reprocess_cmd)
            #resp = self._wait_for_reply()
            #print "Reprocess SOLVE.  Response is", resp 

            #reprocess_cmd = "start RTFromFile"
            #self._send_command(reprocess_cmd)
            #resp = self._wait_for_reply()
            #print "start RTFromFile.  Response is", resp 
            
            cmd = "releasecontrol"
            self._send_command(cmd)
            resp = self._wait_for_reply()
            print "Release response is ", resp
        else:
            print "No XML sent"
            
        return resp


    def get_latest_event(self):
        self._send_command('getstate')

        return self._wait_for_reply(event=True)

    def set_version(self, version='1.18'):
        self._send_command('version {}'.format(version))

        return self._wait_for_reply()

    def _data_received(self):
        self._receiver.data_received(self._socket.readAll().data())

    def stream(self, *args):
        if args is ():
            args = ['all']

        self._send_command('streamframes allframes {}'.format(' '.join(args)))

        self.streaming = True

    def stop_stream(self):
        self._send_command('streamframes stop')
        # Hackish so that any packets already on the way will be delivered and parsed correctly.
        QtCore.QTimer.singleShot(500, self._delayed_stream_stop)

    def connect_to_qtm(self, host='127.0.0.1', timeout=3000):
        if self._connected:
            return False

        self._socket.connectToHost(host, 22223)

        if self._socket.waitForConnected(timeout):
            self.connected = self._handshake()

        return self.connected

    def disconnect(self):
        if not self._connected:
            return

        self._socket.disconnectFromHost()

    # ignorant try
    def _flush_connection(self):
        try:
            resp = self._wait_for_reply()
            print "Flush 1 response: ", resp
            resp = self._wait_for_reply(event=True)
            print "Flush 2 response: ", resp
            return True
        except:
            print "Flush 3 captured error"
            return False

    def _wait_for_right_reply(self, replies, maxTries = 2):

        for i in range (maxTries):
            print "WFRR: Iteration", str(i)
            try:
                resp = self._wait_for_reply()
                print "WFRR: response is:", resp
                
                value = replies.get(resp, None)
                print "WFRR: value is:", str(value)
                
                if value != None:
                    return value
            except:
                return False
        return False
                

    def send_StopRTCommand(self, password = ""):
        takeControl_replies = {"You are now master": True,
                               "You are aleady master": True,
                               'Client control disabled in QTM': False,
                               'Wrong or missing password': False,
                               'Parse error': False}

        cmd = "takecontrol "+password
        self._send_command(cmd)
        if self._wait_for_right_reply(takeControl_replies) :

            cmd = "stop"
            self._send_command(cmd)
            resp = self._wait_for_reply()
            print "PWRTO: start RTFromFile.  Response is", resp 

            cmd = "releasecontrol"
            self._send_command(cmd)
            resp = self._wait_for_reply()
            print "Send Stop: Release response is ", resp
        else:
            print "Send Stop: Did not take control"
            
        
    def send_StartRTCommand(self, password = ""):
        takeControl_replies = {"You are now master": True,
                               "You are aleady master": True,
                               'Client control disabled in QTM': False,
                               'Wrong or missing password': False,
                               'Parse error': False}

        cmd = "takecontrol "+password
        self._send_command(cmd)
        if self._wait_for_right_reply(takeControl_replies):

            cmd = "start RTFromFile"
            self._send_command(cmd)
            resp = self._wait_for_reply()
            print "PWRTO: start RTFromFile.  Response is", resp 

            cmd = "releasecontrol"
            self._send_command(cmd)
            resp = self._wait_for_reply()
            print "Send Start: Release response is ", resp

            resp = self.get_latest_event(event=True)
            print "Send Start: Latest Event: is ", resp

        else:
            print "Send Start: Did not take control"
            

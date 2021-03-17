# SituationBoard - Alarm Display for Fire Departments
# Copyright (C) 2017-2021 Sebastian Maier
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Optional

import serial
import binascii
import threading
import datetime

from backend.event.AlarmEvent import AlarmEvent
from backend.source.SourceDriver import SourceDriver, SourceState
from backend.source.MessageParser import MessageParser
from backend.event.SourceEvent import SourceEvent
from backend.event.UnhandledEvent import UnhandledEvent
from backend.util.Settings import Settings


class SourceDriverBOS925(SourceDriver):

    def __init__(self, instanceName: str, settings: Settings, parser: MessageParser) -> None:
        super().__init__("bos925", instanceName, settings, parser)
        self.__serial = serial.Serial(self.getSettingFilename("serial", '/dev/ttyUSB1'))

        self.__dataObject = None
        self.__dataObjectThread = ObjectPOCSAG()

        self.__thread = threading.Thread(target=self.listenSerial)
        self.__thread.start()

    def retrieveEvent(self) -> Optional[SourceEvent]:
        if self.__thread is None:
            return None

        if self.isSerialDone():
            self.__dataObject = None

            moment = datetime.datetime.now()
            ts = moment.strftime(SourceEvent.TIMESTAMP_FORMAT)

            sourceEvent = SourceEvent()
            sourceEvent.source = SourceEvent.SOURCE_BOS925
            sourceEvent.timestamp = ts
            sourceEvent.sender = "BOS925"
            sourceEvent.raw = "#K01;N5254685E1070341;%38524; %Sassenburg; %Grußendorf; %Streystättenring; %3; %Teich im Garten %Kleiner Motzkopf steckt im Teich fest ! %*001* %H2Y %Person klemmt % FW Grußendorf"
            #sourceEvent.raw = "#K01;N5243486E1058547; %38550; %Isenbüttel; %Isenbüttel; %Calberlaher Straße; %; %, 2b%ölspur am Kreisel Isenbüttel, in Calberlah \nan der Grundschule bis in die Bahnhofstraße ! %*33228* %H1 % mit SoSi % Fw Isenbüttel"
            parsedSourceEvent = self.parser.parseMessage(sourceEvent, None)

            if parsedSourceEvent is not None:
                return parsedSourceEvent

        return None

    def getSourceState(self) -> SourceState:
        if self.__serial is None:
            return SourceState.ERROR
        return SourceState.OK

    def isSerialDone(self):
        return self.__dataObject is not None

    def retrieveSerial(self, object):
        if self.__dataObject is None:
            self.__dataObject = object

    def listenSerial(self):
        while True:
            if self.__dataObjectThread.isDone():
                self.retrieveSerial(self.__dataObjectThread.getAsObject())
                self.__dataObjectThread.reset()
            else:
                msg = self.__serial.readline()
                msg = str(binascii.hexlify(msg), 'ascii')
                msg = msg.replace("0d0a", "")
                if msg is not None and msg != "":
                    msg = binascii.unhexlify(msg)
                    print(msg)
                    self.__dataObjectThread.addAttribute(msg)


class ObjectPOCSAG:
    __timePattern = r"(\d{2}):(\d{2}) (\d{2}).(\d{2}).(\d{2})"
    __codePattern = r""

    def __init__(self, counter=0, alarmTime=None, alarmCode=None, alarmMessage=None):
        self.counter = counter
        self.__alarmTime = alarmTime
        self.__alarmCode = alarmCode
        self.__alarmMessage = alarmMessage

    def reset(self):
        self.counter = 0
        self.__alarmTime = None
        self.__alarmCode = None
        self.__alarmMessage = None

    def addAttribute(self, text):
        if self.counter == 0:
            self.__alarmTime = text
        elif self.counter == 1:
            self.__alarmCode = text
        elif self.counter == 2:
            self.__alarmMessage = text
        else:
            pass

        self.counter += 1

    def isDone(self):
        return self.counter > 2

    def getAsObject(self):
        return ObjectPOCSAG(3, self.__alarmTime, self.__alarmCode, self.__alarmMessage)

    def getAlarmTime(self):
        return self.__alarmTime

    def getAlarmCode(self):
        return self.__alarmCode

    def getAlarmMessage(self):
        return self.__alarmMessage

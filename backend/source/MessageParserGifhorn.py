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

import datetime
import string

from typing import List, Optional

from enum import Enum

from backend.util.Settings import Settings
from backend.event.AlarmEvent import AlarmEvent
from backend.event.SettingEvent import SettingEvent
from backend.event.UnhandledEvent import UnhandledEvent
from backend.event.SourceEvent import SourceEvent
from backend.source.MessageParser import MessageParser

class MessageParserGifhorn(MessageParser):

    def __init__(self, instanceName: str, settings: Settings) -> None:
        super().__init__("bos925", instanceName, settings)

    def parseMessage(self, sourceEvent: SourceEvent, lastEvent: Optional[SourceEvent]) -> Optional[SourceEvent]:
        if self.isEmpty(sourceEvent):
            return None

        if sourceEvent is None:
            return None

        alarmEvent = AlarmEvent.fromSourceEvent(sourceEvent)
        alarmEvent.timestamp = sourceEvent.timestamp
        alarmEvent.alarmTimestamp = sourceEvent.timestamp
        alarmEvent.source = sourceEvent.source
        alarmEvent.flags = AlarmEvent.FLAGS_VALID
        alarmEvent.raw = "Alarm Message Landkreis Gifhorn"
        alarmEvent.sender = sourceEvent.sender

        # parse raw data
        dataList = sourceEvent.raw.split("%")

        # GPS
        lat, long = dataList[0].split(";")[1][1:].split("E")
        lat = self.insert_str(lat, ".", 2)
        long = self.insert_str(long, ".", 2)
        alarmEvent.locationLatitude  = float(lat)
        alarmEvent.locationLongitude = float(long)

        for i in range(len(dataList)):
            dataList[i] = dataList[i].replace(";", "")

        # Einsatzcode
        alarmEvent.event = dataList[9]
        # Details
        alarmEvent.eventDetails = dataList[6]
        # Position
        alarmEvent.location = f"{dataList[1]} {dataList[3]}"
        # Straße Hausnummer
        alarmEvent.locationDetails = f"{dataList[4]} {dataList[5]}"
        # Beschreibung
        alarmEvent.comment = dataList[7]

        sourceEvent = None
        return alarmEvent

    def insert_str(self, string, str_to_insert, index):
        return string[:index] + str_to_insert + string[index:]

    def isEmpty(self, sourceEvent: SourceEvent) -> bool:
        return sourceEvent.raw is None or sourceEvent.raw == ""

    def getRawLines(self, sourceEvent: SourceEvent) -> List[str]:
        return sourceEvent.raw.split('\n') # split will always return at least [""]

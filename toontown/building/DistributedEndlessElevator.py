from direct.distributed.ClockDelta import *
from direct.fsm import ClassicFSM, State
from direct.interval.IntervalGlobal import *
from panda3d.core import *
from toontown.building import DistributedElevator, DistributedElevatorExt, DistributedEndlessSuitInterior
from toontown.building.ElevatorConstants import *
from toontown.building.ElevatorUtils import *
from toontown.hood import ZoneUtil
from toontown.toonbase import ToontownGlobals, TTLocalizer


class DistributedEndlessElevator(DistributedElevatorExt.DistributedElevatorExt):

    def __init__(self, cr):
        DistributedElevatorExt.DistributedElevatorExt.__init__(self, cr)

    def generate(self):
        DistributedElevatorExt.DistributedElevatorExt.generate(self)

    def delete(self):
        self.elevatorModel.removeNode()
        del self.elevatorModel
        DistributedElevatorExt.DistributedElevatorExt.delete(self)

    def setEntranceId(self, entranceId):
        # In the future have another entrance for different difficulty
        self.entranceId = entranceId

        # These hard coded poshprs should be replaced with nodes in the model
        # if self.entranceId == 0:
        # Front of the factory (south entrance)
        #self.elevatorModel.setPosHpr(62.74, -85.31, 0.00, 2.00, 0.00, 0.00)

    def setupElevator(self):
        """setupElevator(self)
        Called when the building doId is set at construction time,
        this method sets up the elevator for business.
        """
        # TODO: place this on a node indexed by the entraceId
        self.elevatorModel = loader.loadModel(
            "phase_4/models/modules/elevator")
        self.elevatorModel.reparentTo(render)
        self.elevatorModel.setScale(1.05)
        self.leftDoor = self.elevatorModel.find("**/left-door")
        self.rightDoor = self.elevatorModel.find("**/right-door")
        # No lights on this elevator
        self.elevatorModel.find("**/light_panel").removeNode()
        self.elevatorModel.find("**/light_panel_frame").removeNode()
        self.elevatorModel.setPos(-134.8,  44.586,  0.525)
        self.elevatorModel.setH(-455.152 - 180)
        DistributedElevator.DistributedElevator.setupElevator(self)

    def getElevatorModel(self):
        return self.elevatorModel

    def setBldgDoId(self, bldgDoId):
        # The doId is junk, there is no building object for the endless
        # exterior elevators. Do the appropriate things that
        # DistributedElevator.gotBldg does.
        self.bldg = None
        self.setupElevator()

    def getZoneId(self):
        return 0

    def _getDoorsClosedInfo(self):
        return 'endlessSuitInterior', 'endlessSuitInterior'

    def __doorsClosed(self, zoneId):
        return
        assert(self.notify.debug('doorsClosed()'))
        DistributedEndlessSuitInterior.DistributedEndlessSuitInterior(
            self, base.cr)
        if (self.localToonOnBoard):
            hoodId = ZoneUtil.getHoodId(zoneId)
            loader, where = self._getDoorsClosedInfo()
            doneStatus = {
                'loader': loader,
                'where': where,
                'hoodId': hoodId,
                'zoneId': zoneId,
                'shardId': None,
            }

            elevator = self.elevatorFSM  # self.getPlaceElevator()
            del self.elevatorFSM
            elevator.signalDone(doneStatus)

    def setEndlessInteriorZone(self, zoneId):
        if (self.localToonOnBoard):
            hoodId = self.cr.playGame.hood.hoodId
            doneStatus = {
                'loader': "endlessSuitInterior",
                'where': 'endlessSuitInterior',
                'how': "teleportIn",
                'zoneId': zoneId,
                'hoodId': hoodId,
                'shardId': None,
            }
            self.cr.playGame.getPlace().elevator.signalDone(doneStatus)

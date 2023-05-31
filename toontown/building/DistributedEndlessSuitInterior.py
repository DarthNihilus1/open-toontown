import random

from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject
from direct.distributed.ClockDelta import *
from direct.fsm import ClassicFSM, State
from direct.interval.IntervalGlobal import *
from panda3d.otp import CFSpeech
from toontown.battle import BattleBase
from toontown.hood import ZoneUtil
from toontown.toon import NPCToons
from toontown.toonbase import (ToontownBattleGlobals, ToontownGlobals,
                               TTLocalizer)

from . import ElevatorUtils
from .ElevatorConstants import *


class DistributedEndlessSuitInterior(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        'DistributedSuitInterior')
    id = 0

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.toons = []
        self.activeIntervals = {}

        self.openSfx = base.loader.loadSfx("phase_5/audio/sfx/elevator_door_open.ogg")
        self.closeSfx = base.loader.loadSfx("phase_5/audio/sfx/elevator_door_close.ogg")

        self.suits = []
        self.reserveSuits = []
        self.joiningReserves = []

        self.distBldgDoId = 0

        # we increment this each time we come out of an elevator:
        self.currentFloor = -1
        self.chunkFloor = self.currentFloor % 5

        self.elevatorName = self.__uniqueName('elevator')
        self.floorModel = None

        self.elevatorOutOpen = 0
        self.cage = None

        # initial cog positions vary based on the cog office model
        self.BottomFloor_SuitPositions = [
            Point3(0, 15, 0),
            Point3(10, 20, 0),
            Point3(-7, 24, 0),
            Point3(-10, 0, 0)]
        self.BottomFloor_SuitHs = [75, 170, -91, -44]  # Heading angles

        self.Cubicle_SuitPositions = [
            Point3(0, 18, 0),
            Point3(10, 12, 0),
            Point3(-9, 11, 0),
            Point3(-3, 13, 0)]
        self.Cubicle_SuitHs = [170, 56, -52, 10]

        self.BossOffice_SuitPositions = [
            Point3(0, 15, 0),
            Point3(10, 20, 0),
            Point3(-10, 6, 0),
            Point3(-17, 34, 11),
        ]
        self.BossOffice_SuitHs = [170, 120, 12, 38]

        self.waitMusic = base.loader.loadMusic(
            'phase_7/audio/bgm/encntr_toon_winning_indoor.ogg')
        self.elevatorMusic = base.loader.loadMusic(
            'phase_7/audio/bgm/tt_elevator.ogg')
        self.fsm = ClassicFSM.ClassicFSM('DistributedEndlessSuitInterior',
                                         [State.State('WaitForAllToonsInside',
                                                      self.enterWaitForAllToonsInside,
                                                      self.exitWaitForAllToonsInside,
                                                      ['Elevator']),
                                          State.State('Elevator',
                                                      self.enterElevator,
                                                      self.exitElevator,
                                                      ['Battle', 'Resting']),
                                          State.State('Battle',
                                                      self.enterBattle,
                                                      self.exitBattle,
                                                      ['Resting',
                                                       'Reward',
                                                       'ReservesJoining']),
                                          State.State('ReservesJoining',
                                                      self.enterReservesJoining,
                                                      self.exitReservesJoining,
                                                      ['Battle']),
                                          State.State('Resting',
                                                      self.enterResting,
                                                      self.exitResting,
                                                      ['Elevator']),
                                          State.State('Reward',
                                                      self.enterReward,
                                                      self.exitReward,
                                                      ['Off', 'Resting', 'Elevator']),
                                          State.State('Off',
                                                      self.enterOff,
                                                      self.exitOff,
                                                      ['Elevator',
                                                       'WaitForAllToonsInside',
                                                       'Battle']),
                                          ],
                                         # Initial State
                                         'Off',
                                         # Final State
                                         'Off',
                                         )

        # make sure we're in the initial state
        self.fsm.enterInitialState()
        self.cr = cr
        self.extZoneId = 2000
        self.wantCheckpoint = True

    def __uniqueName(self, name):
        DistributedEndlessSuitInterior.id += 1
        return name + f'{DistributedEndlessSuitInterior.id}'

    def generate(self):
        """generate(self)
        This method is called when the DistributedObject is reintroduced
        to the world, either for the first time or from the cache.
        """
        assert (self.notify.debug("generate()"))
        DistributedObject.DistributedObject.generate(self)

        # listen for the generate event, which will be thrown after the
        # required fields are filled in
        self.announceGenerateName = self.uniqueName('generate')
        self.accept(self.announceGenerateName, self.handleAnnounceGenerate)

        # Load the elevator model
        self.elevatorModelIn = loader.loadModel(
            'phase_4/models/modules/elevator')
        self.leftDoorIn = self.elevatorModelIn.find('**/left-door')
        self.rightDoorIn = self.elevatorModelIn.find('**/right-door')

        self.elevatorModelOut = loader.loadModel(
            'phase_4/models/modules/elevator')
        self.leftDoorOut = self.elevatorModelOut.find('**/left-door')
        self.rightDoorOut = self.elevatorModelOut.find('**/right-door')

    def setElevatorLights(self, elevatorModel):
        # we don't want elevator lights for endless buildings
        if not elevatorModel.find("**/light_panel").isEmpty():
            elevatorModel.find("**/light_panel").removeNode()
            elevatorModel.find("**/light_panel_frame").removeNode()
        return

    def handleAnnounceGenerate(self, obj):
        """
        handleAnnounceGenerate is called after all of the required fields are
        filled in
        'obj' is another copy of self
        """
        self.ignore(self.announceGenerateName)
        self.cageDoorSfx = loader.loadSfx('phase_5/audio/sfx/CHQ_SOS_cage_door.ogg')
        self.cageLowerSfx = loader.loadSfx('phase_5/audio/sfx/CHQ_SOS_cage_lower.ogg')
        assert (self.notify.debug('joining DistributedSuitInterior'))
        # Update the minigame AI to join our local toon doId
        self.sendUpdate('setAvatarJoined', [])

    def disable(self):
        assert (self.notify.debug('disable()'))
        self.fsm.requestFinalState()
        self.__cleanupIntervals()
        self.ignoreAll()
        self.__cleanup()
        DistributedObject.DistributedObject.disable(self)

    def delete(self):
        assert (self.notify.debug('delete()'))
        del self.waitMusic
        del self.elevatorMusic
        del self.openSfx
        del self.closeSfx
        del self.fsm
        # No more battle multiplier
        base.localAvatar.inventory.setBattleCreditMultiplier(1)
        DistributedObject.DistributedObject.delete(self)

    def __cleanup(self):
        self.toons = []
        self.suits = []
        self.reserveSuits = []
        self.joiningReserves = []
        # Clean up elevator models
        if (self.elevatorModelIn is not None):
            self.elevatorModelIn.removeNode()
        if (self.elevatorModelOut is not None):
            self.elevatorModelOut.removeNode()
        # Clean up current floor
        if (self.floorModel is not None):
            self.floorModel.removeNode()
        self.leftDoorIn = None
        self.rightDoorIn = None
        self.leftDoorOut = None
        self.rightDoorOut = None

    def __cleanupIntervals(self):
        for interval in list(self.activeIntervals.values()):
            interval.finish()
        self.activeIntervals = {}

    def __closeInElevator(self):
        self.leftDoorIn.setPos(3.5, 0, 0)
        self.rightDoorIn.setPos(-3.5, 0, 0)

    def __playElevator(self, ts, name, callback):
        # Load the floor model

        SuitHs = []  # Heading angles
        SuitPositions = []

        if self.floorModel:
            self.floorModel.removeNode()
            self.floorModel = None

        if self.currentFloor == 0:
            # bottom floor
            self.floorModel = loader.loadModel('phase_7/models/modules/suit_interior')
            SuitHs = self.BottomFloor_SuitHs
            SuitPositions = self.BottomFloor_SuitPositions
        elif self.chunkFloor == 3:
            # Boss floor
            self.floorModel = loader.loadModel('phase_7/models/modules/boss_suit_office')
            SuitHs = self.BossOffice_SuitHs
            SuitPositions = self.BossOffice_SuitPositions
        elif self.chunkFloor == 4 and self.wantCheckpoint:
            # Checkpoint floor

            # Set up the cage
            self.floorModel = loader.loadModel('phase_7/models/modules/suit_interior')
            if self.cage:
                self.cage = None


        else:
            # middle floor
            self.floorModel = loader.loadModel('phase_7/models/modules/cubicle_room')
            SuitHs = self.Cubicle_SuitHs
            SuitPositions = self.Cubicle_SuitPositions

        self.floorModel.reparentTo(render)

        # We need to name this something more useful (and we'll need the
        # location of the opposite elevator as well)
        elevIn = self.floorModel.find('**/elevator-in')
        elevOut = self.floorModel.find('**/elevator-out')

        # Position the suits
        for index in range(len(self.suits)):
            # check to make sure we have a suit in this index by checking the length of the suits list
            if index > len(self.suits) - 1:
                break 
            if index > len(SuitPositions) - 1:
                break

            
            self.suits[index].setPos(SuitPositions[index])
            if len(self.suits) > 2:
                self.suits[index].setH(SuitHs[index])
            else:
                # if there's 2 or 1 suits, make them face fwd since there's no other suits
                # they would be to be talking to
                self.suits[index].setH(
                    170)
            self.suits[index].loop('neutral')

        # Position the toons
        for toon in self.toons:
            toon.reparentTo(self.elevatorModelIn)
            assert (self.toonIds.count(toon.doId) == 1)
            index = self.toonIds.index(toon.doId)
            assert (index >= 0 and index <= 3)
            toon.setPos(ElevatorPoints[index][0],
                        ElevatorPoints[index][1],
                        ElevatorPoints[index][2])
            toon.setHpr(180, 0, 0)
            toon.loop('neutral')

        # Show the elevator and position it in the correct place for the floor
        self.elevatorModelIn.reparentTo(elevIn)
        # Start with the doors in closed position
        self.leftDoorIn.setPos(3.5, 0, 0)
        self.rightDoorIn.setPos(-3.5, 0, 0)

        # Show the elevator and position it in the correct place for the floor
        self.elevatorModelOut.reparentTo(elevOut)
        # Start with the doors in closed position
        self.leftDoorOut.setPos(3.5, 0, 0)
        self.rightDoorOut.setPos(-3.5, 0, 0)

        # Position the camera behind the toons
        camera.reparentTo(self.elevatorModelIn)
        camera.setH(180)
        camera.setPos(0, 14, 4)

        # Play elevator music
        base.playMusic(self.elevatorMusic, looping=1, volume=0.8)

        # Ride the elevator, then open the doors.
        track = Sequence(
            ElevatorUtils.getRideElevatorInterval(ELEVATOR_NORMAL),
            ElevatorUtils.getOpenInterval(self, self.leftDoorIn, self.rightDoorIn,
                                          self.openSfx, None, type=ELEVATOR_NORMAL),
            Func(camera.wrtReparentTo, render),
        )

        for toon in self.toons:
            track.append(Func(toon.wrtReparentTo, render))
        track.append(Func(callback))
        track.start(ts)
        self.activeIntervals[name] = track


      

    def enterElevator(self, ts=0):
        # Load model for the current floor and the suit models for the floor
        try:
            Discord.endlessBuilding()
        except BaseException:
            self.notify.warning("Toon isn't running discord")
        self.notify.info('enterElevator()')

        self.currentFloor += 1
        self.chunkFloor = self.currentFloor % 5
        # self.cr.playGame.getPlace().currentFloor = self.currentFloor
        self.setElevatorLights(self.elevatorModelIn)
        self.setElevatorLights(self.elevatorModelOut)

        self.__playElevator(ts, self.elevatorName, self.__handleElevatorDone)

        # Get the floor multiplier a constant 6x value
        mult = ToontownBattleGlobals.getCreditMultiplier(6)
        # Now set the inventory battleCreditMult
        base.localAvatar.inventory.setBattleCreditMultiplier(mult)

    def __addToon(self, toon):
        assert (self.notify.debug('addToon(%d)' % toon.doId))
        self.accept(toon.uniqueName('disable'),
                    self.__handleUnexpectedExit, extraArgs=[toon])

    def __handleUnexpectedExit(self, toon):
        self.notify.warning('handleUnexpectedExit() - toon: %d' % toon.doId)

        self.__removeToon(toon, unexpected=1)

    def __removeToon(self, toon, unexpected=0):
        # Reward the toon for their efforts based on last checkpoint
        self.rewardToonBasedOnCheckpoint(toon)
        if (self.toons.count(toon) == 1):
            self.toons.remove(toon)
        self.ignore(toon.uniqueName('disable'))

    def __finishInterval(self, name):
        """ Force the specified interval to jump to the end
        """
        if (name in self.activeIntervals):
            interval = self.activeIntervals[name]
            if (interval.isPlaying()):
                assert (self.notify.debug('finishInterval(): %s' % \
                                          interval.getName()))
                interval.finish()

    def rewardToonBasedOnCheckpoint(self, toon):
        # TODO write logic for this

        # Reward gag experience and whatnot

        return

    def enterReward(self, ts=0):
        assert (self.notify.debug('enterReward()'))
        # base.localAvatar.b_setParent(ToontownGlobals.SPHidden)
        return None

    def exitReward(self):
        return None

    def getZoneId(self):
        return self.zoneId

    def setZoneId(self, zoneId):
        self.zoneId = zoneId
        self.notify.debug(f'Zone id : {self.zoneId}')

    def exitResting(self):
        self.waitMusic.stop()
        return

    def getExtZoneId(self):
        return self.extZoneId

    def setExtZoneId(self, extZoneId):
        self.extZoneId = extZoneId

    def getDistBldgDoId(self):
        return 0

    def setDistBldgDoId(self, distBldgDoId):
        self.distBldgDoId = distBldgDoId

    def setToons(self, toonIds, hack):
        assert (self.notify.debug('setToons(): %s' % toonIds))
        self.toonIds = toonIds
        oldtoons = self.toons
        self.toons = []
        for toonId in toonIds:
            if (toonId != 0):
                if (toonId in self.cr.doId2do):
                    toon = self.cr.doId2do[toonId]
                    toon.stopSmooth()
                    self.toons.append(toon)
                    if (oldtoons.count(toon) == 0):
                        assert (self.notify.debug('setToons() - new toon: %d' % \
                                                  toon.doId))
                        self.__addToon(toon)
                else:
                    self.notify.warning('setToons() - no toon: %d' % toonId)
        for toon in oldtoons:
            if (self.toons.count(toon) == 0):
                self.__removeToon(toon)

    def setSuits(self, suitIds, reserveIds, values):
        self.notify.debug('setSuits(): active %s reserve %s values %s' \
                          % (suitIds, reserveIds, values))
        oldsuits = self.suits
        self.suits = []
        self.joiningReserves = []
        for suitId in suitIds:
            if (suitId in self.cr.doId2do):
                suit = self.cr.doId2do[suitId]
                self.suits.append(suit)
                # Set this on the client
                suit.fsm.request('Battle')
                # This will allow client to respond to setState() from the
                # server from here on out
                suit.buildingSuit = 1
                suit.reparentTo(render)
                if (oldsuits.count(suit) == 0):
                    assert (self.notify.debug('setSuits() suit: %d joining' % \
                                              suit.doId))
                    self.joiningReserves.append(suit)
            else:
                self.notify.warning('setSuits() - no suit: %d' % suitId)
        self.reserveSuits = []
        assert (len(reserveIds) == len(values))
        for index in range(len(reserveIds)):
            suitId = reserveIds[index]
            if (suitId in self.cr.doId2do):
                suit = self.cr.doId2do[suitId]
                self.reserveSuits.append((suit, values[index]))
            else:
                self.notify.warning('setSuits() - no suit: %d' % suitId)

        if (len(self.joiningReserves) > 0):
            assert (self.notify.debug('setSuits() reserves joining'))
            self.fsm.request('ReservesJoining')

    def setState(self, state, timestamp):
        self.notify.info("setState(%s, %d)" % \
                         (state, timestamp))
        self.fsm.request(state, [globalClockDelta.localElapsedTime(timestamp)])

    def d_elevatorDone(self):
        assert (self.notify.debug('network:elevatorDone(%d)' % base.localAvatar.doId))
        self.sendUpdate('elevatorDone', [])

    def d_reserveJoinDone(self):
        assert (self.notify.debug('network:reserveJoinDone(%d)' % base.localAvatar.doId))
        self.sendUpdate('reserveJoinDone', [])

    def enterOff(self, ts=0):
        self.notify.debug('enterOff()')
        return None

    def exitOff(self):
        return None

    def enterWaitForAllToonsInside(self, ts=0):
        return None

    def exitWaitForAllToonsInside(self):
        return None

    def __handleElevatorDone(self):
        self.notify.info('handleElevatorDone()')
        self.d_elevatorDone()

    def exitElevator(self):
        self.elevatorMusic.stop()
        self.__finishInterval(self.elevatorName)
        return None

    def __playCloseElevatorOut(self, name):
        # Close the elevator doors
        track = Sequence(
            Wait(SUIT_LEAVE_ELEVATOR_TIME),
            Parallel(SoundInterval(self.closeSfx),
                     LerpPosInterval(self.leftDoorOut,
                                     ElevatorData[ELEVATOR_NORMAL]['closeTime'],
                                     ElevatorUtils.getLeftClosePoint(ELEVATOR_NORMAL),
                                     startPos=Point3(0, 0, 0),
                                     blendType='easeOut'),
                     LerpPosInterval(self.rightDoorOut,
                                     ElevatorData[ELEVATOR_NORMAL]['closeTime'],
                                     ElevatorUtils.getRightClosePoint(ELEVATOR_NORMAL),
                                     startPos=Point3(0, 0, 0),
                                     blendType='easeOut')
                     ),
        )
        track.start()
        self.activeIntervals[name] = track

    def enterBattle(self, ts=0):
        #if self.chunkFloor == 4:

            #self.setState('Resting')
            
            #return
            
            
        self.notify.info('enterBattle()')
        if (self.elevatorOutOpen == 1):
            self.__playCloseElevatorOut(self.uniqueName('close-out-elevator'))

            # Watch reserve suits as they walk from the elevator
            camera.setPos(0, -15, 6)
            camera.headsUp(self.elevatorModelOut)
        return None

    def exitBattle(self):
        if (self.elevatorOutOpen == 1):
            self.__finishInterval(self.uniqueName('close-out-elevator'))
            self.elevatorOutOpen = 0
        return None

    ##### ReservesJoining state #####

    def __playReservesJoining(self, ts, name, callback):
        # Position the joining suits
        index = 0
        assert (len(self.joiningReserves) <= 4)
        for suit in self.joiningReserves:
            suit.reparentTo(render)
            suit.setPos(self.elevatorModelOut, Point3(ElevatorPoints[index][0],
                                                      ElevatorPoints[index][1],
                                                      ElevatorPoints[index][2]))
            index += 1
            suit.setH(180)
            suit.loop('neutral')

        # Aim the camera at the far elevator
        track = Sequence(
            Func(camera.wrtReparentTo, self.elevatorModelOut),
            Func(camera.setPos, Point3(0, -8, 2)),
            Func(camera.setHpr, Vec3(0, 10, 0)),

            # Open the elevator doors
            Parallel(SoundInterval(self.openSfx),
                     LerpPosInterval(self.leftDoorOut,
                                     ElevatorData[ELEVATOR_NORMAL]['closeTime'],
                                     Point3(0, 0, 0),
                                     startPos=ElevatorUtils.getLeftClosePoint(ELEVATOR_NORMAL),
                                     blendType='easeOut'),
                     LerpPosInterval(self.rightDoorOut,
                                     ElevatorData[ELEVATOR_NORMAL]['closeTime'],
                                     Point3(0, 0, 0),
                                     startPos=ElevatorUtils.getRightClosePoint(ELEVATOR_NORMAL),
                                     blendType='easeOut'),
                     ),

            # Hold the camera angle for a couple of beats
            Wait(SUIT_HOLD_ELEVATOR_TIME),

            # Reparent the camera to render (enterWaitForInput will
            # position it properly again by the battle)
            Func(camera.wrtReparentTo, render),
            Func(callback),
        )
        track.start(ts)
        self.activeIntervals[name] = track

    def enterReservesJoining(self, ts=0):
        self.notify.info('enterReservesJoining()')
        self.__playReservesJoining(ts, self.uniqueName('reserves-joining'),
                                   self.__handleReserveJoinDone)
        return None

    def __handleReserveJoinDone(self):
        self.notify.info('handleReserveJoinDone()')
        self.joiningReserves = []
        self.elevatorOutOpen = 1
        self.d_reserveJoinDone()

    def exitReservesJoining(self):
        self.__finishInterval(self.uniqueName('reserves-joining'))
        return None

    ##### Resting state #####

    def enterResting(self, ts=0):

        
        if self.chunkFloor == 4:
            #TODO make this a checkpoint floor with gag restock barrels 
            self.cr.playGame.getPlace().setState('walk')
        self.notify.info('enterResting()')
        base.playMusic(self.waitMusic, looping=1, volume=0.7)
        self.__closeInElevator()
        return

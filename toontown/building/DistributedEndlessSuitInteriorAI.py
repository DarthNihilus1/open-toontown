import copy
import random
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import *
from direct.distributed import DistributedObjectAI
from direct.fsm import ClassicFSM, State
from direct.task import Timer
from otp.ai.AIBaseGlobal import *
from toontown.battle import BattleBase, DistributedBattleBldgAI
from toontown.toon import NPCToons
from toontown.toonbase.ToontownBattleGlobals import *
from toontown.building import DistributedElevatorIntAI
from .ElevatorConstants import *

class DistributedEndlessSuitInteriorAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedEndlessSuitInteriorAI')
    # Call this class in toontown central and base it off how sellbot factory entrance is made
    # Will be moved to neo toontown central in the future

    def __init__(self, air, elevator, interiorZoneId):
        self.air = air
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.numFloors = float('inf')
        self.extZoneId = 2000
        self.zoneId = interiorZoneId
        self.avatarExitEvents = []
        self.toons = []
        self.toonSkillPtsGained = {}
        self.toonExp = {}
        self.toonOrigQuests = {}
        self.toonItems = {}
        self.toonOrigMerits = {}
        self.toonMerits = {}
        self.toonParts = {}
        self.helpfulToons = []

        self.currentFloor = 0
        self.chunkFloor = self.currentFloor % 5
        # There is no top floor >:)
        self.topFloor = float('inf')
        #self.bldg = elevator.bldg
        self.elevator = elevator

        self.suits = []
        self.activeSuits = []
        self.reserveSuits = []
        self.joinedReserves = []
        self.suitsKilled = []
        self.suitsKilledPerFloor = []
        self.battle = None

        self.timer = Timer.Timer()

        self.responses = {}
        self.ignoreResponses = 0
        self.ignoreElevatorDone = 0
        self.ignoreReserveJoinDone = 0

        # Register all the toons
        self.toonIds = copy.copy(elevator.seats)
        for toonId in self.toonIds:
            if (toonId != None):
                self.__addToon(toonId)



        self.fsm = ClassicFSM.ClassicFSM(
            'DistributedEndlessSuitInteriorAI',
            [State.State('WaitForAllToonsInside',
                         self.enterWaitForAllToonsInside,
                         self.exitWaitForAllToonsInside,
                         ['Elevator']),
             State.State('Elevator',
                         self.enterElevator,
                         self.exitElevator,
                         ['Battle']),
             State.State('Battle',
                         self.enterBattle,
                         self.exitBattle,
                         ['ReservesJoining',
                          'Resting'
                          'BattleDone']),
             State.State('ReservesJoining',
                         self.enterReservesJoining,
                         self.exitReservesJoining,
                         ['Battle']),
             State.State('BattleDone',
                         self.enterBattleDone,
                         self.exitBattleDone,
                         ['Resting',
                          'Reward']),
             State.State('Resting',
                         self.enterResting,
                         self.exitResting,
                         ['Elevator']),
             State.State('Reward',
                         self.enterReward,
                         self.exitReward,
                         ['Resting']),
             State.State('Off',
                         self.enterOff,
                         self.exitOff,
                         ['WaitForAllToonsInside'])],
            # Initial state
            'Off',
            # Final state
            'Off',
            onUndefTransition=ClassicFSM.ClassicFSM.ALLOW)
        self.fsm.enterInitialState()



    def delete(self):
        assert(self.notify.debug('delete()'))
        self.ignoreAll()
        self.toons = []
        self.toonIds = []
        self.fsm.requestFinalState()
        del self.fsm
        #del self.bldg
       # del self.elevator
        self.timer.stop()
        del self.timer
        self.__cleanupFloorBattle()

        taskName = self.taskName('deleteInterior')
        taskMgr.remove(taskName)

        DistributedObjectAI.DistributedObjectAI.delete(self)

    def __addToon(self, toonId):
        if toonId not in self.air.doId2do:
            self.notify.warning('addToon() - no toon for doId: %d' % toonId)
            return

        # Handle unexpected exits for the toon
        event = self.air.getAvatarExitEvent(toonId)
        self.avatarExitEvents.append(event)
        self.accept(event, self.__handleUnexpectedExit, extraArgs=[toonId])

        self.toons.append(toonId)
        self.responses[toonId] = 0

    def __removeToon(self, toonId):
        # Reward the player based on last checkpoint
        toon = self.air.doId2do.get(toonId)
        self.rewardToon(toon)
        if self.toons.count(toonId):
            self.toons.remove(toonId)

        if self.toonIds.count(toonId):
            self.toonIds[self.toonIds.index(toonId)] = None

        if toonId in self.responses:
            del self.responses[toonId]

        # Ignore future exit events for the toon
        event = self.air.getAvatarExitEvent(toonId)
        if self.avatarExitEvents.count(event):
            self.avatarExitEvents.remove(event)
        self.ignore(event)

    def __handleUnexpectedExit(self, toonId):
        self.notify.warning('toon: %d exited unexpectedly' % toonId)
        self.__removeToon(toonId)
        if (len(self.toons) == 0):
            assert(self.notify.debug('last toon is gone!'))
            self.timer.stop()
            # The last toon exited unexpectedly - if we're in a battle, let
            # the battle clean up first, if we're in Resting state, let
            # the interior elevator clean up first, otherwise, just
            # reset the suit interior.

            # Reward the player based on last checkpoint
            if (self.fsm.getCurrentState().getName() == 'Resting'):
                pass
            elif (self.battle is None):
                self.elevator.deleteSuitInterior()
            self.air.deallocateZone(self.zoneId)


    def elevatorDone(self):
        """elevatorDone(self)
        This message is sent from a client toon to indicate that it has
        finished viewing the elevator movie.
        """
        toonId = self.air.getAvatarIdFromSender()
        if (self.ignoreResponses == 1):
            assert(self.notify.debug('elevatorDone() ignoring toon: %d' % \
                toonId))
            return
        elif (self.fsm.getCurrentState().getName() != 'Elevator'):
            self.notify.warning('elevatorDone() - in state: %s' % \
                self.fsm.getCurrentState().getName())
            return
        elif (self.toons.count(toonId) == 0):
            self.notify.warning('elevatorDone() - toon not in toon list: %d' \
                % toonId)
            assert(self.notify.debug('toons: %s toonIds: %s' % \
                        (self.toons, self.toonIds)))
            return
        assert(toonId in self.responses)
        self.responses[toonId] += 1
        assert(self.notify.debug('toon: %d done with elevator' % toonId))

        if self.__allToonsResponded() and not self.ignoreElevatorDone:
            self.b_setState('Battle')


    def __createFloorBattle(self):
        if (self.chunkFloor == 3):
            assert (self.notify.debug('createFloorBattle() - boss battle'))
            bossBattle = 1
        else:
            bossBattle = 0
        # Create the battle for the floor
        self.battle = DistributedBattleBldgAI.DistributedBattleBldgAI(
            self.air, self.zoneId,
            self.__handleRoundDone, self.__handleBattleDone,
            bossBattle=bossBattle)

        # We store the lists of experience gained and suits killed in
        # the DistributedSuitInterior object, and share these pointers
        # in all battles created for this building.  This way, each
        # battle will actually be modifying the same objects, these,
        # and will thus accumulate the experience from previous
        # battles.
        self.battle.suitsKilled = self.suitsKilled
        self.battle.suitsKilledPerFloor = self.suitsKilledPerFloor
        self.battle.battleCalc.toonSkillPtsGained = self.toonSkillPtsGained
        self.battle.toonExp = self.toonExp
        self.battle.toonOrigQuests = self.toonOrigQuests
        self.battle.toonItems = self.toonItems
        self.battle.toonOrigMerits = self.toonOrigMerits
        self.battle.toonMerits = self.toonMerits
        self.battle.toonParts = self.toonParts
        self.battle.helpfulToons = self.helpfulToons

        # We must set the members of a building battle before we
        # generate it.
        self.battle.setInitialMembers(self.toons, self.suits)
        self.battle.generateWithRequired(self.zoneId)

        # We get a bonus factor applied toward each attack's experience credit.

        # Have constant double exp multiplier in building
        # Also have the highest multiplier be consistent throughought the building
        mult = getCreditMultiplier(6)

        # If there is an invasion, multiply the exp for the duration of this battle
        # Now, if the invasion ends midway through this battle, the players will
        # continue getting credit. This is ok I guess.
        #    if self.air.suitInvasionManager.getInvading():
        # mult *= getInvasionMultiplier()

        self.battle.battleCalc.setSkillCreditMultiplier(mult)

    def __cleanupFloorBattle(self):
        for suit in self.suits:
            self.notify.debug('cleaning up floor suit: %d' % suit.doId)
            if suit.isDeleted():
                self.notify.debug('whoops, suit %d is deleted.' % suit.doId)
            else:
                suit.requestDelete()
        self.suits = []
        self.reserveSuits = []
        self.activeSuits = []
        if (self.battle != None):
            self.battle.requestDelete()
        self.battle = None

    def __handleRoundDone(self, toonIds, totalHp, deadSuits):
        # Determine if any reserves need to join
        self.notify.debug('handleRoundDone() - hp: %d' % totalHp)
        # Calculate the total max HP for all the suits currently on the floor
        totalMaxHp = 0
        for suit in self.suits:
            totalMaxHp += suit.maxHP

        for suit in deadSuits:
            self.activeSuits.remove(suit)

        # Determine if any reserve suits need to join
        if (len(self.reserveSuits) > 0 and len(self.activeSuits) < 4):
            self.joinedReserves = []
            hpPercent = 100 - (totalHp / totalMaxHp * 100.0)
            for info in self.reserveSuits:
                if (info[1] <= hpPercent and
                    len(self.activeSuits) < 4):
                    self.suits.append(info[0])
                    self.activeSuits.append(info[0])
                    self.joinedReserves.append(info)
            for info in self.joinedReserves:
                self.reserveSuits.remove(info)
            if (len(self.joinedReserves) > 0):
                # setSuits() triggers the state change on the client
                self.fsm.request('ReservesJoining')
                self.d_setSuits()
                return

        # See if the battle is done
        if (len(self.activeSuits) == 0):
            self.fsm.request('BattleDone', [toonIds])
        else:
            # No reserve suits to join - tell the battle to continue
            self.battle.resume()

    def __handleBattleDone(self, zoneId, toonIds):
        # self.fsm.request('BattleDone', [toonIds])
        if (len(toonIds) == 0):
            # Rather than shutting down immediately, we give the last
            # toon a few seconds to finish playing his teleport-out
            # animation before the world goes away.

            taskName = self.taskName('deleteInterior')
            taskMgr.doMethodLater(10, self.__doDeleteInterior, taskName)

            # This is not b_setState, because enterReward has to do
            # some things before the broadcast takes place. enterReward
            # will call d_setState when it is ready.

        # We give reward every floor
        # TODO since this calls battlebase we need to check in battlebase if we are in an endless building skip the reward visual
        # Commenting  this out bc testbed exp will be temp
        #self.setState('Reward')
        self.b_setState('Resting')

    def enterBattle(self):
        if self.chunkFloor == 4:
            self.b_setState('Resting')
            return
        if self.battle is None:
            self.__createFloorBattle()
        #self.elevator.d_setFloor(self.currentFloor)
        #self.battle.d_setMembers()

    def exitBattle(self):
        return None


##### BattleDone state #####

    def enterBattleDone(self, toonIds):

        # Find out if any toons are gone
        if (len(toonIds) != len(self.toons)):
            deadToons = []
            for toon in self.toons:
                if (toonIds.count(toon) == 0):
                    deadToons.append(toon)
            for toon in deadToons:
                self.__removeToon(toon)
        self.d_setToons()

        if (len(self.toons) == 0):
            self.elevator.deleteSuitInterior()
            self.air.deallocateZone(self.zoneId)

        else:
           # if (self.currentFloor == self.topFloor):
           #     # Toons beat the building
            #    self.battle.resume(self.currentFloor, topFloor=1)
            #else:
                # The building isn't finished yet - gather up experience and
                # activate the elevator
            self.battle.resume(self.currentFloor, topFloor=0)

    def exitBattleDone(self):
        self.__cleanupFloorBattle()
        return None

    def rewardToon(self, toon):
        # whatever extra rewards we want go here
        return


##### Reward state #####

    def enterReward(self):
       # #Tell the client its reward time
        self.d_setState('Reward')
        return None

    def enterElevator(self):
        self.notify.debug('enterElevator()')

        # Create the suits and place them in their initial positions on
        # the floor
        self.sendZonetoClient()
        self.elevator.planner._genSuitInfos(self.currentFloor)
        suitHandles = self.elevator.planner.genFloorSuits(self.currentFloor)
        self.suits = suitHandles['activeSuits']
        self.activeSuits = []
        for suit in self.suits:
            self.activeSuits.append(suit)
        self.reserveSuits = suitHandles['reserveSuits']

        self.d_setToons()
        self.d_setSuits()
        self.__resetResponses()

        self.d_setState('Elevator')

        self.timer.startCallback(BattleBase.ELEVATOR_T + \
                       ElevatorData[ELEVATOR_NORMAL]['openTime'] + \
                       BattleBase.SERVER_BUFFER_TIME, self.__serverElevatorDone)
        return None

    def sendZonetoClient(self):
        self.notify.debug('Sending client zone id')
        self.sendUpdate('setZoneId', [self.zoneId])
        self.notify.debug('Sending client zone id done')

    def __resetResponses(self):
        self.responses = {}
        for toon in self.toons:
            self.responses[toon] = 0
        self.ignoreResponses = 0

    def __allToonsResponded(self):
        for toon in self.toons:
            if (self.responses[toon] == 0):
                return 0
        self.ignoreResponses = 1
        return 1

    def getZoneId(self):
        assert(self.notify.debug('network:getZoneId()'))
        return self.zoneId

    def getExtZoneId(self):
        return self.extZoneId

    def getDistBldgDoId(self):
        return 0

    def getNumFloors(self):
        return 

  # setToons()
        
    def d_setToons(self):
        assert(self.notify.debug('network:setToons()'))
        self.sendUpdate('setToons', self.getToons())

    def getToons(self):
        sendIds = []
        for toonId in self.toonIds:
            if (toonId == None):
                sendIds.append(0)
            else:
                sendIds.append(toonId)
        assert(self.notify.debug('getToons(): %s' % sendIds))
        return [sendIds, 0]

    # setSuits()

    def d_setSuits(self):
        assert(self.notify.debug('network:setSuits()'))
        self.sendUpdate('setSuits', self.getSuits())

    def getSuits(self):
        suitIds = []
        for suit in self.activeSuits:
            suitIds.append(suit.doId)
        reserveIds = []
        values = []
        for info in self.reserveSuits:
            reserveIds.append(info[0].doId)
            values.append(info[1])
        return [suitIds, reserveIds, values]

    # setState()

    def b_setState(self, state):
        self.d_setState(state)
        self.setState(state)

    def d_setState(self, state):
        assert(self.notify.debug('network:setState(%s)' % state))
        stime = globalClock.getRealTime() + BattleBase.SERVER_BUFFER_TIME
        self.sendUpdate('setState', [state, globalClockDelta.localToNetworkTime(stime)])
        
    def setState(self, state):
        self.fsm.request(state)
        
    def getState(self):
        return [self.fsm.getCurrentState().getName(),
               globalClockDelta.getRealNetworkTime()]

    ##### Messages from the clients #####

    def setAvatarJoined(self):
        """setAvatarJoined(self)
        This message is sent from a client toon to indicate that it
        has finished loading the interior.
        """
        avId = self.air.getAvatarIdFromSender()
        if (self.toons.count(avId) == 0):
            self.air.writeServerEvent('suspicious', avId, 'DistributedSuitInteriorAI.setAvatarJoined from toon not in %s.' % (self.toons))
            self.notify.warning('setAvatarJoined() - av: %d not in list' % \
                avId)
            return

        avatar = self.air.doId2do.get(avId)

        
        assert(avId in self.responses)
        self.responses[avId] += 1
        assert(self.notify.debug('toon: %d in suit interior' % avId))
        if (self.__allToonsResponded()):
            self.fsm.request('Elevator')

   

    def reserveJoinDone(self):
        """reserveJoinDone(self)
        This message is sent from a client toon to indicate that it has
        finished viewing the ReservesJoining movie.
        """
        toonId = self.air.getAvatarIdFromSender()
        if (self.ignoreResponses == 1):
            assert(self.notify.debug('reserveJoinDone() ignoring toon: %d' % \
                toonId))
            return
        elif (self.fsm.getCurrentState().getName() != 'ReservesJoining'):
            self.notify.warning('reserveJoinDone() - in state: %s' % \
                self.fsm.getCurrentState().getName())
            return
        elif (self.toons.count(toonId) == 0):
            self.notify.warning('reserveJoinDone() - toon not in list: %d' \
                % toonId)
            assert(self.notify.debug('toons: %s toonIds: %s' % \
                        (self.toons, self.toonIds)))
            return
        assert(toonId in self.responses)
        self.responses[toonId] += 1
        assert(self.notify.debug('toon: %d done with joining reserves' % \
                                toonId))
        if (self.__allToonsResponded() and
            self.ignoreReserveJoinDone == 0):
            self.b_setState('Battle')

    # Specific State Functions

    ##### Off state #####

    def enterOff(self):
        assert(self.notify.debug('enterOff()'))
        return None

    def exitOff(self):
        return None

    ##### WaitForAllToonsInside state #####

    def enterWaitForAllToonsInside(self):
        assert(self.notify.debug('enterWaitForAllToonsInside()'))
        self.__resetResponses()
        return None

    def exitWaitForAllToonsInside(self):
        self.__resetResponses()
        return None

    ##### Elevator state #####


    def __serverElevatorDone(self):
        assert(self.notify.debug('serverElevatorDone()'))
        self.ignoreElevatorDone = 1
        self.b_setState('Battle')

    def exitElevator(self):
        self.timer.stop()
        self.__resetResponses()
        return None




   


    def __doDeleteInterior(self, task):
        self.elevator.deleteSuitInterior()
        self.air.deallocateZone(self.zoneId)




    ##### ReservesJoining state #####

    def enterReservesJoining(self):
        assert(self.notify.debug('enterReservesJoining()'))
        self.__resetResponses()
        self.timer.startCallback(
            ElevatorData[ELEVATOR_NORMAL]['openTime'] + \
            SUIT_HOLD_ELEVATOR_TIME + \
            BattleBase.SERVER_BUFFER_TIME, 
            self.__serverReserveJoinDone)
        return None

    def __serverReserveJoinDone(self):
        """__serverReserveJoinDone()
        This callback is made only if some of the toons don't send
        their reserveJoinDone() message in a reasonable time--rather
        than waiting for everyone, we simply carry on without them.
        """
        assert(self.notify.debug('serverReserveJoinDone()'))
        self.ignoreReserveJoinDone = 1
        self.b_setState('Battle')

    def exitReservesJoining(self):
        self.timer.stop()
        self.__resetResponses()
        # Join the suits to the battle and tell it to resume
        for info in self.joinedReserves:
            self.battle.suitRequestJoin(info[0])
        self.battle.resume()
        self.joinedReserves = []
        return None



    ##### Resting state #####

    def __handleEnterElevator(self):
        self.fsm.request('Elevator')

    def enterResting(self):
        # TODO Free the npc and reward the player
        self.notify.debug('enterResting()')

        # Tell the elevator to start accepting entrants
        self.intElevator = DistributedElevatorIntAI.DistributedElevatorIntAI(
            self.air, self, self.toons)
        self.intElevator.generateWithRequired(self.zoneId)

        return None

    def handleAllAboard(self, seats):
        if not hasattr(self, "fsm"):
            # If we've already been cleaned up, never mind.
            return
        
        self.notify.debug('handleAllAboard() - toons: %s' % self.toons)

        # Make sure the number of empty seats is correct. If it is empty,
        # reset and get us out of here.
        numOfEmptySeats = seats.count(None)
        if (numOfEmptySeats == 4):
            self.elevator.deleteSuitInterior()
            self.air.deallocateZone(self.zoneId)
            return
        elif (numOfEmptySeats >= 0) and (numOfEmptySeats <=3):
            pass
        else:
            self.error("Bad number of empty seats: %s" % numOfEmptySeats)
        
        for toon in self.toons:
            if seats.count(toon) == 0:
                self.__removeToon(toon)
        self.toonIds = copy.copy(seats)
        self.toons = []
        for toonId in self.toonIds:
            if (toonId != None):
                self.toons.append(toonId)

        self.d_setToons()

        # Increment the floor number
        self.currentFloor += 1
        self.chunkFloor = self.currentFloor % 5
        self.fsm.request('Elevator')
        return

    def exitResting(self):
        self.intElevator.requestDelete()
        del self.intElevator
        return None

    ##### Reward state #####



    def exitReward(self):
        return None
    
    def setNextFloor(self, floor):
        # subtract one since the elevator process adds one
        self.currentFloor = floor - 1
        self.chunkFloor = self.currentFloor % 5
        # self.fsm.request('Elevator')

    def isToonInInterior(self, toonId):
        return (toonId in self.toons)
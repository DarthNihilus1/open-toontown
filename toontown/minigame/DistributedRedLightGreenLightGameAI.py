from math import *
from .DistributedMinigameAI import *
from direct.distributed.ClockDelta import *
from direct.fsm import ClassicFSM, State
from direct.task.Task import Task
from . import RedLightGreenLightGlobals
import random

class DistributedRedLightGreenLightGameAI(DistributedMinigameAI):
    """
    Server-side representation of the Red Light Green Light minigame.
    Handles the FSM and game-specific logic.
    """
    def __init__(self, air):
        super().__init__(air)

        self.gameFSM = ClassicFSM.ClassicFSM('DistributedRedLightGreenLightGameAI',
            [State.State('off', self.enterOff, self.exitOff, ['waitingForPlayers']),
             State.State('waitingForPlayers', self.enterWaitingForPlayers, self.exitWaitingForPlayers, ['instructions']),
             State.State('instructions', self.enterInstructions, self.exitInstructions, ['greenLight']),
             State.State('greenLight', self.enterGreenLight, self.exitGreenLight, ['redLight']),
             State.State('redLight', self.enterRedLight, self.exitRedLight, ['greenLight', 'gameOver']),
             State.State('gameOver', self.enterGameOver, self.exitGameOver, ['off'])])

        self.addChildGameFSM(self.gameFSM)
        self.lightState = RedLightGreenLightGlobals.LIGHT_GREEN
        self.toonsEliminated = set()
        self.toonsPositions = {}

    def generate(self):
        super().generate()
        self.gameFSM.enterInitialState()

    def delete(self):
        self.gameFSM.requestFinalState()
        self.ignoreAll()
        super().delete()

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterWaitingForPlayers(self):
        self.notify.debug('Waiting for players...')

    def exitWaitingForPlayers(self):
        pass

    def enterInstructions(self):
        self.notify.debug('Showing instructions...')

    def exitInstructions(self):
        pass

    def enterGreenLight(self):
        self._setLightState(RedLightGreenLightGlobals.LIGHT_GREEN)

    def exitGreenLight(self):
        self._clearLightChangeTask()

    def enterRedLight(self):
        self._setLightState(RedLightGreenLightGlobals.LIGHT_RED)
        taskMgr.add(self._checkMovement, 'movementCheckTask')

    def exitRedLight(self):
        self._clearLightChangeTask()
        taskMgr.remove('movementCheckTask')

    def enterGameOver(self):
        self.notify.debug('Game over.')
        self._endGame()

    def exitGameOver(self):
        pass

    def _setLightState(self, state):
        self.lightState = state
        duration = random.uniform(*(
            RedLightGreenLightGlobals.GREEN_LIGHT_DURATION_RANGE if state == RedLightGreenLightGlobals.LIGHT_GREEN else RedLightGreenLightGlobals.RED_LIGHT_DURATION_RANGE
        ))
        self.lightChangeTask = taskMgr.doMethodLater(duration, self._changeLight, 'lightChangeTask')
        self.sendUpdate('setLightState', [state])

    def _clearLightChangeTask(self):
        if self.lightChangeTask:
            taskMgr.remove('lightChangeTask')
            self.lightChangeTask = None

    def _changeLight(self, task):
        nextState = 'redLight' if self.lightState == RedLightGreenLightGlobals.LIGHT_GREEN else 'greenLight'
        self.gameFSM.request(nextState)
        return Task.done

    def _checkMovement(self, task):
        for toon in self.toonsList:
            if toon.doId in self.toonsEliminated:
                continue

            currentPos = toon.getPos()
            if toon.doId in self.toonsPositions:
                if currentPos != self.toonsPositions[toon.doId]:
                    self._eliminateToon(toon)

            self.toonsPositions[toon.doId] = currentPos
        return Task.cont

    def _eliminateToon(self, toon):
        self.toonsEliminated.add(toon.doId)
        self.sendUpdate('eliminateToon', [toon.doId])

        if len(self.toonsEliminated) == len(self.toonsList):
            self.gameFSM.request('gameOver')

    def _endGame(self):
        self.notify.debug('Ending game. Cleaning up...')
        self.gameFSM.requestFinalState()
        self.ignoreAll()
        self.toonsEliminated.clear()
        self.toonsPositions.clear()

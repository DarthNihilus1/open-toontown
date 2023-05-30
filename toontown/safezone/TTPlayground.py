from panda3d.core import *
from toontown.toonbase import ToontownGlobals
from . import Playground
import random
from toontown.launcher import DownloadForceAcknowledge
from direct.task.Task import Task
from toontown.hood import ZoneUtil
from direct.fsm import ClassicFSM, State
from toontown.building import Elevator

class TTPlayground(Playground.Playground):

    def __init__(self, loader, parentFSM, doneEvent):
        Playground.Playground.__init__(self, loader, parentFSM, doneEvent)
        self.fsm = ClassicFSM.ClassicFSM('Playground',
                           [State.State('start',
                                        self.enterStart,
                                        self.exitStart,
                                        ['walk', 'deathAck', 
                                        'doorIn', 'tunnelIn']),
                            State.State('walk',
                                        self.enterWalk,
                                        self.exitWalk,
                                        ['drive', 'sit', 'stickerBook',
                                         'TFA', 'DFA', 'trialerFA',
                                         'trolley', 'final',
                                         'doorOut', 'elevator', 'options', 'quest',
                                         'purchase', 'stopped', 'fishing']),
                            State.State('stickerBook',
                                        self.enterStickerBook,
                                        self.exitStickerBook,
                                        ['walk', 'DFA', 'TFA',
                                         # You can get to all of these by jumping over 
                                         # the trigger then opening your book
                                         'trolley', 'final',
                                         'doorOut', 'quest',
                                         'elevator',
                                         'purchase', 'stopped',
                                         'fishing', 'trialerFA',
                                         ]),
                            State.State('sit',
                                        self.enterSit,
                                        self.exitSit,
                                        ['walk',
                                         'DFA', # So you can teleport to a friend
                                         'trialerFA',
                                         ]),
                            State.State('drive',
                                        self.enterDrive,
                                        self.exitDrive,
                                        ['walk',
                                         'DFA', # So you can teleport to a friend
                                         'trialerFA',
                                         ]),
                            State.State('trolley',
                                        self.enterTrolley,
                                        self.exitTrolley,
                                        ['walk']),
                            State.State('doorIn',
                                        self.enterDoorIn,
                                        self.exitDoorIn,
                                        ['walk']),
                            State.State('doorOut',
                                        self.enterDoorOut,
                                        self.exitDoorOut,
                                        ['walk']), # 'final'
                            # Tutorial Force Acknowledge:
                            State.State('TFA',
                                        self.enterTFA,
                                        self.exitTFA,
                                        ['TFAReject', 'DFA']),
                            State.State('TFAReject',
                                        self.enterTFAReject,
                                        self.exitTFAReject,
                                        ['walk']),
                            # Trialer Force Acknowledge:
                            State.State('trialerFA',
                                        self.enterTrialerFA,
                                        self.exitTrialerFA,
                                        ['trialerFAReject', 'DFA']),
                            State.State('trialerFAReject',
                                        self.enterTrialerFAReject,
                                        self.exitTrialerFAReject,
                                        ['walk']),
                            # Download Force Acknowledge
                            State.State('DFA',
                                        self.enterDFA,
                                        self.exitDFA,
                                        ['DFAReject', 'NPCFA', 'HFA']),
                            State.State('DFAReject',
                                        self.enterDFAReject,
                                        self.exitDFAReject,
                                        ['walk']),
                            # NPC Force Acknowledge:
                            State.State('NPCFA',
                                        self.enterNPCFA,
                                        self.exitNPCFA,
                                        ['NPCFAReject', 'HFA']),
                            State.State('NPCFAReject',
                                        self.enterNPCFAReject,
                                        self.exitNPCFAReject,
                                        ['walk']),
                            # Health Force Acknowledge
                            State.State('HFA',
                                        self.enterHFA,
                                        self.exitHFA,
                                        ['HFAReject', 'teleportOut', 'tunnelOut']),
                            State.State('HFAReject',
                                        self.enterHFAReject,
                                        self.exitHFAReject,
                                        ['walk']),
                            State.State('deathAck',
                                        self.enterDeathAck,
                                        self.exitDeathAck,
                                        ['teleportIn']),
                            State.State('teleportIn',
                                        self.enterTeleportIn,
                                        self.exitTeleportIn,
                                        ['walk', 'popup']),
                            State.State('popup',
                                        self.enterPopup,
                                        self.exitPopup,
                                        ['walk']),
                            State.State('teleportOut',
                                        self.enterTeleportOut,
                                        self.exitTeleportOut,
                                        ['deathAck', 'teleportIn']), # 'final'
                            State.State('died', # No transitions to "died" in the playground.
                                        self.enterDied,
                                        self.exitDied,
                                        ['final']),
                            State.State('tunnelIn',
                                        self.enterTunnelIn,
                                        self.exitTunnelIn,
                                        ['walk']),
                            State.State('tunnelOut',
                                        self.enterTunnelOut,
                                        self.exitTunnelOut,
                                        ['final']),
                            State.State('elevator',
                                        self.enterElevator,
                                        self.exitElevator,
                                        ['walk', 'stopped']),
                            State.State('quest',
                                        self.enterQuest,
                                        self.exitQuest,
                                        ['walk']),
                            State.State('purchase',
                                        self.enterPurchase,
                                        self.exitPurchase,
                                        ['walk']),
                            State.State('stopped',
                                        self.enterStopped,
                                        self.exitStopped,
                                        ['walk', 'elevator']),
                            State.State('fishing',
                                        self.enterFishing,
                                        self.exitFishing,
                                        ['walk']),                            
                            State.State('final',
                                        self.enterFinal,
                                        self.exitFinal,
                                        ['start'])],

                           # Initial State
                           'start',
                           # Final State
                           'final',
                           )
        self.parentFSM = parentFSM
        self.elevatorDoneEvent = "elevatorDone"

    def load(self):
        Playground.Playground.load(self)

    def unload(self):
        Playground.Playground.unload(self)

    def enter(self, requestStatus):
        Playground.Playground.enter(self, requestStatus)
        taskMgr.doMethodLater(1, self.__birds, 'TT-birds')

    def exit(self):
        Playground.Playground.exit(self)
        taskMgr.remove('TT-birds')

    def __birds(self, task):
        base.playSfx(random.choice(self.loader.birdSound))
        t = random.random() * 20.0 + 1
        taskMgr.doMethodLater(t, self.__birds, 'TT-birds')
        return Task.done

    def doRequestLeave(self, requestStatus):
        self.fsm.request('trialerFA', [requestStatus])

    def enterDFA(self, requestStatus):
        doneEvent = 'dfaDoneEvent'
        self.accept(doneEvent, self.enterDFACallback, [requestStatus])
        self.dfa = DownloadForceAcknowledge.DownloadForceAcknowledge(doneEvent)
        hood = ZoneUtil.getCanonicalZoneId(requestStatus['hoodId'])
        if hood == ToontownGlobals.MyEstate:
            self.dfa.enter(base.cr.hoodMgr.getPhaseFromHood(ToontownGlobals.MyEstate))
        elif hood == ToontownGlobals.GoofySpeedway:
            self.dfa.enter(base.cr.hoodMgr.getPhaseFromHood(ToontownGlobals.GoofySpeedway))
        elif hood == ToontownGlobals.PartyHood:
            self.dfa.enter(base.cr.hoodMgr.getPhaseFromHood(ToontownGlobals.PartyHood))
        else:
            self.dfa.enter(5)

    def showPaths(self):
        from toontown.classicchars import CCharPaths
        from toontown.toonbase import TTLocalizer
        self.showPathPoints(CCharPaths.getPaths(TTLocalizer.Mickey))

    def detectedElevatorCollision(self, distElevator):
        self.notify.debug("detectedElevatorCollision()")
        self.fsm.request("elevator", [distElevator])

    # elevator state
    # (For boarding a building elevator)

    def enterElevator(self, distElevator, skipDFABoard=0):
        self.notify.debug("enterElevator()")

        self.accept(self.elevatorDoneEvent, self.handleElevatorDone)
        self.elevator = Elevator.Elevator(self.fsm.getStateNamed("elevator"),
                                          self.elevatorDoneEvent,
                                          distElevator)
        if skipDFABoard:
            self.elevator.skipDFABoard = 1
        # elevatorFSM is now on the DO
        distElevator.elevatorFSM = self.elevator
        self.elevator.load()
        self.elevator.enter()

    def exitElevator(self):
        assert(self.notify.debug("exitElevator()"))
        self.ignore(self.elevatorDoneEvent)
        self.elevator.unload()
        self.elevator.exit()
        del self.elevator

    def handleElevatorDone(self, doneStatus):
        self.notify.debug("handling elevator done event")
        where = doneStatus['where']
        if (where == 'reject'):
            # If there has been a reject the Elevator should show an
            # elevatorNotifier message and put the toon in the stopped state.
            # Don't request the walk state here. Let the the toon be stuck in the
            # stopped state till the player removes that message from his screen.
            # Removing the message will automatically put him in the walk state there.
            # Put the player in the walk state only if there is no elevator message.
            if hasattr(base.localAvatar, "elevatorNotifier") and base.localAvatar.elevatorNotifier.isNotifierOpen():
                pass
            else:
                self.fsm.request("walk")
        elif (where == 'exit'):
            self.fsm.request("walk")
        elif where == 'TTPlayground':
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)
            
        elif (where == 'endlessSuitInterior'):
            # this shouldn't even be possible but just in case
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)
        else:
            self.notify.error("Unknown mode: " + where +
                              " in handleElevatorDone")
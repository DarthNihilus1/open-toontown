from otp.ai.AIBaseGlobal import *
from panda3d.core import *
from .DistributedNPCToonBaseAI import *
from . import ToonDNA
from direct.task.Task import Task
from toontown.ai import DatabaseObject
from toontown.estate import ClosetGlobals

class DistributedNPCTailorAI(DistributedNPCToonBaseAI):
    freeClothes = simbase.config.GetBool('free-clothes', 0)
    housingEnabled = simbase.config.GetBool('want-housing', 1)

    def __init__(self, air, npcId):
        DistributedNPCToonBaseAI.__init__(self, air, npcId)
        self.timedOut = 0
        self.givesQuests = 0
        self.customerDNA = None
        self.customerId = None
        return

    def getTailor(self):
        return 1

    def delete(self):
        taskMgr.remove(self.uniqueName('clearMovie'))
        self.ignoreAll()
        self.customerDNA = None
        self.customerId = None
        DistributedNPCToonBaseAI.delete(self)
        return

    def avatarEnter(self):
        avId = self.air.getAvatarIdFromSender()
        if avId not in self.air.doId2do:
            self.notify.warning('Avatar: %s not found' % avId)
            return
        if self.isBusy(avId):
            self.freeAvatar(avId)
            return
        av = self.air.doId2do[avId]
        self.customerDNA = ToonDNA.ToonDNA()
        self.customerDNA.makeFromNetString(av.getDNAString())
        self.customerId = avId
        av.b_setDNAString(self.customerDNA.makeNetString())
        self.acceptOnce(self.air.getAvatarExitEvent(avId), self.__handleUnexpectedExit, extraArgs=[avId])
        flag = NPCToons.PURCHASE_MOVIE_START_BROWSE
        if self.freeClothes:
            flag = NPCToons.PURCHASE_MOVIE_START
            if self.housingEnabled and self.isClosetAlmostFull(av):
                flag = NPCToons.PURCHASE_MOVIE_START_NOROOM
        elif self.air.questManager.hasTailorClothingTicket(av, self) == 1:
            flag = NPCToons.PURCHASE_MOVIE_START
            if self.housingEnabled and self.isClosetAlmostFull(av):
                flag = NPCToons.PURCHASE_MOVIE_START_NOROOM
        elif self.air.questManager.hasTailorClothingTicket(av, self) == 2:
            flag = NPCToons.PURCHASE_MOVIE_START
            if self.housingEnabled and self.isClosetAlmostFull(av):
                flag = NPCToons.PURCHASE_MOVIE_START_NOROOM
        self.sendShoppingMovie(avId, flag)
        DistributedNPCToonBaseAI.avatarEnter(self)

    def isClosetAlmostFull(self, av):
        numClothes = len(av.clothesTopsList) / 4 + len(av.clothesBottomsList) / 2
        if numClothes >= av.maxClothes - 1:
            return 1
        return 0

    def sendShoppingMovie(self, avId, flag):
        if avId not in self.busy:
            self.busy.append(avId)
        self.sendUpdate('setMovie', [flag,
         self.npcId,
         avId,
         ClockDelta.globalClockDelta.getRealNetworkTime()])
        taskMgr.doMethodLater(NPCToons.TAILOR_COUNTDOWN_TIME, self.sendTimeoutMovie, self.uniqueName('clearMovie'))

    def rejectAvatar(self, avId):
        self.notify.warning('rejectAvatar: should not be called by a Tailor!')

    def sendTimeoutMovie(self, task):
        avId = self.air.getAvatarIdFromSender()
        toon = self.air.doId2do.get(self.customerId)
        if toon != None and self.customerDNA:
            toon.b_setDNAString(self.customerDNA.makeNetString())
        self.timedOut = 1
        self.sendUpdate('setMovie', [NPCToons.PURCHASE_MOVIE_TIMEOUT,
         self.npcId,
         avId,
         ClockDelta.globalClockDelta.getRealNetworkTime()])
        self.sendClearMovie(None)
        return Task.done

    def sendClearMovie(self, task):
        avId = self.air.getAvatarIdFromSender()
        self.ignore(self.air.getAvatarExitEvent(avId))
        self.customerDNA = None
        self.customerId = None
        self.busy.remove(avId)
        self.timedOut = 0
        self.sendUpdate('setMovie', [NPCToons.PURCHASE_MOVIE_CLEAR,
         self.npcId,
         avId,
         ClockDelta.globalClockDelta.getRealNetworkTime()])
        self.sendUpdate('setCustomerDNA', [0, ''])
        return Task.done

    def completePurchase(self, avId):
        if avId not in self.busy:
            self.busy.append(avId)
        self.sendUpdate('setMovie', [NPCToons.PURCHASE_MOVIE_COMPLETE,
         self.npcId,
         avId,
         ClockDelta.globalClockDelta.getRealNetworkTime()])
        self.sendClearMovie(None)
        return

    def setDNA(self, blob, finished, which):
        avId = self.air.getAvatarIdFromSender()
        if avId != self.customerId:
            if self.customerId:
                self.air.writeServerEvent('suspicious', avId, 'DistributedNPCTailorAI.setDNA customer is %s' % self.customerId)
                self.notify.warning('customerId: %s, but got setDNA for: %s' % (self.customerId, avId))
            return
        testDNA = ToonDNA.ToonDNA()
        if not testDNA.isValidNetString(blob):
            self.air.writeServerEvent('suspicious', avId, 'DistributedNPCTailorAI.setDNA: invalid dna: %s' % blob)
            return
        if avId in self.air.doId2do:
            av = self.air.doId2do[avId]
            if finished == 2 and which > 0:
                if self.air.questManager.removeClothingTicket(av, self) == 1 or self.freeClothes:
                    av.b_setDNAString(blob)
                    if which & ClosetGlobals.SHIRT:
                        if av.addToClothesTopsList(self.customerDNA.topTex, self.customerDNA.topTexColor, self.customerDNA.sleeveTex, self.customerDNA.sleeveTexColor) == 1:
                            av.b_setClothesTopsList(av.getClothesTopsList())
                        else:
                            self.notify.warning('NPCTailor: setDNA() - unable to save old tops - we exceeded the tops list length')
                    if which & ClosetGlobals.SHORTS:
                        if av.addToClothesBottomsList(self.customerDNA.botTex, self.customerDNA.botTexColor) == 1:
                            av.b_setClothesBottomsList(av.getClothesBottomsList())
                        else:
                            self.notify.warning('NPCTailor: setDNA() - unable to save old bottoms - we exceeded the bottoms list length')
                    self.air.writeServerEvent('boughtTailorClothes', avId, '%s|%s|%s' % (self.doId, which, self.customerDNA.asTuple()))
                else:
                    self.air.writeServerEvent('suspicious', avId, 'DistributedNPCTailorAI.setDNA bogus clothing ticket')
                    self.notify.warning('NPCTailor: setDNA() - client tried to purchase with bogus clothing ticket!')
                    if self.customerDNA:
                        av.b_setDNAString(self.customerDNA.makeNetString())
            elif finished == 1:
                if self.customerDNA:
                    av.b_setDNAString(self.customerDNA.makeNetString())
            else:
                self.sendUpdate('setCustomerDNA', [avId, blob])
        else:
            self.notify.warning('no av for avId: %d' % avId)
        if self.timedOut == 1 or finished == 0:
            return
        if avId in self.busy:
            taskMgr.remove(self.uniqueName('clearMovie'))
            self.completePurchase(avId)
        # elif self.busy:
        #     self.air.writeServerEvent('suspicious', avId, 'DistributedNPCTailorAI.setDNA busy with %s' % self.busy)
        #     self.notify.warning('setDNA from unknown avId: %s busy: %s' % (avId, self.busy))

    def __handleUnexpectedExit(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' has exited unexpectedly')
        if self.customerId == avId:
            toon = self.air.doId2do.get(avId)
            if toon == None:
                toon = DistributedToonAI.DistributedToonAI(self.air)
                toon.doId = avId
            if self.customerDNA:
                toon.b_setDNAString(self.customerDNA.makeNetString())
                db = DatabaseObject.DatabaseObject(self.air, avId)
                db.storeObject(toon, ['setDNAString'])
        else:
            self.notify.warning('invalid customer avId: %s, customerId: %s ' % (avId, self.customerId))
        if avId in self.busy:
            self.sendClearMovie(None)
        else:
            self.notify.warning('not busy with avId: %s, busy: %s ' % (avId, self.busy))
        return

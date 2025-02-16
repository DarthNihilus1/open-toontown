
# taken from Anesidora

# PartyDB and inviteDB - DarthMDev

import time
import math
import json
import os 
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.AsyncRequest import AsyncRequest
from otp.distributed import OtpDoGlobals
#from toontown.uberdog.PartiesUdLog import partiesUdLog
from toontown.toonbase import ToontownGlobals
from toontown.parties import PartyGlobals
from toontown.parties import PartyUtils
from toontown.ai.ToontownAIMsgTypes import PARTY_MANAGER_UD_TO_ALL_AI
from datetime import timedelta  # Used for testing, to create random test party
from datetime import datetime   # Used for testing, to create random test party

class PartyDb:
    """
     PartyDB is the base class for all party database interface implementations.
    """
    def __init__(self, partyManager):
        self.partyManager = partyManager
        # setup partyToId dictionary
        self.partyDbFilePath = config.GetString('partydb-local-file', 'astron/databases/parties.json')
        # Load the JSON file if it exists.
        if os.path.exists(self.partyDbFilePath):
            with open(self.partyDbFilePath, 'r') as file:
                self.partyToId = json.load(file)
        else:
            # If not, create a blank file.
            self.partyToId = {}
            with open(self.partyDbFilePath, 'w') as file:
                json.dump(self.partyToId, file)
        


    def save(self):
        """Save the current state of the partyToId dictionary to the JSON file."""
        with open(self.partyDbFilePath, 'w') as file:
            json.dump(self.partyToId, file)

    def load(self):
        """Load the current state of the partyToId dictionary from the JSON file."""
        with open(self.partyDbFilePath, 'r') as file:
            self.partyToId = json.load(file)

    def putParty(self, hostId, startTime, endTime, isPrivate, inviteTheme, activities, decorations, status):
        """
        Add a party to the database.
        """
        self.load()
        partyId = len(self.partyToId) + 1  # Generate a new party ID
        party = {
            'partyId': partyId,
            'hostId': hostId,
            'startTime': startTime,
            'endTime': endTime,
            'isPrivate': isPrivate,
            'inviteTheme': inviteTheme,
            'activities': activities,
            'decorations': decorations,
            'statusId': status
        }
        self.partyToId[partyId] = party
        self.save()
        return True
    

    def getPartiesOfHost(self, hostId):
        """
        Get all parties of a host.
        """
        self.load()
        for party in self.partyToId.values():
            if party['hostId'] == hostId:
                yield party
        

    def getPartiesOfHostThatCanStart(self, hostId):
        """
        Get all parties of a host that can start.
        """
        self.load()
        for party in self.partyToId.values():
            if party['hostId'] == hostId and party['statusId'] == PartyGlobals.PartyStatus.Pending:
                yield party

    def getPartiesAvailableToStart(self, thresholdTime):
        """
        Get all parties that can start.
        """
        self.load()
        for party in self.partyToId.values():
            if party['startTime'] <= thresholdTime and party['statusId'] == PartyGlobals.PartyStatus.Pending:
                yield party

    def getPrioritizedParties(self, partyIds, thresholdTime, limit, future, cancelled):
        """
        Get a prioritized list of parties.

        partyIds: list of partyIds to consider
        thresholdTime: the time to compare against
        limit: the maximum number of parties to return
        future: whether to consider future or past parties
        cancelled: whether to consider cancelled or finished parties

        Returns a list of partyInfo dictionaries.
        """
        self.load()
        for partyId in partyIds:
            party = self.partyToId[partyId]
            if future:
                if party['startTime'] >= thresholdTime:
                    if not cancelled:
                        if party['statusId'] == PartyGlobals.PartyStatus.Pending:
                            yield party
                    else:
                        if party['statuId'] == PartyGlobals.PartyStatus.Cancelled:
                            yield party
            else:
                if party['startTime'] < thresholdTime:
                    if not cancelled:
                        if party['statusId'] == PartyGlobals.PartyStatus.Finished:
                            yield party
                    else:
                        if party['statusId'] == PartyGlobals.PartyStatus.Cancelled:
                            yield party


    def getHostPrioritizedParties(self, hostId, thresholdTime, limit, future, cancelled):
        """
        Get a prioritized list of parties of a host.

        hostId: the host to consider
        thresholdTime: the time to compare against
        limit: the maximum number of parties to return
        future: whether to consider future or past parties
        cancelled: whether to consider cancelled or finished parties

        Returns a list of partyInfo dictionaries.
        """
        self.load()
        for party in self.partyToId.values():
            if party['hostId'] == hostId:
                if future:
                    if party['startTime'] >= thresholdTime:
                        if not cancelled:
                            if party['statusId'] == PartyGlobals.PartyStatus.Pending:
                                yield party
                        else:
                            if party['statusId'] == PartyGlobals.PartyStatus.Cancelled:
                                yield party
                else:
                    if party['startTime'] < thresholdTime:
                        if not cancelled:
                            if party['statusId'] == PartyGlobals.PartyStatus.Finished:
                                yield party
                        else:
                            if party['statusId'] == PartyGlobals.PartyStatus.Cancelled:
                                yield party


    def getParty(self, partyId):
        """
        Get a party by partyId.
        """
        self.load()
        return self.partyToId.get(partyId, None)
    
    def changePrivate(self, partyId, newPrivateStatus):
        """
        Change a party to public or private.
        """
        self.load()
        if partyId in self.partyToId.values():
            self.partyToId[partyId]['isPrivate'] = newPrivateStatus
            self.save()
            return True
        return False

    def deleteParty(self, partyId):
        """
        Delete a party.
        """
        self.load()
        if partyId in self.partyToId.values():
            del self.partyToId[partyId]
            self.save()
            return True
        return False
    
    def changePartyStatus(self, partyId, newPartyStatus):
        """
        Change the status of a party.
        """
        self.load()
        if partyId in self.partyToId.values():
            self.partyToId[partyId]['statusId'] = newPartyStatus
            self.save()
            return True
        return False
    
    def forceFinishForStarted(self, thresholdTime):
        """
        Force finish all started parties.
        """
        self.load()
        for party in self.partyToId.values():
            if party['endTime'] < thresholdTime and party['statusId'] == PartyGlobals.PartyStatus.Started:
                party['statusId'] = PartyGlobals.PartyStatus.Finished
        self.save()

    def forceNeverStartedForCanStart(self, thresholdTime):
        """
        Force never started all parties that can start.
        """
        self.load()
        for party in self.partyToId.values():
            if party['endTime'] < thresholdTime and party['statusId'] == PartyGlobals.PartyStatus.Pending:
                party['statusId'] = PartyGlobals.PartyStatus.NeverStarted
        self.save()

    def getMultipleParties(self, partyIds):
        """
        Get multiple parties by partyId.
        """
        self.load()
        for partyId in partyIds:
            yield self.partyToId.get(partyId, None)
            
    def changeMultiplePartiesStatus(self, partyIds, newPartyStatus):
        """
        Change the status of multiple parties.
        """
        self.load()
        for partyId in partyIds:
            if partyId in self.partyToId.values():
                self.partyToId[partyId]['statusId'] = newPartyStatus
        self.save()

class InviteDB():
    """
    InviteDB is the base class for all invite database interface implementations.
    """
    def __init__(self, partyManager):
        self.partyMsanager = partyManager
        self.inviteDbFilePath = config.GetString('invitedb-local-file', 'astron/databases/invites.json')
        # Load the JSON file if it exists.
        if os.path.exists(self.inviteDbFilePath):
            with open(self.inviteDbFilePath, 'r') as file:
                self.inviteToId = json.load(file)
        else:
            # If not, create a blank file.
            self.inviteToId = {}
            with open(self.inviteDbFilePath, 'w') as file:
                json.dump(self.inviteToId, file)

    def save(self):
        """Save the current state of the inviteToId dictionary to the JSON file."""
        with open(self.inviteDbFilePath, 'w') as file:
            json.dump(self.inviteToId, file)
                      
    def putInvite(self, partyId, inviteeId):
        """
        Add an invite to the database.
        """
        inviteKey = len(self.inviteToId) + 1
        invite = {
            'inviteKey': inviteKey,
            'partyId': partyId,
            'inviteeId': inviteeId,
            'statusId': PartyGlobals.InviteStatus.NotRead
        }
        self.inviteToId[inviteKey] = invite
        self.save()

    def getInvites(self, avatarId):
        """
        Get all invites for an avatar.
        """
        for invite in self.inviteToId:
            if invite['inviteeId'] == avatarId:
                yield invite

    def getOneInvite(self, inviteKey):
        """
        Get one invite by inviteKey.
        """
        return self.inviteToId.get(inviteKey, None)

    def updateInvite(self, inviteKey, newStatus):
        """
        Update the status of an invite.
        """
        if inviteKey in self.inviteToId:
            self.inviteToId[inviteKey]['statusId'] = newStatus
            self.save()
            return True
        return False

    def getReplies(self, partyId):
        """
        Get all replies for a party.
        """
        for invite in self.inviteToId:
            if invite['partyId'] == partyId:
                yield invite

    def deleteInvite(self, inviteKey):
        """
        Delete an invite.
        """
        if inviteKey in self.inviteToId:
            del self.inviteToId[inviteKey]
            self.save()
            return True
        return False

    def getInviteesOfParty(self, partyId):
        """
        Get all invitees of a party.
        """
        for invite in self.inviteToId:
            if invite['partyId'] == partyId:
                yield invite

class DistributedPartyManagerUD(DistributedObjectGlobalUD):
    """UD side class for the party manager."""

    # WARNING this is a global OTP object
    # DistributedPartyManagerAI is NOT!
    # Hence the use of sendUpdateToDoId when sending back to AI

    notify = DirectNotifyGlobal.directNotify.newCategory("DistributedPartyManagerUD")

    def __init__(self, air):
        DistributedObjectGlobalUD.__init__(self, air)
        # self.printlog = partiesUdLog("PartiesUdMonitor","localhost",12346)

        # avId is key, if present, avatar is online
        self.isAvatarOnline = {}

        self.hostAvIdToAllPartiesInfo = {}
        #                 0       1         2        3
        # hostAvId to ( shardId, zoneId, isPrivate, number of toons there,
        #                 4         5              6             7
        #               hostName,activityIds, actualStartTime, partyId)

        # The uberdog has the database, and knows when every party in every shard
        # is allowed to start, or rather, when the 'go' button is activated. So,
        # every 15 minutes (parties can only start on increments of 15 minutes)
        # we'll check and see what parties are allowed to start and make the calls
        # to enable their go buttons.  We'll do the 1st check a minute in...
        taskMgr.doMethodLater(60, self._checkForPartiesStarting, "DistributedPartyManagerUD_checkForPartiesStarting" )



        self.partyDb = PartyDb(self)
                                

        self.inviteDb = InviteDB(self)

        # in minutes, how often do we check if a party can start
        self.startPartyFrequency = config.GetFloat('start-party-frequency', PartyGlobals.UberdogCheckPartyStartFrequency)

        # The uberdog has the database, we need to check if party has been started but never finished
        # We'll do the 1st check a 1 second in...
        self.partiesSanityCheckFrequency = config.GetInt('parties-sanity-check-frequency',
                                                              PartyGlobals.UberdogPartiesSanityCheckFrequency)
        taskMgr.doMethodLater(1, self._sanityCheckParties, "DistributedPartyManagerUD_sanityCheckParties")

    def announceGenerate(self):
        DistributedObjectGlobalUD.announceGenerate(self)
        self.accept("avatarOnlinePlusAccountInfo", self.avatarOnlinePlusAccountInfo, [])
        self.accept("avatarOffline", self.avatarOffline, [])
        # assuming we are restarting, tell all the AIs so they can reply back with their
        # currently running parties
        self.sendUpdateToAllAis("partyManagerUdStartingUp", [])


    def avatarLoggedIn(self, avatarId):
        """Handle an avatar just logging in."""
        # Note this is no longer sent by the AI but is instead in response to
        # avatarOnlinePlusAccountInfo from otp_server
        # for now we get all the invites, then send them across the wire to the client.
        DistributedPartyManagerUD.notify.debug( "avatarLoggedIn( avaterId=%d )" % avatarId )
        # we are blasting everything for now
        partyIds, partyInfo = self._updateInvites( avatarId )

        # we've sent invites, send party details related to those invites
        self._updateInvitedToParties( avatarId, partyIds, partyInfo )

        # send out the details of the parties he's hosting
        hostedPartyIds, hostedPartyInfo = self._updateHostedParties( avatarId )

        # send out replies to his parties
        self._updatePartyReplies(avatarId, hostedPartyIds, hostedPartyInfo)

    def addParty(self, pmDoId, hostId, startTime, endTime, isPrivate, inviteTheme, activities, decorations, inviteeIds, costOfParty):
        """Add a party to the the invite and party dbs."""
        DistributedPartyManagerUD.notify.info( "addParty( hostId=%d, startTime=%s, endTime=%s, isPrivate=%s, inviteTheme=%s, invitees=%s... )" %(hostId, startTime, endTime, isPrivate, PartyGlobals.InviteTheme(inviteTheme)._name_ ,str(inviteeIds))  ) 
        putSucceeded = self.partyDb.putParty(hostId, startTime, endTime, isPrivate, inviteTheme, activities, decorations, PartyGlobals.PartyStatus.Pending)
        if not putSucceeded:
            DistributedPartyManagerUD.notify.warning( "putParty call for party with hostID %s failed." % hostId )
            # TODO having too many parties is not the only reason putParty can fail
            # add those cases too
            # case 1: too many decors
            self.sendAddPartyResponse(pmDoId, hostId, PartyGlobals.AddPartyErrorCode.TooManyHostedParties)
            return

        errorCode = PartyGlobals.AddPartyErrorCode.AllOk
        partiesTuple = tuple(self.partyDb.getPartiesOfHost(hostId))
        if len(partiesTuple) > 0:
            partyId = partiesTuple[-1]['partyId'] # TODO-parties: is getting the -1 index guranteed to get the party we just pushed to the database?
            # send out the details of the parties he's hosting
            hostedPartyIds, hostedPartyInfo = self._updateHostedParties(hostId)

            # Send out updates to invitees
            for inviteeId in inviteeIds:
                self.inviteDb.putInvite(partyId, inviteeId)
                if self.isOnline(inviteeId):
                    # update invitee's invites
                    partyIds, partyInfo = self._updateInvites( inviteeId )
                    # update invitee's InvitedTo parties
                    self._updateInvitedToParties( inviteeId, partyIds, partyInfo )

            # send out replies to his parties
            self._updatePartyReplies(hostId, [partyId], hostedPartyInfo)
        else:
            DistributedPartyManagerUD.notify.warning( "Unable to find a party for hostId %s in the party database." % hostId )
            errorCode = PartyGlobals.AddPartyErrorCode.DatabaseError
        self.sendAddPartyResponse(pmDoId, hostId, errorCode, costOfParty)

    def markInviteAsReadButNotReplied( self, partyManagerDoId, inviteKey):
        """Just mark the invite as read in the database."""
        invite = self.inviteDb.getOneInvite(inviteKey)
        if not invite:
            # how the heck did this happen, inviteKey isn't there
            DistributedPartyManagerUD.notify.warning('markInviteAsReadButNotReplied inviteKey=%s not found in inviteDb' % inviteKey)
            return

        # verify the party is still there
        partyId = invite[0]['partyId']
        party = self.partyDb.getParty(partyId)
        if not party:
            return

        updateResult = self.inviteDb.updateInvite(inviteKey, PartyGlobals.InviteStatus.ReadButNotReplied)
        self.updateHostAndInviteeStatus(inviteKey, partyId, invite, party, PartyGlobals.InviteStatus.ReadButNotReplied )

    def updateHostAndInviteeStatus(self, inviteKey, partyId, invite, party, newStatus):
        """Tell the invitee and host toons of the change in inviteStatus."""
        # tell the Invitee DistributedToon
        inviteeId = invite[0]['guestId']

        DistributedPartyManagerUD.notify.debug( "Calling DistributedToon::updateInvite( inviteKey=%s, newStatus=%s ) across the network with inviteeId %d." %(inviteKey, PartyGlobals.InviteStatus(newStatus).name, inviteeId ) )
        self.air.sendUpdateToDoId(
            "DistributedToon",
            "updateInvite",
            inviteeId,
            [inviteKey, newStatus],
        )

        # tell the host, he might not be logged in
        hostId = party[0]['hostId']

        DistributedPartyManagerUD.notify.debug( "Calling DistributedToon::updateReply( partyId=%d, inviteeId=%d, newStatus=%s ) across the network with hostId %d." %(partyId, inviteeId, PartyGlobals.InviteStatus(newStatus).name, hostId ) )
        self.air.sendUpdateToDoId(
            "DistributedToon",
            "updateReply",
            hostId,
            [partyId, inviteeId, newStatus],
        )

    def respondToInvite(self, partyManagerDoId, mailboxDoId, context, inviteKey, newStatus):
        """Handle accepting/rejecting an invite."""
        DistributedPartyManagerUD.notify.debug( "respondToInvite( partyManagerDoId=%d, mailboxDoId=%d, ..., inviteKey=%d, newStatus=%s )" %(partyManagerDoId, mailboxDoId, inviteKey, PartyGlobals.InviteStatus(newStatus).name ) )
        replyToChannelAI = self.air.getSenderReturnChannel()
        retcode = ToontownGlobals.P_InvalidIndex
        invite = self.inviteDb.getOneInvite(inviteKey)
        if not invite:
            # how the heck did this happen, inviteKey isn't there
            DistributedPartyManagerUD.notify.warning('inviteKey=%s not found in inviteDb' % inviteKey)
            self.air.sendUpdateToDoId(
                "DistributedPartyManager",
                "respondToInviteResponse",
                partyManagerDoId,
                [mailboxDoId, context, inviteKey, retcode, newStatus],
            )
            return

        # verify the party is still there
        partyId = invite[0]['partyId']
        party = self.partyDb.getParty(partyId)
        if not party:
            self.air.sendUpdateToDoId(
                "DistributedPartyManager",
                "respondToInviteResponse",
                partyManagerDoId,
                [mailboxDoId, context, inviteKey, ToontownGlobals.P_PartyNotFound, newStatus],
            )
            return

        # we have a valid party and invite, update the status
        # TODO updateResult is always empty, do we need to verify the update took?
        updateResult = self.inviteDb.updateInvite(inviteKey, newStatus)

        self.air.sendUpdateToDoId(
            "DistributedPartyManager",
            "respondToInviteResponse",
            partyManagerDoId,
            [mailboxDoId, context, inviteKey, ToontownGlobals.P_ItemAvailable, newStatus]
        )

        # tell the invitee and host he accepted/rejected
        self.updateHostAndInviteeStatus(inviteKey, partyId, invite, party, newStatus)

    def sendAddPartyResponse(self, pmDoId, hostId, errorCode, costOfParty=0):
        """Tell the AI if all went well or if there's a problem adding the party."""
        self.air.sendUpdateToDoId(
            "DistributedPartyManager",
            'addPartyResponseUdToAi',
            pmDoId,
            [hostId, errorCode, costOfParty],
        )

    def _updateInvites(self, avatarId):
        """
        Push invites and setInviteMailNotify across to the DistributedToon.

        Returns a list of prioritized partyIds and the partyInfo that avatarId is invited to.
        """
        DistributedPartyManagerUD.notify.debug( "_updateInvites( avatarId=%d )" % avatarId )

        invitesTuple = self.inviteDb.getInvites(avatarId)
        DistributedPartyManagerUD.notify.debug( "Found %d invites for avatarId %d in the invite database." % (len(invitesTuple), avatarId) )

        # with 8 bytes inviteKey, 8 bytes partyId, 1 byte status = 17 bytes for the 1 invite
        # 64kb / 17 = 3855
        # the party info related to these invites is the limiting factor
        # However cancelled parties will show up in this list
        # if we really want to be 100% sure we can pull the parties from the database
        # and examine them one by one.

        # But an extremely large number should cover it, say 1000
        invitesTuple = invitesTuple[-PartyGlobals.MaxSetInvites:]

        # ok we really need to examine the parties
        # since we need to figure out the correct value for inviteMailNotify
        # we can have an invite that's not read, so it will trigger as a new invite in the
        # mailbox, but since it's so far in the future the partyInvitedTo is not sent
        # we get the case of a mailbox being flagged but having nothing in it!
        partyIds = [inviteInfo['partyId'] for inviteInfo in invitesTuple]

        prioritizedPartyIds, prioritizedPartyInfo = self.reprioritizeParties(partyIds, PartyGlobals.MaxSetPartiesInvitedTo)

        formattedInvites = []
        partyIds = []
        numOld = 0
        numNew = 0
        for item in invitesTuple:
            partyId = item['partyId']
            if partyId not in prioritizedPartyIds:
                # skip this invite, too far in the past or in the future
                continue
            inviteKey = item['inviteId']
            status = item['statusId']
            if status == PartyGlobals.InviteStatus.NotRead:
                numNew += 1
            elif status == PartyGlobals.InviteStatus.ReadButNotReplied:
                numOld += 1
            # send even the rejected invites, it will show up in invites tab
            formattedInvites.append( (inviteKey, partyId, status) )
            partyIds.append(partyId)

        DistributedPartyManagerUD.notify.debug( "Calling DistributedToon::setInvites across the network with avatarId %d. Sending %d formatted invites." %(avatarId, len(formattedInvites) ) )
        self.air.sendUpdateToDoId(
            "DistributedToon",
            "setInvites",
            avatarId,
            [formattedInvites],
        )

        # we let DistributedToon.updateInviteMailNotify() properly
        # set the right value for inviteMailNotify now instead of uberdog doing it here

        return prioritizedPartyIds, prioritizedPartyInfo

    def reprioritizeParties(self, partyIds, limit):
        """Return a prioritized list of partyIds and the associated partyInfo."""
        thresholdTime = self.getThresholdTime()
        futurePendingParties = ()
        futureCancelledParties = ()
        pastFinishedParties =()
        pastCancelledParties = ()
        prioritizedPartyIds = []
        prioritizedPartyInfo = ()

        futurePendingParties = tuple(self.partyDb.getPrioritizedParties(\
            partyIds,
            thresholdTime.strftime("%Y-%m-%d %H:%M:%S"),
            limit,
            future = True,
            cancelled = False))
        self.notify.debug('futurePendingParties = %s' % str(futurePendingParties))
        prioritizedPartyIds += [partyInfo['partyId'] for partyInfo in futurePendingParties]
        prioritizedPartyInfo += futurePendingParties
        slotsLeft = limit - len(futurePendingParties)

        if slotsLeft > 0:
            futureCancelledParties = tuple(self.partyDb.getPrioritizedParties(\
                partyIds,
                thresholdTime.strftime("%Y-%m-%d %H:%M:%S"),
                slotsLeft,
                future = True,
                cancelled = True))
            #self.notify.debug('futureCancelledParties = %s' % str(futureCancelledParties))
            prioritizedPartyIds += [partyInfo['partyId'] for partyInfo in futureCancelledParties]
            prioritizedPartyInfo += futureCancelledParties
        slotsLeft -= len(futureCancelledParties)
        if slotsLeft > 0:
            pastFinishedParties = tuple(self.partyDb.getPrioritizedParties(\
                partyIds,
                thresholdTime.strftime("%Y-%m-%d %H:%M:%S"),
                slotsLeft,
                future = False,
                cancelled = False))
            #self.notify.debug('pastFinishedParties = %s' % str(pastFinishedParties))
            prioritizedPartyIds += [partyInfo['partyId'] for partyInfo in pastFinishedParties]
            prioritizedPartyInfo += pastFinishedParties
        slotsLeft -= len(pastFinishedParties)
        if slotsLeft > 0:
            pastCancelledParties = tuple(self.partyDb.getPrioritizedParties(\
                partyIds,
                thresholdTime.strftime("%Y-%m-%d %H:%M:%S"),
                slotsLeft,
                future = False,
                cancelled = True))
            #self.notify.debug('pastCancelledParties = %s' % str(pastCancelledParties))
            prioritizedPartyIds += [partyInfo['partyId'] for partyInfo in pastCancelledParties]
            prioritizedPartyInfo += pastCancelledParties

        # prioritizedPartyIds should have everything, prioritizing pending parties in the future
        # then cancelled parties in the future, then started parties in the past
        # then cancelled parties in the past

        return prioritizedPartyIds, prioritizedPartyInfo

    def _updateInvitedToParties(self, avatarId, passedPartyIds, passedPartyInfo):
        """
        Push information about parties that avatarId is invited to across to the DistributedToon.

        partyIds: list of partyIds that avatarId is invited to
        """
        partyIds = passedPartyIds
        partyInfo = passedPartyInfo
        DistributedPartyManagerUD.notify.debug( "_updateInvitedToParties( avatarId=%d, partyIds=%s )" %(avatarId, partyIds) )
        if partyInfo == None:
            partyIds, partyInfo = self.reprioritizeParties(passedPartyIds, PartyGlobals.MaxSetPartiesInvitedTo)

        formattedPartiesInvitedTo = []
        formattedPartiesSize = 0
        for partyInfoDict in partyInfo:
            formattedPartyInfo = self.getFormattedPartyInfo(partyInfoDict)
            partyInfoSize = self._getPartyInfoSize(formattedPartyInfo)
            formattedPartiesSize += partyInfoSize
            # A full party info can be as big as 383 bytes, and we can only send 16KB over the wire.
            # So we clip off any party after 15.8 KB (we leave some leeway for any extra info)
            if (formattedPartiesSize < 15800):
                formattedPartiesInvitedTo.append(formattedPartyInfo)
            else:
                break

        DistributedPartyManagerUD.notify.debug( "Calling DistributedToon::setPartiesInvitedTo across the network with avatarId %d. Sending %d formatted parties." %(avatarId, len(formattedPartiesInvitedTo) ) )
        self.air.sendUpdateToDoId(
            "DistributedToon",
            "setPartiesInvitedTo",
            avatarId,
            [formattedPartiesInvitedTo],
        )

    def getThresholdTime(self):
        """Return the server threshold time for high priority parties."""
        # Some parties could have started recently.
        # threshold time, let's get the current server time, subtract default party time
        # and then subtract it again to get the threshold
        thresholdTime = self.air.toontownTimeManager.getCurServerDateTime()
        thresholdTime += timedelta(hours = -(2*PartyGlobals.DefaultPartyDuration ))

        return thresholdTime

    def getFormattedPartyInfo(self, partyInfoDict):
        """
        Formats the party information from the given dictionary into a tuple.
        Args:
            partyInfoDict (dict): A dictionary containing party information with the following keys:
                - 'partyId' (int): The ID of the party.
                - 'hostId' (int): The ID of the host.
                - 'startTime' (str): The start time of the party.
                - 'endTime' (str): The end time of the party.
                - 'activities' (tuple): The activities of the party.
                - 'decorations' (tuple): The decorations of the party.
                - 'isPrivate' (bool): A boolean indicating if the party is private.
                - 'inviteTheme' (int): The theme of the invitation.
                - 'statusId' (int): The status ID of the party.
        Returns:
            tuple: A tuple containing the formatted party information in the following order:
                - partyId (int)
                - hostId (int)
                - startTime year (int)
                - startTime month (int)
                - startTime day (int)
                - startTime hour (int)
                - startTime minute (int)
                - endTime year (int)
                - endTime month (int)
                - endTime day (int)
                - endTime hour (int)
                - endTime minute (int)
                - isPrivate (bool)
                - inviteTheme (int)
                - formattedActivities (list of tuples): Each tuple contains 4 integers representing an activity.
                - formattedDecors (list of tuples): Each tuple contains 4 integers representing a decoration.
                - statusId (int)
        """
        startTime = partyInfoDict['startTime']
        endTime = partyInfoDict['endTime']
        # convert the date strings to datetime 
        startTime = datetime.strptime(startTime, "%Y-%m-%d %H:%M:%S")
        endTime = datetime.strptime(endTime, "%Y-%m-%d %H:%M:%S")
        activities = partyInfoDict['activities']
        formattedActivities = [tuple(activity) for activity in activities]
        
        # for i in range (int(len(activitiesStr) / 4)):
        #     oneActivity = (ord(activitiesStr[i*4]),
        #                    ord(activitiesStr[i*4 + 1]),
        #                    ord(activitiesStr[i*4 + 2]),
        #                    ord(activitiesStr[i*4 + 3])
        #                    )
        #     formattedActivities.append(oneActivity)
        # decorStr = partyInfoDict['decorations']
        # formattedDecors = []
        # for i in range(int(len(decorStr) / 4)):
        #     oneDecor = (ord(decorStr[i*4]),
        #                 ord(decorStr[i*4 + 1]),
        #                 ord(decorStr[i*4 + 2]),
        #                 ord(decorStr[i*4 + 3])
        #                 )
        #     formattedDecors.append(oneDecor)
        decorations = partyInfoDict['decorations']
        formattedDecors = [tuple(decor) for decor in decorations]
        isPrivate = partyInfoDict['isPrivate']
        inviteTheme = partyInfoDict['inviteTheme']

        return(
            partyInfoDict['partyId'],
            partyInfoDict['hostId'],
            startTime.year,
            startTime.month,
            startTime.day,
            startTime.hour,
            startTime.minute,
            endTime.year,
            endTime.month,
            endTime.day,
            endTime.hour,
            endTime.minute,
            isPrivate,
            inviteTheme,
            formattedActivities,
            formattedDecors,
            partyInfoDict['statusId']
        )

    def reprioritizeHostedParties(self, hostId, limit):
        """Return a prioritized list of partyIds and the associated partyInfo."""
        thresholdTime = self.getThresholdTime()
        futurePendingParties = ()
        futureCancelledParties = ()
        pastFinishedParties =()
        pastCancelledParties = ()
        prioritizedPartyIds = []
        prioritizedPartyInfo = ()

        futurePendingParties = tuple(self.partyDb.getHostPrioritizedParties(\
            hostId,
            thresholdTime.strftime("%Y-%m-%d %H:%M:%S"),
            limit,
            future = True,
            cancelled = False))
        self.notify.debug('futurePendingParties = %s' % str(futurePendingParties))
        prioritizedPartyIds += [partyInfo['partyId'] for partyInfo in futurePendingParties]
        prioritizedPartyInfo += futurePendingParties
        slotsLeft = limit - len(futurePendingParties)

        if slotsLeft > 0:
            futureCancelledParties = tuple(self.partyDb.getHostPrioritizedParties(\
                hostId,
                thresholdTime.strftime("%Y-%m-%d %H:%M:%S"),
                slotsLeft,
                future = True,
                cancelled = True))
            self.notify.debug('futureCancelledParties = %s' % str(futureCancelledParties))
            prioritizedPartyIds += [partyInfo['partyId'] for partyInfo in futureCancelledParties]
            prioritizedPartyInfo += futureCancelledParties
        slotsLeft -= len(futureCancelledParties)
        if slotsLeft > 0:
            pastFinishedParties = tuple(self.partyDb.getHostPrioritizedParties(\
                hostId,
                thresholdTime.strftime("%Y-%m-%d %H:%M:%S"),
                slotsLeft,
                future = False,
                cancelled = False))
            self.notify.debug('pastFinishedParties = %s' % str(pastFinishedParties))
            prioritizedPartyIds += [partyInfo['partyId'] for partyInfo in pastFinishedParties]
            prioritizedPartyInfo += pastFinishedParties
        slotsLeft -= len(pastFinishedParties)
        if slotsLeft > 0:
            pastCancelledParties = tuple(self.partyDb.getHostPrioritizedParties(\
                hostId,
                thresholdTime.strftime("%Y-%m-%d %H:%M:%S"),
                slotsLeft,
                future = False,
                cancelled = True))
            self.notify.debug('pastCancelledParties = %s' % str(pastCancelledParties))
            prioritizedPartyIds += [partyInfo['partyId'] for partyInfo in pastCancelledParties]
            prioritizedPartyInfo += pastCancelledParties

        # prioritizedPartyIds should have everything, prioritizing pending parties in the future
        # then cancelled parties in the future, then started parties in the past
        # then cancelled parties in the past

        return prioritizedPartyIds, prioritizedPartyInfo


    def _updateHostedParties(self, avatarId):
        """
        Push information about parties that avatarId is hosting across to the DistributedToon.

        Returns a list of hostedPartyIds
        """
        DistributedPartyManagerUD.notify.debug( "_updateHostedParties( avatarId=%d )" % avatarId )
        hostedPartyIds, hostedParties = self.reprioritizeHostedParties(avatarId, PartyGlobals.MaxSetHostedParties)

        formattedHostedParties = []
        formattedPartiesSize = 0
        for partyInfoDict in hostedParties:
            if partyInfoDict['startTime'] and partyInfoDict['endTime']:

                formattedPartyInfo = self.getFormattedPartyInfo(partyInfoDict)
                partyInfoSize = self._getPartyInfoSize(formattedPartyInfo)
                formattedPartiesSize += partyInfoSize
                # A full party info can be as big as 383 bytes, and we can only send 16KB over the wire.
                # So we clip off any party after 15.8 KB (we leave some leeway for any extra info)
                if (formattedPartiesSize < 15800):
                    formattedHostedParties.append(formattedPartyInfo)
                else:
                    break
            else:
                self.notify.warning("partyId=%s has an invalid start or end time startTime=%s endTime=%s" % \
                                    ( str(partyInfoDict["partyId"]),
                                      str(partyInfoDict['startTime']),
                                      str(partyInfoDict['endTime'])
                                      ))

        DistributedPartyManagerUD.notify.debug( "Calling DistributedToon::setHostedParties across the network with avatarId %d. Sending %d formatted parties." %(avatarId, len(formattedHostedParties) ) )
        self.air.sendUpdateToDoId(
            "DistributedToon",
            "setHostedParties",
            avatarId,
            [formattedHostedParties],
        )

        return hostedPartyIds, hostedParties

    def _updatePartyReplies(self, avatarId, hostedPartyIds, hostedParties):
        """
        Look up replies to all parties avatarId is hosting from the database
        and push them across to DistributedToon.
        """
        DistributedPartyManagerUD.notify.debug( "_updatePartyReplies( avatarId=%d, hostedPartyIds=%s )" %(avatarId, hostedPartyIds) )
        thresholdTime = self.getThresholdTime()
        formattedRepliesForAllParties = []
        for index, partyId in enumerate( hostedPartyIds):
            if index >= len(hostedParties):
                self.notify.warning(f'skipping len(hostedPartyIds)={len(hostedPartyIds)} != len(hostedParties)={len(hostedParties)}')
                continue
            gotCorrectPartyInfo = True
            partyInfoDict = hostedParties[index]
            if partyInfoDict['partyId'] != partyId:
                gotCorrectPartyInfo = False
                for hostedInfo in hostedParties:
                    if hostedInfo['partyId'] == partyId:
                        gotCorrectPartyInfo = True
                        partyInfoDict = hostedInfo
                        break

            if not gotCorrectPartyInfo:
                self.notify.warning('partyId =%d not in hostedPartyIds' % partyId)
                continue

            getRepliesForThisParty = True
            # we only need replies for parties in the future that are not cancelled
            # temporarily turned off as shticker book is not happy
            #if partyInfoDict['statusId'] != PartyGlobals.PartyStatus.Cancelled and \
            #   thresholdTime < partyInfoDict['startTime']:
            #   getRepliesForThisParty = True

            if getRepliesForThisParty:
                formattedReplies = []
                replies = self.inviteDb.getReplies(partyId)
                for oneReply in replies:
                    formattedReplies.append((
                        oneReply['guestId'],
                        oneReply['statusId']
                        ))
                formattedRepliesForAllParties.append( (partyId, formattedReplies) )
        DistributedPartyManagerUD.notify.debug( "Calling DistributedToon::setPartyReplies across the network with avatarId %d. Sending %d formatted replies." %(avatarId, len(formattedRepliesForAllParties) ) )
        self.air.sendUpdateToDoId(
            "DistributedToon",
            "setPartyReplies",
            avatarId,
            [formattedRepliesForAllParties],
        )

    def changePrivateRequestAiToUd(self, pmDoId, partyId, newPrivateStatus):
        """Handle AI requesting to change a party to public or private."""
        errorCode = PartyGlobals.ChangePartyFieldErrorCode.AllOk

        # verify the party is still there
        party = self.partyDb.getParty(partyId)
        if not party:
            errorCode = PartyGlobals.ChangePartyFieldErrorCode.DatabaseError
            self.air.sendUpdateToDoId(
                "DistributedPartyManager",
                'changePrivateResponseUdToAi',
                pmDoId,
                [0, partyId, newPrivateStatus, errorCode ],
            )
            return

        if party[0]['statusId'] == PartyGlobals.PartyStatus.Started:
            errorCode = PartyGlobals.ChangePartyFieldErrorCode.AlreadyStarted
            self.air.sendUpdateToDoId(
                "DistributedPartyManager",
                'changePrivateResponseUdToAi',
                pmDoId,
                [party[0]['hostId'], partyId, newPrivateStatus, errorCode ],
            )
            return


        # TODO updateResult is always empty, do we need to verify the update took?
        updateResult = self.partyDb.changePrivate(partyId, newPrivateStatus)

        self.air.sendUpdateToDoId(
            "DistributedPartyManager",
            'changePrivateResponseUdToAi',
            pmDoId,
            [ party[0]['hostId'], partyId, newPrivateStatus, errorCode ],
        )

        # TODO do we need to send out partiesInvitedTo again?

    def changePartyStatusRequestAiToUd(self, pmDoId, partyId, newPartyStatus):
        """Handle AI requesting to change the party status."""
        DistributedPartyManagerUD.notify.debug("changePartyStatusRequestAiToUd partyId = %s, newPartyStatus = %s" % (partyId, newPartyStatus))
        errorCode = PartyGlobals.ChangePartyFieldErrorCode.AllOk

        # verify the party is still there
        party = self.partyDb.getParty(partyId)
        if not party:
            errorCode = PartyGlobals.ChangePartyFieldErrorCode.DatabaseError
            self.air.sendUpdateToDoId(
                "DistributedPartyManager",
                'changePartyStatusResponseUdToAi',
                pmDoId,
                [0, partyId, newPartyStatus, errorCode ],
            )

            return errorCode
        partyDict = party[0]
        # Check to see if this is a party that has finished
        if partyDict["statusId"] == PartyGlobals.PartyStatus.Started.value and newPartyStatus == PartyGlobals.PartyStatus.Finished.value:
            # It's over, send word to all the AIs so they can update for their public party gates
            if partyDict["hostId"] in self.hostAvIdToAllPartiesInfo:
                self.sendUpdateToAllAis("partyHasFinishedUdToAllAi", [partyDict["hostId"]])
                del self.hostAvIdToAllPartiesInfo[partyDict["hostId"]]

        # TODO updateResult is always empty, do we need to verify the update took?
        updateResult = self.partyDb.changePartyStatus(partyId, newPartyStatus)
        self.air.sendUpdateToDoId(
            "DistributedPartyManager",
            'changePartyStatusResponseUdToAi',
            pmDoId,
            [ partyDict['hostId'], partyId, newPartyStatus, errorCode ],
        )

        return errorCode
        # TODO do we need to send out partiesInvitedTo again?

    def partyInfoOfHostRequestAiToUd(self, pmDoId, hostId):
        """
        A host is trying to create a party, check to see if this host has a
        party available and, if so, return the party info and inviteeIds
        """
        DistributedPartyManagerUD.notify.debug( "partyInfoOfHostRequestAiToUd( pmDoId=%d, hostId=%d )" %(pmDoId, hostId) )

        # Query the database, get the info!
        hostedParties = tuple(self.partyDb.getPartiesOfHostThatCanStart(hostId))

        partyFail = False
        partyInfo = None
        if len(hostedParties) == 0:
            DistributedPartyManagerUD.notify.info( "partyInfoOfHostRequestAiToUd : party failed because avatar is not hosting any parties." )
            partyFail = True
        else:
            curServerDateTime = self.air.toontownTimeManager.getCurServerDateTime()
            partyInfoDict = hostedParties[0]
            # Check to see if this party's startTime is before the current time
            # Note: Must make partyInfoDict["startTime"]'s time aware of any
            #       time offsets by creating a new datetime based on it but
            #       using the ToontownTimeManager's serverTimeZone info
            partyStartTime = partyInfoDict["startTime"]
            # convert string of datetime to datetime
            partyStartTime = datetime.strptime(partyStartTime, "%Y-%m-%d %H:%M:%S")
            partyStartTime = datetime(
                partyStartTime.year,
                partyStartTime.month,
                partyStartTime.day,
                partyStartTime.hour,
                partyStartTime.minute,
                tzinfo=self.air.toontownTimeManager.serverTimeZone,
            )
            curServerDateTime = datetime(
                curServerDateTime.year,
                curServerDateTime.month,
                curServerDateTime.day,
                curServerDateTime.hour,
                curServerDateTime.minute,
                tzinfo=self.air.toontownTimeManager.serverTimeZone,
            )
            if partyStartTime <= curServerDateTime:
                pass
            else:
                DistributedPartyManagerUD.notify.debug("partyInfoOfHostRequestAiToUd : party failed because avatar's party's start time has not passed yet.")
                DistributedPartyManagerUD.notify.debug(" startTime = %s, servertime = %s" % (partyStartTime, curServerDateTime))
                partyFail = True

            partyEndTime = partyInfoDict["endTime"]
            # convert string of datetime to datetime
            partyEndTime = datetime.strptime(partyEndTime, "%Y-%m-%d %H:%M:%S")
            partyEndTime = datetime(
                partyEndTime.year,
                partyEndTime.month,
                partyEndTime.day,
                partyEndTime.hour,
                partyEndTime.minute,
                tzinfo=self.air.toontownTimeManager.serverTimeZone,
            )
            if partyEndTime < curServerDateTime:
                DistributedPartyManagerUD.notify.debug("partyInfoOfHostRequestAiToUd : party failed because avatar's party's end time has already passed.")
                DistributedPartyManagerUD.notify.debug(" endTime = %s, servertime = %s" % (partyEndTime, curServerDateTime))
                partyFail = True

        if partyFail:
            # Something is fishy... this host is not allowed to start this party now or has no parties planned
            randomPartyCreationAllowed = uber.config.GetBool('allow-random-party-creation', 0)
            if not randomPartyCreationAllowed:
                self.air.sendUpdateToDoId(
                    "DistributedPartyManager",
                    'partyInfoOfHostFailedResponseUdToAi',
                    pmDoId,
                    [hostId],
                )
                return
            else:
                # We're allowed to create random parties for testing purposes
                # We'll base the partyId on the current time...
                curServerDateTime = self.air.toontownTimeManager.getCurServerDateTime()
                partyDuration = timedelta(hours=PartyGlobals.DefaultPartyDuration)
                endTime = curServerDateTime + partyDuration
                partyId = int(time.time())
                partyId = int(str(partyId)[1:])
                DistributedPartyManagerUD.notify.debug( "partyInfoOfHostRequestAiToUd : Creating random test party with partyId %d" % partyId)
                activities = []
                # Let's make one of each activity, arranged in a circle/oval in the party grounds
                numActivities = len(PartyGlobals.ActivityIds)
                circleStep = (2*math.pi)/numActivities
                xRadius = 60.0
                yRadius = 80.0
                for i in range(numActivities):
                    # these are unsigned 8 bit ints (0-255)
                    activities += "%s%s%s%s"%(
                        chr(i),
                        chr(PartyUtils.convertDistanceToPartyGrid(math.cos(i*circleStep)*xRadius, 0)),
                        chr(PartyUtils.convertDistanceToPartyGrid(math.sin(i*circleStep)*yRadius, 1)),
                        chr(PartyUtils.convertDegreesToPartyGrid((i*circleStep*180)/math.pi + 270.0))
                    )
                partyInfoDict = {
                    "partyId" : partyId,
                    "hostId" : hostId,
                    "startTime" : curServerDateTime,#.strftime("%Y-%m-%d %H:%M:%S"),
                    "endTime" : endTime,#.strftime("%Y-%m-%d %H:%M:%S"),
                    "isPrivate" : False,
                    "inviteTheme" : 0,
                    "activities" : activities,
                    "decorations" : [],
                    "statusId" : 0,
                }

        # Form the list of inviteeIds
        inviteeIds = []
        inviteeDict = self.inviteDb.getInviteesOfParty(partyInfoDict["partyId"])
        if inviteeDict is not None:
            for info in inviteeDict:
                inviteeIds.append(info['guestId'])

        # Send the party info back to the AI who requested it
        self.air.sendUpdateToDoId(
            "DistributedPartyManager",
            'partyInfoOfHostResponseUdToAi',
            pmDoId,
            [self.getFormattedPartyInfo(partyInfoDict), inviteeIds],
        )

    def _checkForPartiesStarting(self, task):
        """ Called every 15 minutes to alert hosts to parties that can start """
        DistributedPartyManagerUD.notify.debug( "_checkForPartiesStarting : Checking for parties starting..." )
        curServerDateTime = self.air.toontownTimeManager.getCurServerDateTime()
        # force started parties to finished if they've gone for for too long
        self.forceFinishedForStarted()
        # first mark as never started parties who went past the end time
        self.forceNeverStartedForCanStart()

        partiesStartingTuples = tuple(self.partyDb.getPartiesAvailableToStart(curServerDateTime.strftime("%Y-%m-%d %H:%M:%S")))
        # Now we know the partyIds and hostIds of parties that can start, let's
        # send those directly out to the DistributedToons who can use them!
        for infoDict in partiesStartingTuples:
            self.notify.debug('%d can   %d' % (infoDict['hostId'], infoDict['partyId']))
            self.air.sendUpdateToDoId(
                "DistributedToon",
                "setPartyCanStart",
                infoDict['hostId'],
                [infoDict['partyId']],
            )
        timeToNextCheck = ((self.startPartyFrequency - (curServerDateTime.minute % self.startPartyFrequency)) * 60) - curServerDateTime.second + 1
        self.notify.debug("timeToNextCheck=%s" % timeToNextCheck)
        if task:
            taskMgr.doMethodLater(timeToNextCheck, self._checkForPartiesStarting, "DistributedPartyManagerUD_checkForPartiesStarting" )
        else:
            # if we got here through ~party checkStart, don't schedule another check
            self.notify.debug("not rescheduling self._checkForPartiesStarting")

    def _sanityCheckParties(self, task):
        """ Called every 60 minutes to check the database for started but never finished parties """
        self.notify.debug( "_sanityCheckParties :..." )
        self.forceFinishedForStarted()
        # check is now done every 5 minutes as part of check parties starting
        # taskMgr.doMethodLater(self.partiesSanityCheckFrequency * 60, self._sanityCheckParties, "DistributedPartyManagerUD_sanityCheckParties")

    def forceFinishedForStarted(self):
        """check the database for started but never finished parties."""
        curServerDateTime = self.air.toontownTimeManager.getCurServerDateTime()
        thresholdTime = curServerDateTime + timedelta(hours = -(PartyGlobals.DefaultPartyDuration ))
        result = self.partyDb.forceFinishForStarted(thresholdTime.strftime("%Y-%m-%d %H:%M:%S"))
        # first make sure result isn't an empty or invalid list
        if not result:
            return
        for info in result:
            partyId = info['partyId']
            hostId = info['hostId']
            if self.isOnline(hostId):
                status = PartyGlobals.PartyStatus.Finished
                self.sendNewPartyStatus(hostId, partyId, status)

    def forceNeverStartedForCanStart(self):
        curServerDateTime = self.air.toontownTimeManager.getCurServerDateTime()
        result = self.partyDb.forceNeverStartedForCanStart(curServerDateTime.strftime("%Y-%m-%d %H:%M:%S"))
        # first make sure result isn't an empty list or invalid list
        if not result:
            return
        for info in result:
            partyId = info['partyId']
            hostId = info['hostId']
            if self.isOnline(hostId):
                status = PartyGlobals.PartyStatus.NeverStarted
                self.sendNewPartyStatus(hostId, partyId, status)

    def sendNewPartyStatus(self, avatarId, partyId, newStatus):
        """Tell a toon a party status has changed."""
        DistributedPartyManagerUD.notify.debug( "Calling DistributedToon::sendNewPartyStatus  across the network with avatarId %d. partyId=%d newStatus=%d." %(avatarId, partyId, newStatus ) )
        self.air.sendUpdateToDoId(
            "DistributedToon",
            "setPartyStatus",
            avatarId,
            [partyId, newStatus],
            )

    def toonHasEnteredPartyAiToUd(self, hostId):
        """ This gets called when a toon enters a party. """
        DistributedPartyManagerUD.notify.debug("toonHasEnteredPartyAiToUd : someone entered hostIds %s party"%hostId)
        if hostId in self.hostAvIdToAllPartiesInfo:
            self.hostAvIdToAllPartiesInfo[hostId][3] += 1
            if self.hostAvIdToAllPartiesInfo[hostId][3] >= 0:
                self.sendUpdateToAllAis("updateToPublicPartyCountUdToAllAi", [hostId, self.hostAvIdToAllPartiesInfo[hostId][3]])

    def toonHasExitedPartyAiToUd(self, hostId):
        """ This gets called when a toon exits a party. """
        DistributedPartyManagerUD.notify.debug("toonHasExitedPartyAiToUd : someone exited hostIds %s party"%hostId)
        if hostId in self.hostAvIdToAllPartiesInfo:
            self.hostAvIdToAllPartiesInfo[hostId][3] -= 1
            if self.hostAvIdToAllPartiesInfo[hostId][3] >= 0:
                self.sendUpdateToAllAis("updateToPublicPartyCountUdToAllAi", [hostId, self.hostAvIdToAllPartiesInfo[hostId][3]])

    def partyHasStartedAiToUd(self, pmDoId, partyId, shardId, zoneId, hostName):
        """
        This gets called by an AI when a party is started, updates
        hostAvIdToAllPartiesInfo for use by other AIs and their public party
        gates.
        """
        DistributedPartyManagerUD.notify.debug("partyHasStartedAiToUd : pmDoId=%s partyId=%s shardId=%s zoneId=%s hostName=%s " % (pmDoId, partyId, shardId, zoneId, hostName))
        errorCode = self.changePartyStatusRequestAiToUd(pmDoId, partyId, PartyGlobals.PartyStatus.Started)
        if errorCode != PartyGlobals.ChangePartyFieldErrorCode.AllOk:
            return
        party = self.partyDb.getParty(partyId)
        partyInfo = party[0]
        activityIds = []
        for i in range(len(partyInfo["activities"])):
            if i%4 == 0:
                activityIds.append(partyInfo["activities"][i])
        # we can not rely on globalClock.getRealTime() as that depends on when the process is started
        # and will definitely be different between the uberdog and AI
        actualStartTime = int(time.time())
        self.hostAvIdToAllPartiesInfo[partyInfo["hostId"]] = [shardId, zoneId, partyInfo["isPrivate"], 0, hostName, activityIds,actualStartTime, partyId]
        self.sendUpdateToAllAis("updateToPublicPartyInfoUdToAllAi", [partyInfo["hostId"], actualStartTime, shardId, zoneId, partyInfo["isPrivate"], 0, hostName, activityIds, partyId])
        self.informInviteesPartyHasStarted(partyId)

    def sendUpdateToAllAis(self, message, args):
        pass 
    #TODO figure out alternative for PARTY_MANAGER_UD_TO_ALL_AI
        #dg = self.dclass.aiFormatUpdateMsgType(
               # message, self.doId, self.doId, self.air.ourChannel, PARTY_MANAGER_UD_TO_ALL_AI, args)
        #self.air.send(dg)

    def sendTestMsg(self):
        """Send a test msg to all AIs to prove it can be done."""
        fieldName = 'testMsgUdToAllAi'
        args = []
        dg = self.dclass.aiFormatUpdateMsgType(
                fieldName, self.doId, self.doId, self.air.ourChannel, PARTY_MANAGER_UD_TO_ALL_AI, args)
        self.air.send(dg)

    def forceCheckStart(self):
        """Do an immediate check which parties can start."""
        self._checkForPartiesStarting(None)

    def avatarOnlinePlusAccountInfo(self,avatarId,accountId,playerName,
                                    playerNameApproved,openChatEnabled,
                                    createFriendsWithChat,chatCodeCreation):
        # otp server is telling us an avatar just logged in
        # this is far far better than having the AI be the one to tell us
        assert self.notify.debugCall()
        assert avatarId

        self.notify.debug("avatarOnlinePlusAccountInfo")
        self.avatarLoggedIn(avatarId)
        self.markAvatarOnline(avatarId)

    def avatarOffline(self, avatarId):
        """Handle otp_server telling us an avatar is offline."""
        self.markAvatarOffline(avatarId)


    def markAvatarOnline(self, avatarId):
        """Mark an avatar as online."""

        if avatarId in self.isAvatarOnline:
            assert self.notify.debug(
                "\n\nWe got a duplicate avatar online notice %s"%(avatarId,))
        if avatarId and avatarId not in self.isAvatarOnline:
            self.isAvatarOnline[avatarId]=True

    def markAvatarOffline(self, avatarId):
        """Mark an avatar as offline."""
        self.isAvatarOnline.pop(avatarId,None)

    def isOnline(self, avatarId):
        """Return True if an avatar is online."""
        result = avatarId in self.isAvatarOnline
        return result

    def handleInterruptedPartiesOnShard(self, shardId):
        """Tell other shards the parties on this shard are gone, set party status back to CanStart."""
        # figure out which partyIds are running on that shard
        assert self.notify.debugStateCall(self)
        interruptedParties = []
        interruptedPartiesToCanStart = []
        interruptedPartiesToFinished = []
        interruptedHostIds = []
        for hostId in  self.hostAvIdToAllPartiesInfo:
            partyInfo = self.hostAvIdToAllPartiesInfo[hostId]
            if partyInfo[0] == shardId:
                interruptedParties.append(partyInfo[7])
                interruptedHostIds.append(hostId)

        # TODO is it possible for a toon to get back online before we hit this point?
        # Currently if the current server time is past party end time, he is SOL and can't start a party
        curServerTime = self.air.toontownTimeManager.getCurServerDateTime()
        interruptedInfo = tuple(self.partyDb.getMultipleParties(interruptedParties))
        for info in interruptedInfo:
            endTime = info["endTime"]
            endTime = datetime(
                endTime.year,
                endTime.month,
                endTime.day,
                endTime.hour,
                endTime.minute,
                tzinfo=self.air.toontownTimeManager.serverTimeZone,
            )
            if endTime < curServerTime:
                interruptedPartiesToFinished.append(info["partyId"])
            else:
                interruptedPartiesToCanStart.append(info["partyId"])

        if interruptedPartiesToCanStart:
            self.notify.debug('setting these parties to CanStart %s' % interruptedPartiesToCanStart)
        if interruptedPartiesToFinished:
            self.notify.debug('setting these parties to Finished %s' % interruptedPartiesToFinished)

        # the toon just got kicked out, he will probably want to go back and restart
        self.partyDb.changeMultiplePartiesStatus(interruptedPartiesToCanStart,
                                                 PartyGlobals.PartyStatus.CanStart)
        self.partyDb.changeMultiplePartiesStatus(interruptedPartiesToFinished,
                                                 PartyGlobals.PartyStatus.Finished)

        for index,hostId  in enumerate(interruptedHostIds):
            if self.isOnline(hostId):
                partyId = interruptedParties[index]
                if partyId in interruptedPartiesToCanStart:
                    status = PartyGlobals.PartyStatus.CanStart
                else:
                    status = PartyGlobals.PartyStatus.Finished
                self.sendNewPartyStatus(hostId, partyId, status)

        # tell all AI servers the party has finished since it was interrupted
        for hostId in interruptedHostIds:
            self.sendUpdateToAllAis("partyHasFinishedUdToAllAi", [hostId])
            del self.hostAvIdToAllPartiesInfo[hostId]


    def partyManagerAIStartingUp(self, pmDoId, shardId):
        """An AI server is starting up (or restarting) , send him all public parties running."""
        # if this shardId is starting up, it implies that all parties running on this
        # shard have been interrupted
        assert self.notify.debugStateCall(self)
        # we still need this check just in case uberdog was accidentally shut down
        # before the AI servers
        self.handleInterruptedPartiesOnShard(shardId)

        for hostId in self.hostAvIdToAllPartiesInfo:
            publicInfo = self.hostAvIdToAllPartiesInfo[hostId]
            numToons = publicInfo[3]
            if numToons <0:
                numToons = 0
            self.air.sendUpdateToDoId(
                "DistributedPartyManager",
                'updateToPublicPartyInfoUdToAllAi',
                pmDoId,
                [hostId, publicInfo[6], publicInfo[0], publicInfo[1], publicInfo[2], numToons,
                 publicInfo[4], publicInfo[5], publicInfo[7]],
            )

    def partyManagerAIGoingDown(self, pmDoId, shardId):
        """An AI server is going down, interupt parties appropriately"""
        # if this shardId is going down, it implies that all parties running on this
        # shard have been interrupted
        assert self.notify.debugStateCall(self)
        self.handleInterruptedPartiesOnShard(shardId)


    def updateAllPartyInfoToUd(self, hostId, startTime, shardId, zoneId, isPrivate, numberOfGuests, \
                               hostName, activityIds, partyId):
        """Handle an AI server telling us all the information about a party running on him."""
        if hostId in self.hostAvIdToAllPartiesInfo:
            self.notify.warning("hostId %s already in self.hostAvIdToAllPartiesInfo %s" % (
                hostId, self.hostAvIdToAllPartiesInfo[hostId]))

        self.hostAvIdToAllPartiesInfo[hostId] = [
            shardId, zoneId, isPrivate, numberOfGuests,
            hostName, activityIds, startTime, partyId]

    def informInviteesPartyHasStarted(self, partyId):
        """The host has started his party, tell the invitees."""
        # WARNING since this is not sent through a ram field, if the toon switches
        # districts the AI on the other district could have the party status wrong.
        # To do it 100% safe we'd need to do a _updateInvites and _updatePartiesInvitedTo
        # but those are fairly expensive operations, let's just try this for now
        inviteeDict = self.inviteDb.getInviteesOfParty(partyId)
        for info in inviteeDict:
            avId = info['guestId']
            if self.isOnline(avId):
                self.sendNewPartyStatus( avId, partyId, PartyGlobals.PartyStatus.Started)

    def _getPartyInfoSize(self, partyInfo):
        """
        Calculate the size of the party info and return the value in bytes.
        This is the format of the party info from toon.dc:
        struct party{
        uint64 partyId;         - 8 bytes
        uint32 hostId;          - 4 bytes
        uint16 startYear;       - 2 bytes
        uint8  startMonth;      - 1 byte
        uint8  startDay;        - 1 byte
        uint8  startHour;       - 1 byte
        uint8  startMinute;     - 1 byte
        uint16 endYear;         - 2 bytes
        uint8  endMonth;        - 1 byte
        uint8  endDay;          - 1 byte
        uint8  endHour;         - 1 byte
        uint8  endMinute;       - 1 byte
        uint8  isPrivate;       - 1 byte
        uint8  inviteTheme;     - 1 byte
        activity activities[];  - 4 bytes * numberOfActivities
        decoration decors[];    - 4 bytes * numberOfDecors
        uint8  status;          - 1 byte
        };
        So the basic party info size is:
        partyInfoSize = (27 + 4*numberOfActivities + 4*numberOfDecors) bytes

        Note: We assume that the party info format in toon.dc won't change.
        Please change this method and calculation if the format changes.
        """
        activities = partyInfo[14]
        decors = partyInfo[15]
        basePartySize = 27
        numActivities = 0
        numDecors = 0

        if (type(activities) == type([])):
            numActivities = len(activities)
        else:
            self.notify.warning("partyId=%s has an incorrect partyInfo format for activities" %str(partyInfo[0]))

        if (type(decors) == type([])):
            numDecors = len(decors)
        else:
            self.notify.warning("partyId=%s has an incorrect partyInfo format for decors" %str(partyInfo[0]))

        partyInfoSize = basePartySize + (4 * numActivities) + (4 * numDecors)
        return partyInfoSize
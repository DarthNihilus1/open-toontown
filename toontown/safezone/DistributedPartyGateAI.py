# Referenced Anesidora to help make some functions
#-------------------------------------------------------------------------------
# Contact: Shawn Patton
# Created: Sep 2008
#
# Purpose: AI side of the party hat which is where toon's go to access public
#          parties.
#-------------------------------------------------------------------------------

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.task import Task
from toontown.parties import PartyGlobals

class DistributedPartyGateAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPartyGateAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
    
    def getPartyList(self, avId):
        """
        Retrieves the list of all public parties for the given avatar ID (avId).
        This method checks if the provided avId matches the sender's avatar ID.
        If they do not match, it logs a suspicious event and returns without
        sending the party list. If they match, it sends the list of all public
        parties to the avatar.
        Args:
            avId (int): The avatar ID requesting the party list.
        Returns:
            None
        """
        
        senderId = self.air.getAvatarIdFromSender()
        if avId != senderId:
            self.air.writeServerEvent('suspicious', avId, 'DistributedPartyGateAI.getPartyList avId: %s does not match sender avId: %s' % (avId, senderId))
            return
        self.sendUpdateToAvatarId(avId, 'listAllPublicParties', [self.air.partyManager.getAllPublicParties()])

    def partyChoiceRequest(self, avId, shardId, zoneId):
        """
            This function 
            1. Checks if the avId matches the sender
            2. Gets all public parties
            3. Checks if the party is full
            4. Sends the party information to the avatar
        """
        senderId = self.air.getAvatarIdFromSender()
        if avId != senderId:
            self.air.writeServerEvent('suspicious', avId, 'DistributedPartyGateAI.partyChoiceRequest avId: %s does not match sender avId: %s' % (avId, senderId))
            return
        allPublicParties = self.air.partyManager.getAllPublicParties()

        if len(allPublicParties) == 0:
            # No public parties available
            self.sendUpdateToAvatarId(avId, 'partyRequestDenied', [PartyGlobals.PartyGateDenialReasons.Unavailable])
            return
        else:
            for party in allPublicParties:
                if party[0] == shardId and party[1] == zoneId:
                    # Party found
                    if party[2] < PartyGlobals.MaxToonsAtAParty:
                        # Party is not full
                        self.sendUpdateToAvatarId(avId, 'setParty', [party])
                        return
                    else:
                        # Party is full
                        self.sendUpdateToAvatarId(avId, 'partyRequestDenied', [PartyGlobals.PartyGateDenialReasons.Full])
                        return
                    break #

            else:
                # Party not found
                self.sendUpdateToAvatarId(avId, 'partyRequestDenied', [PartyGlobals.PartyGateDenialReasons.Unavailable])
                return
        
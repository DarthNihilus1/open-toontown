from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from toontown.parties import PartyGlobals
from toontown.parties.DistributedPartyCatchActivityAI import DistributedPartyCatchActivityAI

class DistributedPartyWinterCatchActivityAI(DistributedPartyCatchActivityAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPartyWinterCatchActivityAI')

    def __init__(self, air, partyDoId, x, y, h):
        DistributedPartyCatchActivityAI.__init__(self,
                                            air,
                                            partyDoId,
                                            x, y, h
                                            )
        self.notify.debug("Intializing.")
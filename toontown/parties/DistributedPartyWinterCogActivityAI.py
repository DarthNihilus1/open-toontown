from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from toontown.parties.DistributedPartyCogActivityAI import DistributedPartyCogActivityAI

class DistributedPartyWinterCogActivityAI(DistributedPartyCogActivityAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPartyWinterCogActivityAI')
    
    def __init__(self, air, partyDoId, x, y, h):
        DistributedPartyCogActivityAI.__init__(self, air, partyDoId, x, y, h)

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from .DistributedPartyTrampolineActivityAI import DistributedPartyTrampolineActivityAI
from . import  PartyGlobals 

class DistributedPartyWinterTrampolineActivityAI(DistributedPartyTrampolineActivityAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPartyWinterTrampolineActivityAI')

    def __init__(self, air, partyDoId, x, y, h, actId=PartyGlobals.ActivityIds.PartyWinterTrampoline):
        DistributedPartyTrampolineActivityAI.__init__(self, air, partyDoId, x, y, h, actId)

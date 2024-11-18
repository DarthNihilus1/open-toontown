from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from toontown.parties.DistributedPartyDanceActivityBaseAI import DistributedPartyDanceActivityBaseAI
from toontown.parties import PartyGlobals
class DistributedPartyValentineDanceActivityAI(DistributedPartyDanceActivityBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPartyValentineDanceActivityAI')

    def __init__(self, air, partyDoId, x, y, h):
        DistributedPartyDanceActivityBaseAI.__init__(self,
            air,
            partyDoId,
            x, y, h,
            PartyGlobals.ActivityIds.PartyValentineDance,
            PartyGlobals.DancePatternToAnims,
            )
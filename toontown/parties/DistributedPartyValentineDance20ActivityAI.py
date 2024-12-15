from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from toontown.parties.DistributedPartyDanceActivityBaseAI import DistributedPartyDanceActivityBaseAI
from toontown.parties import PartyGlobals
class DistributedPartyValentineDance20ActivityAI(DistributedPartyDanceActivityBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPartyValentineDance20ActivityAI')

    def __init__(self, air, partyDoId, x, y, h):
        self.notify.debug("Intializing.")
        DistributedPartyDanceActivityBaseAI.__init__(self,
                                            air,
                                            partyDoId,
                                            x, y, h,
                                            PartyGlobals.ActivityIds.PartyValentineDance20,
                                            PartyGlobals.DancePatternToAnims,
                                            )
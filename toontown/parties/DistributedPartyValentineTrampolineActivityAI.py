from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from toontown.parties import PartyGlobals
from toontown.parties.DistributedPartyTrampolineActivityAI import DistributedPartyTrampolineActivityAI

class DistributedPartyValentineTrampolineActivityAI(DistributedPartyTrampolineActivityAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPartyValentineTrampolineActivityAI')

    def __init__(self, air, partyDoId, x, y, h):
        DistributedPartyTrampolineActivityAI.__init__(self,
                                            air,
                                            partyDoId,
                                            x, y, h,
                                            PartyGlobals.ActivityIds.PartyValentineTrampoline,
                                            )
        self.notify.debug("Intializing.")
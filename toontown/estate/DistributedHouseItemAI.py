from direct.distributed import DistributedObject
from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
class DistributedHouseItem(DistributedObject.DistributedObject):
    notify = directNotify.newCategory('DistributedHouseItem')

    def __init__(self):
        pass
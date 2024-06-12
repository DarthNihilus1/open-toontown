from toontown.suit import SuitDNA
from toontown.toonbase import TTLocalizer
from otp.otpbase import OTPGlobals
from enum import IntEnum
PartsPerSuit = (17,
 14,
 12,
 10)
PartsPerSuitBitmasks = (131071,
 130175,
 56447,
 56411)
AllBits = 131071
MinPartLoss = 2
MaxPartLoss = 4
MeritsPerLevel = ((100,
  130,
  160,
  190,
  800),
 (160,
  210,
  260,
  310,
  1300),
 (260,
  340,
  420,
  500,
  2100),
 (420,
  550,
  680,
  810,
  3400),
 (680,
  890,
  1100,
  1310,
  5500),
 (1100,
  1440,
  1780,
  2120,
  8900),
 (1780,
  2330,
  2880,
  3430,
  14400),
 (2880,
  3770,
  4660,
  5500,
  23300,
  2880,
  23300,
  2880,
  3770,
  4660,
  5500,
  23300,
  2880,
  3770,
  4660,
  5500,
  6440,
  7330,
  8220,
  9110,
  10000,
  23300,
  2880,
  3770,
  4660,
  5500,
  6440,
  7330,
  8220,
  9110,
  10000,
  23300,
  2880,
  3770,
  4660,
  5500,
  6440,
  7330,
  8220,
  9110,
  10000,
  23300,
  0),
 (60,
  80,
  100,
  120,
  500),
 (100,
  130,
  160,
  190,
  800),
 (160,
  210,
  260,
  310,
  1300),
 (260,
  340,
  420,
  500,
  2100),
 (420,
  550,
  680,
  810,
  3400),
 (680,
  890,
  1100,
  1310,
  5500),
 (1100,
  1440,
  1780,
  2120,
  8900),
 (1780,
  2330,
  2880,
  3430,
  14400,
  1780,
  14400,
  1780,
  2330,
  2880,
  3430,
  14400,
  1780,
  2330,
  2880,
  3430,
  3980,
  4530,
  5080,
  5630,
  6180,
  14400,
  1780,
  2330,
  2880,
  3430,
  3980,
  4530,
  5080,
  5630,
  6180,
  14400,
  1780,
  2330,
  2880,
  3430,
  3980,
  4530,
  5080,
  5630,
  6180,
  14400,
  0),
 (40,
  50,
  60,
  70,
  300),
 (60,
  80,
  100,
  120,
  500),
 (100,
  130,
  160,
  190,
  800),
 (160,
  210,
  260,
  310,
  1300),
 (260,
  340,
  420,
  500,
  2100),
 (420,
  550,
  680,
  810,
  3400),
 (680,
  890,
  1100,
  1310,
  5500),
 (1100,
  1440,
  1780,
  2120,
  8900,
  1100,
  8900,
  1100,
  1440,
  1780,
  2120,
  8900,
  1100,
  1440,
  1780,
  2120,
  2460,
  2800,
  3140,
  3480,
  3820,
  8900,
  1100,
  1440,
  1780,
  2120,
  2460,
  2800,
  3140,
  3480,
  3820,
  8900,
  1100,
  1440,
  1780,
  2120,
  2460,
  2800,
  3140,
  3480,
  3820,
  8900,
  0),
 (20,
  30,
  40,
  50,
  200),
 (40,
  50,
  60,
  70,
  300),
 (60,
  80,
  100,
  120,
  500),
 (100,
  130,
  160,
  190,
  800),
 (160,
  210,
  260,
  310,
  1300),
 (260,
  340,
  420,
  500,
  2100),
 (420,
  550,
  680,
  810,
  3400),
 (680,
  890,
  1100,
  1310,
  5500,
  680,
  5500,
  680,
  890,
  1100,
  1310,
  5500,
  680,
  890,
  1100,
  1310,
  1520,
  1730,
  1940,
  2150,
  2360,
  5500,
  680,
  890,
  1100,
  1310,
  1520,
  1730,
  1940,
  2150,
  2360,
  5500,
  680,
  890,
  1100,
  1310,
  1520,
  1730,
  1940,
  2150,
  2360,
  5500,
  0))
# merits required to get to next level for v2 suit (not required to enter boss)
v2MeritsPerLevel = ((
    # bossbot
2620, # 8
3040, # 9
3460, # 10
3880, # 11
15200, # 12
2620, # 13
15200, # 14
2620, # 15
3040, # 16
3460, # 17
3880, # 18
15200, # 19
2620, # 20
3040, # 21
3460, # 22
3880, # 23
4300, # 24
4720, # 25
5140, # 26
5560, # 27
5980, # 28
15200, # 29
2620, # 30
3040, # 31
3460, # 32
3880, # 33
4300, # 34
4720, # 35
5140, # 36
5560, # 37
5980, # 38
15200, # 39
2620, # 40
3040, # 41
3460, # 42
3880, # 43
4300, # 44
4720, # 45
5140, # 46
5560, # 47
5980, # 48
15200), # 49
    # lawbot
    (2200, # 8
    2620, # 9
    3040, # 10
    3460, # 11
    13100, # 12
    2200, # 13
    13100, # 14
    2200, # 15
    2620, # 16
    3040, # 17
    3460, # 18
    13100, # 19
    2200, # 20
    2620, # 21
    3040, # 22
    3460, # 23
    3880, # 24
    4300, # 25
    4720, # 26
    5140, # 27
    5560, # 28
    13100, # 29
    2200, # 30
    2620, # 31
    3040, # 32
    3460, # 33
    3880, # 34
    4300, # 35
    4720, # 36
    5140, # 37
    5560, # 38
    13100, # 39
    2200, # 40
    2620, # 41
    3040, # 42
    3460, # 43
    3880, # 44
    4300, # 45
    4720, # 46
    5140, # 47
    5560, # 48
    13100), # 49
    # cashbot
    (1780, # 8
    2200, # 9
    2620, # 10
    3040, # 11
    11000, # 12
    1780, # 13
    11000, # 14
    1780, # 15
    2200, # 16
    2620, # 17
    3040, # 18
    11000, # 19
    1780, # 20
    2200, # 21
    2620, # 22
    3040, # 23
    3460, # 24
    3880, # 25
    4300, # 26
    4720, # 27
    5140, # 28
    11000, # 29
    1780, # 30
    2200, # 31
    2620, # 32
    3040, # 33
    3460, # 34
    3880, # 35
    4300, # 36
    4720, # 37
    5140, # 38
    11000, # 39
    1780, # 40
    2200, # 41
    2620, # 42
    3040, # 43
    3460, # 44
    3880, # 45
    4300, # 46
    4720, # 47
    5140, # 48
    11000), # 49
    # sellbot
    (1360, # 8
    1780, # 9
    2200, # 10
    2620, # 11
    8900, # 12
    1360, # 13
    8900, # 14
    1360, # 15
    1780, # 16
    2200, # 17
    2620, # 18
    8900, # 19
    1360, # 20
    1780, # 21
    2200, # 22
    2620, # 23
    3040, # 24
    3460, # 25
    3880, # 26
    4300, # 27
    4720, # 28
    8900, # 29
    1360, # 30
    1780, # 31
    2200, # 32
    2620, # 33
    3040, # 34
    3460, # 35
    3880, # 36
    4300, # 37
    4720, # 38
    8900, # 39
    1360, # 40
    1780, # 41
    2200, # 42
    2620, # 43
    3040, # 44
    3460, # 45
    3880, # 46
    4300, # 47
    4720, # 48
    8900)) # 49
leftLegUpper = 1
leftLegLower = 2
leftLegFoot = 4
rightLegUpper = 8
rightLegLower = 16
rightLegFoot = 32
torsoLeftShoulder = 64
torsoRightShoulder = 128
torsoChest = 256
torsoHealthMeter = 512
torsoPelvis = 1024
leftArmUpper = 2048
leftArmLower = 4096
leftArmHand = 8192
rightArmUpper = 16384
rightArmLower = 32768
rightArmHand = 65536
upperTorso = torsoLeftShoulder
leftLegIndex = 0
rightLegIndex = 1
torsoIndex = 2
leftArmIndex = 3
rightArmIndex = 4
PartsQueryShifts = (leftLegUpper,
 rightLegUpper,
 torsoLeftShoulder,
 leftArmUpper,
 rightArmUpper)
PartsQueryMasks = (leftLegFoot + leftLegLower + leftLegUpper,
 rightLegFoot + rightLegLower + rightLegUpper,
 torsoPelvis + torsoHealthMeter + torsoChest + torsoRightShoulder + torsoLeftShoulder,
 leftArmHand + leftArmLower + leftArmUpper,
 rightArmHand + rightArmLower + rightArmUpper)
PartNameStrings = TTLocalizer.CogPartNames
SimplePartNameStrings = TTLocalizer.CogPartNamesSimple
PartsQueryNames = ({1: PartNameStrings[0],
  2: PartNameStrings[1],
  4: PartNameStrings[2],
  8: PartNameStrings[3],
  16: PartNameStrings[4],
  32: PartNameStrings[5],
  64: PartNameStrings[6],
  128: PartNameStrings[7],
  256: PartNameStrings[8],
  512: PartNameStrings[9],
  1024: PartNameStrings[10],
  2048: PartNameStrings[11],
  4096: PartNameStrings[12],
  8192: PartNameStrings[13],
  16384: PartNameStrings[14],
  32768: PartNameStrings[15],
  65536: PartNameStrings[16]},
 {1: PartNameStrings[0],
  2: PartNameStrings[1],
  4: PartNameStrings[2],
  8: PartNameStrings[3],
  16: PartNameStrings[4],
  32: PartNameStrings[5],
  64: SimplePartNameStrings[0],
  128: SimplePartNameStrings[0],
  256: SimplePartNameStrings[0],
  512: SimplePartNameStrings[0],
  1024: PartNameStrings[10],
  2048: PartNameStrings[11],
  4096: PartNameStrings[12],
  8192: PartNameStrings[13],
  16384: PartNameStrings[14],
  32768: PartNameStrings[15],
  65536: PartNameStrings[16]},
 {1: PartNameStrings[0],
  2: PartNameStrings[1],
  4: PartNameStrings[2],
  8: PartNameStrings[3],
  16: PartNameStrings[4],
  32: PartNameStrings[5],
  64: SimplePartNameStrings[0],
  128: SimplePartNameStrings[0],
  256: SimplePartNameStrings[0],
  512: SimplePartNameStrings[0],
  1024: PartNameStrings[10],
  2048: PartNameStrings[11],
  4096: PartNameStrings[12],
  8192: PartNameStrings[12],
  16384: PartNameStrings[14],
  32768: PartNameStrings[15],
  65536: PartNameStrings[15]},
 {1: PartNameStrings[0],
  2: PartNameStrings[1],
  4: PartNameStrings[1],
  8: PartNameStrings[3],
  16: PartNameStrings[4],
  32: PartNameStrings[4],
  64: SimplePartNameStrings[0],
  128: SimplePartNameStrings[0],
  256: SimplePartNameStrings[0],
  512: SimplePartNameStrings[0],
  1024: PartNameStrings[10],
  2048: PartNameStrings[11],
  4096: PartNameStrings[12],
  8192: PartNameStrings[12],
  16384: PartNameStrings[14],
  32768: PartNameStrings[15],
  65536: PartNameStrings[15]})
suitTypes = IntEnum('suitTypes', ('NoSuit', 'NoMerits', 'FullSuit'), start=0)

def getNextPart(parts, partIndex, dept):
    dept = dept2deptIndex(dept)
    needMask = PartsPerSuitBitmasks[dept] & PartsQueryMasks[partIndex]
    haveMask = parts[dept] & PartsQueryMasks[partIndex]
    nextPart = ~needMask | haveMask
    nextPart = nextPart ^ nextPart + 1
    nextPart = nextPart + 1 >> 1
    return nextPart


def getPartName(partArray):
    index = 0
    for part in partArray:
        if part:
            return PartsQueryNames[index][part]
        index += 1


def isSuitComplete(parts, dept):
    dept = dept2deptIndex(dept)
    for p in range(len(PartsQueryMasks)):
        if getNextPart(parts, p, dept):
            return 0

    return 1


def isPaidSuitComplete(av, parts, dept):
    isPaid = 0
    base = getBase()
    if av and av.getGameAccess() == OTPGlobals.AccessFull:
        isPaid = 1
    if isPaid:
        if isSuitComplete(parts, dept):
            return 1
    return 0


def getTotalMerits(toon, index):
    from toontown.battle import SuitBattleGlobals
    cogIndex = toon.cogTypes[index] + SuitDNA.suitsPerDept * index
    cogTypeStr = SuitDNA.suitHeadTypes[cogIndex]
    cogBaseLevel = SuitBattleGlobals.SuitAttributes[cogTypeStr]['level']
    cogLevel = toon.cogLevels[index] - cogBaseLevel
    cogLevel = max(min(cogLevel, len(MeritsPerLevel[cogIndex]) - 1), 0)
    return MeritsPerLevel[cogIndex][cogLevel]

def getTotalV2Merits(toon, index):
    # this is different from getTotalMerits because it doesn't have the other cog tiers , just the highest tier of the department
    from toontown.battle import SuitBattleGlobals
    # this will be just the last tier of the department
    cogBaseLevel = 7
    cogLevel = toon.cogLevels[index] - cogBaseLevel
    # cogLevel = max(min(cogLevel, len(v2MeritsPerLevel[cogIndex]) - 1), 0)
    return v2MeritsPerLevel[index][cogLevel]

def getTotalParts(bitString, shiftWidth = 32):
    sum = 0
    for shift in range(0, shiftWidth):
        sum = sum + (bitString >> shift & 1)

    return sum


def asBitstring(number):
    array = []
    shift = 0
    if number == 0:
        array.insert(0, '0')
    while pow(2, shift) <= number:
        if number >> shift & 1:
            array.insert(0, '1')
        else:
            array.insert(0, '0')
        shift += 1

    str = ''
    for i in range(0, len(array)):
        str = str + array[i]

    return str


def asNumber(bitstring):
    num = 0
    for i in range(0, len(bitstring)):
        if bitstring[i] == '1':
            num += pow(2, len(bitstring) - 1 - i)

    return num


def dept2deptIndex(dept):
    if type(dept) == str:
        dept = SuitDNA.suitDepts.index(dept)
    return dept

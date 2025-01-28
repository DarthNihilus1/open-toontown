from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from direct.distributed.PyDatagram import *
from direct.distributed.MsgTypes import  *
from otp.otpbase import OTPGlobals
import random
import string
import json
class FriendsOperation:
    """
    Base class for all friend-related operations.
    """

    def __init__(self, friendsManager, sender):
        """
        Initialize the FriendsOperation.

        :param friendsManager: The friends manager instance.
        :param sender: The sender's ID.
        """
        self.friendsManager = friendsManager
        self.sender = sender

    def _handleDone(self):
        """
        Handle the completion of the operation.
        """
        self.friendsManager.operations.remove(self)

    def _handleError(self, error):
        """
        Handle an error during the operation.

        :param error: The error message.
        """
        self.friendsManager.notify.warning(error)
        self.friendsManager.operations.remove(self)


class GetFriendsListOperation(FriendsOperation):
    """
    Operation to retrieve the friends list of a sender.
    """

    def __init__(self, friendsManager, sender):
        """
        Initialize the GetFriendsListOperation.

        :param friendsManager: The friends manager instance.
        :param sender: The sender's ID.
        """
        FriendsOperation.__init__(self, friendsManager, sender)
        self.friendsList = None
        self.tempFriendsList = None
        self.onlineFriends = None
        self.currentFriendIdx = None

    def start(self):
        """
        Start the operation to retrieve the friends list.
        """
        self.friendsList = []
        self.tempFriendsList = []
        self.onlineFriends = []
        self.currentFriendIdx = 0
        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, self.sender,
                                                        self.__handleSenderRetrieved)

    def __handleSenderRetrieved(self, dclass, fields):
        """
        Handle the retrieval of the sender's data.

        :param dclass: The data class of the sender.
        :param fields: The fields of the sender.
        """
        if dclass != self.friendsManager.air.dclassesByName['DistributedToonUD']:
            self._handleError('Retrieved sender is not a DistributedToonUD!')
            return

        self.tempFriendsList = fields['setFriendsList'][0]
        if len(self.tempFriendsList) <= 0:
            self._handleDone()
            return

        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, self.tempFriendsList[0][0],
                                                        self.__handleFriendRetrieved)

    def __handleFriendRetrieved(self, dclass, fields):
        """
        Handle the retrieval of a friend's data.

        :param dclass: The data class of the friend.
        :param fields: The fields of the friend.
        """
        if dclass != self.friendsManager.air.dclassesByName['DistributedToonUD']:
            self._handleError('Retrieved friend is not a DistributedToonUD!')
            return

        friendId = self.tempFriendsList[self.currentFriendIdx][0]
        self.friendsList.append([friendId, fields['setName'][0], fields['setDNAString'][0], fields['setPetId'][0]])
        if len(self.friendsList) >= len(self.tempFriendsList):
            self.__checkFriendsOnline()
            return

        self.currentFriendIdx += 1
        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId,
                                                        self.tempFriendsList[self.currentFriendIdx][0],
                                                        self.__handleFriendRetrieved)

    def __checkFriendsOnline(self):
        """
        Check which friends are currently online.
        """
        self.currentFriendIdx = 0
        for friendDetails in self.friendsList:
            self.friendsManager.air.getActivated(friendDetails[0], self.__gotActivatedResp)

    def __gotActivatedResp(self, avId, activated):
        """
        Handle the response of checking if a friend is activated.

        :param avId: The avatar ID.
        :param activated: Whether the friend is activated.
        """
        self.currentFriendIdx += 1
        if activated:
            self.onlineFriends.append(avId)

        if self.currentFriendIdx >= len(self.friendsList):
            self._handleDone()

    def __sendFriendsList(self, success):
        """
        Send the friends list to the sender.

        :param success: Whether the operation was successful.
        """
        self.friendsManager.sendUpdateToAvatarId(self.sender, 'getFriendsListResponse', [success, self.friendsList if success else []])
        for friendId in self.onlineFriends:
            self.friendsManager.sendFriendOnline(self.sender, friendId, 0, 1)

    def _handleDone(self):
        """
        Handle the completion of the operation.
        """
        self.__sendFriendsList(True)
        FriendsOperation._handleDone(self)

    def _handleError(self, error):
        """
        Handle an error during the operation.

        :param error: The error message.
        """
        self.__sendFriendsList(False)
        FriendsOperation._handleError(self, error)


class GetAvatarDetailsOperation(FriendsOperation):
    """
    Operation to retrieve the details of an avatar.
    """

    def __init__(self, friendsManager, sender):
        """
        Initialize the GetAvatarDetailsOperation.

        :param friendsManager: The friends manager instance.
        :param sender: The sender's ID.
        """
        FriendsOperation.__init__(self, friendsManager, sender)
        self.avId = None
        self.dclass = None
        self.fields = None

    def start(self, avId):
        """
        Start the operation to retrieve the avatar details.

        :param avId: The avatar ID.
        """
        self.avId = avId
        self.fields = {}
        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, avId,
                                                        self.__handleAvatarRetrieved)

    def __handleAvatarRetrieved(self, dclass, fields):
        """
        Handle the retrieval of the avatar's data.

        :param dclass: The data class of the avatar.
        :param fields: The fields of the avatar.
        """
        if dclass not in (self.friendsManager.air.dclassesByName['DistributedToonUD'],
                          self.friendsManager.air.dclassesByName['DistributedPetAI']):
            self._handleError('Retrieved avatar is not a DistributedToonUD or DistributedPetAI!')
            return

        self.dclass = dclass
        self.fields = fields
        self.fields['avId'] = self.avId
        self._handleDone()

    def __packAvatarDetails(self, dclass, fields):
        """
        Pack the avatar details into a byte array.

        :param dclass: The data class of the avatar.
        :param fields: The fields of the avatar.
        :return: The packed avatar details.
        """
        # Pack required fields.
        fieldPacker = DCPacker()
        for i in range(dclass.getNumInheritedFields()):
            field = dclass.getInheritedField(i)
            if not field.isRequired() or field.asMolecularField():
                continue

            k = field.getName()
            v = fields.get(k, None)

            fieldPacker.beginPack(field)
            if not v:
                fieldPacker.packDefaultValue()
            else:
                field.packArgs(fieldPacker, v)

            fieldPacker.endPack()

        return fieldPacker.getBytes()

    def __sendAvatarDetails(self, success):
        """
        Send the avatar details to the sender.

        :param success: Whether the operation was successful.
        """
        datagram = PyDatagram()
        datagram.addUint32(self.fields['avId'])  # avId
        datagram.addUint8(0 if success else 1)  # returnCode
        if success:
            avatarDetails = self.__packAvatarDetails(self.dclass, self.fields)
            datagram.appendData(avatarDetails)  # fields

        self.friendsManager.sendUpdateToAvatarId(self.sender, 'getAvatarDetailsResponse', [datagram.getMessage()])

    def _handleDone(self):
        """
        Handle the completion of the operation.
        """
        self.__sendAvatarDetails(True)
        FriendsOperation._handleDone(self)

    def _handleError(self, error):
        """
        Handle an error during the operation.

        :param error: The error message.
        """
        self.__sendAvatarDetails(False)
        FriendsOperation._handleError(self, error)


class MakeFriendsOperation(FriendsOperation):
    """
    Operation to make two avatars friends.
    """

    def __init__(self, friendsManager):
        """
        Initialize the MakeFriendsOperation.

        :param friendsManager: The friends manager instance.
        """
        FriendsOperation.__init__(self, friendsManager, None)
        self.avatarAId = None
        self.avatarBId = None
        self.flags = None
        self.context = None
        self.resultCode = None
        self.onlineToons = None
        self.avatarAFriendsList = None
        self.avatarBFriendsList = None

    def start(self, avatarAId, avatarBId, flags, context):
        """
        Start the operation to make two avatars friends.

        :param avatarAId: The first avatar's ID.
        :param avatarBId: The second avatar's ID.
        :param flags: The friendship flags.
        :param context: The context of the operation.
        """
        self.avatarAId = avatarAId
        self.avatarBId = avatarBId
        self.flags = flags
        self.context = context
        self.resultCode = 0
        self.onlineToons = []
        self.friendsManager.air.getActivated(self.avatarAId, self.__gotActivatedAvatarA)

    def __handleActivatedResp(self, avId, activated):
        """
        Handle the response of checking if an avatar is activated.

        :param avId: The avatar ID.
        :param activated: Whether the avatar is activated.
        """
        if activated:
            self.onlineToons.append(avId)

    def __gotActivatedAvatarA(self, avId, activated):
        """
        Handle the response of checking if the first avatar is activated.

        :param avId: The avatar ID.
        :param activated: Whether the avatar is activated.
        """
        self.__handleActivatedResp(avId, activated)
        self.friendsManager.air.getActivated(self.avatarBId, self.__gotActivatedAvatarB)

    def __handleMakeFriends(self, dclass, fields, friendId):
        """
        Handle the process of making friends.

        :param dclass: The data class of the avatar.
        :param fields: The fields of the avatar.
        :param friendId: The friend's ID.
        :return: A tuple indicating success and the updated friends list.
        """
        if dclass != self.friendsManager.air.dclassesByName['DistributedToonUD']:
            self._handleError('Retrieved avatar is not a DistributedToonUD!')
            return False, []

        friendsList = fields['setFriendsList'][0]
        if len(friendsList) >= OTPGlobals.MaxFriends:
            self._handleError('Avatar\'s friends list is full!')
            return False, []

        newFriend = (friendId, self.flags)
        if newFriend in friendsList:
            self._handleError('Already friends!')
            return False, []

        friendsList.append(newFriend)
        return True, friendsList

    def __handleAvatarARetrieved(self, dclass, fields):
        """
        Handle the retrieval of the first avatar's data.

        :param dclass: The data class of the avatar.
        :param fields: The fields of the avatar.
        """
        success, avatarAFriendsList = self.__handleMakeFriends(dclass, fields, self.avatarBId)
        if success:
            self.avatarAFriendsList = avatarAFriendsList
            self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, self.avatarBId,
                                                            self.__handleAvatarBRetrieved)

    def __gotActivatedAvatarB(self, avId, activated):
        """
        Handle the response of checking if the second avatar is activated.

        :param avId: The avatar ID.
        :param activated: Whether the avatar is activated.
        """
        self.__handleActivatedResp(avId, activated)
        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, self.avatarAId,
                                                        self.__handleAvatarARetrieved)

    def __handleAvatarBRetrieved(self, dclass, fields):
        """
        Handle the retrieval of the second avatar's data.

        :param dclass: The data class of the avatar.
        :param fields: The fields of the avatar.
        """
        success, avatarBFriendsList = self.__handleMakeFriends(dclass, fields, self.avatarAId)
        if success:
            self.avatarBFriendsList = avatarBFriendsList
            self._handleDone()

    def __handleSetFriendsList(self, avId, friendsList):
        """
        Handle setting the friends list for an avatar.

        :param avId: The avatar ID.
        :param friendsList: The updated friends list.
        """
        if avId in self.onlineToons:
            self.friendsManager.sendUpdateToAvatar(avId, 'setFriendsList', [friendsList])
        else:
            self.friendsManager.air.dbInterface.updateObject(self.friendsManager.air.dbId, avId,
                                                             self.friendsManager.air.dclassesByName[
                                                                 'DistributedToonUD'],
                                                             {'setFriendsList': [friendsList]})

    def _handleDone(self):
        """
        Handle the completion of the operation.
        """
        self.resultCode = 1
        if self.avatarAFriendsList is not None and self.avatarBFriendsList is not None:
            self.__handleSetFriendsList(self.avatarAId, self.avatarAFriendsList)
            self.__handleSetFriendsList(self.avatarBId, self.avatarBFriendsList)

        if self.avatarAId in self.onlineToons and self.avatarBId in self.onlineToons:
            self.friendsManager.declareObject(self.avatarAId, self.avatarBId)
            self.friendsManager.declareObject(self.avatarBId, self.avatarAId)

        self.friendsManager.sendMakeFriendsResponse(self.avatarAId, self.avatarBId, self.resultCode, self.context)
        FriendsOperation._handleDone(self)

    def _handleError(self, error):
        """
        Handle an error during the operation.

        :param error: The error message.
        """
        self.resultCode = 0
        self.friendsManager.sendMakeFriendsResponse(self.avatarAId, self.avatarBId, self.resultCode, self.context)
        FriendsOperation._handleError(self, error)


class RemoveFriendOperation(FriendsOperation):
    """
    Operation to remove a friend from the sender's friends list.
    """

    def __init__(self, friendsManager, sender):
        """
        Initialize the RemoveFriendOperation.

        :param friendsManager: The friends manager instance.
        :param sender: The sender's ID.
        """
        FriendsOperation.__init__(self, friendsManager, sender)
        self.friendId = None
        self.onlineToons = None
        self.senderFriendsList = None
        self.friendFriendsList = None

    def start(self, friendId):
        """
        Start the operation to remove a friend.

        :param friendId: The friend's ID.
        """
        self.friendId = friendId
        self.onlineToons = []
        self.friendsManager.air.getActivated(self.sender, self.__gotSenderActivated)

    def __handleActivatedResp(self, avId, activated):
        """
        Handle the response of checking if an avatar is activated.

        :param avId: The avatar ID.
        :param activated: Whether the avatar is activated.
        """
        if activated:
            self.onlineToons.append(avId)

    def __gotSenderActivated(self, avId, activated):
        """
        Handle the response of checking if the sender is activated.

        :param avId: The avatar ID.
        :param activated: Whether the avatar is activated.
        """
        self.__handleActivatedResp(avId, activated)
        self.friendsManager.air.getActivated(self.friendId, self.__gotFriendActivated)

    def __gotFriendActivated(self, avId, activated):
        """
        Handle the response of checking if the friend is activated.

        :param avId: The avatar ID.
        :param activated: Whether the avatar is activated.
        """
        self.__handleActivatedResp(avId, activated)
        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, self.sender,
                                                        self.__handleSenderRetrieved)

    def __handleRemoveFriend(self, dclass, fields, friendId):
        """
        Handle the process of removing a friend.

        :param dclass: The data class of the avatar.
        :param fields: The fields of the avatar.
        :param friendId: The friend's ID.
        :return: A tuple indicating success and the updated friends list.
        """
        if dclass != self.friendsManager.air.dclassesByName['DistributedToonUD']:
            self._handleError('Retrieved sender is not a DistributedToonUD!')
            return False, []

        friendsList = fields['setFriendsList'][0]
        removed = False
        for index, friend in enumerate(friendsList):
            if friend[0] == friendId:
                del friendsList[index]
                removed = True
                break

        if removed:
            return True, friendsList
        else:
            self._handleError('Unable to remove friend!')
            return False, []

    def __handleSenderRetrieved(self, dclass, fields):
        """
        Handle the retrieval of the sender's data.

        :param dclass: The data class of the sender.
        :param fields: The fields of the sender.
        """
        success, senderFriendsList = self.__handleRemoveFriend(dclass, fields, self.friendId)
        if success:
            self.senderFriendsList = senderFriendsList
            self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, self.friendId,
                                                            self.__handleFriendRetrieved)

    def __handleFriendRetrieved(self, dclass, fields):
        """
        Handle the retrieval of the friend's data.

        :param dclass: The data class of the friend.
        :param fields: The fields of the friend.
        """
        success, friendFriendsList = self.__handleRemoveFriend(dclass, fields, self.sender)
        if success:
            self.friendFriendsList = friendFriendsList
            self._handleDone()

    def __handleSetFriendsList(self, avId, friendsList):
        """
        Handle setting the friends list for an avatar.

        :param avId: The avatar ID.
        :param friendsList: The updated friends list.
        """
        if avId in self.onlineToons:
            self.friendsManager.sendUpdateToAvatar(avId, 'setFriendsList', [friendsList])
        else:
            self.friendsManager.air.dbInterface.updateObject(self.friendsManager.air.dbId, avId,
                                                             self.friendsManager.air.dclassesByName[
                                                                 'DistributedToonUD'],
                                                             {'setFriendsList': [friendsList]})

    def _handleDone(self):
        """
        Handle the completion of the operation.
        """
        if self.senderFriendsList is not None and self.friendFriendsList is not None:
            self.__handleSetFriendsList(self.sender, self.senderFriendsList)
            self.__handleSetFriendsList(self.friendId, self.friendFriendsList)

        if self.sender in self.onlineToons and self.friendId in self.onlineToons:
            self.friendsManager.undeclareObject(self.sender, self.friendId)
            self.friendsManager.undeclareObject(self.friendId, self.sender)

        if self.friendId in self.onlineToons:
            self.friendsManager.sendUpdateToAvatar(self.friendId, 'friendsNotify', [self.sender, 1])

        FriendsOperation._handleDone(self)


class ComingOnlineOperation(FriendsOperation):
    """
    Operation to handle an avatar coming online.
    """

    def __init__(self, friendsManager):
        """
        Initialize the ComingOnlineOperation.

        :param friendsManager: The friends manager instance.
        """
        FriendsOperation.__init__(self, friendsManager, None)
        self.avId = None
        self.friendsList = None
        self.currentFriendIdx = None

    def start(self, avId, friendsList):
        """
        Start the operation to handle an avatar coming online.

        :param avId: The avatar ID.
        :param friendsList: The friends list of the avatar.
        """
        self.avId = avId
        self.friendsList = friendsList
        self.__checkFriendsOnline()

    def __checkFriendsOnline(self):
        """
        Check which friends are currently online.
        """
        self.currentFriendIdx = 0
        for friendId in self.friendsList:
            self.friendsManager.air.getActivated(friendId, self.__gotFriendActivated)

    def __gotFriendActivated(self, avId, activated):
        """
        Handle the response of checking if a friend is activated.

        :param avId: The avatar ID.
        :param activated: Whether the friend is activated.
        """
        self.currentFriendIdx += 1
        if activated:
            self.friendsManager.declareObject(avId, self.avId)
            self.friendsManager.declareObject(self.avId, avId)
            self.friendsManager.sendFriendOnline(avId, self.avId, 0, 1)

        if self.currentFriendIdx >= len(self.friendsList):
            self._handleDone()


class GoingOfflineOperation(FriendsOperation):
    """
    Operation to handle an avatar going offline.
    """

    def __init__(self, friendsManager):
        """
        Initialize the GoingOfflineOperation.

        :param friendsManager: The friends manager instance.
        """
        FriendsOperation.__init__(self, friendsManager, None)
        self.avId = None
        self.friendsList = None
        self.accId = None
        self.currentFriendIdx = None

    def start(self, avId):
        """
        Start the operation to handle an avatar going offline.

        :param avId: The avatar ID.
        """
        self.avId = avId
        self.friendsList = []
        self.accId = 0
        self.friendsManager.air.dbInterface.queryObject(self.friendsManager.air.dbId, self.avId, self.__handleAvatarRetrieved)

    def __handleAvatarRetrieved(self, dclass, fields):
        """
        Handle the retrieval of the avatar's data.

        :param dclass: The data class of the avatar.
        :param fields: The fields of the avatar.
        """
        if dclass != self.friendsManager.air.dclassesByName['DistributedToonUD']:
            self._handleError('Retrieved avatar is not a DistributedToonUD!')
            return

        self.friendsList = fields['setFriendsList'][0]
        self.accId = fields['setDISLid'][0]
        self.__checkFriendsOnline()

    def __checkFriendsOnline(self):
        """
        Check which friends are currently online.
        """
        self.currentFriendIdx = 0
        for friendId, _ in self.friendsList:
            self.friendsManager.air.getActivated(friendId, self.__gotFriendActivated)

    def __gotFriendActivated(self, avId, activated):
        """
        Handle the response of checking if a friend is activated.

        :param avId: The avatar ID.
        :param activated: Whether the friend is activated.
        """
        self.currentFriendIdx += 1
        if activated:
            self.friendsManager.undeclareObject(avId, self.avId)
            self.friendsManager.undeclareObject(self.accId, avId, isAccount=True)
            self.friendsManager.sendFriendOffline(avId, self.avId)

        if self.currentFriendIdx >= len(self.friendsList):
            self._handleDone()

class GenerateSecretOperation(FriendsOperation):
    """
    Operation to generate a secret.
    """

    def __init__(self, friendsManager):
        """
        Initialize the GenerateSecretOperation.

        :param friendsManager: The friends manager instance.
        :param requesterId: The requester's ID.
        """
        FriendsOperation.__init__(self, friendsManager, None)
        self.secret = None
        self.requesterId = None

    def start(self, requesterId):
        """
        Start the operation to generate a secret.
        Format of secret:
        TT 3 random letters/numbers 3 random letters/numbers
        """
        self.requesterId = requesterId
        self.friendsManager.loadSecretsDB()
        # check if too many secrets
        # TODO
        self.secret = ''
        for i in range(3):
            self.secret += random.choice(string.ascii_letters + string.digits)
        self.secret += ' '
        for i in range(3):
            self.secret += random.choice(string.ascii_letters + string.digits)

        self.friendsManager.secrets[self.secret] = requesterId
        self._handleDone()

    def _handleDone(self):
        """
        Handle the completion of the operation.
        """
        FriendsOperation._handleDone(self)
        self.friendsManager.updateSecretsDB()
        # send the response to the requester that it was a success, the result and the secret
        self.friendsManager.sendRequestSecretResponse(self.requesterId, 1, self.secret)


    def _handleError(self, error):
        """
        Handle an error during the operation.

        :param error: The error message.
        """
        FriendsOperation._handleError(self, error)
        # send the response to the requester that it was a failure, the result and the secret
        self.friendsManager.sendRequestSecretResponse(self.requesterId, 0, '')
    
class ToontownFriendsManagerUD(DistributedObjectGlobalUD):
    """
    The main friends manager class for Toontown.
    """
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownFriendsManagerUD')

    def __init__(self, air):
        """
        Initialize the ToontownFriendsManagerUD.

        :param air: The AI repository instance.
        """
        DistributedObjectGlobalUD.__init__(self, air)
        self.secret = None
        self.operations = []
        self.secrets = {}

    def sendMakeFriendsResponse(self, avatarAId, avatarBId, result, context):
        """
        Send the response for making friends.

        :param avatarAId: The first avatar's ID.
        :param avatarBId: The second avatar's ID.
        :param result: The result of the operation.
        :param context: The context of the operation.
        """
        self.sendUpdate('makeFriendsResponse', [avatarAId, avatarBId, result, context])

    def declareObject(self, doId, objId):
        """
        Declare an object to the client.

        :param doId: The distributed object ID.
        :param objId: The object ID.
        """
        datagram = PyDatagram()
        datagram.addServerHeader(self.GetPuppetConnectionChannel(doId), self.air.ourChannel, CLIENTAGENT_DECLARE_OBJECT)
        datagram.addUint32(objId)
        datagram.addUint16(self.air.dclassesByName['DistributedToonUD'].getNumber())
        self.air.send(datagram)

    def undeclareObject(self, doId, objId, isAccount=False):
        """
        Undeclare an object to the client.

        :param doId: The distributed object ID.
        :param objId: The object ID.
        :param isAccount: Whether the object is an account.
        """
        datagram = PyDatagram()
        if isAccount:
            datagram.addServerHeader(self.GetAccountConnectionChannel(doId), self.air.ourChannel,
                                     CLIENTAGENT_UNDECLARE_OBJECT)

        else:
            datagram.addServerHeader(self.GetPuppetConnectionChannel(doId), self.air.ourChannel,
                                     CLIENTAGENT_UNDECLARE_OBJECT)
        datagram.addUint32(objId)
        self.air.send(datagram)

    def sendFriendOnline(self, avId, friendId, commonChatFlags, whitelistChatFlags):
        """
        Notify that a friend has come online.

        :param avId: The avatar ID.
        :param friendId: The friend's ID.
        :param commonChatFlags: The common chat flags.
        :param whitelistChatFlags: The whitelist chat flags.
        """
        self.sendUpdateToAvatarId(avId, 'friendOnline', [friendId, commonChatFlags, whitelistChatFlags])

    def sendFriendOffline(self, avId, friendId):
        """
        Notify that a friend has gone offline.

        :param avId: The avatar ID.
        :param friendId: The friend's ID.
        """
        self.sendUpdateToAvatarId(avId, 'friendOffline', [friendId])

    def sendUpdateToAvatar(self, avId, fieldName, args=[]):
        """
        Send an update to an avatar.

        :param avId: The avatar ID.
        :param fieldName: The field name to update.
        :param args: The arguments for the update.
        """
        dclass = self.air.dclassesByName['DistributedToonUD']
        if not dclass:
            return

        field = dclass.getFieldByName(fieldName)
        if not field:
            return

        datagram = field.aiFormatUpdate(avId, avId, self.air.ourChannel, args)
        self.air.send(datagram)

    def runSenderOperation(self, operationType, *args):
        """
        Run an operation initiated by the sender.

        :param operationType: The type of operation.
        :param args: The arguments for the operation.
        """
        sender = self.air.getAvatarIdFromSender()
        if not sender:
            return

        newOperation = operationType(self, sender)
        self.operations.append(newOperation)
        newOperation.start(*args)

    def runServerOperation(self, operationType, *args):
        """
        Run an operation initiated by the server.

        :param operationType: The type of operation.
        :param args: The arguments for the operation.
        """
        newOperation = operationType(self)
        self.operations.append(newOperation)
        newOperation.start(*args)

    def getFriendsListRequest(self):
        """
        Handle a request to get the friends list.
        """
        self.runSenderOperation(GetFriendsListOperation)

    def getAvatarDetailsRequest(self, avId):
        """
        Handle a request to get avatar details.

        :param avId: The avatar ID.
        """
        self.runSenderOperation(GetAvatarDetailsOperation, avId)

    def makeFriends(self, avatarAId, avatarBId, flags, context):
        """
        Handle a request to make two avatars friends.

        :param avatarAId: The first avatar's ID.
        :param avatarBId: The second avatar's ID.
        :param flags: The friendship flags.
        :param context: The context of the operation.
        """
        self.runServerOperation(MakeFriendsOperation, avatarAId, avatarBId, flags, context)

    def removeFriend(self, friendId):
        """
        Handle a request to remove a friend.

        :param friendId: The friend's ID.
        """
        self.runSenderOperation(RemoveFriendOperation, friendId)

    def requestSecret(self, requesterId):
        """
        Handle a request to generate a secret.

        """
        self.runServerOperation(GenerateSecretOperation, requesterId)

    def submitSecret(self, avId, secret):
        """
        Handle a request to submit a secret.

        :param avId: The avatar ID.
        :param secret: The secret.
        """
        self.loadSecretsDB()
        recipient = self.secrets.get(secret, None)
        if recipient:
            self.runServerOperation(MakeFriendsOperation, avId, recipient, 0, 0)
            self.sendSubmitSecretResponse(avId, 1, recipient)
        else:
            self.sendSubmitSecretResponse(avId, 0, recipient)

    def sendSubmitSecretResponse(self, requesterId, success, recipient):
        """
        Send a response to a secret submission.

        :param requesterId: The requester's ID.
        :param success: Whether the operation was successful.
        :param secret: The secret.
        :param recipient: The recipient's ID.
        """
        self.sendUpdate('submitSecretResponse', [success, recipient, requesterId])

    def comingOnline(self, avId, friendsList):
        """
        Handle a request for an avatar coming online.

        :param avId: The avatar ID.
        :param friendsList: The friends list of the avatar.
        """
        self.runServerOperation(ComingOnlineOperation, avId, friendsList)

    def goingOffline(self, avId):
        """
        Handle a request for an avatar going offline.

        :param avId: The avatar ID.
        """
        self.runServerOperation(GoingOfflineOperation, avId)

    def sendRequestSecretResponse(self, requesterId, success, secret):
        """
        Send a response to a secret request.

        :param requesterId: The requester's ID.
        :param success: Whether the operation was successful.
        :param secret: The generated secret.
        """
        self.sendUpdate('requestSecretResponse', [success, secret, requesterId])


    def updateSecretsDB(self):
        with open('astron/databases/secrets.json', 'w') as f:
            json.dump(self.secrets, f)
        self.notify.debug('Updated secrets database')

    def loadSecretsDB(self):
        try:
            with open('astron/databases/secrets.json', 'r') as f:
                self.secrets = json.load(f)
            self.notify.debug('Loaded secrets database')
        except:
            self.notify.warning('Failed to load secrets database')
        
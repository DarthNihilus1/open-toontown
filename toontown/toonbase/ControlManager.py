from direct.directnotify import DirectNotifyGlobal
from direct.showbase.DirectObject import DirectObject

from toontown.toonbase import ToontownGlobals

import string
from otp.otpbase import OTPLocalizer


class ControlManager(DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('ControlManager')

    def __init__(self):
        DirectObject.__init__(self)
        self.changing = False
        self.disableChat = 1
        self.disabledHotkeys = []
        self.activeHotkeys = []
        self.changedHotkeys = {ToontownGlobals.HotkeyGroup: []}
        self.disableAlphaNumericHotkeys = False
        self.reloadHotkeys(True)
        

    def reloadHotkeys(self, realtime=False):
        self.ignoreAll()
        disableChat = 1
        activeHotkeys = []
        controlCategory = base.settings.getSetting('controls', {})
        if controlCategory is None:
            controlCategory = {}
            
        for key in controlCategory.keys():
            hotkey = controlCategory.get(key)
            alphaNumeric = self.isAlphaNumericHotkey(hotkey)
            if disableChat and alphaNumeric:
                disableChat = 0
            if ToontownGlobals.HotkeyGroupDefaults.get(key) != hotkey:
                changedHotkeys = self.changedHotkeys.get('HotKeys')
                changedHotkeys.append(key)
                self.changedHotkeys[0] = changedHotkeys
            activeHotkeys.append(hotkey)
            self.accept(hotkey, self.hotkeyPressed, extraArgs=[self.getHotkeyName('HotKeys', key), hotkey, key])
            self.accept(hotkey + '-up', self.hotkeyPressed, extraArgs=[self.getHotkeyName('HotKeys', key, True), hotkey, key])

        self.activeHotkeys = activeHotkeys

        controlCategory = base.settings.getSetting('controls', {})
        if controlCategory is None:
            controlCategory = {}
        for key in controlCategory.keys():
            hotkey = controlCategory.get(key)
            for bonus in ('shift', 'control', 'alt'):
                failSafeKey = bonus + ToontownGlobals.Separater + hotkey
                if not hotkey.startswith(str(key)) and failSafeKey not in activeHotkeys:
                    self.accept(failSafeKey, self.hotkeyPressed, extraArgs=[self.getHotkeyName(ToontownGlobals.HotkeyGroup, key), hotkey, key])
                    self.accept(failSafeKey + '-up', self.hotkeyPressed, extraArgs=[self.getHotkeyName(ToontownGlobals.HotkeyGroup, key, True), hotkey, key])

        self.disableChat = disableChat

        if hasattr(base, 'localAvatar') and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
            base.localAvatar.chatMgr.setBackgroundFocus(disableChat)
            if not disableChat:
                base.localAvatar.chatMgr.chatLog.enableHotkey()
            else:
                base.localAvatar.chatMgr.chatLog.disableHotkey()
        
    def getHotkeyName(self, category, id, released=False):
        hotkey = 'hotkey-' + category + '-' + str(id)
        if released:
            hotkey += '-up'
        return hotkey

    def setChanging(self, state):
        self.changing = state

    def getChanging(self):
        return self.changing

    def getKeyName(self, category, id):
        """
        Gets the key name based on the category  specified and the id specified 
        you can find these in ToontownGlobals  under the  "New Hotkeys globals " comment
        categories: 'movement' and interaction
        ids: 0-10 
        """
        #Might be a better way of doing this but for now this is what I came up with
        names = OTPLocalizer.HotkeyNames[0]

        hotkeys = ToontownGlobals.HotkeyGroupDefaults.keys()
        controlCategory = base.settings.getSetting('controls', {})
        if controlCategory is None:
            controlCategory = {}
        for hotkey in hotkeys:
            if hotkey == id:
                hotkeyName = names.get(hotkey)
                
                if controlCategory.get(str(hotkey)) is not None:
                #If we have the keys in settings
                    keyName = controlCategory.get(str(hotkey).lower())
                    break
                else:
                #Get the default keys defined in toontownglobals
                    keyName = ToontownGlobals.HotkeyGroupDefaults.get(hotkey).lower()
                    break

        if keyName is None:
            self.notify.warning(f"Key name is None. Category : {category} hotkey: {hotkeyName}")
        return keyName

    def hotkeyPressed(self, hotkeyName, hotkey, key, event=None):
        if not self.getChanging() and int(key) not in self.disabledHotkeys:
            if self.disableAlphaNumericHotkeys:
                if 'enter' in hotkey:
                    messenger.send('exitChat')
                    return
                elif not self.isAlphaNumericHotkey(hotkey):
                    messenger.send(hotkeyName)
                elif hotkeyName.endswith('-up'):
                    messenger.send(hotkeyName)
                else:
                    return
            messenger.send(hotkeyName)

    def getControlName(self, name, label=False):
        """
        Adds a seperator to the name of the control specified and adds any special keys.
        Also gives it a title format 
        """
        if ToontownGlobals.Separater in name:
            name = name.replace(ToontownGlobals.Separater, ' + ')

        for key in ToontownGlobals.SpecialKeys.keys():
            if key in name:
                value = ToontownGlobals.SpecialKeys.get(key)
                name = name.replace(key, value)
                break
        name = name.title()

        if label:
            name += ' Key'
            if '+' in name:
                name += 's'
        return name

    def convertHotkeyString(self, dialog, activator):
        for x in range(dialog.count(activator)):
            split = dialog.split(activator, 1)
            first = split[0][:-1]
            info = split[1]
            category = int(info[:2])
            index = int(info[2:4])
            controlCategory = base.settings.getSetting('controls', {})
            hotkey = self.getControlName(controlCategory.get(str(index)), True)
            dialog = first + hotkey + info[4:]

        return dialog

    def isAlphaNumericHotkey(self, hotkey):
        hotkey = str(hotkey)
        for prefix in ('shift', 'control', 'alt'):
            if prefix in hotkey:
                hotkey = hotkey.replace(prefix, '')
                if ToontownGlobals.Separater in hotkey:
                    hotkey = hotkey.replace(ToontownGlobals.Separater, '')
                else:
                    return False

        if len(hotkey) > 1:
            if hotkey == 'space':
                return True
            return False

        characters = string.printable
        if hotkey in characters:
            return True

        return False

    def getChatDisabled(self):
        return self.disableChat

    def addDisabledHotkey(self, hotkey):
        if hotkey not in self.disabledHotkeys:
            self.disabledHotkeys.append(hotkey)

    def removeDisabledHotkey(self, hotkey):
        if hotkey in self.disabledHotkeys:
            self.disabledHotkeys.remove(hotkey)

    def getKeyInUse(self, hotkey):
        for key in self.activeHotkeys:
            if hotkey in key:
                return True
        return False

    def getChangedHotkeys(self):
        return self.changedHotkeys
from direct.gui.DirectGui import *
from direct.directnotify import DirectNotifyGlobal

from otp.otpbase import OTPLocalizer

from panda3d.core import *

from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals

class ControlSettingsDialog(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('ControlSettingsDialog')

    def __init__(self):
        DirectFrame.__init__(self, pos=(0, 0, 0.3), relief=None, image=DGG.getDefaultDialogGeom(),
                             image_scale=(1.6, 1, 1.2), image_pos=(0, 0, -0.05),
                             image_color=ToontownGlobals.GlobalDialogColor, text=TTLocalizer.ControlSettingsTitle,
                             text_scale=0.12, text_pos=(0, 0.4), borderWidth=(0.01, 0.01))
        self.setBin('gui-popup', 0)
        self.initialiseoptions(ControlSettingsDialog)
        self.keyButtons = []
        self.controls = {}
        self.queuedKey = None
        self.button = None
        self.load()

        self.enter()
        return

    def unload(self):
        self.exit()
        DirectFrame.destroy(self)
        return None

    def load(self):
        guiButton = loader.loadModel('phase_3/models/gui/quit_button')
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        nameShopGui = loader.loadModel('phase_3/models/gui/nameshop_gui')
        circleModel = loader.loadModel('phase_3/models/gui/tt_m_gui_mat_nameShop')
        scrollBkgd = OnscreenImage(image='phase_3/maps/slider.png')
        scrollBkgd.setTransparency(TransparencyAttrib.MAlpha)
        self.apply = DirectButton(parent=self, relief=None, image=(guiButton.find('**/QuitBtn_UP'),
                                                                   guiButton.find('**/QuitBtn_DN'),
                                                                   guiButton.find('**/QuitBtn_RLVR')),
                                  image_scale=(0.6, 1, 1), text=TTLocalizer.DisplaySettingsApply, text_scale=0.06,
                                  text_pos=(0, -0.02), pos=(-0.55, 0, -0.53), command=self.__apply)
        self.cancel = DirectButton(parent=self, relief=None, text=TTLocalizer.ControlSettingsExit,
                                   image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'),
                                          guiButton.find('**/QuitBtn_RLVR')),
                                   image_scale=(0.6, 1, 1), text_scale=TTLocalizer.DSDcancel,
                                 text_pos=TTLocalizer.DSDcancelPos, pos=(-0.1, 0, -0.53), command=self.__cancel)
        
        self.resetToDefaults = DirectButton(parent=self, relief=None, text=TTLocalizer.ControlSettingsResetToDefault,
                                   image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'),
                                          guiButton.find('**/QuitBtn_RLVR')),
                                   image_scale=(1.5, 1, 1), text_scale=TTLocalizer.DSDcancel ,
                                   text_pos=TTLocalizer.DSDcancelPos , pos=(0.42, 0, -0.53), command=self.__resetToDefault)

        self.infoLabel = DirectLabel(parent=self, relief=None, text=TTLocalizer.ControlSettingsInfoLabelDefault,
                                     text_scale=TTLocalizer.CSButton , text_pos=TTLocalizer.DSDcancelPos,
                                     pos=(0, 0, 0.29))
        self.hotkeysList = DirectScrolledFrame(parent=self, frameSize=(-0.65, 0.65, -0.4, 0.2), relief=DGG.SUNKEN,
                                               geom=scrollBkgd, geom_scale=(0.3, 1, 0.025), geom_pos=(0.6, 0, -0.1),
                                               geom_hpr=(0, 0, 90), borderWidth=(0.01, 0.01),
                                               frameColor=(0.85, 0.95, 1, 1), manageScrollBars=True,
                                               autoHideScrollBars=True, canvasSize=(-1, 0, -2, 1))
        self.hotkeysList.verticalScroll['relief'] = None
        self.hotkeysList.verticalScroll['frameTexture'] = None
        self.hotkeysList.verticalScroll.incButton['relief'] = None
        self.hotkeysList.verticalScroll.decButton['relief'] = None
        self.hotkeysList.verticalScroll.thumb['geom'] = circleModel.find('**/tt_t_gui_mat_namePanelCircle')
        self.hotkeysList.verticalScroll['resizeThumb'] = False
        self.hotkeysList.verticalScroll.incButton.reparentTo(hidden)
        self.hotkeysList.verticalScroll.decButton.reparentTo(hidden)
        canvas = self.hotkeysList.getCanvas()
        posX = -0.88
        xOffset = 0.35
        #button = DirectButton(parent=self, relief=None, text=OTPLocalizer.HotkeyCategoryNames.get("HotKeys"),
           #                       image=(guiButton.find('**/QuitBtn_RLVR'), guiButton.find('**/QuitBtn_RLVR'),
            #                             guiButton.find('**/QuitBtn_RLVR')),
             #                     image_scale=(0.6, 1, 1), text_scale=TTLocalizer.CSButton,
              #                    text_pos=TTLocalizer.DSDcancelPos, pos=(posX + (xOffset * 1), 0, 0.3),
               #                   command=self.__changeCategory, extraArgs=[index])
            #self.categoryButtons.append(button)
        node = canvas.attachNewNode('category-%s' % 0)
        node.setPos(-0.95, 0, 0.75)
        names = OTPLocalizer.HotkeyNames[0]
        posZ = 0.15
        zOffset = -0.15
        num = 0
        hotkeys = ToontownGlobals.HotkeyGroupDefaults.keys()
        controlSettings = base.settings.getSetting('controls', {})
       # if controlCategory is None:
            #controlCategory = {}
        self.controls = controlSettings
        for hotkey in hotkeys:
            hotkeyName = names.get(hotkey)
            if not hotkeyName:
                continue
            if controlSettings.get(str(hotkey)) is not None:
                #If we have the keys in settings
                keyName = base.controlManager.getControlName(controlSettings.get(str(hotkey)))
            else:
                #Get the default keys defined in toontownglobals
                    keyName = base.controlManager.getControlName(ToontownGlobals.HotkeyGroupDefaults.get(hotkey))
            DirectLabel(parent=node, relief=None, text=hotkeyName, text_align=TextNode.ALeft,
                        text_scale=TTLocalizer.CSButton, text_pos=TTLocalizer.DSDcancelPos,
                        pos=(0, 0, posZ + (zOffset * num)))
            button = DirectButton(parent=node, relief=None, image=(guiButton.find('**/QuitBtn_UP'),
                                                                    guiButton.find('**/QuitBtn_DN'),
                                                                    guiButton.find('**/QuitBtn_RLVR')),
                                    image_scale=(0.6, 1, 1), text=keyName, text_scale=TTLocalizer.CSKeyButton,
                                    text_pos=TTLocalizer.DSDcancelPos, pos=(0.8, 0, posZ - 0.025 + (zOffset * num)))
            button.bind(DGG.B1RELEASE, self.__changeKey, extraArgs=[hotkey])
            self.keyButtons.append((hotkey, button))
            num += 1


        guiButton.removeNode()
        gui.removeNode()
        nameShopGui.removeNode()
        circleModel.removeNode()
        scrollBkgd.destroy()
        self.hide()
        return

    def enter(self):
        base.controlManager.setChanging(True)
        base.transitions.fadeScreen(0.5)
        if hasattr(base, 'localAvatar') and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
            base.localAvatar.chatMgr.setBackgroundFocus(False)
        self.show()
        return

    def exit(self):
        base.controlManager.setChanging(False)
        base.transitions.noTransitions()
        #if hasattr(base, 'localAvatar') and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
            #base.localAvatar.chatMgr.setBackgroundFocus(base.localAvatar.chatMgr.wantBackgroundFocus, True)
        self.infoLabel['text'] = TTLocalizer.ControlSettingsInfoLabelDefault
        if self.button:
            self.button.clearColorScale()
            self.button = None
        self.ignoreAll()
        self.hide()
        return None

    def __apply(self):
        self.applyChanges()
        self.infoLabel['text'] = TTLocalizer.ControlSettingsChangesApplied

    def __cancel(self):
        self.exit()

    def __resetToDefault(self):
        base.settings.updateSetting('controls', {})
        base.settings.writeSettings()
        self.controls = {}
        base.controlManager.reloadHotkeys()
        base.reloadControls()
        base.localAvatar.controlManager.reload()
        base.localAvatar.controlManager.disable()


    def __changeKey(self, id, event):
        self.ignoreAll()
        if self.button:
            self.button.clearColorScale()

        self.infoLabel['text'] = TTLocalizer.ControlSettingsInfoLabelChangeKey

        self.button = self.getButton(id)
        self.button.setColorScale(1, 0.2, 0.2, 1)

        event = 'pressButton'
        base.buttonThrowers[0].node().setButtonDownEvent(event)
        self.acceptOnce(event, self.pressedButton, [self.button, id])

        event = 'releaseButton'
        base.buttonThrowers[0].node().setButtonUpEvent(event)
        self.acceptOnce(event, self.releasedButton, [self.button, id])

    def getButton(self, id):
        for button in self.keyButtons:
            if button[0] == id:
                break
        return button[1]

    def pressedButton(self, button, id, key):
        if key[1:] in ('shift', 'control', 'alt') and (key.startswith('l') or key.startswith('r')):
            event = 'pressButton'
            self.acceptOnce(event, self.pressedButton, [button, id])
            return
        if key in ('shift', 'control', 'alt'):
            self.queuedKey = key
            event = 'pressButton'
            self.acceptOnce(event, self.pressedButton, [button, id])
        elif self.queuedKey:
            self.ignore('releaseButton')
            self.releasedButton(button, id, key)

    def releasedButton(self, button, id, key):
        if key[1:] in ('shift', 'control', 'alt') and (key.startswith('l') or key.startswith('r')):
            return

        if key in ('shift', 'control', 'alt'):
            self.queuedKey = None

        activeHotkeys = self.getActiveHotkeys()
        if key in activeHotkeys or 'mouse' in key:
            message = TTLocalizer.ControlSettingsAlreadyInUse
            if 'mouse' in key or 'wheel' in key:
                message = TTLocalizer.ControlSettingsInfoLabelChangeKey
            self.infoLabel['text'] = message

            event = 'pressButton'
            self.acceptOnce(event, self.pressedButton, [button, id])

            event = 'releaseButton'
            self.acceptOnce(event, self.releasedButton, [button, id])
            return

        self.controls[str(id)] = key

        self.infoLabel['text'] = TTLocalizer.ControlSettingsSuccessful

        button.clearColorScale()
        button['text'] = base.controlManager.getControlName(key)

    def getActiveHotkeys(self):
        hotkeys = []
        for hotkey in self.controls.values():
            hotkeys.append(hotkey)
        return hotkeys

    def applyChanges(self):
        base.settings.updateSetting('controls', self.controls)
        base.settings.writeSettings()
        base.controlManager.reloadHotkeys()
        base.localAvatar.controlManager.reload()
        base.reloadControls()
        base.localAvatar.controlManager.disable()


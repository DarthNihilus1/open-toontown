from panda3d.core import *
from direct.gui.DirectGui import *
from otp.otpbase import OTPLocalizer, OTPGlobals
from toontown.shtiker.OptionsPage import speedChatStyles
from toontown.toonbase import ToontownGlobals, TTLocalizer
from panda3d.otp import NametagGlobals
from otp.speedchat.ColorSpace import *
from direct.showbase.PythonUtil import makeTuple
from panda3d.otp import WhisperPopup


class ChatLog(DirectButton):
    notify = directNotify.newCategory('ChatLog')

    def __init__(self, chatMgr, **kwargs):
        self.chatMgr = chatMgr
        gui = loader.loadModel('phase_3/models/gui/ChatPanel')
        self.wantGuildChat = ConfigVariableBool('want-guild-chat', False)

        def findNodes(names, model = gui):
            results = []
            for name in names:
                for nm in makeTuple(name):
                    node = model.find('**/%s' % nm)
                    if not node.isEmpty():
                        results.append(node)
                        break

            return results

        def scaleNodes(nodes, scale):
            bgTop, bgBottom, bgLeft, bgRight, bgMiddle, bgTopLeft, bgBottomLeft, bgTopRight, bgBottomRight = nodes
            bgTopLeft.setSx(aspect2d, scale)
            bgTopLeft.setSz(aspect2d, scale)
            bgBottomRight.setSx(aspect2d, scale)
            bgBottomRight.setSz(aspect2d, scale)
            bgBottomLeft.setSx(aspect2d, scale)
            bgBottomLeft.setSz(aspect2d, scale)
            bgTopRight.setSx(aspect2d, scale)
            bgTopRight.setSz(aspect2d, scale)
            bgTop.setSz(aspect2d, scale)
            bgBottom.setSz(aspect2d, scale)
            bgLeft.setSx(aspect2d, scale)
            bgRight.setSx(aspect2d, scale)

        nodes = findNodes([('top', 'top1'), 'bottom', 'left', 'right', 'middle', 'topLeft', 'bottomLeft', 'topRight',
                           'bottomRight'])
        scaleNodes(nodes, 0.25)

        args = {'parent': self.chatMgr.chatLogNode, 'relief': None, 'geom': gui, 'geom_scale': (1, 1, 0.55),
                'sortOrder': DGG.FOREGROUND_SORT_INDEX}
        kwargs.update(args)
        DirectButton.__init__(self, **kwargs)
        self.initialiseoptions(ChatLog)

        scaleNodes(nodes, 0.45)
        buttonRowOffset = 0.25
        centerOffset = 0.035
        self.currentTab = 0
        self.chatTabs = []
        self.wantGlobalChat = ConfigVariableBool('want-global-chat', False)
        mainTab = DirectButton(parent=self, relief=None, geom=gui, geom_scale=(1.2, 1, 0.55), text=TTLocalizer.ChatLogTabMain,
                               text_scale=0.25, text_pos=(0.6, -0.3, 0.0), scale=0.15, pos=(centerOffset, 0.0, 0.09),
                               command=self.__toggleButton, extraArgs=[0])
        whisperTab = DirectButton(parent=self, relief=None, geom=gui, geom_scale=(1.2, 1, 0.55), text=TTLocalizer.ChatLogTabWhispers,
                                  text_scale=0.25, text_pos=(0.6, -0.3, 0.0), text_fg=(0, 0, 0, 0.5), scale=0.15,
                                  pos=(buttonRowOffset + centerOffset, 0.0, 0.09), command=self.__toggleButton, extraArgs=[1])
        systemTab = DirectButton(parent=self, relief=None, geom=gui, geom_scale=(1.2, 1, 0.55), text=TTLocalizer.ChatLogTabSystem,
                                 text_scale=0.25, text_pos=(0.6, -0.3, 0.0), text_fg=(0, 0, 0, 0.5), scale=0.15,
                                 pos=((buttonRowOffset * 3) + centerOffset, 0.0, 0.09), command=self.__toggleButton)
        if self.wantGlobalChat:
            globalTab = DirectButton(parent=self, relief=None, geom=gui, geom_scale=(1.2, 1, 0.55), text=TTLocalizer.ChatLogTabGlobal,
                                 text_scale=0.25, text_pos=(0.6, -0.3, 0.0), text_fg=(0, 0, 0, 0.5), scale=0.15,
                                 pos=((buttonRowOffset * 2) + centerOffset, 0.0, 0.09), command=self.__toggleButton, extraArgs=[2])
            systemTab['extraArgs'] = [3]

        else:
            systemTab['extraArgs'] = [2]

        self.chatTabs.append(mainTab)
        self.chatTabs.append(whisperTab)
        if self.wantGlobalChat:
            self.chatTabs.append(globalTab)
        self.chatTabs.append(systemTab)

        self.logs = []
        self.realLogs = []
        self.currents = []
        self.texts = []
        self.textNodes = []
        self.notificationBubbles = []
        # Generate the stuff for each tab
        for x in range(len(self.chatTabs)):
            chatTab = self.chatTabs[x]
            chatTabPos = chatTab.getPos()
            chatTab.flattenStrong()
            chatTab.wrtReparentTo(self.chatMgr.chatLogNode)
            log = []
            realLog = []
            current = 0
            text = TextNode('text')
            text.setWordwrap(23.5)
            text.setAlign(TextNode.ALeft)
            text.setTextColor(0, 0, 0, 1)
            text.setFont(ToontownGlobals.getToonFont())
            textNode = self.attachNewNode(text, 0)
            textNode.setPos(0.0, 0.0, -0.05)
            textNode.setScale(0.04)
            notificationBubble = DirectLabel(self, relief=None, scale=0.075, pos=chatTabPos, text='0', text_pos=(2.0, 0.0, 0.0), text_fg=(1, 0, 0, 1), text_shadow=(0, 0, 0, 1))
            notificationBubble.hide()
            self.logs.append(log)
            self.realLogs.append(realLog)
            self.currents.append(current)
            self.texts.append(text)
            self.textNodes.append(textNode)
            self.notificationBubbles.append(notificationBubble)

        self.guildHint = None
        scaleNodes(nodes, 0.25)
        if self.wantGuildChat:
            self.guildEntry = DirectEntry(self, relief=None, state=DGG.NORMAL, geom=gui, geom_scale=(1, 1, 0.085),
                                          text_scale=0.045, text_pos=(0.0, -0.05, 0.0), pos=(0.0, 0.0, -0.575),
                                          numLines=1, width=20.0, cursorKeys=False)

            self.guildEntry.setTransparency(True)
            self.guildEntry.bind(DGG.OVERFLOW, self.sendGuildChat)
            self.guildEntry.bind(DGG.TYPE, self.typeCallback)
            self.guildEntry.bind(DGG.ERASE, self.typeCallback)
            self.guildEntry.bind(DGG.ENTER, self.enterCallback)
            self.guildEntry.bind(DGG.EXIT, self.exitCallback)
            self.accept('enter', self.sendGuildChat)
        else:
            self.guildEntry = None

        # TODO: Temporary
        self.resetGuildHint()

        gui.removeNode()

        self.autoScroll = True
        self.closed = False

        # Left clicking the Chat Log will drag it around the screen
        self.bind(DGG.B1PRESS, self.dragStart)
        self.bind(DGG.B1RELEASE, self.dragStop)

        # Right clicking the Chat Log will scale it up and down
        self.bind(DGG.B3PRESS, self.scaleStart)
        self.bind(DGG.B3RELEASE, self.scaleStop)

        # Middle mouse button will go through the allowed opacities
        self.bind(DGG.B2PRESS, self.opacityStart, extraArgs=[True])
        self.bind(DGG.B2RELEASE, self.opacityStart, extraArgs=[False])

        self.accept('addChatHistory', self.__addChatHistory)
        self.accept('SpeedChatStyleChange', self.__updateSpeedChatStyle)
        self.__toggleButton(0)

        self.hotkey = None

        self.opacity = 0.5
        self.closeChatlog()

    def setGuildHint(self, hintText):
        return
        if not self.guildEntry:
            return

        self.guildEntry.set(hintText)
        self.guildEntry.setCursorPosition(0)
        self.guildHint = hintText

    def resetGuildHint(self):
        return
        self.setGuildHint(TTLocalizer.ChatLogSendToGuild)

    def sendGuildChat(self, *args):
        if not self.guildEntry:
            return
        if self.guildHint:
            return

        message = self.guildEntry.get(plain=True).strip()
        self.resetGuildHint()

        if message:
            base.talkAssistant.sendGuildTalk(message)

        self.guildEntry['focus'] = 1

    def typeCallback(self, *args):
        message = self.guildEntry.get(plain=True)

        if self.guildHint and message != self.guildHint:
            message = message.replace(self.guildHint, '')
            self.guildHint = None

        if base.whiteList:
            message = base.whiteList.processThroughAll(message)

        if message:
            self.guildEntry.set(message)
        else:
            self.resetGuildHint()

    def enterCallback(self, *args):
        self.chatMgr.chatInputNormal.chatEntry['backgroundFocus'] = 0

    def exitCallback(self, *args):
        if self.chatMgr.wantBackgroundFocus:
            self.chatMgr.chatInputNormal.chatEntry['backgroundFocus'] = 1

    def enableHotkey(self):
        self.hotkey = base.CHAT_LOG
        self.accept(self.hotkey, self.toggleChatLog)

    def disableHotkey(self):
        self.ignore(self.hotkey)

    def destroy(self):
        if not hasattr(self, 'logs'):
            return

        del self.logs
        del self.texts

        for textNode in self.textNodes:
            textNode.removeNode()
        del self.textNodes

        taskMgr.remove(self.taskName('dragTask'))
        taskMgr.remove(self.taskName('scaleTask'))
        DirectButton.destroy(self)
        self.ignoreAll()

    def show(self):
        if self.closed:
            return

        DirectButton.show(self)
        node = self.chatMgr.chatLogNode
        node.show()
        self.__updateSpeedChatStyle()
        self.computeRealLog(0, opening=True)
        self.bind(DGG.ENTER, self.acceptWheelMovements)
        self.bind(DGG.EXIT, self.ignoreWheelMovements)

    def hide(self):
        DirectButton.hide(self)
        node = self.chatMgr.chatLogNode
        node.hide()
        self.ignoreWheelMovements()

    def closeChatlog(self):
        self.closed = True
        self.hide()

    def openChatlog(self):
        if not self.closed:
            return

        if not base.localAvatar.tutorialAck:
            return

        self.closed = False
        self.show()

    def toggleChatLog(self):
        if self.closed:
            self.openChatlog()
        else:
            self.closeChatlog()

    def scrollToCurrent(self, tab):
        minimum = max(0, self.currents[tab] - 12)
        self.texts[tab].setText('\n'.join(self.realLogs[tab][minimum:self.currents[tab]]))

    def computeRealLog(self, tab, opening=False, forcePush=False):
        oldText = self.texts[tab].getText()
        self.texts[tab].setText('\n'.join(self.logs[tab]))
        self.realLogs[tab] = self.texts[tab].getWordwrappedText().split('\n')
        notificationBubble = self.notificationBubbles[tab]
        missedNotifications = int(notificationBubble['text'])
        if not opening:
            if not forcePush:
                self.notify.debug('forcepush: ' + str(forcePush))
                if tab != self.currentTab:
                    missedNotifications += 1
                    notificationBubble.setText(str(missedNotifications))

        if missedNotifications > 0 and tab != self.currentTab:
            notificationBubble.show()
        else:
            notificationBubble.hide()

        if self.autoScroll:
            self.currents[tab] = len(self.realLogs[tab])
            self.scrollToCurrent(tab)
        else:
            self.texts[tab].setText(oldText)

    def __updateSpeedChatStyle(self):
        color = speedChatStyles[base.localAvatar.speedChatStyleIndex][3]
        h, s, v = rgb2hsv(*color)
        color = hsv2rgb(h, 0.5 * s, v)
        r, g, b = color
        self['geom_color'] = (r, g, b, self.opacity)
        for tab in self.chatTabs:
            tab['geom_color'] = (r, g, b, self.opacity)
        if self.wantGuildChat:
            self.guildEntry['geom_color'] = (r, g, b, self.opacity)

    def __addChatHistory(self, name=None, font=None, speechFont=None, color=None,
                         chat=None, type=WhisperPopup.WTNormal):
        tab = 0
        colon = ':'
        forcePush = False

        if name and not font and not speechFont:
            tab = 0
        if not speechFont:
            speechFont = OTPGlobals.getInterfaceFont()
        if font == ToontownGlobals.getSuitFont():
            color = 5
        if not name:
            if ":" in chat:
                name, chat = chat.split(":", 1)
            else:
                name = 'System'
            tab = 2
        if not font:
            font = OTPGlobals.getInterfaceFont()

        if type == WhisperPopup.WTSystem:
            tab = 3
            if isinstance(color, int):
                color = Vec4(0.8, 0.3, 0.6, 1)
        # TODO implement WhisperPopup.WTGuild
        #elif type == WhisperPopup.WTGuild:
           # tab = 2
        elif type == WhisperPopup.WTQuickTalker:
            forcePush = True

        if isinstance(color, int):
            color = NametagGlobals.getArrowColor(color)
        #TODO figure out color and font
       # self.logs[tab].append('\x01%s\x01\x01%s\x01%s%s\x02\x02 \x01%s\x01%s\x02' % (OTPLocalizer.getPropertiesForFont(font),
                                                         #                            OTPLocalizer.getPropertiesForColor(color),
                                        #                           name, colon, OTPLocalizer.getPropertiesForFont(speechFont),
                                                                       #              chat))
        self.logs[tab].append(f'{name} {colon} {chat}')

        while len(self.logs[tab]) > 250:
            del self.logs[tab][0]

        self.computeRealLog(tab, forcePush=forcePush)

    def __wheel(self, amount):
        oldCurrent = self.currents[self.currentTab]
        minimum = min(12, len(self.realLogs[self.currentTab]))
        self.currents[self.currentTab] += amount
        self.autoScroll = self.currents[self.currentTab] >= len(self.realLogs[self.currentTab])

        if self.autoScroll:
            self.currents[self.currentTab] = len(self.realLogs[self.currentTab])
        if self.currents[self.currentTab] < minimum:
            self.currents[self.currentTab] = minimum

        if oldCurrent != self.currents[self.currentTab]:
            self.scrollToCurrent(self.currentTab)

    def dragStart(self, event):
        node = self.chatMgr.chatLogNode
        taskMgr.remove(self.taskName('dragTask'))
        vWidget2render2d = node.getPos(render2d)
        vMouse2render2d = Point3(event.getMouse()[0], 0, event.getMouse()[1])
        editVec = Vec3(vWidget2render2d - vMouse2render2d)
        task = taskMgr.add(self.dragTask, self.taskName('dragTask'))
        task.editVec = editVec

    def dragTask(self, task):
        node = self.chatMgr.chatLogNode
        mwn = base.mouseWatcherNode
        if mwn.hasMouse():
            vMouse2render2d = Point3(mwn.getMouse()[0], 0, mwn.getMouse()[1])
            newPos = vMouse2render2d + task.editVec
            if newPos[0] < 0.5:
                node.wrtReparentTo(base.a2dBottomLeft)
            else:
                node.wrtReparentTo(base.a2dBottomRight)
            windowSizeX = base.win.getProperties().getXSize()
            windowSizeY = base.win.getProperties().getYSize()
            pixelPos = self.getPos(pixel2d)
            nodePixelPos = node.getPos(pixel2d)
            if pixelPos[0] < -100:
                node.setPos(pixel2d, nodePixelPos.getX() + 10, 0, pixelPos[2])
            elif pixelPos[0] > windowSizeX - windowSizeX / 7.5:
                node.setPos(pixel2d, nodePixelPos.getX() - 10, 0, pixelPos[2])
            elif pixelPos[2] > 100:
                node.setZ(pixel2d, nodePixelPos.getZ() - 10)
            elif pixelPos[2] < -windowSizeY + 50:
                node.setZ(pixel2d, nodePixelPos.getZ() + 10)
            else:
                node.setPos(render2d, newPos)
        return task.cont

    def dragStop(self, event):
        taskMgr.remove(self.taskName('dragTask'))
        node = self.chatMgr.chatLogNode
        pos = node.getPos(render2d)
        self.notify.debug("chat log pos is {}".format(pos))

    def scaleStart(self, event):
        node = self.chatMgr.chatLogNode
        taskMgr.remove(self.taskName('scaleTask'))
        vWidget2render2d = node.getPos(render2d)
        vMouse2render2d = Point3(event.getMouse()[0], 0, event.getMouse()[1])
        editVecLen = Vec3(vWidget2render2d - vMouse2render2d).length()
        task = taskMgr.add(self.scaleTask, self.taskName('scaleTask'))
        task.editVecLen = editVecLen
        task.refPos = vWidget2render2d
        task.initScale = node.getScale()

    def scaleTask(self, task):
        node = self.chatMgr.chatLogNode
        mwn = base.mouseWatcherNode
        if mwn.hasMouse():
            vMouse2render2d = Point3(mwn.getMouse()[0], 0, mwn.getMouse()[1])
            newEditVecLen = Vec3(task.refPos - vMouse2render2d).length()
            newScale = task.initScale * (newEditVecLen/task.editVecLen)
            if newScale > 5:
                newScale = 5
            if newScale < 0.25:
                newScale = 0.25
            node.setScale(newScale)
        return task.cont

    def scaleStop(self, event):
        taskMgr.remove(self.taskName('scaleTask'))
        node = self.chatMgr.chatLogNode
        scale = node.getScale(render2d)
        self.notify.debug("scale is {}".format(scale))

    def opacityStart(self, state, event):
        if state:
            taskMgr.doMethodLater(0.1, self.updateOpacity, self.uniqueName('opacity'))
        else:
            taskMgr.remove(self.uniqueName('opacity'))

    def updateOpacity(self, task):
        value = 0.05
        opacity = self.opacity - value
        if opacity > 0.9:
            opacity = 0.1
        elif opacity < 0.1:
            opacity = 0.9
        self.opacity = opacity
        self.__updateSpeedChatStyle()

        return task.again

    def __toggleButton(self, index):
        self.currentTab = index
        for x in range(len(self.chatTabs)):
            self.chatTabs[x]['text_fg'] = (0, 0, 0, 0.5)
            self.textNodes[x].hide()
        self.chatTabs[index]['text_fg'] = (0, 0, 0, 1)
        self.textNodes[index].show()
        self.scrollToCurrent(index)
        notificationBubble = self.notificationBubbles[index]
        notificationBubble.setText('0')
        notificationBubble.hide()

        if index == 2:
            if self.wantGuildChat:
                self.guildEntry.show()
        else:
            if self.wantGuildChat:
                self.guildEntry.hide()

    def acceptWheelMovements(self, bind):
        self.accept('wheel_up-up', self.__wheel, [-1])
        self.accept('wheel_down-up', self.__wheel, [1])

    def ignoreWheelMovements(self, bind = None):
        self.ignore('wheel_up-up')
        self.ignore('wheel_down-up')

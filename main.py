#Adrian Piackus
import time
import pyautogui

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--window-size=1920,800")
chrome = webdriver.Chrome(chrome_options=chrome_options)

timeToEndCall = 1 * 60  # czas do wyjścia ze spotkania w minutach


class Channel:
    def __init__(self, name, meeting):
        self.name = name
        self.meeting = meeting

    def __str__(self):
        return self.name

    def getChannelElem(self, parent):
        try:
            channelElem = parent.find_element_by_css_selector(f"ul>ng-include>li[data-tid*='channel-{self.name}-li']")
        except:
            return None

        return channelElem


class Team:
    def __init__(self, name, elem, channels=None):
        if channels is None:
            channels = []
        self.name = name
        self.elem = elem
        self.channels = channels

    def __str__(self):
        channelName = '\n\t'.join([str(channel) for channel in self.channels])

        return str(f"{self.name}\n\t{channelName}")

    def expandChannels(self):
        try:
            elem = self.elem.find_element_by_css_selector("div[class='channels']")
        except exceptions.NoSuchElementException:
            try:
                self.elem.click()
                elem = self.elem.find_element_by_css_selector("div[class='channels']")
            except exceptions.NoSuchElementException:
                return None
        return elem

    def initialiseChannels(self):
        channelsElem = self.expandChannels()

        channelElems = channelsElem.find_elements_by_css_selector("ul>ng-include>li")

        channelNames = [channelsElem.get_attribute("data-tid") for channelsElem in channelElems]
        channelNames = [channelName[channelName.find('-channel-') + 9:channelName.rfind("-li")] for channelName in
                        channelNames
                        if channelName is not None]

        self.channels = [Channel(channelName, []) for channelName in channelNames]

    def tryToJoinMeeting(self):
        channels = self.expandChannels()
        for channel in self.channels:

            channelElem = channel.getChannelElem(channels)

            try:
                meetingElem = channelElem.find_element_by_css_selector("a > active-calls-counter")
            except:
                continue
            meetingElem.click()
            if wait_till_found("button[ng-click='ctrl.joinCall()']", 60) is None:
                continue

            joinMeeting = chrome.find_element_by_css_selector("button[ng-click='ctrl.joinCall()']")
            joinMeeting.click()

            if wait_till_found("toggle-button[data-tid='toggle-mute']>div>button",
                               60) is None:  # tu było trochę problemów z dziwnym rodzajem guzika
                continue

            microphoneSlider = chrome.find_element_by_css_selector("toggle-button[data-tid='toggle-mute']>div>button")
            if microphoneSlider.get_attribute("aria-pressed") == "true":
                microphoneSlider.click()

            if wait_till_found("toggle-button[data-tid='toggle-video']>div>button",
                               60) is None:  # tu było trochę problemów z dziwnym rodzajem guzika
                continue

            videoSlider = chrome.find_element_by_css_selector("toggle-button[data-tid='toggle-video']>div>button")
            if videoSlider.get_attribute("aria-pressed") == "true":
                videoSlider.click()

            joinButton = chrome.find_element_by_css_selector("button[data-tid='prejoin-join-button']")
            joinButton.click()

            endMeeting()
            time.sleep(4)  # zapobiega crashą(czeka na doczytanie strony)
            break


def wait_till_found(sel,
                    timeout):  # funkcja znaleziona w internecie, pozwala zastąpić 'time.sleep()' w trakcie czekania na załadowanie strony
    try:
        element_present = EC.presence_of_element_located((By.CSS_SELECTOR, sel))
        WebDriverWait(chrome, timeout).until(element_present)

        return chrome.find_element_by_css_selector(sel)
    except exceptions.TimeoutException:
        print("Timeout waiting for element.")
        return None


def getTeamsNames():
    teamElems = chrome.find_elements_by_css_selector("ul>li[role='treeitem']>div[sv-element]")
    teamNames = [teamElem.get_attribute("data-tid") for teamElem in teamElems]

    teamsList = [Team(teamNames[i], teamElems[i], None) for i in range(len(teamElems))]
    return teamsList


def endMeeting():
    time.sleep(timeToEndCall)

    pyautogui.moveTo(400, 700, duration=0.25)
    pyautogui.moveTo(900, 700, duration=0.25)

    endButton = chrome.find_element_by_css_selector("button[data-tid='call-hangup']")
    endButton.click()


def workingPart():
    teamButton = chrome.find_element_by_css_selector("#teams-app-bar > ul > li:nth-child(3)")
    teamButton.click()

    teams = getTeamsNames()
    for team in teams:
        team.initialiseChannels()
        team.expandChannels()

    while 1:
        for team in teams:
            try:
                team.tryToJoinMeeting()
            except: #po odłączeniu się od spotkania wyrzuca błąd który nie wiem jak naprawić, więc reloaduje stronę i działa
                chrome.get('https://teams.microsoft.com')
                time.sleep(2)
                workingPart()


def main():
    chrome.get('https://teams.microsoft.com')
    login = wait_till_found("input[type='email']", 5)
    if login is not None:
        login = chrome.find_element_by_id('i0116')
        loginFile = open(
            'dane.txt')  # dane do logowania przytrzymywane są w zwykłym pliku .txt, na moje potrzeby aktualnie program nie wymaga szyfrowania
        login.send_keys(loginFile.readline())
        login.send_keys(Keys.ENTER)

    time.sleep(
        1)  # w tym wypadku wait_till_found() z jakiegoś powodu nie chce działać (prawdopodobnie załadowane jest odrazu z poprzednim wykonaniem)
    haslo = chrome.find_element_by_id('i0118')
    haslo.send_keys(loginFile.readline())
    haslo.send_keys(Keys.ENTER)

    loginFile.close()
    try:
        klawisz = chrome.find_element_by_id('idSIButton9')  # czasami wymaga potwierzenia że chcemy się logować
        klawisz.send_keys(Keys.ENTER)
    except:
        pass

    print("Poczekaj na ladowanie strony")

    button = chrome.find_element_by_css_selector("#download-desktop-page > div > a")
    button.click()

    if wait_till_found("div[data-tid='team-channel-list']", 60) is None:
        exit(1)

    teamButton = chrome.find_element_by_css_selector("#teams-app-bar>ul>li:nth-child(3)")
    teamButton.click()

    teams = getTeamsNames()
    for team in teams:
        team.initialiseChannels()
        team.expandChannels()

    print("Znalezione zespoły")
    for team in teams:
        print(team)  # todo - zrobić lepsze formatowanie tej listy

    while 1:
        workingPart()


main()

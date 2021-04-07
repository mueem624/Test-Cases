"""
Description:
The AIM of the test case is to verify the behavior of the DUT, when it failed to get the Local IP due to DHCP server's
response packet delay

Prerequisite:
First time installation is successful and linear channel is playing for 5 minutes
KMAX Network emulator reset

Parameters:
--server 10.13.130.182 --slot 13 --motionTime 10 --times 5

Author:
Md Muttayem Al Mueem

Reviewer:

"""

from framework.Test import Test
from framework import api
from framework.model.utility.connectivityImpairment import KImpairment
from framework.model.utility.errorDetection import ErrorCheck
from framework.model.utility.sdoLib import SDOLib
from framework.model.application.linearTV.LinearTV import LinearTV
from framework.model.utility.testUtil import handleTestException, defineStep, setStepStatus, resetStepNumber
from framework.model.application.Application import Application
from framework.model.utility.SDONavigator import SDONavigator
from framework.factory.services.ADBLogsv2 import ADBLogs
from framework.configs.slotInfo import slotInfo

# Parmeters
parameters = [

    {
        "name": "reboot",
        "type": "boolean",
        "value": True,
        "description": "Deep standby wake up"
    },
    {
        "name": "motionTime",
        "type": "int",
        "value": 10,
        "description": "Detect motion continuously "
    },
    {
        "name": "verifySettings",
        "type": "boolean",
        "value": True,
        "description": "Detect motion continuously "
    }
]

t = Test(initialiseDUT=True, optionsDict=parameters, autoRecover=True)
config = t.config
application = Application(config)
tv = LinearTV(config)
sdoLib = SDOLib()
adbLogs = ADBLogs(verbose=True, port=5038)
sodNavigator = SDONavigator()
deviceIP = slotInfo[t.server][str(t.slotNo)]["ip"]
kmaxImpairment = KImpairment(deviceIP=deviceIP)
errorCheck = ErrorCheck()
nav = tv.utility.navigator

# Config File Parameter
slotNo = config.getConfigItem("slotNumber")
server = config.getConfigItem("server")
timesLoop = config.getConfigItem("times")
ipKmax = config.getConfigItem("ipKmax")
filterNo = (slotNo % 4) + 1

# Dynamic Parameters
reboot = config.getConfigItem("reboot")
motionTime = (config.getConfigItem("motionTime"))
verifySettings = (config.getConfigItem("verifySettings"))

# ============
# STEP
# ============

step_name = "Precondition: Open Linear Channel"
expected_result = "Precondition should be fulfilled"
defineStep(step_name, step_name, expected_result)

kmaxImpairment.switchImpairment_OFF(filterNo=filterNo)
api.pressButtons(['OK', 'MENU', '5'], 3)

result = tv.open('LiveScreen')
api.writeDebugLine("Return values for tv.open(): {}".format(result))
if result[0]:
    setStepStatus(api.TM.PASS)
else:
    result = tv.checkUnExpectedScreen()
    api.writeDebugLine("Check UnExpectedScreen Results: {}".format(result))

    if result[1] != 'Motion':
        result = tv.recoverFromUnExpectedScreen(screenToRecoverFrom=result[1])
        api.writeDebugLine("Recover UnExpectedScreen Results: {}".format(result))

        if result is None or not result[0]:
            api.captureImageEx(None, "Failure_Exception.png")[0][2].Close()
            errorMessage = "Unexpected Screen. Cannot proceed...."
            raise Exception(errorMessage)

try:
    for iteration in range(1, int(timesLoop) + 1):

        # ============
        # STEP
        # ============

        step_name = "Iteration: {} : Fresh boot up from the powerless state".format(iteration)
        expected_result = "Booting up without any issue"
        defineStep(step_name, step_name, expected_result)

        if reboot:
            api.powerOffSTB()
            api.powerOnSTB()
        else:
            print("No need to reboot")
        setStepStatus(api.TM.PASS)

        # ============
        # STEP
        # ============
        step_name = "Iteration: {} : Initialise KMAX network emulator".format(iteration)
        expected_result = "Set up network impairment as per filter"
        defineStep(step_name, step_name, expected_result)

        kmaxImpairment.switchImpairment_ON(impairment='DHCP', drop=0, delay=20, filterNo=filterNo)
        api.waitSec(105)
        setStepStatus(api.TM.PASS)

        # ============
        # STEP
        # ============

        step_name = "Iteration: {} : Validate the current screen".format(iteration)
        expected_result = "Error code 0100 on the screen "
        defineStep(step_name, step_name, expected_result)

        errorResult = errorCheck.getErrorCode()
        print(errorResult)
        if errorResult[0]:
            setStepStatus(api.TM.PASS)
        else:
            print('Not an error screen/Unknown error screen')
            api.captureImageEx(None, "currentScreen.png")[0][2].Close()
            setStepStatus(api.TM.FAIL)

        # ============
        # STEP
        # ============

        step_name = "Iteration: {} : Remove the network impairment".format(iteration)
        expected_result = "Reset the KMAX and recover the error state"
        defineStep(step_name, step_name, expected_result)

        kmaxImpairment.switchImpairment_OFF(filterNo=filterNo)
        api.waitSec(180)

        errorResult = errorCheck.getErrorCode()
        print(errorResult)
        if errorResult[0]:
            print('DUT stuck in the error state')
            api.powerOffSTB()
            api.powerOnSTB()
            api.waitSec(100)
            api.pressButton('5', 5)
            setStepStatus(api.TM.FAIL)
        else:
            api.waitSec(300)
            api.writeDebugLine("Successfully recover from the error state")
            print('DHCP server ACK')
            adbLogs.printGenericLogs(t.server, t.slotNo, tag="DhcpClient:D", search="ACK")
            setStepStatus(api.TM.PASS)

        # ============
        # STEP
        # ============

        step_name = "Iteration: {} : Validate the current screen".format(iteration)
        expected_result = "Linear channel playing and motion shall be detected continuously for {} Seconds".format(
            motionTime)
        defineStep(step_name, step_name, expected_result)

        if verifySettings:
            nav.resetLastNavScreen()
            nav.navigateTo("OpenSystemSetting")
            api.waitSec(5)
            api.pressButtons(["OK", "OK", "DOWN", "DOWN", "DOWN", "DOWN"], 5)
            ethernetIP_rect = (2492, 1529, 265, 54)
            region = api.ocrRegion("", "ethernetIP", rect=ethernetIP_rect, verify=False)
            sdo = api.screenDefinition()
            sdo.Regions.append(region)
            returnSDO = sdo.Match()[0][1]
            api.writeDebugLine("Actual IP: {}".format(returnSDO.Regions[0].ResultText))
        api.pressButtons(['MENU', '5'], 10)

        checkForReady = False
        screenStatus = tv.identifyScreen()
        if screenStatus[1] == "LiveScreen":
            checkForReady = True
        elif screenStatus[1] == "parentalPIN":
            checkForReady = tv.verifyAndEnterParentalPin()[0]
            if not checkForReady:
                api.captureImageEx(None, "parentalPIN.png")[0][2].Close()
                comments = "Unable to find livescreen after entering parental pin"
        elif screenStatus[1] in ["premiumChannel", "technicalErrorPage", "generalLinearStreamingError"]:
            api.captureImageEx(None, "{}.png".format(screenStatus[1]))[0][2].Close()
            comments = screenStatus[1]
        else:
            api.captureImageEx(None, "Failure_Exception.png")[0][2].Close()
            comments = "Unexpected Screen"
            api.pressButtons(['BACK', 'BACK', 'BACK'], 2)

        if checkForReady:
            motionDetected, motionStatusList, successRate = tv.detectMotionContinuously(motionTime)
            api.writeDebugLine("DetectMotion:: " + str(motionDetected))

            if motionDetected:
                api.writeDebugLine("Motion Detected, success rate: {}".format(successRate))
                setStepStatus(api.TM.PASS)

            else:
                api.writeDebugLine("Motion Not Detected, success rate: {}".format(successRate))
                api.captureImageEx(None, "MotionDetection_Failure.png")[0][2].Close()
                setStepStatus(api.TM.FAIL, "Motion detection failed. SuccessRate was {}".format(successRate))
        else:
            api.captureImageEx(None, "Failure_Exception.png")[0][2].Close()
            setStepStatus(api.TM.FAIL, "Unexpected Screen")

        defineStep("Closing Iteration {}".format(str(iteration)), "Close test gracefully")
        if iteration != int(timesLoop):
            resetStepNumber()

    # ============
    # STEP
    # ============

    step_name = "Teardown Environment"
    expected_result = "Successfully disconnect from StormTest"
    defineStep(step_name, step_name, expected_result)

    api.writeDebugLine("DHCP Discover packet delayed and recover passed")
    setStepStatus(api.TM.PASS)
    api.returnTestResult(api.TM.PASS)


except Exception as e:
    kmaxImpairment.switchImpairment_OFF(filterNo=filterNo)
    print(e)
    api.captureImageEx(None, "Failure_Exception.png")[0][2].Close()
    handleTestException()
    api.returnTestResult(api.TM.FAIL)

finally:
    t.adb.saveAllLogs(server, slotNo)
    t.disconnect()

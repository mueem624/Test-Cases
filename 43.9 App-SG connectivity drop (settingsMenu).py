"""
Description:
The AIM of the test case is to verify the behavior of the DUT,while Launcher come back from background to foreground and
it's failed to get the response from session Guard due to packet drop

Prerequisite:
First time installation is successful and linear channel is playing for 5 minutes
KMAX Network emulator reset
Check the DUT VF launcher version, if a debug APK is installed on the DUT, use debugApk as a parameter and assign it True
to get the application related logcat.

Parameters:
--server 10.13.130.182 --slot 14 --times 5 --debugApk True

Author:
Md Muttayem Al Mueem

Reviewer:

"""
from framework.Test import Test
from framework import api
from framework.model.application.linearTV.LinearTV import LinearTV
from framework.model.utility.testUtil import defineStep, setStepStatus, handleTestException, resetStepNumber
from framework.factory.services.ADBLogsv2 import ADBLogs
from framework.model.utility.connectivityImpairment import KImpairment
from framework.model.utility.errorDetection import ErrorCheck
from framework.configs.slotInfo import slotInfo

# Parmeters
parameters = [

    {
        "name": "motionTime",
        "type": "int",
        "value": 10,
        "description": "Detect motion continuously "
    },
    {
        "name": "debugApk",
        "type": "boolean",
        "value": True,
        "description": "Release APK install on the DUT"
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
tv = LinearTV(config)
adbLogs = ADBLogs(verbose=True, port=5038)
nav = tv.utility.navigator
deviceIP = slotInfo[t.server][str(t.slotNo)]["ip"]
kmaxImpairment = KImpairment(deviceIP=deviceIP)
errorCheck = ErrorCheck()

# Config attributes
slotNo = config.getConfigItem("slotNumber")
server = config.getConfigItem("server")
timesLoop = config.getConfigItem("times")
ipKmax = config.getConfigItem("ipKmax")
filterNo = (slotNo % 4) + 1

# Dynamic Parameter
motionTime = (config.getConfigItem("motionTime"))
verifySettings = (config.getConfigItem("verifySettings"))
debugApk = (config.getConfigItem("debugApk"))

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
        step_name = "Iteration: {} : Linear channel is playing".format(iteration)
        expected_result = "Linear Channel should be played and motion should be detected continuously"
        defineStep(step_name, step_name, expected_result)

        api.pressButtons(['MENU', '5'], 10)

        motion_result = tv.isMotion()
        api.writeDebugLine("Motion Result::{}".format(motion_result))

        if motion_result[0]:
            setStepStatus(api.TM.PASS)
        else:
            setStepStatus(api.TM.FAIL)

        # ============
        # STEP
        # ============
        step_name = "Iteration: {} : Initialise KMAX network emulator".format(iteration)
        expected_result = "Set up network impairment as per filter"
        defineStep(step_name, step_name, expected_result)

        if verifySettings:
            nav.resetLastNavScreen()
            nav.navigateTo("OpenSystemSetting")
            api.waitSec(5)
            api.pressButtons(["OK", "OK", "DOWN"], 5)

        else:
            api.pressButtons(['POWER', 'POWER', '5'], 10)

        kmaxImpairment.switchImpairment_ON(impairment='SG', drop=100, filterNo=filterNo)

        setStepStatus(api.TM.PASS)

        # ============
        # STEP
        # ============

        step_name = "Iteration: {} : Validate the current screen".format(iteration)
        expected_result = "Error code 0500 on the screen "
        defineStep(step_name, step_name, expected_result)

        api.pressButton('MENU')
        api.waitSec(300)

        if debugApk:
            api.writeDebugLine("Session Guard connectivity")
            adbLogs.printGenericLogs(t.server, t.slotNo, tag="VeopApp:D", search='connect: failed to connect')

        errorResult = errorCheck.getErrorCode()
        print(errorResult)
        if errorResult[0]:
            setStepStatus(api.TM.PASS)
        else:
            print('This is not an error screen/unknown error scrren')
            api.captureImageEx(None, "currentScreen.png")[0][2].Close()
            setStepStatus(api.TM.FAIL)

        # ============
        # STEP
        # ============

        step_name = "Iteration: {} : Remove the network impairment".format(iteration)
        expected_result = "Reset the KMAX and recover the error state"
        defineStep(step_name, step_name, expected_result)

        kmaxImpairment.switchImpairment_OFF(filterNo=filterNo)
        api.waitSec(30)
        api.pressButtons(['OK', 'MENU'], 3)

        errorResult = errorCheck.getErrorCode()
        print(errorResult)
        if errorResult[0]:
            print('DUT stuck in the error state')
            api.powerOffSTB()
            api.powerOnSTB()
            api.waitSec(100)
            setStepStatus(api.TM.FAIL)
        else:
            api.writeDebugLine("Successfully recover from the error state")
            setStepStatus(api.TM.PASS)

        # ============
        # STEP
        # ============

        step_name = "Iteration: {} : Validate the current screen".format(iteration)
        expected_result = "Linear channel playing and motion shall be detected continuously for {} Seconds".format(
            motionTime)
        defineStep(step_name, step_name, expected_result)

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

    api.writeDebugLine("Session Guard connectivity packet dropped and recover passed")
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

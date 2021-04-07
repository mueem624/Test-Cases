# Test-Cases
This test cases covered 18 error scenarios. The general structure of the test case is the following:

Step 1: precondtion: check the application is in normal operation.

Step 2: Create the network impairment programmatically using KMAX network emulator.

Step 3: Observe the application trying to connect backend server and failed to connect.

Step 4: Application goes to the error state and verify the error state through, error detection module, ADB logs and Wireshark. 

Step 5:Remove the network impairment.

Step 6: Observe the application recover from the error.

Step 7: Application recover from the error state and verify the recovery procedure through, error detection module, ADB logs and Wireshark.

Step 8: Check the applcation return back to the normal operation.

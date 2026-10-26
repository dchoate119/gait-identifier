from arduino.app_utils import App

import imu_test

App.run(user_loop=imu_test.loop)

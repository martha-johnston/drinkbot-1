import asyncio
from inspect import getcallargs
import numpy

from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.components.motor import Motor
from viam.services.types import ServiceType
from viam.services.vision import DetectorConfig, DetectorType
from viam.components.camera import Camera
from viam.components.base import Base, Vector3
from PIL import Image

linear_zero = Vector3(x = 0, y = 0, z = 0)
angular_zero = Vector3(x = 0, y = 0, z = 0)

async def client():
    creds = Credentials(
        type='robot-location-secret',
        payload='lauqrt4op4x6ubhji867wue0qsnqdq76x00ljfv7vcoyq7mi')
    opts = RobotClient.Options(
        refresh_interval=0,
        dial_options=DialOptions(credentials=creds)
    )
    async with await RobotClient.at_address(
        'drinkbot-main.rdt5n4brox.local.viam.cloud:8080',
        opts) as robot:
        print('Resources:')
        print(robot.resource_names)
    
    # vis = await getVisService(robot)
    vis = robot.get_service(ServiceType.VISION)
    motor = Motor.from_robot(robot, 'motor')
    wheels = Base.from_robot(robot, 'base')

    names = await vis.get_detector_names()
    print(names)
    
    while 1:

        # check camera for detections
        detections = await vis.get_detections_from_camera("cam", "detector_color")

        # found no detections
        if len(detections) == 0:
            detections = await find_target(vis, wheels, detections)

        # found detection
        if len(detections) != 0:
            # move to target
            await move_to_target(vis, wheels, detections)

            # pour
            await motor.set_power(0.35)
            await asyncio.sleep(4.5)
            await motor.set_power(0)
            await asyncio.sleep(2)
            await motor.set_power(-0.35)
            await asyncio.sleep(4.5)
            await motor.set_power(0)

            return

    await robot.close()

async def move_to_target(vis, wheels, detections):
    x_center = (detections[0].x_max + detections[0].x_min)/2
    linear = Vector3(x = 0, y = 0.5, z = 0)
    angular = angular_zero
    while 1:
        if(x_center < 160):
            angular = Vector3(x = 0, y = 0, z = 0.05)
        elif(x_center > 160):
            angular = Vector3(x = 0, y = 0, z = -0.05)
        elif(x_center == 160):
            angular = angular_zero
        await wheels.set_power(linear, angular)

        detections = await vis.get_detections_from_camera("cam", "detector_color")
        print(len(detections))

        if len(detections) > 10:
            await wheels.stop()
            break

        x_center = (detections[0].x_max + detections[0].x_min)/2
        
    print("in range for pick up")
    await wheels.stop()
    await asyncio.sleep(1)

async def find_target(vis, wheels, detections):
    rotation_count = 0

    # creat power vectors to only spin
    angular = Vector3(x = 0, y = 0, z = 0.5)

    # found no detections
    while (len(detections) == 0):
        print("rotation count = ", rotation_count)
        # if 360 deg with no detections, task completed
        if rotation_count > 52:
            print("all objects cleared")
            return
        # await wheels.spin(10, 90) <-- not currently working, but ideal implementation
        await wheels.set_power(linear_zero, angular)
        await asyncio.sleep(0.2)
        await wheels.stop()
        rotation_count += 1

        detections = await vis.get_detections_from_camera("cam", "detector_color")
        
    print("found object")
    return detections


if __name__ == '__main__':
    asyncio.run(client())

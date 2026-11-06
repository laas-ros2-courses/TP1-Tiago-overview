import math

import rclpy
import rclpy.task
from rclpy.action import ActionServer
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TwistStamped

from tiago_go_to_point_interfaces.action import GoToPoint


def yaw_from_quaternion(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                       1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class GoToPointActionServer(Node):
    """
    Action GoToPoint pour TIAGo : envoie la base mobile vers un point donne
    (coordonnees dans le repere odom), avec un retour de progression
    (feedback) pendant le trajet. Portage direct de l'exercice TD2 turtlesim
    (go_to_point_server.py) : /turtle1/pose -> /mobile_base_controller/odom,
    /turtle1/cmd_vel -> /mobile_base_controller/cmd_vel, theta direct ->
    yaw extrait du quaternion. mobile_base_controller (diff_drive_controller)
    attend un TwistStamped sur ce topic : `use_stamped_vel` a ete retire de
    ros2_controllers en 4.17.0 (dec. 2024, migration Twist->TwistStamped),
    le parametre `use_stamped_vel: False` encore present dans la config
    PAL d'origine est donc ignore par cette version.
    """

    def __init__(self):
        super().__init__('go_to_point_action_server')

        self._action_server = ActionServer(
            self, GoToPoint, 'go_to_point', self.execute_callback)
        self.x = None
        self.y = None
        self.theta = None
        self.cmd_pub = self.create_publisher(
            TwistStamped, '/mobile_base_controller/cmd_vel', 10)
        self.odom_sub = self.create_subscription(
            Odometry, '/mobile_base_controller/odom', self.odom_callback, 10)

    def _stamped_twist(self, linear_x=0.0, angular_z=0.0):
        cmd = TwistStamped()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.header.frame_id = 'base_footprint'
        cmd.twist.linear.x = linear_x
        cmd.twist.angular.z = angular_z
        return cmd

    def odom_callback(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        self.theta = yaw_from_quaternion(msg.pose.pose.orientation)

    async def _sleep(self, seconds):
        """Point d'attente compatible avec les coroutines rclpy."""
        future = rclpy.task.Future()
        timer = self.create_timer(seconds, lambda: self._resolve(future, timer))
        await future

    def _resolve(self, future, timer):
        timer.cancel()
        if not future.done():
            future.set_result(None)

    async def execute_callback(self, goal_handle):
        self.get_logger().info(
            'Executing goal: (%.2f, %.2f)' % (goal_handle.request.x, goal_handle.request.y))
        feedback_msg = GoToPoint.Feedback()
        goal_x, goal_y = goal_handle.request.x, goal_handle.request.y
        tolerance = 0.1
        kp_linear, kp_angular = 0.5, 1.5

        while self.x is None:
            await self._sleep(0.05)

        while True:
            dx, dy = goal_x - self.x, goal_y - self.y
            distance = math.hypot(dx, dy)
            feedback_msg.distance_remaining = distance
            goal_handle.publish_feedback(feedback_msg)

            if distance < tolerance:
                break

            angle_to_goal = math.atan2(dy, dx)
            angle_error = angle_to_goal - self.theta
            angle_error = math.atan2(math.sin(angle_error), math.cos(angle_error))

            linear_x = kp_linear * distance
            angular_z = kp_angular * angle_error
            self.cmd_pub.publish(self._stamped_twist(linear_x, angular_z))

            await self._sleep(0.05)

        self.cmd_pub.publish(self._stamped_twist())  # stop
        goal_handle.succeed()

        result = GoToPoint.Result()
        result.success = True
        result.final_x = self.x
        result.final_y = self.y
        return result


def main(args=None):
    rclpy.init(args=args)
    node = GoToPointActionServer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

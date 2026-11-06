import sys

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.utilities import remove_ros_args

from tiago_go_to_point_interfaces.action import GoToPoint


class GoToPointActionClient(Node):
    """
    Client de l'action GoToPoint pour TIAGo, structure calquee sur le
    tutoriel officiel "Writing an action server and client (Python)"
    (goal_msg, wait_for_server, send_goal_async + feedback_callback,
    goal_response_callback -> get_result_async, get_result_callback).
    """

    def __init__(self):
        super().__init__('go_to_point_action_client')
        self._action_client = ActionClient(self, GoToPoint, 'go_to_point')

    def send_goal(self, x, y):
        goal_msg = GoToPoint.Goal()
        goal_msg.x = x
        goal_msg.y = y

        self._action_client.wait_for_server()

        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg, feedback_callback=self.feedback_callback)
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected :(')
            return

        self.get_logger().info('Goal accepted :)')

        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(
            'Result: success=%s, final=(%.2f, %.2f)' %
            (result.success, result.final_x, result.final_y))
        rclpy.shutdown()

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(
            'Received feedback: distance_remaining=%.3f' % feedback.distance_remaining)


def main(args=None):
    rclpy.init(args=args)

    action_client = GoToPointActionClient()

    # Coordonnees dans le repere odom (origine = point de spawn du robot).
    cli_args = remove_ros_args(args=sys.argv)
    x = float(cli_args[1]) if len(cli_args) > 1 else 1.0
    y = float(cli_args[2]) if len(cli_args) > 2 else 0.0
    action_client.send_goal(x, y)

    rclpy.spin(action_client)


if __name__ == '__main__':
    main()

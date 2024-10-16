import random
from collections import deque

import carla

from car_dreamer.toolkit.planner.fixed_path_planner import FixedPathPlanner

from .carla_wpt_fixed_env import CarlaWptFixedEnv
from .toolkit import get_vehicle_pos


class CarlaRightTurnEnv(CarlaWptFixedEnv):
    """
    Vehicle passes the crossing (turn right) and avoid collision.

    **Provided Tasks**: ``carla_right_turn_simple``, ``carla_right_turn_medium``, ``carla_right_turn_hard``
    """

    def on_reset(self) -> None:
        if self._config.direction == 4:
            random_num = random.randint(0, len(self._config.lane_start_point) - 1)
        elif self._config.direction >= 0 and self._config.direction < 4:
            random_num = self._config.direction

        self.ego_src = self._config.lane_start_point[random_num]
        ego_transform = carla.Transform(carla.Location(*self.ego_src[:3]), carla.Rotation(yaw=self.ego_src[3]))
        self.ego = self._world.spawn_actor(transform=ego_transform)
        self.ego_path = self._config.ego_path[random_num]
        self.use_road_waypoints = self._config.use_road_waypoints
        self.ego_planner = FixedPathPlanner(vehicle=self.ego, vehicle_path=self.ego_path, use_road_waypoints=self.use_road_waypoints)
        self.waypoints, self.planner_stats = self.ego_planner.run_step()
        self.num_completed = self.planner_stats["num_completed"]

        # Initialize car flow
        self.actor_flow = deque()
        flow_spawn_point = self._config.flow_spawn_point[random_num]
        self.flow_transform = carla.Transform(carla.Location(*flow_spawn_point[:3]), carla.Rotation(yaw=flow_spawn_point[3]))

    def on_step(self) -> None:
        if len(self.actor_flow) > 0:
            vehicle = self.actor_flow[0]
            x, y = get_vehicle_pos(self.actor_flow[0])
            if y < -181.9 or y > -81.2:
                self._world.destroy_actor(vehicle.id)
                self.actor_flow.popleft()
        super().on_step()

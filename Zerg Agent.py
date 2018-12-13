from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.lib import actions, features, units
from absl import app
import random


class ZergAgent(base_agent.BaseAgent):
    def __init__(self):
        super(ZergAgent, self).__init__()

        self.attack_coordinates = None

    # checks if the current unit type is selected
    def unit_type_is_selected(self, obs, unit_type):
        # if something is selected and checks to see if the first selecting thing is same as passed unit type
        if len(obs.observation.single_select) > 0 and obs.observation.single_select[0].unit_type == unit_type or \
                len(obs.observation.multi_select) > 0 and obs.observation.multi_select[0].unit_type == unit_type:
            return True

        return False

    # returns a list of all units of that type
    def get_units_by_type(self, obs, unit_type):
        units = []
        for unit in obs.observation.feature_units:
            if unit.unit_type == unit_type:
                units.append(unit)
        return units

    # checks if the agent meets all criteria to do the given action
    def can_do(self, obs, action):
        return action in obs.observation.available_actions

    # step() is similar to on_step() from sc2 library
    def step(self, obs):
        super(ZergAgent, self).step(obs)

        # obs.first() checks if its first step
        if obs.first():
            player_y, player_x = (obs.observation.feature_minimap.player_relative == features.PlayerRelative.SELF).nonzero()

            x_mean = player_x.mean()
            y_mean = player_y.mean()

            if x_mean <= 31 and y_mean <= 31:
                self.attack_coordinates = (49, 49)
            else:
                self.attack_coordinates = (12, 16)

        # creates overlord if supply <= 4 and all criteria met
        supply_left = obs.observation.player.food_cap - obs.observation.player.food_used
        if supply_left <= 4 and self.can_do(obs, actions.FUNCTIONS.Train_Overlord_quick.id):
                return actions.FUNCTIONS.Train_Overlord_quick("now")

        # creates 1 spawning pool if all criteria met
        spawning_pools = self.get_units_by_type(obs, units.Zerg.SpawningPool)
        if len(spawning_pools) == 0:
            if self.unit_type_is_selected(obs, units.Zerg.Drone) \
             and self.can_do(obs, actions.FUNCTIONS.Build_SpawningPool_screen.id):
                    x = random.randint(0, 83)
                    y = random.randint(0, 83)
                    return actions.FUNCTIONS.Build_SpawningPool_screen("now", (x, y))

        # creates 1 roach warren if all criteria met
        roach_warren = self.get_units_by_type(obs, units.Zerg.RoachWarren)
        if len(roach_warren) == 0:
            if self.unit_type_is_selected(obs, units.Zerg.RoachWarren) \
             and self.can_do(obs, actions.FUNCTIONS.Build_RoachWarren_screen.id):
                x = random.randint(0, 83)
                y = random.randint(0, 83)
                return actions.FUNCTIONS.Build_RoachWarren_screen("now", (x, y))

        # creates zerglings if all criteria met
        if self.unit_type_is_selected(obs, units.Zerg.Larva) \
                and self.can_do(obs, actions.FUNCTIONS.Train_Roach_quick.id):
            return actions.FUNCTIONS.Train_Roach_quick("now")

        # attack with roaches
        roaches = self.get_units_by_type(obs, units.Zerg.Roach)
        if len(roaches) > 10:
            # attacks with all roaches if they are selected
            if self.unit_type_is_selected(obs, units.Zerg.Roach) \
             and self.can_do(obs, actions.FUNCTIONS.Attack_minimap.id):
                return actions.FUNCTIONS.Attack_minimap("now", self.attack_coordinates)
            # select the roaches since they aren't selected
            if self.can_do(obs, actions.FUNCTIONS.select_army.id):
                return actions.FUNCTIONS.select_army("select")

        # selects random larva
        larvae = self.get_units_by_type(obs, units.Zerg.Larva)
        if len(larvae) > 0:
            larva = random.choice(larvae)
            return actions.FUNCTIONS.select_point("select_all_type", (larva.x, larva.y))

        # selects random drone
        drones = self.get_units_by_type(obs, units.Zerg.Drone)
        if len(drones) > 0:
            drone = random.choice(drones)
            # "select_all_type" works like ctrl clicking and drone's (x,y) is passed
            return actions.FUNCTIONS.select_point("select_all_type", (drone.x, drone.y))

        return actions.FUNCTIONS.no_op()


# main() requires a argument so put a placeholder that won't be used
def main(unused_argv):
    agent = ZergAgent()
    try:
        while True:
            with sc2_env.SC2Env(
                    # passes in a map to play on
                    map_name="AbyssalReef",
                    # passes a list of players
                    players=[sc2_env.Agent(sc2_env.Race.zerg),
                             sc2_env.Bot(sc2_env.Race.random, sc2_env.Difficulty.very_easy)],
                    # passes the screen and minimap resolutions
                    agent_interface_format=features.AgentInterfaceFormat(
                        feature_dimensions=features.Dimensions(screen=84, minimap=64),
                        use_feature_units=True),
                    # game steps that passes before bot chooses an action
                    # default is 8 which is 300 APM, 16 is 150 APM
                    step_mul=16,
                    # length of game, 0 means game runs forever
                    # every integer = 1 second
                    game_steps_per_episode=0,
                    # enables the visualisation
                    visualize=True) as env:

                # loops for step details for the agent, receiving actions until game ends/terminated
                agent.setup(env.observation_spec(), env.action_spec())

                timesteps = env.reset()
                agent.reset()

                while True:
                    step_actions = [agent.step(timesteps[0])]
                    if timesteps[0].last():
                        break
                    timesteps = env.step(step_actions)

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    app.run(main)

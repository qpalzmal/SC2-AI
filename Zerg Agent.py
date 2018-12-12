from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.lib import actions, features, units
from absl import app
import random


class ZergAgent(base_agent.BaseAgent):
    def unit_type_is_selected(self, obs, unit_type):
        # if something is selected and checks to see if the first selecting thing is same as passed unit type
        if len(obs.observation.single_select) > 0 and obs.observation.single_select[0].unit_type == unit_type or \
                len(obs.observation.multi_select) > 0 and obs.observation.multi_select[0].unit_type == unit_type:
            return True

        return False

    def get_units_by_type(self, obs, unit_type):
        units = []
        for unit in obs.observation.feature_units:
            if unit.unit_type == unit_type:
                units.append(unit)
        return units

    # step() is similar to on_step() from sc2 library
    def step(self, obs):
        super(ZergAgent, self).step(obs)

        # checks if agent meets all criteria to build a spawning pool and only builds 1 spawning pool
        spawning_pools = self.get_units_by_type(obs, units.Zerg.SpawningPool)
        if len(spawning_pools) == 0:
            if self.unit_type_is_selected(obs, units.Zerg.Drone):
                if actions.FUNCTIONS.Build_SpawningPool_screen.id in obs.observation.available_actions:
                    x = random.randint(0, 83)
                    y = random.randint(0, 83)
                    return actions.FUNCTIONS.Build_SpawningPool_screen("now", (x, y))

        # gets all units then adds them to the drones list if that unit is a drone
        drones = self.get_units_by_type(obs, units.Zerg.Drone)
        if len(drones) > 0:
            drone = random.choice(drones)
            # "select_all_type" works like ctrl clicking and drone's (x,y) is passed
            return actions.FUNCTIONS.select_point("select_all_type", (drone.x, drone.y))

        return actions.FUNCTIONS.no_op()


def main():
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

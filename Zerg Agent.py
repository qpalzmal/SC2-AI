from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.lib import actions, features, units
from absl import app


class ZergAgent(base_agent.BaseAgent):
    # step() is similar to on_step() from sc2 library
    def step(self, obs):
        super(ZergAgent, self).step(obs)

        return actions.FUNCTIONS.no_op()


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
                    feature_dimensions=features.Dimensions(screen=84, minimap=64)),
                # game steps that passes before bot chooses an action
                # default is 8 which is 300 APM, 16 is 150 APM
                step_mul=16,
                # length of game, 0 means game runs forever
                game_steps_per_episode=0,
                # enables the visualisation
                visualize=True) as env:
                    agent.setup(env.observation_spec(), env.action_spec())

                    timesteps = env.reset()
                    



if __name__ == "__main__":
    app.run(main)

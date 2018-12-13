import random
import math
import numpy as np
import pandas as pd
from pysc2.agents import base_agent
from pysc2.lib import actions, features, units
from pysc2.env import sc2_env

_NO_OP = actions.FUNCTIONS.no_op.id
_SELECT_POINT = actions.FUNCTIONS.select_point.id
_BUILD_SPAWNING_POOL = actions.FUNCTIONS.Build_SpawningPool.id
_BUILD_ROACH_WARREN = actions.FUNCTIONS.Build_RoachWarren.id
_TRAIN_ROACH = actions.FUNCTIONS.Train_Roach_quick.id
_SELECT_ARMY = actions.FUNCTIONS.select_army.id
_ATTACK_MINIMAP = actions.FUNCTIONS.Attack_minimap.id

_PLAYER_RELATIVE = features.SCREEN_FEATURES.player_relative.index
_UNIT_TYPE = features.SCREEN_FEATURES.unit_type.index
_PLAYER_ID = features.SCREEN_FEATURES.player_id.index

_PLAYER_SELF = 1

_ZERG_HATCHERY = units.Zerg.Hatchery
_ZERG_DRONE = units.Zerg.Drone
_ZERG_OVERLORD = units.Zerg.Overlord
_ZERG_SPAWNINGPOOL = units.Zerg.SpawningPool
_ZERG_ROACHWARREN = units.Zerg.RoachWarren
_ZERG_ROACH = units.Zerg.Roach

_NOT_QUEUED = [0]
_QUEUED = [1]




# Taken from https://github.com/MorvanZhou/Reinforcement-learning-with-tensorflow
# keeps track of all states and actions for agent to receive rewards/score for actions
class QLearningTable:
    def __init__(self, actions, learning_rate=0.01, reward_decay=0.9, e_greedy=0.9):
        self.actions = actions
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon = e_greedy
        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float64)

    def choose_action(self, observation):
        self.check_state_exist(observation)

        if np.random.uniform() < self.epsilon:
            # choose best action
            state_action = self.q_table.ix[observation, :]

            # some actions have the same value
            state_action = state_action.reindex(np.random.permutation(state_action.index))

            action = state_action.idxmax()
        else:
            # choose random action
            action = np.random.choice(self.actions)

        return action

    def learn(self, s, a, r, s_):
        self.check_state_exist(s_)
        self.check_state_exist(s)

        q_predict = self.q_table.ix[s, a]
        q_target = r + self.gamma * self.q_table.ix[s_, :].max()

        # update
        self.q_table.ix[s, a] += self.lr * (q_target - q_predict)

    def check_state_exist(self, state):
        if state not in self.q_table.index:
            # append new state to q table
            self.q_table = self.q_table.append(
                pd.Series([0] * len(self.actions), index=self.q_table.columns, name=state))


class ZergAgent(base_agent.BaseAgent):
    def transformLocation(self, x, x_distance, y, y_distance):
        if not self.base_top_left:
            return [x - x_distance, y - y_distance]
        return [x + x_distance, y + y_distance]

    def step(self, obs):
        super(ZergAgent, self).step(obs)


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
                    visualize=False) as env:

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






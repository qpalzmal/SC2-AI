from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.lib import actions, features, units
from absl import app
import random
import math
import numpy as np
import pandas as pd


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
    def __init__(self):
        super(ZergAgent, self).__init__()

        self.attack_coordinates = None

        # list of actions for agent to do
        self.smart_actions = ["donothing",
                              "selectdrone",
                              "trainoverlord",
                              "buildspawningpool",
                              "selectlarva",
                              "trainroach",
                              "traindrone",
                              "selectarmy",
                              "attack",
                              "buildroachwarren",
                              "buildextractor",
                              "trainzergling"]

        self.qlearn = QLearningTable(actions=list(range(len(self.smart_actions))))

    # checks if the current unit type is selected
    def unit_type_is_selected(self, obs, unit_type):
        # if something is selected and checks to see if the first selecting thing is same as passed unit type
        if len(obs.observation.single_select) > 0 and obs.observation.single_select[0].unit_type == unit_type \
                or len(obs.observation.multi_select) > 0 and obs.observation.multi_select[0].unit_type == unit_type:
            print("SOMETHING GOOD HAPPENED")
            return True
        else:
            print("SOMETHING BAD HAPPENED")
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

    def select_larva(self, obs):
        larvae = self.get_units_by_type(obs, units.Zerg.Larva)
        if len(larvae) > 0:
            larva = random.choice(larvae)
            return actions.FUNCTIONS.select_point("select_all_type", (larva.x, larva.y))

    def select_drone(self, obs):
        drones = self.get_units_by_type(obs, units.Zerg.Drone)
        if len(drones) > 0:
            drone = random.choice(drones)
            # "select_all_type" works like ctrl clicking and drone's (x,y) is passed
            return actions.FUNCTIONS.select_point("select_all_type", (drone.x, drone.y))

    # step() is similar to on_step() from sc2 library
    def step(self, obs):
        super(ZergAgent, self).step(obs)

        # obs.first() checks if its first step
        # hard coded to find the player start location - only works on abyssalreef
        if obs.first():
            player_y, player_x = (
                    obs.observation.feature_minimap.player_relative == features.PlayerRelative.SELF).nonzero()

            x_mean = player_x.mean()
            y_mean = player_y.mean()

            # gets the targeted attack coordinate based on where player spawned
            # only works for AbyssalReef
            if x_mean <= 31 and y_mean <= 31:
                # attack bottom right
                # spawned top left
                self.attack_coordinates = (49, 49)
                self.base_x = 12
                self.base_y = 16
            else:
                # attack top left
                # spawned bottom right
                self.attack_coordinates = (12, 16)
                self.base_x = 49
                self.base_y = 49

        # generates a random action for the agent to execute
        smart_action = self.smart_actions[random.randrange(0, len(self.smart_actions))]
        print(smart_action)

        # gets the current game state

        # current_state = [overlord_count,
        #                  supply_limit,
        #                  army_supply]

        # agent does nothing
        if smart_action == "donothing":
            return actions.FUNCTIONS.no_op()

        # creates overlord if supply <= 4 and all criteria met
        elif smart_action == "trainoverlord":
            self.select_larva(obs)
            supply_left = obs.observation.player.food_cap - obs.observation.player.food_used
            if supply_left <= 4 and self.unit_type_is_selected(obs, units.Zerg.Larva) \
                    and self.can_do(obs, actions.FUNCTIONS.Train_Overlord_quick.id):
                return actions.FUNCTIONS.Train_Overlord_quick("now")

        # elif smart_action == "buildextractor":
        #     self.select_drone(obs)
        #     if self.unit_type_is_selected(obs, units.Zerg.Drone) \
        #             and self.can_do(obs, actions.FUNCTIONS.Build_Extractor_screen.id):
        #         x = 0
        #         y = 0
        #         return actions.FUNCTIONS.Build_Extractor_screen("now", (x, y))

        # creates 1 spawning pool if all criteria met
        elif smart_action == "buildspawningpool":
            spawning_pools = self.get_units_by_type(obs, units.Zerg.SpawningPool)
            print("CHECKING AMOUNT OF SPAWNING POOLS")
            if len(spawning_pools) == 0:
                print("TRYING TO SELECT A DRONE")
                self.select_drone(obs)
                print("GOT A DRONE")
                if self.unit_type_is_selected(obs, units.Zerg.Drone):
                    # if self.can_do(obs, actions.FUNCTIONS.Build_SpawningPool_screen.id):
                    #     x = random.randint(0, 83)
                    #     y = random.randint(0, 83)
                    #     return actions.FUNCTIONS.Build_SpawningPool_screen("now", (x, y))
                    print("IM GOING TO START BUILDING A SPAWNING POOL")
                    if self.can_do(obs, actions.FUNCTIONS.Build_SpawningPool_screen.id):
                        x = random.randint(self.base_x - 5, self.base_x + 5)
                        y = random.randint(self.base_y - 5, self.base_y + 5)
                        print("GOT THESE COORDINATES: ", x, " ", y)
                        return actions.FUNCTIONS.Build_SpawningPool_screen("now", (x, y))

        # creates 1 roach warren if all criteria met
        elif smart_action == "buildroachwarren":
            roach_warrens = self.get_units_by_type(obs, units.Zerg.RoachWarren)
            if len(roach_warrens) == 0:
                self.select_drone(obs)
                if self.unit_type_is_selected(obs, units.Zerg.Drone) \
                        and self.can_do(obs, actions.FUNCTIONS.Build_RoachWarren_screen.id):
                    x = random.randint(self.base_x - 5, self.base_x + 5)
                    y = random.randint(self.base_y - 5, self.base_y + 5)
                    print("GOT THESE COORDINATES: ", x, " ", y)
                    return actions.FUNCTIONS.Build_RoachWarren_screen("now", (x, y))

        elif smart_action == "traindrone":
            self.select_larva(obs)
            if self.unit_type_is_selected(obs, units.Zerg.Larva) \
                    and self.can_do(obs, actions.FUNCTIONS.Train_Drone_quick.id):
                return actions.FUNCTIONS.Train_Drone_quick("now")

        elif smart_action == "trainzergling":
            self.select_larva(obs)
            if self.unit_type_is_selected(obs, units.Zerg.Larva) \
                    and self.can_do(obs, actions.FUNCTIONS.Train_Zergling_quick.id):
                return actions.FUNCTIONS.Train_Zergling_quick("now")

        # creates roaches if all criteria met
        elif smart_action == "trainroach":
            self.select_larva(obs)
            if self.unit_type_is_selected(obs, units.Zerg.Larva) \
                    and self.can_do(obs, actions.FUNCTIONS.Train_Roach_quick.id):
                return actions.FUNCTIONS.Train_Roach_quick("now")

        # attack with roaches
        elif smart_action == "attack":
            # roaches = self.get_units_by_type(obs, units.Zerg.Roach)
            # if len(roaches) > 10:
            # # select the roaches since they aren't selected
            # if self.can_do(obs, actions.FUNCTIONS.select_army.id):
            #     return actions.FUNCTIONS.select_army("select")
            # attacks with all roaches if they are selected
            roaches = self.get_units_by_type(obs, units.Zerg.Roach)
            if self.unit_type_is_selected(obs, units.Zerg.Roach) and len(roaches) >= 10:
                if self.can_do(obs, actions.FUNCTIONS.Attack_minimap.id):
                    return actions.FUNCTIONS.Attack_minimap("now", self.attack_coordinates)

            # used to force select the army
            elif not self.unit_type_is_selected(obs, units.Zerg.Roach):
                if self.can_do(obs, actions.FUNCTIONS.select_army.id):
                    return actions.FUNCTIONS.select_army("select")
                if self.can_do(obs, actions.FUNCTIONS.Attack_minimap.id) and len(roaches) >= 10:
                    return actions.FUNCTIONS.Attack_minimap("now", self.attack_coordinates)

        # selects the roaches
        elif smart_action == "selectarmy":
            # roaches = self.get_units_by_type(obs, units.Zerg.Roach)
            # if len(roaches) > 10:
            # attacks with all roaches if they are selected
            # if self.unit_type_is_selected(obs, units.Zerg.Roach) \
            #  and self.can_do(obs, actions.FUNCTIONS.Attack_minimap.id):
            #     return actions.FUNCTIONS.Attack_minimap("now", self.attack_coordinates)
            # select the roaches since they aren't selected
            if self.can_do(obs, actions.FUNCTIONS.select_army.id):
                return actions.FUNCTIONS.select_army("select")

        # selects random larva
        elif smart_action == "selectlarva":
            self.select_larva(obs)

            # larvae = self.get_units_by_type(obs, units.Zerg.Larva)
            # if len(larvae) > 0:
            #     larva = random.choice(larvae)
            #     return actions.FUNCTIONS.select_point("select_all_type", (larva.x, larva.y))

            # pass

        # selects random drone
        elif smart_action == "selectdrone":
            self.select_drone(obs)

            # drones = self.get_units_by_type(obs, units.Zerg.Drone)
            # if len(drones) > 0:
            #     drone = random.choice(drones)
            #     # "select_all_type" works like ctrl clicking and drone's (x,y) is passed
            #     return actions.FUNCTIONS.select_point("select_all_type", (drone.x, drone.y))

            # pass

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

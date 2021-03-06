import sc2
from sc2 import run_game, maps, Race, Difficulty, position, Result
from sc2.constants import *
from sc2.player import Bot, Computer, Human
import cv2
import numpy as np
import random
import time
import keras
import sys
import pprint

HEADLESS = False


class Protoss_Death_Ball(sc2.BotAI):
    def __init__(self):
        sc2.BotAI.__init__(self)
        self.built_natural = False
        self.built_first_pylon = False
        self.delay = 0
        # 1 second =  2.5 iteration
        self.four_minutes_iteration = 600
        self.use_model = False
        self.train_data = []

        # army composition
        self.unit_type = [STALKER, IMMORTAL, COLOSSUS]

        # list containing structures to chrono boost -- top bottom priority
        self.structures = [
            CYBERNETICSCORE,
            TWILIGHTCOUNCIL,
            FORGE,
            ROBOTICSBAY,
            NEXUS,
            ROBOTICSFACILITY,
            WARPGATE
        ]

        # forge upgrades -- index priority
        self.upgrade_list = [
            AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1,
            AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL2,
            AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL3,

            AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1,
            AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2,
            AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL3,

            AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL1,
            AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL2,
            AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL3
        ]

        # list of units that will be drawn
        self.draw_dict_units = [
            # structures
            NEXUS,
            PYLON,
            ASSIMILATOR,
            GATEWAY,
            CYBERNETICSCORE,
            WARPGATE,
            FORGE,
            ROBOTICSFACILITY,
            ROBOTICSBAY,
            TWILIGHTCOUNCIL,

            # units
            PROBE,
            STALKER,
            IMMORTAL,
            COLOSSUS,
            OBSERVER
        ]

        # values for how to draw the units
        # [SIZE, (BLUE, GREEN, RED)]
        self.draw_dict = {
            # structures
            NEXUS: [15, (0, 255, 0)],
            PYLON: [2, (30, 255, 0)],
            ASSIMILATOR: [3, (15, 255, 0)],
            GATEWAY: [5, (100, 255, 0)],
            CYBERNETICSCORE: [4, (45, 255, 0)],
            WARPGATE: [5, (100, 255, 0)],
            FORGE: [4, (60, 255, 0)],
            ROBOTICSFACILITY: [5, (125, 255, 0)],
            ROBOTICSBAY: [4, (75, 255, 0)],
            TWILIGHTCOUNCIL: [4, (90, 255, 0)],

            # units
            PROBE: [1, (255, 100, 0)],
            STALKER: [6, (255, 75, 0)],
            IMMORTAL: [7, (255, 50, 0)],
            COLOSSUS: [8, (255, 25, 0)],
            OBSERVER: [2, (255, 125, 0)]
        }

        if self.use_model:
            print("Using Model")
            self.model = keras.models.load_mode("BasicCNN-30-epochs-0.0001-LR-42")

    # saves the data if ai won game
    def on_end(self, game_result):
        # print("---- on_end called ----")
        # print(game_result)

        if game_result == Result.Victory:
            np.save("Training Data/{}.npy".format(str(int(time.time()))), np.array(self.train_data))

    # on_step function is called for every game step
    # it takes current game state and iteration
    async def on_step(self, iteration):

        if iteration == 0:
            await self.chat_send("glhf")

        # await self.chat_send(("Iteration: " + str(iteration)))

        await self.intel()
        await self.scout()
        await self.build_tech()
        await self.research_upgrades()
        await self.distribute_workers()
        await self.build_workers()
        await self.build_supply()
        await self.chronoboost()
        await self.build_assimilator()
        # await self.transform_gateways()
        await self.build_army()
        await self.command_army(iteration)

        # expands
        if self.units(NEXUS).amount < 2 and not self.already_pending(NEXUS) and self.can_afford(NEXUS):
            self.built_natural = True
            await self.expand_now()
        # expands every 4 minutes after the 2nd nexus
        elif self.units(NEXUS).amount >= 2 and not self.already_pending(NEXUS) and self.can_afford(NEXUS)\
                and iteration % self.four_minutes_iteration == 0:
            self.four_minutes_iteration += 600
            # await self.chat_send("Building Nexus")
            await self.expand_now()

        # sends observer to enemy base
        for observer in self.units(OBSERVER).idle:
            await self.do(observer.move(self.enemy_start_locations[0]))

    async def intel(self):
        # arrays are y - x images are x - y so flip array to image
        # game data is the image
        game_data = np.zeros((self.game_info.map_size[1], self.game_info.map_size[0], 3), np.uint8)

        # draws opponent's units
        main_bases = ["NEXUS", "COMMANDCENTER", "PLANETARYFORTRESS", "ORBITALCOMMAND", "HATCHERY", "LAIR", "HIVE"]
        # draws opponent's main base as big circle and other structures as small ones
        for enemy_structure in self.known_enemy_structures:
            pos = enemy_structure.position
            if enemy_structure.name in main_bases:
                cv2.circle(game_data, (int(pos[0]), int(pos[1])), radius=15, color=(0, 0, 255))
            else:
                cv2.circle(game_data, (int(pos[0]), int(pos[1])), radius=5, color=(155, 0, 255))
        workers = ["PROBE", "SCV", "DRONE"]
        # draws opponent's workers as small circles and other units as big ones
        for enemy_unit in self.known_enemy_units:
            pos = enemy_unit.position
            if enemy_unit.name in workers:
                cv2.circle(game_data, (int(pos[0]), int(pos[1])), radius=1, color=(155, 155, 255))
            else:
                cv2.circle(game_data, (int(pos[0]), int(pos[1])), radius=5, color=(55, 55, 255))

        # draws own units
        for unit_type in self.draw_dict_units:
            if self.units(unit_type).ready.amount >= 1:
                for unit in self.units(unit_type).ready:
                    unit_pos = unit.position
                    # enters the (x, y) position, size, and color parameters to draw a circle
                    cv2.circle(game_data, (int(unit_pos[0]), int(unit_pos[1])), radius=self.draw_dict[unit_type][0],
                               color=self.draw_dict[unit_type][1])

        line_max = 50

        # mineral ratio
        mineral_ratio = self.minerals / 1100
        if mineral_ratio > 1.0:
            mineral_ratio = 1.0

        vespene_ratio = self.vespene / 900
        if vespene_ratio > 1.0:
            vespene_ratio = 1.0

        current_supply_ratio = self.supply_used / self.supply_cap
        if current_supply_ratio > 1.0:
            current_supply_ratio = 1.0

        max_supply_ratio = self.supply_used / 200
        if max_supply_ratio > 1.0:
            max_supply_ratio = 1.0

        worker_ratio = len(self.units(PROBE).ready) / self.supply_used
        if worker_ratio > 1.0:
            worker_ratio = 1.0

        # mineral ratio
        cv2.line(game_data, (0, 3), (int(line_max * mineral_ratio), 3), (250, 250, 250), 3)
        # vespene ratio
        cv2.line(game_data, (0, 7), (int(line_max * vespene_ratio), 7), (200, 200, 200), 3)
        # current supply ratio
        cv2.line(game_data, (0, 10), (int(line_max * current_supply_ratio), 10), (150, 150, 150), 3)
        # max supply ratio
        cv2.line(game_data, (0, 10), (int(line_max * max_supply_ratio), 10), (100, 100, 100), 3)
        # worker
        cv2.line(game_data, (0, 10), (int(line_max * worker_ratio), 10), (50, 50, 50), 3)

        self.flipped = cv2.flip(game_data, 0)

        if not HEADLESS:
            resized = cv2.resize(self.flipped, dsize=None, fx=2, fy=2)
            cv2.imshow("Intel", resized)
            cv2.waitKey(1)

    def random_location(self, enemy_start_location):
        # start locations is a list of points
        x = enemy_start_location[0]
        y = enemy_start_location[1]

        # generates random coordinates around the enemy start location
        x += ((random.randrange(-20, 20)) / 100) * enemy_start_location[0]
        y += ((random.randrange(-20, 20)) / 100) * enemy_start_location[1]

        # keeps coordinates in side map coordinates
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if x > self.game_info.map_size[0]:
            x = self.game_info.map_size[0]
        if y > self.game_info.map_size[1]:
            y = self.game_info.map_size[1]

        new_location = position.Point2(position.Pointlike((x, y)))
        return new_location

    async def scout(self):
        for observer in self.units(OBSERVER).ready:
            if observer.is_idle:
                enemy_location = self.enemy_start_locations[0]
                random_location = self.random_location(enemy_location)
                # print(random_location)
                await self.do(observer.move(random_location))

    # checks all nexus if they are queued up, if not queue up a probe up to 20 per base to a max of 50
    async def build_workers(self):
        if self.units(PROBE).amount <= 40 and self.units(NEXUS).ready:
            for nexus in self.units(NEXUS).ready.noqueue:
                if self.can_afford(PROBE) and self.units(NEXUS).ready.amount * 20 > self.units(PROBE).amount:
                    await self.do(nexus.train(PROBE))

    # builds a pylon on demand
    async def build_supply(self):
        if self.built_natural is False:
            supply_left = 6
        else:
            supply_left = 12
        if not self.already_pending(PYLON) and self.supply_left <= supply_left:
            nexus = self.units(NEXUS).ready
            if nexus.exists and self.can_afford(PYLON):
                self.built_first_pylon = True
                await self.build(PYLON, near=nexus.random)
        # puts pylon in middle of map to stall a loss
        if self.units(NEXUS).amount == 0:
            await self.build(PYLON, near=self.game_info.map_center)

    # builds assimilator if there are any gateways
    async def build_assimilator(self):
        for nexus in self.units(NEXUS).ready:
            # finds all the vespene geyser that is by each nexus
            self.vespene_geysers = self.state.vespene_geyser.closer_than(20.0, nexus)
            for vespene_geyser in self.vespene_geysers:
                # checks if can afford to make assmililator and there is already a gateway warping in
                if self.can_afford(ASSIMILATOR) and self.already_pending(GATEWAY) or self.units(GATEWAY).ready.exists:
                    # checks if there is already a assimilator at the geyser, if not builds an assimilator
                    worker = self.select_build_worker(vespene_geyser.position, force=True)
                    if not self.units(ASSIMILATOR).closer_than(5.0, vespene_geyser).exists:
                        await self.do(worker.build(ASSIMILATOR, vespene_geyser))

    async def build_tech(self):
        # builds 1 gate if on 1 nexus then up to 3 per nexus at 2 nexus and up
        if self.units(PYLON).ready.exists and self.can_afford(GATEWAY) and self.units(NEXUS).ready:
            if self.built_natural and self.units(NEXUS).amount - self.units(GATEWAY).amount > -1:
                await self.build(GATEWAY, near=self.units(PYLON).ready.random, max_distance=6)
            elif self.units(GATEWAY).amount < 1:
                await self.build(GATEWAY, near=self.units(PYLON).ready.random, max_distance=6)

        # builds a robo if there is a pylon/cybernetics, can afford one, and on 2 bases or more
        if self.units(PYLON).ready.exists and self.units(NEXUS).amount - self.units(ROBOTICSFACILITY).amount > 1 \
                and self.can_afford(ROBOTICSFACILITY) and self.units(CYBERNETICSCORE).ready:
            await self.build(ROBOTICSFACILITY, near=self.units(PYLON).ready.random, max_distance=6)

        # builds a forge if there is already a pylon/gateway/cybernetics/nexus and can afford one
        if self.units(NEXUS).ready and self.units(PYLON).ready and self.units(GATEWAY).ready \
                and self.units(CYBERNETICSCORE).ready and self.can_afford(FORGE) and not self.already_pending(FORGE) \
                and not self.units(FORGE).exists and self.built_natural:
            await self.build(FORGE, near=self.units(PYLON).ready.random, max_distance=6)

        # builds a twilight if there is already a pylon/cybernetics and can afford one
        if self.units(CYBERNETICSCORE).ready and self.units(PYLON).ready and not self.already_pending(TWILIGHTCOUNCIL) \
                and self.can_afford(TWILIGHTCOUNCIL) and self.built_natural and not self.units(TWILIGHTCOUNCIL).exists:
            await self.build(TWILIGHTCOUNCIL, near=self.units(PYLON).ready.random, max_distance=6)

        # builds a cybernetics if there is already a gateway and can afford one
        if not self.units(CYBERNETICSCORE).exists and self.units(GATEWAY).ready.exists \
                and self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
            await self.build(CYBERNETICSCORE, near=self.units(PYLON).ready.random, max_distance=6)

    async def research_upgrades(self):
        # researches warpgate
        if self.units(CYBERNETICSCORE).ready.amount >= 1:
            abilities = await self.get_available_abilities(self.units(CYBERNETICSCORE).ready.noqueue)
            if AbilityId.RESEARCH_WARPGATE in abilities:
                if self.units(CYBERNETICSCORE).ready.noqueue and self.can_afford(RESEARCH_WARPGATE):
                    await self.do(self.units(CYBERNETICSCORE).ready.first(RESEARCH_WARPGATE))
                    # await self.chat_send("Researching Warpgate")

        # researches blink
        # if self.units(TWILIGHTCOUNCIL).ready and self.can_afford(RESEARCH_BLINK) and self.built_natural:
        #     await self.do(self.units(TWILIGHTCOUNCIL).ready.first(RESEARCH_BLINK))
            # await self.chat_send("Researching Blink")

        # researches thermal lance
        # if self.units(ROBOTICSBAY).ready and self.can_afford(RESEARCH_THERMALLANCE) and self.units(NEXUS).amount == 3:
        #     await self.do(self.units(ROBOTICSBAY).ready.first(RESEARCH_THERMALLANCE))
            # await self.chat_send("Researching Thermal Lance")

        # researches weapon, armor, shield in that order
        if self.units(FORGE).ready and self.built_natural and self.units(FORGE).noqueue and self.supply_used >= 75:
            forge = self.units(FORGE).ready.first
            abilities = await self.get_available_abilities(forge)
            for upgrade in range(len(self.upgrade_list)):
                if self.upgrade_list[upgrade] in abilities and self.can_afford(self.upgrade_list[upgrade]):
                    await self.do(forge(self.upgrade_list[upgrade]))
                    # await self.chat_send("Researching Forge Upgrade")

    # transforms the gateways to warpgates
    # async def transform_gateways(self):
    #     for gateway in self.units(GATEWAY).ready:
    #         abilities = await self.get_available_abilities(gateway)
    #         if AbilityId.MORPH_WARPGATE in abilities and self.can_afford(AbilityId.MORPH_WARPGATE):
    #             await self.do(gateway(MORPH_WARPGATE))
                # await self.chat_send("Transforming Gateways")

    # chronos structures
    async def chronoboost(self):
        for nexus in self.units(NEXUS).ready:
            abilities = await self.get_available_abilities(nexus)
            # chronos stuff in priority order
            # checks if there is energy for chrono, building is ready, building is queued, not already chronoed
            if AbilityId.EFFECT_CHRONOBOOST in abilities:
                for structure in self.structures:
                    if self.units(structure).ready and self.can_afford(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST) \
                         and self.units(structure).noqueue is False and self.built_first_pylon\
                            and not structure.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                        await self.do(nexus(BuffId.CHRONOBOOSTENERGYCOST, self.units(structure).first))

                        await self.chat_send("Chronoing stuff")

    # makes units
    async def build_army(self):
        if self.units(CYBERNETICSCORE).ready.exists:
            # gateway section
            for gateway in self.units(GATEWAY).ready.noqueue:
                # ONE ROUND OF PRODUCTION
                if self.built_natural:
                    # queues all stalkers at same time from non queued up gateways
                    gateway_count = self.units(GATEWAY).ready.noqueue.amount
                    if self.minerals >= gateway_count * 125 and self.vespene >= gateway_count * 50:
                        # if self.can_afford(STALKER) and self.supply_left >= 2:
                            await self.do(gateway.train(STALKER))
                            # await self.chat_send("GATEWAY Stalkers")

                # CONSTANT PRODUCTION
                # if self.can_afford(STALKER) and self.supply_left >= 2:
                #     await self.do(gateway.train(STALKER))

            # warpgate section
            if self.units(WARPGATE).ready.exists and self.built_natural:
                warpgate_count = self.units(WARPGATE).ready.amount

                for warpgate in self.units(WARPGATE).ready:
                    abilities = await self.get_available_abilities(warpgate)
                    if AbilityId.WARPGATETRAIN_STALKER in abilities:
                        # gets initial position for stalker warp-in then moves with a placements step for next warps
                        if self.supply_left >= 2:
                            # ONE ROUND OF PRODUCTION
                            if self.minerals >= len(self.units(WARPGATE).ready) * 125\
                             and self.vespene >= warpgate_count * 50:
                                position = self.units(PYLON).ready.random.position.to2.random_on_distance(4)
                                placement = await self.find_placement(WARPGATETRAIN_STALKER, position, placement_step=2)
                                if placement is None:
                                    break
                                await self.do(warpgate.warp_in(STALKER, placement))
                            #     # await self.chat_send("WARPGATE STALKER")

                            # CONSTANT PRODUCTION
                            # if self.can_afford(STALKER):
                            #     position = self.units(PYLON).ready.random.position.to2.random_on_distance(4)
                            #     placement = await self.find_placement(WARPGATETRAIN_STALKER, position, placement_step=2)
                            #     if placement is None:
                            #         break
                            #     await self.do(warpgate.warp_in(STALKER, placement))
                                # await self.chat_send("WARPGATE STALKER")

        # creates observers/immortal/colossus from robos
        if self.units(ROBOTICSFACILITY).ready.exists:
            for robo in self.units(ROBOTICSFACILITY).ready.noqueue:
                robo_count = self.units(ROBOTICSFACILITY).ready.noqueue.amount

                # queues up all observers at same time from non queued robos
                # always makes 1 observers
                if self.supply_left >= 1 and self.units(OBSERVER).amount < 2:
                    # ONE ROUND OF PRODUCTION
                    if self.minerals >= robo_count * 25 and self.vespene >= robo_count * 75:
                        await self.do(robo.train(OBSERVER))

                    # CONSTANT PRODUCTION
                    # if self.can_afford(OBSERVER):
                    #     await self.do(robo.train(OBSERVER))

                # queues up all immortals at same time from non queued robos
                # keeps a 2:1 ratio of immortals to colossus
                if self.supply_left >= 4 and int(self.units(IMMORTAL).amount / 2) <= self.units(COLOSSUS).amount:
                    # ONE ROUND OF PRODUCTION
                    if self.minerals >= robo_count * 250 and self.vespene >= robo_count * 100:
                        await self.do(robo.train(IMMORTAL))
                    # await self.chat_send("Building Immortal")

                    # CONSTANT PRODUCTION
                    # if self.can_afford(IMMORTAL):
                    #     await self.do(robo.train(IMMORTAL))

                # queues up all colo at same time fron non queued robos
                if self.supply_left >= 6:
                    # ONE ROUND OF PRODUCTION
                    if self.minerals >= robo_count * 300 and self.vespene >= robo_count * 200:
                        await self.do(robo.train(COLOSSUS))

                    # CONSTANT PRODUCTION
                    # if self.can_afford(COLOSSUS):
                    #     await self.do(robo.train(COLOSSUS))
                    # await self.chat_send("Building Colossus")

    async def command_army(self, iteration):
        target = False
        if iteration > self.delay:
            # uses the model otherwise falls back to generating random choice 1-4
            if self.use_model:
                prediction = self.model.predict([self.flipped.reshape([-1, 176, 200, 3])])
                choice = np.argmax(prediction[0])

                choice_dict = {0: "No attack",
                               1: "Attack closest to our nexus",
                               2: "Attack ene structures",
                               3: "Attack enemy start"}

                print("Choice #{}:{}".format(choice, choice_dict[choice]))
            else:
                choice = random.randrange(0, 4)

            # doesn't attack
            if choice == 0:
                wait_time = random.randrange(75, 150)
                self.delay = iteration + wait_time

            # attacks units closest to a random nexus
            elif choice == 1:
                if len(self.known_enemy_units) > 0:
                    target = self.known_enemy_units.closest_to(self.units(NEXUS).random)

            # attacks a random enemy building
            elif choice == 2:
                if len(self.known_enemy_structures) > 0:
                    target = self.known_enemy_structures.random

            # attacks the enemy start location
            elif choice == 3:
                target = self.enemy_start_locations[random.randrange(0, len(self.enemy_start_locations))]

            if target:
                for unit_type in self.unit_type:
                    if self.units(unit_type).ready.amount > 0:
                        for unit in self.units(unit_type).idle:
                            await self.do(unit.attack(target))

            # appends data to training data
            y = np.zeros(4)
            y[choice] = 1
            self.train_data.append([y, self.flipped])


# reads from a file contains names of maps and appends them to a map list
map_list = []
map_file = open("Maps.txt")
for line in map_file:
    word = ""
    # removes the "n" from "\n" at every line
    # the last map on the file needs to have a blank line after or the last letter will cut off
    for character in line[:len(line) - 1]:
        # print("CHARACTER", character)
        word += character
        # print("WORD IN PROGRESS", word)
    # print("FINAL WORD", word)
    map_list.append(word)
map_file.close()
# pprint.pprint(map_list)


# function used to get a random map, check if the user has it, then returns that map
def map_finder(map_name):
    # used to remove a map the user doesn't have
    temp_map = map_list[random.randrange(0, len(map_list))]
    if map_name and len(map_list) > 1 or temp_map == map_name:
        map_list.remove(map_name)

    # tries to get a random map from the list if error then user has none of the maps AI can play on
    try:
        map_name = map_list[random.randrange(0, len(map_list))]
    except ValueError:
        print("You don't have any maps the AI can play on")
        sys.exit(1)

    # recursion to see if the user has the map generated
    print("RANDOM MAP: ", map_name)
    try:
        map = maps.get(map_name)
        print("GOT THIS MAP: ", map_name)
        return map
    except KeyError:
        print("MISSING MAP: ", map_name)
        return map_finder(map_name)


# enters map, list of players, and game speed
def main():
    run_game(map_finder(map_list[random.randrange(0, len(map_list))]), [
        Bot(Race.Protoss, Protoss_Death_Ball()),
        Computer(Race.Random, Difficulty.Easy)
        # Human(Race.Random)
        ], realtime=True)


if __name__ == "__main__":
    main()

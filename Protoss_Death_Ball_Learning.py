import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer \
    # ,Human
import cv2
import numpy as np


class MassStalkerBot(sc2.BotAI):
    def __init__(self):
        sc2.BotAI.__init__(self)
        self.built_natural = False
        self.built_first_pylon = False
        self.warpgate_count = 0
        self.four_minutes_iteration = 600
        self.unit_type = [STALKER, IMMORTAL, COLOSSUS]
            # , OBSERVER]
        self.structures = [
            CYBERNETICSCORE,
            TWILIGHTCOUNCIL,
            FORGE,
            ROBOTICSBAY,
            NEXUS,
            ROBOTICSFACILITY,
            WARPGATE
        ]

        self.upgrade_list = [
            AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1,
            AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1,
            AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL1,
            AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2,
            AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2,
            AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL2,
            AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL3,
            AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL3,
            AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL3
        ]

        # [SIZE, (BLUE, GREEN, RED)]
        self.draw_dict = {
            # structures
            NEXUS: [15, (0, 255, 0)],
            PYLON: [2, (30, 255, 0)],
            ASSIMILATOR: [3, (15, 255, 0)],
            GATEWAY: [5, (100, 255, 0)],
            CYBERNETICSCORE: [36, (45, 255, 0)],
            WARPGATE: [5, (100, 255, 0)],
            FORGE: [4, (60, 255, 0)],
            ROBOTICSFACILITY: [5, (125, 255, 0)],
            ROBOTICSBAY: [4, (75, 255, 0)],
            TWILIGHTCOUNCIL: [4, (90, 255, 0)],

            # units
            PROBE: [1, (255, 100, 0)],
            OBSERVER: [2, (255, 115, 0)],
            STALKER: [6, (255, 75, 0)],
            IMMORTAL: [7, (255, 50, 0)],
            COLOSSUS: [8, (255, 25, 0)]
        }

    # on_step function is called for every game step
    # it takes current game state and iteration
    async def on_step(self, iteration):

        if iteration == 0:
            await self.chat_send("glhf")

        # await self.chat_send(("Iteration: " + str(iteration)))

        await self.intel()
        await self.distribute_workers()
        await self.build_workers()
        await self.build_supply()
        await self.chronoboost()
        await self.build_assimilator()
        await self.build_gateways()
        await self.build_robo()
        await self.build_cybernetics()
        await self.build_forge()
        await self.build_twilight()
        await self.transform_gateways()
        await self.build_army()

        # expands
        if self.units(NEXUS).amount < 2 and not self.already_pending(NEXUS) and self.can_afford(NEXUS):
            self.built_natural = True
            await self.expand_now()
        # expands every 4 minutes after the 2nd nexus
        elif self.units(NEXUS) >= 2 and not self.already_pending(NEXUS) and self.can_afford(NEXUS)\
                and iteration % self.four_minutes_iteration == 0:
            self.four_minutes_iteration += 600
            await self.chat_send("Building Nexus")
            await self.expand_now()

        # researches warpgate
        if self.units(CYBERNETICSCORE).ready.noqueue and self.can_afford(RESEARCH_WARPGATE):
            await self.do(self.units(CYBERNETICSCORE).ready.first(RESEARCH_WARPGATE))
            await self.chat_send("Researching Warpgate")

        # researches blink
        if self.units(TWILIGHTCOUNCIL).ready and self.can_afford(RESEARCH_BLINK) and self.built_natural:
            await self.do(self.units(TWILIGHTCOUNCIL).ready.first(RESEARCH_BLINK))
            await self.chat_send("Researching Blink")

        # researches thermal lance
        if self.units(ROBOTICSBAY).ready and self.can_afford(RESEARCH_THERMALLANCE) and self.units(NEXUS).amount == 3:
            await self.do(self.units(ROBOTICSBAY).ready.first(RESEARCH_THERMALLANCE))
            await self.chat_send("Researching Thermal Lance")

        # researches weapon, armor, shield in that order
        if self.units(FORGE).ready and self.built_natural and self.units(FORGE).noqueue:
            forge = self.units(FORGE).ready.first
            abilities = await self.get_available_abilities(forge)
            for upgrade in range(len(self.upgrade_list)):
                if self.upgrade_list[upgrade] in abilities and self.can_afford(self.upgrade_list[upgrade]):
                    await self.do(forge(self.upgrade_list[upgrade]))
                    await self.chat_send("Researching Forge Upgrade")

        # sends observer to enemy base
        for observer in self.units(OBSERVER).idle:
            await self.do(observer.move(self.enemy_start_locations[0]))

        # sets up observer to stationary mode
        for observer in self.units(OBSERVER).idle:
            abilities = self.get_available_abilities(observer)




            if AbilityId.MORPH_SURVEILLANCEMODE





        # moves idle units to a random nexus
        for unit_type in self.unit_type:
            for unit in self.units(unit_type).idle:
                await self.do(unit.move(self.units(NEXUS).random))

        # attacks with all units if supply is over 100
        if self.supply_used >= 100:
            for unit_type in self.unit_type:
                for unit in self.units(unit_type).idle:
                    if len(self.known_enemy_units) > 0:
                        await self.do(unit.attack(self.known_enemy_units))
                    elif len(self.known_enemy_structures) > 0:
                        await self.do(unit.attack(self.known_enemy_structures))
                    else:
                        await self.do(unit.attack(self.enemy_start_locations[0]))

        # sends army to attack known enemy units
        if len(self.known_enemy_units) > 0:
            for unit_type in self.unit_type:
                for unit in self.units(unit_type).idle:
                    await self.do(unit.attack(self.known_enemy_units))

        # low health stalkers will micro out of range and attack again
        if len(self.known_enemy_units) > 0:
            # for unit_type in self.army:
            for stalker in self.units(STALKER):
                abilities = await self.get_available_abilities(stalker)
                if stalker.health_percentage <= 10 and stalker.shield_percentage <= 10:
                    if AbilityId.EFFECT_BLINK in abilities:
                        await self.do(stalker(AbilityId.EFFECT_BLINK, self.units(NEXUS).first))
                        await self.do(stalker.move(self.units(NEXUS).first))
                    else:
                        # await self.do(stalker.move(not stalker.in_attack_range_of(self.known_enemy_units)))
                        await self.do(stalker.move(self.units(NEXUS).first))
                        # if not stalker.in_attack_range_of(self.known_enemy_units):
                        #     await self.do(stalker.attack(self.known_enemy_units))

    async def intel(self):
        # arrays are y - x images are x - y so flip array to image
        # game data is the image
        game_data = np.zeros((self.game_info.map_size[1], self.game_info.map_size[0], 3), np.uint8)
        for unit_type in self.draw_dict:
            for unit in self.units(unit_type).ready:
                unit_pos = unit.ready.position
                # enters the (x, y) position, size, and color parameters to draw a circle
                cv2.circle(game_data, (int(unit_pos[0]), int(unit_pos[1])),
                           self.draw_dict[unit_type[0]], self.draw_dict[unit_type[1]])



        flipped = cv2.flip(game_data, 0)
        resized = cv2.resize(flipped, dsize=None, fx=2, fy=2)
        cv2.imshow("Intel", resized)
        cv2.waitKey(1)

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

    # builds 1 gate if on 1 nexus then up to 3 per nexus at 2 nexus and up
    async def build_gateways(self):
        if self.units(PYLON).ready.exists and self.can_afford(GATEWAY) and self.units(NEXUS).ready:
            if self.built_natural and self.units(NEXUS).amount - self.units(GATEWAY).amount > -2:
                await self.build(GATEWAY, near=self.units(PYLON).ready.random, max_distance=6)
            elif self.units(GATEWAY).amount < 1:
                await self.build(GATEWAY, near=self.units(PYLON).ready.random, max_distance=6)

    # builds a robo if there is a pylon/nexus/cybernetics and can afford one
    async def build_robo(self):
        if self.units(PYLON).ready.exists and self.units(NEXUS).amount - self.units(ROBOTICSFACILITY).amount > 1 \
         and self.can_afford(ROBOTICSFACILITY) and self.units(CYBERNETICSCORE).ready:
            await self.build(ROBOTICSFACILITY, near=self.units(PYLON).ready.random, max_distance=6)

    # builds a forge if there is already a pylon/gateway/cybernetics/nexus and can afford one
    async def build_forge(self):
        if self.units(NEXUS).ready and self.units(PYLON).ready and self.units(GATEWAY).ready \
         and self.units(CYBERNETICSCORE).ready and self.can_afford(FORGE) and not self.already_pending(FORGE) \
         and not self.units(FORGE).exists and self.built_natural:
            await self.build(FORGE, near=self.units(PYLON).ready.random, max_distance=6)

    async def build_twilight(self):
        if self.units(CYBERNETICSCORE).ready and self.units(PYLON).ready and not self.already_pending(TWILIGHTCOUNCIL) \
         and self.can_afford(TWILIGHTCOUNCIL) and self.built_natural and not self.units(TWILIGHTCOUNCIL).exists:
            await self.build(TWILIGHTCOUNCIL, near=self.units(PYLON).ready.random, max_distance=6)

    # builds a cybernetics if there is a gateway and can afford
    async def build_cybernetics(self):
        if not self.units(CYBERNETICSCORE).exists and self.units(GATEWAY).ready.exists \
         and self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
            await self.build(CYBERNETICSCORE, near=self.units(PYLON).ready.random, max_distance=6)

    # transforms the gateways to warpgates
    async def transform_gateways(self):
        for gateway in self.units(GATEWAY).ready:
            abilities = await self.get_available_abilities(gateway)
            if AbilityId.MORPH_WARPGATE in abilities and self.can_afford(AbilityId.MORPH_WARPGATE):
                await self.do(gateway(MORPH_WARPGATE))
                await self.chat_send("Transforming Gateways")

    # chronos structures
    async def chronoboost(self):
        for nexus in self.units(NEXUS).ready:
            abilities = await self.get_available_abilities(nexus)
            # chronos stuff in priority order
            # first checks if there is energy for chrono and building is ready
            # then checks if building is queued and isn't already chronoed
            if AbilityId.EFFECT_CHRONOBOOST in abilities:
                for structure in self.structures:
                    if self.units(structure).ready:
                        if self.can_afford(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST) \
                         and self.units(structure).noqueue is False and self.built_first_pylon:
                            await self.do(nexus(AbilityId.EFFECT_CHRONOBOOST, self.units(structure).first))
                            await self.chat_send("Chronoing stuff")

    # makes units
    async def build_army(self):
        # gateway section
        if self.units(CYBERNETICSCORE).ready.exists:
            for gateway in self.units(GATEWAY).ready.noqueue:
                if self.built_natural:
                    # queues all stalkers at same time from non queued up gateways
                    gateway_count = self.units(GATEWAY).ready.noqueue.amount
                    if self.minerals >= gateway_count * 125 and self.vespene >= gateway_count * 50:
                        # if self.can_afford(STALKER) and self.supply_left >= 2:
                            await self.do(gateway.train(STALKER))
                            await self.chat_send("GATEWAY Stalkers")

                # CONSTANT PRODUCTION
                # if self.can_afford(STALKER):
                #     await self.do(gateway.train(STALKER))

            # warpgate section
            if self.units(WARPGATE).ready.exists and self.built_natural:
                for warpgate in self.units(WARPGATE).ready:
                    abilities = await self.get_available_abilities(warpgate)
                    if AbilityId.WARPGATETRAIN_STALKER in abilities:
                        self.warpgate_count += 1
                        if self.supply_left >= 2 and self.minerals >= self.warpgate_count * 125\
                                and self.vespene >= self.warpgate_count * 50:
                            # gets initial position for stalker warp-in then moves with a placements step for next warps
                            position = self.units(PYLON).ready.random.position.to2.random_on_distance(4)
                            placement = await self.find_placement(WARPGATETRAIN_STALKER, position, placement_step=2)
                            if placement is None:
                                break
                            await self.do(warpgate.warp_in(STALKER, placement))
                            await self.chat_send("WARPGATE STALKER")
        # creates observers from robos
        if self.units(ROBOTICSFACILITY).ready.exists:
            for robo in self.units(ROBOTICSFACILITY).ready.noqueue:
                # queues up all observers at same time from non queued robos
                robo_count = self.units(ROBOTICSFACILITY).ready.noqueue.amount
                # always makes 2 observers
                if self.supply_left >= 1 and self.minerals >= robo_count * 25 and self.vespene >= robo_count * 75 \
                    and self.units(OBSERVER).amount < 2:
                    await self.do(robo.train(OBSERVER))

        # makes immortals from robos
        if self.units(ROBOTICSFACILITY).ready.exists:
            for robo in self.units(ROBOTICSFACILITY).ready.noqueue:
                # queues up all immortals at same time from non queued robos
                robo_count = self.units(ROBOTICSFACILITY).ready.noqueue.amount
                # keeps a 2:1 ratio of immortals to colossus
                if self.supply_left >= 4 and self.minerals >= robo_count * 250 and self.vespene >= robo_count * 100\
                        and int(self.units(IMMORTAL).amount / 2) <= self.units(COLOSSUS).amount:
                    await self.do(robo.train(IMMORTAL))
                    await self.chat_send("Building Immortal")

        # makes colossus from robos
        if self.units(ROBOTICSFACILITY).ready.exists:
            for robo in self.units(ROBOTICSFACILITY).ready.noqueue:
                # queues up all colo at same time fron non queued robos
                robo_count = self.units(ROBOTICSFACILITY).ready.noqueue.amount
                if self.supply_left >= 6 and self.minerals >= robo_count * 300 and self.vespene >= robo_count * 200:
                    await self.do(robo.train(COLOSSUS))
                    await self.chat_send("Building Colossus")


def main():
    run_game(maps.get("(2)16-BitLE"), [
        # Human(Race.Protoss),
        Bot(Race.Protoss, MassStalkerBot()),
        Computer(Race.Protoss, Difficulty.VeryEasy)
    ], realtime=False)


if __name__ == "__main__":
    main()

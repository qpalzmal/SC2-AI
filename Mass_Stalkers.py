import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer\
    # ,Human


class MassStalkerBot(sc2.BotAI):
    def __init__(self):
        sc2.BotAI.__init__(self)
        self.built_natural = False
        self.built_first_pylon = False
        self.unit_type = [STALKER, IMMORTAL]
        self.upgrade_list = [
            AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1,
            AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1,
            AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL1,
            AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2,
            AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2,
            AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL2,
            AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL3,
            AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL3,
            AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL3]

    # on_step function is called for every game step
    # it takes current game state and iteration
    async def on_step(self, iteration):

        if iteration == 0:
            await self.chat_send("glhf")

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
        if self.units(NEXUS).amount < 3 and not self.already_pending(NEXUS) and self.can_afford(NEXUS):
            if self.units(NEXUS).amount == 2:
                self.built_natural = True
            await self.expand_now()

        # puts 2 probes on each gas
        # for assimilator in self.units(ASSIMILATOR):
        #     if assimilator.assigned_harvesters < 2 and assimilator.ready:
        #         worker = self.select_build_worker(assimilator.position)
        #         if worker.exists:
        #             await self.do(worker.gather(assimilator))

        # researches warpgate
        if self.units(CYBERNETICSCORE).ready and self.can_afford(RESEARCH_WARPGATE):
            await self.do(self.units(CYBERNETICSCORE).ready.first(RESEARCH_WARPGATE))

        # researches blink
        if self.units(TWILIGHTCOUNCIL).ready and self.can_afford(RESEARCH_BLINK) and self.built_natural:
            await self.do(self.units(TWILIGHTCOUNCIL).ready.first(RESEARCH_BLINK))

        # researches weapon, armor, shield in that order
        if self.units(FORGE).ready and self.built_natural and self.units(FORGE).noqueue:
            forge = self.units(FORGE).ready.first
            abilities = await self.get_available_abilities(forge)



            for upgrade in self.upgrade_list:
                if




            if AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1 in abilities\
                    and self.can_afford(AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1):
                await self.do(forge(AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1))
            elif AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1 in abilities \
                    and self.can_afford(AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1):
                await self.do(forge(AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1))
            elif AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL1 in abilities \
                    and self.can_afford(AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL1):
                await self.do(forge(AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL1))

        # moves idle units to a random nexus
        for unit_type in self.unit_type:
            for unit in self.units(unit_type).idle:
                await self.do(unit.move(self.units(NEXUS).random))

        # attacks with all units of that type if there are 25+ of them
        for unit_type in self.unit_type:
            if self.units(unit_type).amount >= 25:
                for unit in self.units(unit_type).idle:
                    if self.known_enemy_units.amount > 0:
                        await self.do(unit.attack(self.known_enemy_units))
                    elif self.known_enemy_structures.amount > 0:
                        await self.do(unit.attack(self.known_enemy_structures))
                    else:
                        await self.do(unit.attack(self.enemy_start_locations[0]))

        # ---- OLD DELETE LATER ----
        if self.units().amount.format() >= 25:
            for stalker in self.units(STALKER).idle:
                if self.known_enemy_units.amount > 0:
                    await self.do(stalker.attack(self.known_enemy_units))
                elif self.known_enemy_structures.amount > 0:
                    await self.do(stalker.attack(self.known_enemy_structures))
                else:
                    await self.do(stalker.attack(self.enemy_start_locations[0]))
        # ---- OLD DELETE LATER ----

        # sends stalkers to attack known enemy units
        # if self.known_enemy_units.amount > 0:
            # for unit_type in self.army:
            # for stalker in self.units(STALKER).idle:
            #     await self.do(stalker.attack(self.known_enemy_units))

        # low health stalkers will micro out of range and attack again
        # if self.known_enemy_units.amount > 0:
        #     # for unit_type in self.army:
        #     for stalker in self.units(STALKER).in_attack_range_of(self.known_enemy_units):
        #         if stalker.health_percentage <= 10 and stalker.shield_percentage <= 10:
        #             await self.do(stalker.move(not stalker.in_attack_range_of(self.known_enemy_units)))
        #             await self.do(stalker.attack(self.known_enemy_units))

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
            supply_left = 10
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
                    worker = self.select_build_worker(vespene_geyser.position)
                    if not self.units(ASSIMILATOR).closer_than(1.0, vespene_geyser).exists:
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
        if self.units(PYLON).ready.exists and self.units(NEXUS).amount - self.units(ROBOTICSFACILITY).amount > 1\
         and self.can_afford(ROBOTICSFACILITY) and self.units(CYBERNETICSCORE).ready:
            await self.build(ROBOTICSFACILITY, near=self.units(PYLON).ready.random, max_distance=6)

    # builds a forge if there is already a pylon/gateway/cybernetics/nexus and can afford one
    async def build_forge(self):
        if self.units(NEXUS).ready and self.units(PYLON).ready and self.units(GATEWAY).ready\
         and self.units(CYBERNETICSCORE).ready and self.can_afford(FORGE) and not self.already_pending(FORGE)\
         and not self.units(FORGE).exists and self.built_natural:
            await self.build(FORGE, near=self.units(PYLON).ready.random, max_distance=6)

    async def build_twilight(self):
        if self.units(CYBERNETICSCORE).ready and self.units(PYLON).ready and not self.already_pending(TWILIGHTCOUNCIL)\
         and self.can_afford(TWILIGHTCOUNCIL) and self.built_natural and not self.units(TWILIGHTCOUNCIL).exists:
            await self.build(TWILIGHTCOUNCIL, near=self.units(PYLON).ready.random, max_distance=6)

    # builds a cybernetics if there is a gateway and can afford
    async def build_cybernetics(self):
        if not self.units(CYBERNETICSCORE).exists and self.units(GATEWAY).ready.exists\
         and self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
            await self.build(CYBERNETICSCORE, near=self.units(PYLON).ready.random, max_distance=6)

    # transforms the gateways to warpgates
    async def transform_gateways(self):
        for gateway in self.units(GATEWAY).ready:
            abilities = await self.get_available_abilities(gateway)
            if AbilityId.MORPH_GATEWAY in abilities and self.can_afford(AbilityId.MORPH_GATEWAY):
                await self.do(gateway(AbilityId.MOPRH_GATEWAY))

    # chronos the cybernetics
    async def chronoboost(self):
        for nexus in self.units(NEXUS).ready:
            abilities = await self.get_available_abilities(nexus)
            # chronos stuff in priority order
            # first checks if there is energy for chrono and building is ready
            # then checks if building is queued and isn't already chronoed
            if AbilityId.EFFECT_CHRONOBOOST in abilities:
                cybernetics = self.units(CYBERNETICSCORE).ready.first
                forge = self.units(CYBERNETICSCORE).ready.first
                twilight = self.units(TWILIGHTCOUNCIL).ready.first
                # chronos cybernetics
                if self.can_afford(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST) and self.units(CYBERNETICSCORE).ready:
                    if self.units(CYBERNETICSCORE).noqueue is False\
                     and not cybernetics.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                        await self.do(nexus(AbilityId.EFFECT_CHRONOBOOST, self.units(cybernetics)))

                # chronos twilight
                elif self.can_afford(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST) and self.units(TWILIGHTCOUNCIL).ready:
                    if self.units(TWILIGHTCOUNCIL).noqueue is False\
                     and not twilight.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                        await self.do(nexus(AbilityId.EFFECT_CHRONOBOOST, self.units(twilight)))

                # chronos forge
                elif self.can_afford(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST) and self.units(FORGE).ready:
                    if self.units(FORGE).noqueue is False and not forge.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                        await self.do(nexus(AbilityId.EFFECT_CHRONOBOOST, self.units(forge)))

                # chronos nexus
                # additional check to see if first pylon has been made
                else:
                    if self.can_afford(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST) and self.units(NEXUS).ready:
                        if self.units(NEXUS).noqueue is False and not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST)\
                         and self.built_first_pylon:
                            await self.do(nexus(AbilityId.EFFECT_CHRONOBOOST, self.units(cybernetics)))

    # makes stalkers from all gateways/warpgates
    async def build_army(self):
        # makes stalkers from gateway and warpgates and only if more than 1 nexus
        if self.units(CYBERNETICSCORE).ready.exists:
            # gateway section
            if self.units(GATEWAY).ready.exists and self.built_natural:
                # queues all stalkers at same time from non queued up gateways
                gateway_count = self.units(GATEWAY).ready.noqueue.amount
                if self.minerals >= gateway_count * 125 and self.vespene >= gateway_count * 50:
                    for gateway in self.units(GATEWAY).ready.noqueue:
                        if self.can_afford(STALKER) and self.supply_left >= 2:
                            await self.do(gateway.train(STALKER))

            # warpgate section
            if self.units(WARPGATE).ready.exists:
                for warpgate in self.units(WARPGATE).ready and self.built_natural:
                    abilities = await self.get_available_abilities(warpgate)
                    warp_gate_count = 0
                    if AbilityId.WARPGATETRAIN_STALKER in abilities:
                        warpgate_count += 1
                        if self.can_afford(STALKER) and self.supply_left >= 2 and self.minerals >= warpgate_count * 125\
                                and self.vespene >= warpgate_count * 50:
                            # gets initial position for stalker warp-in then moves with a placements step for next warps
                            position = self.units(PYLON).ready.random.position
                            placement = self.find_placement(AbilityId.WARPGATETRAIN_STALKER, position, placement_step=2)
                            if placement is None:
                                break
                            await self.do(warpgate.warp_in(STALKER, placement))

        # makes immortals from robos
        if self.units(ROBOTICSFACILITY).ready.exists:
            for robo in self.units(ROBOTICSFACILITY).ready.noqueue:
                # queues up all immortals at same time from non queued robos
                robo_count = self.units(ROBOTICSFACILITY).ready.noqueue.amount
                if self.can_afford(IMMORTAL) and self.supply_left >= 4 and self.minerals >= robo_count * 250\
                        and self.vespene >= robo_count * 100:
                    await self.do(robo.train(IMMORTAL))


def main():
    run_game(maps.get("(2)16-BitLE"), [
        # Human(Race.Protoss),
        Bot(Race.Protoss, MassStalkerBot()),
        Computer(Race.Protoss, Difficulty.VeryEasy)
    ], realtime=False)


if __name__ == "__main__":
    main()

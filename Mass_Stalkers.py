import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer\
    # ,Human


class MassStalkerBot(sc2.BotAI):
    def __init__(self):
        sc2.BotAI.__init__(self)
        self.warp_researched = False

    # on_step function is called for every game step
    # it takes current game state and iteration
    async def on_step(self, iteration):

        await self.distribute_workers()
        await self.build_workers()
        await self.build_supply()
        await self.build_assimilator()
        await self.build_cybernetics()
        await self.build_gateways()
        await self.transform_gateways()
        await self.build_stalkers()
        await self.chronoboost()

        # researches warpgate research
        if self.units(CYBERNETICSCORE).ready and self.can_afford(RESEARCH_WARPGATE) and not self.warp_researched:
            self.warp_researched = True
            await self.do(self.units(CYBERNETICSCORE).ready.first(RESEARCH_WARPGATE))

        # attacks with all stalkers if supply is at or over 75
        if self.supply_used >= 75:
            for stalker in self.units(STALKER):
                await self.do(stalker.attack(self.enemy_start_locations[0]))

    # checks all nexus if they are queued up, if not queue up a probe
    async def build_workers(self):
        for nexus in self.units(NEXUS).ready.noqueue:
            if self.can_afford(PROBE) and self.units(NEXUS).amount * 22 > self.units(PROBE).amount:
                await self.do(nexus.train(PROBE))

    # builds a pylon if there isn't one being made and if there is only 10 or less supply left
    async def build_supply(self):
        if self.supply_left <= 6 and not self.already_pending(PYLON):
            nexus = self.units(NEXUS).ready
            if nexus.exists:
                if self.can_afford(PYLON):
                    await self.build(PYLON, near=nexus.random)

    # builds assimilator if there are any gateways
    async def build_assimilator(self):
        for nexus in self.units(NEXUS).ready:
            # finds all the vespene geyser that is by each nexus
            self.vespene_geysers = self.state.vespene_geyser.closer_than(10.0, nexus)
            for vespene_geyser in self.vespene_geysers:
                # checks if can afford to make assmililator and there is already a gateway warping in
                if self.can_afford(ASSIMILATOR) and self.already_pending(GATEWAY) or self.units(GATEWAY).ready.exists:
                    # checks if there is already a assimilator at the geyser, if not builds an assimilator
                    worker = self.select_build_worker(vespene_geyser.position)
                    if not self.units(ASSIMILATOR).closer_than(1.0, vespene_geyser).exists:
                        await self.do(worker.build(ASSIMILATOR, vespene_geyser))

    # builds a gateways of there are 8 or less
    async def build_gateways(self):
        if self.units(PYLON).ready.exists:
            if self.can_afford(GATEWAY) and self.units(GATEWAY).amount <= 8:
                await self.build(GATEWAY, near=self.units(PYLON).ready.random, max_distance=6)

    # builds a cybernetics if there isn't one already
    async def build_cybernetics(self):
        if not self.units(CYBERNETICSCORE).exists:
            if self.units(GATEWAY).ready.exists and self.can_afford(CYBERNETICSCORE)\
                    and not self.already_pending(CYBERNETICSCORE):
                await self.build(CYBERNETICSCORE, near=self.units(PYLON).ready.random)

    # transforms the gateways to warpgates
    async def transform_gateways(self):
        for gateway in self.units(GATEWAY).ready.exists:
            abilities = self.get_available_abilities(gateway)
            if AbilityId.MORPH_GATEWAY in abilities and self.can_afford(AbilityId.MORPH_GATEWAY):
                await self.do(gateway(MOPRH_GATEWAY))

    # chronos the cybernetics
    async def chronoboost(self):
        for nexus in self.units(NEXUS).ready.exists:
            abilities = self.get_available_abilities(nexus)
            if AbilityId.EFFECT_CHRONOBOOST in abilities and self.can_afford(AbilityId.EFFECT_CHRONOBOOST):
                target = self.units(CYBERNETICSCORE)
                await self.do(nexus)

    # makes stalkers from all gateways/warpgates
    async def build_stalkers(self):
        if self.units(CYBERNETICSCORE).ready.exists:
            if self.units(GATEWAY).ready.exists:
                for gateway in self.units(GATEWAY).ready.noqueue:
                    if self.can_afford(STALKER):
                        await self.do(gateway.train(STALKER))
            if self.units(WARPGATE).ready.exists:
                for warpgate in self.units(WARPGATE).ready:
                    abilities = self.get_available_abilities(warpgate)
                    if self.can_afford(STALKER) and AbilityId.WARPGATETRAIN_STALKER in abilities:
                        position = self.units(PYLON).ready.random.position
                        placement = self.find_placement(AbilityId.WARPGATETRAIN_STALKER, position, placement_step=2)
                        if placement is None:
                            break
                        await self.do(warpgate.warp_in(STALKER, placement))


def main():
    run_game(maps.get("(2)16-BitLE"), [
        # Human(Race.Protoss),
        Bot(Race.Protoss, MassStalkerBot()),
        Computer(Race.Protoss, Difficulty.VeryEasy)
    ], realtime=False)


if __name__ == "__main__":
    main()

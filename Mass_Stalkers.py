import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer, Human
from sc2.constants import *


class MassStalkerBot(sc2.BotAI):
    # on_step function is called for every game step
    # it takes current game state and iteration
    async def on_step(self, iteration):

        await self.distribute_workers()
        await self.build_workers()
        await self.build_supply()
        await self.build_assimilator()

    # checks all nexus if they are queued up, if not queue up a probe
    async def build_workers(self):
        for nexus in self.units(NEXUS).ready.noqueue:
            if self.can_afford(PROBE):
                await self.do(nexus.train(PROBE))

    # builds a pylon if there isn't one being made and if there is only 10 or less supply left
    async def build_supply(self):
        if self.supply_left <= 8 and not self.already_pending(PYLON):
            nexus = self.units(NEXUS).ready
            if nexus.exists:
                if self.can_afford(PYLON):
                    await self.build(PYLON, near=nexus.first)

    # builds assimilator if there are any gateways
    async def build_assimilator(self):
        for nexus in self.units(NEXUS).ready:
            # finds all the vespene geyser that is by each nexus
            self.vespene_geysers = self.state.vespene_geyser.closer_than(10.0, nexus)
            for vespene_geyser in self.vespene_geysers:
                # checks if can afford to make assmililator and there is already a gateway warping in
                if not self.can_afford(ASSIMILATOR)\
                        and not self.already_pending(GATEWAY) or self.units(GATEWAY).not_ready:
                    break
                worker = self.select_build_worker(vespene_geyser.position)
                if worker is None:
                    break
                # checks if there is already a assimilator at the geyser, if not builds an assimilator
                if not self.units(ASSIMILATOR).closer_than(1.0, vespene_geyser).exists:
                    await self.do(worker.build(ASSIMILATOR, vespene_geyser))


run_game(maps.get("(2)16-BitLE"), [
    # Human(Race.Protoss),
    Bot(Race.Protoss, MassStalkerBot()),
    Computer(Race.Protoss, Difficulty.VeryEasy)
], realtime=True)

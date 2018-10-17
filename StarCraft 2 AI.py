import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Human, Computer
from sc2.constants import NEXUS, PROBE, PYLON, ASSIMILATOR


class WorkerRushBot(sc2.BotAI):
    # on_step function is called for every game step
    # it takes current game state and iteration
    async def on_step(self, iteration):

        # ---- WORKER RUSH ----
        # if it is the first frame on the game
        # if iteration == 0:
        #     for worker in self.workers:
        #         # have the worker attack the enemy start position
        #         await self.do(worker.attack(self.enemy_start_locations[0]))
        # ---- WORKER RUSH ----

        await self.distribute_workers()
        await self.build_workers()
        await self.build_supply()
        await self.build_assimilator()

    async def build_workers(self):
        for nexus in self.units(NEXUS).ready.noqueue:
            if self.can_afford(PROBE):
                await self.do(nexus.train(PROBE))

    async def build_supply(self):
        if self.supply_left <= 10 and not self.already_pending(PYLON):
            nexus = self.units(NEXUS).ready
            if nexus.exists:
                if self.can_afford(PYLON):
                    await self.build(PYLON, near=nexus.first)

    async def build_assimilator(self):
        for nexus in self.units(NEXUS).ready:
            self.vespene_geysers = self.state.vespene_geyser.closer_than(10.0, nexus)
            for vespene_geyser in self.vespene_geysers:
                if not self.can_afford(ASSIMILATOR) or self.supply_left <= 5:
                    break
                if not self.units(ASSIMILATOR).closer_than(1.0, vespene_geyser).exists:
                    worker = self.select_build_worker(vespene_geyser.position)
                    if worker is None:
                        break
                    await self.do(worker.build(ASSIMILATOR, vespene_geyser))


run_game(maps.get("(2)16-BitLE"), [
    # Human(Race.Protoss),
    Bot(Race.Protoss, WorkerRushBot()),
    Computer(Race.Protoss, Difficulty.VeryEasy)
], realtime=True)


import random
from dreamgpt.constants import THEME_SEED_COUNT
from dreamgpt.engine.prompts.combinePrompts import combinePrompt
from dreamgpt.engine.prompts.dreamPrompts import dreamPrompt
from dreamgpt.engine.prompts.themeExpansionPrompts import themeExpansionPrompt
from dreamgpt.llm.llm import chatComplete
from dreamgpt.store.entity import getEntityFromJSON
from dreamgpt.store.store import Store
from time import time
from nistbeacon import NistBeacon, NistBeaconValue


class DreamEngine:
    def __init__(self):

        self.next_time = 0
        self.beacon_value: NistBeaconValue = None
        self.next_beacon()

        self.store = Store()

    def next_beacon(self):
        t = time()
        if t < self.next_time:
            return False
        
        self.beacon_value = NistBeacon.get_last_record()
        random.seed(self.beacon_value.seed_value)
        self.next_time = t + self.beacon_value.frequency
        return True
    
    def expandTheme(self, theme):
        if theme is None:
            return []
        else:
            print(f"Generating seeds for \"{theme}\"...")
            themeConcepts = []
            gptPrompt = themeExpansionPrompt(theme, THEME_SEED_COUNT)
            themeConcepts = chatComplete(gptPrompt)
            return themeConcepts

    def dream(self, themeSeeds):
        print("Generating concepts...")
        concepts = []
        self.next_beacon()

        gptPrompt = dreamPrompt(themeSeeds)
        jsonData = chatComplete(gptPrompt)
        try:
            print("Calculating embeddings...")
            for concept in jsonData:
                concepts.append(getEntityFromJSON(concept))
        except Exception as e:
            print(f"Exception: {e}")

        if len(concepts) > 0:
            self._save(concepts)
        else:
            print("No concepts generated.")

        return concepts

    def combine(self, dreams):
        print("Combining dreams...")
        comboDreams = []
        dreamPairs = self._get_unique_pairs(dreams, 6)
        self.next_beacon()

        for pair in dreamPairs:
            gptPrompt = combinePrompt(pair)
            jsonData = chatComplete(gptPrompt)
            print("Calculating embeddings...")
            parentIDs = [dream.id for dream in pair]
            comboDreams.append(getEntityFromJSON(jsonData, parentIDs))

        if len(comboDreams) > 0:
            self._save(comboDreams)
        else:
            print("No concepts generated.")

        return comboDreams

    def pick(self, dreams, count=6):
        print("Picking the best dreams...")
        CUTOFF_PERCENTAGE = 0.5
        bestDreams = sorted(dreams, key=lambda item: item.totalScore, reverse=True)[
            :(int(len(dreams) * CUTOFF_PERCENTAGE))]
        return bestDreams

    def _save(self, dreams):
        print("Saving dreams...")
        try:
            self.store.addEntities(dreams)
            print(f"{len(dreams)} dreams saved!")
        except Exception as error:
            print(f"Error saving dreams: {error}")

    def _get_unique_pairs(self, lst, count):
        if len(lst) < 2:
            return []
        pairs = []
        self.next_beacon()

        while len(pairs) < count:
            pair = random.sample(lst, 2)
            if pair not in pairs:
                pairs.append(pair)
        return pairs

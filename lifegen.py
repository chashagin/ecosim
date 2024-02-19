# Standard Library Imports
import math
import random
import traceback
from collections import Counter, defaultdict
from typing import List, Tuple

# Third-party Imports
import noise
import pygame
from pygame.locals import BLEND_RGBA_MULT

# Initialize Pygame and constants
pygame.init()
WIDTH, HEIGHT = 1024, 768
GRID_SIZE = 10
ROWS, COLS = HEIGHT // GRID_SIZE, WIDTH // GRID_SIZE
font = pygame.font.Font("DejaVuSans.ttf", 8)
bold_font = pygame.font.Font("DejaVuSans-Bold.ttf", 8)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ecosystem Simulator")

# Global variables
animal_id_counter = 0

class Terrain:
    def __init__(self, terrain_type, elevation, water_volume=0):
        self.terrain_type = terrain_type
        self.elevation = elevation
        self.water_volume = water_volume
        self.metadata = {}  # Add this line

    @property
    def symbol(self):
        terrain_symbols = {
            'water': '▓', 
            'land': '▒', 
            'vegetation': '♣', 
            'sand': '░'
        }
        return terrain_symbols.get(self.terrain_type, '?')

    @property
    def color(self):
        terrain_colors = {
            'water': (0, 0, 255),
            'land': (139, 69, 19),
            'vegetation': (0, 255, 0),
            'sand': (255, 255, 0)
        }
        return terrain_colors.get(self.terrain_type, (255, 255, 255))

class Water:
    def __init__(self):
        self.volume = 100  # in liters

class Plant:
    def __init__(self):
        self.nutrition = 30
        self.is_dead = False
        self.ambient_temperature = 20  # Default value

    def handle_vital_stats(self):
        if self.ambient_temperature >= 35:
            self.is_dead = True

class Season:
    # Represents a season in the ecosystem, affecting temperature, food growth, and predator efficiency.

    def __init__(self, name, temperature_modifier, food_growth_rate, predator_efficiency):
        self.name = name
        self.temperature_modifier = temperature_modifier
        self.food_growth_rate = food_growth_rate
        self.predator_efficiency = predator_efficiency

    def apply_seasonal_effects(self, ecosystem):
        #Apply seasonal effects to the ecosystem, adjusting temperature, plant nutrition, and predator efficiency.

        ecosystem.ambient_temperature += self.temperature_modifier
        for plant in ecosystem.plants:
            plant.nutrition *= (self.food_growth_rate / 2) 
        for predator in ecosystem.predators:
            predator.hunting_success_rate *= self.predator_efficiency

class Animal:
    # Base class for animals in the ecosystem, defining common attributes and behaviors.

    def __init__(self, row, col, speed, sex, color, species):
        global animal_id_counter
        self.id = animal_id_counter
        animal_id_counter += 1
        self.row = row
        self.col = col
        self.speed = speed
        self.sex = sex
        self.color = color
        self.species = species
        self._initialize_basic_attributes()

    def _initialize_basic_attributes(self):
        # Initialize basic attributes related to physiological needs, lifecycle, biological traits, etc.
        self.hunger, self.thirst, self.energy = 0, 0, 100
        self.age = random.randint(20, 40) if random.choice([True, False]) else 0
        self.is_adult = self.is_dead = False
        self.cause_of_death = None
        self.decay = 100
        self.max_age = random.randint(50, 100)
        self._initialize_biological_attributes()

    def _initialize_biological_attributes(self):
        # Initialize biological attributes like body temperature, strength, agility, intelligence, etc.

        self.body_temperature = 37.0
        self.strength = random.uniform(0.5, 1.5)
        self.agility = random.uniform(0.5, 1.5)
        self.wisdom = random.uniform(0.5, 1.5)
        self.intelligence = random.uniform(0.5, 1.5)
        self.fertility = self.immune_system = random.uniform(0.5, 1.5)
        self.sensory_perception = random.uniform(0.5, 1.5)
        self.gestation_period = self.reproduction_cooldown = 0
        self.is_pregnant = False
        self.offspring_count = 0
        self.social_hierarchy_rank = random.randint(1, 10)
        self.territory_size = random.uniform(1.0, 10.0)
        self.migratory_pattern = random.choice(['None', 'Seasonal', 'Nomadic'])
        self.behavioral_traits = {'aggressive': random.random(), 'curious': random.random(), 'social': random.random()}
        self.colon = self.bladder = 0
        self.random_move_probability = 0.2
        self.nutrition = 40
        self.born = True
        self.predator_list = []
        self.prey_list = []
        self.defense_mechanisms = []

    def undergo_decay(self):
        # Handle the decay process of a dead animal, reducing its decay attribute over time.

        if self.is_dead:
            self.decay = max(self.decay - 5, 0)

    def move(self, valid_moves, nearby_adults=None, ecosystem=None):
        # Move the animal to a new location based on available moves, considering nearby adults for herd behavior.
        try:
            if valid_moves and self.energy > 0 and not self.is_dead:
                # Filter moves to avoid tiles occupied by the same species
                valid_moves = [move for move in valid_moves if not ecosystem.is_tile_occupied_by_same_species(move, self.species)]
                if valid_moves:
                    # Choose a new location from the valid moves
                    new_row, new_col = self._choose_new_location(valid_moves, nearby_adults)
                    # Remove from the current tile in the ecosystem's tracking dictionary
                    if self in ecosystem.animals_on_tile[(self.row, self.col)]:
                        ecosystem.animals_on_tile[(self.row, self.col)].remove(self)
                    # Update the position
                    self.row, self.col = new_row, new_col
                    # Add to the new tile in the ecosystem's tracking dictionary
                    ecosystem.animals_on_tile[(self.row, self.col)].append(self)
        except Exception as e:
            print(f"Error in move: {e}")

    def _choose_new_location(self, valid_moves, nearby_adults):
        # Choose a new location for the animal to move to, prioritizing staying close to nearby adults.
        if nearby_adults and not self.is_adult:
            center_row = sum(h.row for h in nearby_adults) / len(nearby_adults)
            center_col = sum(h.col for h in nearby_adults) / len(nearby_adults)
            new_row, new_col = min(valid_moves, key=lambda pos: abs(pos[0] - center_row) + abs(pos[1] - center_col))
        else:
            new_row, new_col = random.choice(valid_moves)
        
        return new_row, new_col

    def feed(self, food_source):
        # Consume food to reduce hunger, and increment colon fill level.

        try:
            self.hunger = max(self.hunger - food_source.nutrition, 0)
            self.energy = max(self.energy + food_source.nutrition, 0)
            self._increase_colon_fill()
        except Exception as e:
            print(f"Error in feed: {e}")

    def _increase_colon_fill(self):
        # Increase the colon fill level, with a cap at 100.

        self.colon = min(self.colon + 20, 100)

    def drink(self):
        # Drink water to satisfy thirst and increment bladder fill level.

        try:
            self.thirst = max(self.thirst - 50, 0)
            self._increase_bladder_fill()
        except Exception as e:
            print(f"Error in drink: {e}")

    def _increase_bladder_fill(self):
        # Increase the bladder fill level, with a cap at 100.

        self.bladder = min(self.bladder + 30, 100)

    def defecate(self, ecosystem):
        # Defecate, emptying the colon and marking the current tile with feces.

        try:
            self.colon = 0
            ecosystem.grid[self.row][self.col].metadata['feces'] = True
        except Exception as e:
            print(f"Error in defecate: {e}")

    def urinate(self, ecosystem):
        # Urinate, emptying the bladder and marking the current tile with urine.

        try:
            self.bladder = 0
            ecosystem.grid[self.row][self.col].metadata['urine'] = True
        except Exception as e:
            print(f"Error in urinate: {e}")

    def update_fertility(self):
        # Update the fertility status of the animal based on its reproductive cycle.

        if self.sex == 'F':
            self.reproductive_day = (self.reproductive_day + 1) % 28
            self.fertility = self._calculate_fertility()

    def _calculate_fertility(self):
        # Calculate the fertility level based on the reproductive day.

        if 7 <= self.reproductive_day <= 14:
            return min(self.fertility + 1, 10)  # Peak fertility period
        else:
            return max(self.fertility - 1, 0)  # Decrease fertility outside peak period

    def can_reproduce(self):
        # Check if the animal meets the conditions for reproduction.

        return (
            self.sex == 'F' and
            not self.is_pregnant and
            self.reproduction_cooldown <= 0 and
            self.age > 20 and
            self.age < 50 and
            self.hunger < 20 and
            self.thirst < 20 and
            self.fertility >= 8  # Fertility threshold
        )

    def reproduce(self, other):
        # Engage in reproduction with another animal, potentially resulting in pregnancy.

        if self._meets_reproduction_conditions(other):
            self._initiate_pregnancy()
            return None  # No immediate birth
        return None

    def _meets_reproduction_conditions(self, other):
        # Check if the reproduction conditions are met with another animal.

        return (self.is_adult and other.is_adult and self.species == other.species and
                self.sex == 'F' and not other.sex == 'F' and not self.is_dead and not other.is_dead)

    def _initiate_pregnancy(self):
        # Initiate the pregnancy process for the animal.

        self.gestation_period = 100  # Example gestation period
        self.is_pregnant = True

    def give_birth(self, ecosystem):
        # Give birth to offspring if the gestation period is over.

        if self.gestation_period <= 0 and self.is_pregnant:
            child_attributes = self.inherit_attributes(other)
            child = self.__class__(self.row, self.col, **child_attributes)
            ecosystem.add_animal(child)
            self._reset_post_birth_conditions()

    def _reset_post_birth_conditions(self):
        # Reset the conditions related to pregnancy and reproduction after giving birth.

        self.is_pregnant = False
        self.reproduction_cooldown = 300  # Cooldown period after giving birth

    def inherit_attributes(self, other):
        # Inherit attributes from parents with a mutation factor, creating the attributes for the offspring.

        mutation_factor = 0.1
        return {
            'speed': self._mutate_attribute(self.speed, other.speed, mutation_factor),
            'strength': self._mutate_attribute(self.strength, other.strength, mutation_factor),
            # Additional attributes like agility, wisdom, intelligence, etc., will be added here.
            'color': self.mutate_color(self.color, other.color)
        }

    def _mutate_attribute(self, attribute1, attribute2, mutation_factor):
        # Apply mutation to a given attribute during inheritance.

        average = (attribute1 + attribute2) / 2
        return average + random.uniform(-mutation_factor, mutation_factor)

    def mutate_color(self, color1, color2):
        # Mutate the color attribute during inheritance.

        new_color = [(c1 + c2) // 2 + random.randint(-10, 10) for c1, c2 in zip(color1, color2)]
        return [max(0, min(255, c)) for c in new_color]

    def handle_vital_stats(self):
        # Update vital statistics of the animal such as age, hunger, thirst, and check for death conditions.

        self._age_animal()
        self._increase_hunger()
        self._increase_thirst()
        self._check_death_conditions()
        self._regenerate_energy()
        
    def _age_animal(self):
        # Increment the age of the animal and update its adult status.

        self.age += 1
        if self.age >= 20 and not self.is_adult:
            self.is_adult = True

    def _increase_hunger(self):
        # Increase hunger level with a maximum cap.

        self.hunger = min(self.hunger + 10, 100)

    def _increase_thirst(self):
        # Increase thirst level with a maximum cap.

        self.thirst = min(self.thirst + 10, 100)

    def _regenerate_energy(self):
        if self.hunger < 100:
            self.energy = min(self.energy + 5, 100)  # Regenerate some energy each cycle

    def _check_death_conditions(self):
        # Check various conditions that could lead to the animal's death.

        if self.age >= self.max_age:
            self.die("Old Age")
        elif self.hunger >= 100:
            self.die("Starvation")
        elif self.thirst >= 100:
            self.die("Dehydration")
        elif self.body_temperature >= 42:
            self.die("Hyperthermia")
        elif self.energy <= 0:
            self.die("Exhaustion")

    def die(self, cause_of_death):
        # Set the animal's status to dead and record the cause of death.

        if not self.is_dead:
            self.is_dead = True
            self.cause_of_death = cause_of_death
            self._handle_post_death()

    def _handle_post_death(self):
        # Handle additional logic after the animal's death, such as resetting flags and printing death info.

        self.born = False  # Assuming born is used to track if the death message is printed
        print(f"{type(self).__name__} {self.id} died from {self.cause_of_death}. Attributes: Age: {self.age}, Hunger: {self.hunger}, Thirst: {self.thirst}, Energy: {self.energy}, Body Temperature: {self.body_temperature}")

    def update(self, ecosystem):
        # Call defecate and urinate within the update method
        self.update_fertility()  # Update the fertility status each day
        self.defecate(ecosystem)
        self.urinate(ecosystem)
        if self.age >= 20 and not self.is_adult:  # Set adulthood at age 20
            self.is_adult = True
        if self.is_pregnant:
            self.gestation_period -= 1
            if self.gestation_period <= 0:
                self.give_birth(ecosystem)
        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown -= 1  # Decrement cooldown each cycle

class Herbivore(Animal):
    # Represents a herbivore in the ecosystem with specific attributes and behaviors.

    def __init__(self, row, col, speed, sex):
        super().__init__(row, col, speed, sex, (0, 255, 255), 'Herbivore')
        self.reproduction_count = random.randint(1, 5)
        self.gestation_period = 40  # Gestation period specific to herbivores
        self.is_pregnant = False
        self.reproduction_cooldown = 0

    def feed(self, food_source):
        # Herbivores can only feed on plant sources. Overrides the generic feed method.

        if isinstance(food_source, Plant):
            super().feed(food_source)
        else:
            print("Herbivores can only eat plants.")

    def can_reproduce(self):
        # Check if the herbivore meets specific conditions for reproduction. Overrides the generic method.

        basic_conditions = super().can_reproduce()
        return basic_conditions and self.is_adult  # Ensuring only adults can reproduce

    def reproduce(self, other):
        # Specific reproduction logic for herbivores. Overrides the generic reproduce method.

        if self.can_reproduce() and other.is_adult and self.species == other.species and self.sex != other.sex:
            self.is_pregnant = True
            self.gestation_period = 20  # Specific gestation period for herbivores
            return None

    def give_birth(self, ecosystem):
        # Herbivores give birth to offspring. Overrides the generic give_birth method.

        if self.gestation_period <= 0 and self.is_pregnant:
            child_attributes = self.inherit_attributes(other)
            child = self.__class__(self.row, self.col, **child_attributes)
            ecosystem.add_animal(child)
            self._reset_post_birth_conditions()

    def update(self, ecosystem):
        super().update(ecosystem)  # Call the parent update method
        if self.is_pregnant:
            self.gestation_period -= 1  # Decrement the gestation period
            if self.gestation_period <= 0:
                self.give_birth(ecosystem)
        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown -= 1  # Decrement the cooldown

# Create the Predator class
class Predator(Animal):
    # Represents a predator in the ecosystem with enhanced attributes and hunting behaviors.

    def __init__(self, row, col, speed, sex):
        super().__init__(row, col, speed, sex, (255, 0, 0), 'Predator')
        self.hunting_success_rate = self._calculate_hunting_success_rate(speed)
        self.hunger_decrease_on_feed = 80  # How much hunger is decreased when feeding
        self.immune_system = random.uniform(1.0, 2.0)  # Enhanced immune system

    def _calculate_hunting_success_rate(self, speed):
        # Calculate the hunting success rate based on the predator's speed.

        base_rate = 0.2
        speed_factor = (speed - 3.5) / 1.0
        return min(base_rate + speed_factor, 1.0)  # Ensure it doesn't exceed 100%

    def feed(self, ecosystem):
        # Predators feed by hunting nearby herbivores. Overrides the generic feed method.

        potential_prey = self._find_nearby_prey(ecosystem)
        if potential_prey:
            prey = random.choice(potential_prey)
            self.hunt(prey, ecosystem)

    def _find_nearby_prey(self, ecosystem):
        # Find nearby herbivores that can be hunted.

        return [herbivore for herbivore in ecosystem.herbivores if self._is_near(herbivore)]

    def hunt(self, prey, ecosystem):
        # Attempt to hunt a prey. Success is based on the hunting success rate.

        self.energy -= 20  # Hunting consumes energy
        if random.random() < self.hunting_success_rate:
            prey.die("Predation")
            self._consume_prey(prey, ecosystem)

    def _consume_prey(self, prey, ecosystem):
        # Consume the prey, reducing hunger and thirst.

        self.hunger = max(self.hunger - self.hunger_decrease_on_feed, 0)
        self.thirst = max(self.thirst - 50, 0)
        ecosystem.herbivores.remove(prey)

    def _is_near(self, herbivore):
        # Check if a herbivore is within the adjacent cell to the predator.

        return abs(self.row - herbivore.row) <= 1 and abs(self.col - herbivore.col) <= 1

    def move(self, valid_moves, ecosystem=None):
        if valid_moves and self.energy > 0 and not self.is_dead:
            # Predators do not consider other animals while moving
            new_row, new_col = random.choice(valid_moves)
            self.row, self.col = new_row, new_col
            self.energy -= 1

class Ecosystem:
    # Represents the ecosystem where animals, plants, and other environmental elements interact.
    # This class manages the simulation's environment, including terrain generation and ecosystem dynamics.

    INITIAL_HERBIVORE_COUNT = 150  # Class constant for initial herbivore count
    INITIAL_PREDATOR_COUNT = 75    # Class constant for initial predator count
    INITIAL_PLANT_COUNT = 200      # You can also define a constant for initial plant count

    def __init__(self, rows, cols, initial_herbivore_count=150, initial_predator_count=75):
        self.rows, self.cols = rows, cols
        self.grid = [[None for _ in range(cols)] for _ in range(rows)]  # Initialize the grid here
        self.manual_temperature_control = False  # Initialize the attribute here
        self._initialize_environment_attributes()
        self._generate_terrain()
        self._smooth_terrain()
        self._initialize_animals(initial_herbivore_count, initial_predator_count)
        print(f"Initialized {len(self.herbivores)} herbivores and {len(self.predators)} predators")

        # Initialize population data lists
        self.herbivore_population_data = []
        self.predator_population_data = []
        self.plant_population_data = []
        self.animals_on_tile = defaultdict(list)  # Initializes a dictionary with a default value of an empty list

    def _initialize_animals(self, herbivore_count, predator_count):
        self.herbivores = [Herbivore(*self._generate_valid_location(), random.uniform(0.5, 1.5), random.choice(['M', 'F'])) for _ in range(herbivore_count)]
        # Corrected the order and type of arguments for Predator
        self.predators = [Predator(*self._generate_valid_location(), random.uniform(0.5, 1.5), random.choice(['M', 'F'])) for _ in range(predator_count)]


    def _generate_valid_location(self):
        while True:
            row, col = random.randint(0, self.rows - 1), random.randint(0, self.cols - 1)
            if self.grid[row][col].symbol != '▓' and not self.is_tile_occupied(row, col):
                return row, col

    def _initialize_environment_attributes(self):
        # Initialize attributes related to the environment like temperature, precipitation, and seasons.

        self.herbivores = []  # List of Herbivore objects
        self.predators = []  # List of Predator objects
        self.plants = []  # List of Plant objects
        self.cycle = 0
        self.ambient_temperature = 20.0
        self.precipitation_level = 0
        self.seasons = [Season("Spring", 5, 1.2, 1.0), Season("Summer", 10, 1.0, 1.2), 
                        Season("Autumn", 0, 0.8, 1.0), Season("Winter", -5, 0.5, 1.1)]
        self.current_season = self.seasons[0]
        self.season_cycle = 0
        self.season_duration = 50

    def _generate_terrain(self):
        for row in range(self.rows):
            for col in range(self.cols):
                elevation = random.uniform(0, 100)
                terrain_type = self._choose_terrain_type(elevation)
                water_volume = 100 if terrain_type == 'water' else 0
                self.grid[row][col] = Terrain(terrain_type, elevation, water_volume)

        self.expand_water_bodies(expansion_cycles=3)

    def _choose_terrain_type(self, elevation):
        if elevation < 30:
            return 'water' if random.random() < 0.4 else 'land'
        return random.choice(['vegetation', 'land'])

    def _smooth_terrain(self):
        for _ in range(3):
            new_grid = [[self._calculate_smoothed_terrain(row, col) for col in range(self.cols)] for row in range(self.rows)]
            self.grid = new_grid
        
        self.refine_water_bodies_and_create_shorelines()  # Regenerate shorelines after smoothing

    def _calculate_smoothed_terrain(self, row, col):
        neighbors = self._get_neighbors(row, col)
        terrain_types = Counter(self.grid[r][c].terrain_type for r, c in neighbors)
        if terrain_types['water'] > 10:
            return Terrain('water', self.grid[row][col].elevation)
        return self.grid[row][col]

    def smooth_map(self):
        for _ in range(3):  # Number of smoothing iterations
            for row in range(self.rows):
                for col in range(self.cols):
                    water_neighbors = self.count_water_neighbors(row, col)
                    if water_neighbors >= 4:
                        self.grid[row][col].symbol = '▓'
                    elif water_neighbors < 2:
                        self.grid[row][col].symbol = '░'

    def expand_water_bodies(self, expansion_cycles):
        for _ in range(expansion_cycles):
            new_water_tiles = self._identify_new_water_tiles()
            self._convert_to_water(new_water_tiles)

    def _identify_new_water_tiles(self):
        new_water_tiles = []
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col].symbol != '▓' and self.is_land_and_surrounded_by_water(row, col, 3):
                    new_water_tiles.append((row, col))
        return new_water_tiles

    def _convert_to_water(self, new_water_tiles):
        for row, col in new_water_tiles:
            self.grid[row][col] = Terrain('water', self.grid[row][col].elevation, 100)

    def is_land_and_surrounded_by_water(self, row, col, threshold):
        water_count = sum(1 for r, c in self._get_neighbors(row, col) if self.grid[r][c].terrain_type == 'water')
        return self.grid[row][col].terrain_type != 'water' and water_count >= threshold

    def count_water_neighbors(self, row, col):
        # Count the number of water tile neighbors for a given tile at (row, col).

        water_neighbor_count = 0
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if (i, j) != (0, 0):  # Exclude the tile itself
                    neighbor_row, neighbor_col = row + i, col + j
                    # Check boundaries and if the neighbor is water
                    if 0 <= neighbor_row < self.rows and 0 <= neighbor_col < self.cols:
                        if self.grid[neighbor_row][neighbor_col].symbol == '▓':
                            water_neighbor_count += 1
        return water_neighbor_count

    def refine_water_bodies_and_create_shorelines(self):
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col].terrain_type == 'water' and self.count_water_neighbors(row, col) < 2:
                    new_type = 'land' if random.random() < 0.5 else 'sand'
                    self.grid[row][col] = Terrain(new_type, self.grid[row][col].elevation)
        self._generate_shorelines()

    def _generate_shorelines(self):
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col].terrain_type in ['land', 'vegetation'] and self.is_adjacent_to_water(row, col):
                    self.grid[row][col] = Terrain('sand', self.grid[row][col].elevation)

    def _is_adjacent_to_water(self, row, col):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid[nr][nc].terrain_type == 'water':
                    return True
        return False

    def _adjust_temperature(self):
        # Adjust the ambient temperature based on the simulation cycle, using a sinusoidal function for variation.

        if not self.manual_temperature_control:
            try:
                self.ambient_temperature = 10 * math.sin(math.pi * self.cycle / 180) + 20
            except Exception as e:
                print(f"Error in adjust_temperature: {e}")

    def adjust_water_volume(self):
        try:
            for row in range(self.rows):
                for col in range(self.cols):
                    if self.grid[row][col].terrain_type == 'water':
                        for r, c in self._get_neighbors(row, col):
                            if self.grid[r][c].elevation < self.grid[row][col].elevation:
                                water_movement = min(self.grid[row][col].water_volume * 0.05, self.grid[row][col].water_volume)
                                self.grid[r][c].water_volume += water_movement
                                self.grid[row][col].water_volume -= water_movement
                                if self.grid[row][col].water_volume < 10:
                                    self.grid[row][col] = Terrain('land', self.grid[row][col].elevation)
                                if self.grid[r][c].water_volume > 10 and self.grid[r][c].terrain_type != 'water':
                                    self.grid[r][c] = Terrain('water', self.grid[r][c].elevation, self.grid[r][c].water_volume)
        except Exception as e:
            print(f"Exception in adjust_water_volume: {e}")

    def _adjust_water_volume_for_tile(self, row, col):
        # Adjust the water volume for a single tile, distributing water to lower elevation neighbors.

        for r, c in self._get_neighbors(row, col):
            if self.grid[r][c].elevation < self.grid[row][col].elevation:
                self._redistribute_water(row, col, r, c)

    def _redistribute_water(self, source_row, source_col, target_row, target_col):
        # Redistribute water from a source tile to a target tile based on elevation differences.

        water_movement = min(self.grid[source_row][source_col].water_volume * 0.05, self.grid[source_row][source_col].water_volume)
        self.grid[target_row][target_col].water_volume += water_movement
        self.grid[source_row][source_col].water_volume -= water_movement
        self._update_terrain_based_on_water(source_row, source_col, target_row, target_col)

    def _update_terrain_based_on_water(self, source_row, source_col, target_row, target_col):
        # Update the terrain symbol based on the water volume after redistribution.

        if self.grid[source_row][source_col].water_volume < 10:
            self.grid[source_row][source_col].symbol = '░'
        if self.grid[target_row][target_col].water_volume > 10 and self.grid[target_row][target_col].symbol != '▓':
            self.grid[target_row][target_col].symbol = '▓'

    def _precipitate(self):
        # Simulate precipitation in the ecosystem, potentially creating new water bodies or expanding existing ones.
        try:
            if random.randint(0, 100) < self.precipitation_level:
                for row in range(self.rows):
                    for col in range(self.cols):
                        if self.grid[row][col].terrain_type == 'water':
                            self._flood_fill(row, col, 200)
                self.adjust_water_volume()
        except Exception as e:
            print(f"Error in precipitate: {e}")

    def _flood_fill(self, row, col, water_amount):
            # Apply a basic flood-fill algorithm to distribute water to neighboring tiles, simulating water spread.
        stack = [(row, col)]
        while stack:
            r, c = stack.pop()
            self.grid[r][c].water_volume += water_amount / 4
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    neighbor = self.grid[nr][nc]
                    if neighbor.terrain_type != 'water' and neighbor.elevation < 0.2:
                        self.grid[nr][nc] = Terrain('water', neighbor.elevation)
                        stack.append((nr, nc))

    def _evaporate_water(self):
        # Simulate water evaporation based on the ambient temperature and terrain elevation.
        base_evaporation_rate = 0.1
        additional_rate_per_degree = 1.05
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col].terrain_type == 'water':
                    elevation_based_modifier = 0.01 * (100 - self.grid[row][col].elevation)
                    total_evaporation_rate = base_evaporation_rate + additional_rate_per_degree * max(0, self.ambient_temperature - 20)
                    evaporated_volume = self.grid[row][col].water_volume * (total_evaporation_rate / 100)
                    self.grid[row][col].water_volume = max(0, self.grid[row][col].water_volume - evaporated_volume)
                    if self.grid[row][col].water_volume <= 0:
                        self.grid[row][col] = Terrain('land', self.grid[row][col].elevation)

    def _handle_extreme_heat(self):
        # Handle extreme heat conditions in the ecosystem, affecting water bodies and terrain.

        if self.ambient_temperature >= 100:
            for row in range(self.rows):
                for col in range(self.cols):
                    if self.grid[row][col].terrain_type == 'water':
                        self.grid[row][col] = Terrain('land', self.grid[row][col].elevation)

    def _update_season_cycle(self):
        # Update the cycle count for the current season and transition to the next season when necessary.

        self.season_cycle += 1
        if self.season_cycle >= self.season_duration:
            self._change_season()

    def _change_season(self):
        # Change to the next season in the sequence and apply its effects to the ecosystem.

        next_season_index = (self.seasons.index(self.current_season) + 1) % len(self.seasons)
        self.current_season = self.seasons[next_season_index]
        self.season_cycle = 0
        self.current_season.apply_seasonal_effects(self)

    def update_environment(self):
        # Update the environmental conditions of the ecosystem, including temperature, precipitation, and season effects.

        self._adjust_temperature()
        self._precipitate()
        # self._evaporate_water()
        self._handle_extreme_heat()
        self._update_season_cycle()

    def update(self):
        # Main update method for the ecosystem, called each simulation cycle to update environment, animals, and plants.

        self.update_environment()
        self.update_herbivores()
        self.update_predators()
        self.grow_plants()
        self.update_plants()
        self._update_animal_body_temperature_and_plant_nutrition()
        self.update_population_data()
        self.cycle += 1
        self.print_daily_summary()

    def _update_animal_body_temperature_and_plant_nutrition(self):
        # Update the body temperature of animals and nutrition of plants based on the ambient temperature.

        for animal in self.herbivores + self.predators:
            animal.body_temperature += (self.ambient_temperature - animal.body_temperature) * 0.01

        for plant in self.plants:
            plant.nutrition += (self.ambient_temperature - 20) * 0.1
   
    def add_animal(self, animal):
        # Add an animal to the ecosystem. The animal is added to the appropriate list based on its type.

        if isinstance(animal, Herbivore):
            self.herbivores.append(animal)
        elif isinstance(animal, Predator):
            self.predators.append(animal)

    def _get_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        # Get neighboring tiles' coordinates for a given tile in the grid.

        return [(row + i, col + j) for i in range(-1, 2) for j in range(-1, 2) 
                if 0 <= row + i < self.rows and 0 <= col + j < self.cols]

    def _get_valid_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        # Determine valid moves for an animal located at a specific grid cell.
        # This method excludes water tiles from valid moves.

        try:
            moves = [(row + i, col + j) for i in [-1, 0, 1] for j in [-1, 0, 1]]
            valid_moves = [(r, c) for r, c in moves if 0 <= r < self.rows and 0 <= c < self.cols]
            valid_moves = [(r, c) for r, c in valid_moves if self.grid[r][c].terrain_type in ['land', 'vegetation']]
            random.shuffle(valid_moves)
            return valid_moves
        except Exception as e:
            print(f"Error in get_valid_moves: {e}")
            return []
        
    def is_tile_occupied_by_same_species(self, tile, species):
        # Check if a given tile is occupied by an animal of the same species.

        # Quick lookup to see if the tile is occupied by an animal of the same species
        return any(animal.species == species for animal in self.animals_on_tile[tile])

    def is_tile_occupied(self, row, col):
        # Check if any animal is present on the given tile

        for animal in self.herbivores + self.predators:
            if animal.row == row and animal.col == col:
                return True
        return False

    def update_population_data(self):
        # Update and track the population data for herbivores, predators, and plants each cycle.

        living_herbivores = len([h for h in self.herbivores if not h.is_dead])
        living_predators = len([p for p in self.predators if not p.is_dead])
        total_plants = len(self.plants)

        self.herbivore_population_data.append(living_herbivores)
        self.predator_population_data.append(living_predators)
        self.plant_population_data.append(total_plants)

    def draw_population_graph(self, screen):
        # Draw a graph on the screen representing the population trends of herbivores, predators, and plants.

        max_length = 100
        graph_height = 150
        graph_width = WIDTH - 20
        start_x = 10
        start_y = HEIGHT - graph_height - 10
        padding_top = 20

        herbivore_data = self._scale_data(self.herbivore_population_data[-max_length:], graph_height, padding_top)
        predator_data = self._scale_data(self.predator_population_data[-max_length:], graph_height, padding_top)
        plant_data = self._scale_data(self.plant_population_data[-max_length:], graph_height, padding_top)

        self._draw_graph_lines(screen, herbivore_data, (0, 255, 255), start_x, start_y, graph_width, max_length, padding_top)
        self._draw_graph_lines(screen, predator_data, (255, 0, 0), start_x, start_y, graph_width, max_length, padding_top)
        self._draw_graph_lines(screen, plant_data, (0, 64, 0), start_x, start_y, graph_width, max_length, padding_top)

        pygame.draw.rect(screen, (255, 255, 255), (start_x, start_y, graph_width, graph_height), 2)

    def _scale_data(self, data, graph_height, padding_top):
        # Scale the data to fit within the graph's dimensions.

        max_population = max(data, default=1)
        return [y / max_population * (graph_height - padding_top) for y in data]

    def _draw_graph_lines(self, screen, data, color, start_x, start_y, graph_width, max_length, padding_top):
        # Draw lines on the graph based on the scaled data.

        if len(data) > 1:
            for i in range(len(data) - 1):
                start_pos = (start_x + i * (graph_width / max_length), start_y + graph_height - data[i] - padding_top)
                end_pos = (start_x + (i + 1) * (graph_width / max_length), start_y + graph_height - data[i + 1] - padding_top)
                pygame.draw.line(screen, color, start_pos, end_pos, 2)

    def print_daily_summary(self):
        # Print a daily summary of the ecosystem, including total numbers and causes of death for animals.

        total_herbivores = len(self.herbivores)
        total_predators = len(self.predators)
        alive_herbivores = sum(1 for h in self.herbivores if not h.is_dead)
        dead_herbivores = total_herbivores - alive_herbivores
        alive_predators = sum(1 for p in self.predators if not p.is_dead)
        dead_predators = total_predators - alive_predators

        herbivore_deaths = Counter(h.cause_of_death for h in self.herbivores if h.is_dead)
        predator_deaths = Counter(p.cause_of_death for p in self.predators if p.is_dead)

        # print(f"Day {self.cycle}:")
        # print(f"Total Herbivores: {total_herbivores} (Alive: {alive_herbivores}, Dead: {dead_herbivores})")
        # print(f"Causes of Death for Herbivores: {dict(herbivore_deaths)}")
        # print(f"Total Predators: {total_predators} (Alive: {alive_predators}, Dead: {dead_predators})")
        # print(f"Causes of Death for Predators: {dict(predator_deaths)}")

    def update_herbivores(self):
        # Update the state of each herbivore in the ecosystem. This includes handling their movement, feeding, drinking, 
        # reproduction, and decay if deceased.

        new_herbivores = []
        remaining_herbivores = []

        for herbivore in self.herbivores:
            self.handle_decay(herbivore, remaining_herbivores)
            herbivore.handle_vital_stats()

            if not herbivore.is_dead:
                self.handle_feeding(herbivore)
                self.handle_drinking(herbivore)
                self.handle_movement(herbivore)
                self.handle_reproduction(herbivore, new_herbivores)
                herbivore.defecate(self)
                herbivore.urinate(self)

                remaining_herbivores.append(herbivore)

        self.herbivores = remaining_herbivores + new_herbivores

    def update_predators(self):
        # Update the state of each predator in the ecosystem, including their movement, feeding, and vital stats management.

        remaining_predators = []

        for predator in self.predators:
            predator.handle_vital_stats()

            if not predator.is_dead:
                valid_moves = self._get_valid_moves(predator.row, predator.col)
                predator.move(valid_moves)
                self.handle_drinking(predator)
                self.handle_feeding(predator)

                remaining_predators.append(predator)

        self.predators = remaining_predators

    def update_plants(self):
        # Update the plants in the ecosystem, handling their vital stats and removing dead plants.

        for plant in self.plants:
            plant.ambient_temperature = self.ambient_temperature
            plant.handle_vital_stats()

        self.plants = [plant for plant in self.plants if not plant.is_dead]

    def grow_plants(self):
        plant_growth_chance = 0.01
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col].terrain_type == 'land' and random.random() < plant_growth_chance:
                    self.grid[row][col] = Terrain('vegetation', self.grid[row][col].elevation)
                    new_plant = Plant()
                    self.plants.append(new_plant)

    def handle_decay(self, animal, remaining_animals):
        # Handle the decay process for a dead animal. If the animal has not fully decayed, it remains in the ecosystem.

        if animal.is_dead:
            animal.undergo_decay()
            if animal.decay > 0:
                remaining_animals.append(animal)

    def get_nearby_animals(self, animal, radius=5):
        # Combine herbivores and predators into a single list for searching
        
        all_animals = self.herbivores + self.predators
        nearby_animals = [a for a in all_animals if a != animal and a.is_adult and self._is_within_radius(animal, a, radius)]
        return nearby_animals

    def _is_within_radius(self, animal1, animal2, radius):
        # Check if two animals are within a specified radius of each other.

        distance = math.sqrt((animal1.row - animal2.row)**2 + (animal1.col - animal2.col)**2)
        return distance <= radius

    def handle_movement(self, animal):
        # Handle the movement of an animal based on available valid moves and nearby adult animals.

        if not animal.is_dead:
            valid_moves = self._get_valid_moves(animal.row, animal.col)
            nearby_adults = self.get_nearby_animals(animal)
            animal.move(valid_moves, nearby_adults, ecosystem=self)

    def handle_drinking(self, animal):
        # Manage the drinking behavior of an animal. If adjacent to water, the animal's thirst is reduced.

        try:
            if not animal.is_dead and self._is_adjacent_to_water(animal.row, animal.col):
                animal.thirst = max(animal.thirst - 50, 0)
        except Exception as e:
            print(f"Error in handle_drinking: {e}")

    def is_adjacent_to_water(self, row, col):
        adjacent_tiles = [(row + i, col + j) for i in [-1, 0, 1] for j in [-1, 0, 1] if (i, j) != (0, 0)]
        return any(self.grid[r][c].terrain_type == 'water' for r, c in adjacent_tiles if 0 <= r < self.rows and 0 <= c < self.cols)

    def handle_feeding(self, animal):
        # Manage the feeding behavior of an animal, differentiating between herbivores and predators.

        try:
            row, col = animal.row, animal.col
            if not animal.is_dead:
                if isinstance(animal, Herbivore):
                    self._feed_herbivore(animal, row, col)
                elif isinstance(animal, Predator):
                    self._feed_predator(animal)
        except Exception as e:
            print(f"Error in handle_feeding: {e}")

    def _feed_herbivore(self, herbivore, row, col):
        # Handle feeding for a herbivore.

        if self.grid[row][col].terrain_type == 'vegetation':
            herbivore.feed(Plant())
            self.grid[row][col] = Terrain('land', self.grid[row][col].elevation)

    def _feed_predator(self, predator):
        # Handle feeding for a predator, which involves hunting nearby herbivores.

        for herbivore in self.herbivores:
            if self._is_adjacent(predator.row, predator.col, herbivore.row, herbivore.col) and not herbivore.is_dead:
                predator.feed(self)
                break

    def _is_adjacent(self, row1, col1, row2, col2):
        # Check if two grid cells are adjacent to each other.

        return abs(row1 - row2) <= 1 and abs(col1 - col2) <= 1

    def handle_reproduction(self, animal, new_animals):
        # Manage the reproduction process for an animal. If conditions are met, new animals of the same species may be added.

        for other in self._get_same_species(animal):
            if self._can_reproduce_together(animal, other):
                child = animal.reproduce(other)
                if child:
                    new_animals.append(child)
                    break

    def _get_same_species(self, animal):
        # Retrieve all animals of the same species as the given animal.

        if isinstance(animal, Herbivore):
            return [other for other in self.herbivores if other != animal]
        elif isinstance(animal, Predator):
            return [other for other in self.predators if other != animal]
        return []

    def _can_reproduce_together(self, animal1, animal2):
        # Check if two animals can reproduce together, considering species, sex, and proximity.

        return (animal1.species == animal2.species and animal1.sex != animal2.sex and
                abs(animal1.row - animal2.row) <= 1 and abs(animal1.col - animal2.col) <= 1)
    
    def handle_vital_stats(self, animal):
        # Update the vital statistics such as age, hunger, and thirst for an animal.

        animal.age += 1
        animal.hunger = min(animal.hunger + 10, 100)  # Increase hunger but cap at 100
        animal.thirst = min(animal.thirst + 10, 100)  # Increase thirst but cap at 100

        # Check for adulthood
        if animal.age >= 20 and not animal.is_adult:
            animal.is_adult = True

    def draw(self, screen):
        # Draw the current state of the ecosystem, including terrain, animals, and other visual elements.

        screen.fill((30, 30, 30))  # Dark background for better contrast

        # Make sure this is visible for debugging
        test_text = "Ecosystem Visualization"
        test_surface = bold_font.render(test_text, True, (255, 0, 0))  # Bright red for visibility
        screen.blit(test_surface, (20, 20))  # Top left corner

        # Draw terrain
        for row in range(self.rows):
            for col in range(self.cols):
                self._draw_terrain_cell(screen, row, col)

        # Additional UI elements like semi-transparent rectangles, season information, population counters
        self._draw_UI_elements(screen)

        # Draw animals
        for herbivore in self.herbivores:
            self._draw_animal(screen, herbivore)
        for predator in self.predators:
            self._draw_animal(screen, predator)

        # Draw precipitation level if applicable
        if self.precipitation_level > 0:
            self._draw_precipitation_level(screen)

    def _draw_terrain_cell(self, screen, row, col):
        # Draw a single terrain cell on the screen.

        terrain = self.grid[row][col]
        color = terrain.color  # Use the color property from the Terrain object
        symbol_surface = font.render(terrain.symbol, True, color)
        screen.blit(symbol_surface, (col * GRID_SIZE, row * GRID_SIZE))

    def _draw_UI_elements(self, screen):
        # Draw user interface elements such as season information and population counters.

        self._draw_transparent_rectangle(screen)
        self._draw_season_info(screen)
        self._draw_population_counters(screen)

    def _draw_transparent_rectangle(self, screen):
        # Draw a semi-transparent rectangle for better visibility of text.

        transparent_surface = pygame.Surface((WIDTH, 50), pygame.SRCALPHA)
        transparent_surface.fill((0, 0, 0, 180))
        screen.blit(transparent_surface, (0, 0))

    def _draw_season_info(self, screen):
        # Display the current season information on the screen.

        season_text = f"Season: {self.current_season.name}"
        season_surface = bold_font.render(season_text, True, (255, 255, 255))
        screen.blit(season_surface, (10, HEIGHT - 30))

    def _draw_population_counters(self, screen):
        # Display population counters for herbivores, predators, and plants.

        # Calculate counts
        adult_herbivores, infant_herbivores, adult_predators, infant_predators = self._calculate_population_counts()

        # Display text
        counter_text = f"Adult Herbivores: {adult_herbivores} | Infant Herbivores: {infant_herbivores} | Adult Predators: {adult_predators} | Infant Predators: {infant_predators}"
        counter_surface = font.render(counter_text, True, (255, 255, 255))
        text_rect = counter_surface.get_rect(center=(WIDTH // 2, 25))
        screen.blit(counter_surface, text_rect.topleft)

    def _calculate_population_counts(self):
        # Calculate the number of adult and infant herbivores and predators.

        adult_herbivores = sum(1 for h in self.herbivores if h.is_adult and not h.is_dead)
        infant_herbivores = sum(1 for h in self.herbivores if not h.is_adult and not h.is_dead)
        adult_predators = sum(1 for p in self.predators if p.is_adult and not p.is_dead)
        infant_predators = sum(1 for p in self.predators if not p.is_adult and not p.is_dead)
        return adult_herbivores, infant_herbivores, adult_predators, infant_predators

    def _draw_animal(self, screen, animal):
        # Draw an animal on the screen.

        symbol = 'H' if isinstance(animal, Herbivore) else 'P'
        symbol = symbol.lower() if not animal.is_adult else symbol.upper()
        color = self._get_animal_color(animal)
        symbol_surface = font.render(symbol, True, color)
        screen.blit(symbol_surface, (animal.col * GRID_SIZE, animal.row * GRID_SIZE))

    def _get_animal_color(self, animal):
        # Determine the color of an animal for drawing.

        if animal.is_dead:
            alpha = int(255 * (animal.decay / 100))
            return (alpha, alpha, alpha)  # Grayscale for dead animals
        return animal.color

    def _draw_precipitation_level(self, screen):
        # Display the current precipitation level if applicable.

        precipitation_text = f"Precipitation Level: {self.precipitation_level}"
        precipitation_surface = bold_font.render(precipitation_text, True, (255, 255, 255))
        screen.blit(precipitation_surface, (10, 10))

    def simulate_cycle(self):
        # Simulate a single cycle of the ecosystem. This involves updating all elements and drawing the current state.

        self.update()
        self.draw(screen)

    def initialize_ecosystem(self):
        for _ in range(self.INITIAL_HERBIVORE_COUNT):
            location = self._generate_valid_location()
            self.herbivores.append(Herbivore(*location, random.uniform(0.5, 1.5), random.choice(['M', 'F'])))

        for _ in range(self.INITIAL_PREDATOR_COUNT):
            location = self._generate_valid_location()
            self.predators.append(Predator(*location, random.uniform(0.5, 1.5), random.choice(['M', 'F'])))

        for _ in range(self.INITIAL_PLANT_COUNT):
            row, col = self._find_valid_plant_location()
            self.grid[row][col] = Terrain('vegetation', self.grid[row][col].elevation)
            self.plants.append(Plant())

    def _initialize_plants(self):
        for _ in range(self.INITIAL_PLANT_COUNT):
            row, col = self._find_valid_plant_location()
            self.grid[row][col] = Terrain('vegetation', self.grid[row][col].elevation)
            self.plants.append(Plant())

    def _find_valid_plant_location(self):
        # Find a valid location for planting a new plant.

        while True:
            row, col = random.randint(0, self.rows - 1), random.randint(0, self.cols - 1)
            if self.grid[row][col].terrain_type != 'water':
                return row, col

def generate_valid_location(ecosystem):
    while True:
        row, col = random.randint(0, ROWS - 1), random.randint(0, COLS - 1)
        # Check if the tile is non-water and not occupied by any animal
        if ecosystem.grid[row][col].terrain_type != 'water' and not ecosystem.is_tile_occupied(row, col):
            return row, col

def handle_key_press(event, ecosystem, is_paused):
    if event.key == pygame.K_SPACE:
        is_paused = not is_paused
    if ecosystem.manual_temperature_control:
        if event.key == pygame.K_UP:
            ecosystem.ambient_temperature += 1
        elif event.key == pygame.K_DOWN:
            ecosystem.ambient_temperature -= 1

def main():
    ecosystem = Ecosystem(ROWS, COLS)
    ecosystem.initialize_ecosystem()  # Ensure ecosystem is initialized

    running = True
    clock = pygame.time.Clock()
    is_paused = False  # Start with the simulation unpaused

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                handle_key_press(event, ecosystem, is_paused)

        screen.fill((0, 0, 0))  # Fill the screen with black for clarity

        if not is_paused:
            ecosystem.simulate_cycle()  # Update and draw the ecosystem

        pygame.display.flip()  # Update the display
        clock.tick(60)  # Maintain 60 frames per second

        pygame.time.delay(200)

    pygame.quit()

if __name__ == "__main__":
    main()
import sys
import time
import pandas as pd
import numpy as np
import pygame

from pygame.locals import *
from itertools import product
from utils import display


class Flanker(object):
    def __init__(self, screen, background, blocks=1, compatibility=False):
        # Get the pygame display window
        self.screen = screen
        self.background = background

        # Sets font and font size
        self.font = pygame.font.SysFont("arial", 30)
        self.font_stim = pygame.font.SysFont("arial", 90)

        # Get screen info
        self.screen_x = self.screen.get_width()
        self.screen_y = self.screen.get_height()

        # Fill background
        self.background.fill((255, 255, 255))
        pygame.display.set_caption("Eriksen Flanker Task")
        pygame.mouse.set_visible(0)

        # Experiment options
        self.NUM_BLOCKS = blocks
        self.COMPATIBILITY = compatibility  # compatibility condition
        self.FIXATION_DURATION = 1000
        self.FLANKER_DURATION = 200
        self.MAX_RESPONSE_TIME = 1000
        self.FEEDBACK_DURATION = 1500
        self.ITI = 1500

        # Specify factor levels
        self.CONGRUENCY_LEVELS = ("congruent", "incongruent")
        self.DIRECTION_LEVELS = ("left", "right")

        # Create level combinations
        # Level combinations give us 4 trials.
        self.combinations = list(
            product(self.CONGRUENCY_LEVELS, self.DIRECTION_LEVELS))

        # Create output dataframe
        self.all_data = pd.DataFrame()

    def create_block(self, block_num, combinations, trial_type):
        if trial_type == "main":
            cur_combinations = combinations * 30  # 120 total trials
        else:
            cur_combinations = combinations * 5  # 20 practice trials

        # Add shuffled combinations to dataframe
        np.random.shuffle(cur_combinations)
        cur_block = pd.DataFrame(data=cur_combinations,
                                 columns=('congruency', 'direction'))

        # Add timing info to dataframe
        cur_block["block"] = block_num + 1

        return cur_block

    def display_flanker(self, flanker_type, direction):
        # Left flanker
        if direction == "left":
            if flanker_type == "congruent":
                stimulus = "< < < < <"
            else:
                stimulus = "> > < > >"
        # Right flanker
        else:
            if flanker_type == "congruent":
                stimulus = "> > > > >"
            else:
                stimulus = "< < > < <"

        display.text(self.screen, self.font_stim, stimulus, "center", "center")

    def display_trial(self, trial_num, data):
        # Check for a quit press after stimulus was shown
        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_F12:
                sys.exit(0)

        # Display fixation
        self.screen.blit(self.background, (0, 0))
        display.text(self.screen, self.font, "+", "center", "center")
        pygame.display.flip()

        display.wait(self.FIXATION_DURATION)

        # Display flanker stimulus
        self.screen.blit(self.background, (0, 0))
        self.display_flanker(data["congruency"][trial_num],
                             data["direction"][trial_num])
        pygame.display.flip()

        # Clear the event queue before checking for responses
        start_time = int(round(time.time() * 1000))
        pygame.event.clear()
        response = "NA"
        too_slow = False
        wait_response = True
        while wait_response:
            for event in pygame.event.get():
                if event.type == KEYDOWN and event.key == K_LEFT:
                    response = "left"
                    wait_response = False
                elif event.type == KEYDOWN and event.key == K_RIGHT:
                    response = "right"
                    wait_response = False
                elif event.type == KEYDOWN and event.key == K_F12:
                    sys.exit(0)

            end_time = int(round(time.time() * 1000))

            if end_time - start_time >= self.FLANKER_DURATION:
                self.screen.blit(self.background, (0, 0))
                pygame.display.flip()

            if end_time - start_time >= self.MAX_RESPONSE_TIME:
                # If time limit has been reached, consider it a missed trial
                wait_response = False
                too_slow = True

        # Store reaction time and response
        rt = int(round(time.time() * 1000)) - start_time
        data.set_value(trial_num, 'RT', rt)
        data.set_value(trial_num, 'response', response)

        correct = 1 if response == data["direction"][trial_num] else 0
        data.set_value(trial_num, 'correct', correct)

        # Display feedback
        self.screen.blit(self.background, (0, 0))
        if too_slow:
            display.text(self.screen, self.font, "too slow",
                         "center", "center", (0, 0, 0))
        else:
            if correct == 1:
                display.text(self.screen, self.font, "right",
                             "center", "center", (0, 255, 0))
            else:
                display.text(self.screen, self.font, "wrong",
                             "center", "center", (255, 0, 0))
        pygame.display.flip()

        display.wait(self.FEEDBACK_DURATION)

        # Display fixation
        self.screen.blit(self.background, (0, 0))
        display.text(self.screen, self.font, "+", "center", "center")
        pygame.display.flip()
        display.wait(self.ITI)

    def run_block(self, block_num, total_blocks, block_type):
        cur_block = self.create_block(
            block_num, self.combinations, block_type)

        for i in range(cur_block.shape[0]):
            self.display_trial(i, cur_block)

        if block_type == "main":
            # Add block data to all_data
            self.all_data = pd.concat([self.all_data, cur_block])

        # End of block screen
        if block_num != total_blocks - 1:  # If not the final block
            self.screen.blit(self.background, (0, 0))
            display.text(self.screen, self.font,
                         "End of current block. "
                         "Start next block when you're ready...",
                         100, "center")
            display.text_space(self.screen, self.font,
                               "center", (self.screen_y/2) + 100)
            pygame.display.flip()

            display.wait_for_space()

    def run(self):
        # Instructions
        self.screen.blit(self.background, (0, 0))
        display.text(self.screen, self.font, "Eriksen Flanker Task",
                     "center", self.screen_y/2 - 300)
        display.text(self.screen, self.font,
                     "Keep your eyes on the fixation cross at the "
                     "start of each trial:",
                     100, self.screen_y/2 - 200)
        display.text(self.screen, self.font, "+", "center", self.screen_y/2 - 150)
        display.text(self.screen, self.font,
                     "A set of arrows will appear somewhere on the screen:",
                     100, self.screen_y/2 - 100)
        display.text(self.screen, self.font_stim,
                     "> > < > >", "center", self.screen_y/2 - 50)
        display.text(self.screen, self.font,
                     "Use the Left / Right arrow keys to indicate "
                     "the direction of the CENTER arrow.",
                     100, self.screen_y/2 + 50)
        display.text(self.screen, self.font,
                     "In example above, you should press the Left arrow.",
                     100, self.screen_y/2 + 100)
        display.text_space(self.screen, self.font,
                           "center", (self.screen_y/2) + 300)
        pygame.display.flip()

        display.wait_for_space()

        # Instructions Practice
        self.screen.blit(self.background, (0, 0))
        display.text(self.screen, self.font,
                     "We'll begin with a some practice trials...",
                     "center", "center")
        display.text_space(self.screen, self.font,
                           "center", self.screen_y/2 + 100)
        pygame.display.flip()

        display.wait_for_space()

        # Practice trials
        self.run_block(0, 1, "practice")

        # Instructions Practice End
        self.screen.blit(self.background, (0, 0))
        display.text(self.screen, self.font,
                     "We will now begin the main trials...",
                     100, self.screen_y/2)
        display.text_space(self.screen, self.font,
                           "center", self.screen_y/2 + 200)
        pygame.display.flip()

        display.wait_for_space()

        # Main task
        for i in range(self.NUM_BLOCKS):
            self.run_block(i, self.NUM_BLOCKS, "main")

        # Create trial number column
        self.all_data["trial"] = list(range(1, len(self.all_data) + 1))

        # Rearrange the dataframe
        columns = ['trial', 'block', 'congruency', 'direction',
                   'response', 'correct', 'RT']
        self.all_data = self.all_data[columns]

        # End screen
        self.screen.blit(self.background, (0, 0))
        display.text(self.screen, self.font, "End of task", "center", "center")
        display.text_space(self.screen, self.font,
                           "center", self.screen_y/2 + 100)
        pygame.display.flip()

        display.wait_for_space()

        print("- Flanker complete")

        return self.all_data

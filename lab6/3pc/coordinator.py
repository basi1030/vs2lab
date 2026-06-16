import random
import logging

import stablelog

from const3pc import (
    VOTE_REQUEST,
    PREPARE_COMMIT,
    GLOBAL_COMMIT,
    GLOBAL_ABORT,
    VOTE_COMMIT,
    VOTE_ABORT,
    READY_COMMIT,
    TIMEOUT
)


class Coordinator:
    CRASH_BEFORE_VOTE_REQUEST = 0.10
    CRASH_AFTER_VOTE_REQUEST = 0.90
    CRASH_AFTER_PREPARE_COMMIT = 0.30

    def __init__(self, chan):

        self.channel = chan

        self.coordinator = self.channel.join(
            'coordinator'
        )

        self.participants = []

        self.stable_log = stablelog.create_log(
            "coordinator-" + self.coordinator
        )

        self.logger = logging.getLogger(
            "vs2lab.lab6.3pc.Coordinator"
        )

        self.state = None

    @staticmethod
    def _crash(probability):
        return random.random() < probability

    def _enter_state(self, state): 
        self.stable_log.info(state) 
        self.logger.info( "Coordinator {} entered state {}" .format(self.coordinator, state) ) 
        
        self.state = state

    def init(self):

        self.channel.bind(
            self.coordinator
        )

        self.participants = self.channel.subgroup(
            'participant'
        )

        self._enter_state('INIT')

    def run(self):

        #
        # PHASE 1
        #

        self._enter_state('WAIT')

        if self._crash(self.CRASH_BEFORE_VOTE_REQUEST):

            self.logger.info(
                "Coordinator crashed before VOTE_REQUEST"
            )

            return (
                "Coordinator crashed before VOTE_REQUEST"
            )

        self.channel.send_to(
            self.participants,
            VOTE_REQUEST
        )

        #
        # Crash nach VOTE_REQUEST
        #

        if self._crash(self.CRASH_AFTER_VOTE_REQUEST):

            self.logger.info(
                "Coordinator crashed after VOTE_REQUEST"
            )

            return (
                "Coordinator crashed after VOTE_REQUEST"
            )

        waiting = list(self.participants)

        while waiting:

            msg = self.channel.receive_from(
                self.participants,
                TIMEOUT
            )

            #
            # participant failure in WAIT
            # -> ABORT
            #

            if not msg:

                self._enter_state('ABORT')

                self.channel.send_to(
                    self.participants,
                    GLOBAL_ABORT
                )

                return (
                    "Coordinator aborted "
                    "(participant timeout)"
                )

            sender, vote = msg

            if vote == VOTE_ABORT:

                self._enter_state('ABORT')

                self.channel.send_to(
                    self.participants,
                    GLOBAL_ABORT
                )

                return (
                    "Coordinator aborted "
                    "(vote abort)"
                )

            assert vote == VOTE_COMMIT

            waiting.remove(sender)

        #
        # PHASE 2
        #

        self._enter_state('PRECOMMIT')

        self.channel.send_to(
            self.participants,
            PREPARE_COMMIT
        )

        #
        # Crash nach PREPARE_COMMIT
        #

        if self._crash(self.CRASH_AFTER_PREPARE_COMMIT):

            self.logger.info(
                "Coordinator crashed after PREPARE_COMMIT"
            )

            return (
                "Coordinator crashed after PREPARE_COMMIT"
            )

        waiting = list(self.participants)

        while waiting:

            msg = self.channel.receive_from(
                self.participants,
                TIMEOUT
            )

            #
            # participant failure in PRECOMMIT
            # -> COMMIT
            #

            if not msg:

                self._enter_state('COMMIT')

                self.channel.send_to(
                    self.participants,
                    GLOBAL_COMMIT
                )

                return (
                    "Coordinator committed "
                    "(participant timeout in PRECOMMIT)"
                )

            sender, answer = msg

            if answer != READY_COMMIT:

                self._enter_state('ABORT')

                self.channel.send_to(
                    self.participants,
                    GLOBAL_ABORT
                )

                return (
                    "Coordinator aborted "
                    "(invalid response)"
                )

            waiting.remove(sender)

        #
        # PHASE 3
        #

        self._enter_state('COMMIT')

        self.channel.send_to(
            self.participants,
            GLOBAL_COMMIT
        )

        return (
            "Coordinator {} terminated in state COMMIT."
            .format(self.coordinator)
        )
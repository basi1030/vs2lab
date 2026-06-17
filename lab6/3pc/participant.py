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
    LOCAL_ABORT,
    LOCAL_SUCCESS,
    TIMEOUT
)


class Participant:

    def __init__(self, chan):

        self.channel = chan

        self.participant = self.channel.join(
            'participant'
        )

        self.stable_log = stablelog.create_log(
            "participant-" + self.participant
        )

        self.logger = logging.getLogger(
            "vs2lab.lab6.3pc.Participant"
        )

        self.state = None

    @staticmethod
    def _do_work():

        return (
            LOCAL_ABORT
            if random.random() > 2 / 3
            else LOCAL_SUCCESS
        )

    def _enter_state(self, state):

        self.stable_log.info(state)

        self.logger.info(
            "Participant {} entered state {}"
            .format(self.participant, state)
        )

        self.state = state

    def _new_coordinator(self):
        return min(
            self.participants,
            key=int
        )

    def init(self):

        self.channel.bind(
            self.participant
        )

        self.coordinator = self.channel.subgroup(
            'coordinator'
        )

        self.participants = self.channel.subgroup(
            'participant'
        )

        self._enter_state('INIT')

    def run(self):

        #
        # wait for vote request
        #

        msg = self.channel.receive_from(
            self.coordinator,
            TIMEOUT
        )

        if not msg:

            self._enter_state('ABORT')

            return (
                "Participant {} aborted."
                .format(self.participant)
            )

        assert msg[1] == VOTE_REQUEST

        #
        # local transaction
        #

        result = self._do_work()

        if result == LOCAL_ABORT:

            self.channel.send_to(
                self.coordinator,
                VOTE_ABORT
            )

            self._enter_state('ABORT')

            return (
                "Participant {} aborted."
                .format(self.participant)
            )

        #
        # READY
        #

        self._enter_state('READY')

        self.channel.send_to(
            self.coordinator,
            VOTE_COMMIT
        )

        #
        # wait PREPARE_COMMIT
        #

        msg = self.channel.receive_from(
            self.coordinator,
            TIMEOUT
        )

        if not msg:

            #
            # Coordinator crashed while READY
            # 3PC termination: ABORT
            #

            new_coord = self._new_coordinator()

            if self.participant == new_coord:

                self.logger.info(
                    "Participant {} : Becoming coordinator (READY)".format(self.participant)
                )

                self.channel.send_to(
                    self.participants,
                    GLOBAL_ABORT
                )

            self._enter_state('ABORT')

            return (
                "Participant {} terminated in state ABORT."
                .format(self.participant)
            )

        if msg[1] == GLOBAL_ABORT:

            self._enter_state('ABORT')

            return (
                "Participant {} aborted."
                .format(self.participant)
            )

        assert msg[1] == PREPARE_COMMIT

        #
        # PRECOMMIT
        #

        self._enter_state('PRECOMMIT')

        self.channel.send_to(
            self.coordinator,
            READY_COMMIT
        )

        #
        # wait GLOBAL_COMMIT
        #

        msg = self.channel.receive_from(
            self.coordinator,
            TIMEOUT
        )

        if not msg:

            #
            # Coordinator crashed while PRECOMMIT
            # 3PC termination: COMMIT
            #

            new_coord = self._new_coordinator()

            if self.participant == new_coord:

                self.logger.info(
                    "Participant {} : Becoming coordinator (PRECOMMIT)".format(self.participant)
                )

                self.channel.send_to(
                    self.participants,
                    GLOBAL_COMMIT
                )

            self._enter_state('COMMIT')

            return (
                "Participant {} terminated in state COMMIT."
                .format(self.participant)
            )

        assert msg[1] == GLOBAL_COMMIT

        self._enter_state('COMMIT')

        return (
            "Participant {} terminated in state COMMIT."
            .format(self.participant)
        )
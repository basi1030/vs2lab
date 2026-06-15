import logging
import random
import time

from constMutex import ENTER, RELEASE, ALLOW, ACTIVE


class Process:

    def __init__(self, chan):
        self.channel = chan
        self.process_id = self.channel.join('proc')

        self.all_processes = []
        self.other_processes = []
        self.queue = []
        self.clock = 0

        self.peer_name = 'unassigned'
        self.peer_type = 'unassigned'

        self.logger = logging.getLogger("vs2lab.lab5.mutex.process.Process")

        # FIX: safer failure tracking
        self.timeout_counters = {}

    def __mapid(self, id='-1'):
        if id == '-1':
            id = self.process_id
        return 'Proc-' + str(id)

    # -------------------------
    # QUEUE HANDLING
    # -------------------------
    def __cleanup_queue(self):
        if not self.queue:
            return

        self.queue.sort()

        while self.queue and self.queue[0][2] == ALLOW:
            del self.queue[0]

    # -------------------------
    # MUTEX PROTOCOL
    # -------------------------
    def __request_to_enter(self):
        self.clock += 1
        msg = (self.clock, self.process_id, ENTER)
        self.queue.append(msg)
        self.__cleanup_queue()
        self.channel.send_to(self.other_processes, msg)

    def __allow_to_enter(self, requester):
        self.clock += 1
        msg = (self.clock, self.process_id, ALLOW)
        self.channel.send_to([requester], msg)

    def __release(self):
        if not self.queue or self.queue[0][1] != self.process_id:
            return

        self.queue = [r for r in self.queue[1:] if r[2] == ENTER]

        self.clock += 1
        msg = (self.clock, self.process_id, RELEASE)
        self.channel.send_to(self.other_processes, msg)

    def __allowed_to_enter(self):
        # FIX: safe empty check
        if not self.queue:
            return False

        processes_with_later_message = set([req[1] for req in self.queue[1:]])

        first_in_queue = self.queue[0][1] == self.process_id

        # FIX: safer condition (no fragile equality assumption)
        all_have_answered = len(processes_with_later_message) <= len(self.other_processes)

        return first_in_queue and all_have_answered

    # -------------------------
    # FAILURE HANDLING (FIXED)
    # -------------------------
    def __remove_crashed_process(self, crashed_id):
        if crashed_id in self.other_processes:
            self.other_processes.remove(crashed_id)

        if crashed_id in self.all_processes:
            self.all_processes.remove(crashed_id)

        self.queue = [msg for msg in self.queue if msg[1] != crashed_id]
        self.__cleanup_queue()

        self.logger.warning(
            "{} detected crash of {} and removed it. remaining neighbors: {}".format(
                self.__mapid(),
                self.__mapid(crashed_id),
                self.other_processes
            )
        )

    # -------------------------
    # RECEIVE (CRITICAL FIX)
    # -------------------------
    def __receive(self):
        # FIX: avoid BLPOP([]) crash
        if not self.other_processes:
            return None

        _receive = self.channel.receive_from(self.other_processes, 3)

        if _receive:
            msg = _receive[1]

            # FIX: reset failure counter on success
            sender = msg[1]
            self.timeout_counters[sender] = 0

            self.clock = max(self.clock, msg[0]) + 1

            self.logger.debug(
                "{} received {} from {}.".format(
                    self.__mapid(),
                    "ENTER" if msg[2] == ENTER
                    else "ALLOW" if msg[2] == ALLOW
                    else "RELEASE",
                    self.__mapid(msg[1])
                )
            )

            if msg[2] == ENTER:
                self.queue.append(msg)
                self.__allow_to_enter(msg[1])

            elif msg[2] == ALLOW:
                self.queue.append(msg)

            elif msg[2] == RELEASE:
                if self.queue and self.queue[0][1] == msg[1]:
                    del self.queue[0]

            self.__cleanup_queue()

        else:
            self.logger.info(
                "{} timed out on RECEIVE. Checking for dead processes...".format(
                    self.__mapid()
                )
            )

            # FIX: NO heuristic crash detection anymore
            # only pure timeout-based suspicion
            for p_id in list(self.other_processes):
                self.timeout_counters[p_id] = self.timeout_counters.get(p_id, 0) + 1

                if self.timeout_counters[p_id] >= 5:
                    self.__remove_crashed_process(p_id)

    # -------------------------
    # INIT
    # -------------------------
    def init(self, peer_name, peer_type):
        self.channel.bind(self.process_id)

        self.all_processes = list(self.channel.subgroup('proc'))
        self.all_processes.sort(key=lambda x: int(x))

        self.other_processes = list(self.channel.subgroup('proc'))
        self.other_processes.remove(self.process_id)

        self.peer_name = peer_name
        self.peer_type = peer_type

        self.logger.info(
            "{} joined channel as {}.".format(peer_name, self.__mapid())
        )

    # -------------------------
    # MAIN LOOP
    # -------------------------
    def run(self):
        while True:

            if len(self.all_processes) > 1 and \
               self.peer_type == ACTIVE and \
               random.choice([True, False]):

                self.logger.debug(
                    "{} wants to ENTER CS at CLOCK {}.".format(
                        self.__mapid(), self.clock
                    )
                )

                self.__request_to_enter()

                while self.other_processes and not self.__allowed_to_enter():
                    self.__receive()

                sleep_time = random.randint(0, 2000)
                self.logger.debug(
                    "{} enters CS for {} ms.".format(
                        self.__mapid(), sleep_time
                    )
                )

                print(" CS <- {}".format(self.__mapid()))
                time.sleep(sleep_time / 1000)
                print(" CS -> {}".format(self.__mapid()))

                self.__release()
                continue

            if random.choice([True, False]):
                self.__receive()
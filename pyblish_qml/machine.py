from PyQt5 import QtCore

import util


class Machine(QtCore.QStateMachine):
    def __init__(self, parent=None):
        super(Machine, self).__init__(parent)

        #  _______________
        # |               |
        # |               |
        # |               |
        # |_______________|
        #
        group = util.QState("group", QtCore.QState.ParallelStates, machine)

        #  _______________
        # | ____     ____ |
        # ||    |---|    ||
        # ||____|---|____||
        # |_______________| - Parallell State
        #
        visibility = util.QState("visibility", group)

        hidden = util.QState("hidden", visibility)
        visible = util.QState("visible", visibility)

        #  _______________
        # | ____     ____ |
        # ||    |---|    ||
        # ||____|---|____||
        # |_______________| - Parallell State
        #
        operation = util.QState("operation", group)

        ready = util.QState("ready", operation)
        publishing = util.QState("publishing", operation)
        finished = util.QState("finished", operation)
        repairing = util.QState("repairing", operation)
        initialising = util.QState("initialising", operation)
        stopping = util.QState("stopping", operation)
        stopped = util.QState("stopped", operation)
        saving = util.QState("saving", operation)

        #  _______________
        # | ____     ____ |
        # ||    |---|    ||
        # ||____|---|____||
        # |_______________| - Parallell State
        #
        errored = util.QState("errored", group)

        clean = util.QState("clean", errored)
        dirty = util.QState("dirty", errored)

        #  _______________
        # | ____     ____ |
        # ||    |---|    ||
        # ||____|---|____||
        # |_______________|
        # | ____     ____ |
        # ||    |---|    ||
        # ||____|---|____||
        # |_______________|
        #
        hidden.addTransition(self.s_show, visible)
        visible.addTransition(self.s_hide, hidden)

        ready.addTransition(self.s_publishing, publishing)
        ready.addTransition(self.s_initialising, initialising)
        ready.addTransition(self.s_repairing, repairing)
        ready.addTransition(self.s_saving, saving)
        saving.addTransition(self.s_saved, ready)
        publishing.addTransition(self.s_stopping, stopping)
        publishing.addTransition(self.s_finished, finished)
        finished.addTransition(self.s_initialising, initialising)
        initialising.addTransition(self.s_initialised, ready)
        stopping.addTransition(self.s_stopped, stopped)
        stopped.addTransition(self.s_finished, finished)

        dirty.addTransition(self.s_initialising, clean)
        clean.addTransition(self.s_plugin_failure, dirty)

        # Set initial states
        for compound, state in {self: group,
                                visibility: hidden,
                                operation: initialising,
                                errored: clean}.items():
            compound.setInitialState(state)

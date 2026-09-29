//! Deployable single-decree Paxos for a three-replica cluster.
//!
//! [`Node`] is the complete protocol state of one replica: acceptor, proposer
//! (with ballot allocation and preemption handling) and learner. It performs no
//! I/O and is deterministic. Each call to [`Node::handle`] consumes one input and
//! emits at most one message; this is the code extracted to Lean and verified.
//!
//! Runtime contract (implemented by `src/bin/paxosd.rs`):
//! * inputs to one node are processed one at a time;
//! * the state returned by `handle` is durably stored *before* its message is
//!   sent, and a restarted replica resumes from its last stored state;
//! * `Deliver { from, .. }` is only produced for a message that replica `from`
//!   actually emitted to this replica (authenticated, possibly duplicated,
//!   delayed, reordered or lost);
//! * a message addressed to [`Dest::All`] is offered to every replica, itself included.

/// Replica identifiers are `0..NODES`; any two replicas form a quorum.
pub const NODES: u8 = 3;
/// Ballot allocation stops at this bound, so ballot arithmetic cannot overflow.
pub const BALLOT_LIMIT: u64 = 4_611_686_018_427_387_904; // 2^62

#[derive(Clone, Copy, PartialEq, Eq)]
pub struct Vote {
    pub ballot: u64,
    pub value: u64,
}

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Msg {
    /// Client value, broadcast so that whichever replica leads can propose it.
    Request { value: u64 },
    Prepare { ballot: u64 },
    Promise { ballot: u64, accepted: Option<Vote> },
    Accept { vote: Vote },
    Accepted { vote: Vote },
    /// The acceptor refused `ballot` because it has promised `promised`.
    Nack { ballot: u64, promised: u64 },
}

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Dest {
    To(u8),
    All,
}

#[derive(Clone, Copy, PartialEq, Eq)]
pub struct Send {
    pub to: Dest,
    pub msg: Msg,
}

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Input {
    /// A client asks the cluster to decide `value`.
    Submit { value: u64 },
    Deliver { from: u8, msg: Msg },
    /// Timer: start or restart a ballot when needed, otherwise retransmit.
    Tick,
}

/// One replica. Fields are public so the runtime can persist and restore them;
/// they must only ever hold a state previously returned by `new` or `handle`.
#[derive(Clone, Copy, PartialEq, Eq)]
pub struct Node {
    pub id: u8,
    // Acceptor.
    pub promised: u64,
    pub accepted: Option<Vote>,
    // Proposer. `ballot == 0` means no attempt has started. Ballots owned by
    // replica `i` are exactly those congruent to `i` modulo `NODES`.
    pub value: Option<u64>,
    pub ballot: u64,
    pub max_seen: u64,
    pub proposal: Option<u64>,
    pub promise0: Option<Option<Vote>>,
    pub promise1: Option<Option<Vote>>,
    pub promise2: Option<Option<Vote>>,
    // Learner: the highest-ballot vote announced by each acceptor.
    pub vote0: Option<Vote>,
    pub vote1: Option<Vote>,
    pub vote2: Option<Vote>,
    pub decided: Option<u64>,
}

fn higher(a: u64, b: u64) -> u64 {
    if a < b {
        b
    } else {
        a
    }
}

/// The smallest ballot above `floor` owned by replica `id`.
/// Callers keep `floor < BALLOT_LIMIT`, so this cannot overflow.
pub fn next_ballot(floor: u64, id: u8) -> u64 {
    (floor / 3 + 1) * 3 + id as u64
}

/// Value to propose after promises from two distinct acceptors: the value of
/// the highest-ballot vote reported, or the proposer's own value if none.
pub fn select(left: Option<Vote>, right: Option<Vote>, offered: u64) -> u64 {
    match (left, right) {
        (Some(a), Some(b)) => {
            if b.ballot > a.ballot {
                b.value
            } else {
                a.value
            }
        }
        (Some(a), None) => a.value,
        (None, Some(b)) => b.value,
        (None, None) => offered,
    }
}

fn same(a: Vote, b: Vote) -> bool {
    a.ballot == b.ballot && a.value == b.value
}

/// Two distinct acceptors announced the same vote.
fn agreed(v0: Option<Vote>, v1: Option<Vote>, v2: Option<Vote>) -> Option<u64> {
    if let (Some(a), Some(b)) = (v0, v1) {
        if same(a, b) {
            return Some(a.value);
        }
    }
    if let (Some(a), Some(c)) = (v0, v2) {
        if same(a, c) {
            return Some(a.value);
        }
    }
    if let (Some(b), Some(c)) = (v1, v2) {
        if same(b, c) {
            return Some(b.value);
        }
    }
    None
}

/// Promises recorded from two distinct acceptors, if any.
fn quorum(
    p0: Option<Option<Vote>>,
    p1: Option<Option<Vote>>,
    p2: Option<Option<Vote>>,
) -> Option<(Option<Vote>, Option<Vote>)> {
    match (p0, p1, p2) {
        (Some(a), Some(b), _) => Some((a, b)),
        (Some(a), None, Some(c)) => Some((a, c)),
        (None, Some(b), Some(c)) => Some((b, c)),
        _ => None,
    }
}

impl Node {
    pub fn new(id: u8) -> Node {
        Node {
            id,
            promised: 0,
            accepted: None,
            value: None,
            ballot: 0,
            max_seen: 0,
            proposal: None,
            promise0: None,
            promise1: None,
            promise2: None,
            vote0: None,
            vote1: None,
            vote2: None,
            decided: None,
        }
    }

    /// Process one input. Never panics, for every state and input.
    pub fn handle(&mut self, input: Input) -> Option<Send> {
        match input {
            Input::Submit { value } => Some(Send {
                to: Dest::All,
                msg: Msg::Request { value },
            }),
            Input::Deliver { from, msg } => self.deliver(from, msg),
            Input::Tick => self.tick(),
        }
    }

    fn deliver(&mut self, from: u8, msg: Msg) -> Option<Send> {
        if from >= NODES {
            return None;
        }
        match msg {
            Msg::Request { value } => {
                if let None = self.value {
                    self.value = Some(value);
                }
                None
            }
            Msg::Prepare { ballot } => self.on_prepare(from, ballot),
            Msg::Promise { ballot, accepted } => self.on_promise(from, ballot, accepted),
            Msg::Accept { vote } => self.on_accept(from, vote),
            Msg::Accepted { vote } => self.on_accepted(from, vote),
            Msg::Nack { ballot: _, promised } => {
                if promised > self.max_seen {
                    self.max_seen = promised;
                }
                None
            }
        }
    }

    fn on_prepare(&mut self, from: u8, ballot: u64) -> Option<Send> {
        if ballot > self.promised {
            self.promised = ballot;
            Some(Send {
                to: Dest::To(from),
                msg: Msg::Promise {
                    ballot,
                    accepted: self.accepted,
                },
            })
        } else {
            Some(Send {
                to: Dest::To(from),
                msg: Msg::Nack {
                    ballot,
                    promised: self.promised,
                },
            })
        }
    }

    fn on_accept(&mut self, from: u8, vote: Vote) -> Option<Send> {
        if vote.ballot >= self.promised {
            self.promised = vote.ballot;
            self.accepted = Some(vote);
            Some(Send {
                to: Dest::All,
                msg: Msg::Accepted { vote },
            })
        } else {
            Some(Send {
                to: Dest::To(from),
                msg: Msg::Nack {
                    ballot: vote.ballot,
                    promised: self.promised,
                },
            })
        }
    }

    fn on_promise(&mut self, from: u8, ballot: u64, accepted: Option<Vote>) -> Option<Send> {
        if ballot != self.ballot || ballot == 0 {
            return None;
        }
        if let Some(_) = self.proposal {
            return None;
        }
        if from == 0 {
            self.promise0 = Some(accepted);
        } else if from == 1 {
            self.promise1 = Some(accepted);
        } else {
            self.promise2 = Some(accepted);
        }
        let offered = match self.value {
            Some(v) => v,
            None => return None,
        };
        match quorum(self.promise0, self.promise1, self.promise2) {
            Some((left, right)) => {
                let value = select(left, right, offered);
                self.proposal = Some(value);
                Some(Send {
                    to: Dest::All,
                    msg: Msg::Accept {
                        vote: Vote { ballot, value },
                    },
                })
            }
            None => None,
        }
    }

    fn on_accepted(&mut self, from: u8, vote: Vote) -> Option<Send> {
        let current = if from == 0 {
            self.vote0
        } else if from == 1 {
            self.vote1
        } else {
            self.vote2
        };
        let newer = match current {
            Some(old) => vote.ballot > old.ballot,
            None => true,
        };
        if newer {
            if from == 0 {
                self.vote0 = Some(vote);
            } else if from == 1 {
                self.vote1 = Some(vote);
            } else {
                self.vote2 = Some(vote);
            }
        }
        if let None = self.decided {
            self.decided = agreed(self.vote0, self.vote1, self.vote2);
        }
        None
    }

    fn tick(&mut self) -> Option<Send> {
        if self.ballot == 0 {
            match self.value {
                Some(_) => self.start(),
                None => None,
            }
        } else if self.max_seen > self.ballot {
            self.start()
        } else {
            match self.proposal {
                Some(value) => Some(Send {
                    to: Dest::All,
                    msg: Msg::Accept {
                        vote: Vote {
                            ballot: self.ballot,
                            value,
                        },
                    },
                }),
                None => Some(Send {
                    to: Dest::All,
                    msg: Msg::Prepare {
                        ballot: self.ballot,
                    },
                }),
            }
        }
    }

    /// Begin phase 1 with a fresh ballot above everything this replica has seen.
    fn start(&mut self) -> Option<Send> {
        let floor = higher(higher(self.max_seen, self.promised), self.ballot);
        if floor >= BALLOT_LIMIT {
            return None;
        }
        let ballot = next_ballot(floor, self.id);
        self.ballot = ballot;
        self.proposal = None;
        self.promise0 = None;
        self.promise1 = None;
        self.promise2 = None;
        Some(Send {
            to: Dest::All,
            msg: Msg::Prepare { ballot },
        })
    }
}

#[cfg(test)]
mod tests;

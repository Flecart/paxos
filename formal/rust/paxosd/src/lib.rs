//! Deployable single-decree Paxos for a cluster of `n` replicas (1 ≤ n ≤ 255).
//!
//! [`Node`] is the complete protocol state of one replica: acceptor, proposer
//! (with ballot allocation and preemption handling) and learner. It performs no
//! I/O and is deterministic. Each call to [`Node::handle`] consumes one input and
//! emits at most one message; this is the code extracted to Lean and verified.
//! Any strict majority of the `n` replicas is a quorum.
//!
//! Runtime contract (implemented by `src/bin/paxosd`):
//! * inputs to one node are processed one at a time;
//! * the state returned by `handle` is durably stored *before* its message is
//!   sent, and a restarted replica resumes from its last stored state;
//! * `Deliver { from, .. }` is only produced for a message that replica `from`
//!   actually emitted to this replica (authenticated, possibly duplicated,
//!   delayed, reordered or lost);
//! * a message addressed to [`Dest::All`] is offered to every replica, itself included.

/// Ballot allocation stops at this bound, so ballot arithmetic cannot overflow.
pub const BALLOT_LIMIT: u64 = 4_611_686_018_427_387_904; // 2^62

#[derive(Clone, Copy, PartialEq, Eq)]
pub struct Vote {
    pub ballot: u64,
    pub value: u64,
}

/// A promise for `ballot` reporting the acceptor's last vote.
#[derive(Clone, Copy, PartialEq, Eq)]
pub struct Promise {
    pub ballot: u64,
    pub accepted: Option<Vote>,
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
#[derive(Clone, PartialEq, Eq)]
pub struct Node {
    pub id: u8,
    /// Cluster size.
    pub n: u8,
    // Acceptor.
    pub promised: u64,
    pub accepted: Option<Vote>,
    // Proposer. `ballot == 0` means no attempt has started. Ballots owned by
    // replica `i` are exactly those congruent to `i` modulo `n`.
    pub value: Option<u64>,
    pub ballot: u64,
    pub max_seen: u64,
    pub proposal: Option<u64>,
    /// Latest promise received from each acceptor; only entries whose ballot
    /// equals `ballot` count, so a new ballot needs no reset.
    pub promises: Vec<Option<Promise>>,
    // Learner: the highest-ballot vote announced by each acceptor.
    pub votes: Vec<Option<Vote>>,
    pub decided: Option<u64>,
}

fn higher(a: u64, b: u64) -> u64 {
    if a < b {
        b
    } else {
        a
    }
}

/// The smallest ballot above `floor` owned by replica `id` in a cluster of `n`.
/// Callers keep `floor < BALLOT_LIMIT` and `n > 0`, so this cannot overflow.
pub fn next_ballot(floor: u64, id: u8, n: u8) -> u64 {
    (floor / n as u64 + 1) * n as u64 + id as u64
}

/// Strict majority of `n`.
pub fn majority(count: u64, n: u8) -> bool {
    count > n as u64 / 2
}

/// Number of acceptors whose recorded promise is for ballot `b`.
pub fn count_promises(ps: &Vec<Option<Promise>>, b: u64) -> u64 {
    let mut i: usize = 0;
    let mut c: u64 = 0;
    while i < ps.len() {
        if let Some(p) = ps[i] {
            if p.ballot == b {
                c += 1;
            }
        }
        i += 1;
    }
    c
}

/// Highest-ballot vote reported by the promises recorded for ballot `b`.
pub fn highest(ps: &Vec<Option<Promise>>, b: u64) -> Option<Vote> {
    let mut i: usize = 0;
    let mut best: Option<Vote> = None;
    while i < ps.len() {
        if let Some(p) = ps[i] {
            if p.ballot == b {
                if let Some(v) = p.accepted {
                    best = match best {
                        Some(m) => {
                            if v.ballot > m.ballot {
                                Some(v)
                            } else {
                                Some(m)
                            }
                        }
                        None => Some(v),
                    };
                }
            }
        }
        i += 1;
    }
    best
}

/// Number of acceptors whose announced vote is exactly `v`.
pub fn count_votes(vs: &Vec<Option<Vote>>, v: Vote) -> u64 {
    let mut i: usize = 0;
    let mut c: u64 = 0;
    while i < vs.len() {
        if let Some(x) = vs[i] {
            if x.ballot == v.ballot && x.value == v.value {
                c += 1;
            }
        }
        i += 1;
    }
    c
}

impl Node {
    pub fn new(id: u8, n: u8) -> Node {
        let mut promises = Vec::new();
        let mut votes = Vec::new();
        let mut i: u8 = 0;
        while i < n {
            promises.push(None);
            votes.push(None);
            i += 1;
        }
        Node {
            id,
            n,
            promised: 0,
            accepted: None,
            value: None,
            ballot: 0,
            max_seen: 0,
            proposal: None,
            promises,
            votes,
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
        if from >= self.n {
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
        if from as usize >= self.promises.len() {
            return None;
        }
        self.promises[from as usize] = Some(Promise { ballot, accepted });
        let offered = match self.value {
            Some(v) => v,
            None => return None,
        };
        if majority(count_promises(&self.promises, ballot), self.n) {
            let value = match highest(&self.promises, ballot) {
                Some(m) => m.value,
                None => offered,
            };
            self.proposal = Some(value);
            Some(Send {
                to: Dest::All,
                msg: Msg::Accept {
                    vote: Vote { ballot, value },
                },
            })
        } else {
            None
        }
    }

    fn on_accepted(&mut self, from: u8, vote: Vote) -> Option<Send> {
        if from as usize >= self.votes.len() {
            return None;
        }
        let newer = match self.votes[from as usize] {
            Some(old) => vote.ballot > old.ballot,
            None => true,
        };
        if newer {
            self.votes[from as usize] = Some(vote);
        }
        if let None = self.decided {
            if majority(count_votes(&self.votes, vote), self.n) {
                self.decided = Some(vote.value);
            }
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
        if self.n == 0 {
            return None;
        }
        let floor = higher(higher(self.max_seen, self.promised), self.ballot);
        if floor >= BALLOT_LIMIT {
            return None;
        }
        let ballot = next_ballot(floor, self.id, self.n);
        self.ballot = ballot;
        self.proposal = None;
        Some(Send {
            to: Dest::All,
            msg: Msg::Prepare { ballot },
        })
    }
}

#[cfg(test)]
mod tests;

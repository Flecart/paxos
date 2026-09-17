//! Single-decree Paxos protocol core. Transport supplies authenticated messages.
//! Ballots are globally unique; the runtime must retain acceptor state on recovery.

#[derive(Clone, Copy, PartialEq, Eq)]
pub struct Vote {
    pub ballot: u64,
    pub value: u64,
}

#[derive(Clone, Copy, PartialEq, Eq)]
pub struct Promise {
    pub ballot: u64,
    pub accepted: Option<Vote>,
}

#[derive(PartialEq, Eq)]
pub struct Acceptor {
    promised: u64,
    accepted: Option<Vote>,
}

impl Acceptor {
    pub fn new() -> Self {
        Self {
            promised: 0,
            accepted: None,
        }
    }

    /// Return a snapshot only when this prepare raises the promise.
    pub fn prepare(&mut self, ballot: u64) -> Option<Promise> {
        if ballot > self.promised {
            self.promised = ballot;
            Some(Promise {
                ballot,
                accepted: self.accepted,
            })
        } else {
            None
        }
    }

    /// The proposer must send only one value per globally unique ballot.
    pub fn accept(&mut self, vote: Vote) -> bool {
        if vote.ballot >= self.promised {
            self.promised = vote.ballot;
            self.accepted = Some(vote);
            true
        } else {
            false
        }
    }
}

/// Highest accepted vote from two distinct members of a three-acceptor quorum.
/// Promise provenance, distinct membership and matching ballot are checked by
/// the message dispatcher before these snapshots are supplied.
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

/// One proposer instance per globally unique ballot. The selected proposal is
/// immutable; retransmissions use `issued`, rather than rerunning phase 1.
#[derive(PartialEq, Eq)]
pub struct Proposer {
    ballot: u64,
    issued: Option<Vote>,
}

impl Proposer {
    pub fn new(ballot: u64) -> Self {
        Self {
            ballot,
            issued: None,
        }
    }

    /// Retransmit the immutable issued proposal without reselecting its value.
    pub fn retransmit(&self) -> Option<Vote> {
        self.issued
    }

    pub fn issue(
        &mut self,
        first: u8,
        left: Promise,
        second: u8,
        right: Promise,
        offered: u64,
    ) -> Option<Vote> {
        if first >= 3
            || second >= 3
            || first == second
            || left.ballot != self.ballot
            || right.ballot != self.ballot
        {
            return None;
        }
        match self.issued {
            Some(_) => None,
            None => {
                let vote = Vote {
                    ballot: self.ballot,
                    value: select(left.accepted, right.accepted, offered),
                };
                self.issued = Some(vote);
                Some(vote)
            }
        }
    }
}

/// Two distinct authenticated acceptor votes constitute a decision certificate.
pub fn learn(first: u8, left: Vote, second: u8, right: Vote) -> Option<u64> {
    if first < 3
        && second < 3
        && first != second
        && left.ballot == right.ballot
        && left.value == right.value
    {
        Some(left.value)
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn intersecting_quorums_duplicates_stale_messages_and_highest_vote() {
        let mut nodes: [Acceptor; 3] = std::array::from_fn(|_| Acceptor::new());
        let mut p = Proposer::new(1);
        let l = nodes[0].prepare(1).unwrap();
        let r = nodes[1].prepare(1).unwrap();
        assert!(p.issue(0, l, 0, l, 99).is_none());
        let first = p.issue(0, l, 1, r, 42).unwrap();
        assert!(p.issue(0, l, 1, r, 99).is_none());
        assert!(p.retransmit() == Some(first));
        assert!(nodes[0].accept(first));
        assert!(nodes[1].accept(first));
        assert!(nodes[1].accept(first));
        assert_eq!(learn(0, first, 1, first), Some(42));
        assert_eq!(learn(0, first, 0, first), None);
        let mut next = Proposer::new(2);
        let l = nodes[1].prepare(2).unwrap();
        let r = nodes[2].prepare(2).unwrap();
        let second = next.issue(1, l, 2, r, 99).unwrap();
        assert_eq!(second.value, 42);
        assert!(nodes[1].accept(second));
        assert!(nodes[2].accept(second));
        assert!(!nodes[1].accept(first));
        assert_eq!(learn(1, second, 2, second), Some(42));
        assert_eq!(
            select(
                Some(Vote {
                    ballot: 3,
                    value: 7
                }),
                Some(Vote {
                    ballot: 9,
                    value: 8
                }),
                0
            ),
            8
        );
    }
}

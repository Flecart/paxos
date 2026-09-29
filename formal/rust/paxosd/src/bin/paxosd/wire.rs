//! Byte encodings for protocol messages, replica state and client requests.
//! Decoding rejects truncated input, trailing bytes and unknown tags.

use deployable_paxos::{Dest, Msg, Node, Promise, Send, Vote};

/// Largest cluster size, hence the largest vector length a decoder accepts.
pub const MAX_REPLICAS: usize = 255;

#[derive(Default)]
pub struct Writer(pub Vec<u8>);

impl Writer {
    pub fn u8(&mut self, x: u8) {
        self.0.push(x);
    }
    pub fn u16(&mut self, x: u16) {
        self.0.extend_from_slice(&x.to_be_bytes());
    }
    pub fn u32(&mut self, x: u32) {
        self.0.extend_from_slice(&x.to_be_bytes());
    }
    pub fn u64(&mut self, x: u64) {
        self.0.extend_from_slice(&x.to_be_bytes());
    }
    pub fn bytes(&mut self, x: &[u8]) {
        self.0.extend_from_slice(x);
    }
    fn vote(&mut self, v: Vote) {
        self.u64(v.ballot);
        self.u64(v.value);
    }
    fn opt_vote(&mut self, v: Option<Vote>) {
        match v {
            None => self.u8(0),
            Some(v) => {
                self.u8(1);
                self.vote(v);
            }
        }
    }
    fn opt_u64(&mut self, v: Option<u64>) {
        match v {
            None => self.u8(0),
            Some(x) => {
                self.u8(1);
                self.u64(x);
            }
        }
    }
    fn opt_promise(&mut self, p: Option<Promise>) {
        match p {
            None => self.u8(0),
            Some(p) => {
                self.u8(1);
                self.u64(p.ballot);
                self.opt_vote(p.accepted);
            }
        }
    }
    pub fn msg(&mut self, m: &Msg) {
        match *m {
            Msg::Request { value } => {
                self.u8(0);
                self.u64(value);
            }
            Msg::Prepare { ballot } => {
                self.u8(1);
                self.u64(ballot);
            }
            Msg::Promise { ballot, accepted } => {
                self.u8(2);
                self.u64(ballot);
                self.opt_vote(accepted);
            }
            Msg::Accept { vote } => {
                self.u8(3);
                self.vote(vote);
            }
            Msg::Accepted { vote } => {
                self.u8(4);
                self.vote(vote);
            }
            Msg::Nack { ballot, promised } => {
                self.u8(5);
                self.u64(ballot);
                self.u64(promised);
            }
        }
    }
    pub fn send(&mut self, s: &Send) {
        match s.to {
            Dest::All => self.u8(0xff),
            Dest::To(i) => self.u8(i),
        }
        self.msg(&s.msg);
    }
    /// Vector lengths are written as u16; callers only store nodes whose
    /// vectors have at most `MAX_REPLICAS` entries.
    pub fn node(&mut self, n: &Node) {
        self.u8(n.id);
        self.u8(n.n);
        self.u64(n.promised);
        self.opt_vote(n.accepted);
        self.opt_u64(n.value);
        self.u64(n.ballot);
        self.u64(n.max_seen);
        self.opt_u64(n.proposal);
        self.u16(n.promises.len() as u16);
        for p in &n.promises {
            self.opt_promise(*p);
        }
        self.u16(n.votes.len() as u16);
        for v in &n.votes {
            self.opt_vote(*v);
        }
        self.opt_u64(n.decided);
    }
}

pub struct Reader<'a> {
    buf: &'a [u8],
    pos: usize,
}

impl<'a> Reader<'a> {
    pub fn new(buf: &'a [u8]) -> Self {
        Reader { buf, pos: 0 }
    }
    pub fn done(&self) -> bool {
        self.pos == self.buf.len()
    }
    pub fn take(&mut self, n: usize) -> Option<&'a [u8]> {
        let end = self.pos.checked_add(n)?;
        let out = self.buf.get(self.pos..end)?;
        self.pos = end;
        Some(out)
    }
    pub fn u8(&mut self) -> Option<u8> {
        Some(self.take(1)?[0])
    }
    pub fn u16(&mut self) -> Option<u16> {
        Some(u16::from_be_bytes(self.take(2)?.try_into().ok()?))
    }
    pub fn u32(&mut self) -> Option<u32> {
        Some(u32::from_be_bytes(self.take(4)?.try_into().ok()?))
    }
    pub fn u64(&mut self) -> Option<u64> {
        Some(u64::from_be_bytes(self.take(8)?.try_into().ok()?))
    }
    fn vote(&mut self) -> Option<Vote> {
        Some(Vote {
            ballot: self.u64()?,
            value: self.u64()?,
        })
    }
    fn opt_vote(&mut self) -> Option<Option<Vote>> {
        match self.u8()? {
            0 => Some(None),
            1 => Some(Some(self.vote()?)),
            _ => None,
        }
    }
    fn opt_u64(&mut self) -> Option<Option<u64>> {
        match self.u8()? {
            0 => Some(None),
            1 => Some(Some(self.u64()?)),
            _ => None,
        }
    }
    fn opt_promise(&mut self) -> Option<Option<Promise>> {
        match self.u8()? {
            0 => Some(None),
            1 => Some(Some(Promise {
                ballot: self.u64()?,
                accepted: self.opt_vote()?,
            })),
            _ => None,
        }
    }
    /// A u16 length prefix, rejected above `MAX_REPLICAS`.
    fn len(&mut self) -> Option<usize> {
        let n = self.u16()? as usize;
        if n > MAX_REPLICAS {
            return None;
        }
        Some(n)
    }
    pub fn msg(&mut self) -> Option<Msg> {
        Some(match self.u8()? {
            0 => Msg::Request { value: self.u64()? },
            1 => Msg::Prepare { ballot: self.u64()? },
            2 => Msg::Promise {
                ballot: self.u64()?,
                accepted: self.opt_vote()?,
            },
            3 => Msg::Accept { vote: self.vote()? },
            4 => Msg::Accepted { vote: self.vote()? },
            5 => Msg::Nack {
                ballot: self.u64()?,
                promised: self.u64()?,
            },
            _ => return None,
        })
    }
    pub fn send(&mut self) -> Option<Send> {
        let to = match self.u8()? {
            0xff => Dest::All,
            i => Dest::To(i),
        };
        Some(Send {
            to,
            msg: self.msg()?,
        })
    }
    pub fn node(&mut self) -> Option<Node> {
        Some(Node {
            id: self.u8()?,
            n: self.u8()?,
            promised: self.u64()?,
            accepted: self.opt_vote()?,
            value: self.opt_u64()?,
            ballot: self.u64()?,
            max_seen: self.u64()?,
            proposal: self.opt_u64()?,
            promises: {
                let len = self.len()?;
                let mut ps = Vec::with_capacity(len);
                for _ in 0..len {
                    ps.push(self.opt_promise()?);
                }
                ps
            },
            votes: {
                let len = self.len()?;
                let mut vs = Vec::with_capacity(len);
                for _ in 0..len {
                    vs.push(self.opt_vote()?);
                }
                vs
            },
            decided: self.opt_u64()?,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn roundtrip_send(s: Send) {
        let mut w = Writer::default();
        w.send(&s);
        let mut r = Reader::new(&w.0);
        assert!(r.send() == Some(s));
        assert!(r.done());
        for cut in 0..w.0.len() {
            let mut r = Reader::new(&w.0[..cut]);
            assert!(r.send().is_none() || !r.done() || cut == w.0.len());
        }
    }

    #[test]
    fn messages_roundtrip_and_truncations_fail() {
        let v = Vote { ballot: 7, value: u64::MAX };
        for msg in [
            Msg::Request { value: 3 },
            Msg::Prepare { ballot: 4 },
            Msg::Promise { ballot: 5, accepted: None },
            Msg::Promise { ballot: 5, accepted: Some(v) },
            Msg::Accept { vote: v },
            Msg::Accepted { vote: v },
            Msg::Nack { ballot: 1, promised: 2 },
        ] {
            roundtrip_send(Send { to: Dest::All, msg });
            roundtrip_send(Send { to: Dest::To(2), msg });
            roundtrip_send(Send { to: Dest::To(254), msg });
        }
        // Unknown message tag.
        assert!(Reader::new(&[3, 9, 0, 0, 0, 0, 0, 0, 0, 1]).send().is_none());
        assert!(Reader::new(&[0xff, 9]).send().is_none());
    }

    fn sample() -> Node {
        let mut n = Node::new(2, 5);
        n.promised = 12;
        n.accepted = Some(Vote { ballot: 12, value: 1 });
        n.value = Some(1);
        n.ballot = 12;
        n.promises[1] = Some(Promise { ballot: 12, accepted: None });
        n.promises[4] = Some(Promise {
            ballot: 12,
            accepted: Some(Vote { ballot: 5, value: 9 }),
        });
        n.proposal = Some(1);
        n.votes[0] = Some(Vote { ballot: 12, value: 1 });
        n.votes[3] = Some(Vote { ballot: 7, value: 2 });
        n.decided = Some(1);
        n
    }

    #[test]
    fn node_state_roundtrips_and_truncations_fail() {
        let n = sample();
        let mut w = Writer::default();
        w.node(&n);
        let mut r = Reader::new(&w.0);
        assert!(r.node() == Some(n));
        assert!(r.done());
        for cut in 0..w.0.len() {
            assert!(Reader::new(&w.0[..cut]).node().is_none(), "cut {cut}");
        }
    }

    #[test]
    fn node_decoding_rejects_bad_lengths_and_entries() {
        let mut n = Node::new(0, 1);
        n.promises.clear();
        n.votes.clear();
        let mut w = Writer::default();
        w.node(&n);
        // Layout: id, n, promised(8), accepted(1), value(1), ballot(8),
        // max_seen(8), proposal(1), then the promises length.
        let at = 2 + 8 + 1 + 1 + 8 + 8 + 1;
        assert_eq!(&w.0[at..at + 2], &[0, 0]);
        let mut long = w.0.clone();
        long[at..at + 2].copy_from_slice(&256u16.to_be_bytes());
        assert!(Reader::new(&long).node().is_none());
        // One promise entry with an unknown option tag.
        let mut bad = w.0[..at].to_vec();
        bad.extend_from_slice(&[0, 1, 7]);
        bad.extend_from_slice(&w.0[at + 2..]);
        assert!(Reader::new(&bad).node().is_none());
    }
}

//! Byte encodings for protocol messages, replica state and client requests.
//! Decoding rejects truncated input, trailing bytes and unknown tags.

use deployable_paxos::{Dest, Msg, Node, Send, Vote};

#[derive(Default)]
pub struct Writer(pub Vec<u8>);

impl Writer {
    pub fn u8(&mut self, x: u8) {
        self.0.push(x);
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
    fn slot(&mut self, v: Option<Option<Vote>>) {
        match v {
            None => self.u8(0),
            Some(p) => {
                self.u8(1);
                self.opt_vote(p);
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
    pub fn node(&mut self, n: &Node) {
        self.u8(n.id);
        self.u64(n.promised);
        self.opt_vote(n.accepted);
        self.opt_u64(n.value);
        self.u64(n.ballot);
        self.u64(n.max_seen);
        self.opt_u64(n.proposal);
        self.slot(n.promise0);
        self.slot(n.promise1);
        self.slot(n.promise2);
        self.opt_vote(n.vote0);
        self.opt_vote(n.vote1);
        self.opt_vote(n.vote2);
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
    fn slot(&mut self) -> Option<Option<Option<Vote>>> {
        match self.u8()? {
            0 => Some(None),
            1 => Some(Some(self.opt_vote()?)),
            _ => None,
        }
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
            i if i < 3 => Dest::To(i),
            _ => return None,
        };
        Some(Send {
            to,
            msg: self.msg()?,
        })
    }
    pub fn node(&mut self) -> Option<Node> {
        Some(Node {
            id: self.u8()?,
            promised: self.u64()?,
            accepted: self.opt_vote()?,
            value: self.opt_u64()?,
            ballot: self.u64()?,
            max_seen: self.u64()?,
            proposal: self.opt_u64()?,
            promise0: self.slot()?,
            promise1: self.slot()?,
            promise2: self.slot()?,
            vote0: self.opt_vote()?,
            vote1: self.opt_vote()?,
            vote2: self.opt_vote()?,
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
        }
        assert!(Reader::new(&[3, 1, 0, 0, 0, 0, 0, 0, 0, 1]).send().is_none());
        assert!(Reader::new(&[0xff, 9]).send().is_none());
    }

    #[test]
    fn node_state_roundtrips() {
        let mut n = Node::new(2);
        n.promised = 8;
        n.accepted = Some(Vote { ballot: 8, value: 1 });
        n.value = Some(1);
        n.ballot = 8;
        n.promise1 = Some(None);
        n.promise2 = Some(Some(Vote { ballot: 5, value: 9 }));
        n.proposal = Some(1);
        n.vote0 = Some(Vote { ballot: 8, value: 1 });
        n.decided = Some(1);
        let mut w = Writer::default();
        w.node(&n);
        let mut r = Reader::new(&w.0);
        assert!(r.node() == Some(n));
        assert!(r.done());
    }
}

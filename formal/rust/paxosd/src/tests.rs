use super::*;

/// Deterministic xorshift generator so failures are reproducible from the seed.
struct Rng(u64);

impl Rng {
    fn next(&mut self) -> u64 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        self.0
    }
    fn below(&mut self, n: u64) -> u64 {
        self.next() % n
    }
}

#[derive(Clone, Copy, PartialEq, Eq)]
struct Packet {
    src: u8,
    send: Send,
}

fn addressed(p: &Packet, to: u8) -> bool {
    match p.send.to {
        Dest::All => true,
        Dest::To(i) => i == to,
    }
}

/// The verified network model: every emitted packet is retained forever and
/// may be delivered any number of times, in any order, or never.
struct World {
    nodes: Vec<Node>,
    net: Vec<Packet>,
    submitted: Vec<u64>,
}

impl World {
    fn new() -> World {
        World::sized(3)
    }

    fn sized(n: u8) -> World {
        World {
            nodes: (0..n).map(|i| Node::new(i, n)).collect(),
            net: Vec::new(),
            submitted: Vec::new(),
        }
    }

    fn apply(&mut self, i: u8, input: Input) {
        if let Input::Submit { value } = input {
            self.submitted.push(value);
        }
        if let Some(send) = self.nodes[i as usize].handle(input) {
            let packet = Packet { src: i, send };
            if !self.net.contains(&packet) {
                self.net.push(packet);
            }
        }
    }

    fn deliver(&mut self, i: u8, k: usize) -> bool {
        let p = self.net[k];
        if !addressed(&p, i) {
            return false;
        }
        self.apply(i, Input::Deliver { from: p.src, msg: p.send.msg });
        true
    }

    fn check_safety(&self) {
        let decided: Vec<u64> = self.nodes.iter().filter_map(|n| n.decided).collect();
        for d in &decided {
            assert_eq!(*d, decided[0], "agreement violated");
            assert!(self.submitted.contains(d), "validity violated");
        }
    }
}

#[test]
fn happy_path_decides_on_every_replica() {
    let mut w = World::new();
    w.apply(2, Input::Submit { value: 42 });
    for i in 0..3 {
        w.deliver(i, 0);
    }
    w.apply(0, Input::Tick);
    // Deliver everything repeatedly until quiescent.
    for _ in 0..5 {
        for k in 0..w.net.len() {
            for i in 0..3 {
                w.deliver(i, k);
            }
        }
    }
    for n in &w.nodes {
        assert_eq!(n.decided, Some(42));
    }
}

#[test]
fn preempted_leader_retries_and_keeps_chosen_value() {
    let mut w = World::new();
    w.apply(0, Input::Submit { value: 7 });
    w.apply(1, Input::Submit { value: 9 });
    w.deliver(0, 0);
    w.deliver(1, 1);
    w.deliver(2, 1);
    assert_eq!(w.nodes[1].value, Some(9));
    // Replica 0 gets value 7 chosen by acceptors 0 and 1.
    w.apply(0, Input::Tick);
    let prepare = w.net.len() - 1;
    w.deliver(0, prepare);
    w.deliver(1, prepare);
    let promises: Vec<usize> = (0..w.net.len())
        .filter(|&k| matches!(w.net[k].send.msg, Msg::Promise { .. }))
        .collect();
    for k in promises {
        w.deliver(0, k);
    }
    let accept = w.net.len() - 1;
    assert!(matches!(w.net[accept].send.msg, Msg::Accept { vote } if vote.value == 7));
    w.deliver(0, accept);
    w.deliver(1, accept);
    // Replica 1 starts a higher ballot; it must adopt 7, not its own 9.
    w.apply(1, Input::Tick);
    let prepare = w.net.len() - 1;
    w.deliver(1, prepare);
    w.deliver(2, prepare);
    let promises: Vec<usize> = (0..w.net.len())
        .filter(|&k| matches!(w.net[k].send.msg, Msg::Promise { ballot, .. } if ballot % 3 == 1))
        .collect();
    for k in promises {
        w.deliver(1, k);
    }
    assert_eq!(w.nodes[1].proposal, Some(7));
    // The stale leader's retransmission is refused; the nack makes it retry.
    w.apply(0, Input::Tick);
    let old_accept = w
        .net
        .iter()
        .position(|p| p.src == 0 && matches!(p.send.msg, Msg::Accept { .. }))
        .unwrap();
    w.deliver(2, old_accept);
    let nack = w.net.len() - 1;
    assert!(matches!(w.net[nack].send.msg, Msg::Nack { .. }));
    w.deliver(0, nack);
    assert!(w.nodes[0].max_seen > w.nodes[0].ballot);
    w.apply(0, Input::Tick);
    assert!(w.nodes[0].ballot > w.nodes[1].ballot);
    w.check_safety();
}

#[test]
fn malformed_inputs_are_ignored_without_panicking() {
    let mut n = Node::new(1, 3);
    let before = n.clone();
    assert!(n
        .handle(Input::Deliver { from: 3, msg: Msg::Prepare { ballot: 5 } })
        .is_none());
    assert!(n == before);
    let mut n = Node::new(2, 3);
    n.max_seen = u64::MAX;
    n.ballot = 5;
    assert!(n.handle(Input::Tick).is_none(), "ballot space exhausted");
    let mut n = Node::new(255, 255);
    n.value = Some(1);
    n.handle(Input::Tick);
    assert_eq!(n.ballot, 255 + 255);
    // Vectors shorter than the cluster size (never produced by `new`) are tolerated.
    let mut n = Node::new(0, 3);
    n.promises.clear();
    n.votes.clear();
    n.ballot = 3;
    n.value = Some(1);
    let v = Vote { ballot: 3, value: 1 };
    assert!(n.handle(Input::Deliver { from: 2, msg: Msg::Promise { ballot: 3, accepted: None } }).is_none());
    assert!(n.handle(Input::Deliver { from: 2, msg: Msg::Accepted { vote: v } }).is_none());
    let mut n = Node::new(0, 0);
    n.value = Some(1);
    assert!(n.handle(Input::Tick).is_none(), "empty cluster");
}

#[test]
fn ballot_allocation_is_owned_and_increasing() {
    for n in [1u8, 2, 3, 5, 255] {
        for floor in [0u64, 1, 2, 3, 4, 5, 1000, BALLOT_LIMIT - 1] {
            for id in 0..n {
                let b = next_ballot(floor, id, n);
                assert!(b > floor);
                assert_eq!(b % n as u64, id as u64);
                assert!(b < floor + 2 * n as u64);
            }
        }
    }
}

/// Random adversarial schedules, including restarts from durable state
/// (which is the current state, since the runtime persists before sending).
#[test]
fn randomized_schedules_preserve_safety_and_decide_after_stabilization() {
    for seed in 1..=300u64 {
        let mut rng = Rng(seed.wrapping_mul(0x9E37_79B9_7F4A_7C15) | 1);
        let size = [1u8, 2, 3, 4, 5, 7][rng.below(6) as usize];
        let mut w = World::sized(size);
        let chaos = 50 + rng.below(400);
        for _ in 0..chaos {
            let i = rng.below(size as u64) as u8;
            match rng.below(10) {
                0 => w.apply(i, Input::Submit { value: rng.below(5) }),
                1 | 2 => w.apply(i, Input::Tick),
                _ => {
                    if !w.net.is_empty() {
                        let k = rng.below(w.net.len() as u64) as usize;
                        w.deliver(i, k);
                    }
                }
            }
            w.check_safety();
        }
        // Stabilization: one leader with a client value, a crashed minority,
        // fair delivery among the rest, and a periodic timer at the leader.
        let leader = rng.below(size as u64) as u8;
        let mut crashed: Vec<u8> = Vec::new();
        for i in 0..size {
            if i != leader && (crashed.len() + 1) * 2 < size as usize && rng.below(2) == 0 {
                crashed.push(i);
            }
        }
        w.apply(leader, Input::Submit { value: 99 });
        let quorum: Vec<u8> = (0..size).filter(|i| !crashed.contains(i)).collect();
        let mut rounds = 0;
        while quorum.iter().any(|&i| w.nodes[i as usize].decided.is_none()) {
            rounds += 1;
            assert!(rounds < 200, "seed {seed}: no decision after stabilization");
            w.apply(leader, Input::Tick);
            let mut k = 0;
            while k < w.net.len() {
                if !crashed.contains(&w.net[k].src) {
                    for &i in &quorum {
                        w.deliver(i, k);
                    }
                }
                k += 1;
            }
            w.check_safety();
        }
    }
}

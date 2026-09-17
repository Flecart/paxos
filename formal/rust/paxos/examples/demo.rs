//! Executable in-process transport demonstration; the verified library owns the
//! protocol transitions. Socket transport and crash recovery are not modeled here.
use verified_paxos::{learn, Acceptor, Proposer};

fn main() {
    let offered = std::env::args()
        .nth(1)
        .unwrap_or_else(|| "42".into())
        .parse::<u64>()
        .expect("value must be a u64");
    let mut acceptors: [Acceptor; 3] = std::array::from_fn(|_| Acceptor::new());
    let mut proposer = Proposer::new(1);
    let left = acceptors[0].prepare(1).unwrap();
    let right = acceptors[2].prepare(1).unwrap();
    let vote = proposer.issue(0, left, 2, right, offered).unwrap();
    assert!(acceptors[1].accept(vote));
    assert!(acceptors[2].accept(vote));
    println!("chosen={}", learn(1, vote, 2, vote).unwrap());
}

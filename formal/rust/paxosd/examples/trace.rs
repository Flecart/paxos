//! Print every step of three replicas running the verified `Node::handle`,
//! with an in-memory network that delivers packets in send order.
use deployable_paxos::{Dest, Input, Msg, Node, Send};
use std::collections::VecDeque;

fn show(m: &Msg) -> String {
    match *m {
        Msg::Request { value } => format!("Request({value})"),
        Msg::Prepare { ballot } => format!("Prepare(b={ballot})"),
        Msg::Promise { ballot, accepted } => match accepted {
            Some(v) => format!("Promise(b={ballot}, accepted=({},{}))", v.ballot, v.value),
            None => format!("Promise(b={ballot}, accepted=none)"),
        },
        Msg::Accept { vote } => format!("Accept(b={}, v={})", vote.ballot, vote.value),
        Msg::Accepted { vote } => format!("Accepted(b={}, v={})", vote.ballot, vote.value),
        Msg::Nack { ballot, promised } => format!("Nack(b={ballot}, promised={promised})"),
    }
}

fn step(nodes: &mut [Node], net: &mut VecDeque<(u8, u8, Msg)>, i: u8, input: Input, label: &str) {
    let out = nodes[i as usize].handle(input);
    let n = &nodes[i as usize];
    print!("r{i} <- {label:34}");
    match out {
        Some(Send { to, msg }) => {
            let dest = match to { Dest::All => "all".to_string(), Dest::To(j) => format!("r{j}") };
            print!(" -> {:34} to {dest}", show(&msg));
            for j in 0..nodes.len() as u8 {
                if matches!(to, Dest::All) || to == Dest::To(j) { net.push_back((i, j, msg)); }
            }
        }
        None => print!(" {:40}", ""),
    }
    println!("  [promised={} ballot={} decided={:?}]", n.promised, n.ballot, n.decided);
}

fn run(nodes: &mut [Node], net: &mut VecDeque<(u8, u8, Msg)>, down: Option<u8>) {
    while let Some((from, to, msg)) = net.pop_front() {
        if Some(to) == down || Some(from) == down { continue; }
        step(nodes, net, to, Input::Deliver { from, msg }, &format!("{} from r{from}", show(&msg)));
    }
}

fn main() {
    let mut nodes: Vec<Node> = (0..3).map(|i| Node::new(i, 3)).collect();
    let mut net = VecDeque::new();
    println!("== client submits 42 at r2; r0 leads");
    step(&mut nodes, &mut net, 2, Input::Submit { value: 42 }, "Submit(42)");
    run(&mut nodes, &mut net, None);
    step(&mut nodes, &mut net, 0, Input::Tick, "Tick");
    run(&mut nodes, &mut net, None);
    println!("\n== r0 crashes; r1 takes over with value 7 and must re-propose 42");
    step(&mut nodes, &mut net, 1, Input::Submit { value: 7 }, "Submit(7)");
    run(&mut nodes, &mut net, Some(0));
    step(&mut nodes, &mut net, 1, Input::Tick, "Tick");
    run(&mut nodes, &mut net, Some(0));
}

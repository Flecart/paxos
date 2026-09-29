//! Process-level tests: clusters of `paxosd` replicas on localhost UDP.

use std::net::UdpSocket;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::time::Duration;

const KEY: &str = "cluster-test-shared-secret";

struct Cluster {
    ports: Vec<u16>,
    dir: PathBuf,
    children: Vec<Option<Child>>,
}

impl Cluster {
    /// A cluster of `size` replicas; none is started yet.
    fn new(name: &str, size: usize) -> Cluster {
        let ports = (0..size)
            .map(|_| UdpSocket::bind("127.0.0.1:0").unwrap().local_addr().unwrap().port())
            .collect();
        let dir = std::env::temp_dir().join(format!("paxosd-{name}-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&dir);
        Cluster { ports, dir, children: (0..size).map(|_| None).collect() }
    }

    fn size(&self) -> usize {
        self.ports.len()
    }

    fn addr(&self, i: usize) -> String {
        format!("127.0.0.1:{}", self.ports[i])
    }

    fn start(&mut self, i: usize) {
        let peers: Vec<String> = (0..self.size()).map(|j| self.addr(j)).collect();
        let child = Command::new(env!("CARGO_BIN_EXE_paxosd"))
            .args(["serve", "--id", &i.to_string(), "--peers", &peers.join(",")])
            .args(["--data", self.dir.join(i.to_string()).to_str().unwrap(), "--key", KEY])
            .args(["--tick-ms", "20", "--suspect-ms", "300"])
            .stderr(Stdio::null())
            .spawn()
            .unwrap();
        self.children[i] = Some(child);
        std::thread::sleep(Duration::from_millis(100));
    }

    fn kill(&mut self, i: usize) {
        if let Some(mut c) = self.children[i].take() {
            c.kill().unwrap();
            c.wait().unwrap();
        }
    }

    fn cli(&self, args: &[&str]) -> String {
        let out = Command::new(env!("CARGO_BIN_EXE_paxosd")).args(args).output().unwrap();
        String::from_utf8(out.stdout).unwrap().trim().to_string()
    }

    fn propose(&self, i: usize, value: u64) -> String {
        self.cli(&["propose", "--node", &self.addr(i), "--timeout-ms", "15000", &value.to_string()])
    }

    fn status(&self, i: usize) -> String {
        self.cli(&["status", "--node", &self.addr(i)])
    }

    fn await_status(&self, i: usize, want: &str) {
        for _ in 0..150 {
            if self.status(i) == want {
                return;
            }
            std::thread::sleep(Duration::from_millis(100));
        }
        panic!("replica {i} did not reach {want:?}; last status {:?}", self.status(i));
    }
}

impl Drop for Cluster {
    fn drop(&mut self) {
        for i in 0..self.size() {
            self.kill(i);
        }
        let _ = std::fs::remove_dir_all(&self.dir);
    }
}

#[test]
fn decides_once_and_recovers_from_restart() {
    let mut c = Cluster::new("basic", 3);
    for i in 0..3 {
        c.start(i);
    }
    assert_eq!(c.propose(2, 42), "decided 42");
    for i in 0..3 {
        c.await_status(i, "decided 42");
    }
    // Single decree: a later proposal returns the existing decision.
    assert_eq!(c.propose(1, 7), "decided 42");
    // The leader crashes and restarts from its durable state.
    c.kill(0);
    c.start(0);
    assert_eq!(c.status(0), "decided 42");
}

#[test]
fn majority_without_the_preferred_leader_decides_and_late_replica_catches_up() {
    let mut c = Cluster::new("failover", 3);
    c.start(1);
    c.start(2);
    assert_eq!(c.propose(2, 5), "decided 5");
    c.await_status(1, "decided 5");
    c.start(0);
    c.await_status(0, "decided 5");
}

#[test]
fn concurrent_conflicting_proposals_agree() {
    let mut c = Cluster::new("concurrent", 3);
    for i in 0..3 {
        c.start(i);
    }
    let answers: Vec<String> = std::thread::scope(|s| {
        let handles: Vec<_> = (0..3)
            .map(|i| {
                let c = &c;
                s.spawn(move || c.propose(i, 100 + i as u64))
            })
            .collect();
        handles.into_iter().map(|h| h.join().unwrap()).collect()
    });
    assert!(answers.iter().all(|a| a == &answers[0]), "{answers:?}");
    assert!(["decided 100", "decided 101", "decided 102"].contains(&answers[0].as_str()));
    for i in 0..3 {
        c.await_status(i, &answers[0]);
    }
}

#[test]
fn crashes_during_the_protocol_do_not_break_agreement() {
    let mut c = Cluster::new("crashes", 3);
    for i in 0..3 {
        c.start(i);
    }
    let addr = c.addr(2);
    let proposer = std::thread::spawn(move || {
        let out = Command::new(env!("CARGO_BIN_EXE_paxosd"))
            .args(["propose", "--node", &addr, "--timeout-ms", "20000", "77"])
            .output()
            .unwrap();
        String::from_utf8(out.stdout).unwrap().trim().to_string()
    });
    // Crash and restart every replica in turn while the value is being decided,
    // including replica 2, which is serving the client.
    for round in [0, 1, 2, 0] {
        c.kill(round);
        std::thread::sleep(Duration::from_millis(60));
        c.start(round);
    }
    assert_eq!(proposer.join().unwrap(), "decided 77");
    for i in 0..3 {
        c.await_status(i, "decided 77");
    }
}

#[test]
fn five_replicas_decide_without_the_two_preferred_leaders_and_late_replica_catches_up() {
    let mut c = Cluster::new("failover5", 5);
    // Replicas 0 and 1 are down; 2, 3 and 4 form a majority and 2 must lead.
    for i in 2..5 {
        c.start(i);
    }
    assert_eq!(c.propose(4, 9), "decided 9");
    for i in 2..5 {
        c.await_status(i, "decided 9");
    }
    c.start(0);
    c.await_status(0, "decided 9");
    assert_eq!(c.propose(0, 11), "decided 9");
}

#[test]
fn five_replicas_concurrent_conflicting_proposals_agree() {
    let mut c = Cluster::new("concurrent5", 5);
    for i in 0..5 {
        c.start(i);
    }
    let answers: Vec<String> = std::thread::scope(|s| {
        let handles: Vec<_> = (0..5)
            .map(|i| {
                let c = &c;
                s.spawn(move || c.propose(i, 200 + i as u64))
            })
            .collect();
        handles.into_iter().map(|h| h.join().unwrap()).collect()
    });
    assert!(answers.iter().all(|a| a == &answers[0]), "{answers:?}");
    let allowed: Vec<String> = (200..205).map(|v| format!("decided {v}")).collect();
    assert!(allowed.contains(&answers[0]), "{answers:?}");
    for i in 0..5 {
        c.await_status(i, &answers[0]);
    }
}

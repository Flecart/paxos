//! `paxosd`: a three-replica Paxos service around the verified `Node`.
//!
//! The runtime implements the environment contract of the Lean model:
//! * inputs are processed one at a time; the new replica state and the packet it
//!   emits are made durable *before* the packet leaves the process;
//! * every packet a replica has sent is retransmitted forever (with backoff),
//!   also after restarts, so fair-lossy links deliver it eventually;
//! * packets carry an HMAC over sender, destination and message; a replica
//!   delivers only packets addressed to it. Replays are harmless: the model
//!   already allows any sent packet to be delivered again;
//! * only replicas that suspect every lower-numbered replica fire the protocol
//!   timer, which approximates the stable-leader assumption of the liveness proof.
//!
//! Commands:
//!   paxosd serve   --id N --peers A0,A1,A2 --data DIR --key SECRET [--tick-ms 50] [--suspect-ms 600]
//!   paxosd propose --node ADDR VALUE [--timeout-ms 10000]
//!   paxosd status  --node ADDR

mod sha256;
mod store;
mod wire;

use deployable_paxos::{Dest, Input, Node, Send};
use std::collections::VecDeque;
use std::io;
use std::net::{SocketAddr, ToSocketAddrs, UdpSocket};
use std::path::PathBuf;
use std::process::ExitCode;
use std::time::{Duration, Instant};
use store::Store;
use wire::{Reader, Writer};

const PEER: &[u8; 4] = b"PXP1";
const HEARTBEAT: &[u8; 4] = b"PXH1";
const CLIENT: &[u8; 4] = b"PXC1";
const REPLY: &[u8; 4] = b"PXR1";
const TAG: usize = 16;
const OUTBOX_LIMIT: usize = 100_000;

struct Config {
    id: u8,
    peers: Vec<SocketAddr>,
    data: PathBuf,
    key: Vec<u8>,
    tick: Duration,
    suspect: Duration,
}

struct Server {
    cfg: Config,
    sock: UdpSocket,
    store: Store,
    node: Node,
    outbox: Vec<Send>,
    heard: [Instant; 3],
    waiting: Vec<SocketAddr>,
    next_tick: Instant,
    next_resend: Instant,
    resend_gap: Duration,
}

fn sign(key: &[u8], body: &[u8]) -> [u8; TAG] {
    let mut tag = [0u8; TAG];
    tag.copy_from_slice(&sha256::hmac(key, body)[..TAG]);
    tag
}

fn log(id: u8, text: &str) {
    eprintln!("[replica {id}] {text}");
}

impl Server {
    fn start(cfg: Config) -> io::Result<Server> {
        let sock = UdpSocket::bind(cfg.peers[cfg.id as usize])?;
        sock.set_read_timeout(Some(cfg.tick / 2))?;
        let store = Store::open(&cfg.data)?;
        let (node, outbox) = match store.load(cfg.id)? {
            Some(saved) => {
                log(cfg.id, &format!("recovered durable state, {} packets to retransmit", saved.1.len()));
                saved
            }
            None => (Node::new(cfg.id), Vec::new()),
        };
        let now = Instant::now();
        let tick = cfg.tick;
        let server = Server {
            cfg,
            sock,
            store,
            node,
            outbox,
            // A (re)started replica first listens for a while before leading.
            heard: [now; 3],
            waiting: Vec::new(),
            next_tick: now,
            next_resend: now,
            resend_gap: tick,
        };
        server.store.save(&server.node, &server.outbox)?;
        Ok(server)
    }

    fn peer_packet(&self, send: &Send) -> Vec<u8> {
        let mut w = Writer::default();
        w.bytes(PEER);
        w.u8(self.cfg.id);
        w.send(send);
        let tag = sign(&self.cfg.key, &w.0);
        w.bytes(&tag);
        w.0
    }

    fn transmit(&self, send: &Send) {
        let bytes = self.peer_packet(send);
        for (j, addr) in self.cfg.peers.iter().enumerate() {
            let wanted = match send.to {
                Dest::All => true,
                Dest::To(i) => i as usize == j,
            };
            if wanted && j != self.cfg.id as usize {
                // Loss is tolerated by the model; retransmission recovers it.
                let _ = self.sock.send_to(&bytes, addr);
            }
        }
    }

    /// Run one input through the verified state machine, persisting before sending.
    fn process(&mut self, input: Input) -> io::Result<()> {
        let mut queue = VecDeque::from([input]);
        while let Some(input) = queue.pop_front() {
            let before = self.node;
            let out = self.node.handle(input);
            let mut dirty = self.node != before;
            if let Some(send) = out {
                if !self.outbox.contains(&send) {
                    if self.outbox.len() >= OUTBOX_LIMIT {
                        log(self.cfg.id, "outbox limit reached; dropping the oldest packet");
                        self.outbox.remove(0);
                    }
                    self.outbox.push(send);
                    dirty = true;
                    self.resend_gap = self.cfg.tick;
                }
            }
            if dirty {
                self.store.save(&self.node, &self.outbox)?;
            }
            if before.decided.is_none() {
                if let Some(v) = self.node.decided {
                    log(self.cfg.id, &format!("decided {v}"));
                }
            }
            if let Some(send) = out {
                self.transmit(&send);
                let local = match send.to {
                    Dest::All => true,
                    Dest::To(i) => i == self.cfg.id,
                };
                if local {
                    queue.push_back(Input::Deliver {
                        from: self.cfg.id,
                        msg: send.msg,
                    });
                }
            }
        }
        self.answer_waiting();
        Ok(())
    }

    fn reply(&self, addr: SocketAddr) {
        let mut w = Writer::default();
        w.bytes(REPLY);
        match self.node.decided {
            Some(v) => {
                w.u8(1);
                w.u64(v);
            }
            None => {
                w.u8(0);
                w.u64(0);
            }
        }
        let _ = self.sock.send_to(&w.0, addr);
    }

    fn answer_waiting(&mut self) {
        if self.node.decided.is_some() {
            for addr in std::mem::take(&mut self.waiting) {
                self.reply(addr);
            }
        }
    }

    fn leading(&self, now: Instant) -> bool {
        (0..self.cfg.id as usize).all(|j| now.duration_since(self.heard[j]) > self.cfg.suspect)
    }

    fn datagram(&mut self, bytes: &[u8], from: SocketAddr) -> io::Result<()> {
        let mut r = Reader::new(bytes);
        match r.take(4) {
            Some(m) if m == PEER || m == HEARTBEAT => {
                if bytes.len() < 4 + 1 + TAG {
                    return Ok(());
                }
                let (body, tag) = bytes.split_at(bytes.len() - TAG);
                if !sha256::equal(&sign(&self.cfg.key, body), tag) {
                    return Ok(());
                }
                let mut r = Reader::new(&body[4..]);
                let src = match r.u8() {
                    Some(s) if s < 3 && s != self.cfg.id => s,
                    _ => return Ok(()),
                };
                self.heard[src as usize] = Instant::now();
                if m == PEER {
                    let send = match r.send() {
                        Some(s) if r.done() => s,
                        _ => return Ok(()),
                    };
                    let addressed = match send.to {
                        Dest::All => true,
                        Dest::To(i) => i == self.cfg.id,
                    };
                    if addressed {
                        self.process(Input::Deliver { from: src, msg: send.msg })?;
                    }
                }
            }
            Some(m) if m == CLIENT => match (r.u8(), r.u64()) {
                (Some(1), Some(value)) if r.done() => {
                    if self.node.decided.is_some() {
                        self.reply(from);
                    } else {
                        self.waiting.push(from);
                        self.process(Input::Submit { value })?;
                    }
                }
                (Some(2), Some(_)) if r.done() => self.reply(from),
                _ => {}
            },
            _ => {}
        }
        Ok(())
    }

    fn run(&mut self) -> io::Result<()> {
        let mut buf = [0u8; 2048];
        loop {
            let now = Instant::now();
            if now >= self.next_tick {
                self.next_tick = now + self.cfg.tick;
                let mut w = Writer::default();
                w.bytes(HEARTBEAT);
                w.u8(self.cfg.id);
                let tag = sign(&self.cfg.key, &w.0);
                w.bytes(&tag);
                for (j, addr) in self.cfg.peers.iter().enumerate() {
                    if j != self.cfg.id as usize {
                        let _ = self.sock.send_to(&w.0, addr);
                    }
                }
                if self.leading(now) {
                    self.process(Input::Tick)?;
                }
            }
            if now >= self.next_resend {
                for send in self.outbox.clone() {
                    self.transmit(&send);
                }
                self.resend_gap = (self.resend_gap * 2).min(Duration::from_secs(2));
                self.next_resend = now + self.resend_gap;
            }
            match self.sock.recv_from(&mut buf) {
                Ok((len, from)) => self.datagram(&buf[..len], from)?,
                Err(e)
                    if matches!(
                        e.kind(),
                        io::ErrorKind::WouldBlock
                            | io::ErrorKind::TimedOut
                            | io::ErrorKind::ConnectionRefused
                            | io::ErrorKind::ConnectionReset
                    ) => {}
                Err(e) => return Err(e),
            }
        }
    }
}

/// Ask a replica to decide `value` (or report the existing decision).
fn client(addr: &str, op: u8, value: u64, timeout: Duration) -> io::Result<Option<u64>> {
    let target = addr
        .to_socket_addrs()?
        .next()
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidInput, "bad address"))?;
    let sock = UdpSocket::bind(if target.is_ipv4() { "0.0.0.0:0" } else { "[::]:0" })?;
    sock.set_read_timeout(Some(Duration::from_millis(200)))?;
    let mut w = Writer::default();
    w.bytes(CLIENT);
    w.u8(op);
    w.u64(value);
    let deadline = Instant::now() + timeout;
    let mut buf = [0u8; 64];
    loop {
        sock.send_to(&w.0, target)?;
        if let Ok((len, _)) = sock.recv_from(&mut buf) {
            let mut r = Reader::new(&buf[..len]);
            if r.take(4) == Some(REPLY.as_slice()) {
                match (r.u8(), r.u64()) {
                    (Some(1), Some(v)) => return Ok(Some(v)),
                    (Some(0), Some(_)) if op == 2 => return Ok(None),
                    _ => {}
                }
            }
        }
        if Instant::now() >= deadline {
            return Ok(None);
        }
    }
}

fn flag<'a>(args: &'a [String], name: &str) -> Option<&'a str> {
    args.iter()
        .position(|a| a == name)
        .and_then(|i| args.get(i + 1))
        .map(|s| s.as_str())
}

fn millis(args: &[String], name: &str, default: u64) -> Result<Duration, String> {
    match flag(args, name) {
        None => Ok(Duration::from_millis(default)),
        Some(s) => s
            .parse()
            .map(Duration::from_millis)
            .map_err(|_| format!("{name} expects milliseconds")),
    }
}

fn required<'a>(args: &'a [String], name: &str) -> Result<&'a str, String> {
    flag(args, name).ok_or_else(|| format!("missing {name}"))
}

fn serve(args: &[String]) -> Result<(), String> {
    let id: u8 = required(args, "--id")?
        .parse()
        .map_err(|_| "--id expects 0, 1 or 2".to_string())?;
    let peers = required(args, "--peers")?
        .split(',')
        .map(|p| {
            p.to_socket_addrs()
                .ok()
                .and_then(|mut a| a.next())
                .ok_or_else(|| format!("bad peer address {p}"))
        })
        .collect::<Result<Vec<_>, _>>()?;
    if peers.len() != 3 || id >= 3 {
        return Err("exactly three peers are required and --id must be 0, 1 or 2".into());
    }
    let key = required(args, "--key")?.as_bytes().to_vec();
    if key.len() < 16 {
        return Err("--key must be at least 16 bytes".into());
    }
    let cfg = Config {
        id,
        peers,
        data: PathBuf::from(required(args, "--data")?),
        key,
        tick: millis(args, "--tick-ms", 50)?,
        suspect: millis(args, "--suspect-ms", 600)?,
    };
    let mut server = Server::start(cfg).map_err(|e| e.to_string())?;
    log(id, "serving");
    server.run().map_err(|e| e.to_string())
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let result = match args.first().map(|s| s.as_str()) {
        Some("serve") => serve(&args),
        Some("propose") => (|| {
            let node = required(&args, "--node")?;
            let value: u64 = args
                .last()
                .and_then(|v| v.parse().ok())
                .ok_or("propose expects a u64 value as the last argument")?;
            let timeout = millis(&args, "--timeout-ms", 10_000)?;
            match client(node, 1, value, timeout).map_err(|e| e.to_string())? {
                Some(v) => {
                    println!("decided {v}");
                    Ok(())
                }
                None => Err("no decision before the timeout".into()),
            }
        })(),
        Some("status") => (|| {
            let node = required(&args, "--node")?;
            match client(node, 2, 0, Duration::from_secs(2)).map_err(|e| e.to_string())? {
                Some(v) => println!("decided {v}"),
                None => println!("undecided"),
            }
            Ok(())
        })(),
        _ => Err("usage: paxosd serve|propose|status (see source header)".into()),
    };
    match result {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("paxosd: {e}");
            ExitCode::FAILURE
        }
    }
}

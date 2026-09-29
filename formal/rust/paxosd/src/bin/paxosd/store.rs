//! Durable replica state: the verified `Node` plus every packet it has sent.
//!
//! The file is replaced atomically (write temporary file, fsync, rename, fsync
//! directory) and carries a SHA-256 checksum. A replica refuses to start from a
//! corrupt file rather than silently resetting, which could break safety.

use crate::sha256::sha256;
use crate::wire::{Reader, Writer};
use deployable_paxos::{Node, Send};
use std::fs::{self, File};
use std::io::{self, Write};
use std::path::{Path, PathBuf};

/// `PXS2`: the N-replica layout (cluster size plus length-prefixed vectors).
const MAGIC: &[u8; 4] = b"PXS2";

pub struct Store {
    dir: PathBuf,
}

fn corrupt(what: &str) -> io::Error {
    io::Error::new(io::ErrorKind::InvalidData, format!("state file {what}"))
}

impl Store {
    pub fn open(dir: &Path) -> io::Result<Store> {
        fs::create_dir_all(dir)?;
        Ok(Store {
            dir: dir.to_path_buf(),
        })
    }

    fn path(&self) -> PathBuf {
        self.dir.join("replica.state")
    }

    /// Load the stored state of replica `id` in a cluster of `n` replicas.
    pub fn load(&self, id: u8, n: u8) -> io::Result<Option<(Node, Vec<Send>)>> {
        let bytes = match fs::read(self.path()) {
            Ok(b) => b,
            Err(e) if e.kind() == io::ErrorKind::NotFound => return Ok(None),
            Err(e) => return Err(e),
        };
        if bytes.len() < 36 {
            return Err(corrupt("is truncated"));
        }
        let (body, sum) = bytes.split_at(bytes.len() - 32);
        if sha256(body) != sum {
            return Err(corrupt("checksum mismatch"));
        }
        let mut r = Reader::new(body);
        if r.take(4) != Some(MAGIC.as_slice()) {
            return Err(corrupt("has an unknown format"));
        }
        let node = r.node().ok_or_else(|| corrupt("has a malformed replica"))?;
        if node.id != id {
            return Err(corrupt("belongs to a different replica id"));
        }
        if node.n != n {
            return Err(corrupt("belongs to a cluster of a different size"));
        }
        if node.promises.len() != n as usize || node.votes.len() != n as usize {
            return Err(corrupt("has vectors that do not match the cluster size"));
        }
        let count = r.u32().ok_or_else(|| corrupt("is truncated"))?;
        let mut outbox = Vec::new();
        for _ in 0..count {
            outbox.push(r.send().ok_or_else(|| corrupt("has a malformed packet"))?);
        }
        if !r.done() {
            return Err(corrupt("has trailing bytes"));
        }
        Ok(Some((node, outbox)))
    }

    pub fn save(&self, node: &Node, outbox: &[Send]) -> io::Result<()> {
        let mut w = Writer::default();
        w.bytes(MAGIC);
        w.node(node);
        w.u32(outbox.len() as u32);
        for s in outbox {
            w.send(s);
        }
        let sum = sha256(&w.0);
        w.bytes(&sum);
        let tmp = self.dir.join("replica.state.tmp");
        {
            let mut f = File::create(&tmp)?;
            f.write_all(&w.0)?;
            f.sync_all()?;
        }
        fs::rename(&tmp, self.path())?;
        File::open(&self.dir)?.sync_all()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use deployable_paxos::{Dest, Msg};

    #[test]
    fn save_load_and_detect_corruption() {
        let dir = std::env::temp_dir().join(format!("paxosd-store-{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        let store = Store::open(&dir).unwrap();
        assert!(store.load(1, 3).unwrap().is_none());
        let mut n = Node::new(1, 3);
        n.promised = 4;
        let outbox = vec![Send {
            to: Dest::To(1),
            msg: Msg::Nack { ballot: 3, promised: 4 },
        }];
        store.save(&n, &outbox).unwrap();
        let (m, o) = store.load(1, 3).unwrap().unwrap();
        assert!(m == n && o == outbox);
        assert!(store.load(2, 3).is_err());
        assert!(store.load(1, 5).is_err());
        // Vectors whose length disagrees with `n` are rejected.
        let mut short = n.clone();
        short.votes.pop();
        store.save(&short, &outbox).unwrap();
        assert!(store.load(1, 3).is_err());
        store.save(&n, &outbox).unwrap();
        let mut bytes = fs::read(dir.join("replica.state")).unwrap();
        bytes[6] ^= 1;
        fs::write(dir.join("replica.state"), bytes).unwrap();
        assert!(store.load(1, 3).is_err());
        fs::remove_dir_all(&dir).unwrap();
    }
}

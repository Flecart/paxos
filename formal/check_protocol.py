"""Check the RM-native Paxos model and its declared protocol contract."""
import argparse
import json
from pathlib import Path
from protocol_paxos import build
from zrth.protocol import check


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend",choices=("z3","lean","both"),default="both")
    parser.add_argument("--profile",choices=("small","compatibility"),default="small")
    parser.add_argument("--depth",type=int,default=16)
    parser.add_argument("--timeout",type=float,default=30)
    parser.add_argument("--lean-timeout",type=float,default=600)
    parser.add_argument("--out",type=Path,default=Path(__file__).resolve().parent/"protocol-evidence")
    args=parser.parse_args()
    print(f"Building direct RM Paxos ({args.profile})...",flush=True)
    protocol=build(args.profile)
    print("Checking complete RM state transitions...",flush=True)
    result=check(protocol,args.backend,directory=args.out,depth=args.depth,timeout=args.timeout,lean_timeout=args.lean_timeout)
    print(json.dumps(result,indent=2))


if __name__=="__main__": main()
